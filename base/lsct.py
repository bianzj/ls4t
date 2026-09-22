"""Multi-angle component-temperature inversion in radiance space."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .quality import QualityFlag, new_flags, set_flag
from .radiometry import inverse_planck

# Window retrieval restored from the AATSR product history; re-exported here so
# the SLSTR study-area cases keep importing everything from base.lsct.
from base.lsct_window import inv_lsct2_window, inv_lsct3_window  # noqa: F401


@dataclass(frozen=True)
class ComponentRetrievalResult:
    temperature_k: np.ndarray
    radiance: np.ndarray
    residual_rms: np.ndarray
    condition_number: np.ndarray
    quality_flag: np.ndarray


def retrieve_components(
    observed_radiance: np.ndarray,
    effective_weights: np.ndarray,
    wavelength_um: float,
    *,
    observation_uncertainty: np.ndarray | None = None,
    ridge: float = 0.0,
    max_condition_number: float = 1.0e6,
    valid_temperature_range_k: tuple[float, float] = (200.0, 380.0),
) -> ComponentRetrievalResult:
    """Solve ``weights @ component_radiance = observed_radiance`` per pixel.

    The last radiance axis is observation/angle and the final weights axes are
    ``(observation, component)``. Invalid observations are omitted per pixel.
    """
    y = np.asarray(observed_radiance, dtype=np.float64)
    matrix = np.asarray(effective_weights, dtype=np.float64)
    if matrix.ndim < 2 or y.shape != matrix.shape[:-1]:
        raise ValueError("effective_weights must have shape (..., observation, component)")
    spatial_shape = y.shape[:-1]
    n_obs, n_components = matrix.shape[-2:]
    if n_obs < n_components:
        raise ValueError("at least as many observations as components are required")
    if ridge < 0:
        raise ValueError("ridge must be non-negative")

    if observation_uncertainty is None:
        sigma = np.ones_like(y)
    else:
        sigma = np.broadcast_to(np.asarray(observation_uncertainty, dtype=np.float64), y.shape)

    flat_y = y.reshape(-1, n_obs)
    flat_a = matrix.reshape(-1, n_obs, n_components)
    flat_sigma = sigma.reshape(-1, n_obs)
    solved = np.full((flat_y.shape[0], n_components), np.nan)
    residual = np.full(flat_y.shape[0], np.nan)
    condition = np.full(flat_y.shape[0], np.nan)
    flags = new_flags((flat_y.shape[0],))

    for index, (values, design, errors) in enumerate(zip(flat_y, flat_a, flat_sigma)):
        valid = (
            np.isfinite(values)
            & np.all(np.isfinite(design), axis=1)
            & np.isfinite(errors)
            & (errors > 0)
        )
        if valid.sum() < n_components:
            flags[index] |= np.uint16(QualityFlag.INPUT_INVALID | QualityFlag.RETRIEVAL_FAILED)
            continue
        weighted_a = design[valid] / errors[valid, None]
        weighted_y = values[valid] / errors[valid]
        condition[index] = np.linalg.cond(weighted_a)
        if not np.isfinite(condition[index]) or condition[index] > max_condition_number:
            flags[index] |= np.uint16(QualityFlag.ILL_CONDITIONED | QualityFlag.RETRIEVAL_FAILED)
            continue
        try:
            if ridge:
                lhs = weighted_a.T @ weighted_a + ridge * np.eye(n_components)
                rhs = weighted_a.T @ weighted_y
                solution = np.linalg.solve(lhs, rhs)
            else:
                solution = np.linalg.lstsq(weighted_a, weighted_y, rcond=None)[0]
        except np.linalg.LinAlgError:
            flags[index] |= np.uint16(QualityFlag.RETRIEVAL_FAILED)
            continue
        if np.any(solution <= 0):
            flags[index] |= np.uint16(QualityFlag.OUT_OF_RANGE | QualityFlag.RETRIEVAL_FAILED)
            continue
        solved[index] = solution
        difference = design[valid] @ solution - values[valid]
        residual[index] = np.sqrt(np.mean(difference**2))

    temperatures = inverse_planck(wavelength_um, solved)
    low, high = valid_temperature_range_k
    bad_temperature = np.any(
        ~np.isfinite(temperatures) | (temperatures < low) | (temperatures > high), axis=1
    )
    set_flag(flags, bad_temperature, QualityFlag.OUT_OF_RANGE)
    temperatures[bad_temperature] = np.nan
    solved[bad_temperature] = np.nan
    return ComponentRetrievalResult(
        temperature_k=temperatures.reshape(spatial_shape + (n_components,)),
        radiance=solved.reshape(spatial_shape + (n_components,)),
        residual_rms=residual.reshape(spatial_shape),
        condition_number=condition.reshape(spatial_shape),
        quality_flag=flags.reshape(spatial_shape),
    )


def retrieve_components_window(
    observed_radiance: np.ndarray,
    effective_weights: np.ndarray,
    wavelength_um: float,
    *,
    window_size: int = 5,
    observation_uncertainty: np.ndarray | None = None,
    ridge: float = 0.0,
    max_condition_number: float = 1.0e6,
    valid_temperature_range_k: tuple[float, float] = (200.0, 380.0),
) -> ComponentRetrievalResult:
    """Window LSCT for cases with fewer angles than components.

    Component radiances are assumed locally constant inside each moving window,
    while effective-emissivity weights may vary by pixel and angle. This is the
    production baseline corresponding to the legacy 5x5 constant-window solves.
    """
    values = np.asarray(observed_radiance, dtype=np.float64)
    weights = np.asarray(effective_weights, dtype=np.float64)
    if values.ndim != 3 or weights.ndim != 4 or weights.shape[:-1] != values.shape:
        raise ValueError(
            "window retrieval requires radiance (row, col, observation) and weights "
            "(row, col, observation, component)"
        )
    if window_size < 1 or window_size % 2 == 0:
        raise ValueError("window_size must be a positive odd integer")
    if observation_uncertainty is None:
        errors = np.ones_like(values)
    else:
        errors = np.broadcast_to(np.asarray(observation_uncertainty, dtype=np.float64), values.shape)

    rows, columns, _ = values.shape
    n_components = weights.shape[-1]
    radius = window_size // 2
    padded_values = np.pad(values, ((radius, radius), (radius, radius), (0, 0)), constant_values=np.nan)
    padded_weights = np.pad(
        weights,
        ((radius, radius), (radius, radius), (0, 0), (0, 0)),
        constant_values=np.nan,
    )
    padded_errors = np.pad(errors, ((radius, radius), (radius, radius), (0, 0)), constant_values=np.nan)
    temperature = np.full((rows, columns, n_components), np.nan)
    radiance = np.full_like(temperature, np.nan)
    residual = np.full((rows, columns), np.nan)
    condition = np.full((rows, columns), np.nan)
    flags = new_flags((rows, columns))

    for row in range(rows):
        for column in range(columns):
            window = (slice(row, row + window_size), slice(column, column + window_size))
            local_values = padded_values[window].reshape(-1)
            local_weights = padded_weights[window].reshape(-1, n_components)
            local_errors = padded_errors[window].reshape(-1)
            result = retrieve_components(
                local_values,
                local_weights,
                wavelength_um,
                observation_uncertainty=local_errors,
                ridge=ridge,
                max_condition_number=max_condition_number,
                valid_temperature_range_k=valid_temperature_range_k,
            )
            temperature[row, column] = result.temperature_k
            radiance[row, column] = result.radiance
            residual[row, column] = result.residual_rms
            condition[row, column] = result.condition_number
            flags[row, column] = result.quality_flag
    return ComponentRetrievalResult(temperature, radiance, residual, condition, flags)


# ---------------------------------------------------------------------------
# SLSTR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
from numpy import exp
import numpy as np
from base.radiometry import planck
from base.rt.gap import gap_probability_hom_analytical
from base.rt.hom import Hom


ndvi_min_g = 0.05


ndvi_max_g = 0.99


def sample_hom_Emis(lai, hspot, wavelength, emissivity_soil, emissivity_leaf, vza, sza, raa):
    '''1.initial'''
    hom = Hom()
    '''2.set variables'''
    hom.set_structure(lai, hspot)
    hom.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    hom.set_angle(vza, sza, raa)
    ''''3.run'''
    emis = hom.run_emis()
    vza[raa == 180] = vza[raa == 180] * -1
    return emis


def sample_hom_Emis2(lai, hspot, wavelength, emissivity_soil, emissivity_leaf, vza, sza, raa):
    '''1.initial'''
    hom = Hom()
    '''2.set variables'''
    hom.set_structure(lai, hspot)
    hom.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    hom.set_angle(vza, sza, raa)
    ''''3.run'''
    emis = hom.run_emis2()
    vza[raa == 180] = vza[raa == 180] * -1
    return emis


def cal_rad_from_lst(lst,wl,lai,vza,emisS,emisV):
    '''
    根据lst计算rad
    :param lst: 反演出来的lst nl*ns
    :param wl: 波长
    :param lai: 叶面积 nl * ns
    :param vza: 天顶角 nl*ns
    :param emisS: 土壤发射率 nl*ns
    :param emisV: 植被发射率 nl*ns
    :return:
    '''
    fvc = 1 - gap_probability_hom_analytical(lai, vza)
    rad = planck(wl, lst)
    # 多次散射项
    F = 0.75
    C = (1 - emisS) * emisV * F * (1 - fvc)
    rad = rad * (fvc * emisV + (1 - fvc) * emisS + C)
    return rad


def cal_fvc_from_lai(thetav,lai):
    G = 0.5
    rd = np.pi / 180.0
    costhetanv = np.cos(thetav * rd)
    fvc = 1 - exp(-G*lai/costhetanv)
    fvc[fvc>1] = 1
    fvc[fvc<0] = 0
    return fvc


def cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vza, sza, vaa, saa, n , m, CI=1.0):
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
    sza[sza>=90] = 89.9
    if lai.ndim == 0:  # 标量输入，转换为点输入
        # 点输入处理
        vza = np.atleast_1d(vza)
        sza = np.atleast_1d(sza)
        vaa = np.atleast_1d(vaa)
        saa = np.atleast_1d(saa)
        w4 = sample_hom_Emis(lai, hspot, wl, emisS, emisV, vza, sza, np.abs(vaa-saa))
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
            if m == 2:
                result = sample_hom_Emis2(lai, hspot, wl, emisS, emisV, 
                                   vza[:, :, ni], sza[:, :, ni], vsa[:, :, ni])
            else:
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
        return w.transpose(0, 1, 3, 2) # nl*ns*n*m


# ---------------------------------------------------------------------------
# AATSR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
from scipy.linalg import lstsq
import numpy as np
from numpy import max, min
from base.fitting import fitting_unknown_linear_ls, fitting_unknown_linear_sklearn
from base.radiometry import planck


def cal_rad_from_lst_fvc(lst,wl,fvc,emisS,emisV):
    '''
    根据lst计算rad，不输入lai，直接输入fvc，适用于NDVI反演
    :param lst: 反演出来的lst nl*ns
    :param wl: 波长
    :param fvc: 植被覆盖度 nl * ns
    :param emisS: 土壤发射率 nl*ns
    :param emisV: 植被发射率 nl*ns
    :return:
    '''
    rad = planck(wl, lst)
    # 多次散射项
    F = 0.75
    C = (1 - emisS) * emisV * F * (1 - fvc)
    rad = rad * (fvc * emisV + (1 - fvc) * emisS + C)
    return rad


def cal_psoil_hom(lai,sza):
    '''
    计算均值假设下冠层的光照土壤占总土壤的比例
    :param lai: 叶面积指数
    :param sza: 太阳天顶角
    :return: psoil 光照土壤占总土壤的比例
    计算公式：psoil = exp(-G*LAI/cos(sza))
    '''
    sza = np.atleast_1d(np.asarray(sza))
    lai = np.atleast_1d(lai)
    if sza.ndim == 1:
        sza = sza.reshape(1, 1)
    nl, ns = np.shape(sza)
    psoil = gap_probability_hom_analytical(lai, sza)
    if nl == 1 and ns == 1:
        psoil = psoil.squeeze()
    return psoil


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
    d12_min = planck(wl, lsta + d[0] / 2) - planck(10.8, lsta - d[0] / 2)
    d12_max = planck(wl, lsta + d[1] / 2) - planck(10.8, lsta - d[1] / 2)
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
    d12_min = planck(wl, lsta + d12[0] / 2) - planck(10.8, lsta - d12[0] / 2)
    d12_max = planck(wl, lsta + d12[1] / 2) - planck(10.8, lsta - d12[1] / 2)
    d23_min = planck(wl, lsta + d23[0] / 2) - planck(10.8, lsta - d23[0] / 2)
    d23_max = planck(wl, lsta + d23[1] / 2) - planck(10.8, lsta - d23[1] / 2)
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


def set_x0_bnds_Nangle_Mcomponent(lst, n, m, ws=None, wl=10.8):
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
    # print(lsta,np.nanmax(lst),np.nanmin(lst))
    if m == 2:
        x0 = np.array([max(b) + 5, min(b) - 3])
        bounds = [[planck(wl, lsta - 10), planck(wl, lsta + 40)], [planck(wl, lsta - 10), planck(wl, lsta + 10)]]
    elif m == 3:
        x0 = np.array([max(b) + 10, np.min(b) - 5, np.average(b)])
        bounds = [[planck(wl, lsta - 10), planck(wl, lsta + 40)], [planck(wl, lsta - 30), planck(wl, lsta + 30)],
                  [planck(wl, lsta - 10), planck(wl, lsta + 20)]]
    elif m == 4:
        x0 = np.array([max(b) + 10, np.min(b) - 5, np.average(b), min(b) - 5])
        bounds = [[planck(wl, lsta - 10), planck(wl, lsta + 40)], [planck(wl, lsta - 30), planck(wl, lsta + 30)],
                  [planck(wl, lsta - 20), planck(wl, lsta + 20)], [planck(wl, lsta - 30), planck(wl, lsta + 30)]]
    return x0, bounds


def set_x0_bnds_Nangle_Mcomponent_night(lst, n, m, ws=None, wl=10.8):
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
        x0 = np.array([np.max(b), np.min(b)])
        bounds = [[planck(wl, lsta - 10), planck(wl, lsta + 10)], [planck(wl, lsta - 10), planck(wl, lsta + 10)]]
    elif m == 3:
        x0 = np.array([max(b), np.min(b), np.average(b)])
        bounds = [[planck(wl, lsta - 10), planck(wl, lsta + 10)], [planck(wl, lsta - 10), planck(wl, lsta + 10)],
                  [planck(wl, lsta - 10), planck(wl, lsta + 10)]]
    elif m == 4:
        x0 = np.array([max(b), np.min(b), np.average(b), min(b)])
        bounds = [[planck(wl, lsta - 10), planck(wl, lsta + 40)], [planck(wl, lsta - 30), planck(wl, lsta + 30)],
                  [planck(wl, lsta - 20), planck(wl, lsta + 20)], [planck(wl, lsta - 30), planck(wl, lsta + 30)]]
    return x0, bounds


def fitting_Nangle_Mcomponent_point(w, b, n, m, method='ridge'):
    '''
    多角度 多组分 点
    :param w: 有效发射率矩阵, shape (n,m)
    :param b: 亮温矩阵, shape (n,)
    :param n: 角度数
    :param m: 组分数
    :param method: 线性求解方法 ridge、lasso、bayesianridge、ls
    :return: p： 组分能量，shape (m,)
    '''
    w, b = np.asarray(w), np.asarray(b)
    if w.shape[0] != n or w.shape[1] != m:
        print('Error: w shape is not match n angles and m components')
        return -1
    if b.shape[0] != n:
        print('Error: b shape is not match n angles')
        return -1
    if method in ['ridge', 'lasso', 'bayesianridge']:
        p = fitting_unknown_linear_sklearn(b, w, method=method)
    elif method == 'ls':
        p = fitting_unknown_linear_ls(b, w)
    return p


def fitting_Nangle_Mcomponent_window_quadratic(w, b, n, m, mask,weight, window_size=5):
    '''
    多角度 多组分 窗口内组分温度二次分布
    :param w: 有效发射率矩阵 shape(ws,ws,n,m) ws:窗口大小
    :param b: 亮温矩阵 shape(ws,ws,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(ws,ws,n)
    :param n: 角度数
    :param m: 组分数
    :param window_size: 窗口大小
    :return: p： 组分能量 shape(nl,ns,m）
    '''
    ws = window_size
    w, b, mask = np.asarray(w), np.asarray(b), np.asarray(mask)
    weight = np.asarray(weight)

    # --- 基础检查 ---
    if w.shape[0] != ws or w.shape[1] != ws or w.shape[2] != n or w.shape[3] != m:
        print('Error: w shape mismatch')
        return -1
    if b.shape[0] != ws or b.shape[1] != ws or b.shape[2] != n:
        print('Error: b shape mismatch')
        return -1
    if mask.shape[0] != ws or mask.shape[1] != ws or mask.shape[2] != n:
        print('Error: mask shape mismatch')
        return -1

    # --- 展平数据 ---
    # 展平后的顺序：Pixel(0,0)_Ang0, Pixel(0,0)_Ang1, Pixel(0,1)_Ang0...
    w_flat = w.reshape(-1, m)   # (ws*ws*n, m)
    b_flat = b.reshape(-1)      # (ws*ws*n, )
    mask_flat = mask.reshape(-1).astype(bool) # (ws*ws*n, )

    if np.sum(mask_flat) < 6 * m: 
        return np.full((m,), np.nan)

    # --- 构建几何矩阵 X ---
    radius = window_size // 2 
    offsets = np.arange(-radius, radius + 1)
    ns_grid, nl_grid = np.meshgrid(offsets, offsets)
    ns_temp = ns_grid.flatten()
    nl_temp = nl_grid.flatten()
    n0 = np.ones(len(ns_temp))
    
    # x_base: (6, 25)
    x_base = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
    
    # 【修正1】使用 repeat 而不是 tile
    # 这里的 repeat_factor 通常等于 n (角度数)
    # 结果: [x0, x0, x1, x1...] 对应 [p0_a1, p0_a2, p1_a1, p1_a2...]
    x = np.repeat(x_base, n, axis=1) # (6, 50)
    
    # --- 构建 WW 和 BB ---
    part = 6
    ww_list = [w_flat[:, j] * x[i, :] for j in range(m) for i in range(part)]
    ww = np.asarray(ww_list).T
    bb = b_flat

    # --- 求解 ---
    try:
        coeffprior = np.asarray(lstsq(ww[mask_flat], bb[mask_flat], rcond=None)[0])
        # print(coeffprior)
    except Exception:
        return np.full((m,), np.nan)
        
    coeffs = coeffprior.reshape(m, part)
    p_final = coeffs[:,0].reshape(-1)
    # p_distribution = np.dot(coeffs, x_base) # (m, 25)
    
    # # 扩展权重以匹配观测序列 (50,) -> [w0, w0, w1, w1...]
    # w_obs_full = np.repeat(weight.flatten(), n)
    
    # # 应用掩膜：无效观测的权重置为0
    # # 注意：这里直接乘 mask_flat，也就是 0 的位置权重变 0
    # w_obs_valid = w_obs_full * mask_flat # (50, )
    
    # # 聚合回空间维度 (25, )
    # # 将 50 个观测权重变回 25 个像元权重 (对每个像元的 n 个角度求和)
    # w_spatial_agg = w_obs_valid.reshape(-1, n).sum(axis=1) # (25, )
    
    # sum_weights = np.sum(w_spatial_agg)
    # if sum_weights == 0:
    #     return np.full((m,), np.nan)
        
    # w_norm = w_spatial_agg / sum_weights # (25, )
    
    # p_final = np.dot(p_distribution, w_norm)
    
    return p_final
