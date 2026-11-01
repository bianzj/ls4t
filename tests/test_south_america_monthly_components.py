"""Scientific contract checks for the Amazon monthly component composites."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from osgeo import gdal

PATH = Path(__file__).resolve().parents[1]/'cases/slstr-america/monthly_components.py'
spec = importlib.util.spec_from_file_location('amazon_monthly', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_signed_and_legacy_geolocation_and_fill():
    raw = np.array([-1200, 10200, -32768, 1200], dtype=np.int16)
    actual = m.decode_geo(raw, -32768, 90.)
    np.testing.assert_allclose(actual, [-12., -12., np.nan, 12.], equal_nan=True)
    np.testing.assert_allclose(m.decode_geo(np.array([-6500, 24500]), None, 180), [-65, -65])


def test_common_mask_and_native_collisions():
    # First two native samples land in the same grid cell; third lacks LST.
    values = np.array([[300, 302, 300], [290, 292, 290], [310, 312, 310],
                       [295, 297, 295], [299, 301, 0]], np.float32)[:, None, :]
    ids, binned, n = m.bin_scene(values, np.array([[.9, .9, .9]]),
                               np.array([[.1, .1, .6]]), (0, 0, 1, 1), .5)
    np.testing.assert_array_equal(ids, [0])
    np.testing.assert_allclose(binned[:, 0], [301, 291, 311, 296, 300])
    assert n == 2


def test_daily_overlap_then_equal_day_mean():
    total = np.zeros((5, 2), np.float64)
    count = np.zeros(2, np.uint16)
    day = np.zeros((5, 2), np.float32)
    day[:, 0] = 280  # early acquisition
    day[:, 0] = 300  # later acquisition replaces it
    m.accumulate_day(total, count, day)
    day.fill(0); day[:, 0] = 310
    m.accumulate_day(total, count, day)
    np.testing.assert_allclose(total[:, 0]/count[0], 305)
    np.testing.assert_array_equal(count, [2, 0])


def test_grid_boundaries_are_not_clipped_into_window():
    values = np.full((5, 1, 4), 300, np.float32)
    ids, _, n = m.bin_scene(values, np.array([[1, .5, 0, .5]]),
                           np.array([[0, 1, .5, -.1]]), (0, 0, 1, 1), .5)
    np.testing.assert_array_equal(ids, [0])
    assert n == 1


def test_rejects_unphysical_soil_order():
    v = np.array([300, 290, 290, 310, 300], np.float32).reshape(5, 1, 1)
    with pytest.raises(ValueError, match='sunlit soil'):
        m.bin_scene(v, np.array([[0.]]), np.array([[-60.]]))


def test_monthly_geotiff_roundtrip_common_mask_counts_and_units(tmp_path, monkeypatch):
    monkeypatch.setattr(m, 'BOUNDS', (0., 0., 1., 1.))
    monkeypatch.setattr(m, 'RESOLUTION', .5)
    total = np.zeros((5, 2, 2), np.float64)
    total[:, 0, 0] = np.array([300, 290, 310, 295, 299]) * 2
    count = np.array([[2, 0], [0, 0]], np.uint16)
    p = tmp_path/'month.tif'
    m.write_tif(p, total, count)
    stats = m.verify_tif(p)
    assert stats['valid_pixels'] == 1
    assert stats['maximum_valid_days'] == 2
    ds = gdal.Open(str(p))
    assert ds.GetRasterBand(1).GetUnitType() == 'K'
    assert ds.GetRasterBand(6).GetUnitType() == 'days'
    a = ds.ReadAsArray()
    np.testing.assert_allclose(a[:5, 0, 0], [300, 290, 310, 295, 299])
    np.testing.assert_array_equal(a[:5, 1, 1], [-9999]*5)
    assert a[5, 1, 1] == 0


def test_month_job_uses_late_scene_then_equal_days_and_detects_changed_output(tmp_path, monkeypatch):
    monkeypatch.setattr(m, 'BOUNDS', (0., 0., 1., 1.))
    monkeypatch.setattr(m, 'RESOLUTION', .5)
    scenes = []
    for k, (day, time, temperatures) in enumerate([
        ('20240401', '100000', [300, 290, 310, 295, 299]),
        ('20240401', '110000', [304, 294, 314, 299, 303]),
        ('20240402', '100000', [306, 296, 316, 301, 305]),
    ]):
        folder = tmp_path/f'scene{k}'; folder.mkdir()
        paths = []
        for i, value in enumerate(temperatures + [75, 25]):
            p = folder/f'{i}.tif'
            ds = gdal.GetDriverByName('GTiff').Create(str(p), 1, 1, 1, gdal.GDT_Float32)
            ds.GetRasterBand(1).WriteArray(np.array([[value * (100 if i == 4 else 1)]], np.float32))
            ds = None
            paths.append(str(p))
        scenes.append({'scene': f'scene{k}', 'day': day, 'time': time,
                       'paths': paths, 'files': {p:m.stamp(p) for p in paths}})
    task = ('202404', list(reversed(scenes)), str(tmp_path/'output'), str(tmp_path/'run'))
    result = m.month_job(task)
    assert result['valid_days'] == ['20240401', '20240402']
    assert result['maximum_valid_days'] == 2
    ds = gdal.Open(result['output'])
    np.testing.assert_allclose(ds.ReadAsArray()[:, 0, 0], [305, 295, 315, 300, 304, 2])
    ds = None
    assert m.month_job(task)['reused'] is True
    with Path(result['output']).open('ab') as handle:
        handle.write(b'changed')
    with pytest.raises(ValueError, match='existing output differs'):
        m.month_job(task)
