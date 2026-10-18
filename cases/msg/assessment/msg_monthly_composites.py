"""Monthly UTC-stratified means of local MSG LST and LSCT products.

The two LSCT collections stay separate. Native means retain each collection's
own valid acquisitions. Paired means use one common pixel-date mask for all
four component states and both bulk LST observations. Units are kelvin.
"""
from __future__ import annotations

import argparse
import calendar
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import traceback

import h5py
import numpy as np
import rasterio
from rasterio.windows import Window

COLLECTIONS = {
    'LSCT': ('LSCT/MLST_COMPONENT', 'h5'),
    'LSCT_COMPONENT2': ('LSCT/MLST_COMPONENT2', 'h5'),
    'MSG_EURO': ('MSG/MLST/GEOTIFF', 'tif'),
    'MSG_IODC': ('MSG-IODC/MLST/GEOTIFF', 'tif'),
}
COMPONENTS = ['background_soil', 'canopy', 'sunlit_soil', 'shaded_soil']
PAIRED_BANDS = COMPONENTS + ['lst_euro', 'lst_iodc']
PROTOCOL = {
    'version': 1, 'units': 'K', 'utc_hours': list(range(10, 17)),
    'years': [2017, 2025], 'minimum_observations': 1,
    'valid_temperature_range_k': [250.0, 350.0],
    'mean': 'arithmetic mean of valid acquisition temperatures, separately by UTC hour',
    'component_mask': 'all four component states valid on the same acquisition',
    'paired_mask': 'all four states and EURO/IODC bulk LST valid on the same pixel-date',
    'bulk_decode': 'restore signed int16 Celsius*100 from projected uint16; /100 +273.15',
    'component_decode': 'unsigned kelvin*100 /100',
    'projected_bulk_nodata': 0,
    'low_support_flag': '1 or 2 valid acquisitions; mean retained',
    'daylight_filter': 'no additional filter; inherited from source retrievals',
    'uncertainty': 'not estimated; no invented error layer',
}
PROTOCOL_HASH = hashlib.sha256(json.dumps(PROTOCOL, sort_keys=True).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, data):
    path = Path(path)
    part = path.with_name(path.name + '.partial')
    part.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf8')
    # Windows readers may briefly hold a handle without delete sharing.
    # A progress-file collision must not discard a scientific monthly group.
    for attempt in range(40):
        try:
            os.replace(part, path)
            return
        except PermissionError:
            if attempt == 39:
                raise
            time.sleep(0.05)


