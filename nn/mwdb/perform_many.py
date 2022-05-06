import math
from pathlib import Path
from apply_2 import perform
import utils
import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import json
import psutil
import os

eng = create_engine("postgresql://postgres:postgres@localhost/dns",)
db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")


### FOR DOCUMENTATION:
models = utils.get_models(db)
print('\n'.join([ f'###   {id}={models[id]["name"]}' for id in models ]))

with db.cursor() as cur:
    cur.execute("SELECT max(top10m) FROM public.dn2;")
    top10mmax = cur.fetchone()
print('top10m', top10mmax[0])


with db.cursor() as cur:
    cur.execute("SELECT min(logit) FROM public.dn_nn where logit != '-Infinity'")
    ninf = cur.fetchone()
print('NINF', ninf[0])


with db.cursor() as cur:
    cur.execute("SELECT max(logit) FROM public.dn_nn where logit != 'Infinity'")
    pinf = cur.fetchone()
print('PINF', pinf[0])

###
### MODELS:
###   1=nosfx
###   2=domain
###   3=any
###   4=domain_sfx
###   7=ICANN_1
###   8=NONE_1
###   9=PRIVATE_1
###   10=TLD_1
###
### WTYPE:
###   LLR, NX
###
### WINDOWING:
###   RES, REQ, BOTH
###
### TOP10M:
###   [0, 9999645]
###
### WSIZE:
### 100, 500, 2500
###
### PINF, NINF:
###   PINF > NINF
###   

def get_thrange(min, max, nth):
    nth = 100
    th_max = int(math.ceil(min))
    th_min = int(math.ceil(max))
    thrange = th_max - th_min
    th_step = int(thrange / nth)
    return [ th for th in range(th_min, th_max, th_step) ]


def usage():
    process = psutil.Process(os.getpid())
    return process.memory_info()[0] / float(2 ** 20)

if __name__ == '__main__':

    models = [ 7, 8, 9, 10 ]

    wtypes = [ 'llr' ]

    top10ms = [ (0, 0), (1000, -50), (100_000, -50), (1_000_000, -50), (1_000_000, -10) ]

    wsizes = [ 2500, 500, 100 ]

    windowings = [ 'req', 'res', 'both' ]

    infs = [ ( -20, 20 ), ( -80, 20 ), ( -80, 80 ), ( -200, 200 ) ]

    outdir = Path('./perform_many/')

    outdir.mkdir(exist_ok=True)

    configs = {}
    configs_json = {}
    for model_id in models:
        for wtype in wtypes:
            for top10m in top10ms:
                for wsize in wsizes:
                    for windowing in windowings:
                        for inf in infs:
                            config = utils.ApplyConfiguration(
                                '',
                                model_id,
                                wtype,
                                top10m,
                                wsize,
                                windowing,
                                inf
                            )
                            configs[config.__hash__()] = config
                            configs_json[config.__hash__()] = config.__dict__
                            configs_json[config.__hash__()]['performed'] = False
                            pass
    
    if not outdir.joinpath('configs.json').exists():
        with open(outdir.joinpath('configs.json'), 'w') as fp:
            json.dump(configs_json, fp)

        pass

    with open(outdir.joinpath('configs.json'), 'r') as fp:
        configs_json = json.load(fp)
    
    def set_performed(hash):
        configs_json[hash]['performed'] = True
        with open(outdir.parent.joinpath('configs.json'), 'w') as fp:
            json.dump(configs_json, fp)
        pass


    outdir = outdir.joinpath('csvs')
    outdir.mkdir(exist_ok=True)

    i = 0
    n = len(list(configs_json.keys()))
    for hash in configs:
        i += 1
        config = configs[hash]
        if not configs_json[hash]['performed']:
            df = perform(config)

            df.to_csv(outdir.joinpath(config.__hash__()).with_suffix('.csv'), index=False)
            
            set_performed(hash)

            print(f'{i}/{n}\t{hash}', end='done.\n')
            pass
        pass


    nths = [ 200 ] # 20, 50, 100, 200 ]


    for nth in nths:
        rows = []
        for i, hash in enumerate(configs):
            print(f'Thresholding {i}...')
            if not outdir.joinpath(hash).with_suffix('.csv').exists():
                continue

            config = configs[hash]

            df = pd.read_csv(outdir.joinpath(hash).with_suffix('.csv'), index_col=None)

            thrange = np.linspace(df.wvalue.min(), df.wvalue.max(), num=nth, dtype=np.float32)

            p = {
                dga: sum(df.dga == dga)
                for dga in utils.DGAS
            }
            p[0] = sum(df.dga > 0)

            n = sum(df.dga == 0)

            config.name = i

            row = { ('config', l): config.__dict__[l] for l in config.__dict__ }
            row[('wvalue', 'min')] = df.wvalue.min()
            row[('wvalue', 'max')] = df.wvalue.max()
            row[('wvalue', 'nth')] = nth

            cms = []
            for th in thrange:
                tn = sum((df.dga == 0) & (df.wvalue <= th))
                fp = n - tn

                df_i = df[(df.dga > 0) & (df.wvalue > th)]
                tp = [ df_i.shape[0], 0, 0, 0 ]
                fn = [ p[0] - df_i.shape[0], 0, 0, 0 ]
                for dga in utils.DGAS:
                    tp[dga] = sum(df_i.dga == dga)
                    fn[dga] = p[dga] - tp[dga]
                    pass
                cms.append( [tn, fp, fn, tp ])
                pass

            row[('thrange', 'cms')] = cms

            rows.append(row)

            if i == 0:
                df_config = pd.DataFrame(rows)
                df_config.columns = pd.MultiIndex.from_tuples(df_config.columns)
                df_config.to_csv(f'thranges_{nth}.csv', mode='w', index=None)
                rows = []
            elif len(rows) % 5 == 0:
                df_config = pd.DataFrame(rows)
                df_config.columns = pd.MultiIndex.from_tuples(df_config.columns)
                df_config.to_csv(f'thranges_{nth}.csv', mode='a', header=False, index=None)
                rows = []

            pass

        pass