#!/usr/bin/env python3
"""Project one or more SLSTR UTC days with PROJ and mosaic nadir/oblique LST.

Unlike the degree-grid prototype, this version explicitly transforms every
valid geolocation with pyproj/PROJ from WGS84 (EPSG:4326) to a projected CRS.
The target grid is EPSG:6933 at a 1 km cell size by default.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

import numpy as np

# Make the same PROJ database visible to pyproj and GDAL before either library
# is imported.  This keeps EPSG:6933 metadata authoritative on this system.
if os.path.isdir("/usr/share/proj"):
    os.environ["PROJ_LIB"] = "/usr/share/proj"
    os.environ["PROJ_DATA"] = "/usr/share/proj"

from pyproj import CRS, Transformer
from osgeo import gdal

from south_america_daily_mosaic import (
    discover_scenes,
    intersects_region,
    load_region,
    parse_date,
    read_band,
    scale_geolocation,
)


DEFAULT_REGION = Path(__file__).with_name("south_america_tropical_amazon.geojson")
DEFAULT_ROOT = Path("/media/hero/slstr-southA-lst")
DEFAULT_OUTPUT = Path("/home/hero/work/ls4t/cases/slstr/regions/proj_test_output")


def projected_bounds(region: dict[str, float], transformer: Transformer) -> tuple[float, float, float, float]:
    """Return projected bounds for the four corners of the lon/lat window."""
    lon = np.array([region["west"], region["east"], region["west"], region["east"]], dtype=float)
    lat = np.array([region["south"], region["south"], region["north"], region["north"]], dtype=float)
    x, y = transformer.transform(lon, lat)
    return float(x.min()), float(x.max()), float(y.min()), float(y.max())


def accumulate_scene_projected(
    scene_tif: Path,
    scene_lst: Path,
    sums: np.ndarray,
    counts: np.ndarray,
    region: dict[str, float],
    transformer: Transformer,
    grid: tuple[float, float, float, float, float],
    mode: str,
) -> tuple[int, int]:
    """Transform one view's pixels and aggregate them into the projected grid."""
    lat_path = scene_tif / f"lat_{mode}.tif"
    lon_path = scene_tif / f"lon_{mode}.tif"
    value_path = scene_lst / f"lst_{mode}.tif"
    if not lat_path.is_file() or not lon_path.is_file() or not value_path.is_file():
        return 0, 0

    lat = scale_geolocation(read_band(lat_path))
    lon = scale_geolocation(read_band(lon_path))
    values = read_band(value_path).astype(np.float32) / 100.0
    if lat.shape != values.shape or lon.shape != values.shape:
        return 0, 0
    if not intersects_region(lat, lon, region):
        return 0, 0

    valid = (
        np.isfinite(lat) & np.isfinite(lon) & np.isfinite(values)
        & (values > 0)
        & (lon >= region["west"]) & (lon < region["east"])
        & (lat > region["south"]) & (lat <= region["north"])
    )
    if not np.any(valid):
        return 0, 0

    # This is the explicit PROJ operation: lon/lat -> projected x/y metres.
    x, y = transformer.transform(lon[valid], lat[valid])
    xmin, xmax, ymin, ymax, resolution = grid
    rows = np.floor((ymax - y) / resolution).astype(np.int64)
    cols = np.floor((x - xmin) / resolution).astype(np.int64)
    height, width = sums.shape
    inside = (rows >= 0) & (rows < height) & (cols >= 0) & (cols < width)
    if not np.any(inside):
        return 0, 0
    rows, cols = rows[inside], cols[inside]
    vals = values[valid][inside]

    row0, row1 = int(rows.min()), int(rows.max())
    col0, col1 = int(cols.min()), int(cols.max())
    local_width = col1 - col0 + 1
    local_height = row1 - row0 + 1
    local_index = (rows - row0) * local_width + (cols - col0)
    local_size = local_width * local_height
    local_sum = np.bincount(local_index, weights=vals, minlength=local_size).astype(np.float32)
    local_count = np.bincount(local_index, minlength=local_size).astype(np.uint32)
    sums[row0:row1 + 1, col0:col1 + 1] += local_sum.reshape(local_height, local_width)
    counts[row0:row1 + 1, col0:col1 + 1] += local_count.reshape(local_height, local_width)
    return int(vals.size), 1


