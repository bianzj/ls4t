import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from base.util_lsct.packages import *
from base.util_lsct.forward import sample_hom_Emis, sample_crown_Emis

'''
lsct_emis
计算有效发射率方法
'''

def cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,angle_number,component_number):
    '''
    计算均值假设下冠层的有效发射率
    :param lai: 叶面积指数 float
    :param hspot: 热点参数 float
    :param wl: 波长 float
    :param emisS: 土壤发射率 float
    :param emisV: 植被发射率 float
    :param vza: 观测天顶角 (n,)
    :param sza: 太阳天顶角 (n,)
    :param vaa: 观测方位角 (n,)
    :param saa: 太阳方位角 (n,)
    :param component_number: 组分数量，2，3，4
    :return: w 有效发射率 (n,m)
    '''
    # 获取数组形状 (处理标量输入的情况)
    vza = np.atleast_1d(np.asarray(vza))
    sza = np.atleast_1d(np.asarray(sza))
    vaa = np.atleast_1d(np.asarray(vaa))
    saa = np.atleast_1d(np.asarray(saa))
    w4 = sample_hom_Emis(lai,hspot,wl,emisS,emisV,vza,sza,np.abs(vaa-saa))
    w4 = reshape(w4,(4,angle_number)) # 4*n
    w = np.zeros([component_number, angle_number]) # m*n 后面再转置
    if component_number == 2:
        w[0,:] = w4[0,:] + w4[1,:]
        w[1,:] = w4[2,:] + w4[3,:]
    if component_number == 3:
        w[0:2,:] = w4[0:2,:]
        w[2,:] = w4[2,:] + w4[3,:]
    if component_number == 4:
        w = w4
    return w.T

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