import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import pickle
import numpy as np
import json
import pandas as pd
from tabulate import tabulate

import sys, os
sys.path.append('../')

from function_p import get_cms_relative
import utils
from utils import ApplyConfiguration

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
        _path_csv = os.path.join(utils.ROOT_DIR, f'./functions_output/f/{config.__hash__()}.csv')
        _path_pkl = os.path.join(utils.ROOT_DIR, f'./functions_output/f/{config.__hash__()}.pickle')
        
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

            
        plt.rcParams.update({
            "text.usetex": True,
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica"]
        })

        fig, axs = plt.subplots(len(utils.DGAS0), sharex=True)

        tabs = [ [0] for _ in utils.DGAS0 ]

        for dga in utils.DGAS0:

            tp = 'tp$^{\\omega_{%d}}$' % dga

            df = df.rename(columns={ 'ths': 'th', f'tp_{dga}': tp})


            df['tn + tp'] = df.tn + df[tp]

            ax = df.plot(x='th', y=['tn', tp], figsize=(10,6), color=[ 'CornflowerBlue', 'OrangeRed', 'green'], ax=axs[dga])
            plt.tight_layout()

            max_ms_idx = df['tn + tp'].idxmax()

            max_ms_th = df.th[max_ms_idx]
            
            max_ms_tn = df.tn[max_ms_idx]
            max_ms_tp = df[tp][max_ms_idx]
                    
            tabs[dga][0] = f'{max_ms_tn:0.2f}, {max_ms_tp:0.2f}'

            axs[dga].set_ylabel(f'$\\omega^{dga}$', color='g')

            # axs[dga].text(max_ms_th, 1, 'max(tn + tp$^{\\omega_0}$)', ha='center')

            axs[dga].scatter([max_ms_th, max_ms_th], [max_ms_tn, max_ms_tp], c=['CornflowerBlue', 'OrangeRed'])

            gap_tp = 0.04 if abs(max_ms_tn - max_ms_tp) < 0.05 else 0
            sign_tp = 1 if max_ms_tn > max_ms_tp else -1
            
            axs[dga].annotate(f'{max_ms_tn:.2f}', xy=(df.th.min(), max_ms_tn + sign_tp*gap_tp), color='CornflowerBlue', fontsize=10, horizontalalignment='right', verticalalignment='center')
            axs[dga].annotate(f'{max_ms_tp:.2f}', xy=(df.th.min(), max_ms_tp - sign_tp*gap_tp), color='OrangeRed', fontsize=10, horizontalalignment='right', verticalalignment='center')

            axs[dga].plot([max_ms_th, max_ms_th], [-0.05, max_ms_tp if max_ms_tp > max_ms_tn else max_ms_tn], color='grey', linestyle='--', linewidth=0.5)
            axs[dga].plot([df.th.iloc[0], max_ms_th], [max_ms_tn, max_ms_tn], color='CornflowerBlue', linestyle='--', linewidth=0.5)
            axs[dga].plot([df.th.iloc[0], max_ms_th], [max_ms_tp, max_ms_tp], color='OrangeRed', linestyle='--', linewidth=0.5)

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
                    th_start = df.th[group[0] - 1 if group[0] > 0 else group[0]]
                    th_end = df.th[group[1] + 1 if group[1] > nth else group[1]]

                    tabs[dga].append((th_end-th_start) / (df.th.max() - df.th.min()))

                    axs[dga].annotate('', xy=(th_start, th2), xytext=(th_end, th2), arrowprops=dict(arrowstyle='<->', linewidth=0.5))
                    axs[dga].annotate(f'$th_2={th2:.2f}$', xy=(-36000, th2), horizontalalignment='center', verticalalignment='top')
                    axs[dga].annotate(f'$m_s({th2})$', xy=(th_start + (th_end - th_start) / 2, th2 - 0.07), fontsize=8, horizontalalignment='center', verticalalignment='center')

                pass

            # plt.legend(bbox_to_anchor=(0.95, 0.95), prop={'size': 12})

            yticks = [ 0 ] + th2s
            axs[dga].yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
            axs[dga].set_yticks(yticks)

            plt.setp(axs[dga].get_yticklabels(), rotation=30, horizontalalignment='right')

            axs[dga].set_xlim(df.th.iloc[0], df.th.iloc[-1])
            axs[dga].set_ylim(-0.005, 1.2)

            pass

        print(tabulate(tabs))

        print(tabulate(tabs, tablefmt='latex'))
                
        plt.xticks([ x for x in list(plt.xticks()[0]) if x >= df.th.iloc[0] and x != -20000 ] + [ max_ms_th ])

        plt.subplots_adjust(left=0.1,
                        bottom=0.1,
                        right=0.9, 
                        top=0.9, 
                        wspace=0.05, 
                        hspace=0.05)

        plt.savefig(f'/tmp/plot_metric_dga_{dga}.png')

        plt.show()

        pass

    pass