import sys
sys.path.append('opt_lsct/rt/')
import numpy as np
import scipy.integrate as sci
from base.rt.gap import *
from base.rt.hotspot import *
# from scatter import *
import matplotlib.pyplot as plt

'''
冠层内组分的可视比例
proportion_directional: 表示单向的；
proportion_bidirectional: 表示双向的；
voxel: 表示体素的进体素的出；
one： 表示参数化方法直接算组分；
voxel_one: 表示体素方法直接积分到组分；
voxel_layer: 表示体素方法积分到了等效层；
_unit: 表示四组分,默认四组分，直接隐去；
_individual: 表示六组分，四组分外加树干；
_endmember:表示八组分，四组分外加树干和低层植被，端元可以直接是一组分、两组分、三组分。。。；

'''

####################################################################
###### Analytical Solution
####################################################################


def proprotion_directional_crown_one(lai,std,hcr,rcr,xza, G = 0.5):
    '''
    计算单向的组分可视比例，观测方向或者太阳方向
    :param lai:
    :param std:
    :param hcr:
    :param rcr:
    :param xza:
    :param G:
    :return:
    '''
    Psoil = gap_probability_crown_analytical(lai, std, hcr, rcr, xza, G)
    Pleaf = 1- Psoil
    return Psoil,Pleaf

def proportion_directional_hom_one(lai,xza,CI = 1.0, G = 0.5):
    Psoil = gap_probability_hom_analytical(lai,xza)
    Pleaf = 1-Psoil
    return Psoil,Pleaf

def proportion_directional_row_one(lai,row_width, row_blank, row_height, xza, xaa, raa):
    xra = np.abs(xaa - raa)
    Psoil = gap_probability_row_analytical(lai,row_width,row_blank,row_height,xza,xra)
    Pleaf = 1 - Psoil
    return Psoil, Pleaf

def proportion_bidirectional_crown_one(lai, std, hspot, hcr, rcr, vza, sza, vsa, G = 0.5):
    '''
    参数化方法，计算森林冠层四组分的可视比例
    :param lai:
    :param std:
    :param hspot:
    :param hcr:
    :param rcr:
    :param vza:
    :param sza:
    :param vsa:
    :param G:
    :return:
    '''

    bv = gap_probability_crown_analytical(lai, std, hcr, rcr, vza)
    bi = gap_probability_crown_analytical(lai, std, hcr, rcr, sza)
    Psoil = bv
    Pleaf = 1 - Psoil
    uv = np.cos(np.deg2rad(vza))
    ui = np.cos(np.deg2rad(sza))
    CIv = -np.log(bv) * uv / (lai * G)
    CIi = -np.log(bi) * ui / (lai * G)
    Psoil_sunlit = hotspot_layer(lai, hspot, vza, sza, vsa, CIi, CIv)
    Pleaf_sunlit = hotspot_analytical(lai, hspot, vza, sza, vsa, CIi, CIv)
    Psoil_shaded = Psoil - Psoil_sunlit
    Pleaf_shaded = Pleaf - Pleaf_sunlit

    return Psoil_sunlit,Psoil_shaded,Pleaf_sunlit,Pleaf_shaded

def proportion_bidirectional_hom_one(lai,hspot,vza,sza,vsa):
    Psoil = gap_probability_hom_analytical(lai, vza)
    Pleaf = 1 - Psoil
    Psoil_sunlit = hotspot_layer(lai, hspot, vza, sza, vsa)
    Pleaf_sunlit = hotspot_analytical(lai, hspot, vza, sza, vsa)
    Psoil_shaded = Psoil - Psoil_sunlit
    Pleaf_shaded = Pleaf - Pleaf_sunlit
    return Psoil_sunlit,Psoil_shaded,Pleaf_sunlit,Pleaf_shaded

def proportion_bidirectional_row_one(lai,hspot,row_width,row_blank,row_height,vza,vaa,sza,saa,raa,G = 0.5):

    vsa = np.abs(saa - vaa)
    sra = np.abs(saa - raa) % 180
    vra = np.abs(vaa - raa) % 180
    vsa[vsa > 180] = 360 - vsa[vsa > 180]

    bv = gap_probability_row_analytical(lai, row_width, row_blank, row_height, vza, vra)
    bi = gap_probability_row_analytical(lai, row_width, row_blank, row_height, sza, sra)
    Psoil = bv
    Pleaf = 1 - Psoil
    cthetv = np.cos(np.deg2rad(vza))
    cthets = np.cos(np.deg2rad(sza))
    CIv = -np.log(bv) * cthetv / (lai * G)
    CIi = -np.log(bi) * cthets / (lai * G)
    Psoil_sunlit = hotspot_layer(lai, hspot, vza, sza, vsa, CIi, CIv)
    Pleaf_sunlit = hotspot_analytical(lai, hspot, vza, sza, vsa, CIi, CIv)
    ####################################################################
    ##### '''Interesting !!!'''
    ####################################################################

    saa_ = saa - raa
    vaa_ = vaa - raa
    saa_[saa_ < 0] = 360 + saa_[saa_ < 0]
    vaa_[vaa_ < 0] = 360 + vaa_[vaa_ < 0]
    saa_[saa_ > 360] = saa_[saa_ > 360] - 360
    vaa_[vaa_ > 360] = vaa_[vaa_ > 360] - 360
    shadow_s = row_height * np.tan(np.deg2rad(sza)) * np.sin(np.deg2rad(sra))
    shadow_v = row_height * np.tan(np.deg2rad(vza)) * np.sin(np.deg2rad(vra))
    shadow_v[shadow_v > row_blank] = row_blank
    shadow_s[shadow_s > row_blank] = row_blank
    '''同向'''
    ind = (row_blank > shadow_v) * (row_blank > shadow_s) * ((saa_ - 180) * (vaa_ - 180) > 0)
    correction = np.ones(np.size(vza))
    if np.sum(ind) > 0:
        shadow = shadow_v * 1.0
        shadow[shadow < shadow_s] = shadow_s[shadow < shadow_s]
        correction[ind] = (row_width + row_blank) / (shadow[ind] + row_width)
    '''不同向'''
    ind = ((saa_ - 180) * (vaa_ - 180) < 0) * ((shadow_s + shadow_v) < row_blank)
    if np.sum(ind) > 0:
        shadow = shadow_s + shadow_v
        correction[ind] = (row_width + row_blank) / (shadow[ind] + row_width)
    '''顺垄'''
    ind = (shadow_s * shadow_v == 0) * (row_blank > shadow_v) * (row_blank > shadow_s)
    if np.sum(ind) > 0:
        shadow = shadow_v * 1.0
        shadow[shadow < shadow_s] = shadow_s[shadow < shadow_s]
        correction[ind] = (row_width + row_blank) / (shadow[ind] + row_width)
    testi = (shadow_s + row_width) / (row_blank + row_width)
    testv = (shadow_v + row_width) / (row_width + row_blank)
    Ksoil_sunlit = Psoil_sunlit / Psoil
    Ksoil_sunlit = Ksoil_sunlit / correction + (1 - 1.0 / correction)
    Psoil_sunlit = Psoil * Ksoil_sunlit

    Psoil_shaded = Psoil - Psoil_sunlit
    Pleaf_shaded = Pleaf - Pleaf_sunlit
    return Psoil_sunlit,Psoil_shaded,Pleaf_sunlit,Pleaf_shaded

