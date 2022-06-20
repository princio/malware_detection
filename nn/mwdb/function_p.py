from distutils.command.config import config
import pickle
import json
from re import DEBUG
import sys
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
import numpy as np
import matplotlib.pyplot as plt
import utils
from utils import TN, TP, FN, FP
from matplotlib import colors

eng = create_engine("postgresql://postgres:postgres@localhost/dns",)
db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")

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

def get_cms_relative(cms):
    """
    Return NTH confusion matrix in that format:
    [ TN, FP, [ FN0, FN1, FN2 ], [ TP0, TP1, TP2 ] ]
    """
    n = cms[0][TN] + cms[0][FP]
    p = {
        dga: cms[0][FN][dga] + cms[0][TP][dga]
        for dga in utils.DGAS0
    }

    df_cms = pd.DataFrame()

    df_cms[('N', 'tn')] = np.asarray([ cm[0] for cm in cms ])
    df_cms[('N', 'fp')] = np.asarray([ cm[1] for cm in cms ])

    for dga in utils.DGAS0:
        df_cms[( dga, 'fn' )] = np.asarray([ cm[2][dga] for cm in cms ])
        df_cms[( dga, 'tp' )] = np.asarray([ cm[3][dga] for cm in cms ])

    # cms = [
    #     np.asarray([ cm[0] for cm in cms ]),
    #     np.asarray([ cm[1] for cm in cms ]),
    #     [ np.asarray([ cm[2][dga] for cm in cms ]) for dga in utils.DGAS0 ],
    #     [ np.asarray([ cm[3][dga] for cm in cms ]) for dga in utils.DGAS0 ]
    # ]

    cms_relative = [
        np.asarray([ cm[0] for cm in cms ]),
        np.asarray([ cm[1] for cm in cms ]),
        { dga: np.asarray([ cm[2][dga] for cm in cms ]) for dga in utils.DGAS0 },
        { dga: np.asarray([ cm[3][dga] for cm in cms ]) for dga in utils.DGAS0 }
    ]

    cms_relative = [
        cms_relative[TN] / n,
        cms_relative[FP] / n,
        { dga: cms_relative[FN][dga] / p[dga] for dga in utils.DGAS0 },
        { dga: cms_relative[TP][dga] / p[dga] for dga in utils.DGAS0 },
    ]

    return cms_relative


