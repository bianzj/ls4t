"""Separate physical 5x5 MSG collection; resumable instantaneous -> month/hour means.

Never overwrites the historical collection. This is an experimental collection:
projected zero/NoData ambiguity and static view-angle provenance remain unresolved.
"""
from pathlib import Path
import argparse, calendar, datetime as dt, hashlib, json, os, sys, time, traceback
import h5py
import numpy as np
import pandas as pd
from scipy.ndimage import uniform_filter
from osgeo import gdal
import pvlib

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
C1 = 2 * 6.62607015e-34 * 299792458**2
C2 = 6.62607015e-34 * 299792458 / 1.380649e-23
WL = 10.5e-6
BANDS = ['background_soil', 'canopy', 'sunlit_soil', 'shaded_soil']
PROTOCOL = {
    'version': 'MSG_5X5_PHYSICAL_V1', 'release_status': 'experimental',
    'first_window': 5, 'second_window': 5, 'hotspot': .05, 'lambda': 1000.,
    'delta_radiance': 3., 'radiance_units': 'W m-2 sr-1 um-1',
    'wavelength_m': WL, 'residual_mode': 'center_constant_sunlit_over_entire_5x5',
    'minimum_valid_neighbors': 10, 'determinant_threshold': 1e-8,
    'neighborhood_boundary': 'nearest; 2-pixel halo between processing tiles',
    'observation_mask': 'common finite dual-view radiance and all six weights; daylight; valid land/emissivity/angles',
    'source_LST': 'uint16 viewed as signed int16 Celsius*100; zero and -8000 excluded',
    'temperature_limits_K': [250., 350.], 'minimum_LAI': .05,
    'output_mask': 'all four components finite and within limits; no reference-dependent rejection',
    'instant_encoding': 'uint16 kelvin*100 rounded; 0=NoData',
    'monthly': 'arithmetic mean of encoded instantaneous K separately for each UTC hour; common four-band support',
    'minimum_monthly_observations': 1, 'low_support': 'n < 3 flagged; no filling',
    'solar_geometry': 'legacy pixel-corner grid, 10x coarse nearest pvlib zenith/azimuth; altitude 0 m',
    'auxiliary_sampling': 'land and soil emissivity use their own CRS and geotransform; nearest cell',
    'limitations': ['Valid 0 C cannot be recovered from projected zero/NoData; conservatively excluded.',
                   'Static viewing angles retained; temporal provenance, especially after June 2022, unresolved.',
                   'Land-cover raster declares an unspecified Clarke 1866 datum; geographic transformation accuracy unresolved.',
                   'Regional 5x5 baseline, not a demonstrated globally optimal parameter set.',
                   'Calendar gaps and clear-sky sampling remain; monthly mean is not an all-weather mean.'],
}
PROTOCOL_HASH = hashlib.sha256(json.dumps(PROTOCOL, sort_keys=True).encode()).hexdigest()


def sha(path):
    h=hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024), b''): h.update(b)
    return h.hexdigest()


def atomic_json(path, obj):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.partial')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf8')
    os.replace(tmp,path)


def planck(t):
    with np.errstate(all='ignore'):
        return C1/(WL**5*np.expm1(C2/(WL*np.asarray(t))))*1e-6


def inverse(r):
    with np.errstate(all='ignore'):
        return np.where(r>0,C2/(WL*np.log1p(C1*1e-6/(WL**5*r))),np.nan)


def hotspot(lai,vza,sza,vsa):
    with np.errstate(all='ignore'):
        v,s,a=np.radians(vza),np.radians(sza),np.radians(vsa)
        kv,ks=.5/np.cos(v),.5/np.cos(s)
        dist=np.sqrt(np.maximum(np.tan(v)**2+np.tan(s)**2-2*np.tan(v)*np.tan(s)*np.cos(a),0))
        alpha=dist/(PROTOCOL['hotspot']*(kv+ks)/2)
        factor=np.where(alpha<1e-5,1.,-np.expm1(-alpha)/alpha)
        return np.exp(-(kv+ks-np.sqrt(kv*ks)*factor)*lai),np.exp(-kv*lai)


