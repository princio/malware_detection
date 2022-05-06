from re import DEBUG
import psycopg2
import pandas as pd
import utils
from sqlalchemy import create_engine
import os

eng = create_engine("postgresql://postgres:postgres@localhost/dns",)
db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")



pd.options.display.float_format = '{:.2f}'.format

pcaps = pd.read_sql(
    f"""SELECT PCAP.ID, MALWARE.DGA FROM PCAP JOIN MALWARE ON PCAP.MALWARE_ID=MALWARE.ID ORDER BY qr""" + (' LIMIT 5' if os.environ.get('DEBUG') else ''),
    eng,
)

malwares = pd.read_sql(
    f"""SELECT * FROM MALWARE WHERE DGA > 0""",
    eng,
)

vs = []
dfs = []
descs = []
i=0
for _, malware in malwares.iterrows():

    pcaps_mw = pd.read_sql(
        f"""SELECT PCAP.ID FROM PCAP JOIN MALWARE ON PCAP.MALWARE_ID=MALWARE.ID WHERE MALWARE.ID = {malware['id']} ORDER BY qr""",
        eng,
    )


for _, malware in malwares.iterrows():

    pcaps_mw = pd.read_sql(
        f"""SELECT PCAP.ID FROM PCAP JOIN MALWARE ON PCAP.MALWARE_ID=MALWARE.ID WHERE MALWARE.ID = {malware['id']} ORDER BY qr""",
        eng,
    )

    messages = []
    for _, pcap in pcaps_mw.iterrows():
        messages += [
            pd.read_sql(f"SELECT DN_ID, TOP10M, IS_RESPONSE, RCODE FROM MESSAGES_{pcap['id']} JOIN DN2 AS D ON DN_ID=D.ID", eng)
        ]

    messages = pd.concat(messages)

    messages['ok'] = messages['rcode'] == 0
    messages['nx'] = messages['rcode'] == 3

    responses = messages[messages.is_response]

    nt10 = responses[responses.top10m.isna()]

    apps_tot = nt10.shape[0]

    # il numero di media(nx domain / app domain) dove domain e' un domain unico fuori da top10m avente almeno un nx domain

    nt10 = nt10[['dn_id', 'ok', 'nx']].groupby('dn_id').agg({
        'ok': 'sum',
        'nx': 'sum'
    })

    nt10['apps'] = nt10.ok + nt10.nx

    # nt10 = nt10[nt10.nx > 0]

    vapps = (nt10.apps).mean()
    vapps_std = (nt10.apps).std()
    vok = (nt10.ok / nt10.apps).mean()
    vnx = (nt10.nx / nt10.apps).mean()

    vs.append([ malware['id'], malware['dga'], vapps, vapps_std, vok, vnx, nt10.shape[0], apps_tot ])
    
    # if i == 10: break
    # i+=1

    pass

print(pd.DataFrame(vs, columns=[ "mwid", "vdga", "mean(apps)", "std(apps)", "ok", "nx", "uniques", "apps" ]).round(3).to_markdown())

"""

dga	apps	ok	nx	uniques	mwid
1	2.74	0.97	0.03	457	20
1	7922.12	0.52	0.48	268	24
1	22721.93	0.93	0.07	14	27
1	23.86	0.96	0.04	720	2
1	2.89	0.99	0.01	522	22
1	8.72	0.96	0.04	29914	5
2	165.51	1	0	4873	1
2	336.87	0.98	0.02	103	17
2	47.89	0.72	0.28	4180	6
2	2.41	0.96	0.04	3640	19
3	120.39	0.01	0.99	2952	10
3	209.96	0.02	0.98	1001	23
3	3.99	0.06	0.94	2013	9
3	148.07	0.24	0.76	96	12
3	608.8	0	1	1001	14
3	1.03	0	1	2649	3
3	3028.85	0.3	0.7	1120	15
3	98.98	0.07	0.93	3861	8
3	38.47	0.58	0.42	6296	4
3	5.46	0.01	0.99	5581	7

"""