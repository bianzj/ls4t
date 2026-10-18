"""Real early-summer/winter and new-slot acceptance; isolated pilot directory."""
import argparse
import calendar
import json
from pathlib import Path
import produce_msg_ls4t as p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    if root.name != 'MSG_LS4T_H025_5X5_DECLARED_V1_ACCEPTANCE_20261012':
        raise ValueError('Acceptance requires its separate pilot directory')
    root.mkdir(parents=True, exist_ok=True)
    settings = argparse.Namespace(input_root=Path('E:/'), geometry_module=p.HERE/'msg_view_geometry.py',
        geometry_plan=p.HERE/'geometry_plan.json', legacy_case_root=Path('C:/work/ls4t-msg/cases/official'))
    identity, plan = p.build_identity(settings, p.grid_info(settings.input_root))
    p.atomic_json(root/'production_identity.json', dict(identity, protocol=p.PROTOCOL))
    config = {'input_root': 'E:/', 'output': str(root), 'tile_rows': 256,
              'geometry_module': str(settings.geometry_module), 'geometry_plan': str(settings.geometry_plan)}
    p.worker_init(config, identity, plan)
    records = []
    for stamp in ['201708151200', '202001151200', '202001161200', '202407151200']:
        record = p.produce_scene(stamp)
        assert record['status'] in ['written', 'resumed'], record
        record.update(updated_UTC=p.now(), run_id='declared_geometry_acceptance')
        p.append_json(root/'scene_manifest.jsonl', record)
        records.append(record)
        print('ACCEPTANCE SCENE', stamp, record['valid_pixels'], flush=True)
    for month in ['201708', '202001', '202407']:
        source = [Path(r['hdf5']) for r in records if r['timestamp'].startswith(month)]
        expected = [f'{month}{day:02d}1200' for day in range(1, calendar.monthrange(int(month[:4]), int(month[4:]))[1]+1)]
        done = {r['timestamp'] for r in records if r['timestamp'].startswith(month)}
        omitted = [{'timestamp': s, 'status': 'acceptance_not_processed'} for s in expected if s not in done]
        record = p.monthly(root, month, 12, source, expected, omitted, identity, 256)
        record.update(updated_UTC=p.now(), run_id='declared_geometry_acceptance')
        p.append_json(root/'monthly_manifest.jsonl', record)
        print('ACCEPTANCE MONTHLY', month, record['source_count'], flush=True)
    p.atomic_json(root/'acceptance_result.json', {'status': 'products_created_pending_independent_review',
        'scenes': len(records), 'monthly': 3, 'identity_hash': identity['identity_hash'],
        'not_production_counts': True})


if __name__ == '__main__':
    main()
