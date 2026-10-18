"""Quality-control a station replay and check collocated ICOS observations.

UTC matching, physical bounds and the comparison variables follow the maintained
paper validation workflow. ICOS soil-probe and air temperatures are indirect
references, not direct component radiometric validation.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_single_scene_windows import sha256


def scores(reference, estimate):
    error = (estimate - reference).to_numpy(dtype=float)
    return {'n': int(error.size), 'rmse_K': float(np.sqrt(np.mean(error**2))) if error.size else None,
            'bias_K': float(error.mean()) if error.size else None,
            'mae_K': float(np.abs(error).mean()) if error.size else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-directory', type=Path, required=True)
    parser.add_argument('--data-root', type=Path, default=Path('E:/'))
    args = parser.parse_args()
    out = args.run_directory
    report = json.loads((out / 'report.json').read_text(encoding='utf-8'))
    d = pd.read_csv(out / 'station_predictions.csv')
    site = report['site']
    components = ['T_Soil', 'T_Vegetation', 'T_Sunlit_Soil', 'T_Shaded_Soil']
    kelvin = d[components] + 273.15
    d['qc_temperature_range'] = kelvin.ge(250).all(axis=1) & kelvin.le(350).all(axis=1)
    d['qc_daylight'] = d.SZA.ge(0) & d.SZA.lt(90)
    d['qc_sunlit_shaded_order'] = d.T_Sunlit_Soil.ge(d.T_Shaded_Soil - .01)
    d['qc_background_between_soils'] = d.T_Soil.ge(d.T_Shaded_Soil - .02) & d.T_Soil.le(d.T_Sunlit_Soil + .02)
    d['qc_all'] = d[['qc_temperature_range', 'qc_daylight', 'qc_sunlit_shaded_order', 'qc_background_between_soils']].all(axis=1)
    d.to_csv(out / 'station_quality_flags.csv', index=False)
    d.loc[d.qc_all].to_csv(out / 'station_predictions_qc.csv', index=False)
    result = {'site': site, 'prediction_sha256': sha256(out / 'station_predictions.csv'),
              'reproduction_match_percent': report['comparison']['exact_match_percent_union'],
              'raw_records': len(d), 'physical_range_pass': int(d.qc_temperature_range.sum()),
              'physical_range_pass_percent': float(100*d.qc_temperature_range.mean()),
              'all_quality_checks_pass': int(d.qc_all.sum()),
              'all_quality_checks_pass_percent': float(100*d.qc_all.mean()),
              'ground_validation': {},
              'scope': 'Reproduction, internal physical checks and indirect ground comparison are distinct metrics.'}
    field = args.data_root / f'field/ICOSETC_{site}_METEO_L2/ICOSETC_{site}_METEO_L2.csv'
    if not field.is_file():
        raise FileNotFoundError(field)
    result['field'] = {'path': str(field), 'sha256': sha256(field)}
    g = pd.read_csv(field, usecols=['TIMESTAMP_START', 'TA', 'TS_1'], na_values=[-9999, -9999.0])
    g['field_time'] = pd.to_datetime(g.TIMESTAMP_START.astype('Int64').astype(str), format='%Y%m%d%H%M', utc=True, errors='coerce')
    g = g.dropna(subset=['field_time']).sort_values('field_time')
    if g.duplicated('field_time').any():
        raise ValueError('Duplicate ground timestamps require resolution')
    d['time'] = pd.to_datetime(d.DateTime.astype(str), format='%Y%m%d%H%M', utc=True)
    x = d.loc[d.time.dt.hour.between(11, 16) & d.qc_daylight].sort_values('time')
    x = pd.merge_asof(x, g, left_on='time', right_on='field_time', direction='nearest', tolerance=pd.Timedelta(minutes=30))
    x['offset_minutes'] = (x.time-x.field_time).dt.total_seconds()/60
    all_matches = []
    for name, prediction, reference in [('background_soil', 'T_Soil', 'TS_1'), ('canopy', 'T_Vegetation', 'TA')]:
        columns = [prediction, reference, 'LST_Euro']
        valid = x[columns].notna().all(axis=1) & x[columns].ge(250-273.15).all(axis=1) & x[columns].le(350-273.15).all(axis=1)
        z = x.loc[valid, ['time', 'field_time', 'offset_minutes', prediction, reference, 'LST_Euro']].copy()
        z = z.rename(columns={prediction: 'estimate_C', reference: 'reference_C', 'LST_Euro': 'bulk_C'})
        z['component'] = name; z['month'] = z.time.dt.strftime('%Y-%m'); all_matches.append(z)
        month = z.groupby('month', as_index=False).agg(estimate_C=('estimate_C', 'mean'), reference_C=('reference_C', 'mean'), bulk_C=('bulk_C', 'mean'), n=('reference_C', 'size'))
        month = month.loc[month.n >= 3]
        month.to_csv(out / f'{name}_monthly_ground_comparison.csv', index=False)
        result['ground_validation'][name] = {
            'reference': reference, 'comparison_type': 'indirect consistency',
            'instantaneous_component': scores(z.reference_C, z.estimate_C),
            'instantaneous_bulk_same_samples': scores(z.reference_C, z.bulk_C),
            'monthly_component': scores(month.reference_C, month.estimate_C),
            'monthly_bulk_same_samples': scores(month.reference_C, month.bulk_C),
            'month_count': len(month),
            'maximum_time_offset_minutes': float(z.offset_minutes.abs().max()) if len(z) else None,
        }
    pd.concat(all_matches, ignore_index=True).to_csv(out / 'ground_matches.csv', index=False)
    result['protocol'] = {'time': 'TIMESTAMP_START interpreted as UTC; nearest within 30 minutes',
                          'hours_UTC': list(range(11, 17)), 'temperature_bounds_K': [250, 350],
                          'residual_screen': None, 'monthly_minimum_pairs': 3,
                          'ground_mask': 'per-component estimate, reference and bulk all within physical range; same samples for bulk comparison'}
    (out / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
