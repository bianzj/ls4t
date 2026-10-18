"""Frozen physical 5x5 parameter selection using EVO and indirect stations.

Development scores alone choose the candidate. Previously inspected later
periods are retrospective validation, never claimed as untouched test data.
"""
from pathlib import Path
import datetime as dt,hashlib,itertools,json
import numpy as np
import pandas as pd
from search_evo_parameters import prepare,retrieve,planck,inverse
from run_station_full_2018_2024 import functions,STATIC,BANDS
from validate_msg_5x5_europe import clean_ground

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'results/production_assessment'
STATIONS=BASE/'msg_5x5/station_direct_2018_2024'
EVO=BASE/'parameter_search'
OUT=BASE/'joint_parameter_selection'
KEYS=['sza','saa','lai','lst_e','lst_i']+STATIC
GRID={'hotspot':[.05,.1,.15,.2,.25,.3,.4,.5], 'lambda':[.01,.1,1,10,100,1000], 'delta':[.5,1,2,3,5]}
REFERENCE={'hotspot':.25,'lambda':1000.,'delta':3.}
PENALTY=20.

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')

def physical_mask(data):
    bad=~np.isfinite(data['sza'])|(data['sza']<0)|(data['sza']>=90)|~np.isfinite(data['saa'])
    bad|=~np.isfinite(data['lai'])|(data['lai']<0)|(data['lai']>10)
    for k in ['vza_e','vza_i']:bad|=~np.isfinite(data[k])|(data[k]<0)|(data[k]>=90)
    for k in ['vaa_e','vaa_i']:bad|=~np.isfinite(data[k])
    for k in ['emis_s','emis_v']:bad|=~np.isfinite(data[k])|(data[k]<=0)|(data[k]>1)
    for k in ['lst_e','lst_i']:
        data[k][bad|~np.isfinite(data[k])|(data[k]<150)|(data[k]>400)]=np.nan
    common=np.isfinite(data['lst_e'])&np.isfinite(data['lst_i'])
    return common[:,2,2]&(data['lai'][:,2,2]>=.05)&(common.sum(axis=(1,2))>=10)

def load_panel():
    pieces=[];frames=[];manifest={};grounds={}
    ep=pd.read_csv(EVO/'frozen_reference_panel.csv');ep['time']=pd.to_datetime(ep.time,utc=True)
    with np.load(EVO/'input_cache.npz') as c:
        ed={k:np.broadcast_to(c[k],(len(ep),5,5)).copy() for k in KEYS}
    egood=physical_mask(ed)&ep.eligible.to_numpy(bool)
    ep['site']='EVO';ep['domain']='direct';ep['split']=np.where(ep.time.dt.month.le(10),'development','validation')
    ep['input_eligible']=egood;ep['soil_reference']=pd.to_numeric(ep.soil_reference);ep['canopy_reference']=pd.to_numeric(ep.canopy_reference)
    frames.append(ep[['site','domain','time','split','input_eligible','soil_reference','canopy_reference']]);pieces.append(ed)
    for p in [EVO/'input_cache.npz',EVO/'frozen_reference_panel.csv',EVO/'input_manifest.json']:manifest[str(p)]=sha(p)
    old_ground=json.loads((STATIONS/'ground_manifest.json').read_text())
    for done in sorted((STATIONS/'partitions').glob('*/*/complete.json')):
        info=json.loads(done.read_text());sid=info['site'];folder=done.parent
        for name,key in [('input_cache.npz','cache_sha256'),('predictions.csv.gz','predictions_sha256')]:
            assert sha(folder/name)==info[key];manifest[str(folder/name)]=info[key]
        rawpanel=pd.read_csv(folder/'predictions.csv.gz',dtype={'timestamp':str})
        rawpanel=rawpanel.loc[rawpanel.model.eq('physical_h025')].reset_index(drop=True)
        n=len(rawpanel)
        if not n:continue
        with np.load(folder/'input_cache.npz') as c:
            d={k:np.broadcast_to(c[k],(n,5,5)).copy() for k in ['sza','saa','lai']+STATIC}
            for sat in ['e','i']:
                raw=c[f'lst_{sat}_raw'];signed=np.where(raw>=32768,raw-65536,raw) if info['input_raw_dtypes'][sat]=='uint16' else raw.copy()
                a=signed/100+273.15;a[(signed==0)|(signed==-8000)]=np.nan;d[f'lst_{sat}']=a
        eligible=physical_mask(d)
        if sid not in grounds:
            path=Path(old_ground[sid]['path']);assert sha(path)==old_ground[sid]['sha256']
            grounds[sid]=clean_ground(path)[0];manifest[str(path)]=sha(path)
        p=pd.DataFrame({'site':sid,'domain':'indirect','time':pd.to_datetime(rawpanel.timestamp,format='%Y%m%d%H%M',utc=True),
                        'input_eligible':eligible})
        p=pd.merge_asof(p,grounds[sid],left_on='time',right_on='field_time',direction='nearest',tolerance=pd.Timedelta(minutes=30))
        p['soil_reference']=p.TS_1;p['canopy_reference']=p.TA
        p['input_eligible']&=p.time.dt.hour.between(11,16)
        p['split']=np.where(p.time.dt.year.le(2022),'development','validation')
        frames.append(p[frames[0].columns]);pieces.append(d)
    panel=pd.concat(frames,ignore_index=True);data={k:np.concatenate([d[k] for d in pieces]) for k in KEYS}
    panel['year']=panel.time.dt.year;panel['month']=panel.time.dt.strftime('%Y%m');panel['hour']=panel.time.dt.hour
    panel['date']=panel.time.dt.strftime('%Y-%m-%d');panel['bulk']=data['lst_e'][:,2,2]-273.15
    for comp in ['soil','canopy']:
        panel[f'eligible_{comp}']=panel.input_eligible&panel[f'{comp}_reference'].between(-23.15,76.85)
    assert not panel.duplicated(['site','time']).any()
    panel.to_csv(OUT/'frozen_reference_panel.csv.gz',index=False);write_json('input_manifest.json',manifest)
    return data,panel

