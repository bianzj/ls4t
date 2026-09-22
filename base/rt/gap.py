"""Canopy radiative-transfer helpers: gap probability."""


# ---------------------------------------------------------------------------
# SLSTR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
import numpy as np


def gap_probability_hom_analytical(lai, xza, CI=1.0, G=0.5):
    '''
    计算均质场景的透过率
    :param lai: 叶面积指数
    :param xza: 观测/太阳天顶角
    :param CI: 聚集指数
    :param G: 投影比例
    :return: 透过率
    '''
    cthetx = np.cos(np.deg2rad(xza))
    return np.exp(-lai * G * CI / cthetx)


def gap_probability_hom_hemisphere_analytical(lai, CI=1.0):
    '''
    均质场景的半球平均透过率，一种参数化估算方案
    :param lai: 叶面积指数
    :param CI:  聚集指数
    :return: 半球平均透过率
    '''
    ### 等效结果，通过拟合得到, 见 FR97 et al. FR02 et al.
    ### coeff 相当于投影比例 G
    coeff = 0.825
    return np.exp(-coeff * lai * CI)