def retrieve(d):
    """Exact rolling equivalent of the station-center algorithm, in physical units."""
    lai,sza=d['lai'],d['sza']
    with np.errstate(all='ignore'):
        we,be=hotspot(lai,d['vza_e'],sza,(d['saa']-d['vaa_e']+180)%360-180)
        wi,bi=hotspot(lai,d['vza_i'],sza,(d['saa']-d['vaa_i']+180)%360-180)
        w=np.stack([d['emis_s']*we,d['emis_s']*(be-we),d['emis_v']*(1-be),
                    d['emis_s']*wi,d['emis_s']*(bi-wi),d['emis_v']*(1-bi)],axis=-1)
        re=planck(d['lst_e'])*w[...,:3].sum(-1)
        ri=planck(d['lst_i'])*w[...,3:].sum(-1)
    good=np.isfinite(re)&np.isfinite(ri)&np.isfinite(w).all(-1)
    good &= (sza>=0)&(sza<90)&(lai>=0)&(lai<=10)
    for k in ['vza_e','vza_i']: good &= (d[k]>=0)&(d[k]<90)
    for k in ['emis_s','emis_v']: good &= (d[k]>0)&(d[k]<=1)
    if 'land' in d: good &= (d['land']>0)&(d['land']<=17)
    # Every normal-equation term uses the SAME observation mask.
    def total(a): return uniform_filter(np.where(good,a,0.).astype('float64'),size=5,mode='nearest')*25
    n=np.rint(total(np.ones_like(re))).astype('uint8')
    def solve(aa,ab,bb,u,v):
        det=aa*bb-ab*ab
        with np.errstate(all='ignore'):
            x=(u*bb-v*ab)/det; y=(v*aa-u*ab)/det
        valid=good&(n>=10)&(np.abs(det)>=1e-8)&(x>=0)&(y>=0)
        return np.where(valid,x,np.nan),np.where(valid,y,np.nan)
    a,b,c,e,f,g=[w[...,i] for i in range(6)]
    sun,_=solve(total(a*a+e*e),total(a*(b+c)+e*(f+g)),total((b+c)**2+(f+g)**2),
                total(a*re+e*ri),total((b+c)*re+(f+g)*ri))
    # S(center) is constant over each neighborhood; expand sums algebraically.
    shade,veg=solve(total(b*b+f*f),total(b*c+f*g),total(c*c+g*g),
                    total(b*re+f*ri)-sun*total(b*a+f*e),
                    total(c*re+g*ri)-sun*total(c*a+g*e))
    rre,rri=re-a*sun,ri-e*sun
    delta=PROTOCOL['delta_radiance']; p,q=b+c,f+g
    vc=(p*(rre-b*delta)+q*(rri-f*delta))/(p*p+q*q+1e-9); sc=vc+delta
    vd=(p*(rre+b*delta)+q*(rri+f*delta))/(p*p+q*q+1e-9); sd=vd-delta
    ec=(rre-b*sc-c*vc)**2+(rri-f*sc-g*vc)**2
    ed=(rre-b*sd-c*vd)**2+(rri-f*sd-g*vd)**2
    bound=np.abs(shade-veg)>delta
    shade=np.minimum(np.where(bound,np.where(ec<=ed,sc,sd),shade),sun)
    veg=np.where(bound,np.where(ec<=ed,vc,vd),veg)
    prior=np.stack([sun,shade,veg],axis=-1)
    # Only finite systems are sent to LAPACK; invalid pixels remain missing.
    ok=good&np.isfinite(prior).all(-1)&(lai>=.05)
    final=np.full_like(prior,np.nan)
    A=w[ok].reshape(-1,2,3); rad=np.stack([re[ok],ri[ok]],-1)
    lhs=np.einsum('nki,nkj->nij',A,A)+PROTOCOL['lambda']*np.eye(3)
    rhs=np.einsum('nki,nk->ni',A,rad)+PROTOCOL['lambda']*prior[ok]
    final[ok]=np.linalg.solve(lhs,rhs[...,None])[...,0]
    final[...,1]=np.minimum(final[...,1],final[...,0])
    with np.errstate(all='ignore'): gap=np.exp(-.5*lai/np.cos(np.radians(sza)))
    soil=final[...,0]*gap+final[...,1]*(1-gap)
    temp=inverse(np.stack([soil,final[...,2],final[...,0],final[...,1]]))
    valid=np.isfinite(temp).all(0)&(temp>=250).all(0)&(temp<=350).all(0)&ok
    temp[:,~valid]=np.nan
    # Bit 0 invalid input; 1 low neighbors; 2 low LAI; 3 failed/range;
    # bit 4 constraint active (informational, can coexist with valid output).
    qa=(~good).astype('uint8') | ((n<10).astype('uint8')<<1) | ((lai<.05).astype('uint8')<<2)
    qa |= ((~valid & good & (n>=10) & (lai>=.05)).astype('uint8')<<3)
    qa |= bound.astype('uint8')<<4
    return temp,n,qa


