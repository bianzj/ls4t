'''
核驱动模拟拟合
'''
from util.util import *
from util_kernel import *
from scipy.linalg import lstsq
from sklearn.linear_model import Lasso
from sklearn.linear_model import Ridge


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

def cost_kernel_R(x,y,kvol,fhs):
    a = x[0]
    b = x[1]
    c = x[2]
    k = x[3]
    kR = np.exp(-k * fhs)
    mea = y
    mod = a * kvol + b * kR + c
    res = mod - mea
    return np.sum(res * res)

def cost_kernel_RL(x,y,kvol,fhs,fn):
    a = x[0]
    b = x[1]
    c = x[2]
    k = x[3]
    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
    mea = y
    mod = a * kvol + b * kRL + c
    res = mod - mea
    return np.sum(res * res)





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
    F = (1-phi*phi)/(1+phi*phi-2*phi*cos(np.pi-g))
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

def fitting_kernel_RL_min(fun,y,kvol,fhs,fn,x0,bnds,method = 'Powell'):
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





