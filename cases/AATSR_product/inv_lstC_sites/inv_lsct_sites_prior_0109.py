import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from cases.AATSR_product.util.util_aatsr import *
import time
import warnings
warnings.filterwarnings("ignore")

'''2025.1.9'''
'''加入td_dif 也就是先验知识来跑'''
'''2026.1.6'''
'''不加多次散射项来跑'''
'''2025.12.4'''
'''补充异温方法和对比'''
'''2025.11.18'''
'''贝叶斯反演'''
'''2025.10.21'''
'''站点切片组分温度反演 python311'''
'''反演两组分/三组分+lai/NDVI结果，并验证'''

soil_radiance_variance = 2.0
leaf_radiance_variance = 1.0
sensor_noise = 0.05

class Homnew(Hom):
    '''
    继承 hom 类，并添加无散射计算功能
    '''
    def run_emis_noscatter(self, ifradiance=0):
        # 这里直接复制你的代码
        el = self.emissivity_leaf
        es = self.emissivity_soil

        vza = self.viewing_zenith_angle
        sza = self.solar_zenith_angle
        vsa = self.relative_azimuth_angle
        lai = self.leaf_area_index
        hspot = self.hspot

        Ecom = np.asarray([es, es, el, el])
        
        Pcom = proportion_bidirectional_hom_one(lai, hspot, vza, sza, vsa)
        Ecom_direct, Ecom_direct_sum = emissivity_direct(Pcom, Ecom)

        emis = Ecom_direct
        emis = np.nan_to_num(emis)
        return emis

def get_planck_slope(rad, wavelength=10.8):
    """
    计算普朗克函数在特定辐射值处的斜率 k = dR/dT,泰勒展开时使用
    用于线性化方程: Rs - Rv = k * (Ts - Tv)
    """
    # 1. 先反演得到该辐射对应的亮温 LST (作为展开点)
    # 直接复用上面的逻辑，或者调用上面的函数
    c1 = 11910.439340652 * 10000
    c2 = 14388.291040407
    
    # 防止 rad 为 0 或负数导致报错
    rad = np.maximum(rad, 1e-6)
    
    term_log = c1 / (rad * np.power(wavelength, 5)) + 1
    T = c2 / (wavelength * np.log(term_log))
    
    # 2. 计算导数 dR/dT
    # 数学推导公式: dR/dT = (c2 * R) / (lambda * T^2) * [ (c1 / (R * lambda^5)) + 1 ] / [ c1 / (R * lambda^5) ]
    # 化简后更稳定的形式: dR/dT = (c2 * R) / (lambda * T^2) * (1 + (R * lambda^5) / c1)
    # 这里利用了恒等式: exp(c2/lambda*T) / (exp(...) - 1) = 1 + 1/(exp(...) - 1) = 1 + R*lam^5/c1
    
    factor = 1 + (rad * np.power(wavelength, 5)) / c1
    slope = (rad * c2) / (wavelength * np.power(T, 2)) * factor
    
    return slope

def sample_hom_Emis(lai, hspot, wavelength, emissivity_soil, emissivity_leaf, vza, sza, raa):
    '''1.initial'''
    hom = Homnew()
    '''2.set variables'''
    hom.set_structure(lai, hspot)
    hom.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    hom.set_angle(vza, sza, raa)
    ''''3.run'''
    # print('no scatter')
    emis = hom.run_emis_noscatter()
    vza[raa == 180] = vza[raa == 180] * -1
    return emis

def cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vza, sza, vaa, saa, n, m, CI=1.0):
    '''
    计算均值假设下冠层的有效发射率，既能处理单点多角度输入又能处理区域输入
    :param lai: 叶面积指数 float 或 nl*ns
    :param hspot: 热点参数 float
    :param wl: 波长 float
    :param emisS: 土壤发射率 float 或 nl*ns
    :param emisV: 植被发射率 float 或 nl*ns
    :param vza: 观测天顶角 (n,) 或 nl*ns*n
    :param sza: 太阳天顶角 (n,)/float 或 nl*ns*n(nl*ns)
    :param vaa: 观测方位角 (n,) 或 nl*ns*n
    :param saa: 太阳方位角 (n,)/float 或 nl*ns*n(nl*ns)
    :param n: 观测角度数量
    :param m: 组分数量，2，3，4
    :param CI: 聚集指数 float
    :return: w 有效发射率 (n,m) 或 nl*ns*n*m
    '''
    # 确保输入为numpy数组
    lai = np.asarray(lai)
    emisS = np.asarray(emisS)
    emisV = np.asarray(emisV)
    vza = np.asarray(vza)
    sza = np.asarray(sza)
    vaa = np.asarray(vaa)
    saa = np.asarray(saa)
    sza[sza >= 90] = 89.9
    soil_radiance_variance = 2.0
    if lai.ndim == 0:  # 标量输入，转换为点输入
        # 点输入处理
        vza = np.atleast_1d(vza)
        sza = np.atleast_1d(sza)
        vaa = np.atleast_1d(vaa)
        saa = np.atleast_1d(saa)
        w4 = sample_hom_Emis(lai, hspot, wl, emisS, emisV, vza, sza, np.abs(vaa - saa))
        w4 = w4.reshape((4, n))  # 4*n
        w = np.zeros([m, n])  # m*n 后面再转置
        if m == 2:
            w[0, :] = w4[0, :] + w4[1, :]
            w[1, :] = w4[2, :] + w4[3, :]
        elif m == 3:
            w[0:2, :] = w4[0:2, :]
            w[2, :] = w4[2, :] + w4[3, :]
        elif m == 4:
            w = w4
        return w.T

    else:  # 区域输入处理
        nl, ns = lai.shape  # 区域大小
        if sza.shape != vza.shape:
            sza = np.repeat(sza[:, :, np.newaxis], n, axis=2)
            saa = np.repeat(saa[:, :, np.newaxis], n, axis=2)
        vsa = np.abs(vaa - saa)
        w4 = np.zeros([nl, ns, 4, n])  # nl*ns*4*n
        for ni in range(n):
            result = sample_hom_Emis(lai, hspot, wl, emisS, emisV,
                                     vza[:, :, ni], sza[:, :, ni], vsa[:, :, ni])
            w4[:, :, :, ni] = result.transpose(1, 2, 0)

        w = np.zeros([nl, ns, m, n])  # nl*ns*m*n

        if m == 2:
            w[:, :, 0, :] = w4[:, :, 0, :] + w4[:, :, 1, :]
            w[:, :, 1, :] = w4[:, :, 2, :] + w4[:, :, 3, :]
        elif m == 3:
            w[:, :, 0:2, :] = w4[:, :, 0:2, :]
            w[:, :, 2, :] = w4[:, :, 2, :] + w4[:, :, 3, :]
        elif m == 4:
            w = w4
        return w.transpose(0, 1, 3, 2)  # nl*ns*n*m

def inv_lsct2_winconst(w, b, mask, lst,n, m=2, ws=5, wl=10.8,method = 'SLSQP',ifcons = 0, ifbayesian = 0):
    '''
    多角度 多组分 窗口反演 BFGS/powell/SLSQP/L-BFGS-B/TNC
    :param w: 有效发射率矩阵 shape(nl,ns,n,m)
    :param b: 亮温矩阵 shape(nl,ns,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(nl,ns,n)
    :param n: 角度数
    :param m: 组分数
    :param ws: 窗口大小
    :param wl: 波长
    :param method: 非线性求解方法 
    :param ifcons: 是否使用温差约束
    :return: p： 组分能量 shape(nl,ns,m）
    '''
    off = ws//2 # 窗口偏移量
    weights = set_weights(ws) # 窗口权重
    nl,ns = w.shape[0], w.shape[1]
    result = np.zeros([nl,ns,m])
    Cm_inv = np.linalg.inv(np.diag([soil_radiance_variance, leaf_radiance_variance]))
    inv_sensor_noise = 1.0 / sensor_noise
    for i in range(off,nl-off):
        for j in range(off,ns-off):
            if np.sum(mask[i,j,:]) >= n:
                w_win = w[i-off:i+off+1,j-off:j+off+1,:,:]
                b_win = b[i-off:i+off+1,j-off:j+off+1,:]
                mask_win = mask[i-off:i+off+1,j-off:j+off+1,:]
                lst_win = lst[i-off:i+off+1,j-off:j+off+1,:]

                if ifcons == 1:
                    # 两组分温差约束
                    d = [-5,30]
                    constraints = {
                        'type': 'ineq',  # 不等式约束
                        'fun': constraint_func_Nangle_2component,
                        'args': (lst_win, d,ws, wl)  # 注意是元组
                    }

                    x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst_win,n,m,ws)

                    p = fitting_Nangle_Mcomponent_window_constant(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method = method)
                    result[i,j,:] = p
                else:
                    n_win = np.sum(mask_win)
                    p = fitting_Nangle_Mcomponent_point(w_win[mask_win], b_win[mask_win], n_win, m, method=method)
                    result[i,j,:] = p

                    if ifbayesian == 1:
                        w_point = w[i, j, :, :]
                        b_point = b[i, j, :]
                        mask_point = mask[i, j, :]
                        w_arr = w_point  # shape (n, m)
                        b_arr = b_point  # shape (n,)
                        p2_arr = p  # shape (m,)

                        KT = w_arr.T
                        KTK = KT @ w_arr
                        posterior_cov_inv = KTK * inv_sensor_noise + Cm_inv

                        KTb = KT @ b_arr
                        term2 = KTb * inv_sensor_noise + Cm_inv @ p2_arr

                        try:
                            p3 = np.linalg.solve(posterior_cov_inv, term2)
                            result[i, j, :] = p3
                        except np.linalg.LinAlgError:
                            result[i, j, :] = np.nan
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    return lsct

