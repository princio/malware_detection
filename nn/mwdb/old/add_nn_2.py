from matplotlib.style import available
import psycopg2
import pandas as pd
from keras.models import load_model as keras_load_model
from keras.preprocessing.sequence import pad_sequences
from tensorflow import convert_to_tensor
import os
import numpy as np
from psycopg2.extras import execute_values

max_len = 60

vocabulary = ['', '-', '.', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '_', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

pslremove_order = [
    'private', 'icann', 'tld'
]


db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")


df_dn = pd.read_sql(
            f"""SELECT *
                FROM public.dn2
                ORDER BY id;"""
        ,
        db)

def show_test(df_dn):
    df_dn = df_dn.loc[df_dn.icann.str.count('\.').sort_values().index]
    print(df_dn[~df_dn.private.isna()].head())
    print(df_dn[df_dn.private.isna() & (df_dn.icann.str.count('\.') > 1 ) & ~df_dn.icann.isna()].head())
    print(df_dn[df_dn.private.isna() & ~df_dn.icann.isna()].head())
    print(df_dn[df_dn.private.isna() & df_dn.icann.isna() & ~df_dn.tld.isna()].head())
    print(df_dn[df_dn.private.isna() & df_dn.icann.isna() & df_dn.tld.isna()].head())
    pass



def predict(df_dn, pslremove):

    def remove_psl(row, pslremove=''):
        if row['invalid']:
            return row['dn']
        
        availables = []
        for pslr in pslremove_order:
            if row[pslr] is not None:
                availables += [ pslr ]

        if pslremove in availables:
            nlabels = row[pslremove].count('.') + 1
            return '.'.join(row['dn'].split('.')[0:-nlabels])
        elif len(availables) > 0:
            nlabels = row[availables[0]].count('.') + 1
            return '.'.join(row['dn'].split('.')[0:-nlabels])
            
        return row['dn']
    
    df_dn = df_dn[~df_dn.invalid].copy()
    if pslremove == 'none':
        X = df_dn.dn.copy()
    else:
        X = df_dn.apply(remove_psl, axis=1, pslremove=pslremove)
    
    df_dn['X__'] = X
    
    X = X.apply(lambda x: '.'.join(x.split('.')[::-1]))

    df_dn['X_'] = X

    X = X.apply(lambda x: [ vocabulary.index(c) for c in x[:max_len] ])
    X = pad_sequences(
        X.values.tolist(), maxlen=max_len, padding='post', dtype="int32",
        truncating='pre', value=vocabulary.index('')
    )

    X = convert_to_tensor(X)

    df_dn['X'] = [ str(x) for x in X ]

    df_dn['Y'] = nn.predict(X, batch_size=128, verbose=1)[:,0]

    return df_dn


def load_model(path):
    return keras_load_model(path)


df_models = pd.read_sql(
    f"""SELECT *
        FROM public.nns
        ORDER BY id;"""
,
db)


if os.environ.get('DEBUG'):
    df_dn = pd.read_sql(
        f"""SELECT *
            FROM public.dn2
            ORDER BY id
            LIMIT 100
        """
    , db)
else:
    df_dn = pd.read_sql(
        f"""SELECT *
            FROM public.dn2
            ORDER BY id
        """
    , db)


for _, model in df_models.iterrows():
    if model['extractor'] in [ 'nosfx', 'domain', 'any', 'domain_sfx' ]:
        continue

    nn = load_model(model['path'])

    df = predict(df_dn, model['extractor'])

    df.to_csv('/tmp/Y_%s.csv' % model['extractor'])

    num = df['Y']
    den = np.ones(len(num)) - num

    logit = np.log(num / den)

    df['logit'] = logit

    df['nn_id'] = model['id']

    df.reset_index(inplace=True)

    with db.cursor() as cursor:
        cursor.execute('DELETE FROM public.dn2_nn WHERE nn_id = %s', [ model['id'] ])
        execute_values(
            cursor,
            """INSERT INTO public.dn2_nn(
                    dn_id, nn_id, value, logit)
                VALUES  %s;""",
            df[['id', 'nn_id', 'Y', 'logit']].values.tolist()
        )
    db.commit()

    pass
