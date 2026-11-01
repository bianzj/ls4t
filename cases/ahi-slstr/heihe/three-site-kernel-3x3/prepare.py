"""Read-only Heihe archive adapter. No temperature residual or ground-data filter."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

from functions import (decode_hhmm, geostationary_angles, kernel_basis,
                       radiance_mean, sha256, match_minutes)
from joint import window_mask


class Reader:
    def __init__(self):
        self.receipts = {}

    def read(self, path, template=None):
        path = Path(path)
        before = path.stat()
        with rasterio.open(path) as ds:
            profile = dict(shape=ds.shape, crs=ds.crs, transform=ds.transform)
            if template is not None and (ds.shape != template['shape'] or ds.crs != template['crs'] or
                                          not ds.transform.almost_equals(template['transform'])):
                raise ValueError(f'Grid mismatch: {path}')
            a = ds.read(1, masked=True).astype(float).filled(np.nan)
            metadata = dict(path=str(path), size=before.st_size, mtime_ns=before.st_mtime_ns,
                            shape=ds.shape, crs=str(ds.crs), transform=list(ds.transform),
                            dtype=ds.dtypes[0], nodata=ds.nodata, scales=ds.scales, offsets=ds.offsets)
            if ds.scales != (1.,) or ds.offsets != (0.,):
                raise ValueError(f'Unexpected automatic raster scaling: {path}')
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError(f'Input changed while reading: {path}')
        self.receipts[str(path)] = metadata
        return a, profile

    def finalize(self):
        for item in self.receipts.values():
            p = Path(item['path']); stat = p.stat()
            if (stat.st_size, stat.st_mtime_ns) != (item['size'], item['mtime_ns']):
                raise RuntimeError(f'Input changed before hashing: {p}')
            item['sha256'] = sha256(p)
        return list(self.receipts.values())


def load_sites(config):
    sites = {}
    for line in Path(config['station_file']).read_text(encoding='utf-8-sig').splitlines():
        code, lon, lat, elevation = [v.strip() for v in line.split(',')]
        sites[code] = dict(code=code, lon=float(lon), lat=float(lat), elevation_m=float(elevation),
                           name=config['site_names'].get(code, code))
    return [sites[code] for code in config['sites']]


def blocks2(a):
    """Exact 2x2 native cells; incomplete outer edge is never padded."""
    nr, nc = a.shape[:2]
    return a[:nr//2*2, :nc//2*2].reshape(nr//2, 2, nc//2, 2, *a.shape[2:])


def mean2(a):
    return blocks2(a).mean(axis=(1, 3))


def all2(a):
    return blocks2(a).all(axis=(1, 3))


def subpixels(a):
    b = blocks2(a)
    axes = [0,2,1,3]+list(range(4,b.ndim))
    return b.transpose(axes).reshape(b.shape[0],b.shape[2],4,*b.shape[4:])


def extract_date(config, day, platform):
    reader = Reader(); root = Path(config['data_root'])
    directory = root / ('s3a_heihe' if platform == 'S3A' else 's3b_heihe/s3b_heihe')
    prefix = f'{platform}_{day.year}{day.timetuple().tm_yday:03d}_day'
    raw, profile = {}, None
    fields = ['time', 'red_nadir', 'nir_nadir']
    fields += [f'{field}_{view}' for view in ('nadir', 'obliq')
               for field in ('lst', 'cloud', 'vza', 'sza', 'vaa', 'saa')]
    for field in fields:
        raw[field], p = reader.read(directory/('lst' if field.startswith('lst') else 'tif')/f'{prefix}_{field}.tif', profile)
        profile = p
    transform = profile['transform']
    if transform.b or transform.d or abs(transform.a-1000) > .01 or abs(transform.e+1000) > .01:
        raise ValueError('Expected archived north-up 1 km SLSTR grid')
    coarse_shape = (profile['shape'][0]//2, profile['shape'][1]//2)
    rows, cols = np.indices(coarse_shape)
    native_minutes = decode_hhmm(raw['time'])
    valid = np.isfinite(native_minutes) & (native_minutes > 0)
    coarse = {'row': rows, 'col': cols, 'slstr_minute': mean2(native_minutes)}
    basis = {}
    for short, view in [('n', 'nadir'), ('o', 'obliq')]:
        temp = raw[f'lst_{view}']
        v, s = raw[f'vza_{view}']*.01, raw[f'sza_{view}']*.01
        az, saz = raw[f'vaa_{view}']*.01, raw[f'saa_{view}']*.01
        raa = (az-saz) % 360
        angles_valid = np.isfinite(v+s+az+saz) & (az >= 0) & (az <= 360) & (saz >= 0) & (saz <= 360)
        valid &= np.isfinite(temp) & (temp >= 220) & (temp <= 365) & (raw[f'cloud_{view}'] == 0) & angles_valid
        for width in [config['rl_width']]+config['width_sensitivity']:
            k = kernel_basis(v, s, raa, width)
            basis[(short, width)] = mean2(k)
            valid &= np.isfinite(k).all(axis=-1)
            native_k = subpixels(k)
            for j in range(4):
                coarse[f'lsf_{short}_{j}'] = native_k[...,j,0]
                coarse[f'rl_{short}_w{width:g}_{j}'] = native_k[...,j,1]
        native_t = subpixels(temp)
        for j in range(4):
            coarse[f't_{short}_{j}'] = native_t[...,j]
        coarse[f't_{short}'] = radiance_mean(blocks2(temp), axis=(1, 3))
        coarse[f'vza_{short}'] = mean2(v)
        coarse[f'sza_{short}'] = mean2(s)
        coarse[f'raa_{short}'] = np.rad2deg(np.arctan2(mean2(np.sin(np.deg2rad(raa))), mean2(np.cos(np.deg2rad(raa))))) % 360
    red, nir = raw['red_nadir'], raw['nir_nadir']
    denominator = mean2(nir)+mean2(red)
    ndvi = np.divide(mean2(nir)-mean2(red), denominator, out=np.full(coarse_shape, np.nan), where=denominator > 0)
    # NDVI is diagnostic in the requested spatial 3x3 window, not a membership filter.
    valid_coarse = all2(valid)
    # Native acquisition times within a footprint may not be averaged across a discontinuity.
    span = np.max(blocks2(native_minutes), axis=(1, 3))-np.min(blocks2(native_minutes), axis=(1, 3))
    valid_coarse &= span <= config['maximum_time_difference_minutes']
    coarse['ndvi'] = ndvi
    for (short, width), k in basis.items():
        coarse[f'lsf_{short}'] = k[..., 0]
        coarse[f'rl_{short}_w{width:g}'] = k[..., 1]
    x, y = transform.c+(cols+.5)*2000, transform.f-(rows+.5)*2000
    to_geo = Transformer.from_crs(profile['crs'], 4326, always_xy=True)
    lon, lat = to_geo.transform(x, y)
    coarse['lon'], coarse['lat'] = lon, lat
    avza, avaa = geostationary_angles(lon, lat)
    coarse['vza_a'] = avza
    ahi_cache = {}
    site_rows = []; diagnostics = []
    to_map = Transformer.from_crs(4326, profile['crs'], always_xy=True)
    for site in load_sites(config):
        sx, sy = to_map.transform(site['lon'], site['lat'])
        sr, sc = int(np.floor((transform.f-sy)/2000)), int(np.floor((sx-transform.c)/2000))
        diag = dict(site=site['code'], centre_row=sr, centre_col=sc)
        diagnostics.append(diag)
        if not (0 <= sr < coarse_shape[0] and 0 <= sc < coarse_shape[1]) or not valid_coarse[sr, sc]:
            diag['status'] = 'station_slstr_quality_rejected'; continue
        centre_time = coarse['slstr_minute'][sr, sc]
        selection = valid_coarse & window_mask(rows,cols,sr,sc)
        selection &= abs(coarse['slstr_minute']-centre_time) <= config['maximum_acquisition_span_minutes']/2
        rr, cc = rows[selection], cols[selection]
        frame = pd.DataFrame({k: a[selection] for k, a in coarse.items()})
        frame['site'] = site['code']; frame['platform'] = platform; frame['date'] = str(day)
        frame['station_centre'] = (rr == sr) & (cc == sc)
        frame['split'] = np.where(frame['station_centre'],'centre','neighbor')
        # AHI now joins the calibration triplet. Each CV fold excludes all three views together.
        nearest_float, same_day_match = match_minutes(frame['slstr_minute'].to_numpy(), config['maximum_time_difference_minutes'])
        nearest = nearest_float.astype(int)
        frame['ahi_minute'] = nearest
        frame['ahi_time_difference_minutes'] = abs(nearest-frame['slstr_minute'])
        for column in ['t_a', 'tcc_a', 'sza_a', 'raa_a', 'lsf_a']+[f'rl_a_w{w:g}' for w in [config['rl_width']]+config['width_sensitivity']]:
            frame[column] = np.nan
        frame['ahi_qa'] = False
        for minute in np.unique(nearest):
            ahi_day = day + timedelta(days=int(minute//1440)); minute_in_day = minute % 1440
            stamp = f'{minute_in_day//60:02d}{minute_in_day%60:02d}'
            key = (str(ahi_day), stamp)
            if key not in ahi_cache:
                afolder = root/'ahi2019_heihe'; part = f'{ahi_day.month:02d}/{ahi_day.day:02d}'
                aprefix = f'AHI_{ahi_day.year}{ahi_day.timetuple().tm_yday:03d}_{stamp}'
                afields = {}
                try:
                    for field in ['lst', 'tcc', 'sza', 'saa']:
                        a, ap = reader.read(afolder/('lst' if field == 'lst' else 'tif')/part/f'{aprefix}_{field}.tif')
                        expected_transform = transform*rasterio.Affine.scale(2, 2)
                        if ap['crs'] != profile['crs'] or not ap['transform'].almost_equals(expected_transform) or ap['shape'][0] != coarse_shape[0] or ap['shape'][1] not in (coarse_shape[1], coarse_shape[1]+1):
                            raise ValueError('AHI/SLSTR footprint grids are not nested')
                        afields[field] = a[:coarse_shape[0], :coarse_shape[1]]
                    ahi_cache[key] = afields
                except FileNotFoundError:
                    ahi_cache[key] = None
            aa = ahi_cache[key]
            if aa is None: continue
            take = np.flatnonzero(nearest == minute); r, c = rr[take], cc[take]
            temp, tcc, sza, saa = aa['lst'][r,c], aa['tcc'][r,c]*.001, aa['sza'][r,c]*.01, aa['saa'][r,c]*.01
            raa = (avaa[r,c]-saa) % 360
            frame.loc[take, ['t_a','tcc_a','sza_a','raa_a']] = np.column_stack([temp,tcc,sza,raa])
            good = np.isfinite(temp+tcc+sza+saa) & (temp >= 220) & (temp <= 365) & (tcc >= 0) & (tcc <= config['maximum_ahi_tcc_proxy']) & (saa >= 0) & (saa <= 360)
            for width in [config['rl_width']]+config['width_sensitivity']:
                k = kernel_basis(avza[r,c], sza, raa, width)
                frame.loc[take, ['lsf_a', f'rl_a_w{width:g}']] = k
                good &= np.isfinite(k).all(axis=1)
            good &= same_day_match[take]
            frame.loc[take, 'ahi_qa'] = good
        centre = frame[frame['station_centre']].iloc[0]
        diag.update(centre_ndvi=float(ndvi[sr,sc]) if np.isfinite(ndvi[sr,sc]) else None, slstr_minute=float(centre_time),
                    requested_footprints=9, slstr_qa_footprints=len(frame), complete_triplets=int(frame['ahi_qa'].sum()),
                    centre_ahi_qa=bool(centre['ahi_qa']), centre_tcc=float(centre['tcc_a']) if np.isfinite(centre['tcc_a']) else None)
        supported = frame['ahi_qa'].sum() >= config['minimum_complete_triplets'] and bool(centre['ahi_qa'])
        diag['status'] = 'eligible' if supported else 'insufficient_quality_support'
        site_rows.append(frame)
    return (pd.concat(site_rows, ignore_index=True) if site_rows else pd.DataFrame()), diagnostics, reader
