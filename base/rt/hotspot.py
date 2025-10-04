import sys
import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import numpy
import numpy as np
import scipy.integrate as sci
from base.rt.gap import *

'''
热点/双向透过率
layer:均质场景观测角度决定；
pl：  异质场景路径长度决定；
area: 异质场景几何投影+路径长度决定；

'''

def hotspot_layer(lai, hspot, vza, sza, vsa, CIs=1, CIv = 1, G = 0.5):
    '''
    热点函数，用于土壤热点计算
    :param lai: 叶面积指数
    :param hspot: 热点系数
    :param vza:  观测天顶角
    :param sza:  太阳天顶角
    :param vsa:  观测-太阳方位角
    :param CIi:  聚集指数
    :param CIv:  聚集指数
    :param G:  投影系数
    :return: 双向透过率
    '''

    cthetv = np.cos(np.deg2rad(vza))
    cthets = np.cos(np.deg2rad(sza))
    sthets = np.sin(np.deg2rad(sza))
    sthetv = np.sin(np.deg2rad(vza))
    cphivs = np.cos(np.deg2rad(vsa))

    ### correction 是SAIL 采纳的系数
    kv = G/cthetv
    ks = G/cthets
    correction = 2.0 / (kv + ks)

    H = 1.0
    d = H * hspot / correction
    delta = np.power(cthets, -2) + np.power(cthetv, -2) - 2 * (cthets * cthetv + sthets * sthetv * cphivs) / (cthets * cthetv)
    # delta = np.array(delta)

    # delta = 1.0 * np.sqrt(delta)
    if type(delta) == numpy.float64:
        if delta<0: delta=0
        alpha = H * np.sqrt(delta) / d
        w = (1 - np.exp(- alpha)) / alpha
    else:
        delta[delta < 0] = 0
        w = delta*1.0
        ind0 = np.where(delta < 0.0001)
        ind1 = np.where(delta > 0.0001)
        if np.size(ind0)>0:
            w[ind0] = 1
        if np.size(ind1)>0:
            alpha = H * np.sqrt(delta[ind1]) / d[ind1]
            w[ind1] = (1 - np.exp(- alpha)) / alpha

    pls = CIs * G / cthets
    plv = CIv * G / cthetv
    overlapping = np.sqrt(plv * pls)*w
    gapvs = np.exp(-( pls + plv - overlapping) * lai)
    return gapvs

