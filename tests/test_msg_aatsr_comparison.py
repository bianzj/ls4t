"""Independent checks for the experimental MSG/AATSR transfer adapter."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

pytest.importorskip('osgeo')
EXAMPLES = Path(__file__).parent/'examples'
sys.path.insert(0,str(EXAMPLES))
spec = importlib.util.spec_from_file_location('msg_aatsr_comparison',EXAMPLES/'msg_aatsr_comparison.py')
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


def make_weights(m=2):
    rng=np.random.default_rng(901)
    w=rng.uniform(.1,1,(5,5,2,m))
    return w/w.sum(-1,keepdims=True)*.98


def test_window_ls_and_ridge_match_existing_core():
    from base.lsct import retrieve_components
    w=make_weights()
    r=comparison.planck([310.,300.])
    y=w@r
    for method,ridge in [('ls2',0.),('ridge2',.01)]:
        expected=retrieve_components(y.reshape(-1),w.reshape(-1,2),10.5,ridge=ridge).radiance
        actual=comparison.solve_window(y,w,np.array([305.,306.]),method)
        np.testing.assert_allclose(actual,expected,atol=1e-10)


def test_quadratic_recovers_known_spatial_radiance_surface():
    w=make_weights()
    yy,xx=np.mgrid[-2:3,-2:3]
    truth=np.stack([10.+.1*xx+.05*yy**2,8.+.08*yy+.03*xx*yy],-1)
    y=np.einsum('xyac,xyc->xya',w,truth)
    center,surface=comparison.quadratic(w,y,np.ones(y.shape,bool))
    np.testing.assert_allclose(surface,truth,atol=1e-10)
    np.testing.assert_allclose(center,[10.,8.],atol=1e-10)


def test_delta_constraint_changes_only_configured_inequalities():
    w=make_weights()
    truth=comparison.planck([300.,315.])
    y=w@truth
    center_lst=comparison.inverse_planck(10.5,y[2,2]/w[2,2].sum(-1))
    off=comparison.solve_window(y,w,center_lst,'slsqp_no_delta2')
    on=comparison.solve_window(y,w,center_lst,'slsqp2')
    np.testing.assert_allclose(off,truth,atol=1e-5)
    lo=comparison.planck(center_lst.mean()-2.5)-comparison.planck(center_lst.mean()+2.5)
    assert off[0]-off[1]<lo
    assert on[0]-on[1]>=lo-1e-6


@pytest.mark.parametrize('common_residual_mask',[False,True])
def test_msg_production_adapter_preserves_uniform_component_temperature(common_residual_mask):
    rng=np.random.default_rng(912)
    w=rng.uniform(.1,1,(10,10,2,3))
    w=w/w.sum(-1,keepdims=True)*.98
    rad=float(comparison.planck(300.))
    y=w.sum(-1)*rad
    actual=comparison.msg_iter(y,w,comparison.production_functions(),common_residual_mask)
    np.testing.assert_allclose(actual[3:7,3:7],rad,atol=1e-7)


def test_map_matches_gaussian_update_identity():
    a=np.array([[.3,.68],[.65,.33]])
    prior=np.array([10.,8.])
    obs=np.array([9.1,9.4])
    cm=np.diag([2.,1.]); cd=np.eye(2)*.05
    expected=prior+cm@a.T@np.linalg.solve(a@cm@a.T+cd,obs-a@prior)
    np.testing.assert_allclose(comparison.posterior(a,obs,prior),expected,atol=1e-12)
