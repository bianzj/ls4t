"""Small authorized station-only experiment, 12 sites and complete 10-16 UTC."""
from pathlib import Path
import itertools,json,hashlib
import numpy as np
import pandas as pd
import select_joint_station_parameters as joint
from compare_monthly_hour_factors import window_prepare
from search_evo_parameters import retrieve
from parameter_argument_monthly_hour import scalar_window_check

ROOT=Path('C:/work/ls4t-msg/cases/official/results/production_assessment')
J=ROOT/'joint_parameter_selection'
PARENT=J/'threshold_sensitivity/europe_10_16_joint/subset_12_sites'
OUT=PARENT/'hotspot_window_experiment'
OLD=ROOT/'msg_5x5/station_direct_2018_2024'
EXCLUDED={'IT-TrF','FR-EM2'}
BASE='h0.25_w5_5'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')

def main():
    OUT.mkdir(exist_ok=True)
    if (OUT/'complete.json').exists():raise RuntimeError('Completed experiment exists; inspect it instead of overwriting.')
    paused=Path('E:/PRODUCTS/LSCT/MSG_5X5_PHYSICAL_V1/status.json');paused_hash=sha(paused)
    assert json.loads(paused.read_text(encoding='utf-8-sig'))['status']=='paused'
    configs={f'h{h:g}_w{w1}_{w2}':dict(hotspot=h,**{'lambda':1000},delta=3,first_window=w1,second_window=w2)
             for h,w1,w2 in itertools.product([.1,.2,.25,.3],[3,5],[3,5])}
    # Declare screening before computing or inspecting new candidate scores.
    protocol=dict(configs=configs,baseline=BASE,excluded_sites=sorted(EXCLUDED),period='2018-2024 10-16 UTC',
        primary='shaded soil versus TS_1 and canopy versus TA; joint inclusive 0-60 C and both residuals <=10 K before monthly-hour aggregation',
        minimum='3 pairs per monthly-hour group, 3 groups per site',
        ranking='2018-2022 only: equal mean of squared ratios of soil/canopy mean-site RMSE to baseline',
        gates='Same scored sites; per-site retained instantaneous pairs cannot decrease by >2 percentage points of fixed eligible references; per-site monthly-hour count cannot decrease by >5 percentage points of fixed eligible monthly-hour groups; candidate common-range (without 10 K) mean-site RMSE <=1.10 times baseline for each component',
        retrospective='2023-2024 results previously inspected; post-hoc station exclusion; not independent validation. Rank only development; no reranking on later period.',
        provenance='Local station input caches only; no regional product changed; all four bands and 10 UTC saved',
        source_time='Existing frozen matched references; source-specific time conventions not newly verified')
    save('protocol.json',protocol)
    sources={};fp=J/'frozen_reference_panel.csv.gz';sources[str(fp)]=sha(fp)
    refs=pd.read_csv(fp);refs=refs.loc[refs.domain.eq('indirect')&~refs.site.isin(EXCLUDED)]
    blocks=[];tables=[]
    for done in sorted((OLD/'partitions').glob('*/*/complete.json')):
        info=json.loads(done.read_text());sid=info['site']
        if sid in EXCLUDED:continue
        folder=done.parent
        for name,key in [('input_cache.npz','cache_sha256'),('predictions.csv.gz','predictions_sha256')]:
            path=folder/name;sources[str(path)]=sha(path);assert sources[str(path)]==info[key]
        raw=pd.read_csv(folder/'predictions.csv.gz',dtype={'timestamp':str});raw=raw.loc[raw.model.eq('physical_h025')].reset_index(drop=True)
        n=len(raw)
        if not n:continue
        with np.load(folder/'input_cache.npz') as c:
            d={k:np.broadcast_to(c[k],(n,5,5)).copy() for k in ['sza','saa','lai']+joint.STATIC}
            for sat in ['e','i']:
                a=c[f'lst_{sat}_raw'];signed=np.where(a>=32768,a-65536,a) if info['input_raw_dtypes'][sat]=='uint16' else a.copy()
                d['lst_'+sat]=signed/100+273.15;d['lst_'+sat][(signed==0)|(signed==-8000)]=np.nan
        eligible=joint.physical_mask(d)
        p=pd.DataFrame({'site':sid,'time':pd.to_datetime(raw.timestamp,format='%Y%m%d%H%M',utc=True).astype(str),'input_eligible':eligible})
        p['bulk']=d['lst_e'][:,2,2]-273.15
        p=p.merge(refs[['site','time','year','month','hour','soil_reference','canopy_reference']],on=['site','time'],validate='one_to_one')
        assert len(p)==n
        for band in ['background_soil','canopy','sunlit_soil','shaded_soil']:p['old_'+band]=raw[band].to_numpy()
        blocks.append(d);tables.append(p)
    panel=pd.concat(tables,ignore_index=True);data={k:np.concatenate([d[k] for d in blocks]) for k in blocks[0]}
    del blocks
    assert panel.site.nunique()==12 and panel.year.between(2018,2024).all() and panel.hour.between(10,16).all()
    assert not panel.duplicated(['site','time']).any()
    panel.to_csv(OUT/'reference_panel.csv.gz',index=False)
    save('source_manifest.json',sources)
    ns=joint.functions();predictions={};scalar=[]
    for i,(name,c) in enumerate(configs.items()):
        with np.errstate(all='ignore'):
            pre=window_prepare(data,c['hotspot'],c['first_window'],c['second_window'],ns['hotspot_layer'])
            if c['hotspot']==.25:scalar.extend(scalar_window_check(data,pre,c))
            t,valid,_=retrieve(pre,data,c['lambda'],c['delta'],return_raw=True)
            t=t-273.15;t[~valid|~panel.input_eligible.to_numpy()]=np.nan
        predictions[name]=t
        print('INVERSION',i+1,'/',len(configs),name,flush=True)
        save('progress.json',dict(status='inverting',completed=i+1,total=len(configs)))
    old=panel[['old_'+b for b in ['background_soil','canopy','sunlit_soil','shaded_soil']]].to_numpy()
    assert np.array_equal(np.isfinite(old),np.isfinite(predictions[BASE]))
    baseline_diff=float(np.nanmax(np.abs(old-predictions[BASE])));assert baseline_diff<1e-8
    np.savez_compressed(OUT/'all_component_predictions.npz',**predictions)
    pd.DataFrame(scalar).to_csv(OUT/'scalar_window_checks.csv',index=False)
    soil=panel.soil_reference.to_numpy();canopy=panel.canopy_reference.to_numpy();bulk=panel.bulk.to_numpy()
    refok=panel.input_eligible.to_numpy()&np.isfinite(soil)&np.isfinite(canopy)&(soil>=0)&(soil<=60)&(canopy>=0)&(canopy<=60)&(bulk>=0)&(bulk<=60)
    ranges={};kept={}
    for name,t in predictions.items():
        ranges[name]=refok&np.isfinite(t).all(axis=1)&(t[:,3]>=0)&(t[:,3]<=60)&(t[:,1]>=0)&(t[:,1]<=60)
        kept[name]=ranges[name]&(np.abs(t[:,3]-soil)<=10)&(np.abs(t[:,1]-canopy)<=10)
    records=[];monthly=[];coverage=[]
    for name,t in predictions.items():
        common=ranges[name]&ranges[BASE];common10=kept[name]&kept[BASE]
        support_masks={'own_joint':kept[name],'common_range':common,'common_both10':common10}
        for period in ['development','retrospective','all']:
            pm=np.ones(len(panel),bool) if period=='all' else panel.year.le(2022).to_numpy() if period=='development' else panel.year.ge(2023).to_numpy()
            for site,idx in panel.loc[pm].groupby('site').groups.items():
                eligible=panel.loc[idx].loc[refok[idx]]
                den=eligible.groupby(['year','month','hour']).size();den=den.loc[den>=3]
                k=panel.loc[idx].loc[kept[name][idx]].groupby(['year','month','hour']).size();k=k.loc[k>=3]
                coverage.append(dict(model=name,period=period,site=site,eligible_pairs=int(refok[idx].sum()),kept_pairs=int(kept[name][idx].sum()),eligible_groups=len(den),kept_groups=len(k)))
            for support,mask in support_masks.items():
                choose=mask&pm
                z=panel.loc[choose,['site','year','month','hour']].copy()
                z['soil_reference']=soil[choose];z['canopy_reference']=canopy[choose]
                for comp,col in [('soil',3),('canopy',1)]:
                    z[comp+'_prediction']=t[choose,col];z[comp+'_baseline']=predictions[BASE][choose,col]
                g=z.groupby(['site','year','month','hour'],as_index=False).agg(**{c:(c,'mean') for c in z if c not in ['site','year','month','hour']},n_raw=('site','size'))
                g=g.loc[g.n_raw>=3].copy();g['model']=name;g['period']=period;g['support']=support;monthly.append(g)
                for site,a in g.groupby('site'):
                    if len(a)<3:continue
                    for comp in ['soil','canopy']:
                        e=a[comp+'_prediction']-a[comp+'_reference'];be=a[comp+'_baseline']-a[comp+'_reference']
                        records.append(dict(model=name,period=period,support=support,site=site,component=comp,rmse_K=float(np.sqrt(np.mean(e**2))),baseline_rmse_K=float(np.sqrt(np.mean(be**2))),n_groups=len(a),n_raw=int(a.n_raw.sum())))
        print('METRICS',name,flush=True)
    metrics=pd.DataFrame(records);cv=pd.DataFrame(coverage);months=pd.concat(monthly,ignore_index=True)
    summary=metrics.groupby(['model','period','support','component'],as_index=False).agg(mean_site_rmse_K=('rmse_K','mean'),baseline_common_rmse_K=('baseline_rmse_K','mean'),sites=('site','size'),n_groups=('n_groups','sum'),n_raw=('n_raw','sum'))
    oldm=pd.read_csv(PARENT/'station_metrics.csv');oldm=oldm.loc[oldm.soil_type.eq('shaded_soil')&oldm.start_hour.eq(10)&oldm.scale.eq('monthly_hour')]
    new=metrics.loc[metrics.model.eq(BASE)&metrics.period.eq('all')&metrics.support.eq('own_joint')]
    test=oldm.merge(new,on=['site','component'],validate='one_to_one',suffixes=('_old','_new'))
    assert len(test)==24 and (test.rmse_K_old-test.rmse_K_new).abs().max()<1e-8
    assert test.n_groups_old.eq(test.n_groups_new).all() and test.n_raw_old.eq(test.n_raw_new).all()
    rankings=[]
    for period in ['development','retrospective']:
        b=summary.loc[summary.model.eq(BASE)&summary.period.eq(period)&summary.support.eq('own_joint')].set_index('component')
        bcv=cv.loc[cv.model.eq(BASE)&cv.period.eq(period)].set_index('site')
        for name in configs:
            own=summary.loc[summary.model.eq(name)&summary.period.eq(period)&summary.support.eq('own_joint')].set_index('component')
            paired=summary.loc[summary.model.eq(name)&summary.period.eq(period)&summary.support.eq('common_range')].set_index('component')
            c=cv.loc[cv.model.eq(name)&cv.period.eq(period)].set_index('site')
            loss_pairs=((bcv.kept_pairs-c.kept_pairs)/bcv.eligible_pairs.replace(0,np.nan)).fillna(0).max()
            loss_groups=((bcv.kept_groups-c.kept_groups)/bcv.eligible_groups.replace(0,np.nan)).fillna(0).max()
            ratios=paired.mean_site_rmse_K/paired.baseline_common_rmse_K
            bs=set(metrics.loc[metrics.model.eq(BASE)&metrics.period.eq(period)&metrics.support.eq('own_joint'),'site'])
            cs=set(metrics.loc[metrics.model.eq(name)&metrics.period.eq(period)&metrics.support.eq('own_joint'),'site'])
            qualified=bs==cs and loss_pairs<=.02+1e-12 and loss_groups<=.05+1e-12 and ratios.le(1.1+1e-12).all()
            score=float(((own.mean_site_rmse_K/b.mean_site_rmse_K)**2).mean())
            rankings.append(dict(model=name,period=period,score=score,qualified=bool(qualified),max_pair_coverage_loss=float(loss_pairs),max_group_coverage_loss=float(loss_groups),max_common_rmse_ratio=float(ratios.max())))
    ranking=pd.DataFrame(rankings)
    chosen=ranking.loc[ranking.period.eq('development')&ranking.qualified].sort_values(['score','model']).iloc[0].model
    later=ranking.loc[ranking.period.eq('retrospective')&ranking.model.eq(chosen)].iloc[0]
    selection=dict(development_winner=chosen,configuration=configs[chosen],retrospective_gates_passed=bool(later.qualified),retrospective_score=float(later.score),production_updated=False,
        interpretation='Passing coverage/non-inferiority gates is not evidence of improvement; retrospective score above 1 is worse than baseline')
    save('selection.json',selection)
    metrics.to_csv(OUT/'station_metrics.csv',index=False);summary.to_csv(OUT/'summary.csv',index=False);cv.to_csv(OUT/'coverage.csv',index=False);ranking.to_csv(OUT/'ranking.csv',index=False)
    months.to_csv(OUT/'monthly_pairs.csv.gz',index=False)
    back=pd.read_csv(OUT/'monthly_pairs.csv.gz');errs=[]
    for r in metrics.sample(64,random_state=20261009).itertuples():
        a=back.loc[back.model.eq(r.model)&back.period.eq(r.period)&back.support.eq(r.support)&back.site.eq(r.site)]
        assert len(a)==r.n_groups and a.n_raw.sum()==r.n_raw
        errs.append(abs(float(np.sqrt(np.mean((a[r.component+'_prediction']-a[r.component+'_reference'])**2)))-r.rmse_K))
    assert max(errs)<1e-9 and sha(paused)==paused_hash
    assert sources=={p:sha(Path(p)) for p in sources}
    lines=['# 欧洲12站hotspot与两阶段窗口试验','','已授权的站点缓存反演，共16组；不生产区域数据。保留全部四组分和10—16点预测，便于后续按不同验证口径复核。',
        '2018—2024年，排除IT-TrF、FR-EM2。阴影土壤对TS_1、冠层对TA；联合0—60°C和10 K筛选后计算逐小时月均，至少3对/组、至少3组/站，RMSE逐站等权平均。λ=1000、δ=3固定。',
        '2018—2022年排序；2023—2024年为已经查看过的回顾性核查，不能称独立验证。12站也是事后筛选。共同样本不做10 K筛选的结果与覆盖率门槛用于防止只靠丢弃困难样本取得改善。源文件时区仍沿用原匹配，未新增核实。',
        '排序规则及门槛在运行前写入protocol.json。窗口顺序为第一阶段/第二阶段。','','| hotspot | 窗口1/2 | 全期土壤RMSE/K | 全期冠层RMSE/K | 站数 | 月小时组数 | 开发期分数 | 开发期门槛 |','|---:|---|---:|---:|---:|---:|---:|---|']
    for name,c in configs.items():
        a=summary.loc[summary.model.eq(name)&summary.period.eq('all')&summary.support.eq('own_joint')].set_index('component')
        r=ranking.loc[ranking.model.eq(name)&ranking.period.eq('development')].iloc[0]
        lines.append(f"| {c['hotspot']} | {c['first_window']}/{c['second_window']} | {a.loc['soil','mean_site_rmse_K']:.6f} | {a.loc['canopy','mean_site_rmse_K']:.6f} | {int(a.loc['soil','sites'])} | {int(a.loc['soil','n_groups'])} | {r.score:.6f} | {'通过' if r.qualified else '未通过'} |")
    lines+=['',f'开发期合格候选第一名：{chosen}。后期门槛通过：{bool(later.qualified)}；后期相对分数：{later.score:.6f}。',
        '这里的候选第一名仅限本次固定网格和事后12站，不代表全局最优或EVO最优；未修改生产参数。后期分数大于1表示综合表现劣于基准，覆盖率/非劣效门槛通过不等于优于基准。',
        'all_component_predictions.npz每个数组列顺序为背景土壤、冠层、光照土壤、阴影土壤，单位°C，行与reference_panel.csv.gz对应。']
    (OUT/'欧洲12站_hotspot与窗口参数试验.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    save('complete.json',dict(status='passed',configs=len(configs),stations=12,rows=len(panel),baseline_prediction_max_difference_K=baseline_diff,
        scalar_checks=len(scalar),readback_checks=len(errs),max_readback_error=max(errs),regional_status_unchanged=True,source_hashes_verified=True))
    save('progress.json',dict(status='completed',completed=16,total=16))
    print('SELECTION',selection,flush=True)
    print(summary.loc[summary.period.eq('all')&summary.support.eq('own_joint')].to_string(index=False),flush=True)
    print(ranking.to_string(index=False),flush=True)

if __name__=='__main__':main()
