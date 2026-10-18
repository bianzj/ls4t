"""Resumable LS4T temperatures on the existing MSG WGS84 grid and UTC scenes.

The parent process owns manifests/status; spawned workers own disjoint scenes.
Geometry must be supplied by the audited timestamp-aware geometry provider.
"""
from __future__ import annotations

import os
# Set before importing NumPy/SciPy/GDAL, including in Windows spawned children.
for _thread_var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                    'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS'):
    os.environ[_thread_var] = '1'
os.environ['GDAL_NUM_THREADS'] = '1'

import argparse
import calendar
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
import datetime as dt
import hashlib
import importlib.util
import json
import multiprocessing as mp
from pathlib import Path
import sys
import time
import traceback
import uuid

import cv2
import h5py
import numpy as np
from osgeo import gdal, osr
import pandas as pd
import pvlib
from scipy.ndimage import uniform_filter

gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = Path('E:/PRODUCTS/LSCT/MSG_LS4T_H025_5X5_V1')
LEGACY_PRODUCER = Path('C:/work/ls4t-msg/cases/official/implementation/produce_msg_5x5.py')
LEGACY_CORE = Path('C:/work/ls4t-msg/cases/official/implementation/msg_lsct3.2-iter.py')
LEGACY_CORE_SHA = '763de469c6023b2b830061658d9130fcc851b7f7e9397903c27ac2fa159df9c3'
C1 = 2 * 6.62607015e-34 * 299792458**2
C2 = 6.62607015e-34 * 299792458 / 1.380649e-23
WL = 10.5e-6
BANDS = ['background_soil', 'canopy', 'sunlit_soil', 'shaded_soil']
BAND_DESCRIPTIONS = ['ts', 'tv', 'tss', 'tsh']
EXPECTED_SHAPE = (3333, 2633)
PROTOCOL = {
    'version': 'MSG_LS4T_H025_5X5_V1',
    'first_window': 5, 'second_window': 5, 'hotspot': .25, 'lambda': 1000.,
    'delta_radiance': 3., 'radiance_units': 'W m-2 sr-1 um-1',
    'wavelength_m': WL, 'residual_mode': 'center_constant_sunlit_over_entire_5x5',
    'minimum_valid_neighbors': 10, 'determinant_threshold': 1e-8,
    'neighborhood_boundary': 'nearest with 2-row halos between processing tiles',
    'observation_mask': 'common finite dual-view radiances and all six weights; daylight; valid land/emissivity/angles',
    'source_LST': 'signed int16 Celsius*100; uint16 storage reinterpreted int16; zero/-8000/declared NoData excluded',
    'temperature_limits_K': [250., 350.], 'minimum_LAI': .05,
    'output_mask': 'all four components finite and within limits; no observation-reference-dependent rejection',
    'instant_encoding': 'uint16 Kelvin*100 rounded; 0=NoData',
    'monthly': 'arithmetic mean of encoded instantaneous values on common four-band support, each UTC hour separately',
    'monthly_encoding': 'float32 Kelvin*100; NaN=NoData; scale_factor=0.01',
    'minimum_monthly_observations': 1, 'low_support': '1-2 observations flagged; no gap filling',
    'solar_geometry': 'legacy pixel-corner coordinates; 10x coarse nearest pvlib zenith/azimuth; altitude 0 m',
    'view_geometry': 'audited timestamp-aware provider; unresolved metadata deferred, never guessed',
    'auxiliary_sampling': 'land and soil emissivity sampled separately using their declared CRS/grid; legacy cell truncation',
    'grid': 'existing MSG 3333 rows x 2633 columns, EPSG:4326',
    'ownership': 'derived LS4T component temperatures; source MSG/MSG-IODC LST and MSG LAI attribution retained',
    'limitations': ['Projected zero/NoData ambiguity excludes unrecoverable 0 Celsius observations.',
                   'Land-cover Clarke 1866 datum has no specified transformation; auxiliary alignment follows declared CRS.',
                   'Monthly values describe available clear-sky samples, not all-weather averages.'],
}


def json_text(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def hash_object(value):
    return hashlib.sha256(json_text(value).encode('utf8')).hexdigest()


PROTOCOL_HASH = hash_object(PROTOCOL)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.partial')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf8')
    os.replace(temporary, path)


def append_json(path, value):
    with Path(path).open('a', encoding='utf8') as stream:
        stream.write(json_text(value) + '\n')
        stream.flush()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def planck(t):
    with np.errstate(all='ignore'):
        return C1 / (WL**5 * np.expm1(C2 / (WL * np.asarray(t)))) * 1e-6


def inverse(r):
    with np.errstate(all='ignore'):
        return np.where(r > 0, C2 / (WL * np.log1p(C1 * 1e-6 / (WL**5 * r))), np.nan)


def hotspot(lai, vza, sza, vsa):
    with np.errstate(all='ignore'):
        v, s, a = np.radians(vza), np.radians(sza), np.radians(vsa)
        kv, ks = .5 / np.cos(v), .5 / np.cos(s)
        distance = np.sqrt(np.maximum(np.tan(v)**2 + np.tan(s)**2 - 2 * np.tan(v) * np.tan(s) * np.cos(a), 0))
        alpha = distance / (PROTOCOL['hotspot'] * (kv + ks) / 2)
        factor = np.where(alpha < 1e-5, 1., -np.expm1(-alpha) / alpha)
        return np.exp(-(kv + ks - np.sqrt(kv * ks) * factor) * lai), np.exp(-kv * lai)


