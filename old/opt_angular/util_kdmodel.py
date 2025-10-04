from util.util import *
from util_kernel import *

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
    c = coeffs[2]
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

def model_LSFRL(coeffs,vza,sza,raa):
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

def model_RossThickRL(coeffs,vza,sza,raa):
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

def model_VinRL(coeffs,vza,sza,raa):
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
    F = (1 - phi * phi) / (1 + phi * phi - 2 * phi * cos(np.pi - g))
    R = 1 + (1 - obs0) / (1 + G)
    return obs0 * M * F * R



