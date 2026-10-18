"""Frozen development-only monthly-hour selection by station ecosystem class."""
from pathlib import Path
import datetime,itertools,json,hashlib
import numpy as np
import pandas as pd
import select_joint_station_parameters as joint
from compare_monthly_hour_factors import window_prepare
from search_evo_parameters import retrieve

IMPL=Path('C:/work/ls4t-msg/cases/official/implementation')
BASE_DIR=IMPL.parent/'results/production_assessment'
OUT=BASE_DIR/'landcover_parameter_selection'
CLASSFILE=BASE_DIR/'parameter_argument_monthly_hour/landcover_stratification/site_classification.csv'
REFERENCE=dict(hotspot=.25,**{'lambda':1000.},delta=3.,first_window=5,second_window=5)
GRID=dict(hotspot=[.025,.05,.1,.15,.2,.25,.3,.35,.4,.5],
          **{'lambda':[.0001,.001,.01,.1,1.,10.,100.,1000.]},
          delta=[0.,.25,.5,1.,2.,3.,4.,5.,7.,10.],first_window=[3,5],second_window=[3,5])
CLASSES=['forest','cropland','grassland']
FIELDS=['penalized_monthly_mse_10K','raw_pair_coverage','filtered_pair_coverage','filtered_monthly_coverage',
        'common_raw_mse_candidate','common_raw_mse_baseline','own_filtered_rmse','own_raw_rmse',
        'n_monthly_filtered','n_monthly_raw','n_monthly_common','n_pairs_filtered','n_eligible_pairs']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf8')
def md(df):
    x=df.copy()
    for c in x:
        if pd.api.types.is_float_dtype(x[c]):x[c]=x[c].map(lambda v:'NA' if pd.isna(v) else f'{v:.3f}')
    return '| '+' | '.join(x.columns)+' |\n| '+' | '.join(['---']*len(x.columns))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in x.itertuples(index=False,name=None))

def predict(data,config,ns,pre=None):
    with np.errstate(all='ignore'):
        if pre is None:pre=window_prepare(data,config['hotspot'],config['first_window'],config['second_window'],ns['hotspot_layer'])
        temp,valid,_=retrieve(pre,data,config['lambda'],config['delta'],return_raw=True)
    temp=temp-273.15;temp[~valid]=np.nan
    return temp

def make_specs(panel):
    specs=[]
    for site,z in panel.groupby('site'):
        for comp in ['soil','canopy']:
            ids=z.index[z['eligible_'+comp]].to_numpy()
            if not len(ids):continue
            tags=panel.loc[ids,'month'].astype(str)+'_'+panel.loc[ids,'hour'].astype(str)
            codes,labels=pd.factorize(tags,sort=True);ng=len(labels)
            counts=np.bincount(codes,minlength=ng);good=counts>=3
            if good.sum()<3:continue
            keep=good[codes];ids=ids[keep];codes=codes[keep]
            specs.append(dict(site=site,station_group=z.station_group.iloc[0],component=comp,ids=ids,codes=codes,
                ng=ng,good=good,reference=panel.loc[ids,comp+'_reference'].to_numpy(),labels=labels,
                n_eligible_pairs=len(ids),n_eligible_monthly=int(good.sum())))
    return specs

