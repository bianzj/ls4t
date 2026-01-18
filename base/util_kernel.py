from base.util_data import *
from base.util_lst import *

'''
各种核驱动的核函数
和dtc函数
'''


'''
组分差异核
'''

def kernel_Vin(vza):
    '''
    Vinnikov emissivity
    :param vza:
    :return: Vin 核值
    '''
    Kvin = 1 - np.cos(np.deg2rad(vza))
    return Kvin

'''
几何光学核，热点核
'''

def kernel_LiDense(vza,sza,raa, h = 2, r = 1, b = 1):
    '''

    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    ind = raa > 180
    raa[ind] = 360 - raa[ind]

    ### 椭球到球体的转换
    vza = np.arctan(b/r * np.tan(np.deg2rad(vza))) * 180 / np.pi
    sza = np.arctan(b / r * np.tan(np.deg2rad(sza))) * 180 / np.pi

    cthetv = np.cos(np.deg2rad(vza))
    sthetv = np.sin(np.deg2rad(vza))
    cthets = np.cos(np.deg2rad(sza))
    sthets = np.sin(np.deg2rad(sza))
    cphivs = np.cos(np.deg2rad(raa))
    sphivs = np.sin(np.deg2rad(raa))
    tgths = np.tan(np.deg2rad(sza))
    tgthv = np.tan(np.deg2rad(vza))

    calpha =cthets * cthetv + sthetv * sthets * cphivs
    DD = np.power(tgths, 2) + np.power(tgthv, 2) - 2 * tgths * tgthv * cphivs
    DD[DD < 0] = 0
    D = np.sqrt(DD)

    cost = h / b  *np.sqrt(D * D + np.power(tgthv * tgths * sphivs, 2)) / (1.0 / cthets + 1.0 / cthetv)
    cost[cost < -1] = -0.999
    cost[cost > 1] = 0.999

    t = np.arccos(cost)
    O = (1 / np.pi) * (t - np.sin(t) * np.cos(t)) * (1.0 / cthets + 1.0 / cthetv)
    Kli = (1 + calpha) * (1.0 / cthets * 1.0 / cthetv) / (1.0 / cthetv + 1 / cthets - O) - 2
    ### 热点消除
    # Kli[sza >= 75] = 0
    return Kli



def kernel_LiSparse(vza, sza, raa, h = 2, r = 1, b = 1):
    '''

    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    ind = raa > 180
    raa[ind] = 360 - raa[ind]

    ### 椭球到球体的转换
    vza = np.arctan(b/r * np.tan(np.deg2rad(vza))) * 180 / np.pi
    sza = np.arctan(b / r * np.tan(np.deg2rad(sza))) * 180 / np.pi

    cthetv = np.cos(np.deg2rad(vza))
    sthetv = np.sin(np.deg2rad(vza))
    cthets = np.cos(np.deg2rad(sza))
    sthets = np.sin(np.deg2rad(sza))
    cphivs = np.cos(np.deg2rad(raa))
    sphivs = np.sin(np.deg2rad(raa))
    tgths = np.tan(np.deg2rad(sza))
    tgthv = np.tan(np.deg2rad(vza))


    DD = np.power(tgths, 2) + np.power(tgthv, 2) - 2 * tgths * tgthv * cphivs
    DD[DD < 0] = 0
    D = np.sqrt(DD)
    cost = h / b * np.sqrt(D * D + np.power(tgthv * tgths * sphivs, 2)) / (1.0 / cthets + 1.0 / cthetv)
    cost[cost < -1] = -0.999
    cost[cost > 1] = 0.999
    calpha = cthetv * cthets + sthetv * sthets * cphivs
    t = np.arccos(cost)
    O = (1 / np.pi) * (t - np.sin(t) * np.cos(t)) * (1.0 / cthets + 1.0 / cthetv)
    Kli = O - 1.0/cthetv - 1.0/cthets + 0.5*(1+calpha) *(1.0/cthets)*(1.0/cthetv)

    ### 热点消除
    # Kli[sza >= 75] = 0

    return Kli


def kernel_Solar(vza,sza,raa):
    '''
    vinnikov solar
    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    ind = raa > 180
    raa[ind] = 360 - raa[ind]
    thetas = np.deg2rad(sza)
    thetaa = np.deg2rad(raa)
    thetav = np.deg2rad(abs(vza))
    kz = np.zeros(np.size(vza))
    kz[:] = 1.0
    ua = np.cos(thetaa)
    uv = np.cos(thetav)
    us = np.cos(thetas)
    vv = np.sin(thetav)
    vs = np.sin(thetas)
    kS = vv*vs*us*ua*np.cos(thetas-thetav)
    return kS


def kernel_RLf(vza,sza,raa):
    '''
    Roujean hotspot angular distance function
    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    tgths = np.tan(np.deg2rad(sza))
    tgthv = np.tan(np.deg2rad(vza))
    cphivs = np.cos(np.deg2rad(raa))
    f = np.sqrt((np.power(tgthv, 2) + np.power(tgths, 2) - 2 * tgths * tgthv * cphivs))
    return f

'''
多次散射核
'''

def kernel_LSF_analytical(vza):
    '''
    一种LSF核的参数化方案
    :param vza: 观测天顶角
    :return: LSF核值
    '''
    ### 这个参数化方案是JL.Roujean 提出的
    cthetv = np.cos(np.deg2rad(vza))
    kLSF = 0.069*cthetv*cthetv-0.215*cthetv+1.176
    return kLSF