def write_raster(path: Path, data: np.ndarray, crs: CRS, geotransform: tuple[float, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataset = gdal.GetDriverByName("GTiff").Create(
        str(path), data.shape[1], data.shape[0], 1, gdal.GDT_Float32,
        options=["TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=IF_SAFER"],
    )
    if dataset is None:
        raise RuntimeError(f"Cannot create raster: {path}")
    dataset.SetGeoTransform(geotransform)
    dataset.SetProjection(crs.to_wkt())
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(0.0)
    band.WriteArray(data.astype(np.float32, copy=False))
    band.FlushCache()
    dataset.FlushCache()
    dataset = None


def run_day(
    day: date,
    scenes: list[tuple[Path, Path]],
    args: argparse.Namespace,
    region: dict[str, float],
    crs: CRS,
    transformer: Transformer,
    grid: tuple[float, float, float, float, float],
    geotransform: tuple[float, ...],
) -> dict[str, dict]:
    xmin, xmax, ymin, ymax, resolution = grid
    width = int(np.ceil((xmax - xmin) / resolution))
    height = int(np.ceil((ymax - ymin) / resolution))
    outputs: dict[str, dict] = {}
    modes = ("nadir", "obliq") if args.view == "all" else (args.view,)
    for mode in modes:
        output_dir = args.output_root / str(day.year) / mode
        output_path = output_dir / f"{day:%Y%m%d}_lst_daily_{mode}.tif"
        count_path = output_dir / f"{day:%Y%m%d}_lst_count_{mode}.tif"
        if output_path.exists() and count_path.exists() and not args.overwrite:
            print(f"{day} {mode}: skip existing", flush=True)
            continue

        sums = np.zeros((height, width), dtype=np.float32)
        counts = np.zeros((height, width), dtype=np.uint32)
        used_scenes = 0
        observations = 0
        print(f"{day} {mode}: {len(scenes)} scenes, grid={width}x{height}", flush=True)
        for index, (scene_tif, scene_lst) in enumerate(scenes, start=1):
            n_obs, n_modes = accumulate_scene_projected(
                scene_tif, scene_lst, sums, counts, region, transformer, grid, mode
            )
            if n_obs:
                used_scenes += 1
                observations += n_obs
            if index % 20 == 0 or index == len(scenes):
                print(f"  {index}/{len(scenes)} scenes, used={used_scenes}, observations={observations}", flush=True)

        mosaic = np.zeros_like(sums)
        valid = counts > 0
        mosaic[valid] = sums[valid] / counts[valid]
        write_raster(output_path, mosaic, crs, geotransform)
        write_raster(count_path, counts.astype(np.float32), crs, geotransform)
        outputs[mode] = {
            "output": str(output_path),
            "count_output": str(count_path),
            "input_scenes": len(scenes),
            "used_scenes": used_scenes,
            "observations": observations,
            "valid_pixels": int(np.count_nonzero(valid)),
            "max_count": int(counts.max()),
        }
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--region-file", type=Path, default=DEFAULT_REGION)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--start-date", default="2017-01-18")
    parser.add_argument("--end-date", default="2017-01-18")
    parser.add_argument("--view", choices=("all", "nadir", "obliq"), default="all")
    parser.add_argument("--target-crs", default="EPSG:6933")
    parser.add_argument("--resolution-m", type=float, default=1000.0)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    region = load_region(args.region_file)
    start, end = parse_date(args.start_date), parse_date(args.end_date)
    grouped = discover_scenes(args.source_root, start, end)
    if not grouped:
        raise SystemExit("No usable LST scenes found for the requested date range")

    source_crs = CRS.from_epsg(4326)
    target_crs = CRS.from_user_input(args.target_crs)
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    xmin, xmax, ymin, ymax = projected_bounds(region, transformer)
    resolution = float(args.resolution_m)
    width = int(np.ceil((xmax - xmin) / resolution))
    height = int(np.ceil((ymax - ymin) / resolution))
    grid = (xmin, xmax, ymin, ymax, resolution)
    geotransform = (xmin, resolution, 0.0, ymax, 0.0, -resolution)

    args.output_root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source_crs": source_crs.to_string(),
        "target_crs": target_crs.to_string(),
        "target_crs_wkt": target_crs.to_wkt(),
        "resolution_m": resolution,
        "projected_bounds_xy": [xmin, xmax, ymin, ymax],
        "width": width,
        "height": height,
        "days": {},
    }
    print(f"PROJ transformation: {source_crs.to_string()} -> {target_crs.to_string()}", flush=True)
    print(f"target grid: {width} x {height} at {resolution:g} m", flush=True)
    for day, scenes in grouped.items():
        manifest["days"][day.isoformat()] = run_day(
            day, scenes, args, region, target_crs, transformer, grid, geotransform
        )
    with (args.output_root / "manifest.json").open("w", encoding="utf-8") as fp:
        json.dump(manifest, fp, ensure_ascii=False, indent=2)
    print(f"manifest: {args.output_root / 'manifest.json'}")


if __name__ == "__main__":
    main()
