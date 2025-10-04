import numpy as np
import scipy.integrate as sci
from base.rt.physicsF import *

'''
gap probability 透过率
inside: 表示穿过了相干冠层
outside: 表示穿过了不相干冠层
'''




#############################################################################
##### Analytical Solution
#############################################################################

#### 均质结构
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


#### 树冠结构

def gap_probability_crown_analytical(lai, std, hcr, rcr, xza, G=0.5):
    '''
    树冠的透过率
    :param lai: 叶面积指数
    :param std: 森林树密度
    :param hcr: 垂直方向的半径
    :param rcr: 水平方向的半径
    :param xza: 天顶角
    :param G: 投影系数
    :return: 透过率
    '''
    #### FRT
    tgthx = np.tan(np.deg2rad(xza))
    cthetx = np.cos(np.deg2rad(xza))
    ### 计算椭球树冠在地面的投影面积，即需要计算透过率的部分
    areav = np.sqrt(rcr * rcr + np.power(hcr * tgthx, 2)) * np.pi * rcr
    ### lai /(areav*std) 植被部分的等效LAI
    bv_in = np.exp(-lai / (areav * std) * G / cthetx)
    ### 面积*面积的透过率，这里面积就是考虑了几何形状，然后以该几何形状作为个体；而不是通过每个小面元作为个体。
    ### 原理一样，但是处理的基本单元不同，每个叶片还是叶片的集合*叶片的等效不透过率
    bv = np.exp(-areav * (1 - bv_in) * std)

    #### Li Ju Cai et al. 不太推荐使用，有偏差可能
    # area0 = np.pi * np.power(rcr, 2)
    # slai = lai / area0 / std
    # tv = np.tan(np.deg2rad(vza))
    # areav = np.sqrt(rcr * rcr + np.power(hcr * tv, 2)) * np.pi * rcr
    ### 椭球体到球体的转换，之后可以直接用
    # theta = np.arctan(hcr / rcr * np.tan(np.deg2rad(vza)))
    # uv = np.cos(theta)
    # bv_betweeen = np.exp(-std * area0/uv)
    # bv_in = np.exp(-slai/uv * G)
    # bv = bv_betweeen + (1-bv_betweeen) * bv_in

    return bv


#### 垄行结构

