"""Scene-specific view angles, with explicit audited projection and orbit gates.

Does not modify LST, use NOMINAL_* as an ephemeris fallback, or extrapolate
positions for acquisitions whose MEAN_SS* metadata are missing/conflicting.
"""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import h5py
import numpy as np

SATELLITE_GEOCENTRIC_RADIUS_M=42164000.
WGS84_SEMI_MAJOR_M=6378137.
WGS84_ECCENTRICITY_SQUARED=6.6943799901413165e-3


class GeometryUnavailable(ValueError):
    """This acquisition is deferred rather than assigned an invented geometry."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def native_path(stamp,view):
    channel='MSG' if view=='e' else 'MSG-IODC'
    disk='MSG-Disk' if view=='e' else 'IODC-Disk'
    return Path('E:/PRODUCTS')/channel/'MLST/HDF5'/stamp[:4]/stamp[4:6]/stamp[6:8]/f'HDF5_LSASAF_{channel}_LST_{disk}_{stamp}'


def _decode(value):
    if isinstance(value,bytes):return value.decode('utf-8')
    if isinstance(value,np.ndarray):return [_decode(x) for x in value.tolist()]
    if isinstance(value,np.generic):return value.item()
    return value


@lru_cache(maxsize=256)
def read_position(stamp,view):
    path=native_path(stamp,view)
    if not path.is_file():raise GeometryUnavailable('Native metadata source absent: '+str(path))
    with h5py.File(path,'r') as source:
        keys=['IMAGE_ACQUISITION_TIME','SATELLITE','PROJECTION_NAME','MEAN_SSLAT','MEAN_SSLON','NOMINAL_LAT','NOMINAL_LONG']
        meta={key:_decode(source.attrs[key]) for key in keys if key in source.attrs}
    if str(meta.get('IMAGE_ACQUISITION_TIME',''))[:12]!=stamp:
        raise GeometryUnavailable('Acquisition metadata/filename mismatch: '+str(path))
    try:
        latitude=float(meta['MEAN_SSLAT']);longitude=float(meta['MEAN_SSLON'])
    except (KeyError,TypeError,ValueError) as error:
        raise GeometryUnavailable('MEAN_SS position is absent: '+str(path)) from error
    if not np.isfinite([latitude,longitude]).all() or abs(latitude)>20 or abs(longitude)>180:
        raise GeometryUnavailable('MEAN_SS position is outside supported GEO bounds: '+str(path))
    if latitude==0 and longitude==0:
        raise GeometryUnavailable('MEAN_SS position is the observed zero/zero placeholder: '+str(path))
    stat=path.stat()
    return {'latitude_deg':latitude,'longitude_deg':longitude,'metadata':meta,'path':str(path),'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}


def look_angles(lat,lon,satellite_lat,satellite_lon,radius=SATELLITE_GEOCENTRIC_RADIUS_M):
    """WGS84 geodetic ground -> ECEF -> local ENU; azimuth N=0,E=90.

    Satellite latitude is the geocentric sub-satellite direction supplied by
    the source. Ground height is zero. The orbit radius is explicit, not fitted.
    Azimuth looks from the ground towards the satellite; output range 0..360.
    """
    lat=np.asarray(lat,dtype=np.float64);lon=np.asarray(lon,dtype=np.float64)
    if lat.shape!=lon.shape:raise ValueError('Latitude and longitude shapes differ')
    phi=np.radians(lat);lam=np.radians(lon)
    normal=WGS84_SEMI_MAJOR_M/np.sqrt(1-WGS84_ECCENTRICITY_SQUARED*np.sin(phi)**2)
    x=normal*np.cos(phi)*np.cos(lam)
    y=normal*np.cos(phi)*np.sin(lam)
    z=normal*(1-WGS84_ECCENTRICITY_SQUARED)*np.sin(phi)
    sphi=np.radians(satellite_lat);slam=np.radians(satellite_lon)
    dx=radius*np.cos(sphi)*np.cos(slam)-x
    dy=radius*np.cos(sphi)*np.sin(slam)-y
    dz=radius*np.sin(sphi)-z
    east=-np.sin(lam)*dx+np.cos(lam)*dy
    north=-np.sin(phi)*np.cos(lam)*dx-np.sin(phi)*np.sin(lam)*dy+np.cos(phi)*dz
    up=np.cos(phi)*np.cos(lam)*dx+np.cos(phi)*np.sin(lam)*dy+np.sin(phi)*dz
    zenith=np.degrees(np.arctan2(np.hypot(east,north),up))
    azimuth=np.degrees(np.arctan2(east,north))%360
    valid=np.isfinite(lat)&np.isfinite(lon)&(np.abs(lat)<=90)&(np.abs(lon)<=180)
    return np.where(valid,zenith,np.nan),np.where(valid,azimuth,np.nan)


def _validate_plan(plan):
    if isinstance(plan,(str,Path)):
        plan=json.loads(Path(plan).read_text(encoding='utf-8'))
    if plan.get('status')!='approved_for_eligible_metadata':
        raise GeometryUnavailable('An audited eligible-metadata geometry plan is required')
    if plan.get('geometry_helper_sha256')!=sha(__file__):
        raise GeometryUnavailable('Geometry helper differs from the audited plan')
    if plan.get('position_policy')!='MEAN_SS_only_no_NOMINAL_fallback':
        raise GeometryUnavailable('Unsupported position policy')
    return plan


def geometry_metadata(stamp,plan):
    """Cheap per-scene eligibility check; does not allocate full-grid angles."""
    plan=_validate_plan(plan)
    epoch=next((entry for entry in plan['iodc_projection_epochs'] if entry['first_stamp']<=stamp<=entry['last_stamp']),None)
    if epoch is None:raise GeometryUnavailable('Acquisition outside audited projection epochs: '+stamp)
    positions={view:read_position(stamp,view) for view in ['e','i']}
    expected=float(epoch['native_grid_longitude_deg'])
    if abs(positions['i']['longitude_deg']-expected)>float(plan['iodc_position_longitude_tolerance_deg']):
        raise GeometryUnavailable(f'IODC source position {positions["i"]["longitude_deg"]} conflicts with observed native grid {expected}: {stamp}')
    lower,upper=plan['euro_position_longitude_bounds_deg']
    if not lower<=positions['e']['longitude_deg']<=upper:
        raise GeometryUnavailable('MSG Europe source position outside documented full-disc/backup bounds: '+stamp)
    return {'timestamp_UTC':stamp,'position_policy':plan['position_policy'],'positions':positions,'iodc_native_grid_longitude_deg':expected,'satellite_geocentric_radius_m':SATELLITE_GEOCENTRIC_RADIUS_M,'ground_ellipsoid':'WGS84','ground_height_m':0.,'target_pixel_reference':plan['target_pixel_reference'],'azimuth_convention':'ground_to_satellite_north_0_east_90_0_to_360','helper_sha256':sha(__file__)}


def view_geometry(stamp,lat,lon,base_static,plan):
    """Producer interface; retain original pixel convention supplied by caller.

    base_static is accepted for interface compatibility; its old view-angle
    fields are intentionally excluded from the returned scene-specific angles.
    """
    meta=geometry_metadata(stamp,plan)
    fields={}
    for view in ['e','i']:
        position=meta['positions'][view]
        zenith,azimuth=look_angles(lat,lon,position['latitude_deg'],position['longitude_deg'])
        fields['vza_'+view]=zenith
        fields['vaa_'+view]=azimuth
    return fields,meta
