"""Compare 10-16 versus 11-16 UTC using existing physical_h025 predictions."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

ROOT=Path('C:/work/ls4t-msg/cases/official/results/production_assessment')
JOINT=ROOT/'joint_parameter_selection'
OUT=JOINT/'threshold_sensitivity/europe_10_16_joint'

def main():
    sources=[ROOT/'msg_5x5/station_direct_2018_2024/station_predictions_all_models.csv.gz',
        JOINT/'selected_station_predictions.csv.gz',JOINT/'frozen_reference_panel.csv.gz',
        JOINT/'threshold_sensitivity/range_0_60_joint/station_metrics.csv',JOINT/'selected_config.json']
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    raw=pd.read_csv(sources[0]);raw=raw.loc[raw.model.eq('physical_h025')].copy()
    selected=pd.read_csv(sources[1]);selected=selected.loc[selected.domain.eq('indirect')]
    panel=pd.read_csv(sources[2]);panel=panel.loc[panel.domain.eq('indirect')]
    config=json.loads(sources[4].read_text())
    assert config['configuration']['hotspot']==.25 and config['configuration']['lambda']==1000 and config['configuration']['delta']==3
    assert config['first_window']==config['second_window']==5
    compare=raw.merge(selected,on=['site','time'],suffixes=('_raw','_joint'),validate='one_to_one')
    assert len(compare)==len(raw)==len(selected)
    existing=compare.loc[compare.hour_raw.between(11,16)]
    assert existing.valid_raw.eq(existing.valid_joint).all()
    bands=['background_soil','canopy','sunlit_soil','shaded_soil']
    diff=np.abs(existing.loc[existing.valid_raw,[b+'_raw' for b in bands]].to_numpy()-existing.loc[existing.valid_raw,[b+'_joint' for b in bands]].to_numpy())
    max_diff=float(diff.max());assert max_diff<1e-9
    x=raw.merge(panel[['site','time','soil_reference','canopy_reference']],on=['site','time'],validate='one_to_one')
    assert x.site.nunique()==14 and x.year.between(2018,2024).all()
    ts=pd.to_datetime(x.time,utc=True)
    assert x.hour.eq(ts.dt.hour).all() and not x.duplicated(['site','time']).any()
    metrics=[];monthly=[];retention=[];kept=[]
    for soil in ['shaded_soil','background_soil']:
        cols=[soil,'canopy','soil_reference','canopy_reference','bulk']
        range_ok=x[cols].ge(0).all(axis=1)&x[cols].le(60).all(axis=1)
        error_ok=(x[soil]-x.soil_reference).abs().le(10)&(x.canopy-x.canopy_reference).abs().le(10)
        for start_hour in [11,10]:
            start=x.valid&x.hour.between(start_hour,16)&np.isfinite(x[['soil_reference','canopy_reference']]).all(axis=1)
            mask=start&range_ok&error_ok
            retention.append(dict(soil_type=soil,start_hour=start_hour,initial=int(start.sum()),after_range=int((start&range_ok).sum()),after_joint_10K=int(mask.sum()),retained_10=int((mask&x.hour.eq(10)).sum())))
            z=x.loc[mask,['site','time','year','month','hour',soil,'canopy','soil_reference','canopy_reference']].rename(columns={soil:'soil_prediction','canopy':'canopy_prediction'}).copy()
            z['soil_type']=soil;z['start_hour']=start_hour;kept.append(z)
            for scale in ['monthly_hour','monthly_calendar']:
                keys=['site','year','month']+(['hour'] if scale=='monthly_hour' else [])
                g=z.groupby(keys).agg(soil_prediction=('soil_prediction','mean'),canopy_prediction=('canopy_prediction','mean'),soil_reference=('soil_reference','mean'),canopy_reference=('canopy_reference','mean'),n_raw=('time','size'))
                g=g.loc[g.n_raw>=3].reset_index()
                for comp in ['soil','canopy']:
                    for site,a in g.groupby('site'):
                        if len(a)<3:continue
                        e=a[comp+'_prediction']-a[comp+'_reference']
                        metrics.append(dict(soil_type=soil,start_hour=start_hour,scale=scale,component=comp,site=site,rmse_K=float(np.sqrt(np.mean(e**2))),bias_K=float(e.mean()),n_groups=len(a),n_raw=int(a.n_raw.sum())))
                g['soil_type']=soil;g['start_hour']=start_hour;g['scale']=scale;monthly.append(g)
    metrics=pd.DataFrame(metrics)
    summary=metrics.groupby(['soil_type','start_hour','scale','component'],as_index=False).agg(mean_site_rmse_K=('rmse_K','mean'),sites=('site','size'),n_groups=('n_groups','sum'),n_raw=('n_raw','sum'))
    assert summary.sites.eq(14).all()
    previous=pd.read_csv(sources[3]);errors=[]
    for soil,prefix in [('shaded_soil','shaded'),('background_soil','background')]:
        old=previous.loc[previous['mode'].eq(prefix+'_joint_0_60_10K')]
        new=metrics.loc[metrics.soil_type.eq(soil)&metrics.start_hour.eq(11)&metrics.scale.eq('monthly_hour')]
        c=old.merge(new,on=['site','component'],validate='one_to_one',suffixes=('_old','_new'))
        assert len(c)==28
        errors.extend((c.rmse_K_old-c.rmse_K_new).abs().tolist())
        assert c.n_groups_old.eq(c.n_groups_new).all() and c.n_raw_old.eq(c.n_raw_new).all()
    assert max(errors)<1e-9
    assert hashes=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    OUT.mkdir(parents=True,exist_ok=True)
    metrics.to_csv(OUT/'station_metrics.csv',index=False);summary.to_csv(OUT/'summary.csv',index=False)
    pd.DataFrame(retention).to_csv(OUT/'retention.csv',index=False)
    pd.concat(monthly,ignore_index=True).to_csv(OUT/'monthly_pairs.csv.gz',index=False)
    pd.concat(kept,ignore_index=True).to_csv(OUT/'retained_instantaneous_pairs.csv.gz',index=False)
    audit=dict(status='passed',new_inversions=0,configuration=config,period='2018-2024',
        soil_primary='shaded_soil',reference_time_convention='Unchanged existing frozen panel; source-specific timestamp interpretation not newly verified',
        filtering='Chosen soil, canopy, both references and bulk LST in inclusive [0,60] C; both instantaneous absolute residuals <=10 K',
        min_pairs_per_group=3,min_groups_per_station=3,max_overlap_prediction_difference_K=max_diff,max_old_station_metric_difference_K=max(errors),
        original_10_hour_valid=int((raw.valid&raw.hour.eq(10)).sum()),source_sha256=hashes)
    (OUT/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    lines=['# 欧洲14站10—16点与11—16点验证比较','','使用已有physical_h025预测，不重新反演。hotspot=0.25、λ=1000、δ=3，两阶段5×5。',
        '2018—2024年；阴影土壤为主方案，背景土壤作为对照。所选土壤、冠层、双方参考值及LST均在[0,60]°C内，两个组分瞬时绝对残差均≤10 K；先筛选，再对相同配对求月均，每组至少3对，每站至少3组，最终RMSE按站点等权平均。',
        '10点预测来自原全时段物理配置结果。11—16点预测和56项逐站RMSE全部复现此前结果。冻结参考表中的10点资格标志含旧时段排除，故本次使用原有效预测与已保存参考值重新应用上述范围和残差规则。',
        '沿用既有参考时间匹配；本次没有重新确认各站原文件时区。结果是条件性间接一致性，不是独立组分辐射温度精度。','','| 土壤方案 | 时段UTC | 尺度 | 土壤RMSE/K | 冠层RMSE/K | 组数 | 瞬时对数 |','|---|---|---|---:|---:|---:|---:|']
    for soil in ['shaded_soil','background_soil']:
        for scale in ['monthly_hour','monthly_calendar']:
            for start in [11,10]:
                a=summary.loc[summary.soil_type.eq(soil)&summary.scale.eq(scale)&summary.start_hour.eq(start)].set_index('component')
                lines.append(f"| {'阴影土壤' if soil=='shaded_soil' else '背景土壤'} | {start}—16 | {'逐小时月均' if scale=='monthly_hour' else '日间合并月均'} | {a.loc['soil','mean_site_rmse_K']:.6f} | {a.loc['canopy','mean_site_rmse_K']:.6f} | {int(a.loc['soil','n_groups'])} | {int(a.loc['soil','n_raw'])} |")
    (OUT/'欧洲14站_10点起始验证.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(summary.to_string(index=False));print(pd.DataFrame(retention).to_string(index=False));print('AUDIT PASSED',OUT)

if __name__=='__main__':main()
