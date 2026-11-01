import json
from pathlib import Path
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import pytest
import numpy as np

from gui.server import Handler
from base.radiometry import planck_radiance, inverse_planck


@pytest.fixture
def service():
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    server.server_close()
    thread.join()


def test_sample_api_roundtrip_and_bad_request(service):
    with urlopen(service+'/api/workbench/sample') as r:
        payload = json.load(r)
    request = Request(service+'/api/workbench/run', data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
    with urlopen(request) as r:
        result = json.load(r)
    assert result['fit_count'] == 2 and result['heldout_count'] == 1
    assert result['fixed'] == payload['fixed']
    assert result['heldout_rmse_k'] == pytest.approx(.3236851116416233, abs=1e-5)
    payload['fixed']['lai'] = -1
    with pytest.raises(HTTPError) as error:
        urlopen(Request(service+'/api/workbench/run', data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'}))
    assert error.value.code == 400
    assert 'LAI' in json.load(error.value)['error']
    with urlopen(service+'/') as r:
        assert 'home.js' in r.read().decode()
    with urlopen(service+'/batch.html') as r:
        assert 'app.js' in r.read().decode()


def test_workspace_pages_and_tool_endpoints(service):
    for path, script in [('/retrieval','home.js'),('/normalization','home.js'),
                         ('/retrieval/surface','workbench.js'),('/retrieval/components','workbench.js'),
                         ('/retrieval/batch','app.js'),('/normalization/angle','workbench.js'),
                         ('/normalization/time','normalize.js'),('/normalization/space','normalize.js'),
                         ('/normalization/batch','normalize.js')]:
        with urlopen(service+path) as response:
            html=response.read().decode()
        assert script in html and 'navigation.js' in html
    payload={'route':'time','reference_hour':12,'amplitude_k':0,'peak_hour':12,
             'observations':[{'lst_k':300,'hour':6}]}
    for path,p in [('/api/time/run',payload),('/api/space/run',{'target_shape':[1,2],
        'observations':[{'lst_k':300,'row':0,'column':0}]}),('/api/normalization/batch',{'jobs':[payload]})]:
        with urlopen(Request(service+path,data=json.dumps(p).encode(),headers={'Content-Type':'application/json'})) as response:
            assert json.load(response)['schema'].startswith('ls4t.')
    with urlopen(service+'/api/workbench/sample') as response:
        p=json.load(response)
    with urlopen(Request(service+'/api/surface/run',data=json.dumps(p).encode(),headers={'Content-Type':'application/json'})) as response:
        assert json.load(response)['route']=='surface'
    for path in ['/api/time/run','/api/space/run','/api/surface/run','/api/normalization/batch']:
        with pytest.raises(HTTPError) as error:
            urlopen(Request(service+path,data=b'{}',headers={'Content-Type':'application/json'}))
        assert error.value.code==400


def test_source_pixels_reproduce_brightness_temperature_inputs():
    folder = Path(__file__).resolve().parents[1]/'gui/examples/ahi_slstr'
    payload = json.loads((folder/'sample.json').read_text(encoding='utf-8'))
    with np.load(folder/'source_pixels.npz', allow_pickle=False) as raw:
        for index,view in enumerate(['nadir','obliq']):
            for band,wavelength in [('bt1',10.85),('bt2',12.)]:
                pixels=raw[f'slstr_{band}_{view}']
                assert pixels.shape == (2,2) and np.all(pixels>0)
                expected=float(inverse_planck(wavelength, np.mean(planck_radiance(wavelength,pixels*.01))))
                assert payload['observations'][index][band+'_k'] == pytest.approx(expected, abs=1e-9)
        assert payload['fixed']['lai'] == pytest.approx(raw['lai_raw'].item()*.001)
        assert payload['observations'][2]['bt1_k'] == pytest.approx(raw['ahi_bt1'].item()*.01)


def test_routes_have_independent_inputs_and_outputs(service):
    with urlopen(service+'/api/normalization/sample') as r:
        p=json.load(r)
    assert 'fixed' not in p and 'components' not in p
    assert all('bt1_k' not in o for o in p['observations'])
    with urlopen(Request(service+'/api/normalization/run',data=json.dumps(p).encode(),headers={'Content-Type':'application/json'})) as r:
        result=json.load(r)
    assert result['route']=='normalization' and 'temperature_k' not in result
    assert 'normalized_k' in result['observations'][0]
    with urlopen(service+'/api/workbench/sample') as r:
        p=json.load(r)
    with urlopen(Request(service+'/api/retrieval/run',data=json.dumps(p).encode(),headers={'Content-Type':'application/json'})) as r:
        result=json.load(r)
    assert result['route']=='retrieval' and 'reference_vza' not in result
    assert 'normalized_k' not in result['observations'][0]


def test_legacy_driver_snapshot_hashes_and_imports():
    import hashlib
    from gui.legacy import slstr_lst_scene_parallel, slstr_lsct2_scene_parallel
    folder=Path(__file__).resolve().parents[1]/'gui/legacy'
    for item in json.loads((folder/'SOURCE.json').read_text())['files']:
        assert hashlib.sha256((folder/item['file']).read_bytes()).hexdigest()==item['sha256']
    assert callable(slstr_lst_scene_parallel.process_day)
    assert callable(slstr_lsct2_scene_parallel.process_day)
