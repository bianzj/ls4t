"""Direct station-cache 5x5 inversion; never reads regional temperature products."""
from pathlib import Path
import datetime as dt,hashlib,json,os,sys,time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from osgeo import gdal
from search_evo_parameters import prepare,retrieve,planck,inverse
from validate_msg_5x5_europe import clean_ground,score

HERE=Path(__file__).resolve().parent
ROOT=Path('E:/PRODUCTS/SITE')
OUT=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/msg_5x5/station_direct_validation')
YEAR=2024
HOURS=list(range(11,17))
STATIC=['vza_e','vaa_e','vza_i','vaa_i','emis_s','emis_v']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    source=HERE/'msg_lsct3.2-iter-site-cons-ig-center.py'
    sys.path.insert(0,str(HERE.parents[2]));ns={}
    exec(compile(source.read_text(encoding='utf8').split('# ================= 主程序')[0],str(source),'exec'),ns)
    inventory=pd.read_csv('E:/field/sites-2025-selected.csv')
    sites=inventory.loc[inventory.id.str[:3].isin(['CZ-','DE-','FI-','FR-','IT-','SE-'])]
    assert len(sites)==14
    protocol={'workflow':'Direct inversion of existing native station-centered 5x5 input cache; NO regional product extraction',
        'year':YEAR,'year_choice':'Latest complete pre-2025 calendar year, fixed before examining errors; common year for all selected sites',
        'sites':sites.id.tolist(),'hours_UTC':HOURS,'input_root':str(ROOT),'shape':[5,5],'center':[2,2],
        'hotspot':.05,'lambda':1000,'delta_radiance':3,'first_window':5,'second_window':5,
        'residual':'same first-stage center radiance subtracted across entire 5x5 window',
        'planck':'SI-consistent 10.5e-6 m; W m-2 sr-1 um-1',
        'LST_decode':'cached uint16 viewed as int16 Celsius*100; zero and -8000 excluded',
        'LAI_angles_emissivity':'cached physical values; no second scale conversion',
        'masks':'common finite dual-view input and weights; 0<=SZA,VZA<90; 0<=LAI<=10; 0<emissivity<=1; center LAI>=0.05',
        'output':'all four physical temperatures 250-350 K; no reference-dependent residual rejection',
        'reference':'TS_1 soil probe and TA air temperature; indirect consistency only',
        'time_matching':'Audited ICOS local non-DST TIMESTAMP_START converted to UTC using fixed site offsets, nearest +/-30 minutes',
        'monthly':'matched dates only, min 3 raw pairs; both calendar month and month/hour reported',
        'summary':'equal-site mean RMSE; >=3 raw pairs for instantaneous, >=3 groups for monthly',
        'limits':['Cached auxiliary/geolocation/angle provenance retained, not independently reprojected or repaired.',
                  'Cached native station windows differ from regional output grid; earlier regional scores are not method-matched.',
                  'Missing encoded zero may include valid 0 C; conservatively excluded.',
                  'One year is not a full 2018-2025 evaluation; reference depths/heights need metadata verification.'],
        'sources':{str(p):sha(p) for p in [Path(__file__),source,HERE/'search_evo_parameters.py',HERE/'validate_msg_5x5_europe.py']}}
    (OUT/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2),encoding='utf8')
    pd.DataFrame(sites).to_csv(OUT/'selected_stations.csv',index=False)
    production_status=Path('E:/PRODUCTS/LSCT/MSG_5X5_PHYSICAL_V1/status.json')
    paused_hash=sha(production_status);assert json.loads(production_status.read_text(encoding='utf-8-sig'))['status']=='paused'
    all_predictions=[];all_matches=[];all_metrics=[];all_month=[];coverage=[];scalar_checks=[]
    manifest=(OUT/'input_manifest.jsonl').open('w',encoding='utf8')
    prefetch={}
    def load(path):
        ds=gdal.Open(str(path));assert ds is not None,path
        a=ds.ReadAsArray();assert a.shape==(5,5),(path,a.shape)
        return a,{'path':str(path),'sha256':sha(path),'dtype':str(a.dtype),'shape':list(a.shape)}
    def read(path):
        a,record=prefetch.pop(str(path)) if str(path) in prefetch else load(path)
        manifest.write(json.dumps(record)+'\n')
        return a
    pool=ThreadPoolExecutor(max_workers=8)
    try:
        for station in sites.itertuples():
            sid=station.id;site=ROOT/sid;begin=time.monotonic()
            static={k:read(site/'static'/f'{k}.tif').astype(float) for k in STATIC}
            location={k:float(read(site/'static'/f'{k}.tif')[2,2]) for k in ['lat','lon']}
            badstatic=np.zeros((5,5),bool)
            for k in ['vza_e','vza_i']:badstatic|=~np.isfinite(static[k])|(static[k]<0)|(static[k]>=90)
            for k in ['emis_s','emis_v']:badstatic|=~np.isfinite(static[k])|(static[k]<=0)|(static[k]>1)
            arrays={k:[] for k in ['lst_e','lst_i','lai','sza','saa']};records=[];failures=[]
            for date in pd.date_range(f'{YEAR}-01-01',f'{YEAR}-12-31',freq='D'):
                directory=site/date.strftime('%Y/%m/%d')
                names=set(os.listdir(directory)) if directory.is_dir() else set()
                # Independent tiny TIFF reads overlap Windows file-open latency;
                # all numerical operations and manifest writes remain serial.
                wanted=[directory/f'LAI_{date:%Y%m%d}.tif']
                for h in HOURS:
                    stamp=date.strftime('%Y%m%d')+f'{h:02d}00'
                    wanted += [directory/f'LST_{stamp}_e.tif',directory/f'LST_{stamp}_i.tif',directory/f'SZA_{stamp}.tif',directory/f'SAA_{stamp}.tif']
                wanted=[p for p in wanted if p.name in names]
                prefetch={str(path):item for path,item in zip(wanted,pool.map(load,wanted))}
                lai=None
                for h in HOURS:
                    stamp=date.strftime('%Y%m%d')+f'{h:02d}00'
                    expected={'lst_e':f'LST_{stamp}_e.tif','lst_i':f'LST_{stamp}_i.tif',
                              'sza':f'SZA_{stamp}.tif','saa':f'SAA_{stamp}.tif','lai':f'LAI_{stamp[:8]}.tif'}
                    absent=[v for v in expected.values() if v not in names]
                    if absent:
                        failures.append({'site':sid,'timestamp':stamp,'reason':'missing_input_file','detail':';'.join(absent)});continue
                    d={}
                    for k in ['lst_e','lst_i']:
                        raw=read(directory/expected[k]);signed=raw.view('int16') if raw.dtype==np.uint16 else raw
                        d[k]=signed.astype(float)/100.+273.15
                        d[k][(signed==0)|(signed==-8000)|(d[k]<150)|(d[k]>400)]=np.nan
                    if not np.isfinite([d['lst_e'][2,2],d['lst_i'][2,2]]).all():
                        failures.append({'site':sid,'timestamp':stamp,'reason':'invalid_center_LST','detail':''});continue
                    if lai is None:lai=read(directory/expected['lai']).astype(float)
                    d['lai']=lai
                    for k in ['sza','saa']:d[k]=read(directory/expected[k]).astype(float)
                    bad=badstatic|~np.isfinite(lai)|(lai<0)|(lai>10)|~np.isfinite(d['sza'])|(d['sza']<0)|(d['sza']>=90)|~np.isfinite(d['saa'])
                    for k in ['lst_e','lst_i']:d[k][bad]=np.nan
                    if bad[2,2] or lai[2,2]<.05:
                        failures.append({'site':sid,'timestamp':stamp,'reason':'invalid_center_geometry_or_LAI','detail':''});continue
                    for k in arrays:arrays[k].append(d[k].copy())
                    records.append({'site':sid,'timestamp':stamp,'bulk':d['lst_e'][2,2]-273.15,'sza':d['sza'][2,2]})
            if not records:
                pd.DataFrame(failures).to_csv(OUT/f'{sid}_input_failures.csv',index=False)
                coverage.append({'site':sid,'scheduled':366*len(HOURS),'center_input_valid':0,'retrieval_valid':0,**location})
                print('SITE',sid,'no valid center inputs',flush=True);continue
            data={k:np.stack(v) for k,v in arrays.items()};data.update({k:v[None] for k,v in static.items()})
            pre=prepare(data,.05,'physical',5,'center',ns['hotspot_layer'])
            temps,valid,bound=retrieve(pre,data,1000,3,'physical',return_raw=True)
            # Check batch retrieval against original independent scalar routines.
            ids=np.flatnonzero(valid)
            for j in ids[np.linspace(0,len(ids)-1,min(5,len(ids)),dtype=int)] if len(ids) else []:
                d={k:v[0 if len(v)==1 else j] for k,v in data.items()}
                we,be=ns['hotspot_layer'](d['lai'],.05,d['vza_e'],d['sza'],d['saa']-d['vaa_e'])
                wi,bi=ns['hotspot_layer'](d['lai'],.05,d['vza_i'],d['sza'],d['saa']-d['vaa_i'])
                w=np.stack([d['emis_s']*we,d['emis_s']*(be-we),d['emis_v']*(1-be),d['emis_s']*wi,d['emis_s']*(bi-wi),d['emis_v']*(1-bi)],-1)
                re=planck(d['lst_e'])*w[...,:3].sum(-1);ri=planck(d['lst_i'])*w[...,3:].sum(-1)
                sun,_=ns['solve_2x2_system_center'](re,ri,w[...,0],w[...,1]+w[...,2],w[...,3],w[...,4]+w[...,5])
                sh,ve=ns['solve_constrained_vectorized2_center'](re-w[...,0]*sun,ri-w[...,3]*sun,w[...,1],w[...,2],w[...,4],w[...,5],sun,dif=3)
                a,b,c=ns['solve_joint_center'](re,ri,w,np.array([sun,min(sh,sun),ve]),lmbda=1000)
                gap=np.exp(-.5*d['lai'][2,2]/np.cos(np.radians(d['sza'][2,2])))
                ref=inverse(np.array([a*gap+b*(1-gap),c,a,b]));error=float(np.max(np.abs(ref-temps[j])))
                assert error<1e-7;scalar_checks.append({'site':sid,'timestamp':records[j]['timestamp'],'max_error_K':error})
            pred=pd.DataFrame(records)
            for i,k in enumerate(['background_soil','canopy','sunlit_soil','shaded_soil']):pred[k]=np.where(valid,temps[:,i]-273.15,np.nan)
            pred['valid']=valid;pred['constraint_active']=bound
            pred['time']=pd.to_datetime(pred.timestamp,format='%Y%m%d%H%M',utc=True)
            pred.to_csv(OUT/f'{sid}_direct_predictions.csv',index=False)
            pd.DataFrame(failures,columns=['site','timestamp','reason','detail']).to_csv(OUT/f'{sid}_input_failures.csv',index=False)
            all_predictions.append(pred)
            gpath=Path(f'E:/field/ICOSETC_{sid}_METEO_L2/ICOSETC_{sid}_METEO_L2.csv')
            manifest.write(json.dumps({'path':str(gpath),'sha256':sha(gpath)})+'\n')
            g,conflict=clean_ground(gpath)
            x=pd.merge_asof(pred.sort_values('time'),g,left_on='time',right_on='field_time',direction='nearest',tolerance=pd.Timedelta(minutes=30))
            x['offset_minutes']=(x.time-x.field_time).dt.total_seconds()/60
            x['month']=x.time.dt.strftime('%Y-%m');x['hour']=x.time.dt.hour
            cv={'site':sid,'scheduled':366*len(HOURS),'center_input_valid':len(pred),'retrieval_valid':int(valid.sum()),
                'ground_duplicate_conflicts':conflict,'elapsed_seconds':time.monotonic()-begin,**location}
            for comp,ref in [('background_soil','TS_1'),('canopy','TA')]:
                cols=[comp,ref,'bulk'];ok=x.valid&x[cols].notna().all(axis=1)&x[cols].ge(-23.15).all(axis=1)&x[cols].le(76.85).all(axis=1)
                z=x.loc[ok,['site','time','field_time','offset_minutes','month','hour',comp,ref,'bulk']].rename(columns={comp:'estimate',ref:'reference'})
                z['component']=comp;all_matches.append(z);cv[comp+'_pairs']=len(z)
                for scale,keys in [('instantaneous',None),('monthly_calendar',['month']),('monthly_hour',['month','hour'])]:
                    if keys:
                        q=z.groupby(keys,as_index=False).agg(estimate=('estimate','mean'),reference=('reference','mean'),bulk=('bulk','mean'),n_raw=('reference','size'))
                        q=q.loc[q.n_raw>=3].copy();q['site']=sid;q['component']=comp;q['scale']=scale;all_month.append(q)
                    else:q=z
                    for method,col in [('direct_5x5','estimate'),('bulk','bulk')]:
                        all_metrics.append({'site':sid,'component':comp,'scale':scale,'method':method,**score(q.reference,q[col]),
                                            'n_raw':int(q.n_raw.sum()) if keys else len(q),'enough_groups':len(q)>=3})
            coverage.append(cv)
            print('SITE',sid,'inputs',len(pred),'valid',int(valid.sum()),'soil/canopy pairs',cv['background_soil_pairs'],cv['canopy_pairs'],'seconds',round(cv['elapsed_seconds'],1),flush=True)
            (OUT/'progress.json').write_text(json.dumps({'status':'running','completed_sites':len(coverage),'current_site':sid}),encoding='utf8')
    finally:
        pool.shutdown(wait=True);manifest.close()
    preds=pd.concat(all_predictions,ignore_index=True);matches=pd.concat(all_matches,ignore_index=True)
    metrics=pd.DataFrame(all_metrics);monthly=pd.concat(all_month,ignore_index=True);coverage=pd.DataFrame(coverage)
    preds.to_csv(OUT/'direct_predictions.csv',index=False);matches.to_csv(OUT/'matched_observations.csv',index=False)
    metrics.to_csv(OUT/'station_metrics.csv',index=False);monthly.to_csv(OUT/'matched_monthly.csv',index=False);coverage.to_csv(OUT/'coverage.csv',index=False)
    summary=[]
    for (component,scale,method),z in metrics.loc[metrics.enough_groups].groupby(['component','scale','method']):
        summary.append({'component':component,'scale':scale,'method':method,'sites':len(z),'mean_site_rmse_K':float(z.rmse_K.mean()),
                        'mean_site_bias_K':float(z.bias_K.mean()),'total_pairs':int(z.n.sum()),'total_raw_pairs':int(z.n_raw.sum())})
    pd.DataFrame(summary).to_csv(OUT/'summary.csv',index=False)
    assert sha(production_status)==paused_hash
    result={'status':'completed','workflow':protocol['workflow'],'year':YEAR,'selected_sites':14,
            'sites_with_valid_retrievals':int((coverage.retrieval_valid>0).sum()),'valid_retrievals':int(coverage.retrieval_valid.sum()),
            'summary':summary,'scalar_checks':scalar_checks,'max_scalar_error_K':max(q['max_error_K'] for q in scalar_checks),
            'production_still_paused':True,'elapsed_seconds':time.monotonic()-started}
    (OUT/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf8')
    (OUT/'progress.json').write_text(json.dumps({'status':'completed','completed_sites':14}),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='scalar_checks'},indent=2),flush=True)


if __name__=='__main__':main()