def function_p(cms, ths, plot=False) -> dict:
    """
    Input:
        - cms: an nth array of confusion matrixs.
        - th2s: an array thresholds indicating the minimum value that tn and tp should have.
    
    Output:
        - metrics: a dictionary of metrics.

    Given an array of confusion matrixs, it calculates the following metrics:
        - for each dga:
            - tn2+tp2:  the maxinum value of sqrt(tn^2 + tp^2)
            - tn,tp:    the maxinum value of tn,tp
            - for each th2 in th2s:
                - the maxinum domain portion of contiguos th where (tn > th2 and tp > th2)
    
    Returns an array of metrics:
        [ ]
    """

    cms_relative = get_cms_relative(cms)

    if plot:
        fig, axs = plt.subplots(len(utils.DGAS0), figsize=(5, 10), sharex=True)
        plt.tight_layout()
        fig.subplots_adjust(hspace=0.05)

    metrics = {}

    nth = len(cms_relative[TN])
    for dga in utils.DGAS0:
        metrics[dga] = {}

        step = ths[1] - ths[0]
        aree = []

        tns = cms_relative[TN]
        tps = cms_relative[TP][dga]

        y = [ tns[i] if (tns[i] < tps[i]) else tps[i] for i in range(nth) ]
        y05 = [ y[i] if (y[i] >= 0.5) else 0.5 for i in range(nth) ]
        
        area_sottesa = sum([ y[i] * step for i in range(nth) ])
        area_sottesa05 = sum([ (y05[i] - 0.5) * step for i in range(nth) ])
        area_totale  = ths[-1] - ths[0]

        tn_above = cms_relative[TN] >= 0.5
        tp_above = cms_relative[TP][dga] >= 0.5

        tntpmax = np.argmax(cms_relative[TN] + cms_relative[TP][dga])
        
        s = pd.Series(tn_above & tp_above) # select the longest group of consecutive wvalues greaters then th2
        s = s.cumsum()-s.cumsum().where(~s).ffill().fillna(0).astype(int)

        metrics[dga][0.5] = s.max() / s.shape[0]
        
        metrics[dga]['int'] = area_sottesa / area_totale
        metrics[dga]['int05'] = area_sottesa05 / area_totale

        if plot:
            from matplotlib import colors
            axs[dga].set_ylabel('$\omega=%d$' % (dga))
            axs[dga].plot(ths, cms_relative[TN], color="CornflowerBlue", label='tn')
            axs[dga].plot(ths, cms_relative[TP][dga], color="OrangeRed", label='tp')
            # axs[dga].plot(ths, y, color="green", linestyle="--")
            # axs[dga].fill_between(ths, y, np.zeros(len(y)), interpolate=True, color=colors.to_rgba("LightBlue", 0.75))

            _ths = [ ths[i] for i in range(nth) if y05[i] != 0.5 ]
            _d = [ 0.5 for i in range(nth) if y05[i] != 0.5 ]
            y05 = [ y05[i] for i in range(nth) if y05[i] != 0.5 ]
            # axs[dga].fill_between(_ths, y05, _d, interpolate=True, color=colors.to_rgba("Red", 0.25))

            axs[dga].annotate('$m_i=%0.2f$' % (area_sottesa / area_totale), xy=(ths[tntpmax], 0.4), xytext=(ths[tntpmax], 0.4))
            # axs[dga].annotate('$m^{>}_i=%0.2f$' % (area_sottesa05 / area_totale), xy=(ths[tntpmax], 0.55), xytext=(ths[tntpmax], 0.55))

    if plot:
        axs[0].legend()
        return fig

    return metrics



def function_p_figs(cms, ths) -> dict:

    cms_relative = get_cms_relative(cms)

    

    metrics = {}

    figs = []

    nth = len(cms_relative[TN])
    for dga in utils.DGAS0:
        fig = plt.figure(figsize=(5, 10))
        fig.tight_layout()

        metrics[dga] = {}

        step = ths[1] - ths[0]
        aree = []

        tns = cms_relative[TN]
        tps = cms_relative[TP][dga]

        y = [ tns[i] if (tns[i] < tps[i]) else tps[i] for i in range(nth) ]
        y05 = [ y[i] if (y[i] >= 0.5) else 0.5 for i in range(nth) ]
        
        area_sottesa = sum([ y[i] * step for i in range(nth) ])
        area_sottesa05 = sum([ (y05[i] - 0.5) * step for i in range(nth) ])
        area_totale  = ths[-1] - ths[0]

        tn_above = cms_relative[TN] >= 0.5
        tp_above = cms_relative[TP][dga] >= 0.5

        tntpmax = np.argmax(cms_relative[TN] + cms_relative[TP][dga])
        
        s = pd.Series(tn_above & tp_above) # select the longest group of consecutive wvalues greaters then th2
        s = s.cumsum()-s.cumsum().where(~s).ffill().fillna(0).astype(int)

        metrics[dga][0.5] = s.max() / s.shape[0]
        
        metrics[dga]['int'] = area_sottesa / area_totale
        metrics[dga]['int05'] = area_sottesa05 / area_totale

        plt.plot(ths, cms_relative[TN], color="CornflowerBlue", label='tn')
        plt.plot(ths, cms_relative[TP][dga], color="OrangeRed", label='tp')
        plt.ylabel('$\omega=%d$' % (dga))
        # plt.plot(ths, y, color="green", linestyle="--")
        plt.fill_between(ths, y, np.zeros(len(y)), interpolate=True, color=colors.to_rgba("LightBlue", 0.75))

        _ths = [ ths[i] for i in range(nth) if y05[i] != 0.5 ]
        _d = [ 0.5 for i in range(nth) if y05[i] != 0.5 ]
        y05 = [ y05[i] for i in range(nth) if y05[i] != 0.5 ]

        # plt.annotate('$m_i=%0.2f$' % (area_sottesa / area_totale), xy=(ths[tntpmax], 0.4), xytext=(ths[tntpmax], 0.4))

        figs.append(fig)

    return figs

