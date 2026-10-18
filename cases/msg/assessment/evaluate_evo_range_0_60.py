"""Postprocess saved EVO predictions; no inversion or production changes."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

SOURCE = Path('C:/work/ls4t-msg/cases/official/results/production_assessment/joint_parameter_selection')
OUT = SOURCE / 'threshold_sensitivity/evo_range_0_60_joint'


def main():
    files = [SOURCE / n for n in ['selected_station_predictions.csv.gz',
             'frozen_reference_panel.csv.gz', 'selected_config.json', 'full_period_summary.csv']]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    pred, panel = pd.read_csv(files[0]), pd.read_csv(files[1])
    config = json.loads(files[2].read_text(encoding='utf8'))
    assert config['configuration']['hotspot'] == .25
    assert config['configuration']['lambda'] == 1000 and config['configuration']['delta'] == 3
    assert config['first_window'] == config['second_window'] == 5
    refs = ['soil_reference', 'canopy_reference', 'bulk', 'eligible_soil', 'eligible_canopy']
    x = pred.loc[pred.domain.eq('direct')].merge(panel[['site', 'time'] + refs],
                on=['site', 'time'], validate='one_to_one')
    assert set(x.site) == {'EVO'} and set(x.year) == {2017}
    time = pd.to_datetime(x.time, utc=True)
    assert x.hour.eq(time.dt.hour).all() and x.year.eq(time.dt.year).all()
    assert x.month.eq(time.dt.year * 100 + time.dt.month).all()
    assert x.hour.between(10, 16).all() and time.dt.month.between(8, 12).all()
    rows, retention, aggregates, instants = [], [], [], []
    for soil in ['sunlit_soil', 'background_soil']:
        cols = [soil, 'canopy', 'soil_reference', 'canopy_reference', 'bulk']
        start = x.valid & x.eligible_soil & x.eligible_canopy
        start &= np.isfinite(x[[soil, 'canopy', 'soil_reference', 'canopy_reference']]).all(axis=1)
        range_ok = x[cols].ge(0).all(axis=1) & x[cols].le(60).all(axis=1)
        soil_ok = (x[soil] - x.soil_reference).abs().le(10)
        canopy_ok = (x.canopy - x.canopy_reference).abs().le(10)
        selected = start & range_ok & soil_ok & canopy_ok
        retention.append(dict(soil=soil,initial_pairs=int(start.sum()),
            after_range=int((start & range_ok).sum()),after_joint_10K=int(selected.sum()),
            removed_by_range=int((start & ~range_ok).sum()),
            removed_by_10K_after_range=int((start & range_ok & ~(soil_ok & canopy_ok)).sum())))
        for rule, mask in [('existing_unfiltered', start), ('joint_0_60_10K', selected)]:
            z = x.loc[mask, ['site', 'time', 'year', 'month', 'hour'] + cols].copy()
            z = z.rename(columns={soil: 'soil_prediction', 'canopy': 'canopy_prediction'})
            if rule == 'joint_0_60_10K':
                assert z[['soil_prediction', 'canopy_prediction', 'soil_reference', 'canopy_reference', 'bulk']].ge(0).all().all()
                assert z[['soil_prediction', 'canopy_prediction', 'soil_reference', 'canopy_reference', 'bulk']].le(60).all().all()
                assert (z.soil_prediction - z.soil_reference).abs().le(10).all()
                assert (z.canopy_prediction - z.canopy_reference).abs().le(10).all()
            z['soil_type'], z['rule'] = soil, rule
            instants.append(z)
            for scale in ['monthly_hour', 'monthly_calendar']:
                keys = ['site', 'year', 'month'] + (['hour'] if scale == 'monthly_hour' else [])
                g = z.groupby(keys).agg(soil_prediction=('soil_prediction', 'mean'),
                    canopy_prediction=('canopy_prediction', 'mean'), soil_reference=('soil_reference', 'mean'),
                    canopy_reference=('canopy_reference', 'mean'), n_raw=('time', 'size'))
                g = g.loc[g.n_raw >= 3].copy()
                assert len(g) >= 3
                for comp in ['soil', 'canopy']:
                    error = g[comp + '_prediction'] - g[comp + '_reference']
                    # Verify means of paired residuals independently of separate temperature means.
                    zz = z.assign(residual=z[comp + '_prediction'] - z[comp + '_reference'])
                    check = zz.groupby(keys).residual.mean().reindex(g.index)
                    assert np.allclose(error, check, atol=1e-12, rtol=0)
                    rows.append(dict(soil_type=soil, rule=rule, scale=scale, component=comp,
                        rmse_K=float(np.sqrt(np.mean(error**2))), bias_K=float(error.mean()),
                        n_groups=len(g), n_raw=int(g.n_raw.sum())))
                g['soil_type'], g['rule'], g['scale'] = soil, rule, scale
                aggregates.append(g.reset_index())
    summary = pd.DataFrame(rows)
    old = pd.read_csv(files[3])
    old = old.loc[old.model.eq('joint_selected') & old.domain.eq('direct') & old.scale.isin(['monthly_hour', 'monthly_calendar'])]
    current = summary.loc[summary.soil_type.eq('sunlit_soil') & summary.rule.eq('existing_unfiltered')]
    match = current.merge(old, on=['scale', 'component'], validate='one_to_one')
    assert len(match) == 4
    difference = float((match.rmse_K - match.mean_site_rmse_K).abs().max())
    assert difference < 1e-10 and (match.n_raw_x == match.n_raw_y).all()
    assert hashes == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    OUT.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT / 'summary.csv', index=False)
    pd.DataFrame(retention).to_csv(OUT / 'retention.csv', index=False)
    pd.concat(aggregates, ignore_index=True).to_csv(OUT / 'monthly_pairs.csv.gz', index=False)
    pd.concat(instants, ignore_index=True).to_csv(OUT / 'instantaneous_pairs.csv.gz', index=False)
    audit = dict(status='passed', new_inversions=0, configuration=config,
        period='EVO 2017 Aug-Dec, 10-16 UTC', temperature_unit='Celsius',
        rule='Chosen soil prediction, canopy prediction, both component references and bulk LST all in inclusive [0,60]; both absolute residuals <=10 K before aggregation',
        monthly_min_pairs=3, baseline_reproduction_max_difference_K=difference, source_sha256=hashes,
        reference_caveat='Soil reference measures sunlit soil. Background comparison is a component-mismatched diagnostic, not direct background validation.')
    (OUT / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf8')
    names = {'sunlit_soil': '光照土壤', 'background_soil': '背景土壤'}
    scales = {'monthly_hour': '逐小时月均', 'monthly_calendar': '日间合并月均'}
    lines = ['# EVO追加0—60°C与联合10 K筛选', '',
        '仅重新聚合已有预测，没有重新反演。hotspot=0.25、λ=1000、δ=3，两阶段均5×5，使用物理单位修正后的结果。',
        '2017年8—12月、10—16 UTC。保持EVO原有小时范围；欧洲站点此前使用11—16 UTC。',
        '所选土壤预测、冠层预测、土壤实测、冠层实测及LST均须在[0,60]°C内；土壤与冠层预测相对各自实测的绝对偏差均≤10 K。任一条件不满足则整对时刻剔除，恰好10 K保留。',
        '先筛瞬时配对，再按年—月—小时或年—月聚合；每组至少3对。日间合并按有效瞬时记录平均，不是各小时均值等权平均。', '',
        '| 土壤方案 | 口径 | 土壤RMSE/K | 冠层RMSE/K | 月均组数 | 参与聚合瞬时对数 |',
        '|---|---|---:|---:|---:|---:|']
    for (soil, scale), g in summary.loc[summary.rule.eq('joint_0_60_10K')].groupby(['soil_type', 'scale'], sort=False):
        t = g.set_index('component')
        lines.append(f"| {names[soil]} | {scales[scale]} | {t.loc['soil','rmse_K']:.6f} | {t.loc['canopy','rmse_K']:.6f} | {int(t.loc['soil','n_groups'])} | {int(t.loc['soil','n_raw'])} |")
    lines += ['', '## 样本保留', '']
    for r in retention:
        lines.append(f"- {names[r['soil']]}：原有效配对{r['initial_pairs']}；范围筛选后{r['after_range']}；联合10 K筛选后{r['after_joint_10K']}。")
    lines += ['', 'EVO土壤实测对象是光照土壤；背景土壤也与同一光照土壤实测比较，仅为跨组分诊断，不能称为背景土壤的直接验证精度。两种方案可保留不同样本，冠层指标也随之变化。',
        '范围筛选会剔除部分实测超过60°C的记录，不能直接判定这些观测错误。按实测偏差筛选后的精度仅描述保留样本，不能代表未筛选产品精度。',
        '无追加筛选的对照保存在summary.csv中，原光照土壤与冠层月均指标已逐项复核一致。']
    (OUT / 'EVO_0至60度与10K联合筛选.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
    print(summary.to_string(index=False))
    print(pd.DataFrame(retention).to_string(index=False))
    print('AUDIT PASSED', OUT)


if __name__ == '__main__':
    main()
