import numpy as np
import scipy.integrate as sci
from backup_old.old_version_backup.AATSR_product_new.util.rt.gap import *
from backup_old.old_version_backup.AATSR_product_new.util.rt.hotspot import *
from backup_old.old_version_backup.AATSR_product_new.util.rt.scatter import *
import matplotlib.pyplot as plt
from backup_old.old_version_backup.AATSR_product_new.util.rt.emissivity import *


'''
冠层辐射
unit：四组分
individual: 六组分
endmember：八组分
layer：标识，标识其中的上层植被部分是分层计算的
'''


# def radiance_direct(Ecom,Rcom):
#     # number_component = np.size(Rcom)
#     number_component = 4
#     Ecom = np.reshape(Ecom, (4, -1))
#     Rcom = np.reshape(Rcom, (4, -1))
#     number_angle = np.shape(Ecom)[1]
#     # if np.shape(Ecom)[0]== 4:
#     #     number_angle = 1
#     # else:
#     #     number_angle = np.shape(Ecom[0])[0]
#     Rcomnew = np.zeros([number_component,number_angle])
#     for k in range(number_component):
#         Rcomtemp = Rcom[k]
#         Rcomtemp = np.transpose(np.tile(Rcomtemp,[number_angle,1]))
#         Rcomnew[k,:] = np.sum(np.asarray(Ecom[k])*Rcomtemp,axis=0)
#     # Rcomnew = np.asarray([Ecom[k,:]*Rcom[k] for k in range(number_component)])
#     Rcomnew = np.sum(Rcomnew,axis=0)
#     return Rcomnew

def radiance_direct(Ecom,Rcom):
    number_component = np.size(Rcom)
    number_angle = np.shape(Ecom[0])[0]
    Rcomnew = np.zeros([number_component,number_angle])
    for k in range(number_component):
        Rcomtemp = Rcom[k]
        Rcomtemp = np.transpose(np.tile(Rcomtemp,[number_angle,1]))
        Rcomnew[k,:] = np.sum(np.asarray(Ecom[k])*Rcomtemp,axis=0)
    # Rcomnew = np.asarray([Ecom[k,:]*Rcom[k] for k in range(number_component)])
    Rcomnew = np.sum(Rcomnew,axis=0)
    return Rcomnew

def radiance_direct_new(Ecom,Rcom):
    number_component = 4 # 输入是4个温度
    shape = np.shape(Ecom)
    if len(np.shape(Ecom)) == 2: # 二维数组
        number_angle = np.shape(Ecom)[1]
    if len(np.shape(Ecom)) == 3:
        number_angle = np.shape(Ecom)[1] * np.shape(Ecom)[2]
    Rcomnew = np.zeros([number_component,number_angle])
    Rcom = np.reshape(Rcom,[number_component,-1])
    Ecom = np.reshape(Ecom,[number_component,number_angle])
    for k in range(number_component):
        Rcomtemp = Rcom[k]
        if np.size(Rcomtemp) == 1: Rcomtemp = np.reshape(Rcomtemp,[number_angle,1])
        Rcomnew[k,:] = np.asarray(Ecom[k])*Rcomtemp
    Rcomnew = np.sum(Rcomnew,axis=0)
    Rcomnew = np.reshape(Rcomnew,shape[1:])
    return Rcomnew



def radiance_scatter(Ecom,Rcom):
    Ecom =np.asarray(Ecom)
    Rcom = np.asarray(Rcom)
    number_component = np.size(Rcom)
    Rcomnew = np.asarray([Ecom[k,:]*Rcom[k] for k in range(number_component)])
    Rcomnew = np.sum(Rcomnew,axis=0)
    return Rcomnew

def radiance_scatter_new(Ecom,Rcom):
    number_component = 4 # 输入是4个温度
    shape = np.shape(Ecom)
    if len(np.shape(Ecom)) == 2: # 二维数组
        number_angle = np.shape(Ecom)[1]
    if len(np.shape(Ecom)) == 3:
        number_angle = np.shape(Ecom)[1] * np.shape(Ecom)[2]
    Rcomnew = np.zeros([number_component,number_angle])
    Rcom = np.reshape(Rcom,[number_component,-1])
    Ecom = np.reshape(Ecom,[number_component,number_angle])
    for k in range(number_component):
        Rcomtemp = Rcom[k]
        if np.size(Rcomtemp) == 1: Rcomtemp = np.reshape(Rcomtemp,[number_angle,1])
        Rcomnew[k,:] = np.asarray(Ecom[k])*Rcomtemp
    Rcomnew = np.sum(Rcomnew,axis=0)
    Rcomnew = np.reshape(Rcomnew,shape[1:])
    return Rcomnew