def retrieve(d):
    """Legacy scalar-center-equivalent two 5x5 stages and center joint solve."""
    lai, sza = d['lai'], d['sza']
    with np.errstate(all='ignore'):
        we, be = hotspot(lai, d['vza_e'], sza, (d['saa'] - d['vaa_e'] + 180) % 360 - 180)
        wi, bi = hotspot(lai, d['vza_i'], sza, (d['saa'] - d['vaa_i'] + 180) % 360 - 180)
        w = np.stack([d['emis_s'] * we, d['emis_s'] * (be - we), d['emis_v'] * (1 - be),
                      d['emis_s'] * wi, d['emis_s'] * (bi - wi), d['emis_v'] * (1 - bi)], axis=-1)
        re = planck(d['lst_e']) * w[..., :3].sum(-1)
        ri = planck(d['lst_i']) * w[..., 3:].sum(-1)
    good = np.isfinite(re) & np.isfinite(ri) & np.isfinite(w).all(-1)
    good &= (sza >= 0) & (sza < 90) & (lai >= 0) & (lai <= 10)
    for key in ['vza_e', 'vza_i']:
        good &= (d[key] >= 0) & (d[key] < 90)
    for key in ['emis_s', 'emis_v']:
        good &= (d[key] > 0) & (d[key] <= 1)
    if 'land' in d:
        good &= (d['land'] > 0) & (d['land'] <= 17)

    def total(a):
        return uniform_filter(np.where(good, a, 0.).astype('float64'), size=5, mode='nearest') * 25

    n = np.rint(total(np.ones_like(re))).astype('uint8')

    def solve(aa, ab, bb, u, v):
        determinant = aa * bb - ab * ab
        with np.errstate(all='ignore'):
            x = (u * bb - v * ab) / determinant
            y = (v * aa - u * ab) / determinant
        valid = good & (n >= 10) & (np.abs(determinant) >= 1e-8) & (x >= 0) & (y >= 0)
        return np.where(valid, x, np.nan), np.where(valid, y, np.nan)

    a, b, c, e, f, g = [w[..., i] for i in range(6)]
    sun, _ = solve(total(a*a + e*e), total(a*(b+c) + e*(f+g)), total((b+c)**2 + (f+g)**2),
                   total(a*re + e*ri), total((b+c)*re + (f+g)*ri))
    shade, veg = solve(total(b*b + f*f), total(b*c + f*g), total(c*c + g*g),
                       total(b*re + f*ri) - sun*total(b*a + f*e),
                       total(c*re + g*ri) - sun*total(c*a + g*e))
    rre, rri = re - a*sun, ri - e*sun
    delta = PROTOCOL['delta_radiance']
    p, q = b+c, f+g
    vc = (p*(rre-b*delta) + q*(rri-f*delta)) / (p*p + q*q + 1e-9)
    sc = vc + delta
    vd = (p*(rre+b*delta) + q*(rri+f*delta)) / (p*p + q*q + 1e-9)
    sd = vd - delta
    ec = (rre-b*sc-c*vc)**2 + (rri-f*sc-g*vc)**2
    ed = (rre-b*sd-c*vd)**2 + (rri-f*sd-g*vd)**2
    bound = np.abs(shade-veg) > delta
    shade = np.minimum(np.where(bound, np.where(ec <= ed, sc, sd), shade), sun)
    veg = np.where(bound, np.where(ec <= ed, vc, vd), veg)
    prior = np.stack([sun, shade, veg], axis=-1)
    ok = good & np.isfinite(prior).all(-1) & (lai >= .05)
    final = np.full_like(prior, np.nan)
    A = w[ok].reshape(-1, 2, 3)
    radiance = np.stack([re[ok], ri[ok]], -1)
    lhs = np.einsum('nki,nkj->nij', A, A) + PROTOCOL['lambda'] * np.eye(3)
    rhs = np.einsum('nki,nk->ni', A, radiance) + PROTOCOL['lambda'] * prior[ok]
    final[ok] = np.linalg.solve(lhs, rhs[..., None])[..., 0]
    final[..., 1] = np.minimum(final[..., 1], final[..., 0])
    with np.errstate(all='ignore'):
        gap = np.exp(-.5 * lai / np.cos(np.radians(sza)))
    soil = final[..., 0] * gap + final[..., 1] * (1-gap)
    temp = inverse(np.stack([soil, final[..., 2], final[..., 0], final[..., 1]]))
    valid = np.isfinite(temp).all(0) & (temp >= 250).all(0) & (temp <= 350).all(0) & ok
    temp[:, ~valid] = np.nan
    qa = (~good).astype('uint8') | ((n < 10).astype('uint8') << 1) | ((lai < .05).astype('uint8') << 2)
    qa |= ((~valid & good & (n >= 10) & (lai >= .05)).astype('uint8') << 3)
    qa |= bound.astype('uint8') << 4
    return temp, n, qa


def decode_lst(raw, nodata=None):
    raw = np.asarray(raw)
    signed = raw.view('int16') if raw.dtype == np.uint16 else raw
    result = signed.astype('float64') / 100. + 273.15
    invalid = (signed == 0) | (signed == -8000) | (result < 150) | (result > 400)
    if nodata is not None:
        invalid |= (raw == nodata) | (signed == nodata)
    result[invalid] = np.nan
    return result


def decode_lai(raw, nodata=None):
    result = np.asarray(raw).astype('float64') / 1000.
    invalid = (result < 0) | (result > 10)
    if nodata is not None:
        invalid |= np.asarray(raw) == nodata
    result[invalid] = np.nan
    return result


def paths(stamp, input_root=Path('E:/')):
    root = Path(input_root)
    day = Path(stamp[:4]) / stamp[4:6] / stamp[6:8]
    return {
        'lst_e': root/'PRODUCTS/MSG/MLST/GEOTIFF'/day/f'HDF5_LSASAF_MSG_LST_MSG-Disk_{stamp}.tif',
        'lst_i': root/'PRODUCTS/MSG-IODC/MLST/GEOTIFF'/day/f'HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_{stamp}.tif',
        'lai': root/'PRODUCTS/MSG/MDLAI/GEOTIFF'/day/f'HDF5_LSASAF_MSG_LAI_MSG-Disk_{stamp[:8]}0000.tif',
    }


def static_paths(input_root):
    root = Path(input_root)
    return {'vza_e': root/'Static/combined_euro_vza.tif',
            'vaa_e': root/'Static/combined_euro_vaa.tif',
            'land': root/'map/MCD12C1_2011_0.01.tif',
            'emis_s': root/'lse/AG1km.v003.SoilEmi.ABI.Global.001D_LSE12.tif',
            'emis_v_table': root/'lse/IGBP_Emi.txt'}


