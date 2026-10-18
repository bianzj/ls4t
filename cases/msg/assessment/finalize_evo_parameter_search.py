"""Verify and summarize the frozen EVO search without reselecting on holdout."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from search_evo_parameters import metrics, sha256

P=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/parameter_search')


def main():
    r=json.loads((P/'search_results.json').read_text(encoding='utf-8'))
    legacy=json.loads((P/'historical_replay/report.json').read_text(encoding='utf-8'))
    history=json.loads((P/'historical_validation_reproduction.json').read_text(encoding='utf-8'))
    physical=json.loads((P/'historical_physical_control.json').read_text(encoding='utf-8'))
    panel=pd.read_csv(P/'frozen_reference_panel.csv');panel['time']=pd.to_datetime(panel.time,utc=True)
    preds=pd.read_csv(P/'selected_and_control_predictions.csv');preds['time']=pd.to_datetime(preds.time,utc=True)
    def get(label):
        z=preds.loc[preds.variant.eq(label)].pivot(index='time',columns='component',values='prediction')
        return z.reindex(pd.DatetimeIndex(panel.time))[['sunlit_soil','canopy']].to_numpy()
    base,best=get('B01_physical_R04'),get('OPT_selected')
    common=[]
    for split in ['development','holdout']:
        mask=panel.eligible.to_numpy()&panel.split.eq(split).to_numpy()&np.isfinite(base).all(axis=1)&np.isfinite(best).all(axis=1)
        for name,pred in [('B01_physical_R04',base),('OPT_selected',best)]:
            common.append({'variant':name,'split':split,**metrics(pred,panel,mask)})
    (P/'common_support_comparison.json').write_text(json.dumps(common,indent=2),encoding='utf-8')
    def m(label,split):return next(x for x in r['comparisons'] if x['variant']==label and x['split']==split)
    def row(label,title,split):
        q=m(label,split)
        return f"| {title} | {'8—10月开发期' if split=='development' else '11—12月保留期'} | {q['sunlit_soil_monthly_rmse_K']:.3f} | {q['canopy_monthly_rmse_K']:.3f} | {q['valid_n']}/{q['eligible_n']} | {q['penalized_macro_rmse_K']:.3f} |"
    table='\n'.join(row(label,title,split) for split in ['development','holdout'] for label,title in [('B01_physical_R04','单位修正后的R04基准'),('OPT_selected','开发期最优P0120')])
    common_rows='\n'.join(f"| {q['split']} | {q['variant']} | {q['valid_n']} | {q['sunlit_soil_monthly_rmse_K']:.3f} | {q['canopy_monthly_rmse_K']:.3f} |" for q in common)
    controls='\n'.join(f"| {q['variant']} | {q['sunlit_soil_monthly_rmse_K']:.3f} | {q['canopy_monthly_rmse_K']:.3f} | {q['penalized_macro_rmse_K']:.3f} |" for q in r['comparisons'] if q['split']=='development')
    mask=json.loads((P/'regional_mask_audit.json').read_text(encoding='utf-8'))
    example=mask['examples'][0]
    bootstrap=r['test_date_block_bootstrap']
    text=f'''# LS4T-MSG 参数比对、历史复现与最优候选

本报告对应冻结的960组搜索，选择记录见`selection.json`。**已经找出历史EVO表的关键参数差异，并复现原验证指标；也找到了本次搜索范围内的开发期最优候选。但保留期没有证明整体稳健改进，暂不将该候选用于全域重新生产。**

## 1. 历史参数差异已经定位

将现存站点入口的hotspot从0.25改为 **0.05**，保持λ=1000、δ=3、5×5中心解算及其余历史实现不变，实际重跑738条：

- 阳照土壤、冠层、阴影土壤三列均738/738完全相同。
- 四列共同完全相同737/738，比例99.8645%；剩余1条背景土壤相差0.01 K。时间戳完全对应，没有新增或丢失记录。
- 在原图件相同样本与分组上，阳照土壤641个原始配对、冠层644个，均为35个月—小时均值，RMSE复现为 **{history[0]['rmse_K']:.6f} K / {history[1]['rmse_K']:.6f} K**。

这直接支持此前R04未对上历史表主要是hotspot设置不同。这里只确认这一组配置能够重现历史结果，并不以数值一致代替物理正确性。完整结果为`historical_replay/`；这不是把历史CSV直接复制成预测。

## 2. 搜索前后发现的两个实现问题

### 2.1 原站点版本的普朗克单位不一致

原站点源码写入SI形式常数c1=1.191042972×10⁻¹⁶、c2=0.01438776877，但将波长10.5直接代入。若使用这些SI常数，10.5 μm需要先变为10.5×10⁻⁶ m，并明确每米到每微米的谱辐亮度换算。依据为[NIST的SI常数定义](https://www.nist.gov/si-redefinition/definitions-si-base-units)和[CIE普朗克定律](https://cie.co.at/eilvterm/17-24-005)。

实算300 K、10.5 μm：原站点函数返回 **{r['unit_audit']['legacy_B300']:.12g}**，SI一致的实现返回 **{r['unit_audit']['physical_B300_W_m2_sr_um']:.9f} W m⁻² sr⁻¹ μm⁻¹**。原函数正反变换能够互相抵消，并不证明辐射物理正确；其δ=3的物理含义也不成立。这一问题存在于本次复现所用的站点分支，不能据此声称采用另一套常数的区域入口也有相同单位错误。

因此，历史1.89/2.95 K仅说明该历史实现的数值验证结果可重现，不能继续作为该物理实现已经正确的证据。960组主搜索均采用SI一致的普朗克计算，原错误单位版本只作为历史对照，不参与最优物理配置选择。

### 2.2 区域代码与站点代码的缺测掩膜不同

区域`solve_2x2_system_5x5`分别将正规方程各项的NaN置0；当观测缺测而权重有限时，Aᵀb项变0，但AᵀA仍可能保留该缺测位置的权重。站点求解器则先用共同有效掩膜，令同一观测的全部方程项同时参加或退出求解。

在同一站点输入窗口的 {example['time']} 示例中，仅1个输入像元缺测：历史区域求和方式得到第一阶段阳照土壤 **{example['regional_first_sunlit_K']:.3f} K**，共同掩膜得到 **{example['consistent_mask_first_sunlit_K']:.3f} K**。这是中间解的实现敏感性，不是相对于地面真值的误差，也不是已经完成全域影响量化。

主搜索采用共同掩膜；`local_vector`表示在同一缓存5×5块上逐像元计算首阶段并扣除，边界采用nearest扩展。它保留共同掩膜，**不等同于原区域代码的缺测求和，也不等同于读取足够外围像元的全域反演**。包括A06在内的“regional-like”配置只能解释为区域式参数/残差的局部对照，不能宣称区域产品已复现。

## 3. 搜索协议与最优候选

在看保留期评分前，固定以下范围和判据：

| 维度 | 比较范围 |
|---|---|
| hotspot | 0.05、0.10、0.15、0.20、0.25、0.30、0.40、0.50 |
| λ | 0.01、0.1、1、10、100、1000 |
| δ，单位W m⁻² sr⁻¹ μm⁻¹ | 0.5、1、2、3、5 |
| 第一阶段窗口 | 3×3、5×5 |
| 第二阶段残差构造 | 中心首阶段估计用于整块；逐像元首阶段估计 |
| 第二阶段窗口 | 固定5×5 |

共960组。地面参考、输入角度/发射率/LAI、日期、物理有效范围和验证流程保持固定。无按反演—地面残差删除样本。

开发期为2017年8—10月，冻结输入/地面有效面板435个时刻；保留期为11—12月，239个时刻。两组均10—16 UTC。所有四个输出温度必须在250—350 K内，任一不满足则该产品时刻失效。此条件比此前R04只检查两个验证分量更严格，因此不能将新表直接与之前369个配对的全期指标混用。

选择指标为：两个分量等权、三个开发月份等权的逐时均方误差，再开方；固定面板上的失败预测按每分量20 K误差计入。另要求开发期有效率至少达到单位修正R04基准减1个百分点，本次门槛为98.7701%。这样不会仅通过放弃困难样本获得低分。

**开发期最优：P0120，hotspot=0.05、λ=1000、δ=5、第一阶段5×5、逐像元残差。** 960组均通过有效率门槛。该候选位于hotspot下边界、δ和λ上边界，故只能称为此次预设范围内最优，不是连续参数空间的全局最优。未在看到保留期结果后继续扩大搜索、改变损失或更换赢家。

## 4. 最优候选是否通过保留期检查

下面的两个RMSE是各自有效日期汇总的月—小时均值指标；最右列同时计入失败预测，是选择和完整覆盖比较所用指标。

| 配置 | 时段 | 土壤月—小时RMSE（K） | 冠层月—小时RMSE（K） | 有效/固定时刻 | 计入失败惩罚的总评分（K） |
|---|---|---:|---:|---:|---:|
{table}

开发期总体评分明显改善。但保留期最优候选失效5个时刻，基准失效4个；候选总评分从基准的3.815升至3.987 K，未达到“总体稳健更好”的要求。不能只强调月均RMSE下降而隐藏有效域变化。

为排除样本差异，另在双方共同有效时刻上比较：

| 时段 | 配置 | 相同原始配对数 | 土壤月—小时RMSE（K） | 冠层月—小时RMSE（K） |
|---|---|---:|---:|---:|
{common_rows}

对保留期按日期重采样2000次，候选减基准的日期等权、含失败惩罚的MSE差均值为{bootstrap['mean']:.3f} K²，95%区间[{bootstrap['ci95'][0]:.3f}, {bootstrap['ci95'][1]:.3f}] K²，跨过0，不能证明稳定优势。该日期等权统计与选择时的月份等权统计权重不同，不能混为同一个评分。

保留期虽然没有参与本轮选参，但此前会话已查看过覆盖这些日期的汇总结果；它不是从未接触过的外部独立验证集。单个EVO站点的结果也不能作为全欧洲—非洲的最优参数结论。

## 5. 哪些调整影响较大

以下单因素对照均基于同一SI修正后的R04基准，表中为开发期结果：

| 对照 | 土壤月—小时RMSE（K） | 冠层月—小时RMSE（K） | 含失败惩罚评分（K） |
|---|---:|---:|---:|
{controls}

A01仅将λ从1000改100；A02仅将hotspot从0.25改0.20；A03仅将第一阶段窗口改3×3；A04仅改逐像元残差；A05仅加入350 K冠层异常替换；A06同时采用区域式参数、窗口和残差，因此不是单因素试验。λ=100与1000之间的影响较小，不能把10倍参数差直接解释成主要误差来源。历史hotspot=0.05则已由逐值复现单独证实。

历史参数查明后，另补了其SI一致版本P0084（hotspot=0.05、λ=1000、δ=3、5×5中心解算），开发期土壤/冠层月—小时RMSE为{physical['evaluations'][0]['sunlit_soil_monthly_rmse_K']:.3f}/{physical['evaluations'][0]['canopy_monthly_rmse_K']:.3f} K，保留期为{physical['evaluations'][1]['sunlit_soil_monthly_rmse_K']:.3f}/{physical['evaluations'][1]['canopy_monthly_rmse_K']:.3f} K。该对照用于说明历史参数与单位修正的关系，未用来改选冻结的P0120，也不视为新的独立确认。

## 6. 当前可采取的配置决策

1. **历史复现配置已找到：** hotspot=0.05、λ=1000、δ=3、5×5中心解算，保留历史实现可重现原表。仅用于历史追溯，不作为继续使用错误单位的理由。
2. **后续物理实验的候选已保存：** P0120为本轮开发期最优；P0084是单位修正后的历史参数基线。两者均需更多独立站点/年份及真正区域输入支持验证；当前没有证据宣布P0120可替代整个生产档案。
3. **优先修复实现与确认范围：** 波长单位、正规方程共同缺测掩膜、原始LST/NoData与角度来源应先核实，再进行局部区域重放。参数调整不能代替这些处理。
4. 原生产源码、E:数据及论文图片均未覆盖。脚本仅新增可记录的`--hotspot`参数给站点试验入口；默认仍保持原值，任何生产配置都未静默切换。

## 7. 可复核文件

- `protocol.json`、`frozen_reference_panel.csv`：搜索范围、划分与固定参考面板。
- `development_grid_scores.csv`：960组开发期指标及编号；`selection.json`：在保留期评价前写入的选择记录。
- `candidate_predictions.npz`：所有候选预测，用于重算开发期指标；不将全体候选按保留期重排名。
- `controlled_comparisons.csv`、`selected_and_control_predictions.csv`：冻结候选及对照结果。
- `unit_audit.json`、`regional_mask_audit.json`：单位与缺测处理证据。
- `scalar_solver_verification.json`、`local_vector_solver_verification.json`：原标量求解器对26个真实时刻的独立数值核对，容差10⁻⁸ K。
- `historical_replay/`、`historical_validation_reproduction.json`：原入口实跑及1.89/2.95 K复现证据。
- `input_manifest.json`、`input_cache.npz`：只读输入的完整文件哈希与数值缓存。

代码位于`C:/work/ls4t-msg/cases/official/implementation/search_evo_parameters.py`及`finalize_evo_parameter_search.py`。本目录维护一份当前报告，不生成新的论文版本。
'''
    (P/'参数比对与推荐配置.md').write_text(text,encoding='utf-8')
    print('COMMON SUPPORT',json.dumps(common))
    print(P/'参数比对与推荐配置.md')


if __name__=='__main__':main()
