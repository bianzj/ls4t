import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from base.util_lsct.packages import *

'''
lsct_rad
计算辐射亮度
'''
def cal_rad_from_lst(lst,wl,lai,vza,emisS,emisV):
    '''
    根据lst计算rad
    :param lst: 反演出来的lst nl*ns
    :param wl: 波长
    :param lai: 叶面积 nl * ns
    :param vza: 天顶角 nl*ns
    :param emisS: 土壤发射率 nl*ns
    :param emisV: 植被发射率 nl*ns
    :return:
    '''
    fvc = 1 - gap_probability_hom_analytical(lai, vza)
    rad = planck(wl, lst)
    # 多次散射项
    F = 0.75
    C = (1 - emisS) * emisV * F * (1 - fvc)
    rad = rad * (fvc * emisV + (1 - fvc) * emisS + C)
    return rad

def cal_lst_from_bt(bt,wl,lai,vza,emisS,emisV):
    '''
    根据bt计算lst
    :param bt: 反演出来的btnl*ns
    :param wl: 波长
    :param lai: 叶面积nl*ns
    :param vza: 天顶角 nl*ns
    :param emisS: 土壤发射率 nl*ns
    :param emisV: 植被发射率 nl*ns
    :return:   
    '''
    fvc = 1 - gap_probability_hom_analytical(lai, vza)
    rad = planck(wl, bt)
    # 多次散射项
    F = 0.75
    C = (1 - emisS) * emisV * F * (1 - fvc)
    rad = rad / (fvc * emisV + (1 - fvc) * emisS + C)
    lst = inv_planck(wl, rad)
    return lst