def grid_info(input_root):
    reference = gdal.Open(str(static_paths(input_root)['vza_e']), gdal.GA_ReadOnly)
    shape = (reference.RasterYSize, reference.RasterXSize)
    projection = reference.GetProjection()
    crs = osr.SpatialReference()
    crs.ImportFromWkt(projection)
    crs.AutoIdentifyEPSG()
    if shape != EXPECTED_SHAPE or crs.GetAuthorityCode(None) != '4326':
        raise ValueError('The MSG reference must be the existing 3333x2633 EPSG:4326 raster')
    return {'shape': list(shape), 'GeoTransform': list(reference.GetGeoTransform()), 'Projection': projection, 'EPSG': 4326}


def grid_check(dataset, grid):
    if dataset is None:
        raise ValueError('Cannot open raster')
    first, second = osr.SpatialReference(), osr.SpatialReference()
    first.ImportFromWkt(dataset.GetProjection())
    second.ImportFromWkt(grid['Projection'])
    if ((dataset.RasterYSize, dataset.RasterXSize) != tuple(grid['shape']) or
            not np.allclose(dataset.GetGeoTransform(), grid['GeoTransform'], rtol=0, atol=1e-9) or
            not first.IsSame(second)):
        raise ValueError('Input raster grid mismatch: ' + dataset.GetDescription())


def sample_ancillary(path, lat, lon):
    """Legacy nearest-cell truncation, with each ancillary's own declared CRS."""
    dataset = gdal.Open(str(path), gdal.GA_ReadOnly)
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)
    target = osr.SpatialReference()
    target.ImportFromWkt(dataset.GetProjection())
    for crs in [source, target]:
        crs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    transform = osr.CoordinateTransformation(source, target)
    inverse_gt = gdal.InvGeoTransform(dataset.GetGeoTransform())
    image = dataset.ReadAsArray()
    output = np.full(lat.shape, np.nan, dtype='float64')
    nodata = dataset.GetRasterBand(1).GetNoDataValue()
    for y in range(0, lat.shape[0], 256):
        section = slice(y, min(y+256, lat.shape[0]))
        points = np.column_stack([lon[section].ravel(), lat[section].ravel()])
        projected = np.asarray(transform.TransformPoints(points))
        x, z = projected[:, 0], projected[:, 1]
        finite = np.isfinite(x) & np.isfinite(z)
        col = np.trunc(np.where(finite, inverse_gt[0]+inverse_gt[1]*x+inverse_gt[2]*z, -1)).astype('int64')
        row = np.trunc(np.where(finite, inverse_gt[3]+inverse_gt[4]*x+inverse_gt[5]*z, -1)).astype('int64')
        valid = finite & (row >= 0) & (row < image.shape[0]) & (col >= 0) & (col < image.shape[1])
        sampled = np.full(len(row), np.nan)
        sampled[valid] = image[row[valid], col[valid]]
        if nodata is not None:
            sampled[sampled == nodata] = np.nan
        output[section] = sampled.reshape(lat[section].shape)
    return output


