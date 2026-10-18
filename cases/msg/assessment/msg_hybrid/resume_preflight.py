"""One actual mixed-orbit scene in the unified collection before batch resume."""
from pathlib import Path
from types import SimpleNamespace
import json

import produce_msg_ls4t as p

HERE = Path(__file__).resolve().parent


def main():
    args = SimpleNamespace(input_root=Path('E:/'), geometry_module=HERE/'msg_view_geometry.py',
        geometry_plan=HERE/'geometry_plan.json', legacy_case_root=Path('C:/work/ls4t-msg/cases/official'))
    p.assert_code_review(HERE/'independent_code_review.json', args.geometry_module, args.geometry_plan)
    identity, plan = p.build_identity(args, p.grid_info(args.input_root))
    root = p.DEFAULT_ROOT.resolve()
    config = {'input_root':str(args.input_root.resolve()), 'output':str(root), 'tile_rows':256,
              'geometry_module':str(args.geometry_module), 'geometry_plan':str(args.geometry_plan)}
    with p.production_lock(root):
        if json.loads((root/'production_identity.json').read_text(encoding='utf8')) != dict(identity, protocol=p.PROTOCOL):
            raise RuntimeError('Preflight collection identity mismatch')
        p.worker_init(config, identity, plan)
        record = p.scene_job('202012311200')
        if record['status'] not in ['written','resumed']:
            raise RuntimeError(p.json_text(record))
        record.update(preflight=True, updated_UTC=p.now())
        p.append_json(root/'scene_manifest.jsonl', record)
        p.atomic_json(HERE/'actual_preflight_scene.json', record)
        print(p.json_text(record), flush=True)


if __name__ == '__main__':
    main()
