
import psycopg2
import pandas as pd
import sys, os
from psycopg2.extras import execute_values
import re
from pslregex import PSLdict


psldict = PSLdict()
psldict.init(download=False, update=False)


db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")


ds = pd.read_sql(
        f"""SELECT id, dn, bdn
            FROM public.dn2
            ORDER BY id
        """
    ,
    db)


sfx = [ psldict.match(dn) for dn in ds.dn.values ]


ds['dn'] = ds['dn'].str.lower()
ds['bdn'] = ds['bdn'].str.lower()


ds['tld'] = ds.dn.apply(lambda dn: None if dn.count('.') == 0 or dn[-1] == '.' else dn[dn.rfind('.')+1:])
ds['icann'] = [ s['icann']['suffix'] if s['icann'] is not None else None for s in sfx if s is not None ]
ds['private'] = [ s['private']['suffix'] if s['private'] is not None else None for s in sfx if s is not None ]


ds['bdn'] = ds['bdn'].apply(lambda bdn: bdn if bdn != 'ukw' else None)


# https://stackoverflow.com/a/26987741
regex = re.compile(r'^(((?!\-))(xn\-\-)?[a-z0-9\-_]{0,61}[a-z0-9]{1,1}\.)*(xn\-\-)?([a-z0-9\-]{1,61}|[a-z0-9\-]{1,30})\.[a-z]{2,}$')


ds['invalid'] = ds.dn.apply(lambda dn: regex.match(dn) is None)


with db.cursor() as cur:
    execute_values(
        cur,
        f"""UPDATE DN2 AS D SET 
        DN=E.DN,
        BDN=E.BDN,
        TLD=E.TLD,
        ICANN=E.ICANN,
        PRIVATE=E.PRIVATE,
        INVALID=E.INVALID
        FROM (VALUES %s) AS E(DN, BDN, TLD, ICANN, PRIVATE, INVALID, ID)  WHERE D.ID=E.ID""",
        ds[['dn', 'bdn', 'tld', 'icann', 'private', 'invalid', 'id']].values.tolist()
    )
    db.commit()