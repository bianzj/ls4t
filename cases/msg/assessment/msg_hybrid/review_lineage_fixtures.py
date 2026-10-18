"""Independent tiny legacy-compatibility/month-merge tests; no production."""
from copy import deepcopy
from pathlib import Path
import datetime as dt
import json
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import h5py
import numpy as np
from osgeo import gdal, osr
import collection_lineage as lineage
import merge_collection as merger
import produce_msg_ls4t as p

HERE = Path(__file__).resolve().parent


def rejected(call, expected=RuntimeError):
    try:
        call()
    except expected:
        return
    raise AssertionError('Invalid reuse unexpectedly accepted')


def geometry(stamp, mode):
    return {'timestamp_UTC': stamp,
            'position_policy': ('MEAN_SS_only_no_NOMINAL_fallback' if mode == 'dynamic'
                                else 'declared_geostationary_slots_nominal_latitude_zero'),
            'positions': {'e': {'latitude_deg': 2. if mode == 'dynamic' else 0.,
                                'longitude_deg': -.1 if mode == 'dynamic' else 0.},
                          'i': {'latitude_deg': -8. if mode == 'dynamic' else 0.,
                                'longitude_deg': 41.4 if mode == 'dynamic' else 41.5}},
            'satellite_geocentric_radius_m': 42164000., 'ground_ellipsoid': 'WGS84',
            'ground_height_m': 0., 'target_pixel_reference': 'legacy_pixel_corner_coordinates_supplied_by_producer',
            'azimuth_convention': 'ground_to_satellite_north_0_east_90_0_to_360',
            'iodc_native_grid_longitude_deg': 41.5}


def selected(old, mode):
    new = deepcopy(old)
    new['position_policy'] = 'per_view_dynamic_MEAN_SS_then_declared_static_slot'
    new['geometry_modes'] = {'e': mode, 'i': mode}
    for view in ['e', 'i']:
        new['positions'][view]['mode'] = mode
    return new


