"""Replay the maintained 5x5 station entry and compare its archived records.

This measures reproduction agreement, not a percentage of physical accuracy.
The default period includes 2017; local missing years are reported explicitly.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import difflib
import json
from pathlib import Path
import re
import sys
import time

import numpy as np
import pandas as pd
from run_single_scene_windows import Tee, sha256

COMPONENTS = ['T_Soil', 'T_Vegetation', 'T_Sunlit_Soil', 'T_Shaded_Soil']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--site', required=True)
    p.add_argument('--start', default='2017-01-01')
    p.add_argument('--end', default='2026-01-01', help='Exclusive date')
    p.add_argument('--data-root', type=Path, default=Path('E:/'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--hotspot', type=float, help='Explicit hotspot override for a recorded parameter experiment')
    args = p.parse_args()
    if args.hotspot is not None and (not np.isfinite(args.hotspot) or args.hotspot <= 0):
        raise ValueError('hotspot must be finite and positive')
    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end)
    if start >= end:
        raise ValueError('start must precede end')
    repo = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo))
    source = Path(__file__).with_name('msg_lsct3.2-iter-site-cons-ig-center.py')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    product = out / 'station_predictions.csv'
    if product.exists():
        raise FileExistsError(f'Existing test output: {product}')
    site_root = args.data_root / 'PRODUCTS/SITE' / args.site
    if not site_root.is_dir():
        raise FileNotFoundError(site_root)
    selected = [x for x in site_root.glob('*/*/*') if x.is_dir() and
                start.isoformat() <= '/'.join(x.parts[-3:]).replace('/', '-') < end.isoformat()]
    if not selected:
        raise ValueError('No local station input dates in the requested period')
    manifest = {str(x): {'bytes': x.stat().st_size, 'sha256': sha256(x)}
                for d in [site_root / 'static', *sorted(selected)]
                for x in sorted(d.glob('*.tif'))}
    code = source.read_text(encoding='utf-8')
    effective = code
    replacements = {
        'indir': repr(args.data_root.resolve().as_posix()),
        'infile_sites': repr((out / 'site.csv').as_posix()),
        'outfile_csv': repr(product.as_posix()),
    }
    if args.hotspot is not None:
        replacements['hspot_val'] = repr(args.hotspot)
    for name, value in replacements.items():
        effective, n = re.subn(rf'^{name} = .+$', f'{name} = {value}', effective, count=1, flags=re.M)
        if n != 1:
            raise ValueError(f'Cannot override {name}')
    effective, n = re.subn(r'for kyear in range\(\d{4},\s*\d{4}\):',
                          f'for kyear in range({start.year}, {end.year + 1}):', effective, count=1)
    if n != 1:
        raise ValueError('Cannot restrict years')
    marker = '        for date_dir in sorted(date_folders):'
    if effective.count(marker) != 1:
        raise ValueError('Source date loop changed')
    effective = effective.replace(marker, marker + '\n' +
        '            _test_date = "-".join(Path(date_dir).parts[-3:])\n' +
        f'            if not ({start.isoformat()!r} <= _test_date < {end.isoformat()!r}):\n' +
        '                continue', 1)
    (out / 'site.csv').write_text(args.site + ',0,0\n', encoding='utf-8')
    # Coordinates in this inventory are unused: the entry reads cached angles.
    (out / 'runtime_changes.diff').write_text(''.join(difflib.unified_diff(
        code.splitlines(True), effective.splitlines(True),
        fromfile=str(source), tofile='single_station_runtime')), encoding='utf-8')
    report = {
        'status': 'running', 'site': args.site, 'start': args.start, 'end_exclusive': args.end,
        'executed_UTC': dt.datetime.now(dt.timezone.utc).isoformat(),
        'source': str(source), 'source_sha256': sha256(source),
        'runner_sha256': sha256(__file__), 'archive': str(args.archive),
        'archive_sha256': sha256(args.archive), 'inputs': manifest,
        'input_date_count': len(selected),
        'parameters': {'lambda': 1000, 'hspot': .25 if args.hotspot is None else args.hotspot,
                       'dif_radiance': 3, 'hours_UTC': list(range(9, 17))},
        'criterion': 'Four stored component values equal at 0.01 K precision, divided by union of predicted and archived timestamps.',
        'scientific_scope': 'Historical station algorithm; not numerically equivalent to the full regional retrieval.',
    }
    report_path = out / 'report.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    with (out / 'run.log').open('w', encoding='utf-8') as log:
        with contextlib.redirect_stdout(Tee(sys.stdout, log)), contextlib.redirect_stderr(Tee(sys.stderr, log)):
            begin = time.monotonic()
            exec(compile(effective, str(source), 'exec'), {'__name__': '__main__', '__file__': str(source), 'Path': Path})
            report['retrieval_elapsed_seconds'] = time.monotonic() - begin
    if not product.is_file():
        raise RuntimeError('No predictions produced')
    new, old = pd.read_csv(product), pd.read_csv(args.archive)
    for frame in (new, old):
        frame['DateTime'] = frame.DateTime.astype(str)
    lo, hi = start.strftime('%Y%m%d'), end.strftime('%Y%m%d')
    old = old.loc[(old.Site == args.site) & (old.DateTime >= lo) & (old.DateTime < hi)]
    keys = ['Site', 'DateTime']
    if new.duplicated(keys).any() or old.duplicated(keys).any():
        raise ValueError('Duplicate site/timestamp records')
    pair = new.merge(old, on=keys, how='outer', suffixes=('_new', '_archive'), indicator=True, validate='one_to_one')
    shared = pair['_merge'].eq('both').to_numpy()
    identical = shared.copy()
    metrics = {}
    for band in COMPONENTS:
        delta = pair[band + '_new'] - pair[band + '_archive']
        same = delta.abs().le(1e-8).to_numpy()
        identical &= same
        metrics[band] = {'common_n': int(shared.sum()), 'exact_n': int((same & shared).sum()),
                         'rmse_K': float(np.sqrt(np.nanmean(delta.to_numpy() ** 2))),
                         'max_abs_difference_K': float(delta.abs().max())}
    pair['all_four_equal'] = identical
    pair.to_csv(out / 'archive_comparison.csv', index=False)
    report['comparison'] = {
        'new_records': len(new), 'archive_records': len(old), 'union_records': len(pair),
        'shared_records': int(shared.sum()), 'all_four_equal_records': int(identical.sum()),
        'exact_match_percent_union': float(100 * identical.sum() / len(pair)) if len(pair) else None,
        'above_99_percent': bool(identical.sum() / len(pair) > .99) if len(pair) else False,
        'new_only': int(pair['_merge'].eq('left_only').sum()),
        'archive_only': int(pair['_merge'].eq('right_only').sum()), 'bands': metrics,
    }
    report['status'] = 'completed'
    report['output_sha256'] = sha256(product)
    report['archive_unchanged'] = sha256(args.archive) == report['archive_sha256']
    report['source_unchanged'] = sha256(source) == report['source_sha256']
    assert report['archive_unchanged'] and report['source_unchanged']
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report['comparison'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
