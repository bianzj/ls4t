"""Independent LST angular normalization; no component retrieval dependency.

One-parameter secant model: T(v) = intercept + c * (sec(v) - 1).
Estimate c from same-time, same-surface, same-sensor angular pairs, or supply
an externally calibrated c. This model does not describe solar/azimuth effects.
"""
from copy import deepcopy
from datetime import datetime
import numpy as np


def _number(value, label, low, high):
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f'{label} 必须为有效数值') from None
    if not np.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{label} 必须在 {low}–{high} 范围内')
    return value


def _kernel(v):
    return 1 / np.cos(np.deg2rad(v)) - 1


def normalize_observations(payload):
    if not isinstance(payload, dict):
        raise ValueError('归一化配置必须为对象')
    rows = deepcopy(payload.get('observations'))
    if not isinstance(rows, list) or not 1 <= len(rows) <= 64:
        raise ValueError('需要 1–64 条已有 LST 观测')
    reference = _number(payload.get('reference_vza', 0), '参考天顶角', 0, 75)
    mode = payload.get('coefficient_mode', 'fit')
    if mode not in ('fit', 'supplied'):
        raise ValueError('请选择角度配对标定或已有系数')
    y, v, sigma, mask = [], [], [], []
    for row in rows:
        if not isinstance(row, dict) or row.get('cloud', False):
            raise ValueError('需要有效无云 LST 观测')
        if row.get('sensor') not in ('AHI', 'SLSTR'):
            raise ValueError('传感器应为 AHI 或 SLSTR')
        y.append(_number(row.get('lst_k'), 'LST (K)，归一化不接收亮温', 220, 365))
        v.append(_number(row.get('vza'), '观测天顶角', 0, 80))
        sigma.append(_number(row.get('sigma_k', 1), '不确定度', .01, 20))
        use = row.get('use_for_fit', True)
        if not isinstance(use, bool):
            raise ValueError('标定用途应为布尔值')
        mask.append(use if mode == 'fit' else False)
    y, v, sigma, mask = np.array(y), np.array(v), np.array(sigma), np.array(mask)
    k = _kernel(v)
    diagnostics = dict(fit_count=0, heldout_count=0, fit_rmse_k=None, heldout_rmse_k=None, condition_number=None)
    warnings = ['独立 secant 角度模型；不求解组分温度，不改变观测时间，不校正太阳/方位角和光谱差异。']
    predicted = None
    if mode == 'fit':
        if mask.sum() < 2 or np.ptp(v[mask]) < 1e-6:
            raise ValueError('标定至少需要两个不同观测角度的 LST')
        if len({rows[i]['sensor'] for i in np.flatnonzero(mask)}) != 1:
            raise ValueError('标定观测必须来自同一传感器，避免将传感器偏差拟合成角度效应')
        times = []
        for row in rows:
            try:
                t = datetime.fromisoformat(row['time_utc'].replace('Z', '+00:00'))
                if t.utcoffset() is None: raise ValueError()
                times.append(t.timestamp())
            except (KeyError, TypeError, ValueError):
                raise ValueError('角度配对标定和留出检验需要带时区的时间') from None
        if max(times)-min(times) > 600:
            raise ValueError('时间跨度超过 10 分钟，请先进行时间配对')
        a = np.column_stack([np.ones(mask.sum()), k[mask]]) / sigma[mask, None]
        condition = float(np.linalg.cond(a))
        if not np.isfinite(condition) or condition > 1e4:
            raise ValueError('标定角度信息不足，矩阵病态')
        intercept, coefficient = np.linalg.lstsq(a, y[mask]/sigma[mask], rcond=None)[0]
        predicted = intercept+coefficient*k
        diagnostics.update(fit_count=int(mask.sum()), heldout_count=int((~mask).sum()),
            fit_rmse_k=float(np.sqrt(np.mean((predicted[mask]-y[mask])**2))),
            heldout_rmse_k=float(np.sqrt(np.mean((predicted[~mask]-y[~mask])**2))) if (~mask).any() else None,
            condition_number=condition)
        if mask.sum() == 2:
            warnings.append('两角度仅确定截距和角度系数，没有额外标定自由度；零残差不是精度证明。')
        if len({row['sensor'] for row in rows}) > 1:
            warnings.append('向另一传感器应用同一角度系数属于探索性迁移；留出差异仍含光谱和足迹影响。')
    else:
        coefficient = _number(payload.get('coefficient_k'), '已有角度系数 (K)', -100, 100)
    correction = coefficient*(_kernel(reference)-k)
    normalized = y+correction
    if not np.all(np.isfinite(normalized)) or np.any((normalized < 220) | (normalized > 365)):
        raise ValueError('归一化结果超出 220–365 K，请检查角度系数的适用范围')
    for i, row in enumerate(rows):
        row.update(lst_k=float(y[i]), correction_k=float(correction[i]), normalized_k=float(normalized[i]))
        if predicted is not None:
            row.update(predicted_k=float(predicted[i]), residual_k=float(y[i]-predicted[i]))
    return dict(schema='ls4t.angular-result/v1', route='normalization', method='secant',
        coefficient_mode=mode, coefficient_k=float(coefficient), reference_vza=reference,
        observations=rows, warnings=warnings, **diagnostics,
        provenance=deepcopy(payload.get('provenance', {})))
