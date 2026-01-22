import os
from re import M
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from base.util_data import *
from base.util_fitting import *
from base.rt.hom import *
from base.rt.crown import *
from base.util_phys import *
from scipy.optimize import fsolve
from multiprocessing import Pool, freeze_support, cpu_count

'''
0. define the number of observations, and the number of components;
1. calculate the effective emissivity of compoments based on surface structure;
2. calculate the ground-leaving radiance from lst and emissivity;
3. calculate the temperatures of components according to y = ax + b or y = ax + b + f(yprio)
'''

'''
ls4t_generate
正向模型
'''
def sample_hom_bt(Tsl, Tsh, Tvl, Tvh, lai, hspot, wavelength, emissivity_soil, emissivity_leaf, vza, sza, raa):
    # 注意输入 全部为单值（角度为list） 或全部为array
    '''1.initial'''
    hom = Hom()
    '''2.set variables'''
    hom.set_thermal(Tsl, Tsh, Tvl, Tvh)
    hom.set_structure(lai, hspot)
    hom.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    hom.set_angle(vza, sza, raa)
    ''''3.run'''
    bt = hom.run()
    vza[raa == 180] = vza[raa == 180] * -1
    return bt


def sample_hom_Emis(lai, hspot, wavelength, emissivity_soil, emissivity_leaf, vza, sza, raa):
    '''1.initial'''
    hom = Hom()
    '''2.set variables'''
    hom.set_structure(lai, hspot)
    hom.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    hom.set_angle(vza, sza, raa)
    ''''3.run'''
    emis = hom.run_emis()
    vza[raa == 180] = vza[raa == 180] * -1
    return emis

def sample_hom_Emis2(lai, hspot, wavelength, emissivity_soil, emissivity_leaf, vza, sza, raa):
    '''1.initial'''
    hom = Hom()
    '''2.set variables'''
    hom.set_structure(lai, hspot)
    hom.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    hom.set_angle(vza, sza, raa)
    ''''3.run'''
    emis = hom.run_emis2()
    vza[raa == 180] = vza[raa == 180] * -1
    return emis


def sample_crown_bt(Tsl, Tsh, Tvl, Tvh, lai, hspot, stand, rcr, hcr, wavelength, emissivity_soil, emissivity_leaf, vza,
                    sza, raa):
    '''1.initial'''
    crown = Crown()
    '''2.set variables'''
    crown.set_thermal(Tsl, Tsh, Tvl, Tvh)
    crown.set_structure(lai, hspot, stand, hcr, rcr)
    crown.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    crown.set_angle(vza, sza, raa)
    ''''3.run'''
    bt = crown.run()
    vza[raa == 180] = vza[raa == 180] * -1
    return bt


def sample_crown_Emis(lai, hspot, stand, rcr, hcr, wavelength, emissivity_soil, emissivity_leaf, vza, sza, raa):
    '''1.initial'''
    crown = Crown()
    '''2.set variables'''
    crown.set_structure(lai, hspot, stand, hcr, rcr)
    crown.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    crown.set_angle(vza, sza, raa)
    ''''3.run'''
    emis = crown.run_emis()
    vza[raa == 180] = vza[raa == 180] * -1
    return emis


