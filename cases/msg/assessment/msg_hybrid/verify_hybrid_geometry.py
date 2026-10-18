"""Geometry selection, static-cache reuse and real-source metadata checks only."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
from unittest.mock import patch

import h5py
import numpy as np
import msg_view_geometry as g

HERE = Path(__file__).resolve().parent


def main():
    plan = json.loads((HERE/'geometry_plan.json').read_text(encoding='utf8'))
    assert g.sha(plan['static_geometry_file']) == plan['static_geometry_sha256']
    checks = []
    with h5py.File(plan['static_geometry_file'], 'r') as cache:
        grid = json.loads(cache.attrs['grid_json'])
        lat, lon = cache['geolocation/latitude'][:], cache['geolocation/longitude'][:]
        assert lat.shape == lon.shape == (3333, 2633)
        for y in [0, 128, 1000, 3332]:
            for x in [0, 256, 1300, 2632]:
                gt = grid['GeoTransform']
                assert lon[y,x] == gt[0]+x*gt[1]+y*gt[2]
                assert lat[y,x] == gt[3]+x*gt[4]+y*gt[5]
                for key, declaration in plan['declarations'].items():
                    vza, vaa = g.look_angles(np.array([lat[y,x]]), np.array([lon[y,x]]),
                                             0., declaration['orbital_slot_longitude_deg'])
                    assert cache[key+'/vza'][y,x] == vza[0]
                    assert cache[key+'/vaa'][y,x] == vaa[0]
    checks.append('Precomputed float64 coordinates and all three slot angles equal direct calculation at boundaries/interior')
    with tempfile.TemporaryDirectory(prefix='geometry_fixture_', dir=HERE) as folder:
        p = deepcopy(plan)
        p['input_root'] = folder
        stamp = '202001151200'

        def write(view, latitude, longitude, acquisition=stamp, projection=None):
            file = g.native_path(stamp, view, folder)
            file.parent.mkdir(parents=True, exist_ok=True)
            with h5py.File(file, 'w') as f:
                f.attrs.update(IMAGE_ACQUISITION_TIME=acquisition+'00', MEAN_SSLAT=latitude,
                               MEAN_SSLON=longitude, PROJECTION_NAME=projection or ('GEOS(+000.0)' if view=='e' else 'GEOS(+041.5)'))
            return file

        # Without native metadata both views must use the stored static fields.
        with patch.object(g, 'look_angles', side_effect=AssertionError('Static geometry recalculated')):
            fields, record = g.view_geometry(stamp, lat, lon, {}, p)
            again, second = g.view_geometry(stamp, lat, lon, {}, p)
        assert record['geometry_modes'] == {'e':'static','i':'static'}
        assert fields['vza_e'] is again['vza_e'] and fields['vza_i'] is again['vza_i']
        assert not fields['vza_i'].flags.writeable
        checks.append('Absent dynamic metadata directly loads static auxiliary fields and reuses immutable arrays without recalculation')
        write('e', 0., 0.)
        write('i', -9.4, 41.4)
        mixed = g.geometry_metadata(stamp, p)
        assert mixed['geometry_modes'] == {'e':'static','i':'dynamic'}
        assert mixed['positions']['i']['latitude_deg'] == -9.4
        assert mixed['positions']['e']['fallback_reason'] == 'observed_zero_zero_dynamic_placeholder'
        checks.append('Each view independently chooses dynamic first; no whole-scene static substitution')
        write('e', 0., 0., projection='Geos<000.0>')
        write('i', 0., 0., projection='Geos<000.0>')
        legacy = g.geometry_metadata(stamp, p)
        assert legacy['geometry_modes'] == {'e':'static','i':'static'}
        assert 'generic template' in legacy['positions']['i']['native_source']['projection_note']
        checks.append('Known legacy generic projection template does not block static fallback; explicit slot conflicts remain deferred')
        write('i', -9.4, 41.4)
        write('e', 1., -.2)
        assert g.geometry_metadata(stamp, p)['geometry_modes'] == {'e':'dynamic','i':'dynamic'}
        write('e', float('nan'), float('nan'))
        record = g.geometry_metadata(stamp, p)
        json.dumps(record, allow_nan=False)
        assert record['geometry_modes']['e'] == 'static'
        checks.append('Nonfinite dynamic metadata uses an explicit fallback with a finite JSON signature')
        for view, latitude, longitude, acquisition, projection in [
                ('e', 1., -.2, '202001141200', None),
                ('i', 1., 45.5, stamp, 'GEOS(+045.5)'),
                ('i', 1., 45.5, stamp, 'GEOS(+041.5)')]:
            write(view, latitude, longitude, acquisition, projection)
            try:
                g.geometry_metadata(stamp, p)
                raise AssertionError('Conflicting input geometry was accepted')
            except g.GeometryUnavailable:
                pass
            if view == 'e':
                write('e', 0., 0.)
        checks.append('Acquisition/grid/orbit conflicts deferred rather than hidden by static fallback')
        write('i', -9.4, 41.4)
        g.native_path(stamp, 'e', folder).write_bytes(b'not HDF5')
        try:
            g.geometry_metadata(stamp, p)
            raise AssertionError('Unreadable HDF source was disguised as static fallback')
        except OSError:
            pass
        checks.append('Unreadable orbit metadata remains a source error')
        for date in ['202206011200', '202001151230', '202001150900']:
            try:
                g.geometry_metadata(date, p)
                raise AssertionError('Excluded month/non-hour/outside UTC time accepted')
            except g.GeometryUnavailable:
                pass
        checks.append('Input-geolocation exclusion and UTC 10-16 policy retained')
    real = []
    for stamp in ['201708151200', '202012311200', '202407151200']:
        record = g.geometry_metadata(stamp, plan)
        real.append({'timestamp':stamp, 'modes':record['geometry_modes'],
                     'positions':{view:{key:position[key] for key in ['mode','latitude_deg','longitude_deg','fallback_reason']}
                                  for view,position in record['positions'].items()}})
    assert real[1]['modes'] == {'e':'static','i':'dynamic'}
    report = {'status':'PASS', 'checks':checks, 'real_source_metadata':real,
              'writes':'Only temporary local fixtures and this QA report; no temperature products or source edits',
              'helper_sha256':g.sha(g.__file__), 'static_geometry_sha256':plan['static_geometry_sha256']}
    (HERE/'hybrid_geometry_qa.json').write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=True))


if __name__ == '__main__':
    main()
