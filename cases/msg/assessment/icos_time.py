"""Read the audited ICOS interval starts as fixed local standard time."""
from pathlib import Path
import hashlib
import json
import pandas as pd

AUDIT = Path(__file__).resolve().parent.parent / 'results/time_verification_20261010/source_time_audit.json'

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def source_contract(path):
    audit = json.loads(AUDIT.read_text(encoding='utf-8'))
    if not audit['all_icos_confirmed'] or audit.get('errors'):
        raise ValueError('The source time audit is not confirmed.')
    target = str(Path(path).resolve()).casefold()
    rows = [r for r in audit['stations'] if str(Path(r['source']).resolve()).casefold() == target]
    if len(rows) != 1:
        raise ValueError(f'No unique audited time contract for {path}; do not assume UTC.')
    row = rows[0]
    if row['uses_dst'] or row['utc_offset_hours'] not in (1, 2):
        raise ValueError('Unexpected ICOS time convention; check source metadata.')
    if not all(row[k] for k in ('coverage_agrees', 'csv_matches_frozen_manifest', 'archive_matches_provider')):
        raise ValueError('Source provenance checks have not passed.')
    manifest_path = AUDIT.parent.parent / 'production_assessment/joint_parameter_selection/input_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    expected = [v for k, v in manifest.items() if str(Path(k).resolve()).casefold() == target]
    if len(expected) != 1 or sha256_file(path) != expected[0]:
        raise ValueError(f'Source CSV changed since the time audit: {path}')
    return row

def local_interval_start_utc(values, offset_hours):
    # Fixed standard time: subtract the audited offset; never apply DST rules.
    local = pd.to_datetime(values.astype('Int64').astype(str), format='%Y%m%d%H%M', utc=True, errors='coerce')
    return local - pd.Timedelta(hours=offset_hours)

def clean_ground(path):
    contract = source_contract(path)
    g = pd.read_csv(path, usecols=['TIMESTAMP_START', 'TA', 'TS_1'], na_values=[-9999, -9999.])
    g['field_time'] = local_interval_start_utc(g.TIMESTAMP_START, contract['utc_offset_hours'])
    g = g.dropna(subset=['field_time'])
    conflicts = 0
    if g.field_time.duplicated().any():
        grouped = g.groupby('field_time')[['TA', 'TS_1']]
        counts = grouped.nunique()
        g = grouped.first()
        conflicts = int((counts > 1).any(axis=1).sum())
        g = g.mask(counts > 1).reset_index()
    g = g.sort_values('field_time')
    g.attrs['time_contract'] = contract
    return g, conflicts
