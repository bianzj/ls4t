"""Independent code/auxiliary audit. Never launches production or migration."""
from pathlib import Path
import argparse
import ast
from copy import deepcopy
from contextlib import ExitStack
import datetime as dt
import hashlib
import json
import sys
import tempfile
from unittest.mock import patch

import h5py
import numpy as np
import msg_view_geometry as geometry
import produce_msg_ls4t as producer

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / 'msg_compatible' / 'produce_msg_ls4t.py'
REVIEW_FILES = ['produce_msg_ls4t.py', 'msg_view_geometry.py', 'geometry_plan.json',
                'build_static_geometry.py', 'static_geometry.h5', 'collection_lineage.py', 'merge_collection.py']


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as file:
        for block in iter(lambda: file.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def canonical_functions(path):
    tree = ast.parse(Path(path).read_text(encoding='utf8'))
    return {node.name: ast.dump(node, include_attributes=False)
            for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def independent_angles(latitude, longitude, orbit_latitude, orbit_longitude):
    """Analytic ENU components, independent of the helper's ECEF subtraction."""
    a, b, radius = 6378137., 6356752.314245179, 42164000.
    phi = np.deg2rad(latitude)
    satellite_phi = np.deg2rad(orbit_latitude)
    delta = np.deg2rad(orbit_longitude - longitude)
    eccentricity = 1. - (b / a)**2
    normal = a / np.sqrt(1. - eccentricity * np.sin(phi)**2)
    east = radius * np.cos(satellite_phi) * np.sin(delta)
    north = (radius * (np.sin(satellite_phi) * np.cos(phi)
             - np.cos(satellite_phi) * np.cos(delta) * np.sin(phi))
             + eccentricity * normal * np.sin(phi) * np.cos(phi))
    up = (radius * (np.cos(satellite_phi) * np.cos(delta) * np.cos(phi)
          + np.sin(satellite_phi) * np.sin(phi))
          - normal * (1. - eccentricity * np.sin(phi)**2))
    return (np.rad2deg(np.arctan2(np.hypot(east, north), up)),
            np.rad2deg(np.arctan2(east, north)) % 360.)


def angle_error(actual, expected):
    return float(abs((float(actual) - float(expected) + 180.) % 360. - 180.))


def audit_cache(plan, hashes):
    assert plan['geometry_helper_sha256'] == hashes['msg_view_geometry.py']
    assert plan['static_geometry_sha256'] == hashes['static_geometry.h5']
    cache_path = Path(plan['static_geometry_file'])
    assert cache_path.resolve() == (HERE / 'static_geometry.h5').resolve()
    assert cache_path.stat().st_size == plan['static_geometry_bytes']
    assert plan['nominal_satellite_latitude_deg'] == 0.
    assert plan['position_policy'] == geometry.POSITION_POLICY
    assert plan['excluded_input_geolocation_months'] == ['202206']
    assert plan['legacy_native_projection_placeholder'] == 'Geos<000.0>'
    slots = {'euro': 0., 'iodc_old': 41.5, 'iodc_new': 45.5}
    assert {key: value['orbital_slot_longitude_deg'] for key, value in plan['declarations'].items()} == slots
    sources = {}
    for key, declaration in plan['declarations'].items():
        file = Path(declaration['path'])
        actual = sha(file)
        assert actual == declaration['sha256']
        assert file.stat().st_size == declaration['bytes']
        sources[key] = {'path': str(file), 'sha256': actual}
    maximum_zenith, maximum_azimuth = 0., 0.
    with h5py.File(cache_path, 'r') as file:
        assert int(file.attrs['complete']) == 1
        assert file.attrs['helper_sha256'] == hashes['msg_view_geometry.py']
        assert file.attrs['builder_sha256'] == hashes['build_static_geometry.py']
        assert file.attrs['satellite_geocentric_radius_m'] == 42164000.
        assert file.attrs['ground_ellipsoid'] == 'WGS84'
        assert file.attrs['ground_height_m'] == 0.
        assert file.attrs['target_pixel_reference'] == 'legacy_pixel_corner_coordinates_supplied_by_producer'
        assert file.attrs['azimuth_convention'] == 'ground_to_satellite_north_0_east_90_0_to_360'
        grid = json.loads(file.attrs['grid_json'])
        assert grid == producer.grid_info(Path(plan['input_root']))
        assert grid['shape'] == [3333, 2633] and grid['EPSG'] == 4326
        names = ['geolocation/latitude', 'geolocation/longitude']
        names += [key + '/' + field for key in slots for field in ['vza', 'vaa']]
        for name in names:
            dataset = file[name]
            assert dataset.shape == (3333, 2633) and dataset.dtype == np.dtype('float64')
            assert dataset.compression == 'gzip' and dataset.shuffle and dataset.fletcher32
            assert dataset.attrs['units'] == ('degrees_north' if name.endswith('latitude') else
                                              'degrees_east' if name.endswith('longitude') else 'degree')
        points = {(y, x) for y in [0, 128, 1000, 3332] for x in [0, 256, 1300, 2632]}
        generator = np.random.default_rng(20261012)
        points |= set(zip(generator.integers(0, 3333, 32).tolist(),
                          generator.integers(0, 2633, 32).tolist()))
        gt = grid['GeoTransform']
        for y, x in sorted(points):
            latitude, longitude = file['geolocation/latitude'][y, x], file['geolocation/longitude'][y, x]
            assert latitude == gt[3] + x * gt[4] + y * gt[5]
            assert longitude == gt[0] + x * gt[1] + y * gt[2]
            for key, slot in slots.items():
                assert file[key].attrs['latitude_deg'] == 0.
                assert file[key].attrs['longitude_deg'] == slot
                assert json.loads(file[key].attrs['declaration_json']) == plan['declarations'][key]
                expected_vza, expected_vaa = independent_angles(latitude, longitude, 0., slot)
                maximum_zenith = max(maximum_zenith, abs(float(file[key + '/vza'][y, x]) - expected_vza))
                maximum_azimuth = max(maximum_azimuth, angle_error(file[key + '/vaa'][y, x], expected_vaa))
        assert maximum_zenith < 1e-10 and maximum_azimuth < 1e-10
    return {'coordinate_points': len(points), 'angle_pairs': len(points) * 3,
            'independent_formula': 'Analytic ENU with WGS84 semi-major/minor axes and fixed geocentric radius',
            'maximum_zenith_difference_deg': maximum_zenith,
            'maximum_circular_azimuth_difference_deg': maximum_azimuth,
            'declared_source_files': sources, 'grid': grid}


def audit_core():
    old, new = canonical_functions(BASELINE), canonical_functions(HERE / 'produce_msg_ls4t.py')
    required = ['planck', 'inverse', 'hotspot', 'retrieve', 'decode_lst', 'decode_lai', 'paths',
                'static_paths', 'grid_info', 'grid_check', 'sample_ancillary', 'attrs', 'data_attrs',
                'create_tif', 'commit_products', 'inventory']
    for name in required:
        assert old[name] == new[name], 'Unexpected baseline change: ' + name
    before = ast.parse(BASELINE.read_text(encoding='utf8'))
    after = ast.parse((HERE / 'produce_msg_ls4t.py').read_text(encoding='utf8'))
    old_scene = next(n for n in before.body if isinstance(n, ast.FunctionDef) and n.name == 'produce_scene')
    new_scene = next(n for n in after.body if isinstance(n, ast.FunctionDef) and n.name == 'produce_scene')
    # Geometry selection now precedes resume, while large angle arrays load
    # only for a new scene. Compare every temperature/I/O statement after it.
    def temperature_body(function):
        start = next(index for index, node in enumerate(function.body)
                     if isinstance(node, ast.For) and isinstance(node.target, ast.Name)
                     and node.target.id == 'path')
        return [ast.dump(node, include_attributes=False) for node in function.body[start:]]
    assert temperature_body(old_scene) == temperature_body(new_scene)
    old_month = next(n for n in before.body if isinstance(n, ast.FunctionDef) and n.name == 'monthly')
    new_month = deepcopy(next(n for n in after.body if isinstance(n, ast.FunctionDef) and n.name == 'monthly'))
    assert new_month.args.args[-1].arg == 'validated_records'
    new_month.args.args.pop()
    new_month.args.defaults.pop()
    old_condition = next(node.test for node in ast.walk(old_month) if isinstance(node, ast.If)
                         and 'source.attrs' in ast.unparse(node.test))
    class NormalizeMonthlyProvenance(ast.NodeTransformer):
        def visit_Expr(self, node):
            if isinstance(node.value, ast.Call) and ast.unparse(node.value.func) == 'lineage.check_month_sources':
                return None
            return self.generic_visit(node)
        def visit_If(self, node):
            if ast.unparse(node.test) == 'not lineage.monthly_source_identity(source, identity)':
                node.test = deepcopy(old_condition)
            return self.generic_visit(node)
    new_month = NormalizeMonthlyProvenance().visit(new_month)
    assert ast.dump(new_month, include_attributes=False) == ast.dump(old_month, include_attributes=False)
    assert producer.PROTOCOL['hotspot'] == .25
    assert producer.PROTOCOL['lambda'] == 1000. and producer.PROTOCOL['delta_radiance'] == 3.
    assert producer.PROTOCOL['first_window'] == producer.PROTOCOL['second_window'] == 5
    assert producer.PROTOCOL['minimum_valid_neighbors'] == 10
    assert producer.PROTOCOL['temperature_limits_K'] == [250., 350.]
    assert producer.PROTOCOL['minimum_LAI'] == .05
    return {'baseline': str(BASELINE), 'baseline_sha256': sha(BASELINE),
            'ast_identical_functions': required,
            'monthly_arithmetic_mask_flags_encoding_and_output_ast_identical_after_provenance_guard_normalization': True,
            'produce_scene_temperature_and_file_writing_body_ast_identical': True,
            'produce_scene_integration_change': 'Read lightweight per-view metadata before resume; calculate/load angles only for new scenes; recheck metadata consistency before any product writes.'}


def audit_positions(plan):
    records = []
    for stamp, modes in [('201708151200', {'e': 'static', 'i': 'static'}),
                          ('202012311200', {'e': 'static', 'i': 'dynamic'}),
                          ('202407151200', {'e': 'dynamic', 'i': 'dynamic'})]:
        record = geometry.geometry_metadata(stamp, plan)
        assert record['geometry_modes'] == modes
        json.dumps(record, allow_nan=False)
        for position in record['positions'].values():
            if position['mode'] == 'static':
                assert position['latitude_deg'] == 0. and position['fallback_reason']
            else:
                assert position['fallback_reason'] is None
                metadata = position['metadata']
                assert position['latitude_deg'] == float(metadata['MEAN_SSLAT'])
                assert position['longitude_deg'] == float(metadata['MEAN_SSLON'])
                # Dynamic calculation agrees with the independently derived formula.
                latitude = np.array([-20., 0., 35., 60.])
                longitude = np.array([0., 20., 45., 60.])
                vza, vaa = geometry.look_angles(latitude, longitude,
                    position['latitude_deg'], position['longitude_deg'])
                independent = independent_angles(latitude, longitude,
                    position['latitude_deg'], position['longitude_deg'])
                np.testing.assert_allclose(vza, independent[0], rtol=0, atol=1e-10)
                np.testing.assert_allclose((vaa - independent[1] + 180.) % 360. - 180., 0., rtol=0, atol=1e-10)
        records.append({'timestamp': stamp, 'modes': modes, 'positions': {
            view: {key: position[key] for key in ['latitude_deg', 'longitude_deg', 'fallback_reason']}
            for view, position in record['positions'].items()}})
    for stamp in ['202206011200', '202206301600', '202407151230', '202407150900']:
        try:
            geometry.geometry_metadata(stamp, plan)
        except geometry.GeometryUnavailable:
            pass
        else:
            raise AssertionError('Rejected acquisition accepted: ' + stamp)
    return {'real_sources': records, 'excluded_month_and_utc_boundaries_rejected': True}


def audit_guards(hashes):
    results = []
    with tempfile.TemporaryDirectory(prefix='independent_code_fixture_', dir=HERE) as temporary:
        folder = Path(temporary)
        valid = folder / 'pass.json'
        valid.write_text(json.dumps({'status': 'PASS', 'reviewed_files': hashes}), encoding='utf8')
        producer.assert_code_review(valid, HERE / 'msg_view_geometry.py', HERE / 'geometry_plan.json')
        reports = [folder / 'absent.json']
        failed = folder / 'fail.json'
        failed.write_text(json.dumps({'status': 'FAIL', 'reviewed_files': hashes}), encoding='utf8')
        reports.append(failed)
        for name in [name for name in REVIEW_FILES if name != 'merge_collection.py']:
            stale = dict(hashes, **{name: '0' * 64})
            path = folder / ('stale_' + name + '.json')
            path.write_text(json.dumps({'status': 'PASS', 'reviewed_files': stale}), encoding='utf8')
            reports.append(path)
        for index, report in enumerate(reports):
            output = folder / ('blocked_' + str(index))
            arguments = ['produce_msg_ls4t.py', '--output', str(output), '--code-review', str(report)]
            with patch.object(sys, 'argv', arguments), patch.object(producer, 'ProcessPoolExecutor',
                    side_effect=AssertionError('Worker pool must never start')):
                try:
                    producer.main()
                except (FileNotFoundError, RuntimeError):
                    pass
                else:
                    raise AssertionError('Unreviewed code passed main guard')
            assert not output.exists(), 'Output mutation before review refusal'
        results.append('Missing/FAIL/stale six runtime-file reviews rejected before output directory creation; migration-file gate tested separately')
        for inventory_only in [False, True]:
            output = folder / ('old_identity_' + str(inventory_only))
            output.mkdir()
            identity_file = output / 'production_identity.json'
            identity_file.write_text(json.dumps({'identity_hash': 'old_frozen_identity'}), encoding='utf8')
            manifests = [identity_file, output / 'inventory.json', output / 'missing_inputs.json', output / 'status.json']
            for path in manifests[1:]:
                path.write_text('existing manifest preserved', encoding='utf8')
            before = {path.name: path.read_bytes() for path in manifests}
            arguments = ['produce_msg_ls4t.py', '--output', str(output), '--code-review', str(valid)]
            if inventory_only:
                arguments += ['--inventory-only']
            with ExitStack() as stack:
                stack.enter_context(patch.object(sys, 'argv', arguments))
                stack.enter_context(patch.object(producer, 'grid_info', return_value={'fixture': True}))
                stack.enter_context(patch.object(producer, 'build_identity',
                    return_value=({'identity_hash': 'new_hybrid_identity'}, {})))
                for name in ['inventory', 'atomic_json', 'ProcessPoolExecutor']:
                    stack.enter_context(patch.object(producer, name,
                        side_effect=AssertionError('Identity mismatch must block ' + name)))
                try:
                    producer.main()
                except RuntimeError as error:
                    assert 'audited in-place migration' in str(error)
                else:
                    raise AssertionError('Existing identity was overwritten')
            assert before == {path.name: path.read_bytes() for path in manifests}
        results.append('Existing incompatible identity rejects normal and inventory-only runs before manifest writes or workers')
    return {'checks': results, 'fixture_scope': 'Private workspace directory only; original product roots never passed to main'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE / 'independent_code_review.json')
    args = parser.parse_args()
    hashes = {name: sha(HERE / name) for name in REVIEW_FILES}
    report = {'status': 'FAIL', 'reviewed_UTC': dt.datetime.now(dt.timezone.utc).isoformat(),
              'scope': 'Code and prebuilt auxiliary geometry review with small local fixtures; not real hybrid product acceptance or migration authorization.',
              'reviewed_files': hashes}
    try:
        plan = json.loads((HERE / 'geometry_plan.json').read_text(encoding='utf8'))
        report['core_review'] = audit_core()
        report['static_cache_review'] = audit_cache(plan, hashes)
        report['position_selection_review'] = audit_positions(plan)
        report['write_guard_review'] = audit_guards(hashes)
        fixtures = json.loads((HERE/'independent_lineage_fixture_review.json').read_text(encoding='utf8'))
        assert fixtures['status'] == 'PASS'
        assert fixtures['producer_sha256'] == hashes['produce_msg_ls4t.py']
        assert fixtures['lineage_sha256'] == hashes['collection_lineage.py']
        assert fixtures['merge_sha256'] == hashes['merge_collection.py']
        report['lineage_and_merge_fixture_review'] = fixtures
        frozen = {}
        for entry in plan['compatible_legacy_identities']:
            file = Path(entry['path'])
            assert sha(file) == entry['sha256']
            old = json.loads(file.read_text(encoding='utf8'))
            payload = {key: value for key, value in old.items() if key not in ['identity_hash', 'protocol']}
            assert producer.hash_object(payload) == old['identity_hash']
            assert producer.hash_object(old['protocol']) == old['protocol_hash']
            assert old['grid'] == report['static_cache_review']['grid']
            import collection_lineage as lineage
            assert all(old['protocol'][key] == producer.PROTOCOL[key] for key in lineage.NUMERIC_KEYS)
            frozen[old['identity_hash']] = {'identity_snapshot_sha256': entry['sha256'],
                                          'numeric_protocol_and_grid_equal': True}
        report['frozen_legacy_identity_review'] = frozen
        evidence = {}
        for name in ['verification.json', 'product_schema_qa.json', 'hybrid_geometry_qa.json']:
            file = HERE / name
            data = json.loads(file.read_text(encoding='utf8'))
            assert str(data['status']).lower() in ['pass', 'passed']
            if name != 'hybrid_geometry_qa.json':
                assert data['producer_sha256'] == hashes['produce_msg_ls4t.py']
            else:
                assert data['helper_sha256'] == hashes['msg_view_geometry.py']
                assert data['static_geometry_sha256'] == hashes['static_geometry.h5']
            evidence[name] = {'sha256': sha(file), 'status': data['status']}
        report['executor_small_test_evidence'] = evidence
        report['launcher_sha256'] = sha(HERE / 'run_msg_ls4t.ps1')
        report['launcher_review'] = 'Only explicit invocation; numerical verification then guarded producer; no launch during review.'
        assert hashes == {name: sha(HERE / name) for name in REVIEW_FILES}, 'Files changed during audit'
        report['limitations'] = ['Declared static slots are an authorized approximation, not measured ephemeris.',
                                'June 2022 projected/native IODC geolocation conflict remains excluded.',
                                'Authorized collection migration must use the reviewed seven files; this review itself does not execute real migration.',
                                'No production process or real temperature product was created or altered by this audit.']
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        args.output.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding='utf8')
        print(json.dumps(report, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
