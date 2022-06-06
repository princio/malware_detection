from re import DEBUG
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import pprint
import argparse
import utils
import inquirer
from sqlalchemy import create_engine
import os

eng = create_engine("postgresql://postgres:postgres@localhost/dns",)
db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")


def get_llr_query(pcap_id, apply_config: utils.ApplyConfiguration):
    tmp_llr = f"""
            CASE WHEN LOGIT IS NULL THEN 0 ELSE 
                (CASE WHEN LOGIT = 'Infinity' THEN {apply_config.inf[1]} ElSE
                    (CASE WHEN LOGIT='-Infinity' THEN {apply_config.inf[0]} ELSE LOGIT END)
                END)
            END"""
        
    if not(apply_config.top10m is None):
        tmp_llr = f"""CASE WHEN TOP10M <= {apply_config.top10m[0]} THEN {apply_config.top10m[1]} ElSE ({tmp_llr}) END"""

    tmp_where = ("WHERE IS_RESPONSE IS %s " % ("FALSE" if apply_config.windowing == "req" else "TRUE")) if apply_config.windowing != "both" else ""

    # warning: changing wcount to wlen
    query = f"""
        SELECT
            COUNT(*) as wlen,
            SUM({tmp_llr}) AS wvalue,
            FLOOR(M.FN_REQ / {apply_config.wsize}) AS wnum
        FROM MESSAGES_{pcap_id} AS M
            LEFT JOIN 
            (SELECT DN.ID, DN.DN, DN.TOP10M, DN2_NN.LOGIT FROM DN LEFT JOIN DN2_NN ON (DN.ID = DN2_NN.DN_ID AND NN_ID = {apply_config.model_id}))
                AS DNN ON (M.DN_ID = DNN.ID)
        {tmp_where}
        GROUP BY wnum 
        ORDER BY wnum
    """
    
    return query


def get_nx_query(pcap_id, apply_config: utils.ApplyConfiguration):
    query = f"""
        SELECT
            COUNT(*) as wcount,
            SUM(CASE WHEN RCODE=3 THEN 1 ELSE 0 END) AS wvalue,
            FLOOR(M.FN_REQ / {apply_config.wsize}) AS wnum
        FROM MESSAGES_{pcap_id} AS M
            LEFT JOIN 
            (SELECT DN.ID, DN.DN, DN2_NN.LOGIT FROM DN LEFT JOIN DN2_NN ON (DN.ID = DN2_NN.DN_ID AND NN_ID = 1))
                AS DNN ON (M.DN_ID = DNN.ID)
        GROUP BY wnum 
        ORDER BY wnum
    """
    
    return query




def run(apply_id: int, apply_config: utils.ApplyConfiguration):

    summer = utils.apply_qr_count(db, apply_id)

    if summer['wsum'] == summer['psum']:
        print("Apply#%d already done." % apply_id)
        return

    wtype = apply_config.wtype

    pd.options.display.float_format = '{:.2f}'.format

    pcaps = pd.read_sql(
        f"""SELECT * FROM PCAP ORDER BY qr""",
        eng,
    )

    cur = db.cursor()
    for pcap_id in pcaps["id"].values.tolist():

        if wtype == 'llr':
            query = get_llr_query(pcap_id, apply_config)
        elif wtype == 'nx':
            query = get_nx_query(pcap_id, apply_config)
        else:
            raise Exception(f'Wrong WTYPE {{{wtype}}}')


        df_windows = pd.read_sql(query, db)

        df_windows['pcap_id'] = pcap_id
        df_windows['apply_id'] = apply_id

        execute_values(
            cur,
            """INSERT INTO public.windows(apply_id, pcap_id, wnum, wcount, wvalue)
                VALUES  %s;""",
            df_windows[['apply_id', 'pcap_id', 'wnum', 'wcount', 'wvalue']].values.tolist()
        )
        db.commit()
    pass #end batch