def paths(stamp):
    day=f'{stamp[:4]}/{stamp[4:6]}/{stamp[6:8]}'
    return {
        'lst_e':Path('E:/PRODUCTS/MSG/MLST/GEOTIFF')/day/f'HDF5_LSASAF_MSG_LST_MSG-Disk_{stamp}.tif',
        'lst_i':Path('E:/PRODUCTS/MSG-IODC/MLST/GEOTIFF')/day/f'HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_{stamp}.tif',
        'lai':Path('E:/PRODUCTS/MSG/MDLAI/GEOTIFF')/day/f'HDF5_LSASAF_MSG_LAI_MSG-Disk_{stamp[:8]}0000.tif'}


def load_static():
    # Keep historical geolocation/auxiliary sampling fixed for this comparison.
    # No source mutation or execution of its processing loop.
    sys.path.insert(0,str(REPO))
    source=HERE/'msg_lsct3.2-iter.py'
    assert sha(source)=='763de469c6023b2b830061658d9130fcc851b7f7e9397903c27ac2fa159df9c3'
    code=source.read_text(encoding='utf8').split('# ================= 循环处理')[0]
    code=code.replace('indir = "/media/hero/MSG/"',"indir = 'E:/'")
    ns={'__name__':'_read_only_static_loader_'}
    exec(compile(code,str(source),'exec'),ns)
    # Ancillaries have equal index grids but DIFFERENT declared CRS. Sample
    # soil using its own CRS; never silently reuse the land-cover indices.
    lm=gdal.Open(ns['infile_source']); sm=gdal.Open(ns['infile_soil_emis'])
    iy,ix=ns['loc2map'](ns['lat'],ns['lon'],sm)
    ns['emis_s']=sm.ReadAsArray()[iy,ix].reshape(ns['land_type'].shape).astype('float64')
    if np.nanmean(ns['emis_s'][ns['emis_s']>0])>1:ns['emis_s']/=1000.
    result={k:ns[v] for k,v in {'vza_e':'vza_euro','vza_i':'vza_iodc','vaa_e':'vaa_euro',
            'vaa_i':'vaa_iodc','emis_s':'emis_s','emis_v':'emis_v','land':'land_type'}.items()}
    ds=ns['dataset_ref']
    for k in ['infile_vza_e','infile_vza_i','infile_vaa_e','infile_vaa_i']:
        grid_check(gdal.Open(ns[k]),result['land'].shape,ds.GetGeoTransform(),ds.GetProjection())
    return result,ns['latt'],ns['lonn'],ds.GetGeoTransform(),ds.GetProjection()


def grid_check(ds,shape,gt,pr):
    if (ds.RasterYSize,ds.RasterXSize)!=shape or not np.allclose(ds.GetGeoTransform(),gt,rtol=0,atol=1e-9) or ds.GetProjection()!=pr:
        raise ValueError('Input raster grid mismatch: '+ds.GetDescription())


def attrs(f,gt,pr):
    f.attrs.update(protocol_hash=PROTOCOL_HASH,protocol_json=json.dumps(PROTOCOL),
                   code_sha256=sha(__file__),GeoTransform=gt,Projection=pr,
                   bands=json.dumps(BANDS),release_status='experimental',time_zone='UTC')


def instant_path(root,stamp):
    return root/'INSTANTANEOUS'/stamp[:4]/stamp[4:6]/stamp[6:8]/f'MSG_LSCT_5X5_{stamp}.h5'


