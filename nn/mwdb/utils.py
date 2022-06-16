from dataclasses import dataclass
from typing import Tuple
import psycopg2
import psycopg2.extras
import hashlib
from pathlib import Path
import os
import pandas as pd
import numpy as np
import pickle

"""
 7=ICANN
 8=NONE
 9=PRIVATE
10=TLD
"""

MODEL_NAME2ID = {
    'icann': 7,
    'none': 8,
    'private': 9,
    'tld': 10,
    'nx': 'nx'
}
DGAS0 = [ 0, 1, 2 ]
DGAS = [ 1, 2 ]
CDGAS = { 0: 0, 1: 1, 3: 2 }

TN = 0
FP = 1
FN = 2
TP = 3

ROOT_DIR = Path(__file__).parent

@dataclass
class ApplyConfiguration:
    name: str
    model_id: str
    wtype: str
    top10m: Tuple[bool, int]
    wsize: int
    windowing: str
    inf: Tuple[int, int]
    pass

    @staticmethod
    def from_dict(dict):
        return ApplyConfiguration(
            name=dict['name'] if 'name' in dict else None,
            model_id=dict['model_id'],
            wtype=dict['wtype'],
            top10m=tuple(dict['top10m']),
            wsize=dict['wsize'],
            windowing=dict['windowing'],
            inf=tuple(dict['inf'])
        )
    
    def to_dict(self):
        d = dict(
            name=self.name,
            model_id=self.model_id,
            wtype=self.wtype,
            top10m=self.top10m,
            wsize=self.wsize,
            windowing=self.windowing,
            inf=self.inf
        )
        if self.wtype == 'nx':
            d['inf'] = ( -20, 20 )
            d['model_id'] = 'nx %0.1f, %0.1f' % self.inf

        return d

    def __hash__(self):
        sha = hashlib.md5()
        seed = repr((
            self.model_id,
            self.wtype,
            self.top10m,
            self.wsize,
            self.windowing,
            self.inf
        )).encode('utf-8')
        sha.update(seed)
        return sha.hexdigest()
    
    def tolist(self):
        return [ self.model_id, self.wtype, self.top10m, self.wsize, self.windowing, self.inf ]

def get_db():
    return psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")

def get_model(db, name):
    with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM nns WHERE name=%s", [ name ])
        return cur.fetchone()

def get_models(db):
    with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM nns ORDER BY id", [])
        return { d['id']: dict(d) for d in cur.fetchall() }

def model_id2name(db):
    with db.cursor() as cur:
        cur.execute("""SELECT * FROM public.nns ORDER BY id ASC LIMIT 100""")
        nns = cur.fetchall()
        model_id2name = { nn[0]: nn[1] for nn in nns }
    return model_id2name

def get_apply(db, fn: ApplyConfiguration):
    with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT *
                FROM applies
                WHERE
                name=%s         AND
                wsize=%s        AND
                windowing=%s    AND
                wtype=%s      AND
                (nn_id=%s  OR nn_id IS NULL)        AND
                (top10m=%s OR top10m IS NULL)       AND
                (pinf=%s   OR pinf IS NULL)         AND
                (ninf=%s   OR ninf IS NULL)""",
            [ fn.name, fn.wsize, fn.windowing, fn.wtype, fn.model_id, fn.top10m, fn.pinf, fn.ninf ])
        res = cur.fetchone()
        return res['id'] if res is not None else None
    
def get_apply_byname(db, name):
    with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """SELECT * FROM applies WHERE name=%s""",
            [ name ]
        )
        apply = cur.fetchone()
        return ApplyConfiguration(
            apply['id'],
            apply['name'],
            apply['nn_id'],
            apply['wtype'],
            apply['top10m'],
            apply['wsize'],
            apply['windowing'],
            apply['pinf'],
            apply['ninf']
        )

def apply_qr_count(db, apply_id):
    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT *
                FROM applies
                WHERE
                id=%s""",
            [ apply_id ])
        apply = cur.fetchone()

        summer = "SUM(%s)" % { 'req': 'Q', 'res': 'R', 'both': 'RQ'}[apply.windowing]

        cur.execute(f"""
        SELECT wsum, psum::integer FROM
        (SELECT SUM(W.WCOUNT) AS WSUM FROM WINDOWS AS W WHERE APPLY_ID=%s) AS W
        CROSS JOIN (SELECT {summer} AS PSUM FROM PCAP) AS P
        """, [ apply_id ])
        summer = cur.fetchone()
        pass
    return summer
    
