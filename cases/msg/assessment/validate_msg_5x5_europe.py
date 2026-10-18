"""Evaluate produced regional 5x5 pixels at selected European ICOS stations.

Read-only production access. Soil-probe and air temperature are indirect
references. Comparisons use common timestamp support without residual filtering.
"""
from pathlib import Path
import hashlib,json,datetime as dt
import h5py
import numpy as np
import pandas as pd
from osgeo import gdal

ROOT=Path('E:/PRODUCTS/LSCT/MSG_5X5_PHYSICAL_V1')
OUT=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/msg_5x5/europe_validation')
HOURS=list(range(11,17))
BANDS=['background_soil','canopy','sunlit_soil','shaded_soil']


def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def score(obs,pred):
    e=np.asarray(pred)-np.asarray(obs)
    return {'n':len(e),'rmse_K':float(np.sqrt(np.mean(e*e))) if len(e) else None,
            'bias_K':float(np.mean(e)) if len(e) else None,'mae_K':float(np.mean(np.abs(e))) if len(e) else None}


from icos_time import clean_ground


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    status_before=sha(ROOT/'status.json')
    status=json.loads((ROOT/'status.json').read_text(encoding='utf-8-sig'))
    assert status['status']=='paused','Production must remain paused during this fixed snapshot'
    invpath=Path('E:/field/sites-2025-selected.csv');inventory=pd.read_csv(invpath)
    sites=inventory.loc[inventory.id.str[:3].isin(['CZ-','DE-','FI-','FR-','IT-','SE-'])].copy()
    assert len(sites)==14
    files=sorted((ROOT/'INSTANTANEOUS').rglob('*.h5'))
    files=[p for p in files if p.stem[-12:-8]>='2018' and int(p.stem[-4:-2]) in HOURS]
    monthfiles=sorted((ROOT/'MONTHLY_HOUR').rglob('*.h5'))
    months={}
    for p in monthfiles:
        with h5py.File(p) as f:
            m=str(f.attrs['month']);h=int(f.attrs['hour_UTC'])
            if int(m[:4])>=2018 and h in HOURS:months.setdefault(m,set()).add(h)
    complete_months=sorted(m for m,hs in months.items() if hs==set(HOURS))
    assert complete_months
    with h5py.File(files[0]) as f:
        gt=tuple(f.attrs['GeoTransform']);pr=f.attrs['Projection'];_,H,W=f['data'].shape
        protocol_hash=f.attrs['protocol_hash'];code_hash=f.attrs['code_sha256']
    assert gt[2]==gt[4]==0 and '4326' in pr
    sites['row']=np.floor((sites.lat-gt[3])/gt[5]).astype(int)
    sites['column']=np.floor((sites.lon-gt[0])/gt[1]).astype(int)
    sites['pixel_lat']=gt[3]+(sites.row+.5)*gt[5];sites['pixel_lon']=gt[0]+(sites.column+.5)*gt[1]
    sites['center_distance_km']=111.195*np.sqrt((sites.lat-sites.pixel_lat)**2+((sites.lon-sites.pixel_lon)*np.cos(np.radians(sites.lat)))**2)
    assert sites.row.between(0,H-1).all() and sites.column.between(0,W-1).all()
    sites.to_csv(OUT/'selected_stations.csv',index=False)
    protocol={'product':str(ROOT),'protocol_hash':protocol_hash,'producer_sha256':code_hash,
              'validation_sha256':sha(__file__),'selected_european_sites':sites.id.tolist(),
              'extraction':'one containing grid pixel from 5x5 inversion; no second 5x5 smoothing',
              'primary_months':complete_months,'hours_UTC':HOURS,'all_completed_snapshot_scenes_in_hours':len(files),
              'time_match':'Audited ICOS local non-DST TIMESTAMP_START converted to UTC using fixed site offsets; nearest +/-30 min',
              'monthly_pair_minimum':3,'station_summary_minimum_months':3,'bounds_C':[-23.15,76.85],
              'monthly_calendar':'pair-matched average of retained 11-16 UTC observations within a calendar month',
              'monthly_hour':'pair-matched average at each UTC hour; existing whole-month file scored separately only when all valid product dates have reference',
              'comparison_masks':['new_bulk: valid new component, reference, bulk LST','new_old_bulk: additionally valid old regional component'],
              'references':{'background_soil':'TS_1 shallow-soil probe','canopy':'TA air temperature'},
              'residual_filter':None,'production_snapshot':status,'interpretation':'Indirect consistency, not direct component radiometric accuracy.'}
    (OUT/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2),encoding='utf8')
    # Freeze station reference coverage before examining model error.
    ground={};coverage=[];manifest={'station_inventory_sha256':sha(invpath),'ground':{},'products':{}}
    for row in sites.itertuples():
        path=Path(f'E:/field/ICOSETC_{row.id}_METEO_L2/ICOSETC_{row.id}_METEO_L2.csv')
        g,conflicts=clean_ground(path);ground[row.id]=g
        use=g.field_time.dt.strftime('%Y%m').isin(complete_months)&g.field_time.dt.hour.isin(HOURS)
        coverage.append({'site':row.id,'first_ground_time':str(g.field_time.min()),'last_ground_time':str(g.field_time.max()),
                         'ground_rows_primary':int(use.sum()),'valid_TS1_primary':int(g.loc[use,'TS_1'].between(-23.15,76.85).sum()),
                         'valid_TA_primary':int(g.loc[use,'TA'].between(-23.15,76.85).sum()),'conflicting_ground_timestamps':conflicts})
        manifest['ground'][row.id]={'path':str(path),'sha256':sha(path)}
    rows=[]
    for k,p in enumerate(files):
        stamp=p.stem[-12:];date=f'{stamp[:4]}/{stamp[4:6]}/{stamp[6:8]}'
        oldpath=Path('E:/PRODUCTS/LSCT/MLST_COMPONENT')/date/f'MSG_LSCT_{stamp}.h5'
        bulkpath=Path('E:/PRODUCTS/MSG/MLST/GEOTIFF')/date/f'HDF5_LSASAF_MSG_LST_MSG-Disk_{stamp}.tif'
        bulk=gdal.Open(str(bulkpath))
        assert bulk is not None and tuple(bulk.GetGeoTransform())==gt
        old=h5py.File(oldpath) if oldpath.is_file() else None
        if old:
            assert old['data'].shape==(4,H,W) and np.allclose(old['data'].attrs['GeoTransform'],gt,rtol=0,atol=1e-9)
        with h5py.File(p) as f:
            assert f.attrs['complete']==1 and f.attrs['protocol_hash']==protocol_hash
            for s in sites.itertuples():
                a=f['data'][:,s.row,s.column].astype(float)
                if not np.all((a>=25000)&(a<=35000)):a[:]=np.nan
                a=a*.01-273.15
                b=old['data'][:,s.row,s.column].astype(float) if old else np.full(4,np.nan)
                if not np.all((b>=25000)&(b<=35000)):b[:]=np.nan
                b=b*.01-273.15
                raw=bulk.ReadAsArray(s.column,s.row,1,1)
                v=int(raw.view('int16')[0,0]) if raw.dtype==np.uint16 else float(raw[0,0])
                lst=v/100 if v not in [0,-8000] else np.nan
                rows.append({'site':s.id,'timestamp':stamp,'month':stamp[:6],'hour':int(stamp[8:10]),
                             'primary_month':stamp[:6] in complete_months,
                             **{f'new_{bname}':a[i] for i,bname in enumerate(BANDS)},
                             **{f'old_{bname}':b[i] for i,bname in enumerate(BANDS)},'bulk':lst})
        if old:old.close()
        manifest['products'][stamp]={'new':str(p),'new_sha256':sha(p),
                                    'old':str(oldpath),'old_sha256':sha(oldpath) if oldpath.is_file() else None,
                                    'bulk':str(bulkpath),'bulk_sha256':sha(bulkpath)}
        if (k+1)%100==0:print('EXTRACTED',k+1,'/',len(files),flush=True)
    predictions=pd.DataFrame(rows);predictions['time']=pd.to_datetime(predictions.timestamp,format='%Y%m%d%H%M',utc=True)
    matched=[]
    for sid,x in predictions.groupby('site'):
        m=pd.merge_asof(x.sort_values('time'),ground[sid],left_on='time',right_on='field_time',direction='nearest',tolerance=pd.Timedelta(minutes=30))
        m['offset_minutes']=(m.time-m.field_time).dt.total_seconds()/60;matched.append(m)
    matched=pd.concat(matched,ignore_index=True)
    matched.to_csv(OUT/'all_extracted_matches.csv',index=False)
    (OUT/'input_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    metrics=[];paired=[];monthrows=[];hourrows=[];coverage=pd.DataFrame(coverage)
    primary=matched.loc[matched.primary_month].copy()
    for s in sites.itertuples():
        x=primary.loc[primary.site.eq(s.id)].copy()
        coverage.loc[coverage.site.eq(s.id),'new_valid_scenes_primary']=int(x.new_canopy.notna().sum())
        for component,ref in [('background_soil','TS_1'),('canopy','TA')]:
            for support in ['new_bulk','new_old_bulk']:
                cols=[f'new_{component}',ref,'bulk']
                if support=='new_old_bulk':cols.append(f'old_{component}')
                good=x[cols].ge(-23.15).all(axis=1)&x[cols].le(76.85).all(axis=1)&x[cols].notna().all(axis=1)
                z=x.loc[good,['site','time','field_time','offset_minutes','month','hour',f'new_{component}',f'old_{component}','bulk',ref]].rename(columns={f'new_{component}':'new_5x5',f'old_{component}':'old_regional',ref:'reference'})
                z['component']=component;z['support']=support;paired.append(z)
                methods=['new_5x5','bulk']+(['old_regional'] if support=='new_old_bulk' else [])
                aggregate={'reference':'mean',**{m:'mean' for m in methods}}
                for scale,keys,destination in [('monthly_calendar',['month'],monthrows),('monthly_hour',['month','hour'],hourrows)]:
                    a=z.groupby(keys,as_index=False).agg(**{k:(k,v) for k,v in aggregate.items()},n_raw=('reference','size'))
                    a=a.loc[a.n_raw>=3].copy();a['site']=s.id;a['component']=component;a['support']=support
                    destination.append(a)
                    for method in methods:metrics.append({'site':s.id,'component':component,'support':support,'scale':scale,'method':method,
                        **score(a.reference,a[method]),'n_raw':int(a.n_raw.sum()),'enough_groups':len(a)>=3})
                for method in methods:metrics.append({'site':s.id,'component':component,'support':support,'scale':'instantaneous','method':method,
                        **score(z.reference,z[method]),'n_raw':len(z),'enough_groups':len(z)>=3})
    met=pd.DataFrame(metrics);pairs=pd.concat(paired,ignore_index=True);months_table=pd.concat(monthrows,ignore_index=True);hours_table=pd.concat(hourrows,ignore_index=True)
    met.to_csv(OUT/'station_metrics.csv',index=False);pairs.to_csv(OUT/'paired_observations.csv',index=False)
    months_table.to_csv(OUT/'matched_monthly_calendar.csv',index=False);hours_table.to_csv(OUT/'matched_monthly_hour.csv',index=False)
    coverage.to_csv(OUT/'station_coverage.csv',index=False)
    # Actual monthly product readback: eligibility demands identical date support.
    file_pairs=[];monthly_checks=[]
    for mp in monthfiles:
        with h5py.File(mp) as f:
            m=str(f.attrs['month']);h=int(f.attrs['hour_UTC'])
            if m not in complete_months or h not in HOURS:continue
            for s in sites.itertuples():
                n=int(f['n_obs'][s.row,s.column]);a=f['data'][:,s.row,s.column].astype(float)-273.15
                predicted=primary.loc[primary.site.eq(s.id)&primary.month.eq(m)&primary.hour.eq(h)]
                valid=predicted.new_canopy.notna();assert int(valid.sum())==n
                if n:
                    err=float(np.max(np.abs(a-predicted.loc[valid,[f'new_{b}' for b in BANDS]].mean().to_numpy())))
                    assert err<2e-5
                    monthly_checks.append(err)
                for comp,idx,ref in [('background_soil',0,'TS_1'),('canopy',1,'TA')]:
                    z=predicted.loc[valid&predicted[ref].between(-23.15,76.85)]
                    if n>=3 and len(z)==n:
                        file_pairs.append({'site':s.id,'month':m,'hour':h,'component':comp,'n':n,'estimate':a[idx],'reference':z[ref].mean()})
    fp=pd.DataFrame(file_pairs);fp.to_csv(OUT/'actual_monthly_file_pairs.csv',index=False)
    file_scores=[]
    if len(fp):
        for (s,c),z in fp.groupby(['site','component']):file_scores.append({'site':s,'component':c,**score(z.reference,z.estimate),'n_raw':int(z.n.sum())})
    pd.DataFrame(file_scores).to_csv(OUT/'actual_monthly_file_metrics.csv',index=False)
    summary=[]
    for (comp,support,scale),group in met.groupby(['component','support','scale']):
        for method,z in group.groupby('method'):
            z=z.loc[z.enough_groups]
            summary.append({'component':comp,'support':support,'scale':scale,'method':method,'sites':len(z),
                            'mean_site_rmse_K':float(z.rmse_K.mean()) if len(z) else None,'mean_site_bias_K':float(z.bias_K.mean()) if len(z) else None,
                            'total_pairs':int(z.n.sum()),'total_raw_pairs':int(z.n_raw.sum())})
    pd.DataFrame(summary).to_csv(OUT/'summary.csv',index=False)
    result={'status':'completed','primary_months':complete_months,'selected_sites':14,
            'sites_with_primary_ground':int((coverage.ground_rows_primary>0).sum()),
            'sites_with_valid_new_ground_pairs':int(pairs.loc[pairs.support.eq('new_bulk')].site.nunique()),
            'actual_monthly_values_checked':len(monthly_checks),'max_monthly_readback_difference_K':max(monthly_checks,default=0),
            'summary':summary,'actual_monthly_file_scores':file_scores,'producer_remains_paused':sha(ROOT/'status.json')==status_before}
    assert result['producer_remains_paused']
    (OUT/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf8')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
