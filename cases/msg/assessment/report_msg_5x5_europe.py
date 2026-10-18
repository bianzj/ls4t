"""Summarize paired regional-product validation; no paper figure replacements."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd

OUT=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/msg_5x5/europe_validation')
def f(x):return '—' if pd.isna(x) else f'{float(x):.2f}'

def main():
    r=json.loads((OUT/'result.json').read_text());p=json.loads((OUT/'protocol.json').read_text())
    m=pd.read_csv(OUT/'station_metrics.csv');s=pd.read_csv(OUT/'summary.csv')
    c=pd.read_csv(OUT/'station_coverage.csv');a=pd.read_csv(OUT/'all_extracted_matches.csv',parse_dates=['time'])
    sites=pd.read_csv(OUT/'selected_stations.csv')
    comparison=m.loc[m.support.eq('new_old_bulk')&m.scale.eq('monthly_calendar')]
    comparisons=[]
    for comp in ['background_soil','canopy']:
        w=comparison.loc[comparison.component.eq(comp)].pivot(index='site',columns='method',values='rmse_K')
        n=comparison.loc[comparison.component.eq(comp)&comparison.method.eq('new_5x5')].set_index('site')['n']
        w=w.loc[n>=3].dropna()
        comparisons.append({'component':comp,'eligible_sites':len(w),'new_better_than_old':int((w.new_5x5<w.old_regional).sum()),
                            'new_better_than_bulk':int((w.new_5x5<w.bulk).sum()),
                            'mean_new_rmse_K':w.new_5x5.mean(),'mean_old_rmse_K':w.old_regional.mean(),'mean_bulk_rmse_K':w.bulk.mean()})
    coverage=[]
    for sid,x in a.loc[a.primary_month].groupby('site'):
        for comp,ref in [('background_soil','TS_1'),('canopy','TA')]:
            valid_ref=x[ref].between(-23.15,76.85)&x.bulk.between(-23.15,76.85)
            new=valid_ref&x[f'new_{comp}'].between(-23.15,76.85)
            old=valid_ref&x[f'old_{comp}'].between(-23.15,76.85)
            coverage.append({'site':sid,'component':comp,'reference_bulk_candidates':int(valid_ref.sum()),
                             'new_pairs':int(new.sum()),'old_pairs':int(old.sum()),'common_pairs':int((new&old).sum())})
    cov=pd.DataFrame(coverage);cov.to_csv(OUT/'paired_coverage.csv',index=False)
    # Equal site weighting; report only sites with >=3 distinct monthly pairs.
    table=[]
    for sid in sites.id:
        def cell(comp):
            z=comparison.loc[comparison.site.eq(sid)&comparison.component.eq(comp)].set_index('method')
            if z.empty or z.loc['new_5x5','n']==0:return '— | — | — | 0'
            return ' | '.join([f(z.loc[k,'rmse_K']) for k in ['new_5x5','old_regional','bulk']]+[str(int(z.loc['new_5x5','n']))])
        table.append(f'| {sid} | {cell("background_soil")} | {cell("canopy")} |')
    summaryrows=[]
    for _,z in s.loc[s.support.eq('new_bulk')].iterrows():
        summaryrows.append(f'| {z.component} | {z.scale} | {z.method} | {int(z.sites)} | {f(z.mean_site_rmse_K)} | {f(z.mean_site_bias_K)} | {int(z.total_pairs)} |')
    covrows=[]
    for sid in sites.id:
        z=cov.loc[cov.site.eq(sid)].set_index('component')
        covrows.append(f"| {sid} | {int(z.loc['background_soil','new_pairs'])} / {int(z.loc['background_soil','old_pairs'])} / {int(z.loc['background_soil','common_pairs'])} | {int(z.loc['canopy','new_pairs'])} / {int(z.loc['canopy','old_pairs'])} / {int(z.loc['canopy','common_pairs'])} |")
    valid_ground=(c.valid_TS1_primary>0)|(c.valid_TA_primary>0)
    excluded=c.loc[~valid_ground,'site'].tolist()
    actual=pd.read_csv(OUT/'actual_monthly_file_metrics.csv')
    actualrows=[]
    for sid in sites.id:
        def actualcell(comp):
            z=actual.loc[actual.site.eq(sid)&actual.component.eq(comp)]
            return '— | 0' if z.empty else f"{f(z.iloc[0].rmse_K)} | {int(z.iloc[0].n)}"
        actualrows.append(f'| {sid} | {actualcell("background_soil")} | {actualcell("canopy")} |')
    conclusions=[]
    for q in comparisons:
        title='背景土壤—浅层土壤探针' if q['component']=='background_soil' else '冠层—气温'
        change='降低' if q['mean_new_rmse_K']<q['mean_old_rmse_K'] else '升高'
        conclusions.append(f"- **{title}**：同样本下，站点等权平均月均 RMSE 从旧版 {q['mean_old_rmse_K']:.2f} K 变为 5×5 的 {q['mean_new_rmse_K']:.2f} K（{change}）；原始 EURO LST 为 {q['mean_bulk_rmse_K']:.2f} K。{q['eligible_sites']} 个可评价站点中，{q['new_better_than_old']} 个优于旧版、{q['new_better_than_bulk']} 个优于原始 LST。")
    text='''# MSG 5×5：欧洲所选站点验证

## 结论

**目前不能认定该版本已通过欧洲站点验证，建议保持批量生产暂停。** 新产品与 EURO LST 共同日期上的站点等权平均 RMSE：瞬时背景土壤 **15.66 K（7站）**、冠层 **5.48 K（8站）**；按同一 UTC 小时计算月均后为 **11.82 K（6站）**、**5.49 K（7站）**。土壤分量与浅层探针的差异仍很大；站点间有效月份也不均衡。

下面与旧版的严格同样本比较受旧版可用性限制，不能用其少数站点平均代替以上更完整的新产品结果：

'''+ '\n'.join(conclusions)+f'''

这些是**间接一致性误差**，不是组分辐射温度的直接精度，也不是“正确率”。TS_1 是浅层土壤探针温度，TA 是气温；与卫星背景土壤、冠层辐射温度的物理含义不同。不将该结果与 EVO 的直接组分验证 RMSE 混合。

## 本次范围和方法

- 使用暂停时已经落盘的区域 5×5 瞬时产品，**没有重新启动批量生产，也没有改动论文或原图**。
- 共核对 14 个欧洲站点；主评价期 **2018 年 1—7 月，11—16 UTC**。8 月各时次尚未全部完成，不计入主评分。2017 年不纳入原论文从 2018 年开始的其他站点比较口径。
- {int(valid_ground.sum())} 个站点具有该时段有效实测，{r['sites_with_valid_new_ground_pairs']} 个站点有有效新产品—实测配对。无重叠有效实测的站点：{', '.join(excluded)}；不能据此判断这些站点的产品精度。FI-Hyy 虽有该时段时间行，温度列均为缺测，不能计为有效观测覆盖。
- 按站点经纬度提取包含站点的区域网格像元；产品本身是 5×5 邻域反演，未额外进行 5×5 空间平均。网格约 0.03°，站点与像元中心距离见 `selected_stations.csv`。
- 地面 TIMESTAMP_START 沿用原流程解释为 UTC，最近邻匹配容差 ±30 分钟。时区、观测区间代表时刻和各站探针深度仍需逐站元数据核实。
- 各温度的有效范围为 250—350 K；缺测保留，不用反演残差筛选日期或异常点，不调参数。
- 新版、旧版区域产品、原始 EURO LST 的优劣比较只用三者及参照均有效的**相同日期**。另报告新产品与 LST 的共同有效样本，避免旧版缺测掩盖新产品可用性。
- 每月/每月每时次至少 3 个有效配对；月尺度站点等权汇总至少需 3 个月或 3 个月—时次组合，瞬时汇总至少需 3 个原始配对。偏差定义为估计减参照。本次实际保留配对的时间差均为 0 分钟，未使用 ±30 分钟的偏移匹配。

## 同样本月均比较

这里采用论文已有口径：同一自然月内汇总有效的 11—16 UTC 配对，再计算月均误差。数字为 RMSE（K），n 为配对月份数；n<3 的站点不参加跨站平均。

| 站点 | 土壤5×5 | 土壤旧版 | 土壤LST | n月 | 冠层5×5 | 冠层旧版 | 冠层LST | n月 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(table)+'''

## 瞬时与按小时月均结果

下表为新产品和 LST 共同有效样本。汇总值是站点 RMSE/偏差的算术平均，不是将全部站点样本混在一起计算的 RMSE。monthly_calendar 是上面的自然月口径；monthly_hour 是每月按 UTC 小时分别平均；instantaneous 是原始配对时刻。

| 分量 | 时间尺度 | 方法 | 站点数 | 平均RMSE（K） | 平均偏差（K） | 配对总数 |
|---|---|---|---:|---:|---:|---:|
'''+ '\n'.join(summaryrows)+f'''

月均必须使用与地面观测相同的日期。`matched_monthly_hour.csv` 是共同日期重新汇总的逐小时月均；它不一定等于包含全部产品有效日期的月均文件。

不能仅引用自然月汇总后的冠层 3.18 K：这一数值合并了不同时次，且只保留至少 3 个月的 5 个站点。高山站 IT-Tor、IT-TrF 只有 2 个有效月份，不参加该平均；其按小时月均冠层 RMSE 仍分别约 8.44、9.63 K。FI-Sii 仅 16 个原始配对，土壤瞬时 RMSE 约 20.07 K，不能用少量冬夏样本掩盖这一差异。偏差成因尚未分离：需分别核查观测深度/高度与空间代表性、地形、时刻约定和反演稳定性，不把全部差异归因于某一个参数。

另直接读取已生产月均文件，核对了 {r['actual_monthly_values_checked']} 个站点—月份—小时值与瞬时均值的一致性，最大差异 {r['max_monthly_readback_difference_K']:.8f} K。仅在月均文件全部有效日期均有参照、且 n≥3 时，纳入 `actual_monthly_file_metrics.csv`，对应原始配对见 `actual_monthly_file_pairs.csv`。这样不会拿不同采样日期的两个平均值假装同样本验证。

下表直接评价已保存的逐小时月均文件，数字为 RMSE（K），n 为符合共同日期要求的月份—小时组合数；这些样本不一定与上一表相同，不应横向混算。

| 站点 | 土壤月均文件RMSE | n | 冠层月均文件RMSE | n |
|---|---:|---:|---:|---:|
'''+ '\n'.join(actualrows)+'''

## 样本覆盖

以下每格依次为：新产品与参照配对数 / 旧产品与参照配对数 / 新旧共同配对数，均要求同时有有效 EURO LST。新旧独立有效样本数可以不同，不能直接据其独立 RMSE 判断谁更好。

| 站点 | 土壤：新 / 旧 / 共同 | 冠层：新 / 旧 / 共同 |
|---|---:|---:|
'''+ '\n'.join(covrows)+'''

## 使用限制及复现

仅一个不完整年度、8 个有时间重叠的欧洲站点，不能外推为 2017—2025 全区域精度，也不证明全区域最优参数。空间代表性、高山/湿地异质性、参考温度物理差异和冬季有效观测不足都可能影响结果。现有零值/NoData 混淆、静态观测角和辅助数据坐标系统问题未因这次统计而消除。

来源与哈希见 `input_manifest.json`；冻结的样本范围、参数、坐标提取及比较协议见 `protocol.json`。逐站全部尺度的 RMSE、偏差、MAE、配对数见 `station_metrics.csv`；原始提取和匹配见 `all_extracted_matches.csv`。批量生产的暂停状态在验证前后 SHA-256 一致。

复现入口：`C:\\work\\ls4t-msg\\cases\\official\\implementation\\validate_msg_5x5_europe.py`；报告入口：`report_msg_5x5_europe.py`。
'''
    (OUT/'欧洲站点5×5验证报告.md').write_text(text,encoding='utf8')
    (OUT/'comparison_conclusions.json').write_text(json.dumps(comparisons,indent=2),encoding='utf8')
    print(json.dumps(comparisons,indent=2))
    print(s.loc[s.support.eq('new_bulk')].to_string(index=False))

if __name__=='__main__':main()
