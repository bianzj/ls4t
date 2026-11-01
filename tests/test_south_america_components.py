"""Resume and completion gates for the South American production case."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import time

import pytest
import h5py
import numpy as np

from cases.slstr import slstr_lsct3_bayes_scene as retrieval
from cases.slstr import slstr_lst_scene_parallel as lst_module

REPO=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('america_components',
    REPO/'cases/slstr-america/run_components.py')
runner=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
SCENE='S3A_SL_1_RBT____20170517T110000_20170517T110300_sample.SEN3'
BOUNDS=(-80.,-18.,-44.,12.)


def paired_tree(root):
    source=root/'2017/tif'/SCENE;source.mkdir(parents=True)
    for field in ('vza','vaa','cloud','lat','lon','bt8','bt9'):
        for view in ('nadir','obliq'):
            (source/f'{field}_{view}.tif').touch()
    directory=root/'2017/lst'/SCENE;directory.mkdir(parents=True)
    for view in ('nadir','obliq'):
        (directory/f'lst_{view}.tif').touch()
    return root/'2017/lsct3_components'/SCENE


def test_inventory_cannot_call_missing_lst_or_components_complete(tmp_path):
    output=paired_tree(tmp_path)
    result=runner.inventory(tmp_path,2017,BOUNDS)
    assert result['pending_scenes']==[SCENE]
    assert not result['complete']
    (tmp_path/'2017/lst'/SCENE/'lst_obliq.tif').unlink()
    result=runner.inventory(tmp_path,2017,BOUNDS)
    assert result['missing_lst_scenes']==[SCENE]
    assert result['pending_scenes']==[]
    assert not result['complete']


def test_empty_result_reuse_invalidated_by_source_or_bounds(tmp_path,monkeypatch):
    output=paired_tree(tmp_path)
    monkeypatch.setattr(retrieval,'_STATE',{'root':tmp_path,'bounds':BOUNDS})
    retrieval.mark_empty(output,2017,SCENE,'night')
    marker=output/'no_valid_pixels.json'
    # Keep timestamp comparisons independent of filesystem clock precision.
    stamp=time.time_ns()+2_000_000_000
    os.utime(marker,ns=(stamp,stamp))
    assert runner.inventory(tmp_path,2017,BOUNDS)['complete']
    assert retrieval.cached_result(tmp_path,2017,SCENE,(-82.,-25.,-34.,20.)) is None
    source=tmp_path/'2017/tif'/SCENE/'sza_obliq.tif'
    source.write_bytes(b'new solar input')
    assert retrieval.cached_result(tmp_path,2017,SCENE,BOUNDS) is None


def test_legacy_empty_marker_is_retried(tmp_path):
    output=paired_tree(tmp_path);output.mkdir(parents=True)
    (output/'no_valid_pixels.json').write_text(json.dumps({
        'method':retrieval.METHOD,'reason':'no physical posterior temperatures'}))
    assert runner.inventory(tmp_path,2017,BOUNDS)['pending_scenes']==[SCENE]


def test_partial_component_product_set_is_never_reused(tmp_path):
    output=paired_tree(tmp_path);output.mkdir(parents=True)
    for name in retrieval.PRODUCTS[:-1]:
        (output/name).touch()
    marker=output/'bayes_5x5_homogeneous.json'
    marker.write_text(json.dumps({'method':retrieval.METHOD,'valid_pixels':12}))
    assert retrieval.cached_result(tmp_path,2017,SCENE,BOUNDS) is None


def test_missing_original_geometry_remains_explicitly_incomplete(tmp_path):
    paired_tree(tmp_path)
    (tmp_path/'2017/tif'/SCENE/'lon_obliq.tif').unlink()
    report=runner.inventory(tmp_path,2017,BOUNDS)
    assert report['missing_source_scenes']==[{
        'scene':SCENE,'missing_files':['lon_obliq.tif']}]
    assert report['pending_scenes']==[]
    assert not report['complete']


def test_lock_blocks_second_writer_and_releases_after_error(tmp_path):
    path=tmp_path/'run.lock'
    with pytest.raises(RuntimeError):
        with runner.run_lock(path):
            with pytest.raises(OSError):
                with runner.run_lock(path):
                    pytest.fail('A second process could write the same products')
            raise RuntimeError('interrupted')
    with runner.run_lock(path):
        pass


def test_explicit_lai_root_accepts_both_periods_and_name_cases(tmp_path,monkeypatch):
    scene=SCENE.replace('20170517','20250517')
    file=tmp_path/'2025/lai_2025137.h5'
    file.parent.mkdir();file.touch()
    monkeypatch.setattr(retrieval,'_STATE',{'lai_root':str(tmp_path)})
    assert retrieval.lai_path_for_scene(2025,scene)==file


def test_legacy_integer_tcwv_without_scale_is_rejected(tmp_path):
    path=tmp_path/'tcwv.h5'
    with h5py.File(path,'w') as handle:
        handle.create_dataset('tcw',shape=(24,721,1440),dtype='uint16')
    with pytest.raises(ValueError,match='lacks scale_factor'):
        lst_module.load_tcwv_cm(path)


@pytest.mark.parametrize('key,dtype,raw,scale',[
    ('data','float32',30.,None),('tcw','uint16',3000,.01)])
def test_tcwv_layouts_with_explicit_units_match_cm(tmp_path,key,dtype,raw,scale):
    path=tmp_path/'tcwv.h5'
    with h5py.File(path,'w') as handle:
        field=handle.create_dataset(key,shape=(24,721,1440),dtype=dtype,fillvalue=raw)
        if scale is not None:
            field.attrs['scale_factor']=scale
    cube=lst_module.load_tcwv_cm(path)
    assert np.allclose(cube,3.)


def test_geometry_only_empty_does_not_require_lst(tmp_path,monkeypatch):
    output=paired_tree(tmp_path)
    monkeypatch.setattr(retrieval,'_STATE',{'root':tmp_path,'bounds':BOUNDS})
    for view in ('nadir','obliq'):
        (tmp_path/'2017/lst'/SCENE/f'lst_{view}.tif').unlink()
    retrieval.mark_empty(output,2017,SCENE,'outside_region')
    assert retrieval.cached_result(tmp_path,2017,SCENE,BOUNDS)[1]=='no_valid'
    assert runner.inventory(tmp_path,2017,BOUNDS)['complete']
    (tmp_path/'2017/tif'/SCENE/'lat_obliq.tif').write_bytes(b'changed source')
    assert retrieval.cached_result(tmp_path,2017,SCENE,BOUNDS) is None


def test_posterior_empty_still_requires_paired_lst(tmp_path,monkeypatch):
    output=paired_tree(tmp_path)
    monkeypatch.setattr(retrieval,'_STATE',{'root':tmp_path,'bounds':BOUNDS})
    retrieval.mark_empty(output,2017,SCENE,'no physical posterior temperatures')
    (tmp_path/'2017/lst'/SCENE/'lst_obliq.tif').unlink()
    assert retrieval.cached_result(tmp_path,2017,SCENE,BOUNDS) is None