def score_specs(panel,split):
    """Weights: domain -> equal sites -> equal years -> equal months -> records."""
    specs={}
    for domain,comp in itertools.product(['direct','indirect'],['soil','canopy']):
        use=panel.split.eq(split)&panel.domain.eq(domain)&panel[f'eligible_{comp}']
        z=panel.loc[use,['site','year','month']].copy()
        groups=z.groupby(['site','year','month']).size();z=z.join(groups.rename('n_month'),on=['site','year','month'])
        z=z.loc[z.n_month>=3].copy()
        cells=z[['site','year','month']].drop_duplicates()
        months=cells.groupby(['site','year']).size().rename('n_months')
        years=cells[['site','year']].drop_duplicates().groupby('site').size().rename('n_years')
        z=z.join(months,on=['site','year']).join(years,on='site')
        weight=1/(z.n_month*z.n_months*z.n_years*z.site.nunique())
        assert abs(weight.sum()-1)<1e-9 and len(z)>0,(split,domain,comp)
        sites={s:g.index.to_numpy() for s,g in z.groupby('site')}
        specs[(domain,comp)]={'indices':z.index.to_numpy(),'weights':weight.to_numpy(),
                             'sites':sites,'reference':panel.loc[z.index,f'{comp}_reference'].to_numpy(float)}
    return specs

def projected(temp,panel):
    soil=np.where(panel.domain.eq('direct'),temp[:,2],temp[:,0])
    return {'soil':soil,'canopy':temp[:,1]}

def evaluate(temp,panel,specs):
    values=projected(temp,panel);result={};coverage={}
    for (domain,comp),s in specs.items():
        indices=s['indices'];v=values[comp][indices];valid=np.isfinite(v)
        loss=np.where(valid,(v-s['reference'])**2,PENALTY**2)
        prefix=f'{domain}_{comp}'
        result[prefix+'_rmse']=float(np.sqrt(np.dot(s['weights'],loss)))
        result[prefix+'_coverage']=float(valid.mean());result[prefix+'_n']=len(v)
        for sid,index in s['sites'].items():coverage[(domain,comp,sid)]=(float(np.isfinite(values[comp][index]).mean()),len(index))
    return result,coverage

def prediction(data,config,ns,pre=None):
    with np.errstate(all='ignore'):
        if pre is None:pre=prepare(data,config['hotspot'],'physical',5,'center',ns['hotspot_layer'])
        t,valid,active=retrieve(pre,data,config['lambda'],config['delta'],'physical',return_raw=True)
    t=t-273.15;t[~valid]=np.nan
    return t,valid,active