def kernel_LSF(vza):
    '''
    LSF核的原始计算方法
    :param vza: 观测天顶角
    :return: LSF核
    '''
    ### 这个方案是Su. 提出的，对hapke的简化，考虑了上层和下层间的差异
    cthetv = np.cos(np.deg2rad(vza))
    kLSF = ((1 + 2 * cthetv) / (np.sqrt(0.96) + 2 * 0.96 * cthetv) - 0.25 * cthetv
            / (1 + 2 * cthetv) + 0.15 * (1 - np.exp(-0.75 / cthetv)))
    return kLSF



def kernel_TLSF(vza,w=0.10):
    '''
    LSF核的原始计算方法
    :param vza: 观测天顶角
    :return: LSF核
    '''
    ### 这个方案是Su. 提出的，对hapke的简化，考虑了上层和下层间的差异
    cthetv = np.cos(np.deg2rad(vza))
    kLSF = ((1 + 2 * cthetv) / (np.sqrt(1-w) + 2 * np.sqrt(1-w) * cthetv) - 0.25 * cthetv
            / (1 + 2 * cthetv))
    return kLSF

def kernel_VLSF(vza,w=0.15):
    '''
    LSF核的原始计算方法
    :param vza: 观测天顶角
    :return: LSF核
    '''
    ### 这个方案是Su. 提出的，对hapke的简化，考虑了上层和下层间的差异
    cthetv = np.cos(np.deg2rad(vza))
    kLSF = ((1 + 2 * cthetv) / (np.sqrt(1-w) + 2 * np.sqrt(1-w) * cthetv) - 0.25 * cthetv
            / (1 + 2 * cthetv))
    return kLSF

def kernel_Thapke(vza,w=0.10,K=1.0):
    '''
    LSF核的原始计算方法
    :param vza: 观测天顶角
    :return: LSF核
    '''
    ### 这个方案是Su. 提出的，对hapke的简化，考虑了上层和下层间的差异
    cthetv = np.cos(np.deg2rad(vza))
    fa = 2*cthetv/K
    ra = np.sqrt(1-w)
    kLSF = ra*(1+fa)/(1+fa*ra)
    return kLSF

def kernel_RossThick(vza, sza, raa):
    '''
    Ross 简化模型，用于多次散射项计算
    :param sza:
    :param vza:
    :param raa:
    :return:
    '''
    ind = raa > 180
    raa[ind] = 360 - raa[ind]
    cthetv = np.cos(np.deg2rad(vza))
    sthetv = np.sin(np.deg2rad(vza))
    cthets = np.cos(np.deg2rad(sza))
    sthets = np.sin(np.deg2rad(sza))
    cphivs = np.cos(np.deg2rad(raa))


    calpha = cthetv * cthets + sthetv * sthets * cphivs
    alpha = np.arccos(calpha)
    salpha = np.sin(alpha)
    Kross = ((np.pi/2.0 - alpha)*calpha + salpha)/(cthetv+cthets)-np.pi/4.0
    return Kross

def kernel_RossThin(vza, sza, raa):
    '''
    Ross 简化模型，用于多次散射项计算
    :param sza:
    :param vza:
    :param raa:
    :return:
    '''
    ind = raa > 180
    raa[ind] = 360 - raa[ind]
    cthetv = np.cos(np.deg2rad(vza))
    sthetv = np.sin(np.deg2rad(vza))
    cthets = np.cos(np.deg2rad(sza))
    sthets = np.sin(np.deg2rad(sza))
    cphivs = np.cos(np.deg2rad(raa))

    calpha = cthetv * cthets + sthetv * sthets * cphivs
    alpha = np.arccos(calpha)
    salpha = np.sin(alpha)
    Kross = ((np.pi / 2.0 - alpha) * calpha + salpha) / (cthetv * cthets) - np.pi / 2.0

    return Kross


'''
kernel combination
'''



def kernel_LSFLiDense(vza,sza,raa):
    '''
    LSF组分温度差 和 Li 热点核
    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    Klsf = kernel_LSF(vza)
    Kli = kernel_LiDense(vza,sza,raa)
    number = np.size(vza)
    Kiso = np.ones(number)
    return Klsf,Kli,Kiso




def kernel_LSFLiDenseRossThick(vza,sza,raa):
    '''
    LSF组分温度差 和 Li 热点核
    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    Klsf = kernel_LSF(vza)
    Kli = kernel_LiDense(vza,sza,raa)
    Kross = kernel_RossThick(vza,sza,raa)
    number = np.size(vza)
    Kiso = np.ones(number)
    return Klsf,Kli,Kross,Kiso



