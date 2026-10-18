"""Small real HDF5/GDAL contract test; never writes research data or products."""
from copy import deepcopy
from pathlib import Path
import tempfile
import numpy as np
import h5py
from osgeo import gdal, osr
import produce_msg_ls4t as p


def main():
    crs=osr.SpatialReference()
    crs.ImportFromEPSG(4326)
    identity={'identity_hash':'schema-fixture','code_sha256':p.sha(p.__file__),
              'implementation_sha256':'schema-fixture','static_source_hash':'schema-fixture',
              'geometry_plan_sha256':'schema-fixture',
              'grid':{'shape':[8,12],'GeoTransform':[-18,.03,0,65,0,-.03],
                      'Projection':crs.ExportToWkt(),'EPSG':4326}}
    signed=np.array([[-8000,-500,0,2000]],dtype='int16')
    decoded=p.decode_lst(signed.view('uint16'))
    assert np.isnan(decoded[0,0]) and np.isnan(decoded[0,2])
    np.testing.assert_allclose(decoded[0,[1,3]],[268.15,293.15],rtol=0,atol=1e-12)
    assert np.isnan(p.decode_lai(np.array([[65535]],dtype='uint16'))).all()
    cases=[]
    with tempfile.TemporaryDirectory(prefix='schema_',dir=Path(__file__).resolve().parent) as folder:
        root=Path(folder)
        files=[]
        for day,value in [(1,30000),(2,30200),(3,30400)]:
            file=root/f'MSG_LS4T_202407{day:02d}1200.h5'
            a=np.full((4,8,12),value,dtype='uint16')
            a[:,0,0]=0
            if day==1:
                a[1,0,1]=0  # Common support must exclude the entire observation.
            with h5py.File(file,'w') as output:
                p.attrs(output,identity)
                output.attrs['complete']=1
                data=output.create_dataset('data',data=a)
                p.data_attrs(data,identity)
            files.append(file)
        expected=[f'202407{day:02d}1200' for day in range(1,32)]
        omissions=[{'timestamp':stamp,'status':'deferred_geometry','error':'fixture missing source',
                    'run_id':'first','updated_UTC':'first','attempt':1} for stamp in expected[2:]]
        result=p.monthly(root,'202407',12,files[:2],expected,omissions,identity,tile_rows=3)
        assert result['status']=='written'
        hdf,tif=Path(result['hdf5']),Path(result['geotiff'])
        first_hash=p.sha(hdf)
        with h5py.File(hdf,'r') as source:
            assert source['data'].id==source['Monthly_Hour_Mean_LST'].id
            assert source['data'].shape==(4,8,12)
            assert source['data'].dtype==np.dtype('float32')
            assert source['data'].attrs['Scale_Factor']==100
            assert source['data'].attrs['scale_factor']==.01
            assert source.attrs['TimeZone']=='UTC'
            assert source.attrs['Scale_Factor']==100 and source.attrs['Units']=='K'
            assert np.isnan(source.attrs['Missing_Value'])
            assert source.attrs['Stored_Value_Convention']=='stored_value = kelvin * Scale_Factor'
            assert source.attrs['Year']==2024 and source.attrs['Month']==7 and source.attrs['Hour']==12
            assert np.isnan(source['data'][:,0,0]).all() and source['n_obs'][0,0]==0
            assert source['n_obs'][0,1]==1 and source['n_obs'][1,1]==2
            np.testing.assert_allclose(source['data'][:,1,1],30100)
            assert source['low_support'][1,1]==1 and source['qa'][1,1]==6
        dataset=gdal.Open(str(tif))
        assert dataset.RasterCount==4
        assert dataset.GetGeoTransform()==tuple(identity['grid']['GeoTransform'])
        for i,name in enumerate(p.BAND_DESCRIPTIONS,1):
            band=dataset.GetRasterBand(i)
            # GDAL omits an identity scale/offset tag; their defaults are 1/0.
            assert band.GetDescription()==name and band.GetScale() in [None,1.] and band.GetUnitType()=='K'
            assert np.isnan(band.GetNoDataValue())
            np.testing.assert_allclose(band.ReadAsArray()[1,1],301.,rtol=0,atol=1e-5)
            band=None
        dataset=None
        cases.append('MSG-compatible monthly HDF5 DN scale/hardlink, common support and direct-K GeoTIFF')

        changed=[dict(item,run_id='second',updated_UTC='second',attempt=5,traceback='new diagnostic') for item in omissions]
        resumed=p.monthly(root,'202407',12,files[:2],expected,changed,identity,tile_rows=3)
        assert resumed['status']=='resumed' and p.sha(hdf)==first_hash
        cases.append('Volatile run metadata does not invalidate monthly resume')
        refreshed=p.monthly(root,'202407',12,files,expected,omissions[1:],identity,tile_rows=3)
        assert refreshed['status']=='written'
        with h5py.File(hdf,'r') as source:
            assert source['n_obs'][1,1]==3 and source['low_support'][1,1]==0
            np.testing.assert_allclose(source['data'][:,1,1],30200)
        cases.append('Recovered committed scenes refresh a month under the same frozen identity')

        mixed=deepcopy(identity)
        mixed['identity_hash']='another-implementation'
        try:
            p.monthly(root,'202407',12,files,expected,omissions[1:],mixed,tile_rows=3)
            raise AssertionError('Different implementation was resumed')
        except RuntimeError as error:
            assert 'identity' in str(error)
        cases.append('Different implementation cannot reuse committed products')

        instant=root/'instant.tif.partial'
        raster=p.create_tif(instant,identity,gdal.GDT_UInt16,'2024-07-01T12:00:00+00:00',.01,0)
        for i in range(4):
            raster.GetRasterBand(i+1).WriteArray(np.full((8,12),30000,dtype='uint16'))
        raster.FlushCache()
        raster=None
        raster=gdal.Open(str(instant))
        for i in range(4):
            band=raster.GetRasterBand(i+1)
            assert band.DataType==gdal.GDT_UInt16 and band.GetScale()==.01
            assert band.GetNoDataValue()==0 and band.GetUnitType()=='K'
            band=None
        raster=None
        cases.append('Instantaneous UInt16 four-band GIS scale .01, K units and nodata 0')
    report={'status':'PASS','producer_sha256':p.sha(p.__file__),'checks':cases,
            'writes':'Temporary fixtures inside implementation workspace only; no real products modified'}
    p.atomic_json(Path(__file__).resolve().parent/'product_schema_qa.json',report)
    print(p.json_text(report))


if __name__=='__main__':
    main()
