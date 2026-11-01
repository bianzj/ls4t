"""Fixed-date 3x3 joint AHI + SLSTR experiment, with full-triplet LOO checks."""
from __future__ import annotations
import argparse
from datetime import date,datetime
import json
from pathlib import Path
import shutil
import numpy as np
import pandas as pd

from functions import metrics,sha256,write_json
from joint import data_from_frame,fit_joint,subset,correction_limits


def analyze(frame,config):
    models=[];predictions=[];verification=[]
    for site in config['sites']:
        f=frame[(frame.site==site)&frame.ahi_qa].sort_values(['row','col']).reset_index(drop=True)
        if len(f)<config['minimum_complete_triplets']:
            models.append(dict(site=site,status='rejected',reason='insufficient complete 3x3 triplets'))
            continue
        for model in ['lsf','lsf_rl']:
            data=data_from_frame(f,model,config['rl_width'])
            for fold in [-1]+list(range(len(f))):
                role='all_window_fit' if fold<0 else 'leave_one_footprint_out'
                train=np.ones(len(f),bool) if fold<0 else np.arange(len(f))!=fold
                query=np.ones(len(f),bool) if fold<0 else ~train
                key=f'{site}:{model}:{fold}'
                record=dict(id=key,site=site,model=model,role=role,heldout_row_id=None if fold<0 else f.loc[fold,'row_id'],
                            training_row_ids=f.loc[train,'row_id'].tolist())
                out=f.loc[query].copy();out['model']=model;out['role']=role;out['fit_id']=key
                try:
                    fitted=fit_joint(subset(data,train),config['maximum_condition'])
                    record.update(fitted,status='fitted')
                    norms,deltas,maximum,accepted=correction_limits(subset(data,query),fitted['coefficients'],config['maximum_correction_k'])
                    for j,view in enumerate(('n','o','a')):
                        out['norm_'+view]=norms[:,j];out['correction_'+view]=deltas[:,j]
                        out['max_native_correction_'+view]=maximum[:,j]
                        out['usable_norm_'+view]=np.where(accepted,norms[:,j],np.nan)
                    out['accepted']=accepted
                    if fold>=0:
                        perturbed={k:v.copy() for k,v in data.items()}
                        for field in ('tn','to','ta'):perturbed[field][fold]+=15
                        again=fit_joint(subset(perturbed,train),config['maximum_condition'])
                        delta=float(np.max(abs(again['coefficients']-fitted['coefficients'])))
                        if delta!=0:raise AssertionError('Heldout triplet leaked into fitting')
                        verification.append(dict(fit_id=key,heldout_value_perturbation_max_coefficient_change=delta))
                except ValueError as exc:
                    record.update(status='rejected',reason=str(exc));out['accepted']=False
                    for view in ('n','o','a'):
                        for prefix in ('norm','correction','max_native_correction','usable_norm'):out[prefix+'_'+view]=np.nan
                models.append(record);predictions.append(out)
    if not predictions:raise ValueError('No site had sufficient complete matched triplets')
    pred=pd.concat(predictions,ignore_index=True)
    summary=[]
    for (site,model,role),d in pred.groupby(['site','model','role'],sort=False):
        for label,left,right in [('AHI minus SLSTR-nadir','a','n'),('SLSTR-oblique minus nadir','o','n')]:
            for cohort,mask in [('all_input_valid',np.ones(len(d),bool)),('accepted_common',d.accepted.to_numpy(bool))]:
                for method,prefix in [('raw','t'),('normalized','norm')]:
                    error=(d[prefix+'_'+left]-d[prefix+'_'+right]).to_numpy()[mask]
                    summary.append(dict(site=site,model=model,role=role,comparison=label,cohort=cohort,method=method,
                                        requested_n=int(mask.sum()),coverage_complete=bool(np.isfinite(error).all()),**metrics(error)))
    return models,pred,pd.DataFrame(summary),verification


