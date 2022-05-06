import psycopg2
from sqlalchemy import create_engine
import utils

eng = create_engine("postgresql://postgres:postgres@localhost/dns",)
db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")



# input:
#       df:     result of function f
#       th:     the threshold
#       p:      { vDGA: number of windows having vDGA }
#       n:      { vDGA: number of windows having vDGA==0 }
# output:
#       cm:   [ tn, fp, [ fn0, fn1, fn2, fn3 ], [ tp0, tp1, tp2, tp3 ] ]
def function_g(df, th, n=None, p=None):
    if p is None:
        p = { dga: sum(df.dga == dga) for dga in utils.DGAS }
        p[0] = sum(df.dga > 0)

    if n is None:
        n = sum(df.dga == 0)

    tn = sum((df.dga == 0) & (df.wvalue <= th))
    fp = n - tn

    df_tp = df[(df.dga > 0) & (df.wvalue > th)]

    tp = [ 0, 0, 0, 0 ]
    fn = [ 0, 0, 0, 0 ]
    for dga in utils.DGAS0:
        if dga == 0:
            tp[dga] = df_tp.shape[0]
            fn[dga] = p[0] - df_tp.shape[0]
        else:
            tp[dga] = sum(df_tp.dga == dga)
            fn[dga] = p[dga] - tp[dga]
        pass

    return [ tn, fp, fn, tp ]