def kernel_LSFLiSparse(vza,sza,raa):
    '''
    LSF 组分差异核 LiSparse 热点核
    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    Klsf = kernel_LSF(vza)
    Kli = kernel_LiSparse(vza,sza,raa)
    number = np.size(vza)
    Kiso = np.ones(number)
    return Klsf,Kli,Kiso

def kernel_RossThickLiSparse(vza,sza,raa):
    '''
    体散射核核几何光学核，分别为Ross和Li
    :param vza:
    :param sza:
    :param raa:
    :return: 体散射核核几何光学核
    '''

    Kvol = kernel_RossThick(vza,sza, raa)
    Kgeo = kernel_LiSparse(vza, sza, raa)
    number = np.size(vza)
    Kiso = np.ones(number)
    return Kvol,Kgeo,Kiso

def kernel_RossThickLiDense(vza,sza,raa):
    '''
    体散射核核几何光学核，分别为Ross和Li
    :param vza:
    :param sza:
    :param raa:
    :return: 体散射核核几何光学核
    '''

    Kvol = kernel_RossThick(vza, sza, raa)
    Kgeo = kernel_LiDense(vza, sza, raa)
    number = np.size(vza)
    Kiso = np.ones(number)
    return Kvol,Kgeo,Kiso

def kernel_VinLiDense(vza,sza,raa):
    '''
    体散射核核几何光学核，分别为Ross和Li
    :param vza:
    :param sza:
    :param raa:
    :return: 体散射核核几何光学核
    '''

    Kcom = kernel_Vin(vza)
    Kgeo = kernel_LiDense(vza, sza, raa)
    number = np.size(vza)
    Kiso = np.ones(number)
    return Kcom,Kgeo,Kiso

def kernel_VinLiSparse(vza,sza,raa):
    '''
    体散射核核几何光学核，分别为Ross和Li
    :param vza:
    :param sza:
    :param raa:
    :return: 体散射核核几何光学核
    '''

    Kcom = kernel_Vin(vza)
    Kgeo = kernel_LiSparse(vza, sza, raa)
    number = np.size(vza)
    Kiso = np.ones(number)
    return Kcom,Kgeo,Kiso

def kernel_LSFRL(vza,sza,raa):
    '''
    LSF and roujean-lagourade
    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    Klsf = kernel_LSF(vza)
    Kf = kernel_RLf(vza,sza,raa)
    Kz = np.zeros(np.size(vza))
    Kz[:] = 1.0
    return Kz,Klsf,Kf


def kernel_VinSolar(vza,sza,raa):
    '''
    Vinnikov original kernel combination
    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    Kcom = kernel_Vin(vza)
    Kf = kernel_Solar(vza,sza,raa)
    Kz = np.zeros(np.size(vza))
    Kz[:] = 1.0
    return Kcom,Kf,Kz


'''
核驱动模拟拟合
'''


'''
进行拟合或反演的时候可以采用线性或非线性的方式
可以是多角度或者多像元的方式进行
一般情况：行代表了不同的角度，列代表不同的像元
xxx 为矩阵
xxx0 为参考矩阵
这里包括2中:
1种是直接，没有后缀
1种是差异，后缀diff
其中直接的多用于可见光、差异的多用于热红外

Kvol:  体散射核
Kgeo: 几何光学核
Kcom: 组分差异核
Kiso: 各向同性核


