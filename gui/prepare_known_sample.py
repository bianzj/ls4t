"""Extract a small real AHI/SLSTR example; source data are read-only.

Run with the GUI's GDAL-enabled Python. Only January 1 2019 is used. Selection
uses coverage/cloud flags and distance to (112 E, 32 N), never retrieval error.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import h5py
import numpy as np
from osgeo import gdal, osr
from base.calibration import legacy_split_window_model, save_split_window_model
from base.known_inputs import run_workbench
from base.radiometry import planck_radiance, inverse_planck

ROOT = Path('E:/remote-sensing')
DATA = ROOT / 'temperature-emissivity/multi-sensor-2019'
OUT = Path(__file__).resolve().parent / 'examples/ahi_slstr'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def geo_angles(lon, lat):
    # Nominal Himawari position, WGS84 ECEF -> local east/north/up.
    phi, lam = np.deg2rad([lat, lon])
    n = 6378137 / np.sqrt(1 - 6.69437999014e-3*np.sin(phi)**2)
    ground = np.array([n*np.cos(phi)*np.cos(lam), n*np.cos(phi)*np.sin(lam),
                       n*(1-6.69437999014e-3)*np.sin(phi)])
    slon = np.deg2rad(140.7)
    ray = np.array([42164000*np.cos(slon), 42164000*np.sin(slon), 0])-ground
    east = np.dot(ray, [-np.sin(lam), np.cos(lam), 0])
    north = np.dot(ray, [-np.sin(phi)*np.cos(lam), -np.sin(phi)*np.sin(lam), np.cos(phi)])
    up = np.dot(ray, [np.cos(phi)*np.cos(lam), np.cos(phi)*np.sin(lam), np.sin(phi)])
    return float(np.rad2deg(np.arctan2(np.hypot(east, north), up))), float(np.rad2deg(np.arctan2(east, north)) % 360)


def main():
    gdal.UseExceptions()
    osr.UseExceptions()
    OUT.mkdir(parents=True, exist_ok=True)
    seen, raw = {}, {}
    wgs = osr.SpatialReference(); wgs.ImportFromEPSG(4326)
    wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    base = gdal.Open(str(DATA/'ahi_tif/01/01/AHI_2019001_0250_bt1.tif'))
    srs = osr.SpatialReference(wkt=base.GetProjection())
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    x, y, _ = osr.CoordinateTransformation(wgs, srs).TransformPoint(112, 32)
    g = base.GetGeoTransform()
    cx, cy = int((x-g[0])/g[1]), int((y-g[3])/g[5])

    def pixel(path, x, y, key, thermal=False):
        path = Path(path)
        ds = gdal.Open(str(path))
        target = osr.SpatialReference(wkt=ds.GetProjection())
        target.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        xx, yy, _ = osr.CoordinateTransformation(srs, target).TransformPoint(x, y)
        gt = ds.GetGeoTransform()
        col, row = int((xx-gt[0])/gt[1]), int((yy-gt[3])/gt[5])
        # Native SLSTR 1 km BT: aligned 2x2 block, radiance averaging at each band.
        n = 2 if thermal and abs(gt[1]-1000) < .01 else 1
        if n == 2:
            col, row = col-1, row-1
        a = ds.ReadAsArray(col, row, n, n)
        seen[str(path)] = dict(path=str(path), size=path.stat().st_size)
        raw[key] = a
        if thermal:
            if np.any((a < 20000) | (a > 40000)):
                return float('nan')
            wl = 12. if 'bt2' in key else 10.85
            return float(inverse_planck(wl, np.mean(planck_radiance(wl, a*.01))))
        return float(a.mean())

    # Scan a 20x20 km window nearest the stated centre, without fitting/scoring.
    candidates = sorted([(dx,dy) for dx in range(-5,5) for dy in range(-5,5)], key=lambda p:(p[0]**2+p[1]**2,p))
    selected = None
    for dx,dy in candidates:
        col,row=cx+dx,cy+dy
        x,y=g[0]+(col+.5)*2000,g[3]-(row+.5)*2000
        vals={}
        for field in ['bt1_nadir','bt2_nadir','bt1_obliq','bt2_obliq','cloud_nadir','cloud_obliq','time','tcw','vza_nadir','vza_obliq','sza_nadir','saa_nadir','vaa_nadir','vaa_obliq']:
            vals[field]=pixel(DATA/'s3a_tif'/f'S3A_2019001_day_{field}.tif',x,y,'slstr_'+field,field.startswith('bt'))
        if not all(np.isfinite(vals[k]) for k in ['bt1_nadir','bt2_nadir','bt1_obliq','bt2_obliq']): continue
        if vals['cloud_nadir'] != 0 or vals['cloud_obliq'] != 0 or vals['time'] <= 0: continue
        hhmm=int(vals['time']); minute=hhmm//100*60+hhmm%100
        if hhmm//100>23 or hhmm%100>59: continue
        nearest=int((minute+5)//10*10); stamp=f'{nearest//60:02d}{nearest%60:02d}'
        ap=DATA/'ahi_tif/01/01'/f'AHI_2019001_{stamp}'
        lp=DATA/'ahi_lst/01/01'/f'AHI_2019001_{stamp}_lst.tif'
        if not Path(str(ap)+'_bt1.tif').exists() or not lp.exists():continue
        # Legacy LST lacks georeferencing: only use as same-index validity mask,
        # never as geolocation or as an independently validated reference.
        ld=gdal.Open(str(lp))
        if (ld.RasterXSize,ld.RasterYSize)!=(base.RasterXSize,base.RasterYSize):raise ValueError('AHI mask grid size mismatch')
        av=float(ld.ReadAsArray(col,row,1,1).item())
        if not 22000<av<36500:continue
        a1=pixel(str(ap)+'_bt1.tif',x,y,'ahi_bt1')*.01
        a2=pixel(str(ap)+'_bt2.tif',x,y,'ahi_bt2')*.01
        if not 220<a1<365 or not 220<a2<365:continue
        selected=(col,row,x,y,vals,stamp,a1,a2,lp,av)
        break
    if selected is None:raise RuntimeError('No covered cloud-screened example in the predetermined window')
    col,row,x,y,v,stamp,a1,a2,lp,av=selected
    lon,lat,_=osr.CoordinateTransformation(srs,wgs).TransformPoint(x,y)
    lai_path=ROOT/'vegetation-structure-state/MUSYQ-LAI/standardized/lai_2002-2020_0p01deg/2019/LAI_2019001.h5'
    with h5py.File(lai_path) as f:
        d=f['data']; lai_raw=int(d[int((90-lat)/.01),int((lon+180)/.01)])
        if not 10<=lai_raw<=10000:raise ValueError('Invalid LAI for selected sample')
        lai=lai_raw*float(d.attrs['scale_factor'])
    seen[str(lai_path)]=dict(path=str(lai_path),size=lai_path.stat().st_size)
    soil=[]
    for band in [11,12]:
        ep=ROOT/'temperature-emissivity/emissivity'/f'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE{band}.tif'
        soil.append(pixel(ep,x,y,f'soil_{band}')*.001)
    fixed=dict(lai=lai,tcwv_cm=v['tcw']*.001,soil_emissivity=soil,
               vegetation_emissivity=[.985,.99],hotspot=.2)
    coefficients={}
    for sensor, rel in [('SLSTR','Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt'),('AHI','map-ahi/Himawari8_AHI_SW_Seebor_Coef_Day.txt')]:
        source=ROOT/'temperature-emissivity/emissivity'/rel
        table=np.loadtxt(source)
        nodes=np.unique(table[:,1])*.1
        assert table.shape==(66,15) and np.array_equal(table[:,0],np.tile(np.arange(6),11))
        model=legacy_split_window_model(table,nodes,np.array([0,1.25,2.25,3.25,4.25,5.25,100]),coefficient_columns=slice(2,10))
        target=OUT/f'{sensor.lower()}_coefficients.npz'
        save_split_window_model(target,model,sensor=sensor,version='local-Seebor-day-table')
        coefficients[sensor]=str(target)
        seen[str(source)]=dict(path=str(source),size=source.stat().st_size)
    obs=[]
    for view in ['nadir','obliq']:
        obs.append(dict(sensor='SLSTR',name='SLSTR '+view,vza=v['vza_'+view]*.01,sza=v['sza_nadir']*.01,
            raa=abs(v['vaa_'+view]-v['saa_nadir'])*.01%360,wavelength_um=10.85,
            bt1_k=v['bt1_'+view],bt2_k=v['bt2_'+view],sigma_k=1.,use_for_fit=True,
            coefficient_file=coefficients['SLSTR'],time_utc=f"2019-01-01T{int(v['time'])//100:02d}:{int(v['time'])%100:02d}:00Z"))
    az,aa=geo_angles(lon,lat)
    ahi_sza=pixel(DATA/'ahi_tif/01/01'/f'AHI_2019001_{stamp}_sza.tif',x,y,'ahi_sza')*.01
    ahi_saa=pixel(DATA/'ahi_tif/01/01'/f'AHI_2019001_{stamp}_saa.tif',x,y,'ahi_saa')*.01
    obs.append(dict(sensor='AHI',name='AHI 留出检验',vza=az,sza=ahi_sza,raa=abs(aa-ahi_saa)%360,
        wavelength_um=10.4,bt1_k=a1,bt2_k=a2,sigma_k=1.,use_for_fit=False,
        coefficient_file=coefficients['AHI'],time_utc=f'2019-01-01T{stamp[:2]}:{stamp[2:]}:00Z'))
    seen[str(lp)]=dict(path=str(lp),size=lp.stat().st_size)
    for item in seen.values():item['sha256']=sha(item['path'])
    provenance=dict(label='2019-01-01 中国中部真实观测 / 已知参数情景',source_root=str(ROOT),
        longitude=lon,latitude=lat,ahi_grid_pixel=[col,row],grid='AHI UTM49N 2 km cell; SLSTR aligned 2x2 radiance average',
        selection='Nearest covered clear-flag pixel to 112E,32N within fixed 20 km window; no retrieval-error selection',
        fixed_sources={'lai':'MUSYQ LAI_2019001, scale 0.001','tcwv':'SLSTR archived tcw; assumed kg m-2 x100 -> cm x0.001',
        'soil_emissivity':'MODIS LSE11/12 map scale 0.001; spectral proxy for AHI/SLSTR',
        'vegetation_emissivity':'User-editable scenario assumptions 0.985/0.990, not measured truth',
        'hotspot':'Fixed homogeneous-canopy scenario 0.2'},
        limitations=['Exploratory real-observation replay; no ground temperature accuracy claim.',
        'SLSTR ancillary angles/time/cloud are 10 km nearest-neighbour; spatial footprints remain approximate.',
        'Archived time values are decoded as HHMM UTC (range and AHI pairing consistent); no raw L1 timestamp audit.',
        'AHI view derived from nominal 140.7E geostationary geometry; not per-scan navigation.',
        'AHI screening uses existing positive LST as valid-mask proxy; no independent native cloud flag.',
        'Known parameter scenario and local legacy coefficient tables are not sensor response validation.'],
        decoding={'bt':'stored K x100; zero invalid','angles':'stored degrees x100','time':'stored HHMM UTC; nearest AHI <=5 min'},
        files=list(seen.values()))
    payload=dict(fixed=fixed,observations=obs,components=2,reference_vza=0.,reference_raa=0.,
                 optimize=True,prior_strength=0.,prior_sigma_k=10.,prior_k=[280.,280.],provenance=provenance)
    (OUT/'sample.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    np.savez_compressed(OUT/'source_pixels.npz',**raw,lai_raw=lai_raw,ahi_lst_mask_raw=av)
    result=run_workbench(payload)
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['temperature_k','fit_rmse_k','heldout_rmse_k','condition_number']},ensure_ascii=False))
    print('Sample:',OUT,'location:',lon,lat,'fixed:',fixed)


if __name__=='__main__':main()
