import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from base.util_lsct import *
import numpy as np

nl, ns = 2,2
# lai = np.random.uniform(0.1, 5.0, size=(nl, ns))
# emisS = np.random.uniform(0.9, 0.97, size=(nl, ns))  # 土壤发射率
# emisV = np.random.uniform(0.93, 0.97, size=(nl, ns))  # 植被发射率
# vza1 = np.random.uniform(0, 30, size=(nl, ns))  # 观测天顶角
# vaa1 = np.random.uniform(0, 360, size=(nl, ns))  # 观测方位角
# vza2 = np.random.uniform(54, 56, size=(nl, ns))
# vaa2 = np.random.uniform(0, 360, size=(nl, ns))
# sza = np.random.uniform(0, 70, size=(nl, ns))  # 太阳天顶角
# saa = np.random.uniform(0, 360, size=(nl, ns))  # 太阳方位角

lai = np.array([[1,2],[3,4]])
emisS = np.array([[0.95,0.95],[0.95,0.95]])
emisV =np.array([[0.97,0.97],[0.97,0.97]])
vza = np.array([[1,2],[3,4]])
sza = np.array([[1,2],[3,4]])
raa = np.array([[1,2],[3,4]])

Tsl = 315
Tsh = 300
Tvl = 303
Tvh = 298

hspot = 0.2
wavelength = 10.8

bt = sample_hom_bt(315, 300, 303, 298, lai[1, 1], 0.2, 10.8, emisS[1, 1], emisV[1, 1], [vza[1, 1]],
                                    [sza[1, 1]], [raa[1, 1]])

bt_ = sample_hom_bt(315, 300, 303, 298, lai.reshape(-1), 0.2, 10.8, emisS.reshape(-1), emisV.reshape(-1), vza.reshape(-1),
                                    sza.reshape(-1), raa.reshape(-1))
# bt__ = sample_hom_bt(315, 300, 303, 298, np.array(lai.reshape(-1)), 0.2, 10.8, np.array(emisS.reshape(-1)), np.array(emisV.reshape(-1)), np.array(vza1.reshape(-1)),
#                                     np.array(sza.reshape(-1)), raa.reshape(-1))
print(multiple_scattering_analytical_sunlit(lai[1, 1],vza[1, 1],sza[1, 1],1-emisS[1, 1],1-emisV[1, 1]))
print(multiple_scattering_analytical_sunlit(lai,vza,sza,1-emisS,1-emisV))
print(bt,bt_)