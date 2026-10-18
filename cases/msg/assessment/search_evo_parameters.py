"""Frozen, date-blocked EVO parameter experiment; never writes production data.

Legacy R04 is replay-checked before comparing physically consistent Planck
implementations. Selection uses Aug-Oct only, equal component/month weights,
and explicit missing-prediction penalties. Nov-Dec is evaluated after freezing
the winner. This is single-site exploration, not external product validation.
"""
from pathlib import Path
import argparse, datetime as dt, hashlib, itertools, json, sys
import numpy as np
import pandas as pd
from osgeo import gdal
from scipy.ndimage import uniform_filter
from validate_existing_evo_grid import correction, sha256

ROOT = Path('C:/work/ls4t-msg')
SOURCE = ROOT/'cases/official/implementation/msg_lsct3.2-iter-site-cons-ig-center.py'
PAPER = ROOT/'cases/official/results'
SITE = Path('E:/PRODUCTS/SITE/Evora')
C1, C2, WL = 2*6.62607015e-34*299792458**2, 6.62607015e-34*299792458/1.380649e-23, 10.5e-6


def planck(t, mode='physical'):
    t=np.asarray(t,dtype=float)
    if mode=='legacy':
        return 1.191042972e-16/(10.5**5*(np.exp(.01438776877/t/10.5)-1))*10000
    return C1/(WL**5*np.expm1(C2/(WL*t)))*1e-6


def inverse(r, mode='physical'):
    with np.errstate(invalid='ignore',divide='ignore'):
        if mode=='legacy':
            x=1.191042972e-12/(r*10.5**5)+1
            return np.where(x>1,.01438776877/(10.5*np.log(x)),np.nan)
        return np.where(r>0,C2/(WL*np.log1p(C1*1e-6/(WL**5*r))),np.nan)


