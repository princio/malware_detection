import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import json
from tabulate import tabulate
import streamlit as st

import numpy as np

import os
import sys
sys.path.append('../../')

from function_p import function_p, function_p_figs
import utils



if __name__ == "__main__":

    with open(os.path.join(utils.ROOT_DIR, 'functions_output/configs.json'), 'r') as fp:
        configs = json.load(fp)


    configs_set = {}

    for config_hash in configs['configs']:
        if config_hash in [ 'th2s', 'nth' ]: 
            continue

        for config_key in configs['configs'][config_hash]:
            if config_key not in configs_set:
                configs_set[config_key] = []
            if configs['configs'][config_hash][config_key] not in configs_set[config_key]:
                configs_set[config_key] += [ configs['configs'][config_hash][config_key] ]

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

    _inf = []
    nx = []
    for inf in configs_set['inf']:
        if int(inf[0]) == inf[0]:
            _inf.append(inf)
        else:
            def inv_logit(l):
                il = np.exp(l)/(1+np.exp(l))
                sil = str(il)
                if sil[-1] not in ['1', '9']:
                    il += (10 - int(sil[-1])) * 10 ** (- len(sil[sil.find('.')+1:]))
                return il
            nx.append([
                inv_logit(inf[0]),
                inv_logit(inf[1])
            ])
    

    configs_set['inf'] = _inf
    configs_set['nx'] = nx


    col1, col2 = st.columns(2)

    scol1, scol2, scol3 = st.columns(3)

    with col1:
        with scol1:
            st.selectbox('model_id', configs_set['model_id'])
            st.selectbox('wtype', configs_set['wtype'])
            st.selectbox('top10m', configs_set['top10m'])

        with scol2:
            st.selectbox('wsize', configs_set['wsize'])
            st.selectbox('windowing', configs_set['wtype'])

        with scol3:
            st.selectbox('inf', configs_set['inf'])
            st.selectbox('nx', configs_set['nx'])
            
        df_f, cms_ths, ths = utils.load(config_hash)

        plot = function_p(cms_ths, ths, plot=True)

        st.plotly_chart(plot)

    pass

"""

3bd929d0c28982bcaff354535e91c0a1
{'name': '', 'model_id': 7, 'wtype': 'llr', 'top10m': [0, 0], 'wsize': 2500, 'windowing': 'req', 'inf': [-20, 20]}

171f60b67a8acf78c29bbd876dedcbc4
{'name': '', 'model_id': 7, 'wtype': 'llr', 'top10m': [0, 0], 'wsize': 2500, 'windowing': 'req', 'inf': [-20, 200]}

"""