def gap_probability_row_analytical(lai, row_width, row_blank, row_height, xza, xra, CI=1.0, G=0.5):
    '''
    垄行植被类型的透过率，参数化解决方案,是多个区域的平均
    :param lai: 叶面积指数
    :param row_width: 行植被宽度
    :param row_blank: 行空白宽度
    :param row_height: 行高度
    :param xza: 太阳/观测天顶角
    :param xra: 太阳/观测-垄行相对方位角
    :param CI: 聚集指数
    :param G: 投影系数
    :return: 透过率
    '''
    row_spacing = row_width + row_blank
    laie = lai * row_spacing / row_width
    density = laie / row_height

    ### homgeneous vegetation
    ### 阈值判断，当小于0.03时候，认为垄行情况退化为均质
    if 1.0 * row_blank / row_spacing < 0.03:
        uv = np.cos(np.deg2rad(xza))
        bv = np.exp(-G * lai * CI / uv)
        return bv

    ### row-planted crop for angle = 0
    ### 观测方位角方向和垄行方向相同的时候，就是情况0
    ### 观测天顶角方向是0时，也是情况0
    number_angle = np.size(xza)
    bv = np.zeros(number_angle)
    ind = (xra % 180 == 0)
    if np.sum(ind):
        bv[ind] = gap_probability_row_zero(row_width, row_blank, row_height, density, xza[ind])
    ind = (xza == 0)
    if np.sum(ind):
        bv[ind] = gap_probability_row_zero(row_width, row_blank, row_height, density, xza[ind])

    ### 其他情况分别处理 ind0是排除以上情况类型；ind是ind0和各个情况
    ind0 = (xra % 180 != 0) * (xza != 0)
    if np.sum(ind0) > 0:
        row_width_ = np.zeros(number_angle)
        row_blank_ = np.zeros(number_angle)
        row_height_ = np.zeros(number_angle)
        number = np.zeros(number_angle)

        sr = np.sin(np.deg2rad(xra[ind0] % 180))
        row_width_[ind0] = row_width / sr
        row_blank_[ind0] = row_blank / sr
        row_spacing_ = row_width_ + row_blank_
        row_height_[ind0] = row_height * np.tan(np.deg2rad(xza[ind0]))
        number[ind0] = np.floor(row_height_[ind0] / row_spacing_[ind0])

        ### 详见 论文
        ### part 1
        ind = ind0 * ((number * row_spacing_) <= row_height_) * (
                    row_height_ <= (number * row_spacing_ + row_width_)) * (row_width_ <= row_blank_)
        if np.sum(ind) > 0:
            bv[ind] = gap_probability_row_part14(row_width_[ind], row_blank_[ind], row_height, number[ind], density,
                                                 xza[ind])
        ### part 2
        ind = ind0 * ((number * row_spacing_ + row_width_) <= row_height_) * (
                    row_height_ <= (number * row_spacing_ + row_blank_)) * (row_width_ <= row_blank_)
        if np.sum(ind) > 0:
            bv[ind] = gap_probability_row_part2(row_width_[ind], row_blank_[ind], row_height, number[ind], density,
                                                xza[ind])
        ### part 3
        ind = ind0 * ((number * row_spacing_ + row_blank_) <= row_height_) * (
                    row_height_ <= (number * row_spacing_ + row_spacing_)) * (row_width_ <= row_blank_)
        if np.sum(ind) > 0:
            bv[ind] = gap_probability_row_part36(row_width_[ind], row_blank_[ind], row_height, number[ind], density,
                                                 xza[ind])
        ### part 4
        ind = ind0 * ((number * row_spacing_) <= row_height_) * (
                    row_height_ <= (number * row_spacing_ + row_blank_)) * (row_width_ > row_blank_)
        if np.sum(ind) > 0:
            bv[ind] = gap_probability_row_part14(row_width_[ind], row_blank_[ind], row_height, number[ind], density,
                                                 xza[ind])
        ### part 5
        ind = ind0 * ((number * row_spacing_ + row_blank_) <= row_height_) * (
                    row_height_ <= (number * row_spacing_ + row_width_)) * (row_width_ > row_blank_)
        if np.sum(ind) > 0:
            bv[ind] = gap_probability_row_part5(row_width_[ind], row_blank_[ind], row_height, number[ind], density,
                                                xza[ind])
        ### part 6
        ind = ind0 * ((number * row_spacing_ + row_width_) <= row_height_) * (
                    row_height_ <= (number * row_spacing_ + row_spacing_)) * (row_width_ > row_blank_)
        if np.sum(ind) > 0:
            bv[ind] = gap_probability_row_part36(row_width_[ind], row_blank_[ind], row_height, number[ind], density,
                                                 xza[ind])

    return bv


def gap_probability_row_zero(row_width, row_blank, row_height, density, xza, CI=1.0, G=0.5):
    '''
    垂直方向、天顶角0、平行垄行方向
    :param row_width: 行植被宽度
    :param row_blank: 行空白宽度
    :param row_height: 行高度
    :param xza: 太阳/观测天顶角
    :param xra: 太阳/观测-垄行相对方位角
    :param CI: 聚集指数
    :param G: 投影系数
    :return:
    '''
    row_spacing = row_width + row_blank
    cthetx = np.cos(np.deg2rad(xza))
    bv = (row_width * np.exp(-G * row_height * density * CI / cthetx) + row_blank) / row_spacing
    return bv


def gap_probability_row_part14(row_width_, row_blank_, row_height, number, density, xza, G=0.5):
    '''
    条带1/4
    :param row_width: 行植被宽度
    :param row_blank: 行空白宽度
    :param row_height: 行高度
    :param xza: 太阳/观测天顶角
    :param xra: 太阳/观测-垄行相对方位角
    :param CI: 聚集指数
    :param G: 投影系数
    :return:
    '''
    row_spacing_ = row_width_ + row_blank_
    uv = np.cos(np.deg2rad(xza))
    tv = np.tan(np.deg2rad(xza))
    sv = np.sin(np.deg2rad(xza))
    ctg = 1.0 / tv
    p1 = (number * row_spacing_ + row_width_ - row_height * tv - 2 * sv / G / density) * \
         np.exp(-G * density * (row_height - number * row_blank_ * ctg) / uv)
    p2 = (number * row_spacing_ + row_blank_ - row_height * tv + 2 * sv / G / density) * \
         np.exp(-number * G * density * row_width_ * ctg / uv)
    return (p1 + p2) / row_spacing_