def solve(r1,r2,a1,b1,a2,b2,size=5,spatial=False):
    valid=np.isfinite(r1)&np.isfinite(r2)&np.isfinite(a1)&np.isfinite(b1)&np.isfinite(a2)&np.isfinite(b2)
    terms=[a1*a1+a2*a2,a1*b1+a2*b2,b1*b1+b2*b2,a1*r1+a2*r2,b1*r1+b2*r2]
    def total(x):
        x=np.where(valid,x,0.)
        if spatial:
            return uniform_filter(x,size=(1,size,size),mode='nearest')*size**2
        s=slice(2-size//2,3+size//2)
        return x[:,s,s].sum(axis=(1,2))
    aa,ab,bb,d1,d2=[total(x) for x in terms]
    count=total(np.ones_like(r1))
    det=aa*bb-ab*ab
    with np.errstate(invalid='ignore',divide='ignore'):
        x=(d1*bb-d2*ab)/det;y=(d2*aa-d1*ab)/det
    center_valid=valid if spatial else valid[:,2,2]
    good=(np.abs(det)>=1e-8)&(count>=size*size*.4)&(x>=0)&(y>=0)&center_valid
    return np.where(good,x,np.nan),np.where(good,y,np.nan)


def prepare(data,hspot,mode,window,residual,hotspot):
    vsa_e=np.abs(data['saa']-data['vaa_e']);vsa_e=np.where(vsa_e>180,360-vsa_e,vsa_e)
    vsa_i=np.abs(data['saa']-data['vaa_i']);vsa_i=np.where(vsa_i>180,360-vsa_i,vsa_i)
    with np.errstate(all='ignore'):
        w1,b1=hotspot(data['lai'],hspot,data['vza_e'],data['sza'],vsa_e)
        w2,b2=hotspot(data['lai'],hspot,data['vza_i'],data['sza'],vsa_i)
    w=np.stack([data['emis_s']*w1,data['emis_s']*(b1-w1),data['emis_v']*(1-b1),
                data['emis_s']*w2,data['emis_s']*(b2-w2),data['emis_v']*(1-b2)],axis=-1)
    re=planck(data['lst_e'],mode)*w[...,:3].sum(axis=-1)
    ri=planck(data['lst_i'],mode)*w[...,3:].sum(axis=-1)
    first,_=solve(re,ri,w[...,0],w[...,1]+w[...,2],w[...,3],w[...,4]+w[...,5],size=window,spatial=residual=='local_vector')
    if residual=='center':
        first_center=first;first=first[:,None,None]
    else:
        first_center=first[:,2,2]
    rre=re-w[...,0]*first;rri=ri-w[...,3]*first
    shaded,canopy=solve(rre,rri,w[...,1],w[...,2],w[...,4],w[...,5],size=5)
    return w[:,2,2],re[:,2,2],ri[:,2,2],rre[:,2,2],rri[:,2,2],first_center,shaded,canopy


def retrieve(pre,data,lmbda,delta,mode='physical',cap=False,return_raw=False):
    w,re,ri,rre,rri,sun,shade,veg=pre
    shade,veg=shade.copy(),veg.copy()
    a,b,c,d=w[:,1],w[:,2],w[:,4],w[:,5]
    e,f=a+b,c+d
    vc=(e*(rre-a*delta)+f*(rri-c*delta))/(e*e+f*f+1e-9);sc=vc+delta
    vd=(e*(rre+a*delta)+f*(rri+c*delta))/(e*e+f*f+1e-9);sd=vd-delta
    ec=(rre-a*sc-b*vc)**2+(rri-c*sc-d*vc)**2
    ed=(rre-a*sd-b*vd)**2+(rri-c*sd-d*vd)**2
    violate=np.abs(shade-veg)>delta
    shade=np.where(violate,np.where(ec<=ed,sc,sd),shade)
    veg=np.where(violate,np.where(ec<=ed,vc,vd),veg)
    shade=np.minimum(shade,sun)
    if cap:
        veg=np.where(veg>planck(350.,mode),shade,veg)
    prior=np.stack([sun,shade,veg],axis=-1)
    A=np.stack([w[:,:3],w[:,3:]],axis=1)
    lhs=np.einsum('nki,nkj->nij',A,A)+lmbda*np.eye(3)
    rhs=np.einsum('nki,nk->ni',A,np.stack([re,ri],axis=-1))+lmbda*prior
    final=np.linalg.solve(lhs,rhs[...,None])[...,0]
    final[:,1]=np.minimum(final[:,1],final[:,0])
    gap=np.exp(-.5*data['lai'][:,2,2]/np.cos(np.radians(data['sza'][:,2,2])))
    soil=final[:,0]*gap+final[:,1]*(1-gap)
    # Four-band product order: background, canopy, sunlit, shaded.
    temps=inverse(np.stack([soil,final[:,2],final[:,0],final[:,1]],axis=-1),mode)
    valid=np.isfinite(temps).all(axis=1)&(temps>=250).all(axis=1)&(temps<=350).all(axis=1)
    if return_raw:return temps,valid,violate
    target=temps[:,[2,1]]-273.15
    target[~valid]=np.nan
    return target,valid,violate


def load_data(out):
    field=Path('E:/field/Evo-2017.csv')
    g=pd.read_csv(field)
    g['time']=pd.to_datetime(g.Time,format='%d/%m/%Y %H:%M',utc=True)
    g=g.loc[(g.time>='2017-08-01')&(g.time<'2017-12-31')&g.time.dt.hour.between(10,16)&g.time.dt.minute.eq(0)].copy()
    assert not g.time.duplicated().any()
    for c in ['Ts','Tcrown']:
        g[c]=pd.to_numeric(g[c],errors='coerce')
        g.loc[~g[c].between(-23.15,76.85),c]=np.nan
        g[c]=correction(g[c])
    manifest={}
    def read(p):
        d=gdal.Open(str(p));a=d.ReadAsArray().astype(float);d=None
        assert a.shape==(5,5),str(p)
        manifest[str(p)]={'sha256':sha256(p),'bytes':p.stat().st_size}
        return a
    data={x:read(SITE/'static'/f'{x}.tif')[None] for x in ['vza_e','vaa_e','vza_i','vaa_i','emis_s','emis_v']}
    arrays={x:[] for x in ['lst_e','lst_i','sza','saa','lai']};rows=[];missing=[];lai_cache={}
    for _,row in g.iterrows():
        t=row.time;stamp=t.strftime('%Y%m%d%H%M');day=t.strftime('%Y%m%d');directory=SITE/t.strftime('%Y/%m/%d')
        paths={'lst_e':directory/f'LST_{stamp}_e.tif','lst_i':directory/f'LST_{stamp}_i.tif',
               'sza':directory/f'SZA_{stamp}.tif','saa':directory/f'SAA_{stamp}.tif','lai':directory/f'LAI_{day}.tif'}
        if not all(p.is_file() for p in paths.values()):
            missing.append(stamp);continue
        if day not in lai_cache:lai_cache[day]=read(paths['lai'])
        for k,p in paths.items():
            a=lai_cache[day] if k=='lai' else read(p)
            if k.startswith('lst'):
                a=np.where(a==0,np.nan,a/100+273.15)
            arrays[k].append(a)
        rows.append({'time':t,'soil_reference':row.Ts,'canopy_reference':row.Tcrown})
    data.update({k:np.stack(v) for k,v in arrays.items()})
    panel=pd.DataFrame(rows)
    obs=panel[['soil_reference','canopy_reference']].to_numpy()
    eligible=np.isfinite(obs).all(axis=1)&(obs>=-23.15).all(axis=1)&(obs<=76.85).all(axis=1)
    for k in ['lst_e','lst_i']:
        eligible &= np.isfinite(data[k][:,2,2])&(data[k][:,2,2]>=250)&(data[k][:,2,2]<=350)
    eligible &= np.isfinite(data['sza'][:,2,2])&(data['sza'][:,2,2]>=0)&(data['sza'][:,2,2]<90)&(data['lai'][:,2,2]>=.05)
    panel['eligible']=eligible
    panel['split']=np.where(panel.time.dt.month<=10,'development','holdout')
    panel.to_csv(out/'frozen_reference_panel.csv',index=False)
    (out/'input_manifest.json').write_text(json.dumps({'field_sha256':sha256(field),'files':manifest,'missing_timestamps':missing},indent=2),encoding='utf-8')
    np.savez_compressed(out/'input_cache.npz',**data)
    return data,panel,eligible,manifest


def metrics(pred,panel,mask):
    obs=panel[['soil_reference','canopy_reference']].to_numpy()
    ok=np.isfinite(pred).all(axis=1)&mask
    months=panel.time.dt.month.to_numpy()
    errs=pred-obs
    # Fixed-panel failures count as a predeclared 20 K error for each component.
    loss=np.where(np.isfinite(errs),errs**2,400.)
    macro=[loss[mask&(months==m)].mean(axis=0) for m in sorted(set(months[mask]))]
    objective=float(np.sqrt(np.mean(macro)))
    result={'eligible_n':int(mask.sum()),'valid_n':int(ok.sum()),'coverage':float(ok.sum()/mask.sum()),
            'penalized_macro_rmse_K':objective}
    for b,component in enumerate(['sunlit_soil','canopy']):
        e=errs[ok,b]
        result[component+'_raw_rmse_K']=float(np.sqrt(np.mean(e*e))) if len(e) else None
        result[component+'_raw_bias_K']=float(e.mean()) if len(e) else None
        z=pd.DataFrame({'time':panel.time[ok],'reference':obs[ok,b],'prediction':pred[ok,b]})
        z['month']=z.time.dt.month;z['hour']=z.time.dt.hour
        m=z.groupby(['month','hour']).agg(reference=('reference','mean'),prediction=('prediction','mean'),n=('reference','size'))
        m=m.loc[m.n>=2];e=m.prediction-m.reference
        result[component+'_monthly_n']=len(m)
        result[component+'_monthly_rmse_K']=float(np.sqrt(np.mean(e*e))) if len(e) else None
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if (out/'selection.json').exists():raise FileExistsError('Selection already frozen; do not adaptively rerank using holdout.')
    protocol={'created_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),'source':str(SOURCE),'source_sha256':sha256(SOURCE),
              'development_months':[8,9,10],'holdout_months':[11,12],
              'grid':{'hspot':[.05,.1,.15,.2,.25,.3,.4,.5],'lambda':[.01,.1,1,10,100,1000],
                      'delta_radiance':[.5,1,2,3,5],'first_window':[3,5],'residual':['center','local_vector']},
              'second_window':5,'search_planck':'SI, wavelength 10.5e-6 m; output W m-2 sr-1 um-1',
              'selection':'Lowest equal-month/equal-component raw penalized RMSE on Aug-Oct; failed predictions cost 20 K per component',
              'coverage_gate':'development coverage >= max(0.80, physical R04 baseline coverage - 0.01)',
              'postprocess':'shaded <= sunlit; all four output temperatures must be 250-350 K; no residual filtering',
              'local_vector_boundary':'nearest padding on cached 5x5 inputs; implementation sensitivity, not full-regional reproduction',
              'holdout_caveat':'Nov-Dec excluded from this parameter selection, but earlier aggregate analyses included these dates; not a never-seen external dataset',
              'units_source':'https://www.nist.gov/si-redefinition/definitions-si-base-units',
              'planck_source':'https://cie.co.at/eilvterm/17-24-005'}
    (out/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2),encoding='utf-8')
    sys.path.insert(0,str(ROOT));ns={}
    exec(compile(SOURCE.read_text(encoding='utf-8').split('# ================= 主程序')[0],str(SOURCE),'exec'),ns)
    data,panel,eligible,manifest=load_data(out)
    obs=panel[['soil_reference','canopy_reference']].to_numpy()
    dev=eligible&panel.time.dt.month.le(10).to_numpy();test=eligible&panel.time.dt.month.ge(11).to_numpy()
    print('FROZEN PANEL',int(dev.sum()),int(test.sum()),flush=True)
    # Verify batch math against the actual historical entry, not a mirror test.
    legacy_pre=prepare(data,.25,'legacy',5,'center',ns['hotspot_layer'])
    legacy_temp,legacy_valid,_=retrieve(legacy_pre,data,1000,3,'legacy',return_raw=True)
    recorded=pd.read_csv(PAPER/'production_assessment/evora_5x5/station_replay/station_predictions.csv')
    recorded['time']=pd.to_datetime(recorded.DateTime.astype(str),format='%Y%m%d%H%M',utc=True)
    rawcols=['T_Soil','T_Vegetation','T_Sunlit_Soil','T_Shaded_Soil']
    generated=pd.DataFrame(np.round(legacy_temp-273.15,2),columns=rawcols);generated['time']=panel.time
    shared=generated.merge(recorded[['time',*rawcols]],on='time',suffixes=('_batch','_entry'))
    differences=np.stack([shared[c+'_batch']-shared[c+'_entry'] for c in rawcols],axis=-1)
    assert np.isfinite(differences).all() and np.max(np.abs(differences))<=.0100001
    reproduction={'shared_records':len(shared),'all_four_exact':int(np.all(np.abs(differences)<1e-8,axis=1).sum()),
                  'maximum_code_difference_K':float(np.max(np.abs(differences)))}
    # An independent looped call checks the physical batch pathway at real dates.
    physical_pre=prepare(data,.25,'physical',5,'center',ns['hotspot_layer'])
    baseline,bv,_=retrieve(physical_pre,data,1000,3)
    coverage_floor=max(.8,metrics(baseline,panel,dev)['coverage']-.01)
    print('physical baseline',metrics(baseline,panel,dev),'coverage floor',coverage_floor,flush=True)
    for t in [250.,273.15,300.,350.]:
        assert abs(float(inverse(planck(t)))-t)<1e-9
    audit={'legacy_B300':float(planck(300.,'legacy')),'physical_B300_W_m2_sr_um':float(planck(300.)),
           'legacy_reproduction':reproduction,'source_constants':{'c1':ns['planck_c1'],'c2':ns['planck_c2'],'wavelength_argument':10.5}}
    (out/'unit_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    results=[];predictions=[];configs=[]
    for h,window,residual in itertools.product(protocol['grid']['hspot'],[3,5],['center','local_vector']):
        pre=prepare(data,h,'physical',window,residual,ns['hotspot_layer'])
        for delta,lmbda in itertools.product(protocol['grid']['delta_radiance'],protocol['grid']['lambda']):
            pred,valid,violate=retrieve(pre,data,lmbda,delta)
            cfg={'id':f'P{len(configs)+1:04d}','hspot':h,'lambda':lmbda,'delta_radiance':delta,'first_window':window,'residual':residual}
            met=metrics(pred,panel,dev)
            met['qualified']=met['coverage']>=coverage_floor
            met['development_constraint_trigger_fraction']=float(violate[dev].mean())
            results.append({**cfg,**met});predictions.append(pred);configs.append(cfg)
        print('searched',len(configs),'hspot',h,'window',window,'residual',residual,flush=True)
    scores=pd.DataFrame(results);scores.to_csv(out/'development_grid_scores.csv',index=False)
    qualified=scores.loc[scores.qualified].sort_values(['penalized_macro_rmse_K','id'])
    if qualified.empty:raise RuntimeError('No candidate satisfies frozen coverage requirements.')
    winner_id=qualified.iloc[0]['id'];index=next(i for i,c in enumerate(configs) if c['id']==winner_id)
    selection={'selected':configs[index],'development':results[index],'coverage_floor':coverage_floor,
               'selection_time_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),
               'selected_without_holdout_scores':True,'grid_candidates':len(configs),
               'qualified_candidates':int(scores.qualified.sum())}
    (out/'selection.json').write_text(json.dumps(selection,indent=2),encoding='utf-8')
    # Holdout calculations occur only below the persisted selection.
    winner=predictions[index]
    np.savez_compressed(out/'candidate_predictions.npz',predictions=np.stack(predictions),ids=np.array([c['id'] for c in configs]))
    legacy_target=legacy_temp[:,[2,1]]-273.15;legacy_target[~legacy_valid]=np.nan
    variant_predictions={'R04_legacy_units':legacy_target,'B01_physical_R04':baseline,'OPT_selected':winner}
    # One-factor controls around the physically corrected baseline, frozen before comparing holdout.
    controls=[('A01_lambda100',.25,5,'center',100,3,False),('A02_hotspot020',.2,5,'center',1000,3,False),
              ('A03_window3',.25,3,'center',1000,3,False),('A04_local_residual',.25,5,'local_vector',1000,3,False),
              ('A05_cap350',.25,5,'center',1000,3,True),('A06_regional_like_patch',.2,3,'local_vector',100,3,True)]
    for label,h,w,res,lam,delta,cap in controls:
        pre=prepare(data,h,'physical',w,res,ns['hotspot_layer'])
        variant_predictions[label]=retrieve(pre,data,lam,delta,cap=cap)[0]
    evaluations=[];prediction_rows=[]
    for label,pred in variant_predictions.items():
        for split,mask in [('development',dev),('holdout',test)]:
            evaluations.append({'variant':label,'split':split,**metrics(pred,panel,mask)})
        for k,component in enumerate(['sunlit_soil','canopy']):
            prediction_rows.append(pd.DataFrame({'time':panel.time,'split':panel.split,'eligible':eligible,
                                  'variant':label,'component':component,'reference':obs[:,k],'prediction':pred[:,k]}))
    pd.DataFrame(evaluations).to_csv(out/'controlled_comparisons.csv',index=False)
    pd.concat(prediction_rows,ignore_index=True).to_csv(out/'selected_and_control_predictions.csv',index=False)
    # Date-block bootstrap of frozen-test penalized MSE, selected minus physical baseline.
    loss_w=np.where(np.isfinite(winner), (winner-obs)**2,400.).mean(axis=1)
    loss_b=np.where(np.isfinite(baseline),(baseline-obs)**2,400.).mean(axis=1)
    block=pd.DataFrame({'date':panel.time.dt.strftime('%Y-%m-%d'),'delta':loss_w-loss_b}).loc[test].groupby('date').delta.mean().to_numpy()
    rng=np.random.default_rng(20261008)
    boot=np.array([rng.choice(block,len(block),replace=True).mean() for _ in range(2000)])
    bootstrap={'quantity':'date-mean penalized MSE difference (selected minus physical R04), K^2; distinct from equal-month selection score',
               'dates':len(block),'mean':float(block.mean()),'ci95':np.quantile(boot,[.025,.975]).tolist(),'resamples':2000}
    report={'status':'completed','script_sha256':sha256(__file__),'protocol':protocol,'unit_audit':audit,
            'selection':selection,'comparisons':evaluations,'test_date_block_bootstrap':bootstrap,
            'eligible_development':int(dev.sum()),'eligible_holdout':int(test.sum()),
            'limits':['Single site and partial 2017; candidate optimum only within the predefined grid.',
                      'Station input geometry and ground time convention not independently resolved.',
                      'Past exploratory work already saw aggregate statistics spanning the present holdout.',
                      'Cached local_vector padding is not full-regional retrieval; no archive reprocessing authorized by a low score alone.',
                      'Current R04 has inconsistent Planck wavelength units and is not a physically valid optimization target.']}
    (out/'search_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print('SELECTED',json.dumps(selection),flush=True)
    print('EVALUATION',json.dumps(evaluations),flush=True)
    print('BOOTSTRAP',json.dumps(bootstrap),flush=True)


if __name__=='__main__':
    main()
