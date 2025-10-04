import numpy as np
import scipy.integrate as sci
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from base.rt.gap import *
from base.rt.hotspot import *
from base.rt.proportion import *

''' 
多次散射项
首先实现变量扩展的方法；
然后才开始矩阵方法转化；
'''

def multiple_scattering_analytical(lai,vza,refl_soil,refl_leaf):
    '''
    参数化的方案计算多次散射,FR97
    :param lai: 叶面积指数
    :param vza: 观测天顶角
    :param refl_soil:  土壤反射率
    :param refl_leaf:  叶片反射率
    :return:  冠层的多次散射项
    '''

    bv = gap_probability_hom_analytical(lai, vza)
    M = gap_probability_hom_hemisphere_analytical(lai)
    alpha = np.asarray([0.2855375, 0.2885375, 0.2964427, 0.3003953, 0.3083004, 0.3201581, 0.3399209, 0.3715415, 0.4189723, 1])
    vza_index_bottom = np.asarray(vza / 10, dtype=np.int)
    vza_index_top = vza_index_bottom + 1

    ratio = (vza % 10) / 10.0
    alphanew = alpha[vza_index_bottom] * (1-ratio) + alpha[vza_index_top] * ratio
    multiple_scattering_emissivity = bv * (1-M)* refl_soil  + (1-alphanew)*(1-bv*M) *(1-bv)*refl_leaf
    multiple_scattering_emissivity = multiple_scattering_emissivity *(1-refl_leaf)

    return multiple_scattering_emissivity


def multiple_scattering_analytical_sunlit(lai,vza,sza,refl_soil,refl_leaf):
    '''
	参数化的方案计算多次散射,区分光照和阴影
    :param lai: 叶面积指数
    :param vza: 观测天顶角
    :param sza: 太阳天顶角
    :param Kleaf: 比例系数
    :param refl_soil: 土壤反射率
    :param refl_leaf: 叶片反射率
    :return:
    '''
    bv = gap_probability_hom_analytical(lai, vza)
    M = gap_probability_hom_hemisphere_analytical(lai)
    alpha = np.asarray([0.2885375, 0.2885375, 0.2964427, 0.3003953, 0.3083004, 0.3201581, 0.3399209, 0.3715415, 0.4189723, 1])
    vza_index = np.asarray(vza / 10, dtype=int)
    Vsunlit = hotspot_vegetation_volume(lai, sza)
    Vshaded = 1 - Vsunlit
    multiple_scattering_emissivity_sunlit = bv * (1-M)* refl_soil*Vsunlit + (1-alpha[vza_index])*(1-bv*M) *(1-bv)*refl_leaf*Vsunlit
    multiple_scattering_emissivity_sunlit = multiple_scattering_emissivity_sunlit *(1-refl_leaf)
    multiple_scattering_emissivity_shaded = bv * (1-M)* refl_soil*Vshaded + (1-alpha[vza_index])*(1-bv*M) *(1-bv)*refl_leaf*Vshaded
    multiple_scattering_emissivity_shaded = multiple_scattering_emissivity_shaded *(1-refl_leaf)

    return multiple_scattering_emissivity_sunlit,multiple_scattering_emissivity_shaded



