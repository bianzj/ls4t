"""Maintain one full-period report and one original-parameter audit in cases."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'results/production_assessment/msg_5x5/station_direct_2018_2024'

def fmt(x,d=2):return '—' if pd.isna(x) else f'{x:.{d}f}'
def table(frame,columns,headers=None):
    x=frame[columns].copy()
    for c in x.columns:
        if pd.api.types.is_float_dtype(x[c]):x[c]=x[c].map(fmt)
    names=headers or columns
    return '| '+' | '.join(names)+' |\n| '+' | '.join(['---']*len(names))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in x.itertuples(index=False,name=None))

def main():
    result=json.loads((OUT/'result.json').read_text());assert result['status']=='completed'
    hist=json.loads((OUT/'historical_audit.json').read_text());summary=pd.read_csv(OUT/'summary.csv')
    duplicate=json.loads((OUT/'historical_duplicate_audit.json').read_text())
    scores=pd.read_csv(OUT/'station_metrics.csv');cov=pd.read_csv(OUT/'retrieval_coverage_by_year.csv')
    yearly=pd.read_csv(OUT/'primary_summary_by_year.csv');sensitivity=pd.read_csv(OUT/'historical_protocol_sensitivity.csv')
    controls=pd.read_csv(OUT/'common_support_controls.csv');ground=pd.read_csv(OUT/'ground_coverage.csv')
    fingerprint=pd.read_csv(OUT/'original_parameter_fingerprint.csv');probe=pd.read_csv(OUT/'original_parameter_sensitivity_replay.csv')
    primary=summary.loc[summary.hours_scope.eq('11_16_UTC')&summary.model.eq('physical_h005')]
    compact=primary.loc[primary.component.isin(['background_soil','canopy'])].copy()
    bystation=scores.loc[scores.hours_scope.eq('11_16_UTC')&scores.model.eq('physical_h005')&scores.method.eq('estimate')&scores.scale.eq('monthly_hour')]
    statrows=[]
    for sid in sorted(cov.site.unique()):
        c=cov.loc[cov.site.eq(sid)];g=ground.loc[ground.site.eq(sid)&ground.year.le(2024)]
        row={'站点':sid,'有效瞬时':int(c.physical_h005.fillna(0).sum()),'有结果年份':','.join(c.loc[c.physical_h005.gt(0),'year'].astype(str))}
        for comp,label in [('background_soil','土壤'),('canopy','冠层')]:
            z=bystation.loc[bystation.site.eq(sid)&bystation.component.eq(comp)]
            row[label+'RMSE(K)']=float(z.rmse_K.iloc[0]) if len(z) else np.nan
            row[label+'月小时数']=int(z.n.iloc[0]) if len(z) else 0
        row['有TS1年份']=','.join(g.loc[g.valid_TS1.gt(0),'year'].astype(str));statrows.append(row)
    statrows=pd.DataFrame(statrows)
    def val(comp,scale):
        z=primary.loc[primary.component.eq(comp)&primary.scale.eq(scale)&primary.method.eq('estimate')].iloc[0]
        return f'{z.mean_site_rmse_K:.2f} K（{int(z.sites)}站）'
    history=sensitivity.loc[sensitivity.method.eq('estimate')].copy()
    retention=pd.read_csv(OUT/'historical_protocol_retention.csv')
    n0=int(retention.loc[retention.protocol.eq('H0_original')&retention.component.eq('soil'),'raw_pairs'].iloc[0])
    n1=int(retention.loc[retention.protocol.eq('H1_no_residual_filter')&retention.component.eq('soil'),'raw_pairs'].iloc[0])
    history['soil_definition']=np.where(history.protocol.isin(['H0_original','H1_no_residual_filter','H2_wider_range']),'shaded_soil','background_soil')
    h25=fingerprint.loc[fingerprint.model.eq('historical_raw_h025')]
    h25n=int(h25.reasonable_rows.sum());h25tol=int(h25.reasonable_within_001.sum())
    alln=int(h25.shared_all_four.sum());alltol=int(h25.all_four_within_001.sum())
    def control(comp,model):
        return float(controls.loc[controls.comparison.eq('hotspot_physical')&controls.component.eq(comp)&
            controls.model.eq(model)&controls.scale.eq('monthly_hour')&controls.method.eq('estimate'),'mean_site_rmse_K'].iloc[0])
    parameter_lines=[]
    for sid in sorted(cov.site.unique()):
        z=h25.loc[h25.site.eq(sid)].iloc[0]
        pp=probe.loc[probe.site.eq(sid)&probe.factor.eq('hotspot')&probe.hotspot.eq(.25)].iloc[0]
        ll=probe.loc[probe.site.eq(sid)&probe.factor.eq('lambda')&probe['lambda'].eq(1000)].iloc[0]
        parameter_lines.append({'站点':sid,'合理温度存档共同数':int(z.reasonable_rows),'四温度差≤0.01K':int(z.reasonable_within_001),
            '全共同记录数':int(z.shared_all_four),'两位小数完全一致数':int(z.all_four_exact_rounded),
            'h025抽查一致数':int(pp.all_four_exact),'抽查数':int(pp.sample_n),'lambda1000抽查一致数':int(ll.all_four_exact)})
    param=pd.DataFrame(parameter_lines)
    text=f'''# 2018—2024年欧洲站点5×5直接反演与历史差异

## 本次结果

已完成 **14站 × 7年 = 98个站点年份任务**，直接读取 `E:/PRODUCTS/SITE` 中站点5×5原始输入。对本地存在的全部小时文件进行检查，不从区域反演产品提取温度；缺输入时明确记录并跳过，不补造缺测值。

- 当前试验配置（physical_h005）：有效瞬时 **{result['primary_valid_instantaneous']}条**，覆盖 **{result['primary_sites_with_results']}站**。
- 逐小时月均：**{result['primary_month_hour_groups']}组**，其中至少3个有效时刻的组合 **{result['primary_month_hour_groups_n_ge_3']}组**。
- 主比较时段11—16 UTC，瞬时站点等权平均RMSE：背景土壤 **{val('background_soil','instantaneous')}**，冠层 **{val('canopy','instantaneous')}**。
- 同月同小时平均后：背景土壤 **{val('background_soil','monthly_hour')}**，冠层 **{val('canopy','monthly_hour')}**。
- 同月所有11—16 UTC合并平均后：背景土壤 **{val('background_soil','monthly_calendar')}**，冠层 **{val('canopy','monthly_calendar')}**。

“冠层”对应TA气温，“土壤”对应TS_1土壤探针，均属**间接一致性评价**，不是组分辐射温度直接验证。数值是各站RMSE算术平均；不把所有站样本混合计算一个RMSE。

当前h=0.05来自前期EVO追溯/试验，不代表已找到欧洲各站最优参数。本次同时运行h=0.25等固定对照，未根据本轮实测误差选择并宣布通用最优配置。

## 为什么比旧结论高

旧CSV统计表中的15站平均土壤 **{hist['saved_15_soil_rmse_mean']:.2f} K**、冠层 **{hist['saved_15_canopy_rmse_mean']:.2f} K**已追溯。使用当前本地存档和地面数据重放旧R程序的规则，各站RMSE与旧表最大差异 **{hist['replay_max_abs_difference_K']:.6f} K**，在旧表保留三位小数的舍入范围内。

旧规则有五个关键差别：

1. `T_Soil = inv_valid$T_Shaded_Soil`：旧表所谓“土壤”实际是阴影土壤，而非输出字段`T_Soil`背景土壤。不能沿用背景土壤的标签引用该旧数值。
2. 先要求冠层、阴影土壤、LST、TA、TS1都在0—60°C，再删除冠层或土壤预测—实测绝对差超过10 K的时刻。该筛选直接使用验证误差，保留样本上的RMSE不能代表未筛选产品的整体精度。
3. 旧月均将11—16 UTC混在同一个年月内平均；逐小时月均则保留日变化，各小时偏差更难互相抵消。
4. 旧报告包括2018—2025年及CD-Ygb，前次直接反演只有2024年，本次是欧洲14站2018—2024年；站点、年份、地面观测覆盖不同。
5. 旧欧洲存档更支持h=0.25、λ=1000的中心5×5实现；前次新配置用了h=0.05，同时修正了普朗克单位、负温编码和输入掩膜。参数和算法单位也确实发生变化。

下面固定**旧预测值本身**，统一欧洲14站、2018—2024年，只依次改变评价规则：

{table(history,['protocol','component','soil_definition','scale','sites','mean_site_rmse_K','total_pairs','total_raw_pairs'])}

H0=旧规则；H1=仅去掉误差阈值筛选；H2=温度范围改为−23.15—76.85°C；H3=土壤切换为背景土壤；H4=两个分量分别配对；H5=按年月及UTC小时聚合；H6=再去除相同站点时刻的重复记录。这些步骤会改变样本及参评支持，顺序会影响数值，不能把逐步变化当作可相加的独立因果贡献。

另发现旧存档在2018—2024年SE-Deg包含**{duplicate['identical_extra_rows_removed']}条额外的完全重复记录**。为复现原论文数值，旧协议回放及H0—H5保持原表重复权重；H6检验去重影响。原始参数回放比对已经去重；新反演逐站时刻唯一。重复明细及处理规则保存于`historical_duplicate_*`文件。

在欧洲14站2018—2024年、已通过0—60°C共同范围筛选的{n1}个配对中，旧10 K误差规则保留{n0}个，剔除{n1-n0}个（{100*(n1-n0)/n1:.1f}%）。该计数位于月均聚合前，与表中经过每月至少3对门槛后的total_raw_pairs不同。

“误差更大”和“温度更高”是不同问题。各模型在相同站点、相同时刻的温度差、偏差和RMSE分别保存在`common_support_temperature_changes.csv`及`common_support_controls*.csv`；不能仅由RMSE升高推断所有土壤或冠层温度都偏高。

## 固定参数对照：共同时间支持

每一对配置使用相同的站点时刻、参照与有效范围，避免把覆盖变化直接解释为参数效果。以下为月小时尺度；比较之间的共同样本仍可能不同。

{table(controls.loc[controls.scale.eq('monthly_hour')&controls.method.eq('estimate')&controls.component.isin(['background_soil','canopy'])],['comparison','component','model','sites','mean_site_rmse_K','mean_site_bias_K','total_pairs'])}

`hotspot_physical`只改变hotspot；`units_h005/h025`比较单位公式；`input_decode_and_mask_h025`同时改变输入解码和掩膜；`combined_new_vs_historical`是完整新旧组合比较，不可解释成单因素效应。legacy分支仅用于追溯错误实现，不能因某个RMSE较小便作为物理正确的生产方案。

在物理单位与共同时间支持下，h从0.05改为0.25使背景土壤月小时RMSE从{control('background_soil','physical_h005'):.2f}降至{control('background_soil','physical_h025'):.2f} K，冠层则从{control('canopy','physical_h005'):.2f}升至{control('canopy','physical_h025'):.2f} K。当前欧洲试验不支持将EVO的h=0.05直接视为两类分量均最优的通用参数；也不能据这次已查看的验证结果宣称0.25通过独立最优性检验。

## 各站覆盖和月小时误差

{table(statrows,list(statrows.columns))}

地面数据并非每站均覆盖2018—2024年全部年份；`ground_coverage.csv`逐年列明。反演覆盖和验证覆盖分开统计。无有效地面配对或不足3个月小时组合的站点不进入对应汇总，不将其误差设为0。

## 分尺度结果及原始LST对照

{table(compact,['component','scale','method','sites','mean_site_rmse_K','mean_site_bias_K','total_pairs','total_raw_pairs'])}

`estimate`=本次5×5站点反演；`bulk`=相同日期的EURO原始LST。背景土壤与阴影土壤的评分在完整CSV中分开保留。

## 数据、质量规则与验证

参数为h=0.05、λ=1000、δ=3 W m⁻² sr⁻¹ μm⁻¹，两阶段5×5，中心[2,2]。第一阶段中心阳照土壤辐射用于整个窗口第二阶段残差；最少10个共同有效邻域像元，行列式阈值1e−8。普朗克计算波长为10.5e−6 m。uint16负温按int16位模式恢复，0和−8000视为缺测；输入温度150—400 K，角度、LAI、发射率做物理范围检查，中心LAI≥0.05；四温度同时在250—350 K才算当前物理分支有效。

地面按TIMESTAMP_START视为UTC、最近±30分钟匹配；本次最大实际匹配差 **{result['max_ground_offset_minutes']:.1f}分钟**。逐站时区约定、测温深度/高度和辅助输入来源仍需元数据独立核实，时间戳相等本身不能证明这些约定。

批量结果与原始标量函数比较 **{result['scalar_checks']}次**，物理分支最大差 **{result['max_physical_scalar_difference_K']:.3g} K**；从保存配对重新计算 **{result['primary_metric_rows_verified']}行**主要指标，最大差 **{result['max_metric_recompute_difference_K']:.3g} K**。这是实现和统计一致性检查，不是“99%测温正确率”。

## 输出文件

- `station_instantaneous_primary.csv.gz`：全部可用小时有效瞬时温度，单位°C。
- `station_monthly_hour_primary.csv.gz`：按站点、年月、UTC小时计算的月均，含n_obs及至少3次观测标识；这里用全部有效反演日期，不受地面缺测影响。
- `matched_observations_all_models.csv.gz`：各配置与地面数据的配对。验证月均在相同配对日期上计算，不能直接拿未配对的产品月均代替。
- `station_predictions_all_models.csv.gz`：6个配置，包含无效标记；legacy控制分支不是可发布产品。
- `station_metrics.csv`、`summary.csv`、`primary_*_by_year.csv`：逐站、逐尺度、逐年结果；`all_available_hours`另报全部可用小时。
- `partitions/<site>/<year>/`：原始输入缓存、输入失败原因、逐文件哈希和断点记录；`input_failure_summary.csv`区分整日无EURO文件与具体时刻缺测，两类计数不混称缺测时刻数。
- `原始反演参数核查.md`：源码默认值、逐站历史回放及参数可辨识范围。

所有本轮成果位于 `{OUT.as_posix()}`。旧路径按results根目录的`storage_migration_20261009.json`迁移清单定位；历史原始日志不改写。区域生产保持暂停，论文正文与图件内容没有修改。
'''
    (OUT/'2018—2024站点直接反演与历史差异报告.md').write_text(text,encoding='utf8')
    static=pd.read_csv(OUT/'station_static_input_parameters.csv');static=static.loc[static.year.eq(2018)]
    landcover=pd.read_csv(OUT/'station_landcover_emissivity_audit.csv')
    st=static.pivot(index='site',columns='variable',values='center').reset_index()
    source=pd.read_csv(OUT/'source_parameter_inventory.csv');source['source']=source.source.map(lambda s:Path(s).name)
    h=probe.loc[probe.factor.eq('hotspot')].groupby('hotspot',as_index=False).agg(sample_n=('sample_n','sum'),exact=('all_four_exact','sum'),within001=('all_four_within_001','sum'))
    lamb=probe.loc[probe.factor.eq('lambda')].groupby('lambda',as_index=False).agg(sample_n=('sample_n','sum'),exact=('all_four_exact','sum'),within001=('all_four_within_001','sum'),max_difference_K=('max_diff_K','max'))
    delta=probe.loc[probe.factor.eq('delta')].groupby('delta_legacy',as_index=False).agg(sample_n=('sample_n','sum'),constraint_active=('constraint_active','sum'),max_change_K=('max_change_from_h025_l1000_d3_K','max'))
    report=f'''# 欧洲站点原始反演参数核查

## 结论与证据等级

历史欧洲14站存档在现有站点输入上，最支持 **中心5×5、hotspot=0.25、λ=1000、旧普朗克公式** 的组合。全2018—2024年回放中，存档四温度都处于−23.15—76.85°C的共同记录为 **{h25n}条**，其中 **{h25tol}条（{100*h25tol/h25n:.3f}%）**四温度差均≤0.01 K。

包括非物理极值在内，去重后的全部**{alln}条**历史有效记录都找到了对应回放；其中**{alltol}条（{100*alltol/alln:.3f}%）**四温度差均≤0.01 K。这个一致率超过99%，但不是测温精度或与地面实测的正确率。

这是与历史文件的数值一致性，不是对实测温度的精度。旧表中SE-Deg的{duplicate['identical_extra_rows_removed']}条完全重复记录已在参数比对前去重；极端非物理温度记录及存档缺项单独保留，不能为追求一致率悄悄删除；详见逐年及逐站fingerprint CSV。

中心入口源码实际传入δ=3；但回放δ=0.5、1、3、10得到相同结果，且这些抽查样本的约束均未触发。因此δ=3目前是**源码证据**，不是可由旧CSV唯一辨识的实际历史值。λ=1000优于本次检验的1、10、100候选，不能由有限候选证明连续参数空间中的数学唯一性。

## 中心站点入口

`{(HERE/'msg_lsct3.2-iter-site-cons-ig-center.py').as_posix()}`

| 参数或处理 | 原始入口 | 本次当前物理试验 |
|---|---|---|
| hotspot | 0.25；历史数值回放支持 | 0.05；另设0.25对照 |
| 叶倾角投影G / 聚集系数CIs、CIv | 0.5 / 1、1；hotspot_layer默认传值 | 同左 |
| λ | 主程序实际传入1000；函数默认100未被采用 | 1000 |
| δ | 3；原有辐射数值尺度，不能称3 K | 3 W m⁻² sr⁻¹ μm⁻¹，不能称3 K |
| 波长参数 | 10.5直接代入SI常数，单位不一致 | 10.5e−6 m，输出每μm谱辐射 |
| 第一/第二阶段 | 5×5 / 5×5，最少10个有效像元 | 同左 |
| 中心及残差 | [2,2]；中心阳照土壤值用于全邻域残差 | 同左 |
| 方程病态阈值 | abs(det)≥1e−8 | 同左 |
| 联合平差 | 两个方向观测＋三个分量先验 | 同左 |
| 时间 | 主程序9—16 UTC；旧验证11—16 UTC | 检查本地全部小时；主验证11—16 UTC |
| 温度解码 | 原数组直接/100+273.15，仅0剔除 | 恢复uint16负温；剔除0/−8000 |
| 输出范围 | 无四温度共同250—350 K约束 | 四温度共同250—350 K |
| 存档精度 | 温度保存2位小数 | 保留未舍入浮点数 |

旧辐射数值约为10⁻¹²量级，δ=3相对这个尺度非常大。在本次δ抽查中，它不发挥预期的温差限制作用；修正单位以后约束的有效强度也改变了。因此“只改单位而保留数字3”并不保证与旧反演等价。

土壤背景量在辐射域按gap=exp(−0.5×LAI/cos(SZA))混合阳照及阴影土壤后逆普朗克得到，不等于两者温度直接线性平均。原始验证R脚本取的却是阴影土壤列。

## 各站实际历史匹配

{table(param,list(param.columns))}

“合理温度”子集用于区分物理范围内的记录与历史非物理极值；全共同记录一致数也同时列出。筛选该子集不用于报告测温精度。

最大历史差异32.44 K出现在CZ-BK1 2021-11-24 14:00的约707万°C阳照土壤异常值上；物理范围内唯一超过0.01 K的记录为IT-Lsn 2020-10-07 16:00，最大差0.02 K。对这些记录重新调用原始标量函数，与批量实现仍一致至2.33e−10 K。剩余差异与历史CSV有关，现有证据尚不能唯一确定历史运行库、数值精度或存档处理原因；未把差异悄悄置零。详见`historical_replay_largest_differences.csv`和`historical_extreme_scalar_audit.json`。

## 参数候选回放

每站每年从存档共同且四温度合理的时刻均匀取最多16个，所有候选使用同一抽查时间集；不使用TA/TS1作为选参目标。

{table(h,list(h.columns))}

{table(lamb,list(lamb.columns))}

{table(delta,list(delta.columns))}

EVO旧结果此前更接近hotspot=0.05；这与欧洲14站的0.25不能混成一套已验证通用参数。本次欧洲样本的原始参数追溯不能替代独立站点/年份的精度验证。

## 站点原始输入参数

以下为实际静态5×5缓存中心值；角度单位为度，emis_s/emis_v无量纲。静态文件只存一套，7年读取值相同不证明它适用于7年全部卫星轨道时期。

{table(st,['site','lat','lon','vza_e','vaa_e','vza_i','vaa_i','emis_s','emis_v'])}

`station_static_input_parameters.csv`保留每站每年、中心及窗口极值。`station_dynamic_input_parameters.csv`保留LAI、SZA、SAA和双星LST原始编码的逐年中心值范围、5/50/95百分位及原始类型。统计仅针对双星中心输入均存在的候选时刻，不代表缺测时刻或完整全年气候分布。uint16中≥32768计数只表示需要检查有符号解码的编码数量，不能直接全部认定为有效负温。

实际查表核验表明14站植被发射率均与本地`IGBP_Emi.txt`的地类编码查表一致。原始提取代码将该表第1列除以1000作为植被发射率，土壤来源为`AG1km.v003.SoilEmi.ABI.Global.001D_LSE11.tif`，土地覆盖来源为`MCD12C1_2011_0.01.tif`。这证明当前缓存与查表规则一致，不证明这些常数代表站点每年的真实发射率。

{table(landcover,['site','station_type','cached_lc','emis_v','approx_center_distance_km','lc_5x5_codes'])}

FI-Let及SE-Svb登记为常绿针叶林，但缓存中心地类编码为8、植被发射率0.965；CZ-BK1及FI-Hyy缓存编码为1、发射率0.989。其他站点也存在站点类型与像元类型差异。按缓存经纬度估计的中心距离约{landcover.approx_center_distance_km.min():.2f}—{landcover.approx_center_distance_km.max():.2f} km，这些是空间代表性差异线索，不能仅据此判定地图或定位错误。

本地土壤发射率图和土地覆盖图的尺寸、地理变换相同，但CRS字符串不同（土地覆盖为Clarke 1866相关未知基准标签，发射率图为WGS84）；原始代码直接共用行列索引。这需要核实是否仅为标签差异，当前没有擅自重投影或重生产。

原始静态观测角时期、双星地理配准及LAI具体源版本仍需上游元数据独立核对；本次保留现有缓存，不重建上游数据。相关来源哈希和栅格元数据保存在`station_auxiliary_source_audit.json`。

## 同目录其他原始分支

{table(source,['source','line','declaration'])}

函数默认值与调用传值不同，以实际调用为准。其他分支出现h=0.1/0.2、λ=1/100/1000、δ=1/3/10，仅证明代码版本不同；不能据此给站点指定历史参数。源码SHA-256和声明行保存在`source_parameter_inventory.csv`；执行协议的确切源码哈希保存在`protocol.json`。
'''
    (OUT/'原始反演参数核查.md').write_text(report,encoding='utf8')
    print('REPORTS_SAVED',OUT,flush=True)

if __name__=='__main__':main()
