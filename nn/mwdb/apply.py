from re import DEBUG
from numpy.lib.arraysetops import unique
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import pprint
import argparse
import utils
import inquirer

pp = pprint.PrettyPrinter(indent=4)

db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")


def get_llr_query(pcap_id, wsize):
    tmp_llr = f"""
            CASE WHEN LOGIT IS NULL THEN 0 ELSE 
                (CASE WHEN LOGIT = 'Infinity' THEN {apply["pinf"]} ElSE
                    (CASE WHEN LOGIT='-Infinity' THEN {apply["ninf"]} ELSE LOGIT END)
                END)
            END"""
        
    if not(apply['top10m'] is None):
        tmp_llr = f"""CASE WHEN TOP10M <= {apply["top10m"]} THEN -50 ElSE ({tmp_llr}) END"""

    tmp_where = ("WHERE IS_RESPONSE IS %s " % ("FALSE" if apply["windowing"] == "req" else "TRUE")) if apply["windowing"] != "both" else ""

    query = f"""
        SELECT
            COUNT(*) as wcount,
            SUM({tmp_llr}) AS wvalue,
            FLOOR(M.FN_REQ / {wsize}) AS wnum
        FROM MESSAGES_{pcap_id} AS M
            LEFT JOIN 
            (SELECT DN.ID, DN.DN, DN.TOP10M, DN_NN.LOGIT FROM DN LEFT JOIN DN_NN ON (DN.ID = DN_NN.DN_ID AND NN_ID = {apply['nn_id']}))
                AS DNN ON (M.DN_ID = DNN.ID)
        {tmp_where}
        GROUP BY wnum 
        ORDER BY wnum"""
    
    return query


def get_nx_query(pcap_id, wsize):
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
    return query




def run(apply):

    summer = utils.apply_qr_count(db, apply['id'])

    if summer['wsum'] == summer['psum']:
        print("Apply#%d already done." % apply['id'])
        return

    wsize = apply['wsize']
    wtype = apply['wtype']

    pd.options.display.float_format = '{:.2f}'.format

    pcaps = pd.read_sql(
        f"""SELECT * FROM PCAP ORDER BY qr """,
        db,
    )

    cur = db.cursor()
    for pcap_id in pcaps["id"].values.tolist():

        if wtype == 'llr':
            query = get_llr_query(pcap_id, wsize)
        elif wtype == 'nx':
            query = get_nx_query(pcap_id, wsize)
        else:
            raise Exception(f'Wrong WTYPE {{{wtype}}}')


        df_windows = pd.read_sql(query, db)

        df_windows['pcap_id'] = pcap_id
        df_windows['apply_id'] = apply['id']

        execute_values(
            
            cur,
            """INSERT INTO public.windows(apply_id, pcap_id, wnum, wcount, wvalue)
                VALUES  %s;""",
            df_windows[['apply_id', 'pcap_id', 'wnum', 'wcount', 'wvalue']].values.tolist()
        )
        db.commit()
    pass #end batch



if __name__ == "__main__":

    max_top10m = utils.max_top10m(db)

    parser = argparse.ArgumentParser(description='Apply LLR window function.')
    parser.add_argument('--model', metavar="MODEL", type=str, required=True,
                        help='The model name.')
    parser.add_argument('--wtype',
                        default='llr',
                        type=str,
                        choices=[ 'llr', 'nx' ],
                        required=True,
                        help=f'Windowing type: nx or llr.')
    parser.add_argument('--top10m', required=False,
                        type=int,
                        help=f'If a DN has a top10m rank lower than \'value\' then it will be zeroed. Between 0 and {max_top10m}')
    parser.add_argument('--wsize', required=False,
                        default=500,
                        type=int,
                        choices=[ 100, 500, 2500 ],
                        help=f'Windows size.')
    parser.add_argument('--windowing', required=False,
                        default="req",
                        choices=[ "both", "req", "res" ],
                        help=f'How windows are defined.')
    parser.add_argument('--positive-inf', required=False,
                        default=100,
                        type=int,
                        help=f'Replace value for positive infinite.')
    parser.add_argument('--negative-inf', required=False,
                        default=-100,
                        type=int,
                        help=f'Replace value for negative infinite.')
    parser.add_argument('--inf', required=False,
                        default=None,
                        type=int,
                        help=f'Replace absolute value for both infinite.')
    parser.add_argument('--redo', help='If present the program will overwrite previous applies.', action=argparse.BooleanOptionalAction)
    parser.add_argument('name', metavar="NAME", help='The name of this LLR window function.')
    args = parser.parse_args()

    if args.inf is not None:
        pinf = args.inf
        ninf = -args.inf
    else:
        pinf = args.positive_inf
        ninf = args.negative_inf

    model = utils.get_model(db, args.model)
    if model is None:
        print(f"Model [{args.model}] doesn't exists")
        exit(1)
    
    ###
    dn_number = utils.get_dn_number(db)
    inferenced_number = utils.get_inferenced_number(db, model['id'])
    if utils.get_dn_number(db) != utils.get_inferenced_number(db, model['id']):
        print(f"Mismatch between infereced and DN number: should be {dn_number} while it is {inferenced_number}")
        exit(1)
    ###

    apply = dict(name=args.name, wsize=args.wsize, wtype=args.wtype, nn_id=model["id"], top10m=args.top10m, windowing=args.windowing, pinf=pinf, ninf=ninf)

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
                    message=f"{num_applied_windows} on {num_toapply_windows} already applied with '{apply['name']} [{apply['id']}' and wsize {args.wsize}, overwrite?",
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
