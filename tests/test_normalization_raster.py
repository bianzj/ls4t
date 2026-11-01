import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from base.quality import QualityFlag
from base.raster import read_raster


def write_tif(path, values, *, transform=(100, 2, 0, 200, 0, -2), nodata=None, scale=None):
    from osgeo import gdal, osr
    gdal.UseExceptions()
    values = np.asarray(values, dtype=float)
    path.parent.mkdir(parents=True, exist_ok=True)
    ds = gdal.GetDriverByName("GTiff").Create(str(path), values.shape[1], values.shape[0], 1, gdal.GDT_Float64)
    ds.SetGeoTransform(transform)
    crs = osr.SpatialReference()
    crs.ImportFromEPSG(32650)
    ds.SetProjection(crs.ExportToWkt())
    band = ds.GetRasterBand(1)
    band.WriteArray(values)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    if scale is not None:
        band.SetScale(scale)
    ds = None


def test_angle_geotiff_decodes_nodata_and_scale_preserves_grid(tmp_path):
    from base.normalization.raster import angle_normalize_raster
    from osgeo import gdal
    source, target = tmp_path / "source.tif", tmp_path / "angle.tif"
    write_tif(source, [[15000, -9999]], nodata=-9999, scale=.02)
    angle_normalize_raster(source, target, view_zenith_deg=60, solar_zenith_deg=30,
                           relative_azimuth_deg=0, coefficients_k=[2, 0, 0])
    fields, metadata = read_raster(target)
    assert fields["temperature_k"][0, 0] == pytest.approx(298.)
    assert np.isnan(fields["temperature_k"][0, 1])
    assert int(fields["quality_flag"][0, 1]) & QualityFlag.INPUT_INVALID
    ds = gdal.Open(str(target))
    assert ds.GetGeoTransform() == (100, 2, 0, 200, 0, -2)
    assert np.isnan(ds.GetRasterBand(1).GetNoDataValue())
    np.testing.assert_array_equal(ds.GetRasterBand(1).GetMaskBand().ReadAsArray(), [[255, 0]])
    assert "angle" in metadata["LS4T_NORMALIZATION"]
    ds = None
    with pytest.raises(FileExistsError):
        angle_normalize_raster(source, target, view_zenith_deg=60, solar_zenith_deg=30,
                               relative_azimuth_deg=0, coefficients_k=[2, 0, 0])


def test_auxiliary_grid_shift_is_rejected(tmp_path):
    from base.normalization.raster import time_normalize_raster
    source, aux = tmp_path / "source.tif", tmp_path / "hour.tif"
    write_tif(source, [[300, 301]])
    write_tif(aux, [[12, 12]], transform=(101, 2, 0, 200, 0, -2))
    with pytest.raises(ValueError, match="grid|align"):
        time_normalize_raster(source, tmp_path / "out.tif", local_solar_time_hour={"path": str(aux)},
                              amplitude_k=8, peak_hour=14)


def test_downscale_raster_requires_nested_geographic_grid(tmp_path):
    from base.normalization.raster import downscale_raster
    source, aux = tmp_path / "source.tif", tmp_path / "ndvi.tif"
    coarse = 299 - 2*np.arange(6).reshape(2, 3)
    fine = np.repeat(np.repeat(np.arange(6).reshape(2, 3), 2, 0), 2, 1)
    write_tif(source, coarse)
    write_tif(aux, fine, transform=(101, 1, 0, 200, 0, -1))
    with pytest.raises(ValueError, match="grid|align|extent"):
        downscale_raster(source, tmp_path / "out.tif", predictors=[{"path": str(aux)}])
    write_tif(aux, fine, transform=(100, 1, 0, 200, 0, -1))
    target = tmp_path / "out.tif"
    downscale_raster(source, target, predictors=[{"path": str(aux)}])
    fields, metadata = read_raster(target)
    np.testing.assert_allclose(fields["temperature_k"].reshape(2, 2, 3, 2).mean((1, 3)), coarse)
    assert "training_rmse_k" in metadata["LS4T_NORMALIZATION"]