如果是线性，就直接的进行线性回归；
如果是非线性，则需要在这里进行迭代优化求解
'''

def cost_kernel_VolR(x,y,kvol,fhs):
    a = x[0]
    b = x[1]
    c = x[2]
    k = x[3]
    kR = np.exp(-k * fhs)
    mea = y
    mod = a * kvol + b * kR + c
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_VolRB(x,y,kvol,fhs,fn):
    a = x[0]
    b = x[1]
    c = x[2]
    k = x[3]
    kR = np.exp(-k * fhs)-np.exp(-k*fn)
    mea = y
    mod = a * kvol + b * kR + c
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_VolRL(x,y,kvol,fhs,fn):
    a = x[0]
    b = x[1]
    c = x[2]
    k = x[3]
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mea = y
    mod = a * kvol + b * kRL + c
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_RL(x,y,fhs,fn):
    b = x[0]
    c = x[1]
    k = x[2]
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mea = y
    mod = b * kRL + c
    res = mod - mea
    return np.sum(res * res)


def cost_kernel_RL_dif(x,y,fhs,fn):
    b = x[0]
    k = x[1]
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mea = y
    mod = b * kRL
    res = mod - mea
    return np.sum(res * res)



def cost_kernel_VolR_ab(x,k,y,kvol,fhs,fn):
    a = x[0]
    b = x[1]
    c = x[2]
    kRL = np.exp(-k * fhs)
    mea = y
    mod = a * kvol + b * kRL + c
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_VolR_ab_k(x,a,b,c,y,kvol,fhs,fn):
    k = x[0]

    kRL = (np.exp(-k * fhs))
    mea = y
    mod = a * kvol + b * kRL + c
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_VolRL_ab_k(x,a,b,c,y,kvol,fhs,fn):
    k = x[0]

    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mea = y
    mod = a * kvol + b * kRL + c
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_VolRLEB(x,y,kvol,fhs,fn,ref,refplus):
    a = x[0]
    b = x[1]
    c = x[2]
    k = x[3]
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mea = y
    mod = a *ref* kvol + b *refplus* kRL + c
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_VolRLEB_dif(x,y,kvol,fhs,fn,ref,refplus):
    a = x[0]
    b = x[1]
    k = x[2]
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mea = y
    mod = a *ref* kvol + b *refplus* kRL
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_RLEB_dif(x,y,fhs,fn,ref,refplus):
    b = x[0]
    k = x[1]
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mea = y
    mod =  b *refplus* kRL
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_VolRLEB_dif_ab(x,k,y,kvol,fhs,fn,ref,refplus):
    a = x[0]
    b = x[1]
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mea = y
    mod = a *ref* kvol + b *refplus* kRL
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_VolRLEB_dif_ab_k(x,a,b,y,kvol,fhs,fn,ref,refplus):
    k = x[0]
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mea = y
    mod = a *ref* kvol + b *refplus* kRL
    res = mod - mea
    return np.sum(res * res)


def cost_kernel_VolREB_dif(x,y,kvol,fhs,fn,ref,refplus):
    a = x[0]
    b = x[1]
    k = x[2]
    kRL = np.exp(-k * fhs)
    mea = y
    mod = a *ref* kvol + b *refplus* kRL
    res = mod - mea
    return np.sum(res * res)


def cost_kernel_VolR_dif(x,y,kvol,fhs,fn):
    a = x[0]
    b = x[1]
    k = x[2]
    kRL = np.exp(-k * fhs)-np.exp(-k*fn)
    mea = y
    mod = a * kvol + b * kRL
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_VolREBB_dif(x,y,kvol,fhs,fn,ref,refplus):
    a = x[0]
    b = x[1]
    k = x[2]
    kRL = np.exp(-k * fhs)-np.exp(-k*fn)
    mea = y
    mod = a *ref* kvol + b *refplus* kRL
    res = mod - mea
    return np.sum(res * res)
def cost_kernel_VolREB_dif_ab(x,k,y,kvol,fhs,fn,ref,refplus):
    a = x[0]
    b = x[1]
    kRL = np.exp(-k * fhs)
    mea = y
    mod = a *ref* kvol + b *refplus* kRL
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_VolREB_dif_ab_k(x,a,b,y,kvol,fhs,fn,ref,refplus):
    k = x[0]
    kRL = np.exp(-k * fhs)
    mea = y
    mod = a *ref* kvol + b *refplus* kRL
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_VolRLE_dif(x,lst1,lst2,phi1,phi2,f1,f2,fn,rad):
    a = x[0]
    b = x[1]
    k = x[2]
    # if k ==0: k = 0.0001
    mea = lst1 - lst2
    mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.0001 - np.exp(-k * fn))
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_VolVRLE_dif(x,lst1,lst2,phi1,phi2,f1,f2,fn,ref,rad):
    a = x[0]
    b = x[1]
    k = x[2]
    # if k ==0: k = 0.0001
    mea = lst1 - lst2
    mod = a * ref*(phi1*lst2 - phi2*lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.0001 - np.exp(-k * fn))
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_VolRLELSF_dif(x,lst1,lst2,phi1,phi2,f1,f2,fn,lsf1,lsf2,ref,rad):
    a = x[0]
    b = x[1]
    c = x[2]
    k = x[3]
    # if k ==0: k = 0.0001
    mea = lst1 - lst2
    mod = a *(phi1*lst2 - phi2*lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn)) + c *ref* (lsf1*lst2 - lsf2*lst1)
    res = mod - mea
    return np.sum(res*res)


def cost_kernel_VolRE_dif(x,lst1,lst2,phi1,phi2,f1,f2,fn,rad):
    a = x[0]
    b = x[1]
    k = x[2]
    # if k ==0: k = 0.0001
    mea = lst1 - lst2
    mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2))
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_VolRE_dif_ab(x,lst1,lst2,phi1,phi2,f1,f2,fn,rad):
    a = x[0]
    b = x[1]
    k = 1.0
    # if k ==0: k = 0.0001
    mea = lst1 - lst2
    mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2))
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_VolRE_dif_ab_k(x,k,lst1,lst2,phi1,phi2,f1,f2,fn,rad):
    a = x[0]
    b = x[1]
    # if k ==0: k = 0.0001
    mea = lst1 - lst2
    mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2))
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_VolRLE_dif_ab(x,lst1,lst2,phi1,phi2,f1,f2,fn,rad):
    a = x[0]
    b = x[1]
    k = 1.0
    # if k ==0: k = 0.0001
    mea = lst1 - lst2
    mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn))
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_VolRLE_dif_ab_k(x,k,lst1,lst2,phi1,phi2,f1,f2,fn,rad):
    a = x[0]
    b = x[1]
    # k = 1.0
    # if k ==0: k = 0.0001
    mea = lst1 - lst2
    mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn))
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_VolRE_dif_k(x,a,b,lst1,lst2,phi1,phi2,f1,f2,rad):
    k = x[0]

    mea = lst1 - lst2
    mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2))
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_RossR_dif_k(x,a,b,lst1,lst2,kvol1,kvol2,f1,f2,da,rad):
    k = x[0]

    mea = lst2 - lst1
    mod = a * da * (kvol2-kvol1) + b * rad * (np.exp(-k * f2) - np.exp(-k * f1))
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_RossRL_dif_k(x,a,b,lst1,lst2,kvol1,kvol2,f1,f2,fn,da,rad):
    k = x[0]

    mea = lst2 - lst1
    mod = a * da * (kvol2-kvol1) + b * rad * (np.exp(-k * f2) - np.exp(-k * f1))/(1.0001-np.exp(-k*fn))
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_VolRLE_dif_k(x,a,b,lst1,lst2,phi1,phi2,f1,f2,fn,rad):
    k = x[0]

    mea = lst1 - lst2
    mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn))
    res = mod - mea
    return np.sum(res*res)


def cost_kernel_VolVRE_dif(x,lst1,lst2,phi1,phi2,f1,f2,ref,rad):
    a = x[0]
    b = x[1]
    k = x[2]
    # if k ==0: k = 0.0001
    mea = lst1 - lst2
    mod = a *ref* (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2))
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_Vin(x,lst1,lst2,phi1,phi2):
    a = x[0]
    mea = lst1 - lst2
    mod = a * (phi1 * lst2 - phi2 * lst1)
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_VinV(x,lst1,lst2,phi1,phi2,ref):
    a = x[0]
    mea = lst1 - lst2
    mod = a *ref* (phi1 * lst2 - phi2 * lst1)
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_RLE_dif(x,a,lst1,lst2,phi1,phi2,f1,f2,fn,rad):
    b = x[0]
    k = x[1]
    # if k ==0: k = 0.0001
    mea = lst1 - lst2
    mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn))
    res = mod - mea
    return np.sum(res*res)

# def cost_kernel_RLEB_dif(x,a,lst1,lst2,phi1,phi2,f1,f2,fn,lsf1,lsf2,rad,ref):
#     b = x[0]
#     c = x[1]
#     k = x[2]
#     # if k ==0: k = 0.0001
#     mea = lst1 - lst2
#     mod = a * (phi1 * lst2 - phi2 * lst1) + \
#           b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn)) + \
#           c * ref * (lsf1-lsf2)*100.0
#     res = mod - mea
#     return np.sum(res*res)




def cost_kernel_RLEB2_dif(x,a,b,lst1,lst2,phi1,phi2,f1,f2,fn,rad):
    k = x[0]
    # if k ==0: k = 0.0001
    mea = lst1 - lst2
    mod = a * (phi1 * lst2 - phi2 * lst1) + \
          b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn))
    res = mod - mea
    return np.sum(res*res)

def cost_kernel_RE_dif(x,a,lst1,lst2,phi1,phi2,f1,f2,fn,rad):
    b = x[0]
    k = x[1]
    # if k ==0: k = 0.0001
    mea = lst1 - lst2
    mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2))
    res = mod - mea
    return np.sum(np.abs(res))

def cost_DTC(x, mea,t):
    '''
    DTC 函数
    :param x:未知数
    :param mea: 温度
    :param t: 时间
    :return: 误差
    '''
    T0 = x[0]
    Ta = x[1]
    tm = x[2]
    tsr = x[3]
    omg = 4/3.0*(tm-tsr)
    mod = T0 + Ta*np.cos(np.pi/omg*(t-tm))
    res = mod - mea
    return np.sum(res*res)

def cost_KDTC_RVT(x, mea,pst,vi,bf,tsr,tm,k=1.0):

    T01 = x[0]
    Ta1 = x[1]
    T02 = x[2]
    Ta2 = x[3]

    omg = 4 / 3.0 * (tm - tsr)
    fbf = T02 + Ta2 * np.cos(np.pi / omg * (pst - tm))
    fvi = T01 + Ta1 * np.cos(np.pi / omg * (pst - tm))

    mod = fvi*vi+fbf*bf
    res = mod - mea +fbf*fbf*0.0001 + fvi*fvi*0.0001

    return np.sum(res*res)


def cost_KDTC_DVT(x, mea,pst,vi,bf):

    T01 = x[0]
    Ta1 = x[1]
    T02 = x[2]
    Ta2 = x[3]
    T03 = x[4]
    Ta3 = x[5]
    tm = x[6]
    tsr = x[7]

    omg = 4 / 3.0 * (tm - tsr)
    fbf = T02 + Ta2 * np.cos(np.pi / omg * (pst - tm))
    fvi = T01 + Ta1 * np.cos(np.pi / omg * (pst - tm))
    fiso = T03 + Ta3 * np.cos(np.pi / omg * (pst - tm))

    mod = fvi*vi+fbf*bf+fiso
    res = mod - mea +fbf*fbf*0.0001 + fvi*fvi*0.0001

    return np.sum(res*res)


def cost_RPV(x,obs,sza,vza,raa):
    obs0 = x[0]
    k = x[1]
    phi = x[2]

    ind = raa > 180
    if np.sum(ind)>0:
        raa[ind] = 360 - raa[ind]
    ind = raa < 0
    if np.sum(ind)>0:
        raa[ind] = raa[ind] + 360
    thetas = np.deg2rad(sza)
    thetaa = np.deg2rad(raa)
    thetav = np.deg2rad(abs(vza))
    ua = np.cos(thetaa)
    uv = np.cos(thetav)
    us = np.cos(thetas)
    va = np.sin(thetaa)
    vv = np.sin(thetav)
    vs = np.sin(thetas)
    tv = np.tan(thetav)
    ts = np.tan(thetas)
    cv = 1.0 / uv
    cs = 1.0 / us

    g = np.arccos(uv*us+va*vs*ua)
    G = tv*tv + ts*ts - 2*tv*ts
    M = np.power(uv,k-1)*np.power(us,k-1)/np.power(uv+us,1-k)
    F = (1-phi*phi)/(1+phi*phi-2*phi*np.cos(np.pi-g))
    R = 1+ (1- obs0)/(1+G)
    res = obs - obs0*M*F*R
    return np.sum(res*res)



def fitting_kernel_R_min(fun,y,kvol,fhs,x0,bnds,method = 'Powell'):
    '''
    非线性反演/回归，基于minimize函数，能给初值，也能给边界条件
    :param fun: 函数
    :param y: 因变量
    :param x: 自变量，是个多列数组
    :param x0: 初值
    :param xn: 列数
    :param bnds: 边界
    :param method: 方法，默认为powell，还有slsqp，L-BFGS-B，TNC，
    :return: 回归系数
    '''
    res = minimize(fun, x0,
                   args=(y,kvol,fhs),
                   method=method,
                   bounds=bnds, )
    return res.x

def fitting_kernel_RL_min(fun,y,kvol,fhs,fn,x0,bnds,method = 'slsqp'):
    '''
    非线性反演/回归，基于minimize函数，能给初值，也能给边界条件
    :param fun: 函数
    :param y: 因变量
    :param x: 自变量，是个多列数组
    :param x0: 初值
    :param xn: 列数
    :param bnds: 边界
    :param method: 方法，默认为powell，还有slsqp，L-BFGS-B，TNC，
    :return: 回归系数
    '''
    res = minimize(fun, x0,
                   args=(y,kvol,fhs,fn),
                   method=method,
                   bounds=bnds, )
    return res.x



############################################3
#### forward model
### 正向模拟
###########################################3

def model_Vin(x,vza,coeffa):

    phi = kernel_Vin(vza)
    mod = (phi * coeffa + 1) * x

    return mod

def model_VinLiDense(coeffs,vza,sza,raa):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[3]##############
    Kcom,Kgeo,Kiso = kernel_VinLiDense(vza,sza,raa)
    sim = a * Kcom + b * Kgeo + c * Kiso
    return sim

def model_VinSolar(coeffs,vza,sza,raa):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[2]
    Kcom,Kgeo,Kiso = kernel_VinSolar(vza,sza,raa)
    sim = a * Kcom + b * Kgeo + c * Kiso
    return sim

def model_VinLiSparse(coeffs,vza,sza,raa):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[2]
    Kcom,Kgeo,Kiso = kernel_VinLiSparse(vza,sza,raa)
    sim = a * Kcom + b * Kgeo + c * Kiso
    return sim

def model_LSFLiDense(coeffs,vza,sza,raa):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[2]
    Kcom,Kgeo,Kiso = kernel_LSFLiDense(vza,sza,raa)
    sim = a * Kcom + b * Kgeo + c * Kiso
    return sim

def model_LSFLiDenseRossThick(coeffs,vza,sza,raa):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[2]
    d = coeffs[3]
    Kcom,Kgeo,Kvol,Kiso = kernel_LSFLiDenseRossThick(vza,sza,raa)
    sim = a * Kcom + b * Kgeo + c * Kiso + Kvol * d
    return sim

def model_LSFLiSparse(coeffs,vza,sza,raa):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[2]
    Kcom,Kgeo,Kiso = kernel_LSFLiSparse(vza,sza,raa)
    sim = a * Kcom + b * Kgeo + c * Kiso
    return sim

def model_LSFR(coeffs, vza, sza, raa):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[2]
    k = coeffs[3]
    Kcom= kernel_LSF(vza)
    RLf = kernel_RLf(vza,sza,raa)
    Kgeo = np.exp(-k*RLf)
    number = np.size(vza)
    Kiso = np.ones(number)
    sim = a * Kcom + b * Kgeo + c * Kiso
    return sim

def model_LSFRL(coeffs, vza, sza, raa):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[2]
    k = coeffs[3]
    Kcom= kernel_LSF(vza)
    RLf = kernel_RLf(vza,sza,raa)
    fn = np.tan(np.deg2rad(sza))
    Kgeo = (exp(-k*RLf)- exp(-k*fn))/(1- exp(-k*fn))
    number = np.size(vza)
    Kiso = np.ones(number)
    sim = a * Kcom + b * Kgeo + c * Kiso
    return sim


def model_RossThickR(coeffs, vza, sza, raa):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[2]
    k = coeffs[3]
    Kvol= kernel_RossThick(vza,sza,raa)
    RLf = kernel_RLf(vza,sza,raa)
    Kgeo = np.exp(-k*RLf)
    number = np.size(vza)
    Kiso = np.ones(number)
    sim = a * Kvol + b * Kgeo + c * Kiso
    return sim

def model_RossThickLiSparse(coeffs,vza,sza,raa):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[2]
    Kvol,Kgeo,Kiso = kernel_RossThickLiSparse(vza,sza,raa)
    sim = a * Kvol + b * Kgeo + c * Kiso
    return sim

def model_RossThickLiDense(coeffs,vza,sza,raa):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[2]
    Kvol,Kgeo,Kiso = kernel_RossThickLiDense(vza,sza,raa)
    sim = a * Kvol + b * Kgeo + c * Kiso
    return sim

def model_VinR(coeffs, vza, sza, raa):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[2]
    k = coeffs[3]
    Kcom= kernel_Vin(vza)
    RLf = kernel_RLf(vza,sza,raa)
    Kgeo = np.exp(-k*RLf)
    number = np.size(vza)
    Kiso = np.ones(number)
    sim = a * Kcom + b * Kgeo + c * Kiso
    return sim


def model_RPV(coeffs,sza,vza,raa):
    obs0 = coeffs[0]
    k = coeffs[1]
    phi = coeffs[2]

    ind = raa > 180
    raa[ind] = 360 - raa[ind]
    thetas = np.deg2rad(sza)
    thetaa = np.deg2rad(raa)
    thetav = np.deg2rad(abs(vza))
    ua = np.cos(thetaa)
    uv = np.cos(thetav)
    us = np.cos(thetas)
    va = np.sin(thetaa)
    vv = np.sin(thetav)
    vs = np.sin(thetas)
    tv = np.tan(thetav)
    ts = np.tan(thetas)
    cv = 1.0 / uv
    cs = 1.0 / us

    g = np.arccos(uv * us + va * vs * ua)
    G = tv * tv + ts * ts - 2 * tv * ts
    M = np.power(uv, k - 1) * np.power(us, k - 1) / np.power(uv + us, 1 - k)
    F = (1 - phi * phi) / (1 + phi * phi - 2 * phi * np.cos(np.pi - g))
    R = 1 + (1 - obs0) / (1 + G)
    return obs0 * M * F * R


rd = 3.14159/180.0
def fun_DTC(x, mea,t):

    T0 = x[0]
    Ta = x[1]
    tm = x[2]
    tsr = x[3]

    omg = 4/3.0*(tm-tsr)
    mod = T0 + Ta*np.cos(np.pi/omg*(t-tm))
    res = mod - mea

    return np.sum(res*res)

def fitting_DTC( obs,pst,Tbase = 0):
    '''
    直接进行DTC系数的拟合
    :param obs:
    :param pst:
    :return:
    '''
    x0 = np.asarray([6+Tbase,16,12,6])
    res = fmin(fun_DTC, x0,args=(obs,pst), disp = 0)
    return res

def model_DTC(x,t):
    T0 = x[0]
    Ta = x[1]
    tm = x[2]
    tsr = x[3]

    omg = 4 / 3.0 * (tm - tsr)
    mod = T0 + Ta * np.cos(np.pi / omg * (t - tm))

    return mod


def fun_DTCRL(x, mea,t,fhs,fn):

    T0 = x[0]
    Ta = x[1]
    tm = x[2]
    tsr = x[3]
    a = x[4]
    k = x[5]


    omg = 4/3.0*(tm-tsr)
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mod = T0 + Ta*np.cos(np.pi/omg*(t-tm)) + a*kRL
    res = mod - mea

    return np.sum(res*res)

# def fitting_DTCRL( obs,pst,fhs,fn,Tbase = 0):
#     '''
#     直接进行DTC系数的拟合
#     :param obs:
#     :param pst:
#     :return:
#     '''
#     x0 = np.asarray([6+Tbase,16,14,6,1,0.5])
#     res = fmin(fun_DTCRL, x0,args=(obs,pst,fhs,fn), disp = 0)
#     return res

