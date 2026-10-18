"""Complete 2017 monthly exports from local, audited source acquisitions."""
from pathlib import Path
import json
import os
import time

import h5py

from export_monthly_hour_compatible import FOLDER, SOURCES, layout, export_one
from msg_monthly_composites import atomic_json, process_job, signature, verify_output
from run_single_scene_windows import sha256


def main():
    product_root = Path('E:/PRODUCTS')
    composite_root = product_root / 'MONTHLY_COMPOSITES'
    report_root = Path('E:/EXPERIMENTS/LSCT_2017_COMPLETION')
    report_root.mkdir(parents=True, exist_ok=True)
    lock = report_root / 'run.lock'
    handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(handle, str(os.getpid()).encode()); os.close(handle)
    state = {'status': 'running', 'pid': os.getpid(), 'exports': [], 'errors': [],
             'start_year': 2017, 'LSCT_local_first_date': '2017-08-03',
             'unavailable_LSCT_IODC_months': ['2017-%02d' % n for n in range(1, 8)]}
    report = report_root / 'monthly_completion.json'
    try:
        manifest_path = composite_root / 'input_manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        # The only repaired acquisition was the unreadable 2017-06-11 EURO TIFF.
        repair = json.loads((report_root / 'projection_repair.json').read_text(encoding='utf-8-sig'))
        if not repair.get('installed'):
            raise RuntimeError('Install the verified native-data repair first')
        restored = Path(repair['original'])
        if sha256(restored) != repair['candidate_sha256']:
            raise RuntimeError('Repaired source fingerprint changed')
        record = manifest['jobs']['20170612']['MSG_EURO']['201706111200']
        if Path(record['path']).resolve() != restored.resolve():
            raise ValueError('Unexpected source record')
        record.update(bytes=restored.stat().st_size, mtime_ns=restored.stat().st_mtime_ns)
        manifest['repair_201706111200'] = {'report': str(report_root / 'projection_repair.json'),
                                         'source_sha256': repair['candidate_sha256']}
        atomic_json(manifest_path, manifest)
        key = '20170612'
        destination = composite_root / '2017' / 'MSG_MONTHLY_201706_UTC12.h5'
        if destination.exists():
            with h5py.File(destination) as f:
                if f.attrs['Input_Signature'] != signature(manifest['jobs'][key]):
                    raise RuntimeError('Existing repaired month has another input signature')
        else:
            print('COMPUTING repaired June 2017 at 12 UTC', flush=True)
            process_job(key, manifest['jobs'][key], destination)
        state['repaired_month_validation'] = verify_output(destination)
        schema = layout(product_root / 'LSCT/MLST_COMPONENT' / FOLDER / 'MLST_MONTH_201801_HH12.h5')
        jobs = {k: v for k, v in manifest['jobs'].items() if k.startswith('2017')}
        state['expected_exports'] = {group: sum(group in s for s in jobs.values()) for group in SOURCES}
        state['previous_2018_2025'] = {
            group: {p.name: [p.stat().st_size, p.stat().st_mtime_ns]
                    for p in (product_root / rel / FOLDER).glob('MLST_MONTH_*.h5')
                    if not p.name.startswith('MLST_MONTH_2017')}
            for group, rel in SOURCES.items()}
        atomic_json(report, state)
        for key, sources in sorted(jobs.items()):
            source = composite_root / '2017' / f'MSG_MONTHLY_{key[:6]}_UTC{key[6:]}.h5'
            if not source.is_file():
                raise FileNotFoundError(source)
            for group, relative in SOURCES.items():
                if group not in sources:
                    continue
                destination = product_root / relative / FOLDER / f'MLST_MONTH_{key[:6]}_HH{key[6:]}.h5'
                reference = product_root / 'LSCT/MLST_COMPONENT' / FOLDER / 'MLST_MONTH_201801_HH12.h5'
                created = export_one(source, group, destination, schema, reference)
                state['exports'].append({'key': key, 'group': group, 'path': str(destination),
                                         'created': created, 'sha256': sha256(destination)})
                print(f'EXPORTED {len(state["exports"])} {key} {group}', flush=True)
                atomic_json(report, state)
        state['export_counts'] = {g: sum(x['group'] == g for x in state['exports']) for g in SOURCES}
        assert state['export_counts'] == state['expected_exports']
        for group, original in state['previous_2018_2025'].items():
            directory = product_root / SOURCES[group] / FOLDER
            actual = {p.name: [p.stat().st_size, p.stat().st_mtime_ns]
                      for p in directory.glob('MLST_MONTH_*.h5') if not p.name.startswith('MLST_MONTH_2017')}
            assert actual == original, f'Other years changed: {group}'
        state['existing_other_years_unchanged'] = True
        state['status'] = 'complete'
        atomic_json(report, state)
        print(json.dumps({'status': state['status'], 'counts': state['export_counts']}, indent=2), flush=True)
    except Exception as error:
        state['status'] = 'failed'; state['errors'].append(str(error)); atomic_json(report, state)
        raise
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
