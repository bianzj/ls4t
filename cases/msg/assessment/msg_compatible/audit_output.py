"""独立核查实际完整影像、MSG配套格式及逐时次月均；不修改产品。"""
from contextlib import ExitStack
from pathlib import Path
import argparse
import hashlib
import json

import h5py
import numpy as np
from osgeo import gdal, osr


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def grid_check(ds, reference):
    assert (ds.RasterYSize, ds.RasterXSize) == (reference.RasterYSize, reference.RasterXSize)
    np.testing.assert_allclose(ds.GetGeoTransform(), reference.GetGeoTransform(), rtol=0, atol=1e-9)
    assert osr.SpatialReference(wkt=ds.GetProjection()).IsSame(osr.SpatialReference(wkt=reference.GetProjection()))


def commit_check(path):
    marker = json.loads(Path(str(path) + '.complete.json').read_text(encoding='utf-8'))
    for filename, record in marker['files'].items():
        assert Path(filename).is_file() and Path(filename).stat().st_size == record['bytes']
        assert sha(filename) == record['sha256'], filename
    return marker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--month', default='202407')
    parser.add_argument('--hour', type=int, default=12)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('actual_product_audit.json'))
    args = parser.parse_args()
    gdal.UseExceptions()
    reference = gdal.Open('E:/Static/combined_euro_vza.tif')
    monthly_path = args.root / 'MONTHLY_HOUR' / args.month[:4] / f'MLST_MONTH_{args.month}_HH{args.hour:02d}.h5'
    marker = commit_check(monthly_path)
    scene_checks = []
    with h5py.File(monthly_path, 'r') as month:
        assert month['data'].id == month['Monthly_Hour_Mean_LST'].id
        assert month['data'].shape == (4, reference.RasterYSize, reference.RasterXSize)
        assert month['data'].dtype == np.float32
        assert month['data'].attrs['Scale_Factor'] == 100 and month['data'].attrs['scale_factor'] == .01
        assert month.attrs['Scale_Factor'] == 100 and month.attrs['scale_factor'] == .01
        assert month.attrs['Units'] == 'K' and np.isnan(month.attrs['Missing_Value'])
        assert month.attrs['Stored_Value_Convention'] == 'stored_value = kelvin * Scale_Factor'
        assert month.attrs['TimeZone'] == 'UTC'
        assert int(month.attrs['Year']) == int(args.month[:4])
        assert int(month.attrs['Month']) == int(args.month[4:]) and int(month.attrs['Hour']) == args.hour
        sources = list(json.loads(month.attrs['source_sha256_json']))
        assert len(sources) == int(month.attrs['source_count'])
        stamps = json.loads(month.attrs['source_timestamps_json'])
        assert all(stamp.startswith(args.month) and stamp[8:] == f'{args.hour:02d}00' for stamp in stamps)
        sample_indices = sorted(set([0, len(sources) // 2, len(sources) - 1]))
        for index in sample_indices:
            path = Path(sources[index])
            scene_marker = commit_check(path)
            with h5py.File(path, 'r') as scene:
                values = scene['data'][...]
                valid = np.all((values >= 25000) & (values <= 35000), axis=0)
                assert np.array_equal(valid, np.any(values != 0, axis=0))
                assert np.array_equal(np.any(values == 0, axis=0), np.all(values == 0, axis=0))
                assert int(valid.sum()) == int(scene.attrs['valid_pixels']) and valid.any()
                neighbors = scene['valid_neighbors'][...]
                qa = scene['qa'][...]
                assert np.all(neighbors[valid] >= 10) and np.all(neighbors <= 25)
                assert np.all((qa[valid] & 15) == 0)
                timestamp = str(scene.attrs['timestamp_UTC'])
                assert timestamp.endswith('+00:00') and int(timestamp[11:13]) == args.hour
                assert scene.attrs['identity_hash'] == month.attrs['identity_hash']
                geometry = json.loads(scene.attrs['geometry_json'])
                assert geometry['position_policy'] == 'MEAN_SS_only_no_NOMINAL_fallback'
                assert all(not (p['latitude_deg'] == 0 and p['longitude_deg'] == 0) for p in geometry['positions'].values())
                ds = gdal.Open(scene_marker['geotiff'])
                grid_check(ds, reference)
                assert ds.RasterCount == 4 and ds.GetMetadataItem('TIME_ZONE') == 'UTC'
                for band in range(1, 5):
                    rb = ds.GetRasterBand(band)
                    assert rb.GetScale() == .01 and rb.GetUnitType() == 'K' and rb.GetNoDataValue() == 0
                    np.testing.assert_array_equal(rb.ReadAsArray(), values[band - 1])
                scene_checks.append({'timestamp_UTC': timestamp, 'valid_pixels': int(valid.sum()),
                                     'hdf5': str(path), 'geotiff': scene_marker['geotiff'], 'status': 'passed'})
        means = month['data'][...]
        counts = month['n_obs'][...]
        valid = counts > 0
        assert np.array_equal(valid, np.isfinite(means).all(axis=0))
        assert np.all(np.isnan(means[:, ~valid])) and np.all((means[:, valid] >= 25000) & (means[:, valid] <= 35000))
        assert int(counts.max()) <= len(sources)
        assert np.array_equal(month['low_support'][...], ((counts > 0) & (counts < 3)).astype('uint8'))
        rng = np.random.default_rng(20261011)
        positions = np.flatnonzero(valid)
        selected = rng.choice(positions, min(20, len(positions)), replace=False)
        pixels = [(int(p // counts.shape[1]), int(p % counts.shape[1])) for p in selected]
        pixels += [(0, 0), (counts.shape[0] - 1, counts.shape[1] - 1)]
        verification = []
        with ExitStack() as stack:
            scenes = [stack.enter_context(h5py.File(path, 'r')) for path in sources]
            for y, x in pixels:
                raw = np.asarray([scene['data'][:, y, x] for scene in scenes])
                good = np.all((raw >= 25000) & (raw <= 35000), axis=1)
                assert int(counts[y, x]) == int(good.sum())
                if good.any():
                    np.testing.assert_allclose(means[:, y, x], raw[good].mean(axis=0), rtol=0, atol=.002)
                else:
                    assert np.isnan(means[:, y, x]).all()
                verification.append({'row': y, 'column': x, 'effective_days': int(good.sum())})
        ds = gdal.Open(marker['geotiff'])
        grid_check(ds, reference)
        for band in range(1, 5):
            rb = ds.GetRasterBand(band)
            assert rb.GetScale() in [None, 1] and rb.GetUnitType() == 'K' and np.isnan(rb.GetNoDataValue())
            np.testing.assert_allclose(rb.ReadAsArray(), means[band - 1].astype('float64') * .01,
                                       rtol=0, atol=4e-5, equal_nan=True)
        result = {'status': 'passed', 'month': args.month, 'hour_UTC': args.hour, 'source_scenes': len(sources),
                  'full_scene_checks': scene_checks, 'monthly_valid_pixels': int(valid.sum()),
                  'monthly_pixel_checks': verification, 'mean_count_same_support': True,
                  'grid_CRS_UTC_scale_band_order_verified': True, 'hdf5_geotiff_values_verified': True,
                  'completed_file_hashes_verified': True, 'monthly_hdf5': str(monthly_path),
                  'monthly_geotiff': marker['geotiff'], 'identity_hash': month.attrs['identity_hash'],
                  'limits': 'Actual product consistency and implementation checks; not independent ground accuracy.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
