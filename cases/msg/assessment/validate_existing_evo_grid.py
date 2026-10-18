"""Read-only EVO regional-grid diagnostic, with independent temporal selection.

Uses existing daily components, reconciles all 35 monthly 2017 exports at a
3x3 site window, then evaluates observations and retrievals on identical times.
Station-mode estimates and residual screening never enter the primary sample.
Ground UTC and radiometric correction retain the manuscript conventions.
"""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json

import h5py
import numpy as np
import pandas as pd

BANDS = ('background_soil', 'canopy', 'sunlit_soil', 'shaded_soil')
COMPONENTS = {'sunlit_soil': ('Ts', 2), 'canopy': ('Tcrown', 1)}
C1 = 2 * 6.62607015e-34 * 299792458 ** 2
C2 = 6.62607015e-34 * 299792458 / 1.380649e-23
WAVELENGTH = 10.5e-6


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def correction(celsius):
    def planck(t):
        return C1 / (WAVELENGTH ** 5 * np.expm1(C2 / (WAVELENGTH * t)))
    r = (planck(np.asarray(celsius) + 273.15) - .015 * planck(250)) / .985
    return C2 / (WAVELENGTH * np.log1p(C1 / (WAVELENGTH ** 5 * r))) - 273.15


def score(frame):
    e = np.asarray(frame.prediction - frame.reference, dtype=float)
    if not len(e):
        return {'n': 0}
    return {'n': len(e), 'rmse_K': float(np.sqrt(np.mean(e ** 2))),
            'bias_K': float(e.mean()), 'mae_K': float(np.abs(e).mean())}


