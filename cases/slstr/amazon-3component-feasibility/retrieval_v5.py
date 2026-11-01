#!/usr/bin/env python3
"""Homogeneous three-component SLSTR retrieval from freshly recomputed LST.

The 5x5 nadir and oblique samples contribute one Gaussian radiance posterior.
A soft 9 +/- 10 K prior on oblique-view aggregate soil minus vegetation is
applied by two Gauss-Newton steps. This is a Laplace/MAP approximation to the
EVO sampling posterior, chosen for regional-scale processing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import h5py
import numpy as np
from scipy.ndimage import uniform_filter
from osgeo import gdal

from base.radiometry import inv_planck, planck
from base.rt.hotspot import hotspot_layer
from base.slstr.slstr_grid import adjust_xmin_no_g, adjust_xmax_no_g
import scene_helpers as lst_module

WL = 10.8
PRODUCTS = ('soil.tif', 'vegetation.tif', 'sunlit_soil.tif', 'shaded_soil.tif')
METHOD = 'homogeneous_3component_bayes_map_5x5_lai_only_v5'
PRIOR_TEMP = np.array([50., 50., 10.])
PRIOR_RHO = .25
NOISE_K = 10.
GAP_MEAN_K = 9.
GAP_SD_K = 10.
MIN_SAMPLES_VIEW = 8
TEMP_MIN, TEMP_MAX = 200., 400.
SCENE_TIME = re.compile(r'RBT____(\d{8})T(\d{6})_(\d{8})T(\d{6})')
_STATE = {}


def read(path: Path) -> np.ndarray:
    ds = gdal.Open(str(path), gdal.GA_ReadOnly)
    if ds is None:
        raise FileNotFoundError(path)
    arr = ds.ReadAsArray()
    ds = None
    lst_module.drop_file_cache(path)
    return np.asarray(arr)


def solar_from_time(scene: str, lat: np.ndarray, lon: np.ndarray):
    match = SCENE_TIME.search(scene)
    if not match:
        raise ValueError(f'No acquisition timestamp in {scene}')
    start = datetime.strptime(match.group(1)+match.group(2), '%Y%m%d%H%M%S')
    end = datetime.strptime(match.group(3)+match.group(4), '%Y%m%d%H%M%S')
    mid = start+(end-start)/2
    day = mid.timetuple().tm_yday
    minutes = mid.hour*60+mid.minute+mid.second/60
    gamma = 2*np.pi/365*(day-1+(minutes/60-12)/24)
    eq = 229.18*(.000075+.001868*np.cos(gamma)-.032077*np.sin(gamma)
                 -.014615*np.cos(2*gamma)-.040849*np.sin(2*gamma))
    dec = (.006918-.399912*np.cos(gamma)+.070257*np.sin(gamma)
           -.006758*np.cos(2*gamma)+.000907*np.sin(2*gamma)
           -.002697*np.cos(3*gamma)+.00148*np.sin(3*gamma))
    latr = np.deg2rad(lat)
    ha = np.deg2rad(np.mod(minutes+eq+4*lon,1440)/4-180)
    cosz = np.sin(latr)*np.sin(dec)+np.cos(latr)*np.cos(dec)*np.cos(ha)
    zenith = np.rad2deg(np.arccos(np.clip(cosz,-1,1)))
    azimuth = np.mod(np.rad2deg(np.arctan2(np.sin(ha),np.cos(ha)*np.sin(latr)-np.tan(dec)*np.cos(latr)))+180,360)
    return zenith.astype(np.float32),azimuth.astype(np.float32)


def derivative(T):
    return (planck(WL,T+.01)-planck(WL,T-.01))/.02


def box_sum(a: np.ndarray) -> np.ndarray:
    return uniform_filter(a.astype(np.float32,copy=False),size=5,mode='constant',cval=0.)*25.


def write(path: Path, data: np.ndarray, description: str):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp = path.with_suffix('.tmp.tif')
    ds = gdal.GetDriverByName('GTiff').Create(str(tmp),data.shape[1],data.shape[0],1,
      gdal.GDT_Float32,options=['TILED=YES','COMPRESS=DEFLATE','BIGTIFF=IF_SAFER'])
    if ds is None:
        raise RuntimeError(f'Cannot write {tmp}')
    ds.SetGeoTransform((0,1,0,0,0,1))
    band=ds.GetRasterBand(1);band.SetNoDataValue(0);band.SetDescription(description)
    band.WriteArray(data.astype(np.float32,copy=False));band.FlushCache();ds.FlushCache();ds=None
    os.replace(tmp,path)


def temperature_quality_policy(input_lst_min_k=285.,component_temp_min_k=285.):
    input_lst_min_k=float(input_lst_min_k)
    component_temp_min_k=float(component_temp_min_k)
    if not np.isfinite(input_lst_min_k) or not TEMP_MIN<=input_lst_min_k<=360.:
        raise ValueError('Input LST minimum must be between 200 and 360 K')
    if not np.isfinite(component_temp_min_k) or not TEMP_MIN<=component_temp_min_k<=TEMP_MAX:
        raise ValueError('Component minimum must be between 200 and 400 K')
    return {'daytime_only':True,'input_lst_min_k':input_lst_min_k,
      'component_temp_min_k':component_temp_min_k,
      'input_pair_rule':'both_views_at_or_above_minimum',
      'output_rule':'all_three_components_at_or_above_minimum',
      'invalid_value':0}


def setup(root: str,bounds: tuple[float,float,float,float],quality_control=None,output_dir=None):
    global _STATE
    root = Path(root)
    base = root/'base'
    if quality_control is not None:
        if quality_control.get('daytime_only') is not True:
            raise ValueError('This production case only supports daytime')
        quality_control=temperature_quality_policy(quality_control['input_lst_min_k'],
                                                   quality_control['component_temp_min_k'])
    _STATE = {'root':root,'bounds':bounds,'lai_key':None,'quality_control':quality_control,
      'output_dir':Path(output_dir) if output_dir is not None else None,
      'type':read(base/'type/type_world_1000.tif'),
      'soil_emis':read(base/'emis/AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'),
      'veg_emis':np.loadtxt(base/'emis/IGBP_Emi.txt',dtype=np.float32)[:,0]}


def lai_for_scene(year:int,scene:str):
    match=SCENE_TIME.search(scene)
    if not match:
        raise ValueError('Scene time missing')
    day=datetime.strptime(match.group(1),'%Y%m%d')
    doy4=(int(day.strftime('%j'))//4)*4+1
    folder=('lai_2002-2020_0p01deg' if year<=2020 else 'lai_2021-2025_0p01deg')
    root=Path('H:/data/rs/lai/lai-modis-doy')/str(year)
    candidates=[root/f'LAI_{year}{doy4:03d}.h5',root/f'lai_{year}{doy4:03d}.h5']
    path=next((p for p in candidates if p.is_file()),candidates[0])
    if _STATE['lai_key']!=path:
        with h5py.File(path,'r') as h:
            _STATE['lai']=h['/data'][:]
        lst_module.drop_file_cache(path)
        _STATE['lai_key']=path
    return _STATE['lai']


def scene(year:int,scene_name:str):
    root=_STATE['root'];src=root/str(year);tif=src/'tif'/scene_name
    quality_control=_STATE.get('quality_control')
    out=Path(_STATE['output_dir'])/scene_name
    signature=out/'bayes_5x5_homogeneous.json'
    lst_paths=[src/'lst'/scene_name/f'lst_{view}.tif' for view in ('nadir','obliq')]
    if (signature.is_file() and all((out/name).is_file() for name in PRODUCTS)
            and all(path.is_file() and signature.stat().st_mtime_ns>path.stat().st_mtime_ns
                    for path in lst_paths)):
        try:
            metadata=json.loads(signature.read_text())
            if metadata.get('method')==METHOD and metadata.get('quality_control')==quality_control:
                return scene_name,'existing',int(metadata.get('valid_pixels',0))
        except (OSError,ValueError):
            pass
    required=[tif/f'{name}_{view}.tif' for name in ('vza','vaa','cloud') for view in ('nadir','obliq')]
    required += [tif/'lat_obliq.tif',tif/'lon_obliq.tif',src/'lst'/scene_name/'lst_nadir.tif',src/'lst'/scene_name/'lst_obliq.tif']
    if any(not p.is_file() for p in required):
        return scene_name,'missing_input',0
    lat=read(tif/'lat_obliq.tif').astype(np.float32)/100.
    lon=read(tif/'lon_obliq.tif').astype(np.float32)/100.
    lat=np.where(lat>=90,-(lat-90),lat);lon=np.where(lon>=180,-(lon-180),lon)
    h,w=lat.shape
    west,south,east,north=_STATE['bounds']
    region=np.isfinite(lat)&np.isfinite(lon)&(lon>=west)&(lon<=east)&(lat>=south)&(lat<=north)
    if not region.any():
        return scene_name,'outside_region',0
    sza_path=next((p for p in (tif/'sza_obliq.tif',tif/'sza_nadir.tif') if p.is_file()),None)
    saa_path=next((p for p in (tif/'saa_obliq.tif',tif/'saa_nadir.tif') if p.is_file()),None)
    if sza_path and saa_path:
        sza=read(sza_path).astype(np.float32)/100.
        saa=read(saa_path).astype(np.float32)/100.
        if sza.shape!=(h,w):sza=sza[:,adjust_xmin_no_g:adjust_xmax_no_g]
        if saa.shape!=(h,w):saa=saa[:,adjust_xmin_no_g:adjust_xmax_no_g]
        solar_source='saved_angles'
    else:
        sza,saa=solar_from_time(scene_name,lat,lon)
        solar_source='scene_midpoint'
    if sza.shape!=(h,w) or saa.shape!=(h,w):
        raise ValueError('Solar angle grid shape mismatch')
    lai0=lai_for_scene(year,scene_name)
    row,col=lst_module.grid_index(lat,lon,18000,36000,.01)
    lai=lai0[row,col].astype(np.float32)/1000.
    cls=np.clip(_STATE['type'][row,col].astype(np.int16),0,17)
    es=_STATE['soil_emis'][row,col].astype(np.float32)/1000.
    ev=_STATE['veg_emis'][cls]/1000.
    fvc=1-np.exp(-.825*lai*.5)
    emis=np.minimum(es*(1-fvc)+ev*fvc+(1-es)*ev*.05*(1-fvc),.995)
    views=[];solar_good=np.isfinite(sza)&(sza>=0)&(sza<90)
    for view in ('nadir','obliq'):
        raw={name:read(tif/f'{name}_{view}.tif') for name in ('vza','vaa','cloud')}
        lst=read(src/'lst'/scene_name/f'lst_{view}.tif')
        if view=='nadir':
            raw={k:a[:,adjust_xmin_no_g:adjust_xmax_no_g] for k,a in raw.items()}
            lst=lst[:,adjust_xmin_no_g:adjust_xmax_no_g]
        if lst.shape!=(h,w) or any(a.shape!=(h,w) for a in raw.values()):
            raise ValueError(f'{view} array shape mismatch')
        vza=raw['vza'].astype(np.float32)/100.
        vaa=raw['vaa'].astype(np.float32)/100.
        tlst=lst.astype(np.float32)/100.
        vza_model=np.clip(vza,0,89.9);sza_model=np.clip(sza,0,89.9)
        fv=1-np.exp(-.5*lai/np.cos(np.deg2rad(vza_model)))
        with np.errstate(invalid='ignore',divide='ignore',over='ignore'):
            sun=hotspot_layer(lai,.25,vza_model,sza_model,np.abs(vaa-saa))
        soil=1-fv
        shade=soil-sun
        W=np.stack([es*sun,es*shade,ev*fv],axis=-1).astype(np.float32)
        good=(region&solar_good&(raw['cloud']==0)&(vza>=0)&(vza<80)&
          np.isfinite(lai)&(lai>.05)&(lai<=10)&np.isfinite(es)&(es>0)&
          np.isfinite(ev)&(ev>0)&np.isfinite(tlst)&(tlst>=200)&(tlst<=360)&
          np.isfinite(W).all(axis=-1)&(W>=-1e-6).all(axis=-1))
        W[~good]=0
        Y=(planck(WL,tlst)*emis).astype(np.float32)
        Y[~good]=0
        views.append((W,Y,good,tlst,sun,soil))
    quality_counts={'base_paired_daytime_pixels':int((views[0][2]&views[1][2]).sum()),
                    'paired_input_below_min_rejected':0,
                    'component_below_min_rejected':0}
    if quality_control is not None:
        # Remove the complete observation pair before any 5x5 accumulation.
        # A cold observation must not influence another pixel's inversion.
        threshold=quality_control['input_lst_min_k']
        paired_temperature_good=(np.isfinite(views[0][3])&np.isfinite(views[1][3])&
                                  (views[0][3]>=threshold)&(views[1][3]>=threshold))
        quality_counts['paired_input_below_min_rejected']=int(
          (views[0][2]&views[1][2]&~paired_temperature_good).sum())
        for view,(W,Y,good,*_) in zip(('nadir','obliq'),views):
            quality_counts[f'input_observations_removed_{view}']=int((good&~paired_temperature_good).sum())
            good &= paired_temperature_good
            W[~good]=0
            Y[~good]=0
    quality_counts['paired_daytime_pixels_after_input_filter']=int((views[0][2]&views[1][2]).sum())
    if not (views[0][2]&views[1][2]).any():
        out.mkdir(parents=True,exist_ok=True)
        (out/'no_valid_pixels.json').write_text(json.dumps({'method':METHOD,'reason':'no paired valid day pixels'}))
        for name in PRODUCTS:(out/name).unlink(missing_ok=True)
        signature.unlink(missing_ok=True)
        return scene_name,'no_valid',0
    counts=[box_sum(z[2].astype(np.float32)) for z in views]
    selected=(views[0][2]&views[1][2]&(counts[0]>=MIN_SAMPLES_VIEW-1e-3)&
              (counts[1]>=MIN_SAMPLES_VIEW-1e-3))
    selected[:2]=False;selected[-2:]=False;selected[:,:2]=False;selected[:,-2:]=False
    rr,cc=np.where(selected)
    quality_counts['selected_5x5_centers']=int(len(rr))
    if not len(rr):
        out.mkdir(parents=True,exist_ok=True)
        (out/'no_valid_pixels.json').write_text(json.dumps({'method':METHOD,'reason':'no 5x5 paired neighborhood'}))
        for name in PRODUCTS:(out/name).unlink(missing_ok=True)
        signature.unlink(missing_ok=True)
        return scene_name,'no_valid',0
    gram=np.zeros((h,w,3,3),dtype=np.float32)
    rhs=np.zeros((h,w,3),dtype=np.float32)
    for W,Y,*_ in views:
        for i in range(3):
            rhs[:,:,i]+=box_sum(W[:,:,i]*Y)
            for j in range(i,3):
                gram[:,:,i,j]+=box_sum(W[:,:,i]*W[:,:,j])
    for i in range(3):
        for j in range(i):gram[:,:,i,j]=gram[:,:,j,i]
    d300=float(derivative(300.))
    prior_cov=np.outer(PRIOR_TEMP,PRIOR_TEMP)*PRIOR_RHO
    np.fill_diagonal(prior_cov,PRIOR_TEMP**2)
    prior_precision=np.linalg.inv(prior_cov*d300*d300)
    x0=np.repeat(float(planck(WL,300.)),3)
    outputs=np.zeros((4,h,w),dtype=np.float32)
    valid_count=0
    order_count=0
    for start in range(0,len(rr),8192):
        r=rr[start:start+8192];c=cc[start:start+8192]
        center_T=(views[0][3][r,c]+views[1][3][r,c])/2
        sigma2=np.maximum((NOISE_K*derivative(center_T))**2,1e-10)
        A=gram[r,c].astype(np.float64)/sigma2[:,None,None]+prior_precision[None,:,:]
        b=rhs[r,c].astype(np.float64)/sigma2[:,None]+prior_precision@x0
        try:x=np.linalg.solve(A,b[...,None])[...,0]
        except np.linalg.LinAlgError:continue
        share=np.clip(views[1][4][r,c]/np.maximum(views[1][5][r,c],1e-6),0,1)
        for _ in range(2):
            xs=np.clip(x,float(planck(WL,TEMP_MIN)),float(planck(WL,TEMP_MAX)))
            mix=share*xs[:,0]+(1-share)*xs[:,1]
            soil_T=inv_planck(WL,mix)
            veg_T=inv_planck(WL,xs[:,2])
            diff=soil_T-veg_T
            dsoil=1/np.maximum(derivative(soil_T),1e-8)
            dveg=1/np.maximum(derivative(veg_T),1e-8)
            J=np.stack([share*dsoil,(1-share)*dsoil,-dveg],axis=-1)
            target=GAP_MEAN_K-diff+np.sum(J*x,axis=1)
            ag=A+np.einsum('ni,nj->nij',J,J)/GAP_SD_K**2
            bg=b+J*(target/GAP_SD_K**2)[:,None]
            try:x=np.linalg.solve(ag,bg[...,None])[...,0]
            except np.linalg.LinAlgError:break
        # Daytime sunlit soil must not be cooler than shaded soil in this
        # three-component parameterization. Project active cases onto the
        # exact x_sun == x_shade boundary of the local quadratic objective.
        reversed_order=x[:,0]<x[:,1]
        if reversed_order.any():
            C=np.array([[1.,0.],[1.,0.],[0.,1.]])
            small_A=np.einsum('ki,nkl,lj->nij',C,ag[reversed_order],C)
            small_b=bg[reversed_order]@C
            try:
                reduced=np.linalg.solve(small_A,small_b[...,None])[...,0]
                x[reversed_order]=reduced@C.T
            except np.linalg.LinAlgError:
                pass
            order_count+=int(reversed_order.sum())
        lo=float(planck(WL,TEMP_MIN));hi=float(planck(WL,TEMP_MAX))
        okay=np.isfinite(x).all(axis=1)&(x>=lo).all(axis=1)&(x<=hi).all(axis=1)
        if not okay.any():continue
        r=r[okay];c=c[okay];x=x[okay];share=share[okay]
        temp=inv_planck(WL,x)
        soil=inv_planck(WL,share*x[:,0]+(1-share)*x[:,1])
        if quality_control is not None:
            threshold=quality_control['component_temp_min_k']
            # Check the temperatures that will actually be stored in Float32.
            keep=((temp.astype(np.float32)>=threshold).all(axis=1)&
                   (soil.astype(np.float32)>=threshold))
            quality_counts['component_below_min_rejected']+=int((~keep).sum())
            r=r[keep];c=c[keep];temp=temp[keep];soil=soil[keep]
        outputs[0,r,c]=soil;outputs[1,r,c]=temp[:,2]
        outputs[2,r,c]=temp[:,0];outputs[3,r,c]=temp[:,1]
        valid_count+=len(r)
    if not valid_count:
        out.mkdir(parents=True,exist_ok=True)
        (out/'no_valid_pixels.json').write_text(json.dumps({'method':METHOD,'quality_control':quality_control,
          'quality_counts':quality_counts,'reason':'no posterior temperatures passing physical and quality filters'}))
        for name in PRODUCTS:(out/name).unlink(missing_ok=True)
        signature.unlink(missing_ok=True)
        return scene_name,'no_valid',0
    for name,array,description in zip(PRODUCTS,outputs,
      ('Soil mixture K','Vegetation K','Sunlit soil K','Shaded soil K')):
        write(out/name,array,description)
    (out/'no_valid_pixels.json').unlink(missing_ok=True)
    signature.write_text(json.dumps({'method':METHOD,'year':year,'scene':scene_name,
      'valid_pixels':valid_count,'sun_shade_order_active':order_count,
      'quality_control':quality_control,'quality_counts':quality_counts,
      'solar_source':solar_source,'LST_source':str(src/'lst')+'; not recomputed during this run'})+'\n')
    return scene_name,'written',valid_count


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--year',type=int,required=True)
    ap.add_argument('--bounds',type=float,nargs=4,required=True)
    ap.add_argument('--lst-report',type=Path,required=True)
    ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--min-input-lst-k',type=float,default=285.)
    ap.add_argument('--min-component-temp-k',type=float,default=285.)
    ap.add_argument('--output-dir',type=Path,required=True,
                    help='Scene output directory, normally beneath E:/lsct/lsct3')
    ap.add_argument('--report',type=Path,required=True)
    ap.add_argument('--max-scene-errors',type=int,default=0,
                    help='continue past up to this many bad scenes, recording each')
    args=ap.parse_args()
    lst_report=json.loads(args.lst_report.read_text())
    if lst_report.get('year')!=args.year or Path(lst_report.get('root','')).resolve()!=args.root.resolve():
        raise ValueError('LST report does not match requested region/year')
    scenes=sorted(set(lst_report.get('updated_scenes',[])))
    if not scenes:
        raise ValueError('No scenes with two freshly recomputed LST views')
    t0=time.time();count=Counter();pixels=0;errors=[];missing_scenes=[]
    args.report.parent.mkdir(parents=True,exist_ok=True)
    quality_control=temperature_quality_policy(args.min_input_lst_k,args.min_component_temp_k)
    with ProcessPoolExecutor(max_workers=args.workers,initializer=setup,
      initargs=(str(args.root),tuple(args.bounds),quality_control,str(args.output_dir))) as pool:
        future={pool.submit(scene,args.year,name):name for name in scenes}
        for i,f in enumerate(as_completed(future),1):
            try:
                name,status,n=f.result();count[status]+=1;pixels+=n
                if status=='missing_input':missing_scenes.append(name)
            except Exception as exc:
                count['error']+=1;errors.append({'scene':future[f],'error':repr(exc)[:350]})
            if i%100==0 or i==len(future):
                report={'method':METHOD,'quality_control':quality_control,'output_dir':str(args.output_dir),
                  'root':str(args.root),'year':args.year,'bounds_wsen':args.bounds,
                  'model_parameters':{'components':['sunlit_soil','shaded_soil','vegetation'],
                   'geometry':'homogeneous, measured per-pixel angles',
                   'window':'5x5 in each view; at least 8 valid pixels per view',
                   'hotspot':0.25,'soil_prior_sd_K':[50,50],
                   'vegetation_prior_sd_K':10,'prior_correlation':0.25,
                   'total_likelihood_sd_K':10,'soil_minus_vegetation_gap_K':[9,10],
                   'daytime_sunlit_at_least_shaded':True,
                   'posterior':'Gaussian radiance update plus 2-step MAP gap approximation',
                   'land_cover_mask':'none; IGBP class used only for vegetation emissivity',
                   'LAI_valid_range':'0.05 < LAI <= 10'},
                  'LST_report':str(args.lst_report),'queued':len(scenes),'done':i,'counts':dict(count),
                  'valid_pixels':pixels,'errors':errors,'missing_scenes':missing_scenes,
                  'max_scene_errors':args.max_scene_errors,'elapsed_s':round(time.time()-t0,1),
                  'complete':i==len(future) and len(errors)+len(missing_scenes)<=args.max_scene_errors}
                args.report.write_text(json.dumps(report,indent=2)+'\n')
                print(f'{args.year} {i}/{len(future)} {dict(count)} pixels={pixels} elapsed={time.time()-t0:.0f}s',flush=True)
    return 0 if report['complete'] else 3


if __name__=='__main__':
    sys.exit(main())
