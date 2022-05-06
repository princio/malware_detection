import math
from pathlib import Path

from matplotlib.pyplot import fill
from apply_2 import perform
import utils
import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import json


eng = create_engine("postgresql://postgres:postgres@localhost/dns",)
db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")

with db.cursor() as cur:
    cur.execute("""SELECT * FROM public.nns ORDER BY id ASC LIMIT 100""")
    nns = cur.fetchall()
    model_id2name = { nn[0]: nn[1] for nn in nns }

def cmss_to_df(cmss):
    df_cmss = pd.DataFrame()

    df_cmss[('N', 'tn')] = np.asarray([ cm[0] for cms in cmss for cm in cms ])
    df_cmss[('N', 'fp')] = np.asarray([ cm[1] for cms in cmss for cm in cms ])

    for dga in utils.DGAS0:
        df_cmss[( dga, 'fn' )] = np.asarray([ cm[2][dga] for cms in cmss for cm in cms ])
        df_cmss[( dga, 'tp' )] = np.asarray([ cm[3][dga] for cms in cmss for cm in cms ])

    df_cmss.columns = pd.MultiIndex.from_tuples(df_cmss.columns.to_list())

    return df_cmss



def cms_to_df(cms):
    df_cms = pd.DataFrame()

    df_cms[('N', 'tn')] = np.asarray([ cm[0] for cm in cms ])
    df_cms[('N', 'fp')] = np.asarray([ cm[1] for cm in cms ])

    for dga in utils.DGAS0:
        df_cms[( dga, 'fn' )] = np.asarray([ cm[2][dga] for cm in cms ])
        df_cms[( dga, 'tp' )] = np.asarray([ cm[3][dga] for cm in cms ])

    df_cms.columns = pd.MultiIndex.from_tuples(df_cms.columns.to_list())

    return df_cms

### CMS:
### [tn, fp, fn, tp ]
### fn,tp = [ all, 1, 2, 3 ]

dgas = utils.DGAS0

thrange = 200

df = pd.read_csv(f'thranges/thranges_{thrange}.csv', index_col=0, header=[0,1])

df[('thrange', 'cms')] = np.asarray(df[('thrange', 'cms')].apply(json.loads))

cmss = df[('thrange', 'cms')].to_numpy().tolist()

df.drop(columns=[('thrange', 'cms')], inplace=True)

th2ranges = [ 0.25, 0.5, 0.75 ]

aboves = []
for _, row in df.iterrows():
    if _ %10 == 0:
        print(_)

    df_cms = cms_to_df(cmss[_])

    ths = np.linspace(row[('wvalue', 'min')], row[('wvalue', 'max')], num=row[('wvalue', 'nth')])

    tmp_cm = df_cms.iloc[0]
    n = tmp_cm[('N', 'tn')] + tmp_cm[('N', 'fp')]
    p = {
        dga: tmp_cm[(dga, 'fn')] + tmp_cm[(dga, 'tp')]
        for dga in dgas
    }

    # print(tmp_cm)

    # print(df_cms[[('N', 'tn')] + [(dga, 'tp') for dga in dgas]].to_markdown())

    df_cms_relative = df_cms.copy()

    for column in df_cms.columns:
        if column[0] == 'N':
            df_cms_relative[column] = df_cms[column] / n
        else:
            df_cms_relative[column] = df_cms[column] / p[column[0]]

    df_cms_relative['th'] = ths
    df_cms_relative = df_cms_relative[[('N', 'tn')] + [(dga, 'tp') for dga in dgas]]

    # print(df_cms_relative.to_markdown())
    
    # thrange:
    # largest portion of th domain whereas (tp > th2 and tn > th2)
    # if I want to use a config that allows me to check the 50% of windows correctly then:
    # - th2 = 50%
    #   - thrange = 2%? Then I have a little portion of the domain whereas the windows are correctly identified
    #   - thrange = 50%? Then I have a wide portion of the domain whereas the windows are correctly identified
    # I can choose one of the th included in thrange and I will get wrong only the (1-th2)% of times.
    # Wider is the thrange than better are identified the windows.
    # Which is the best th?
    # there is always a best th in thrange, near ~(1,1), but can I choose only one th?
    # The thrange shows how many th I can chose within a range with the expected error.
    # But how can I use the a th within thrange?
    # I choose a th having ~(1,1) but the probability that the error is wrong is greater.
    # I can choose a th having (>th2, >th2) with a lower probability of choosing the wrong threshold.

    d_both_above = {}
    for dga in dgas:
        k = (df_cms_relative[('N', 'tn')].pow(2) + df_cms_relative[(dga, 'tp')].pow(2)).pow(1/2)
        
        tn_max = df_cms_relative[('N', 'tn')].iloc[k.idxmax()]
        tp_max = df_cms_relative[(dga, 'tp')].iloc[k.idxmax()]

        d_both_above[(dga, 'tn2+tp2')] = f'{k.max():.2f}'
        d_both_above[(dga, 'tn,tp')] = f'{tn_max:.2f},{tp_max:.2f}'

        for th2 in th2ranges:
            df_th2 = pd.DataFrame({
                'tn': df_cms_relative[('N', 'tn')] >= th2,
                'tp': df_cms_relative[(dga, 'tp')] >= th2
            })
            
            # select the longest group of consecutive wvalues greaters then th2
            s = df_th2['tn'] & df_th2['tp']
            s = s.cumsum()-s.cumsum().where(~s).ffill().fillna(0).astype(int)
            d_both_above[(dga, th2)] = s.max() / s.shape[0]

            pass

        pass
    
    config = row[[ ('config', l) for l in ['model_id','wtype','top10m','wsize','windowing','inf']]].to_dict()
    config[('config', 'model_id')] = model_id2name[config[('config', 'model_id')]]
    aboves.append(config | d_both_above)
    pass

print(pd.DataFrame(aboves))

pd.DataFrame(aboves).to_csv(f'thranges/above_{thrange}.csv')