from re import DEBUG
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import pprint
import argparse
import utils
from blessed import Terminal
import inquirer


pp = pprint.PrettyPrinter(indent=4)

db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")

def run(apply):
    term = Terminal()
    with term.location(0, 0):
        print(term.clear())
        print('This is ' + term.underline('underlined') + '!', end='')

    wsize = apply['wsize']

    pd.options.display.float_format = '{:.2f}'.format

    pcaps = pd.read_sql(
        f"""SELECT * FROM PCAP ORDER BY qr """,
        db,
    )

    cur = db.cursor()
    for i, pcap in pcaps.iterrows():
        
        pcap_id = pcap['id']
        with term.location(0, 0):
            print(term.clear + f'{i+1}/{pcaps.shape[0]}\tProcessing ' + term.underline(pcap['name']), end='')

        query = f"""
            SELECT
                COUNT(*) as wcount,
                SUM(CASE WHEN RCODE=3 THEN 1 ELSE 0 END) AS wvalue,
                FLOOR(M.FN_REQ / {wsize}) AS wnum
            FROM MESSAGES_{pcap_id} AS M
                LEFT JOIN 
                (SELECT DN.ID, DN.DN, DN_NN.LOGIT FROM DN LEFT JOIN DN_NN ON (DN.ID = DN_NN.DN_ID AND NN_ID = 1))
                    AS DNN ON (M.DN_ID = DNN.ID)
            GROUP BY wnum 
            ORDER BY wnum"""

        df_windows = pd.read_sql(query, db)

        with term.location(5, 1):
            print(f'> Fetched windows number: {df_windows.shape[0]}', end='')


        df_windows['pcap_id'] = pcap_id
        df_windows['apply_id'] = apply['id']

        with term.location(5, 2):
            print(f'> Updating database...', end='')

        execute_values(
            cur,
            """INSERT INTO public.windows(
                    apply_id, pcap_id, wnum, wcount, wvalue)
                VALUES  %s;""",
            df_windows[['apply_id', 'pcap_id', 'wnum', 'wcount', 'wvalue']].values.tolist()
        )
        db.commit()
    pass #end batch


if __name__ == "__main__":

    max_top10m = utils.max_top10m(db)

    parser = argparse.ArgumentParser(description='Apply LLR window function.')
    parser.add_argument('--wsize', required=False,
                        default=500,
                        type=int,
                        choices=[ 100, 500, 2500 ],
                        help=f'Windows size.')
    parser.add_argument('--redo', help='If present the program will overwrite previous applies.', action=argparse.BooleanOptionalAction)
    parser.add_argument('name', metavar="NAME", help='The name of this LLR window function.')
    args = parser.parse_args()

    apply = dict(name=args.name, wsize=args.wsize, wtype='nx', nn_id=None, top10m=None, windowing='res', pinf=None, ninf=None)

    ###
    apply_tmp = utils.get_apply(db, apply)
    
    if apply_tmp is None:
        yn = utils.get_yn(f"Function not exists, create it? [Y/n]\n{apply}")
        if yn == 'y':
            apply = utils.create_apply(db, apply)
        else:
            exit(0)
    else:
        apply = apply_tmp
    ###

    ###
    if args.redo == False or args.redo is None:
        num_applied_windows = utils.count_applied_windows(db, apply['id'])
        num_toapply_windows = utils.count_toapply_windows(db, apply['wsize'])

        if num_applied_windows > 0:
            questions = [
            inquirer.List('overwrite',
                    message=f"{num_applied_windows} on {num_toapply_windows} already applied with '{apply['name']}' and wsize {args.wsize}, overwrite?",
                    choices=[ 'Cancel', 'Re-do', 'Fill' ],
                ),
            ]
            answers = inquirer.prompt(questions)
            if answers['overwrite'] == 'Re-do':
                with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("DELETE FROM windows WHERE apply_id=%s", [ apply['id'] ])
                    print("Deleted previous apply.")
            elif answers['overwrite'] == 'Cancel':
                print('Exiting')
                exit(1)
    ###

    run(apply)
    
    pass