def create_apply(db, apply) -> int:
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO applies (name, wsize, windowing, wtype, nn_id, top10m, pinf, ninf) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING ID",
            [ apply.name, apply.wsize, apply.windowing, apply.wtype, apply.nn_id, apply.top10m, apply.pinf, apply.ninf ]
        )
    db.commit()
    return cur.fetchone()[0]

def get_dn_number(db):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM dn WHERE suffix is distinct from '-ukw-'")
        return cur.fetchone()[0]

def get_dn2_number(db):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM dn2 WHERE invalid IS FALSE")
        return cur.fetchone()[0]

def count_applied_windows(db, apply_id):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM windows WHERE apply_id=%s", (apply_id, ))
        return cur.fetchone()[0]

def count_toapply_windows(db, wsize):
    with db.cursor() as cur:
        cur.execute(f"""
        SELECT count(t1.WCOUNT) AS WCOUNTTOT FROM
            (SELECT FLOOR(FN_REQ / {wsize}) AS WNUM, COUNT(*) as wcount
                FROM MESSAGES_MASTER
                GROUP BY PCAP_ID, WNUM) AS t1
        """)
        return cur.fetchone()[0]
    
def count_windows(db):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM windows")
        return cur.fetchone()[0]

def get_inferenced_number(db, model_id):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM dn_nn WHERE nn_id = %s", ( model_id, ))
        return cur.fetchone()[0]

def get_inferenced_number2(db, model_id):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM dn2_nn WHERE nn_id = %s", ( model_id, ))
        return cur.fetchone()[0]

def max_top10m(db):
    with db.cursor() as cur:
        cur.execute("SELECT TOP10M FROM PUBLIC.DN WHERE TOP10M IS NOT NULL ORDER BY TOP10M DESC LIMIT 1")
        return cur.fetchone()[0]

def get_yn(message):
    print(message)
    input1 = input()
    while not input1 in [ "y", "n" ]:
        input1 = input()
    return input1

def load(config_hash, nth=200):
    df_f = None
    cms_ths = None
    ths = None

    csv_path = os.path.join(ROOT_DIR, f'./functions_output/f/{config_hash}.csv')
    if os.path.exists(csv_path):
        df_f = pd.read_csv(csv_path)
        df_f.dga = df_f.dga.where(df_f.dga != 2, 1)
        ths = np.linspace(df_f.wvalue.min(), df_f.wvalue.max(), num=nth, dtype=np.float32)

    cms = os.path.join(ROOT_DIR, f'./functions_output/f/{config_hash}.pickle')
    if os.path.exists(cms):
        with open(cms, 'rb') as f:
            cms_ths = pickle.load(f)

    for i, cm in enumerate(cms_ths):
        cm2 = [ 0, 0, [ 0, 0, 0 ], [ 0, 0, 0 ] ]
        cm2[TN] = cm[TN]
        cm2[FP] = cm[FP]
        for fntp in [ FN, TP ]:
            cm2[fntp][0] = cm[fntp][0]
            cm2[fntp][1] = cm[fntp][1] + cm[fntp][2]
            cm2[fntp][2] = cm[fntp][3]
        cms_ths[i] = cm2

    return df_f, cms_ths, ths


def cms_vertical(cms):
    return [
        np.array([ cm[TN] for cm in cms]),
        np.array([ cm[FP] for cm in cms]),
        [
            np.array([ cm[FN][0] for cm in cms]),
            np.array([ cm[FN][1] for cm in cms]),
            np.array([ cm[FN][2] for cm in cms]),
        ],
        [
            np.array([ cm[TP][0] for cm in cms]),
            np.array([ cm[TP][1] for cm in cms]),
            np.array([ cm[TP][2] for cm in cms])
        ]
    ]


if __name__ == '__main__':
    print(get_model(get_db(), "ciao"))
    print(get_dn_number(get_db()))