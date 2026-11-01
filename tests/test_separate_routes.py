import copy
import pytest
from base.known_inputs import run_workbench


def test_retrieval_does_not_evaluate_reference_geometry():
    from test_known_inputs import scenario
    p=scenario()
    p['reference_vza']='not a retrieval input'
    r=run_workbench(p)
    assert 'temperature_k' in r
    assert 'curve' not in r and 'reference_vza' not in r
    assert all('normalized_k' not in o for o in r['observations'])


def test_angular_route_is_independent_and_recovers_secant_slope(monkeypatch):
    from base.normalization.workbench import normalize_observations
    import base.known_inputs as ki
    monkeypatch.setattr(ki,'run_workbench',lambda *a:pytest.fail('component solver must not run'))
    p={'coefficient_mode':'fit','reference_vza':0,'observations':[
        {'name':'nadir','sensor':'SLSTR','lst_k':300,'vza':0,'sigma_k':1,'use_for_fit':True,'time_utc':'2019-01-01T02:50:00Z'},
        {'name':'oblique','sensor':'SLSTR','lst_k':303,'vza':60,'sigma_k':1,'use_for_fit':True,'time_utc':'2019-01-01T02:50:00Z'},
        {'name':'heldout','sensor':'AHI','lst_k':304,'vza':60,'sigma_k':1,'use_for_fit':False,'time_utc':'2019-01-01T02:50:00Z'}]}
    saved=copy.deepcopy(p)
    r=normalize_observations(p)
    assert p==saved
    assert r['coefficient_k']==pytest.approx(3)
    assert [o['normalized_k'] for o in r['observations']]==pytest.approx([300,300,301])
    assert 'temperature_k' not in r and 'fixed' not in r
    p['observations'][2]['lst_k']=310
    assert normalize_observations(p)['coefficient_k']==pytest.approx(3)


def test_supplied_angle_coefficient_allows_single_lst():
    from base.normalization.workbench import normalize_observations
    p={'coefficient_mode':'supplied','coefficient_k':4,'reference_vza':60,
       'observations':[{'sensor':'AHI','lst_k':300,'vza':60}]}
    assert normalize_observations(p)['observations'][0]['normalized_k']==pytest.approx(300)
    p['reference_vza']=0
    assert normalize_observations(p)['observations'][0]['normalized_k']==pytest.approx(296)


def test_normalization_rejects_brightness_temperature_and_identical_fit_angles():
    from base.normalization.workbench import normalize_observations
    p={'coefficient_mode':'supplied','coefficient_k':1,'observations':[{'sensor':'AHI','bt1_k':300,'vza':30}]}
    with pytest.raises(ValueError,match='LST'):normalize_observations(p)
    p={'coefficient_mode':'fit','observations':[{'sensor':'SLSTR','lst_k':300,'vza':30,'time_utc':'2019-01-01T02:50:00Z'}]*2}
    with pytest.raises(ValueError,match='角度'):normalize_observations(p)
