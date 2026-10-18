"""All cached station timestamps, 2018-2024; direct 5x5 inversion and controls.

No regional retrieval files are read or written. The incorrect historical
Planck branch is evaluated ONLY as an explicitly labelled forensic control.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor,as_completed
import argparse,calendar,datetime as dt,hashlib,json,os,re as regex,sys,time,traceback
import numpy as np
import pandas as pd
from osgeo import gdal
from search_evo_parameters import prepare,retrieve,planck,inverse

HERE=Path(__file__).resolve().parent
OUT=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/msg_5x5/station_direct_2018_2024')
ROOT=Path('E:/PRODUCTS/SITE')
STATIC=['vza_e','vaa_e','vza_i','vaa_i','emis_s','emis_v']
BANDS=['background_soil','canopy','sunlit_soil','shaded_soil']
MODELS=[('physical_h005',.05,'physical',True),('physical_h025',.25,'physical',True),
        ('legacy_units_h005',.05,'legacy',True),('legacy_units_h025',.25,'legacy',True),
        ('historical_raw_h025',.25,'legacy',False),('historical_raw_h005',.05,'legacy',False)]
NS=None

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def atomic(path,obj):
    tmp=path.with_suffix(path.suffix+'.partial');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    for attempt in range(100):
        try:os.replace(tmp,path);break
        except PermissionError:
            if attempt==99:raise
            time.sleep(.1)

def functions():
    global NS
    if NS is None:
        sys.path.insert(0,str(HERE.parents[2]));NS={};p=HERE/'msg_lsct3.2-iter-site-cons-ig-center.py'
        exec(compile(p.read_text(encoding='utf8').split('# ================= 主程序')[0],str(p),'exec'),NS)
    return NS

def load(p):
    ds=gdal.Open(str(p));assert ds is not None,p
    a=ds.ReadAsArray();assert a.shape==(5,5),(p,a.shape)
    # Preserve stored signedness; uint16 may contain signed Celsius bit patterns.
    return a,{'path':str(p),'sha256':sha(p),'dtype':str(a.dtype),'bytes':p.stat().st_size}

def worker(job):
    sid,year,protocol_hash=job;out=OUT/'partitions'/sid/str(year);out.mkdir(parents=True,exist_ok=True)
    record=out/'complete.json'
    if record.exists():
        old=json.loads(record.read_text());assert old['protocol_hash']==protocol_hash
        assert sha(out/'predictions.csv.gz')==old['predictions_sha256']
        return old
    began=time.monotonic();ns=functions();site=ROOT/sid
    arrays={k:[] for k in ['lst_e_raw','lst_i_raw','sza','saa','lai']};records=[];fail=[];static={};raw_dtypes={}
    with (out/'input_manifest.jsonl').open('w',encoding='utf8') as log,ThreadPoolExecutor(max_workers=8) as pool:
        def read(p):
            a,meta=load(p);log.write(json.dumps(meta)+'\n');return a
        def many(paths):
            result={}
            for p,(a,meta) in zip(paths,pool.map(load,paths)):
                log.write(json.dumps(meta)+'\n');result[p.name]=a
            return result
        for k in STATIC+['lat','lon']:static[k]=read(site/'static'/f'{k}.tif').astype(float)
        for date in pd.date_range(f'{year}-01-01',f'{year}-12-31'):
            directory=site/date.strftime('%Y/%m/%d')
            names=set(os.listdir(directory)) if directory.is_dir() else set()
            stamps=sorted(m.group(1) for n in names if (m:=regex.fullmatch(r'LST_(\d{12})_e\.tif',n)))
            if not stamps:
                fail.append({'timestamp':date.strftime('%Y%m%d'),'reason':'no_EURO_files_for_day'});continue
            complete=[]
            for stamp in stamps:
                assert stamp[:8]==date.strftime('%Y%m%d')
                needed=[f'LST_{stamp}_i.tif',f'SZA_{stamp}.tif',f'SAA_{stamp}.tif',f'LAI_{stamp[:8]}.tif']
                missing=[n for n in needed if n not in names]
                if missing:fail.append({'timestamp':stamp,'reason':'missing:'+','.join(missing)})
                else:complete.append(stamp)
            # Avoid reading other inputs when the EURO center is already missing.
            euro=many([directory/f'LST_{s}_e.tif' for s in complete]);candidate=[]
            for stamp in complete:
                a=euro[f'LST_{stamp}_e.tif']
                if not np.isfinite(a[2,2]) or a[2,2]==0:
                    fail.append({'timestamp':stamp,'reason':'invalid_EURO_center'});continue
                candidate.append(stamp)
            iodc=many([directory/f'LST_{s}_i.tif' for s in candidate]);both=[]
            for stamp in candidate:
                a=iodc[f'LST_{stamp}_i.tif']
                if not np.isfinite(a[2,2]) or a[2,2]==0:
                    fail.append({'timestamp':stamp,'reason':'invalid_IODC_center'});continue
                both.append(stamp)
            if not both:continue
            extra=many([directory/f'LAI_{date:%Y%m%d}.tif']+[directory/f'{v}_{s}.tif' for s in both for v in ['SZA','SAA']])
            for stamp in both:
                for sat,values in [('e',euro),('i',iodc)]:
                    a=values[f'LST_{stamp}_{sat}.tif'];raw_dtypes[sat]=str(a.dtype)
                    # Store physical signed code as float, and original code for legacy decoding.
                    arrays[f'lst_{sat}_raw'].append(a.astype('float64'))
                for k,name in [('sza',f'SZA_{stamp}.tif'),('saa',f'SAA_{stamp}.tif'),('lai',f'LAI_{stamp[:8]}.tif')]:arrays[k].append(extra[name].astype('float64'))
                records.append({'site':sid,'timestamp':stamp,'year':year})
    pd.DataFrame(fail,columns=['timestamp','reason']).to_csv(out/'input_failures.csv.gz',index=False)
    controls=[];checks=[];cache={k:np.stack(v) if v else np.empty((0,5,5)) for k,v in arrays.items()}
    cache.update({k:v[None] for k,v in static.items()})
    np.savez_compressed(out/'input_cache.npz',**cache)
    if records:
        corrected={k:cache[k].copy() for k in ['sza','saa','lai']+STATIC}
        original={k:v.copy() for k,v in corrected.items()}
        for sat in ['e','i']:
            raw=cache[f'lst_{sat}_raw'];signed=np.where(raw>=32768,raw-65536,raw) if raw_dtypes[sat]=='uint16' else raw.copy()
            corrected[f'lst_{sat}']=signed/100.+273.15
            corrected[f'lst_{sat}'][(signed==0)|(signed==-8000)|(corrected[f'lst_{sat}']<150)|(corrected[f'lst_{sat}']>400)]=np.nan
            original[f'lst_{sat}']=np.where(raw==0,np.nan,raw/100.+273.15)
        bad=~np.isfinite(corrected['sza'])|(corrected['sza']<0)|(corrected['sza']>=90)|~np.isfinite(corrected['saa'])
        bad|=~np.isfinite(corrected['lai'])|(corrected['lai']<0)|(corrected['lai']>10)
        for k in ['vza_e','vza_i']:bad|=~np.isfinite(corrected[k])|(corrected[k]<0)|(corrected[k]>=90)
        for k in ['emis_s','emis_v']:bad|=~np.isfinite(corrected[k])|(corrected[k]<=0)|(corrected[k]>1)
        for k in ['lst_e','lst_i']:corrected[k][bad]=np.nan
        for model,h,mode,use_corrected in MODELS:
            data=corrected if use_corrected else original
            with np.errstate(all='ignore'):
                pre=prepare(data,h,mode,5,'center',ns['hotspot_layer'])
                temp,valid,bound=retrieve(pre,data,1000,3,mode,return_raw=True)
            center_good=np.isfinite(data['lst_e'][:,2,2])&np.isfinite(data['lst_i'][:,2,2])
            if use_corrected:valid &= center_good&(data['lai'][:,2,2]>=.05)
            else:valid=np.isfinite(temp[:,1:]).all(1)&center_good
            pred=pd.DataFrame(records);pred['model']=model;pred['valid']=valid
            pred['bulk']=data['lst_e'][:,2,2]-273.15;pred['sza']=data['sza'][:,2,2];pred['lai']=data['lai'][:,2,2]
            for k,b in enumerate(BANDS):pred[b]=np.where(valid,temp[:,k]-273.15,np.nan)
            pred['constraint_active']=bound;controls.append(pred)
            # Scalar verification across each year/site for physical and historical branches.
            if model in ['physical_h005','historical_raw_h025']:
                ids=np.flatnonzero(valid)
                for j in ids[np.linspace(0,len(ids)-1,min(2,len(ids)),dtype=int)] if len(ids) else []:
                    d={k:v[0 if len(v)==1 else j] for k,v in data.items()}
                    we,be=ns['hotspot_layer'](d['lai'],h,d['vza_e'],d['sza'],d['saa']-d['vaa_e'])
                    wi,bi=ns['hotspot_layer'](d['lai'],h,d['vza_i'],d['sza'],d['saa']-d['vaa_i'])
                    w=np.stack([d['emis_s']*we,d['emis_s']*(be-we),d['emis_v']*(1-be),d['emis_s']*wi,d['emis_s']*(bi-wi),d['emis_v']*(1-bi)],-1)
                    re=planck(d['lst_e'],mode)*w[...,:3].sum(-1);ri=planck(d['lst_i'],mode)*w[...,3:].sum(-1)
                    sun,_=ns['solve_2x2_system_center'](re,ri,w[...,0],w[...,1]+w[...,2],w[...,3],w[...,4]+w[...,5])
                    shade,veg=ns['solve_constrained_vectorized2_center'](re-w[...,0]*sun,ri-w[...,3]*sun,w[...,1],w[...,2],w[...,4],w[...,5],sun,dif=3)
                    a,b,c=ns['solve_joint_center'](re,ri,w,np.array([sun,min(shade,sun),veg]),lmbda=1000)
                    gap=np.exp(-.5*d['lai'][2,2]/np.cos(np.radians(d['sza'][2,2])))
                    expected=inverse(np.array([a*gap+b*(1-gap),c,a,b]),mode)
                    error=float(np.nanmax(np.abs(expected-temp[j])))
                    assert error<(1e-7 if mode=='physical' else .011),(sid,year,model,error)
                    checks.append({'model':model,'timestamp':records[j]['timestamp'],'max_error_K':error})
    predictions=pd.concat(controls,ignore_index=True) if controls else pd.DataFrame(columns=['site','timestamp','year','model','valid','bulk','sza','lai',*BANDS,'constraint_active'])
    tmp=out/'predictions.csv.gz.partial';predictions.to_csv(tmp,index=False,compression='gzip');os.replace(tmp,out/'predictions.csv.gz')
    complete={'site':sid,'year':year,'status':'complete','protocol_hash':protocol_hash,'input_center_pairs':len(records),
              'failed_input_timestamps':len(fail),'valid_by_model':{str(k):int(v) for k,v in predictions.groupby('model').valid.sum().items()},
              'input_raw_dtypes':raw_dtypes,'scalar_checks':checks,'elapsed_seconds':time.monotonic()-began,
              'predictions_sha256':sha(out/'predictions.csv.gz'),'cache_sha256':sha(out/'input_cache.npz'),
              'input_manifest_sha256':sha(out/'input_manifest.jsonl')}
    atomic(record,complete)
    return complete

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=4);ap.add_argument('--test-one',action='store_true');args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    sites=pd.read_csv('E:/field/sites-2025-selected.csv').id.tolist();sites=[s for s in sites if not s.startswith('CD-')];assert len(sites)==14
    source_files=[Path(__file__),HERE/'search_evo_parameters.py',HERE/'msg_lsct3.2-iter-site-cons-ig-center.py']
    protocol={'years':list(range(2018,2025)),'sites':sites,'scope':'All cached LST timestamps for each station and year; only complete source-input tuples can be inverted',
              'models':MODELS,'production_model':'physical_h005','controls_are_not_release_products':True,
              'lambda':1000,'delta':3,'windows':[5,5],'input_root':str(ROOT),'no_regional_product_reads':True,
              'primary_statistics_hours_UTC':list(range(11,17)),'also_report_all_available_hours':True,
              'source_sha256':{str(p):sha(p) for p in source_files}}
    ph=hashlib.sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest();protocol['protocol_hash']=ph
    pp=OUT/'protocol.json'
    if pp.exists():
        existing=json.loads(pp.read_text())
        if existing['protocol_hash']!=ph:
            relocation=json.loads((OUT/'source_relocation.json').read_text())
            assert existing['protocol_hash']==relocation['original_protocol_hash']
            assert protocol['source_sha256']==relocation['relocated_source_sha256'],'Changed source: do not mix results'
            core=lambda p:json.loads(json.dumps({k:v for k,v in p.items() if k not in ['source_sha256','protocol_hash']}))
            assert core(existing)==core(protocol),'Changed scientific protocol: do not mix results'
            atomic(OUT/'runtime_relocated_sources.json',{'source_sha256':protocol['source_sha256'],'output_root':str(OUT)})
            ph=existing['protocol_hash'];protocol=existing
    atomic(pp,protocol)
    paused=Path('E:/PRODUCTS/LSCT/MSG_5X5_PHYSICAL_V1/status.json');paused_hash=sha(paused)
    assert json.loads(paused.read_text(encoding='utf-8-sig'))['status']=='paused'
    jobs=[('CZ-BK1',2024,ph)] if args.test_one else [(s,y,ph) for y in range(2018,2025) for s in sites]
    progress={'status':'running','pid':os.getpid(),'jobs_total':len(jobs),'jobs_completed':0,'valid_primary':0,'started_UTC':dt.datetime.now(dt.timezone.utc).isoformat()}
    atomic(OUT/'progress.json',progress)
    try:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures={pool.submit(worker,j):j for j in jobs}
            for future in as_completed(futures):
                result=future.result();progress['jobs_completed']+=1
                progress['valid_primary']+=result['valid_by_model'].get('physical_h005',0)
                progress['last_completed']=[result['site'],result['year']];progress['updated_UTC']=dt.datetime.now(dt.timezone.utc).isoformat()
                atomic(OUT/'progress.json',progress)
                print('COMPLETE',progress['jobs_completed'],'/',len(jobs),result['site'],result['year'],'primary',result['valid_by_model'].get('physical_h005',0),'seconds',round(result['elapsed_seconds'],1),flush=True)
        assert sha(paused)==paused_hash;progress['status']='test_complete' if args.test_one else 'completed';progress['production_still_paused']=True
    except Exception:
        progress['status']='failed';progress['error']=traceback.format_exc();raise
    finally:atomic(OUT/'progress.json',progress)

if __name__=='__main__':main()
