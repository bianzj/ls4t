"""Export bulk LST monthly products in the existing 12 UTC LSCT file layout.

The maintained composites are already in kelvin. This step only changes the
container layout and stored scale to K*100; it does not recompute temperatures.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import time

import h5py
import numpy as np

from msg_monthly_composites import atomic_json, now, COMPONENTS

FORMAT_VERSION = 1
DATASET = 'Monthly_Hour_Mean_LST'
SOURCES = {
    'MSG_EURO': 'MSG/MLST',
    'MSG_IODC': 'MSG-IODC/MLST',
    'LSCT': 'LSCT/MLST_COMPONENT',
}
FOLDER = 'MONTHLY_HOUR_TOPLEVEL_2017-2025'


def read_json_retry(path):
    for attempt in range(40):
        try:
            return json.loads(path.read_text(encoding='utf8'))
        except (PermissionError, json.JSONDecodeError):
            if attempt == 39:
                raise
            time.sleep(0.05)


def pid_exists(pid):
    # OpenProcess queries the worker without sending a signal on Windows.
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, int(pid))
    if not handle:
        return ctypes.get_last_error() == 5
    try:
        code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value == 259
    finally:
        kernel.CloseHandle(handle)


def layout(reference):
    with h5py.File(reference, 'r') as f:
        d = f[DATASET]
        if d.ndim != 3 or d.shape[0] != 4 or d.dtype != np.dtype('float32'):
            raise ValueError(f'Unexpected reference layout: {reference}')
        return {'shape': d.shape[1:], 'chunks': d.chunks,
                'compression': d.compression, 'compression_opts': d.compression_opts,
                'scale': 100.0}


def export_one(source, group, destination, schema, reference):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(source, 'r') as f:
        if group not in f:
            raise ValueError(f'Missing source group: {source}: {group}')
        year, month, hour = (int(f.attrs[k]) for k in ('Year', 'Month', 'UTC_Hour'))
        d = f[group + '/mean']
        expected_bands = 4 if group == 'LSCT' else 1
        if (d.shape != (expected_bands, *schema['shape']) or d.attrs['Units'] != 'K'
                or float(d.attrs['Scale_Factor']) != 1.0):
            raise ValueError(f'Unexpected LST shape/encoding: {source}: {group}')
        signature = str(f.attrs['Input_Signature'])
        protocol = str(f.attrs['Protocol_Hash'])
        if destination.exists():
            with h5py.File(destination, 'r') as old:
                if (old.attrs.get('Source_Input_Signature') == signature
                        and old.attrs.get('Source_Protocol_Hash') == protocol
                        and old.attrs.get('Format_Version') == FORMAT_VERSION
                        and old[DATASET].shape == d.shape):
                    return False
            raise FileExistsError(f'Refusing to overwrite an incompatible product: {destination}')
        partial = destination.with_name(destination.name + '.partial')
        with h5py.File(partial, 'w') as out:
            dst = out.create_dataset(DATASET, shape=d.shape, dtype='float32',
                                     chunks=schema['chunks'],
                                     compression=schema['compression'],
                                     compression_opts=schema['compression_opts'])
            for row in range(0, d.shape[1], 256):
                block = d[:, row:row+256, :]
                dst[:, row:row+256, :] = block * np.float32(schema['scale'])
            out.attrs.update({
                'Year': year, 'Month': month, 'Hour': hour,
                'Valid_K_Range': '[25000.0,35000.0]',
                'Effective_Days': int(f[group].attrs['Source_Acquisition_Count']),
                'Units': 'K', 'Scale_Factor': 100.0,
                'Stored_Value_Convention': 'stored_value = kelvin * Scale_Factor',
                'Missing_Value': np.nan, 'Band_Names': json.dumps(COMPONENTS if group == 'LSCT' else ['bulk_lst']),
                'GeoTransform': f.attrs['GeoTransform'], 'Projection': f.attrs['Projection'],
                'EPSG': int(f.attrs['EPSG']), 'Source_Group': group,
                'Source_Monthly_Composite': str(source),
                'Valid_Count_Dataset': group + '/valid_count',
                'Quality_Flag_Dataset': group + '/quality_flag',
                'Source_Input_Signature': signature, 'Source_Protocol_Hash': protocol,
                'Reference_12UTC_File': str(reference), 'Format_Version': FORMAT_VERSION,
                'Created_UTC': now(),
            })
            dst.attrs.update({'Units': 'K', 'Scale_Factor': 100.0,
                              'Band_Names': '["bulk_lst"]', 'Missing_Value': np.nan})
        # Validate every exported value and missing pixel before publication.
        with h5py.File(partial, 'r') as out:
            assert set(out) == {DATASET}
            assert out[DATASET].dtype == np.dtype('float32')
            for row in range(0, d.shape[1], 256):
                original = d[:, row:row+256, :]
                actual = out[DATASET][:, row:row+256, :]
                np.testing.assert_array_equal(actual, original * np.float32(100))
                recovered = actual.astype(np.float64) / 100
                valid = np.isfinite(original)
                if valid.any():
                    assert np.max(np.abs(recovered[valid] - original[valid])) < 0.00004
        os.replace(partial, destination)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--product-root', type=Path, default=Path('E:/PRODUCTS'))
    parser.add_argument('--composite-root', type=Path, default=Path('E:/PRODUCTS/MONTHLY_COMPOSITES'))
    parser.add_argument('--key', help='Export one YYYYMMHH pilot group')
    parser.add_argument('--start-year', type=int, default=2017)
    parser.add_argument('--end-year', type=int, default=2025)
    parser.add_argument('--groups', nargs='+', choices=list(SOURCES), default=['MSG_EURO', 'MSG_IODC'])
    parser.add_argument('--follow', action='store_true', help='Follow the existing calculation worker')
    args = parser.parse_args()
    selected_sources = {g: SOURCES[g] for g in args.groups}
    reference = args.product_root / 'LSCT/MLST_COMPONENT' / FOLDER / 'MLST_MONTH_201801_HH12.h5'
    schema = layout(reference)
    manifest = read_json_retry(args.composite_root / 'input_manifest.json')
    # The lock PID is stable while the main worker runs. Avoid repeatedly
    # opening its frequently replaced progress file on Windows.
    parent_lock = args.composite_root / 'run.lock'
    parent_pid = int(parent_lock.read_text(encoding='utf8')) if parent_lock.exists() else None
    jobs = {k: v for k, v in manifest['jobs'].items() if args.start_year <= int(k[:4]) <= args.end_year}
    if args.key:
        jobs = {args.key: jobs[args.key]}
    expected = {g: sum(g in v for v in jobs.values()) for g in selected_sources}
    state_path = args.composite_root / 'compatible_export_status.json'
    lock = args.composite_root / 'compatible_export.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode()); os.close(fd)
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    state = {'pid': os.getpid(), 'status': 'running', 'started_utc': now(),
             'reference_12utc': str(reference), 'script_sha256': script_hash,
             'expected': expected, 'exported': {g: 0 for g in selected_sources}, 'errors': {},
             'destinations': {g: str(args.product_root / p / FOLDER) for g,p in selected_sources.items()},
             'current': None}
    done = set()
    try:
        for g, relative in selected_sources.items():
            outroot = args.product_root / relative / FOLDER
            outroot.mkdir(parents=True, exist_ok=True)
            (outroot / 'README.md').write_text(
                '# Monthly temperatures at fixed UTC hours\n\n'
                f'Source collection: {g}. Product period starts in 2017; UTC hours: 10–16.\n'
                'Local LSCT and IODC inputs begin on 2017-08-03; January–July 2017 are unavailable for these collections.\n'
                'Files use the existing LSCT 12 UTC layout: '
                '`MLST_MONTH_YYYYMM_HHhh.h5`, dataset `Monthly_Hour_Mean_LST`, '
                f'float32 with shape ({4 if g == "LSCT" else 1}, 3333, 2633), gzip compression.\n\n'
                'Stored values are kelvin × 100; divide by 100 to recover K. '
                'NaN indicates no valid acquisition. `Effective_Days` counts input '
                'acquisitions, not valid days at every pixel. Per-pixel valid counts '
                'and quality flags remain in the corresponding maintained '
                '`E:\\PRODUCTS\\MONTHLY_COMPOSITES` file, identified in each file attribute.\n\n'
                'These are fixed-hour monthly means, not 24-hour averages. '
                'The original component monthly files are retained. This export '
                'changes layout and storage scale only.\n', encoding='utf8')
        while True:
            for key, sources in jobs.items():
                source = args.composite_root / key[:4] / f'MSG_MONTHLY_{key[:6]}_UTC{key[6:]}.h5'
                if not source.exists():
                    continue
                for group, relative in selected_sources.items():
                    token = key + ':' + group
                    if group not in sources or token in done or token in state['errors']:
                        continue
                    destination = args.product_root / relative / FOLDER / f'MLST_MONTH_{key[:6]}_HH{key[6:]}.h5'
                    state['current'] = token; state['updated_utc'] = now()
                    atomic_json(state_path, state)
                    try:
                        created = export_one(source, group, destination, schema, reference)
                        done.add(token); state['exported'][group] += 1
                        print(('EXPORTED ' if created else 'VERIFIED_EXISTING ') + str(destination), flush=True)
                    except Exception as error:
                        state['errors'][token] = str(error)
                        print('FAILED ' + token + ': ' + str(error), flush=True)
            state['current'] = None; state['updated_utc'] = now()
            atomic_json(state_path, state)
            if not args.follow:
                state['status'] = 'snapshot_complete' if not state['errors'] else 'snapshot_with_errors'
                break
            if parent_pid is None or not pid_exists(parent_pid):
                parent = read_json_retry(args.composite_root / 'status.json')
                # One final scan captures a file published after the preceding scan.
                if state.get('final_scan'):
                    complete = all(state['exported'][g] == expected[g] for g in selected_sources)
                    state['status'] = 'complete' if complete and not state['errors'] else 'incomplete'
                    state['calculation_status'] = parent['status']
                    break
                state['final_scan'] = True
                continue
            time.sleep(5)
        state['finished_utc'] = now()
        atomic_json(state_path, state)
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
