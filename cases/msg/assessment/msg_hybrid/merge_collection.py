"""Snapshot controller metadata; import equivalent static scenes; keep old bytes."""
from pathlib import Path
from types import SimpleNamespace
import argparse
import json
import os
import shutil

import produce_msg_ls4t as p

HERE = Path(__file__).resolve().parent


def prepare(root, static_root, input_root):
    args = SimpleNamespace(input_root=input_root, geometry_module=HERE/'msg_view_geometry.py',
        geometry_plan=HERE/'geometry_plan.json', legacy_case_root=Path('C:/work/ls4t-msg/cases/official'))
    p.assert_code_review(HERE/'independent_code_review.json', args.geometry_module, args.geometry_plan)
    review = json.loads((HERE/'independent_code_review.json').read_text(encoding='utf8'))
    if review['reviewed_files'].get('merge_collection.py') != p.sha(__file__):
        raise RuntimeError('Collection migration code changed after review')
    identity, plan = p.build_identity(args, p.grid_info(input_root))
    provider = p.load_geometry_module(args.geometry_module)
    with p.production_lock(root):
        old = json.loads((root/'production_identity.json').read_text(encoding='utf8'))
        expected = (dict(identity, protocol=p.PROTOCOL) if old['identity_hash'] == identity['identity_hash']
                    else identity['compatible_legacy_identities'].get(old['identity_hash']))
        if old != expected:
            raise RuntimeError('Collection identity is not an exact approved predecessor')
        provenance = root/'_PROVENANCE'/'unification_20261012'
        for source, label in [(root, 'dynamic_phase'), (static_root, 'static_phase')]:
            snapshot = provenance/label
            snapshot.mkdir(parents=True, exist_ok=True)
            for name in ['production_identity.json','status.json','inventory.json','eligible_inventory.json',
                         'scene_manifest.jsonl','monthly_manifest.jsonl','failed_scenes.json',
                         'failed_monthly_groups.json','deferred_geometry.json','missing_inputs.json',
                         'static_source_manifest.json']:
                src, dst = source/name, snapshot/name
                if src.is_file() and not dst.exists():
                    shutil.copy2(src, dst)
                    if p.sha(src) != p.sha(dst):
                        raise RuntimeError('Provenance snapshot hash mismatch')
        journal = provenance/'import_manifest.jsonl'
        committed = sorted((static_root/'INSTANTANEOUS').rglob('*.h5.complete.json'))
        imported = rejected = present = 0
        for marker in committed:
            record = json.loads(marker.read_text(encoding='utf8'))
            stamp = record['timestamp']
            hdf, tif = p.instant_path(root, stamp), p.scene_tif_path(root, stamp)
            geometry = provider.geometry_metadata(stamp, plan)
            inputs = p.file_manifest(p.paths(stamp, input_root).values())
            context = {'inputs':inputs, 'geometry':geometry}
            signature = p.hash_object(context)
            if p.commit_path(hdf).is_file():
                if p.check_resume(hdf, tif, identity, signature, context=context) is None:
                    raise RuntimeError('Existing same-time product is incompatible: '+stamp)
                present += 1
                continue
            verified = p.check_resume(Path(record['hdf5']), Path(record['geotiff']), identity,
                                      signature, context=context)
            if verified is None:
                rejected += 1
                p.append_json(journal, {'timestamp':stamp, 'status':'requires_recomputation'})
                continue
            original_marker = provenance/'static_markers'/marker.name
            original_marker.parent.mkdir(parents=True, exist_ok=True)
            if not original_marker.exists():
                shutil.copy2(marker, original_marker)
            for source, destination in [(Path(record['hdf5']), hdf), (Path(record['geotiff']), tif)]:
                destination.parent.mkdir(parents=True, exist_ok=True)
                temporary = Path(str(destination)+'.partial')
                shutil.copy2(source, temporary)
                if p.sha(temporary) != record['files'][str(source)]['sha256']:
                    raise RuntimeError('Imported product hash mismatch')
                if destination.exists():
                    if p.sha(destination) != p.sha(temporary):
                        raise RuntimeError('Refusing to overwrite a different existing output')
                    temporary.unlink()
                else:
                    os.replace(temporary, destination)
            migrated = dict(record, hdf5=str(hdf), geotiff=str(tif),
                files={str(hdf):record['files'][record['hdf5']], str(tif):record['files'][record['geotiff']]},
                import_provenance={'original_marker':str(original_marker), 'original_marker_sha256':p.sha(original_marker),
                                   'original_root':str(static_root)},
                validated_collection_identity=identity['identity_hash'], canonical_source_signature=signature,
                geometry_modes=geometry['geometry_modes'])
            p.atomic_json(p.commit_path(hdf), migrated)  # Commit only after both byte-exact copies.
            p.append_json(root/'scene_manifest.jsonl', dict(migrated, status='imported', updated_UTC=p.now()))
            p.append_json(journal, {'timestamp':stamp, 'status':'imported', 'files':migrated['files']})
            imported += 1
            if imported % 50 == 0:
                print('IMPORTED', imported, '/', len(committed), flush=True)
        p.atomic_json(root/'production_identity.json', dict(identity, protocol=p.PROTOCOL))
        p.atomic_json(root/'static_source_manifest.json', {'files':identity['static_sources']})
        report = {'status':'ready', 'checked_UTC':p.now(), 'identity_hash':identity['identity_hash'],
                  'imported_static_scenes':imported, 'already_present':present,
                  'requires_recomputation':rejected, 'static_committed_scenes':len(committed),
                  'monthly_policy':'Do not import static monthly outputs; regenerate from unified validated scenes',
                  'source_product_bytes_unchanged':True, 'root':str(root)}
        p.atomic_json(provenance/'migration_report.json', report)
        p.atomic_json(HERE/'production_frozen_identity.json', dict(identity, protocol=p.PROTOCOL))
        print(p.json_text(report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=p.DEFAULT_ROOT)
    parser.add_argument('--static-root', type=Path, default=Path('E:/PRODUCTS/LSCT/MSG_LS4T_H025_5X5_DECLARED_V1'))
    parser.add_argument('--input-root', type=Path, default=Path('E:/'))
    args = parser.parse_args()
    prepare(args.root.resolve(), args.static_root.resolve(), args.input_root.resolve())
