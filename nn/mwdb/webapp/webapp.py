from ctypes import util
from email import utils
from flask import Flask, request, send_from_directory
from flask_cors import CORS, cross_origin
import os
import json
import psycopg2
import psycopg2.extras
import pandas as pd
import pickle
import numpy as np

import sys, os
sys.path.append('../')
from utils import DGAS, DGAS0, MODEL_NAME2ID, ROOT_DIR, TP, TN
from function_p import get_cms_relative


models_names = {
     7: 'icann',
     8: 'none',
     9: 'private',
    10: 'tld',
}

app = Flask(__name__)
CORS(app)
DIR_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'csv')

db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")


with open('/home/princio/Desktop/malware_detection/nn/mwdb/functions_output/configs.json') as fp:
    configs = json.load(fp)
NTH = configs['nth']
configs = configs['configs']
configs_array = [ ( hash, configs[hash] ) for hash in configs ]

@app.route('/csv/<string:filename>')
@cross_origin()
def send_json(filename):
    return send_from_directory(DIR_CSV, filename, as_attachment=False)


@app.route('/mwdb/configs')
@cross_origin()
def get_applies():

    df = pd.DataFrame.from_dict(configs).transpose()

    llr = df[df.wtype == 'llr']
    nx = df[df.wtype == 'nx']

    def convert_values(values):
        dd = {
            '-6.906754778648554': "λ(0.001)",
            '2.1972245773362196': "λ(0.9)",
            '6.906754778648553': "λ(0.999)",
            '13.815509557935018': "λ(0.999999)"
        }
        rvs = []
        for value in values:
            rvs.append(dd[str(value)] if str(value) in dd else value)
        return rvs
    

    return {
        'all_configs': {
            'models': ['nx'] + llr.model_id.drop_duplicates().apply(lambda x: models_names[x]).to_numpy().tolist(),
            'top10m': llr.top10m.drop_duplicates().to_numpy().tolist(),
            'wsize':  llr.wsize.drop_duplicates().to_numpy().tolist(),
            'windowing': llr.windowing.drop_duplicates().to_numpy().tolist(),
            'replace_values': [
                ['llr', rv, convert_values(rv)] for rv in llr.inf.drop_duplicates().to_numpy().tolist() ]\
                + [ ['nx', rv, convert_values(rv)] for rv in nx.inf.drop_duplicates().to_numpy().tolist()
                ]
        }
    }

@app.route('/mwdb/configs/hash', methods = ['POST'])
@cross_origin()
def get_apply_hash():

    _config_ = request.get_json()['config']

    _hash_ = [
        config[0] for config in configs_array
        if config[1]['model_id'] == MODEL_NAME2ID[_config_['model']]
        and
        config[1]['top10m'] == _config_['top10m']
        and
        config[1]['wsize'] == _config_['wsize']
        and
        config[1]['windowing'] == _config_['windowing']
        and
        (config[1]['inf'] == _config_['replace_values'][1] or config[1]['inf'] == _config_['replace_values'][1])
    ]
    _hash_ = _hash_[0]

    print(_config_, _hash_)

    return { 'hash': _hash_ }

@app.route('/mwdb/cms', methods = ['POST'])
@cross_origin()
def get_cm():
    _hash_ = request.get_json()['hash']

    _path_csv = os.path.join(ROOT_DIR, f'./functions_output/f/{_hash_}.csv')
    _path_pkl = os.path.join(ROOT_DIR, f'./functions_output/f/{_hash_}.pickle')
    
    df_f = pd.read_csv(_path_csv)

    with open(_path_pkl, 'rb') as f:
        cms_ths = pickle.load(f)

    ths = np.linspace(df_f.wvalue.min(), df_f.wvalue.max(), num=NTH, dtype=np.float32)
    
    cms_ths_rel = get_cms_relative(cms_ths)

    return {
        'ths': ths.tolist(),
        'cms': {
            'tn': cms_ths_rel[TN].tolist(),
            'tp': [
                cms_ths_rel[TP][dga].tolist()
                for dga in DGAS0
            ]
        }
    }

@app.route('/mwdb/pcap')
@cross_origin()
def get_pcaps():

    df = pd.read_sql("""SELECT * FROM pcap""", db)

    df = df.drop(columns='hash')

    return {
        'header': df.columns.tolist(),
        'values': df.values.tolist() #.to_json(orient='values')
    }


@app.route('/mwdb/pcap/json')
@cross_origin()
def get_pcaps_json():

    df = pd.read_sql("""SELECT * FROM pcap""", db)

    return df.to_json(orient='records')


@app.route('/mwdb/apply/<apply_id>', methods = ['POST'])
@cross_origin()
def get_window_grouped(apply_id, rounder=10):

    if 'rounder' in request.get_json() and type(request.get_json()['rounder']) == int:
        rounder = request.get_json()['rounder']

    with db.cursor() as cur:
        cur.execute("""
            SELECT MAX(WVALUE), MIN(WVALUE)
                FROM windows
                WHERE
                apply_id=%s""",
            [ apply_id ])
        bounds = cur.fetchone()
        rounder = (bounds[0] - bounds[1])/rounder
        pass

    df = pd.read_sql(f"""
        SELECT COUNT(*) AS WCOUNT,
            COUNT(DISTINCT PCAP_ID) AS PCAPS,
            MW.DGA,
            WVALUE
        FROM
            (SELECT APPLY_ID,
                    PCAP_ID,
                    WCOUNT,
                    ROUND(WVALUE::float / {rounder}) * {rounder} AS WVALUE
                FROM WINDOWS) AS W
        JOIN PCAP AS P ON W.PCAP_ID = P.ID
        JOIN MALWARE AS MW ON MW.ID = P.MALWARE_ID
        WHERE APPLY_ID = {apply_id}
        GROUP BY WVALUE,
	    DGA;""", db)

    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT *
                FROM applies
                WHERE
                id=%s""",
            [ apply_id ])
        apply = cur.fetchone()
        pass

    with db.cursor() as cur:
        cur.execute(f"""
            SELECT 
            MIN(ABS(W.WVALUE - W2.WVALUE))::integer AS "MIN",
            MAX(ABS(W.WVALUE - W2.WVALUE))::integer AS "MAX",
            AVG(ABS(W.WVALUE - W2.WVALUE))::integer AS "AVG"
            FROM WINDOWS AS W
            LEFT JOIN WINDOWS AS W2 ON W.PCAP_ID = W2.PCAP_ID
            AND W.WNUM = (W2.WNUM-1)
            AND W.APPLY_ID = W2.APPLY_ID
            WHERE W.APPLY_ID=%s
            """,
            [ apply_id ])
        steps = cur.fetchone()
        steps = dict(zip(['min','max','avg'], steps))
        pass


    return {
        "apply": apply,
        "steps": steps,
        "values": df.values.tolist(),
        "columns": df.columns.tolist()
    }

# @app.route('/mwdb/apply/exec/<apply_id>', methods = ['POST'])
# @cross_origin()
# def apply_exec(apply_id, rounder=10):

#     with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
#         cur.execute("""
#             SELECT *
#                 FROM applies
#                 WHERE
#                 id=%s""",
#             [ apply_id ])
#         apply = cur.fetchone()
#         pass

#     apply_lib.run(apply=apply)
    
#     pass

if __name__ == "__main__":
    app.run(port=3000, debug=True)