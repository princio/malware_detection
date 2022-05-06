from itsdangerous import json
from function_f import function_f
from function_l import function_l
from function_p import function_p
from function_s import function_s
import pickle
from utils import ApplyConfiguration

import os, json
from pathlib import Path
import pandas as pd

import numpy as np


def tonumpy():
    with open('/tmp/csv.npy', 'w') as f:
        import numpy as np
        df_f.to_numpy().astype(np.int32).tofile(f)
    
    with open('/tmp/csv.npy', 'r') as f:
        npy_df = np.fromfile(f, dtype=np.single)
        col = int(npy_df.shape[0] / 5)

        df_f2 = pd.DataFrame(npy_df.reshape(col, 5), columns=['wlen', 'wvalue', 'wnum', 'dga', 'pcap_id'])
    pass

def gen_configs():
    models = [ 7, 8, 9, 10 ]

    wtypes = [ 'llr' ]

    top10ms = [ (0, 0), (1000, -50), (100_000, -50), (1_000_000, -50), (1_000_000, -10) ]

    wsizes = [ 2500, 500, 100 ]

    windowings = [ 'req', 'res', 'both' ]

    infs = [ ( -20, 20 ), ( -20, 200 ), ( -200, 20 ) ]

    outdir = Path('./perform_many/')

    outdir.mkdir(exist_ok=True)

    configs = []
    for model_id in models:
        for wtype in wtypes:
            for top10m in top10ms:
                for wsize in wsizes:
                    for windowing in windowings:
                        for inf in infs:
                            config = ApplyConfiguration(
                                '',
                                model_id,
                                wtype,
                                top10m,
                                wsize,
                                windowing,
                                inf
                            )
                            configs.append(config)
                            pass
    def logit(x):
        return np.log(x/(1-x))

    nx_values = [
        (0, 1),
        ( logit(0.001), logit(0.9) ),
        ( logit(0.001), logit(0.999) ),
        ( logit(0.001), logit(0.999999) ),
    ]

    for top10m in top10ms:
        for wsize in wsizes:
            for windowing in windowings:
                for nxv in nx_values:
                    config = ApplyConfiguration(
                        '',
                        'nx',
                        'nx',
                        top10m,
                        wsize,
                        windowing,
                        nxv
                    )
                    configs.append(config)
                    pass

    return configs

if __name__ == "__main__":

    nth = 200

    th2s = [ 0.25, 0.5, 0.75 ]
    
    configs = gen_configs()

    configs_done = []
    for i, config in enumerate(configs):
        _path_csv = f'./functions_output/f/{config.__hash__()}.csv'
        _path_pkl = f'./functions_output/f2/{config.__hash__()}.pickle'
        if not os.path.exists(_path_csv):
            print(i, 'function f and l')
            print(config)
            df_f = function_f(config)
            df_f.to_csv(_path_csv)
            
            cms_ths = function_l(df_f, nth)
            with open(_path_pkl, 'wb') as f:
                pickle.dump(cms_ths, f)
            
        elif True: #not os.path.exists(_path_pkl):
            print(i, 'function l')
            df_f = pd.read_csv(_path_csv)
            df_f['dga'] = df_f['dga'].where(df_f['dga'] != 2, 1)
            cms_ths = function_l(df_f, nth)
            with open(_path_pkl, 'wb') as f:
                pickle.dump(cms_ths, f)

        # metricss.append(function_p(cms_ths, th2s))
        
        configs_done.append(config)

        pass
    
    with open('functions_output/configs.json', 'w') as f:
        dj = {}

        dj['nth'] = nth
        dj['th2s'] = th2s

        dj['configs'] = { c.__hash__(): c.__dict__ for c in configs }

        json.dump(dj, f)
    
    # compare = function_s(configs, metricss, [ 0 ], [ 'tn2+tp2', 0.75 ], 'top10m')

    pass