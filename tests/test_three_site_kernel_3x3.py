"""Joint three-view support and genuine leave-one-footprint-out invariants."""
import importlib.util
from pathlib import Path
import sys
import numpy as np
import pytest

CASE=Path(__file__).resolve().parents[1]/'cases/ahi-slstr/heihe/three-site-kernel-3x3'


def module():
    assert (CASE/'joint.py').is_file(), 'Joint 3x3 solver missing'
    sys.path.insert(0,str(CASE))
    try:
        spec=importlib.util.spec_from_file_location('joint_3x3',CASE/'joint.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    finally:sys.path.pop(0)
    return m


def fixture():
    rng=np.random.default_rng(91)
    kn=rng.uniform(-.03,.04,(9,4,2));ko=rng.uniform(-.1,.1,(9,4,2));ka=rng.uniform(-.1,.1,(9,2))
    beta=np.array([8.,-5.]);background=rng.uniform(240,335,(9,4))
    # Native support varies strongly to expose incorrect aggregate-before-correct implementations.
    c2=14387.76877;wl=10.85
    iso=c2/(wl*np.log1p(1/np.mean(1/np.expm1(c2/(wl*background)),axis=1)))
    return dict(tn=background+kn@beta,to=background+ko@beta,ta=iso+ka@beta,kn=kn,ko=ko,ka=ka),beta


def test_joint_coefficients_recovered_with_heterogeneous_native_backgrounds():
    m=module();data,beta=fixture();fit=m.fit_joint(data)
    np.testing.assert_allclose(fit['coefficients'],beta,atol=1e-7)
    norms=m.correct(data,fit['coefficients'])
    np.testing.assert_allclose(norms[:,0],norms[:,1],atol=1e-8)
    np.testing.assert_allclose(norms[:,0],norms[:,2],atol=1e-8)


def test_heldout_triplet_cannot_change_its_coefficients():
    m=module();data,_=fixture()
    a=m.leave_one_out(data)[4]['coefficients']
    changed={k:v.copy() for k,v in data.items()}
    for k in ('tn','to','ta'):changed[k][4]+=15
    b=m.leave_one_out(changed)[4]['coefficients']
    np.testing.assert_array_equal(a,b)


def test_ahi_is_training_input_in_new_design():
    m=module();data,_=fixture();a=m.fit_joint(data)['coefficients']
    data['ta']=data['ta']+1
    b=m.fit_joint(data)['coefficients']
    assert np.linalg.norm(a-b)>0.01


def test_missing_view_or_rank_deficiency_is_rejected():
    m=module();data,_=fixture();data['ta'][0]=np.nan
    with pytest.raises(ValueError,match='finite|invalid'):m.fit_joint(data)
    data,_=fixture()
    for k in ('kn','ko','ka'):data[k][...,1]=data[k][...,0]
    with pytest.raises(ValueError,match='rank|condition'):m.fit_joint(data)


def test_window_is_exactly_3x3_not_a_radius_or_9x9():
    m=module();r,c=np.mgrid[10:21,20:31]
    mask=m.window_mask(r,c,15,25)
    assert mask.sum()==9
    assert set(r[mask])=={14,15,16} and set(c[mask])=={24,25,26}


def test_native_temperature_range_cannot_be_hidden_by_aggregation():
    m=module()
    t=np.array([[220.,300.,300.,300.]])
    data=dict(tn=t,to=t.copy(),ta=np.array([290.]),kn=np.ones((1,4,1)),ko=np.ones((1,4,1)),ka=np.ones((1,1)))
    norms,delta,maximum,accepted=m.correction_limits(data,np.array([10.]))
    assert (norms>220).all() and (maximum<=10).all()
    assert not accepted[0], 'A 210 K corrected native subpixel must fail even if its aggregate is valid'
