"""Single-day, three-site LS4T kernel experiment and frozen-input replay."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

from functions import fit_pairs, metrics, normalize, normalize_native, radiance_mean, sha256, write_json


def basis(frame, view, model, width):
    names = [f'lsf_{view}']
    if model == 'lsf_rl': names.append(f'rl_{view}_w{width:g}')
    return frame[names].to_numpy(float)


def native_arrays(frame, view, model, width):
    if f't_{view}_0' not in frame:
        # Single-support arrays remain useful for scalar numerical tests.
        return frame[f't_{view}'].to_numpy(float)[:,None], basis(frame,view,model,width)[:,None,:]
    t=frame[[f't_{view}_{j}' for j in range(4)]].to_numpy(float)
    k=[]
    for j in range(4):
        columns=[f'lsf_{view}_{j}']
        if model=='lsf_rl':columns.append(f'rl_{view}_w{width:g}_{j}')
        k.append(frame[columns].to_numpy(float))
    return t,np.stack(k,axis=1)


def fit_site(frame, config, model, width, *, bootstrap=True):
    """Only SLSTR calibration rows are accessed for coefficients/uncertainty."""
    train = frame[frame['split'] == 'train']
    if len(train) < config['minimum_train_pairs'] or train['block_id'].nunique() < config['minimum_train_blocks']:
        raise ValueError('insufficient independent calibration blocks')
    tn,n = native_arrays(train,'n',model,width);to,o = native_arrays(train,'o',model,width)
    ns=tn.shape[1]
    tn,to=tn.ravel(),to.ravel();n,o=n.reshape(-1,n.shape[-1]),o.reshape(-1,o.shape[-1])
    weights = np.repeat(1/train.groupby('block_id')['block_id'].transform('size').to_numpy(float)/ns, ns)
    fit = fit_pairs(tn, to, n, o, weights=weights, max_condition=config['maximum_condition'])
    fit['training_footprints'] = len(train)
    fit['fitting_resolution_m'] = 1000 if ns==4 else None
    fit['training_blocks'] = int(train['block_id'].nunique())
    fit['training_row_ids'] = train['row_id'].astype(str).tolist()
    betas = []
    if bootstrap:
        rng = np.random.default_rng(config['seed'])
        block_ids = np.repeat(train['block_id'].to_numpy(), ns); blocks = np.unique(block_ids)
        for _ in range(config['bootstrap_blocks']):
            sample = rng.choice(blocks, size=len(blocks), replace=True)
            indices = np.concatenate([np.flatnonzero(block_ids == b) for b in sample])
            try:
                b = fit_pairs(tn[indices], to[indices], n[indices], o[indices],
                              weights=weights[indices], max_condition=config['maximum_condition'])
                betas.append(b['coefficients'])
            except ValueError:
                pass
    fit['bootstrap_successes'] = len(betas)
    fit['bootstrap_requested'] = config['bootstrap_blocks'] if bootstrap else 0
    if betas:
        fit['coefficient_ci95'] = np.quantile(betas, [.025, .975], axis=0)
    return fit, np.asarray(betas)


def analyze(frame, config, *, bootstrap=True):
    models, outputs = [], []
    variants = [('lsf', config['rl_width']), ('lsf_rl', config['rl_width'])]
    variants += [('lsf_rl', w) for w in config['width_sensitivity']]
    for site in config['sites']:
        data = frame[frame['site'] == site].copy()
        for model, width in variants:
            label = model if model == 'lsf' or width == config['rl_width'] else f'lsf_rl_w{width:g}'
            record = dict(site=site, model=label, rl_width=width if model == 'lsf_rl' else None)
            out = data.copy(); out['model'] = label
            try:
                fit, betas = fit_site(data, config, model, width, bootstrap=bootstrap)
                record.update(fit); record['status'] = 'fitted'
                beta = fit['coefficients']
                for view in ('n', 'o', 'a'):
                    k = basis(data, view, model, width)
                    if view=='a':
                        out[f'correction_{view}'] = -k@beta
                        out[f'norm_{view}'] = normalize(data[f't_{view}'], k, beta)
                        out[f'max_native_correction_{view}'] = abs(k@beta)
                        boot_values=k@betas.T if len(betas)>1 else None
                    else:
                        t_native,k_native=native_arrays(data,view,model,width)
                        norm,delta,maximum=normalize_native(t_native,k_native,beta)
                        out[f'norm_{view}']=norm;out[f'correction_{view}']=delta
                        out[f'max_native_correction_{view}']=maximum
                        boot_values=radiance_mean(t_native[...,None]-np.einsum('ijp,bp->ijb',k_native,betas),axis=1) if len(betas)>1 else None
                    out[f'correction_sd_{view}'] = np.std(boot_values, axis=1, ddof=1) if boot_values is not None else np.nan
                    # Geometric leverage is a diagnostic, not a temperature-residual filter.
                    out[f'leverage_{view}'] = np.einsum('ij,jk,ik->i', k, fit['gram_inverse'], k)
                slstr = np.isfinite(out['norm_n']+out['norm_o'])
                slstr &= (out['max_native_correction_n'] <= config['maximum_correction_k']) & (out['max_native_correction_o'] <= config['maximum_correction_k'])
                slstr &= out['norm_n'].between(220, 365) & out['norm_o'].between(220, 365)
                ahi = slstr & out['ahi_qa'] & np.isfinite(out['norm_a'])
                ahi &= abs(out['correction_a']) <= config['maximum_correction_k']
                ahi &= out['norm_a'].between(220, 365)
                out['slstr_normalization_accepted'] = slstr
                out['ahi_normalization_accepted'] = ahi
                for view in ('n','o','a'):
                    out[f'usable_norm_{view}']=out[f'norm_{view}'].where(ahi if view=='a' else slstr)
                record['maximum_correction_k'] = float(np.nanmax(abs(out[['correction_n','correction_o','correction_a']].to_numpy())))
                record['station_normalization_status']='accepted' if bool(out.loc[out.station_centre,'ahi_normalization_accepted'].iloc[0]) else 'rejected_correction_or_output_range'
            except ValueError as exc:
                record.update(status='rejected', reason=str(exc))
                for view in ('n', 'o', 'a'):
                    for field in ('correction','norm','correction_sd','leverage','usable_norm','max_native_correction'):
                        out[f'{field}_{view}'] = np.nan
                out['slstr_normalization_accepted'] = False
                out['ahi_normalization_accepted'] = False
            models.append(record); outputs.append(out)
    predictions = pd.concat(outputs, ignore_index=True)
    rows = []
    for site in config['sites']:
        raw = frame[(frame['site'] == site) & (frame['split'] == 'test')]
        rows.append(dict(site=site, model='uncorrected', comparison='SLSTR oblique minus nadir', cohort='all_eligible_holdout', **metrics(raw['t_o']-raw['t_n'])))
        qa = raw['ahi_qa']
        rows.append(dict(site=site, model='uncorrected', comparison='AHI minus SLSTR nadir', cohort='all_eligible_holdout', **metrics((raw['t_a']-raw['t_n'])[qa])))
        for label in predictions['model'].unique():
            d = predictions[(predictions['site'] == site) & (predictions['model'] == label) & (predictions['split'] == 'test')]
            for comparison, left, right, maskcol in [('SLSTR oblique minus nadir','o','n','slstr_normalization_accepted'),
                                                     ('AHI minus SLSTR nadir','a','n','ahi_normalization_accepted')]:
                # An unfiltered paired comparison remains visible even when corrections are rejected.
                input_mask = np.ones(len(d), dtype=bool) if left == 'o' else d['ahi_qa'].to_numpy(bool)
                accepted = d[maskcol].to_numpy(bool) & input_mask
                for cohort, mask in [('all_eligible_holdout', input_mask), ('accepted_common_holdout', accepted)]:
                    for method, prefix in [('uncorrected', 't'), (label, 'norm')]:
                        diff = (d[f'{prefix}_{left}']-d[f'{prefix}_{right}']).to_numpy()[mask]
                        rows.append(dict(site=site, model=method, paired_with=label, comparison=comparison,
                                         cohort=cohort, eligible_n=int(input_mask.sum()), accepted_n=int(accepted.sum()),
                                         coverage_status='complete' if np.isfinite(diff).all() else 'partial_or_failed', **metrics(diff)))
    return models, predictions, pd.DataFrame(rows)


def verify_leakage(frame, config, models):
    changed = frame.copy()
    changed['t_a'] = changed['t_a'].fillna(0)+1000
    holdout = changed['split'] != 'train'
    changed.loc[holdout, 't_n'] += 2000; changed.loc[holdout, 't_o'] -= 2000
    for j in range(4):
        if f't_n_{j}' in changed:
            changed.loc[holdout,f't_n_{j}'] += 2000; changed.loc[holdout,f't_o_{j}'] -= 2000
    # AHI QA and temperature must not influence coefficient solving either.
    changed['ahi_qa'] = ~changed['ahi_qa']
    largest = 0.
    for original in models:
        if original['status'] != 'fitted': continue
        model = 'lsf' if original['model'] == 'lsf' else 'lsf_rl'
        fit, _ = fit_site(changed[changed['site'] == original['site']], config, model,
                          original['rl_width'] or config['rl_width'], bootstrap=False)
        largest = max(largest, float(np.max(abs(fit['coefficients']-original['coefficients']))))
    if largest != 0: raise AssertionError('Validation observations leaked into coefficient fitting')
    for site in config['sites']:
        d = frame[frame['site'] == site]
        assert not set(d.loc[d['split']=='train','block_id']) & set(d.loc[d['split']=='test','block_id'])
        assert (d.loc[d['station_centre'],'split'] == 'test').all()
    return dict(ahi_and_holdout_perturbation_max_coefficient_change=largest,
                spatial_blocks_disjoint=True, station_centres_held_out=True,
                no_ground_data_used=True)


def compare_models(current, previous):
    a={(m['site'],m['model']):m for m in current};b={(m['site'],m['model']):m for m in previous}
    if len(a)!=len(current) or len(b)!=len(previous) or a.keys()!=b.keys():
        raise AssertionError('Replay model keys/count changed')
    largest=0.
    for key in a:
        if a[key]['status']!=b[key]['status']:
            raise AssertionError(f'Replay model status changed: {key}')
        if a[key]['status']=='fitted':
            delta=np.asarray(a[key]['coefficients'])-np.asarray(b[key]['coefficients'])
            largest=max(largest,float(np.max(abs(delta))))
    if largest>1e-8:raise AssertionError('Replay coefficients changed')
    return largest


def figures(predictions, output, config):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.5), constrained_layout=True)
    for col, site in enumerate(config['sites']):
        d = predictions[(predictions['site']==site)&(predictions['model']=='lsf_rl')&(predictions['split']=='test')]
        for row, (view, title) in enumerate([('o','SLSTR oblique - nadir'),('a','AHI - SLSTR nadir')]):
            a = axes[row,col]
            if view == 'a': dplot = d[d['ahi_qa']]
            else: dplot = d
            raw = (dplot[f't_{view}']-dplot['t_n']).to_numpy()
            corrected = (dplot[f'norm_{view}']-dplot['norm_n']).to_numpy()
            ok = np.isfinite(raw+corrected)
            a.scatter(raw[ok],corrected[ok],s=14,alpha=.7,color='#187e82')
            if ok.any():
                lim=max(1.,float(np.max(abs(np.r_[raw[ok],corrected[ok]]))))*1.05
                a.plot([-lim,lim],[-lim,lim],color='#aaaaaa',linestyle='--',linewidth=.8)
                a.set_xlim(-lim,lim); a.set_ylim(-lim,lim)
                a.text(.03,.97,f'n={ok.sum()}\nRMSE {metrics(raw[ok])["rmse_k"]:.2f} -> {metrics(corrected[ok])["rmse_k"]:.2f} K',transform=a.transAxes,va='top',fontsize=9)
            a.axhline(0,color='#555555',linewidth=.6); a.axvline(0,color='#555555',linewidth=.6)
            a.set_title(f'{site} | {title}'); a.set_xlabel('Before (K)'); a.set_ylabel('After LSF-RL (K)')
    fig.suptitle('Spatial holdout | all input-QA-eligible pairs | no residual clipping',fontsize=13)
    fig.savefig(output/'holdout_comparison.png',dpi=160); plt.close(fig)
    fig, axes = plt.subplots(1,3,figsize=(13,4),constrained_layout=True)
    for ax,site in zip(axes,config['sites']):
        d=predictions[(predictions['site']==site)&(predictions['model']=='lsf_rl')]
        for label,color in [('train','#458b69'),('test','#e07b39'),('buffer','#bbbbbb')]:
            q=d[d['split']==label];ax.scatter(q['lon'],q['lat'],s=12,c=color,label=label,marker='s')
        q=d[d['station_centre']];ax.scatter(q['lon'],q['lat'],s=85,c='black',marker='*',label='station pixel')
        ax.set_title(site); ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude');ax.legend(fontsize=7)
    fig.savefig(output/'spatial_split.png',dpi=160);plt.close(fig)


def report(output, config, selection, models, metric_table, station):
    lines=['# AHI / SLSTR 三站点单日核驱动角度归一化', '',
           f"日期：{selection['date']}；平台：{selection['platform']}；目标：保持太阳几何的天底方向。", '',
           '主方法：固定热点宽度 k=1 的 LSF–RL；LSF 单核为对照；k=0.5/2 仅作敏感性分析，不按 AHI 误差择优。',
           '在1 km原生配对层拟合温差并校正，然后将四个校正后的子像元辐亮度聚合到2 km。各站点独立系数。相同10 km块等权；中心块留出，周围一圈块作为缓冲区。', '',
           '## 主方法结果（全部输入质量合格的空间留出样本）', '',
           '|站点|比较|样本数|原始 RMSE/K|LSF–RL RMSE/K|原始 Bias/K|LSF–RL Bias/K|',
           '|---|---|---:|---:|---:|---:|---:|']
    def num(x): return 'NA' if pd.isna(x) else f'{x:.3f}'
    for site in config['sites']:
        for comparison in ['SLSTR oblique minus nadir','AHI minus SLSTR nadir']:
            q=metric_table[(metric_table.site==site)&(metric_table.paired_with=='lsf_rl')&(metric_table.comparison==comparison)&(metric_table.cohort=='all_eligible_holdout')]
            raw=q[q.model=='uncorrected'].iloc[0]; norm=q[q.model=='lsf_rl'].iloc[0]
            comparable = raw['n']==norm['n']
            lines.append(f"|{config['site_names'][site]}|{comparison}|{int(raw['n'])}/{int(norm['n'])}|{num(raw.rmse_k)}|{num(norm.rmse_k) if comparable else 'NA: incomplete'}|{num(raw.bias_k)}|{num(norm.bias_k) if comparable else 'NA: incomplete'}|")
    lines += ['', '样本数列为原始/模型有效数量；不同数量时不进行RMSE优劣比较。上表包括被幅度门槛拒绝的原始模型提议，不能将其当作通过质量控制的产品。', '',
              '## 站点中心质量判定', '', '|站点|主方法判定|SLSTR最大子像元修正/K|AHI修正/K|', '|---|---|---:|---:|']
    for site in config['sites']:
        d=station[(station.site==site)&(station.model=='lsf_rl')].iloc[0]
        status='通过预设幅度/范围门槛' if bool(d.ahi_normalization_accepted) else '拒绝：幅度超限、输出越界或不可辨识'
        lines.append(f"|{config['site_names'][site]}|{status}|{num(max(d.max_native_correction_n,d.max_native_correction_o))}|{num(d.correction_a)}|")
    lines += ['', '拟合成功不等于归一化可用；usable_norm_*字段已把拒绝结果设为缺测，norm_*保留诊断提议。单核LSF和热点宽度敏感性结果完整保留在metrics.csv，不按AHI验证误差事后选择最佳方法。']
    lines += ['', '## 质量及解释', '',
              '- 数据为既有投影归档：SLSTR 1 km、AHI 2 km；SLSTR 四像元在 10.85 μm 等效辐亮度空间聚合。不是原生仪器足迹卷积或完整光谱响应积分。',
              '- SLSTR cloud=0 和有效 LST 联合筛选；原始 L1 云位定义和投影链未重新审核。AHI 使用有效 LST 及 tcc/1000≤0.20 的云量代理，不能等同原生云检测。',
              '- 角度按归档值/100、时刻按 HHMM UTC 解码；双视角共用归档时间字段。AHI 方向根据名义 140.7°E 同步轨道推算。',
              '- 站点半径 30 km、中心 NDVI ±0.10 是地表相似性近似，未证明区域温度各向异性完全相同；块内像元与邻近站点也不完全独立。',
              '- AHI 的谱间差异、上游 LST 偏差及最多 5 分钟的真实温度变化未校正。所有 AHI 和 SLSTR 验证块均不参与拟合。',
              '- 主表保留所有输入质量合格样本，不按校正残差删点。metrics.csv 同时给出修正幅度≤10 K且结果在220–365 K的接受样本及相同样本上的原始指标。',
              '- bootstrap 以训练块为单位，表示该区域抽样敏感性，不包含上游测量、云、光谱或模型结构的全部不确定度。',
              '- 没有使用地面温度；只能评价跨视角/跨传感器一致性，不能证明地面绝对精度。单站中心仅一个像元配对，不单独报告有统计意义的 RMSE。', '',
              '## 交付', '',
              '`station_results.csv` 为三个站点中心原始/归一化温度与修正量；`models.json` 为参数、条件数和块 bootstrap；`paired_observations.csv` 是可重放输入；`source_manifest.json` 保存原始文件哈希；`verification.json` 记录防泄漏验证。', '',
              '![空间留出比较](holdout_comparison.png)', '', '![空间划分](spatial_split.png)', '']
    (output/'report.md').write_text('\n'.join(lines),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=Path(__file__).with_name('config.json'))
    parser.add_argument('--replay',type=Path,help='Existing result directory; no raw imagery needed')
    parser.add_argument('--selection-from',type=Path,help='Re-extract the previously quality-selected date, preserving its audit')
    args=parser.parse_args()
    if args.replay and args.selection_from:raise ValueError('Choose replay or selection-from, not both')
    startup_hashes={p.name:sha256(p) for p in Path(__file__).parent.iterdir() if p.is_file() and p.suffix in ('.py','.json','.md','.txt','.ps1')}
    if args.replay:
        receipt=json.loads((args.replay/'checksums.json').read_text(encoding='utf-8'))
        for name in ['config.json','selection.json','source_manifest.json','models.json','predictions.csv','paired_observations.csv']:
            if receipt.get(name)!=sha256(args.replay/name):raise AssertionError(f'Frozen input checksum mismatch: {name}')
    config=json.loads((args.replay/'config.json' if args.replay else args.config).read_text(encoding='utf-8'))
    parent=Path(config['output_parent']).resolve(); root=Path(config['data_root']).resolve()
    code_dir=Path(__file__).resolve().parent
    repo=next((p for p in code_dir.parents if (p/'pyproject.toml').is_file() and (p/'base').is_dir()), code_dir)
    if parent==root or parent.is_relative_to(root) or root.is_relative_to(parent) or parent.is_relative_to(repo):
        raise ValueError('Input, repository and output must be separate')
    parent.mkdir(parents=True,exist_ok=True)
    output=parent/('replay_' if args.replay else 'run_')
    output=output.with_name(output.name+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    output.mkdir(exist_ok=False)
    write_json(output/'config.json',config)
    try:
        if args.replay:
            frame=pd.read_csv(args.replay/'paired_observations.csv')
            if 't_n_0' not in frame:raise ValueError('This replay requires native subpixel inputs; re-extract the selected date')
            selection=json.loads((args.replay/'selection.json').read_text(encoding='utf-8'))
            source=json.loads((args.replay/'source_manifest.json').read_text(encoding='utf-8'))
        else:
            from prepare import select_day, load_sites, extract_date
            if args.selection_from:
                from datetime import date
                previous_selection=json.loads((args.selection_from/'selection.json').read_text(encoding='utf-8'))
                previous_config=json.loads((args.selection_from/'config.json').read_text(encoding='utf-8'))
                if config!=previous_config:raise ValueError('A selected date can only be reused with the identical predeclared config')
                selection=previous_selection
                frame,diagnostics,reader=extract_date(config,date.fromisoformat(selection['date']),selection['platform'])
                if not all(d['status']=='eligible' for d in diagnostics):raise ValueError('Selected date no longer passes input QA/support')
                selection=dict(selection,sites=diagnostics,reextraction_from=str(args.selection_from),sampling='native 1 km fit/correct before 2 km aggregation')
                write_json(output/'candidate_audit.json',selection['candidates'])
            else:
                frame,selection,reader=select_day(config, output/'candidate_audit.json')
            frame['row_id']=[f'{s}:{p}:{d}:{r}:{c}' for s,p,d,r,c in zip(frame.site,frame.platform,frame.date,frame.row,frame.col)]
            source=dict(files=reader.finalize(),station_file=dict(path=config['station_file'],sha256=sha256(config['station_file'])),sites=load_sites(config))
        write_json(output/'selection.json',selection);write_json(output/'source_manifest.json',source)
        frame.to_csv(output/'paired_observations.csv',index=False)
        models,predictions,metric_table=analyze(frame,config)
        write_json(output/'models.json',models)
        predictions.to_csv(output/'predictions.csv',index=False);metric_table.to_csv(output/'metrics.csv',index=False)
        station=predictions[predictions.station_centre].copy();station.to_csv(output/'station_results.csv',index=False)
        verification=verify_leakage(frame,config,models)
        verification.update(date=selection['date'],sites=config['sites'],observations=len(frame),
                            main_models={m['site']:m['status'] for m in models if m['model']=='lsf_rl'},
                            station_normalization_status={m['site']:m.get('station_normalization_status','fit_rejected') for m in models if m['model']=='lsf_rl'},
                            input_sha256=sha256(output/'paired_observations.csv'))
        if args.replay:
            previous=json.loads((args.replay/'models.json').read_text(encoding='utf-8'))
            max_change=compare_models(models,previous)
            verification['replay_max_coefficient_change']=max_change
            old=pd.read_csv(args.replay/'predictions.csv')
            if old[['row_id','model']].to_dict('list')!=predictions[['row_id','model']].to_dict('list'):raise AssertionError('Replay prediction rows changed')
            for column in ['norm_n','norm_o','norm_a','usable_norm_n','usable_norm_o','usable_norm_a']:
                np.testing.assert_allclose(predictions[column],old[column],rtol=0,atol=1e-7,equal_nan=True)
            verification['replay_predictions_equal_within_1e-7_k']=True
        figures(predictions,output,config);report(output,config,selection,models,metric_table,station)
        snapshot=output/'code';snapshot.mkdir()
        for file in Path(__file__).parent.iterdir():
            if file.is_file() and file.suffix in ('.py','.json','.md','.txt','.ps1'):
                if startup_hashes.get(file.name)!=sha256(file):raise RuntimeError(f'Code changed during execution: {file.name}')
                shutil.copy2(file,snapshot/file.name)
        verification['code_hashes']={p.name:sha256(p) for p in snapshot.iterdir()}
        write_json(output/'verification.json',verification)
        write_json(output/'checksums.json',{p.name:sha256(p) for p in output.iterdir() if p.is_file()})
        print(json.dumps(dict(output=str(output),date=selection['date'],main_models=verification['main_models']),ensure_ascii=False),flush=True)
    except Exception as exc:
        write_json(output/'failure.json',dict(error=type(exc).__name__,message=str(exc)))
        raise


if __name__=='__main__':
    main()
