from tkinter import X
from matplotlib.patches import ArrowStyle
import pickle
import numpy as np
import json, os, inspect, sys
import pandas as pd
import matplotlib.pyplot as plt

import sys, os
sys.path.append('../')

from function_p import get_cms_relative
import utils
from utils import ApplyConfiguration

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from function_p import get_cms_relative
from utils import ApplyConfiguration
        
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica"]})



with open('../functions_output/configs.json', 'r') as fp:
    configs = json.load(fp)


nth = configs['nth']


th2s = configs['th2s']

configs = configs['configs']

NCONFIG = 200

dga = 2


config = [
    ApplyConfiguration.from_dict(configs[hash])
    for hash in configs if hash not in [ 'nth', 'th2s'] 
][NCONFIG]


_path_csv = f'../functions_output/f/{config.__hash__()}.csv'
_path_pkl = f'../functions_output/f/{config.__hash__()}.pickle'
    
df_f = pd.read_csv(_path_csv)

with open(_path_pkl, 'rb') as f:
    cms_ths = pickle.load(f)

ths = np.linspace(df_f.wvalue.min(), df_f.wvalue.max(), num=nth, dtype=np.float32)

ths = pd.Index(ths, name='th')

with open('/tmp/csvtmp.csv', 'w') as fp:
    str_ = pd.DataFrame(cms_ths, index=ths, columns=[ 'TN', 'FP', 'FN', 'TP']).reset_index().to_string()
    fp.write(str_)

cms_ths_rel = get_cms_relative(cms_ths)

with open('/tmp/csvtmp_relative.csv', 'w') as fp:
    df = pd.DataFrame()
    df['ths'] = ths
    df['tn'] = cms_ths_rel[0]
    df['tp'] = [ [ '%0.2f' % round(cms_ths_rel[3][d][i], 2) for d in utils.DGAS0 ] for i in range(cms_ths_rel[3][0].shape[0])  ]
    for d in utils.DGAS0:
        df['tp_%d' % d] = cms_ths_rel[3][d]

    fp.write(df.round(2).to_latex(index=False))

    pass

tp = 'tp'

df = df.drop(columns='tp').rename(columns={ 'ths': 'th', f'tp_{dga}': tp})

print(df)

df.th = df.th.astype(int)

df = df[df.th < -4000]

df['tn + tp'] = df.tn + df[tp]

ax = df.plot(x='th', y=['tn', tp], figsize=(10,6), color=[ 'CornflowerBlue', 'OrangeRed', 'green'])
plt.tight_layout()

max_ms_idx = df['tn + tp'].idxmax()

max_ms_th = df.th[max_ms_idx]
    
max_ms_tn = df.tn[max_ms_idx]
max_ms_tp = df[tp][max_ms_idx]
            

gap_tp = 0.04 if abs(max_ms_tn - max_ms_tp) < 0.05 else 0
sign_tp = 1 if max_ms_tn > max_ms_tp else -1


th2s = [ 0.25, 0.5, 0.75 ]
for j, th2 in enumerate(th2s):

    s = (df['tn'] > th2) & (df[tp] > th2)
    sa = s.cumsum()-s.cumsum().where(~s).ffill().fillna(0).astype(int)


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
        g = 0

        x = []
        def cc(g):
            x1 = df.th[g - 1]
            x2 = df.th[g]

            y1 = df.tn[g - 1]
            y2 = df.tn[g]
            if (y1 > th2 and y2 > th2):
                y1 = df[tp][g - 1]
                y2 = df[tp][g]

            if y1 == y2:
                x = x2
            else:
                x = (th2-y1)/(y2-y1) * (x2-x1)  + x1
            
            return x

        arrow_gap = 50
        x0 = cc(group[0]) - arrow_gap
        x1 = cc(group[1]) + arrow_gap

        ap = dict(
            arrowstyle=ArrowStyle('<->'),
            linewidth=0.5
        )

        # plt.plot([x0,x1], [th2,th2])

        plt.annotate('', xy=(x0, th2), xytext=(x1, th2), xycoords='data', arrowprops=ap)

        xt = x0-1400 if x1-x0 < 1000 else (x1+x0)/2
        yt = th2 if x1-x0 < 1000 else th2 - 0.04

        plt.annotate(f'$m_s^{{{th2}}}$', xy=(xt, yt), xytext=(xt, yt), fontsize=14, horizontalalignment='left', verticalalignment='center')

    pass

# plt.legend(bbox_to_anchor=(0.95, 0.95), prop={'size': 12})


pass

# plt.xticks([ x for x in list(plt.xticks()[0]) if x >= df.th.iloc[0] and x != -20000 ] + [ max_ms_th ])

plt.subplots_adjust(left=0.1,
                bottom=0.1,
                right=0.9, 
                top=0.9, 
                wspace=0.05, 
                hspace=0.05)


ax.set_xlim(df.th.iloc[0], df.th.iloc[-1])
ax.set_ylim(-0.005, 1.05)

plt.savefig(f'/tmp/plot_metric_dga_{dga}.png')

plt.show()
