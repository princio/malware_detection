import dataclasses
from apply_2 import perform
from flask import Flask, request, send_from_directory
from flask_cors import CORS, cross_origin
import os
import json
import psycopg2
import psycopg2.extras
import pandas as pd
import apply as apply_lib
import threading
import utils
from werkzeug.exceptions import NotFound
from sqlalchemy import create_engine

apply_threads = {}

def json_applies_load():
    applies = {}
    if os.path.exists('webapp-cache/applies.json'):
        with open('webapp-cache/applies.json') as f:
            applies = json.load(f)
    return applies

def json_applies_dump(applies):
    with open('webapp-cache/applies.json', 'w') as f:
        json.dump(applies, f)
    pass

def json_applies_add(apply_config: utils.ApplyConfiguration):
    applies = json_applies_load()
    applies[apply_config.__hash__()] = apply_config.__dict__
    json_applies_dump(applies)
    pass

def json_applies_delete(hash_):
    applies = json_applies_load()
    applies = { h_: applies[h_] for h_ in applies if h_ != hash_}
    json_applies_dump(applies)
    pass

app = Flask(__name__)
CORS(app)
DIR_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'csv')

eng = create_engine(
    "postgresql://postgres:postgres@localhost/dns",
)

db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")


@app.route('/csv/<string:filename>')
@cross_origin()
def send_json(filename):
    return send_from_directory(DIR_CSV, filename, as_attachment=False)


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


@app.route('/mwdb/apply/get/<apply_id>', methods = ['GET'])
@cross_origin()
def get_apply(apply_id):
    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT *
                FROM applies
                WHERE
                id=%s""",
            [ apply_id ])
        apply = cur.fetchone()
        pass

    summer = utils.apply_qr_count(db, apply_id)

    print(summer)

    apply['check'] = summer['wsum'] == summer['psum']

    return { "apply": apply }



@app.route('/mwdb/model/fetch', methods = [ 'GET' ])
@cross_origin()
def model_fetch():
    df = pd.read_sql("SELECT * FROM nns", db)
    return { 'models': df.to_dict(orient='records') }



@app.route('/mwdb/apply/clear-cache', methods = [ 'GET' ])
@cross_origin()
def apply_clear_cache():
    for f in os.listdir('webapp-cache/'):
        os.remove(os.path.join('webapp-cache/', f))
    return { 'files': os.listdir('webapp-cache/') }



@app.route('/mwdb/apply/fetch', methods = [ 'GET' ])
@cross_origin()
def apply_fetch2():
    applies = {}
    if os.path.exists('webapp-cache/applies.json'):
        with open('webapp-cache/applies.json', 'r') as f:
            applies = json.load(f)
    return { 'applies': applies }



@app.route('/mwdb/apply/do', methods = [ 'POST' ])
@cross_origin()
def apply_do():
    data = request.json
    
    apply_config = utils.ApplyConfiguration(
        data['name'],
        data['model_id'],
        data['wtype'],
        data['top10m'],
        data['wsize'],
        data['windowing'],
        data['pinf'],
        data['ninf']
    )

    fpath = f'webapp-cache/{apply_config.__hash__()}'
    if not os.path.exists(f'{fpath}.csv'):
        df = perform(apply_config)
        df.to_csv(f'{fpath}.csv')
        json_applies_add(apply_config)
        pass

    return {
        'hash': apply_config.__hash__()
    }



@app.route('/mwdb/apply/get', methods = ['POST'])
@cross_origin()
def apply_get():
    
    hash_ = request.json['hash']
    rounder = request.json.get('rounder', 10)

    fpath = f'webapp-cache/{hash_}.csv'

    if not os.path.exists(fpath):
        raise NotFound()
    
    if os.path.exists(fpath):
        df = pd.read_csv(fpath, index_col=0)
        df['wcount'] = 1
        df.wvalue = df.wvalue // rounder * rounder

        df = df.groupby(['wvalue', 'dga']).aggregate({
            'wcount': sum,
            'wlen': sum
        }).reset_index()
        pass

    return {
        "max": df['wvalue'].max(),
        "min": df['wvalue'].min(),
        "values": df.values.tolist(),
        "columns": df.columns.tolist()
    }



@app.route('/mwdb/apply/delete', methods = [ 'POST' ])
@cross_origin()
def apply_delete():
    hash_ = request.json['hash']

    fpath = f'webapp-cache/{hash_}.csv'

    if os.path.exists(fpath):
        os.remove(f'webapp-cache/{hash_}.csv')

    json_applies_delete(hash_)

    return {
        'ok': True
    }



@app.route('/mwdb/applies')
@cross_origin()
def get_applies():

    df = pd.read_sql(
        """SELECT a.*, max(w.wvalue), min(w.wvalue) FROM applies as a
            JOIN windows as w
            ON a.id=w.apply_id
            GROUP BY a.id""",
        db).fillna("--")

    df['check'] = None

    for i, a in df.iterrows():
        summer = utils.apply_qr_count(db, a['id'])
        df.at[i, 'check'] = summer['wsum'] == summer['psum']

    return {
        "applies": df.to_dict(orient='records')
    }



@app.route('/mwdb/apply/<apply_id>', methods = ['POST'])
@cross_origin()
def apply_fetch(apply_id, rounder=10):

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
        rounder = int((bounds[0] - bounds[1])/rounder)
        pass

    df = pd.read_sql(f"""
        SELECT COUNT(*) AS WCOUNT,
            COUNT(DISTINCT PCAP_ID) AS PCAPS,
            MW.DGA,
            WVALUE
        FROM
            (SELECT 
                    PCAP_ID,
                    ROUND(WVALUE::float / {rounder}) * {rounder} AS WVALUE
                FROM WINDOWS
                WHERE APPLY_ID={apply_id}) AS W
        JOIN PCAP AS P ON W.PCAP_ID = P.ID
        JOIN MALWARE AS MW ON MW.ID = P.MALWARE_ID
        GROUP BY WVALUE, DGA
        """, db)

    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT *
                FROM applies
                WHERE
                id=%s""",
            [ apply_id ])
        apply = cur.fetchone()
        pass

    return {
        "apply": apply,
        # "steps": steps,
        "values": df.values.tolist(),
        "columns": df.columns.tolist()
    }