def inv_lsct3_winconst(w, b, mask, lst, psoil, n, m=3, ws=5, wl=10.8,method = 'SLSQP',ifcons = 0):
    '''
    inv_lsct3_winconst 的 Docstring
    :param w: 说明
    :param b: 说明
    :param mask: 说明
    :param lst: 说明
    :param psoil: 说明
    :param n: 说明
    :param m: 说明
    :param ws: 说明
    :param wl: 说明
    :param method: 说明
    :return: 组分温度 Tsl Tsh Ts Tv
    '''
    off = ws//2 # 窗口偏移量
    weights = set_weights(ws) # 窗口权重
    nl,ns = w.shape[0], w.shape[1]
    result = np.zeros([nl,ns,4])
    for i in range(off,nl-off):
        for j in range(off,ns-off):
            if np.sum(mask[i,j,:]) >= n:
                w_win = w[i-off:i+off+1,j-off:j+off+1,:,:]
                b_win = b[i-off:i+off+1,j-off:j+off+1,:]
                mask_win = mask[i-off:i+off+1,j-off:j+off+1,:]
                lst_win = lst[i-off:i+off+1,j-off:j+off+1,:]
                psoil_p = psoil[i,j]

                if ifcons == 1:
                    # 三组分温差约束
                    d12 = [5,40] # 光照土壤 阴影土壤温差限制 
                    d23 = [-15,15] # 阴影土壤 植被温差限制
                    constraints = {
                        'type': 'ineq',  # 不等式约束
                        'fun': constraint_func_Nangle_3component,
                        'args': (lst_win, d12, d23,ws, wl)  # 注意是元组
                    }

                    lst_win[mask_win==0] = np.nan
                    x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst_win,n,m,ws)

                    p = fitting_Nangle_Mcomponent_window_constant(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method='SLSQP')
                else:
                    n_win = np.sum(mask_win)
                    p = fitting_Nangle_Mcomponent_point(w_win[mask_win], b_win[mask_win], n_win, m, method='ls')

                result[i,j,:2],result[i,j,3] = p[:2],p[2]
                result[i,j,2] = psoil_p * p[0] + (1 - psoil_p) * p[1]
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    return lsct

