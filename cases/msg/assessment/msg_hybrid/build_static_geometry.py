"""Build reusable MSG-grid coordinates and three declared-slot VZA/VAA pairs.

Writes auxiliary geometry only, never component-temperature products.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os

import h5py
import numpy as np
from osgeo import gdal, osr
import msg_view_geometry as geometry

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(reference, plan, output, tile_rows=128):
    if tile_rows < 1:
        raise ValueError('tile_rows must be positive')
    if geometry.sha(geometry.__file__) != plan['geometry_helper_sha256']:
        raise ValueError('Geometry helper changed; update reviewed plan first')
    dataset = gdal.Open(str(reference), gdal.GA_ReadOnly)
    if dataset is None:
        raise ValueError('Cannot read reference MSG grid')
    height, width = dataset.RasterYSize, dataset.RasterXSize
    crs = osr.SpatialReference()
    crs.ImportFromWkt(dataset.GetProjection())
    expected = osr.SpatialReference()
    expected.ImportFromEPSG(4326)
    if (height, width) != (3333, 2633) or not crs.IsSame(expected):
        raise ValueError('Static geometry must use the MSG 3333x2633 EPSG:4326 grid')
    grid = {'shape': [height, width], 'GeoTransform': list(dataset.GetGeoTransform()),
            'Projection': dataset.GetProjection(), 'EPSG': 4326}
    dataset = None
    for declaration in plan['declarations'].values():
        source = Path(declaration['path'])
        if sha(source) != declaration['sha256'] or source.stat().st_size != declaration['bytes']:
            raise ValueError('Static declaration source changed: '+str(source))
    output = Path(output).resolve()
    protected = [Path(reference).resolve()] + [Path(d['path']).resolve() for d in plan['declarations'].values()]
    if output in protected:
        raise ValueError('Auxiliary output must not overwrite a reference source')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(output)+'.partial')
    gt = grid['GeoTransform']
    options = dict(shape=(height, width), dtype='float64', chunks=(min(tile_rows, height), 256),
                   compression='gzip', compression_opts=4, shuffle=True, fletcher32=True)
    with h5py.File(temporary, 'w') as file:
        file.attrs.update(grid_json=json.dumps(grid, sort_keys=True),
                          target_pixel_reference='legacy_pixel_corner_coordinates_supplied_by_producer',
                          helper_sha256=sha(geometry.__file__), builder_sha256=sha(__file__),
                          satellite_geocentric_radius_m=geometry.SATELLITE_GEOCENTRIC_RADIUS_M,
                          ground_ellipsoid='WGS84', ground_height_m=0.,
                          azimuth_convention='ground_to_satellite_north_0_east_90_0_to_360',
                          purpose='static auxiliary geometry; not an LS4T temperature product')
        coordinates = file.create_group('geolocation')
        latitude = coordinates.create_dataset('latitude', **options)
        longitude = coordinates.create_dataset('longitude', **options)
        latitude.attrs['units'], longitude.attrs['units'] = 'degrees_north', 'degrees_east'
        pairs = {}
        for key, declaration in plan['declarations'].items():
            group = file.create_group(key)
            group.attrs.update(latitude_deg=0., longitude_deg=declaration['orbital_slot_longitude_deg'],
                               declaration_json=json.dumps(declaration, sort_keys=True))
            pairs[key] = (group.create_dataset('vza', **options), group.create_dataset('vaa', **options))
            for field in pairs[key]:
                field.attrs['units'] = 'degree'
        columns = np.arange(width)[None, :]
        for y in range(0, height, tile_rows):
            end = min(height, y+tile_rows)
            rows = np.arange(y, end)[:, None]
            lon = gt[0]+columns*gt[1]+rows*gt[2]
            lat = gt[3]+columns*gt[4]+rows*gt[5]
            latitude[y:end], longitude[y:end] = lat, lon
            for key, declaration in plan['declarations'].items():
                vza, vaa = geometry.look_angles(lat, lon, 0., declaration['orbital_slot_longitude_deg'])
                pairs[key][0][y:end], pairs[key][1][y:end] = vza, vaa
            if y % (tile_rows*8) == 0:
                print(f'GEOMETRY rows {end}/{height}', flush=True)
        file.attrs['complete'] = 1
    os.replace(temporary, output)
    return {'file': str(output), 'sha256': sha(output), 'bytes': output.stat().st_size, 'grid': grid}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=HERE/'geometry_plan.json')
    parser.add_argument('--reference', type=Path, default=Path('E:/Static/combined_euro_vza.tif'))
    parser.add_argument('--output', type=Path, default=HERE/'static_geometry.h5')
    args = parser.parse_args()
    print(json.dumps(build(args.reference, json.loads(args.plan.read_text(encoding='utf8')), args.output),
                     ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
