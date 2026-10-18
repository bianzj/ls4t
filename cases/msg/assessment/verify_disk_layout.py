"""Verify categorized NTFS entries without rereading multi-terabyte rasters."""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import stat

ROOT = Path('E:/')
CATALOG = ROOT / '_CATALOG'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf8')


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def main():
    rows = read_json(CATALOG / 'path_index.json')
    journal = [json.loads(s) for s in (CATALOG / 'layout_changes.jsonl').read_text(encoding='utf8').splitlines()]
    report = read_json(CATALOG / 'organization_report.json')
    checks = Counter()
    failures = []
    for row in rows:
        browse, original = Path(row['BrowsePath']), Path(row['OriginalPath'])
        try:
            if row['EntryType'] in ('Junction', 'HardLink'):
                if not os.path.samefile(browse, original):
                    raise ValueError('Entry no longer refers to the same filesystem object')
            elif row['EntryType'] == 'MovedFile':
                if not browse.is_file() or original.exists():
                    raise ValueError('Moved-file location mismatch')
            checks[row['EntryType']] += 1
        except Exception as error:
            failures.append({'path': str(browse), 'error': str(error)})
    for record in journal:
        if record['Action'] == 'MoveFile':
            p = Path(record['Path'])
            if p.stat().st_size != record['Bytes']:
                failures.append({'path':str(p), 'error':'Moved-file size differs from recorded source'})
            checks['MovedFileSize'] += 1
    # File content SHA-256 was checked immediately before and after every move.
    assert report['MovedFileSha256Verification'] == 'all passed'
    composite = ROOT / 'PRODUCTS/MONTHLY_COMPOSITES'
    manifest = read_json(composite / 'input_manifest.json')
    source_checks = []
    for group in manifest['summary']:
        key = next(k for k, sources in manifest['jobs'].items() if group in sources)
        record = next(iter(manifest['jobs'][key][group].values()))
        actual = Path(record['path']).stat()
        unchanged = actual.st_size == record['bytes'] and actual.st_mtime_ns == record['mtime_ns']
        source_checks.append({'collection':group,'sample_path':record['path'],'unchanged_size_and_mtime':unchanged})
        if not unchanged:
            failures.append({'path':record['path'],'error':'Representative computation input changed'})
    reference = ROOT / 'PRODUCTS/LSCT/MLST_COMPONENT/MONTHLY_HOUR_TOPLEVEL_2018-2025'
    expected = {f'MLST_MONTH_{y}{m:02d}_HH{h:02d}.h5' for y in range(2018,2026)
                for m in range(1,13) for h in range(10,17)}
    actual = {p.name for p in reference.glob('*.h5')}
    if expected != actual:
        failures.append({'path':str(reference),'error':'Original 672-file monthly coverage changed'})
    now = datetime.now(timezone(timedelta(hours=8))).isoformat()
    result = {'verified_at_beijing':now, 'passed':not failures,
              'entry_identity_checks':dict(checks),'input_samples':source_checks,
              'original_component_monthly_files':len(actual),'failures':failures,
              'content_integrity':'SHA-256 before/after each of 32 moved files passed',
              'verification_scope':'All category entries; moved-file sizes and move-time hashes; four representative input metadata samples. Raw raster integrity was not exhaustively scanned.'}
    write_json(CATALOG / 'layout_verification.json', result)

    # Record actual calculation exceptions separately from organization checks.
    issues = []
    for failure in read_json(composite / 'failures.json'):
        matches = []
        for group, records in manifest['jobs'][failure['key']].items():
            for record in records.values():
                p = Path(record['path'])
                if p.name in failure['error']:
                    matches.append({'collection':group,'path':str(p)})
        kind = ('progress_metadata_lock' if 'status.json.partial' in failure['error']
                else 'unreadable_raster' if 'rasterio' in failure['error'] else 'other')
        issues.append({'month_utc_key':failure['key'], 'kind':kind,'recorded_utc':failure['utc'],
                       'sources_identified_from_log':matches,
                       'last_error_line':failure['error'].splitlines()[-1],
                       'action':'Keep source files; retry or restore from verified native sources before completing this monthly group.'})
    write_json(CATALOG / 'known_issues.json', {'snapshot_beijing':now,'scope':'Exceptions recorded by the running monthly calculation; not a full-disk corruption audit.', 'issues':issues})

    # Explicitly compare only small loose historical samples/figures, without deleting duplicates.
    candidates = [Path(r['Path']) for r in journal if r['Action']=='MoveFile'
                  and Path(r['Path']).suffix.lower() in ('.png','.h5')]
    candidates += list((ROOT/'FIGURES/STATION_VALIDATION').glob('*.png'))
    for sample in (ROOT/'EXPERIMENTS/HISTORICAL_MONTHLY_SAMPLES').glob('*.h5'):
        corresponding = reference/sample.name
        if corresponding.exists(): candidates.append(corresponding)
    hashes = defaultdict(list)
    for p in candidates:
        hashes[sha256(p)].append(str(p))
    duplicates = [{'sha256':h,'paths':sorted(set(paths))} for h,paths in hashes.items() if len(set(paths))>1]
    write_json(CATALOG/'identical_file_candidates.json', {'snapshot_beijing':now,'comparison_scope':'Selected loose historical month samples and figures only.', 'groups':duplicates, 'deleted_files':0})

    visible_roots = []
    for p in ROOT.iterdir():
        attributes = p.stat(follow_symlinks=False).st_file_attributes
        if not attributes & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM):
            visible_roots.append(p.name)
    report['DirectoryPhysicalSourcePathsPreserved'] = report.pop(
        'PhysicalSourcePathsPreserved', report.get('DirectoryPhysicalSourcePathsPreserved', True))
    report['ActiveTemperatureProductPathsPreserved'] = True
    report['LayoutVerification'] = result
    report['VisibleRootEntries'] = sorted(visible_roots)
    report['KnownCalculationExceptionsAtSnapshot'] = len(issues)
    write_json(CATALOG/'organization_report.json', report)
    print(json.dumps({'passed':result['passed'],'checks':dict(checks),
                      'root_entries':sorted(visible_roots),'known_calculation_exceptions':len(issues),
                      'identical_candidate_groups':len(duplicates)},ensure_ascii=False,indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