def produce_scene(stamp,root,static,latt,lonn,gt,pr,tile=256):
    out=instant_path(root,stamp)
    if out.exists():
        with h5py.File(out) as f:
            assert f.attrs['protocol_hash']==PROTOCOL_HASH and f.attrs['code_sha256']==sha(__file__) and f.attrs['complete']==1
        return out
    started=time.monotonic(); ip=paths(stamp)
    shape=static['land'].shape; H,W=shape
    ds={k:gdal.Open(str(v)) for k,v in ip.items()}
    for d in ds.values(): grid_check(d,shape,gt,pr)
    t=pd.to_datetime(stamp,format='%Y%m%d%H%M',utc=True)
    sol=pvlib.solarposition.get_solarposition(np.repeat(t,latt.size),latt.ravel(),lonn.ravel(),0,method='nrel_numpy')
    import cv2
    solar={k:cv2.resize(sol[v].to_numpy().reshape(latt.shape).astype('float32'),(W,H),interpolation=0)
           for k,v in [('sza','zenith'),('saa','azimuth')]}
    out.parent.mkdir(parents=True,exist_ok=True); tmp=out.with_suffix('.h5.partial')
    valid_n=0; band_sums=np.zeros(4); hist=np.zeros(26,dtype='int64')
    inputs={k:{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for k,p in ip.items()}
    with h5py.File(tmp,'w') as f:
        attrs(f,gt,pr);f.attrs['timestamp_UTC']=t.isoformat();f.attrs['inputs_json']=json.dumps(inputs)
        output=f.create_dataset('data',(4,H,W),dtype='uint16',chunks=(1,128,256),compression='gzip',compression_opts=4)
        output.attrs.update(GeoTransform=gt,Projection=pr,Scale_Factor=100.,scale_factor=.01,add_offset=0.,
                            NoData_Value=0,_FillValue=0,units='K',Description='ts,tv,tss,tsh')
        count=f.create_dataset('valid_neighbors',(H,W),dtype='uint8',chunks=(128,256),compression='gzip')
        qa=f.create_dataset('qa',(H,W),dtype='uint8',chunks=(128,256),compression='gzip')
        qa.attrs['flag_masks']=[1,2,4,8,16]
        qa.attrs['flag_meanings']='invalid_input low_neighbors low_LAI failed_or_out_of_range constraint_active'
        for y in range(0,H,tile):
            end=min(H,y+tile);lo=max(0,y-2);hi=min(H,end+2);crop=slice(y-lo,end-lo)
            d={k:v[lo:hi].astype('float64') for k,v in static.items()}
            d.update({k:v[lo:hi].astype('float64') for k,v in solar.items()})
            for k,src in ds.items():
                raw=src.ReadAsArray(0,lo,W,hi-lo)
                if k=='lai':
                    a=raw.astype('float64')/1000.;a[(a<0)|(a>10)]=np.nan
                else:
                    signed=raw.view('int16') if raw.dtype==np.uint16 else raw
                    a=signed.astype('float64')/100.+273.15
                    a[(signed==0)|(signed==-8000)|(a<150)|(a>400)]=np.nan
                d[k]=a
            temp,n,q=retrieve(d); temp=temp[:,crop];n=n[crop];q=q[crop]
            good=np.isfinite(temp).all(0)
            encoded=np.rint(np.nan_to_num(temp,nan=0.)*100).astype('uint16')
            output[:,y:end]=encoded;count[y:end]=n;qa[y:end]=q
            valid_n+=int(good.sum());band_sums+=np.nansum(temp,axis=(1,2));hist+=np.bincount(n[good],minlength=26)
        f.attrs['valid_pixels']=valid_n;f.attrs['complete']=1
        f.attrs['valid_neighbor_histogram']=hist
    os.replace(tmp,out)
    rec={'timestamp':stamp,'path':str(out),'valid_pixels':valid_n,'sha256':sha(out),'seconds':time.monotonic()-started}
    with (root/'scene_manifest.jsonl').open('a',encoding='utf8') as log: log.write(json.dumps(rec)+'\n')
    print('SCENE',stamp,'valid',valid_n,'seconds',round(rec['seconds'],1),flush=True)
    return out


def monthly(root,month,hour,files,expected,missing,gt,pr):
    out=root/'MONTHLY_HOUR'/month[:4]/f'MSG_LSCT_5X5_MONTH_{month}_H{hour:02d}.h5'
    stamps=[p.stem[-12:] for p in files]
    source_hashes={str(p):sha(p) for p in files}
    if out.exists():
        with h5py.File(out) as f:
            assert f.attrs['protocol_hash']==PROTOCOL_HASH and f.attrs['complete']==1
            assert json.loads(f.attrs['source_sha256_json'])==source_hashes
        return out
    with h5py.File(files[0]) as f: _,H,W=f['data'].shape
    out.parent.mkdir(parents=True,exist_ok=True);tmp=out.with_suffix('.h5.partial')
    support=np.zeros(len(expected)+1,dtype='int64');verify=[]
    with h5py.File(tmp,'w') as f:
        attrs(f,gt,pr)
        f.attrs.update(month=month,hour_UTC=hour,source_count=len(files),calendar_days=len(expected),
                       source_timestamps_json=json.dumps(stamps),missing_sources_json=json.dumps(missing),
                       source_sha256_json=json.dumps(source_hashes),group_processed=1,
                       calendar_input_complete=int(len(files)==len(expected)))
        mean=f.create_dataset('data',(4,H,W),dtype='float32',chunks=(1,128,256),compression='gzip',compression_opts=4,fillvalue=np.nan)
        mean.attrs.update(units='K',scale_factor=1.,NoData_Value=np.nan,GeoTransform=gt,Projection=pr,Description='ts,tv,tss,tsh')
        nout=f.create_dataset('n_obs',(H,W),dtype='uint8',chunks=(128,256),compression='gzip')
        qout=f.create_dataset('low_support',(H,W),dtype='uint8',chunks=(128,256),compression='gzip')
        qout.attrs['description']='1 for 1-2 observations; 0 for >=3 or no observations (see n_obs)'
        for y in range(0,H,256):
            end=min(H,y+256);sums=np.zeros((4,end-y,W));n=np.zeros((end-y,W),dtype='uint8')
            for p in files:
                with h5py.File(p) as src:
                    assert src.attrs['protocol_hash']==PROTOCOL_HASH and src.attrs['complete']==1
                    a=src['data'][:,y:end];good=np.all((a>=25000)&(a<=35000),axis=0)
                    sums+=np.where(good[None],a.astype('float64')*.01,0.);n+=good
            m=np.full_like(sums,np.nan);np.divide(sums,n[None],out=m,where=n[None]>0)
            mean[:,y:end]=m;nout[y:end]=n;qout[y:end]=((n>0)&(n<3)).astype('uint8')
            support+=np.bincount(n.ravel(),minlength=len(expected)+1)
        f.attrs['support_histogram']=support;f.attrs['complete']=1
    os.replace(tmp,out)
    # Independent direct pixel read verifies stored means and counts.
    with h5py.File(out) as f:
        for y,x in [(881,333),(H//2,W//2),(H//3,W//2),(H-1,W-1)]:
            vals=[]
            for p in files:
                with h5py.File(p) as s: vals.append(s['data'][:,y,x])
            vals=np.array(vals);good=np.all((vals>=25000)&(vals<=35000),axis=1)
            assert int(f['n_obs'][y,x])==int(good.sum())
            if good.any(): assert np.allclose(f['data'][:,y,x],vals[good].mean(0)*.01,rtol=0,atol=2e-5)
            else: assert np.isnan(f['data'][:,y,x]).all()
            verify.append({'row':y,'column':x,'n':int(good.sum())})
    rec={'month':month,'hour_UTC':hour,'path':str(out),'source_count':len(files),'calendar_days':len(expected),
         'valid_pixels':int(support[1:].sum()),'support_histogram':support.tolist(),'sha256':sha(out),'pixel_verification':verify}
    with (root/'monthly_manifest.jsonl').open('a',encoding='utf8') as log:log.write(json.dumps(rec)+'\n')
    print('MONTHLY',month,hour,'sources',len(files),'valid',rec['valid_pixels'],flush=True)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('E:/PRODUCTS/LSCT/MSG_5X5_PHYSICAL_V1'))
    p.add_argument('--start-month',default='201708');p.add_argument('--end-month',default='202512')
    p.add_argument('--hours',type=int,nargs='+',default=[12,10,11,13,14,15,16])
    p.add_argument('--tile-rows',type=int,default=256)
    args=p.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=True)
    if not all(10<=x<=16 for x in args.hours) or len(set(args.hours))!=len(args.hours):raise ValueError('Unique UTC hours 10-16 required')
    start=pd.Period(args.start_month,freq='M');end=pd.Period(args.end_month,freq='M')
    if start>end:raise ValueError('Reversed dates')
    # Single Windows process lock, released by OS even after interruption.
    import msvcrt
    lock=open(root/'producer.lock','a+b');lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
    msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    protocol_file=root/'protocol.json'
    if protocol_file.exists():
        old=json.loads(protocol_file.read_text(encoding='utf8'))
        assert old['protocol_hash']==PROTOCOL_HASH and old['code_sha256']==sha(__file__),'Different producer/protocol; do not mix products'
    atomic_json(protocol_file,{'protocol':PROTOCOL,'protocol_hash':PROTOCOL_HASH,'code_sha256':sha(__file__)})
    jobs=[];missing=[]
    for m in pd.period_range(start,end,freq='M'):
        month=f'{m.year:04d}{m.month:02d}'
        for h in args.hours:
            expected=[f'{month}{d:02d}{h:02d}00' for d in range(1,calendar.monthrange(m.year,m.month)[1]+1)]
            available=[];miss=[]
            for stamp in expected:
                absent=[str(x) for x in paths(stamp).values() if not x.is_file()]
                if absent:miss.append({'timestamp':stamp,'missing':absent})
                else:available.append(stamp)
            jobs.append({'month':month,'hour':h,'expected':expected,'available':available,'missing':miss});missing.extend(miss)
    atomic_json(root/'inventory.json',{'start_month':args.start_month,'end_month':args.end_month,'hours_UTC':args.hours,
                  'available_scenes':sum(len(j['available']) for j in jobs),'missing_scenes':len(missing),'jobs':jobs})
    status={'status':'loading_static','pid':os.getpid(),'started_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),
            'available_scenes':sum(len(j['available']) for j in jobs),'missing_input_scenes':len(missing),
            'groups_total':len(jobs),'groups_completed':0,'scenes_completed':0}
    atomic_json(root/'status.json',status)
    try:
        static_paths=[Path('E:/Static')/f'combined_{s}_{a}.tif' for s in ['euro','iodc'] for a in ['vza','vaa']]
        static_paths += [Path('E:/map/MCD12C1_2011_0.01.tif'),Path('E:/lse/AG1km.v003.SoilEmi.ABI.Global.001D_LSE12.tif'),Path('E:/lse/IGBP_Emi.txt')]
        static_paths += [HERE/'msg_lsct3.2-iter.py',*sorted((REPO/'cases/official/support').glob('*.py'))]
        atomic_json(root/'static_source_manifest.json',{'files':{str(x):{'sha256':sha(x),'bytes':x.stat().st_size} for x in static_paths}})
        static,latt,lonn,gt,pr=load_static()
        for j in jobs:
            status.update(status='running',current_month=j['month'],current_hour_UTC=j['hour'])
            files=[]
            for stamp in j['available']:
                status.update(current_timestamp=stamp,updated_UTC=dt.datetime.now(dt.timezone.utc).isoformat())
                atomic_json(root/'status.json',status)
                files.append(produce_scene(stamp,root,static,latt,lonn,gt,pr,args.tile_rows))
                status['scenes_completed']+=1
            if files: monthly(root,j['month'],j['hour'],files,j['expected'],j['missing'],gt,pr)
            status['groups_completed']+=1;atomic_json(root/'status.json',status)
        status['status']='completed_with_input_gaps' if missing else 'completed'
    except Exception:
        status['status']='failed';status['error']=traceback.format_exc();raise
    finally:
        status['updated_UTC']=dt.datetime.now(dt.timezone.utc).isoformat();atomic_json(root/'status.json',status)
        lock.close()


if __name__=='__main__':main()
