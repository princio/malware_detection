from re import DEBUG
import psycopg2
import pandas as pd
import utils
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
            COUNT(*) as wlen,
            SUM(CASE WHEN RCODE=3 THEN {apply_config.inf[1]} ELSE {apply_config.inf[0]} END) AS wvalue,
            FLOOR(M.FN_REQ / {apply_config.wsize}) AS wnum
        FROM MESSAGES_{pcap_id} AS M
            LEFT JOIN 
            (SELECT DN.ID, DN.DN, DN2_NN.LOGIT FROM DN LEFT JOIN DN2_NN ON (DN.ID = DN2_NN.DN_ID AND NN_ID = 1))
                AS DNN ON (M.DN_ID = DNN.ID)
        GROUP BY wnum 
        ORDER BY wnum
    """

    return query



def function_f(apply_config: utils.ApplyConfiguration) -> pd.DataFrame:
    """
    Input:
        - apply_config: an ApplyConfiguration object.
    
    Output:
        - df_f: an F-Dataframe
    
    Given an ApplyConfiguration, it calculates a dataframe with the following columns:
        - wlen: number of packets (req or res) included in the window
        - wvalue: LLR value or NX value
        - wnum: sequencial number of the window
        - dga: vdga value of the window inheritde from the pcap
    
    The dataset is fetched from a database, which calculates most of the columns inside a SQL query.
    """

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
