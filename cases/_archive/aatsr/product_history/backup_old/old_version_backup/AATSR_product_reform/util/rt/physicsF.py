
import numpy as np

# def planck(Ts,wavelength=10.8):
#     c1 = 11910.439340652
#     c2 = 14388.291040407
#     if isinstance(Ts * 1.0, float):
#         if (Ts < 100): Ts = Ts + 273.15
#         wavelength = np.float(wavelength)
#         Ts = np.float(Ts)
#         rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
#     else:
#         Ts[Ts < 100] = Ts[Ts < 100] + 273.15
#         wavelength = np.float(wavelength)
#         rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
#     return rad




# def inv_planck(rad, wavelength= 10.8):
#     c1 = 11910.439340652 * 10000
#     c2 = 14388.291040407
#     temp = c1 / (rad * np.power((wavelength), 5)) + 1
#     Ts = c2 / (wavelength * np.log(temp))
#     return Ts


def leaf_inclination_distribution_function(ala):
    '''
    叶倾角分布函数，通过度数ala计算2.5,7.5.。。87.5度的分布概率，总概率的和为1
    :param ala: 角度，度数
    :return: 中间度数，出现概率
    '''

    ### 计算角度步长的中间代表步长

    n = 18
    tx2 = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85]
    tx1 = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90]
    tx2 = np.asarray(tx2)
    tx1 = np.asarray(tx1)
    x = (tx2 + tx1) / 2.0
    tl1 = tx1 * (np.pi / 180.0)
    tl2 = tx2 * (np.pi / 180.0)
    excent = np.exp(-1.6184e-5 * np.power(ala, 3.) + 2.1145e-3 * np.power(ala, 2.0) - 1.2390e-1 * ala + 3.2491)

    freq = np.zeros(n)
    for i in range(n):
        x1 = excent / (np.sqrt(1.0 + excent * excent * np.tan(tl1[i]) * np.tan(tl1[i])))
        x2 = excent / (np.sqrt(1.0 + excent * excent * np.tan(tl2[i]) * np.tan(tl2[i])))
        if (excent == 1):
            freq[i] = abs(np.cos(tl1[i]) - np.cos(tl2[i]))
        else:
            alpha = excent / np.sqrt(abs(1.0 - excent * excent))
            alpha2 = alpha * alpha
            x12 = x1 * x1
            x22 = x2 * x2
            if (excent > 1):
                alpx1 = np.sqrt(alpha2 + x12)
                alpx2 = np.sqrt(alpha2 + x22)
                dum = x1 * alpx1 + alpha2 * np.log(x1 + alpx1)
                freq[i] = abs(dum - (x2 * alpx2 + alpha2 * np.log(x2 + alpx2)))
            else:
                almx1 = np.sqrt(alpha2 - x12)
                almx2 = np.sqrt(alpha2 - x22)
                dum = x1 * almx1 + alpha2 * np.arcsin(x1 / alpha)
                freq[i] = abs(dum - (x2 * almx2 + alpha2 * np.arcsin(x2 / alpha)))
    sum0 = np.sum(freq)
    freq0 = freq / sum0
    return x, freq0


