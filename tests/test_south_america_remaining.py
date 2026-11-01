"""Guard against treating incomplete geometry as confirmed empty production."""
from pathlib import Path
import importlib.util

import numpy as np
import pytest
from osgeo import gdal

REPO=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('america_remaining',REPO/'cases/slstr-america/audit_remaining.py')
audit=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(audit)
SCENE='S3A_SL_1_RBT____20230113T150411_20230113T150711_example.SEN3'


def raster(path,values):
    path.parent.mkdir(parents=True,exist_ok=True)
    ds=gdal.GetDriverByName('GTiff').Create(str(path),3,2,1,gdal.GDT_Int16)
    ds.GetRasterBand(1).WriteArray(np.rint(np.asarray(values)*100).astype(np.int16))
    ds=None


def view(folder,name,*,inside=True,day=True):
    lat=np.array([[-10,-10,-10],[-9,-9,-9]]) if inside else np.array([[70,70,70],[71,71,71]])
    lon=np.array([[-60,-59,-58],[-60,-59,-58]])
    raster(folder/f'lat_{name}.tif',lat)
    raster(folder/f'lon_{name}.tif',lon)
    raster(folder/f'sza_{name}.tif',np.full((2,3),30 if day else 110))


@pytest.mark.parametrize('inside,day,category',[
    (False,True,'confirmed_oblique_outside_amazon'),
    (True,False,'confirmed_oblique_no_daytime_in_amazon'),
    (True,True,'daytime_amazon_oblique_requires_source_recovery')])
def test_exact_oblique_gate(tmp_path,inside,day,category):
    folder=tmp_path/'2023/tif'/SCENE;view(folder,'obliq',inside=inside,day=day)
    report=audit.classify({'year':2023,'scene':SCENE},tmp_path,{})
    assert report['category']==category
    assert report['definitive_oblique_gate']==category.startswith('confirmed_')


def test_nadir_night_does_not_certify_missing_oblique(tmp_path):
    view(tmp_path/'2023/tif'/SCENE,'nadir',day=False)
    report=audit.classify({'year':2023,'scene':SCENE},tmp_path,{})
    assert report['category']=='nadir_night_oblique_unverified'
    assert not report['definitive_oblique_gate']


def test_zero_filled_geolocation_is_not_a_confirmed_outside_scene(tmp_path):
    folder=tmp_path/'2023/tif'/SCENE
    for view_name in ('nadir','obliq'):
        for field in ('lat','lon'):
            raster(folder/f'{field}_{view_name}.tif',np.zeros((2,3)))
    report=audit.classify({'year':2023,'scene':SCENE},tmp_path,{})
    assert report['category']=='no_readable_geolocation'
    assert not report['definitive_oblique_gate']


def test_audit_leaves_observation_bytes_unchanged(tmp_path):
    folder=tmp_path/'2023/tif'/SCENE;view(folder,'obliq')
    before={p.name:p.read_bytes() for p in folder.iterdir()}
    audit.classify({'year':2023,'scene':SCENE},tmp_path,{})
    assert {p.name:p.read_bytes() for p in folder.iterdir()}==before
