import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *

nl = 10
ns = 10
n = 2
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

w_region = cal_effective_emissivity_hom_region(lai, hspot, wl, emisS, emisV, vza, sza, vaa, saa, n, m)