def finite_mean(a, axis):
    count = np.isfinite(a).sum(axis=axis)
    return np.divide(np.nansum(a, axis=axis), count,
                     out=np.full(count.shape, np.nan, dtype=float), where=count > 0)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    daily = Path('E:/PRODUCTS/LSCT/MLST_COMPONENT')
    monthly = Path('E:/PRODUCTS/MONTHLY/LSCT_4COMPONENTS')
    field_path = Path('E:/field/Evo-2017.csv')
    example = monthly/'MLST_MONTH_201708_HH12.h5'
    with h5py.File(example) as f:
        gt = np.asarray(f.attrs['GeoTransform'])
    lon, lat = -8.0033, 38.5411
    assert gt[2] == gt[4] == 0
    col, row = int(np.floor((lon-gt[0])/gt[1])), int(np.floor((lat-gt[3])/gt[5]))
    rows, cols = slice(row-1, row+2), slice(col-1, col+2)
    ground = pd.read_csv(field_path)
    ground['time'] = pd.to_datetime(ground.Time, format='%d/%m/%Y %H:%M', utc=True)
    ground = ground.loc[(ground.time >= '2017-08-01') & (ground.time < '2017-12-31') &
                        (ground.time.dt.minute == 0) & ground.time.dt.hour.between(10, 16),
                        ['time', 'Ts', 'Tcrown']].copy()
    if ground.duplicated('time', keep=False).any():
        for _, g in ground.loc[ground.duplicated('time', keep=False)].groupby('time'):
            assert all(g[c].nunique(dropna=False) <= 1 for c in ['Ts', 'Tcrown']), 'Conflicting ground duplicate'
        ground = ground.drop_duplicates('time')
    for c in ['Ts', 'Tcrown']:
        ground[c] = pd.to_numeric(ground[c], errors='coerce')
        ground.loc[~ground[c].between(-23.15, 76.85), c] = np.nan
        ground[c] = correction(ground[c])

    records, manifest, missing, reconciliations = [], [], [], []
    daily_by_group = {}
    for date in pd.date_range('2017-08-01', '2017-12-31', freq='D', tz='UTC'):
        for hour in range(10, 17):
            t = date + pd.Timedelta(hours=hour)
            stamp = t.strftime('%Y%m%d%H%M')
            path = daily/t.strftime('%Y/%m/%d')/f'MSG_LSCT_{stamp}.h5'
            if not path.exists():
                missing.append(str(path))
                continue
            with h5py.File(path) as f:
                d = f['data']
                np.testing.assert_allclose(d.attrs['GeoTransform'], gt, rtol=0, atol=1e-12)
                assert d.shape == (4, 3333, 2633)
                raw = d[:, rows, cols]
                scale = float(d.attrs['Scale_Factor'])
            values = raw.astype(float) / scale
            valid = np.all((raw != 0) & (values >= 250) & (values <= 350), axis=0)
            values[:, ~valid] = np.nan
            daily_by_group.setdefault((t.month, hour), []).append(values)
            st = path.stat()
            manifest.append({'path': str(path), 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns,
                             'slice_sha256': hashlib.sha256(raw.tobytes()).hexdigest()})
            centre, neighbourhood = values[:, 1, 1] - 273.15, finite_mean(values, (1, 2)) - 273.15
            rec = {'time': t, 'neighbourhood_valid_pixels': int(valid.sum())}
            rec.update({f'center_{band}': centre[i] for i, band in enumerate(BANDS)})
            rec.update({f'neighbourhood_{band}': neighbourhood[i] for i, band in enumerate(BANDS)})
            records.append(rec)
        if date.day in [1, 15, 31]:
            print('extracted', date.date(), 'files', len(manifest), flush=True)

    monthly_manifest, exported = [], []
    for month in range(8, 13):
        for hour in range(10, 17):
            path = monthly/f'MLST_MONTH_2017{month:02}_HH{hour:02}.h5'
            with h5py.File(path) as f:
                np.testing.assert_allclose(f.attrs['GeoTransform'], gt, rtol=0, atol=1e-12)
                d = f['Monthly_Hour_Mean_LST']
                values = d[:, rows, cols].astype(float) / float(f.attrs['Scale_Factor'])
                companion = Path(f.attrs['Source_Monthly_Composite'])
            a = np.stack(daily_by_group[(month, hour)])
            independent = finite_mean(a, axis=0)
            mask_equal = bool(np.array_equal(np.isfinite(values), np.isfinite(independent)))
            error = np.abs(values - independent)
            max_error = float(np.nanmax(error)) if np.isfinite(error).any() else None
            counts = np.isfinite(a[:, 0]).sum(axis=0)
            with h5py.File(companion) as f:
                stored_counts = f['LSCT/valid_count'][rows, cols]
            counts_equal = bool(np.array_equal(counts, stored_counts))
            reconciliations.append({'month': month, 'hour': hour, 'mask_equal': mask_equal,
                                    'max_abs_error_K': max_error, 'counts_equal': counts_equal,
                                    'center_valid_days': int(counts[1, 1]),
                                    'passed': mask_equal and counts_equal and (max_error is None or max_error < 1e-4)})
            assert reconciliations[-1]['passed'], reconciliations[-1]
            monthly_manifest.append({'path': str(path), 'sha256': sha256(path), 'companion': str(companion)})
            for component, (_, b) in COMPONENTS.items():
                exported.append({'month': month, 'hour': hour, 'component': component,
                                 'monthly_export_center_C': float(values[b, 1, 1]-273.15),
                                 'monthly_export_3x3_mean_C': float(finite_mean(values[b], (0, 1))-273.15),
                                 'center_valid_days_full_month': int(counts[1, 1])})

    daily_table = pd.DataFrame(records)
    paired = daily_table.merge(ground, on='time', how='inner', validate='one_to_one')
    raw_tables, month_tables, scores = [], [], []
    for component, (reference, _) in COMPONENTS.items():
        for method in ['center', 'neighbourhood']:
            prediction = f'{method}_{component}'
            good = paired[reference].between(-23.15, 76.85) & paired[prediction].between(-23.15, 76.85)
            z = paired.loc[good, ['time', reference, prediction, 'neighbourhood_valid_pixels']].copy()
            z = z.rename(columns={reference: 'reference', prediction: 'prediction'})
            z['month'], z['hour'] = z.time.dt.month, z.time.dt.hour
            z['component'], z['method'] = component, method
            raw_tables.append(z)
            m = z.groupby(['month', 'hour'], as_index=False).agg(reference=('reference', 'mean'),
                         prediction=('prediction', 'mean'), n_raw=('reference', 'size'))
            m = m.loc[m.n_raw >= 2].copy()
            m['component'], m['method'] = component, method
            month_tables.append(m)
            scores.append({'component': component, 'method': method,
                           'hourly_pairs': score(z), 'monthly_hour_pairs': score(m),
                           'min_pairs_per_month_hour': int(m.n_raw.min()) if len(m) else None})

    # Report method sensitivity on identical times, so different support is visible.
    common_scores = []
    for component in COMPONENTS:
        c, n = [x for x in raw_tables if x.component.iloc[0] == component]
        both = c.merge(n[['time', 'prediction']], on='time', suffixes=('_center', '_neighbourhood'), validate='one_to_one')
        for method in ['center', 'neighbourhood']:
            z = both.rename(columns={f'prediction_{method}': 'prediction'})
            m = z.groupby(['month', 'hour'], as_index=False).agg(reference=('reference','mean'), prediction=('prediction','mean'), n=('time','size'))
            m = m.loc[m.n >= 2]
            common_scores.append({'component': component, 'method': method,
                                  'hourly_pairs': score(z), 'monthly_hour_pairs': score(m)})

    pd.concat(raw_tables, ignore_index=True).to_csv(out/'evora_grid_matched_pairs.csv', index=False)
    pd.concat(month_tables, ignore_index=True).to_csv(out/'evora_grid_month_hour_means.csv', index=False)
    pd.DataFrame(exported).to_csv(out/'evora_monthly_export_values.csv', index=False)
    report = {
        'created_UTC': dt.datetime.now(dt.timezone.utc).isoformat(),
        'script_sha256': sha256(__file__), 'field_path': str(field_path), 'field_sha256': sha256(field_path),
        'site': {'longitude': lon, 'latitude': lat, 'row_zero_based': row, 'column_zero_based': col,
                 'pixel_center_lon': float(gt[0]+(col+.5)*gt[1]), 'pixel_center_lat': float(gt[3]+(row+.5)*gt[5])},
        'protocol': {'ground_time_convention': 'UTC assumed consistently with existing manuscript; source instrument clock not newly verified',
                     'ground_correction': 'Planck 10.5 um; emissivity 0.985; constant sky 250 K',
                     'reference_window': '[2017-08-01,2017-12-31) UTC', 'hours_UTC': list(range(10,17)),
                     'temperature_bounds_K': [250,350], 'residual_screening': False,
                     'monthly_minimum_pairs': 2, 'scores': 'prediction minus reference, equal month-hour weights',
                     'neighbourhood': 'arithmetic mean of available valid pixels in fixed 3x3, then equal-date temporal mean'},
        'daily_files_read': len(manifest), 'missing_daily_files': missing,
        'monthly_reconciliation': reconciliations, 'scores': scores, 'common_support_scores': common_scores,
        'limitations': [
            'Single site, Aug-Dec 2017 only; not archive-wide temperature accuracy.',
            'Existing uncorrected regional products; cold encoding and view-angle provenance still unresolved.',
            'Product-level scores use co-sampled daily regional values grouped by month/hour, not unmatched full-calendar monthly means.',
            'Full monthly exports are independently reconciled at 9 pixels; monthly export values are reported separately.',
            'Ground canopy/sunlit-soil representativeness and instrument time convention remain conditional.',
            'Daily SHA256 covers only extracted 4x3x3 raw slices; file size and mtime also recorded.'
        ], 'daily_slice_manifest': manifest, 'monthly_file_manifest': monthly_manifest}
    (out/'evora_grid_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({'scores': scores, 'files': len(manifest), 'missing': len(missing),
                      'monthly_reconciled': len(reconciliations)}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