def inv_lsct2_winquad_constraint(w, b, mask,lst,n, m=2, ws=5,wl=10.8,if_bayesian = 1,ifcons = 0):
    '''
    多角度 多组分 窗口反演 假设窗口内组分温度分布为二次函数
    :param n: 角度数
    :param m: 组分数
    :param ws: 窗口大小
    :param wl: 波长
    :param w: 有效发射率矩阵 shape(nl,ns,n,m)
    :param b: 亮温矩阵 shape(nl,ns,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(nl,ns,n)
    :param if_bayesian: 是否使用贝叶斯联合单点解
    :return: p： 组分温度 shape(nl,ns,m）
    '''
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.5

    off = ws // 2 
    weights = set_weights(ws) 
    nl, ns = w.shape[0], w.shape[1]
    result = np.zeros([nl, ns, m])
    weight = set_weights(ws)
    
    inv_Cm = np.linalg.inv(np.diag([soil_radiance_variance, leaf_radiance_variance]))
    inv_Cd = 1.0 / (sensor_noise ** 2)

    for i in range(off, nl - off):
        for j in range(off, ns - off):
            if np.sum(mask[i, j, :]) >= n:
                w_win = w[i-off:i+off+1, j-off:j+off+1, :, :]
                b_win = b[i-off:i+off+1, j-off:j+off+1, :]
                lst_win = lst[i-off:i+off+1, j-off:j+off+1, :]
                mask_win = mask[i-off:i+off+1, j-off:j+off+1, :]
                
                if ifcons == 1:
                    # 初始拟合
                    # p = fitting_Nangle_Mcomponent_window_quadratic(w_win, b_win, n, m, mask_win, weight, window_size=5)
                    x0,bounds = set_x0_bnds_Nangle_Mcomponent_winquad(lst_win,n,2,ws)
                    d12 = [-5,30]
                    constraints = {
                        'type': 'ineq',  # 不等式约束
                        'fun': constraint_func_Nangle_2component_winquad,
                        'args': (lst_win, d12,ws, wl)  # 注意是元组
                    }
                    p = fitting_Nangle_Mcomponent_window_quadratic_constraint(w_win, b_win, n, 2, mask_win, weight,constraints,x0,bounds, window_size=5,method='SLSQP')
                else:
                    p = fitting_Nangle_Mcomponent_window_quadratic(w_win, b_win, n, m, mask_win, weight, window_size=5)
                
                if if_bayesian:
                    valid_idx = mask_win.reshape(-1) == 1
                    w_win = w_win.reshape(-1, m)[valid_idx] # shape变为 (N_valid, m)
                    b_win = b_win.reshape(-1, 1)[valid_idx] # shape变为 (N_valid, 1)

                    if len(b_win) >= m:
                        try:
                            # 公式: (w.T * Cd^-1 * w + Cm^-1)^-1 * (w.T * Cd^-1 * b + Cm^-1 * p)
                            # 部分1: w.T * Cd^-1 * w
                            term1 = (w_win.T @ w_win) * inv_Cd 
                            # 部分2: w.T * Cd^-1 * b
                            term2 = (w_win.T @ b_win) * inv_Cd
                            
                            pre = np.linalg.inv(term1 + inv_Cm)
                            coeff = pre @ (term2 + inv_Cm @ p.reshape(-1, 1))
                            p = coeff.flatten()
                        except np.linalg.LinAlgError:
                            pass # 矩阵不可逆保持原值

                result[i, j, :] = p
            else:
                result[i, j, :] = np.nan
                
    lsct = inv_planck(wl, result)
    return lsct

def inv_lsct3_winquad(w2, w3, b, mask, psoil,n = 2, m = 2, ws = 5, wl = 10.8, if_bayesian = 1,ifcons = 0):
    '''
    两角度 两组分（多像元过程三组分） 窗口反演 假设窗口内组分温度分布为二次函数
    :param n: 角度数
    :param m: 组分数
    :param ws: 窗口大小
    :param wl: 波长
    :param w: 有效发射率矩阵 shape(nl,ns,n,m)
    :param b: 亮温矩阵 shape(nl,ns,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(nl,ns,n)
    :param psoil: 光照土壤占比 (nl,ns)
    :param if_bayesian: 是否使用贝叶斯联合单点解
    :return: p： 组分温度 shape(nl,ns,m）
    '''
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.05

    off = ws // 2 
    weights = set_weights(ws) 
    nl, ns = w3.shape[0], w3.shape[1]

    result = np.zeros([nl, ns, 4])
    weight = set_weights(ws)
    
    inv_Cm = np.linalg.inv(np.diag([soil_radiance_variance, leaf_radiance_variance]))
    inv_Cd = 1.0 / (sensor_noise ** 2)

    for i in range(off, nl - off):
        for j in range(off, ns - off):
            if np.sum(mask[i, j, :]) >= n:
                w_win = w3[i-off:i+off+1, j-off:j+off+1, :, :]
                b_win = b[i-off:i+off+1, j-off:j+off+1, :]
                mask_win = mask[i-off:i+off+1, j-off:j+off+1, :]
                ps = psoil[i,j]
                
                # 初始拟合
                p3 = fitting_Nangle_Mcomponent_window_quadratic(w_win, b_win, n, 3, mask_win, weight, window_size=5)
                p = np.zeros([m])
                p[0] = p3[0] * ps + p3[1] * (1 - ps)
                p[1] = p3[2]
                result[i,j,:2] = p3[:2]  # Tsl Tsh

                if if_bayesian:
                    w_win = w2[i-off:i+off+1, j-off:j+off+1, :, :]
                    valid_idx = mask_win.reshape(-1) == 1
                    w_win = w_win.reshape(-1, m)[valid_idx] # shape变为 (N_valid, m)
                    b_win = b_win.reshape(-1, 1)[valid_idx] # shape变为 (N_valid, 1)

                    if len(b_win) >= m:
                        try:
                            # 公式: (w.T * Cd^-1 * w + Cm^-1)^-1 * (w.T * Cd^-1 * b + Cm^-1 * p)
                            # 部分1: w.T * Cd^-1 * w
                            term1 = (w_win.T @ w_win) * inv_Cd 
                            # 部分2: w.T * Cd^-1 * b
                            term2 = (w_win.T @ b_win) * inv_Cd
                            
                            pre = np.linalg.inv(term1 + inv_Cm)
                            coeff = pre @ (term2 + inv_Cm @ p.reshape(-1, 1))
                            p = coeff.flatten()
                        except np.linalg.LinAlgError:
                            pass # 矩阵不可逆保持原值

                result[i, j, 2:] = p # Ts Tv
            else:
                result[i, j, :] = np.nan
                
    lsct = inv_planck(wl, result)
    return lsct

