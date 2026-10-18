"""Summarize the completed study without changing the frozen experiment."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import parameter_argument_monthly_hour as study

P=study.OUT
s=pd.read_csv(P/'summary.csv');cv=pd.read_csv(P/'station_coverage.csv');members=pd.read_csv(P/'design_membership.csv')
protocol=json.loads((P/'protocol.json').read_text());configs=protocol['configs']
complete=json.loads((P/'complete.json').read_text());assert complete['status']=='passed'
assert all(study.sha(path)==sha for path,sha in protocol['source_sha256'].items())

names=['baseline','hotspot_0.05','hotspot_0.5','delta_0.5','delta_4','lambda_0.0001','lambda_100','window_3_5','window_5_3','interaction_h0.05_d5']
own=s.loc[s.model.isin(names)&s.support.eq('own_10K')&s.split.eq('all')]
table=own.pivot(index='model',columns=['domain','component'],values='mean_site_rmse_K')
table.columns=['_'.join(c)+'_RMSE_K' for c in table.columns];table=table.reindex(names).reset_index()
table.to_csv(P/'key_configuration_comparison.csv',index=False)
paired=s.loc[s.model.isin(names)&s.support.eq('paired_unfiltered')&s.split.eq('all')]
paired.to_csv(P/'key_common_sample_comparison.csv',index=False)

intro='''## 论证结论

本轮支持继续把两阶段5×5、较强正则化（lambda约100—1000）作为稳定基准；hotspot与delta体现直接/间接评价和组分之间的取舍。没有得到同时改善所有域、组分和覆盖率的统一替代结论，不能称唯一最优。

1. **窗口缩小有代价，支持保留两阶段5×5。** 第一阶段改3×3、第二阶段保持5×5，EVO阳照土壤RMSE由1.99升至2.30 K。仅第二阶段改3×3，EVO冠层由3.68升至4.78 K。欧洲某些阈值筛选后的数字下降，但有效率降低；在不按参考误差筛选的共同配对上，这两个窗口候选的欧洲土壤RMSE分别为9.46和9.14 K，对应各自共同样本的基准为8.34和8.45 K。
2. **lambda并非始终影响小，只是在较大取值区间趋于稳定。** 100与1000的结果接近，增加到10000的增益也很小。降到0.0001时，欧洲10 K筛选后的土壤/冠层RMSE为3.74/3.54 K，看起来更低；但土壤保留比例从44.5%降到21.9%，共同未筛选样本土壤RMSE从基准7.62恶化至15.90 K，EVO冠层也从约3.70恶化至5.42 K。不能采用筛选后的最低数值选lambda。
3. **delta对EVO冠层很重要，过小不合适。** delta=0.5时EVO冠层RMSE为6.25 K，基准delta=3为3.68 K；delta=4可降至3.57 K，但欧洲共同未筛选样本的土壤和冠层均略恶化。delta=3是本次可辩护的折中基准，不能据此证明精确最优点为3。
4. **hotspot没有跨域一致的单调最优方向。** 从0.25降到0.05，EVO阳照土壤/冠层由1.99/3.68降至1.92/3.24 K；但欧洲共同未筛选样本的背景土壤由基准8.07恶化至9.76 K。升至0.5有利于欧洲土壤，却使EVO冠层升至4.13 K、阳照土壤升至2.11 K。
5. **hotspot与delta必须共同解释。** h=0.05、delta=5的EVO冠层达到2.87 K，优于该h下delta=3的3.24 K；但其欧洲共同未筛选土壤RMSE为10.10 K，对应基准7.97 K。这个组合不能仅凭EVO的优势直接作为区域生产参数。

以上RMSE均为逐小时月均尺度。标为“共同未筛选”时，每个候选与基准使用相同配对且没有参考误差筛选；基准数值随共同子集变化，因此不能混用。保留比例为各站固定输入参考候选上的比例再等权平均，包含物理反演失败与10 K筛选，不是全年卫星覆盖率。

### 关键配置对比

下表EVO无误差筛选，欧洲按各配置自身瞬时10 K条件筛选，因此须同时参考共同样本与覆盖率文件，不把表中最低值直接当最优。

'''+study.md(table)+'''

这些结果已足以说明为何不宜缩小窗口、为何不宜把lambda降得很小，以及hotspot和delta为何需要折中。它们是站点证据支持的有限范围建议，尚不足以证明跨欧洲—非洲所有地类和季节的普适最优配置。

'''
report=P/'逐小时月均参数论证.md';text=report.read_text(encoding='utf8')
title,body=text.split('\n',1)
text=title+'\n\n'+intro+body
text=text.replace('候选配置不再按自身误差删点，因此候选月均误差可以超过10 K。','候选配置不再按自身误差删点，因此候选月均误差可以超过10 K。该条件仍使用基准误差，可能偏向基准，只用作筛选敏感性诊断，不能当无偏选参依据；主要交叉证据为paired_unfiltered。')
report.write_text(text,encoding='utf8')

# Keep sub-kelvin changes visually proportional instead of auto-scaling a 0.003 K band.
original_savefig=matplotlib.figure.Figure.savefig
def fixed_savefig(fig,*args,**kwargs):
    if len(fig.axes)==12:
        for ax in fig.axes[:8]:
            low,high=ax.get_ylim()
            if high-low<.5:
                mid=(low+high)/2;ax.set_ylim(max(0,mid-.25),mid+.25)
    return original_savefig(fig,*args,**kwargs)
matplotlib.figure.Figure.savefig=fixed_savefig
study.render(s,cv,members,configs)
matplotlib.figure.Figure.savefig=original_savefig

# Re-render the heatmap with readable contrast for annotations on bright cells.
fig,axs=plt.subplots(2,2,figsize=(11,8),layout='constrained')
for i,domain in enumerate(['direct','indirect']):
    for j,comp in enumerate(['soil','canopy']):
        z=s.loc[s.domain.eq(domain)&s.component.eq(comp)&s.support.eq('own_10K')&s.split.eq('development')]
        z=members.loc[members.family.eq('hotspot_delta')].merge(z,on='model')
        z['h']=z.model.map(lambda n:configs[n]['hotspot']);z['d']=z.model.map(lambda n:configs[n]['delta'])
        tab=z.pivot(index='h',columns='d',values='mean_site_rmse_K').sort_index()
        ax=axs[i,j];im=ax.imshow(tab,aspect='auto',cmap='viridis')
        ax.set_xticks(np.arange(len(tab.columns)),tab.columns);ax.set_yticks(np.arange(len(tab)),tab.index)
        ax.set_xlabel('delta (radiance units)');ax.set_ylabel('hotspot');ax.set_title(domain+' '+comp)
        for y in range(len(tab)):
            for x in range(len(tab.columns)):
                v=tab.iloc[y,x];color='black' if im.norm(v)>.55 else 'white'
                ax.text(x,y,f'{v:.2f}',ha='center',va='center',fontsize=8,color=color)
        fig.colorbar(im,ax=ax,label='Monthly-hour RMSE (K)')
fig.suptitle('Development-period h/d interaction | own support | Europe filtered <=10 K\nDirect and indirect references differ; no pooled accuracy or optimum claim')
for suffix in ['png','pdf']:fig.savefig(P/f'hotspot_delta_interaction.{suffix}',dpi=170)
plt.close(fig)
audit={'completed_experiment_unchanged':True,'canonical_report':str(report),'finalizer_sha256':study.sha(__file__),
       'visual_QA':'Inspected three figures, expanded overly narrow RMSE axes and fixed heatmap text contrast',
       'artifacts_sha256':{p.name:study.sha(p) for p in [report,P/'parameter_effects_direct.png',P/'parameter_effects_indirect.png',P/'hotspot_delta_interaction.png']}}
(P/'report_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
print(report)
