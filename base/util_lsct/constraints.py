import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from base.util_lsct.packages import *
from base.util_lsct.phys import *

'''
lsct_constraint
温差限制\窗口权重weight\初值和边界值约束
'''
def constraint_func_Nangle(x, lst, ws=None, wl=10.8):
    '''
    正确性约束（约等于无约束）组分能量与LST的温差约束条件，即可处理点输入，也可处理窗口输入
    :param x: 组分能量
    :param lst: LST数据
    :param ws: 窗口大小（可选），如果提供则使用窗口中心点的LST
    :param wl: 波长，默认为10.8μm
    :return: 约束条件值 [constraint1, constraint2]
    '''
    if ws is not None:
        center = int(ws // 2)
        b = planck(wl, lst[center, center, :])
    else:
        b = planck(wl, lst)
    
    # 计算约束条件
    constraint1 = np.max(x) - np.max(b)
    constraint2 = np.min(b) - np.min(x)
    
    return [constraint1, constraint2]

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
        x0 = np.array([max(b) + 10, np.min(b) - 5, np.average(b)])
        bounds = [[planck(wl, lsta-10), planck(wl, lsta + 40)], [planck(wl, lsta - 30), planck(wl, lsta + 30)], [planck(wl, lsta - 20), planck(wl, lsta + 20)]]
    elif m == 4:
        x0 = np.array([max(b) + 10, np.min(b) - 5, np.average(b), min(b) - 5])
        bounds = [[planck(wl, lsta-10), planck(wl, lsta + 40)], [planck(wl, lsta - 30), planck(wl, lsta + 30)], [planck(wl, lsta - 20), planck(wl, lsta + 20)], [planck(wl, lsta - 30), planck(wl, lsta + 30)]]
    return x0,bounds
