"""Read-only evidence for two legacy scenes; never transfers products."""
from pathlib import Path
import datetime as dt
import hashlib
import json

import h5py
from osgeo import gdal
import msg_view_geometry as geometry
import produce_msg_ls4t as producer

HERE = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    plan = json.loads((HERE / 'geometry_plan.json').read_text(encoding='utf8'))
    evidence = []
    scenarios = [(Path('E:/PRODUCTS/LSCT/MSG_LS4T_H025_5X5_V1'), '202407151200', 'dynamic'),
                 (Path('E:/PRODUCTS/LSCT/MSG_LS4T_H025_5X5_DECLARED_V1'), '201708041200', 'static')]
    model_keys = ['satellite_geocentric_radius_m', 'ground_ellipsoid', 'ground_height_m',
                  'target_pixel_reference', 'azimuth_convention', 'iodc_native_grid_longitude_deg']
    for root, stamp, expected_mode in scenarios:
        hdf, tif = producer.instant_path(root, stamp), producer.scene_tif_path(root, stamp)
        record = json.loads(producer.commit_path(hdf).read_text(encoding='utf8'))
        collection = json.loads((root / 'production_identity.json').read_text(encoding='utf8'))
        with h5py.File(hdf, 'r') as file:
            assert int(file.attrs['complete']) == 1
            assert file.attrs['identity_hash'] == record['identity_hash'] == collection['identity_hash']
            assert file.attrs['source_signature'] == record['source_signature']
            inputs = json.loads(file.attrs['inputs_json'])
            old_geometry = json.loads(file.attrs['geometry_json'])
            assert old_geometry == record['geometry']
        assert producer.hash_object({'inputs': inputs, 'geometry': old_geometry}) == record['source_signature']
        assert inputs == producer.file_manifest(producer.paths(stamp, Path('E:/')).values())
        for file in [hdf, tif]:
            assert sha(file) == record['files'][str(file)]['sha256']
            assert file.stat().st_size == record['files'][str(file)]['bytes']
        raster = gdal.Open(str(tif), gdal.GA_ReadOnly)
        assert raster.GetMetadataItem('IDENTITY_HASH') == record['identity_hash']
        raster = None
        selected = geometry.geometry_metadata(stamp, plan)
        for key in model_keys:
            assert selected[key] == old_geometry[key], 'Geometry model differs: ' + key
        for view in ['e', 'i']:
            assert selected['geometry_modes'][view] == expected_mode
            for key in ['latitude_deg', 'longitude_deg']:
                assert selected['positions'][view][key] == old_geometry['positions'][view][key]
        evidence.append({'timestamp': stamp, 'source_root': str(root),
            'calculation_identity_hash': record['identity_hash'],
            'original_source_signature': record['source_signature'], 'selected_modes': selected['geometry_modes'],
            'model_and_positions_exactly_equal': True, 'input_and_output_sha256_verified': True,
            'marker_sha256': sha(producer.commit_path(hdf)), 'identity_file_sha256': sha(root / 'production_identity.json')})
    result = {'status': 'PASS', 'reviewed_UTC': dt.datetime.now(dt.timezone.utc).isoformat(),
        'scope': 'Two real legacy scene read-only evidence samples; does not authorize unverified scene reuse or migration.',
        'scenes': evidence, 'geometry_helper_sha256': sha(HERE / 'msg_view_geometry.py'),
        'geometry_plan_sha256': sha(HERE / 'geometry_plan.json')}
    output = HERE / 'legacy_reuse_evidence_review.json'
    output.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