def compare_replay(output,previous,models,pred):
    old=json.loads((previous/'models.json').read_text(encoding='utf-8'))
    a={m.get('id',m['site']):m for m in models};b={m.get('id',m['site']):m for m in old}
    if a.keys()!=b.keys() or len(a)!=len(models) or len(b)!=len(old):raise AssertionError('Replay fit identities changed')
    maximum=0.
    for key in a:
        if a[key]['status']!=b[key]['status']:raise AssertionError('Replay model status changed')
        if a[key]['status']=='fitted':
            maximum=max(maximum,float(np.max(abs(np.asarray(a[key]['coefficients'])-b[key]['coefficients']))))
    if maximum>1e-7:raise AssertionError('Replay coefficients changed')
    previous_pred=pd.read_csv(previous/'predictions.csv',float_precision='round_trip')
    ids=['row_id','model','role','fit_id']
    if pred[ids].to_dict('list')!=previous_pred[ids].to_dict('list'):raise AssertionError('Replay output identities changed')
    for column in ['norm_n','norm_o','norm_a','usable_norm_n','usable_norm_o','usable_norm_a']:
        np.testing.assert_allclose(pred[column],previous_pred[column],atol=1e-7,rtol=0,equal_nan=True)
    if pred.accepted.to_list()!=previous_pred.accepted.to_list():raise AssertionError('Replay acceptance changed')
    return maximum


