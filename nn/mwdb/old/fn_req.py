from re import DEBUG
from numpy.lib.arraysetops import unique
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import pprint
import numpy as np

pp = pprint.PrettyPrinter(indent=4)

db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")

pcaps = pd.read_sql("SELECT * FROM PCAP ORDER BY qr", db)

for _, pcap in pcaps.iterrows():
    messages = pd.read_sql(f"SELECT * FROM MESSAGES_{pcap['id']} WHERE FN_REQ IS NULL ORDER BY FN", db)
    if messages.shape[0] == 0: continue

    print(pcap['id'], pcap['qr'])

    c = 0
    isrs = messages['is_response'].values
    fns = np.zeros(messages.shape[0])
    fns[0] = 0
    last_req = -1
    actual_req = 0
    for isr in isrs:
        if not isrs[c]:
            last_req += 1
            fns[c] = last_req
            actual_req = last_req
        else:
            fns[c] = actual_req
        c += 1

    # reqs = messages[~messages['is_response']].copy()

    # reqs['fn_req'] = np.arange(reqs.shape[0])

    # messages = messages.drop(columns='fn_req').join(reqs['fn_req']).fillna(method='ffill')

    messages['fn_req'] = fns

    # if messages['fn_req'].isna().sum() > 0:
    #     print(messages)
    #     print('Fill with zeros?')
    #     if input() == 'y':
    #         messages['fn_req'].fillna(0, inplace=True)

    # print((~(messages['fn_req'] == fns)).sum() == 0)

    with db.cursor() as cur:
        execute_values(
            cur,
            f"""UPDATE MESSAGES_{pcap['id']} AS M SET FN_REQ=E.FN_REQ
            FROM (VALUES %s) AS E(FN_REQ, ID)  WHERE M.ID=E.ID""",
            messages[['fn_req', 'id']].values.tolist()
        )
        db.commit()