def normalized(result,baseline):
    ratios={f'{d}_{c}':(result[f'{d}_{c}_rmse']/baseline[f'{d}_{c}_rmse'])**2 for d,c in itertools.product(['direct','indirect'],['soil','canopy'])}
    ratios['direct_mean']=np.mean([ratios['direct_soil'],ratios['direct_canopy']])
    ratios['indirect_mean']=np.mean([ratios['indirect_soil'],ratios['indirect_canopy']])
    return ratios

def qualified(result,coverage,baseline,basecov):
    reasons=[]
    for d,c in itertools.product(['direct','indirect'],['soil','canopy']):
        k=f'{d}_{c}'
        if result[k+'_rmse']>baseline[k+'_rmse']*1.1+1e-10:reasons.append(k+'_degradation_over_10pct')
    for k,(v,n) in coverage.items():
        threshold=.01 if k[0]=='direct' else .02
        if (k[0]=='direct' or n>=30) and v<basecov[k][0]-threshold-1e-10:reasons.append('_'.join(k)+'_coverage_loss')
    return reasons

def validation_tables(predictions,panel):
    raw=[];monthly=[];metrics=[]
    for name,temp in predictions.items():
        values=projected(temp,panel)
        for comp in ['soil','canopy']:
            mask=panel[f'eligible_{comp}']&np.isfinite(values[comp])
            z=panel.loc[mask,['site','domain','time','split','year','month','hour','date','bulk']].copy()
            z['reference']=panel.loc[mask,f'{comp}_reference'];z['prediction']=values[comp][mask]
            z['component']=comp;z['model']=name;raw.append(z)
            for (site,domain,split),x in z.groupby(['site','domain','split']):
                for scale in ['instantaneous','monthly_calendar','monthly_hour']:
                    if scale=='instantaneous':a=x[['reference','prediction','bulk']].copy();nraw=len(x)
                    else:
                        keys=['month']+(['hour'] if scale=='monthly_hour' else [])
                        a=x.groupby(keys,as_index=False).agg(reference=('reference','mean'),prediction=('prediction','mean'),bulk=('bulk','mean'),n_raw=('prediction','size'))
                        a=a.loc[a.n_raw>=3].copy();nraw=int(a.n_raw.sum())
                        a['site']=site;a['domain']=domain;a['split']=split;a['component']=comp;a['model']=name;a['scale']=scale;monthly.append(a)
                    for method in ['prediction','bulk']:
                        error=a[method]-a.reference
                        metrics.append({'model':name,'site':site,'domain':domain,'split':split,'component':comp,'scale':scale,'method':method,
                            'n':len(a),'n_raw':nraw,'rmse_K':float(np.sqrt(np.mean(error**2))) if len(a) else np.nan,
                            'bias_K':float(error.mean()) if len(a) else np.nan,'enough_groups':len(a)>=3})
    pairs=pd.concat(raw,ignore_index=True);months=pd.concat(monthly,ignore_index=True);met=pd.DataFrame(metrics)
    pairs.to_csv(OUT/'matched_predictions.csv.gz',index=False);months.to_csv(OUT/'matched_monthly.csv.gz',index=False)
    met.to_csv(OUT/'station_metrics.csv',index=False)
    sums=met.loc[met.enough_groups].groupby(['model','domain','split','component','scale','method'],as_index=False).agg(
        sites=('site','size'),mean_site_rmse_K=('rmse_K','mean'),mean_site_bias_K=('bias_K','mean'),n_groups=('n','sum'),n_raw=('n_raw','sum'))
    sums.to_csv(OUT/'validation_summary.csv',index=False)
    # Recompute selected RMSE from the saved monthly and raw tables.
    errors=[]
    for r in met.loc[met.model.eq('joint_selected')].itertuples():
        if not r.n:continue
        source=pairs if r.scale=='instantaneous' else months
        z=source.loc[source.site.eq(r.site)&source.split.eq(r.split)&source.component.eq(r.component)&source.model.eq(r.model)]
        if r.scale!='instantaneous':z=z.loc[z.scale.eq(r.scale)]
        assert len(z)==r.n
        col='prediction' if r.method=='prediction' else 'bulk';error=float(np.sqrt(np.mean((z[col]-z.reference)**2)))
        errors.append(abs(error-r.rmse_K))
    assert max(errors)<1e-9
    return sums,{'rows':len(errors),'max_difference_K':max(errors)}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'selection.json').exists():raise RuntimeError('Selection is frozen; do not rerank after seeing validation scores.')
    paused=Path('E:/PRODUCTS/LSCT/MSG_5X5_PHYSICAL_V1/status.json');paused_hash=sha(paused)
    assert json.loads(paused.read_text(encoding='utf-8-sig'))['status']=='paused'
    protocol={'created_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),'grid':GRID,'baseline':REFERENCE,
        'architecture':'both stages 5x5, center-constant first-stage residual; window/residual architecture not tuned',
        'units':'physical Planck at 10.5e-6 m; delta in W m-2 sr-1 um-1',
        'split':{'EVO_development':'2017 Aug-Oct','EVO_validation':'2017 Nov-Dec','Europe_development':'2018-2022','Europe_validation':'2023-2024'},
        'validation_status':'Retrospective temporal validation: prior analyses already saw aggregate statistics including these periods.',
        'reference_mapping':{'EVO_soil':'direct sunlit soil reference','EVO_canopy':'direct crown reference',
            'Europe_soil':'background soil versus TS_1 probe','Europe_canopy':'canopy versus TA air temperature'},
        'selection':'0.70*mean(direct component MSE / baseline direct component MSE) + 0.30*mean(indirect component MSE / baseline indirect component MSE)',
        'weighting':'Each domain/component separately: equal sites, equal years within site, equal months within year, equal records within month; at least 3 frozen eligible records/month.',
        'missing_prediction_penalty_K':PENALTY,'gates':'Each domain/component penalized RMSE <=1.10*baseline; EVO coverage loss <=1 percentage point; each European site/component with >=30 eligible records loss <=2 points.',
        'residual_filter':None,'physical_output_range_K':[250,350],'input_lai_center_min':.05,
        'post_selection_validation_acceptance':'Same non-inferiority/coverage gates and validation joint normalized score <=1.0; failure does not trigger holdout reranking.',
        'source_sha256':{str(p):sha(p) for p in [Path(__file__),HERE/'search_evo_parameters.py',HERE/'run_station_full_2018_2024.py',HERE/'msg_lsct3.2-iter-site-cons-ig-center.py']}}
    write_json('protocol.json',protocol)
    data,panel=load_panel();ns=functions()
    dev_rows=np.flatnonzero(panel.split.eq('development').to_numpy());devpanel=panel.iloc[dev_rows].reset_index(drop=True)
    devdata={k:v[dev_rows] for k,v in data.items()};devspec=score_specs(devpanel,'development')
    base_temp,_,_=prediction(devdata,REFERENCE,ns);baseline,basecov=evaluate(base_temp,devpanel,devspec)
    configs=[];results=[]
    for h in GRID['hotspot']:
        pre=prepare(devdata,h,'physical',5,'center',ns['hotspot_layer'])
        for l,d in itertools.product(GRID['lambda'],GRID['delta']):
            config={'id':f'J{len(configs)+1:03d}','hotspot':h,'lambda':l,'delta':d};configs.append(config)
            temp,_,_=prediction(devdata,config,ns,pre);met,cov=evaluate(temp,devpanel,devspec)
            norm=normalized(met,baseline);reasons=qualified(met,cov,baseline,basecov)
            results.append({**config,**met,**norm,'joint_score':.7*norm['direct_mean']+.3*norm['indirect_mean'],
                            'qualified':not reasons,'exclusions':';'.join(reasons)})
        pd.DataFrame(results).to_csv(OUT/'development_scores.csv',index=False)
        write_json('progress.json',{'status':'searching','completed':len(configs),'total':240})
        print('SEARCHED',len(configs),'/240',flush=True)
    scores=pd.DataFrame(results);qualified_scores=scores.loc[scores.qualified].sort_values(['joint_score','id'])
    assert len(qualified_scores)>0
    selected_id=qualified_scores.iloc[0].id;selected=next(c for c in configs if c['id']==selected_id)
    # Single-domain leaders are development-only controls, not alternative holdout selections.
    direct_leader=qualified_scores.sort_values(['direct_mean','id']).iloc[0].id
    indirect_leader=qualified_scores.sort_values(['indirect_mean','id']).iloc[0].id
    weight_sensitivity=[]
    for w in [.5,.7,.9]:
        z=qualified_scores.assign(weighted=w*qualified_scores.direct_mean+(1-w)*qualified_scores.indirect_mean).sort_values(['weighted','id']).iloc[0]
        weight_sensitivity.append({'direct_weight':w,'id':z.id,'hotspot':float(z.hotspot),'lambda':float(z['lambda']),'delta':float(z.delta),'score':float(z.weighted)})
    selection={'selected':selected,'development_score':float(qualified_scores.iloc[0].joint_score),
        'qualified_candidates':len(qualified_scores),'candidate_count':len(scores),'baseline_development':baseline,
        'development_weight_sensitivity':weight_sensitivity,'direct_leader_among_joint_gate_qualified':direct_leader,
        'indirect_leader_among_joint_gate_qualified':indirect_leader,'selected_before_validation_scores':True,
        'selection_time_UTC':dt.datetime.now(dt.timezone.utc).isoformat()}
    write_json('selection.json',selection)
    print('FROZEN_SELECTION',json.dumps(selected),flush=True)
    val_specs=score_specs(panel,'validation');dev_specs_full=score_specs(panel,'development')
    controls={'joint_selected':selected,'physical_reference':REFERENCE,
              'previous_h005':{'hotspot':.05,'lambda':1000,'delta':3},
              'direct_development_leader':next(c for c in configs if c['id']==direct_leader),
              'indirect_development_leader':next(c for c in configs if c['id']==indirect_leader)}
    predictions={};evaluations=[];coverage_rows=[];scalar=[]
    for name,config in controls.items():
        t,valid,active=prediction(data,config,ns);t[~panel.input_eligible.to_numpy()]=np.nan;predictions[name]=t
        for split,spec in [('development',dev_specs_full),('validation',val_specs)]:
            met,cov=evaluate(t,panel,spec);evaluations.append({'model':name,'split':split,**met})
            for (domain,comp,site),(value,n) in cov.items():coverage_rows.append({'model':name,'split':split,'domain':domain,'component':comp,'site':site,'n_eligible':n,'coverage':value})
        if name=='joint_selected':
            # Check each domain and temporal split, including active constraints when present.
            for domain,split in itertools.product(['direct','indirect'],['development','validation']):
                ix=np.flatnonzero(panel.domain.eq(domain)&panel.split.eq(split)&np.isfinite(t).all(axis=1))
                chosen=list(ix[np.linspace(0,len(ix)-1,min(3,len(ix)),dtype=int)])
                clipped=ix[active[ix]]
                if len(clipped):chosen.append(int(clipped[0]))
                for j in sorted(set(chosen)):
                    d={k:v[j] for k,v in data.items()};w=[]
                    for sat in ['e','i']:
                        vsa=np.abs(d['saa']-d['vaa_'+sat]);vsa=np.where(vsa>180,360-vsa,vsa)
                        a,b=ns['hotspot_layer'](d['lai'],config['hotspot'],d['vza_'+sat],d['sza'],vsa)
                        w.extend([d['emis_s']*a,d['emis_s']*(b-a),d['emis_v']*(1-b)])
                    w=np.stack(w,-1);re=planck(d['lst_e'])*w[...,:3].sum(-1);ri=planck(d['lst_i'])*w[...,3:].sum(-1)
                    sun,_=ns['solve_2x2_system_center'](re,ri,w[...,0],w[...,1]+w[...,2],w[...,3],w[...,4]+w[...,5])
                    shade,veg=ns['solve_constrained_vectorized2_center'](re-w[...,0]*sun,ri-w[...,3]*sun,w[...,1],w[...,2],w[...,4],w[...,5],sun,dif=config['delta'])
                    a,b,c=ns['solve_joint_center'](re,ri,w,np.array([sun,min(shade,sun),veg]),lmbda=config['lambda'])
                    gap=np.exp(-.5*d['lai'][2,2]/np.cos(np.radians(d['sza'][2,2])))
                    expected=inverse(np.array([a*gap+b*(1-gap),c,a,b]))-273.15
                    error=float(np.max(np.abs(expected-t[j])));assert error<1e-7
                    scalar.append({'site':panel.site[j],'time':str(panel.time[j]),'max_difference_K':error,'constraint_active':bool(active[j])})
    pd.DataFrame(evaluations).to_csv(OUT/'penalized_evaluation.csv',index=False);pd.DataFrame(coverage_rows).to_csv(OUT/'coverage.csv',index=False)
    base_val,base_valcov=evaluate(predictions['physical_reference'],panel,val_specs)
    chosen_val,chosen_valcov=evaluate(predictions['joint_selected'],panel,val_specs)
    norm=normalized(chosen_val,base_val);validation_score=.7*norm['direct_mean']+.3*norm['indirect_mean']
    violations=qualified(chosen_val,chosen_valcov,base_val,base_valcov)
    if validation_score>1.+1e-10:violations.append('validation_joint_score_worse_than_reference')
    sums,audit=validation_tables(predictions,panel)
    # Common-date conventional scores avoid interpreting coverage changes as accuracy gains.
    common_predictions={}
    common=np.isfinite(predictions['joint_selected']).all(axis=1)&np.isfinite(predictions['physical_reference']).all(axis=1)
    common_rows=[]
    for name in ['joint_selected','physical_reference']:
        values=projected(predictions[name],panel)
        for split,domain,comp in itertools.product(['development','validation'],['direct','indirect'],['soil','canopy']):
            eligible=common&panel.split.eq(split)&panel.domain.eq(domain)&panel[f'eligible_{comp}']
            p=panel.loc[eligible,['site','month','hour']].copy();p['reference']=panel.loc[eligible,f'{comp}_reference'];p['prediction']=values[comp][eligible]
            for sid,z in p.groupby('site'):
                for scale in ['instantaneous','monthly_hour']:
                    a=z if scale=='instantaneous' else z.groupby(['month','hour']).agg(reference=('reference','mean'),prediction=('prediction','mean'),n=('prediction','size')).query('n>=3')
                    if len(a)>=3:common_rows.append({'model':name,'split':split,'domain':domain,'component':comp,'site':sid,'scale':scale,'n':len(a),'rmse_K':float(np.sqrt(((a.prediction-a.reference)**2).mean()))})
    cm=pd.DataFrame(common_rows);cm.to_csv(OUT/'common_support_metrics.csv',index=False)
    cm.groupby(['model','split','domain','component','scale'],as_index=False).agg(mean_site_rmse_K=('rmse_K','mean'),sites=('site','size'),n=('n','sum')).to_csv(OUT/'common_support_summary.csv',index=False)
    saved=panel[['site','domain','time','split','year','month','hour']].copy()
    for j,b in enumerate(BANDS):saved[b]=predictions['joint_selected'][:,j]
    saved['valid']=np.isfinite(predictions['joint_selected']).all(axis=1)
    saved.to_csv(OUT/'selected_station_predictions.csv.gz',index=False)
    saved.loc[saved.valid].groupby(['site','domain','year','month','hour'],as_index=False).agg(**{b:(b,'mean') for b in BANDS},n_obs=('time','size')).to_csv(OUT/'selected_station_monthly_hour.csv.gz',index=False)
    result={'status':'completed','selected':selected,'retrospective_validation_passed':not violations,'validation_violations':violations,
        'validation_joint_normalized_score':float(validation_score),'validation_metrics':chosen_val,'reference_validation_metrics':base_val,
        'scalar_checks':scalar,'metric_recompute_audit':audit,'regional_production_unchanged':sha(paused)==paused_hash,
        'interpretation':'Configuration selected within a 240-candidate fixed architecture; indirect comparisons are not direct component accuracy; validation periods previously inspected.'}
    assert result['regional_production_unchanged'];write_json('result.json',result)
    write_json('selected_config.json',{'configuration':selected,'units':protocol['units'],'first_window':5,'second_window':5,'residual':'center',
        'selection_status':'selected_and_retrospectively_supported' if not violations else 'candidate_not_accepted_for_production',
        'postprocessing':'common physical input mask; center LAI>=0.05; all four outputs 250-350 K; no ground-error filtering',
        'scope':'station-cache experiment only; no regional production restarted'})
    write_json('progress.json',{'status':'completed','completed':240,'total':240})
    print('RESULT',json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
