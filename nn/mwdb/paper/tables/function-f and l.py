import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import pickle
import numpy as np
import json
import pandas as pd
from tabulate import tabulate

import os, sys
sys.path.append('../../')

import utils
from utils import ApplyConfiguration, cms_vertical


if __name__ == "__main__":
    with open(os.path.join(utils.ROOT_DIR, 'functions_output/configs.json'), 'r') as fp:
        configs = json.load(fp)

    nth = configs['nth']

    th2s = configs['th2s']

    configs = configs['configs']
    
    configs = [
        ApplyConfiguration.from_dict(configs[hash])
        for hash in configs
    ]

    configs_done = []
    for i, config in enumerate(configs):

        df_f, cms, ths = utils.load(config.__hash__(), nth=200)

        cms = cms_vertical(cms)

        df_l = pd.DataFrame()

        df_l[( '$tn$', None )] = cms[utils.TN]
        df_l[( '$fp$', None )] = cms[utils.FP]
        df_l[( '$fn$', '$\\omega^0$' )] = cms[utils.FN][0]
        df_l[( '$fn$', '$\\omega^1$' )] = cms[utils.FN][1]
        df_l[( '$fn$', '$\\omega^2$' )] = cms[utils.FN][2]
        df_l[( '$tp$', '$\\omega^0$' )] = cms[utils.TP][0]
        df_l[( '$tp$', '$\\omega^1$' )] = cms[utils.TP][1]
        df_l[( '$tp$', '$\\omega^2$' )] = cms[utils.TP][2]

        df_l.columns = pd.MultiIndex.from_tuples(df_l)

        df_l.index = [ round(th) for th in ths ]

        print('Confusion matrix test...', end='')
        if all(df_l[( '$tp$', '$\\omega^0$' )] == (df_l[( '$tp$', '$\\omega^1$' )] + df_l[( '$tp$', '$\\omega^2$' )])):
            print(' passed')
        else:
            print(' error')
            break

        _df_l = df_l.iloc[list(range(3)) + list(range(97, 100)) + list(range(197,200))]

        print(_df_l.to_latex(escape=False))

        n = cms[utils.TN] + cms[utils.FP]
        p0 = cms[utils.FN][0] + cms[utils.TP][0]
        p1 = cms[utils.FN][1] + cms[utils.TP][1]
        p2 = cms[utils.FN][2] + cms[utils.TP][2]

        df_l[( '$tn$', None )] = df_l[( '$tn$', None )] / n
        df_l[( '$fp$', None )] = df_l[( '$fp$', None )] / n
        df_l[( '$fn$', '$\\omega^0$' )] = df_l[( '$fn$', '$\\omega^0$' )] / p0
        df_l[( '$fn$', '$\\omega^1$' )] = df_l[( '$fn$', '$\\omega^1$' )] / p1
        df_l[( '$fn$', '$\\omega^2$' )] = df_l[( '$fn$', '$\\omega^2$' )] / p2
        df_l[( '$tp$', '$\\omega^0$' )] = df_l[( '$tp$', '$\\omega^0$' )] / p0
        df_l[( '$tp$', '$\\omega^1$' )] = df_l[( '$tp$', '$\\omega^1$' )] / p1
        df_l[( '$tp$', '$\\omega^2$' )] = df_l[( '$tp$', '$\\omega^2$' )] / p2

        _df_l = df_l.iloc[list(range(3)) + list(range(97, 100)) + list(range(197,200))]

        print(_df_l.round(2).to_latex(escape=False))

        break