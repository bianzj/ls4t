"""CLI for the same backend used by the workbench; no running server required."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from base.known_inputs import run_workbench
from base.normalization.workbench import normalize_observations
from gui.workspace_tools import run_surface, run_time, run_space, run_batch


def main():
    parser = argparse.ArgumentParser(description='LS4T retrieval and normalization workspaces')
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parent/'examples/ahi_slstr/sample.json')
    parser.add_argument('--output', type=Path, help='Optional output JSON; otherwise print result to stdout')
    args = parser.parse_args()
    payload = json.loads(args.config.read_text(encoding='utf-8'))
    for obs in payload.get('observations', []):
        path = obs.get('coefficient_file')
        if path:
            given = Path(path)
            if not given.is_absolute():
                obs['coefficient_file'] = str(args.config.resolve().parent/given)
            elif not given.exists():
                # Bundled sample is portable when moved to another checkout.
                bundled = args.config.resolve().parent/given.name
                if bundled.exists(): obs['coefficient_file'] = str(bundled)
    operations = {'retrieval':run_workbench, 'surface':run_surface, 'normalization':normalize_observations,
                  'time':run_time, 'space':run_space, 'normalization-batch':run_batch}
    route = payload.get('route', 'retrieval')
    if route not in operations:
        parser.error(f'Unknown route: {route}')
    result = operations[route](payload)
    content = json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(content,encoding='utf-8')
        print(f'Result: {args.output.resolve()}')
    else:
        print(content)


if __name__ == '__main__': main()
