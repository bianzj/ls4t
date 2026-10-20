#!/usr/bin/env python3
"""Resume SLSTR by region and year: LST, then homogeneous components.

One damaged scene is recorded and skipped. A missing daily auxiliary input,
too many scene failures, an invalid annual report, or a failed process stops
the batch instead of silently treating an incomplete year as complete.
"""
from __future__ import annotations

import fcntl
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime

from adaptive_year_run import valid_report


os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                  PROJ_LIB='/usr/share/proj', PROJ_DATA='/usr/share/proj')


REPO = Path('/home/hero/work/ls4t')
LOG = REPO / 'cases/slstr/logs/amazon_then_europe_homogeneous'
PY = '/home/hero/anaconda3/envs/env_311/bin/python'
ADAPT = REPO / 'cases/slstr/adaptive_year_run.py'
HISTORY = LOG / 'adaptive_workers.jsonl'
METHOD = 'homogeneous_3component_bayes_map_5x5_lai_only_v5'
EXCLUSIONS = REPO / 'cases/slstr/amazon_2023_unreadable_inputs.json'
LST_MAX_SCENE_ERRORS = 20
REGIONS = (
    ('amazon', Path('/media/hero/slstr-southA-lst'), (-80., -18., -44., 12.), 'sda'),
    ('europe', Path('/media/hero/slstr-euro-lst'), (-12., 30., 42., 71.5), 'sdb'),
)


def stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec='seconds')


def report_path(region: str, year: int, stage: str) -> Path:
    if stage == 'lst' and year == 2017:
        if region == 'amazon':
            return REPO / 'cases/slstr/logs/amazon_europe_bayes3/amazon_2017_lst.json'
        return REPO / 'cases/slstr/logs/amazon_europe_lst_only/europe_2017_lst.json'
    return LOG / f'{region}_{year}_{stage}.json'


def expected_exclusions(region: str, year: int) -> list[str]:
    return (json.loads(EXCLUSIONS.read_text())['scenes']
            if (region, year) == ('amazon', 2023) else [])


def checked(path: Path, stage: str, region: str, root: Path,
            year: int, bounds: tuple[float, ...]) -> bool:
    if not valid_report(path, stage):
        return False
    try:
        data = json.loads(path.read_text())
        if (data.get('year') != year or Path(data.get('root', '')).resolve() != root.resolve()
                or data.get('bounds_wsen') != list(bounds)):
            return False
        if stage == 'lst':
            return (data.get('excluded_scenes', []) == sorted(set(expected_exclusions(region, year)))
                    and data.get('written', 0) + data.get('empty', 0)
                        + data.get('skipped', 0) == data['scenes'])
        return data.get('method') == METHOD
    except (OSError, ValueError, KeyError, TypeError):
        return False


def record(region: str, year: int, stage: str, code: int, path: Path) -> None:
    with (LOG / 'status.tsv').open('a') as handle:
        handle.write(f'{region}\t{year}\t{stage}\t{code}\t{path}\n')
        handle.flush()
        os.fsync(handle.fileno())


def run_stage(region: str, root: Path, year: int, bounds: tuple[float, ...],
              disk: str, stage: str, lst_report: Path | None = None) -> Path:
    candidate = report_path(region, year, stage)
    if checked(candidate, stage, region, root, year, bounds):
        print(f'[{stamp()}] VERIFIED {region} {year} {stage} {candidate}', flush=True)
        record(region, year, f'{stage}_verified', 0, candidate)
        return candidate
    report = LOG / f'{region}_{year}_{stage}.json'
    if stage == 'components' and lst_report is None:
        raise ValueError('components require a valid LST report')
    if stage == 'lst':
        max_scene_errors = LST_MAX_SCENE_ERRORS
    else:
        # A small fraction of scenes can lack one source view even though the
        # paired LST was made. Keep these visible without stopping a full year.
        selected = len(json.loads(lst_report.read_text())['updated_scenes'])
        max_scene_errors = min(200, max(20, math.ceil(selected * .02)))
    args = [PY, str(ADAPT), '--region', region, '--stage', stage,
            '--year', str(year), '--disk', disk, '--report', str(report),
            '--history', str(HISTORY), '--', PY, '-m',
            ('cases.slstr.slstr_lst_scene_parallel' if stage == 'lst'
             else 'cases.slstr.slstr_lsct3_bayes_scene'),
            '--root', str(root), '--year', str(year), '--bounds',
            *(str(value) for value in bounds), '--workers', '{workers}',
            '--max-scene-errors', str(max_scene_errors), '--report', str(report)]
    if stage == 'lst':
        args += ['--all-scenes', '--overwrite', '--exclude-scenes',
                 *expected_exclusions(region, year)]
    else:
        args += ['--lst-report', str(lst_report)]
    print(f'[{stamp()}] START {region} {year} {stage}', flush=True)
    code = subprocess.call(args, cwd=REPO)
    if code == 0 and not checked(report, stage, region, root, year, bounds):
        code = 3
    record(region, year, stage, code, report)
    print(f'[{stamp()}] END {region} {year} {stage} exit={code}', flush=True)
    if code:
        raise RuntimeError(f'{region} {year} {stage} failed with exit {code}; see {report}')
    return report


def main() -> int:
    LOG.mkdir(parents=True, exist_ok=True)
    with (LOG / 'run.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another Amazon/Europe batch is running', file=sys.stderr)
            return 2
        if not (LOG / 'status.tsv').exists():
            (LOG / 'status.tsv').write_text('region\tyear\tstage\texit_code\treport\n')
        for region, root, bounds, disk in REGIONS:
            for year in range(2017, 2026):
                lst = run_stage(region, root, year, bounds, disk, 'lst')
                run_stage(region, root, year, bounds, disk, 'components', lst)
        print(f'[{stamp()}] ALL REGION-YEARS COMPLETE', flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'[{stamp()}] BATCH STOPPED: {exc}', file=sys.stderr, flush=True)
        sys.exit(3)
