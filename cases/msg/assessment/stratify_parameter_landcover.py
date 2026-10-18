"""Describe land-cover-specific responses from completed station experiments."""
from pathlib import Path
import hashlib,json
import pandas as pd

BASE=Path('C:/work/ls4t-msg/cases/official/results/production_assessment')
STUDY=BASE/'parameter_argument_monthly_hour'
OUT=STUDY/'landcover_stratification'
OUT.mkdir(exist_ok=True)
sources=[STUDY/'station_metrics.csv',STUDY/'station_coverage.csv',BASE/'msg_5x5/station_direct_2018_2024/station_landcover_emissivity_audit.csv']
lc=pd.read_csv(sources[2]);metrics=pd.read_csv(sources[0]);cv=pd.read_csv(sources[1])
station_groups={'evergreen needleleaf forests':'forest','deciduous needleleaf forests':'forest',
 'croplands':'cropland','grasslands':'grassland','permanent wetlands':'wetland','open shrublands':'shrubland'}
expected={'evergreen needleleaf forests':1,'deciduous needleleaf forests':3,'croplands':12,'grasslands':10,'permanent wetlands':11,'open shrublands':7}
def cachegroup(code):
    if code in [1,2,3,4,5]:return 'forest'
    return {6:'shrubland',7:'shrubland',8:'woody_savanna',9:'savanna',10:'grassland',11:'wetland',12:'cropland',14:'crop_mosaic'}.get(code,'other')
lc['station_group']=lc.station_type.map(station_groups)
lc['pixel_group']=lc.cached_lc.map(cachegroup)
lc['station_expected_igbp']=lc.station_type.map(expected)
lc['label_disagreement']=lc.cached_lc.ne(lc.station_expected_igbp)
assert lc.station_group.notna().all() and len(lc)==14
lc.to_csv(OUT/'site_classification.csv',index=False)
counts=lc.groupby('station_group',as_index=False).agg(sites=('site','size'),site_ids=('site',lambda s:', '.join(s)))
m=metrics.loc[metrics.domain.eq('indirect')].merge(lc,on='site',validate='many_to_one')
summary=[]
for scheme in ['station_group','pixel_group']:
    g=m.groupby([scheme,'model','component','support','split'],as_index=False).agg(
      sites=('site','size'),rmse_K=('rmse_K','mean'),baseline_same_pairs_rmse_K=('baseline_rmse_K','mean'),
      mean_mse_change_K2=('mse_difference_K2','mean'),sites_improved=('mse_difference_K2',lambda s:int((s<0).sum())),
      monthly_groups=('n_groups','sum'),instantaneous_pairs=('n_raw','sum'))
    g=g.rename(columns={scheme:'landcover_group'});g['classification_scheme']=scheme;summary.append(g)
summary=pd.concat(summary,ignore_index=True);summary.to_csv(OUT/'stratified_metrics.csv',index=False)
c=cv.loc[cv.domain.eq('indirect')].merge(lc[['site','station_group','pixel_group']],on='site',validate='many_to_one')
c.to_csv(OUT/'classified_station_coverage.csv',index=False)
names=['hotspot_0.05','hotspot_0.5','lambda_0.0001','lambda_100','delta_0.5','delta_5','window_3_5','window_5_3']
key=summary.loc[summary.classification_scheme.eq('station_group')&summary.landcover_group.isin(['forest','cropland'])&summary.model.isin(names)&summary.support.eq('paired_unfiltered')]
key.to_csv(OUT/'forest_cropland_common_sample_comparison.csv',index=False)
def md(df):
    x=df.copy()
    for col in x:
        if pd.api.types.is_float_dtype(x[col]):x[col]=x[col].map(lambda v:'NA' if pd.isna(v) else f'{v:.3f}')
    return '| '+' | '.join(x.columns)+' |\n| '+' | '.join(['---']*len(x.columns))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in x.itertuples(index=False,name=None))