def fitting_DTCRL( obs,pst,fhs,fn,x0 = np.asarray([6,16,14,6,1,0.5])):
    '''
    直接进行DTC系数的拟合
    :param obs:
    :param pst:
    :return:
    '''

    res = fmin(fun_DTCRL, x0,args=(obs,pst,fhs,fn), disp = 0)
    return res

def model_DTCRL(x,t,fhs,fn):
    T0 = x[0]
    Ta = x[1]
    tm = x[2]
    tsr = x[3]
    a = x[4]
    k = x[5]

    omg = 4/3.0*(tm-tsr)
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mod = T0 + Ta*np.cos(np.pi/omg*(t-tm)) + a*kRL

    return mod

def fun_DTCJRL(x, mea,t,fhs,fn,sr):

    T0 = x[0]
    Ta = x[1]
    tm = x[2]
    tsr = x[3]
    a = x[4]
    k = x[5]


    omg = 4/3.0*(tm-tsr)
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    kRL = np.exp(-k * fhs)
    mod = T0 + Ta*np.cos(np.pi/omg*(t-tm)) + a*sr*kRL
    res = mod - mea

    return np.sum(res*res)+0.00000001*np.sum(x*x)

def fitting_DTCJRL( obs,pst,fhs,fn,sr,x0 = np.asarray([6,16,14,6,1,0.5])):
    '''
    直接进行DTC系数的拟合
    :param obs:
    :param pst:
    :return:
    '''

    res = fmin(fun_DTCJRL, x0,args=(obs,pst,fhs,fn,sr), disp = 0)
    return res

