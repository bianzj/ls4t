import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *

# def cal_effective_emissivity_hom_region(lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,angle_number,component_number,CI = 1.0):
#     '''
#     计算均值假设下冠层的有效发射率,处理区域且多角度输入
#     :param lai: 叶面积指数 nl*ns
#     :param hspot: 热点参数 float
#     :param wl: 波长 float
#     :param emisS: 土壤发射率 nl*ns
#     :param emisV: 植被发射率 nl*ns
#     :param vza: 观测天顶角 nl*ns*n
#     :param sza: 太阳天顶角 nl*ns*n 或 nl*ns
#     :param vaa: 观测方位角 nl*ns*n 
#     :param saa: 太阳方位角 nl*ns*n 或 nl*ns
#     :param component_number: 组分数量，2，3，4
#     :param CI: 聚集指数 float
#     :return: w 有效发射率 nl*ns*n*m
#     '''
#     nl,ns = np.shape(lai) # 区域大小
#     n,m = 1,component_number # 观测角度数量和组分数量
#     if vza.shape != lai.shape:
#          n = np.shape(vza)[2]
#     if sza.shape != vza.shape:
#         sza = np.repeat(sza[:, :, np.newaxis], n, axis=2)
#         saa = np.repeat(saa[:, :, np.newaxis], n, axis=2)
#     vsa = np.abs(vaa - saa)

#     w4 = np.zeros([nl,ns,4,n]) # m*n 后面再转置
#     for ni in range(n):
#         result = sample_hom_Emis(lai,hspot,wl,emisS,emisV,vza[:,:,ni],sza[:,:,ni],vsa[:,:,ni])
#         w4[:,:,:,ni] = result.transpose(1,2,0)
    
#     w = np.zeros([nl,ns, component_number, angle_number]) # m*n 后面再转置
#     if component_number == 2:
#         w[:,:,0,:] = w4[:,:,0,:] + w4[:,:,1,:]
#         w[:,:,1,:] = w4[:,:,2,:] + w4[:,:,3,:]
#     if component_number == 3:
#         w[:,:,0:2,:] = w4[:,:,0:2,:]
#         w[:,:,2,:] = w4[:,:,2,:] + w4[:,:,3,:]
#     if component_number == 4:
#         w = w4
#     return w.transpose(0, 1, 3, 2)

nl = 20
ns = 30
n = 4
m = 2
hspot = 1.0
wl = 10.8
lai = np.random.uniform(0.5, 5.0, size=(nl, ns))
emisS = np.random.uniform(0.92, 0.95, size=(nl, ns))  # 土壤发射率
emisV = np.random.uniform(0.93, 0.97, size=(nl, ns))  # 植被发射率
vza = np.random.uniform(0, 70, size=(nl,ns,n))
vaa = np.random.uniform(0, 360, size=(nl,ns,n))
sza = np.full((nl,ns,n),30)
saa = np.full((nl,ns,n),180)

w_point = np.zeros([nl,ns,n,m])
for i in range(nl):
    for j in range(ns):
        lai0,emisS0,emisV0,vza0,vaa0,sza0,saa0 = lai[i,j],emisS[i,j],emisV[i,j],vza[i,j,:],vaa[i,j,:],sza[i,j],saa[i,j]
        w_point[i,j,:,:] = cal_effective_emissivity_hom(lai0,hspot,wl,emisS0,emisV0,vza0,sza0,vaa0,saa0,n,m)

print(w_point[0,0,:,:])

w_region = cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vza, sza, vaa, saa, n, m)
print(w_region[0,0,:,:])

print(np.mean(w_point-w_region))