def cell_metrics(values,baseline,spec):
    ids=spec['ids'];v=values[ids];b=baseline[ids];r=spec['reference'];codes=spec['codes'];ng=spec['ng'];good=spec['good']
    finite=np.isfinite(v);valid10=finite&(np.abs(v-r)<=10)
    def means(mask):
        count=np.bincount(codes[mask],minlength=ng)
        def avg(x):return np.divide(np.bincount(codes[mask],weights=x[mask],minlength=ng),count,out=np.zeros(ng),where=count>0)
        return count,avg(v),avg(r),avg(b) if np.isfinite(b[mask]).all() else None
    n10,p10,r10,_=means(valid10);nv,pv,rv,_=means(finite)
    common=finite&np.isfinite(b);nc,pc,rc,bc=means(common)
    ok10=(n10>=3)&good;okv=(nv>=3)&good;okc=(nc>=3)&good
    loss=np.where(ok10,(p10-r10)**2,100.)
    def rmse(p,r,ok):return float(np.sqrt(np.mean((p[ok]-r[ok])**2))) if ok.sum()>=3 else np.nan
    return np.array([loss[good].mean(),finite.mean(),valid10.mean(),ok10.sum()/good.sum(),
        float(np.mean((pc[okc]-rc[okc])**2)) if okc.sum()>=3 else np.nan,
        float(np.mean((bc[okc]-rc[okc])**2)) if okc.sum()>=3 else np.nan,
        rmse(p10,r10,ok10),rmse(pv,rv,okv),ok10.sum(),okv.sum(),okc.sum(),valid10.sum(),len(ids)],float)

def evaluate(temp,base_temp,panel,specs):
    vals=joint.projected(temp,panel);base=joint.projected(base_temp,panel)
    return np.stack([cell_metrics(vals[s['component']],base[s['component']],s) for s in specs])

def check_cell_independently(values,baseline,spec,expected):
    ids=spec['ids'];q=pd.DataFrame(dict(code=spec['codes'],v=values[ids],b=baseline[ids],r=spec['reference']))
    raw=q.loc[q.v.notna()];filtered=raw.loc[(raw.v-raw.r).abs()<=10];common=raw.loc[raw.b.notna()]
    def aggregate(x):
        a=x.groupby('code').agg(v=('v','mean'),r=('r','mean'),b=('b','mean'),n=('v','size'))
        return a.loc[a.n>=3]
    a=aggregate(filtered);b=aggregate(raw);c=aggregate(common)
    allgroups=np.flatnonzero(spec['good']);loss=pd.Series(100.,index=allgroups)
    loss.loc[a.index]=(a.v-a.r)**2
    def rms(x):return float(np.sqrt(((x.v-x.r)**2).mean())) if len(x)>=3 else np.nan
    actual=np.array([loss.mean(),len(raw)/len(q),len(filtered)/len(q),len(a)/len(allgroups),
        float(((c.v-c.r)**2).mean()) if len(c)>=3 else np.nan,
        float(((c.b-c.r)**2).mean()) if len(c)>=3 else np.nan,rms(a),rms(b),len(a),len(b),len(c),len(filtered),len(q)])
    assert np.allclose(actual,expected,equal_nan=True,atol=1e-8,rtol=1e-10),(spec['site'],spec['component'],actual,expected)

def rank(arr,base,specs,group,exclude=None):
    selected=[i for i,s in enumerate(specs) if s['station_group']==group and s['site']!=exclude]
    if not selected:return None
    m=arr[:,selected];b=base[selected];n=len(arr)
    loss_cov=(m[:,:,1] < b[None,:,1]-.02-1e-12).any(axis=1)
    loss10=(m[:,:,2] < b[None,:,2]-.02-1e-12).any(axis=1)
    loss_month=(m[:,:,3] < b[None,:,3]-.05-1e-12).any(axis=1)
    raw_bad=np.zeros(n,dtype=bool);ratio=[]
    for comp in ['soil','canopy']:
        k=[j for j,i in enumerate(selected) if specs[i]['component']==comp]
        if not k:return None
        ratio.append(m[:,k,0].mean(axis=1)/b[k,0].mean())
        bm=b[k,7];required=np.isfinite(bm)
        raw_bad|=(~np.isfinite(m[:,np.array(k)[required],4])).any(axis=1)
        with np.errstate(invalid='ignore'):
            candidate=np.nanmean(m[:,k,4],axis=1);reference=np.nanmean(m[:,k,5],axis=1)
        raw_bad|=~np.isfinite(candidate)|~np.isfinite(reference)|(candidate>1.21*reference+1e-10)
    score=np.mean(ratio,axis=0);qualified=~(loss_cov|loss10|loss_month|raw_bad)
    ids=np.flatnonzero(qualified);assert len(ids),'Baseline must qualify'
    winner=int(ids[np.argmin(score[ids])])
    return dict(score=score,qualified=qualified,winner=winner,loss_raw_coverage=loss_cov,
                loss_filtered_coverage=loss10,loss_monthly_coverage=loss_month,raw_error_degradation=raw_bad)

