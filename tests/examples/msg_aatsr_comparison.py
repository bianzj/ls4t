"""Controlled transfer of AATSR solvers to real simultaneous MSG dual views.

No production files are changed. All solvers use physical 10.5 um radiance.
The two-component soil is NOT the sunlit soil measured at EVO.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
from scipy.ndimage import uniform_filter
from scipy.optimize import minimize

from msg_evo_sample import ROOT, SAMPLE, load_sample, prepare_frame, sha256, write_stack
from base.lsct import set_weights
from base.radiometry import planck_radiance, inverse_planck
from base.rt.hotspot import hotspot_layer

WL = 10.5
METHODS = {
    'ls2': 2, 'ridge2': 2, 'slsqp_no_delta2': 2, 'slsqp2': 2, 'map_constant2': 2,
    'quadratic2': 2, 'map_quadratic2': 2, 'map_exclude_center2': 2,
    'ls3': 3, 'slsqp_no_delta3': 3, 'slsqp3': 3, 'msg_iter3': 3, 'msg_iter3_commonmask': 3,
}
DEFAULT_REFERENCE = Path('C:/work/ls4t-msg/cases/official/results/production_assessment/'
                         'joint_parameter_selection/frozen_reference_panel.csv.gz')


def planck(t):
    return planck_radiance(WL, t)


def least_squares(a, b, ridge=0.):
    if len(b) < a.shape[1] or np.linalg.matrix_rank(a) < a.shape[1] or np.linalg.cond(a) > 1e6:
        return np.full(a.shape[1], np.nan)
    if ridge:
        return np.linalg.solve(a.T @ a + ridge * np.eye(a.shape[1]), a.T @ b)
    return np.linalg.lstsq(a, b, rcond=None)[0]


def quadratic(w, y, good):
    yy, xx = np.mgrid[-2:3, -2:3]
    basis = np.stack([np.ones_like(xx), xx, yy, xx*yy, xx*xx, yy*yy], -1)
    design = (w[..., :, None] * basis[:, :, None, None, :]).reshape(-1, 12)
    coeff = least_squares(design[good.ravel()], y.ravel()[good.ravel()]).reshape(2, 6)
    return coeff[:, 0], np.einsum('xyk,ck->xyc', basis, coeff)


def posterior(a, b, prior):
    precision = np.diag([.5, 1.])
    return np.linalg.solve(a.T @ a / .05 + precision,
                           a.T @ b / .05 + precision @ prior)


def constrained(a, b, center_lst, spatial_weights, delta_constraint=True):
    """AATSR SLSQP assumptions, with BOTH Planck terms at MSG's wavelength.

    Keep the legacy approximate radiance-difference and bracketing constraints;
    explicitly reject unsuccessful or infeasible optimizer results.
    """
    m = a.shape[1]
    mean = np.mean(center_lst)
    obs_b = planck(center_lst)
    offsets = [(-10, 40), (-10, 10)] if m == 2 else [(-10, 40), (-30, 30), (-10, 20)]
    bounds = [(float(planck(mean+lo)), float(planck(mean+hi))) for lo, hi in offsets]
    ds = [(-5, 30)] if m == 2 else [(5, 40), (-15, 15)]
    limits = [(float(planck(mean+lo/2)-planck(mean-lo/2)),
               float(planck(mean+hi/2)-planck(mean-hi/2))) for lo, hi in ds]

    def cons(x):
        out = [np.max(x)-np.max(obs_b), np.min(obs_b)-np.min(x)]
        for k, (lo, hi) in enumerate(limits if delta_constraint else []):
            out.extend([x[k]-x[k+1]-lo, hi-x[k]+x[k+1]])
        return np.array(out)

    def fun(x):
        return np.sum(spatial_weights * (a @ x-b)**2)

    def jac(x):
        return 2 * a.T @ (spatial_weights * (a @ x-b))

    x0 = np.array([obs_b.max()+5, obs_b.min()-3]) if m == 2 else np.array([obs_b.max()+10, obs_b.min()-5, obs_b.mean()])
    x0 = np.clip(x0, np.array(bounds)[:, 0], np.array(bounds)[:, 1])
    # max/min bracketing is non-convex: the historical warm-soil initial point
    # can trap an otherwise unconstrained cold-soil solution in the wrong branch.
    # Use the SAME legacy and LS starts in the on/off ablation, selecting by SSE.
    starts = [x0]
    ls = least_squares(a*np.sqrt(spatial_weights[:,None]), b*np.sqrt(spatial_weights))
    if np.isfinite(ls).all():
        starts.append(np.clip(ls,np.array(bounds)[:,0],np.array(bounds)[:,1]))
    feasible = []
    for start in starts:
        result = minimize(fun, start, jac=jac, method='SLSQP', bounds=bounds,
                          constraints={'type': 'ineq', 'fun': cons},
                          options={'ftol': 1e-9, 'maxiter': 150})
        if result.success and np.min(cons(result.x)) >= -1e-6:
            feasible.append(result.x)
    return min(feasible,key=fun) if feasible else np.full(m,np.nan)


def solve_window(y, w, center_lst, method, exclude_center=False):
    good = np.isfinite(y) & np.isfinite(w).all(-1)
    if exclude_center:
        good[2, 2] = False
    m = w.shape[-1]
    if np.sum(good.all(-1)) < 10:
        return np.full(m, np.nan)
    a, b = w[good], y[good]
    if method in ('ls2', 'ls3', 'ridge2'):
        return least_squares(a, b, .01 if method == 'ridge2' else 0.)
    if method.startswith('slsqp'):
        sw = np.broadcast_to(set_weights(5)[..., None], y.shape)[good]
        return constrained(a, b, center_lst, sw, delta_constraint='no_delta' not in method)
    if method in ('quadratic2', 'map_quadratic2'):
        center, surface = quadratic(w, y, good)
        if method == 'quadratic2':
            return center
        # Match station Bayesian prior: weighted mean of valid curve predictions.
        kernel = np.array([[1,4,7,4,1],[4,16,26,16,4],[7,26,41,26,7],
                           [4,16,26,16,4],[1,4,7,4,1]], dtype=float)
        keep = good.all(-1) & ((surface > 4.5) & (surface < 20)).all(-1)
        prior = np.average(surface[keep], axis=0, weights=kernel[keep]) if keep.sum() > 1 else center
    else:
        if method == 'map_exclude_center2':
            good[2, 2] = False
            if good.all(-1).sum() < 10:
                return np.full(2, np.nan)
        prior = least_squares(w[good], y[good])
    return posterior(w[2, 2], y[2, 2], prior)


def production_functions():
    # Extract only pure numerical functions: the historical module executes CLI/I/O on import.
    path = ROOT / 'cases/msg/msg_lsct_iter.py'
    wanted = {'solve_2x2_system_5x5', 'solve_constrained_vectorized2', 'solve_joint_vectorized_with_prior'}
    tree = ast.parse(path.read_text(encoding='utf-8'))
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    assert {n.name for n in selected} == wanted
    namespace = {'np': np, 'uniform_filter': uniform_filter}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def msg_iter(y, w, functions, common_residual_mask=False):
    """Current repository production: 3x3 / 5x5, delta=3 radiance, lambda=100."""
    solve = functions['solve_2x2_system_5x5']
    sun, _ = solve(y[..., 0], y[..., 1], w[..., 0, 0], w[..., 0, 1:].sum(-1),
                   w[..., 1, 0], w[..., 1, 1:].sum(-1), size=3)
    residual = y - w[..., 0]*sun[..., None]
    wr = w.copy()
    if common_residual_mask:
        # Stage-one failures create NEW missing residuals. All second-stage
        # normal-equation terms must omit their weights as well as observations.
        wr[~np.isfinite(residual).all(-1)] = np.nan
    shade, veg = functions['solve_constrained_vectorized2'](
        residual[..., 0], residual[..., 1], wr[..., 0, 1], wr[..., 0, 2],
        wr[..., 1, 1], wr[..., 1, 2], sun, dif=3.)
    shade = np.minimum(shade, sun)
    veg = np.where(veg > planck(350.), shade, veg)
    result = functions['solve_joint_vectorized_with_prior'](
        y[..., 0], y[..., 1], w.reshape(*w.shape[:2], 6),
        np.stack([sun, shade, veg], -1), lmbda=100.)
    return np.stack(result, -1)


def three_weights(manifest, data, index, valid):
    # Match current local MSG production hotspot=.2 for ALL three-component methods.
    stamp = manifest['timestamps_utc'][index]
    lai = data['lai'][manifest['lai_dates_utc'].index(stamp[:8])]
    st = data['static']
    weights = []
    for view in ('euro', 'iodc'):
        vza, vaa = st[f'vza_{view}_deg'], st[f'vaa_{view}_deg']
        sza, saa = data['solar_zenith_deg'][index], data['solar_azimuth_deg'][index]
        raa = np.abs((saa-vaa+180) % 360-180)
        sun = hotspot_layer(lai, .2, vza, np.where(sza < 90, sza, np.nan), raa)
        gap = np.exp(-.5*lai/np.cos(np.radians(vza)))
        weights.append(np.stack([st['soil_emissivity']*sun, st['soil_emissivity']*(gap-sun),
                                 st['vegetation_emissivity']*(1-gap)], -1))
    w = np.stack(weights, -2)
    w[~valid] = np.nan
    return w


def metric(pred, ref):
    e = np.asarray(pred)-np.asarray(ref)
    e = e[np.isfinite(e)]
    return {'n': len(e), 'rmse_k': float(np.sqrt(np.mean(e*e))) if len(e) else None,
            'bias_k': float(np.mean(e)) if len(e) else None}


def evaluate_reference(center, source, output):
    if not source.is_file():
        return {'available': False, 'source': str(source)}, []
    panel = pd.read_csv(source)
    panel = panel.loc[panel.site.eq('EVO') & panel.time.str.startswith('2017-10')].copy()
    panel['timestamp_utc'] = pd.to_datetime(panel.time, utc=True).dt.strftime('%Y%m%d%H%M')
    assert not panel.timestamp_utc.duplicated().any()
    assert panel.year.eq(2017).all() and panel.month.eq(201710).all()
    panel.to_csv(output/'reference_october.csv', index=False)
    rows = []
    for name, m in METHODS.items():
        baseline = 'ls2' if m == 2 else 'msg_iter3'
        cur = center[center.method.eq(name)].merge(panel, on='timestamp_utc', validate='one_to_one')
        base = center[center.method.eq(baseline)][['timestamp_utc','component_0_k','vegetation_k']]
        cur = cur.merge(base, on='timestamp_utc', suffixes=('', '_baseline'), validate='one_to_one')
        for comp, col, ref in [('canopy','vegetation_k','canopy_reference'),
                                ('sunlit_soil' if m == 3 else 'bulk_soil_cross_component', 'component_0_k', 'soil_reference')]:
            # Do not use old input_eligible or old prediction-dependent screens.
            reference = cur[ref]+273.15
            good = reference.between(250,350) & np.isfinite(cur[col]) & np.isfinite(cur[col+'_baseline'])
            a = metric(cur.loc[good,col],reference[good])
            b = metric(cur.loc[good,col+'_baseline'],reference[good])
            rows.append(dict(method=name, baseline=baseline, component=comp, **a,
                             baseline_rmse_k=b['rmse_k'], dates=int(cur.loc[good,'date'].nunique()),
                             delta_rmse_k=(a['rmse_k']-b['rmse_k']) if a['n'] else None))
    pd.DataFrame(rows).to_csv(output/'ground_paired_metrics.csv', index=False)
    return {'available': True, 'source': str(source), 'sha256': sha256(source),
            'october_rows': len(panel), 'units_in_source': 'Celsius',
            'matching': 'exact UTC hour; UTC clock assumed by historical source',
            'reference': 'cached radiometric correction: emissivity .985, sky 250 K, 10.5 um',
            'limits': 'Raw E:/field/Evo-2017.csv unavailable. Cached panel is previously assembled, not independent new observations. No error-based trimming. Two-component soil differs from sunlit reference.'}, rows


def constraint_ablation(temps, errs, center, output):
    rows = []
    panel_path = output/'reference_october.csv'
    panel = pd.read_csv(panel_path, dtype={'timestamp_utc': str}) if panel_path.exists() else None
    for m in (2,3):
        off, on = f'slsqp_no_delta{m}', f'slsqp{m}'
        shared = np.isfinite(temps[off]).all(-1) & np.isfinite(temps[on]).all(-1)
        for name in (off,on):
            t = temps[name][shared]
            delta = t[:,0]-t[:,1]
            violation = ((delta < -5) | (delta > 30)) if m==2 else ((delta < 5) | (delta > 40) | (np.abs(t[:,1]-t[:,2])>15))
            record = dict(components=m,method=name,common_n=int(shared.sum()),
                          delta_01_mean_k=float(np.mean(delta)),delta_01_min_k=float(np.min(delta)),
                          delta_01_max_k=float(np.max(delta)),nominal_temperature_limit_exceedances=int(violation.sum()),
                          reconstruction_rmse_k=float(np.sqrt(np.mean(errs[name][shared]**2))))
            if m==3:
                record['delta_shade_veg_mean_k']=float(np.mean(t[:,1]-t[:,2]))
            if panel is not None:
                a = center[center.method.eq(name)].merge(panel,on='timestamp_utc',validate='one_to_one')
                other = center[center.method.eq(on if name==off else off)][['timestamp_utc','vegetation_k','component_0_k']]
                a = a.merge(other,on='timestamp_utc',suffixes=('','_other'),validate='one_to_one')
                for comp,col,ref in [('canopy','vegetation_k','canopy_reference'),('sunlit_soil' if m==3 else 'bulk_soil_cross_component','component_0_k','soil_reference')]:
                    reference=a[ref]+273.15
                    keep=reference.between(250,350)&np.isfinite(a[col])&np.isfinite(a[col+'_other'])
                    stats=metric(a.loc[keep,col],reference[keep])
                    record.update({f'{comp}_{k}':v for k,v in stats.items()})
            rows.append(record)
    pd.DataFrame(rows).to_csv(output/'constraint_ablation.csv',index=False)
    return rows


def write_report(output, rows, ground, cv, ablation):
    def table(items, columns):
        out=['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']
        for row in items:
            def fmt(v):
                return f'{v:.3f}' if isinstance(v,float) else str(v) if v is not None else '—'
            out.append('| '+' | '.join(fmt(row.get(k)) for k in columns)+' |')
        return '\n'.join(out)
    text='''# MSG 数据迁移 AATSR 方法：真实样例对照

数据：EVO，2017 年 10 月，10×10 像元、744 个逐小时时次，EURO/IODC 同时观测。
仅计算白天。比较区域为裁剪内部 4×4，保证 MSG 两阶段算法需要的 7×7 支持完整；
中心输入有效，5×5 至少 10 个双视角有效像元，LST 和输出限定 250–350 K。
全部使用 10.5 μm 物理 Planck、同一 LAI、发射率与输入掩膜；没有 NDVI，未做 NDVI 对照。

## 方法

- `ls2`：现有样例两组分窗口最小二乘基准；`ridge2`：AATSR Ridge，alpha=.01。
- `slsqp_no_delta2/3` 与 `slsqp2/3`：相同空间权重、初值、组分温度边界及观测包围约束，仅开关组分温差约束。检查收敛及约束残差后才接收结果。两者均使用历史初值和 LS 初值，选目标函数更小的可行解，避免 max/min 包围约束将解困在错误温度排序分支；这是本试验对历史单初值调用的适配。
- `map_constant2`：窗口常量先验 + 中心双角度 MAP；`map_exclude_center2` 从先验排除中心，是新增控制实验。
- `quadratic2`：空间辐射二次曲面；`map_quadratic2`：曲面先验加权平均后作 MAP。试验适配器修正历史 scipy.lstsq 的 rcond 接口错误。
- `ls3`：三组分窗口 LS；`msg_iter3`：当前本仓库 MSG 数值函数，第一阶段 3×3、第二阶段 5×5、hotspot=.2、lambda=100、辐射差阈值=3。所有三组分方法共享这一结构权重。
- `msg_iter3_commonmask`：附加缺测诊断。第一阶段失败后，第二阶段除剔除残差外也同步剔除相应权重；原函数在这种情况下的正规方程支持可能不一致。保留原算法结果，并列这个修正控制，不将其静默替换为基准。
- 本试验迁移的是求解思路；未直接运行硬编码 AATSR 批处理，也未移植完整 LAI-RT 模型。

## 覆盖率与重建诊断

重建 RMSE 为中心两视角 LST 的 K 单位误差。核心两组分及三组分各在共同有效集合计算；二次曲面和排除中心变体进一步与其自身有效集合相交。重建观测属于拟合内诊断，不能作为组分实测精度。

'''
    text+=table(rows,['method','valid','eligible','coverage','center_valid','common_n','reconstruction_rmse_k'])
    text+='\n\n## EVO 地面配对\n\n使用既有参考缓存的 2017-10 数据，精确整点 UTC 匹配，不按预测误差筛选，不重新调参。原始 E 盘不在线。缓存温度为已做发射率 .985、天空 250 K 修正的辐射温度；仪器时钟沿用原流程 UTC 假定。冠层和三组分阳照土壤可对应参考对象，两组分平均土壤对阳照土壤只作跨组分诊断。每行与自身基准在相同时间配对，n 不同时不能直接横向排序。\n\n'
    text+=table(ground,['method','baseline','component','n','dates','rmse_k','baseline_rmse_k','delta_rmse_k'])
    text+='\n\n## 单独增加温差约束\n\n两组分名义 Ts−Tv 为 −5~30 K；三组分名义阳照−阴影为 5~40 K、阴影−植被为 −15~15 K。实际约束围绕中心平均 LST 换算成辐射差，故最终温差可能略超出名义 K 限值；下表按严格温度限值计数，不能与优化不收敛混为一谈。\n\n'
    text+=table(ablation,['components','method','common_n','delta_01_mean_k','nominal_temperature_limit_exceedances','canopy_n','canopy_rmse_k','sunlit_soil_rmse_k','reconstruction_rmse_k'])
    text+='\n\n## 留出中心像元观测\n\n从邻域拟合中移除中心的两个观测，再预测中心 LST；所有方法按共同可预测集合评价。这衡量空间预测，不是组分温度真值验证。MAP 使用中心观测，未将其拟合内残差伪装为留出结果。\n\n'
    text+=table(cv,['method','n','heldout_lst_rmse_k'])
    text+='\n\n## 解释范围\n\n单站单月，中心地面配对只有少量日期，不能推广到全 MSG 区域或其他季节。缓存参考来自以前分析过的月份，属于探索性迁移比较。这里只比较当前 ls4t 仓库 MSG 算法，不等于对外发布集合的其他版本。原始样例全部文件 SHA-256 已逐一验证；源代码、输入清单和参考缓存哈希保存于 summary.json。所有原始温度栅格、中心序列、逐方法指标及约束消融指标保存在本目录。\n'
    (output/'REPORT.md').write_text(text,encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=Path, default=SAMPLE)
    parser.add_argument('--output', type=Path, default=ROOT/'tests/outputs/msg_aatsr_201710')
    parser.add_argument('--reference-panel', type=Path, default=DEFAULT_REFERENCE)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest, data = load_sample(args.sample)
    assert manifest['period'] == '2017-10' and manifest['shape'] == [10,10]
    for rel, item in manifest['files'].items():
        assert sha256(args.sample/rel) == item['sha256'], rel
    shape = (744, 10, 10)
    temps = {k: np.full((*shape,m), np.nan) for k,m in METHODS.items()}
    errs = {k: np.full((*shape,2), np.nan) for k in METHODS}
    cv = {k: [] for k in ('ls2','ridge2','quadratic2')}
    eligibility = np.zeros(shape, bool)
    timing = dict.fromkeys(METHODS, 0.)
    functions = production_functions()
    for idx, stamp in enumerate(manifest['timestamps_utc']):
        if not np.any(data['solar_zenith_deg'][idx] < 90):
            continue
        y, w2, valid = prepare_frame(manifest,data,idx,2)
        w3 = three_weights(manifest,data,idx,valid)
        valid &= np.isfinite(w3).all((-1,-2)) & (w3 >= 0).all((-1,-2))
        y[~valid], w2[~valid], w3[~valid] = np.nan, np.nan, np.nan
        lst = np.stack([data['lst_euro'][idx],data['lst_iodc'][idx]],-1)
        production = {}
        for name in ('msg_iter3','msg_iter3_commonmask'):
            start = time.perf_counter()
            with np.errstate(all='ignore'):
                production[name] = msg_iter(y,w3,functions,common_residual_mask=name.endswith('commonmask'))
            timing[name] += time.perf_counter()-start
        # 3x3 then 5x5 MSG uses a 7x7 footprint: score only the common unpadded 4x4 interior.
        for row in range(3,7):
            for col in range(3,7):
                win = (slice(row-2,row+3),slice(col-2,col+3))
                if not valid[row,col] or valid[win].sum() < 10:
                    continue
                eligibility[idx,row,col] = True
                for name,m in METHODS.items():
                    w = w2 if m == 2 else w3
                    start = time.perf_counter()
                    rad = production[name][row,col] if name in production else solve_window(y[win],w[win],lst[row,col],name)
                    if name not in production:
                        timing[name] += time.perf_counter()-start
                    t = inverse_planck(WL,rad)
                    if np.isfinite(t).all() and (t>=250).all() and (t<=350).all():
                        temps[name][idx,row,col] = t
                        reconstructed = inverse_planck(WL,(w[row,col]@rad)/w[row,col].sum(-1))
                        errs[name][idx,row,col] = reconstructed-lst[row,col]
                for name in cv:
                    rad = solve_window(y[win],w2[win],lst[row,col],name,exclude_center=True)
                    pred = inverse_planck(WL,(w2[row,col]@rad)/w2[row,col].sum(-1))
                    cv[name].append([idx,row,col,*pred,*lst[row,col]])
        if int(stamp[8:10]) == 12 and int(stamp[6:8]) % 5 == 0:
            print(f'completed {stamp}', flush=True)
    rows, center = [], []
    common2 = np.logical_and.reduce([np.isfinite(temps[k]).all(-1) for k in ('ls2','ridge2','slsqp2','map_constant2')])
    common3 = np.logical_and.reduce([np.isfinite(temps[k]).all(-1) for k in ('ls3','slsqp3','msg_iter3')])
    for name,m in METHODS.items():
        good = np.isfinite(temps[name]).all(-1)
        shared = (common2 if m == 2 else common3) & good
        baseline = 'ls2' if m == 2 else 'msg_iter3'
        paired = good & np.isfinite(temps[baseline]).all(-1)
        rows.append(dict(method=name,components=m,eligible=int(eligibility.sum()),valid=int(good.sum()),
                         coverage=float(good.sum()/eligibility.sum()),center_valid=int(good[:,5,5].sum()),
                         common_n=int(shared.sum()),reconstruction_rmse_k=float(np.sqrt(np.mean(errs[name][shared]**2))) if shared.any() else None,
                         paired_baseline=baseline,paired_n=int(paired.sum()),
                         paired_temperature_change_rms_k=float(np.sqrt(np.mean((temps[name][paired]-temps[baseline][paired])**2))) if paired.any() else None,
                         elapsed_seconds=timing[name]))
        for idx,stamp in enumerate(manifest['timestamps_utc']):
            center.append(dict(timestamp_utc=stamp,method=name,component_0_k=temps[name][idx,5,5,0],
                               vegetation_k=temps[name][idx,5,5,-1],
                               shaded_soil_k=temps[name][idx,5,5,1] if m==3 else np.nan))
        labels = ['soil','vegetation'] if m==2 else ['sunlit_soil','shaded_soil','vegetation']
        for j,label in enumerate(labels):
            write_stack(args.output/name/(label+'.tif'),temps[name][...,j],manifest['timestamps_utc'],
                        manifest['geotransform'],manifest['projection_wkt'],unit='K')
    pd.DataFrame(rows).to_csv(args.output/'method_metrics.csv',index=False)
    center = pd.DataFrame(center)
    center.to_csv(args.output/'center_predictions.csv',index=False)
    refmeta, ground = evaluate_reference(center,args.reference_panel,args.output)
    cv_arrays = {k:np.asarray(v) for k,v in cv.items()}
    cv_good = np.logical_and.reduce([np.isfinite(v[:,3:5]).all(-1) for v in cv_arrays.values()])
    cv_summary = []
    for name,values in cv_arrays.items():
        np.save(args.output/(name+'_leave_center_out.npy'), values)
        err = values[cv_good,3:5]-values[cv_good,5:7]
        cv_summary.append(dict(method=name,n=int(cv_good.sum()),heldout_lst_rmse_k=float(np.sqrt(np.mean(err**2)))))
    pd.DataFrame(cv_summary).to_csv(args.output/'heldout_metrics.csv',index=False)
    ablation=constraint_ablation(temps,errs,center,args.output)
    write_report(args.output,rows,ground,cv_summary,ablation)
    protocol = dict(period='2017-10',site='EVO',input_shape=list(shape),wavelength_um=WL,
                    evaluated_pixels='rows/columns 3..6 (zero-based); full 7x7 support',
                    mask='daylight, common finite views, LST/output 250..350 K, LAI >= .05, >=10 valid dual-view pixels per 5x5',
                    structure='2c LAI gap; all 3c use MSG hotspot .2; no NDVI supplied',
                    production_baseline='current C:/work/ls4t cases/msg/msg_lsct_iter.py numerical functions, 3x5 windows, lambda100, delta3; physical Planck and common mask adapter',
                    adaptations='MSG 10.5um, physical Planck, common mask, SLSQP convergence checks and same legacy/LS multi-start for constraint on/off; quadratic uses np.linalg.lstsq fixing scipy rcond error. No production solver edited.',
                    bayesian='Cm=diag(2,1), Cd=.05 I; map_constant and map_quadratic reuse center observations; exclude_center is an additional experimental control',
                    reference=refmeta, metrics=rows, ground_metrics=ground, heldout=cv_summary,constraint_ablation=ablation,
                    hashes={str(p):sha256(p) for p in [Path(__file__),ROOT/'tests/examples/msg_evo_sample.py',
                            args.sample/'manifest.json',ROOT/'cases/msg/msg_lsct_iter.py',ROOT/'base/lsct.py',ROOT/'base/radiometry.py']})
    (args.output/'summary.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(pd.DataFrame(rows).to_string(index=False))
    print(pd.DataFrame(ground).to_string(index=False))
    print(pd.DataFrame(cv_summary).to_string(index=False))


if __name__ == '__main__':
    main()