def annot(df, th2s, nth, tp, thmin, thmax, ax):
    for th2 in th2s:

        s = (df['tn'] > th2) & (df[tp] > th2)

        c = 0
        start = 0
        maxg = 0
        group = []
        for i, a in s.iteritems():
            if c == 0 and a != 0:
                start = i
            if c != 0 and a == 0:
                if maxg < c:
                    group = [ start, i ]
                c = 0
            c = a + c

        if group != []:
            th_start = df.th[group[0] - 1 if group[0] > 0 else group[0]]
            th_end = df.th[group[1] + 1 if group[1] > nth else group[1]]


            ax.annotate('', xy=(th_start, th2), xytext=(th_end, th2), arrowprops=dict(arrowstyle='<->', linewidth=0.5))
            ax.annotate(f'$th_2={th2:.2f}$', xy=(-36000, th2), horizontalalignment='center', verticalalignment='top')
            ax.annotate('%0.2f' % ((th_end - th_start)/(thmax-thmin)), xy=(th_start + (th_end - th_start) / 2, th2 - 0.07), fontsize=8, horizontalalignment='center', verticalalignment='center')

        pass

def plot_(cms_ths, ths):

    df = pd.DataFrame()
    df['th'] = ths
    df['tn'] = [ cm[TN] for cm in cms_ths ]
    df['tn'] = df['tn'] / (cms_ths[0][TN] +  cms_ths[0][FP])

    for dga in [ 0,1,2,3 ]:
        df['tp_%d' % dga] = [ cm[TP][dga] for cm in cms_ths ]
        df['tp_%d' % dga] = df['tp_%d' % dga] / (cms_ths[0][TP][dga] +  cms_ths[0][FN][dga])
        df['tn*tp_%d' % dga] = df.tn * df['tp_%d' % dga]

    fig, axs = plt.subplots(4)
    for dga in [ 0,1,2,3 ]:
        df.plot(x='th', y=['tn', 'tp_%d' % dga], ax=axs[dga])
        df.plot(x='th', y=['tn*tp_%d' % dga], style='.', ax=axs[dga])
        annot(df, th2s, configs['nth'], 'tp_%d' % dga, df.th.min(), df.th.max(), axs[dga])

    plt.show()

    pass

if __name__ == "__main__":

    with open('functions_output/configs.json', 'r') as fp:
        configs = json.load(fp)


    for config_hash in configs['configs']:
        if config_hash in [ 'th2s', 'nth' ]: continue

        df_f, cms_ths, ths = load(config_hash)

        metrics = function_p(cms_ths, ths, plot=True)

        # for dga in utils.DGAS0:
        #     plot_(cms_ths, ths)
        #     if metrics[dga][0.50] > metrics[dga][0.25]:
        #         print(dga, '0.50 > 0.25', metrics[dga][0.50], metrics[dga][0.25])
        #     if metrics[dga][0.75] > metrics[dga][0.50]:
        #         print(dga, '0.75 > 0.50', metrics[dga][0.50], metrics[dga][0.75])
        #     if metrics[dga][0.75] > metrics[dga][0.25]:
        #         print(dga, '0.75 > 0.25', metrics[dga][0.75], metrics[dga][0.25])
        #     pass
        pass

    hashes = list(configs.keys())

    config_hash = hashes[int(sys.argv[1])]
    