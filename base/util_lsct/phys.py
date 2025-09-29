import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from base.util_lsct.packages import *
from base.util_constant import *


'''
lsct_phy
物理公式(注意与rt中planck的wavelength和Ts输入顺序不一样 )
'''

def planck(wavelength, Ts):
    '''
    基于planck公式，计算某个波长时候，从温度到辐射的转换
    :param wavelength: 波长，10.5
    :param Ts: 温度，可以是亮温，也可以是摄氏度
    :return: 辐射
    '''
    c1 = planck_c1
    c2 = planck_c2
    if isinstance(Ts * 1.0, float):
        wavelength = float(wavelength)
        Ts = float(Ts)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    else:
        wavelength = float(wavelength)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    return rad

def inv_planck(wavelength, rad):
    '''
    基于planck公式，计算从辐射到亮温的转换
    :param wavelength: 波长,10.5
    :param rad: 辐射
    :return: 亮温 （300）
    '''
    c1 = planck_c1 * 10000
    c2 = planck_c2
    temp = c1 / (rad * np.power((wavelength), 5)) + 1
    Ts = c2 / (wavelength * np.log(temp))
    return Ts