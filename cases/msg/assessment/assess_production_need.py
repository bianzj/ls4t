"""Small, isolated full-scene experiments for deciding reprocessing scope.

The historical production entry and E:/ products remain read-only. Each run
records its exact in-memory adaptations and input hashes. Signed decoding is a
diagnostic only: the projected zero/NoData ambiguity is deliberately retained.
"""
from pathlib import Path
import argparse
import contextlib
import datetime as dt
import difflib
import hashlib
import json
import os
import sys
import time
import traceback

import h5py
import numpy as np
from osgeo import gdal
from run_single_scene_windows import Tee, sha256, replace_once, comparison

SOURCE_SHA = '763de469c6023b2b830061658d9130fcc851b7f7e9397903c27ac2fa159df9c3'
BANDS = ('background_soil', 'canopy', 'sunlit_soil', 'shaded_soil')

def distribution(x):
    x=np.asarray(x); x=x[np.isfinite(x)]
    if not x.size: return {'n':0}
    return {'n':int(x.size),'mean':float(x.mean()),'p50':float(np.quantile(x,.5)),
            'p95':float(np.quantile(x,.95)),'p99':float(np.quantile(x,.99)),
            'max':float(x.max())}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--timestamp',required=True)
    p.add_argument('--variant',choices=['baseline','signed','signed_daylight'],required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    stamp=dt.datetime.strptime(args.timestamp,'%Y%m%d%H%M')
    assert stamp.minute==0 and 10<=stamp.hour<=16
    repo=Path(__file__).resolve().parents[3]
    sys.path.insert(0,str(repo))
    source_path=Path(__file__).with_name('msg_lsct3.2-iter.py')
    assert sha256(source_path)==SOURCE_SHA, 'Historical source changed; review adaptations.'
    out=args.output.resolve()/args.timestamp/args.variant
    out.mkdir(parents=True,exist_ok=True)
    report_path=out/'report.json'
    if report_path.exists(): raise FileExistsError(report_path)
    suffix=f'{stamp:%Y/%m/%d}'
    archive=Path('E:/PRODUCTS/LSCT/MLST_COMPONENT')/suffix/f'MSG_LSCT_{args.timestamp}.h5'
    inputs={
        'EURO':Path('E:/PRODUCTS/MSG/MLST/GEOTIFF')/suffix/f'HDF5_LSASAF_MSG_LST_MSG-Disk_{args.timestamp}.tif',
        'IODC':Path('E:/PRODUCTS/MSG-IODC/MLST/GEOTIFF')/suffix/f'HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_{args.timestamp}.tif',
        'LAI':Path('E:/PRODUCTS/MSG/MDLAI/GEOTIFF')/suffix/f'HDF5_LSASAF_MSG_LAI_MSG-Disk_{stamp:%Y%m%d}0000.tif',
        **{x:Path('E:/Static')/f'combined_{x}.tif' for x in ['euro_vza','euro_vaa','iodc_vza','iodc_vaa']},
        'land_cover':Path('E:/map/MCD12C1_2011_0.01.tif'),
        'soil_emissivity':Path('E:/lse/AG1km.v003.SoilEmi.ABI.Global.001D_LSE12.tif'),
        'vegetation_emissivity':Path('E:/lse/IGBP_Emi.txt')}
    for path in [archive,*inputs.values()]:
        if not path.is_file(): raise FileNotFoundError(path)
    source=source_path.read_text(encoding='utf-8')
    code=replace_once(source,'indir = "/media/hero/MSG/"',"indir = 'E:/'")
    code=replace_once(code,"outdir_root = indir + '/PRODUCTS/LSCT/MLST_COMPONENT/'",f'outdir_root = {out.as_posix()!r}')
    for name,old,value in [('kyear','2017, 2018',stamp.year),('kmonth','8, 13',stamp.month),('kday','1, 32',stamp.day),('khour','9, 17',stamp.hour)]:
        code=replace_once(code,f'for {name} in range({old}):',f'for {name} in range({value}, {value+1}):')
    if args.variant.startswith('signed'):
        for sat in ['e','i']:
            code=replace_once(code,f'lst_{sat} = lst_{sat} / 100.0 + 273.15',
                f'lst_{sat} = lst_{sat}.view(np.int16).astype(np.float64) / 100.0 + 273.15')
    if args.variant=='signed_daylight':
        marker='                        lst_e[bad_mask] = np.nan'
        code=replace_once(code,marker,'                        bad_mask |= (~np.isfinite(sza)) | (sza < 0) | (sza >= 90)\n'+marker)
    (out/'runtime_changes.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True),code.splitlines(True),fromfile=str(source_path),tofile=args.variant)),encoding='utf-8')
    output=out/suffix/f'MSG_LSCT_{args.timestamp}.h5'
    manifest={'status':'preflight','timestamp_UTC':stamp.isoformat()+'Z','variant':args.variant,
        'source':str(source_path),'source_sha256':SOURCE_SHA,'runner_sha256':sha256(__file__),
        'effective_source_sha256':hashlib.sha256(code.encode()).hexdigest(),
        'output':str(output),'archive':str(archive),'inputs':{},
        'limitations':['Pilot scenes are not a representative archive-wide error estimate.',
            'Signed TIFF correction does not recover valid 0 C observations encoded as NoData.',
            'All variants retain existing geolocation and view angles.',
            'Numerical replay agreement is not independent temperature accuracy.']}
    started=time.monotonic()
    with (out/'run.log').open('w',encoding='utf-8') as log:
        with contextlib.redirect_stdout(Tee(sys.stdout,log)),contextlib.redirect_stderr(Tee(sys.stderr,log)):
            try:
                for k,path in inputs.items():manifest['inputs'][k]={'path':str(path),'sha256':sha256(path),'bytes':path.stat().st_size}
                manifest['archive_sha256']=sha256(archive)
                manifest['status']='running'
                report_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
                namespace={'__name__':'__main__','__file__':str(source_path)}
                run_start=time.monotonic()
                exec(compile(code,str(source_path),'exec'),namespace)
                manifest['retrieval_seconds']=time.monotonic()-run_start
                if not output.is_file():raise RuntimeError('Entry did not produce the selected scene; inspect log.')
                manifest['versus_archive']=comparison(output,archive)
                a=namespace['result_u16']; valid=np.all(a!=0,axis=0); sza=namespace['sza']
                with h5py.File(archive) as f: oldvalid=np.all(f['data'][...]!=0,axis=0)
                manifest['daylight']={
                    'output_valid':int(valid.sum()),'output_valid_sza_ge90':int((valid & (sza>=90)).sum()),
                    'archive_valid_sza_ge90':int((oldvalid & (sza>=90)).sum()),
                    'output_valid_sza_ge85':int((valid & (sza>=85)).sum()),
                    'output_valid_sza_range':[float(sza[valid].min()),float(sza[valid].max())]}
                inverse=namespace['inv_planck']; prior=namespace['x_prior']
                manifest['joint_update_temperature_change_K']={}
                for k,key in enumerate(['bs1_final','bs2_final','bv_final']):
                    delta=inverse(10.5,namespace[key])-inverse(10.5,prior[...,k])
                    manifest['joint_update_temperature_change_K'][['sunlit_soil','shaded_soil','canopy'][k]]=distribution(np.abs(delta[valid]))
                manifest['output_sha256']=sha256(output)
                assert sha256(source_path)==SOURCE_SHA and sha256(archive)==manifest['archive_sha256']
                manifest['production_source_and_archive_unchanged']=True
                manifest['status']='completed'
                print('PILOT COMPLETE',args.timestamp,args.variant,manifest['daylight'],flush=True)
            except Exception:
                manifest['status']='failed';manifest['error']=traceback.format_exc();raise
            finally:
                manifest['elapsed_seconds']=time.monotonic()-started
                report_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
