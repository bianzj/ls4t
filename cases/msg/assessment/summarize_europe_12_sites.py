"""User-requested post-hoc exclusion; preserve the full 14-site reference."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

SOURCE=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/joint_parameter_selection/threshold_sensitivity/europe_10_16_joint')
OUT=SOURCE/'subset_12_sites'
EXCLUDED={'IT-TrF','FR-EM2'}

def main():
    files=[SOURCE/n for n in ['station_metrics.csv','summary.csv','monthly_pairs.csv.gz','audit.json']]
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    full=pd.read_csv(files[0]);old=pd.read_csv(files[1]);pairs=pd.read_csv(files[2])
    assert full.site.nunique()==14 and EXCLUDED.issubset(set(full.site))
    retained=full.loc[~full.site.isin(EXCLUDED)].copy()
    assert retained.site.nunique()==12
    keys=['soil_type','start_hour','scale','component']
    def summarize(x):
        return x.groupby(keys,as_index=False).agg(mean_site_rmse_K=('rmse_K','mean'),sites=('site','size'),n_groups=('n_groups','sum'),n_raw=('n_raw','sum'))
    check=summarize(full).merge(old,on=keys,suffixes=('_check','_saved'),validate='one_to_one')
    assert np.allclose(check.mean_site_rmse_K_check,check.mean_site_rmse_K_saved,atol=1e-12,rtol=0)
    summary=summarize(retained);assert summary.sites.eq(12).all()
    comparison=old.merge(summary,on=keys,suffixes=('_14','_12'),validate='one_to_one')
    comparison['rmse_change_K']=comparison.mean_site_rmse_K_12-comparison.mean_site_rmse_K_14
    paired=pairs.loc[~pairs.site.isin(EXCLUDED)].copy()
    checks=0
    for (soil,start,scale,site),g in paired.groupby(['soil_type','start_hour','scale','site']):
        if len(g)<3:continue
        for comp in ['soil','canopy']:
            target=retained.loc[retained.soil_type.eq(soil)&retained.start_hour.eq(start)&retained.scale.eq(scale)&retained.site.eq(site)&retained.component.eq(comp)]
            assert len(target)==1
            rmse=float(np.sqrt(np.mean((g[comp+'_prediction']-g[comp+'_reference'])**2)))
            assert abs(rmse-target.iloc[0].rmse_K)<1e-10
            assert len(g)==target.iloc[0].n_groups and int(g.n_raw.sum())==target.iloc[0].n_raw
            checks+=1
    assert checks==len(retained)
    assert hashes=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    OUT.mkdir(exist_ok=True)
    retained.to_csv(OUT/'station_metrics.csv',index=False)
    summary.to_csv(OUT/'summary.csv',index=False)
    comparison.to_csv(OUT/'comparison_14_vs_12.csv',index=False)
    paired.to_csv(OUT/'monthly_pairs.csv.gz',index=False)
    audit=json.loads(files[3].read_text(encoding='utf8'))
    audit.update(status='passed',new_inversions=0,excluded_sites=sorted(EXCLUDED),retained_sites=sorted(retained.site.unique()),
        exclusion_reason='User-requested after inspecting site errors; no independent instrument or data-quality failure established',
        interpretation='Post-hoc 12-site subset, not an independent demonstration of accuracy improvement; retain full 14-site results',
        parent_audit=str(files[3]),source_sha256=hashes,monthly_pair_rechecks=checks)
    (OUT/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    lines=['# 欧洲12站验证汇总','','按用户要求，排除IT-TrF和FR-EM2，保留其余12站。原14站结果保留在上一级目录。',
        '2018—2024年；当前主口径为10—16 UTC、阴影土壤、逐小时月均。hotspot=0.25、λ=1000、δ=3，两阶段5×5。0—60°C和双组分联合10 K筛选、每组至少3对及每站至少3组条件保持一致。RMSE为逐站RMSE等权平均。',
        '此次排除发生在查看误差之后，属于事后站点子集分析；尚无独立证据表明两个站点存在仪器或数据质量故障。不得将删站后的指标变化称为反演精度提升，正式论文需交代排除依据并保留完整14站对照。',
        '站点冠层参考为气温、土壤参考为探针温度，仍属间接一致性检验。沿用原时间匹配，未重新核实源文件时区。','','| 时段UTC | 尺度 | 阴影土壤RMSE/K | 冠层RMSE/K | 有效组数 | 瞬时配对数 |','|---|---|---:|---:|---:|---:|']
    for start in [10,11]:
        for scale in ['monthly_hour','monthly_calendar']:
            a=summary.loc[summary.soil_type.eq('shaded_soil')&summary.start_hour.eq(start)&summary.scale.eq(scale)].set_index('component')
            lines.append(f"| {start}—16 | {'逐小时月均' if scale=='monthly_hour' else '日间合并月均'} | {a.loc['soil','mean_site_rmse_K']:.6f} | {a.loc['canopy','mean_site_rmse_K']:.6f} | {int(a.loc['soil','n_groups'])} | {int(a.loc['soil','n_raw'])} |")
    lines+=['','## 保留站点','',', '.join(sorted(retained.site.unique())),'','背景土壤对照及14站与12站差异见summary.csv和comparison_14_vs_12.csv。原预测、14站结果和论文均未改写。']
    (OUT/'欧洲12站_排除两站后的验证结果.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(summary.loc[summary.soil_type.eq('shaded_soil')].to_string(index=False))
    print('RECHECKS',checks,'AUDIT PASSED',OUT)

if __name__=='__main__':main()