def gap_probability_row_part2(row_width_, row_blank_, row_height, number, density, xza, G=0.5):
    '''
    条带2
    :param row_width: 行植被宽度
    :param row_blank: 行空白宽度
    :param row_height: 行高度
    :param xza: 太阳/观测天顶角
    :param xra: 太阳/观测-垄行相对方位角
    :param CI: 聚集指数
    :param G: 投影系数
    :return:
    '''
    row_spacing_ = row_width_ + row_blank_
    uv = np.cos(np.deg2rad(xza))
    tv = np.tan(np.deg2rad(xza))
    sv = np.sin(np.deg2rad(xza))
    ctg = 1.0 / tv
    p1 = (-number * row_spacing_ - row_width_ + row_height * tv - 2 * sv / G / density) * \
         np.exp(-(number + 1) * G * density * row_width_ * ctg / uv)
    p2 = (number * row_spacing_ + row_blank_ - row_height * tv + 2 * sv / G / density) * \
         np.exp(-number * G * density * row_width_ * ctg / uv)
    return (p1 + p2) / row_spacing_


def gap_probability_row_part36(row_width_, row_blank_, row_height, number, density, xza, G=0.5):
    '''
    条带3/6
    :param row_width: 行植被宽度
    :param row_blank: 行空白宽度
    :param row_height: 行高度
    :param xza: 太阳/观测天顶角
    :param xra: 太阳/观测-垄行相对方位角
    :param CI: 聚集指数
    :param G: 投影系数
    :return:
    '''
    row_spacing_ = row_width_ + row_blank_
    uv = np.cos(np.deg2rad(xza))
    tv = np.tan(np.deg2rad(xza))
    sv = np.sin(np.deg2rad(xza))
    ctg = 1.0 / tv
    p1 = (-number * row_spacing_ - row_width_ + row_height * tv - 2 * sv / G / density) * \
         np.exp(-(number + 1) * G * density * row_width_ * ctg / uv)
    p2 = (-number * row_spacing_ - row_blank_ + row_height * tv + 2 * sv / G / density) * \
         np.exp(-G * density * (row_height - (number + 1) * row_blank_ * ctg) / uv)
    return (p1 + p2) / row_spacing_


def gap_probability_row_part5(row_width_, row_blank_, row_height, number, density, xza, G=0.5):
    '''
    条带5
    :param row_width: 行植被宽度
    :param row_blank: 行空白宽度
    :param row_height: 行高度
    :param xza: 太阳/观测天顶角
    :param xra: 太阳/观测-垄行相对方位角
    :param CI: 聚集指数
    :param G: 投影系数
    :return:
    '''
    row_spacing_ = row_width_ + row_blank_
    uv = np.cos(np.deg2rad(xza))
    tv = np.tan(np.deg2rad(xza))
    sv = np.sin(np.deg2rad(xza))
    ctg = 1.0 / tv
    p1 = (-number * row_spacing_ - row_blank_ + row_height * tv + 2 * sv / G / density) * \
         np.exp(- G * density * (row_height - (number + 1) * row_blank_ * ctg) / uv)
    p2 = (number * row_spacing_ + row_width_ - row_height * tv - 2 * sv / G / density) * \
         np.exp(- G * density * (row_height - number * row_blank_ * ctg) / uv)
    return (p1 + p2) / row_spacing_


### 树干结构

def gap_probability_trunk_analytical(hc_trunk, dbh_trunk, std_trunk, xza):
    '''
    参数化的方法计算树干的透过率，假设树干是圆柱
    :param hc_trunk:  树干高度
    :param dbh_trunk:  树干宽度
    :param std_trunk:  树干密度
    :param xza:  观测/太阳天顶角
    :return:  透过率
    '''

    ### 树干在观测上的投影面积比例
    tgthx = np.tan(np.deg2rad(xza))
    ### 研究区树干的投影面积
    Strunk = hc_trunk * dbh_trunk * tgthx * std_trunk

    ### 与树冠的投影相同，只是树干的透过率是0
    return np.exp(-Strunk)