def inv_lsct_point_prior(w, b,td_prior, mask,n , m , wl = 10.8,  method='ridge'):
    '''
    多角度 多组分 点反演
    :param w: 有效发射率矩阵 shape(n,m)
    :param b: 亮温矩阵 shape(n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(n)
    :param n: 角度数
    :param m: 组分数
    :param method: 非线性求解方法 ridge、lasso、bayesianridge、ls
    :return: p： 组分温度 shape(nl,ns,m）
    '''
    if m > n:
        print('Error: m Component num > n Observation num')
        return -1
    nl,ns = w.shape[0], w.shape[1]
    result = np.zeros([nl,ns,m])
    for i in range(nl):
        for j in range(ns):
            if np.sum(mask[i,j,:]) >= m:
                w_point = w[i,j,:,:]
                b_point = b[i,j,:]
                mask_point = mask[i,j,:]
                td_point = td_prior[i,j]
                
                w_point_prior = np.zeros([n+1,m])
                w_point_prior[:-1,:] = w_point
                w_point_prior[-1,:] = [1,-1]

                b_point_prior = np.zeros(n+1)
                b_point_prior[:-1] = b_point
                k = get_planck_slope(np.mean(b_point))
                b_point_prior[-1] = td_point * k

                mask_point_prior = np.zeros(n+1,dtype=bool)
                mask_point_prior[:-1] = mask_point
                mask_point_prior[-1] = True

                # --- 求解 ---
                p = fitting_Nangle_Mcomponent_point(w_point_prior[mask_point_prior], b_point_prior[mask_point_prior], n + 1, m, method)
                result[i,j,:] = p
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    return lsct

def inv_lsct2_winconst_prior(w, b, td_prior, mask, lst,n, m=2, ws=5, wl=10.8,method = 'SLSQP',ifcons = 0):
    '''
    多角度 多组分 窗口反演 BFGS/powell/SLSQP/L-BFGS-B/TNC
    :param w: 有效发射率矩阵 shape(nl,ns,n,m)
    :param b: 亮温矩阵 shape(nl,ns,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(nl,ns,n)
    :param n: 角度数
    :param m: 组分数
    :param ws: 窗口大小
    :param wl: 波长
    :param method: 非线性求解方法 
    :param ifcons: 是否使用温差约束
    :return: p： 组分能量 shape(nl,ns,m）
    '''
    off = ws//2 # 窗口偏移量
    weights = set_weights(ws) # 窗口权重
    nl,ns = w.shape[0], w.shape[1]
    result = np.zeros([nl,ns,m])
    for i in range(off,nl-off):
        for j in range(off,ns-off):
            if np.sum(mask[i,j,:]) >= n:
                w_win = w[i-off:i+off+1,j-off:j+off+1,:,:]
                b_win = b[i-off:i+off+1,j-off:j+off+1,:]
                mask_win = mask[i-off:i+off+1,j-off:j+off+1,:]
                lst_win = lst[i-off:i+off+1,j-off:j+off+1,:]

                w_win_prior = np.zeros([ws,ws,n+1,m])
                w_win_prior[:,:,:n,:] = w_win
                w_win_prior[:,:,-1,:] = [1,-1]
                b_win_prior = np.zeros([ws,ws,n+1])
                b_win_prior[:,:,:n] = b_win
                k = get_planck_slope(np.mean(b_win))
                b_win_prior[:,:,-1] = td_prior[i,j] * k
                mask_win_prior = np.zeros([ws,ws,n+1],dtype=bool)
                mask_win_prior[:,:,:n] = mask_win
                mask_win_prior[:,:,-1] = True

                if ifcons == 1:
                    # 两组分温差约束
                    d = [-5,30]
                    constraints = {
                        'type': 'ineq',  # 不等式约束
                        'fun': constraint_func_Nangle_2component,
                        'args': (lst_win, d,ws, wl)  # 注意是元组
                    }

                    x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst_win,n,m,ws)

                    p = fitting_Nangle_Mcomponent_window_constant(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method = method)
                    result[i,j,:] = p
                else:
                    n_win = np.sum(mask_win_prior)
                    # print(w_win_prior.shape, b_win_prior.shape, mask_win_prior.shape, n_win)
                    p = fitting_Nangle_Mcomponent_point(w_win_prior[mask_win_prior], b_win_prior[mask_win_prior], n_win, m, method=method)
                    result[i,j,:] = p
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    return lsct


