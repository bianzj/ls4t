"""Compare the view-geometry provider with independent native angle products."""
from pathlib import Path
import json
import h5py
import numpy as np
from msg_view_geometry import look_angles,sha

HERE=Path(__file__).resolve().parent

def read(path,key):
    with h5py.File(path) as f:
        data=f[key][...].astype(float)
        data[data==f[key].attrs['MISSING_VALUE']]=np.nan
        data/=float(f[key].attrs['SCALING_FACTOR'])
        meta={k:float(f.attrs[k]) for k in ['MEAN_SSLAT','MEAN_SSLON','NOMINAL_LAT','NOMINAL_LONG']}
        stamp=f.attrs['IMAGE_ACQUISITION_TIME'].decode()
    return data[::16,::16],meta,stamp

def main():
    checks=[];sources=[]
    for view,disk,stamp,angle_suffix in [('IODC','IODC-Disk','202207011000','_202406041200'),('EURO','MSG-Disk','202303210900','')]:
        base=Path('E:/Static')/view
        latpath=base/f'HDF5_LSASAF_MSG_LAT_{disk}_{stamp}'
        lonpath=base/f'HDF5_LSASAF_MSG_LON_{disk}_{stamp}'
        lat,_,_=read(latpath,'LAT');lon,_,_=read(lonpath,'LON')
        sources.extend([str(latpath),str(lonpath)])
        for variable in ['VZA','VAA']:
            path=base/f'HDF5_LSASAF_MSG_{variable}_{disk}{angle_suffix}'
            observed,meta,when=read(path,variable)
            sources.append(str(path))
            good=np.isfinite(lat)&np.isfinite(lon)&np.isfinite(observed)&(np.abs(lat)<=90)&(np.abs(lon)<=180)
            z,a=look_angles(lat,lon,meta['MEAN_SSLAT'],meta['MEAN_SSLON'])
            good&=(z<85)
            predicted=z if variable=='VZA' else a
            error=predicted[good]-observed[good]
            if variable=='VAA':error=(error+180)%360-180
            record={'view':view,'variable':variable,'native_angle_file':str(path),'timestamp_native':when,'source_position':'MEAN_SS','satellite_latitude':meta['MEAN_SSLAT'],'satellite_longitude':meta['MEAN_SSLON'],'n':int(good.sum()),'mean_abs_error_deg':float(np.mean(np.abs(error))),'p95_abs_error_deg':float(np.quantile(np.abs(error),.95)),'max_abs_error_deg':float(np.max(np.abs(error))),'native_latlon_orientation':'unflipped native HDF5 latitude and longitude','native_pixel_reference':'native LAT/LON pixel coordinates'}
            record['pass']=record['n']>10000 and record['p95_abs_error_deg']<.25
            checks.append(record)
    report={'pass':all(r['pass'] for r in checks),'helper_sha256':sha(HERE/'msg_view_geometry.py'),'native_angle_checks':checks,'source_files_sha256':{path:sha(path) for path in sorted(set(sources))},'geometry':'WGS84 ellipsoid; ground height zero; satellite geocentric radius42164km; azimuth ground-to-satellite clockwise from north','interpretation':'Agreement is with native provider angles at their stated source timestamps. It does not validate missing early ephemeris or override inconsistent scene metadata. Small differences include native 0.01 degree quantization, specified orbit radius and ground height approximation.'}
    (HERE/'geometry_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    assert report['pass']

if __name__=='__main__':main()
