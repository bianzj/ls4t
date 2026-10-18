"""Read-only audit of cached landcover and emissivity parameters."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from osgeo import gdal

HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'results/production_assessment/msg_5x5/station_direct_2018_2024'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    gdal.UseExceptions();OUT.mkdir(parents=True,exist_ok=True)
    inventory=Path('E:/field/sites-2025-selected.csv');lookup=Path('E:/lse/IGBP_Emi.txt')
    sites=pd.read_csv(inventory);table=np.loadtxt(lookup);rows=[];manifest={}
    for r in sites.loc[~sites.id.str.startswith('CD-')].itertuples():
        root=Path('E:/PRODUCTS/SITE')/r.id/'static';a={}
        for k in ['lc','emis_s','emis_v','lat','lon']:
            p=root/f'{k}.tif';a[k]=gdal.Open(str(p)).ReadAsArray();assert a[k].shape==(5,5)
            manifest[str(p)]=sha(p)
        code=int(a['lc'][2,2]);value=float(a['emis_v'][2,2]);expected=table[code,0]/1000
        distance=111.195*np.sqrt((a['lat'][2,2]-r.lat)**2+((a['lon'][2,2]-r.lon)*np.cos(np.radians(r.lat)))**2)
        rows.append({'site':r.id,'station_type':r.type,'cached_lc':code,'emis_v':value,'lookup_emis_v':expected,
            'lookup_match':bool(abs(value-expected)<1e-6),'station_elevation_m':r.elevation,'approx_center_distance_km':float(distance),
            'lc_5x5_codes':','.join(map(str,np.unique(a['lc']).astype(int)))})
    x=pd.DataFrame(rows);x.to_csv(OUT/'station_landcover_emissivity_audit.csv',index=False)
    rasters={}
    for p in ['E:/map/MCD12C1_2011_0.01.tif','E:/lse/AG1km.v003.SoilEmi.ABI.Global.001D_LSE11.tif']:
        d=gdal.Open(p);rasters[p]={'shape':[d.RasterYSize,d.RasterXSize],'geotransform':list(d.GetGeoTransform()),'projection':d.GetProjection(),'size_bytes':Path(p).stat().st_size}
    source=HERE.parent/'validation/extract_point_static_from_msg.py'
    result={'site_input_hashes':manifest,'station_inventory_sha256':sha(inventory),'emissivity_table_sha256':sha(lookup),
        'extraction_source':str(source),'extraction_source_sha256':sha(source),'global_raster_metadata':rasters,
        'vegetation_lookup_matches_all_sites':bool(x.lookup_match.all()),'min_center_distance_km':float(x.approx_center_distance_km.min()),
        'max_center_distance_km':float(x.approx_center_distance_km.max()),
        'limits':'Cached coordinate rounding and latitude-longitude distance approximation; not a new geolocation validation. Global grids share dimensions/geotransform but CRS strings differ.'}
    (OUT/'station_auxiliary_source_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(x.to_string(index=False),flush=True)

if __name__=='__main__':main()
