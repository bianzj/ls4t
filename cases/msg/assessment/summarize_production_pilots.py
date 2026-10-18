"""Compare isolated retrieval experiments without modifying archived products."""
from pathlib import Path
import argparse
import hashlib
import json

import h5py
import numpy as np

BANDS = ('background_soil', 'canopy', 'sunlit_soil', 'shaded_soil')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def output_from_report(path):
    r = json.loads(path.read_text(encoding='utf-8'))
    assert r['status'] == 'completed', path
    p = Path(r['output'])
    assert sha256(p) == r['output_sha256'], p
    return p, r


def compare(candidate, reference):
    with h5py.File(candidate) as f, h5py.File(reference) as g:
        a, b = f['data'][:], g['data'][:]
    assert a.shape == b.shape and a.shape[0] == 4
    va, vb = np.all(a > 0, axis=0), np.all(b > 0, axis=0)
    common, union = va & vb, va | vb
    delta_codes = a[:, common].astype(np.int32) - b[:, common].astype(np.int32)
    changed = np.any(delta_codes != 0, axis=0)
    result = {
        'candidate_valid': int(va.sum()), 'reference_valid': int(vb.sum()),
        'common_valid': int(common.sum()), 'union_valid': int(union.sum()),
        'gained': int((va & ~vb).sum()), 'lost': int((vb & ~va).sum()),
        'net_valid_change_percent_of_reference': float(100 * (va.sum() - vb.sum()) / vb.sum()),
        'changed_common_any_band': int(changed.sum()),
        'identical_common_all_bands_percent': float(100 * (~changed).mean()),
        'array_equal': bool(np.array_equal(a, b)),
        'common_pixels_any_band_abs_change_above_K': {
            str(t): int(np.any(np.abs(delta_codes) > round(t * 100), axis=0).sum())
            for t in [.1, .5, 1, 5, 10]},
        'bands': {}
    }
    for i, name in enumerate(BANDS):
        d = delta_codes[i].astype(np.float64) / 100
        result['bands'][name] = {
            'bias_K': float(d.mean()), 'mae_K': float(np.abs(d).mean()),
            'rmse_K': float(np.sqrt(np.mean(d ** 2))),
            'p95_abs_K': float(np.quantile(np.abs(d), .95)),
            'max_abs_K': float(np.abs(d).max())}
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--previous', type=Path, required=True)
    args = p.parse_args()
    result = {'scenes': {}, 'note': 'Comparisons are signed vs same-runtime baseline; not temperature accuracy.'}
    for stamp, folder in [(s, args.root/s) for s in ['201801151000', '201808151300', '202512311000']] + [('202512311600', args.previous)]:
        baseline, br = output_from_report(folder/'baseline/report.json')
        signed, sr = output_from_report(folder/'signed/report.json')
        assert br['source_sha256'] == sr['source_sha256']
        item = {'signed_vs_baseline': compare(signed, baseline),
                'baseline_output_sha256': br['output_sha256'],
                'signed_output_sha256': sr['output_sha256']}
        for key in ['daylight', 'joint_update_temperature_change_K']:
            if key in sr:
                item[key] = sr[key]
        daylight_report = args.root/stamp/'signed_daylight/report.json'
        if daylight_report.exists():
            day, dr = output_from_report(daylight_report)
            item['explicit_daylight_vs_signed'] = compare(day, signed)
            item['explicit_daylight_output_diagnostics'] = dr['daylight']
        result['scenes'][stamp] = item
        print(stamp, json.dumps({k:v for k,v in item['signed_vs_baseline'].items() if k != 'bands'}), flush=True)
    path = args.root/'pilot_comparison_summary.json'
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(path)


if __name__ == '__main__':
    main()
