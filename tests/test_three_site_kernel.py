"""Scientific invariants for the standalone Heihe angular-normalization case."""
import importlib.util
from pathlib import Path
import sys
import json

import numpy as np
import pytest

CASE = Path(__file__).resolve().parents[1] / 'cases/ahi-slstr/heihe/three-site-kernel'


def module():
    path = CASE / 'functions.py'
    assert path.exists(), 'Standalone paired-kernel implementation is missing'
    spec = importlib.util.spec_from_file_location('three_site_functions', path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_pair_fit_recovers_coefficients_despite_arbitrary_pixel_temperatures():
    m = module()
    rng = np.random.default_rng(17)
    n, o = rng.normal(size=(2, 80, 2))
    beta = np.array([3., -1.5])
    background = rng.uniform(260, 330, 80)
    fitted = m.fit_pairs(background+n@beta, background+o@beta, n, o)
    np.testing.assert_allclose(fitted['coefficients'], beta, atol=1e-11)


def test_rank_deficient_angles_are_rejected():
    m = module()
    n = np.zeros((30, 2)); o = np.ones((30, 2))
    with pytest.raises(ValueError, match='rank|condition'):
        m.fit_pairs(np.ones(30)*300, np.ones(30)*301, n, o)


def test_nadir_is_identity_and_azimuth_is_periodic():
    m = module()
    a = m.kernel_basis(np.array([0., 35.]), 40., np.array([21., 63.]))
    b = m.kernel_basis(np.array([0., 35.]), 40., np.array([381., 423.]))
    np.testing.assert_allclose(a, b, atol=1e-13)
    np.testing.assert_allclose(a[0], 0., atol=1e-13)
    np.testing.assert_allclose(m.normalize(np.array([300.]), a[:1], np.array([2., 3.])), 300.)


def test_station_block_and_buffer_never_enter_fit():
    m = module()
    rr, cc = np.mgrid[0:35, 0:35]
    split = m.split_blocks(rr.ravel(), cc.ravel(), 17, 17, block_cells=5)
    train = split == 'train'
    distance = np.maximum(np.abs(rr.ravel()//5-3), np.abs(cc.ravel()//5-3))
    assert not train[distance <= 1].any()
    blocks = rr.ravel()//5*1000 + cc.ravel()//5
    assert not set(blocks[train]) & set(blocks[split == 'test'])
    assert (split[distance == 0] == 'test').all()


def test_hhmm_rejects_missing_fractional_and_bad_minutes():
    m = module()
    value = m.decode_hhmm(np.array([337., 1260., 2400., -1., np.nan, 337.4]))
    assert value[0] == 217
    assert np.isnan(value[1:]).all()


def test_fit_is_invariant_to_heldout_and_ahi_temperatures():
    m = module()
    rng = np.random.default_rng(42)
    n = rng.normal(size=(50, 2)); o = rng.normal(size=(50, 2))
    beta = np.array([2., 4.]); train = np.arange(50) < 30
    tn = 300+n@beta; to = 300+o@beta
    first = m.fit_pairs(tn[train], to[train], n[train], o[train])
    tn[~train] += 1000; to[~train] -= 1000
    second = m.fit_pairs(tn[train], to[train], n[train], o[train])
    np.testing.assert_array_equal(first['coefficients'], second['coefficients'])


def test_radiance_aggregation_is_not_arithmetic_temperature_averaging():
    m = module()
    a = np.array([[280., 320.], [280., 320.]])
    assert m.radiance_mean(a, axis=(0, 1)) > a.mean()
    np.testing.assert_allclose(m.radiance_mean(np.ones((2, 2))*300, axis=(0, 1)), 300.)


def runner():
    sys.path.insert(0, str(CASE))
    try:
        spec = importlib.util.spec_from_file_location('three_site_runner', CASE/'run.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    return mod


def test_real_fit_entry_never_accesses_ahi_or_heldout_temperatures():
    import pandas as pd
    m = runner()
    rng = np.random.default_rng(21)
    n, o = rng.normal(size=(2, 100, 2))
    beta = np.array([2., -3.])
    df = pd.DataFrame(dict(t_n=300+n@beta, t_o=300+o@beta,
                          lsf_n=n[:,0], lsf_o=o[:,0],
                          rl_n_w1=n[:,1], rl_o_w1=o[:,1],
                          split=['train']*60+['test']*40,
                          block_id=np.arange(100)//5, row_id=np.arange(100)))
    c = json.loads((CASE/'config.json').read_text(encoding='utf-8'))
    fit, _ = m.fit_site(df, c, 'lsf_rl', 1., bootstrap=False)
    df['t_a'] = np.nan
    df.loc[df.split=='test',['t_n','t_o']] = -9999
    repeated, _ = m.fit_site(df,c,'lsf_rl',1.,bootstrap=False)
    np.testing.assert_allclose(fit['coefficients'], beta, atol=1e-11)
    np.testing.assert_array_equal(fit['coefficients'], repeated['coefficients'])


def test_copied_formula_matches_current_ls4t_kernels():
    from base.normalization.kernels import KernelTerm, evaluate_kernel
    m = module()
    v = np.array([0., 10., 35., 55.]); s = np.array([25., 35., 45., 55.]); a = np.array([0., 45., 120., 250.])
    for width in [.5, 1., 2.]:
        k = m.kernel_basis(v,s,a,width)
        expected = np.column_stack([evaluate_kernel('lsf',v,s,a)-evaluate_kernel('lsf',np.zeros_like(v),s,a),
                                    evaluate_kernel(KernelTerm('rl',{'k':width}),v,s,a)])
        np.testing.assert_allclose(k,expected,rtol=1e-12,atol=1e-12)


def test_native_correction_precedes_nonlinear_radiance_aggregation():
    m = module()
    background = np.array([[230., 345., 230., 345.]])
    kn = m.kernel_basis(np.full((1,4),10.),40.,110.)
    ko = m.kernel_basis(np.full((1,4),55.),40.,110.)
    beta = np.array([80.,-10.])
    tn = background+kn@beta; to = background+ko@beta
    assert hasattr(m, 'normalize_native'), 'Native-resolution correction is required before aggregation'
    nn, _, _ = m.normalize_native(tn,kn,beta)
    no, _, _ = m.normalize_native(to,ko,beta)
    np.testing.assert_allclose(nn,no,atol=1e-11)
    np.testing.assert_allclose(nn,m.radiance_mean(background,axis=1),atol=1e-11)


def test_replay_rejects_changed_model_status():
    m = runner()
    assert hasattr(m,'compare_models'), 'Replay must compare model keys and status before coefficients'
    old=[dict(site='DM',model='lsf',status='fitted',coefficients=[1.])]
    new=[dict(site='DM',model='lsf',status='rejected',reason='insufficient')]
    with pytest.raises(AssertionError,match='status'):
        m.compare_models(new,old)


def test_same_day_match_rejects_midnight_rollover():
    m = module()
    assert hasattr(m,'match_minutes'), 'Same UTC-day matching is required'
    nearest, good=m.match_minutes(np.array([217.,239.,1438.,np.nan]),5)
    np.testing.assert_array_equal(nearest[:3],[220.,240.,1440.])
    np.testing.assert_array_equal(good,[True,True,False,False])
