"""Post-selection threshold sensitivity; never rerank parameters on filtered errors."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent / 'results/production_assessment/joint_parameter_selection'
OUT = ROOT / 'threshold_sensitivity'

def main():
    OUT.mkdir(exist_ok=True)
    p = pd.read_csv(ROOT / 'matched_predictions.csv.gz')
    p = p.loc[p.model.eq('joint_selected') & p.domain.eq('indirect')].copy()
    assert not p.duplicated(['site', 'time', 'component']).any()
    p['error'] = p.prediction - p.reference
    p['pass10'] = p.error.abs().le(10)
    joint = p.groupby(['site', 'time']).agg(n=('component', 'nunique'), ok=('pass10', 'all'))
    joint['joint_ok'] = joint.n.eq(2) & joint.ok
    p = p.merge(joint[['joint_ok']], on=['site', 'time'], validate='many_to_one')
    counts = p.groupby(['site', 'component']).agg(n_before=('error', 'size'),
        n_pass10=('pass10', 'sum'), bias_K=('error', 'mean'),
        n_positive_over10=('error', lambda x: int((x > 10).sum())),
        n_negative_over10=('error', lambda x: int((x < -10).sum())))
    counts['removed_fraction'] = 1 - counts.n_pass10 / counts.n_before
    counts.to_csv(OUT / 'station_threshold_counts.csv')
    rows = []
    for split in ['all', 'development', 'validation']:
        z = p if split == 'all' else p.loc[p.split.eq(split)]
        for mode in ['unfiltered', 'instant_component_10K', 'instant_joint_10K', 'monthly_only_10K']:
            a = z.loc[z.pass10] if mode == 'instant_component_10K' else z.loc[z.joint_ok] if mode == 'instant_joint_10K' else z
            for (site, component), b in a.groupby(['site', 'component']):
                for scale in ['instantaneous', 'monthly_hour', 'monthly_calendar']:
                    if mode == 'monthly_only_10K' and scale == 'instantaneous':
                        continue
                    if scale == 'instantaneous':
                        g = b[['prediction', 'reference']].copy(); g['n'] = 1
                    else:
                        keys = ['month'] + (['hour'] if scale == 'monthly_hour' else [])
                        g = b.groupby(keys).agg(prediction=('prediction', 'mean'), reference=('reference', 'mean'), n=('error', 'size'))
                        g = g.loc[g.n.ge(3)]
                    if mode == 'monthly_only_10K':
                        g = g.loc[(g.prediction - g.reference).abs().le(10)]
                    if len(g) < 3:
                        continue
                    e = g.prediction - g.reference
                    if mode != 'unfiltered':
                        assert e.abs().max() <= 10 + 1e-10
                    rows.append(dict(split=split, mode=mode, site=site, component=component, scale=scale,
                        rmse_K=float(np.sqrt(np.mean(e**2))), bias_K=float(e.mean()), n=len(g), n_raw=int(g.n.sum())))
    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / 'station_metrics.csv', index=False)
    summary = metrics.groupby(['split', 'mode', 'component', 'scale'], as_index=False).agg(
        sites=('site', 'size'), mean_site_rmse_K=('rmse_K', 'mean'), mean_site_bias_K=('bias_K', 'mean'),
        n_groups=('n', 'sum'), n_raw=('n_raw', 'sum'))
    summary.to_csv(OUT / 'summary.csv', index=False)
    old = pd.read_csv(ROOT / 'full_period_summary.csv')
    old = old.loc[old.model.eq('joint_selected') & old.domain.eq('indirect')]
    new = summary.loc[summary.split.eq('all') & summary['mode'].eq('unfiltered')]
    check = old.merge(new, on=['component', 'scale'], suffixes=('_old', '_new'))
    assert len(check) == 6
    maxdiff = float((check.mean_site_rmse_K_old - check.mean_site_rmse_K_new).abs().max())
    assert maxdiff < 1e-9
    totals = counts.groupby('component')[['n_before', 'n_pass10', 'n_positive_over10', 'n_negative_over10']].sum()
    totals['removed_percent'] = 100 * (1 - totals.n_pass10 / totals.n_before)
    totals.to_csv(OUT / 'threshold_totals.csv')
    (OUT / 'audit.json').write_text(json.dumps(dict(status='passed', baseline_max_difference_K=maxdiff,
        parameter_configuration_unchanged=True, threshold_K=10,
        scope='post-selection sensitivity only; no inversion rerun or parameter reranking'), indent=2), encoding='utf8')
    def table(d):
        return d.round(3).to_csv(index=False)
    text = '''# 欧洲间接站点10 K阈值敏感性

固定已选参数h=0.25、lambda=1000、delta=3，2018—2024年14站，11—16 UTC；不重新反演或重新选参。
土壤保持背景土壤对TS_1、冠层对TA。各站RMSE算术平均；月均至少3个有效配对，每站至少3个评价组。

- unfiltered：无参考误差筛选。
- instant_component_10K：各组分分别剔除瞬时绝对温差>10 K，然后双方在同一保留样本上计算月均。
- instant_joint_10K：同一时刻须两个组分均有参考且温差均不超过10 K，再计算月均；会额外损失缺少另一组分参考的记录。
- monthly_only_10K：先用未筛选配对计算月均，再剔除月均绝对温差>10 K。与先筛瞬时记录不同，仅列敏感性。

下列有阈值指标依赖待验证参考，属于条件性一致性评价，不能替代未筛选精度，不能证明反演已改进。
它也不是完整旧流程复现：旧脚本另含0—60摄氏度联合范围限制、阴影土壤及合并小时的月均处理。

## 全时段汇总

```csv
''' + table(summary.loc[summary.split.eq('all')]) + '```\n\n## 瞬时筛选样本损失\n\n```csv\n' + table(totals.reset_index()) + '```\n\n## 未筛选逐小时月均各站\n\n```csv\n' + table(metrics.loc[metrics.split.eq('all') & metrics['mode'].eq('unfiltered') & metrics.scale.eq('monthly_hour')].sort_values(['component','rmse_K'], ascending=[True, False])) + '''```

误差可能包含表面辐射温度与地下探针/空气温度的物理差异、像元与点位代表性、辅助参数及反演误差。当前统计不能将这些原因定量分离。
20 K失败惩罚只用于此前选参目标，不在这里的常规RMSE中；大RMSE不是失败惩罚造成。
'''
    (OUT / '欧洲10K阈值复核.md').write_text(text, encoding='utf8')
    print(summary.loc[summary.split.eq('all') & summary.scale.isin(['monthly_hour', 'monthly_calendar'])].to_string(index=False))
    print(totals.to_string())
    print(metrics.loc[metrics.split.eq('all') & metrics['mode'].eq('unfiltered') & metrics.scale.eq('monthly_hour')].sort_values(['component','rmse_K'], ascending=[True, False]).to_string(index=False))

if __name__ == '__main__':
    main()
