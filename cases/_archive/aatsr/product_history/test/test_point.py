import sys
sys.path.append('/home/hero/code/AATSR_product/')
from util.util_ls4t import *

'''2025.9.9'''
'''点反演测试代码'''

Tsl = 315
Tsh = 300
Tvl = 303
Tvh = 298
hspot = 0.2
lai = 1.5
wavelength = wl = 10.8
emissivity_soil = emisS = 0.92
emissivity_leaf = emisV = 0.98
# vza = [5,55]
# sza = [45,45]
# raa = [45,135]
vza = np.array([5,15,45,65])
sza = np.array([45,45,45,45])
saa = np.array([180,180,180,180])
vaa = np.array([45,135,225,315])
raa = np.abs(vaa-saa)

bt = sample_hom_bt(Tsl, Tsh, Tvl, Tvh,
                   lai,
                   hspot,
                   wavelength,
                   emissivity_soil,
                   emissivity_leaf,
                   vza,
                   sza,
                   raa)
w4 = sample_hom_Emis(lai, hspot, wavelength, emissivity_soil,emissivity_leaf,vza,sza,raa)
print(w4)
w = np.zeros([4,4])
w = w4
# w[0,:] = w4[0,:] + w4[1,:]
# w[1,:] = w4[2,:] + w4[3,:]
# w = cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,component_number=2)
print(bt)
L = planck(wl, bt)
print(w.T)
result = fitting_Nangle_Mcomponent_point(w.T, L, 4,4,method = 'ls')
print(inv_planck(wl, result))