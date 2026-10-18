"""Read-only evidence for each month and the IODC projection transition."""
from pathlib import Path
from collections import defaultdict
import argparse
import hashlib
import json
import re
import time
import h5py
import numpy as np
from osgeo import gdal

HERE=Path(__file__).resolve().parent
gdal.UseExceptions()

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def cv(value):
    if isinstance(value,bytes):return value.decode('utf-8')
    if isinstance(value,np.ndarray):return [cv(v) for v in value.tolist()]
    if isinstance(value,np.generic):return value.item()
    return value

def source_path(stamp,view,projected=False):
    channel='MSG' if view=='e' else 'MSG-IODC'
    disk='MSG-Disk' if view=='e' else 'IODC-Disk'
    return Path('E:/PRODUCTS')/channel/'MLST'/('GEOTIFF' if projected else 'HDF5')/stamp[:4]/stamp[4:6]/stamp[6:8]/(f'HDF5_LSASAF_{channel}_LST_{disk}_{stamp}'+('.tif' if projected else ''))

def metadata(path):
    with h5py.File(path,'r') as f:
        keys=['SATELLITE','PROJECTION_NAME','IMAGE_ACQUISITION_TIME','NOMINAL_PRODUCT_TIME','NOMINAL_LAT','NOMINAL_LONG','MEAN_SSLAT','MEAN_SSLON','PRODUCT_ALGORITHM_VERSION']
        return {k:cv(f.attrs[k]) for k in keys if k in f.attrs}