###
### wlen: number of packets (req or res) included in the window
### wvalue: LLR value or NX value
### wnum: sequencial number of the window
### dga: vdga value of the window inheritde from the pcap
def perform(apply_config: utils.ApplyConfiguration):

    pd.options.display.float_format = '{:.2f}'.format

    pcaps = pd.read_sql(
        f"""SELECT PCAP.ID, MALWARE.DGA FROM PCAP JOIN MALWARE ON PCAP.MALWARE_ID=MALWARE.ID ORDER BY qr""" + (' LIMIT 5' if os.environ.get('DEBUG') else ''),
        eng,
    )

    dfs = []
    for _, pcap in pcaps.iterrows():

        pcap_id = pcap['id']

        if apply_config.wtype == 'llr':
            query = get_llr_query(pcap_id, apply_config)
        elif apply_config.wtype == 'nx':
            query = get_nx_query(pcap_id, apply_config)
        else:
            raise Exception(f'Wrong WTYPE {{{apply_config.wtype}}}')

        df = pd.read_sql(query, eng)
        df['dga'] = pcap['dga']
        df['pcap_id'] = pcap['id']
        dfs.append(df)
        
        pass
    
    return pd.concat(dfs, axis=0).sort_values(by='wvalue')


def perform_rounded(apply_config: utils.ApplyConfiguration, rounder=10):

    pd.options.display.float_format = '{:.2f}'.format

    pcaps = pd.read_sql(
        f"""SELECT * FROM PCAP ORDER BY qr""",
        eng,
    )

    dfs = []
    for pcap_id in pcaps["id"].values.tolist():

        if apply_config.wtype == 'llr':
            query = get_llr_query(pcap_id, apply_config)
        elif apply_config.wtype == 'nx':
            query = get_nx_query(pcap_id, apply_config)
        else:
            raise Exception(f'Wrong WTYPE {{{apply_config.wtype}}}')

        df = pd.read_sql(query, eng)
        dfs.append(df)
        
        pass
    
    return pd.concat(dfs, axis=0)

if __name__ == "__main__":

    max_top10m = utils.max_top10m(db)

    parser = argparse.ArgumentParser(description='Apply LLR window function.')
    parser.add_argument('--model', metavar="MODEL", type=str, required=True,
                        help='The model name.')
    parser.add_argument('--save',
                        required=False,
                        type=bool,
                        default=False)
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
    dn_number = utils.get_dn2_number(db)
    inferenced_number = utils.get_inferenced_number2(db, model['id'])
    if dn_number != inferenced_number:
        print(f"Mismatch between infereced and DN number: should be {dn_number} while it is {inferenced_number}")
        exit(1)
    ###

    apply_config = utils.ApplyConfiguration(
        args.name,
        model['id'],
        args.wtype,
        args.top10m,
        args.wsize,
        args.windowing,
        pinf,
        ninf
    )
    
    if not args.save:
        df = perform(apply_config)
        print(df)
        exit(0)

    ###
    apply_id = utils.get_apply(db, apply_config)
    
    if apply_id is None:
        yn = utils.get_yn(f"Function not exists, create it? [Y/n]\n{apply_config}")
        if yn == 'y':
            apply_id = utils.create_apply(db, apply_config)
        else:
            exit(0)
    ###

    ###
    if args.redo == False or args.redo is None:
        num_applied_windows = utils.count_applied_windows(db, apply_id)
        num_toapply_windows = utils.count_toapply_windows(db, apply_config.wsize)

        if num_applied_windows > 0:
            questions = [
            inquirer.List('overwrite',
                    message=f"{num_applied_windows} on {num_toapply_windows} already applied with '{apply_config.name} [{apply_id}' and wsize {apply_config.wsize}, overwrite?",
                    choices=[ 'Cancel', 'Re-do', 'Fill' ],
                ),
            ]
            answers = inquirer.prompt(questions)
            if answers['overwrite'] == 'Re-do':
                with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("DELETE FROM windows WHERE apply_id=%s", [ apply_id ])
                    print("Deleted previous apply.")
            elif answers['overwrite'] == 'Cancel':
                print('Exiting')
                exit(1)
    ###

    run(apply_id, apply_config)
    
    pass
