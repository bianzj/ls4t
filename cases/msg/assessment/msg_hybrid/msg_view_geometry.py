"""MSG and IODC: select each view's dynamic orbit, then declared static slot.

Missing orbit metadata may use a static slot. Conflicting acquisition/grid
metadata and unreadable source files are never disguised as missing orbit.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re

import h5py
import numpy as np

SATELLITE_GEOCENTRIC_RADIUS_M = 42164000.
WGS84_SEMI_MAJOR_M = 6378137.
WGS84_ECCENTRICITY_SQUARED = 6.6943799901413165e-3
POSITION_POLICY = 'per_view_dynamic_MEAN_SS_then_declared_static_slot'
_STATIC_ANGLES = {}


class GeometryUnavailable(ValueError):
    """Input geometry is conflicting or outside the configured epochs."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _decode(value):
    if isinstance(value, bytes):
        return value.decode('utf8').strip()
    if isinstance(value, np.ndarray):
        return [_decode(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    return value


def native_path(stamp, view, input_root):
    channel, disk = ('MSG', 'MSG-Disk') if view == 'e' else ('MSG-IODC', 'IODC-Disk')
    return (Path(input_root)/'PRODUCTS'/channel/'MLST/HDF5'/stamp[:4]/stamp[4:6]/stamp[6:8]
            /f'HDF5_LSASAF_{channel}_LST_{disk}_{stamp}')


def _read_metadata(path, stamp, expected_longitude, legacy_placeholder):
    if not path.is_file():
        return {}, {'path': str(path), 'exists': False}
    stat = path.stat()
    # I/O errors propagate as source failures, never as static fallbacks.
    with h5py.File(path, 'r') as source:
        keys = ['IMAGE_ACQUISITION_TIME', 'SATELLITE', 'PROJECTION_NAME',
                'MEAN_SSLAT', 'MEAN_SSLON', 'NOMINAL_LAT', 'NOMINAL_LONG']
        metadata = {key: _decode(source.attrs[key]) for key in keys if key in source.attrs}
    if str(metadata.get('IMAGE_ACQUISITION_TIME', ''))[:12] != stamp:
        raise GeometryUnavailable('Acquisition metadata/filename mismatch: '+str(path))
    projection = str(metadata.get('PROJECTION_NAME', '')).strip()
    projection_note = None
    if projection:
        if projection == legacy_placeholder:
            # This exact legacy generic template is not an IODC slot claim.
            # Epochs come from the existing native/projected-value grid audit.
            projection_note = 'known legacy generic template; grid uses audited projection epoch'
        else:
            match = re.fullmatch(r'GEOS\(\s*([+-]?\d+(?:\.\d+)?)\s*\)', projection)
            if match is None or abs(float(match.group(1))-expected_longitude) > .05:
                raise GeometryUnavailable('Native projection conflicts with the input grid epoch: '+str(path))
    return metadata, {'path': str(path), 'exists': True, 'bytes': stat.st_size,
                      'mtime_ns': stat.st_mtime_ns, 'projection_note': projection_note}


def _select_position(stamp, view, epoch, plan):
    expected = 0. if view == 'e' else float(epoch['native_grid_longitude_deg'])
    path = native_path(stamp, view, plan['input_root'])
    metadata, native = _read_metadata(path, stamp, expected, plan['legacy_native_projection_placeholder'])
    reason = None
    if not native['exists']:
        reason = 'native_metadata_source_absent'
    else:
        try:
            latitude = float(metadata['MEAN_SSLAT'])
            longitude = float(metadata['MEAN_SSLON'])
        except (KeyError, TypeError, ValueError):
            reason = 'dynamic_position_fields_missing_or_not_numeric'
        else:
            if not np.isfinite([latitude, longitude]).all():
                reason = 'dynamic_position_not_finite'
            elif latitude == 0. and longitude == 0.:
                reason = 'observed_zero_zero_dynamic_placeholder'
            else:
                if abs(latitude) > 20 or abs(longitude) > 180:
                    raise GeometryUnavailable('Dynamic orbit outside supported GEO bounds: '+str(path))
                if view == 'e':
                    lower, upper = plan['euro_position_longitude_bounds_deg']
                    consistent = lower <= longitude <= upper
                else:
                    consistent = abs(longitude-expected) <= plan['iodc_position_longitude_tolerance_deg']
                if not consistent:
                    raise GeometryUnavailable('Dynamic orbit conflicts with the input grid epoch: '+str(path))
                return {'mode': 'dynamic', 'latitude_deg': latitude, 'longitude_deg': longitude,
                        'native_source': native, 'metadata': metadata, 'fallback_reason': None}
    key = 'euro' if view == 'e' else epoch['declaration_key']
    declaration = plan['declarations'][key]
    return {'mode': 'static', 'latitude_deg': 0.,
            'longitude_deg': float(declaration['orbital_slot_longitude_deg']),
            'position_value_meaning': 'declared static slot; nominal latitude zero is not missing data',
            'declaration': declaration, 'static_geometry_group': key,
            'native_source': native, 'metadata': metadata,
            'fallback_reason': reason}


def _record_metadata(metadata):
    # JSON signatures prohibit NaN/Infinity; preserve their explicit meaning.
    if isinstance(metadata, dict):
        return {key: _record_metadata(value) for key, value in metadata.items()}
    if isinstance(metadata, list):
        return [_record_metadata(value) for value in metadata]
    if isinstance(metadata, float) and not np.isfinite(metadata):
        return {'nonfinite_value': str(metadata)}
    return metadata


def geometry_metadata(stamp, plan):
    if isinstance(plan, (str, Path)):
        plan = json.loads(Path(plan).read_text(encoding='utf8'))
    if plan['position_policy'] != POSITION_POLICY or plan['geometry_helper_sha256'] != sha(__file__):
        raise GeometryUnavailable('Geometry policy/helper differs from configured plan')
    try:
        parsed = dt.datetime.strptime(stamp, '%Y%m%d%H%M')
    except ValueError as error:
        raise GeometryUnavailable('Invalid UTC acquisition timestamp: '+stamp) from error
    if parsed.strftime('%Y%m%d%H%M') != stamp or parsed.minute != 0 or not 10 <= parsed.hour <= 16:
        raise GeometryUnavailable('Acquisition must be an exact UTC hour 10-16: '+stamp)
    if stamp[:6] in plan['excluded_input_geolocation_months']:
        raise GeometryUnavailable('202206 IODC native/projected input geolocation conflict; static fallback cannot repair input mapping')
    epoch = next((item for item in plan['iodc_projection_epochs']
                  if item['first_stamp'] <= stamp <= item['last_stamp']), None)
    if epoch is None:
        raise GeometryUnavailable('Acquisition outside configured projection epochs: '+stamp)
    positions = {view: _select_position(stamp, view, epoch, plan) for view in ['e', 'i']}
    modes = {view: position['mode'] for view, position in positions.items()}
    return _record_metadata({'timestamp_UTC': stamp, 'position_policy': POSITION_POLICY,
            'geometry_modes': modes, 'positions': positions,
            'geometry_accuracy': 'per-view measured orbit where available; declared-slot approximation otherwise',
            'iodc_native_grid_longitude_deg': epoch['native_grid_longitude_deg'],
            'satellite_geocentric_radius_m': SATELLITE_GEOCENTRIC_RADIUS_M,
            'ground_ellipsoid': 'WGS84', 'ground_height_m': 0.,
            'target_pixel_reference': 'legacy_pixel_corner_coordinates_supplied_by_producer',
            'azimuth_convention': 'ground_to_satellite_north_0_east_90_0_to_360',
            'static_geometry_file': plan['static_geometry_file'],
            'helper_sha256': sha(__file__)})


def look_angles(lat, lon, satellite_lat, satellite_lon, radius=SATELLITE_GEOCENTRIC_RADIUS_M):
    lat = np.asarray(lat, dtype=np.float64)
    lon = np.asarray(lon, dtype=np.float64)
    if lat.shape != lon.shape:
        raise ValueError('Latitude and longitude shapes differ')
    phi, lam = np.radians(lat), np.radians(lon)
    normal = WGS84_SEMI_MAJOR_M / np.sqrt(1-WGS84_ECCENTRICITY_SQUARED*np.sin(phi)**2)
    x = normal*np.cos(phi)*np.cos(lam)
    y = normal*np.cos(phi)*np.sin(lam)
    z = normal*(1-WGS84_ECCENTRICITY_SQUARED)*np.sin(phi)
    sphi, slam = np.radians(satellite_lat), np.radians(satellite_lon)
    dx = radius*np.cos(sphi)*np.cos(slam)-x
    dy = radius*np.cos(sphi)*np.sin(slam)-y
    dz = radius*np.sin(sphi)-z
    east = -np.sin(lam)*dx+np.cos(lam)*dy
    north = -np.sin(phi)*np.cos(lam)*dx-np.sin(phi)*np.sin(lam)*dy+np.cos(phi)*dz
    up = np.cos(phi)*np.cos(lam)*dx+np.cos(phi)*np.sin(lam)*dy+np.sin(phi)*dz
    zenith = np.degrees(np.arctan2(np.hypot(east, north), up))
    azimuth = np.degrees(np.arctan2(east, north)) % 360
    valid = np.isfinite(lat) & np.isfinite(lon) & (np.abs(lat) <= 90) & (np.abs(lon) <= 180)
    return np.where(valid, zenith, np.nan), np.where(valid, azimuth, np.nan)


def view_geometry(stamp, lat, lon, base_static, plan):
    if isinstance(plan, (str, Path)):
        plan = json.loads(Path(plan).read_text(encoding='utf8'))
    record = geometry_metadata(stamp, plan)
    fields = {}
    for view, position in record['positions'].items():
        if position['mode'] == 'static':
            # Arrays loaded once per worker/slot; no per-acquisition computation.
            key = (str(Path(plan['static_geometry_file']).resolve()), position['static_geometry_group'])
            if key not in _STATIC_ANGLES:
                with h5py.File(key[0], 'r') as source:
                    if int(source.attrs.get('complete', 0)) != 1 or source.attrs['helper_sha256'] != sha(__file__):
                        raise RuntimeError('Static geometry is incomplete or uses another helper')
                    group = source[key[1]]
                    if group.attrs['latitude_deg'] != position['latitude_deg'] or group.attrs['longitude_deg'] != position['longitude_deg']:
                        raise RuntimeError('Static geometry orbital slot mismatch')
                    # A cached slot is valid only for the supplied MSG grid.
                    np.testing.assert_array_equal(source['geolocation/latitude'][:], lat)
                    np.testing.assert_array_equal(source['geolocation/longitude'][:], lon)
                    pair = (group['vza'][:], group['vaa'][:])
                    for array in pair:
                        array.setflags(write=False)
                    _STATIC_ANGLES[key] = (lat, lon, pair)
            cached_lat, cached_lon, pair = _STATIC_ANGLES[key]
            if cached_lat is not lat or cached_lon is not lon:
                np.testing.assert_array_equal(cached_lat, lat)
                np.testing.assert_array_equal(cached_lon, lon)
            fields['vza_'+view], fields['vaa_'+view] = pair
        else:
            fields['vza_'+view], fields['vaa_'+view] = look_angles(
                lat, lon, position['latitude_deg'], position['longitude_deg'])
    return fields, record
