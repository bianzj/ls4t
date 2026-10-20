"""Portable real-data integration checks; deliberately independent of E:/ sources."""

import importlib.util
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("osgeo")
from osgeo import gdal, osr

gdal.UseExceptions()
osr.UseExceptions()

SCRIPT = Path(__file__).parent / "examples/msg_evo_sample.py"
SPEC = importlib.util.spec_from_file_location("msg_evo_sample", SCRIPT)
example = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(example)


def test_msg_evo_fixture_is_real_full_month_and_one_grid():
    sample = example.SAMPLE
    manifest = json.loads((sample / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["synthetic"] is False
    assert manifest["schema"] == "ls4t.real-msg-test-sample/v2"
    assert manifest["period"] == "2017-10"
    assert manifest["site"]["id"] == "EVO"
    assert manifest["shape"] == [10, 10]
    assert manifest["station_source_row_col"] == [881, 333]
    assert manifest["station_sample_row_col"] == [5, 5]
    assert manifest["missing_source_count"] == 0
    times = manifest["timestamps_utc"]
    assert len(times) == len(set(times)) == 31 * 24
    assert times == sorted(times)
    assert times[0] == "201710010000" and times[-1] == "201710312300"
    assert len(manifest["lai_dates_utc"]) == 31
    expected_crs = osr.SpatialReference()
    expected_crs.ImportFromEPSG(4326)
    for name, record in manifest["files"].items():
        path = sample / name
        assert path.stat().st_size == record["size_bytes"], name
        assert example.sha256(path) == record["sha256"], name
        if path.suffix != ".tif":
            continue
        dataset = gdal.Open(str(path))
        assert (dataset.RasterYSize, dataset.RasterXSize) == (10, 10), name
        np.testing.assert_allclose(dataset.GetGeoTransform(), manifest["geotransform"], rtol=0, atol=1e-10)
        assert osr.SpatialReference(wkt=dataset.GetProjection()).IsSame(expected_crs), name
        if name.startswith("PRODUCTS/"):
            assert dataset.RasterCount == 1
            band = dataset.GetRasterBand(1)
            assert band.DataType == gdal.GDT_UInt16
            assert band.GetNoDataValue() == 0
            assert band.GetScale() is None and band.GetOffset() is None
        if name.startswith("Static/"):
            assert dataset.RasterCount == 1
            assert dataset.GetRasterBand(1).DataType == gdal.GDT_Int16
        dataset = None
    sources = json.loads((sample / "sources.json").read_text(encoding="utf-8"))
    assert not sources["missing_sources"]
    counts = {name: 0 for name in ("lst_euro", "lst_iodc", "lai")}
    for record in sources["records"]:
        if "product" in record:
            counts[record["product"]] += 1
            assert record["timestamp_utc"].startswith("201710")
            assert len(record["window_raw_sha256"]) == 64
            path = Path(record["sample_path"])
            stamp = record["timestamp_utc"]
            sensor, family, variable, disk = {
                "lst_euro": ("MSG", "MLST", "LST", "MSG-Disk"),
                "lst_iodc": ("MSG-IODC", "MLST", "LST", "IODC-Disk"),
                "lai": ("MSG", "MDLAI", "LAI", "MSG-Disk"),
            }[record["product"]]
            assert path.as_posix() == (
                f"PRODUCTS/{sensor}/{family}/GEOTIFF/{stamp[:4]}/{stamp[4:6]}/{stamp[6:8]}/"
                f"HDF5_LSASAF_{sensor}_{variable}_{disk}_{stamp}.tif"
            )
            dataset = gdal.Open(str(sample / path))
            raw = dataset.ReadAsArray()
            assert str(raw.dtype) == record["raw_dtype"]
            assert hashlib.sha256(raw.tobytes()).hexdigest() == record["window_raw_sha256"]
            dataset = None
    assert counts == {"lst_euro": 744, "lst_iodc": 744, "lai": 31}


def test_msg_raw_signed_encoding_and_nodata_are_decoded_only_on_read():
    # Negative Celsius bit patterns survive UInt16 storage; both missing codes are masked.
    raw = np.array([[-100, 1234, -8000, 0]], dtype=np.int16).view(np.uint16)
    information = {"missing_value": -8000, "scaling_factor": 100., "offset": 0.}
    actual = example.decode(raw, 0, information, "LST")
    np.testing.assert_allclose(actual, [[272.15, 285.49, np.nan, np.nan]], equal_nan=True)


def test_real_month_retrieves_components_without_filling_missing_pixels(tmp_path):
    summary, temperature, quality = example.run_sample(output=tmp_path)
    assert summary["valid_pixel_times"] > 100
    assert summary["valid_center_times"] > 0
    assert temperature.shape == (744, 10, 10, 2)
    assert quality.shape == (744, 10, 10)
    valid_output = np.isfinite(temperature).all(-1)
    assert np.all((temperature[valid_output] >= 250.) & (temperature[valid_output] <= 350.))
    manifest, data = example.load_sample()
    for index in range(744):
        if np.any(data["solar_zenith_deg"][index] < 90):
            _, _, valid_input = example.prepare_frame(manifest, data, index)
        else:
            valid_input = np.zeros((10, 10), bool)
        assert not np.any(valid_output[index] & ~valid_input), manifest["timestamps_utc"][index]
    # Check the actual persisted result and its geolocation, not merely an array.
    stored, names, transform, _ = example.read_stack(tmp_path / "soil.tif")
    assert names == manifest["timestamps_utc"]
    np.testing.assert_allclose(stored, temperature[..., 0], rtol=1e-6, equal_nan=True)
    np.testing.assert_allclose(transform, manifest["geotransform"], rtol=0, atol=1e-10)
    assert json.loads((tmp_path / "summary.json").read_text())["valid_pixel_times"] == int(valid_output.sum())


@pytest.mark.parametrize("components", [2, 3])
def test_real_center_agrees_with_independent_neighborhood_least_squares(components):
    manifest, data = example.load_sample()
    _, temperature, _ = example.run_sample(components=components)
    candidates = np.flatnonzero(np.isfinite(temperature[:, 5, 5]).all(-1))
    assert len(candidates) > 0
    index = int(candidates[0])
    observed, weights, _ = example.prepare_frame(manifest, data, index, components)
    y = observed[3:8, 3:8].reshape(-1)
    matrix = weights[3:8, 3:8].reshape(-1, components)
    good = np.isfinite(y) & np.isfinite(matrix).all(-1)
    radiance, _, rank, _ = np.linalg.lstsq(matrix[good], y[good], rcond=None)
    assert rank == components
    # Independent physical constants/formula check wavelength and radiance units.
    h, c, k, wavelength_m = 6.62607015e-34, 299792458., 1.380649e-23, 10.5e-6
    expected = h * c / (k * wavelength_m * np.log1p(2 * h * c**2 / (radiance * 1e6 * wavelength_m**5)))
    np.testing.assert_allclose(temperature[index, 5, 5], expected, rtol=0, atol=1e-6)