def inventory(input_root, output_root):
    jobs = defaultdict(lambda: defaultdict(dict))
    summary = {}
    for name, (relative, extension) in COLLECTIONS.items():
        root = input_root / relative
        n = 0
        for year in range(2017, 2026):
            for month in range(1, 13):
                md = root / str(year) / f'{month:02d}'
                if not md.is_dir():
                    continue
                for day in range(1, calendar.monthrange(year, month)[1] + 1):
                    dd = md / f'{day:02d}'
                    if not dd.is_dir():
                        continue
                    for entry in os.scandir(dd):
                        if not entry.is_file() or not entry.name.lower().endswith('.' + extension):
                            continue
                        match = re.search(r'_(\d{12})\.' + extension + '$', entry.name)
                        if match is None:
                            continue
                        stamp = match.group(1)
                        if stamp[:8] != f'{year}{month:02d}{day:02d}':
                            raise ValueError(f'Filename/date directory mismatch: {entry.path}')
                        hh, minute = int(stamp[8:10]), int(stamp[10:12])
                        if hh not in PROTOCOL['utc_hours'] or minute != 0:
                            continue
                        key = f'{year}{month:02d}{hh:02d}'
                        if stamp in jobs[key][name]:
                            raise ValueError(f'Duplicate acquisition in {name}: {stamp}')
                        stat = entry.stat()
                        jobs[key][name][stamp] = {
                            'path': entry.path, 'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns}
                        n += 1
        keys = sorted(k for k in jobs if name in jobs[k])
        summary[name] = {'input_files': n, 'month_hour_groups': len(keys),
                         'first_group': keys[0] if keys else None,
                         'last_group': keys[-1] if keys else None}
    result = {'created_utc': now(), 'input_root': str(input_root),
              'protocol': PROTOCOL, 'protocol_hash': PROTOCOL_HASH,
              'summary': summary, 'jobs': dict(sorted(jobs.items()))}
    atomic_json(output_root / 'input_manifest.json', result)
    return result


def signature(sources):
    return hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()


def load_source(path, collection):
    if collection.startswith('LSCT'):
        with h5py.File(path, 'r') as f:
            if 'data' not in f or f['data'].ndim != 3 or f['data'].shape[0] != 4:
                raise ValueError(f'Expected data[4,row,col]: {path}')
            d = f['data']
            if d.attrs.get('Scale_Factor') != 100 or d.attrs.get('NoData_Value') != 0:
                raise ValueError(f'Unexpected component scale/NoData: {path}')
            if str(d.attrs.get('Description', '')).replace(' ', '') != 'Bands:ts,tv,tss,tsh':
                raise ValueError(f'Unexpected component band order: {path}')
            grid = {'shape': list(d.shape[1:]),
                    'geotransform': [float(v) for v in d.attrs['GeoTransform']],
                    'crs_wkt': str(d.attrs['Projection'])}
            raw = d[:]
        value = raw.astype(np.float64) / 100.0
        valid = np.all((raw != 0) & (value >= 250.0) & (value <= 350.0), axis=0)
    else:
        with rasterio.open(path) as src:
            if src.count != 1 or src.dtypes[0] != 'uint16' or src.nodata != 0:
                raise ValueError(f'Unexpected projected LST encoding: {path}')
            raw = src.read(1)
            grid = {'shape': list(src.shape), 'geotransform': list(src.transform.to_gdal()),
                    'crs_wkt': src.crs.to_wkt()}
        # Projection casts signed Celsius*100 to uint16; restore the original bits.
        value = (raw.view(np.int16).astype(np.float64) / 100.0 + 273.15)[None, :, :]
        valid = (raw != 0) & np.isfinite(value[0]) & (value[0] >= 250.0) & (value[0] <= 350.0)
    return value, valid, grid


def grid_matches(left, right):
    return (left['shape'] == right['shape'] and
            np.allclose(left['geotransform'], right['geotransform'], rtol=0, atol=1e-10) and
            rasterio.crs.CRS.from_wkt(left['crs_wkt']) == rasterio.crs.CRS.from_wkt(right['crs_wkt']))


class Accumulator:
    def __init__(self, shape, bands):
        self.total = np.zeros((bands, *shape), dtype=np.float64)
        self.count = np.zeros(shape, dtype=np.uint16)
        self.acquisitions = []

    def add(self, value, valid, stamp):
        np.add(self.total, value, out=self.total, where=valid[None, :, :])
        np.add(self.count, valid, out=self.count, casting='unsafe')
        self.acquisitions.append(stamp)


def process_job(key, sources, outpath, update=None):
    accumulators = {}
    grid = None
    stamps = sorted({stamp for mapping in sources.values() for stamp in mapping})
    for offset, stamp in enumerate(stamps):
        loaded = {}
        for name, mapping in sources.items():
            if stamp not in mapping:
                continue
            record = mapping[stamp]
            current = Path(record['path']).stat()
            if current.st_size != record['bytes'] or current.st_mtime_ns != record['mtime_ns']:
                raise RuntimeError(f'Input changed after inventory: {record["path"]}')
            value, valid, metadata = load_source(record['path'], name)
            if grid is None:
                grid = metadata
            elif not grid_matches(grid, metadata):
                raise ValueError(f'Grid mismatch: {record["path"]}')
            acc = accumulators.setdefault(name, None)
            if acc is None:
                acc = accumulators[name] = Accumulator(grid['shape'], value.shape[0])
            acc.add(value, valid, stamp)
            loaded[name] = (value, valid)
        for name in ('LSCT', 'LSCT_COMPONENT2'):
            if all(n in loaded for n in (name, 'MSG_EURO', 'MSG_IODC')):
                value = np.concatenate([loaded[n][0] for n in (name, 'MSG_EURO', 'MSG_IODC')])
                valid = loaded[name][1] & loaded['MSG_EURO'][1] & loaded['MSG_IODC'][1]
                paired = 'PAIRED_' + name
                if paired not in accumulators:
                    accumulators[paired] = Accumulator(grid['shape'], 6)
                accumulators[paired].add(value, valid, stamp)
        if update:
            update(offset + 1, len(stamps), stamp)
        del loaded
    if not accumulators:
        raise ValueError(f'No source acquisitions: {key}')
    outpath.parent.mkdir(parents=True, exist_ok=True)
    partial = outpath.with_name(outpath.name + '.partial')
    result = {'key': key, 'path': str(outpath), 'groups': {}}
    with h5py.File(partial, 'w') as f:
        f.attrs.update({'Year': int(key[:4]), 'Month': int(key[4:6]), 'UTC_Hour': int(key[6:]),
                        'Units': 'K', 'Protocol_Hash': PROTOCOL_HASH,
                        'Input_Signature': signature(sources), 'Created_UTC': now(),
                        'Scale_Factor': 1.0, 'Minimum_Observations': 1,
                        'Valid_K_Range': '[250,350]', 'EPSG': 4326,
                        'GeoTransform': grid['geotransform'], 'Projection': grid['crs_wkt'],
                        'Protocol_JSON': json.dumps(PROTOCOL, sort_keys=True)})
        for name, acc in accumulators.items():
            g = f.create_group(name)
            valid = acc.count > 0
            mean = np.full(acc.total.shape, np.nan, dtype=np.float32)
            np.divide(acc.total, acc.count[None, :, :], out=mean,
                      where=valid[None, :, :], casting='unsafe')
            options = {'compression': 'gzip', 'compression_opts': 1, 'shuffle': True}
            d = g.create_dataset('mean', data=mean, **options)
            bands = PAIRED_BANDS if name.startswith('PAIRED_') else COMPONENTS if name.startswith('LSCT') else ['bulk_lst']
            d.attrs.update({'Units': 'K', 'Scale_Factor': 1.0,
                            'Band_Names': json.dumps(bands), 'Missing_Value': np.nan,
                            'Description': 'Monthly mean at the stated UTC hour'})
            g.create_dataset('valid_count', data=acc.count, **options)
            flags = np.zeros(acc.count.shape, dtype=np.uint8)
            flags[~valid] = 1
            flags[(acc.count > 0) & (acc.count < 3)] = 2
            q = g.create_dataset('quality_flag', data=flags, **options)
            q.attrs['Definitions'] = '1=no valid acquisition; 2=one or two valid acquisitions (mean retained)'
            g.attrs['Source_Acquisition_Count'] = len(acc.acquisitions)
            g.attrs['Acquisition_Timestamps_UTC'] = json.dumps(acc.acquisitions)
            result['groups'][name] = {
                'source_acquisitions': len(acc.acquisitions), 'valid_pixels': int(valid.sum()),
                'min_valid_count': int(acc.count[valid].min()) if valid.any() else 0,
                'max_valid_count': int(acc.count.max()),
                'valid_pixel_acquisitions': int(acc.count.sum(dtype=np.uint64))}
            del mean, flags
        f.create_dataset('source_manifest_json', data=json.dumps(sources, sort_keys=True),
                         dtype=h5py.string_dtype('utf-8'))
        f.flush()
    with h5py.File(partial, 'r') as f:
        for name in accumulators:
            assert f[name]['mean'].shape[1:] == f[name]['valid_count'].shape
            assert f[name]['mean'].attrs['Units'] == 'K'
    os.replace(partial, outpath)
    result['bytes'] = outpath.stat().st_size
    return result


def verify_output(path, positions=None):
    """Independent scalar reconstruction, without using the accumulator code."""
    with h5py.File(path, 'r') as f:
        sources = json.loads(f['source_manifest_json'][()].decode())
        shape = next(f[g]['valid_count'].shape for g in f if isinstance(f[g], h5py.Group))
        if positions is None:
            # Includes ocean/missing pixels and populated Europe/Africa grid cells.
            positions = [(0, 0), (3332, 2632), (550, 1600), (1000, 1000),
                         (1100, 850), (1500, 1200), (1800, 1200), (1900, 1100),
                         (2200, 1300), (2500, 1800)]
            positions = [(y, x) for y, x in positions if y < shape[0] and x < shape[1]]
        samples = defaultdict(dict)
        for name, mapping in sources.items():
            for stamp, record in mapping.items():
                values = []
                if name.startswith('LSCT'):
                    with h5py.File(record['path'], 'r') as src:
                        d = src['data']
                        for y, x in positions:
                            raw = [int(v) for v in d[:, y, x]]
                            temp = [v / float(d.attrs['Scale_Factor']) for v in raw]
                            values.append(temp if all(v != 0 and 250 <= t <= 350 for v, t in zip(raw, temp)) else None)
                else:
                    with rasterio.open(record['path']) as src:
                        for y, x in positions:
                            raw = int(src.read(1, window=Window(x, y, 1, 1))[0, 0])
                            signed = raw - 65536 if raw >= 32768 else raw
                            temp = signed / 100.0 + 273.15
                            values.append([temp] if raw != 0 and 250 <= temp <= 350 else None)
                samples[name][stamp] = values
        checked = 0
        informative = 0
        for name in f:
            if not isinstance(f[name], h5py.Group):
                continue
            names = [name] if not name.startswith('PAIRED_') else [name.removeprefix('PAIRED_'), 'MSG_EURO', 'MSG_IODC']
            stamps = set.intersection(*(set(samples[n]) for n in names))
            for index, (y, x) in enumerate(positions):
                vals = []
                for stamp in sorted(stamps):
                    selected = [samples[n][stamp][index] for n in names]
                    if all(v is not None for v in selected):
                        vals.append([a for v in selected for a in v])
                count = int(f[name]['valid_count'][y, x])
                assert count == len(vals), (name, (y, x), count, len(vals))
                got = f[name]['mean'][:, y, x]
                if vals:
                    expected = [math.fsum(v[b] for v in vals) / len(vals) for b in range(len(vals[0]))]
                    assert np.allclose(got, expected, rtol=0, atol=4e-5), (name, (y, x), got, expected)
                    informative += 1
                else:
                    assert np.isnan(got).all()
                assert int(f[name]['quality_flag'][y, x]) == (1 if not vals else 2 if len(vals) < 3 else 0)
                checked += 1
    return {'path': str(path), 'pixel_group_checks': checked,
            'nonempty_checks': informative, 'mean_tolerance_k': 4e-5, 'passed': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-root', type=Path, default=Path('E:/PRODUCTS'))
    parser.add_argument('--output-root', type=Path, default=Path('E:/PRODUCTS/MONTHLY_COMPOSITES'))
    parser.add_argument('--inventory-only', action='store_true')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--priority', default='20180112')
    parser.add_argument('--verify-output', type=Path)
    args = parser.parse_args()
    if args.verify_output:
        print(json.dumps(verify_output(args.verify_output), indent=2))
        return
    args.output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_root / 'input_manifest.json'
    if args.inventory_only or not manifest_path.exists():
        manifest = inventory(args.input_root, args.output_root)
    else:
        manifest = json.loads(manifest_path.read_text(encoding='utf8'))
        assert manifest['protocol_hash'] == PROTOCOL_HASH
        assert Path(manifest['input_root']).resolve() == args.input_root.resolve()
    print(json.dumps({'job_groups': len(manifest['jobs']), 'sources': manifest['summary']}, indent=2), flush=True)
    if args.inventory_only:
        return
    lock = args.output_root / 'run.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode());os.close(fd)
    state = {'pid': os.getpid(), 'status': 'running', 'started_utc': now(),
             'total': len(manifest['jobs']), 'completed': 0, 'failed': 0,
             'protocol_hash': PROTOCOL_HASH, 'current': None}
    status_path = args.output_root / 'status.json'
    events = args.output_root / 'completed.jsonl'
    failures = []
    processed = 0
    keys = list(manifest['jobs'])
    if args.priority in keys:
        keys.remove(args.priority);keys.insert(0, args.priority)
    try:
        for key in keys:
            sources = manifest['jobs'][key]
            outpath = args.output_root / key[:4] / f'MSG_MONTHLY_{key[:6]}_UTC{key[6:]}.h5'
            if outpath.exists():
                with h5py.File(outpath, 'r') as f:
                    if f.attrs.get('Protocol_Hash') == PROTOCOL_HASH and f.attrs.get('Input_Signature') == signature(sources):
                        state['completed'] += 1
                        continue
            state['current'] = {'key': key, 'stage': 'computing', 'input_dates_done': 0}
            atomic_json(status_path, state)
            start = time.monotonic()
            def update(done, total, stamp):
                state['current'].update(input_dates_done=done, input_dates_total=total, stamp=stamp)
                state['updated_utc'] = now()
                atomic_json(status_path, state)
            try:
                result = process_job(key, sources, outpath, update)
                result.update(elapsed_seconds=round(time.monotonic()-start, 2), finished_utc=now())
                with events.open('a', encoding='utf8') as log:
                    log.write(json.dumps(result, ensure_ascii=False) + '\n')
                state['completed'] += 1
                print(f"DONE {key} groups={list(result['groups'])} seconds={result['elapsed_seconds']} bytes={result['bytes']}", flush=True)
            except Exception:
                error = {'key': key, 'error': traceback.format_exc(), 'utc': now()}
                failures.append(error);state['failed'] += 1
                atomic_json(args.output_root / 'failures.json', failures)
                print('FAILED '+json.dumps(error), flush=True)
            processed += 1
            atomic_json(status_path, state)
            if args.limit and processed >= args.limit:
                state['status'] = 'pilot_complete' if not failures else 'pilot_failed'
                break
        else:
            state['status'] = 'complete' if not failures else 'complete_with_errors'
        state['finished_utc'] = now();state['current'] = None
        atomic_json(status_path, state)
    finally:
        lock.unlink(missing_ok=True)
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
