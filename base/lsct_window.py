"""Window component-temperature retrieval used by the SLSTR study-area cases.

Moved verbatim from the AATSR product history (2026-09-16) after the
2026-09-07 layout flattening dropped the ``inv_lsct2_window`` /
``inv_lsct3_window`` helpers that ``slstr_lsct2_area.py`` and
``slstr_lsct3_area.py`` call. Kept in its own module so its module-level
``planck``/``inv_planck`` do not shadow ``base.radiometry``.
"""

from scipy.optimize import minimize
import numpy as np
from numpy import max, min
from base.radiometry import planck_c1, planck_c2


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


def constraint_func_Nangle_2component(x, lst, d, ws=None, wl=10.8):
    '''
    两组分温差限制,土壤植被 温差限制
    :param x: 组分能量
    :param ws: 窗口大小
    :param lst: 垂直LST,注意此处为ws*ws*n
    :param d: 光照土壤与阴影土壤的温差范围,单位是K [min,max]
    :return: 约束条件值
    '''
    if ws is not None:
        center = int(ws // 2)
        b = planck(wl, lst[center, center, :])
        lsta = np.nanmean(lst[center, center, :])
    else:
        b = planck(wl, lst)
        lsta = np.nanmean(lst)
    d12_min = planck(wl,lsta +  d[0]/2) -planck(10.8,lsta - d[0]/2)
    d12_max = planck(wl,lsta +  d[1]/2) -planck(10.8,lsta - d[1]/2)
    constraint1 = np.max(x) - np.max(b)
    constraint2 = np.min(b) - np.min(x)
    constraint3 = -d12_min + (x[0] - x[1])
    constraint4 = d12_max - (x[0] - x[1])
    return [constraint1, constraint2, constraint3, constraint4]


def constraint_func_Nangle_3component(x, lst, d12, d23, ws=None, wl=10.8):
    '''
    三组分温差限制,光照阴影土壤、阴影土壤植被 温差限制
    :param x: 组分能量
    :param ws: 窗口大小
    :param lst: 垂直LST,注意此处为ws*ws*n
    :param d12: 光照土壤与阴影土壤的温差范围,单位是K [min,max]
    :param d23: 阴影土壤与植被的温差范围,单位是K [min,max]
    :return: 约束条件值
    '''
    if ws is not None:
        center = int(ws // 2)
        b = planck(wl, lst[center, center, :])
        lsta = np.nanmean(lst[center, center, :])
    else:
        b = planck(wl, lst)
        lsta = np.nanmean(lst)
    d12_min = planck(wl,lsta +  d12[0]/2) -planck(10.8,lsta - d12[0]/2)
    d12_max = planck(wl,lsta +  d12[1]/2) -planck(10.8,lsta - d12[1]/2)
    d23_min = planck(wl,lsta +  d23[0]/2) -planck(10.8,lsta - d23[0]/2)
    d23_max = planck(wl,lsta +  d23[1]/2) -planck(10.8,lsta - d23[1]/2)
    constraint1 = np.max(x) - np.max(b)
    constraint2 = np.min(b) - np.min(x)
    constraint3 = -d12_min + (x[0] - x[1])
    constraint4 = d12_max - (x[0] - x[1])
    constraint5 = -d23_min + (x[1] - x[2])
    constraint6 = d23_max - (x[1] - x[2])
    return [constraint1, constraint2, constraint3, constraint4, constraint5, constraint6]


def set_weights(window_size):
    center = window_size // 2
    weights = np.zeros((window_size, window_size))

    for i in range(window_size):
        for j in range(window_size):
            d_ij = np.sqrt((i - center) ** 2 + (j - center) ** 2)
            if d_ij <= window_size:
                weights[i, j] = (1 - (d_ij / window_size) ** 2) ** 2
            else:
                weights[i, j] = 0
    return weights


def set_x0_bnds_Nangle_Mcomponent(lst,n,m,ws=None, wl=10.8):
    '''
    设置初值和边界
    :param lst: LST,注意此处为 (n,)
    :param wl: 波长
    :return: x0,bnds
    '''
    if ws is not None:
        center = int(ws // 2)
        b = planck(wl, lst[center, center, :])
        lsta = np.nanmean(lst[center, center, :])
    else:
        b = planck(wl, lst)
        lsta = np.nanmean(lst)

    if m == 2:
        x0 = np.array([max(b) + 5, min(b) - 3])
        bounds = [[planck(wl, lsta-10), planck(wl, lsta + 40)], [planck(wl, lsta - 30), planck(wl, lsta + 30)]]
    elif m == 3:
        x0 = np.array([max(b) + 15, np.min(b) - 5, np.average(b)])
        bounds = [[planck(wl, lsta-10), planck(wl, lsta + 40)], [planck(wl, lsta - 30), planck(wl, lsta + 30)], [planck(wl, lsta - 20), planck(wl, lsta + 20)]]
    elif m == 4:
        x0 = np.array([max(b) + 10, np.min(b) - 5, np.average(b), min(b) - 5])
        bounds = [[planck(wl, lsta-10), planck(wl, lsta + 40)], [planck(wl, lsta - 30), planck(wl, lsta + 30)], [planck(wl, lsta - 20), planck(wl, lsta + 20)], [planck(wl, lsta - 30), planck(wl, lsta + 30)]]
    return x0,bounds


def fitting_unknown_nonlinear_min(fun, y, A, xn, x0, bnds, method='Powell', constraints=None, **kwargs):
    '''
    非线性反演/回归，基于minimize函数，能给初值，也能给边界条件
    参数:
        fun: 目标函数，格式为fun(x, *args)
        y: 因变量数组
        A: 自变量矩阵
        xn: 变量个数
        x0: 初始值
        bnds: 边界条件列表
        method: 优化方法('Powell','SLSQP'等)
        constraints: 约束条件
        **kwargs: 传递给目标函数的额外参数
    返回:
        优化结果向量
    '''
    # 合并固定参数和额外参数
    fixed_args = (y, A, xn)
    extra_args = tuple(kwargs.values())
    all_args = fixed_args + extra_args
    
    res = minimize(fun, x0,
                  args=all_args,
                  method=method,
                  bounds=bnds,
                  constraints=constraints)
    return res.x


def fitting_Nangle_Mcomponent_window(w,b,n,m,mask,weight,constraints,x0,bounds,window_size =5,method='SLSQP'):
    '''
    多角度 多组分 窗口
    :param w: 有效发射率矩阵 shape(ws,ws,n,m) ws:窗口大小
    :param b: 亮温矩阵 shape(ws,ws,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(ws,ws,n)
    :param n: 角度数
    :param m: 组分数
    :param window_size: 窗口大小
    :param method: 非线性求解方法 BFGS/powell/SLSQP/L-BFGS-B/TNC
    :return: p： 组分能量 shape(nl,ns,m）
    '''
    ws = window_size
    w, b, mask = np.asarray(w), np.asarray(b), np.asarray(mask)
    if w.shape[0]!=ws or w.shape[1]!=ws or w.shape[2]!=n or w.shape[3]!=m:
        print('Error: w shape is not match window size * window size *  n angles * m components')
        return -1
    if b.shape[0]!=ws or b.shape[1]!=ws or b.shape[2]!=n:
        print('Error: b shape is not match window size * window size * n angles')
        return -1
    if mask.shape[0]!=ws or mask.shape[1]!=ws or mask.shape[2]!=n:
        print('Error: mask shape is not match window size * window size * n angles')
        return -1

    w = w.reshape(-1,m)
    b = b.reshape(-1)
    # 将mask沿角度维度重复n次
    # mask = np.tile(mask.reshape(-1,1), (1,n)).reshape(-1)
    mask = mask.astype(bool)
    mask = mask.reshape(-1)
    weight = weight.reshape(-1)
    weight = np.tile(weight.reshape(-1,1), (1,n)).reshape(-1)

    num_val_point = np.sum(mask)
    if num_val_point < 2 * m:
        return np.full((m,), np.nan)
    
    # 将weights应用于mask区域
    masked_weights = weight[mask]
    
    def objective_func(x, y, A, xn, weight):
        residuals = np.dot(A, x) - y
        return np.sum(weight * residuals**2)
        
    x = fitting_unknown_nonlinear_min(objective_func,
                                    b[mask],
                                    w[mask],
                                    m,
                                    x0,
                                    bounds,
                                    method=method,
                                    constraints=constraints,
                                    weight=masked_weights)  # 使用关键字参数传入权重
    return x


def inv_lsct2_window(n, m, ws, wl, w, b, mask, lst):
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

                # 两组分温差约束
                d = [-5,30]
                constraints = {
                    'type': 'ineq',  # 不等式约束
                    'fun': constraint_func_Nangle_2component,
                    'args': (lst_win, d,ws, wl)  # 注意是元组
                }

                x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst_win,n,m,ws)

                p = fitting_Nangle_Mcomponent_window(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method='SLSQP')
                result[i,j,:] = p
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    return lsct


def inv_lsct3_window(n, m, ws, wl, w, b, mask, lst):
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

                # 三组分温差约束
                d12 = [5,40] # 光照土壤 阴影土壤温差限制 
                d23 = [-15,15] # 阴影土壤 植被温差限制
                constraints = {
                    'type': 'ineq',  # 不等式约束
                    'fun': constraint_func_Nangle_3component,
                    'args': (lst_win, d12, d23,ws, wl)  # 注意是元组
                }

                x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst_win,n,m,ws)

                p = fitting_Nangle_Mcomponent_window(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method='SLSQP')
                result[i,j,:] = p
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    return lsct