def model_DTCJRL(x,t,fhs,fn,sr):
    T0 = x[0]
    Ta = x[1]
    tm = x[2]
    tsr = x[3]
    a = x[4]
    k = x[5]

    omg = 4/3.0*(tm-tsr)
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    kRL = np.exp(-k * fhs)
    mod = T0 + Ta*np.cos(np.pi/omg*(t-tm)) + a*sr*kRL

    return mod


def cost_kernel_DTCRL(x,y,t,fhs,fn):
    T0 = x[0]
    Ta = x[1]
    tm = x[2]
    tsr = x[3]
    a = x[4]
    k = x[5]

    omg = 4 / 3.0 * (tm - tsr)
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mod = T0 + Ta * np.cos(np.pi / omg * (t - tm)) + a * kRL
    res = mod - y


    return np.sum(res * res) + 0.00000001*np.sum(x*x)

def fitting_kernel_DTCRL_min(fun,y,t,fhs,fn,x0,bnds,method = 'BFGS'):
    '''
    非线性反演/回归，基于minimize函数，能给初值，也能给边界条件
    :param fun: 函数
    :param y: 因变量
    :param x: 自变量，是个多列数组
    :param x0: 初值
    :param xn: 列数
    :param bnds: 边界
    :param method: 方法，默认为powell，还有slsqp，L-BFGS-B，TNC，
    :return: 回归系数
    '''
    res = minimize(fun, x0,
                   args=(y,t,fhs,fn),
                   method=method,
                   bounds=bnds, )

    # res = minimize(fun, x0,
    #                args=(y,t,fhs,fn),
    #                method=method)

    return res.x

