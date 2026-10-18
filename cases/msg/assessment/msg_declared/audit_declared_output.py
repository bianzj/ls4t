"""Read-only audit of declared-slot LS4T scene and monthly products."""
from pathlib import Path
import argparse
import hashlib
import json
import datetime as dt
import re
from functools import lru_cache
import h5py
import numpy as np
from osgeo import gdal,osr
import pandas as pd
import pvlib
import pvlib.solarposition
import produce_msg_ls4t as producer
from verify_msg_ls4t import load_scalar,oracle
from msg_view_geometry import look_angles

gdal.UseExceptions()
HERE=Path(__file__).resolve().parent

def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):digest.update(block)
    return digest.hexdigest()

@lru_cache(maxsize=3)
def declaration_source(path):
    """Read each frozen static declaration once, never treat it as ephemeris."""
    path=Path(path)
    actual_hash=sha(path)
    dataset=gdal.Open(str(path),gdal.GA_ReadOnly)
    metadata=dataset.GetMetadata()
    declaration=metadata.get('PROJECTION_NAME','').strip()
    match=re.fullmatch(r'GEOS\(([+-]?\d+(?:\.\d+)?)\)',declaration,re.IGNORECASE)
    assert match is not None,('Static source has no explicit orbital-slot declaration',str(path),declaration)
    return actual_hash,float(match.group(1)),metadata

def check_declared_position(stamp,view,position,identity):
    assert not stamp.startswith('202206'),'Known June input geolocation conflict remains excluded'
    expected=0. if view=='e' else 41.5 if stamp<'202206010000' else 45.5
    assert float(position['latitude_deg'])==0.
    assert float(position['longitude_deg'])==expected
    assert float(position['orbital_slot_longitude_deg'])==expected
    source=Path(position['path']).resolve()
    actual_hash,source_slot,metadata=declaration_source(str(source))
    assert source_slot==expected
    assert actual_hash==position['sha256']==identity['static_sources'][str(source)]['sha256']
    assert int(source.stat().st_size)==position['bytes']
    assert position['metadata']['PROJECTION_NAME']==metadata['PROJECTION_NAME']
    assert 'declared orbital slot' in position['position_value_meaning']
    return expected

def decode_lst(raw,nodata):
    signed=raw.astype(np.int64)
    if raw.dtype==np.uint16:signed=np.where(signed>=32768,signed-65536,signed)
    result=signed/100.+273.15
    bad=(signed==0)|(signed==-8000)|(result<150)|(result>400)
    if nodata is not None:bad|=(raw==nodata)|(signed==nodata)
    return np.where(bad,np.nan,result)

def check_grid(tif,grid):
    assert (tif.RasterYSize,tif.RasterXSize)==tuple(grid['shape'])
    np.testing.assert_allclose(tif.GetGeoTransform(),grid['GeoTransform'],rtol=0,atol=1e-9)
    left,right=osr.SpatialReference(),osr.SpatialReference()
    left.ImportFromWkt(tif.GetProjection());right.ImportFromWkt(grid['Projection'])
    assert left.IsSame(right)

def check_commit(hdf,tif,identity):
    path=Path(str(hdf)+'.complete.json')
    record=json.loads(path.read_text(encoding='utf-8'))
    assert record['identity_hash']==identity['identity_hash']
    for source in [hdf,tif]:assert sha(source)==record['files'][str(source)]['sha256']

def sample_ancillary(path,lat,lon):
    source=gdal.Open(str(path),gdal.GA_ReadOnly)
    geographic,target=osr.SpatialReference(),osr.SpatialReference()
    geographic.ImportFromEPSG(4326);target.ImportFromWkt(source.GetProjection())
    for crs in [geographic,target]:crs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    transform=osr.CoordinateTransformation(geographic,target)
    inverse=gdal.InvGeoTransform(source.GetGeoTransform())
    transformed=np.asarray(transform.TransformPoints(np.column_stack([lon.ravel(),lat.ravel()])))
    x,y=transformed[:,0],transformed[:,1]
    cols=np.trunc(inverse[0]+inverse[1]*x+inverse[2]*y).astype(int)
    rows=np.trunc(inverse[3]+inverse[4]*x+inverse[5]*y).astype(int)
    result=np.full(lat.size,np.nan)
    band=source.GetRasterBand(1);nodata=band.GetNoDataValue()
    for i,(row,col) in enumerate(zip(rows,cols)):
        if 0<=row<source.RasterYSize and 0<=col<source.RasterXSize:
            value=float(band.ReadAsArray(int(col),int(row),1,1)[0,0])
            if nodata is None or value!=nodata:result[i]=value
    return result.reshape(lat.shape)