if __name__ == '__main__':
    ###  反演参数设置
    n, m, ws = 2, 2, 5 # n 角度， m组分， ws窗口大小
    ndvi_max, ndvi_min, k = 0.87, 0.15, 1 # ndvi 参数
    lst_min, lst_max = 250, 350 # 范围参数
    hspot, wl = 0.5, 10.8 # 结构参数
    # 反演方法
    method_effective_emissivity = 'lai' # lai / ndvi
    method_mpl_pixel = 'winconst' # point / winconst / winquad / prior
    method_solve = 'bayesian' # bayesian / nobayesian / none
    method = 'ls'
    # 反演站点设置
    if_Dahra = 0 # 只反演Dahra站点
    if_PureSites = 0 # 只反演纯站点
    if_AllSites = 0 # 实际无用
    if_daynight = 'all' # day/night/all

    label = 'inv_%01dc_' % m + method_effective_emissivity + '_' + method_mpl_pixel + '_' + method_solve

    # 输入输出位置
    indir_h5_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/0_raw_h5_Ta_td/'
    infile_pure_soil_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/soil_sites.txt'
    infile_pure_veg_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/veg_sites.txt'
    outdir_h5_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/' + label + '/'
    mkdir_if_not_exist(outdir_h5_sites)
    angle_error_file = indir_h5_sites + r'Angle_error.txt'

    siteNames = search_dir_rej(indir_h5_sites,'-', '.txt')
    for i, siteName in enumerate(siteNames):
        if if_Dahra == 1:
            if siteName != 'SN-Dhr': continue
        if if_PureSites == 1:
            soil_sites_list = np.array(read_txt_str(infile_pure_soil_sites,'\n'))[:,0]
            veg_sites_list = np.array(read_txt_str(infile_pure_veg_sites,'\n'))[:,0]
            soil_sites_list = soil_sites_list.tolist()
            soil_sites_list.append('SN-Dhr')
            if siteName not in soil_sites_list and siteName not in veg_sites_list: continue
        print(i,siteName)
        indir_site = indir_h5_sites + siteName + '/'
        outdir_site = outdir_h5_sites + siteName + '/'
        mkdir_if_not_exist(outdir_site)
        fileNames = search_file_rej(indir_site, ['h5'], 'txt')
        fileNames.sort()
        wl = 10.8
        for i, fileName in enumerate(fileNames):
            year = int(fileName.split('_')[1])
            doy = int(fileName.split('_')[2])
            month,day = doy2date(year,doy)
            # if year != 2009: continue
            # if doy < 120: continue
            # if fileName != 'AATSR_2009_150_101541.h5': continue

            ### 0. 读取数据
            print(i,fileName)
            start_time = time.time()
            infile = indir_site + fileName
            outfile = outdir_site + fileName
            if os.path.exists(outfile):
                # os.remove(outfile)
                continue

            ndviN, ndviF = aatsr_read_sites_obs(infile, ifNDVI=1)
            cloN_mask, cloF_mask = aatsr_read_sites_clo(infile)
            lstN,lstF = aatsr_read_sites_lst(infile)
            vzaN,vzaF,vaaN,vaaF,sza,saa = aatsr_read_sites_angle(infile)
            emisS,emisV,type,lai = aatsr_read_sites_emis(infile)
            indx,indy,ref_indx,ref_indy,lat,lon = aatsr_read_sites_loc(infile)
            utc_time = aatsr_read_sites_time(infile)
            td_prior = read_h5py_item(infile,'td_dif')  # 31*31

            # 筛选控制 
            if np.average(sza) > 89: dn = 'night'
            else: dn = 'day'
            if if_daynight != 'all' and if_daynight != dn: 
                print('Pass day/night')
                continue

            if np.average(vzaF) > 60 or np.average(vzaF) < 50:  # 极少部分数据vzaF值异常
                print('Angle error')
                with open(angle_error_file,'a') as f:
                    f.write(siteName + ' ' + fileName + '\n')
                continue
            if np.mean(lstN) == 0: continue
            if lai.shape != (31,31): continue
            if vzaN.shape != (31,31) or vzaF.shape != (31,31): continue

            nl,ns = lstN.shape
            if nl != 31 or ns != 31: continue

            ### 1.计算有效发射率矩阵 w
            off = ws//2
            if method_effective_emissivity == 'lai':
                vza = np.stack((vzaN, vzaF), axis=2)
                vaa = np.stack((vaaN, vaaF), axis=2)
                # ci = [0.8,1.0]
                # w = cal_effective_emissivity_hom_2_CI(lai,hspot, wl, emisS,emisV,vza,sza,vaa,saa,n,m,ci)
                
                w = cal_effective_emissivity_hom(lai,hspot, wl, emisS,emisV,vza,sza,vaa,saa,n,m)
                w2 = cal_effective_emissivity_hom(lai,hspot, wl, emisS,emisV,vza,sza,vaa,saa,n,2) # FVC,后面可能有用

                if m == 3:
                    psoil = cal_psoil_hom(lai,sza)
                cloN_mask = cloN_mask * (lai>0.01)

            elif method_effective_emissivity == 'ndvi':
                fvcN = cal_fvc_from_ndvi(ndviN,ndvi_min,ndvi_max)  # nl*ns
                fvcF = cal_fvc_from_ndvi(ndviF,ndvi_min,ndvi_max)  # nl*ns
                fvcN[cloN_mask == 0] = 0
                fvcF[cloF_mask == 0] = 0
                wN = np.stack([emisS * (1-fvcN), emisV * fvcN], axis=-1)  # 形状: (nl, ns, m)
                wF = np.stack([emisS * (1-fvcF), emisV * fvcF], axis=-1)  # 形状: (nl, ns, m)
                w = np.stack([wN, wF], axis=2) # 形状: (nl, ns, m, 2)
            
            ### 2.计算观测亮度矩阵 b
            lst = np.stack((lstN,lstF),axis=2)
            if method_effective_emissivity == 'lai': # lai反演0
                bN = cal_rad_from_lst(lstN,wl,lai,vzaN,emisS,emisV)
                bF = cal_rad_from_lst(lstF,wl,lai,vzaF,emisS,emisV)
                b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2) # 形状: (nl, ns, m)
            elif method_effective_emissivity == 'ndvi':
                bN = cal_rad_from_lst_fvc(lstN,wl,fvcN,emisS,emisV)
                bF = cal_rad_from_lst_fvc(lstF,wl,fvcF,emisS,emisV)
                b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2)

            ### 3. 求解
            cloN_mask[np.abs(lstN - lstF)>15] = 0
            cloF_mask[np.abs(lstN - lstF)>15] = 0
            mask = np.concatenate([cloN_mask[:,:,np.newaxis], cloF_mask[:,:,np.newaxis]], axis=2)
            if method_mpl_pixel == 'point':
                lsct = inv_lsct_point(w,b,mask,n,m,wl,method='ls')

            elif method_mpl_pixel == 'winconst':
                if m == 2:
                    if method_solve == 'bayesian': if_bayesian = 1
                    else: if_bayesian = 0
                    lsct = inv_lsct2_winconst(w, b, mask, lst,n, m=2, ws=5, wl=10.8,method = method,ifcons = 0,ifbayesian = if_bayesian)
                elif m == 3:
                    if dn == 'day':
                        lsct = inv_lsct3_winconst(w, b, mask, lst, psoil, n = 2, m=3, ws=5, wl=10.8,method = 'ls',ifcons = 0)
                    elif dn == 'night':
                        lsct = np.zeros([nl,ns,4])
                        lsct[:,:,2:4] = inv_lsct2_winconst(w2, b, mask, lst, n = 2, m=2, ws=5, wl=10.8,method = 'ls',ifcons = 0)
            
            elif method_mpl_pixel == 'winquad':
                if m == 2:
                    if method_solve == 'bayesian': if_bayesian = 1
                    else: if_bayesian = 0

                    lsct = inv_lsct2_winquad_constraint(w, b, mask,lst,n, m=2, ws=5,wl=10.8,if_bayesian = if_bayesian)

                elif m == 3:  # 这里m=2，中间3组分
                    if method_solve == 'bayesian': if_bayesian = 1
                    else: if_bayesian = 0

                    if dn == 'day':
                        lsct = inv_lsct3_winquad(w2, w, b, mask,psoil,n, m=2, ws=5,wl=10.8,if_bayesian = if_bayesian)
                        # lsct = inv_lsct3_winquad_constraint(w2, w, b, mask,lst,psoil,n, m=2, ws=5,wl=10.8,if_bayesian = if_bayesian)
                        
                        # ### 多线程
                        # para = []
                        # for kn in range(off, ns-off):
                        #     wLine = w[:,kn-off:kn+off+1,:,:]
                        #     w2Line = w2[:,kn-off:kn+off+1,:,:]
                        #     bLine = b[:,kn-off:kn+off+1,:]
                        #     maskLine = mask[:,kn-off:kn+off+1,:]
                        #     lstLine = lst[:,kn-off:kn+off+1,:]
                        #     psoilLine = psoil[:,kn-off:kn+off+1]
                        #     para.append([w2Line,wLine,bLine,maskLine,lstLine,psoilLine,n,2,ws,wl,if_bayesian])
                        
                        # tasks= []
                        # pool = Pool(min(192,cpu_count()))
                        # tasks = [pool.apply_async(inv_lsct3_winquad_constraint, tuple(p)) for p in para]
                        # pool.close()
                        # pool.join()
                        # results = [t.get() for t in tasks]
                        # lsct = np.zeros((nl, ns, 4))
                        # for idx, res in enumerate(results):
                        #     kn = idx + off
                        #     # 如果 res 形状是 (nl, m)，直接赋值
                        #     lsct[:, kn, :] = res[:,off,:]
                    
                    elif dn == 'night':
                        lsct = np.full((nl,ns,4),np.nan)
                        lsct[:,:,2:] = inv_lsct2_winquad(w2, b, mask,n, m=2, ws=5,wl=10.8,if_bayesian = if_bayesian)
                        # lsct[:,:,2:] = inv_lsct2_winquad_constraint(w2, b, mask,lst,n, m=2, ws=5,wl=10.8,if_bayesian = if_bayesian)

                        # ### 多线程
                        # para = []
                        # for kn in range(off, ns-off):
                        #     w2Line = w2[:,kn-off:kn+off+1,:,:]
                        #     bLine = b[:,kn-off:kn+off+1,:]
                        #     maskLine = mask[:,kn-off:kn+off+1,:]
                        #     lstLine = lst[:,kn-off:kn+off+1,:]
                        #     para.append([w2Line,bLine,maskLine,lstLine,n,2,ws,wl,if_bayesian])
                            
                        # tasks= []
                        # pool = Pool(min(192,cpu_count()))
                        # tasks = [pool.apply_async(inv_lsct2_winquad_constraint, tuple(p)) for p in para]
                        # pool.close()
                        # pool.join()
                        # results = [t.get() for t in tasks]

                        # for idx, res in enumerate(results):
                        #     kn = idx + off
                        #     # 如果 res 形状是 (nl, m)，直接赋值
                        #     lsct[:, kn, 2:] = res[:,off,:]
            
            elif method_mpl_pixel == 'point_prior':
                lsct = inv_lsct_point_prior(w,b,td_prior, mask,n,m,wl,method='ls')
            elif method_mpl_pixel == 'winconst_prior':
                lsct = inv_lsct2_winconst_prior(w,b,td_prior, mask,lst,n,m,ws,wl,method='ls',ifcons=0)
            ### -1. 保存结果
            name_list = ['lstN','lstF','lai','indx','indy','ref_indx','ref_indy','cloN_mask','cloF_mask']
            data_list = [lstN,lstF,lai,indx,indy,ref_indx,ref_indy,cloN_mask,cloF_mask]
            dtype_list = np.full_like(name_list,'f')
            write_h5py_file(outfile,name_list,data_list,dtype_list,compression=None,ifcover = 1)
            write_h5py_item(outfile,'utc_time',utc_time.isoformat(),dtype=h5py.string_dtype())

            if m == 2:
                write_h5py_item(outfile,'Ts',lsct[:,:,0],'f',if_overwrite=1)
                write_h5py_item(outfile,'Tv',lsct[:,:,1],'f',if_overwrite=1)
            if m == 3:
                write_h5py_item(outfile,'Tsl',lsct[:,:,0],'f',if_overwrite=1)
                write_h5py_item(outfile,'Tsh',lsct[:,:,1],'f',if_overwrite=1)
                write_h5py_item(outfile,'Ts',lsct[:,:,2],'f',if_overwrite=1)
                write_h5py_item(outfile,'Tv',lsct[:,:,3],'f',if_overwrite=1)
            
            if method_mpl_pixel == 'prior':
                write_h5py_item(outfile,'td_prior',td_prior,'f',if_overwrite=1)
            
            end_time = time.time()
            print(f"总执行时间: {end_time - start_time:.4f}秒\n")