def cost_kernel_DTC(x,y,t):
    T0 = x[0]
    Ta = x[1]
    tm = x[2]
    tsr = x[3]


    omg = 4 / 3.0 * (tm - tsr)
    mod = T0 + Ta * np.cos(np.pi / omg * (t - tm))
    res = mod - y


    return np.sum(res * res)

def fitting_kernel_DTC_min(fun,y,t,x0,bnds,method = 'BFGS'):
    '''
    非线性反演/回归，基于minimize函数，能给初值，也能给边界条件
    :param fun: 函数
    :param y: 因变量
    :param x: 自变量，是个多列数组
    :param x0: 初值
    :param xn: 列数
    :param bnds: 边界
    :param method: 方法，默认为powell，还有slsqp，L-BFGS-B，TNC，
    :return: 回归系数
    '''

    res = minimize(fun, x0,
                   args=(y,t),
                   method=method,
                   bounds=bnds, )

    # res = minimize(fun, x0,
    #                args=(y,t),
    #                method=method)
    return res.x



def cost_R(x, mea,fhs):


    a = x[0]
    k = x[1]

    mod = a*np.exp(-k*fhs)
    res = mod - mea

    return np.sum(res*res) + 0.001*np.sum(x*x)

def fitting_R( obs,fhs):
    '''
    直接进行DTC系数的拟合
    :param obs:
    :param pst:
    :return:
    '''
    x0 = np.asarray([0.05,0.5])
    res = fmin(cost_R, x0,args=(obs,fhs), disp = 0)
    return res

