"""Rematch frozen predictions with confirmed offsets; do not rerank parameters."""
from pathlib import Path
import datetime as dt
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from icos_time import clean_ground, source_contract, sha256_file, local_interval_start_utc, AUDIT

CASE = Path(__file__).resolve().parent.parent
BASE = CASE / 'results/production_assessment'
JOINT = BASE / 'joint_parameter_selection'
OUT = CASE / 'results/time_correction_20261010'
EXCLUDED = {'IT-TrF', 'FR-EM2'}
VALUES = ['shaded_soil', 'canopy', 'soil_reference', 'canopy_reference', 'bulk']
KEYS = ['site', 'year', 'month', 'hour']
COMPONENTS = [('soil', 'shaded_soil', 'soil_reference'), ('canopy', 'canopy', 'canopy_reference')]

def masks(x):
    range_ok = x[VALUES].ge(0).all(axis=1) & x[VALUES].le(60).all(axis=1)
    error_ok = (x.shaded_soil - x.soil_reference).abs().le(10) & (x.canopy - x.canopy_reference).abs().le(10)
    return range_ok, range_ok & error_ok

def aggregate(x, mask):
    return x.loc[mask].groupby(KEYS, as_index=False).agg(
        **{v: (v, 'mean') for v in VALUES}, n_raw=('time', 'size')).query('n_raw >= 3').copy()

def score(g, basis, support):
    rows = []
    for nominal in (12, 14):
        subset = g.loc[~g.site.isin(EXCLUDED)] if nominal == 12 else g
        for site, z in subset.groupby('site'):
            if len(z) < 3:
                continue
            for component, pred, ref in COMPONENTS:
                e = z[pred] - z[ref]
                rows.append(dict(basis=basis, support=support, nominal_sites=nominal, site=site,
                    component=component, rmse_K=float(np.sqrt(np.mean(e ** 2))), bias_K=float(e.mean()),
                    bulk_rmse_K=float(np.sqrt(np.mean((z.bulk - z[ref]) ** 2))), n_groups=len(z), n_raw=int(z.n_raw.sum()),
                    years=','.join(map(str, sorted(z.year.unique()))), n_months=z.month.nunique()))
    return rows

