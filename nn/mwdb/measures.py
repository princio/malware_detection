import pandas as pd
import numpy as np

import psycopg2

from pandas.io import json
import argparse, utils

db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")

def run(apply):
    measures = {}
    ths = {}
    dfs = {}
    for dga in utils.DGAS:
        df = pd.read_sql(f"""SELECT w.*, malware.dga
                                FROM windows as w
                                JOIN pcap on pcap_id=pcap.id
                                JOIN malware ON pcap.malware_id=malware.id
                                WHERE apply_id={apply['id']}""",
                                db)
    
    for dga in utils.DGAS:
        measures[fx][size][dga] = []
        ths[fx][size][dga] = []
        DF = df[(df['size'] == size) & ((df.dga == 0) | (df.dga == dga))].copy()

        if fx in [ 'llr', 'llrt' ]:
            thmax = max([ bounds[fx][size][dga]['max'] for dga in utils.DGAS0 ])
            thmin = min([ bounds[fx][size][dga]['min'] for dga in utils.DGAS0 ])
            thstep = 10 if fx == 'llr' or fx == 'llrt' else 1
            nsteps = 1000
            thstep = (thmax - thmin) // nsteps
        else:
            thmax = size
            thmin = 1
            thstep = 1
            nsteps = size

        tprs = {
            'ni': np.zeros(nsteps),
            'i': np.zeros(nsteps),
            'th': np.zeros(nsteps),
        }

        for i in range(nsteps):
            th = thmax - thstep*i
            DF['detected'] = DF[fx] > th
            s_infected = DF.dga == dga
            s_not_infected = DF.dga == 0

            tp = ((DF.detected) & (s_infected)).sum()
            fp = ((DF.detected) & (s_not_infected)).sum()
            fn = ((~DF.detected) & (s_infected)).sum()
            tn = ((~DF.detected) & (s_not_infected)).sum()

            tpr_ni = round(tn / (tn + fp), 2)
            tpr_i = round(tp / (tp + fn), 2)

            tprs['ni'][i] = tpr_ni
            tprs['i'][i] = tpr_i
            tprs['th'][i] = th

        th_ni_max = tprs['th'].item(np.argmax(tprs['ni']))
        th_i_max = tprs['th'].item(np.argmax(tprs['i']))
        th_sum_max = tprs['th'].item(np.argmax(tprs['i'] + tprs['ni']))
        measures[fx][size][dga] = {
            "inf": th_i_max,
            "ninf": th_ni_max,
            "sum": th_sum_max,
        }

        # TODO: gt05 not working
        for gt in [ 3, 5, 7, 8, 9 ]:
            th_gt = tprs['th'][np.logical_and(tprs['ni'] >= gt/10, tprs['i'] >= gt/10)]
            if len(th_gt) > 0:
                measures[fx][size][dga]['gt0%d' % gt] = th_gt.item(0)
            measures[fx][size][0] = {}
            for dga in utils.DGAS0:
                for m in [ 'max', 'mean', 'min' ]:
                    measures[fx][size][dga][m] = bounds[fx][size][dga][m]


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Calculate optimal measures for an apply.')
    parser.add_argument('apply', metavar="APPLY_NAME", help='The apply name.')

    args = parser.parse_args()

    print(args)

    ###
    apply = utils.get_apply_byname(db, args.apply)
    
    if apply is None:
        yn = utils.get_yn("Function not exists.")
        exit(0)
    ###

    run(apply)
    
    pass
