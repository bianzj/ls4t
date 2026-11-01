import copy
import json
from pathlib import Path

import numpy as np
import pytest

from gui.workspace_tools import run_surface, run_time, run_space, run_batch


def test_surface_has_no_component_solver(monkeypatch):
    import base.known_inputs as ki
    monkeypatch.setattr(ki, 'run_workbench', lambda p: pytest.fail('component solver called'))
    folder = Path(__file__).resolve().parents[1] / 'gui/examples/ahi_slstr'
    p = json.loads((folder / 'sample.json').read_text(encoding='utf-8'))
    p['observations'] = p['observations'][:1]
    p['observations'][0]['coefficient_file'] = str(folder / 'slstr_coefficients.npz')
    r = run_surface(p)
    assert r['route'] == 'surface' and 'temperature_k' not in r
    assert r['observations'][0]['lst_k'] == pytest.approx(274.619966, abs=1e-4)
    p['observations'][0] = {'sensor':'AHI','lst_k':300,'vza':0}
    assert run_surface(p)['observations'][0]['lst_k'] == 300
    p['observations'][0]['cloud'] = True
    with pytest.raises(ValueError, match='云'):
        run_surface(p)


def test_time_identity_and_known_harmonic():
    p = {'reference_hour':12, 'amplitude_k':10, 'peak_hour':12,
         'observations':[{'lst_k':290,'hour':6}, {'lst_k':300,'hour':12}]}
    r = run_time(p)
    assert [o['normalized_k'] for o in r['observations']] == pytest.approx([300,300])
    assert r['observations'][1]['correction_k'] == 0
    p['observations'][0]['hour'] = 24
    with pytest.raises(ValueError): run_time(p)


def test_space_weighted_support_and_missing_cells():
    p = {'target_shape':[2,2], 'observations':[
        {'lst_k':300,'row':0,'column':0,'weight':1},
        {'lst_k':304,'row':0,'column':0,'weight':3}]}
    r = run_space(p)
    assert r['grid_k'] == [[303,None],[None,None]]
    assert r['support'] == [[4,0],[0,0]]
    p['observations'][0]['row'] = 2
    with pytest.raises(ValueError): run_space(p)
    p['observations'][0]['row'] = 0.5
    with pytest.raises(ValueError): run_space(p)


def test_batch_independent_failure_and_no_input_mutation():
    jobs = [{'route':'time','reference_hour':12,'amplitude_k':0,'peak_hour':12,
             'observations':[{'lst_k':300,'hour':6}]}, {'route':'retrieval'}, None]
    original = copy.deepcopy(jobs)
    r = run_batch({'jobs':jobs})
    assert [j['status'] for j in r['jobs']] == ['done','failed','failed']
    assert r['jobs'][0]['result']['observations'][0]['normalized_k'] == 300
    assert jobs == original
    json.dumps(r, allow_nan=False)


def test_batch_malformed_angle_does_not_interrupt_later_job():
    angle = {'route':'normalization', 'coefficient_mode':'fit', 'reference_vza':0,
             'observations':[{'sensor':'SLSTR','lst_k':300,'vza':v,'time_utc':123} for v in [0,60]]}
    time = {'route':'time','reference_hour':12,'amplitude_k':0,'peak_hour':12,
            'observations':[{'lst_k':300,'hour':6}]}
    r = run_batch({'jobs':[angle,time]})
    assert [j['status'] for j in r['jobs']] == ['failed','done']
