import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cases.slstr.support.util_packages import *
from cases.slstr.support.util_constant import *
'''
util_phy
物理公式
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
    if np.isscalar(Ts):
        if Ts < temperature_threshold:
            Ts = Ts + temperature_zero
        wavelength = np.float64(wavelength)
        Ts = float(Ts)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    else:
        Ts = np.array(Ts, dtype=np.float64)
        Ts[Ts < temperature_threshold] = Ts[Ts < temperature_threshold] + temperature_zero
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

def vapor(T,eap):
    '''
    计算空气的水汽压
    :param T: 空气温度
    :param eap: 湿度
    :return:
    '''
    a = 7.5
    b = 237.3
    es = 6.107*np.power(10,(7.5*T/(b+T)))
    s = es*np.log(10)*a*b/np.power(b+T,2)
    ea = es*eap*0.01
    return ea

def fieldcalibrate(undertemp,overtemp,atmtemp,underemis,overemis,lai,wl = 10.5):
    '''
    计算消除了大气影响后的温度
    :param undertemp: 测量的地面温度
    :param overtemp: 测量的上层温度
    :param atmtemp: 大气等效温度
    :param underemis: 上层发射率
    :param overemis: 下层发射率
    :param lai: lai
    :param wl: 波长
    :return: 消除大气校正后的结果
    '''
    rad_under = planck(wl,undertemp)
    rad_over = planck(wl,overtemp)
    rad_atm = planck(wl,atmtemp)

    fvc = 1-np.exp(-lai*0.5)
    rad_under = (rad_under - (1-underemis)*(fvc*rad_over +(1-fvc)*rad_atm))/underemis
   # rad_over = (rad_over - (1-overemis)*rad_atm)/overemis
    rad_over = (rad_over - (1-overemis)*(fvc*rad_over +(1-fvc)*rad_atm)) / overemis

    result_under = inv_planck(wl,rad_under)
    result_over = inv_planck(wl,rad_over)
    return result_under-273.15,result_over-273.15


def simpleForward(undertemp,overtemp,atmtemp,underemis,overemis,lai,wl = 10.5):
    '''
    收到大气校正影响
    :param undertemp:
    :param overtemp:
    :param atmtemp:
    :param underemis:
    :param overemis:
    :param lai:
    :param wl:
    :return:
    '''
    rad_under = planck(wl, undertemp)
    rad_over = planck(wl, overtemp)
    rad_atm = planck(wl, atmtemp)

    fvc = 1 - np.exp(-lai * 0.5)
    rad_under = (rad_under*underemis + (1 - underemis) * (fvc * rad_over + (1 - fvc) * rad_atm))
    rad_over = (rad_over*overemis + (1 - overemis) * rad_atm) / overemis

    result_under = inv_planck(wl, rad_under)
    result_over = inv_planck(wl, rad_over)
    return result_under - 273.15, result_over - 273.15

