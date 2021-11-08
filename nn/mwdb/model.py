import time, csv, re, os, random
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
from collections import OrderedDict, Counter as collection_counter
from json import load as json_load
from math import ceil
import numpy as np, pandas as pd
from keras.preprocessing.sequence import pad_sequences
from keras.models import model_from_json
import keras
import tensorflow as tf
from extractor import Extractor
from pathlib import Path


class Model:
    def __init__(self, path, name, tr, with_preproc_layer):
        self.path = path
        self.nn = None
        self.name = name
        self.tr = tr
        self.with_preproc_layer = with_preproc_layer 
        self.vocabulary = ['', '-', '.', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '_', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        self.input_max_len = 60

    @staticmethod
    def my_standardize(tensor):
        return tf.reverse(tf.strings.bytes_split(tf.strings.lower(tensor)), [1])

    def text_vectorization(self, dn):
        try:
            a = [self.vocabulary.index(l) for l in dn.lower().replace('.', '')]
            return a
        except:
            raise Exception('Error translating ///%s///' % dn)

    def load_model(self):
        if self.nn is not None: 
            print('model loaded')
            return
        if self.with_preproc_layer:
            with tf.keras.utils.custom_object_scope({'my_standardize': Model.my_standardize, 'reverse': tf.reverse, 'string_lower': tf.strings.lower, 'string_bytes_split': tf.strings.bytes_split}):
                self.nn = keras.models.load_model(self.path)
        else:
            with  open("%s.json" % self.path, 'r') as json_file:
                loaded_model_json = json_file.read()
            self.nn = model_from_json(loaded_model_json)
            self.nn.load_weights("%s.h5" % self.path)

    def preprocess(self, DN):
        X = DN.apply(self.translator).apply(lambda dn:[ self.vocabulary.index(c) for c in dn[-self.input_max_len:]])

        X = tf.keras.preprocessing.sequence.pad_sequences(
            X.values.tolist(), maxlen=self.input_max_len, padding='post', dtype="int32",
            truncating='pre', value=self.vocabulary.index('')
        )

    def predict(self, DNs, batch_size = 128, transform=True):
        if self.nn is None:
            raise 'Neural network not loaded.'

        if not type(DNs) == 'pandas.core.series.Series':
            DNs = pd.Series(DNs)

        df_tot = DNs.rename('qry').to_frame()
        df_u = df_tot.drop_duplicates().copy()
        if transform:
            df_u['X'] = df_u['qry'].apply(self.tr.translator())
        else:
            df_u['X'] = df_u['qry']
        df_u_x = df_u.drop_duplicates(subset='X').copy()
        
        X = tf.convert_to_tensor(df_u_x['X'].values, dtype=tf.string)
        df_u_x['y'] = self.nn.predict(X, batch_size=128, verbose=1)[:,0]
        
        return df_tot.merge(df_u.merge(df_u_x[['X', 'y']], on='X'), on='qry', how='left')
    

    def predict_raw(self, DNs, batch_size = 128, transform=True):
        if self.nn is None:
            raise 'Neural network not loaded.'

        if not type(DNs) == 'pandas.core.series.Series':
            DNs = pd.Series(DNs)

        X = tf.convert_to_tensor(DNs.values, dtype=tf.string)

        return self.nn.predict(X, batch_size=128, verbose=1)[:,0]

    def __str__(self):
        return self.path.split('/')[-1]

    @staticmethod
    def load(id):
        print(__file__)
        print(Path(__file__).parents)
        dir_ = os.path.dirname(os.path.__file__)
        def _join(path):
            return Path(__file__).parent.parent.parent.joinpath('models/').joinpath(path)
        if id == 'last': #AST
            return Model(_join('LAST/0.0'), 'last',  Extractor.DOMAIN, with_preproc_layer=False)
        if id == 'nosfx_old':
            return Model(_join('NOSFX/0.1/NOTLD_128_69_binary_0__f1-1_e26-30'), 'nosfx_0.0',  Extractor.NOSFX, with_preproc_layer=True)
        if id == 'domain_old':
            return Model(_join('DOMAIN/0.0/DOMAIN_128_63_binary_0__f1-1_e26-30'), 'domain_0.0',  Extractor.DOMAIN, with_preproc_layer=True)
        if id == 'nosfx':
            return Model(_join('NOSFX/0.1/NOSFX_128_63__8_20_binary_0__f5-8_e20-20'), 'nosfx',  Extractor.NOSFX, with_preproc_layer=True)
        if id == 'domain':
            return Model(_join('DOMAIN/0.1/DOMAIN_128_63__8_20_binary_1__f5-8_e20-20'), 'domain',  Extractor.DOMAIN, with_preproc_layer=True)
        if id == 'any':
            return Model(_join('ANY/ANY_128_73_3_30_binary_1__fx-3_e25-30'), 'any',  Extractor.ANY, with_preproc_layer=True)
        return None


if __name__ == "__main__":
    import psycopg2

    db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")

    print(pd.read_sql("SELECT * FROM nns", db).to_markdown(index=False))
