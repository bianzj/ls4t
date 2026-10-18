"""Relative viewing geometry from declared geostationary orbital slots.

Nominal latitude is explicitly zero; this is not a missing MEAN_SS value.
Existing June 2022 IODC input geolocation conflicts remain excluded.
"""
from pathlib import Path
import hashlib
import json
import numpy as np

SATELLITE_GEOCENTRIC_RADIUS_M = 42164000.
WGS84_SEMI_MAJOR_M = 6378137.
WGS84_ECCENTRICITY_SQUARED = 6.6943799901413165e-3
POSITION_POLICY = 'declared_geostationary_slots_nominal_latitude_zero'
_ANGLES = {}


class GeometryUnavailable(ValueError):
    pass


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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


def geometry_metadata(stamp, plan):
    if isinstance(plan, (str, Path)):
        plan = json.loads(Path(plan).read_text(encoding='utf-8'))
    if plan['status'] != 'approved_declared_slots' or plan['position_policy'] != POSITION_POLICY:
        raise GeometryUnavailable('Incorrect declared-position plan')
    if plan['geometry_helper_sha256'] != sha(__file__):
        raise GeometryUnavailable('Declared-position helper differs from frozen plan')
    if stamp[:6] in plan['excluded_input_geolocation_months']:
        raise GeometryUnavailable('June 2022 native IODC declares 41.5E but existing projected LST uses 45.5E; input geolocation conflict, not missing orbit metadata')
    epoch = next((e for e in plan['iodc_projection_epochs'] if e['first_stamp'] <= stamp <= e['last_stamp']), None)
    if epoch is None:
        raise GeometryUnavailable('Acquisition outside declared projection epochs: '+stamp)
    declarations = {'e': plan['declarations']['euro'], 'i': plan['declarations'][epoch['declaration_key']]}
    positions = {}
    for view, declaration in declarations.items():
        positions[view] = dict(declaration, latitude_deg=0., longitude_deg=declaration['orbital_slot_longitude_deg'],
                               position_value_meaning='declared orbital slot; nominal latitude zero; not a missing-value placeholder')
    return {'timestamp_UTC': stamp, 'position_policy': POSITION_POLICY, 'geometry_accuracy': 'relative nominal-position approximation authorized by user',
            'positions': positions, 'iodc_native_grid_longitude_deg': epoch['native_grid_longitude_deg'],
            'satellite_geocentric_radius_m': SATELLITE_GEOCENTRIC_RADIUS_M, 'ground_ellipsoid': 'WGS84', 'ground_height_m': 0.,
            'target_pixel_reference': 'legacy_pixel_corner_coordinates_supplied_by_producer',
            'azimuth_convention': 'ground_to_satellite_north_0_east_90_0_to_360', 'helper_sha256': sha(__file__)}


def view_geometry(stamp, lat, lon, base_static, plan):
    record = geometry_metadata(stamp, plan)
    key = (lat.shape, float(lat.flat[0]), float(lon.flat[0]), float(lat.flat[-1]), float(lon.flat[-1]), record['iodc_native_grid_longitude_deg'])
    if key not in _ANGLES:
        fields = {}
        for view in ['e', 'i']:
            p = record['positions'][view]
            fields['vza_'+view], fields['vaa_'+view] = look_angles(lat, lon, p['latitude_deg'], p['longitude_deg'])
        _ANGLES[key] = fields
    return _ANGLES[key], record