def hotspot_analytical(lai, hspot, vza, sza, vsa, CIi = 1, CIv = 1, G = 0.5):
    '''
    多层植被热点的累计策略，假设为上下两层，上层可视假设全部被光照，下层可视认为层间独立
    与 num 相比 ， 热点窄一点，值稍微低一点
    :param lai:  叶面积指数
    :param hspot:  热点系数
    :param vza:  观测天顶角
    :param sza:  太阳天顶角
    :param vsa:  冠岑-太阳方位角
    :param CIi:  聚集指数
    :param CIv:  聚集指数
    :param G:  投影系数
    :return: 光照植被所占的比例，不归一化，双向透过率
    '''
    cthetv = np.cos(np.deg2rad(vza))
    cthets = np.cos(np.deg2rad(sza))
    sthets = np.sin(np.deg2rad(sza))
    sthetv = np.sin(np.deg2rad(vza))
    cphivs = np.cos(np.deg2rad(vsa))

    bv = np.exp(-G * lai * CIv / cthetv)
    bi = np.exp(-G * lai * CIi / cthets)

    ### 经验系数
    index = 0.83 - 0.04 * np.floor(lai / 0.5)

    kv = G / cthetv
    ki = G / cthets
    correction = 2.0 / (kv + ki)
    # correction[:] = 1.0
    H = 1.0
    # d = H * hspot * np.ones(np.size(correction))
    d = H * hspot / correction

    delta = 1.0 * np.sqrt(
        np.power(cthets, -2) + np.power(cthetv, -2) - 2 * (cthets * cthetv + sthets * sthetv * cphivs) / (
                    cthets * cthetv))
    bv_upper = 1 - (1 - bv) * index
    bi_upper = 1 - (1 - bi) * index
    hv_upper = -np.log(bv_upper) * cthetv / G / lai  ### 在观测方向的上层比例
    hi_upper = -np.log(bi_upper) * cthets / G / lai  ### 在太阳方向的上层比例
    h_upper = np.sqrt(hv_upper * hi_upper)  # 上层高度比例
    # h_upper = (hv_upper + hi_upper)*0.5
    # h_upper = hv_upper  ### 替代，这个可能会跟SAIL更接近
    h_bottom = 1 - h_upper  # 下层高度比例
    H_upper = H * h_upper  ### 上层高度
    H_bottom = H * h_bottom  ### 下层高度
    lai_upper = lai * h_upper  ### 上层的LAI
    lai_bottom = lai * h_bottom  ### 下层的LAI
    ### w_upper = (1 - np.exp(- H_upper * delta / d)) * d / (H_upper * delta)
    w_upper = delta * 1.0
    if type(w_upper) == numpy.float64:
        if delta < 0.0001:
            w_upper = 1
        else:
            w_upper = (1 - np.exp(- H * delta / d)) * d / (H * delta)
    else:
        ind0 = np.where(delta < 0.0001)
        ind1 = np.where(delta > 0.0001)
        if np.size(ind0) > 0:
            w_upper[ind0] = 1
        if np.size(ind1) > 0:
            ### 即使分层不能改变高度和半径的比例
            # alpha = H_upper[ind1] * delta[ind1] / d[ind1]
            alpha = H * delta[ind1] / d[ind1]
            w_upper[ind1] = (1 - np.exp(- alpha)) / alpha

    overlapping = G * np.sqrt(1.0 * CIi * CIv / (cthets * cthetv)) * w_upper
    ### 计算上层植被的光照可视背景
    sunlit_fraction_background_upper = np.exp(-(CIi * G / cthets + CIv * G / cthetv - overlapping) * lai_upper)
    ### w_bottom = (1 - np.exp(-H_bottom * delta / d)) * d / (H_bottom * delta)
    w_bottom = delta * 1.0
    if type(w_bottom) == numpy.float64:
        if delta < 0.0001:
            w_bottom = 1
        else:
            w_bottom = (1 - np.exp(- H * delta / d)) * d / (H * delta)
    else:
        ind0 = np.where(delta < 0.0001)
        ind1 = np.where(delta > 0.0001)
        if np.size(ind0) > 0:
            w_bottom[ind0] = 1
        if np.size(ind1) > 0:
            ### 即使分层不能改变高度和半径的比例
            # alpha = H_bottom[ind1] * delta[ind1] / d[ind1]
            alpha = H * delta[ind1] / d[ind1]
            w_bottom[ind1] = (1 - np.exp(- alpha)) / alpha
    ### 计算下层植被的光照比例
    sunlit_fraction_vegetation_bottom = 1 - np.exp(
        -G * np.sqrt(1.0 * CIv * CIi / (cthetv * cthets)) * w_bottom * lai_bottom)

    ### 上层的透过率，1-bv_upper 上层的不透过率，假设造成这些不透过率的植被就是光照植被
    bv_upper = np.exp(-G * lai_upper * CIv / cthetv)
    gapvs = (1 - bv_upper + sunlit_fraction_vegetation_bottom * sunlit_fraction_background_upper)

    return gapvs

def hotspot_numerical(lai, hspot, vza, sza, vsa, CI = 1, G = 0.5):
    '''
    多层植被热点的累计策略，每一层都通过hotspot_layer计算
    这里是采用了SAIL的方案，并不是按照物理距离分层，而是按照透过率聚集分层
    :param lai: 叶面积指数
    :param hspot: 热点系数
    :param vza: 观测天顶角
    :param sza: 太阳天顶角
    :param vsa: 观测-太阳方位角
    :param CI: 聚集指数
    :param G: 投影系数
    :return:
    '''

    uv = np.cos(np.deg2rad(vza))
    ui = np.cos(np.deg2rad(sza))
    si = np.sin(np.deg2rad(sza))
    sv = np.sin(np.deg2rad(vza))
    cospsi = np.cos(np.deg2rad(vsa))
    delta = 1.0 * np.sqrt(np.power(ui, -2) + np.power(uv, -2) - 2 * (ui * uv + si * sv * cospsi) / (ui * uv))

    bv = np.exp(-G*CI*lai/uv)
    ki = G / ui
    kv = G / uv
    correction = 2.0 / (kv + ki)
    alpha = (delta / hspot) * correction

    if type(alpha) == numpy.float64:
        if alpha < 0.0001: sunlit_fraction = 1
        else:
            x1 = 0
            y1 = 0
            f1 = 1.0
            fhot = lai * CI * np.sqrt(ki * kv)
            fint = (1.0 - np.exp(-alpha)) * 0.05
            sumint = 0
            for i in range(1,20):
                if i < 20:
                    x2 = - np.log(1.0 - i * fint) / alpha
                else:
                    x2 = 1
                y2 = -(ki + kv) * lai * CI * x2 + fhot * (1 - np.exp(-alpha * x2)) / alpha
                f2 = np.exp(y2)
                sumint = sumint + (f2 - f1) * (x2 - x1) / (y2 - y1)
                x1 = x2 * 1.0
                y1 = y2 * 1.0
                f1 = f2 * 1.0
            sunlit_fraction = kv * CI * lai * sumint / (1 - bv)
    else:
        sunlit_fraction = alpha * 1.0
        ind0 = np.where(alpha < 0.0001)
        ind1 = np.where(alpha > 0.0001)
        if np.size(ind0) > 0:
            sunlit_fraction[ind0] = 1.0
        if np.size(ind1) > 1:
            x1 = 0
            y1 = 0
            f1 = 1.0
            fhot = lai * CI * np.sqrt(ki * kv)
            fint = (1.0 - np.exp(-alpha)) * 0.05
            sumint = 0
            for i in range(1,21):
                if i < 20:
                    x2 = - np.log(1.0 - i * fint[ind1]) / alpha[ind1]
                else:
                    x2 = 1
                y2 = -(ki[ind1] + kv[ind1]) * lai * CI * x2 + fhot[ind1] * (1 - np.exp(-alpha[ind1] * x2)) / alpha[ind1]
                f2 = np.exp(y2)
                sumint = sumint + (f2 - f1) * (x2 - x1) / (y2 - y1)
                x1 = x2 * 1.0
                y1 = y2 * 1.0
                f1 = f2 * 1.0
            sunlit_fraction[ind1] = kv[ind1] * CI * lai * sumint / (1 - bv[ind1])

    return sunlit_fraction

