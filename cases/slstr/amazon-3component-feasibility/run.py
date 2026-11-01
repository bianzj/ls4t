"""Run a single SLSTR daytime v5 trial and record diagnostics in the result folder."""
from pathlib import Path
import hashlib, json, time, traceback, os, sys, shutil
import numpy as np
from osgeo import gdal
import retrieval_v5 as model

HERE=Path(__file__).resolve().parent
cfg=json.loads((HERE/'config.json').read_text(encoding='utf-8'))
scene=cfg['scene']; year=cfg['year']; source=Path(cfg['source_root'])
run=Path(cfg['output_root'])
run.mkdir(parents=True,exist_ok=False)
started=time.time(); report={'state':'running','configuration':cfg,'files':{},'code_sha256':{},'started_epoch':started}

def save():
 (run/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
def stamp(p):
 s=p.stat();return {'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
def read(p):
 ds=gdal.Open(str(p),gdal.GA_ReadOnly)
 if ds is None:raise FileNotFoundError(p)
 data=ds.ReadAsArray();ds=None;return data

gdal.UseExceptions()
try:
 for name in ('retrieval_v5.py','run.py','scene_helpers.py','config.json'):
  p=HERE/name
  report['code_sha256'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 tif=source/str(year)/'tif'/scene
 lst=source/str(year)/'lst'/scene
 inputs=[tif/f'{k}_{view}.tif' for k in ('vza','vaa','cloud') for view in ('nadir','obliq')]
 inputs += [tif/'lat_obliq.tif',tif/'lon_obliq.tif',tif/'sza_obliq.tif',tif/'saa_obliq.tif',lst/'lst_nadir.tif',lst/'lst_obliq.tif',Path(cfg['lai']),source/'base/type/type_world_1000.tif',source/'base/emis/AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif',source/'base/emis/IGBP_Emi.txt']
 for p in inputs:
  if not p.is_file():raise FileNotFoundError(p)
  report['files'][str(p)]=stamp(p)
 sza=read(tif/'sza_obliq.tif').astype('float32')/100
 solar_day=np.isfinite(sza)&(sza>=0)&(sza<90)
 report['solar_day_pixels']=int(solar_day.sum())
 if not solar_day.any():raise ValueError('No daytime solar angles in selected scene')
 save();print('Loading global auxiliary fields and running daytime scene',flush=True)
 model.setup(str(source),tuple(cfg['region_wsen']),cfg['quality_control'],str(run/'scene'))
 scene_name,status,count=model.scene(year,scene)
 report.update({'scene_status':status,'valid_pixels':int(count)})
 if status!='written':raise RuntimeError('Trial did not produce images: '+status)
 result_dir=run/'scene'/scene; names=model.PRODUCTS
 marker=json.loads((result_dir/'bayes_5x5_homogeneous.json').read_text())
 report['quality_control']=marker['quality_control']
 report['quality_counts']=marker['quality_counts']
 for filename in ('lat_obliq.tif','lon_obliq.tif'):
  shutil.copy2(tif/filename,result_dir/filename)
  source_hash=hashlib.sha256((tif/filename).read_bytes()).hexdigest()
  assert hashlib.sha256((result_dir/filename).read_bytes()).hexdigest()==source_hash
  report.setdefault('geolocation_sha256',{})[filename]=source_hash
 arrays=np.stack([read(result_dir/name) for name in names]);valid=np.all(np.isfinite(arrays)&(arrays>0),axis=0)
 report['valid_pixels_recounted']=int(valid.sum())
 report['positive_mask_mismatch']=int(np.any((arrays>0)!=valid,axis=0).sum())
 report['band_stats']={}
 for name,a in zip(names,arrays):
  z=a[valid]
  report['band_stats'][name]={'min':float(z.min()),'p01':float(np.percentile(z,1)),'median':float(np.median(z)),'p99':float(np.percentile(z,99)),'max':float(z.max())}
 report['soil_sun_lt_shade']=int((arrays[2,valid]<arrays[3,valid]-1e-3).sum())
 report['soil_below_250K']=int((arrays[0,valid]<250).sum())
 report['sun_above_380K']=int((arrays[2,valid]>380).sum())
 report['valid_daytime_fraction']=float(solar_day[valid].mean()) if valid.any() else None
 input_min=cfg['quality_control']['input_lst_min_k']
 output_min=cfg['quality_control']['component_temp_min_k']
 tn=read(lst/'lst_nadir.tif')[:,model.adjust_xmin_no_g:model.adjust_xmax_no_g].astype(np.float32)/100
 to=read(lst/'lst_obliq.tif').astype(np.float32)/100
 report['filter_verification']={
  'nighttime_output_pixels':int((valid&~solar_day).sum()),
  'output_pixels_with_input_below_min':int((valid&((tn<input_min)|(to<input_min))).sum()),
  'output_pixels_with_any_band_below_min':int((valid&np.any(arrays<output_min,axis=0)).sum()),
  'minimum_input_lst_at_valid_output_K':float(min(tn[valid].min(),to[valid].min())),
  'minimum_output_temperature_K':float(arrays[:,valid].min()),
  'nodata_value':0}
 assert report['positive_mask_mismatch']==0,'Output band masks differ'
 assert report['valid_pixels_recounted']==count,'Valid pixel count differs'
 assert report['filter_verification']['nighttime_output_pixels']==0,'Nighttime result found'
 assert report['filter_verification']['output_pixels_with_input_below_min']==0,'Cold input reached output'
 assert report['filter_verification']['output_pixels_with_any_band_below_min']==0,'Cold component reached output'
 if cfg.get('baseline_output_root'):
  baseline=Path(cfg['baseline_output_root'])/'scene'/scene
  oldsoil=read(baseline/'soil.tif');oldvalid=np.isfinite(oldsoil)&(oldsoil>0)
  report['baseline_filter_comparison']={
   'baseline_valid_pixels':int(oldvalid.sum()),'new_valid_pixels':int(valid.sum()),
   'removed_baseline_pixels':int((oldvalid&~valid).sum()),
   'new_only_pixels':int((valid&~oldvalid).sum()),
   'baseline_soil_below_250K':int((oldvalid&(oldsoil<250)).sum()),
   'baseline_soil_below_250K_still_valid':int((oldvalid&(oldsoil<250)&valid).sum()),
   'previous_coldest_pixel_output_K':arrays[:,366,769].tolist()}
 existing=source/str(year)/'lsct3_components'/scene
 compare={}
 for name,new in zip(names,arrays):
  oldpath=existing/name
  if not oldpath.exists():continue
  old=read(oldpath); common=(old>0)&np.isfinite(old)&valid;diff=np.abs(new[common]-old[common])
  compare[name]={'old_valid':int(((old>0)&np.isfinite(old)).sum()),'common_valid':int(common.sum()),'new_only':int((valid&~((old>0)&np.isfinite(old))).sum()),'old_only':int((((old>0)&np.isfinite(old))&~valid).sum()),'mae_k':float(diff.mean()) if diff.size else None,'max_difference_k':float(diff.max()) if diff.size else None}
 report['comparison_with_existing_scene']=compare
 report['inputs_unchanged']=all(stamp(Path(p))==v for p,v in report['files'].items())
 assert report['inputs_unchanged'],'Inputs changed during this run'
 report['scientific_limit']='Existing-product agreement is reproducibility evidence only, not independent validation. No posterior uncertainty output; daytime sampled only. Scene TIFF has pixel-index coordinates and requires paired lat/lon for map geolocation.'
 report['state']='complete';report['elapsed_seconds']=round(time.time()-started,2);save();print(json.dumps({'state':report['state'],'valid_pixels':report['valid_pixels'],'elapsed_seconds':report['elapsed_seconds'],'band_stats':report['band_stats'],'comparison':compare}),flush=True)
except Exception as exc:
 report['state']='failed';report['error']=repr(exc);report['traceback']=traceback.format_exc();report['elapsed_seconds']=round(time.time()-started,2);save();raise
