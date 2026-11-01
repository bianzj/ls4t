"""Observable kernel parity, identifiability and reference-geometry behavior."""
import numpy as np
import pytest

from base import kernel as legacy
from base.normalization import kernels as km


def geometry(n=140):
    rng = np.random.default_rng(31)
    return rng.uniform(0, 65, n), rng.uniform(10, 65, n), rng.uniform(-360, 720, n)


@pytest.mark.parametrize('name,fn,view_only', [
    ('vin', legacy.kernel_Vin, True), ('lsf', legacy.kernel_LSF, True),
    ('lsf_analytical', legacy.kernel_LSF_analytical, True),
    ('tlsf', legacy.kernel_TLSF, True), ('vlsf', legacy.kernel_VLSF, True),
    ('thapke', legacy.kernel_Thapke, True),
    ('li_dense', legacy.kernel_LiDense, False), ('li_sparse', legacy.kernel_LiSparse, False),
    ('solar', legacy.kernel_Solar, False), ('rl_distance', legacy.kernel_RLf, False),
    ('ross_thick', legacy.kernel_RossThick, False), ('ross_thin', legacy.kernel_RossThin, False),
])
def test_adapter_preserves_legacy_values_without_mutating_angles(name, fn, view_only):
    v, s, a = geometry(12)
    v, s, a = v.reshape(3, 4), s.reshape(3, 4), a.reshape(3, 4)
    original = a.copy()
    folded = np.mod(a.ravel(), 360)
    expected = fn(v.ravel()) if view_only else fn(v.ravel(), s.ravel(), folded.copy())
    np.testing.assert_allclose(km.evaluate_kernel(name, v, s, a), expected.reshape(3, 4))
    np.testing.assert_array_equal(a, original)
    assert np.ndim(km.evaluate_kernel(name, 20., 40., 35.)) == 0


def test_linear_three_physical_kernels_and_reference_correction():
    v, s, a = geometry()
    model = km.kernel_model('lsf_li_dense_ross_thick')
    coeff = np.array([290., 8., 2., -3.])
    y = model.design_matrix(v, s, a) @ coeff
    y[-1] = 1000  # QA-invalid outlier must not affect the fit.
    qa = np.zeros(len(y), dtype='uint16'); qa[-1] = 2
    fit = km.fit_kernel_model(model, y, v, s, a, quality_flag=qa)
    np.testing.assert_allclose(fit.coefficients, coeff, atol=1e-9)
    corrected = fit.normalize(y[:-1] + .7, v[:-1], s[:-1], a[:-1])
    expected = model.design_matrix(0., s[:-1], 0.) @ coeff + .7
    np.testing.assert_allclose(corrected, expected, atol=1e-9)
    assert fit.sample_count == len(y)-1 and fit.solver == 'linear'
    assert np.isnan(fit.normalize(np.nan, 20, 40, 0))


def test_custom_model_and_config_roundtrip():
    model = km.KernelModel(('isotropic', 'lsf', km.KernelTerm('rl', {'k': .7})))
    restored = km.KernelModel.from_dict(model.to_dict())
    v, s, a = geometry()
    np.testing.assert_allclose(model.design_matrix(v, s, a), restored.design_matrix(v, s, a))
    assert model.terms[-1].parameters['k'] == .7
    with pytest.raises(ValueError, match='unknown'):
        km.KernelTerm('missing')
    with pytest.raises(ValueError, match='parameter'):
        km.KernelTerm('lsf', {'k': 1})


def test_hotspot_distance_is_not_the_hotspot_kernel():
    v, s, a = geometry()
    f = legacy.kernel_RLf(v, s, np.mod(a, 360))
    fn = np.tan(np.deg2rad(s))
    expected = (np.exp(-.6*f)-np.exp(-.6*fn))/(1.0001-np.exp(-.6*fn))
    np.testing.assert_allclose(km.evaluate_kernel(km.KernelTerm('rl', {'k': .6}), v,s,a), expected)
    np.testing.assert_allclose(km.evaluate_kernel('rl', 0., s, 0.), 0., atol=1e-12)


def test_minimize_estimates_width_and_linear_coefficients_on_heldout_angles():
    v, s, a = geometry(240)
    truth = km.KernelModel(('isotropic', 'lsf', km.KernelTerm('rl', {'k': .8})))
    y = truth.design_matrix(v, s, a) @ np.array([290., 7., 4.])
    initial = km.kernel_model('lsf_rl')
    fit = km.fit_kernel_model(initial, y[:180], v[:180], s[:180], a[:180],
                              solver='minimize', parameter_bounds={'rl.k': (.1, 3.)})
    assert fit.success and fit.solver == 'minimize'
    assert fit.model.terms[-1].parameters['k'] == pytest.approx(.8, abs=1e-4)
    np.testing.assert_allclose(fit.predict(v[180:], s[180:], a[180:]), y[180:], atol=1e-5)


def test_rank_failures_invalid_geometry_and_optimizer_configuration():
    v, s, a = geometry()
    redundant = km.KernelModel(('isotropic', km.KernelTerm('tlsf', {'w': .1}),
                                km.KernelTerm('vlsf', {'w': .1})))
    with pytest.raises(ValueError, match='rank|condition'):
        km.fit_kernel_model(redundant, np.full(v.shape, 300.), v,s,a)
    assert np.isnan(km.evaluate_kernel('lsf', 90., 30., 0.))
    assert np.isnan(km.evaluate_kernel('li_dense', 20., 90., 0.))
    with pytest.raises(ValueError, match='bounds'):
        km.fit_kernel_model(km.kernel_model('lsf_rl'), np.full(v.shape, 300.),v,s,a,solver='minimize')
    with pytest.raises(ValueError, match='linear'):
        km.fit_kernel_model(km.kernel_model('lsf_rl'), np.full(v.shape, 300.),v,s,a,
                            parameter_bounds={'rl.k': (.1,3.)})


@pytest.mark.parametrize('name', ['li_dense', 'li_sparse'])
def test_common_li_scale_cannot_be_estimated_from_angular_observations(name):
    v,s,a = geometry()
    model = km.KernelModel(('isotropic', name))
    y = model.design_matrix(v,s,a) @ [290.,7.]
    with pytest.raises(ValueError, match='scale|ratio'):
        km.fit_kernel_model(model,y,v,s,a,solver='minimize',
                            parameter_bounds={f'{name}.{p}':(.5,3.) for p in ('h','r','b')})


def test_optimizer_failure_is_not_a_successful_fit():
    v,s,a = geometry()
    model = km.KernelModel(('isotropic','lsf',km.KernelTerm('rl',{'k':.8})))
    y = model.design_matrix(v,s,a) @ [290.,7.,4.]
    with pytest.raises(RuntimeError,match='optimization failed'):
        km.fit_kernel_model(km.kernel_model('lsf_rl'),y,v,s,a,solver='minimize',
                            parameter_bounds={'rl.k':(.1,3.)},options={'maxiter':1})


def test_weighted_solution_matches_direct_weighted_system():
    v,s,a = geometry()
    model = km.kernel_model('lsf_li_dense')
    matrix = model.design_matrix(v,s,a)
    y = matrix @ [290.,7.,2.] + np.sin(np.arange(len(v)))
    weights = np.linspace(.1,2.,len(v))
    fit = km.fit_kernel_model(model,y,v,s,a,weights=weights)
    expected = np.linalg.lstsq(matrix*np.sqrt(weights[:,None]),y*np.sqrt(weights),rcond=None)[0]
    np.testing.assert_allclose(fit.coefficients,expected,atol=1e-9)