def load_static(input_root, grid):
    height, width = grid['shape']
    gt = grid['GeoTransform']
    rows, cols = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
    lon = gt[0] + cols*gt[1] + rows*gt[2]
    lat = gt[3] + cols*gt[4] + rows*gt[5]
    files = static_paths(input_root)
    static = {}
    for key in ['vza_e', 'vaa_e']:
        dataset = gdal.Open(str(files[key]), gdal.GA_ReadOnly)
        grid_check(dataset, grid)
        raw = dataset.ReadAsArray()
        value = raw.astype('float64') / 100.
        nodata = dataset.GetRasterBand(1).GetNoDataValue()
        if nodata is not None:
            value[raw == nodata] = np.nan
        static[key] = value % 360 if key.startswith('vaa') else value
    static['land'] = sample_ancillary(files['land'], lat, lon)
    static['emis_s'] = sample_ancillary(files['emis_s'], lat, lon)
    if np.nanmean(static['emis_s'][static['emis_s'] > 0]) > 1:
        static['emis_s'] /= 1000.
    table = np.loadtxt(files['emis_v_table'])
    if table.ndim == 1:
        table = table[:, None]
    land = static['land']
    valid = np.isfinite(land) & (land >= 0) & (land < table.shape[0])
    static['emis_v'] = np.full_like(land, np.nan)
    static['emis_v'][valid] = table[land[valid].astype('int64'), 0] / 1000.
    coarse_shape = (width // 10, height // 10)
    return static, lat, lon, cv2.resize(lat, coarse_shape, interpolation=cv2.INTER_NEAREST), cv2.resize(lon, coarse_shape, interpolation=cv2.INTER_NEAREST)


def file_manifest(files):
    return {str(Path(path).resolve()): {'sha256': sha(path), 'bytes': Path(path).stat().st_size} for path in files}


def load_geometry_module(path):
    spec = importlib.util.spec_from_file_location('ls4t_view_geometry', path)
    if spec is None or spec.loader is None:
        raise ValueError('Cannot load geometry provider')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not callable(getattr(module, 'view_geometry', None)):
        raise ValueError('Geometry provider must define view_geometry(stamp, lat, lon, base_static, plan)')
    return module


def build_identity(args, grid):
    legacy_core=args.legacy_case_root/'implementation/msg_lsct3.2-iter.py'
    legacy_producer=args.legacy_case_root/'implementation/produce_msg_5x5.py'
    if sha(legacy_core) != LEGACY_CORE_SHA:
        raise ValueError('Historical numerical source changed; independent verification is required')
    code_files = [Path(__file__).resolve(), args.geometry_module.resolve()]
    static_files = list(static_paths(args.input_root).values())
    sources = file_manifest(static_files + [legacy_core, legacy_producer])
    code = file_manifest(code_files)
    plan = json.loads(args.geometry_plan.read_text(encoding='utf8'))
    # Optional declared support sources are frozen along with the plan.
    additional = plan.get('source_files', []) if isinstance(plan, dict) else []
    if additional:
        sources.update(file_manifest([Path(path) for path in additional]))
    identity = {'protocol_hash': PROTOCOL_HASH, 'code_sha256': sha(__file__),
                'implementation_sha256':hash_object(code),
                'code_files': code, 'static_sources': sources,
                'static_source_hash': hash_object(sources), 'geometry_plan_sha256': sha(args.geometry_plan),
                'geometry_module_sha256': sha(args.geometry_module), 'grid': grid,
                'runtime': {'numpy': np.__version__, 'h5py': h5py.__version__, 'GDAL': gdal.VersionInfo(),
                            'pvlib': pvlib.__version__, 'opencv': cv2.__version__}}
    identity['identity_hash'] = hash_object(identity)
    return identity, plan


def assert_current_identity(identity, config):
    if sha(__file__) != identity['code_sha256'] or sha(config['geometry_module']) != identity['geometry_module_sha256']:
        raise RuntimeError('Producer or geometry code changed during the run')
    if sha(config['geometry_plan']) != identity['geometry_plan_sha256']:
        raise RuntimeError('Geometry plan changed during the run')


_WORKER = None
def worker_init(config, identity, plan):
    global _WORKER
    assert_current_identity(identity, config)
    for filename, record in identity['static_sources'].items():
        if sha(filename) != record['sha256']:
            raise RuntimeError('Static/source hash changed: ' + filename)
    geometry = load_geometry_module(config['geometry_module'])
    static, lat, lon, latt, lonn = load_static(config['input_root'], identity['grid'])
    _WORKER = {'config': config, 'identity': identity, 'plan': plan, 'geometry': geometry,
               'static': static, 'lat': lat, 'lon': lon, 'latt': latt, 'lonn': lonn}


def instant_path(root, stamp):
    return Path(root)/'INSTANTANEOUS'/stamp[:4]/stamp[4:6]/stamp[6:8]/f'MSG_LS4T_{stamp}.h5'


def scene_tif_path(root, stamp):
    return Path(root)/'GEOTIFF'/stamp[:4]/stamp[4:6]/stamp[6:8]/f'MSG_LS4T_{stamp}.tif'


def attrs(file, identity):
    grid = identity['grid']
    file.attrs.update(protocol_hash=PROTOCOL_HASH, protocol_json=json_text(PROTOCOL),
                      identity_hash=identity['identity_hash'], code_sha256=identity['code_sha256'],
                      implementation_sha256=identity['implementation_sha256'],
                      static_source_hash=identity['static_source_hash'], geometry_plan_sha256=identity['geometry_plan_sha256'],
                      GeoTransform=grid['GeoTransform'], Projection=grid['Projection'], EPSG=4326,
                      bands=json_text(BANDS), Band_Names=json_text(BAND_DESCRIPTIONS),
                      TimeZone='UTC', time_zone='UTC', Format_Version=1,
                      Scale_Factor=100.,scale_factor=.01,Units='K',Missing_Value=0,
                      Stored_Value_Convention='stored_value = round(kelvin * Scale_Factor); 0 = NoData',
                      Storage_Data_Type='uint16',
                      source_attribution='Derived LS4T; EUMETSAT/LSA SAF MSG and MSG-IODC LST, MSG LAI')


def data_attrs(dataset, identity, encoding='dn'):
    dataset.attrs.update(GeoTransform=identity['grid']['GeoTransform'], Projection=identity['grid']['Projection'],
                         Scale_Factor=100. if encoding=='dn' else 1., scale_factor=.01 if encoding=='dn' else 1.,
                         add_offset=0., Units='K', units='K', Band_Names=json_text(BAND_DESCRIPTIONS),
                         Description=','.join(BAND_DESCRIPTIONS))


def create_tif(path, identity, dtype, timestamp, scale, nodata):
    height, width = identity['grid']['shape']
    dataset = gdal.GetDriverByName('GTiff').Create(str(path), width, height, 4, dtype,
        options=['TILED=YES', 'BLOCKXSIZE=256', 'BLOCKYSIZE=128', 'COMPRESS=DEFLATE',
                 'PREDICTOR=2' if dtype==gdal.GDT_UInt16 else 'PREDICTOR=3', 'BIGTIFF=IF_SAFER', 'NUM_THREADS=1'])
    dataset.SetGeoTransform(identity['grid']['GeoTransform'])
    dataset.SetProjection(identity['grid']['Projection'])
    dataset.SetMetadata({'IDENTITY_HASH': identity['identity_hash'], 'PROTOCOL_HASH': PROTOCOL_HASH,
                         'CODE_SHA256': identity['code_sha256'], 'TIME_ZONE': 'UTC', 'TIMESTAMP_UTC': timestamp,
                         'SOURCE_ATTRIBUTION': 'Derived LS4T; EUMETSAT/LSA SAF MSG, MSG-IODC LST and MSG LAI'})
    for i, description in enumerate(BAND_DESCRIPTIONS, 1):
        band = dataset.GetRasterBand(i)
        band.SetDescription(description)
        band.SetScale(scale)
        band.SetOffset(0.)
        band.SetUnitType('K')
        band.SetNoDataValue(nodata)
    return dataset


def commit_path(hdf):
    return Path(str(hdf) + '.complete.json')


def check_resume(hdf, tif, identity, signature, allow_source_refresh=False):
    marker = commit_path(hdf)
    if marker.exists():
        record = json.loads(marker.read_text(encoding='utf8'))
        if record['identity_hash'] != identity['identity_hash']:
            raise RuntimeError('Existing product has a different frozen identity: ' + str(hdf))
        if record['source_signature'] != signature:
            if not allow_source_refresh:
                raise RuntimeError('Existing product sources changed: ' + str(hdf))
            # A month may gain newly recovered committed scenes on a later run.
            # Its frozen algorithm/static/geometry identity must still match.
            return None
        for path in [hdf, tif]:
            if not path.exists() or sha(path) != record['files'][str(path)]['sha256']:
                raise RuntimeError('Committed product hash mismatch: ' + str(path))
        with h5py.File(hdf, 'r') as source:
            if source.attrs['identity_hash'] != identity['identity_hash'] or int(source.attrs['complete']) != 1:
                raise RuntimeError('Incomplete or mismatched product: ' + str(hdf))
        return record
    if hdf.exists():
        with h5py.File(hdf, 'r') as source:
            if source.attrs.get('identity_hash') != identity['identity_hash']:
                raise RuntimeError('Refusing to replace a product from another identity: ' + str(hdf))
    if tif.exists():
        dataset = gdal.Open(str(tif))
        if dataset.GetMetadataItem('IDENTITY_HASH') != identity['identity_hash']:
            raise RuntimeError('Refusing to replace a GeoTIFF from another identity: ' + str(tif))
    return None


def commit_products(hdf_temp, tif_temp, hdf, tif, identity, signature, record):
    os.replace(tif_temp, tif)
    os.replace(hdf_temp, hdf)
    record.update(identity_hash=identity['identity_hash'], source_signature=signature,
                  files={str(path): {'sha256': sha(path), 'bytes': path.stat().st_size} for path in [hdf, tif]})
    atomic_json(commit_path(hdf), record)
    return record


def produce_scene(stamp):
    worker = _WORKER
    identity, config = worker['identity'], worker['config']
    assert_current_identity(identity, config)
    started = time.monotonic()
    input_paths = paths(stamp, config['input_root'])
    absent = [str(path) for path in input_paths.values() if not path.is_file()]
    if absent:
        return {'status': 'missing_input', 'timestamp': stamp, 'missing': absent}
    geometry, geometry_record = worker['geometry'].view_geometry(stamp, worker['lat'], worker['lon'], worker['static'], worker['plan'])
    if geometry is None:
        return {'status': 'deferred_geometry', 'timestamp': stamp, 'geometry': geometry_record}
    required = ['vza_e', 'vza_i', 'vaa_e', 'vaa_i']
    if any(key not in geometry or geometry[key].shape != tuple(identity['grid']['shape']) for key in required):
        raise ValueError('Geometry provider returned missing fields or a mismatched grid')
    inputs = file_manifest(input_paths.values())
    signature = hash_object({'inputs': inputs, 'geometry': geometry_record})
    root = Path(config['output'])
    hdf, tif = instant_path(root, stamp), scene_tif_path(root, stamp)
    resumed = check_resume(hdf, tif, identity, signature)
    if resumed is not None:
        return dict(resumed, status='resumed', seconds=time.monotonic()-started)
    for path in [hdf, tif]:
        path.parent.mkdir(parents=True, exist_ok=True)
    hdf_temp, tif_temp = Path(str(hdf)+'.partial'), Path(str(tif)+'.partial')
    datasets = {key: gdal.Open(str(path), gdal.GA_ReadOnly) for key, path in input_paths.items()}
    for dataset in datasets.values():
        grid_check(dataset, identity['grid'])
    height, width = identity['grid']['shape']
    timestamp = pd.to_datetime(stamp, format='%Y%m%d%H%M', utc=True)
    solar_table = pvlib.solarposition.get_solarposition(np.repeat(timestamp, worker['latt'].size),
        worker['latt'].ravel(), worker['lonn'].ravel(), 0., method='nrel_numpy')
    solar = {key: cv2.resize(solar_table[field].to_numpy().reshape(worker['latt'].shape).astype('float32'),
                            (width, height), interpolation=cv2.INTER_NEAREST)
             for key, field in [('sza', 'zenith'), ('saa', 'azimuth')]}
    valid_pixels = 0
    histogram = np.zeros(26, dtype='int64')
    raster = create_tif(tif_temp, identity, gdal.GDT_UInt16, timestamp.isoformat(), .01, 0)
    try:
        with h5py.File(hdf_temp, 'w') as file:
            attrs(file, identity)
            file.attrs.update(timestamp_UTC=timestamp.isoformat(), inputs_json=json_text(inputs),
                              geometry_json=json_text(geometry_record), source_signature=signature)
            chunks = (min(128, height), min(256, width))
            output = file.create_dataset('data', (4,height,width), dtype='uint16', chunks=(1,*chunks), compression='gzip', compression_opts=4)
            data_attrs(output, identity)
            output.attrs.update(NoData_Value=0, Missing_Value=0, _FillValue=0)
            neighbors = file.create_dataset('valid_neighbors', (height,width), dtype='uint8', chunks=chunks, compression='gzip')
            file['neighbors'] = neighbors
            qa = file.create_dataset('qa', (height,width), dtype='uint8', chunks=chunks, compression='gzip')
            qa.attrs['flag_masks'] = [1,2,4,8,16]
            qa.attrs['flag_meanings'] = 'invalid_input low_neighbors low_LAI failed_or_out_of_range constraint_active'
            tile = config['tile_rows']
            for y in range(0, height, tile):
                end, lo, hi = min(height,y+tile), max(0,y-2), min(height,y+tile+2)
                crop = slice(y-lo,end-lo)
                d = {key: value[lo:hi].astype('float64') for key,value in worker['static'].items()}
                d.update({key: value[lo:hi].astype('float64') for key,value in geometry.items()})
                d.update({key: value[lo:hi].astype('float64') for key,value in solar.items()})
                for key,dataset in datasets.items():
                    raw = dataset.ReadAsArray(0,lo,width,hi-lo)
                    nodata = dataset.GetRasterBand(1).GetNoDataValue()
                    d[key] = decode_lai(raw,nodata) if key=='lai' else decode_lst(raw,nodata)
                temp, n, q = retrieve(d)
                temp, n, q = temp[:,crop], n[crop], q[crop]
                good = np.isfinite(temp).all(0)
                encoded = np.rint(np.nan_to_num(temp,nan=0.)*100).astype('uint16')
                output[:,y:end], neighbors[y:end], qa[y:end] = encoded, n, q
                for i in range(4):
                    raster.GetRasterBand(i+1).WriteArray(encoded[i],0,y)
                valid_pixels += int(good.sum())
                histogram += np.bincount(n[good],minlength=26)
            file.attrs.update(valid_pixels=valid_pixels, valid_neighbor_histogram=histogram, complete=1)
        raster.FlushCache()
    finally:
        raster = None
        datasets.clear()
    record = {'timestamp': stamp, 'hdf5': str(hdf), 'geotiff': str(tif), 'valid_pixels': valid_pixels,
              'valid_neighbor_histogram': histogram.tolist(), 'geometry': geometry_record,
              'status': 'written', 'seconds': time.monotonic()-started}
    return commit_products(hdf_temp,tif_temp,hdf,tif,identity,signature,record)


def scene_job(stamp):
    try:
        return produce_scene(stamp)
    except Exception as error:
        if type(error).__name__ in ['DeferredGeometry','GeometryUnavailable','UnresolvedGeometry']:
            return {'status': 'deferred_geometry', 'timestamp': stamp, 'error': str(error)}
        return {'status': 'failed', 'timestamp': stamp, 'error': str(error), 'traceback': traceback.format_exc()}


def monthly(root, month, hour, files, expected, omissions, identity, tile_rows=256):
    """MSG-compatible DN means; GeoTIFF stores direct Kelvin float32 values."""
    root = Path(root)
    hdf = root/'MONTHLY_HOUR'/month[:4]/f'MLST_MONTH_{month}_HH{hour:02d}.h5'
    tif = root/'MONTHLY_HOUR_GEOTIFF'/month[:4]/f'MLST_MONTH_{month}_HH{hour:02d}.tif'
    sources = file_manifest(files)
    stable_omissions=[{key:record[key] for key in ['timestamp','status','missing','error'] if key in record}
                      for record in omissions]
    stable_omissions.sort(key=lambda record:record['timestamp'])
    signature = hash_object({'sources':sources,'expected':expected,'omissions':stable_omissions})
    resumed = check_resume(hdf,tif,identity,signature,allow_source_refresh=True)
    if resumed:
        return dict(resumed,status='resumed')
    for path in [hdf,tif]:
        path.parent.mkdir(parents=True,exist_ok=True)
    hdf_temp,tif_temp = Path(str(hdf)+'.partial'),Path(str(tif)+'.partial')
    height,width = identity['grid']['shape']
    support = np.zeros(len(expected)+1,dtype='int64')
    timestamp = f'{month[:4]}-{month[4:6]} UTC {hour:02d}:00 monthly mean'
    raster = create_tif(tif_temp,identity,gdal.GDT_Float32,timestamp,1.,float('nan'))
    chunks = (min(128,height),min(256,width))
    started = time.monotonic()
    try:
        with h5py.File(hdf_temp,'w') as file:
            attrs(file,identity)
            file.attrs.update(Year=int(month[:4]),Month=int(month[4:6]),Hour=hour,hour_UTC=hour,
                Missing_Value=np.nan,Storage_Data_Type='float32',
                Stored_Value_Convention='stored_value = kelvin * Scale_Factor',
                source_count=len(files),calendar_days=len(expected),source_sha256_json=json_text(sources),
                missing_sources_json=json_text(omissions),source_timestamps_json=json_text([Path(p).stem[-12:] for p in files]),
                calendar_input_complete=int(len(files)==len(expected)),group_processed=1,source_signature=signature)
            mean = file.create_dataset('Monthly_Hour_Mean_LST',(4,height,width),dtype='float32',
                chunks=(1,*chunks),compression='gzip',compression_opts=4,fillvalue=np.nan)
            file['data'] = mean
            data_attrs(mean,identity)
            mean.attrs.update(NoData_Value=np.nan,Missing_Value=np.nan,_FillValue=np.nan)
            nout = file.create_dataset('n_obs',(height,width),dtype='uint8',chunks=chunks,compression='gzip')
            qa = file.create_dataset('qa',(height,width),dtype='uint8',chunks=chunks,compression='gzip')
            qa.attrs['flag_masks'] = [1,2,4]
            qa.attrs['flag_meanings'] = 'no_observations low_support calendar_input_incomplete'
            low = file.create_dataset('low_support',(height,width),dtype='uint8',chunks=chunks,compression='gzip')
            for y in range(0,height,tile_rows):
                end = min(height,y+tile_rows)
                sums = np.zeros((4,end-y,width),dtype='float64')
                counts = np.zeros((end-y,width),dtype='uint8')
                for path in files:
                    with h5py.File(path,'r') as source:
                        if source.attrs['identity_hash']!=identity['identity_hash'] or int(source.attrs['complete'])!=1:
                            raise RuntimeError('Monthly source identity/complete mismatch: '+str(path))
                        encoded = source['data'][:,y:end]
                        good = np.all((encoded>=25000)&(encoded<=35000),axis=0)
                        sums += np.where(good[None],encoded.astype('float64'),0.)
                        counts += good
                average = np.full_like(sums,np.nan)
                np.divide(sums,counts[None],out=average,where=counts[None]>0)
                mean[:,y:end] = average
                nout[y:end] = counts
                low_flags = ((counts>0)&(counts<3)).astype('uint8')
                low[y:end] = low_flags
                qa[y:end] = (counts==0).astype('uint8') | (low_flags<<1) | (4 if len(files)!=len(expected) else 0)
                for i in range(4):
                    raster.GetRasterBand(i+1).WriteArray((average[i]*.01).astype('float32'),0,y)
                support += np.bincount(counts.ravel(),minlength=len(expected)+1)
            file.attrs.update(support_histogram=support,complete=1)
        raster.FlushCache()
    finally:
        raster = None
    # Verify values/counts before atomic commit using independent direct reads.
    verification = []
    with h5py.File(hdf_temp,'r') as file:
        for y,x in {(min(881,height-1),min(333,width-1)),(height//2,width//2),(height//3,width//2),(height-1,width-1)}:
            values=[]
            for path in files:
                with h5py.File(path,'r') as source:
                    values.append(source['data'][:,y,x])
            values=np.asarray(values)
            good=np.all((values>=25000)&(values<=35000),axis=1)
            if int(file['n_obs'][y,x])!=int(good.sum()):
                raise RuntimeError('Monthly sample count verification failed')
            if good.any():
                np.testing.assert_allclose(file['data'][:,y,x],values[good].mean(0),rtol=0,atol=.002)
            elif not np.isnan(file['data'][:,y,x]).all():
                raise RuntimeError('Monthly missing values verification failed')
            verification.append({'row':y,'column':x,'n':int(good.sum())})
    record={'month':month,'hour_UTC':hour,'hdf5':str(hdf),'geotiff':str(tif),'source_count':len(files),
            'calendar_days':len(expected),'valid_pixels':int(support[1:].sum()),'support_histogram':support.tolist(),
            'pixel_verification':verification,'status':'written','seconds':time.monotonic()-started}
    return commit_products(hdf_temp,tif_temp,hdf,tif,identity,signature,record)


def inventory(args):
    start,end = pd.Period(args.start_month,freq='M'),pd.Period(args.end_month,freq='M')
    if start>end:
        raise ValueError('Reversed dates')
    if start<pd.Period('201708',freq='M') or end>pd.Period('202512',freq='M'):
        raise ValueError('The production period is August 2017 through December 2025')
    if not all(10<=h<=16 for h in args.hours) or len(set(args.hours))!=len(args.hours):
        raise ValueError('Unique UTC hours 10-16 are required')
    groups=[]
    missing=[]
    for period in pd.period_range(start,end,freq='M'):
        month=f'{period.year:04d}{period.month:02d}'
        for hour in args.hours:
            expected=[f'{month}{day:02d}{hour:02d}00' for day in range(1,calendar.monthrange(period.year,period.month)[1]+1)]
            available=[]
            absent=[]
            for stamp in expected:
                absent_paths=[str(path) for path in paths(stamp,args.input_root).values() if not path.is_file()]
                if absent_paths:
                    record={'timestamp':stamp,'missing':absent_paths}
                    absent.append(record)
                    missing.append(record)
                else:
                    available.append(stamp)
            groups.append({'month':month,'hour':hour,'expected':expected,'available':available,'missing':absent})
    return {'start_month':args.start_month,'end_month':args.end_month,'hours_UTC':args.hours,
            'expected_scenes':sum(len(group['expected']) for group in groups),
            'available_input_scenes':sum(len(group['available']) for group in groups),
            'missing_input_scenes':len(missing),'groups':groups,'missing':missing,
            'note':'Available inputs do not imply eligible viewing geometry'}


@contextmanager
def production_lock(root):
    stream=(root/'producer.lock').open('a+b')
    try:
        stream.seek(0)
        stream.write(b'0')
        stream.flush()
        stream.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    finally:
        stream.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=DEFAULT_ROOT)
    parser.add_argument('--input-root',type=Path,default=Path('E:/'))
    parser.add_argument('--start-month',default='201708')
    parser.add_argument('--end-month',default='202512')
    parser.add_argument('--hours',type=int,nargs='+',default=list(range(10,17)))
    parser.add_argument('--workers',type=int,default=8)
    parser.add_argument('--tile-rows',type=int,default=256)
    parser.add_argument('--retries',type=int,default=1,help='Additional attempts for failed scenes in this run')
    parser.add_argument('--legacy-case-root',type=Path,default=Path('C:/work/ls4t-msg/cases/official'))
    parser.add_argument('--geometry-module',type=Path,default=HERE/'msg_view_geometry.py')
    parser.add_argument('--geometry-plan',type=Path,default=HERE/'geometry_plan.json')
    parser.add_argument('--inventory-only',action='store_true')
    args=parser.parse_args()
    if args.workers<1 or args.tile_rows<1 or args.retries<0:
        parser.error('workers and tile-rows must be positive; retries nonnegative')
    root=args.output.resolve()
    if root==Path('E:/PRODUCTS/LSCT/MSG_5X5_PHYSICAL_V1').resolve():
        parser.error('The historical .05 product root cannot be reused')
    root.mkdir(parents=True,exist_ok=True)
    with production_lock(root):
        listing=inventory(args)
        atomic_json(root/'inventory.json',listing)
        atomic_json(root/'missing_inputs.json',listing['missing'])
        if args.inventory_only:
            print(json_text({k:v for k,v in listing.items() if k not in ['groups','missing']}),flush=True)
            return 0
        if not args.geometry_module.is_file() or not args.geometry_plan.is_file():
            raise RuntimeError('Audited timestamp-aware view geometry module and plan are required before production')
        identity,plan=build_identity(args,grid_info(args.input_root))
        identity_file=root/'production_identity.json'
        if identity_file.exists():
            previous=json.loads(identity_file.read_text(encoding='utf8'))
            if previous['identity_hash']!=identity['identity_hash']:
                raise RuntimeError('Different frozen code/static/protocol/geometry identity; use a separate collection root')
        atomic_json(identity_file,dict(identity,protocol=PROTOCOL))
        atomic_json(root/'static_source_manifest.json',{'files':identity['static_sources']})
        config={'input_root':str(args.input_root.resolve()),'output':str(root),'tile_rows':args.tile_rows,
                'geometry_module':str(args.geometry_module.resolve()),'geometry_plan':str(args.geometry_plan.resolve())}
        geometry_provider=load_geometry_module(args.geometry_module)
        if not callable(getattr(geometry_provider,'geometry_metadata',None)):
            raise RuntimeError('Geometry provider must expose lightweight geometry_metadata(stamp,plan)')
        run_id=uuid.uuid4().hex
        status={'status':'initializing_workers','run_id':run_id,'pid':os.getpid(),'started_UTC':now(),
                'workers':args.workers,'identity_hash':identity['identity_hash'],
                'expected_scenes':listing['expected_scenes'],'available_input_scenes':listing['available_input_scenes'],
                'missing_input_scenes':listing['missing_input_scenes'],'eligible_scenes':0,'scenes_completed':0,
                'scenes_written':0,'scenes_resumed':0,'failed_scenes':0,'deferred_geometry_scenes':0,
                'groups_total':len(listing['groups']),'groups_completed':0,'monthly_outputs':0,'empty_groups':0,
                'failed_monthly_groups':0,'eligibility_checked_scenes':0,
                'eligibility_definition':'Complete projected inputs with trusted native scene geometry; data decoding may still fail'}
        failures=[]
        deferred=[]
        monthly_failures=[]
        atomic_json(root/'status.json',status)
        def publish():
            status['updated_UTC']=now()
            atomic_json(root/'status.json',status)
        try:
            # Do not initialize large worker arrays for dates without trusted geometry.
            status['status']='checking_geometry_eligibility'
            publish()
            for group in listing['groups']:
                eligible=[]
                group['deferred_geometry']=[]
                for stamp in group['available']:
                    try:
                        geometry_provider.geometry_metadata(stamp,plan)
                        eligible.append(stamp)
                        status['eligible_scenes']+=1
                    except Exception as error:
                        record={'status':'deferred_geometry','timestamp':stamp,'error':str(error)}
                        if type(error).__name__ not in ['DeferredGeometry','GeometryUnavailable','UnresolvedGeometry']:
                            # Provider code/runtime faults must not be mislabeled as source gaps.
                            raise
                        deferred.append(record)
                        group['deferred_geometry'].append(record)
                        status['deferred_geometry_scenes']+=1
                    status['eligibility_checked_scenes']+=1
                    if status['eligibility_checked_scenes']%100==0:
                        publish()
                group['eligible']=eligible
            atomic_json(root/'eligible_inventory.json',listing)
            atomic_json(root/'deferred_geometry.json',deferred)
            publish()
            with ProcessPoolExecutor(max_workers=args.workers,mp_context=mp.get_context('spawn'),
                                     initializer=worker_init,initargs=(config,identity,plan)) as pool:
                for group in listing['groups']:
                    assert_current_identity(identity,config)
                    status.update(status='running',current_month=group['month'],current_hour_UTC=group['hour'])
                    publish()
                    pending={pool.submit(scene_job,stamp):(stamp,0) for stamp in group['eligible']}
                    results={}
                    while pending:
                        done,_=wait(pending,timeout=30,return_when=FIRST_COMPLETED)
                        if not done:
                            publish()
                            continue
                        future=next(iter(done))
                        stamp,attempt=pending.pop(future)
                        try:
                            record=future.result()
                        except Exception as error:
                            record={'status':'failed','timestamp':stamp,'error':str(error),'traceback':traceback.format_exc(),
                                    'failure_stage':'worker_future'}
                        record.update(run_id=run_id,attempt=attempt+1,updated_UTC=now())
                        append_json(root/'scene_manifest.jsonl',record)
                        if record['status']=='failed' and attempt<args.retries:
                            try:
                                pending[pool.submit(scene_job,stamp)]=(stamp,attempt+1)
                                append_json(root/'production_log.jsonl',{'event':'retry','timestamp':stamp,'attempt':attempt+2,'run_id':run_id})
                                continue
                            except Exception as error:
                                record['retry_submission_error']=str(error)
                        results[stamp]=record
                        state=record['status']
                        if state in ['written','resumed']:
                            status['scenes_completed']+=1
                            status['scenes_written' if state=='written' else 'scenes_resumed']+=1
                        elif state=='deferred_geometry':
                            status['deferred_geometry_scenes']+=1
                            deferred.append(record)
                        else:
                            status['failed_scenes']+=1
                            failures.append(record)
                        status['last_timestamp']=stamp
                        publish()
                        print('SCENE',stamp,state,'completed',status['scenes_completed'],'failed',status['failed_scenes'],
                              'geometry_deferred',status['deferred_geometry_scenes'],flush=True)
                    files=[Path(results[stamp]['hdf5']) for stamp in group['eligible'] if results[stamp]['status'] in ['written','resumed']]
                    omissions=list(group['missing'])+group['deferred_geometry']+[
                        results[stamp] for stamp in group['eligible'] if results[stamp]['status'] not in ['written','resumed']]
                    if files:
                        status['status']='aggregating_month'
                        publish()
                        try:
                            record=monthly(root,group['month'],group['hour'],files,group['expected'],omissions,identity,args.tile_rows)
                            record.update(run_id=run_id,updated_UTC=now())
                            append_json(root/'monthly_manifest.jsonl',record)
                            status['monthly_outputs']+=1
                            print('MONTHLY',group['month'],group['hour'],'source_count',len(files),record['status'],flush=True)
                        except Exception as error:
                            record={'month':group['month'],'hour_UTC':group['hour'],'error':str(error),'traceback':traceback.format_exc(),
                                    'run_id':run_id,'status':'failed_monthly','updated_UTC':now()}
                            monthly_failures.append(record)
                            append_json(root/'monthly_manifest.jsonl',record)
                            status['failed_monthly_groups']+=1
                    else:
                        status['empty_groups']+=1
                    status['groups_completed']+=1
                    atomic_json(root/'failed_scenes.json',failures)
                    atomic_json(root/'failed_inputs.json',failures)
                    atomic_json(root/'failed_monthly_groups.json',monthly_failures)
                    atomic_json(root/'deferred_geometry.json',deferred)
                    publish()
            status['status']=('incomplete_geometry' if deferred else 'completed_with_failures' if failures or monthly_failures else
                              'completed_with_input_gaps' if listing['missing'] else 'completed')
            return 3 if deferred else 2 if failures or monthly_failures else 0
        except BaseException:
            status.update(status='interrupted' if isinstance(sys.exc_info()[1],KeyboardInterrupt) else 'failed',error=traceback.format_exc())
            raise
        finally:
            atomic_json(root/'failed_scenes.json',failures)
            atomic_json(root/'failed_inputs.json',failures)
            atomic_json(root/'failed_monthly_groups.json',monthly_failures)
            atomic_json(root/'deferred_geometry.json',deferred)
            publish()


if __name__=='__main__':
    mp.freeze_support()
    raise SystemExit(main())