def write_scene(root, stamp, identity, encoded, old_geometry):
    hdf, tif = p.instant_path(root, stamp), p.scene_tif_path(root, stamp)
    for path in [hdf, tif]:
        path.parent.mkdir(parents=True, exist_ok=True)
    input_records = {'input_'+stamp: {'sha256': '9'*64, 'bytes': 123}}
    signature = p.hash_object({'inputs': input_records, 'geometry': old_geometry})
    hdf_temp, tif_temp = Path(str(hdf)+'.partial'), Path(str(tif)+'.partial')
    with h5py.File(hdf_temp, 'w') as file:
        p.attrs(file, identity)
        for key in ['identity_hash', 'code_sha256', 'protocol_hash', 'implementation_sha256',
                    'static_source_hash', 'geometry_plan_sha256']:
            file.attrs[key] = identity[key]
        file.attrs.update(complete=1, source_signature=signature,
                          inputs_json=p.json_text(input_records), geometry_json=p.json_text(old_geometry))
        data = file.create_dataset('data', data=np.full((4, 8, 12), encoded, dtype='uint16'))
        p.data_attrs(data, identity)
    raster = p.create_tif(tif_temp, identity, gdal.GDT_UInt16, stamp, .01, 0)
    raster.SetMetadataItem('PROTOCOL_HASH', identity['protocol_hash'])
    for band in range(1, 5):
        raster.GetRasterBand(band).WriteArray(np.full((8, 12), encoded, dtype='uint16'))
    raster.FlushCache()
    raster = None
    record = p.commit_products(hdf_temp, tif_temp, hdf, tif, identity, signature,
                               {'timestamp': stamp, 'geometry': old_geometry, 'hdf5': str(hdf), 'geotiff': str(tif)})
    return hdf, tif, record, input_records


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix='independent_lineage_fixture_', dir=HERE) as temporary:
        root = Path(temporary)
        crs = osr.SpatialReference()
        crs.ImportFromEPSG(4326)
        base = {'grid': {'shape': [8, 12], 'GeoTransform': [0., .03, 0., 1., 0., -.03],
                         'Projection': crs.ExportToWkt(), 'EPSG': 4326},
                'identity_hash': '1'*64, 'code_sha256': '2'*64, 'protocol_hash': p.PROTOCOL_HASH,
                'implementation_sha256': '3'*64, 'static_source_hash': '4'*64,
                'geometry_plan_sha256': '5'*64, 'static_sources': {}}
        static_identity = dict(base, identity_hash='a'*64, code_sha256='b'*64)
        dynamic_identity = dict(base, identity_hash='c'*64, code_sha256='d'*64)
        identity = dict(base, compatible_legacy_identities={static_identity['identity_hash']: static_identity,
                                                         dynamic_identity['identity_hash']: dynamic_identity})
        (root/'production_identity.json').write_text(p.json_text(identity), encoding='utf8')
        all_records, scenes = [], []
        for stamp, mode, computed, encoded in [('201708011200', 'static', static_identity, 30000),
                                               ('201708021200', 'dynamic', dynamic_identity, 32000),
                                               ('201708031200', 'static', identity, 31000)]:
            old_geometry = geometry(stamp, mode)
            if computed is identity:
                old_geometry = selected(old_geometry, mode)
            hdf, tif, record, inputs = write_scene(root, stamp, computed, encoded, old_geometry)
            context = {'inputs': inputs, 'geometry': selected(old_geometry, mode)}
            before = {str(path): p.sha(path) for path in [hdf, tif, p.commit_path(hdf)]}
            resumed = p.check_resume(hdf, tif, identity, p.hash_object(context), context=context)
            assert resumed['identity_hash'] == computed['identity_hash']
            assert resumed['validated_collection_identity'] == identity['identity_hash']
            assert before == {str(path): p.sha(path) for path in [hdf, tif, p.commit_path(hdf)]}
            all_records.append(resumed)
            scenes.append((hdf, tif, record, context))
        checks.append('Dynamic/static legacy scenes preserve original pair/marker bytes and calculation identity when inputs, positions and model are equivalent')
        hdf, tif, record, context = scenes[0]
        for mutation in ['mixed_view_mode', 'position', 'radius', 'inputs']:
            changed = deepcopy(context)
            if mutation == 'mixed_view_mode':
                changed['geometry']['positions']['i']['mode'] = 'dynamic'
                changed['geometry']['geometry_modes']['i'] = 'dynamic'
            elif mutation == 'position':
                changed['geometry']['positions']['i']['longitude_deg'] += .01
            elif mutation == 'radius':
                changed['geometry']['satellite_geocentric_radius_m'] += 1000.
            else:
                next(iter(changed['inputs'].values()))['sha256'] = '0'*64
            assert p.check_resume(hdf, tif, identity, p.hash_object(changed), context=changed) is None
            folder = root/'_PROVENANCE/replaced'/hdf.stem/record['files'][str(hdf)]['sha256']
            for path in [hdf, tif, p.commit_path(hdf)]:
                assert p.sha(folder/path.name) == p.sha(path)
        checks.append('Mixed view, changed position/model/input require recomputation after verified provenance copies; originals remain byte-identical')
        rejected(lambda: p.check_resume(hdf, tif, dict(identity, compatible_legacy_identities={}),
                                        p.hash_object(context), context=context))
        rejected(lambda: p.check_resume(hdf, tif, identity, record['source_signature']))
        original_marker = p.commit_path(hdf).read_bytes()
        corrupt = dict(record, source_signature='f'*64)
        p.atomic_json(p.commit_path(hdf), corrupt)
        rejected(lambda: p.check_resume(hdf, tif, identity, p.hash_object(context), context=context))
        p.commit_path(hdf).write_bytes(original_marker)
        checks.append('Unapproved identities, legacy instantaneous reuse without physical context, and HDF/marker signature mismatch rejected')
        sources = p.file_manifest([scenes[0][0], scenes[1][0]])
        rejected(lambda: lineage.check_month_sources([scenes[0][0], scenes[1][0]], sources, [], identity))
        forged = deepcopy(all_records[0])
        forged['timestamp'] = '201708991200'
        rejected(lambda: lineage.check_month_sources([scenes[0][0]], p.file_manifest([scenes[0][0]]), [forged], identity))
        checks.append('Legacy monthly inputs require path/timestamp/hash-bound current-collection scene validation')
        expected = ['201708011200', '201708021200', '201708031200']
        initial = [scenes[0][0], scenes[2][0]]
        p.monthly(root, '201708', 12, initial, expected,
                  [{'timestamp': expected[1], 'status': 'failed', 'error': 'fixture recovery'}], identity,
                  tile_rows=3, validated_records=[all_records[0], all_records[2]])
        month = root/'MONTHLY_HOUR/2017/MLST_MONTH_201708_HH12.h5'
        with h5py.File(month, 'r') as file:
            assert file.attrs['source_count'] == 2
            assert np.all(file['data'][:] == 30500.) and np.all(file['n_obs'][:] == 2)
            assert np.all(file['low_support'][:] == 1) and np.all(file['qa'][:] == 6)
        p.monthly(root, '201708', 12, [s[0] for s in scenes], expected, [], identity,
                  tile_rows=3, validated_records=all_records)
        with h5py.File(month, 'r') as file:
            assert file.attrs['source_count'] == 3 and file.attrs['calendar_input_complete'] == 1
            assert np.all(file['data'][:] == 31000.) and np.all(file['n_obs'][:] == 3)
            assert np.all(file['low_support'][:] == 0) and np.all(file['qa'][:] == 0)
            assert json.loads(file.attrs['source_timestamps_json']) == expected
        raster = gdal.Open(str(root/'MONTHLY_HOUR_GEOTIFF/2017/MLST_MONTH_201708_HH12.tif'))
        assert np.all(raster.ReadAsArray() == 310.)
        raster = None
        checks.append('Union of static/dynamic/current scenes refreshes source_count, mean, n_obs, calendar/low-support flags and omissions')
        # Exercise the actual transfer code only against private tiny files.
        destination, staging = root/'merge_destination', root/'merge_staging'
        destination.mkdir()
        staging.mkdir()
        (destination/'production_identity.json').write_text(p.json_text(dynamic_identity), encoding='utf8')
        (staging/'production_identity.json').write_text(p.json_text(static_identity), encoding='utf8')
        old_geometry = geometry('201708041200', 'static')
        legacy_hdf, legacy_tif, legacy_record, inputs = write_scene(staging, '201708041200', static_identity, 30000, old_geometry)
        original_bytes = {path.name: path.read_bytes() for path in [legacy_hdf, legacy_tif, p.commit_path(legacy_hdf)]}
        reviews = root/'merge_review'
        reviews.mkdir()
        (reviews/'independent_code_review.json').write_text(p.json_text({'status': 'PASS',
            'reviewed_files': {'merge_collection.py': p.sha(merger.__file__)}}), encoding='utf8')
        with patch.object(merger, 'HERE', reviews), patch.object(p, 'assert_code_review'), \
                patch.object(p, 'build_identity', return_value=(identity, {})), \
                patch.object(p, 'grid_info', return_value=base['grid']), \
                patch.object(p, 'load_geometry_module', return_value=SimpleNamespace(
                    geometry_metadata=lambda stamp, plan: selected(old_geometry, 'static'))), \
                patch.object(p, 'paths', return_value={'fixture': Path('private-input')}), \
                patch.object(p, 'file_manifest', return_value=inputs):
            merger.prepare(destination, staging, root)
            assert original_bytes == {path.name: path.read_bytes() for path in [legacy_hdf, legacy_tif, p.commit_path(legacy_hdf)]}
            imported = p.instant_path(destination, '201708041200')
            imported_tif = p.scene_tif_path(destination, '201708041200')
            assert imported.read_bytes() == original_bytes[legacy_hdf.name]
            assert imported_tif.read_bytes() == original_bytes[legacy_tif.name]
            imported_record = json.loads(p.commit_path(imported).read_text(encoding='utf8'))
            assert imported_record['identity_hash'] == static_identity['identity_hash']
            assert imported_record['source_signature'] == legacy_record['source_signature']
            assert imported_record['files'][str(imported)] == legacy_record['files'][str(legacy_hdf)]
            assert Path(imported_record['import_provenance']['original_marker']).read_bytes() == original_bytes[p.commit_path(legacy_hdf).name]
            merger.prepare(destination, staging, root)  # Idempotent, original bytes retained.
            merged_identity = json.loads((destination/'production_identity.json').read_text(encoding='utf8'))
            assert merged_identity == dict(identity, protocol=p.PROTOCOL)
            tampered = dict(merged_identity, unexpected_payload='must reject')
            (destination/'production_identity.json').write_text(p.json_text(tampered), encoding='utf8')
            rejected(lambda: merger.prepare(destination, staging, root))
            (reviews/'independent_code_review.json').write_text(p.json_text({'status': 'PASS',
                'reviewed_files': {'merge_collection.py': '0'*64}}), encoding='utf8')
            rejected(lambda: merger.prepare(destination, staging, root))
        checks.append('Private merge preserves source/destination product bytes, original calculation identity/signature and marker snapshot; repeat is idempotent; altered controller/migration-code SHA rejects')
    report = {'status': 'PASS', 'reviewed_UTC': dt.datetime.now(dt.timezone.utc).isoformat(),
              'scope': 'Independent 8x12 private file fixtures only; no real migration or production invoked.',
              'producer_sha256': p.sha(HERE/'produce_msg_ls4t.py'),
              'lineage_sha256': p.sha(HERE/'collection_lineage.py'),
              'merge_sha256': p.sha(HERE/'merge_collection.py'), 'checks': checks}
    (HERE/'independent_lineage_fixture_review.json').write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