def conventional(temp,base_temp,panel,model,group):
    values=joint.projected(temp,panel);base=joint.projected(base_temp,panel);rows=[];months=[]
    for comp in ['soil','canopy']:
        eligible=panel['eligible_'+comp].to_numpy();v=values[comp];b=base[comp];r=panel[comp+'_reference'].to_numpy()
        if group!='EVO':eligible&=panel.station_group.eq(group).to_numpy()
        else:eligible&=panel.domain.eq('direct').to_numpy()
        raw=eligible&np.isfinite(v)
        masks={'unfiltered':raw,'instant_10K':raw&(panel.domain.eq('direct').to_numpy()|(np.abs(v-r)<=10)),
               'common_unfiltered':raw&np.isfinite(b)}
        for support,mask in masks.items():
            z=panel.loc[mask,['site','split','month','hour']].copy();z['prediction']=v[mask];z['baseline']=b[mask];z['reference']=r[mask]
            g=z.groupby(['site','split','month','hour'],as_index=False).agg(prediction=('prediction','mean'),baseline=('baseline','mean'),reference=('reference','mean'),n_raw=('prediction','size'))
            g=g.loc[g.n_raw>=3].copy();g['model']=model;g['station_group']=group;g['component']=comp;g['support']=support;months.append(g)
            for split in ['all','development','validation']:
                x=g if split=='all' else g.loc[g.split.eq(split)]
                for site,a in x.groupby('site'):
                    if len(a)<3:continue
                    e=a.prediction-a.reference;be=a.baseline-a.reference
                    rows.append(dict(model=model,station_group=group,site=site,component=comp,support=support,split=split,
                        rmse_K=float(np.sqrt((e**2).mean())),bias_K=float(e.mean()),n_groups=len(a),n_raw=int(a.n_raw.sum()),
                        paired_baseline_rmse_K=float(np.sqrt((be**2).mean())) if support=='common_unfiltered' else np.nan))
    return rows,months

