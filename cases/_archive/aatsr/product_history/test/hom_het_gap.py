import sys
import os
import numpy as np
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *

Tsl = 312
Tsh = 297
Tvl = 299
Tvh = 295

r = 1
h = 3
sLAI = 6
hspot = 0.2
emis_s = 0.92
emis_l = 0.98
vza = 0
vaa = 30
sza = 80
raa = 60

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

if __name__ == '__main__':
    for lai in np.arange(0.1, 6.1, 0.5):
        stand = lai / np.pi / r**2 / sLAI
        bt_crown = sample_crown_bt(Tsl, Tsh, Tvl, Tvh, lai, hspot, stand, r, h, 10.8, emis_s, emis_l, [vza], [sza], [raa])
        bt_hom = sample_hom_bt(Tsl, Tsh, Tvl, Tvh, lai, hspot, 10.8, emis_s, emis_l, [vza], [sza], [raa])
        emis_hom = sample_hom_Emis(lai, hspot, 10.8, emis_s, emis_l, [vza], [sza], [raa])
        emis_crown = sample_crown_Emis(lai, hspot, stand,r, h, 10.8, emis_s, emis_l, [vza], [sza], [raa])

        print(f'lai: {lai:.2f}, bt_crown: {bt_crown[0]:.2f}, bt_hom: {bt_hom[0]:.2f}')
        print(f'Delta BT: {bt_crown[0]-bt_hom[0]:.2f}')
        print(f'emis_crown: {emis_crown}')
        print(f'emis_hom: {emis_hom}')