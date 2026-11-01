"""Small independent workbench adapters; raster production stays in the task queue."""
from copy import deepcopy

import numpy as np

from base.known_inputs import _lst, number, validate_fixed
from base.normalization.time import normalize_local_solar_time
from base.normalization.space import aggregate_to_grid
from base.normalization.workbench import normalize_observations


def observations(payload):
    if not isinstance(payload, dict):
        raise ValueError('配置必须是对象')
    rows = payload.get('observations')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 4096 or not all(isinstance(o, dict) for o in rows):
        raise ValueError('需要 1–4096 条有效观测')
    return deepcopy(rows)


def run_surface(payload):
    rows = observations(payload)
    fixed = deepcopy(payload.get('fixed', {}))
    validate_fixed(fixed)
    overrides = fixed.get('sensors', {})
    if not isinstance(overrides, dict):
        raise ValueError('传感器发射率配置必须是对象')
    for sensor, values in overrides.items():
        if sensor not in ('AHI', 'SLSTR') or not isinstance(values, dict) or set(values) - {'soil_emissivity', 'vegetation_emissivity'}:
            raise ValueError('传感器配置只允许 AHI/SLSTR 的土壤和植被发射率')
    for o in rows:
        if o.get('cloud', False):
            raise ValueError('地表温度反演需要无云观测')
        if o.get('sensor') not in ('AHI', 'SLSTR'):
            raise ValueError('传感器需要 AHI 或 SLSTR')
        o['vza'] = number(o.get('vza'), '观测天顶角', 0, 80)
        current = dict(fixed, **overrides.get(o['sensor'], {}))
        validate_fixed(current)
        o['lst_k'], o['method'] = _lst(o, current)
    return dict(schema='ls4t.surface-result/v1', route='surface', fixed=fixed,
                observations=rows, warnings=['仅输出逐观测地表温度，不求解组分温度；已有 LST 不重复大气校正。'])


def hour(value, label):
    h = number(value, label, 0, 24)
    if h == 24:
        raise ValueError(f'{label} 必须小于 24')
    return h


def run_time(payload):
    rows = observations(payload)
    ref = hour(payload.get('reference_hour'), '参考地方太阳时')
    amp = number(payload.get('amplitude_k'), '日变化振幅', 0, 100)
    peak = hour(payload.get('peak_hour'), '峰值地方太阳时')
    for o in rows:
        t = number(o.get('lst_k'), 'LST (K)', 150, 400)
        h = hour(o.get('hour'), '观测地方太阳时')
        out = float(normalize_local_solar_time(t, h, amp, peak, reference_hour=ref))
        if not np.isfinite(out):
            raise ValueError('归一化温度超出 150–400 K；请检查日变化参数')
        o.update(lst_k=t, hour=h, normalized_k=out, correction_k=out-t)
    return dict(schema='ls4t.time-result/v1', route='time', reference_hour=ref,
                amplitude_k=amp, peak_hour=peak, observations=rows,
                warnings=['24 小时单谐波模型，振幅和峰值时刻由外部提供；时间均为地方太阳时。',
                          '此路线不改变观测角度或空间网格，也不模拟云影响和非对称昼夜变化。'])


def integer(value, label, low, high):
    v = number(value, label, low, high)
    if not v.is_integer():
        raise ValueError(f'{label} 必须是整数')
    return int(v)


def run_space(payload):
    rows = observations(payload)
    shape = payload.get('target_shape')
    if not isinstance(shape, list) or len(shape) != 2:
        raise ValueError('target_shape 需要 [行数, 列数]')
    shape = tuple(integer(x, '目标网格维数', 1, 256) for x in shape)
    for o in rows:
        o['lst_k'] = number(o.get('lst_k'), 'LST (K)', 150, 400)
        o['row'] = integer(o.get('row'), '目标行号', 0, shape[0]-1)
        o['column'] = integer(o.get('column'), '目标列号', 0, shape[1]-1)
        o['weight'] = number(o.get('weight', 1), '权重', 1e-12, 1e12)
    grid, support = aggregate_to_grid(*[np.array([o[k] for o in rows]) for k in ('lst_k', 'row', 'column')],
                                      shape, weights=np.array([o['weight'] for o in rows]))
    return dict(schema='ls4t.space-result/v1', route='space', target_shape=list(shape),
                grid_k=[[float(x) if np.isfinite(x) else None for x in row] for row in grid],
                support=support.tolist(), observations=rows,
                warnings=['按明确的目标行列号加权聚合温度；空格为缺测，权重和表示支持量。',
                          '这是已有网格映射的温度聚合，不自动重投影、降尺度或进行辐射混合。'])


def run_batch(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('jobs'), list) or not 1 <= len(payload['jobs']) <= 64:
        raise ValueError('批处理需要 1–64 个独立归一化配置')
    results = []
    routes = {'time':run_time, 'space':run_space, 'normalization':normalize_observations}
    for i, job in enumerate(payload['jobs']):
        item = dict(index=i, name=job.get('name', f'任务 {i+1}') if isinstance(job, dict) else f'任务 {i+1}')
        try:
            if not isinstance(job, dict) or job.get('route') not in routes:
                raise ValueError('只接受 time、space、normalization 三种归一化配置')
            item.update(status='done', result=routes[job['route']](job))
        except Exception as error:
            # Each user-supplied job is an isolation boundary; later jobs still run.
            item.update(status='failed', error=str(error))
        results.append(item)
    return dict(schema='ls4t.normalization-batch/v1', route='normalization-batch', jobs=results,
                done=sum(j['status']=='done' for j in results), failed=sum(j['status']=='failed' for j in results))
