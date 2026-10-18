"""Select among 51 existing predictions only. No retrieval function is called."""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
import pandas as pd
from select_landcover_parameters import make_specs,cell_metrics,check_cell_independently,rank,FIELDS,CLASSES,md

BASE=Path('C:/work/ls4t-msg/cases/official/results/production_assessment')
SOURCE=BASE/'parameter_argument_monthly_hour'
OUT=SOURCE/'landcover_stratification/selection_existing'
OUT.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')

def main():
    if (OUT/'selection.json').exists():raise RuntimeError('Existing-data selection already frozen; inspect rather than rerank.')
    interrupted=BASE/'landcover_parameter_selection'
    progress=json.loads((interrupted/'progress.json').read_text())
    progress.update(status='interrupted_by_user',reason='Use only pre-existing 51 configurations; do not rerun inversion',results_used=False)
    (interrupted/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2),encoding='utf8')
    protocol=json.loads((SOURCE/'protocol.json').read_text());configs=protocol['configs'];names=list(configs);assert len(names)==51
    lc=pd.read_csv(SOURCE/'landcover_stratification/site_classification.csv')
    panel=pd.read_csv(SOURCE/'frozen_reference_panel.csv.gz');panel['station_group']=panel.site.map(lc.set_index('site').station_group).fillna('EVO')
    files=[SOURCE/'component_predictions.npz',SOURCE/'frozen_reference_panel.csv.gz',SOURCE/'station_metrics.csv',SOURCE/'protocol.json',SOURCE/'landcover_stratification/site_classification.csv']
    p=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate_count=51,
        action='Postprocessing existing predictions only; no new inversion',
        source_sha256={str(f):sha(f) for f in files},configurations=configs,
        split='Development 2018-2022; retrospective validation 2023-2024; never rerank on validation',
        classification='Local station types: forest, cropland, grassland, not pixel classes',
        objective='Instantaneous absolute error <=10 K, then monthly-hour paired means; fixed eligible group, >=3 pairs; missing group assigned 100 K^2; site-equal MSE, two baseline-normalized components equally weighted',
        gates='At each site/component raw and filtered pair coverage drop <=2 percentage points; monthly coverage drop <=5 points; class/component shared-unfiltered MSE increase <=21%',
        LOSO='Fit on remaining development sites; at least 2 training sites; conditional limited-sample diagnostic',
        discarded_run='The interrupted 3200-grid run and its checkpoints are excluded')
    js('protocol.json',p)
    with np.load(SOURCE/'component_predictions.npz') as f:
        values={name:{comp:f[name+'__'+comp] for comp in ['soil','canopy']} for name in names}
    baseline_index=names.index('baseline');b=values['baseline']
    def evaluate_split(split):
        ix=np.flatnonzero(panel.station_group.isin(CLASSES)&panel.split.eq(split))
        pp=panel.iloc[ix].reset_index(drop=True);specs=make_specs(pp)
        arr=np.stack([np.stack([cell_metrics(values[n][s['component']][ix],b[s['component']][ix],s) for s in specs]) for n in names])
        return ix,pp,specs,arr
    ix,dp,specs,arr=evaluate_split('development');base=arr[baseline_index]
    for j,s in enumerate(specs):check_cell_independently(b[s['component']][ix],b[s['component']][ix],s,base[j])
    js('development_cells.json',[{k:s[k] for k in ['site','station_group','component','n_eligible_pairs','n_eligible_monthly']} for s in specs])
    np.savez_compressed(OUT/'development_scores_by_cell.npz',metrics=arr,fields=np.array(FIELDS),names=np.array(names))
    selections={};rows=[];folds=[]
    for group in CLASSES:
        r=rank(arr,base,specs,group);winner=r['winner'];name=names[winner]
        nearby=[names[i] for i in range(len(names)) if r['qualified'][i] and r['score'][i]<=r['score'][winner]*1.01+1e-12]
        sites=sorted(set(s['site'] for s in specs if s['station_group']==group))
        selections[group]=dict(model=name,configuration=configs[name],development_score=float(r['score'][winner]),
            eligible_candidates=int(r['qualified'].sum()),near_ties_within_one_percent=nearby,development_sites=sites)
        for i,name in enumerate(names):rows.append(dict(station_group=group,model=name,**configs[name],
            **{key:float(v[i]) if key=='score' else bool(v[i]) for key,v in r.items() if key!='winner'}))
        for held in sites:
            if len(sites)<3:
                folds.append(dict(station_group=group,held_site=held,status='insufficient_training_sites',training_sites=len(sites)-1));continue
            rr=rank(arr,base,specs,group,exclude=held);k=rr['winner'];cc=[j for j,s in enumerate(specs) if s['site']==held]
            ratios=[]
            for comp in ['soil','canopy']:
                cells=[j for j in cc if specs[j]['component']==comp]
                if cells:ratios.append(float(arr[k,cells,0].mean()/base[cells,0].mean()))
            folds.append(dict(station_group=group,held_site=held,status='evaluated',training_sites=len(sites)-1,
                model=names[k],held_normalized_score=float(np.mean(ratios))))
    js('selection.json',dict(selected=selections,selection_time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_before_validation=True))
    pd.DataFrame(rows).to_csv(OUT/'candidate_scores.csv',index=False);pd.DataFrame(folds).to_csv(OUT/'leave_one_site_out.csv',index=False)
    vx,vp,vs,va=evaluate_split('validation');vb=va[baseline_index];validation=[]
    for group,a in selections.items():
        k=names.index(a['model']);rr=rank(np.stack([vb,va[k]]),vb,vs,group)
        validation.append(dict(station_group=group,model=a['model'],normalized_score=float(rr['score'][1]),
            gates_passed=bool(rr['qualified'][1]),retrospective_acceptance=bool(rr['qualified'][1] and rr['score'][1]<=1.+1e-12),
            failed_gates=[key for key in ['loss_raw_coverage','loss_filtered_coverage','loss_monthly_coverage','raw_error_degradation'] if rr[key][1]],
            validation_sites=sorted(set(s['site'] for s in vs if s['station_group']==group))))
        for j,s in enumerate(specs):
            if s['station_group']==group:check_cell_independently(values[a['model']][s['component']][ix],b[s['component']][ix],s,arr[k,j])
    js('validation.json',validation)
    existing=pd.read_csv(SOURCE/'station_metrics.csv');existing=existing.merge(lc[['site','station_group']],on='site',how='left')
    output=[];cellrows=[];confs=[]
    for group,a in selections.items():
        for role,model in [('selected',a['model']),('baseline','baseline')]:
            q=existing.loc[existing.station_group.eq(group)&existing.model.eq(model)].copy();q['role']=role;output.append(q)
        v=next(x for x in validation if x['station_group']==group)
        confs.append(dict(station_group=group,model=a['model'],**a['configuration'],development_score=a['development_score'],
            validation_score=v['normalized_score'],validation_passed=v['retrospective_acceptance'],
            development_sites=len(a['development_sites']),near_tie_count=len(a['near_ties_within_one_percent'])))
        for split,ss,ar in [('development',specs,arr),('validation',vs,va)]:
            for j,s in enumerate(ss):
                if s['station_group']!=group:continue
                for role,model in [('selected',a['model']),('baseline','baseline')]:
                    cellrows.append(dict(station_group=group,site=s['site'],component=s['component'],split=split,role=role,model=model,**dict(zip(FIELDS,ar[names.index(model),j]))))
    selected=pd.concat(output,ignore_index=True);selected.to_csv(OUT/'selected_station_metrics.csv',index=False)
    cells=pd.DataFrame(cellrows);cells.to_csv(OUT/'selected_coverage_and_loss.csv',index=False)
    summary=selected.groupby(['station_group','role','model','component','support','split'],as_index=False).agg(
        sites=('site','size'),mean_site_rmse_K=('rmse_K','mean'),n_groups=('n_groups','sum'),n_raw=('n_raw','sum'),
        common_baseline_rmse_K=('baseline_rmse_K','mean'))
    summary.to_csv(OUT/'summary.csv',index=False)
    conf=pd.DataFrame(confs);conf.to_csv(OUT/'selected_configuration_table.csv',index=False)
    js('selected_class_configurations.json',dict(source='Existing 51 complete configurations only',selection=selections,validation=validation,production_changed=False))
    source_months=pd.read_csv(SOURCE/'monthly_hour_pairs.csv.gz');selected_months=[]
    for group,a in selections.items():
        sites=lc.loc[lc.station_group.eq(group),'site'];q=source_months.loc[source_months.model.eq(a['model'])&source_months.site.isin(sites)].copy()
        q['station_group']=group;selected_months.append(q)
    pd.concat(selected_months,ignore_index=True).to_csv(OUT/'selected_monthly_hour_pairs.csv.gz',index=False)
    # Cross-check the selector's conventional filtered metrics against previously saved station metrics.
    checked=0
    for r in cells.itertuples():
        q=selected.loc[selected.role.eq(r.role)&selected.site.eq(r.site)&selected.component.eq(r.component)&selected.split.eq(r.split)&selected.support.eq('own_10K')]
        if np.isfinite(r.own_filtered_rmse):
            assert len(q)==1 and abs(q.iloc[0].rmse_K-r.own_filtered_rmse)<1e-9
            assert q.iloc[0].n_groups==r.n_monthly_filtered;checked+=1
    main=summary.loc[summary.support.eq('own_10K')&summary.split.isin(['all','validation'])]
    text=f'''# 仅使用已有结果筛选森林、农田、草地参数

未重新反演：仅从已完成的51套预测/指标中选择。此前启动的3200组新反演已按用户要求中止，中间结果全部排除。

## 选出的组合

{md(conf)}

窗口数值为正方形边长，first/second分别对应两阶段；delta为W m^-2 sr^-1 um^-1。“最优”限定为已有51候选与下述开发集评价规则。接近最优的组合见selection.json，不将近乎等效的lambda精确识别为唯一值。
validation_passed为后期核验结果；未通过的组合仍作为开发集最优结果报告，不在查看后期数据后另选一组。

## 逐小时月均RMSE

下表使用各配置自身瞬时绝对温差<=10 K后计算逐小时月均，土壤对探针、冠层对气温，都是间接指标。各站RMSE等权平均；样本量差异必须同时看。

{md(main[['station_group','role','component','split','sites','mean_site_rmse_K','n_groups','n_raw']])}

## 筛选及检验

开发2018—2022年；核验2023—2024年，选择文件在计算核验分数前冻结。数据此前已被查看，仅称回顾性核验。
固定输入/参考可用的月小时组，至少3个瞬时配对；不足输出组赋100 K²惩罚。先站点等权，再土壤/冠层相对基准MSE归一化等权。它是选参分数，不是常规RMSE。
每站/组分原始有效率和10 K后有效率下降不得超过2个百分点，月小时有效率下降不得超过5个百分点；未筛选共同样本各类每组分MSE增幅不超过21%（相当于RMSE约10%）。基准永远保留为可选配置。
后期要求同样的约束且归一化分数不高于1，未通过不意味着反演程序错误，只意味着本轮数据不支持替换基准。

### 留一站点结果

每折只在其余开发站点选参，至少保留2个训练站；更少则明确不执行，避免把单站调参包装成类型规律。

{md(pd.DataFrame(folds))}

## 使用限制和交付

类型来自本地站点清单。森林5站、农田3站、草地3站，但开发或核验某些组分可用站点更少；站点标签与像元地类还存在不一致。
这些配置首先是站点分组的条件性最优候选，不是已验证的区域地类参数表；没有修改生产配置。EVO未被擅自归类用于这次欧洲分类型筛选。

- selected_class_configurations.json：三类配置及核验状态。
- candidate_scores.csv：已有51组在三类上的分数和约束判定。
- selected_station_metrics.csv、summary.csv：未筛选、10 K筛选、共同样本等全部既有统计口径。
- selected_monthly_hour_pairs.csv.gz：选中配置的既有逐小时月均配对。
- selected_coverage_and_loss.csv：覆盖率及目标函数分量。
- audit.json：不重新反演的输入溯源与旧指标交叉核验。
'''
    report=OUT/'森林农田草地_已有结果筛选.md';report.write_text(text,encoding='utf8')
    js('audit.json',dict(status='passed',candidates=51,new_inversions=0,interrupted_run_used=False,
        checked_previous_station_metrics=checked,source_hashes_unchanged=all(sha(path)==h for path,h in p['source_sha256'].items()),
        script_sha256=sha(__file__)))
    print(conf.to_string(index=False));print(main.to_string(index=False));print(report)

if __name__=='__main__':main()