def hotspot_layer_function(x):
    '''
    单层的热点函数，与hotspot_layer 相同，差别在于部分系数被放在全局变量
    :param x:  距离系数 0- 1
    :return:
    '''
    global lai0,G0,hspot0,sza0,vza0,raa0
    lai = lai0 *1.0
    G = G0 *1.0
    hspot = hspot0 * 1.0
    sza = sza0 * 1.0
    vza = vza0 * 1.0
    raa = raa0 * 1.0
    eps = 0.001
    rd = np.pi/180.0
    sthetv = np.sin(vza * rd)
    cthetv = np.cos(vza * rd)
    sthets = np.sin(sza * rd)
    cthets = np.cos(sza * rd)
    cospsi = np.cos(raa * rd)
    tants = sthets / cthets
    tanto = sthetv / cthetv
    dso = np.sqrt(tants * tants + tanto * tanto - 2.0 * tants * tanto * cospsi)
    ko = G / cthetv
    ks = G / cthets

    if dso < eps:
        pso = np.exp((ks + ko) * lai * (x) - np.sqrt(ko * ks) * lai * (x))
    else:
        alf = (dso / hspot) * 2 * (ks + ko)
        pso = np.exp((ks + ko) * lai * (x) + np.sqrt(ko * ks) * lai / alf * (1 - np.exp(x * alf)))
    return pso

def hotspot_integrated(lai, hspot, vza, sza, raa,  G = 0.5):
    '''
	通过积分的方式解决层间问题
    :param lai: 叶面积指数
    :param hspot: 热点系数
    :param vza: 观测天顶角
    :param sza: 太阳天顶角
    :param raa: 观测-太阳方位角
    :param CI: 聚集指数
    :param G: 投影系数
    :return:
    '''
    nz = 20
    xl = np.linspace(0,-1,nz)
    dx = np.float(1.0/nz)
    gapvs = np.zeros(nz)
    global lai0,G0,hspot0,sza0,vza0,raa0
    lai0 = lai*1.0
    G0 = G*1.0
    hspot0 = hspot*1.0
    sza0 = sza*1.0
    vza0 = vza*1.0
    raa0 = raa*1.0

    for j in range(nz):
        t1 = xl[j]-dx
        t2 = xl[j]
        gapvs[j] = sci.quad(hotspot_layer_function, t1, t2)[0]
        gapvs[j] = gapvs[j]/np.float(dx)

    return gapvs

def hotspot_vegetation_volume(lai, sza, CI = 1.0, G = 0.5):
    '''
    植被体系的整体的光照比例
    :param lai: 叶面积指数
    :param sza: 太阳天顶角
    :param CI:  聚集指数
    :param G:  投影系数
    :return:  光照比例
    '''
    sthets = np.cos(np.deg2rad(sza))
    ### 植被层的透过率
    # gap_probability_illuminate = np.exp(-G * lai * CI / sthets[0])
    gap_probability_illuminate = np.exp(-G * lai * CI / sthets)
    ### 1-透过率：植被阻挡概率； 植被的叶面积指数情况，计算的只是光照比例
    # sunlit_fraction_volume = (1 - gap_probability_illuminate) / (G * lai * CI) * sthets[0]
    sunlit_fraction_volume = (1 - gap_probability_illuminate) / (G * lai * CI) * sthets
    return sunlit_fraction_volume