@app.route('/mwdb/apply/all', methods = ['POST'])
@cross_origin()
def apply_fetch_all(rounder=10):

    if 'rounder' in request.get_json() and type(request.get_json()['rounder']) == int:
        rounder = request.get_json()['rounder']

    with db.cursor() as cur:
        cur.execute("""
            SELECT MAX(WVALUE), MIN(WVALUE)
                FROM windows""")
        bounds = cur.fetchone()
        rounder = int((bounds[0] - bounds[1])/rounder)
        pass

    df = pd.read_sql(f"""
        SELECT
            APPLY_ID,
            COUNT(*) AS WCOUNT,
            MW.DGA,
            WVALUE
        FROM
            (SELECT APPLY_ID,
                    PCAP_ID,
                    ROUND(WVALUE::float / {rounder}) * {rounder} AS WVALUE
                FROM WINDOWS) AS W
        JOIN PCAP AS P ON W.PCAP_ID = P.ID
        JOIN MALWARE AS MW ON MW.ID = P.MALWARE_ID
        GROUP BY APPLY_ID, WVALUE, DGA
        ORDER BY WVALUE, APPLY_ID, DGA;""", db)

    data = {}
    for apply_id in df.apply_id.values:
        _df = df[df.apply_id == apply_id].drop(columns='apply_id')
        data[f"{apply_id}"] = {
            "values": _df.values.tolist(),
            "columns": _df.columns.tolist()
        }
    
    return data



@app.route('/mwdb/apply/check/<apply_id>', methods = ['GET'])
@cross_origin()
def apply_check(apply_id):

    summer = utils.apply_qr_count(db, apply_id)

    return {
        'wsum': summer['wsum'],
        'psum': summer['psum'],
        'check': summer['wsum'] == summer['psum']
    }
    


@app.route('/mwdb/apply/exec/<apply_id>', methods = ['POST'])
@cross_origin()
def apply_exec(apply_id):

    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT *
                FROM applies
                WHERE
                id=%s""",
            [ apply_id ])
        apply = cur.fetchone()
        pass
    
    executing = 'none'
    message = ''
    if apply_id not in apply_threads:
        apply_threads[apply_id] = threading.Thread(target=apply_lib.run, args=(apply,))
        apply_threads[apply_id].start()
        message = 'Execution started.'
        executing = 'started'
    else:
        if apply_threads[apply_id].is_alive():
            message = 'Executing...'
            executing = 'progress'
        else:
            message = 'Done.'
            executing = 'success'

    return {
        'executing': executing,
        'message': message
    }



if __name__ == "__main__":
    app.run(port=3000, debug=True)