"""Reuse committed legacy bytes only with equal inputs, physics and method."""
from pathlib import Path
import json

import h5py

NUMERIC_KEYS = ('first_window', 'second_window', 'hotspot', 'lambda', 'delta_radiance',
    'radiance_units', 'wavelength_m', 'residual_mode', 'minimum_valid_neighbors',
    'determinant_threshold', 'neighborhood_boundary', 'observation_mask', 'source_LST',
    'temperature_limits_K', 'minimum_LAI', 'output_mask', 'instant_encoding', 'monthly',
    'monthly_encoding', 'minimum_monthly_observations', 'low_support', 'solar_geometry',
    'auxiliary_sampling', 'grid')
MODEL_KEYS = ('satellite_geocentric_radius_m', 'ground_ellipsoid', 'ground_height_m',
              'target_pixel_reference', 'azimuth_convention', 'iodc_native_grid_longitude_deg')


def load_registry(plan, protocol, grid, sha, hash_object):
    registry = {}
    for entry in plan.get('compatible_legacy_identities', []):
        path = Path(entry['path'])
        if sha(path) != entry['sha256']:
            raise RuntimeError('Frozen legacy identity changed: '+str(path))
        old = json.loads(path.read_text(encoding='utf8'))
        payload = {key: value for key, value in old.items() if key not in ['identity_hash', 'protocol']}
        if hash_object(payload) != old['identity_hash'] or hash_object(old['protocol']) != old['protocol_hash']:
            raise RuntimeError('Legacy identity digest is invalid')
        if old['grid'] != grid or any(old['protocol'][key] != protocol[key] for key in NUMERIC_KEYS):
            raise RuntimeError('Legacy grid/numerical protocol is incompatible')
        # All original immutable sources and code must still match their identity.
        for group in ['static_sources', 'code_files']:
            for filename, expected in old[group].items():
                if Path(filename).stat().st_size != expected['bytes'] or sha(filename) != expected['sha256']:
                    raise RuntimeError('Legacy frozen dependency changed: '+filename)
        registry[old['identity_hash']] = old
    return registry


def assert_file_identity(source, record, identity):
    computed = record['identity_hash']
    if source.attrs.get('identity_hash') != computed or int(source.attrs.get('complete', 0)) != 1:
        raise RuntimeError('Product identity/completion mismatch')
    if source.attrs.get('source_signature') != record['source_signature']:
        raise RuntimeError('HDF/marker source signature mismatch')
    old = identity.get('compatible_legacy_identities', {}).get(computed)
    expected = identity if computed == identity['identity_hash'] else old
    if expected is None:
        raise RuntimeError('Unapproved product identity')
    for key in ['code_sha256', 'protocol_hash', 'implementation_sha256',
                'static_source_hash', 'geometry_plan_sha256']:
        if source.attrs.get(key) != expected[key]:
            raise RuntimeError('Product provenance mismatch: '+key)


def scene_equivalent(source, record, context, hash_object):
    """Return false for changed inputs/selected geometry, never relabel bytes."""
    inputs = json.loads(source.attrs['inputs_json'])
    geometry = json.loads(source.attrs['geometry_json'])
    if geometry != record['geometry'] or source.attrs['source_signature'] != record['source_signature']:
        raise RuntimeError('Legacy HDF/marker source provenance mismatch')
    if hash_object({'inputs': inputs, 'geometry': geometry}) != record['source_signature']:
        raise RuntimeError('Legacy source signature is invalid')
    selected = context['geometry']
    if inputs != context['inputs'] or geometry['timestamp_UTC'] != selected['timestamp_UTC']:
        return False
    if any(geometry.get(key) != selected.get(key) for key in MODEL_KEYS):
        return False
    policy = geometry.get('position_policy')
    expected_mode = {'MEAN_SS_only_no_NOMINAL_fallback': 'dynamic',
                     'declared_geostationary_slots_nominal_latitude_zero': 'static'}.get(policy)
    if expected_mode is None:
        return False
    for view in ['e', 'i']:
        old, new = geometry['positions'][view], selected['positions'][view]
        if new['mode'] != expected_mode:
            return False
        if any(old[key] != new[key] for key in ['latitude_deg', 'longitude_deg']):
            return False
    return True


def check_month_sources(files, sources, records, identity):
    """Bind legacy monthly inputs to this run's validated scene records."""
    bindings = {str(Path(record['hdf5'])): record for record in (records or [])}
    for path in files:
        key = str(Path(path))
        with h5py.File(path, 'r') as source:
            if source.attrs.get('identity_hash') == identity['identity_hash']:
                if int(source.attrs.get('complete', 0)) != 1:
                    raise RuntimeError('Incomplete monthly source')
                continue
            if source.attrs.get('identity_hash') not in identity.get('compatible_legacy_identities', {}):
                raise RuntimeError('Monthly source identity is not approved: '+key)
            record = bindings.get(key)
            if (record is None or record.get('validated_collection_identity') != identity['identity_hash']
                    or record['timestamp'] != Path(path).stem[-12:]
                    or record['files'][key] != sources[key]):
                raise RuntimeError('Legacy monthly source lacks current-run validation: '+key)
            assert_file_identity(source, record, identity)


def monthly_source_identity(source, identity):
    # Called only after check_month_sources bound and hashed all input files.
    return (int(source.attrs.get('complete', 0)) == 1 and
            source.attrs.get('identity_hash') in {identity['identity_hash'],
                                                *identity.get('compatible_legacy_identities', {})})