def load_runner():
    path = Path(__file__).resolve().parents[1] / "cases/multisource-normalization/run.py"
    assert path.exists(), "multi-source runnable case is missing"
    spec = importlib.util.spec_from_file_location("normalization_case", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_multisource_demo_runs_three_explicit_stages(tmp_path):
    runner = load_runner()
    config_path = runner.create_demo(tmp_path / "demo with spaces")
    assert not (config_path.parent / "outputs").exists()
    for stage in ("angle", "time", "downscale"):
        outputs = runner.run_stage(config_path, stage)
        assert len(outputs) == 2
    for output in outputs:
        fields, metadata = read_raster(output)
        assert fields["temperature_k"].shape == (4, 6)
        assert np.isfinite(fields["temperature_k"]).all()
        assert not fields["quality_flag"].any()
        history = json.loads(metadata["LS4T_NORMALIZATION"])["history"]
        assert [step["stage"] for step in history] == ["angle", "time", "downscale"]
    first, _ = read_raster(outputs[0])
    second, _ = read_raster(outputs[1])
    np.testing.assert_allclose(first["temperature_k"], second["temperature_k"], atol=1e-4)


def test_demo_rejects_code_storage_and_nested_products(tmp_path):
    runner = load_runner()
    forbidden = runner.ROOT / "cases" / "forbidden-demo-data"
    with pytest.raises(ValueError, match="outside"):
        runner.create_demo(forbidden)
    assert not forbidden.exists()
    with pytest.raises(ValueError, match="separate"):
        runner.create_demo(tmp_path / "data", products_directory=tmp_path / "data/products")
    assert not (tmp_path / "data").exists()


def test_raster_rejects_inplace_and_repeated_stage(tmp_path):
    from base.normalization.raster import time_normalize_raster
    source, target = tmp_path / "source.tif", tmp_path / "time.tif"
    write_tif(source, [[300, 301]])
    kwargs = dict(local_solar_time_hour=10, amplitude_k=8, peak_hour=14)
    with pytest.raises(ValueError, match="source|input"):
        time_normalize_raster(source, source, overwrite=True, **kwargs)
    time_normalize_raster(source, target, **kwargs)
    with pytest.raises(ValueError, match="already"):
        time_normalize_raster(target, tmp_path / "twice.tif", **kwargs)


def test_runner_protects_auxiliary_inputs_of_later_stages(tmp_path):
    runner = load_runner()
    config_path = runner.create_demo(tmp_path / "demo")
    predictor = config_path.parent / "predictor.tif"
    original = predictor.read_bytes()
    config = json.loads(config_path.read_text())
    config["sources"][0]["angle"]["output_path"] = "predictor.tif"
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="input|auxiliary"):
        runner.run_stage(config_path, "angle", overwrite=True)
    assert predictor.read_bytes() == original


def test_tsharp_raster_decodes_ndvi_and_records_method(tmp_path):
    from base.normalization.raster import downscale_raster
    ndvi = np.arange(24).reshape(4,6)*.025+.1
    mean = ndvi.reshape(2,2,3,2).mean((1,3))
    coarse = 310-20*(1-(1-mean)**.625)
    source,aux,target = tmp_path/'lst.tif',tmp_path/'ndvi.tif',tmp_path/'tsharp.tif'
    write_tif(source,coarse)
    write_tif(aux,ndvi*10000,scale=.0001,transform=(100,1,0,200,0,-1))
    downscale_raster(source,target,predictors=[{'path':str(aux)}],method='tsharp')
    fields,metadata = read_raster(target)
    np.testing.assert_allclose(fields['temperature_k'].reshape(2,2,3,2).mean((1,3)),coarse,atol=3e-5)
    params = json.loads(metadata['LS4T_NORMALIZATION'])['history'][-1]['parameters']
    assert params['method'] == 'tsharp'
    assert params['predictor_transform'] == '1-(1-NDVI)**0.625'
    np.testing.assert_allclose(params['coefficients'],[310,-20],atol=1e-8)


def test_tsharp_raster_rejects_multiple_predictors_before_writing(tmp_path):
    from base.normalization.raster import downscale_raster
    output = tmp_path/'out.tif'
    with pytest.raises(ValueError,match='one|single'):
        downscale_raster(tmp_path/'missing.tif',output,method='tsharp',
                         predictors=[{'path':'ndvi.tif'},{'path':'dem.tif'}])
    assert not output.exists()


def test_multisource_tsharp_demo_is_runnable(tmp_path):
    runner = load_runner()
    config = runner.create_demo(tmp_path/'tsharp with spaces',downscale_method='tsharp')
    for stage in ('angle','time','downscale'):
        outputs = runner.run_stage(config,stage)
    fields,metadata = read_raster(outputs[0])
    other,_ = read_raster(outputs[1])
    np.testing.assert_allclose(fields['temperature_k'],other['temperature_k'],atol=3e-5)
    assert np.isfinite(fields['temperature_k']).all()
    assert json.loads(metadata['LS4T_NORMALIZATION'])['history'][-1]['parameters']['method'] == 'tsharp'