def main():
    if (OUT / 'result.json').exists():
        raise RuntimeError('This correction result is already frozen; use a new output directory for a new experiment.')
    OUT.mkdir(parents=True, exist_ok=True)
    checks = local_interval_start_utc(pd.Series([202001010000, 202007011200, 202001010030]), 2)
    assert list(checks.dt.strftime('%Y%m%d%H%M')) == ['201912312200', '202007011000', '201912312230']
    files = [JOINT / 'selected_station_predictions.csv.gz', JOINT / 'frozen_reference_panel.csv.gz',
             JOINT / 'selected_config.json', JOINT / 'selection.json',
             BASE / 'manuscript_validation_update/europe_monthly_hour_pairs.csv.gz', AUDIT]
    source_hashes = {str(p): sha256_file(p) for p in files}
    config = json.loads(files[2].read_text(encoding='utf-8'))
    assert config['configuration']['hotspot'] == .25 and config['configuration']['lambda'] == 1000 and config['configuration']['delta'] == 3
    assert config['first_window'] == config['second_window'] == 5
    pred = pd.read_csv(files[0]); panel = pd.read_csv(files[1])
    raw = pred.loc[pred.domain.eq('indirect') & pred.valid & pred.year.between(2018, 2024) & pred.hour.between(11, 16)].copy()
    raw = raw.merge(panel[['site', 'time', 'soil_reference', 'canopy_reference', 'bulk']], on=['site', 'time'], validate='one_to_one')
    raw['time'] = pd.to_datetime(raw.time, utc=True)
    assert raw.site.nunique() == 14 and not raw.duplicated(['site', 'time']).any()
    assert raw.hour.eq(raw.time.dt.hour).all() and raw.year.eq(raw.time.dt.year).all()
    station_contracts = {r['site']: r for r in json.loads(AUDIT.read_text(encoding='utf-8'))['stations']}
    matched = {'legacy': [], 'corrected': []}; coverage = []; rematch_checks = []
    for site, x in raw.groupby('site', sort=True):
        path = Path(station_contracts[site]['source'])
        g, conflicts = clean_ground(path)
        contract = g.attrs['time_contract']; offset = contract['utc_offset_hours']
        source_hashes[str(path)] = sha256_file(path)
        clean = x.drop(columns=['soil_reference', 'canopy_reference']).sort_values('time')
        for basis in matched:
            ground = g[['field_time', 'TA', 'TS_1']].copy()
            if basis == 'legacy':
                ground['field_time'] += pd.Timedelta(hours=offset)
            m = pd.merge_asof(clean, ground, left_on='time', right_on='field_time',
                              direction='nearest', tolerance=pd.Timedelta(minutes=30))
            m = m.rename(columns={'TS_1': 'soil_reference', 'TA': 'canopy_reference'})
            m['offset_minutes'] = (m.time - m.field_time).dt.total_seconds() / 60
            assert m.offset_minutes.dropna().abs().le(30).all()
            m['source_utc_offset_hours'] = offset
            m['source_interval_start_local'] = m.field_time + (pd.Timedelta(hours=offset) if basis == 'corrected' else pd.Timedelta(0))
            if basis == 'legacy':
                expected = x[['site', 'time', 'soil_reference', 'canopy_reference']]
                check = m.merge(expected, on=['site', 'time'], validate='one_to_one', suffixes=('', '_saved'))
                for c in ['soil_reference', 'canopy_reference']:
                    assert np.allclose(check[c], check[c + '_saved'], rtol=0, atol=1e-12, equal_nan=True), site
                rematch_checks.append(site)
            matched[basis].append(m)
        coverage.append(dict(site=site, utc_offset_hours=offset, source_pid=contract['source_pid'],
            source_csv=str(path), source_sha256=source_hashes[str(path)], duplicates_conflicting=conflicts,
            first_ground_utc=str(g.field_time.min()), last_ground_utc=str(g.field_time.max()), satellite_valid_rows=len(x)))
        print('REMATCHED', site, 'UTC offset', offset, 'satellite rows', len(x), flush=True)
    matched = {k: pd.concat(v, ignore_index=True).sort_values(['site', 'time']).reset_index(drop=True) for k, v in matched.items()}
    assert matched['legacy'][['site', 'time']].equals(matched['corrected'][['site', 'time']])
    for band in ['background_soil', 'canopy', 'sunlit_soil', 'shaded_soil', 'bulk']:
        assert np.array_equal(matched['legacy'][band], matched['corrected'][band], equal_nan=True)
    keep = {basis: masks(x) for basis, x in matched.items()}
    common = keep['legacy'][1] & keep['corrected'][1]
    records = []; months = []; retention = []
    for basis, x in matched.items():
        x.to_csv(OUT / f'{basis}_all_matched.csv.gz', index=False)
        for support, mask in [('joint_10K', keep[basis][1]), ('common_joint_10K', common), ('range_only', keep[basis][0])]:
            g = aggregate(x, mask)
            records.extend(score(g, basis, support))
            g['basis'] = basis; g['support'] = support; months.append(g)
            for site, a in x.groupby('site'):
                ids = a.index
                retention.append(dict(basis=basis, support=support, site=site, n_valid_satellite=len(a),
                    n_paired_reference=int(a[['soil_reference', 'canopy_reference']].notna().all(axis=1).sum()),
                    n_after_range=int(keep[basis][0].loc[ids].sum()), n_retained=int(mask.loc[ids].sum())))
    metrics = pd.DataFrame(records)
    summary = metrics.groupby(['basis', 'support', 'nominal_sites', 'component'], as_index=False).agg(
        sites=('site', 'size'), rmse_K=('rmse_K', 'mean'), bias_K=('bias_K', 'mean'), bulk_rmse_K=('bulk_rmse_K', 'mean'),
        n_groups=('n_groups', 'sum'), n_raw=('n_raw', 'sum'))
    comparison = summary.loc[summary.basis.eq('legacy')].merge(summary.loc[summary.basis.eq('corrected')],
        on=['support', 'nominal_sites', 'component'], suffixes=('_before', '_after'), validate='one_to_one')
    comparison['rmse_change_K'] = comparison.rmse_K_after - comparison.rmse_K_before
    # Reproduce every published Europe12/14 frozen station metric before evaluating the correction.
    saved = pd.read_csv(files[4]); regression = []
    for r in metrics.loc[metrics.basis.eq('legacy') & metrics.support.isin(['joint_10K', 'range_only'])].itertuples():
        z = saved.loc[saved.domain.eq(f'Europe{r.nominal_sites}') & saved.rule.eq(r.support) & saved.site.eq(r.site) & saved.component.eq(r.component)]
        expected = float(np.sqrt(np.mean((z.prediction - z.reference) ** 2)))
        regression.append(abs(expected - r.rmse_K))
        assert len(z) == r.n_groups and int(z.n_raw.sum()) == r.n_raw
    assert len(regression) == 104 and max(regression) < 1e-9
    a = metrics.loc[metrics.support.eq('common_joint_10K')]
    common_check = a.loc[a.basis.eq('legacy')].merge(a.loc[a.basis.eq('corrected')],
        on=['nominal_sites', 'site', 'component'], suffixes=('_before', '_after'), validate='one_to_one')
    assert common_check.n_groups_before.eq(common_check.n_groups_after).all()
    assert common_check.n_raw_before.eq(common_check.n_raw_after).all()
    metrics.to_csv(OUT / 'station_metrics.csv', index=False)
    summary.to_csv(OUT / 'summary.csv', index=False)
    comparison.to_csv(OUT / 'comparison.csv', index=False)
    pd.concat(months, ignore_index=True).to_csv(OUT / 'monthly_hour_pairs.csv.gz', index=False)
    pd.DataFrame(retention).to_csv(OUT / 'retention.csv', index=False)
    pd.DataFrame(coverage).to_csv(OUT / 'source_contracts.csv', index=False)
    plots(metrics, comparison)
    assert source_hashes == {p: sha256_file(p) for p in source_hashes}
    result = dict(status='passed', created_utc=dt.datetime.now(dt.timezone.utc).isoformat(), new_inversions=0,
        configuration=config, satellite_period='2018-2024', hours_utc='11-16', time_match='Audited local non-DST interval start converted to UTC; nearest +/-30 min',
        screening='Inclusive [0,60] C for shaded soil, canopy, both references and bulk; both component-reference differences <=10 K',
        min_pairs_per_group=3, min_groups_per_station=3, station_weighting='equal station RMSE',
        nominal12_excluded=sorted(EXCLUDED), reference_sites=14, source_csvs_verified=True,
        legacy_rematch_checks=rematch_checks, legacy_station_metric_checks=len(regression), legacy_max_difference_K=max(regression),
        prediction_and_bulk_unchanged=True, common_support_counts_verified=True,
        source_sha256=source_hashes, evo_time_assumption_unchanged=True, manuscript_images_unchanged=True,
        interpretation='Conditional indirect consistency; fixed configuration; no parameter reranking; correction does not establish EVO clock convention')
    (OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    report(comparison)
    print(comparison.loc[comparison.support.isin(['joint_10K', 'common_joint_10K'])].to_string(index=False))
    print('PASSED', OUT, flush=True)

def plots(metrics, comparison):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'pdf.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axs = plt.subplots(2, 1, figsize=(10.4, 6.8), sharex=True, layout='constrained')
    sites = sorted(set(metrics.loc[metrics.nominal_sites.eq(12) & metrics.support.eq('joint_10K'), 'site']))
    for ax, component, title in zip(axs, ['soil', 'canopy'], ['Shaded soil versus soil probe', 'Canopy versus air temperature']):
        z = metrics.loc[metrics.nominal_sites.eq(12) & metrics.support.eq('joint_10K') & metrics.component.eq(component)]
        values = z.pivot(index='site', columns='basis', values='rmse_K').reindex(sites)
        pos = np.arange(len(sites))
        ax.bar(pos - .19, values.legacy, .36, color='#9aa4b1', label='Before: local time treated as UTC')
        ax.bar(pos + .19, values.corrected, .36, color='#287b65', label='After: confirmed fixed UTC offset')
        row = comparison.loc[comparison.nominal_sites.eq(12) & comparison.support.eq('joint_10K') & comparison.component.eq(component)].iloc[0]
        ax.set_title(f'{title}  |  mean station RMSE: {row.rmse_K_before:.3f} to {row.rmse_K_after:.3f} K', loc='left')
        ax.set_ylim(0, float(np.nanmax(values.to_numpy())) * 1.25)
        ax.set_ylabel('RMSE (K)'); ax.grid(axis='y', alpha=.2); ax.set_axisbelow(True)
        ax.legend(loc='upper right', fontsize=8, frameon=False)
    axs[-1].set_xticks(np.arange(len(sites)), sites, rotation=35, ha='right')
    fig.suptitle('Time correction only | 2018-2024, 11-16 UTC | joint 10 K screening', fontsize=12)
    fig.savefig(OUT / 'time_correction_station_rmse.png', dpi=220)
    fig.savefig(OUT / 'time_correction_station_rmse.pdf')
    plt.close(fig)

def report(comparison):
    lines = ['# 欧洲源时间修正效果', '', '只修正地面时间转换：芬兰三站减2小时、其余十一站减1小时，不采用夏令时。复用既有组分预测及 bulk LST；不重新反演、选参或替换主稿图像。EVO 沿用原 UTC 假定。', '',
        '2018—2024年、11—16 UTC；区间起点最近邻±30分钟；瞬时联合0—60°C及10 K筛选；按年/月/UTC小时配对平均，每组至少3对、每站至少3组；逐站RMSE等权平均。名义12站排除项保持IT-TrF和FR-EM2，不依据新结果重新删站。', '',
        '| 名义站点集 | 支持 | 组分 | 修正前RMSE/K | 修正后RMSE/K | 变化/K | 可用站数前→后 | 月小时组前→后 | 瞬时对前→后 |', '|---|---|---|---:|---:|---:|---|---|---|']
    for r in comparison.itertuples():
        name = {'joint_10K': '各自筛选样本', 'common_joint_10K': '共同筛选样本', 'range_only': '仅范围筛选诊断'}[r.support]
        lines.append(f'| {r.nominal_sites} | {name} | {"阴影土壤" if r.component == "soil" else "冠层"} | {r.rmse_K_before:.6f} | {r.rmse_K_after:.6f} | {r.rmse_change_K:+.6f} | {r.sites_before}→{r.sites_after} | {r.n_groups_before}→{r.n_groups_after} | {r.n_raw_before}→{r.n_raw_after} |')
    lines += ['', '共同筛选样本要求同一个卫星时刻在修正前、后均满足原有联合规则，再分别与对应地面观测聚合。该对照固定瞬时支持、月小时组和站点构成，用于区分时间对应变化与样本变化；不是通过误差选择时间偏移。', '',
        '程序从实际CSV重建旧配对，并复现冻结稿件表104项逐站指标；新配对使用已核实PID/哈希的时间契约。当前指标仍是筛选条件下、探针/气温参照的间接一致性，不是独立组分辐射温度精度。', '',
        '文件：comparison.csv、station_metrics.csv、monthly_hour_pairs.csv.gz、legacy_all_matched.csv.gz、corrected_all_matched.csv.gz、retention.csv、source_contracts.csv、result.json；诊断图为time_correction_station_rmse.png/pdf。']
    (OUT / '时间修正效果.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
