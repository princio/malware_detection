from re import DEBUG
import psycopg2
import pandas as pd
from function_g import function_g
import utils
from sqlalchemy import create_engine
import numpy as np

eng = create_engine("postgresql://postgres:postgres@localhost/dns",)
db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")

def __test_1(cms_ths):
    """
    Tests if:
        - TN + FP is equal thorugh all the confusion matrixs.
        - FN + TP is equal thorugh all the confusion matrixs, for any dga.
    """
    cm = cms_ths[0]
    n = cm[0] + cm[1]
    p = sum([cm[2][dga] + cm[3][dga] for dga in utils.DGAS])
    
    for cm in cms_ths:
        if cm[0] + cm[1] != n:
            raise f"Exception N"
        if p != sum([cm[2][dga] + cm[3][dga] for dga in utils.DGAS]):
            raise Exception(f"Exception P")
        if (cm[2][0] + cm[3][0]) != sum([cm[2][dga] + cm[3][dga] for dga in utils.DGAS]):
            raise Exception(f"Exception P")
    pass


def __test_2(cms):
    """
    In this case cms_ths:
        [ TN, FP, FN0, TP0, FN1, TP1, FN2, TP2, FN3, TP3 ]
    Where all these elements are arrays.

    So the i-th CM is: [ TN[i], FP[i], FN0[i], TP0[i], FN1[i], TP1[i], FN2[i], TP2[i], FN3[i], TP3[i] ]

    Tests if:
        - TN + FP is equal thorugh all the confusion matrixs.
        - FN + TP is equal thorugh all the confusion matrixs, for any dga.
    """
    n = cms[0, 0] + cms[1, 0]
    p = sum([cms[2 + dga*2, 0] + cms[2 + dga*2 + 1, 0] for dga in utils.DGAS])

    ns = cms[0, :] + cms[1, :]
    if not all(ns == n):
        raise f"Exception N"

    ns = cms[0, :] + cms[1, :]
    
    dga=1
    ps  = cms[2 + dga*2, :] + cms[2 + dga*2 + 1, :]
    dga=2
    ps += cms[2 + dga*2, :] + cms[2 + dga*2 + 1, :]
    dga=3
    ps += cms[2 + dga*2, :] + cms[2 + dga*2 + 1, :]

    if not all(ps == p):
        raise Exception(f"Exception P")
    pass


def function_l(df_f, nth):
    """
    Input:
        - df_f: an F-Dataframe.
        - nth:  the number of threshold chosen linearly within the domain used to
                calculate the confusion matrixs.
    
    Ouput:
        - cms: an nth array of confusion matrixs.
    
    Given an F-Dataframe, returns an nth array of confusion matrixs.
    Each confusion matrix is calculated using the F-Dataframe and a threshold th.
    The nth thresholds are obtained from the domain:
        [ df_f.wvalue.min(), df_f.wvalue.max() ]
    and chosen linearly in this domain.

    Each confusion matrix has this format:
        [ TN, FP, [ FN0, FN1, FN2, FN3 ], [ TP0, TP1, TP2, TP3 ] ]
    """
    cms = []

    ths = np.linspace(df_f.wvalue.min(), df_f.wvalue.max(), num=nth, dtype=np.float32)

    p = { 0: sum(df_f.dga > 0)}
    for dga in utils.DGAS:
        p[dga] = sum(df_f.dga == dga)

    n = sum(df_f.dga == 0)
    
    for th in ths:
        cms.append(function_g(df_f, th, n, p))
        pass
    
    __test_1(cms)

    # cms2 = np.ndarray(shape=(10, len(cms)), dtype=np.int32)


    # cms2[0, :] = np.asarray([ cm[0] for cm in cms ])
    # cms2[1, :] = np.asarray([ cm[1] for cm in cms ])

    # for dga in utils.DGAS0:
    #     cms2[2 + dga*2, :] = np.asarray([ cm[2][dga] for cm in cms ])
    #     cms2[3 + dga*2, :] = np.asarray([ cm[3][dga] for cm in cms ])

    # print(cms2)

    # __test_2(cms2)

    return cms