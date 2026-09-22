"""AATSR case helpers moved from the run project on 2026-09-16."""


# ---------------------------------------------------------------------------
# AATSR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
import numpy as np
from numpy import corrcoef


def cal_rmse_r2(data1,data2,tshred=9):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2
