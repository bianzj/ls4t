"""Apply explicit joint range/residual QC to existing baseline predictions only."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

ROOT=Path('C:/work/ls4t-msg/cases/official/results/production_assessment')
SOURCE=ROOT/'joint_parameter_selection'
OUT=SOURCE/'threshold_sensitivity/range_0_60_joint'
PRIMARY_MODE='shaded_joint_0_60_10K'

def main():
    OUT.mkdir(exist_ok=True)
    files=[SOURCE/'selected_station_predictions.csv.gz',SOURCE/'frozen_reference_panel.csv.gz',
           ROOT/'parameter_argument_monthly_hour/landcover_stratification/site_classification.csv']
    source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    report_path=OUT/'指定参数_0至60度与10K筛选结果.md'
    previous_report=report_path.read_text(encoding='utf8') if report_path.exists() else ''
    supplement_marker='## 补充：'
    supplement=('\n\n'+supplement_marker+previous_report.split(supplement_marker,1)[1]) if supplement_marker in previous_report else ''
    pred=pd.read_csv(files[0]);panel=pd.read_csv(files[1]);lc=pd.read_csv(files[2])
    x=pred.merge(panel[['site','time','soil_reference','canopy_reference','bulk','eligible_soil','eligible_canopy']],on=['site','time'],validate='one_to_one')
    x=x.loc[x.domain.eq('indirect')&x.valid&x.year.between(2018,2024)&x.hour.between(11,16)].copy()
    x=x.merge(lc[['site','station_group']],on='site',validate='many_to_one')
    assert not x.duplicated(['site','time']).any()
    rows=[];monthly=[];retention=[];kept=[]
    cases=[('background_joint_10K_only','background_soil',False,True),
           ('background_joint_0_60_10K','background_soil',True,True),
           ('background_separate_0_60_10K','background_soil',True,False),
           ('shaded_joint_0_60_10K','shaded_soil',True,True)]
    for mode,soil,range_filter,joint in cases:
        for component,col,ref in [('soil',soil,'soil_reference'),('canopy','canopy','canopy_reference')]:
            if joint:
                start=x.eligible_soil&x.eligible_canopy
                cols=[soil,'canopy','soil_reference','canopy_reference','bulk']
                range_ok=x[cols].ge(0).all(axis=1)&x[cols].le(60).all(axis=1) if range_filter else start
                diff_ok=(x[soil]-x.soil_reference).abs().le(10)&(x.canopy-x.canopy_reference).abs().le(10)
            else:
                start=x['eligible_'+component];cols=[col,ref,'bulk']
                range_ok=x[cols].ge(0).all(axis=1)&x[cols].le(60).all(axis=1)
                diff_ok=(x[col]-x[ref]).abs().le(10)
            mask=start&range_ok&diff_ok
            z=x.loc[mask,['site','station_group','time','year','month','hour',col,ref]].rename(columns={col:'prediction',ref:'reference'}).copy()
            z['mode']=mode;z['component']=component;kept.append(z)
            assert (z.prediction-z.reference).abs().le(10+1e-10).all()
            if range_filter:assert z[['prediction','reference']].ge(0).all().all() and z[['prediction','reference']].le(60).all().all()
            for site,a in x.groupby('site'):
                ids=a.index
                retention.append(dict(mode=mode,component=component,site=site,station_group=a.station_group.iloc[0],
                    n_start=int(start.loc[ids].sum()),n_after_range=int((start&range_ok).loc[ids].sum()),n_after_10K=int(mask.loc[ids].sum())))
            g=z.groupby(['site','station_group','year','month','hour'],as_index=False).agg(prediction=('prediction','mean'),reference=('reference','mean'),n_raw=('prediction','size'))
            g=g.loc[g.n_raw>=3].copy();g['mode']=mode;g['component']=component;monthly.append(g)
            for (site,group),a in g.groupby(['site','station_group']):
                if len(a)<3:continue
                e=a.prediction-a.reference
                rows.append(dict(mode=mode,component=component,site=site,station_group=group,
                    rmse_K=float(np.sqrt(np.mean(e**2))),bias_K=float(e.mean()),n_groups=len(a),n_raw=int(a.n_raw.sum())))
    met=pd.DataFrame(rows);met.to_csv(OUT/'station_metrics.csv',index=False)
    summaries=[]
    for group in ['all','forest','cropland','grassland','wetland','shrubland']:
        a=met if group=='all' else met.loc[met.station_group.eq(group)]
        s=a.groupby(['mode','component'],as_index=False).agg(sites=('site','size'),mean_site_rmse_K=('rmse_K','mean'),n_groups=('n_groups','sum'),n_raw=('n_raw','sum'))
        s['station_group']=group;summaries.append(s)
    summary=pd.concat(summaries,ignore_index=True);summary.to_csv(OUT/'summary.csv',index=False)
    month=pd.concat(monthly,ignore_index=True);month.to_csv(OUT/'monthly_hour_pairs.csv.gz',index=False)
    pd.concat(kept,ignore_index=True).to_csv(OUT/'retained_instantaneous_pairs.csv.gz',index=False)
    pd.DataFrame(retention).to_csv(OUT/'retention.csv',index=False)
    previous=pd.read_csv(SOURCE/'threshold_sensitivity/summary.csv')
    old=previous.loc[previous['mode'].eq('instant_joint_10K')&previous.split.eq('all')&previous.scale.eq('monthly_hour')]
    new=summary.loc[summary['mode'].eq('background_joint_10K_only')&summary.station_group.eq('all')]
    check=old.merge(new,on='component',suffixes=('_old','_new'));assert len(check)==2
    delta=float((check.mean_site_rmse_K_old-check.mean_site_rmse_K_new).abs().max());assert delta<1e-9
    # Both components must have identical timestamps and monthly group counts under the joint rule.
    for mode in ['background_joint_0_60_10K','shaded_joint_0_60_10K']:
        a=month.loc[month['mode'].eq(mode)]
        assert a.groupby(['site','year','month','hour']).component.nunique().eq(2).all()
    conf=json.loads((SOURCE/'selected_config.json').read_text())['configuration']
    assert conf['hotspot']==.25 and conf['lambda']==1000 and conf['delta']==3
    audit=dict(status='passed',new_inversions=0,configuration=conf,first_window=5,second_window=5,
        period='Europe 2018-2024 11-16 UTC',temperature_unit='Celsius',soil_primary='shaded soil',primary_mode=PRIMARY_MODE,
        implementation='Existing corrected physical Planck baseline; not old unit-inconsistent code',
        primary_rule='Joint inclusive [0,60] for shaded soil, canopy, TS_1, TA, LST; both absolute residuals <=10 K before monthly-hour means',
        monthly_min_pairs=3,station_min_groups=3,baseline_reproduction_difference_K=delta,
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (OUT/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    assert audit['source_sha256']==source_hashes
    main=summary.loc[summary['mode'].eq(PRIMARY_MODE)]
    text='''# 指定参数下0—60℃与10 K联合筛选

只读取已有预测，不重新反演。hotspot=0.25、lambda=1000、delta=3、两阶段5×5，沿用物理单位修正后的代码结果。
欧洲2018—2024年，11—16 UTC；土壤使用阴影土壤，对TS_1探针；冠层对TA气温。两者均为间接对比。
阴影土壤、冠层、TS_1、TA、LST均在闭区间[0,60]℃内，两个组分瞬时绝对温差均<=10 K，才保留该时刻。
按每年每月每小时分别对双方同一配对求均值，每组至少3个时刻，每站至少3个组；逐站RMSE再等权平均。

## 主结果

```csv
'''+main.round(6).to_csv(index=False)+'''```

## 口径敏感性

主方案为shaded_joint_0_60_10K（阴影土壤）。背景土壤三种口径仅保留作对照：background_joint_0_60_10K使用相同联合阈值；background_joint_10K_only不加0—60℃条件；background_separate_0_60_10K分别筛选两个组分。所有结果仍为逐小时月均，没有合并11—16点。此前基于背景土壤筛选的地表类型参数组合不自动视为阴影土壤最优配置。

```csv
'''+summary.loc[summary.station_group.eq('all')].round(6).to_csv(index=False)+'''```

筛选后的精度只适用于保留的样本，不能代表所有季节与未筛选产品的精度。详细样本保留量、逐站指标、瞬时及月小时配对分别见retention.csv、station_metrics.csv、retained_instantaneous_pairs.csv.gz、monthly_hour_pairs.csv.gz。
'''
    (OUT/'指定参数_0至60度与10K筛选结果.md').write_text(text+supplement,encoding='utf8')
    print(main.to_string(index=False));print(summary.loc[summary.station_group.eq('all')].to_string(index=False))
    print(pd.DataFrame(retention).loc[lambda d:d['mode'].eq(PRIMARY_MODE)].groupby('component')[['n_start','n_after_range','n_after_10K']].sum().to_string())

if __name__=='__main__':main()