def main():
    OUT.mkdir(exist_ok=True)
    if (OUT/'selection.json').exists():raise RuntimeError('Selection frozen: do not rerank after inspecting validation.')
    keys=list(GRID);configs=[]
    for v in itertools.product(*(GRID[k] for k in keys)):configs.append(dict(zip(keys,v)))
    assert len(configs)==3200
    baseline_id=next(i for i,c in enumerate(configs) if c==REFERENCE)
    lc=pd.read_csv(CLASSFILE);mapping=lc.set_index('site').station_group.to_dict()
    protocol=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),grid=GRID,candidate_count=len(configs),baseline=REFERENCE,
        classification='Local station inventory classes, not pixel classes; forest/cropland/grassland only',
        samples={g:lc.loc[lc.station_group.eq(g),'site'].tolist() for g in CLASSES},
        development='2018-2022',validation='2023-2024, retrospective, already previously inspected',
        target='Monthly-hour conditional comparison after component-wise instantaneous absolute error <=10 K, at least 3 pairs per group',
        frozen_panel='Physical-input/reference eligibility; monthly-hour groups with >=3 eligible pairs; cells with >=3 eligible groups',
        loss='Within each fixed monthly-hour group squared mean paired error; missing/insufficient output group assigned 100 K^2; equal groups within site, equal sites within component, two baseline-normalized component MSEs equal weight',
        gates='Each site/component raw and <=10 K instantaneous coverage lose at most 2 percentage points; monthly group coverage loses at most 5 percentage points; each class/component common-unfiltered MSE increases at most 21% (10% RMSE)',
        folds='Leave one development site out, fit using remaining sites only; require >=2 training sites; class with <3 development sites has no credible LOSO fit',
        validation_rule='Selection frozen before computing validation scores; same gates and normalized penalized score <=1.0; no validation-driven reranking',
        window_limit='Both windows independently 3 or 5; existing 5x5 cache; first/second central residual architecture; 1x1 excluded based on prior severe coverage loss',
        EVO='Direct diagnostic only after selection, not a class-matched training reference',
        evidence_limits='Reference-dependent filtering is conditional; finite tested grid; metadata disagreements; no deployment or global optimum claim',
        source_sha256={str(p):sha(p) for p in [Path(__file__),CLASSFILE,IMPL/'select_joint_station_parameters.py',IMPL/'compare_monthly_hour_factors.py',IMPL/'search_evo_parameters.py']})
    js('protocol.json',protocol);pd.DataFrame(configs).rename_axis('candidate_index').to_csv(OUT/'candidates.csv')
    paused=Path('E:/PRODUCTS/LSCT/MSG_5X5_PHYSICAL_V1/status.json');paused_sha=sha(paused);assert json.loads(paused.read_text(encoding='utf-8-sig'))['status']=='paused'
    joint.OUT=OUT;data,panel=joint.load_panel();panel['station_group']=panel.site.map(mapping).fillna('EVO')
    panel.to_csv(OUT/'frozen_reference_panel.csv.gz',index=False)
    idx=np.flatnonzero(panel.station_group.isin(CLASSES)&panel.split.eq('development'))
    dp=panel.iloc[idx].reset_index(drop=True);dd={k:v[idx] for k,v in data.items()};specs=make_specs(dp)
    specmeta=[{k:s[k] for k in ['site','station_group','component','n_eligible_pairs','n_eligible_monthly']} for s in specs]
    js('development_cells.json',specmeta);ns=joint.functions();bt=predict(dd,REFERENCE,ns);bt[~dp.input_eligible.to_numpy()]=np.nan
    base=evaluate(bt,bt,dp,specs);arr=np.full((len(configs),len(specs),len(FIELDS)),np.nan);cache={}
    bvals=joint.projected(bt,dp)
    for j,spec in enumerate(specs):check_cell_independently(bvals[spec['component']],bvals[spec['component']],spec,base[j])
    for i,c in enumerate(configs):
        key=(c['hotspot'],c['first_window'],c['second_window'])
        if key not in cache:
            with np.errstate(all='ignore'):cache[key]=window_prepare(dd,*key,ns['hotspot_layer'])
        t=predict(dd,c,ns,cache[key]);t[~dp.input_eligible.to_numpy()]=np.nan
        arr[i]=evaluate(t,bt,dp,specs)
        if (i+1)%100==0:
            print('SEARCH',i+1,'/',len(configs),flush=True)
            js('progress.json',dict(status='searching_development',completed=i+1,total=len(configs)))
            np.savez_compressed(OUT/'development_checkpoint.npz',metrics=arr[:i+1],baseline=base,fields=np.array(FIELDS))
    assert np.allclose(arr[baseline_id],base,equal_nan=True)
    score_rows=[];selections={};folds=[]
    for group in CLASSES:
        ranked=rank(arr,base,specs,group);winner=ranked['winner'];score=float(ranked['score'][winner])
        close=np.flatnonzero(ranked['qualified']&(ranked['score']<=score*1.01+1e-12)).tolist()
        selections[group]=dict(candidate_index=winner,configuration=configs[winner],development_score=score,
            qualified_candidates=int(ranked['qualified'].sum()),within_one_percent_candidates=close,
            development_sites=sorted(set(s['site'] for s in specs if s['station_group']==group)))
        for i,c in enumerate(configs):
            score_rows.append(dict(station_group=group,candidate_index=i,**c,**{k:float(v[i]) if k=='score' else bool(v[i]) for k,v in ranked.items() if k!='winner'}))
        sites=selections[group]['development_sites']
        for site in sites:
            if len(sites)-1<2:
                folds.append(dict(station_group=group,held_site=site,status='insufficient_training_sites',training_sites=len(sites)-1));continue
            r=rank(arr,base,specs,group,exclude=site);win=r['winner'];held=[i for i,s in enumerate(specs) if s['site']==site]
            ratios=[]
            for comp in ['soil','canopy']:
                cells=[i for i in held if specs[i]['component']==comp]
                if cells:ratios.append(float(arr[win,cells,0].mean()/base[cells,0].mean()))
            folds.append(dict(station_group=group,held_site=site,status='evaluated',training_sites=len(sites)-1,
                candidate_index=win,**configs[win],held_site_normalized_loss=float(np.mean(ratios))))
    selection=dict(selected=selections,baseline_candidate_index=baseline_id,
        selected_before_validation=True,selection_time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    js('selection.json',selection);pd.DataFrame(score_rows).to_csv(OUT/'development_scores.csv',index=False)
    pd.DataFrame(folds).to_csv(OUT/'leave_one_site_out.csv',index=False)
    print('FROZEN_SELECTION',json.dumps(selection,ensure_ascii=False),flush=True)
    # Validation is evaluated only after the preceding immutable selection record exists.
    vix=np.flatnonzero(panel.station_group.isin(CLASSES)&panel.split.eq('validation'))
    vp=panel.iloc[vix].reset_index(drop=True);vs=make_specs(vp)
    bfull=predict(data,REFERENCE,ns);bfull[~panel.input_eligible.to_numpy()]=np.nan
    vb=evaluate(bfull[vix],bfull[vix],vp,vs);all_rows=[];all_months=[];val=[];prediction_rows=[];selected_metrics=[]
    for group in CLASSES:
        c=selections[group]['configuration'];full=predict(data,c,ns);full[~panel.input_eligible.to_numpy()]=np.nan
        devvals=joint.projected(full[idx],dp)
        for j,spec in enumerate(specs):
            if spec['station_group']==group:check_cell_independently(devvals[spec['component']],bvals[spec['component']],spec,arr[selections[group]['candidate_index'],j])
        vm=evaluate(full[vix],bfull[vix],vp,vs);ranking=rank(np.stack([vb,vm]),vb,vs,group)
        val.append(dict(station_group=group,score=float(ranking['score'][1]),gates_passed=bool(ranking['qualified'][1]),
            retrospective_acceptance=bool(ranking['qualified'][1] and ranking['score'][1]<=1.+1e-12),
            failures=[k for k in ['loss_raw_coverage','loss_filtered_coverage','loss_monthly_coverage','raw_error_degradation'] if ranking[k][1]],
            sites=sorted(set(s['site'] for s in vs if s['station_group']==group))))
        for method,t in [('selected',full),('baseline',bfull)]:
            r,m=conventional(t,bfull,panel,method,group);all_rows+=r;all_months+=m
        r,m=conventional(full,bfull,panel,group+'_selected','EVO');all_rows+=r;all_months+=m
        vals=joint.projected(full,panel);mask=panel.station_group.eq(group)|panel.domain.eq('direct')
        z=panel.loc[mask,['site','station_group','domain','time','split','soil_reference','canopy_reference']].copy()
        z['configuration_group']=group;z['soil']=vals['soil'][mask];z['canopy']=vals['canopy'][mask];prediction_rows.append(z)
        for split,p,slist,t,bt0 in [('development',dp,specs,full[idx],bfull[idx]),('validation',vp,vs,full[vix],bfull[vix])]:
            ev=evaluate(t,bt0,p,slist)
            for j,spec in enumerate(slist):
                if spec['station_group']!=group:continue
                selected_metrics.append(dict(split=split,station_group=group,site=spec['site'],component=spec['component'],**dict(zip(FIELDS,ev[j]))))
    js('validation.json',val);pd.DataFrame(selected_metrics).to_csv(OUT/'selected_cell_metrics.csv',index=False)
    pd.concat(prediction_rows,ignore_index=True).to_csv(OUT/'selected_predictions.csv.gz',index=False)
    metrics=pd.DataFrame(all_rows);metrics.to_csv(OUT/'station_metrics.csv',index=False)
    months=pd.concat(all_months,ignore_index=True);months.to_csv(OUT/'monthly_hour_pairs.csv.gz',index=False)
    summary=metrics.groupby(['model','station_group','component','support','split'],as_index=False).agg(
        sites=('site','size'),mean_site_rmse_K=('rmse_K','mean'),mean_site_bias_K=('bias_K','mean'),
        mean_paired_baseline_rmse_K=('paired_baseline_rmse_K','mean'),n_groups=('n_groups','sum'),n_raw=('n_raw','sum'))
    summary.to_csv(OUT/'summary.csv',index=False)
    recommended=[]
    for v in val:
        group=v['station_group'];recommended.append(dict(station_group=group,**selections[group]['configuration'],
            status='retrospectively_supported_candidate' if v['retrospective_acceptance'] else 'development_optimum_not_confirmed',
            validation=v,scope='station experiment only; not deployed; station metadata classes'))
    js('selected_class_configurations.json',recommended)
    # Independently reproduce a sample of the saved monthly metric rows.
    back=pd.read_csv(OUT/'monthly_hour_pairs.csv.gz');err=[]
    for r in metrics.sample(min(80,len(metrics)),random_state=20261009).itertuples():
        z=back.loc[back.model.eq(r.model)&back.station_group.eq(r.station_group)&back.site.eq(r.site)&back.component.eq(r.component)&back.support.eq(r.support)]
        if r.split!='all':z=z.loc[z.split.eq(r.split)]
        assert len(z)==r.n_groups and z.n_raw.sum()==r.n_raw
        err.append(abs(float(np.sqrt(np.mean((z.prediction-z.reference)**2)))-r.rmse_K))
    assert max(err)<1e-9 and sha(paused)==paused_sha
    report(selection,val,summary,pd.DataFrame(folds),lc)
    js('complete.json',dict(status='passed',candidate_count=len(configs),classes=CLASSES,readback_metrics=len(err),
        max_readback_difference_K=max(err),source_hashes_unchanged=all(sha(p)==h for p,h in protocol['source_sha256'].items()),
        regional_status_unchanged=True))
    js('progress.json',dict(status='complete',completed=len(configs),total=len(configs)))
    print(summary.loc[summary.model.isin(['selected','baseline'])&summary.support.eq('instant_10K')&summary.split.eq('validation')].to_string(index=False),flush=True)

def report(selection,val,summary,folds,lc):
    configs=[]
    for group,a in selection['selected'].items():
        v=next(x for x in val if x['station_group']==group)
        configs.append(dict(group=group,**a['configuration'],dev_score=a['development_score'],validation_score=v['score'],
            validation_pass=v['retrospective_acceptance'],dev_sites=len(a['development_sites']),near_ties=len(a['within_one_percent_candidates'])))
    t=pd.DataFrame(configs);t.to_csv(OUT/'selected_configuration_table.csv',index=False)
    results=summary.loc[summary.model.isin(['selected','baseline'])&summary.support.eq('instant_10K')]
    evo=summary.loc[summary.station_group.eq('EVO')&summary.support.eq('unfiltered')&summary.split.eq('all')]
    text=f'''# 森林、农田、草地的参数组合筛选

完成3200组完整组合搜索，仅开发时段用于排序；配置冻结后才计算2023—2024年结果。这里的“最优”仅指预先固定网格、评价规则和覆盖约束下的开发集最小分数，不是全球最优。

## 分类型配置

{md(t)}

first_window和second_window分别为第一、第二阶段正方形窗口边长，单位像元。delta为辐射量单位W m^-2 sr^-1 um^-1。
validation_pass=False意味着后期核验未支持直接采用；不因此用后期结果重新挑选另一组。near_ties为开发分数在最小值1%以内的合格组合数，并不代表统计等价检验。

## 选参规则

站点类型取本地清单：森林5站、农田3站、草地3站。按站点类型而非缓存像元类型分组；两者存在不一致，不能直接照此生成像元分类参数产品。
开发2018—2022年，核验2023—2024年。所有时段此前已查看过，属于回顾性核验。农田实际参与开发的站点数见表，不把缺资料站点算作训练样本。
EVO未归入任何一类参与选参，仅在配置冻结后作为额外直接验证诊断。

逐站、逐年逐月逐UTC小时求反演/参考配对均值；每组至少3条瞬时配对。欧洲土壤对TS_1探针、冠层对TA气温，均为间接评价。瞬时温差<=10 K后求月均；不合格/缺失月小时组在排序目标中赋100 K²惩罚。站点等权、两个组分相对各自基准MSE归一化后等权；因此排序分数不是RMSE。
每站/组分原始有效率和10 K后有效率最多下降2个百分点，月小时组有效率最多下降5个百分点；各类每组分共同未筛选MSE不得升高超过21%（对应RMSE约10%）。这些是预设选择规则，不是自然定律。
常规RMSE另外列出，不含缺失惩罚。10 K筛选依赖参考，只能用于条件性验证，不能作为区域产品的运行筛选条件。

网格详见protocol.json：hotspot从0.025至0.5共10值，lambda从0.0001至1000共8值，delta从0至10共10值，两个阶段各3/5，共3200组。1×1因前轮严重丢失有效样本而不纳入此次候选，更大窗口因原始缓存范围未测试。

## 逐小时月均RMSE（10 K筛选后）

{md(results[['model','station_group','component','split','sites','mean_site_rmse_K','n_groups','n_raw']])}

## 留一站点

每次只用其余开发站点选参，然后在被留站点的开发时段上计算相对基准的含缺失惩罚分数。分数小于1较好。训练站少于2不进行该折；不把同一站多年记录当作多个独立站点。
这是有限样本空间稳定性诊断，不是独立外部测试。各折可能选出不同组合。

{md(folds)}

## EVO额外诊断

这些参数是按欧洲站点类别选取，EVO不是类别匹配的外部测试。下面只用于揭示与直接验证的潜在冲突，不用于事后重排。

{md(evo[['model','component','sites','mean_site_rmse_K','n_groups','n_raw']])}

## 文件与适用边界

- selected_class_configurations.json：实际选出的分类配置、核验状态与使用范围。
- protocol.json、selection.json：预设规则和冻结的开发集选择。
- development_scores.csv：各类别全部3200组分数及约束判定。
- development_checkpoint.npz、development_cells.json：逐候选/站点/组分统计及字段说明，可复算选择。
- leave_one_site_out.csv、validation.json：留站诊断、后期核验。
- selected_predictions.csv.gz、monthly_hour_pairs.csv.gz：选中配置的站点瞬时与逐小时月均配对。
- station_metrics.csv、summary.csv：未筛选、10 K筛选、共同未筛选三种口径。

保留时段通过也只是回顾性支持；森林多为针叶林、农田/草地各仅少量站点、站点/像元类型存在差异。任何类型配置都不能据此声称适用于全部欧洲—非洲相应地类。当前只保存站点研究配置，区域生产仍暂停。
'''
    (OUT/'森林农田草地最优参数组合.md').write_text(text,encoding='utf8')

if __name__=='__main__':main()