def model_R(x,fhs):
    a = x[0]
    k = x[1]

    mod = a * np.exp(-k * fhs)
    return mod


def cost_RL(x, mea,fhs,fn):


    a = x[0]
    k = x[1]
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mod = a*kRL
    res = mod - mea

    return np.sum(res*res)

def fitting_RL( obs,fhs,fn):
    '''
    直接进行DTC系数的拟合
    :param obs:
    :param pst:
    :return:
    '''
    x0 = np.asarray([0.05,0.5])
    res = fmin(cost_RL, x0,args=(obs,fhs,fn), disp = 0)
    return res

def model_RL(x,fhs,fn):
    a = x[0]
    k = x[1]

    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mod = a * kRL

    return mod


def cost_VolR(x, mea,kvol,fhs):


    a = x[0]
    b = x[1]
    k = x[2]

    mod = b*np.exp(-k*fhs) + a*kvol
    res = mod - mea

    return np.sum(res*res) + 0.001*np.sum(x*x)

def fitting_VolR(obs,kvol,fhs):
    '''
    直接进行DTC系数的拟合
    :param obs:
    :param pst:
    :return:
    '''
    x0 = np.asarray([0.05,0.5,0.5])
    res = fmin(cost_VolR, x0,args=(obs,kvol,fhs), disp = 0)
    return res

def model_VolR(x,kvol,fhs):
    a = x[0]
    b = x[1]
    k = x[2]

    mod = b * np.exp(-k * fhs) + a*kvol
    return mod

def cost_VolRL(x, mea,kvol,fhs,fn):


    a = x[0]
    b = x[1]
    k = x[2]
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mod = b*kRL + a*kvol
    res = mod - mea

    return np.sum(res*res) + 0.001*np.sum(x*x)

def fitting_VolRL(obs,kvol,fhs,fn):
    '''
    直接进行DTC系数的拟合
    :param obs:
    :param pst:
    :return:
    '''
    x0 = np.asarray([0.05,0.5,0.5])
    res = fmin(cost_VolRL, x0,args=(obs,kvol,fhs,fn), disp = 0)
    return res

def model_VolRL(x,kvol,fhs,fn):
    a = x[0]
    b = x[1]
    k = x[2]
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mod = b * kRL + a * kvol
    return mod


def fun_DTCR(x, mea,t,fhs):

    T0 = x[0]
    Ta = x[1]
    tm = x[2]
    tsr = x[3]
    a = x[4]
    k = x[5]


    omg = 4/3.0*(tm-tsr)
    kRL = np.exp(-k * fhs)
    mod = T0 + Ta*np.cos(np.pi/omg*(t-tm)) + a*kRL
    res = mod - mea

    return np.sum(res*res)+0.0001*np.sum(x*x)

def fitting_DTCR( obs,pst,fhs, x0 = np.asarray([6,16,14,6,1,0.5])):
    '''
    直接进行DTC系数的拟合
    :param obs:
    :param pst:
    :return:
    '''
    res = fmin(fun_DTCR, x0,args=(obs,pst,fhs), disp = 0)
    return res

def model_DTCR(x,t,fhs):
    T0 = x[0]
    Ta = x[1]
    tm = x[2]
    tsr = x[3]
    a = x[4]
    k = x[5]


    omg = 4/3.0*(tm-tsr)
    kRL = np.exp(-k * fhs)
    mod = T0 + Ta*np.cos(np.pi/omg*(t-tm)) + a*kRL

    return mod


def cost_kernel_DTCR(x,y,t,fhs):
    T0 = x[0]
    Ta = x[1]
    tm = x[2]
    tsr = x[3]
    a = x[4]
    k = x[5]

    omg = 4 / 3.0 * (tm - tsr)
    kRL = np.exp(-k * fhs)
    mod = T0 + Ta * np.cos(np.pi / omg * (t - tm)) + a * kRL
    res = mod - y


    return np.sum(res * res) + 0.0000001*np.sum(x*x)

def fitting_kernel_DTCR_min(fun,y,t,fhs,x0,bnds,method = 'BFGS'):
    '''
    非线性反演/回归，基于minimize函数，能给初值，也能给边界条件
    :param fun: 函数
    :param y: 因变量
    :param x: 自变量，是个多列数组
    :param x0: 初值
    :param xn: 列数
    :param bnds: 边界
    :param method: 方法，默认为powell，还有slsqp，L-BFGS-B，TNC，
    :return: 回归系数
    '''
    res = minimize(fun, x0,
                   args=(y,t,fhs),
                   method=method,
                   bounds=bnds, )

    # res = minimize(fun, x0,
    #                args=(y,t,fhs,fn),
    #                method=method)

    return res.x