illustration=key.loc[key.model.isin(['delta_0.5','window_5_3'])&key.split.eq('all')]
text='''# 森林、农田等地表类型的参数响应

现有站点结果支持“参数响应可能随地类改变”，但还不支持直接发布森林/农田专属最优配置。本次仅重新汇总已完成的51套试验，没有重新反演或改变生产配置。

## 分类与样本

按本地站点清单的生态系统类型分组，另按缓存中心像元IGBP类别独立分组。前者不能代替像元分类；后者也不能证明整个5×5窗口同质。未把EVO单站混入欧洲间接站点。

'''+md(counts)+f'''

本地站点类型与中心像元IGBP类别有{int(lc.label_disagreement.sum())}/14处不一致。它可能包含尺度、混合地表、年代、位置或元数据问题，不能直接断言哪一方错误。
例如森林站FI-Let、SE-Svb缓存为IGBP 8（woody savannas），IT-TrF为10（grasslands）；农田DE-Kli、FR-EM2、IT-BCi中心均为12（croplands）。
森林组仅5站，且以针叶林为主；农田3站，部分分时段/组分只有2站。它们不足以代表所有森林或作物类型。

## 已观察到的差异

以下是2018—2024年逐小时月均RMSE，候选与基准使用共同有效配对，不按10 K参考误差筛选，各站等权平均，单位K；负的MSE变化代表候选更好。
每个候选的共同子集可能不同，基准必须使用表内与其配对的值。

'''+md(illustration[['landcover_group','model','component','sites','rmse_K','baseline_same_pairs_rmse_K','mean_mse_change_K2']])+'''

- delta=0.5：森林组冠层RMSE由4.85降至4.41 K，土壤由8.61降至8.35 K；农田冠层由5.00降至4.92 K，但土壤由8.16升至8.72 K。
- 分时段后，森林冠层改善较一致：2018—2022年5/5站、2023—2024年4/4有指标站改善。但森林土壤在后段恶化，不能称这个delta对森林全面更优。
- 第二阶段5×5改3×3：森林组全时段土壤和冠层均略改善，农田土壤恶化；森林土壤的改善在2023—2024年也未保持。
- hotspot=0.05对农田冠层有利，但背景土壤恶化；hotspot=0.5则呈相反取舍。即使同一地类，也不存在单凭某一个组分即可确定的最优值。
- lambda=100和1000在森林、农田都接近；极小lambda在部分森林冠层—气温对比中较好，却明显恶化土壤。不能把这个现象解释为森林必须使用小lambda。

## 参数如何考虑地类

hotspot直接进入冠层方向权重，更适合结合冠层结构讨论；类型标签只是结构的粗略代理，同为农田也可能随生长期变化。
window在代码中控制参与估计的邻元，实际应结合窗口内地表混合、温度差异及缺测情况，不能仅由森林/农田标签决定。
lambda是观测拟合与先验的权衡，并非地类的物理常数；delta限制先验组分辐射量差，也不应仅按类别固定而忽略时相。
这些是依据模型结构提出的解释假设，尚未用本次数据分离地类、气候、季节、LAI、位置及参考测量差异的因果贡献。

欧洲冠层参照是气温、土壤参照是探针温度。某地类的间接指标改善，可能只是更接近代理变量，不等于真实组分温度更准确。
森林delta=0.5对欧洲间接冠层有利，却明显损害EVO直接冠层验证，也说明两种证据不能简单互换。

## 下一步可检验的方案

先核对站点和像元类型，补充窗口地类比例/LAI异质性和季节；然后在每类中按站点留一、按年份分割，比较统一配置与分类型配置，并同时检查两个组分、覆盖率与未筛选共同样本。
优先检验hotspot、delta和窗口的类型依赖，lambda先保留稳定区间。只有在同类未参与选择的站点上仍获益，才有依据应用类型配置；现有样本尤其需要防止逐站调参过拟合。

## 依据与输出

IGBP编码按[NASA MOD12C1文件定义](https://ladsweb.modaps.eosdis.nasa.gov/filespec/MODIS/4/MOD12C1)解释，仅用于类别编码，不宣称缓存属于该产品版本。
多像元窗口与双角度信息结合的作用见[Bian等，2020](https://publikationen.bibliothek.kit.edu/1000124178)；该文不是本次地类参数最优性的证据。

- site_classification.csv：站点/像元分类、不一致标记、发射率和位置差异。
- stratified_metrics.csv：两套分类下的完整分类型、分时段、分评价口径结果，含欧洲10 K分支。
- forest_cropland_common_sample_comparison.csv：森林、农田关键候选的共同样本对照。
- classified_station_coverage.csv：逐站有效率。
'''
report=OUT/'地表类型与参数响应.md';report.write_text(text,encoding='utf8')
audit=dict(status='passed',sites=14,label_disagreements=int(lc.label_disagreement.sum()),
 source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 no_new_inversion=True,no_class_specific_configuration_selected=True,metadata='Local inventory, not independently verified site classification')
(OUT/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
print(counts.to_string(index=False));print(report)
