"""Identify which local longitude grid reproduces archived IODC projections.

Uses exact discrete source values, observed files and the production 5 km
nearest-neighbour rule. This is a provenance test, not a new viewing-angle model.
"""
from pathlib import Path
import hashlib,json
import h5py,numpy as np
from osgeo import gdal
from pyresample import geometry,kd_tree

OUT=Path(r'C:\work\ls4t-msg\cases\official\results\production_assessment')
STATIC=Path('E:/Static')
TIMES=['201708151200','201801151000','201808151300','202205151200','202206151200','202507151200','202512311000','202512311600']
gdal.UseExceptions()

def read(path):
    d=gdal.Open(str(path)); a=d.ReadAsArray(); return a

def summary(pred,observed):
    observed=observed.astype(np.int64);pred=pred.astype(np.int64)
    either=(pred!=0)|(observed!=0); both=(pred!=0)&(observed!=0)
    return {'n_samples':int(len(pred)),'either_valid':int(either.sum()),
      'both_valid':int(both.sum()),'both_missing':int((~either).sum()),
      'exact_on_either_valid':int(((pred==observed)&either).sum()),
      'exact_fraction_on_either_valid':float(((pred==observed)&either).sum()/max(either.sum(),1)),
      'exact_on_both_valid':int(((pred==observed)&both).sum()),
      'mask_disagreement':int(((pred!=0)!=(observed!=0)).sum())}

def metadata(f):
    keys=['PROJECTION_NAME','SATELLITE','PRODUCT_ALGORITHM_VERSION','IMAGE_ACQUISITION_TIME','NOMINAL_LAT','NOMINAL_LONG','MEAN_SSLAT','MEAN_SSLON']
    def cv(v):
        if isinstance(v,bytes):return v.decode('utf-8')
        if isinstance(v,np.ndarray):return [cv(x) for x in v.tolist()]
        if isinstance(v,np.generic):return v.item()
        return v
    return {k:cv(f.attrs[k]) for k in keys if k in f.attrs}

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    d=gdal.Open(str(STATIC/'combined_iodc_vza.tif'));gt=d.GetGeoTransform()
    rows,cols=np.meshgrid(np.arange(20,d.RasterYSize-20,25),np.arange(20,d.RasterXSize-20,25),indexing='ij')
    rows,cols=rows.ravel(),cols.ravel()
    lon=gt[0]+(cols+.5)*gt[1];lat=gt[3]+(rows+.5)*gt[5]
    target=geometry.SwathDefinition(lons=lon,lats=lat)
    rawlat=read(STATIC/'IODC_Lat.tif').astype(np.float64)/100
    rawlat=np.flipud(rawlat)
    maps={};result={'target_samples':int(rows.size),'target_pixel_convention':'pixel centers',
        'sample_grid_step_pixels':25,'radius_m':5000,'native_latitude_flip':True,
        'native_longitude_flip':False,'lst':{},'view_angles':{}}
    for label,name in [('41.5','IODC_Lon.tif'),('45.5','IODC_Lon-2022.tif')]:
        rawlon=read(STATIC/name).astype(np.float64)/100
        bad=(np.abs(rawlat)>90)|(np.abs(rawlon)>180)
        slat=rawlat.copy();slon=rawlon.copy();slat[bad]=np.nan;slon[bad]=np.nan
        swath=geometry.SwathDefinition(lons=slon,lats=slat)
        vi,vo,ix,dist=kd_tree.get_neighbour_info(swath,target,5000,neighbours=1,epsilon=0,reduce_data=False)
        flat=np.flatnonzero(vi);good=ix<len(flat)
        pick=np.full(rows.size,-1,dtype=np.int64)
        pick[np.flatnonzero(vo)[good]]=flat[ix[good]]
        maps[label]=pick
        print('NEIGHBOUR MAP',label,'matched',int((pick>=0).sum()),flush=True)
    def mapped(raw,label,missing):
        pick=maps[label];out=np.zeros(rows.size,dtype=np.uint16);valid=pick>=0
        values=raw.ravel()[pick[valid]].copy();values[values==missing]=0
        out[valid]=values.astype(np.uint16);return out
    for ts in TIMES:
        suffix=f'{ts[:4]}/{ts[4:6]}/{ts[6:8]}'
        native=Path('E:/PRODUCTS/MSG-IODC/MLST/HDF5')/suffix/f'HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_{ts}'
        tif=Path('E:/PRODUCTS/MSG-IODC/MLST/GEOTIFF')/suffix/(native.name+'.tif')
        if not native.exists() or not tif.exists():
            result['lst'][ts]={'missing_local':True};continue
        observed=read(tif)[rows,cols]
        with h5py.File(native) as f:
            raw=f['LST'][...];missing=f['LST'].attrs['MISSING_VALUE']
            item={'native':str(native),'projected':str(tif),'metadata':metadata(f),'hypotheses':{}}
        for label in maps:item['hypotheses'][label]=summary(mapped(raw,label,missing),observed)
        result['lst'][ts]=item
        print(ts,{k:round(v['exact_fraction_on_either_valid'],4) for k,v in item['hypotheses'].items()},flush=True)
    for var in ['VZA','VAA']:
        native=STATIC/'IODC'/f'HDF5_LSASAF_MSG_{var}_IODC-Disk_202406041200'
        with h5py.File(native) as f:
            raw=f[var][...];missing=f[var].attrs['MISSING_VALUE'];meta=metadata(f)
        observed=read(STATIC/f'combined_iodc_{var.lower()}.tif')[rows,cols]
        # Angle output uses signed values and -32768 NoData, unlike LST uint16.
        item={'native':str(native),'metadata':meta,'hypotheses':{}}
        for label,pick in maps.items():
            predicted=np.full(rows.size,-32768,dtype=np.int16);ok=pick>=0
            values=raw.ravel()[pick[ok]].copy();values[values==missing]=-32768;predicted[ok]=values
            both=(observed!=-32768)&(predicted!=-32768)
            delta=(predicted[both].astype(float)-observed[both])/100
            if var=='VAA':delta=(delta+180)%360-180
            item['hypotheses'][label]={'common_valid':int(both.sum()),'exact_common':int((delta==0).sum()),
                'median_abs_difference_degrees':float(np.median(np.abs(delta))),
                'p95_abs_difference_degrees':float(np.quantile(np.abs(delta),.95))}
        result['view_angles'][var]=item
        print(var,item['hypotheses'],flush=True)
    (OUT/'iodc_geolocation_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    np.savez_compressed(OUT/'geolocation_sample_indices.npz',rows=rows,cols=cols,old=maps['41.5'],new=maps['45.5'])

if __name__=='__main__':main()
