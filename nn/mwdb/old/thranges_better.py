import math
from pathlib import Path

from matplotlib.pyplot import fill
from apply_2 import perform
import utils
import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import sys


eng = create_engine("postgresql://postgres:postgres@localhost/dns",)
db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")

with db.cursor() as cur:
    cur.execute("""SELECT * FROM public.nns ORDER BY id ASC LIMIT 100""")
    nns = cur.fetchall()
    model_id2name = { nn[0]: nn[1] for nn in nns }

df = pd.read_csv('thranges/above_200.csv', index_col=0)

cols = [ col.replace("'", '').replace('(', '').replace(')', '').replace(' ', '').replace('tn,tp', 'tn|tp').split(',') for col in df.columns ]

df.columns = pd.MultiIndex.from_tuples(cols)

# defcol=which metric we want to inspect
defcol = ('config', sys.argv[1])

config = [ col for col in df.columns if col[0] == 'config' and col[1] != defcol[1] ]

# config += [ defcol ]
df  = df.sort_values(by=config + [defcol])
df  = df.set_index(config)


cols = [
    (sys.argv[2], 'tn2+tp2'),
    (sys.argv[2], '0.75')
]

stats = []
for i in df.index.drop_duplicates():
    stat = {}
    for col in cols:
        _df_ = df.loc[i].sort_values(col, ascending=False)
        stat[( col, 'mean' )] = _df_[col].mean()
        stat[( col, 'std' )] = _df_[col].std()
        stat[( col, 'best' )] = _df_[defcol].iloc[0]
        # print(_df_)
        pass
    stats.append(stat)
    pass

df_s = pd.DataFrame(stats)

df_s.columns = pd.MultiIndex.from_tuples(df_s.columns)

df_s = df_s.round(3)

dbts = []
for col in cols:
    print(col)

    dbt = {}

    dbt[('mean', 'mean')] = df_s[(col, 'mean')].mean()
    dbt[('mean', 'max')] = df_s[(col, 'mean')].max()
    dbt[('mean', 'min')] = df_s[(col, 'mean')].min()

    dbt[('std', 'mean')] = df_s[(col, 'std')].mean()
    dbt[('std', 'max')] = df_s[(col, 'std')].max()
    dbt[('std', 'min')] = df_s[(col, 'std')].min()

    dbt[('std', '%min')] = (100 * (df_s[(col, 'std')] / df_s[(col, 'mean')]).min())
    dbt[('std', '%max')] = (100 * (df_s[(col, 'std')] / df_s[(col, 'mean')]).max())
    dbt[('std', '%mean')] = (100 * (df_s[(col, 'std')] / df_s[(col, 'mean')]).mean())

    dbt[('best', '1')] = ', '.join([ f'{k[0]}' for i, k in enumerate(df_s[(col, 'best')].value_counts().iteritems()) ])

    dbts.append(dbt)

    pass

dff = pd.DataFrame(dbts, index=cols)

dff.columns = pd.MultiIndex.from_tuples(dff)

print(dff)

    # for k in s.value_counts().iteritems():
    #     print('\t\t%5s' % k[0], k[1])

    # for stat in [ 'mean', 'std', 'best' ]:
    #     s = df_s[(col, stat)]
    #     if stat != 'best':
    #         dbt[(stat, 'mean')] = df_s[(col, 'mean')].mean()
    #         dbt[(stat, 'max')] = df_s[(col, 'mean')].max()
    #         dbt[(stat, 'min')] = df_s[(col, 'mean')].min()
    #         if stat == 'mean':
    #             dbt[(stat, 'mean')] = df_s[(col, 'mean')].mean()
    #             dbt[(stat, 'max')] = df_s[(col, 'mean')].max()
    #             dbt[(stat, 'min')] = df_s[(col, 'mean')].min()
    #             print('\t', stat, '\t', 'mean: %.2f' % df_s[(col, 'mean')].mean())
    #             print('\t\t', ' min: %.2f' % ((df_s[(col, 'mean')].min())))
    #             print('\t\t', ' max: %.2f' % ((df_s[(col, 'mean')].max())))
    #         elif stat == 'std':
    #             print('\t', stat)
    #             print('\t\t', 'mean: %.2f' % (100 * (df_s[(col, 'std')]).mean()))
    #             print('\t\t', ' std: %.2f' % (100 * (df_s[(col, 'std')]).std()))
    #             print('\t\t', '(std/mean)%:')
    #             print('\t\t\t', 'min:  %.2f%%' % (100 * (df_s[(col, 'std')] / df_s[(col, 'mean')]).min()))
    #             print('\t\t\t', 'max:  %.2f%%' % (100 * (df_s[(col, 'std')] / df_s[(col, 'mean')]).max()))
    #             print('\t\t\t', 'mean: %.2f%%' % (100 * (df_s[(col, 'std')] / df_s[(col, 'mean')]).mean()))
    #     else:
    #         print('\t', '%5s' % stat)
    #         for k in s.value_counts().iteritems():
    #             print('\t\t%5s' % k[0], k[1])
    #     # print(df_s.sort_values(by=(col, stat), ascending=False).head())

df_s.to_csv('thranges/above_200_1.csv')

# a parita' di tutto il resto, qual'e' che si comporta meglio?
# order by "config meno col"