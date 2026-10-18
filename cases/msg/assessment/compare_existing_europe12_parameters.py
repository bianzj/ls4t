"""Compare complete existing physical predictions; no new inversions."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

ROOT=Path('C:/work/ls4t-msg/cases/official/results/production_assessment')
J=ROOT/'joint_parameter_selection'
BASE=J/'threshold_sensitivity/europe_10_16_joint/subset_12_sites'
OUT=BASE/'parameter_comparison_existing'
MODELS=['physical_h025','physical_h005']
EXCLUDED={'IT-TrF','FR-EM2'}

def main():
    files=[ROOT/'msg_5x5/station_direct_2018_2024/station_predictions_all_models.csv.gz',
           J/'frozen_reference_panel.csv.gz',BASE/'station_metrics.csv',
           ROOT/'parameter_argument_monthly_hour/component_predictions.npz',
           ROOT/'parameter_argument_monthly_hour/protocol.json']
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    allpred=pd.read_csv(files[0]);panel=pd.read_csv(files[1]);panel=panel.loc[panel.domain.eq('indirect')&~panel.site.isin(EXCLUDED)].copy()
    panel=panel.sort_values(['site','time']).reset_index(drop=True)
    assert panel.site.nunique()==12 and panel.hour.between(10,16).all() and panel.year.between(2018,2024).all()
    frames={};finite={};ranged={};filtered={}
    for name in MODELS:
        p=allpred.loc[allpred.model.eq(name)&~allpred.site.isin(EXCLUDED)]
        q=panel[['site','time','year','month','hour','soil_reference','canopy_reference']].merge(
            p[['site','time','valid','bulk','shaded_soil','canopy']],on=['site','time'],validate='one_to_one')
        assert len(q)==len(panel) and q[['site','time']].equals(panel[['site','time']])
        frames[name]=q
        cols=['shaded_soil','canopy','soil_reference','canopy_reference','bulk']
        finite[name]=q.valid & np.isfinite(q[cols]).all(axis=1)
        ranged[name]=finite[name]&q[cols].ge(0).all(axis=1)&q[cols].le(60).all(axis=1)
        filtered[name]=ranged[name]&(q.shaded_soil-q.soil_reference).abs().le(10)&(q.canopy-q.canopy_reference).abs().le(10)
    common_range=np.logical_and.reduce([ranged[n] for n in MODELS])
    common_filtered=np.logical_and.reduce([filtered[n] for n in MODELS])
    records=[];groups=[];coverage=[]
    for name,q in frames.items():
        supports={'own_joint_0_60_10K':filtered[name], 'common_range_without_10K':common_range,'common_both_joint_10K':common_filtered}
        for support,mask in supports.items():
            z=q.loc[mask].copy()
            for period in ['all','development_2018_2022','retrospective_2023_2024']:
                periodmask=np.ones(len(q),dtype=bool) if period=='all' else q.year.le(2022) if period.startswith('development') else q.year.ge(2023)
                for site,ii in q.loc[periodmask].groupby('site').groups.items():
                    coverage.append(dict(model=name,support=support,period=period,site=site,
                        finite=int(finite[name].loc[ii].sum()),range_valid=int(ranged[name].loc[ii].sum()),kept=int(np.asarray(mask)[ii].sum())))
                a=z if period=='all' else z.loc[z.year.le(2022)] if period.startswith('development') else z.loc[z.year.ge(2023)]
                for scale in ['monthly_hour','monthly_calendar']:
                    keys=['site','year','month']+(['hour'] if scale=='monthly_hour' else [])
                    g=a.groupby(keys,as_index=False).agg(soil_prediction=('shaded_soil','mean'),canopy_prediction=('canopy','mean'),
                        soil_reference=('soil_reference','mean'),canopy_reference=('canopy_reference','mean'),n_raw=('time','size'))
                    g=g.loc[g.n_raw.ge(3)].copy()
                    g['model']=name;g['support']=support;g['period']=period;g['scale']=scale;groups.append(g)
                    for site,b in g.groupby('site'):
                        if len(b)<3:continue
                        for comp in ['soil','canopy']:
                            error=b[comp+'_prediction']-b[comp+'_reference']
                            records.append(dict(model=name,support=support,period=period,scale=scale,site=site,component=comp,
                                rmse_K=float(np.sqrt(np.mean(error**2))),bias_K=float(error.mean()),n_groups=len(b),n_raw=int(b.n_raw.sum())))
    met=pd.DataFrame(records);monthly=pd.concat(groups,ignore_index=True);cov=pd.DataFrame(coverage)
    summary=met.groupby(['model','support','period','scale','component'],as_index=False).agg(
        mean_site_rmse_K=('rmse_K','mean'),mean_site_bias_K=('bias_K','mean'),sites=('site','size'),n_groups=('n_groups','sum'),n_raw=('n_raw','sum'))
    old=pd.read_csv(files[2]);old=old.loc[old.soil_type.eq('shaded_soil')&old.start_hour.eq(10)]
    new=met.loc[met.model.eq('physical_h025')&met.support.eq('own_joint_0_60_10K')&met.period.eq('all')]
    check=old.merge(new,on=['site','component','scale'],validate='one_to_one',suffixes=('_old','_new'))
    assert len(check)==48
    maxdiff=float((check.rmse_K_old-check.rmse_K_new).abs().max());assert maxdiff<1e-10
    assert check.n_groups_old.eq(check.n_groups_new).all() and check.n_raw_old.eq(check.n_raw_new).all()
    # Pairwise supports must preserve the same raw counts, month groups and station coverage.
    for support in ['common_range_without_10K','common_both_joint_10K']:
        a=monthly.loc[monthly.support.eq(support)]
        k=['period','scale','site','year','month','hour']
        left=a.loc[a.model.eq(MODELS[0])];right=a.loc[a.model.eq(MODELS[1])]
        c=left.merge(right,on=k,validate='one_to_one',suffixes=('_a','_b'))
        assert len(c)==len(left)==len(right) and c.n_raw_a.eq(c.n_raw_b).all()
    with np.load(files[3]) as archive:
        keys=archive.files
        assert len(keys)==102 and all(k.endswith('__soil') or k.endswith('__canopy') for k in keys)
    assert hashes=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    OUT.mkdir(parents=True,exist_ok=True)
    met.to_csv(OUT/'station_metrics.csv',index=False);summary.to_csv(OUT/'summary.csv',index=False)
    cov.to_csv(OUT/'coverage.csv',index=False);monthly.to_csv(OUT/'monthly_pairs.csv.gz',index=False)
    audit=dict(status='passed',new_inversions=0,excluded_sites=sorted(EXCLUDED),sites=sorted(panel.site.unique()),
        period='2018-2024 10-16 UTC',soil='shaded soil vs TS_1',canopy='canopy vs TA',
        configs={n:dict(hotspot=.25 if n=='physical_h025' else .05,lambda_value=1000,delta=3,first_window=5,second_window=5) for n in MODELS},
        available_complete_configs=2,unusable_51_config_reason='Archive projected Europe soil to background soil, discarded shaded soil, and masked 10 UTC',
        interrupted_3200_search_used=False,source_sha256=hashes,max_baseline_metric_difference_K=maxdiff,
        primary_support='own_joint_0_60_10K',sensitivity_supports=['common_range_without_10K','common_both_joint_10K'],
        independence='Post-hoc 12-site subset. Later years previously inspected; all temporal checks retrospective. No independent optimum or production update.')
    (OUT/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    lines=['# 欧洲12站已有参数预测比较','','只使用已有完整物理配置预测，没有重新反演。排除IT-TrF、FR-EM2；2018—2024年、10—16 UTC、阴影土壤对TS_1、冠层对TA。',
        '完整可比配置只有hotspot=0.25与0.05；λ=1000、δ=3，两阶段均5×5。51组参数档案对欧洲仅保存背景土壤和冠层，且10点已屏蔽，不能套用于当前阴影土壤主方案。中断的3200组实验未使用。',
        '主口径：所选土壤、冠层、双方参考及LST均在[0,60]°C内，两组分瞬时残差均≤10 K后求配对月均；每组至少3对、每站至少3组，逐站RMSE等权平均。',
        '额外比较两参数均满足范围条件的相同时刻且不做10 K筛选，以及两参数均通过联合10 K条件的相同时刻，区分预测变化和筛选样本变化。',
        '站点排除与后期年份均已用于先前结果查看，所有比较属于事后探索；不称独立验证或全局最优，不自动修改生产配置。','','| 比较口径 | 时段 | hotspot | 土壤RMSE/K | 冠层RMSE/K | 站数 | 月小时组数 | 瞬时对数 |','|---|---|---:|---:|---:|---:|---:|---:|']
    for support in ['own_joint_0_60_10K','common_range_without_10K','common_both_joint_10K']:
        for period in ['all','development_2018_2022','retrospective_2023_2024']:
            for name in MODELS:
                a=summary.loc[summary.support.eq(support)&summary.period.eq(period)&summary.model.eq(name)&summary.scale.eq('monthly_hour')].set_index('component')
                lines.append(f"| {support} | {period} | {audit['configs'][name]['hotspot']} | {a.loc['soil','mean_site_rmse_K']:.6f} | {a.loc['canopy','mean_site_rmse_K']:.6f} | {int(a.loc['soil','sites'])} | {int(a.loc['soil','n_groups'])} | {int(a.loc['soil','n_raw'])} |")
    lines+=['','逐站指标、覆盖量、日间合并月均结果见同目录CSV；当前12站基准48项指标已复现。']
    (OUT/'欧洲12站_已有参数比较.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(summary.loc[summary.scale.eq('monthly_hour')].round(6).to_string(index=False))
    print('AUDIT PASSED',OUT)

if __name__=='__main__':main()
