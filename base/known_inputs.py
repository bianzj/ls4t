"""Known-input, temperature-only component retrieval.

Scalar/site API: no GUI dependency. LST input is already atmosphere corrected.
BT input requires a versioned sensor-specific split-window calibration. The
Hom canopy model supplies effective emissivities including multiple scattering.
AHI/SLSTR spectral differences are retained; no empirical bias is fitted away.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from base.calibration import load_split_window_model
from base.lst import DualChannelObservation, retrieve_dual_channel_lst
from base.radiometry import inverse_planck, planck_radiance
from base.rt.hom import Hom


def number(value, label, low, high):
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f'{label} 必须是数值') from None
    if not np.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{label} 必须在 {low}–{high} 之间')
    return value


def validate_fixed(fixed):
    if not isinstance(fixed, dict):
        raise ValueError('fixed 必须是已知参数对象')
    number(fixed.get('lai'), 'LAI', .01, 10)
    number(fixed.get('tcwv_cm'), 'TCWV (cm)', 0, 10)
    number(fixed.get('hotspot', .2), '热点参数', .01, 1)
    for key in ('soil_emissivity', 'vegetation_emissivity'):
        values = fixed.get(key)
        if not isinstance(values, (list, tuple)) or len(values) != 2:
            raise ValueError(f'{key} 需要两个波段的发射率')
        for value in values:
            number(value, key, .8, 1.)


def component_weights(fixed, observation, components=2):
    """Order: soil/vegetation or sunlit soil/shaded soil/vegetation."""
    model = Hom()
    model.set_structure(float(fixed['lai']), float(fixed.get('hotspot', .2)))
    model.set_optical(float(observation['wavelength_um']),
                      float(fixed['soil_emissivity'][0]),
                      float(fixed['vegetation_emissivity'][0]))
    model.set_angle(np.array([float(observation['vza'])]),
                    np.array([float(observation['sza'])]),
                    np.array([float(observation['raa'])]))
    e = model.run_emis().reshape(4)
    return np.array([e[0]+e[1], e[2]+e[3]]) if components == 2 else np.array([e[0], e[1], e[2]+e[3]])


def predict_lst(temperature_k, fixed, observation):
    weights = component_weights(fixed, observation, len(temperature_k))
    wl = float(observation['wavelength_um'])
    return inverse_planck(wl, np.dot(weights, planck_radiance(wl, temperature_k)) / weights.sum())


def _lst(observation, fixed):
    if observation.get('lst_k') is not None:
        return number(observation['lst_k'], 'LST (K)', 220, 365), '已有 LST；不重复大气校正'
    path = observation.get('coefficient_file')
    if not path or not Path(path).is_file():
        raise ValueError('亮温反演需要该传感器的 NPZ 分裂窗系数文件')
    with np.load(path, allow_pickle=False) as bundle:
        metadata = json.loads(str(bundle['metadata'].item()))
    if metadata.get('sensor', '').upper() != observation['sensor'].upper():
        raise ValueError('分裂窗系数的传感器与观测不一致')
    b1 = number(observation.get('bt1_k'), 'BT1 (K)', 200, 400)
    b2 = number(observation.get('bt2_k'), 'BT2 (K)', 200, 400)
    a = lambda value: np.array([float(value)])
    item = DualChannelObservation(a(b1), a(b2),
        a(fixed['soil_emissivity'][0]), a(fixed['soil_emissivity'][1]),
        a(fixed['vegetation_emissivity'][0]), a(fixed['vegetation_emissivity'][1]),
        a(fixed['lai']), a(fixed['tcwv_cm']), a(observation['vza']))
    result = retrieve_dual_channel_lst(item, load_split_window_model(path))
    if not np.isfinite(result.temperature_k[0]) or result.quality_flag[0] != 0:
        raise ValueError('分裂窗反演超出系数适用范围或温度范围，请检查水汽、角度和亮温')
    return float(result.temperature_k[0]), '已知 LAI / TCWV / 双波段发射率的分裂窗反演'


def run_workbench(payload: dict) -> dict:
    """Fit only temperatures. Held-out observations never enter the objective.

    This route ends at component temperatures and fit diagnostics.
    Reference geometry and normalization are deliberately not evaluated.
    """
    if not isinstance(payload, dict):
        raise ValueError('配置必须是 JSON 对象')
    fixed = deepcopy(payload.get('fixed', {}))
    validate_fixed(fixed)
    sensor_fixed = fixed.get('sensors', {})
    if not isinstance(sensor_fixed, dict):
        raise ValueError('传感器发射率配置必须是对象')
    for sensor, overrides in sensor_fixed.items():
        if sensor not in ('AHI', 'SLSTR') or not isinstance(overrides, dict) or set(overrides) - {'soil_emissivity', 'vegetation_emissivity'}:
            raise ValueError('传感器独立配置只允许 AHI/SLSTR 的土壤和植被发射率')
    if not isinstance(payload.get('optimize', True), bool):
        raise ValueError('optimize 必须为布尔值')
    components = payload.get('components', 2)
    if components not in (2, 3):
        raise ValueError('组分数只能为 2 或 3')
    observations = deepcopy(payload.get('observations', []))
    if not isinstance(observations, list) or not 2 <= len(observations) <= 64:
        raise ValueError('需要 2–64 条观测')
    times = []
    lst, weights, wavelengths, sigmas, fit_mask = [], [], [], [], []
    for obs in observations:
        if not isinstance(obs, dict):
            raise ValueError('每条观测必须是对象')
        if obs.get('sensor') not in ('SLSTR', 'AHI'):
            raise ValueError('传感器必须是 SLSTR 或 AHI')
        for key, high in [('vza', 80), ('sza', 85), ('raa', 360)]:
            obs[key] = number(obs.get(key), key, 0, high)
        obs['wavelength_um'] = number(obs.get('wavelength_um'), '波长 (µm)', 8, 14)
        obs['sigma_k'] = number(obs.get('sigma_k', 1), '观测不确定度 (K)', .01, 20)
        if obs.get('cloud', False):
            raise ValueError('观测被标记为云污染；请移除该观测后重试')
        try:
            dt = datetime.fromisoformat(obs['time_utc'].replace('Z', '+00:00'))
            if dt.utcoffset() is None:
                raise ValueError()
            times.append(dt.timestamp())
        except (KeyError, ValueError, TypeError):
            raise ValueError('每条观测需要带时区的 time_utc 时间') from None
        # Optional per-sensor fixed emissivities; never included in optimization.
        local = dict(fixed, **fixed.get('sensors', {}).get(obs['sensor'], {}))
        validate_fixed(local)
        value, mode = _lst(obs, local)
        obs['retrieval_mode'] = mode
        lst.append(value)
        weights.append(component_weights(local, obs, components))
        wavelengths.append(obs['wavelength_um'])
        sigmas.append(obs['sigma_k'])
        use = obs.get('use_for_fit', True)
        if not isinstance(use, bool):
            raise ValueError('use_for_fit 必须为布尔值')
        fit_mask.append(use)
    if max(times) - min(times) > 600:
        raise ValueError('观测时间跨度超过 10 分钟；请先配准时间，不可把时间变化当作角度效应')
    y = np.array(lst)
    mask = np.array(fit_mask)
    sigma = np.array(sigmas)
    w = np.array(weights)
    if mask.sum() < components:
        raise ValueError(f'{components} 组分至少需要 {components} 条参与拟合的独立观测')
    condition = float(np.linalg.cond(w[mask]))
    if not np.isfinite(condition) or condition > 1e4 or np.linalg.matrix_rank(w[mask]) < components:
        raise ValueError('观测角度缺少独立信息，组分反演病态或秩不足；请增加不同视角或减少组分')
    wl = np.array(wavelengths)

    def forward(t, matrix=w):
        return np.array([inverse_planck(l, np.dot(row, planck_radiance(l, t)) / row.sum())
                         for row, l in zip(matrix, wl)])

    def residual(t):
        return (forward(t)[mask]-y[mask]) / sigma[mask]

    start = np.full(components, np.mean(y[mask]))
    baseline = least_squares(residual, start, bounds=(220, 365), xtol=1e-11, ftol=1e-11, gtol=1e-11)
    strength = number(payload.get('prior_strength', 0), '先验强度', 0, 100)
    prior = np.array(payload.get('prior_k', [300.]*components), dtype=float)
    if prior.shape != (components,) or not np.all(np.isfinite(prior)) or np.any((prior < 220) | (prior > 365)):
        raise ValueError('每个组分需要 220–365 K 范围内的温度先验')
    prior_sigma = number(payload.get('prior_sigma_k', 10), '先验不确定度 (K)', .1, 100)
    optimize = bool(payload.get('optimize', True))
    def objective(t):
        return np.r_[residual(t), np.sqrt(strength)*(t-prior)/prior_sigma] if strength else residual(t)
    solved = least_squares(objective, baseline.x, bounds=(220, 365), loss='soft_l1',
                           xtol=1e-11, ftol=1e-11, gtol=1e-11) if optimize else baseline
    if not solved.success:
        raise ValueError('温度优化未收敛：' + solved.message)
    if components == 3 and solved.x[0] < solved.x[1]:
        raise ValueError('当前观测导致光照土壤低于阴影土壤；请检查配准、云和模型适用性')
    predicted = forward(solved.x)
    rows = [dict(obs, lst_k=float(y[i]), predicted_k=float(predicted[i]),
                 residual_k=float(y[i]-predicted[i])) for i, obs in enumerate(observations)]
    warnings = ['拟合残差不等于地面验证精度；留出观测用于跨视角一致性检验。']
    if mask.sum() == components:
        warnings.append('拟合观测数等于组分数，没有多余自由度；接近零残差不能证明精度。')
    if np.any((solved.x < 220.01) | (solved.x > 364.99)):
        warnings.append('温度达到优化边界；当前反演不可靠，请检查输入和组分可辨识性。')
    if condition > 100:
        warnings.append('观测矩阵条件数较大，组分温度对输入误差敏感。')
    return dict(schema='ls4t.component-result/v1', route='retrieval', fixed=fixed,
                temperature_k=solved.x.tolist(), baseline_temperature_k=baseline.x.tolist(),
                component_names=['土壤', '植被'] if components == 2 else ['光照土壤', '阴影土壤', '植被'],
                fit_count=int(mask.sum()), heldout_count=int((~mask).sum()),
                condition_number=condition, fit_rmse_k=float(np.sqrt(np.mean((predicted[mask]-y[mask])**2))),
                baseline_rmse_k=float(np.sqrt(np.mean((forward(baseline.x)[mask]-y[mask])**2))),
                heldout_rmse_k=float(np.sqrt(np.mean((predicted[~mask]-y[~mask])**2))) if (~mask).any() else None,
                observations=rows, warnings=warnings,
                optimize=optimize,
                max_time_span_seconds=max(times)-min(times),
                provenance=deepcopy(payload.get('provenance', {})))
