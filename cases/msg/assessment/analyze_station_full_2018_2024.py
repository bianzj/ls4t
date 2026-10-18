"""Audit full station inversions and legacy scoring without tuning to references.

The archived legacy predictions are forensic evidence, not release products.
Air and soil-probe comparisons are indirect consistency evaluations.
"""
from pathlib import Path
import argparse, hashlib, json, re
import numpy as np
import pandas as pd
from validate_msg_5x5_europe import clean_ground, score, sha

HERE=Path(__file__).resolve().parent
PAPER=Path('C:/BaiduSyncdisk/research/ls4t_msg')
OUT=HERE.parent/'results/production_assessment/msg_5x5/station_direct_2018_2024'
ARCHIVE=Path('E:/PRODUCTS/LSCT_Site_Results_2018-2025_all.csv')
SAVED=Path('E:/PRODUCTS/VALIDATION/monthly_rmse_r2_4_groups.csv')
BANDS=['background_soil','canopy','sunlit_soil','shaded_soil']
COMPONENTS=[('background_soil','TS_1'),('canopy','TA'),('shaded_soil','TS_1')]

def save_json(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')

def dates(x):
    x=x.copy();x['time']=pd.to_datetime(x.timestamp.astype(str),format='%Y%m%d%H%M',utc=True)
    x['month']=x.time.dt.strftime('%Y%m');x['hour']=x.time.dt.hour;x['year']=x.time.dt.year
    return x

def ground_all(sites):
    ground={};manifest={};coverage=[]
    for sid in sites:
        p=Path(f'E:/field/ICOSETC_{sid}_METEO_L2/ICOSETC_{sid}_METEO_L2.csv')
        g,conflict=clean_ground(p);ground[sid]=g
        manifest[sid]={'path':str(p),'sha256':sha(p),'conflicting_duplicate_times':conflict}
        for year in range(2018,2026):
            z=g.loc[g.field_time.dt.year.eq(year)&g.field_time.dt.hour.between(11,16)]
            coverage.append({'site':sid,'year':year,'ground_rows_11_16':len(z),
                'valid_TA':int(z.TA.between(-23.15,76.85).sum()),'valid_TS1':int(z.TS_1.between(-23.15,76.85).sum())})
    pd.DataFrame(coverage).to_csv(OUT/'ground_coverage.csv',index=False)
    save_json('ground_manifest.json',manifest)
    return ground

def match(x,ground):
    rows=[]
    for sid,z in x.groupby('site'):
        a=pd.merge_asof(z.sort_values('time'),ground[sid],left_on='time',right_on='field_time',
                        direction='nearest',tolerance=pd.Timedelta(minutes=30))
        a['offset_minutes']=(a.time-a.field_time).dt.total_seconds()/60;rows.append(a)
    return pd.concat(rows,ignore_index=True)

def aggregate(x,scale):
    if scale=='instantaneous':return x.assign(n_raw=1)
    keys=['month']+(['hour'] if scale=='monthly_hour' else [])
    a=x.groupby(keys,as_index=False).agg(estimate=('estimate','mean'),reference=('reference','mean'),bulk=('bulk','mean'),n_raw=('reference','size'))
    return a.loc[a.n_raw>=3].copy()

def metrics(pairs,groupcols,scales=('instantaneous','monthly_calendar','monthly_hour')):
    rows=[]
    for key,x in pairs.groupby(groupcols,dropna=False):
        key=key if isinstance(key,tuple) else (key,)
        for scale in scales:
            a=aggregate(x,scale)
            for method in ['estimate','bulk']:
                rows.append({**dict(zip(groupcols,key)),'scale':scale,'method':method,**score(a.reference,a[method]),
                             'n_raw':int(a.n_raw.sum()),'enough_groups':len(a)>=3})
    return pd.DataFrame(rows)

def summary(met,keys):
    return met.loc[met.enough_groups].groupby(keys,as_index=False).agg(sites=('site','size'),
        mean_site_rmse_K=('rmse_K','mean'),mean_site_bias_K=('bias_K','mean'),total_pairs=('n','sum'),total_raw_pairs=('n_raw','sum'))

def paired(x,components=COMPONENTS):
    rows=[]
    for comp,ref in components:
        cols=[comp,ref,'bulk'];ok=x[cols].ge(-23.15).all(axis=1)&x[cols].le(76.85).all(axis=1)
        z=x.loc[ok,['site','timestamp','time','year','month','hour','model','field_time','offset_minutes',comp,ref,'bulk']].copy()
        z=z.rename(columns={comp:'estimate',ref:'reference'});z['component']=comp;rows.append(z)
    return pd.concat(rows,ignore_index=True)

def legacy_pairs(x,soil='shaded_soil',residual=True,bounds=(0,60),joint=True):
    rows=[];lo,hi=bounds
    jointcols=['canopy',soil,'TA','TS_1','bulk']
    jointok=x[jointcols].ge(lo).all(axis=1)&x[jointcols].le(hi).all(axis=1)
    for comp,ref in [(soil,'TS_1'),('canopy','TA')]:
        cols=[comp,ref,'bulk'];ok=jointok if joint else x[cols].ge(lo).all(axis=1)&x[cols].le(hi).all(axis=1)
        if residual:ok=ok&(x.canopy-x.TA).abs().le(10)&(x[soil]-x.TS_1).abs().le(10)
        z=x.loc[ok,['site','timestamp','time','year','month','hour',comp,ref,'bulk']].rename(columns={comp:'estimate',ref:'reference'}).copy()
        z['component']='soil' if comp==soil else 'canopy';rows.append(z)
    return pd.concat(rows,ignore_index=True)

def legacy_audit(archive,ground):
    a=match(dates(archive),ground);a=a.loc[a.hour.between(11,16)&a.year.between(2018,2025)].copy()
    saved=pd.read_csv(SAVED);saved.to_csv(OUT/'historical_saved_metrics.csv',index=False)
    replay=legacy_pairs(a);met=metrics(replay,['site','component'],('monthly_calendar',))
    met.to_csv(OUT/'historical_exact_protocol_replay_metrics.csv',index=False)
    replay.to_csv(OUT/'historical_exact_protocol_pairs.csv.gz',index=False)
    compare=[]
    for r in met.loc[met.method.eq('estimate')].itertuples():
        c='RMSE_TS_Soil' if r.component=='soil' else 'RMSE_TA_Vegetation'
        old=float(saved.loc[saved.Site.eq(r.site),c].iloc[0])
        compare.append({'site':r.site,'component':r.component,'saved_rmse_K':old,'replayed_rmse_K':r.rmse_K,
                        'difference_K':r.rmse_K-old,'replay_months':r.n})
    pd.DataFrame(compare).to_csv(OUT/'historical_saved_vs_replay.csv',index=False)
    variants=[('H0_original','shaded_soil',True,(0,60),True,'monthly_calendar'),
        ('H1_no_residual_filter','shaded_soil',False,(0,60),True,'monthly_calendar'),
        ('H2_wider_range','shaded_soil',False,(-23.15,76.85),True,'monthly_calendar'),
        ('H3_background_soil','background_soil',False,(-23.15,76.85),True,'monthly_calendar'),
        ('H4_separate_components','background_soil',False,(-23.15,76.85),False,'monthly_calendar'),
        ('H5_month_hour','background_soil',False,(-23.15,76.85),False,'monthly_hour'),
        ('H6_unique_timestamps','background_soil',False,(-23.15,76.85),False,'monthly_hour')]
    eu=a.loc[~a.site.str.startswith('CD-')&a.year.le(2024)].copy()
    allmetrics=[];retention=[]
    for name,soil,resid,bounds,joint,scale in variants:
        source=eu.drop_duplicates(['site','timestamp']) if name=='H6_unique_timestamps' else eu
        p=legacy_pairs(source,soil,resid,bounds,joint);m=metrics(p,['site','component'],(scale,));m['protocol']=name;allmetrics.append(m)
        for comp,z in p.groupby('component'):retention.append({'protocol':name,'component':comp,'raw_pairs':len(z),'sites':z.site.nunique()})
    allmetrics=pd.concat(allmetrics,ignore_index=True);allmetrics.to_csv(OUT/'historical_protocol_sensitivity_site.csv',index=False)
    s=summary(allmetrics,['protocol','component','scale','method']);s.to_csv(OUT/'historical_protocol_sensitivity.csv',index=False)
    pd.DataFrame(retention).to_csv(OUT/'historical_protocol_retention.csv',index=False)
    save_json('historical_audit.json',{'archive_sha256':sha(ARCHIVE),'saved_metric_sha256':sha(SAVED),
        'saved_15_soil_rmse_mean':float(saved.RMSE_TS_Soil.mean()),'saved_15_canopy_rmse_mean':float(saved.RMSE_TA_Vegetation.mean()),
        'saved_europe_14_soil_rmse_mean':float(saved.loc[~saved.Site.str.startswith('CD-'),'RMSE_TS_Soil'].mean()),
        'saved_europe_14_canopy_rmse_mean':float(saved.loc[~saved.Site.str.startswith('CD-'),'RMSE_TA_Vegetation'].mean()),
        'replay_max_abs_difference_K':float(pd.DataFrame(compare).difference_K.abs().max()),
        'replay_sites':int(met.site.nunique()),'archive_selected_rows_2018_2025':len(a),
        'max_ground_offset_minutes':float(a.offset_minutes.abs().max()),
        'caveat':'Replay uses present local reference files; original R chooses second alphabetic CSV; duplicate conflicts are marked missing here.'})
    return eu

def archive_fingerprint(pred,archive):
    old=archive.loc[archive.year.between(2018,2024)].copy()
    duplicate=old.loc[old.duplicated(['site','timestamp'],keep=False)]
    duplicate.to_csv(OUT/'historical_duplicate_records.csv.gz',index=False)
    old=old.drop_duplicates()
    assert not old.duplicated(['site','timestamp']).any()
    save_json('historical_duplicate_audit.json',{'duplicate_rows_including_first':len(duplicate),
        'identical_extra_rows_removed':int(len(duplicate)-len(duplicate.drop_duplicates())),
        'by_site_rows_including_first':{str(k):int(v) for k,v in duplicate.groupby('site').size().items()},
        'conflicting_duplicate_timestamps':0,'scope':'2018-2024',
        'policy':'Original-protocol replay keeps historical duplicates; parameter fingerprints deduplicate identical rows; H6 adds a unique-timestamp sensitivity.'})
    rows=[];yrrows=[]
    for (sid,model),x in pred.loc[pred.model.str.startswith('historical_raw_')].groupby(['site','model']):
        o=old.loc[old.site.eq(sid)];x=x.loc[x.valid]
        z=x.merge(o,on=['site','timestamp'],suffixes=('_new','_old'))
        for year,y in [('all',z)]+list(z.groupby('year_new')):
            a=y[[b+'_new' for b in BANDS]].to_numpy(dtype=float);b=y[[b+'_old' for b in BANDS]].to_numpy(dtype=float)
            good=np.isfinite(a).all(axis=1)&np.isfinite(b).all(axis=1);a=a[good];b=b[good]
            diff=np.abs(np.round(a,2)-b);row={'site':sid,'model':model,'year':year,'shared_all_four':len(a),
                'all_four_exact_rounded':int((diff<1e-7).all(axis=1).sum()),'all_four_within_001':int((diff<=.010001).all(axis=1).sum()),
                'max_difference_K':float(diff.max()) if len(a) else np.nan,
                'median_max_difference_K':float(np.median(diff.max(1))) if len(a) else np.nan}
            reasonable=(b>=-23.15).all(axis=1)&(b<=76.85).all(axis=1);d=diff[reasonable]
            row.update(reasonable_rows=int(reasonable.sum()),reasonable_all_exact=int((d<1e-7).all(axis=1).sum()),
                       reasonable_within_001=int((d<=.010001).all(axis=1).sum()))
            if year=='all':
                row.update(new_valid=len(x),archive_valid=len(o),new_only=len(x)-len(z),archive_only=len(o)-len(z));rows.append(row)
            else:yrrows.append(row)
    pd.DataFrame(rows).to_csv(OUT/'original_parameter_fingerprint.csv',index=False)
    pd.DataFrame(yrrows).to_csv(OUT/'original_parameter_fingerprint_by_year.csv',index=False)

def input_audit(completes):
    rows=[];static=[];inventory=[]
    for f,c in completes:
        with np.load(f.parent/'input_cache.npz') as cache:
            n=cache['lai'].shape[0]
            for k in ['vza_e','vaa_e','vza_i','vaa_i','emis_s','emis_v','lat','lon']:
                a=cache[k][0];static.append({'site':c['site'],'year':c['year'],'variable':k,'center':float(a[2,2]),'min':float(np.nanmin(a)),'max':float(np.nanmax(a))})
            for k in ['lai','sza','saa','lst_e_raw','lst_i_raw']:
                a=cache[k][:,2,2];good=a[np.isfinite(a)]
                rows.append({'site':c['site'],'year':c['year'],'variable':k,'n':n,'finite_n':len(good),
                    'min':float(np.min(good)) if len(good) else np.nan,'p05':float(np.quantile(good,.05)) if len(good) else np.nan,
                    'median':float(np.median(good)) if len(good) else np.nan,'p95':float(np.quantile(good,.95)) if len(good) else np.nan,
                    'max':float(np.max(good)) if len(good) else np.nan,
                    'raw_dtype':c['input_raw_dtypes'].get(k[4], '') if k.startswith('lst_') else '',
                    'center_ge_32768':int((a>=32768).sum()) if k.startswith('lst_') else 0})
    pd.DataFrame(rows).to_csv(OUT/'station_dynamic_input_parameters.csv',index=False)
    st=pd.DataFrame(static);st.to_csv(OUT/'station_static_input_parameters.csv',index=False)
    for (sid,k),z in st.groupby(['site','variable']):assert z.center.nunique(dropna=False)==1,(sid,k)
    for p in HERE.glob('msg_lsct3.2-iter*.py'):
        txt=p.read_text(encoding='utf8')
        for i,line in enumerate(txt.splitlines(),1):
            if re.match(r'^(wavelength|hspot_val|lmbda_val|dif|TARGET_HOURS)\s*=',line):
                inventory.append({'source':str(p),'sha256':sha(p),'line':i,'declaration':line.strip()})
    pd.DataFrame(inventory).to_csv(OUT/'source_parameter_inventory.csv',index=False)

def common_controls(matches):
    combinations=[('hotspot_physical','physical_h005','physical_h025'),
        ('units_h005','physical_h005','legacy_units_h005'),('units_h025','physical_h025','legacy_units_h025'),
        ('input_decode_and_mask_h025','legacy_units_h025','historical_raw_h025'),
        ('combined_new_vs_historical','physical_h005','historical_raw_h025')]
    rows=[];temperature_changes=[]
    for label,m1,m2 in combinations:
        a=matches.loc[matches.model.eq(m1)&matches.hour.between(11,16)]
        b=matches.loc[matches.model.eq(m2),['site','timestamp',*BANDS]]
        z=a.merge(b,on=['site','timestamp'],suffixes=('','_other'))
        for comp,ref in COMPONENTS:
            cols=[comp,comp+'_other',ref,'bulk'];ok=z[cols].ge(-23.15).all(axis=1)&z[cols].le(76.85).all(axis=1)
            for sid,v in z.loc[ok].groupby('site'):
                d=v[comp]-v[comp+'_other']
                temperature_changes.append({'comparison':label,'site':sid,'component':comp,'model_a':m1,'model_b':m2,
                    'n':len(d),'mean_A_minus_B_K':float(d.mean()),'median_A_minus_B_K':float(d.median()),
                    'p05_A_minus_B_K':float(d.quantile(.05)),'p95_A_minus_B_K':float(d.quantile(.95))})
            for model,col in [(m1,comp),(m2,comp+'_other')]:
                p=z.loc[ok,['site','month','hour',col,ref,'bulk']].rename(columns={col:'estimate',ref:'reference'})
                p['component']=comp;p['model']=model;m=metrics(p,['site','component','model']);m['comparison']=label;rows.append(m)
    met=pd.concat(rows,ignore_index=True);met.to_csv(OUT/'common_support_controls_site.csv',index=False)
    summary(met,['comparison','component','model','scale','method']).to_csv(OUT/'common_support_controls.csv',index=False)
    pd.DataFrame(temperature_changes).to_csv(OUT/'common_support_temperature_changes.csv',index=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--historical-only',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    inventory=pd.read_csv('E:/field/sites-2025-selected.csv');all_sites=inventory.id.tolist()
    ground=ground_all(all_sites)
    archive=pd.read_csv(ARCHIVE,dtype={'DateTime':str}).rename(columns={'Site':'site','DateTime':'timestamp','LST_Euro':'bulk',
        'T_Soil':'background_soil','T_Vegetation':'canopy','T_Sunlit_Soil':'sunlit_soil','T_Shaded_Soil':'shaded_soil'})
    archive=dates(archive.loc[archive.site.isin(all_sites)]);legacy_audit(archive,ground)
    if args.historical_only:
        print((OUT/'historical_audit.json').read_text(),flush=True);return
    progress=json.loads((OUT/'progress.json').read_text());assert progress['status']=='completed' and progress['jobs_completed']==98
    files=sorted((OUT/'partitions').glob('*/*/complete.json'));assert len(files)==98
    completes=[(p,json.loads(p.read_text())) for p in files];frames=[];coverage=[];scalar=[];failures=[]
    for p,c in completes:
        assert sha(p.parent/'predictions.csv.gz')==c['predictions_sha256']
        assert sha(p.parent/'input_cache.npz')==c['cache_sha256']
        assert sha(p.parent/'input_manifest.jsonl')==c['input_manifest_sha256']
        z=pd.read_csv(p.parent/'predictions.csv.gz',dtype={'timestamp':str});frames.append(z)
        failed=pd.read_csv(p.parent/'input_failures.csv.gz',dtype={'timestamp':str})
        for reason,f in failed.groupby('reason'):
            failures.append({'site':c['site'],'year':c['year'],'reason':reason,'count':len(f),
                'unit':'day_without_any_EURO_file' if reason=='no_EURO_files_for_day' else 'cached_timestamp'})
        coverage.append({'site':c['site'],'year':c['year'],'input_center_pairs':c['input_center_pairs'],
            'failed_input_timestamps':c['failed_input_timestamps'],**c['valid_by_model']})
        scalar.extend([{'site':c['site'],'year':c['year'],**r} for r in c['scalar_checks']])
    pred=dates(pd.concat(frames,ignore_index=True))
    # Empty station-years otherwise promote numeric columns to object dtype.
    for c in BANDS+['bulk','sza','lai']:pred[c]=pd.to_numeric(pred[c],errors='raise')
    assert set(pred.valid.unique()).issubset({True,False})
    pred['valid']=pred.valid.astype(bool)
    assert not pred.duplicated(['site','timestamp','model']).any()
    pred.to_csv(OUT/'station_predictions_all_models.csv.gz',index=False)
    primary=pred.loc[pred.model.eq('physical_h005')&pred.valid].copy()
    primary.to_csv(OUT/'station_instantaneous_primary.csv.gz',index=False)
    # Product monthly means use all retrieval dates, independent of ground availability.
    product=primary.groupby(['site','year','month','hour'],as_index=False).agg(**{k:(k,'mean') for k in BANDS},n_obs=('timestamp','size'))
    product['at_least_3_observations']=product.n_obs.ge(3);product.to_csv(OUT/'station_monthly_hour_primary.csv.gz',index=False)
    pd.DataFrame(coverage).to_csv(OUT/'retrieval_coverage_by_year.csv',index=False)
    pd.DataFrame(failures).to_csv(OUT/'input_failure_summary.csv',index=False)
    pd.DataFrame(scalar).to_csv(OUT/'scalar_replay_checks.csv',index=False)
    archive_fingerprint(pred,archive);input_audit(completes)
    matches=match(pred,ground);pairs=paired(matches)
    pairs.to_csv(OUT/'matched_observations_all_models.csv.gz',index=False)
    met=[]
    for scope,p in [('all_available_hours',pairs),('11_16_UTC',pairs.loc[pairs.hour.between(11,16)])]:
        m=metrics(p,['site','component','model']);m['hours_scope']=scope;met.append(m)
    met=pd.concat(met,ignore_index=True);met.to_csv(OUT/'station_metrics.csv',index=False)
    sums=summary(met,['hours_scope','component','model','scale','method']);sums.to_csv(OUT/'summary.csv',index=False)
    byyear=metrics(pairs.loc[pairs.hour.between(11,16)&pairs.model.eq('physical_h005')],['site','year','component','model'])
    byyear.to_csv(OUT/'primary_metrics_by_year.csv',index=False)
    summary(byyear,['year','component','model','scale','method']).to_csv(OUT/'primary_summary_by_year.csv',index=False)
    common_controls(matches)
    # Audit primary monthly means and scores independently from saved paired rows.
    errors=[];saved=pd.read_csv(OUT/'matched_observations_all_models.csv.gz')
    for r in met.loc[met.model.eq('physical_h005')].itertuples():
        z=saved.loc[saved.site.eq(r.site)&saved.component.eq(r.component)&saved.model.eq(r.model)]
        if r.hours_scope=='11_16_UTC':z=z.loc[z.hour.between(11,16)]
        col='estimate' if r.method=='estimate' else 'bulk'
        if r.scale!='instantaneous':
            key=['month']+(['hour'] if r.scale=='monthly_hour' else []);group=z.groupby(key);z=group[[col,'reference']].mean().loc[group.size()>=3]
        assert len(z)==r.n
        if len(z):errors.append(abs(float(np.sqrt(((z[col]-z.reference)**2).mean()))-r.rmse_K))
    assert max(errors,default=0)<1e-9
    ph=primary.groupby(['site','month','hour'])[BANDS].mean();back=pd.read_csv(OUT/'station_monthly_hour_primary.csv.gz',dtype={'month':str}).set_index(['site','month','hour'])
    assert np.allclose(ph,back.loc[ph.index,BANDS],rtol=0,atol=1e-10)
    paused=json.loads(Path('E:/PRODUCTS/LSCT/MSG_5X5_PHYSICAL_V1/status.json').read_text(encoding='utf-8-sig'));assert paused['status']=='paused'
    result={'status':'completed','sites':14,'years':list(range(2018,2025)),'jobs_completed':98,
        'primary_valid_instantaneous':len(primary),'primary_sites_with_results':int(primary.site.nunique()),
        'primary_month_hour_groups':len(product),'primary_month_hour_groups_n_ge_3':int(product.at_least_3_observations.sum()),
        'scalar_checks':len(scalar),'max_physical_scalar_difference_K':max([r['max_error_K'] for r in scalar if r['model']=='physical_h005'],default=0),
        'max_legacy_scalar_difference_K':max([r['max_error_K'] for r in scalar if r['model']=='historical_raw_h025'],default=0),
        'primary_metric_rows_verified':len(errors),'max_metric_recompute_difference_K':max(errors,default=0),
        'max_ground_offset_minutes':float(pairs.offset_minutes.abs().max()),'regional_production_status':paused['status'],
        'analysis_sha256':sha(__file__)}
    save_json('result.json',result);print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    print(sums.loc[sums.hours_scope.eq('11_16_UTC')&sums.model.eq('physical_h005')].to_string(index=False),flush=True)

if __name__=='__main__':main()
