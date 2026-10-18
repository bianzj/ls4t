"""Reaggregate existing EVO pairs at 11-16 UTC; retain 10-16 comparison."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd

ROOT=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/joint_parameter_selection/threshold_sensitivity')
SOURCE=ROOT/'evo_range_0_60_joint'
OUT=SOURCE/'hours_11_16'

def main():
    files=[SOURCE/'instantaneous_pairs.csv.gz',SOURCE/'summary.csv',SOURCE/'audit.json',
        ROOT/'europe_10_16_joint/subset_12_sites/summary.csv']
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    x=pd.read_csv(files[0]);old=pd.read_csv(files[1]);audit=json.loads(files[2].read_text(encoding='utf8'))
    assert set(x.site)=={'EVO'} and set(x.year)=={2017}
    assert not x.duplicated(['soil_type','rule','site','time']).any()
    rows=[];months=[];retention=[]
    for (soil,rule),a in x.groupby(['soil_type','rule']):
        if rule=='joint_0_60_10K':
            cols=['soil_prediction','canopy_prediction','soil_reference','canopy_reference','bulk']
            assert a[cols].ge(0).all().all() and a[cols].le(60).all().all()
            for comp in ['soil','canopy']:assert (a[comp+'_prediction']-a[comp+'_reference']).abs().le(10).all()
        for start in [10,11]:
            z=a.loc[a.hour.between(start,16)]
            retention.append(dict(soil_type=soil,rule=rule,start_hour=start,retained_instantaneous=len(z),excluded_hour10=int((a.hour==10).sum()) if start==11 else 0))
            for scale in ['monthly_hour','monthly_calendar']:
                keys=['site','year','month']+(['hour'] if scale=='monthly_hour' else [])
                g=z.groupby(keys).agg(**{c:(c,'mean') for c in ['soil_prediction','canopy_prediction','soil_reference','canopy_reference']},n_raw=('time','size'))
                g=g.loc[g.n_raw>=3].copy();assert len(g)>=3
                for comp in ['soil','canopy']:
                    e=g[comp+'_prediction']-g[comp+'_reference']
                    check=z.assign(error=z[comp+'_prediction']-z[comp+'_reference']).groupby(keys).error.mean().reindex(g.index)
                    assert np.allclose(e,check,atol=1e-12,rtol=0)
                    rows.append(dict(soil_type=soil,rule=rule,start_hour=start,scale=scale,component=comp,rmse_K=float(np.sqrt(np.mean(e**2))),bias_K=float(e.mean()),n_groups=len(g),n_raw=int(g.n_raw.sum())))
                g['soil_type']=soil;g['rule']=rule;g['start_hour']=start;g['scale']=scale;months.append(g.reset_index())
    summary=pd.DataFrame(rows)
    c=summary.loc[summary.start_hour.eq(10)].merge(old,on=['soil_type','rule','scale','component'],validate='one_to_one',suffixes=('_new','_old'))
    assert len(c)==16 and (c.rmse_K_new-c.rmse_K_old).abs().max()<1e-10
    assert c.n_groups_new.eq(c.n_groups_old).all() and c.n_raw_new.eq(c.n_raw_old).all()
    europe=pd.read_csv(files[3]);europe=europe.loc[europe.soil_type.eq('shaded_soil')&europe.start_hour.eq(11)]
    combined=[]
    for r in summary.loc[summary.soil_type.eq('sunlit_soil')&summary.rule.eq('joint_0_60_10K')&summary.start_hour.eq(11)].to_dict('records'):
        combined.append(dict(dataset='EVO',period='2017 Aug-Dec',soil_type='sunlit_soil',sites=1,scale=r['scale'],component=r['component'],rmse_K=r['rmse_K'],n_groups=r['n_groups'],n_raw=r['n_raw']))
    for r in europe.to_dict('records'):
        combined.append(dict(dataset='Europe12',period='2018-2024',soil_type='shaded_soil',sites=r['sites'],scale=r['scale'],component=r['component'],rmse_K=r['mean_site_rmse_K'],n_groups=r['n_groups'],n_raw=r['n_raw']))
    assert hashes=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    OUT.mkdir(exist_ok=True)
    summary.to_csv(OUT/'summary.csv',index=False)
    pd.DataFrame(retention).to_csv(OUT/'retention.csv',index=False)
    pd.concat(months,ignore_index=True).to_csv(OUT/'monthly_pairs.csv.gz',index=False)
    pd.DataFrame(combined).to_csv(OUT/'evo_europe12_same_hours.csv',index=False)
    audit.update(status='passed',new_inversions=0,period='EVO 2017 Aug-Dec, primary hours 11-16 UTC; 10-16 retained for comparison',
        parent_audit=str(files[2]),source_sha256=hashes,baseline_reproduction_max_difference_K=float((c.rmse_K_new-c.rmse_K_old).abs().max()),
        interpretation='Matching UTC hours and thresholds does not make EVO direct sunlit/canopy validation equivalent to European shaded-soil/air-temperature indirect comparison')
    (OUT/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    lines=['# EVO统一到11—16 UTC的验证结果','','读取已有配对，未重新反演。hotspot=0.25、λ=1000、δ=3，两阶段均5×5。2017年8—12月；先对预测土壤、冠层、两组分实测及LST做0—60°C联合范围筛选，再要求两组分瞬时绝对偏差均≤10 K，每个月小时/每月聚合至少3对。',
        '逐小时月均按每年每月每小时分别平均；日间合并月均按每月全部有效瞬时配对平均。','',
        '| 土壤方案 | 时段UTC | 统计尺度 | 土壤RMSE/K | 冠层RMSE/K | 组数 | 瞬时对数 |','|---|---|---|---:|---:|---:|---:|']
    for soil in ['sunlit_soil','background_soil']:
        for scale in ['monthly_hour','monthly_calendar']:
            for start in [11,10]:
                a=summary.loc[summary.soil_type.eq(soil)&summary.rule.eq('joint_0_60_10K')&summary.scale.eq(scale)&summary.start_hour.eq(start)].set_index('component')
                lines.append(f"| {'光照土壤' if soil=='sunlit_soil' else '背景土壤'} | {start}—16 | {'逐小时月均' if scale=='monthly_hour' else '日间合并月均'} | {a.loc['soil','rmse_K']:.6f} | {a.loc['canopy','rmse_K']:.6f} | {int(a.loc['soil','n_groups'])} | {int(a.loc['soil','n_raw'])} |")
    lines+=['','无追加阈值筛选的敏感性结果保存在summary.csv。背景土壤仍对光照土壤实测，仅作跨组分诊断。',
        'evo_europe12_same_hours.csv列出EVO与欧洲12站相同11—16 UTC口径。EVO为光照土壤/冠层辐射温度直接参照，欧洲为阴影土壤对探针/冠层对气温，且年份不同；统一时段不等于统一物理验证对象，不能合并成一个总精度。欧洲时间匹配沿用既有参考表，未重新核实源文件时区。']
    (OUT/'EVO_11至16点统一时段验证.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(summary.loc[summary.rule.eq('joint_0_60_10K')].round(6).to_string(index=False))
    print(pd.DataFrame(combined).round(6).to_string(index=False))
    print('AUDIT PASSED',OUT)

if __name__=='__main__':main()
