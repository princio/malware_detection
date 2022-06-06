import psycopg2
import pandas as pd
import sys, os
from psycopg2.extras import execute_values
import numpy as np
import argparse

max_len = 60

vocabulary = ['', '-', '.', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '_', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")

def run(df, nn_id):

    df_dn = pd.read_sql(
            f"""SELECT id, dn
                FROM public.dn
                WHERE
                    suffix is distinct from '-ukw-'
                ORDER BY id;"""
        ,
        db)


    df_test = df_dn.merge(df, on="id", suffixes=["_db", "_out"], how="left")
    missings = df_test["dn_out"].isna().sum()
    if missings > 0:
        print("Missing %d dn." % missings)
        return

    num = df['value']
    den = np.ones(len(num)) - num

    logit = np.log(num / den)

    df['logit'] = logit

    df['nn_id'] = nn_id

    df.reset_index(inplace=True)

    with db.cursor() as cursor:
        execute_values(
            cursor,
            """INSERT INTO public.dn_nn(
                    dn_id, nn_id, value, logit)
                VALUES  %s;""",
            df[['id', 'nn_id', 'value', 'logit']].values.tolist()
        )
    db.commit()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('model_path', metavar="PATH", type=str, help='The csv file path containing the nn output.')
    parser.add_argument('--nn', help='The name of the neural network.')
    args = parser.parse_args()
    if len(sys.argv) < 2:
        print('Too few arguments', sys.argv)
        exit(1)

    nn_name = args.nn
    file_path = args.csvpath
    with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM nns WHERE name=%s", [ nn_name ])
        nn = cur.fetchone()
        if nn is None:
            cur.execute("INSERT INTO nns (name) VALUES (%s) RETURNING id", [ nn_name ])
            nn_id = cur.fetchone()[0]
        else:
            nn_id = nn[0]

    if not os.path.exists(file_path):
        print("File not exists.")
        exit(1)
    
    df = pd.read_csv(file_path, index_col=None)
    if not all([c in df.columns for c in [ 'id', 'dn', 'value' ]]):
        print("Wrong csv input file.")
        exit(1)

    run(df, nn_id)
