from re import DEBUG
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
import utils

eng = create_engine("postgresql://postgres:postgres@localhost/dns",)
db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")

dgas = utils.DGAS0


TN = 0
FP = 1
FN = 2
TP = 3

#
# this function works with more configs
# input:
#       metrics:     array of metrics, one per each config
#       th2s:        [ 0.25, 0.5, 0.75 ]
# output:
#       cms:        [ cm_th0, cm_th1, ..., cm_thn, ]
def function_s2(df, k):
    """
    Input:
        - configs:      array of config
        - metricss:     array of metrics, each corresponding one config
        - k:    the config k that we want to evaluate, fixing the others config ks.

    Output:
        - df:           A Dataframe where the rows correspond to each config less the fixed config k.
                        The columns illustrate the behaviour of this k:
                            - with the mean
                            - with the standard deviation
                            - 
    
    """


    metrics = [ col for col in df.columns if col[0] != 'config' ]

    columns_configs_less_k = [ col for col in df.columns if col[0] == 'config' and col[1] != k ]
    
    configs_less_k = df[columns_configs_less_k].values

    df  = df.sort_values(by=columns_configs_less_k + [('config', k)])
    df  = df.set_index(columns_configs_less_k)

    ks = df[('config', k)].drop_duplicates().to_numpy().tolist()

    metrics_chosen = []
    for dga in utils.DGAS0:
        metrics_chosen += [ (dga, 'int'), (dga, 'int05') ]

    dfs = {}
    for kv in ks:
        _df_ = df[df[('config', k)] == kv].drop(columns=('config', k))

        dfs[kv] = _df_[metrics_chosen].mean()

        if (dfs[kv] >= 1).sum():
            print(dfs[kv])
    

    dfc = pd.DataFrame.from_dict(dfs, orient='index')

    dfc = dfc #/ dfc.mean()
    dfc_n = dfc / dfc.mean()

    dfc = pd.concat([ dfc, dfc.std().rename("std").to_frame().transpose() ], axis = 0)
    dfc = pd.concat([ dfc, dfc.std(axis=1).rename("std").to_frame() ], axis = 1)
    dfc_n = pd.concat([ dfc_n, dfc_n.std().rename("std").to_frame().transpose() ], axis = 0)
    dfc_n = pd.concat([ dfc_n, dfc_n.std(axis=1).rename("std").to_frame() ], axis = 1)

    return dfc, dfc_n


    print(pd.concat(dfs).to_frame().unstack())

    metrics = [ col for col in df.columns if col[0] != 'config' ]

    columns_configs_less_k = [ col for col in df.columns if col[0] == 'config' and col[1] != k ]
    
    configs_less_k = df[columns_configs_less_k].values


    df  = df.sort_values(by=columns_configs_less_k + [('config', k)])
    df  = df.set_index(columns_configs_less_k)

    # calculate the mean and std for each metric, fixed all the config ks except one.
    # DF:
    # index: corresponding to the field of any config less the variable k. one column for the variable k,
    # columns:
    #   - the first for the variable k
    #   - the others corresponding to the metric calculated in function_p

    stats = []
    index_configs = []
    for config_less_k in configs_less_k:
        stat = {}
        index_configs += [ config_less_k ]
        for metric in metrics:
            _df_ = df.loc[tuple(config_less_k)].sort_values(metric, ascending=False)
            stat[( metric, 'mean' )] = _df_[metric].mean()
            stat[( metric, 'std' )] = _df_[metric].std()
            stat[( metric, 'best' )] = _df_[('config', k)].iloc[0]
            pass
        stats.append(stat)
        pass
    
    # a dataframe where each row corresponds to set of configs having only the variable k changing
    df_s = pd.DataFrame(stats, index=pd.MultiIndex.from_tuples(index_configs))

    

    df_s.columns = pd.MultiIndex.from_tuples(df_s.columns)

    df_s = df_s.round(3)

    dbts = []
    for metric in metrics:
        dbt = {}

        dbt[('mean', 'mean')] = df_s[(metric, 'mean')].mean()
        dbt[('mean', 'max')] = df_s[(metric, 'mean')].max()
        dbt[('mean', 'min')] = df_s[(metric, 'mean')].min()

        dbt[('std', 'mean')] = df_s[(metric, 'std')].mean()
        dbt[('std', 'max')] = df_s[(metric, 'std')].max()
        dbt[('std', 'min')] = df_s[(metric, 'std')].min()

        s_rel = 100 * (df_s[(metric, 'std')] / df_s[(metric, 'mean')])
        dbt[('std', 'min std/mean%')] = s_rel.min()
        dbt[('std', 'max std/mean%')] = s_rel.max()
        dbt[('std', 'avg std/mean%')] = s_rel.mean()

        best_table = [ str(k[0]) for k in df_s[(metric, 'best')].value_counts().iteritems() ]
        dbt[('best', '1')] = best_table[0]
        if len(best_table) > 1:
            dbt[('best', '2')] = best_table[1]
        if len(best_table) > 2:
            dbt[('best', '3')] = best_table[2]

        dbts.append(dbt)

        pass

    df_compare = pd.DataFrame(dbts, index=pd.MultiIndex.from_tuples(metrics))

    df_compare.columns = pd.MultiIndex.from_tuples(df_compare)

    return df_compare