def scalar_pixel(stamp,y,x,identity,geometry,input_files,scalar):
    grid=identity['grid'];height,width=grid['shape'];gt=grid['GeoTransform']
    rows=np.clip(np.arange(y-2,y+3),0,height-1)
    cols=np.clip(np.arange(x-2,x+3),0,width-1)
    rr,cc=np.meshgrid(rows,cols,indexing='ij')
    lat=gt[3]+cc*gt[4]+rr*gt[5];lon=gt[0]+cc*gt[1]+rr*gt[2]
    fields={}
    assert geometry['position_policy']=='declared_geostationary_slots_nominal_latitude_zero'
    for view in ['e','i']:
        position=geometry['positions'][view]
        check_declared_position(stamp,view,position,identity)
        fields['vza_'+view],fields['vaa_'+view]=look_angles(lat,lon,position['latitude_deg'],position['longitude_deg'])
    # Independently reconstruct the exact two nearest resizes of the global
    # pvlib solar grid, including float32 storage before the tile is extracted.
    coarse_h,coarse_w=height//10,width//10
    cy=np.floor(rr*coarse_h/height).astype(int);cx=np.floor(cc*coarse_w/width).astype(int)
    sy=np.floor(cy*height/coarse_h).astype(int);sx=np.floor(cx*width/coarse_w).astype(int)
    solar_lat=gt[3]+sx*gt[4]+sy*gt[5];solar_lon=gt[0]+sx*gt[1]+sy*gt[2]
    timestamp=pd.to_datetime(stamp,format='%Y%m%d%H%M',utc=True)
    solar=pvlib.solarposition.get_solarposition(np.repeat(timestamp,25),solar_lat.ravel(),solar_lon.ravel(),0.,method='nrel_numpy')
    fields['sza']=solar['zenith'].to_numpy().astype(np.float32).astype(float).reshape(5,5)
    fields['saa']=solar['azimuth'].to_numpy().astype(np.float32).astype(float).reshape(5,5)
    for key,path in input_files.items():
        source=gdal.Open(str(path),gdal.GA_ReadOnly)
        # Only the 5x5 unique bounding rectangle is read; edge replication is
        # handled explicitly by the clipped absolute pixel-index vectors.
        block=source.ReadAsArray(int(cols.min()),int(rows.min()),int(cols.max()-cols.min()+1),int(rows.max()-rows.min()+1))
        raw=block[np.ix_(rows-rows.min(),cols-cols.min())]
        nodata=source.GetRasterBand(1).GetNoDataValue()
        if key=='lai':
            value=raw.astype(float)/1000.
            bad=(value<0)|(value>10)
            if nodata is not None:bad|=raw==nodata
            fields[key]=np.where(bad,np.nan,value)
        else:fields[key]=decode_lst(raw,nodata)
    fields['land']=sample_ancillary('E:/map/MCD12C1_2011_0.01.tif',lat,lon)
    fields['emis_s']=sample_ancillary('E:/lse/AG1km.v003.SoilEmi.ABI.Global.001D_LSE12.tif',lat,lon)
    finite=fields['emis_s'][np.isfinite(fields['emis_s'])&(fields['emis_s']>0)]
    if len(finite) and np.mean(finite)>1:fields['emis_s']/=1000.
    table=np.loadtxt('E:/lse/IGBP_Emi.txt')
    if table.ndim==1:table=table[:,None]
    land=fields['land'];valid=np.isfinite(land)&(land>=0)&(land<table.shape[0])
    fields['emis_v']=np.full((5,5),np.nan)
    fields['emis_v'][valid]=table[land[valid].astype(int),0]/1000.
    return oracle(fields,scalar)