def plot_windows(pred,sites,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    selected=pred[(pred.model=='lsf_rl')&(pred.role=='leave_one_footprint_out')]
    values=np.r_[selected.t_a-selected.t_n,selected.norm_a-selected.norm_n]
    vmax=max(1.,float(np.nanmax(abs(values))))
    fig,axes=plt.subplots(3,2,figsize=(8,10),layout='constrained')
    for i,site in enumerate(sites):
        d=selected[selected.site==site];centre=d[d.station_centre]
        if centre.empty:continue
        r,c=int(centre.row.iloc[0]),int(centre.col.iloc[0])
        for j,prefix in enumerate(['t','norm']):
            matrix=np.full((3,3),np.nan)
            for _,row in d.iterrows():matrix[int(row.row)-r+1,int(row.col)-c+1]=row[prefix+'_a']-row[prefix+'_n']
            im=axes[i,j].imshow(matrix,cmap='RdBu_r',vmin=-vmax,vmax=vmax)
            for rr in range(3):
                for cc in range(3):
                    label=f'{matrix[rr,cc]:.2f}' if np.isfinite(matrix[rr,cc]) else 'NA'
                    axes[i,j].text(cc,rr,label,ha='center',va='center',fontsize=12,
                                   color='white' if abs(matrix[rr,cc])>.6*vmax else 'black')
            if j==1:
                for _,point in d[~d.accepted].iterrows():
                    axes[i,j].plot(int(point.col)-c+1,int(point.row)-r+1,marker='x',markersize=32,
                                   markeredgewidth=1.4,color='#555555',alpha=.8)
            axes[i,j].add_patch(Rectangle((.5,.5),1,1,fill=False,edgecolor='black',linewidth=2.5))
            axes[i,j].set_title(f'{site} | '+('Original' if j==0 else 'Joint LSF-RL / footprint LOO\nx = rejected correction'))
            axes[i,j].set_xticks([0,1,2],[-1,0,1]);axes[i,j].set_yticks([0,1,2],[-1,0,1])
            axes[i,j].set_xlabel('AHI-grid column offset (2 km)');axes[i,j].set_ylabel('Row offset (2 km)')
    fig.colorbar(im,ax=axes,label='AHI minus SLSTR-nadir (K)',shrink=.6)
    fig.suptitle(str(selected.date.iloc[0])+' | 3 x 3 matched footprints | centre outlined')
    fig.savefig(out/'window_differences.png',dpi=160);plt.close(fig)


def report(out,config,diag,pred,summary,models):
    main=pred[(pred.model=='lsf_rl')&(pred.role=='leave_one_footprint_out')]
    lines=['# 三站点 3×3 联合核驱动角度归一化','',
           f"日期 {config['date']}；{config['platform']} 双视角 + AHI。参考方向为天底，保留各观测太阳几何。",'',
           '**本地归档格网：SLSTR 1 km，AHI 2 km。3×3按AHI格网定义，约6×6 km；每方向对应6×6个SLSTR原生格网。** 每个2 km足迹包含4个SLSTR子像元，形成两个SLSTR方向温度加一个AHI温度；9个足迹最多27个粗尺度观测，不把AHI重复计数。','',
           '整窗共用LSF与RL两个角度系数（k=1固定），逐足迹背景温度由差分消去。在SLSTR原生子像元上施加角度修正后，再做10.85 μm等效辐亮度聚合；优化直接计算这一非线性聚合。既有LST不重复大气校正。','',
           '**AHI参与标定，所以不能再将AHI当作独立传感器验证。** 以下按整足迹留一法：每轮留出一个像元的全部3个方向，用其余最多8组拟合。邻近像元存在空间相关，9折不是9次独立实验。','',
           '## 配准与样本','', '|站点|原定窗口|SLSTR有效足迹|三方向完整足迹|AHI时间差/分钟|','|---|---:|---:|---:|---:|']
    for d in diag:
        f=main[main.site==d['site']]
        gap=float(f.ahi_time_difference_minutes.max()) if len(f) else None
        lines.append(f"|{config['site_names'][d['site']]}|9|{d.get('slstr_qa_footprints',0)}|{d.get('complete_triplets',0)}|{gap}|")
    lines += ['', '## 留出像元的差异（不是拟合残差）','', '|站点|配对数|AHI–SLSTR原始RMSE/K|联合核校正后RMSE/K|通过幅度门槛的配对数|','|---|---:|---:|---:|---:|']
    for site in config['sites']:
        d=main[main.site==site]
        raw=metrics(d.t_a-d.t_n);norm=metrics(d.norm_a-d.norm_n)
        fmt=lambda v:'NA' if v is None else f'{v:.3f}'
        valid=raw['n']==norm['n']
        lines.append(f"|{config['site_names'][site]}|{raw['n']}/{norm['n']}|{fmt(raw['rmse_k'])}|{fmt(norm['rmse_k']) if valid else 'NA: incomplete'}|{int(d.accepted.sum())}|")
    lines += ['', '## 站点中心：只用周围像元标定','', '|站点|SLSTR-nadir原始/K|SLSTR-oblique原始/K|AHI原始/K|SLSTR-nadir归一化/K|SLSTR-oblique归一化/K|AHI归一化/K|质量通过|','|---|---:|---:|---:|---:|---:|---:|---|']
    for site in config['sites']:
        d=main[(main.site==site)&main.station_centre]
        if d.empty:continue
        r=d.iloc[0];cols=['t_n','t_o','t_a','norm_n','norm_o','norm_a']
        text='|'.join(f'{r[k]:.3f}' if np.isfinite(r[k]) else 'NA' for k in cols)
        lines.append(f"|{config['site_names'][site]}|{text}|{bool(r.accepted)}|")
    rejected=[config['site_names'][s] for s in config['sites'] if len(main[main.site==s]) and not main.loc[main.site==s,'accepted'].any()]
    lines += ['', '**注意：质量未通过的norm值仅用于诊断，不能作为有效归一化温度。**']
    if rejected:lines += ['本次全部留一结果未通过门槛的站点：'+ '、'.join(rejected)+'；其诊断RMSE下降也不能算有效产品改善。']
    lines += ['', '## 边界','',
              '- '+config.get('date_selection_note', f"日期按配置固定为{config['date']}，未根据本轮拟合效果换日。"),
              '- 3×3不按NDVI裁掉邻居，云/温度/时间/格网筛选保留。',
              '- 输入为已投影归档，格网对齐不等于原生传感器PSF完全相同。SLSTR cloud=0和AHI tcc/1000≤0.2都是沿用的归档筛选；AHI后者为云量代理，不是原生云检测。AHI方向用140.7°E名义轨道推算。',
              '- 温度/原生子像元修正≤10 K、归一化温度220–365 K、角度矩阵条件数≤100。norm_*保留诊断值，usable_norm_*只保留通过门槛的结果。没有按观测残差删点。',
              '- 三个方向使用相同1 K误差假设决定拟合权重；这是情景权重，不是传感器独立误差标定。',
              '- AHI进入拟合后，传感器光谱/反演偏差可能被角度系数吸收；拟合或留一一致性改善不等于已分离纯角度效应，亦不等于地面精度提高。',
              '- models.json区分all_window_fit与leave_one_footprint_out。前者每站一组全窗口系数；后者逐折独立拟合，仅用于验证。station_results.csv保留中心留出结果。', '',
              '![3×3温差图](window_differences.png)','']
    (out/'report.md').write_text('\n'.join(lines),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=Path(__file__).with_name('config.json'))
    parser.add_argument('--replay',type=Path)
    parser.add_argument('--output-parent',type=Path,help='External result directory; overrides the frozen machine path')
    args=parser.parse_args()
    if args.replay:
        checks=json.loads((args.replay/'checksums.json').read_text(encoding='utf-8'))
        for name in ['config.json','observations.csv','source_manifest.json','diagnostics.json','models.json','predictions.csv']:
            if checks.get(name)!=sha256(args.replay/name):raise ValueError('Replay checksum mismatch: '+name)
    config=json.loads((args.replay/'config.json' if args.replay else args.config).read_text(encoding='utf-8'))
    if args.output_parent:
        config['output_parent']=str(args.output_parent.resolve())
    if config['window_size']!=3:raise ValueError('This experiment requires a 3x3 AHI-grid window')
    parent=Path(config['output_parent']).resolve();data_root=Path(config['data_root']).resolve();code=Path(__file__).resolve().parent
    repo=next((p for p in code.parents if (p/'pyproject.toml').is_file() and (p/'base').is_dir()),code)
    if parent.is_relative_to(repo) or parent.is_relative_to(data_root) or data_root.is_relative_to(parent):raise ValueError('Code, input and output must be separate')
    hashes={p.name:sha256(p) for p in code.iterdir() if p.is_file() and p.suffix in ('.py','.json','.md','.txt','.ps1')}
    out=parent/(('replay_' if args.replay else 'run_')+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(parents=True,exist_ok=False);write_json(out/'config.json',config)
    try:
        if args.replay:
            frame=pd.read_csv(args.replay/'observations.csv',float_precision='round_trip');diag=json.loads((args.replay/'diagnostics.json').read_text(encoding='utf-8'));source=json.loads((args.replay/'source_manifest.json').read_text(encoding='utf-8'))
        else:
            from prepare import extract_date,load_sites
            frame,diag,reader=extract_date(config,date.fromisoformat(config['date']),config['platform'])
            if frame.empty:raise ValueError('No valid station windows')
            frame['row_id']=[f'{s}:{r}:{c}' for s,r,c in zip(frame.site,frame.row,frame.col)]
            source=dict(files=reader.finalize(),stations=load_sites(config),station_file=dict(path=config['station_file'],sha256=sha256(config['station_file'])))
        write_json(out/'source_manifest.json',source);write_json(out/'diagnostics.json',diag);frame.to_csv(out/'observations.csv',index=False)
        models,pred,summary,leakage=analyze(frame,config)
        write_json(out/'models.json',models);pred.to_csv(out/'predictions.csv',index=False);summary.to_csv(out/'metrics.csv',index=False)
        pred[(pred.role=='leave_one_footprint_out')&pred.station_centre].to_csv(out/'station_results.csv',index=False)
        checks=dict(window_shape=[3,3],ahi_used_for_calibration=True,validation='whole-footprint leave-one-out; spatially dependent',
                    heldout_perturbation=leakage,source_grid_m=dict(SLSTR=1000,AHI=2000),native_cells_per_ahi_footprint=4,
                    matched_triplets_by_site={d['site']:d.get('complete_triplets',0) for d in diag})
        if args.replay:checks['replay_max_coefficient_change']=compare_replay(out,args.replay,models,pred)
        plot_windows(pred,config['sites'],out);report(out,config,diag,pred,summary,models)
        snapshot=out/'code';snapshot.mkdir()
        for name,value in hashes.items():
            if sha256(code/name)!=value:raise RuntimeError('Code changed during run: '+name)
            shutil.copy2(code/name,snapshot/name)
        checks['code_hashes']=hashes;write_json(out/'verification.json',checks)
        write_json(out/'checksums.json',{p.name:sha256(p) for p in out.iterdir() if p.is_file()})
        print(json.dumps(dict(output=str(out),triplets=checks['matched_triplets_by_site']),ensure_ascii=False),flush=True)
    except Exception as exc:
        write_json(out/'failure.json',dict(type=type(exc).__name__,message=str(exc)));raise


if __name__=='__main__':main()
