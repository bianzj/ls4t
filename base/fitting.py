"""AATSR case helpers moved from the run project on 2026-09-16."""


# ---------------------------------------------------------------------------
# AATSR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
from scipy.linalg import lstsq
import numpy as np
from sklearn.linear_model import BayesianRidge, Lasso, RidgeCV


def fitting_unknown_linear_ls(y,A):
    '''
    线性反演未知数，y=ax1+bx2+cx3, x3=1
    :param y: 因变量
    :param x: 自变量
    :return:
    '''
    coeffs = np.asarray(lstsq(A, y)[0])
    return coeffs


def fitting_unknown_linear_sklearn(y,A,method='ridge'):
    '''
    线性反演未知数，
    :param y: 因变量
    :param x: 自变量
    :param method: 方法，推荐ridge，然后是lasso，因为lasso会倾向于拟合0
    :return: 回归系数
    '''
    # alphas = [0.0001,0.001,0.01,0.1,1,10,100]
    alphas = [0.01]
    coeffs = 1.0
    if method=='ridge':
        clf = RidgeCV(alphas=alphas, fit_intercept=False)
        clf.fit(A, y)
        coeffs = clf.coef_
    elif method == 'lasso':
        clf = Lasso(alpha=0.01, fit_intercept=False)
        clf.fit(A, y)
        coeffs = clf.coef_
    elif method =='bayesianridge':
        clf = BayesianRidge(fit_intercept=False)
        clf.fit(A,y)
        coeffs = clf.coef_

    return coeffs