def summary(pred,observed):
    either=(pred!=0)|(observed!=0)
    both=(pred!=0)&(observed!=0)
    return {'either_valid':int(either.sum()),'both_valid':int(both.sum()),'exact_valid':int(((pred==observed)&either).sum()),'exact_fraction':float(((pred==observed)&either).sum()/max(1,either.sum())),'mask_disagreement':int(((pred!=0)!=(observed!=0)).sum())}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=HERE/'geometry_audit.json')
    parser.add_argument('--inventory',type=Path,default=HERE/'input_preflight.json')
    parser.add_argument('--sample-step',type=int,default=1)
    args=parser.parse_args()
    inventory=json.loads(args.inventory.read_text(encoding='utf-8'))
    stamps=inventory['paired_timestamps']
    monthly=defaultdict(list)
    for stamp in stamps:monthly[stamp[:6]].append(stamp)
    selected=set()
    for month,values in monthly.items():
        days=sorted(set(stamp[:8] for stamp in values))
        for day in [days[0],days[len(days)//2],days[-1]]:
            selected.add(min((s for s in values if s[:8]==day),key=lambda s:abs(int(s[8:10])-12)))
    for stamp in stamps:
        if '20220525'<=stamp[:8]<='20220610' and stamp[8:12]=='1200':selected.add(stamp)
    indices=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/geolocation_sample_indices.npz')
    saved=np.load(indices)
    rows=saved['rows'][::args.sample_step];cols=saved['cols'][::args.sample_step]
    maps={'41.5':saved['old'][::args.sample_step],'45.5':saved['new'][::args.sample_step]}
    checks=[]
    failed_sources=[]
    start=time.monotonic()
    for index,stamp in enumerate(sorted(selected),1):
        native=source_path(stamp,'i');projected=source_path(stamp,'i',True)
        try:
            if not native.exists():raise FileNotFoundError(native)
            observed=gdal.Open(str(projected)).ReadAsArray()[rows,cols]
            with h5py.File(native,'r') as f:
                data=f['LST'][...]
                missing=f['LST'].attrs['MISSING_VALUE']
                dataset_attrs={k:cv(v) for k,v in f['LST'].attrs.items()}
                native_zero=int((data==0).sum())
        except Exception as error:
            failed_sources.append({'timestamp_UTC':stamp,'native':str(native),'projected':str(projected),'error':str(error),'action':'Excluded from geometry evidence; retain original inputs without repair or overwrite.'})
            print(json.dumps({'failed_source':stamp,'error':str(error)},ensure_ascii=False),flush=True)
            continue
        hypotheses={}
        for label,picks in maps.items():
            prediction=np.zeros(rows.size,dtype=np.uint16)
            ok=picks>=0
            value=data.ravel()[picks[ok]].copy()
            value[value==missing]=0
            prediction[ok]=value.astype(np.uint16)
            hypotheses[label]=summary(prediction,observed)
        best=max(hypotheses,key=lambda label:hypotheses[label]['exact_fraction'])
        strong=hypotheses[best]['exact_fraction']>=.995 and hypotheses[best]['either_valid']>=50
        if not strong:raise AssertionError((stamp,hypotheses))
        meta=metadata(native)
        euro_meta=metadata(source_path(stamp,'e'))
        decoded_time=str(meta['IMAGE_ACQUISITION_TIME'])[:12]
        assert decoded_time==stamp
        position={}
        for view,viewmeta,expected_lon in [('iodc',meta,float(best)),('euro',euro_meta,0.)]:
            meanlat=float(viewmeta.get('MEAN_SSLAT',float('nan')));meanlon=float(viewmeta.get('MEAN_SSLON',float('nan')))
            nominal_lat=float(viewmeta.get('NOMINAL_LAT',float('nan')));nominal_lon=float(viewmeta.get('NOMINAL_LONG',float('nan')))
            mean_valid=np.isfinite([meanlat,meanlon]).all() and abs(meanlon-expected_lon)<1.5 and abs(meanlat)<=20 and (meanlat!=0 or meanlon!=0)
            nominal_valid=np.isfinite([nominal_lat,nominal_lon]).all() and abs(nominal_lon-expected_lon)<1.5 and abs(nominal_lat)<=20
            position[view]={'expected_projection_longitude':expected_lon,'MEAN_SS_consistent':bool(mean_valid),'NOMINAL_consistent':bool(nominal_valid),'mean_lat':meanlat,'mean_lon':meanlon,'nominal_lat':nominal_lat,'nominal_lon':nominal_lon}
        checks.append({'timestamp_UTC':stamp,'native':str(native),'projected':str(projected),'selected_native_grid':best,'hypotheses':hypotheses,'metadata':meta,'euro_metadata':euro_meta,'positions':position,'native_valid_zero_C_pixels':native_zero,'native_dataset_attrs':dataset_attrs})
        if index%15==0:print(json.dumps({'checked':index,'total':len(selected),'stamp':stamp,'seconds':round(time.monotonic()-start,1)}),flush=True)
    grids_by_month={}
    for month in monthly:
        items=[r for r in checks if r['timestamp_UTC'].startswith(month)]
        grids_by_month[month]={'sampled_dates':sorted(set(r['timestamp_UTC'][:8] for r in items)),'observed_grids':sorted(set(r['selected_native_grid'] for r in items)),'sample_count':len(items)}
    transition=[r for r in checks if r['timestamp_UTC'].startswith(('202205','202206'))]
    report={'status':'passed_with_unreadable_inputs' if failed_sources else 'projection_samples_passed','all_months_sampled_three_dates':all(len(v['sampled_dates'])>=3 for v in grids_by_month.values()),'months':len(monthly),'sampled_scenes':len(checks),'failed_sources':failed_sources,'sampled_target_pixels_per_scene':len(rows),'sample_map_path':str(indices),'sample_map_sha256':sha(indices),'map_provenance':'Existing nearest-neighbor 5 km maps independently checked against current native and projected discrete LST values at every sampled scene. Native latitude orientation follows the original validated remapper. No observations altered.','months_evidence':grids_by_month,'checks':checks,'transition':[{'stamp':r['timestamp_UTC'],'grid':r['selected_native_grid'],'mean_ss_matches':r['positions']['iodc']['MEAN_SS_consistent'],'nominal_matches':r['positions']['iodc']['NOMINAL_consistent']} for r in transition],'position_source_counts':{view:{kind:sum(r['positions'][view][kind] for r in checks) for kind in ['MEAN_SS_consistent','NOMINAL_consistent']} for view in ['euro','iodc']},'unresolved_iodc_positions':[r['timestamp_UTC'] for r in checks if not r['positions']['iodc']['MEAN_SS_consistent'] and not r['positions']['iodc']['NOMINAL_consistent']],'zero_nodata_ambiguity':'Native LST missing=-8000, valid zero Celsius exists. Projection stores both native valid zero Celsius and missing/outside coverage as uint16 zero; this information cannot be recovered from projected TIFF alone.','seconds':time.monotonic()-start}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','months','sampled_scenes','all_months_sampled_three_dates','position_source_counts','unresolved_iodc_positions','seconds']},indent=2),flush=True)

if __name__=='__main__':main()
