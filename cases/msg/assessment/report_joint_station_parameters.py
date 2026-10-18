"""Report the frozen joint selection, with separate direct/indirect metrics."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'results/production_assessment/joint_parameter_selection'

def table(df,cols):
    x=df[cols].copy()
    for c in cols:
        if pd.api.types.is_float_dtype(x[c]):x[c]=x[c].map(lambda v:'—' if pd.isna(v) else f'{v:.3f}')
    return '| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in x.itertuples(index=False,name=None))

def main():
    result=json.loads((OUT/'result.json').read_text());selection=json.loads((OUT/'selection.json').read_text())
    protocol=json.loads((OUT/'protocol.json').read_text());scores=pd.read_csv(OUT/'development_scores.csv')
    sums=pd.read_csv(OUT/'validation_summary.csv');coverage=pd.read_csv(OUT/'coverage.csv')
    pairs=pd.read_csv(OUT/'matched_predictions.csv.gz');months=pd.read_csv(OUT/'matched_monthly.csv.gz')
    panel=pd.read_csv(OUT/'frozen_reference_panel.csv.gz');chosen=pd.read_csv(OUT/'selected_station_predictions.csv.gz')
    selected=selection['selected'];assert result['selected']==selected
    # Independent readback of conventional RMSE, including all-period summaries.
    rows=[]
    for (model,domain,site,comp),z in pairs.groupby(['model','domain','site','component']):
        for scale in ['instantaneous','monthly_calendar','monthly_hour']:
            if scale=='instantaneous':a=z;nraw=len(z)
            else:
                keys=['month']+(['hour'] if scale=='monthly_hour' else [])
                a=z.groupby(keys).agg(reference=('reference','mean'),prediction=('prediction','mean'),n=('prediction','size'))
                a=a.loc[a.n>=3];nraw=int(a.n.sum())
            if len(a)>=3:rows.append({'model':model,'domain':domain,'site':site,'component':comp,'scale':scale,
                'rmse_K':float(np.sqrt(((a.prediction-a.reference)**2).mean())),'n':len(a),'n_raw':nraw})
    full=pd.DataFrame(rows);full.to_csv(OUT/'full_period_station_metrics.csv',index=False)
    fullsum=full.groupby(['model','domain','component','scale'],as_index=False).agg(sites=('site','size'),mean_site_rmse_K=('rmse_K','mean'),n=('n','sum'),n_raw=('n_raw','sum'))
    fullsum.to_csv(OUT/'full_period_summary.csv',index=False)
    errors=[];met=pd.read_csv(OUT/'station_metrics.csv')
    for r in met.loc[met.model.eq('joint_selected')].itertuples():
        if not r.n:continue
        z=pairs.loc[pairs.model.eq(r.model)&pairs.site.eq(r.site)&pairs.component.eq(r.component)&pairs.split.eq(r.split)]
        col='prediction' if r.method=='prediction' else 'bulk'
        if r.scale!='instantaneous':
            keys=['month']+(['hour'] if r.scale=='monthly_hour' else []);g=z.groupby(keys)
            z=g[[col,'reference']].mean().loc[g.size()>=3]
        assert len(z)==r.n;errors.append(abs(float(np.sqrt(((z[col]-z.reference)**2).mean()))-r.rmse_K))
    assert max(errors)<1e-9
    # Verify the selected European outputs against the prior full 2018-2024 run.
    oldroot=HERE.parent/'results/production_assessment/msg_5x5/station_direct_2018_2024'
    old=pd.read_csv(oldroot/'station_predictions_all_models.csv.gz',dtype={'timestamp':str})
    old=old.loc[old.model.eq('physical_h025')&old.valid].copy();old['time']=pd.to_datetime(old.timestamp,format='%Y%m%d%H%M',utc=True)
    new=chosen.loc[chosen.domain.eq('indirect')&chosen.valid].copy();new['time']=pd.to_datetime(new.time,utc=True)
    shared=new.merge(old,on=['site','time'],suffixes=('_new','_old'));bands=['background_soil','canopy','sunlit_soil','shaded_soil']
    delta=np.abs(shared[[b+'_new' for b in bands]].to_numpy()-shared[[b+'_old' for b in bands]].to_numpy())
    assert len(shared)==len(new) and delta.max()<1e-9
    source_ok=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in protocol['source_sha256'].items());assert source_ok
    fixed=chosen[['site','time']].copy();assert not fixed.duplicated().any()
    # Bootstrap retained validation comparisons in explicit blocks. This is a
    # sensitivity interval, not a new independent validation experiment.
    rng=np.random.default_rng(20261009);blocks=[]
    for domain,comp in [('direct','soil'),('direct','canopy'),('indirect','soil'),('indirect','canopy')]:
        a=pairs.loc[pairs.model.eq('joint_selected')&pairs.split.eq('validation')&pairs.domain.eq(domain)&pairs.component.eq(comp)]
        b=pairs.loc[pairs.model.eq('previous_h005')&pairs.split.eq('validation')&pairs.domain.eq(domain)&pairs.component.eq(comp)]
        z=a.merge(b[['site','time','prediction']],on=['site','time'],suffixes=('_joint','_h005'))
        z['mse_difference']=(z.prediction_joint-z.reference)**2-(z.prediction_h005-z.reference)**2
        key='date' if domain=='direct' else 'site';v=z.groupby(key).mse_difference.mean().to_numpy()
        draws=np.array([rng.choice(v,len(v),replace=True).mean() for _ in range(2000)])
        blocks.append({'domain':domain,'component':comp,'block':key,'blocks':len(v),'common_pairs':len(z),
            'mean_block_MSE_joint_minus_h005_K2':float(v.mean()),'ci_low':float(np.quantile(draws,.025)),'ci_high':float(np.quantile(draws,.975))})
    bootstrap=pd.DataFrame(blocks);bootstrap.to_csv(OUT/'validation_block_sensitivity.csv',index=False)
    audit={'status':'passed','saved_metric_rows_checked':len(errors),'max_metric_difference_K':max(errors),
        'europe_selected_values_matching_previous_physical_h025':len(shared),'max_previous_run_difference_K':float(delta.max()),
        'source_hashes_verified':source_ok,'unique_station_timestamps':len(fixed)}
    (OUT/'integrity.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
    qualified=scores.loc[scores.qualified].sort_values('joint_score')
    best_raw=scores.sort_values('joint_score').iloc[0]
    comparison=sums.loc[sums.model.isin(['joint_selected','previous_h005'])&sums.method.eq('prediction')&sums.scale.eq('monthly_hour')]
    selected_cov=coverage.loc[coverage.model.eq('joint_selected')].groupby(['domain','split','component'],as_index=False).agg(
        sites=('site','size'),eligible=('n_eligible','sum'),mean_site_coverage=('coverage','mean'))
    text=f'''# EVO与欧洲间接站点联合确定反演配置

## 推荐配置与适用范围

本轮在240组物理一致的中心5×5候选中，按事先固定的直接验证优先、兼顾间接站点覆盖率与误差的规则，选择：

```json
{{"hotspot": {selected['hotspot']}, "lambda": {selected['lambda']}, "delta_radiance": {selected['delta']}, "first_window": 5, "second_window": 5, "residual": "center"}}
```

**建议把这套配置作为下一步站点验证和生产评估的统一基准。** 波长使用10.5e−6 m的正确普朗克单位；δ单位为W m⁻² sr⁻¹ μm⁻¹。这与历史参数的数值相同，但不恢复旧的普朗克单位错误或按实测误差剔除样本的做法。区域生产仍暂停。

联合选择结果就是物理修正后的原参数基准：本轮没有找到同时满足保覆盖、不显著损害任一验证分量，并优于该基准的替代配置。其保留时段联合分数为1.000，因为被选配置与基准完全相同；不能据此宣称获得了新的独立精度提升。

## 为什么这样联合，而不把15个站点直接混算

- EVO用实测阳照土壤、冠层温度作直接参照；欧洲站点的背景土壤对TS_1探针、冠层对TA气温属于间接一致性评价。两个域的物理含义不同，不汇报一个混合的“总RMSE”。
- 每个域的土壤、冠层分量等权；间接域站点等权，站内年份等权、年内月份等权，防止IT-BCi等多样本站点支配选择。
- 联合排序用相对各自基准MSE的无量纲分数：EVO权重0.70、间接域0.30；0.50和0.90的开发集权重敏感性检验仍选择同一配置。
- 固定输入与参考可用性定义样本，未按预测—实测温差删点。候选反演失败以20 K误差计入开发目标，同时另设覆盖率门槛，避免靠丢掉困难样本取得较低RMSE。
- 每域每分量的带失败惩罚RMSE不得比基准恶化超过10%；EVO有效率最多下降1个百分点；每个有至少30个开发配对的间接站点/分量最多下降2个百分点。这些阈值是本次预设的保守选择规则，不是自然定律。

带失败惩罚的选择分数不等于常规观测RMSE；文件`penalized_evaluation.csv`与下面常规精度表分开保存。

## 分割和候选范围

开发：EVO 2017年8—10月；欧洲2018—2022年。保留时段：EVO 2017年11—12月；欧洲2023—2024年。选择文件在计算保留时段指标前写入，不用保留时段重新排名。

这些时段的汇总结果此前已经查看，所以这里只称**回顾性时间分割验证**，不能称完全未见过数据的独立测试。EVO仍只有单站、2017年部分季节；间接站点时区、探针深度、静态辅助输入的限制仍在。

候选：hotspot={protocol['grid']['hotspot']}；λ={protocol['grid']['lambda']}；δ={protocol['grid']['delta']}，共240组。固定两阶段5×5、中心残差结构。没有把需要更大原始窗口验证边界的local_vector方案混入本次参数选择；此前EVO单站P0120的结构因此不是本次搜索对象。

输入沿用现有缓存并统一物理质量控制。EVO评价时段10—16 UTC；欧洲11—16 UTC。每个固定年月组至少3个参考配对进入选择。选参CSV中的输出也保留这一评价时段限制，不是新增的全区域生产产品。

## 开发集可接受候选

只有{len(qualified)}/240组通过上述门槛：

{table(qualified,['id','hotspot','lambda','delta','joint_score','direct_mean','indirect_mean'])}

λ=100与λ=1000的联合分数差仅约{100*(qualified.loc[qualified['lambda'].eq(100)&qualified.hotspot.eq(.25),'joint_score'].iloc[0]-1):.3f}%，不足以声称1000是可精确辨识的唯一最优值。本轮保留1000以维持统一基准；没有证据支持把λ改成较小数值能带来稳健增益。

不考虑覆盖率等门槛时，最低联合分数为{best_raw.joint_score:.3f}，对应h={best_raw.hotspot}、λ={best_raw['lambda']}、δ={best_raw.delta}。它在EVO上更有利，但触发多个间接站点的覆盖率损失限制，故未被推荐。完整剔除理由见`development_scores.csv`，不能只展示胜出配置而隐藏这些取舍。

## 常规逐小时月均RMSE

直接域soil指阳照土壤；间接域soil指背景土壤。表内指标不含20 K失败惩罚，每组月小时至少3个有效配对；各配置的有效样本数会不同。

{table(comparison,['model','domain','split','component','sites','mean_site_rmse_K','n_groups','n_raw'])}

完整时段汇总（仅描述，不用于回头选参）：

{table(fullsum.loc[fullsum.model.isin(['joint_selected','previous_h005'])&fullsum.scale.eq('monthly_hour')],['model','domain','component','sites','mean_site_rmse_K','n','n_raw'])}

各站的瞬时、按日间小时合并月均、逐小时月均结果分别保存在`station_metrics.csv`及`full_period_station_metrics.csv`，不混用尺度。

## 覆盖与稳定性

{table(selected_cov,['domain','split','component','sites','eligible','mean_site_coverage'])}

这里coverage是对事先固定、每月有足够参考记录的可反演输入候选的有效预测比例，并非全年卫星数据覆盖率；候选输入本身没有的日期不在分母中。

下面比较推荐配置与此前h=0.05、λ=1000、δ=3配置在保留时段共同成功配对上的MSE差；负值有利于推荐配置。EVO按日期、欧洲按站点重采样2000次，只作为敏感性区间，不是重新选择参数或独立性保证。相邻站点可能相关，EVO只有两个保留月份，区间不能消除这些限制。

{table(bootstrap,list(bootstrap.columns))}

## 复核及交付

新参数标量求解核验{len(result['scalar_checks'])}次，包含约束触发案例，最大温差{max(x['max_difference_K'] for x in result['scalar_checks']):.3g} K。从保存的配对文件独立重算{audit['saved_metric_rows_checked']}项指标，最大差{audit['max_metric_difference_K']:.3g} K。欧洲推荐配置的{audit['europe_selected_values_matching_previous_physical_h025']}条有效输出与前一轮h=0.25物理分支一致，最大差{audit['max_previous_run_difference_K']:.3g} K。

- `selected_config.json`：正式保存的本次推荐配置及单位、质量规则。
- `selection.json`、`protocol.json`：冻结选择、候选网格、分割、规则、源代码哈希。
- `development_scores.csv`：全部240组开发集结果及不合格理由。
- `validation_summary.csv`、`coverage.csv`：分域、分时段的精度和覆盖。
- `selected_station_predictions.csv.gz`、`selected_station_monthly_hour.csv.gz`：推荐配置的站点评价时段瞬时及月均结果。
- `frozen_reference_panel.csv.gz`、`input_manifest.json`：固定样本及输入来源。
- `integrity.json`：统计与既有结果一致性核验。

所有结果保存于 `{OUT.as_posix()}`；论文和区域产品尚未替换。该配置是本次240组、固定结构与保守覆盖约束下的推荐基准，不是已证明适用于所有地区、季节和地类的全局最优参数。
'''
    report=OUT/'EVO与间接站点联合参数配置报告.md';report.write_text(text,encoding='utf8')
    print(fullsum.loc[fullsum.model.eq('joint_selected')&fullsum.scale.eq('monthly_hour')].to_string(index=False))
    print('REPORT',report)

if __name__=='__main__':main()
