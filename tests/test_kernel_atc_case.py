"""Case-level checks for split isolation and reproducible model comparison."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT/'cases/multisource-normalization'
spec = importlib.util.spec_from_file_location('kernel_atc_case',CASE/'fit_models.py')
case = importlib.util.module_from_spec(spec)
spec.loader.exec_module(case)


def test_configured_case_uses_common_heldout_samples_and_fits_both_domains():
    data = case.demo_samples()
    config = json.loads((CASE/'models.example.json').read_text(encoding='utf-8'))
    report,predictions = case.run_comparison(data,config)
    assert len(report['angular']) == 5 and len(report['annual']) == 2
    assert {x['heldout_sample_count'] for x in report['angular']} == {60}
    assert {x['heldout_sample_count'] for x in report['annual']} == {31}
    for prefix in ('angle','atc'):
        assert not np.any(predictions[f'{prefix}_heldout_mask'] & data[f'{prefix}_train'])
    optimized = next(x for x in report['angular'] if x['id'] == 'lsf_rl_fit')
    assert optimized['heldout_rmse_k'] < .15  # controlled known signal + .08K noise
    assert report['annual'][1]['heldout_rmse_k'] < .25


def test_heldout_values_cannot_change_fitted_coefficients():
    data = case.demo_samples()
    config = {'angular_models':[{'id':'fixed','preset':'lsf_rl'}],
              'atc_models':[{'id':'annual','harmonics':2}]}
    before,_ = case.run_comparison(data,config)
    for prefix in ('angle','atc'):
        data[f'{prefix}_temperature_k'][~data[f'{prefix}_train']] += 10.
    after,_ = case.run_comparison(data,config)
    for key in ('angular','annual'):
        np.testing.assert_array_equal(before[key][0]['coefficients'],after[key][0]['coefficients'])
        assert after[key][0]['heldout_rmse_k'] > before[key][0]['heldout_rmse_k']+5


def test_case_requires_genuine_split_and_unique_ids():
    data = case.demo_samples()
    config = {'atc_models':[{'id':'annual','harmonics':1}]}
    data['atc_train'][:] = True
    with pytest.raises(ValueError,match='held-out'):
        case.run_comparison(data,config)
    config['atc_models'] *= 2
    with pytest.raises(ValueError,match='unique'):
        case.run_comparison(data,config)
