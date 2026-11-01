import copy

import numpy as np
import pytest

from base import known_inputs as ki


def scenario():
    fixed = dict(lai=1.5, tcwv_cm=1.0, soil_emissivity=[.96, .97],
                 vegetation_emissivity=[.985, .99], hotspot=.2)
    obs = [dict(sensor='SLSTR', name=name, vza=v, sza=40., raa=a,
                wavelength_um=10.85, sigma_k=1., use_for_fit=True,
                time_utc='2019-01-01T03:00:00Z')
           for name, v, a in [('nadir', 5., 0.), ('oblique', 55., 120.)]]
    obs += [dict(obs[0], sensor='AHI', name='AHI', vza=45., raa=60.,
                 wavelength_um=10.4, use_for_fit=False)]
    for o in obs:
        o['lst_k'] = float(ki.predict_lst([310., 295.], fixed, o))
    return dict(fixed=fixed, observations=obs, components=2,
                reference_vza=0., reference_raa=0., optimize=True,
                prior_k=[300., 300.], prior_strength=0.)


def test_recovers_temperatures_and_keeps_known_inputs_immutable():
    payload = scenario()
    saved = copy.deepcopy(payload)
    result = ki.run_workbench(payload)
    np.testing.assert_allclose(result['temperature_k'], [310., 295.], atol=1e-4)
    assert payload == saved
    assert result['fixed'] == saved['fixed']
    assert result['heldout_rmse_k'] < 1e-5
    assert result['fit_count'] == 2


def test_heldout_temperature_never_changes_fit_and_residual_is_preserved():
    payload = scenario()
    before = ki.run_workbench(payload)
    payload['observations'][2]['lst_k'] += 5
    after = ki.run_workbench(payload)
    np.testing.assert_allclose(before['temperature_k'], after['temperature_k'])
    assert after['observations'][2]['residual_k'] - before['observations'][2]['residual_k'] == pytest.approx(5.)
    assert after['heldout_rmse_k'] == pytest.approx(5.)


def test_reference_identity_and_three_component_rank_guard():
    payload = scenario()
    payload['reference_vza'] = 5.
    payload['reference_raa'] = 0.
    result = ki.run_workbench(payload)
    assert 'normalized_k' not in result['observations'][0]
    assert 'reference_vza' not in result
    payload['components'] = 3
    with pytest.raises(ValueError, match='观测|observation'):
        ki.run_workbench(payload)


def test_degenerate_geometry_and_time_mismatch_rejected():
    payload = scenario()
    payload['observations'][1].update(vza=5., raa=0.)
    with pytest.raises(ValueError, match='角度|condition|秩'):
        ki.run_workbench(payload)
    payload = scenario()
    payload['observations'][2]['time_utc'] = '2019-01-01T05:00:00Z'
    with pytest.raises(ValueError, match='时间'):
        ki.run_workbench(payload)


@pytest.mark.parametrize('key,value', [('lai', 0), ('lai', float('nan')),
                                      ('tcwv_cm', -1), ('soil_emissivity', [1.2, .97])])
def test_invalid_fixed_inputs_rejected(key, value):
    payload = scenario()
    payload['fixed'][key] = value
    with pytest.raises(ValueError):
        ki.run_workbench(payload)


def test_bt_requires_sensor_calibration():
    payload = scenario()
    obs = payload['observations'][0]
    del obs['lst_k']
    obs.update(bt1_k=298., bt2_k=297.)
    with pytest.raises(ValueError, match='系数'):
        ki.run_workbench(payload)


def test_three_components_recover_known_state():
    payload = scenario()
    payload.update(components=3, prior_k=[300., 300., 300.])
    for o in payload['observations']:
        o['use_for_fit'] = True
        o['lst_k'] = float(ki.predict_lst([315., 300., 295.], payload['fixed'], o))
    result = ki.run_workbench(payload)
    np.testing.assert_allclose(result['temperature_k'], [315., 300., 295.], atol=1e-4)
    assert result['heldout_rmse_k'] is None


def test_isothermal_scene_has_no_directional_correction():
    payload = scenario()
    for o in payload['observations']:
        o['lst_k'] = 300.
    result = ki.run_workbench(payload)
    np.testing.assert_allclose(result['temperature_k'], [300., 300.], atol=1e-6)
    np.testing.assert_allclose([o['residual_k'] for o in result['observations']], 0, atol=1e-6)


def test_temperature_prior_changes_only_temperature_solution():
    payload = scenario()
    payload.update(prior_strength=10., prior_k=[300., 300.])
    result = ki.run_workbench(payload)
    assert np.linalg.norm(np.array(result['temperature_k'])-300) < np.linalg.norm(np.array(result['baseline_temperature_k'])-300)
    assert result['fixed'] == payload['fixed']
    assert result['fit_rmse_k'] > result['baseline_rmse_k']


def test_existing_lst_does_not_repeat_atmospheric_correction():
    payload = scenario()
    first = ki.run_workbench(payload)
    payload['fixed']['tcwv_cm'] = 6.
    second = ki.run_workbench(payload)
    np.testing.assert_allclose(first['temperature_k'], second['temperature_k'])


def test_sensor_overrides_cannot_silently_change_global_lai():
    payload = scenario()
    payload['fixed']['sensors'] = {'SLSTR': {'lai': 4.}}
    with pytest.raises(ValueError, match='发射率'):
        ki.run_workbench(payload)


@pytest.mark.parametrize('payload', [None, [], {'fixed': []}, {'fixed': {'lai': 1}}])
def test_malformed_configuration_is_a_validation_error(payload):
    with pytest.raises(ValueError):
        ki.run_workbench(payload)


def test_real_sample_replays_offline_and_water_vapour_is_active():
    import json
    from pathlib import Path
    folder = Path(__file__).resolve().parents[1] / 'gui/examples/ahi_slstr'
    payload = json.loads((folder/'sample.json').read_text(encoding='utf-8'))
    for obs in payload['observations']:
        obs['coefficient_file'] = str(folder / (obs['sensor'].lower()+'_coefficients.npz'))
    result = ki.run_workbench(payload)
    expected = json.loads((folder/'result.json').read_text(encoding='utf-8'))
    np.testing.assert_allclose(result['temperature_k'], expected['temperature_k'], atol=1e-5)
    assert result['heldout_rmse_k'] == pytest.approx(expected['heldout_rmse_k'], abs=1e-5)
    payload['fixed']['tcwv_cm'] = 2.
    changed = ki.run_workbench(payload)
    assert abs(changed['observations'][0]['lst_k']-result['observations'][0]['lst_k']) > .01
    payload['observations'][0]['coefficient_file'] = str(folder/'ahi_coefficients.npz')
    with pytest.raises(ValueError, match='传感器'):
        ki.run_workbench(payload)
