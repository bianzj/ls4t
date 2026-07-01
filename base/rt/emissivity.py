import numpy as np
import scipy.integrate as sci
from base.rt.gap import *
from base.rt.hotspot import *
from base.rt.scatter import *
import matplotlib.pyplot as plt


def emissivity_direct(Pcom,Ecom):
    if len(np.array(Pcom).shape) ==1:
        number_component = np.size(Ecom)
        number_angle = np.size(Pcom[0])
        # Pcomnew = np.zeros([number_component,number_angle])
        Pcomnew = []
        Pcomnew_sum = 0
        for k in range(number_component):
            Pcomtemp = Pcom[k]
            Pcomnew.append(Pcomtemp * Ecom[k])
            if np.size(Pcomtemp) > number_angle:
                Pcomnew_sum_temp = np.sum(Pcomtemp * Ecom[k],axis=0)
            else:
                Pcomnew_sum_temp = Pcomtemp * Ecom[k]
            Pcomnew_sum = Pcomnew_sum + Pcomnew_sum_temp
    elif len(np.array(Pcom).shape) ==2: # 4 * n
        Pcom = np.array(Pcom)
        Pcom[Pcom<0] = 0
        Pcom = np.nan_to_num(Pcom)
        Ecom = np.nan_to_num(Ecom)
        # 对应元素相乘
        Pcomnew = Pcom.reshape(4,-1) * Ecom.reshape(4,-1)
        # Pcomnew = Pcom * Ecom
        Pcomnew_sum = np.sum(Pcomnew, axis=0)
    elif len(np.array(Pcom).shape) ==3: # nl*ns *4
        Pcom = np.array(Pcom)
        Pcom[Pcom<0] = 0
        Pcom = np.nan_to_num(Pcom)
        Ecom = np.nan_to_num(Ecom)
        # 对应元素相乘
        # Pcomnew = Pcom.reshape(4,-1) * Ecom.reshape(4,-1)
        Pcomnew = Pcom * Ecom
        Pcomnew_sum = np.sum(Pcomnew, axis=0)
    return Pcomnew,np.asarray(Pcomnew_sum)



def emissivity_scatter_analytical(lai, emis_l, emis_s, vza, sza):
    '''
    组分有效发射率，组分观测比例*组分发射率 + 多次散射项
    :param lai:  叶面积指数
    :param Psoil:  土壤观测比例
    :param Pleaf:  叶片观测比例
    :param Psoil_sunlit:  光照土壤观测比例
    :param Pleaf_sunlit:  光照叶片观测比例
    :param emis_l: 叶片发射率
    :param emis_s: 土壤发射率
    :param vza:    观测天顶角
    :param sza:    太阳天顶角
    :return:
    '''

    refl_s = 1-emis_s
    refl_l = 1-emis_l
    Mleaf_sunlit, Mleaf_shaded = multiple_scattering_analytical_sunlit(
        lai, vza, sza, refl_s, refl_l)
    if len(vza.shape) == 1:
        number_angle = np.size(vza)
        eemis_ss = np.zeros(number_angle)
        eemis_sh = np.zeros(number_angle)
        eemis_ls =  Mleaf_sunlit
        eemis_lh =  Mleaf_shaded
        eemis_sum = eemis_lh + eemis_ls + eemis_sh + eemis_ss
        eemis = np.asarray([eemis_ss,eemis_sh,eemis_ls,eemis_lh])
    elif len(vza.shape) == 2:
        eemis_ss = np.zeros(vza.shape)
        eemis_sh = np.zeros(vza.shape)
        eemis_ls =  Mleaf_sunlit
        eemis_lh =  Mleaf_shaded
        eemis_sum = eemis_lh + eemis_ls + eemis_sh + eemis_ss
        eemis = np.asarray([eemis_ss,eemis_sh,eemis_ls,eemis_lh])
    return eemis,eemis_sum



