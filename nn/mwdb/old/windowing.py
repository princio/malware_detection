from re import DEBUG
from numpy.lib.arraysetops import unique
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import numpy as np
import time
import pprint
import sys

pp = pprint.PrettyPrinter(indent=4)

# With LLR2 we intend to set-to-0 (zeroing) the NOSFX values between two thresholds.
#

def run(s):
    db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")


    def f_llr(s_nosfx):
        num = s_nosfx.replace(
            [0, 1], [0.000_000_000_000_000_1, 1 - 0.000_000_000_000_000_1]
        )
        den = np.ones(len(num)) - num
        llr = np.log(num / den)
        return llr


    df_pcap = pd.read_sql(
        'SELECT id, "name", "malware_id", "infected", "qr", q, r, "unique", days FROM pcap ORDER BY name',
        db,
    )

    windows = [
        2500,
        500,
        100,
    ]

    max_q = np.lcm.reduce(windows) * (1_000_000 // np.lcm.reduce(windows))

    query = """
    DROP TABLE IF EXISTS public.windows;

    CREATE TABLE IF NOT EXISTS public.windows
    (
        id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
        pcap_id integer NOT NULL,
        "window" integer NOT NULL,
        
        "size" integer NOT NULL,
        q integer NOT NULL,
        r integer NOT NULL,

        "first_fn" integer DEFAULT 0,
        "last_fn" integer DEFAULT 0,

        "first_time" real DEFAULT 0.0,
        "last_time" real DEFAULT 0.0,

        CONSTRAINT windows_pkey PRIMARY KEY (id)
    )

    TABLESPACE pg_default;

    ALTER TABLE public.windows
        OWNER to postgres;
    """

    with db.cursor() as cur:
        cur.execute(query)

    db.commit()

    pd.options.display.float_format = '{:.2f}'.format

    for idx, pcap in df_pcap.iterrows():

        cur = db.cursor()

        query = """
            SELECT 
                COUNTER / %d AS W,
                COUNT(COUNTER) as Q,
                MIN(FN) first_fn_q,
                MAX(FN) last_fn_q,
                MIN(TIME_S) first_time_q,
                MAX(TIME_S) last_time_q
            FROM
                (SELECT FN,
                        TIME_S,
                        ROW_NUMBER () OVER (ORDER BY FN) -1 AS COUNTER
                    FROM MESSAGE3 AS M3
                    WHERE PCAP_ID = %d
                        AND IS_RESPONSE IS FALSE
                    ORDER BY FN) AS B
            GROUP BY W
            ORDER BY W""" % (s, pcap.id)
        
        df_fn_q = pd.read_sql(query, db)

        query = """
            SELECT *
            FROM
                MESSAGE3 AS M3
            WHERE pcap_id=%d
            ORDER BY FN
            LIMIT 1""" % (pcap.id)
        
        first_row = pd.read_sql(query, db)

        query = """
            SELECT *
            FROM
                MESSAGE3 AS M3
            WHERE pcap_id=%d
            ORDER BY FN DESC
            LIMIT 1""" % (pcap.id)
        
        last_row = pd.read_sql(query, db)

        df_fn = df_fn_q.copy()

        print("Processing pcap %d [%d/%d]" % (pcap.id, idx, df_pcap.shape[0]))

        # the windows bounds are defined by the number of queries (qnum = s), because I suppose
        # that is better to trigger the intrusion detector whit a threshold dependent on the number of queries.
        # if we count for both of them than we don't know how many times we count the same dn because the responses
        # duplicate them.
        df_fn['first_fn'] = df_fn['first_fn_q']
        df_fn['last_fn'] = df_fn['first_fn'].shift(-1) - 1
        df_fn.at[df_fn.index[0], 'first_fn'] = 0
        df_fn.at[df_fn.index[-1], 'last_fn'] = last_row['fn']

        df_fn['first_time'] = df_fn['first_time_q']
        df_fn['last_time'] = df_fn['first_time_q'].shift(-1)
        df_fn.at[df_fn.index[0], 'first_time'] = first_row['time_s']
        df_fn.at[df_fn.index[-1], 'last_time'] = last_row['time_s']

        df_fn['pcap_id'] = pcap.id
        df_fn['size'] = s
        df_fn['qr'] = None
        df_fn['r'] = None

        cur.execute("""SELECT COUNT(*)
                        FROM
                            (SELECT FN - LAG(FN, 1) OVER (ORDER BY FN) AS DIFF
                                FROM
                                    (SELECT FN
                                        FROM MESSAGES_%s
                                        ORDER BY FN) AS MORD) AS DIFFS
                        WHERE DIFF != 1""", (pcap.id,)
        )
        miss_fns = cur.fetchone()[0]
        if miss_fns != 0:
            print(f"Missing fns: {miss_fns}")
            qrs = []
            for idx, row in df_fn.iterrows():
                cur.execute("""
                    SELECT COUNT(*)
                    FROM
                        MESSAGES_%s
                    WHERE fn >= %s AND fn <= %s""", (pcap.id, row['first_fn'], row['last_fn']))
                qrs.append(cur.fetchone()[0])
            df_fn['qr'] = qrs
            df_fn['r'] = df_fn['qr'] - df_fn['q']
        else:
            df_fn['qr'] = df_fn['last_fn'] - df_fn['first_fn'] + 1
            df_fn['r'] = df_fn['qr'] - df_fn['q']


        values = df_fn[['pcap_id', 'size', 'q', 'r', 'w', 'first_fn', 'last_fn', 'first_time', 'last_time']].values
        execute_values(
            cur,
            """INSERT INTO public.windows(
                pcap_id, "size", q, r, "window", first_fn, last_fn, first_time, last_time)
                VALUES  %s;""",
            values
        )
        db.commit()
        cur.close()
        pass

if __name__ == "__main__":
    size = int(sys.argv[1])

    run(size)
    pass