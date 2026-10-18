"""Report the station-cache inversion separately from regional extraction."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd

OUT=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/msg_5x5/station_direct_validation')
def f(x):return '—' if pd.isna(x) else f'{x:.2f}'

def main():
    result=json.loads((OUT/'result.json').read_text());protocol=json.loads((OUT/'protocol.json').read_text())
    scores=pd.read_csv(OUT/'station_metrics.csv');summary=pd.read_csv(OUT/'summary.csv');coverage=pd.read_csv(OUT/'coverage.csv')
    for col in ['background_soil_pairs','canopy_pairs']:coverage[col]=coverage[col].fillna(0).astype(int)
    sites=pd.read_csv(OUT/'selected_stations.csv');pairs=pd.read_csv(OUT/'matched_observations.csv');monthly=pd.read_csv(OUT/'matched_monthly.csv')
    # Recompute every score from saved unaggregated matched observations.
    errors=[]
    for r in scores.itertuples():
        x=pairs.loc[pairs.site.eq(r.site)&pairs.component.eq(r.component)]
        col='estimate' if r.method=='direct_5x5' else 'bulk'
        if r.scale!='instantaneous':
            keys=['month']+(['hour'] if r.scale=='monthly_hour' else [])
            g=x.groupby(keys);n=g.size();x=g[[col,'reference']].mean().loc[n>=3]
        assert len(x)==r.n
        if len(x):errors.append(abs(float(np.sqrt(np.mean((x[col]-x.reference)**2)))-r.rmse_K))
    assert max(errors)<1e-9
    summaryrows=[]
    for r in summary.itertuples():
        summaryrows.append(f'| {r.component} | {r.scale} | {r.method} | {r.sites} | {r.mean_site_rmse_K:.2f} | {r.mean_site_bias_K:.2f} | {r.total_pairs} |')
    stationrows=[]
    for s in sites.id:
        def cell(comp):
            z=scores.loc[scores.site.eq(s)&scores.component.eq(comp)&scores.scale.eq('monthly_hour')].set_index('method')
            return '— | — | 0' if z.empty else f"{f(z.loc['direct_5x5','rmse_K'])} | {f(z.loc['bulk','rmse_K'])} | {int(z.loc['direct_5x5','n'])}"
        stationrows.append(f'| {s} | {cell("background_soil")} | {cell("canopy")} |')
    covrows=[]
    for r in coverage.itertuples():
        covrows.append(f'| {r.site} | {r.scheduled} | {r.center_input_valid} | {r.retrieval_valid} | {getattr(r,"background_soil_pairs",0)} | {getattr(r,"canopy_pairs",0)} |')
    differences=[]
    for (comp,scale),z in scores.loc[scores.enough_groups].groupby(['component','scale']):
        table=z.pivot(index='site',columns='method',values='rmse_K').dropna()
        differences.append({'component':comp,'scale':scale,'sites':len(table),'direct_better_than_bulk':int((table.direct_5x5<table.bulk).sum())})
    def stat(comp,scale):
        z=summary.loc[summary.component.eq(comp)&summary.scale.eq(scale)&summary.method.eq('direct_5x5')].iloc[0]
        return f'{z.mean_site_rmse_K:.2f} K（{int(z.sites)}站）'
    text=f'''# 欧洲站点 5×5 输入缓存：直接反演与验证

**已有站点层级的反演输入，本次已经直接读取这些输入开展反演，没有从区域组分温度产品提取站点值。**

14 个所选欧洲站点均存在 `E:\\PRODUCTS\\SITE\\<站点名>`，目录含 2018—2025 年。实际抽查的静态及动态输入均为 5×5 矩阵。年度目录存在不等于每天每个时刻均有效，本次逐文件核验范围为 **2024 全年、11—16 UTC**，每站安排 2196 个时刻；具体缺文件、云/缺测和反演失败记录分别保留。

## 数据结构和实际入口

```text
E:\\PRODUCTS\\SITE\\DE-Kli\\
  static\\
    vza_e.tif / vaa_e.tif       EURO观测角（度）
    vza_i.tif / vaa_i.tif       IODC观测角（度）
    emis_s.tif / emis_v.tif     土壤与植被发射率
    lat.tif / lon.tif / lc.tif  经纬度与土地类型
  2024\\06\\15\\
    LAI_20240615.tif           已缩放的LAI
    LST_202406151200_e.tif      EURO温度输入
    LST_202406151200_i.tif      IODC温度输入
    SZA_202406151200.tif        太阳天顶角
    SAA_202406151200.tif        太阳方位角
```

本次直接反演程序：`C:\\work\\ls4t-msg\\cases\\official\\implementation\\validate_station_direct_europe.py`。主程序只读取站点缓存和地面数据；区域生产目录只读取 `status.json` 以确认仍暂停，不作为反演输入。

## 直接反演结果

- 有有效反演结果的站点：**{result['sites_with_valid_retrievals']} / 14**；有效反演时刻：**{result['valid_retrievals']}**。
- 瞬时站点等权平均 RMSE：背景土壤 **{stat('background_soil','instantaneous')}**；冠层 **{stat('canopy','instantaneous')}**。
- 同一 UTC 小时分别计算月均后：背景土壤 **{stat('background_soil','monthly_hour')}**；冠层 **{stat('canopy','monthly_hour')}**。

这里仍是背景土壤对 TS_1 浅层土壤探针、冠层对 TA 气温的**间接一致性评价**，不能解释成组分辐射温度的直接测量精度。前一份区域提取报告使用 2018 年 1—7 月，输入网格和年份都与本次不同，不能把两个报告的 RMSE 相减后称为仅改变反演方式的提升。

## 参数及质量控制

固定 hotspot=0.05、λ=1000、δ=3 W m⁻² sr⁻¹ μm⁻¹，两阶段均 5×5。中心索引为 [2,2]；第一阶段中心阳照土壤估计用于整个邻域第二阶段残差。普朗克计算采用 SI 一致的 10.5 μm 波长，未沿用历史站点分支的错误单位。LAI、观测角、太阳角、发射率使用缓存中的物理值，不重复除缩放系数。

负摄氏 LST 恢复为有符号 int16 后解码；零值与 -8000 保守视为缺测。输入使用共同有效掩膜；太阳和观测天顶角均在 [0°,90°)，中心 LAI≥0.05，四个输出共同满足 250—350 K。没有按照预测—实测误差剔除异常点，也没有在本次结果上继续调参。

批量公式与原站点标量求解函数做了 {len(result['scalar_checks'])} 个跨站、跨时刻比较，最大温差 {result['max_scalar_error_K']:.3g} K。该数字只证明实现一致性，不是温度测量精度。

## 各站点按小时月均误差

同一站点、分量的新反演和原始 EURO LST 始终使用相同的实测配对日期。RMSE 单位为 K，n 是有效月份—小时组合数；每组至少 3 个原始配对。

| 站点 | 土壤直接反演 | 土壤LST对照 | n | 冠层直接反演 | 冠层LST对照 | n |
|---|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(stationrows)+'''

## 各尺度汇总

instantaneous=瞬时配对；monthly_hour=同月同 UTC 小时；monthly_calendar=同月所有 11—16 UTC 有效配对合并。汇总为站点 RMSE 和偏差的算术平均，非全部样本混合 RMSE。瞬时至少 3 对；月尺度至少 3 个有效组合，参评站点随尺度不同。偏差为估计减参照。

| 分量 | 尺度 | 方法 | 站点数 | 平均RMSE(K) | 平均偏差(K) | 配对总数 |
|---|---|---|---:|---:|---:|---:|
'''+ '\n'.join(summaryrows)+'''

## 覆盖与限制

| 站点 | 计划时刻 | 中心输入有效 | 四分量有效 | 土壤实测配对 | 冠层实测配对 |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(covrows)+'''

站点窗口是现有缓存，静态角度的时期适用性、双星窗口对应关系、辅助数据来源及地理定位仍待独立核实；本次没有重建这些上游输入。有效 0°C 与缓存缺测编码可能混淆。地面 TIMESTAMP_START 沿用 UTC、最近 ±30 分钟匹配，需要另行逐站核实时间及测温深度/高度元数据。一个年度不能代表完整八年精度。

FI-Let 的目录存在，但 2024 年 2196 个计划时刻中，47 个缺少所需输入文件，其余 2149 个双星中心 LST 至少一侧无效，因此没有有效直接反演结果，不参加精度汇总。这个问题位于站点输入阶段，不能解释为该站反演 RMSE 为零，也不能据此断言算法在该站准确或不准确。DE-Kli、IT-Lsn 没有本次所用的有效 TS_1 配对，只评价其冠层与气温的间接一致性。

`direct_predictions.csv` 为重新反演的站点温度；`matched_observations.csv` 为实测配对；`matched_monthly.csv` 为相同日期上计算的月均；`station_metrics.csv` 含各站各尺度 RMSE、MAE、偏差和样本数。`input_manifest.jsonl` 记录实际使用输入的 SHA-256，`protocol.json` 记录源码和协议。

区域批量生产仍保持暂停。论文及图件未改动。
'''
    (OUT/'站点直接反演验证报告.md').write_text(text,encoding='utf8')
    audit={'status':'passed','recomputed_metric_rows':len(scores),'max_score_difference_K':max(errors),
           'max_ground_time_offset_minutes':float(pairs.offset_minutes.abs().max()),'direct_better_than_bulk':differences,
           'report_sha256':hashlib.sha256((OUT/'站点直接反演验证报告.md').read_bytes()).hexdigest(),
           'first_station_prefetch_equivalence':hashlib.sha256((OUT/'CZ-BK1_direct_predictions.csv').read_bytes()).hexdigest()=='2183cbeb95c433c2b67848718e1df e1c14e31a78c9437b6d9d6c6a85716b85c2'.replace(' ','')}
    assert audit['first_station_prefetch_equivalence']
    (OUT/'validation_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
    print(summary.to_string(index=False));print('INPUT_CACHE_DIRECT_ONLY',result['valid_retrievals'])

if __name__=='__main__':main()