'''
ls4t_rad
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

def cal_rad_from_lst_fvc(lst,wl,fvc,emisS,emisV):
    '''
    根据lst计算rad，不输入lai，直接输入fvc，适用于NDVI反演
    :param lst: 反演出来的lst nl*ns
    :param wl: 波长
    :param fvc: 植被覆盖度 nl * ns
    :param emisS: 土壤发射率 nl*ns
    :param emisV: 植被发射率 nl*ns
    :return:
    '''
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


'''
ls4t_emis
计算有效发射率方法
'''
def cal_fvc_from_ndvi(ndvi,ndvi_min,ndvi_max,k=1):
    fvc = (ndvi - ndvi_min)/(ndvi_max - ndvi_min)
    fvc = np.power(fvc,k)
    fvc[fvc > 1] = 1
    fvc[fvc < 0] = 0
    return fvc

def cal_fvc_from_lai(thetav,lai):
    G = 0.5
    rd = np.pi / 180.0
    costhetanv = np.cos(thetav * rd)
    fvc = 1 - exp(-G*lai/costhetanv)
    fvc[fvc>1] = 1
    fvc[fvc<0] = 0
    return fvc

def cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vza, sza, vaa, saa, n , m):
    '''
    计算均值假设下冠层的有效发射率，既能处理单点多角度输入又能处理区域输入
    :param lai: 叶面积指数 float 或 nl*ns
    :param hspot: 热点参数 float
    :param wl: 波长 float
    :param emisS: 土壤发射率 float 或 nl*ns
    :param emisV: 植被发射率 float 或 nl*ns
    :param vza: 观测天顶角 (n,) 或 nl*ns*n
    :param sza: 太阳天顶角 (n,)/float 或 nl*ns*n(nl*ns)
    :param vaa: 观测方位角 (n,) 或 nl*ns*n
    :param saa: 太阳方位角 (n,)/float 或 nl*ns*n(nl*ns)
    :param n: 观测角度数量
    :param m: 组分数量，2，3，4
    :param CI: 聚集指数 (n) 每个角度给一个值，默认为1
    :return: w 有效发射率 (n,m) 或 nl*ns*n*m
    '''
    # 确保输入为numpy数组
    lai = np.asarray(lai)
    emisS = np.asarray(emisS)
    emisV = np.asarray(emisV)
    vza = np.asarray(vza)
    sza = np.asarray(sza)
    vaa = np.asarray(vaa)
    saa = np.asarray(saa)
    sza[sza>=90] = 89.9
    if lai.ndim == 0:  # 标量输入，转换为点输入
        # 点输入处理
        vza = np.atleast_1d(vza)
        sza = np.atleast_1d(sza)
        vaa = np.atleast_1d(vaa)
        saa = np.atleast_1d(saa)
        w4 = sample_hom_Emis(lai, hspot, wl, emisS, emisV, vza, sza, np.abs(vaa-saa))
        w4 = w4.reshape((4, n))  # 4*n
        w = np.zeros([m, n])  # m*n 后面再转置
        if m == 2:
            w[0, :] = w4[0, :] + w4[1, :]
            w[1, :] = w4[2, :] + w4[3, :]
        elif m == 3:
            w[0:2, :] = w4[0:2, :]
            w[2, :] = w4[2, :] + w4[3, :]
        elif m == 4:
            w = w4
        return w.T
        
    else:  # 区域输入处理
        nl, ns = lai.shape  # 区域大小
        if sza.shape != vza.shape:
            sza = np.repeat(sza[:, :, np.newaxis], n, axis=2)
            saa = np.repeat(saa[:, :, np.newaxis], n, axis=2)
        vsa = np.abs(vaa - saa)
        w4 = np.zeros([nl, ns, 4, n])  # nl*ns*4*n
        for ni in range(n):
            if m == 2:
                result = sample_hom_Emis2(lai, hspot, wl, emisS, emisV, 
                                   vza[:, :, ni], sza[:, :, ni], vsa[:, :, ni])
            else:
                result = sample_hom_Emis(lai, hspot, wl, emisS, emisV, 
                                   vza[:, :, ni], sza[:, :, ni], vsa[:, :, ni])
            w4[:, :, :, ni] = result.transpose(1, 2, 0)
        w = np.zeros([nl, ns, m, n])  # nl*ns*m*n
        
        if m == 2:
            w[:, :, 0, :] = w4[:, :, 0, :] + w4[:, :, 1, :]
            w[:, :, 1, :] = w4[:, :, 2, :] + w4[:, :, 3, :]
        elif m == 3:
            w[:, :, 0:2, :] = w4[:, :, 0:2, :]
            w[:, :, 2, :] = w4[:, :, 2, :] + w4[:, :, 3, :]
        elif m == 4:
            w = w4
        return w.transpose(0, 1, 3, 2) # nl*ns*n*m

def cal_effective_emissivity_hom_2_CI(lai, hspot, wl, emisS, emisV, vza, sza, vaa, saa, n , m = 2, CI = None):
    '''
    计算均值假设下冠层的有效发射率，既能处理单点多角度输入又能处理区域输入
    :param lai: 叶面积指数 float 或 nl*ns
    :param hspot: 热点参数 float
    :param wl: 波长 float
    :param emisS: 土壤发射率 float 或 nl*ns
    :param emisV: 植被发射率 float 或 nl*ns
    :param vza: 观测天顶角 (n,) 或 nl*ns*n
    :param sza: 太阳天顶角 (n,)/float 或 nl*ns*n(nl*ns)
    :param vaa: 观测方位角 (n,) 或 nl*ns*n
    :param saa: 太阳方位角 (n,)/float 或 nl*ns*n(nl*ns)
    :param n: 观测角度数量
    :param m: 组分数量，2，3，4
    :param CI: 聚集指数 (n) 每个角度给一个值，默认为1
    :return: w 有效发射率 (n,m) 或 nl*ns*n*m
    '''
    # 确保输入为numpy数组
    lai = np.asarray(lai)
    emisS = np.asarray(emisS)
    emisV = np.asarray(emisV)
    vza = np.asarray(vza)
    sza = np.asarray(sza)
    vaa = np.asarray(vaa)
    saa = np.asarray(saa)
    if CI is None:
        CI = np.ones(n)
    sza[sza>=90] = 89.9
    if lai.ndim == 0:  # 标量输入，转换为点输入
        # 点输入处理
        vza = np.atleast_1d(vza)
        sza = np.atleast_1d(sza)
        vaa = np.atleast_1d(vaa)
        saa = np.atleast_1d(saa)
        w = np.zeros([n, m])
        for i in range(n):
            fvc = 1 - gap_probability_hom_analytical(lai[i], vza[i], CI[i])
            w[i, 0] = emisS * (1 - fvc)
            w[i, 1] = emisV * fvc
        return w
        
    else:  # 区域输入处理
        nl, ns = lai.shape  # 区域大小
        if sza.shape != vza.shape:
            sza = np.repeat(sza[:, :, np.newaxis], n, axis=2)
            saa = np.repeat(saa[:, :, np.newaxis], n, axis=2)
        vsa = np.abs(vaa - saa)
        w = np.zeros([nl, ns, n, 2])  # nl*ns*4*n
        for ni in range(n):
            fvc = 1 - gap_probability_hom_analytical(lai[:, :], vza[:, :, ni], CI[ni])
            w[:, :, ni, 0] = emisS * (1 - fvc)
            w[:, :, ni, 1] = emisV * fvc
        return w # nl*ns*n*m


def cal_psoil_hom(lai,sza):
    '''
    计算均值假设下冠层的光照土壤占总土壤的比例
    :param lai: 叶面积指数
    :param sza: 太阳天顶角
    :return: psoil 光照土壤占总土壤的比例
    计算公式：psoil = exp(-G*LAI/cos(sza))
    '''
    sza = np.atleast_1d(np.asarray(sza))
    lai = np.atleast_1d(lai)
    if sza.ndim == 1:
        sza = sza.reshape(1, 1)
    nl, ns = np.shape(sza)
    psoil = gap_probability_hom_analytical(lai, sza)
    if nl == 1 and ns == 1:
        psoil = psoil.squeeze()
    return psoil

def cal_effective_emissivity_crown(lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,classif,std,rcr,hcr,component_number):
    # 未调试
    nl,ns = np.shape(vza)
    w4,psoil = np.zeros([4, nl, ns]),np.zeros([nl, ns])
    crown_class = [1, 2, 3, 4, 5, 8, 9]
    ind_c = np.isin(classif, crown_class) * (rcr != 0) * (std != 0) * (hcr != 0)
    # hom
    w4[:, ~ind_c]  = sample_hom_Emis(lai[:, ~ind_c] ,0.2,wl,emisS[:, ~ind_c],emisV[:, ~ind_c],vza[:, ~ind_c],sza[:, ~ind_c],np.abs(vaa[:, ~ind_c]-saa[:, ~ind_c]))
    psoil[~ind_c]  = gap_probability_hom_analytical(lai[:, ~ind_c] ,sza[:, ~ind_c])
    # crown
    w4[:,ind_c] = sample_crown_Emis(lai[ind_c], hspot, std[ind_c], rcr[ind_c], hcr[ind_c], wl,
                                                  emisS[ind_c], emisV[ind_c], vza[ind_c], sza[ind_c],
                                                  np.abs(vaa[ind_c] - saa[ind_c]))
    psoil[ind_c] = gap_probability_hom_analytical(lai[:, ind_c] ,sza[:, ind_c])
    if component_number == 2:
        w = np.zeros([2,nl,ns])
        w[0,:,:] = w4[0,:,:] + w4[1,:,:]
        w[1,:,:] = w4[2,:,:] + w4[3,:,:]
    if component_number == 3:
        w = np.zeros([3,nl,ns])
        w[0:2,:,:] = w4[0:2,:,:]
        w[2,:,:] = w4[2,:,:] + w4[3,:,:]
    if component_number == 4:
        w = w4
    return w,psoil

def cal_psoil_crown(lai,std,hcr,rcr,sza):
    # 未调试
    sza = np.atleast_1d(np.asarray(sza))
    lai = np.atleast_1d(lai)
    std = np.atleast_1d(std)
    hcr = np.atleast_1d(hcr)
    rcr = np.atleast_1d(rcr)
    if sza.ndim == 1:
        sza = sza.reshape(1, 1)
    nl, ns = np.shape(sza)
    psoil = gap_probability_crown_analytical(lai, std, hcr, rcr, sza, G=0.5)
    if nl == 1 and ns == 1:
        psoil = psoil.squeeze()
    return psoil


'''
util_constraint
温差限制 以及 窗口权重weight
'''
def constraint_func_Nangle(x, lst, ws=None, wl=10.8):
    '''
    正确性约束（约等于无约束）组分能量与LST的温差约束条件，即可处理点输入，也可处理窗口输入
    :param x: 组分能量
    :param lst: LST数据
    :param ws: 窗口大小（可选），如果提供则使用窗口中心点的LST
    :param wl: 波长，默认为10.8μm
    :return: 约束条件值 [constraint1, constraint2]
    '''
    if ws is not None:
        center = int(ws // 2)
        b = planck(wl, lst[center, center, :])
    else:
        b = planck(wl, lst)

    # 计算约束条件
    constraint1 = np.max(x) - np.max(b)
    constraint2 = np.min(b) - np.min(x)

    return [constraint1, constraint2]

def constraint_func_Nangle_2component(x, lst, d, ws=None, wl=10.8):
    '''
    两组分温差限制,土壤植被 温差限制
    :param x: 组分能量
    :param ws: 窗口大小
    :param lst: 垂直LST,注意此处为ws*ws*n
    :param d: 光照土壤与阴影土壤的温差范围,单位是K [min,max]
    :return: 约束条件值
    '''
    if ws is not None:
        center = int(ws // 2)
        b = planck(wl, lst[center, center, :])
        lsta = np.nanmean(lst[center, center, :])
    else:
        b = planck(wl, lst)
        lsta = np.nanmean(lst)
    d12_min = planck(wl, lsta + d[0] / 2) - planck(10.8, lsta - d[0] / 2)
    d12_max = planck(wl, lsta + d[1] / 2) - planck(10.8, lsta - d[1] / 2)
    constraint1 = np.max(x) - np.max(b)
    constraint2 = np.min(b) - np.min(x)
    constraint3 = -d12_min + (x[0] - x[1])
    constraint4 = d12_max - (x[0] - x[1])
    return [constraint1, constraint2, constraint3, constraint4]

def constraint_func_Nangle_2component_winquad(x, lst, d, ws=None, wl=10.8):
    '''
    两组分温差限制,土壤植被 温差限制
    :param x: 组分能量
    :param ws: 窗口大小
    :param lst: 垂直LST,注意此处为ws*ws*n
    :param d: 光照土壤与阴影土壤的温差范围,单位是K [min,max]
    :return: 约束条件值
    '''
    if ws is not None:
        center = int(ws // 2)
        b = planck(wl, lst[center, center, :])
        lsta = np.nanmean(lst[center, center, :])
    else:
        b = planck(wl, lst)
        lsta = np.nanmean(lst)
    d12_min = planck(wl, lsta + d[0] / 2) - planck(10.8, lsta - d[0] / 2)
    d12_max = planck(wl, lsta + d[1] / 2) - planck(10.8, lsta - d[1] / 2)
    constraint1 = np.max([x[0],x[6]]) - np.max(b)
    constraint2 = np.min(b) - np.min([x[0],x[6]])
    constraint3 = -d12_min + (x[0] - x[6])
    constraint4 = d12_max - (x[0] - x[6])
    return [constraint1, constraint2, constraint3, constraint4]


def constraint_func_Nangle_3component(x, lst, d12, d23, ws=None, wl=10.8):
    '''
    三组分温差限制,光照阴影土壤、阴影土壤植被 温差限制
    :param x: 组分能量
    :param ws: 窗口大小
    :param lst: 垂直LST,注意此处为ws*ws*n
    :param d12: 光照土壤与阴影土壤的温差范围,单位是K [min,max]
    :param d23: 阴影土壤与植被的温差范围,单位是K [min,max]
    :return: 约束条件值
    '''
    if ws is not None:
        center = int(ws // 2)
        b = planck(wl, lst[center, center, :])
        lsta = np.nanmean(lst[center, center, :])
    else:
        b = planck(wl, lst)
        lsta = np.nanmean(lst)
    d12_min = planck(wl, lsta + d12[0] / 2) - planck(10.8, lsta - d12[0] / 2)
    d12_max = planck(wl, lsta + d12[1] / 2) - planck(10.8, lsta - d12[1] / 2)
    d23_min = planck(wl, lsta + d23[0] / 2) - planck(10.8, lsta - d23[0] / 2)
    d23_max = planck(wl, lsta + d23[1] / 2) - planck(10.8, lsta - d23[1] / 2)
    constraint1 = np.max(x) - np.max(b)
    constraint2 = np.min(b) - np.min(x)
    constraint3 = -d12_min + (x[0] - x[1])
    constraint4 = d12_max - (x[0] - x[1])
    constraint5 = -d23_min + (x[1] - x[2])
    constraint6 = d23_max - (x[1] - x[2])
    return [constraint1, constraint2, constraint3, constraint4, constraint5, constraint6]


def constraint_func_Nangle_3component_winquad(x, lst, d12, d23, ws=None, wl=10.8):
    '''
    三组分温差限制,光照阴影土壤、阴影土壤植被 温差限制
    :param x: 组分能量
    :param ws: 窗口大小
    :param lst: 垂直LST,注意此处为ws*ws*n
    :param d12: 光照土壤与阴影土壤的温差范围,单位是K [min,max]
    :param d23: 阴影土壤与植被的温差范围,单位是K [min,max]
    :return: 约束条件值
    '''
    if ws is not None:
        center = int(ws // 2)
        b = planck(wl, lst[center, center, :])
        lsta = np.nanmean(lst[center, center, :])
    else:
        b = planck(wl, lst)
        lsta = np.nanmean(lst)
    d12_min = planck(wl, lsta + d12[0] / 2) - planck(10.8, lsta - d12[0] / 2)
    d12_max = planck(wl, lsta + d12[1] / 2) - planck(10.8, lsta - d12[1] / 2)
    d23_min = planck(wl, lsta + d23[0] / 2) - planck(10.8, lsta - d23[0] / 2)
    d23_max = planck(wl, lsta + d23[1] / 2) - planck(10.8, lsta - d23[1] / 2)
    constraint1 = np.max(x) - np.max(b)
    constraint2 = np.min(b) - np.min(x)
    constraint3 = -d12_min + (x[0] - x[6])
    constraint4 = d12_max - (x[0] - x[6])
    constraint5 = -d23_min + (x[6] - x[12])
    constraint6 = d23_max - (x[6] - x[12])
    return [constraint1, constraint2, constraint3, constraint4, constraint5, constraint6]


def set_weights(window_size):
    center = window_size // 2
    weights = np.zeros((window_size, window_size))

    for i in range(window_size):
        for j in range(window_size):
            d_ij = np.sqrt((i - center) ** 2 + (j - center) ** 2)
            if d_ij <= window_size:
                weights[i, j] = (1 - (d_ij / window_size) ** 2) ** 2
            else:
                weights[i, j] = 0
    return weights


def set_x0_bnds_Nangle_Mcomponent(lst, n, m, ws=None, wl=10.8):
    '''
    设置初值和边界
    :param lst: LST,注意此处为 (n,)
    :param wl: 波长
    :return: x0,bnds
    '''
    if ws is not None:
        center = int(ws // 2)
        b = planck(wl, lst[center, center, :])
        lsta = np.nanmean(lst[center, center, :])
    else:
        b = planck(wl, lst)
        lsta = np.nanmean(lst)
    # print(lsta,np.nanmax(lst),np.nanmin(lst))
    if m == 2:
        x0 = np.array([max(b) + 5, min(b) - 3])
        bounds = [[planck(wl, lsta - 10), planck(wl, lsta + 40)], [planck(wl, lsta - 10), planck(wl, lsta + 10)]]
    elif m == 3:
        x0 = np.array([max(b) + 10, np.min(b) - 5, np.average(b)])
        bounds = [[planck(wl, lsta - 10), planck(wl, lsta + 40)], [planck(wl, lsta - 30), planck(wl, lsta + 30)],
                  [planck(wl, lsta - 10), planck(wl, lsta + 20)]]
    elif m == 4:
        x0 = np.array([max(b) + 10, np.min(b) - 5, np.average(b), min(b) - 5])
        bounds = [[planck(wl, lsta - 10), planck(wl, lsta + 40)], [planck(wl, lsta - 30), planck(wl, lsta + 30)],
                  [planck(wl, lsta - 20), planck(wl, lsta + 20)], [planck(wl, lsta - 30), planck(wl, lsta + 30)]]
    return x0, bounds


def set_x0_bnds_Nangle_Mcomponent_night(lst, n, m, ws=None, wl=10.8):
    '''
    设置初值和边界
    :param lst: LST,注意此处为 (n,)
    :param wl: 波长
    :return: x0,bnds
    '''
    if ws is not None:
        center = int(ws // 2)
        b = planck(wl, lst[center, center, :])
        lsta = np.nanmean(lst[center, center, :])
    else:
        b = planck(wl, lst)
        lsta = np.nanmean(lst)

    if m == 2:
        x0 = np.array([np.max(b), np.min(b)])
        bounds = [[planck(wl, lsta - 10), planck(wl, lsta + 10)], [planck(wl, lsta - 10), planck(wl, lsta + 10)]]
    elif m == 3:
        x0 = np.array([max(b), np.min(b), np.average(b)])
        bounds = [[planck(wl, lsta - 10), planck(wl, lsta + 10)], [planck(wl, lsta - 10), planck(wl, lsta + 10)],
                  [planck(wl, lsta - 10), planck(wl, lsta + 10)]]
    elif m == 4:
        x0 = np.array([max(b), np.min(b), np.average(b), min(b)])
        bounds = [[planck(wl, lsta - 10), planck(wl, lsta + 40)], [planck(wl, lsta - 30), planck(wl, lsta + 30)],
                  [planck(wl, lsta - 20), planck(wl, lsta + 20)], [planck(wl, lsta - 30), planck(wl, lsta + 30)]]
    return x0, bounds


def set_x0_bnds_Nangle_Mcomponent_winquad(lst, n, m, ws = 5, wl=10.8):
    '''
    生成二次曲面拟合所需的 x0, bounds
    x 结构: [Comp1_coeff(6个), Comp2_coeff(6个), Comp3_coeff(6个)]
    其中每个组分的第0位是常数项(代表平均辐射亮度)，即 x[0], x[6], x[12]
    '''
    if ws is not None:
        center = int(ws // 2)
        b = planck(wl, lst[center, center, :])
        lst[lst<230.0] = np.nan
        lsta = np.nanmean(lst[center, center, :])
    else:
        b = planck(wl, lst)
        lsta = np.nanmean(lst)
    
    coeff_1 = 1
    coeff_2 = 0.5
    if m == 2:
        x0 = np.array([np.max(b), 0,0,0,0,0,np.min(b),0,0,0,0,0])
        bounds = [[planck(wl, lsta - 5), planck(wl, lsta + 15)],
                  [-coeff_1, coeff_1], [-coeff_1, coeff_1],
                  [-coeff_2, coeff_2], [-coeff_2, coeff_2],
                  [-coeff_2, coeff_2],
                   [planck(wl, lsta - 15), planck(wl, lsta + 15)],
                  [-coeff_1, coeff_1], [-coeff_1, coeff_1],
                  [-coeff_2, coeff_2], [-coeff_2, coeff_2],
                  [-coeff_2, coeff_2]]
    elif m == 3:
        x0 = np.array([max(b),0,0,0,0,0, np.min(b),0,0,0,0,0, np.average(b),0,0,0,0,0])
        bounds = [[planck(wl, lsta), planck(wl, lsta + 40)],
                  [-coeff_1, coeff_1], [-coeff_1, coeff_1],
                  [-coeff_2, coeff_2], [-coeff_2, coeff_2],
                  [-coeff_2, coeff_2],
                  [planck(wl, lsta - 20), planck(wl, lsta + 10)],
                  [-coeff_1, coeff_1], [-coeff_1, coeff_1],
                  [-coeff_2, coeff_2], [-coeff_2, coeff_2],
                  [-coeff_2, coeff_2],
                  [planck(wl, lsta - 20), planck(wl, lsta + 10)],
                  [-coeff_1, coeff_1], [-coeff_1, coeff_1],
                  [-coeff_2, coeff_2], [-coeff_2, coeff_2],
                  [-coeff_2, coeff_2]]
    return x0, bounds


'''
ls4t_inv
组分温度反演方法(针对每个像元)
Nangle_Mcomponent_point/window_Constraints
'''
def fitting_Nangle_Mcomponent_point(w, b, n, m, method='ridge'):
    '''
    多角度 多组分 点
    :param w: 有效发射率矩阵, shape (n,m)
    :param b: 亮温矩阵, shape (n,)
    :param n: 角度数
    :param m: 组分数
    :param method: 线性求解方法 ridge、lasso、bayesianridge、ls
    :return: p： 组分能量，shape (m,)
    '''
    w, b = np.asarray(w), np.asarray(b)
    if w.shape[0] != n or w.shape[1] != m:
        print('Error: w shape is not match n angles and m components')
        return -1
    if b.shape[0] != n:
        print('Error: b shape is not match n angles')
        return -1
    if method in ['ridge', 'lasso', 'bayesianridge']:
        p = fitting_unknown_linear_sklearn(b, w, method=method)
    elif method == 'ls':
        p = fitting_unknown_linear_ls(b, w)
    return p

def fitting_Nangle_Mcomponent_window_constant(w, b, n, m, mask, weight, constraints, x0, bounds, window_size=5, method='SLSQP'):
    '''
    多角度 多组分 窗口组分温度固定
    :param w: 有效发射率矩阵 shape(ws,ws,n,m) ws:窗口大小
    :param b: 亮温矩阵 shape(ws,ws,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(ws,ws,n)
    :param n: 角度数
    :param m: 组分数
    :param window_size: 窗口大小
    :param method: 非线性求解方法 BFGS/powell/SLSQP/L-BFGS-B/TNC
    :return: p： 组分能量 shape(nl,ns,m）
    '''
    ws = window_size
    w, b, mask = np.asarray(w), np.asarray(b), np.asarray(mask)
    if w.shape[0] != ws or w.shape[1] != ws or w.shape[2] != n or w.shape[3] != m:
        print('Error: w shape is not match window size * window size *  n angles * m components')
        return -1
    if b.shape[0] != ws or b.shape[1] != ws or b.shape[2] != n:
        print('Error: b shape is not match window size * window size * n angles')
        return -1
    if mask.shape[0] != ws or mask.shape[1] != ws or mask.shape[2] != n:
        print('Error: mask shape is not match window size * window size * n angles')
        return -1

    w = w.reshape(-1, m)
    b = b.reshape(-1)
    # 将mask沿角度维度重复n次
    # mask = np.tile(mask.reshape(-1,1), (1,n)).reshape(-1)
    mask = mask.astype(bool)
    mask = mask.reshape(-1)
    weight = weight.reshape(-1)
    weight = np.tile(weight.reshape(-1, 1), (1, n)).reshape(-1)

    num_val_point = np.sum(mask)
    if num_val_point < 2 * m:
        return np.full((m,), np.nan)

    # 将weights应用于mask区域
    masked_weights = weight[mask]

    def objective_func(x, y, A, xn, weight):
        residuals = np.dot(A, x) - y
        return np.sum(weight * residuals ** 2)

    x = fitting_unknown_nonlinear_min_condition(objective_func,
                                      b[mask],
                                      w[mask],
                                      m,
                                      x0,
                                      bounds,
                                      method=method,
                                      constraints=constraints,
                                      weight=masked_weights)  # 使用关键字参数传入权重
    return x

def fitting_Nangle_Mcomponent_window_quadratic(w, b, n, m, mask,weight, window_size=5):
    '''
    多角度 多组分 窗口内组分温度二次分布
    :param w: 有效发射率矩阵 shape(ws,ws,n,m) ws:窗口大小
    :param b: 亮温矩阵 shape(ws,ws,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(ws,ws,n)
    :param n: 角度数
    :param m: 组分数
    :param window_size: 窗口大小
    :param method: 非线性求解方法 BFGS/powell/SLSQP/L-BFGS-B/TNC
    :return: p： 组分能量 shape(nl,ns,m）
    '''
    ws = window_size
    w, b, mask = np.asarray(w), np.asarray(b), np.asarray(mask)
    weight = np.asarray(weight)

    # --- 基础检查 ---
    if w.shape[0] != ws or w.shape[1] != ws or w.shape[2] != n or w.shape[3] != m:
        print('Error: w shape mismatch')
        return -1
    if b.shape[0] != ws or b.shape[1] != ws or b.shape[2] != n:
        print('Error: b shape mismatch')
        return -1
    if mask.shape[0] != ws or mask.shape[1] != ws or mask.shape[2] != n:
        print('Error: mask shape mismatch')
        return -1

    # --- 展平数据 ---
    # 展平后的顺序：Pixel(0,0)_Ang0, Pixel(0,0)_Ang1, Pixel(0,1)_Ang0...
    w_flat = w.reshape(-1, m)   # (ws*ws*n, m)
    b_flat = b.reshape(-1)      # (ws*ws*n, )
    mask_flat = mask.reshape(-1).astype(bool) # (ws*ws*n, )

    if np.sum(mask_flat) < 6 * m: 
        return np.full((m,), np.nan)

    # --- 构建几何矩阵 X ---
    radius = window_size // 2 
    offsets = np.arange(-radius, radius + 1)
    ns_grid, nl_grid = np.meshgrid(offsets, offsets)
    ns_temp = ns_grid.flatten()
    nl_temp = nl_grid.flatten()
    n0 = np.ones(len(ns_temp))
    
    # x_base: (6, 25)
    x_base = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
    
    # 【修正1】使用 repeat 而不是 tile
    # 这里的 repeat_factor 通常等于 n (角度数)
    # 结果: [x0, x0, x1, x1...] 对应 [p0_a1, p0_a2, p1_a1, p1_a2...]
    x = np.repeat(x_base, n, axis=1) # (6, 50)
    
    # --- 构建 WW 和 BB ---
    part = 6
    ww_list = [w_flat[:, j] * x[i, :] for j in range(m) for i in range(part)]
    ww = np.asarray(ww_list).T
    bb = b_flat

    # --- 求解 ---
    try:
        coeffprior = np.asarray(lstsq(ww[mask_flat], bb[mask_flat], rcond=None)[0])
        # print(coeffprior)
    except Exception:
        return np.full((m,), np.nan)
        
    coeffs = coeffprior.reshape(m, part)
    p_final = coeffs[:,0].reshape(-1)
    # p_distribution = np.dot(coeffs, x_base) # (m, 25)
    
    # # 扩展权重以匹配观测序列 (50,) -> [w0, w0, w1, w1...]
    # w_obs_full = np.repeat(weight.flatten(), n)
    
    # # 应用掩膜：无效观测的权重置为0
    # # 注意：这里直接乘 mask_flat，也就是 0 的位置权重变 0
    # w_obs_valid = w_obs_full * mask_flat # (50, )
    
    # # 聚合回空间维度 (25, )
    # # 将 50 个观测权重变回 25 个像元权重 (对每个像元的 n 个角度求和)
    # w_spatial_agg = w_obs_valid.reshape(-1, n).sum(axis=1) # (25, )
    
    # sum_weights = np.sum(w_spatial_agg)
    # if sum_weights == 0:
    #     return np.full((m,), np.nan)
        
    # w_norm = w_spatial_agg / sum_weights # (25, )
    
    # p_final = np.dot(p_distribution, w_norm)
    
    return p_final

def fitting_Nangle_Mcomponent_window_quadratic(w, b, n, m, mask,weight, window_size=5):
    '''
    多角度 多组分 窗口内组分温度二次分布
    :param w: 有效发射率矩阵 shape(ws,ws,n,m) ws:窗口大小
    :param b: 亮温矩阵 shape(ws,ws,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(ws,ws,n)
    :param n: 角度数
    :param m: 组分数
    :param window_size: 窗口大小
    :return: p： 组分能量 shape(nl,ns,m）
    '''
    ws = window_size
    w, b, mask = np.asarray(w), np.asarray(b), np.asarray(mask)
    weight = np.asarray(weight)

    # --- 基础检查 ---
    if w.shape[0] != ws or w.shape[1] != ws or w.shape[2] != n or w.shape[3] != m:
        print('Error: w shape mismatch')
        return -1
    if b.shape[0] != ws or b.shape[1] != ws or b.shape[2] != n:
        print('Error: b shape mismatch')
        return -1
    if mask.shape[0] != ws or mask.shape[1] != ws or mask.shape[2] != n:
        print('Error: mask shape mismatch')
        return -1

    # --- 展平数据 ---
    # 展平后的顺序：Pixel(0,0)_Ang0, Pixel(0,0)_Ang1, Pixel(0,1)_Ang0...
    w_flat = w.reshape(-1, m)   # (ws*ws*n, m)
    b_flat = b.reshape(-1)      # (ws*ws*n, )
    mask_flat = mask.reshape(-1).astype(bool) # (ws*ws*n, )

    if np.sum(mask_flat) < 6 * m: 
        return np.full((m,), np.nan)

    # --- 构建几何矩阵 X ---
    radius = window_size // 2 
    offsets = np.arange(-radius, radius + 1)
    ns_grid, nl_grid = np.meshgrid(offsets, offsets)
    ns_temp = ns_grid.flatten()
    nl_temp = nl_grid.flatten()
    n0 = np.ones(len(ns_temp))
    
    # x_base: (6, 25)
    x_base = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
    
    # 【修正1】使用 repeat 而不是 tile
    # 这里的 repeat_factor 通常等于 n (角度数)
    # 结果: [x0, x0, x1, x1...] 对应 [p0_a1, p0_a2, p1_a1, p1_a2...]
    x = np.repeat(x_base, n, axis=1) # (6, 50)
    
    # --- 构建 WW 和 BB ---
    part = 6
    ww_list = [w_flat[:, j] * x[i, :] for j in range(m) for i in range(part)]
    ww = np.asarray(ww_list).T
    bb = b_flat

    # --- 求解 ---
    try:
        coeffprior = np.asarray(lstsq(ww[mask_flat], bb[mask_flat], rcond=None)[0])
        # print(coeffprior)
    except Exception:
        return np.full((m,), np.nan)
        
    coeffs = coeffprior.reshape(m, part)
    p_final = coeffs[:,0].reshape(-1)
    # p_distribution = np.dot(coeffs, x_base) # (m, 25)
    
    # # 扩展权重以匹配观测序列 (50,) -> [w0, w0, w1, w1...]
    # w_obs_full = np.repeat(weight.flatten(), n)
    
    # # 应用掩膜：无效观测的权重置为0
    # # 注意：这里直接乘 mask_flat，也就是 0 的位置权重变 0
    # w_obs_valid = w_obs_full * mask_flat # (50, )
    
    # # 聚合回空间维度 (25, )
    # # 将 50 个观测权重变回 25 个像元权重 (对每个像元的 n 个角度求和)
    # w_spatial_agg = w_obs_valid.reshape(-1, n).sum(axis=1) # (25, )
    
    # sum_weights = np.sum(w_spatial_agg)
    # if sum_weights == 0:
    #     return np.full((m,), np.nan)
        
    # w_norm = w_spatial_agg / sum_weights # (25, )
    
    # p_final = np.dot(p_distribution, w_norm)
    
    return p_final

from numba import jit
# --- 新增的 Numba 加速核心函数 ---
@jit(nopython=True, cache=True, fastmath=True)
def numba_objective(x, A, b):
    """
    计算目标函数值：sum((Ax - b)^2)
    """
    # Numba 会自动优化这个矩阵乘法和减法
    residual = A @ x - b
    return np.sum(residual**2)

@jit(nopython=True, cache=True, fastmath=True)
def numba_jacobian(x, A, b):
    """
    计算梯度 (Jacobian)：2 * A.T @ (Ax - b)
    """
    residual = A @ x - b
    # 2 * A.T @ residual
    return 2.0 * A.T @ residual


def fitting_Nangle_Mcomponent_window_quadratic_constraint(w, b, n, m, mask, weight, constraints, x0, bounds, window_size=5, method='SLSQP'):
    '''
    多角度 多组分 窗口内组分温度二次分布 (非线性约束版)
    '''
    ws = window_size
    w, b, mask = np.asarray(w), np.asarray(b), np.asarray(mask)
    weight = np.asarray(weight)

    if w.shape[0] != ws or w.shape[1] != ws or w.shape[2] != n or w.shape[3] != m:
        print('Error: w shape mismatch')
        return -1
    if b.shape[0] != ws or b.shape[1] != ws or b.shape[2] != n:
        print('Error: b shape mismatch')
        return -1
    if mask.shape[0] != ws or mask.shape[1] != ws or mask.shape[2] != n:
        print('Error: mask shape mismatch')
        return -1

    # --- 展平数据 ---
    w_flat = w.reshape(-1, m)   # (ws*ws*n, m)
    b_flat = b.reshape(-1)      # (ws*ws*n, )
    mask_flat = mask.reshape(-1).astype(bool) # (ws*ws*n, )

    if np.sum(mask_flat) < 6 * m: 
        return np.full((m,), np.nan)

    # --- 构建几何矩阵 X ---
    radius = window_size // 2 
    offsets = np.arange(-radius, radius + 1)
    ns_grid, nl_grid = np.meshgrid(offsets, offsets)
    ns_temp = ns_grid.flatten()
    nl_temp = nl_grid.flatten()
    n0 = np.ones(len(ns_temp))
    
    # x_base: (6, 25)
    x_base = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
    
    # x: (6, 25*n) -> (6, ws*ws*n)
    x = np.repeat(x_base, n, axis=1) 
    
    # --- 构建 WW 和 BB (保留原有的列表推导式写法) ---
    part = 6
    # 这里是你原来的核心逻辑，保持不变
    ww_list = [w_flat[:, j] * x[i, :] for j in range(m) for i in range(part)]
    ww = np.asarray(ww_list).T
    bb = b_flat

    # --- 准备求解数据 ---
    # 提取 mask 后的数据，用于传入 objective_func
    ww_masked = ww[mask_flat]
    bb_masked = bb[mask_flat]
    
    # 处理权重：weight是(ws,ws)，需要展平并重复n次以对应观测
    weight_full = np.repeat(weight.flatten(), n)
    weight_masked = weight_full[mask_flat]

    # --- 非线性求解 ---
    def objective_wrapper(x_params):
        return numba_objective(x_params, ww_masked, bb_masked)

    def jacobian_wrapper(x_params):
        return numba_jacobian(x_params, ww_masked, bb_masked)

    try:
        # 使用 scipy.optimize.minimize
        res = minimize(objective_wrapper,     # 调用 Numba 包装器
                       x0, 
                       method=method, 
                       jac=jacobian_wrapper,  # 调用 Numba 包装器
                       bounds=bounds, 
                       constraints=constraints,
                       tol=1e-3) # 建议：适当放宽精度可以大幅减少迭代次数
        coeffprior = res.x
    except Exception as e:
        return np.full((m,), np.nan)

    # --- 结果后处理 (保留你原有的逻辑) ---
    coeffs = coeffprior.reshape(m, part)
    p_distribution = np.dot(coeffs, x_base) # (m, 25)
    
    w_obs_full = np.repeat(weight.flatten(), n)
    w_obs_valid = w_obs_full * mask_flat # (50, )
    
    # 聚合回空间维度 (25, )
    w_spatial_agg = w_obs_valid.reshape(-1, n).sum(axis=1) 
    
    sum_weights = np.sum(w_spatial_agg)
    if sum_weights == 0:
        return np.full((m,), np.nan)
        
    w_norm = w_spatial_agg / sum_weights # (25, )
    p_final = np.dot(p_distribution, w_norm)
    
    return p_final

'''
ls4t_inv
组分温度反演方法(调用)
Nangle_Mcomponent_point/window_Constraints
'''
######################################################################################################
#### from here specific functions
######################################################################################################

def inv_lsct_point(w, b, mask,n , m , wl = 10.8,  method='ridge'):
    '''
    多角度 多组分 点反演
    :param w: 有效发射率矩阵 shape(n,m)
    :param b: 亮温矩阵 shape(n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(n)
    :param n: 角度数
    :param m: 组分数
    :param method: 非线性求解方法 ridge、lasso、bayesianridge、ls
    :return: p： 组分温度 shape(nl,ns,m）
    '''
    if m > n:
        print('Error: m Component num > n Observation num')
        return -1
    nl,ns = w.shape[0], w.shape[1]
    result = np.zeros([nl,ns,m])
    for i in range(nl):
        for j in range(ns):
            if np.sum(mask[i,j,:]) >= m:
                w_point = w[i,j,:,:]
                b_point = b[i,j,:]
                mask_point = mask[i,j,:]

                # --- 求解 ---
                p = fitting_Nangle_Mcomponent_point(w_point[mask_point], b_point[mask_point], n, m, method)
                result[i,j,:] = p
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    return lsct

def inv_lsct2_winconst(w, b, mask, lst,n, m=2, ws=5, wl=10.8,method = 'SLSQP',ifcons = 1):
    '''
    多角度 多组分 窗口反演 BFGS/powell/SLSQP/L-BFGS-B/TNC
    :param w: 有效发射率矩阵 shape(nl,ns,n,m)
    :param b: 亮温矩阵 shape(nl,ns,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(nl,ns,n)
    :param n: 角度数
    :param m: 组分数
    :param ws: 窗口大小
    :param wl: 波长
    :param method: 非线性求解方法 
    :param ifcons: 是否使用温差约束
    :return: p： 组分能量 shape(nl,ns,m）
    '''
    off = ws//2 # 窗口偏移量
    weights = set_weights(ws) # 窗口权重
    nl,ns = w.shape[0], w.shape[1]
    result = np.zeros([nl,ns,m])
    for i in range(off,nl-off):
        for j in range(off,ns-off):
            if np.sum(mask[i,j,:]) >= n:
                w_win = w[i-off:i+off+1,j-off:j+off+1,:,:]
                b_win = b[i-off:i+off+1,j-off:j+off+1,:]
                mask_win = mask[i-off:i+off+1,j-off:j+off+1,:]
                lst_win = lst[i-off:i+off+1,j-off:j+off+1,:]

                if ifcons == 1:
                    # 两组分温差约束
                    d = [-5,30]
                    constraints = {
                        'type': 'ineq',  # 不等式约束
                        'fun': constraint_func_Nangle_2component,
                        'args': (lst_win, d,ws, wl)  # 注意是元组
                    }

                    x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst_win,n,m,ws)

                    p = fitting_Nangle_Mcomponent_window_constant(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method = method)
                    result[i,j,:] = p
                else:
                    n_win = np.sum(mask_win)
                    p = fitting_Nangle_Mcomponent_point(w_win[mask_win], b_win[mask_win], n_win, m, method='ls')
                    result[i,j,:] = p
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    return lsct
   
def inv_lsct3_winconst(w, b, mask, lst, psoil, n, m=3, ws=5, wl=10.8,method = 'SLSQP'):
    '''
    inv_lsct3_winconst 的 Docstring
    :param w: 说明
    :param b: 说明
    :param mask: 说明
    :param lst: 说明
    :param psoil: 说明
    :param n: 说明
    :param m: 说明
    :param ws: 说明
    :param wl: 说明
    :param method: 说明
    :return: 组分温度 Tsl Tsh Ts Tv
    '''
    off = ws//2 # 窗口偏移量
    weights = set_weights(ws) # 窗口权重
    nl,ns = w.shape[0], w.shape[1]
    result = np.zeros([nl,ns,4])
    for i in range(off,nl-off):
        for j in range(off,ns-off):
            if np.sum(mask[i,j,:]) >= n:
                w_win = w[i-off:i+off+1,j-off:j+off+1,:,:]
                b_win = b[i-off:i+off+1,j-off:j+off+1,:]
                mask_win = mask[i-off:i+off+1,j-off:j+off+1,:]
                lst_win = lst[i-off:i+off+1,j-off:j+off+1,:]
                psoil_p = psoil[i,j]

                # 三组分温差约束
                d12 = [5,40] # 光照土壤 阴影土壤温差限制 
                d23 = [-15,15] # 阴影土壤 植被温差限制
                constraints = {
                    'type': 'ineq',  # 不等式约束
                    'fun': constraint_func_Nangle_3component,
                    'args': (lst_win, d12, d23,ws, wl)  # 注意是元组
                }

                lst_win[mask_win==0] = np.nan
                x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst_win,n,m,ws)

                p = fitting_Nangle_Mcomponent_window_constant(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method='SLSQP')
                result[i,j,:2],result[i,j,3] = p[:2],p[2]
                result[i,j,2] = psoil_p * p[0] + (1 - psoil_p) * p[1]
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    return lsct

def inv_lsct2_winquad(w, b, mask,n, m=2, ws=5,wl=10.8,if_bayesian = 1):
    '''
    多角度 多组分 窗口反演 假设窗口内组分温度分布为二次函数
    :param n: 角度数
    :param m: 组分数
    :param ws: 窗口大小
    :param wl: 波长
    :param w: 有效发射率矩阵 shape(nl,ns,n,m)
    :param b: 亮温矩阵 shape(nl,ns,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(nl,ns,n)
    :param if_bayesian: 是否使用贝叶斯联合单点解
    :return: p： 组分温度 shape(nl,ns,m）
    '''
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.05

    off = ws // 2 
    weights = set_weights(ws) 
    nl, ns = w.shape[0], w.shape[1]
    result = np.zeros([nl, ns, m])
    weight = set_weights(ws)
    
    Cm_mat = np.matrix(np.diag([soil_radiance_variance, leaf_radiance_variance]))
    Cm_inv = np.linalg.inv(Cm_mat)

    for i in range(off, nl - off):
        for j in range(off, ns - off):
            if np.sum(mask[i, j, :]) >= n:
                w_win = w[i-off:i+off+1, j-off:j+off+1, :, :]
                b_win = b[i-off:i+off+1, j-off:j+off+1, :]
                mask_win = mask[i-off:i+off+1, j-off:j+off+1, :]
                
                # 初始拟合
                p = fitting_Nangle_Mcomponent_window_quadratic(w_win, b_win, n, m, mask_win, weight, window_size=5)

                if if_bayesian:
                    w_point = w[i,j,:,:]
                    b_point = b[i,j,:]
                    mask_point = mask[i,j,:]

                    w_mat = np.matrix(w_point)
                    b_vec = np.matrix(b_point).T 
                    if b_vec.shape[1] != 1: b_vec = b_vec.T
                    p_vec = np.matrix(p).T
                    
                    Cd_mat = np.matrix(np.diag(np.ones(n)) * sensor_noise)
                    Cd_inv = np.linalg.inv(Cd_mat)
                    
                    # Term 1: (W^T * Cd^-1 * W + Cm^-1)^-1
                    # 形状: (m,n) * (n,n) * (n,m) + (m,m) -> (m,m)
                    posterior_cov_inv = np.transpose(w_mat) * Cd_inv * w_mat + Cm_inv
                    pre = np.linalg.inv(posterior_cov_inv)
                    
                    # Term 2: W^T * Cd^-1 * b + Cm^-1 * p_prior
                    # 形状: (m,n)*(n,n)*(n,1) + (m,m)*(m,1) -> (m,1)
                    term2 = np.transpose(w_mat) * Cd_inv * b_vec + Cm_inv * p_vec
                    
                    # Result: (m,m) * (m,1) -> (m,1)
                    p = pre * term2
                    
                    # 赋值前转回扁平数组，匹配 result 的维度
                    p = np.array(p).flatten()
                result[i, j, :] = p
            else:
                result[i, j, :] = np.nan
                
    lsct = inv_planck(wl, result)
    return lsct
 
def inv_lsct2_winquad_constraint(w, b, mask,lst,n, m=2, ws=5,wl=10.8,if_bayesian = 1):
    '''
    多角度 多组分 窗口反演 假设窗口内组分温度分布为二次函数
    :param n: 角度数
    :param m: 组分数
    :param ws: 窗口大小
    :param wl: 波长
    :param w: 有效发射率矩阵 shape(nl,ns,n,m)
    :param b: 亮温矩阵 shape(nl,ns,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(nl,ns,n)
    :param if_bayesian: 是否使用贝叶斯联合单点解
    :return: p： 组分温度 shape(nl,ns,m）
    '''
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.5

    off = ws // 2 
    weights = set_weights(ws) 
    nl, ns = w.shape[0], w.shape[1]
    result = np.zeros([nl, ns, m])
    weight = set_weights(ws)
    
    inv_Cm = np.linalg.inv(np.diag([soil_radiance_variance, leaf_radiance_variance]))
    inv_Cd = 1.0 / (sensor_noise ** 2)

    for i in range(off, nl - off):
        for j in range(off, ns - off):
            if np.sum(mask[i, j, :]) >= n:
                w_win = w[i-off:i+off+1, j-off:j+off+1, :, :]
                b_win = b[i-off:i+off+1, j-off:j+off+1, :]
                lst_win = lst[i-off:i+off+1, j-off:j+off+1, :]
                mask_win = mask[i-off:i+off+1, j-off:j+off+1, :]
                
                # 初始拟合
                # p = fitting_Nangle_Mcomponent_window_quadratic(w_win, b_win, n, m, mask_win, weight, window_size=5)
                x0,bounds = set_x0_bnds_Nangle_Mcomponent_winquad(lst_win,n,2,ws)
                d12 = [-5,30]
                constraints = {
                    'type': 'ineq',  # 不等式约束
                    'fun': constraint_func_Nangle_2component_winquad,
                    'args': (lst_win, d12,ws, wl)  # 注意是元组
                }
                p = fitting_Nangle_Mcomponent_window_quadratic_constraint(w_win, b_win, n, 2, mask_win, weight,constraints,x0,bounds, window_size=5,method='SLSQP')

                if if_bayesian:
                    valid_idx = mask_win.reshape(-1) == 1
                    w_win = w_win.reshape(-1, m)[valid_idx] # shape变为 (N_valid, m)
                    b_win = b_win.reshape(-1, 1)[valid_idx] # shape变为 (N_valid, 1)

                    if len(b_win) >= m:
                        try:
                            # 公式: (w.T * Cd^-1 * w + Cm^-1)^-1 * (w.T * Cd^-1 * b + Cm^-1 * p)
                            # 部分1: w.T * Cd^-1 * w
                            term1 = (w_win.T @ w_win) * inv_Cd 
                            # 部分2: w.T * Cd^-1 * b
                            term2 = (w_win.T @ b_win) * inv_Cd
                            
                            pre = np.linalg.inv(term1 + inv_Cm)
                            coeff = pre @ (term2 + inv_Cm @ p.reshape(-1, 1))
                            p = coeff.flatten()
                        except np.linalg.LinAlgError:
                            pass # 矩阵不可逆保持原值

                result[i, j, :] = p
            else:
                result[i, j, :] = np.nan
                
    lsct = inv_planck(wl, result)
    return lsct
 
def inv_lsct3_winquad(w2, w3, b, mask, psoil,n = 2, m = 2, ws = 5, wl = 10.8, if_bayesian = 1):
    '''
    两角度 两组分（多像元过程三组分） 窗口反演 假设窗口内组分温度分布为二次函数
    :param n: 角度数
    :param m: 组分数
    :param ws: 窗口大小
    :param wl: 波长
    :param w: 有效发射率矩阵 shape(nl,ns,n,m)
    :param b: 亮温矩阵 shape(nl,ns,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(nl,ns,n)
    :param psoil: 光照土壤占比 (nl,ns)
    :param if_bayesian: 是否使用贝叶斯联合单点解
    :return: p： 组分温度 shape(nl,ns,m）
    '''
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.05

    off = ws // 2 
    weights = set_weights(ws) 
    nl, ns = w3.shape[0], w3.shape[1]

    result = np.zeros([nl, ns, 4])
    weight = set_weights(ws)
    
    inv_Cm = np.linalg.inv(np.diag([soil_radiance_variance, leaf_radiance_variance]))
    inv_Cd = 1.0 / (sensor_noise ** 2)

    for i in range(off, nl - off):
        for j in range(off, ns - off):
            if np.sum(mask[i, j, :]) >= n:
                w_win = w3[i-off:i+off+1, j-off:j+off+1, :, :]
                b_win = b[i-off:i+off+1, j-off:j+off+1, :]
                mask_win = mask[i-off:i+off+1, j-off:j+off+1, :]
                ps = psoil[i,j]
                
                # 初始拟合
                p3 = fitting_Nangle_Mcomponent_window_quadratic(w_win, b_win, n, 3, mask_win, weight, window_size=5)
                p = np.zeros([m])
                p[0] = p3[0] * ps + p3[1] * (1 - ps)
                p[1] = p3[2]
                result[i,j,:2] = p3[:2]  # Tsl Tsh

                if if_bayesian:
                    w_win = w2[i-off:i+off+1, j-off:j+off+1, :, :]
                    valid_idx = mask_win.reshape(-1) == 1
                    w_win = w_win.reshape(-1, m)[valid_idx] # shape变为 (N_valid, m)
                    b_win = b_win.reshape(-1, 1)[valid_idx] # shape变为 (N_valid, 1)

                    if len(b_win) >= m:
                        try:
                            # 公式: (w.T * Cd^-1 * w + Cm^-1)^-1 * (w.T * Cd^-1 * b + Cm^-1 * p)
                            # 部分1: w.T * Cd^-1 * w
                            term1 = (w_win.T @ w_win) * inv_Cd 
                            # 部分2: w.T * Cd^-1 * b
                            term2 = (w_win.T @ b_win) * inv_Cd
                            
                            pre = np.linalg.inv(term1 + inv_Cm)
                            coeff = pre @ (term2 + inv_Cm @ p.reshape(-1, 1))
                            p = coeff.flatten()
                        except np.linalg.LinAlgError:
                            pass # 矩阵不可逆保持原值

                result[i, j, 2:] = p # Ts Tv
            else:
                result[i, j, :] = np.nan
                
    lsct = inv_planck(wl, result)
    return lsct

def inv_lsct3_winquad_constraint(w2, w3, b, mask,lst, psoil,n = 2, m = 2, ws = 5, wl = 10.8, if_bayesian = 1):
    '''
    两角度 两组分（多像元过程三组分） 窗口反演 假设窗口内组分温度分布为二次函数
    :param n: 角度数
    :param m: 组分数
    :param ws: 窗口大小
    :param wl: 波长
    :param w: 有效发射率矩阵 shape(nl,ns,n,m)
    :param b: 亮温矩阵 shape(nl,ns,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(nl,ns,n)
    :param psoil: 光照土壤占比 (nl,ns)
    :param if_bayesian: 是否使用贝叶斯联合单点解
    :return: p： 组分温度 shape(nl,ns,m）
    '''
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.5  # 0.05

    off = ws // 2 
    nl, ns = w3.shape[0], w3.shape[1]

    result = np.zeros([nl, ns, 4])
    weight = set_weights(ws)
    
    inv_Cm = np.linalg.inv(np.diag([soil_radiance_variance, leaf_radiance_variance]))
    inv_Cd = 1.0 / (sensor_noise ** 2)

    for i in range(off, nl - off):
        for j in range(off, ns - off):
            if np.sum(mask[i, j, :]) >= n:
                w_win = w3[i-off:i+off+1, j-off:j+off+1, :, :]
                b_win = b[i-off:i+off+1, j-off:j+off+1, :]
                mask_win = mask[i-off:i+off+1, j-off:j+off+1, :]
                lst_win = lst[i-off:i+off+1,j-off:j+off+1,:]
                ps = psoil[i,j]
                
                # 初始拟合
                # p30 = fitting_Nangle_Mcomponent_window_quadratic(w_win, b_win, n, 3, mask_win, weight, window_size=5)

                x0,bounds = set_x0_bnds_Nangle_Mcomponent_winquad(lst_win,n,3,ws)

                # 三组分温差约束
                d12 = [5,40] # 光照土壤 阴影土壤温差限制 
                d23 = [-15,15] # 阴影土壤 植被温差限制
                constraints = {
                    'type': 'ineq',  # 不等式约束
                    'fun': constraint_func_Nangle_3component_winquad,
                    'args': (lst_win, d12, d23,ws, wl)  # 注意是元组
                }

                p3 = fitting_Nangle_Mcomponent_window_quadratic_constraint(w_win, b_win, n, 3, mask_win, weight,constraints,x0,bounds, window_size=5,method='SLSQP')
                p = np.zeros([m])
                p[0] = p3[0] * ps + p3[1] * (1 - ps)
                p[1] = p3[2]
                result[i,j,:2] = p3[:2]  # Tsl Tsh

                if if_bayesian:
                    w_win = w2[i-off:i+off+1, j-off:j+off+1, :, :]
                    valid_idx = mask_win.reshape(-1) == 1
                    w_win = w_win.reshape(-1, m)[valid_idx] # shape变为 (N_valid, m)
                    b_win = b_win.reshape(-1, 1)[valid_idx] # shape变为 (N_valid, 1)

                    if len(b_win) >= m:
                        try:
                            # 公式: (w.T * Cd^-1 * w + Cm^-1)^-1 * (w.T * Cd^-1 * b + Cm^-1 * p)
                            # 部分1: w.T * Cd^-1 * w
                            term1 = (w_win.T @ w_win) * inv_Cd 
                            # 部分2: w.T * Cd^-1 * b
                            term2 = (w_win.T @ b_win) * inv_Cd
                            
                            pre = np.linalg.inv(term1 + inv_Cm)
                            coeff = pre @ (term2 + inv_Cm @ p.reshape(-1, 1))
                            p = coeff.flatten()
                        except np.linalg.LinAlgError:
                            pass # 矩阵不可逆保持原值

                result[i, j, 2:] = p # Ts Tv
            else:
                result[i, j, :] = np.nan
                
    lsct = inv_planck(wl, result)
    return lsct


### old version:
def lsct2_inv(wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine,ns = 1024):
    wl = 10.8
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.10
    number_component = 3
    number_angle = 3
    number_value_threshold = 12
    result = np.zeros([3, ns])

    ###
    off_inv = 2
    off_inv2 = 0

    for kk in range(off_inv, ns-off_inv):


        maskk = maskLine[2, kk]
        if maskk == 0: continue

        ns1 = kk - off_inv
        ns2 = kk + off_inv + 1

        w1 = wNLine[:,:, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,:, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))

        bb1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        bb2 = (np.reshape(radOLine[:, ns1:ns2], -1))



        mask = np.reshape(maskLine[:, ns1:ns2],-1)
        ind = (mask==1) * (np.isnan(w1[0,:])==0)

        num_val_point = np.sum(ind)
        if (num_val_point < number_value_threshold): continue

        ### w1 for nadir and w2 for oblique
        ns_temp = np.asarray([-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
        nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
        part = 6

        n0 = np.ones(len(ns_temp))
        x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
        w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
        w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

        ww = np.hstack((w11[:, ind], w22[:, ind]))
        bb = np.hstack((bb1[ind], bb2[ind]))

        ###############################################
        ### least-square method
        ###############################################
        ww = np.transpose(ww)

        coeffprior = fitting_unknown_linear_sklearn(bb,ww,method='ridge')
        # print(kk)
        # coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ###############################################
        ### Bayes method with priori information
        ###############################################
        # bbb = sorted(b)
        # halfpoint = np.int(num_point / 2)
        # rleaf = np.average(bbb[0])
        # rsoil = np.average(bbb[1])
        # coeffprior = np.transpose(np.matrix([rsoil, 0, 0, 0, 0, 0, rleaf, 0, 0, 0, 0, 0]))
        # bb = np.transpose(np.matrix(bb))
        # ww = np.transpose(ww)
        # Cd = np.matrix(np.diag(np.ones(num_point * 2)) * Cdvaluep)
        # Cm = np.matrix(np.diag(np.ones(2 * part)))
        # Cm[0, 0] = 15.0
        # Cm[part, part] = 10.0
        # pre = np.linalg.inv(np.transpose(ww) * np.linalg.inv(Cd) * ww + np.linalg.inv(Cm))
        # ctprior = pre * (np.transpose(ww) * np.linalg.inv(Cd) * bb + np.linalg.inv(Cm) * coeffprior)

        #################################################
        ### first result without averaging information
        #################################################
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ################################################
        ### first reult with averaing information
        ################################################
        offcenter = np.int(((2 * off_inv + 1) * (2 * off_inv + 1) - 1) / 2)
        fd = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
        fd = np.reshape(fd, -1) * 1.0

        coeffprior = np.asarray(coeffprior)
        ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
        ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
        ct3 = np.asarray([np.sum(coeffprior[2 * part:3 * part] * x[:part, j]) for j in range(25)])
        indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                 (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold) * \
                 (ct3 > radiance_min_threshold) * (ct3 < radiance_max_threshold)
        apoint = np.sum(indnew)
        if (apoint <= 1):
            cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
            cd2 = np.sum(coeffprior[part:2 * part] * x[:, offcenter])
            cd3 = np.sum(coeffprior[2 * part:3 * part] * x[:, offcenter])
            ctprior = np.transpose(np.matrix([cd1, cd2, cd3]))
        else:
            fd[indnew] = fd[indnew] / np.sum(fd[indnew])

            # inver-distance weight but not used
            # bb0 = bb1[offcenter]
            # fdnew = np.zeros(25)
            # dismax = max(abs(bb1[indnew] - bb0))
            # if dismax != 0:
            #     fdnew[indnew] = 1.0 - abs(1.0 * bb1[indnew] - bb0) / dismax
            # else:
            #     fdnew[:] = 1
            # fdnew[indnew] = fdnew[indnew] / np.sum(fdnew[indnew])
            # fd[indnew] = (fdnew[indnew] * fd[indnew]) / np.sum(fdnew[indnew] * fd[indnew])

            cd1new = np.sum(ct1[indnew] * fd[indnew])
            cd2new = np.sum(ct2[indnew] * fd[indnew])
            cd3new = np.sum(ct3[indnew] * fd[indnew])
            ctprior = np.transpose(np.matrix([cd1new, cd2new, cd3new]))
        component_temperature = inv_planck(wl, ctprior)
        #################################################
        ### second result by combining one-point result
        #################################################

        ns1 = kk - off_inv2
        ns2 = kk + off_inv2 + 1
        # k22 = np.uint16(kk / 2)
        w1 = wNLine[:, 2, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,2, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        w3 = wALine[:,2, ns1:ns2]
        w3 = np.asarray(np.reshape(w3, (number_component, -1)))

        b1 = np.reshape(radNLine[2, ns1:ns2], -1)
        b2 = np.reshape(radOLine[2, ns1:ns2], -1)
        b3 = np.reshape(radAhiLine[2, ns1:ns2], -1)
        w = np.hstack((w1, w2, w3))
        b = np.hstack((b1, b2, b3))
        w = np.transpose(w)

        #################################################
        ### least-squared method
        #################################################
        # coeffprior = np.asarray(lstsq(w, b))[0]

        #################################################
        ### Bayes method
        #################################################

        w = np.matrix(w)
        b = np.matrix(b)
        b = np.transpose(b)

        Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
        Cm = np.diag([soil_radiance_variance, soil_radiance_variance, leaf_radiance_variance])
        pre = np.linalg.inv(w * Cm * np.transpose(w) + Cd)
        coeff = ctprior + (Cm * np.transpose(w) * pre) * (b - w * ctprior)

        # coeff = ctprior + Cm * w.H * (
        #     lsqr(w * Cm * w.H + Cd, b - w * ctprior, iter_lim=400)[0]
        # )
        component_radiance = np.asarray(coeff)

        if (np.min(component_radiance) < radiance_min_threshold): continue
        if (np.max(component_radiance) > radiance_max_threshold): continue

        component_temperature = inv_planck(wl, component_radiance)
        # rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
        # temperature_soil = inv_planck(wl, rad_soil)

        result[:, kk] = [component_temperature[0], component_temperature[1], component_temperature[2]]

    # result[result < temperature_min_threshold] = default_nan_temperature
    # result[result > temperature_max_threshold] = default_nan_temperature

    return result

def lsct3_inv(wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine,ns = 1024):
    wl = 10.8
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.10
    number_component = 3
    number_angle = 3
    number_value_threshold = 12
    result = np.zeros([3, ns])

    ###
    off_inv = 2
    off_inv2 = 0

    for kk in range(off_inv, ns-off_inv):


        maskk = maskLine[2, kk]
        if maskk == 0: continue

        ns1 = kk - off_inv
        ns2 = kk + off_inv + 1

        w1 = wNLine[:,:, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,:, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))

        bb1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        bb2 = (np.reshape(radOLine[:, ns1:ns2], -1))



        mask = np.reshape(maskLine[:, ns1:ns2],-1)
        ind = (mask==1) * (np.isnan(w1[0,:])==0)

        num_val_point = np.sum(ind)
        if (num_val_point < number_value_threshold): continue

        ### w1 for nadir and w2 for oblique
        ns_temp = np.asarray([-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
        nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
        part = 6

        n0 = np.ones(len(ns_temp))
        x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
        w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
        w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

        ww = np.hstack((w11[:, ind], w22[:, ind]))
        bb = np.hstack((bb1[ind], bb2[ind]))

        ###############################################
        ### least-square method
        ###############################################
        ww = np.transpose(ww)

        coeffprior = fitting_unknown_linear_sklearn(bb,ww,method='ridge')
        # coeffprior = fitting_unknown_linear_sparse(bb,ww)

        # print(kk)
        # coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ###############################################
        ### Bayes method with priori information
        ###############################################
        # bbb = sorted(b)
        # halfpoint = np.int(num_point / 2)
        # rleaf = np.average(bbb[0])
        # rsoil = np.average(bbb[1])
        # coeffprior = np.transpose(np.matrix([rsoil, 0, 0, 0, 0, 0, rleaf, 0, 0, 0, 0, 0]))
        # bb = np.transpose(np.matrix(bb))
        # ww = np.transpose(ww)
        # Cd = np.matrix(np.diag(np.ones(num_point * 2)) * Cdvaluep)
        # Cm = np.matrix(np.diag(np.ones(2 * part)))
        # Cm[0, 0] = 15.0
        # Cm[part, part] = 10.0
        # pre = np.linalg.inv(np.transpose(ww) * np.linalg.inv(Cd) * ww + np.linalg.inv(Cm))
        # ctprior = pre * (np.transpose(ww) * np.linalg.inv(Cd) * bb + np.linalg.inv(Cm) * coeffprior)

        #################################################
        ### first result without averaging information
        #################################################
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ################################################
        ### first reult with averaing information
        ################################################
        offcenter = np.int(((2 * off_inv + 1) * (2 * off_inv + 1) - 1) / 2)
        fd = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
        fd = np.reshape(fd, -1) * 1.0

        coeffprior = np.asarray(coeffprior)
        ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
        ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
        ct3 = np.asarray([np.sum(coeffprior[2 * part:3 * part] * x[:part, j]) for j in range(25)])
        indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                 (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold) * \
                 (ct3 > radiance_min_threshold) * (ct3 < radiance_max_threshold)
        apoint = np.sum(indnew)
        if (apoint <= 1):
            cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
            cd2 = np.sum(coeffprior[part:2 * part] * x[:, offcenter])
            cd3 = np.sum(coeffprior[2 * part:3 * part] * x[:, offcenter])
            ctprior = np.transpose(np.matrix([cd1, cd2, cd3]))
        else:
            fd[indnew] = fd[indnew] / np.sum(fd[indnew])

            # inver-distance weight but not used
            # bb0 = bb1[offcenter]
            # fdnew = np.zeros(25)
            # dismax = max(abs(bb1[indnew] - bb0))
            # if dismax != 0:
            #     fdnew[indnew] = 1.0 - abs(1.0 * bb1[indnew] - bb0) / dismax
            # else:
            #     fdnew[:] = 1
            # fdnew[indnew] = fdnew[indnew] / np.sum(fdnew[indnew])
            # fd[indnew] = (fdnew[indnew] * fd[indnew]) / np.sum(fdnew[indnew] * fd[indnew])

            cd1new = np.sum(ct1[indnew] * fd[indnew])
            cd2new = np.sum(ct2[indnew] * fd[indnew])
            cd3new = np.sum(ct3[indnew] * fd[indnew])
            ctprior = np.transpose(np.matrix([cd1new, cd2new, cd3new]))
        component_temperature = inv_planck(wl, ctprior)
        #################################################
        ### second result by combining one-point result
        #################################################

        ns1 = kk - off_inv2
        ns2 = kk + off_inv2 + 1
        # k22 = np.uint16(kk / 2)
        w1 = wNLine[:, 2, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,2, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        w3 = wALine[:,2, ns1:ns2]
        w3 = np.asarray(np.reshape(w3, (number_component, -1)))

        b1 = np.reshape(radNLine[2, ns1:ns2], -1)
        b2 = np.reshape(radOLine[2, ns1:ns2], -1)
        b3 = np.reshape(radAhiLine[2, ns1:ns2], -1)
        w = np.hstack((w1, w2, w3))
        b = np.hstack((b1, b2, b3))
        w = np.transpose(w)

        #################################################
        ### least-squared method
        #################################################
        # coeffprior = np.asarray(lstsq(w, b))[0]

        #################################################
        ### Bayes method
        #################################################

        w = np.matrix(w)
        b = np.matrix(b)
        b = np.transpose(b)

        Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
        Cm = np.diag([soil_radiance_variance, soil_radiance_variance, leaf_radiance_variance])
        pre = np.linalg.inv(w * Cm * np.transpose(w) + Cd)
        coeff = ctprior + (Cm * np.transpose(w) * pre) * (b - w * ctprior)

        # coeff = ctprior + Cm * w.H * (
        #     lsqr(w * Cm * w.H + Cd, b - w * ctprior, iter_lim=400)[0]
        # )
        component_radiance = np.asarray(coeff)

        if (np.min(component_radiance) < radiance_min_threshold): continue
        if (np.max(component_radiance) > radiance_max_threshold): continue

        component_temperature = inv_planck(wl, component_radiance)
        # rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
        # temperature_soil = inv_planck(wl, rad_soil)

        result[:, kk] = [component_temperature[0], component_temperature[1], component_temperature[2]]

    # result[result < temperature_min_threshold] = default_nan_temperature
    # result[result > temperature_max_threshold] = default_nan_temperature

    return result


'''
util_test
生成测试数据集，验证结果和速度
'''
def _process_block(i_start, i_end, j_start, j_end, Tsl_block, Tsh_block, Tvl_block, Tvh_block,
                   lai_block, hspot, wl, emisS_block, emisV_block, vza_block, sza_block, raa_block, n, m):
    '''generate_hom_Nangle_Mcomponent_mlt 处理单个数据块的辅助函数'''
    block_bt = np.zeros((i_end - i_start, j_end - j_start, n))
    block_w = np.zeros((i_end - i_start, j_end - j_start, n, m))

    for i in range(i_end - i_start):
        for j in range(j_end - j_start):
            block_bt[i, j, :] = sample_hom_bt(
                Tsl_block[i, j], Tsh_block[i, j], Tvl_block[i, j], Tvh_block[i, j],
                lai_block[i, j], hspot, wl, emisS_block[i, j], emisV_block[i, j],
                vza_block[i, j, :], sza_block[i, j, :], raa_block[i, j, :])

            block_w[i, j, :, :] = cal_effective_emissivity_hom(
                lai_block[i, j], hspot, wl, emisS_block[i, j], emisV_block[i, j],
                vza_block[i, j, :], sza_block[i, j, :],
                vza_block[i, j, :] + 180, sza_block[i, j, :] + 180,  # 临时处理方位角
                angle_number=n, component_number=m)

    return block_bt, block_w, (i_start, i_end, j_start, j_end)


def generate_hom_Nangle_Mcomponent_mlt(n, m, nl, ns, Tsl, Tsh, Tvl, Tvh, lai, hspot, wl, emisS, emisV, vza, sza, vaa,
                                       saa, ifmlt):
    '''
    生成均值假设下的区域多角度数据集,加入多线程以加速计算
    :param n: 角度数
    :param m: 组分数
    :param nl: 行数
    :param ns: 列数
    :param Tsl: 光照土壤温度 nl*ns
    :param Tsh: 阴影土壤温度 nl*ns
    :param Tvl: 光照植被温度 nl*ns
    :param Tvh: 阴影植被温度 nl*ns
    :param lai: 叶面积指数 nl*ns
    :param hspot: 热点参数 float
    :param wl: 波长 float
    :param emisS: 土壤发射率 nl*ns
    :param emisV: 植被发射率 nl*ns
    :param vza: 观测天顶角 nl*ns*n
    :param sza: 太阳天顶角 nl*ns*n
    :param vaa: 观测方位角 n*nl*ns
    :param saa: 太阳方位角 n*nl*ns
    :param ifmlt: 是否使用多线程加速
    :return: bt(nl*ns*n),w(nl*ns*n*m)
    '''
    if nl * ns == 1:  # 数量如果小就不用多线程
        Tsl, Tsh, Tvl, Tvh = float(Tsl), float(Tsh), float(Tvl), float(Tvh)
        lai, hspot, wl, emisS, emisV = float(lai), float(hspot), float(wl), float(emisS), float(emisV)
        vza, sza, vaa, saa = np.reshape(vza, -1), np.reshape(sza, -1), np.reshape(vaa, -1), np.reshape(saa, -1)
        bt = sample_hom_bt(Tsl, Tsh, Tvl, Tvh, lai, hspot, wl, emisS, emisV, vza, sza, np.abs(vaa - saa))
        w = cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vza, sza, vaa, saa, n,
                                         m)
        return bt.reshape(n), w.reshape(n, m)

    if not ifmlt:
        bt = np.zeros([nl, ns, n])
        w = np.zeros([nl, ns, n, m])
        for i in range(nl):
            for j in range(ns):
                bt[i, j, :] = sample_hom_bt(Tsl[i, j], Tsh[i, j], Tvl[i, j], Tvh[i, j],
                                            lai[i, j], hspot,
                                            wl,
                                            emisS[i, j], emisV[i, j],
                                            vza[i, j, :], sza[i, j, :], np.abs(vaa[i, j, :] - saa[i, j, :]))
                w[i, j, :, :] = cal_effective_emissivity_hom(lai[i, j], hspot, wl, emisS[i, j], emisV[i, j],
                                                             vza[i, j, :], sza[i, j, :],
                                                             vaa[i, j, :], saa[i, j, :], n,
                                                             m)
    if ifmlt:
        # 分块处理优化 - 将大图像分成多个块并行处理
        block_size = 256  # 每个块的大小，可根据实际调整
        num_blocks_i = (nl + block_size - 1) // block_size
        num_blocks_j = (ns + block_size - 1) // block_size

        # 创建块索引和参数元组
        block_params = []
        for i in range(num_blocks_i):
            for j in range(num_blocks_j):
                i_start = i * block_size
                i_end = min((i + 1) * block_size, nl)
                j_start = j * block_size
                j_end = min((j + 1) * block_size, ns)
                block_params.append((
                    i_start, i_end, j_start, j_end,
                    Tsl[i_start:i_end, j_start:j_end],
                    Tsh[i_start:i_end, j_start:j_end],
                    Tvl[i_start:i_end, j_start:j_end],
                    Tvh[i_start:i_end, j_start:j_end],
                    lai[i_start:i_end, j_start:j_end],
                    hspot, wl,
                    emisS[i_start:i_end, j_start:j_end],
                    emisV[i_start:i_end, j_start:j_end],
                    vza[i_start:i_end, j_start:j_end, :],
                    sza[i_start:i_end, j_start:j_end, :],
                    np.abs(vaa[i_start:i_end, j_start:j_end, :] - saa[i_start:i_end, j_start:j_end, :]),
                    n, m
                ))

        # 使用更大的chunksize减少任务切换开销
        with Pool(processes=cpu_count(), maxtasksperchild=4) as pool:
            results = pool.starmap(_process_block, block_params,
                                   chunksize=max(1, len(block_params) // (cpu_count() * 4)))

        # 合并结果
        bt = np.zeros((nl, ns, n))
        w = np.zeros((nl, ns, n, m))
        for block_bt, block_w, (i_s, i_e, j_s, j_e) in results:
            bt[i_s:i_e, j_s:j_e, :] = block_bt
            w[i_s:i_e, j_s:j_e, :, :] = block_w
    return bt, w