"""Data-contract checks for recovery from retained native observations."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest
from osgeo import gdal
from netCDF4 import Dataset

CASE=Path(__file__).resolve().parents[1]/'cases/slstr-america'
sys.path.insert(0,str(CASE))
spec=importlib.util.spec_from_file_location('native_recovery',CASE/'recover_local_raw.py')
recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)


def test_native_negative_coordinates_are_preserved():
    source=np.array([[-78.1234,-1.005],[8.2234,np.nan]])
    encoded,dtype,nodata=recovery.encode(source,'geo')
    assert dtype==gdal.GDT_Int16 and nodata==-32768
    valid=np.isfinite(source)
    assert np.all(encoded[valid][source[valid]<0]<0)
    assert np.max(abs(encoded[valid]/100-source[valid]))<.01
    assert encoded[1,1]==-32768


def test_cloud_bitfields_are_not_converted_to_clear_pixels():
    source=np.array([[0.,1.,32768.,65533.,np.nan]])
    encoded,_,nodata=recovery.encode(source,'cloud')
    assert encoded.tolist()==[[0,1,32768,65533,65535]]
    assert nodata==65535


def test_tie_geometry_preserves_legacy_linear_grid():
    values=np.tile(np.arange(130,dtype=np.float64),(2,1))
    nadir=recovery.tie_grid(values,'nadir',(2,6))
    assert np.allclose(nadir[0],[7.5,23.5,39.5,55.5,71.5,87.5])
    oblique=recovery.tie_grid(values,'obliq',(2,6))
    expected=36+(np.arange(6)+.5)*59/6-.5
    assert np.allclose(oblique[0],expected)


def test_thermal_encoding_preserves_warm_brightness_without_signed_overflow():
    encoded,dtype,nodata=recovery.encode(np.array([[344.5,np.nan]]),'thermal')
    assert dtype==gdal.GDT_UInt16 and nodata==0
    assert encoded.tolist()==[[34450,0]]


def test_extra_native_scanlines_are_cropped_like_retained_extractor():
    values=np.broadcast_to(np.arange(1202,dtype=np.int16)[:,None],(1202,1500))
    cropped=recovery.image_grid(values,1500)
    assert cropped.shape==(1200,1500)
    assert np.all(cropped[-1]==1199)
    assert np.array_equal(cropped,values[:1200])
    with pytest.raises(ValueError):
        recovery.image_grid(values[:1199],1500)


def test_mixed_native_product_identity_is_rejected(tmp_path):
    path=tmp_path/'observation.nc'
    with Dataset(path,'w') as ds:
        ds.createDimension('x',2)
        ds.createVariable('temperature','f4',('x',))[:]=[290.,300.]
        ds.product_name='different.SEN3'
    with pytest.raises(ValueError,match='metadata mismatch'):
        recovery.native(path,'temperature','requested.SEN3')