def audit_scene(root,stamp,identity):
    hdf=root/'INSTANTANEOUS'/stamp[:4]/stamp[4:6]/stamp[6:8]/f'MSG_LS4T_{stamp}.h5'
    tif=root/'GEOTIFF'/stamp[:4]/stamp[4:6]/stamp[6:8]/f'MSG_LS4T_{stamp}.tif'
    check_commit(hdf,tif,identity)
    raster=gdal.Open(str(tif),gdal.GA_ReadOnly);check_grid(raster,identity['grid'])
    assert raster.RasterCount==4
    assert raster.GetMetadataItem('TIME_ZONE')=='UTC'
    assert raster.GetMetadataItem('IDENTITY_HASH')==identity['identity_hash']
    for i,name in enumerate(['ts','tv','tss','tsh'],1):
        band=raster.GetRasterBand(i)
        assert band.DataType==gdal.GDT_UInt16 and band.GetDescription()==name
        assert band.GetScale()==.01 and band.GetOffset()==0 and band.GetUnitType()=='K' and band.GetNoDataValue()==0
    grid=identity['grid'];height,width=grid['shape'];valid_pixels=0;histogram=np.zeros(26,dtype=np.int64)
    pixels={(0,0),(height-1,width-1),(881,333),(height//2,width//2)}
    with h5py.File(hdf) as source:
        assert int(source.attrs['complete'])==1 and source.attrs['identity_hash']==identity['identity_hash']
        assert source.attrs['code_sha256']==identity['code_sha256']
        assert source.attrs['time_zone']=='UTC'
        assert source['data'].shape==(4,height,width) and source['data'].dtype==np.uint16
        assert source['data'].attrs['Scale_Factor']==100 and source['data'].attrs['scale_factor']==.01
        assert source['data'].attrs['NoData_Value']==0 and source['data'].attrs['units']=='K'
        expected_timestamp=pd.to_datetime(stamp,format='%Y%m%d%H%M',utc=True).isoformat()
        assert source.attrs['timestamp_UTC']==expected_timestamp==raster.GetMetadataItem('TIMESTAMP_UTC')
        geometry=json.loads(source.attrs['geometry_json'])
        input_records=json.loads(source.attrs['inputs_json'])
        input_files=producer.paths(stamp)
        for path in input_files.values():assert sha(path)==input_records[str(path.resolve())]['sha256']
        for y in range(0,height,256):
            end=min(height,y+256);encoded=source['data'][:,y:end]
            raw=raster.ReadAsArray(0,y,width,end-y)
            assert np.array_equal(encoded,raw),'HDF5/GeoTIFF DN bytes differ'
            support=encoded[0]>0
            assert all(np.array_equal(support,encoded[i]>0) for i in range(1,4))
            assert np.all((encoded[:,support]>=25000)&(encoded[:,support]<=35000))
            n=source['valid_neighbors'][y:end];qa=source['qa'][y:end]
            assert np.all(n<=25) and np.all(qa<=31)
            assert np.all(n[support]>=10) and np.all((qa[support]&15)==0)
            assert np.all((qa[~support]&15)!=0)
            valid_pixels+=int(support.sum());histogram+=np.bincount(n[support],minlength=26)
            for relative in [0,end-y-1]:
                columns=np.flatnonzero(support[relative])
                if len(columns) and len(pixels)<16:pixels.add((y+relative,int(columns[len(columns)//2])))
        assert int(source.attrs['valid_pixels'])==valid_pixels and valid_pixels>0
        assert np.array_equal(source.attrs['valid_neighbor_histogram'],histogram)
        scalar=load_scalar();records=[]
        for y,x in sorted(pixels):
            reference,n,qa=scalar_pixel(stamp,y,x,identity,geometry,input_files,scalar)
            expected=np.rint(np.nan_to_num(reference,nan=0)*100).astype(np.uint16)
            actual=source['data'][:,y,x]
            assert np.array_equal(expected,actual),(stamp,y,x,actual,expected,reference)
            assert int(source['valid_neighbors'][y,x])==n and int(source['qa'][y,x])==qa,(stamp,y,x,n,qa)
            records.append({'row':y,'column':x,'encoded_match':True,'valid':bool(np.isfinite(reference).all()),'neighbors':n,'qa':qa})
    return {'pass':True,'timestamp_UTC':stamp,'hdf5_sha256':sha(hdf),'geotiff_sha256':sha(tif),'valid_pixels':valid_pixels,'all_pixels_four_band_mask_QA_and_DN_match':True,'signed_sources_frozen':True,'scalar_actual_pixel_checks':records},sorted(pixels)

def audit_month(root,stamp,identity,pixels):
    month=stamp[:6];hour=int(stamp[8:10])
    hdf=root/'MONTHLY_HOUR'/month[:4]/f'MLST_MONTH_{month}_HH{hour:02d}.h5'
    tif=root/'MONTHLY_HOUR_GEOTIFF'/month[:4]/f'MLST_MONTH_{month}_HH{hour:02d}.tif'
    if not hdf.is_file() or not tif.is_file():return {'pass':False,'status':'pending_monthly_output','expected_hdf5':str(hdf)}
    check_commit(hdf,tif,identity)
    raster=gdal.Open(str(tif),gdal.GA_ReadOnly);check_grid(raster,identity['grid'])
    assert raster.RasterCount==4
    for i,name in enumerate(['ts','tv','tss','tsh'],1):
        band=raster.GetRasterBand(i)
        assert band.DataType==gdal.GDT_Float32 and band.GetDescription()==name
        # A direct-K GeoTIFF may omit the identity scale/offset tags. Validate
        # their default values and independently compare the actual K pixels.
        scale=1. if band.GetScale() is None else band.GetScale()
        offset=0. if band.GetOffset() is None else band.GetOffset()
        assert scale==1 and offset==0 and band.GetUnitType()=='K' and np.isnan(band.GetNoDataValue())
    height,width=identity['grid']['shape'];support=np.zeros(32,dtype=np.int64)
    with h5py.File(hdf) as source:
        assert int(source.attrs['complete'])==1 and source.attrs['identity_hash']==identity['identity_hash']
        assert int(source.attrs['Year'])==int(month[:4]) and int(source.attrs['Month'])==int(month[4:6]) and int(source.attrs['Hour'])==hour
        assert source['Monthly_Hour_Mean_LST'].id==source['data'].id
        assert source['data'].dtype==np.float32 and source['data'].shape==(4,height,width)
        assert source['data'].attrs['Scale_Factor']==100 and source['data'].attrs['scale_factor']==.01
        assert source.attrs['Scale_Factor']==100 and source.attrs['Units']=='K'
        files=json.loads(source.attrs['source_sha256_json'])
        timestamps=json.loads(source.attrs['source_timestamps_json'])
        assert len(timestamps)==len(set(timestamps))==len(files)==int(source.attrs['source_count'])
        assert all(t.startswith(month) and int(t[8:10])==hour and t[10:12]=='00' for t in timestamps)
        incomplete=len(files)!=int(source.attrs['calendar_days'])
        for y in range(0,height,256):
            end=min(height,y+256);encoded=source['data'][:,y:end];kelvin=raster.ReadAsArray(0,y,width,end-y)
            np.testing.assert_allclose(kelvin,encoded.astype(float)*.01,rtol=0,atol=4e-5,equal_nan=True)
            n=source['n_obs'][y:end];qa=source['qa'][y:end];low=source['low_support'][y:end]
            assert np.all(n<=len(files)) and np.all(np.isfinite(encoded)==(n>0)[None])
            expected_low=((n>0)&(n<3)).astype(np.uint8)
            expected_qa=(n==0).astype(np.uint8)|(expected_low<<1)|(4 if incomplete else 0)
            assert np.array_equal(low,expected_low) and np.array_equal(qa,expected_qa)
            support+=np.bincount(n.ravel(),minlength=32)
        actual_hist=np.asarray(source.attrs['support_histogram'])
        assert np.array_equal(actual_hist,support[:len(actual_hist)])
        values=[]
        for path,record in files.items():
            assert sha(path)==record['sha256']
            with h5py.File(path) as scene:
                assert int(scene.attrs['complete'])==1 and scene.attrs['identity_hash']==identity['identity_hash']
                values.append(np.array([scene['data'][:,y,x] for y,x in pixels]))
        values=np.asarray(values);records=[]
        for index,(y,x) in enumerate(pixels):
            samples=values[:,index];good=np.all((samples>=25000)&(samples<=35000),axis=1)
            assert int(source['n_obs'][y,x])==int(good.sum())
            mean=source['data'][:,y,x]
            if good.any():assert np.array_equal(mean,samples[good].astype(float).mean(0).astype(np.float32))
            else:assert np.isnan(mean).all()
            records.append({'row':y,'column':x,'n':int(good.sum()),'direct_encoded_mean_match':True})
    return {'pass':True,'month':month,'hour_UTC':hour,'hdf5_sha256':sha(hdf),'geotiff_sha256':sha(tif),'source_scenes':len(files),'all_pixels_month_mask_count_and_QA_match':True,'geotiff_kelvin_matches_hdf_DN_scale':True,'geotiff_identity_scale_may_be_implicit':True,'direct_pixel_mean_checks':records}

def audit_actual_pixels(root,stamp,identity):
    """Supplement the root's whole-product audit with independent scalar replay."""
    hdf=root/'INSTANTANEOUS'/stamp[:4]/stamp[4:6]/stamp[6:8]/f'MSG_LS4T_{stamp}.h5'
    height,width=identity['grid']['shape']
    pixels={(0,0),(height-1,width-1),(881,333),(height//2,width//2)}
    scalar=load_scalar();records=[]
    with h5py.File(hdf) as source:
        assert source.attrs['identity_hash']==identity['identity_hash'] and int(source.attrs['complete'])==1
        geometry=json.loads(source.attrs['geometry_json'])
        input_files=producer.paths(stamp)
        input_records=json.loads(source.attrs['inputs_json'])
        for path in input_files.values():assert sha(path)==input_records[str(path.resolve())]['sha256']
        for y in [254,255,256,257,510,511,512,513,766,767,768,769,1023,1024]:
            if y>=height:continue
            encoded=source['data'][0,y];neighbors=source['valid_neighbors'][y]
            valid=np.flatnonzero(encoded>0)
            incomplete=np.flatnonzero((encoded>0)&(neighbors<25))
            if len(valid):pixels.add((y,int(valid[len(valid)//2])))
            if len(incomplete):pixels.add((y,int(incomplete[len(incomplete)//2])))
        for y,x in sorted(pixels):
            reference,n,qa=scalar_pixel(stamp,y,x,identity,geometry,input_files,scalar)
            expected=np.rint(np.nan_to_num(reference,nan=0)*100).astype(np.uint16)
            actual=source['data'][:,y,x]
            assert np.array_equal(expected,actual),(stamp,y,x,actual,expected,reference)
            assert int(source['valid_neighbors'][y,x])==n and int(source['qa'][y,x])==qa,(stamp,y,x,n,qa)
            records.append({'row':y,'column':x,'stored_DN':actual.tolist(),'encoded_match':True,'valid':bool(np.isfinite(reference).all()),'neighbors':n,'qa':qa})
    assert sum(record['valid'] for record in records)>=5
    return {'pass':True,'timestamp_UTC':stamp,'hdf5_sha256':sha(hdf),'pixel_checks':records,'valid_actual_pixels':sum(record['valid'] for record in records),'seam_rows':sorted(set(record['row'] for record in records if 254<=record['row']<=1024)),'inputs_reconstruction':'Independent source signed decode, separate ancillary CRS sampling, declared orbital slots verified from frozen provider-static file hashes/PROJECTION_NAME with nominal latitude0, exact global coarse solar lookup, unedited historical scalar-center functions. Stored roundedDN, neighbor count and all QA bits must each agree exactly.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--sample-stamp',required=True)
    parser.add_argument('--output',type=Path,default=HERE/'product_audit.json')
    parser.add_argument('--scalar-only',action='store_true',help='Actual scalar/seam replay; complement the root whole-image and monthly audit')
    parser.add_argument('--verification',type=Path,help='Frozen numerical report for the deployed producer; default resolves its actual code_files path')
    args=parser.parse_args()
    root=args.root.resolve()
    identity=json.loads((root/'production_identity.json').read_text(encoding='utf-8'))
    deployed=next(Path(path) for path in identity['code_files'] if Path(path).name=='produce_msg_ls4t.py')
    verification_path=args.verification or deployed.with_name('verification.json')
    verification=json.loads(verification_path.read_text(encoding='utf-8'))
    assert producer.PROTOCOL['version']=='MSG_LS4T_H025_5X5_DECLARED_V1'
    assert identity['code_sha256']==sha(producer.__file__)==verification['producer_sha256']
    assert verification['status']=='passed'
    assert identity['geometry_module_sha256']==sha(HERE/'msg_view_geometry.py')
    assert identity['geometry_plan_sha256']==sha(HERE/'geometry_plan.json')
    if args.scalar_only:
        scene=audit_actual_pixels(root,args.sample_stamp,identity)
        report={'pass':scene['pass'],'status':'passed','checked_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),'identity_hash':identity['identity_hash'],'producer_sha256':identity['code_sha256'],'actual_scalar_scene':scene,'scope':'Actual source-to-output scalar replay around tile boundaries and explicit missing/edge positions. Whole-image schema and monthly statistics are audited separately by root. No inputs altered.'}
    else:
        scene,pixels=audit_scene(root,args.sample_stamp,identity)
        month=audit_month(root,args.sample_stamp,identity,pixels)
        report={'pass':bool(scene['pass'] and month['pass']),'status':'passed' if month['pass'] else 'scene_passed_monthly_pending','checked_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),'identity_hash':identity['identity_hash'],'producer_sha256':identity['code_sha256'],'scene':scene,'monthly':month,'scope':'Real product encoding, grid, UTC, shared masks, QA, independent historical scalar actual-pixel replay, and direct monthly counts and means. No inputs altered.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    report['geometry_policy']='declared_geostationary_slots_nominal_latitude_zero'
    report['position_checks']='Provider-static orbital-slot declarations verified once per path against actual file SHA/PROJECTION_NAME and frozen identity; this does not assert acquisition ephemeris precision.'
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
