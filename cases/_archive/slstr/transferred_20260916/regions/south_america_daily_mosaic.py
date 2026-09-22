#!/usr/bin/env python3
"""Project existing SLSTR LST scenes to the South America grid and mosaic by UTC day.

The input products in ``slstr-southA-lst`` are geolocation arrays without a
geotransform.  This script performs the geolocation-to-grid reprojection
directly, then accumulates valid observations into a daily mean mosaic.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

# Prefer the system PROJ database when the conda environment has no local
# ``share/proj`` directory.  The products are written in EPSG:4326 and do not
# require a datum transformation, but GDAL still consults PROJ while writing
# CRS metadata.
if os.path.isdir("/usr/share/proj"):
    os.environ["PROJ_LIB"] = "/usr/share/proj"

from osgeo import gdal


SCENE_DATE_RE = re.compile(r"RBT____(\d{8})T")
DEFAULT_ROOT = Path("/media/hero/slstr-southA-lst")
DEFAULT_REGION = Path(__file__).with_name("south_america_tropical_amazon.geojson")
DEFAULT_OUTPUT = DEFAULT_ROOT / "south_america_tropical_daily_0p01"


def read_band(path: Path, band: int = 1) -> np.ndarray:
    dataset = gdal.Open(str(path), gdal.GA_ReadOnly)
    if dataset is None:
        raise RuntimeError(f"Cannot open raster: {path}")
    array = dataset.GetRasterBand(band).ReadAsArray()
    dataset = None
    return np.asarray(array)


def load_region(path: Path) -> dict[str, float]:
    with path.open(encoding="utf-8") as fp:
        collection = json.load(fp)
    feature = next(
        f for f in collection["features"]
        if f["properties"].get("role") == "final_output_window"
    )
    props = feature["properties"]
    return {key: float(props[key]) for key in ("west", "east", "south", "north", "grid_resolution_degree")}


def scene_date(scene_name: str) -> date | None:
    match = SCENE_DATE_RE.search(scene_name)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%Y%m%d").date()


def scale_geolocation(array: np.ndarray) -> np.ndarray:
    array = np.asarray(array)
    if np.issubdtype(array.dtype, np.integer) or np.nanmax(np.abs(array)) > 180:
        return array.astype(np.float32) / 100.0
    return array.astype(np.float32)


def discover_scenes(root: Path, start: date | None, end: date | None) -> dict[date, list[tuple[Path, Path]]]:
    grouped: dict[date, list[tuple[Path, Path]]] = defaultdict(list)
    for year_dir in sorted(root.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        year_value = int(year_dir.name)
        if start and year_value < start.year:
            continue
        if end and year_value > end.year:
            continue
        tif_dir = year_dir / "tif"
        lst_dir = year_dir / "lst"
        if not tif_dir.is_dir() or not lst_dir.is_dir():
            continue
        year_count = 0
        # The LST tree is the authoritative product index.  Scanning it once
        # avoids repeated stat calls on the much larger geolocation tree.
        for scene_entry in os.scandir(lst_dir):
            if not scene_entry.is_dir():
                continue
            day = scene_date(scene_entry.name)
            if day is None or (start and day < start) or (end and day > end):
                continue
            scene_lst = Path(scene_entry.path)
            if not (scene_lst / "lst_nadir.tif").exists():
                continue
            scene_tif = tif_dir / scene_entry.name
            if not scene_tif.exists():
                continue
            grouped[day].append((scene_tif, scene_lst))
            year_count += 1
        print(f"scanned {year_dir.name}: {year_count} LST scenes", flush=True)
    return dict(sorted(grouped.items()))


def intersects_region(lat: np.ndarray, lon: np.ndarray, region: dict[str, float], stride: int = 20) -> bool:
    lat_s = lat[::stride, ::stride]
    lon_s = lon[::stride, ::stride]
    valid = np.isfinite(lat_s) & np.isfinite(lon_s)
    if not np.any(valid):
        return False
    return bool(
        np.any(
            valid
            & (lon_s >= region["west"])
            & (lon_s < region["east"])
            & (lat_s > region["south"])
            & (lat_s <= region["north"])
        )
    )


def accumulate_scene(
    scene_tif: Path,
    scene_lst: Path,
    sum_grid: np.ndarray,
    count_grid: np.ndarray,
    region: dict[str, float],
    view: str,
) -> tuple[int, int]:
    modes = ("nadir", "obliq") if view == "all" else (view,)
    observations = 0
    used_modes = 0
    height, width = sum_grid.shape
    res = region["grid_resolution_degree"]

    for mode in modes:
        coord_suffix = mode
        lat_path = scene_tif / f"lat_{coord_suffix}.tif"
        lon_path = scene_tif / f"lon_{coord_suffix}.tif"
        value_path = scene_lst / f"lst_{mode}.tif"
        if not lat_path.is_file() or not lon_path.is_file() or not value_path.is_file():
            continue

        lat = scale_geolocation(read_band(lat_path))
        lon = scale_geolocation(read_band(lon_path))
        values = read_band(value_path).astype(np.float32) / 100.0
        if lat.shape != values.shape or lon.shape != values.shape:
            continue
        if not intersects_region(lat, lon, region):
            continue

        valid = (
            np.isfinite(lat) & np.isfinite(lon) & np.isfinite(values)
            & (values > 0)
            & (lon >= region["west"]) & (lon < region["east"])
            & (lat > region["south"]) & (lat <= region["north"])
        )
        if not np.any(valid):
            continue

        rows = np.floor((region["north"] - lat[valid]) / res).astype(np.int64)
        cols = np.floor((lon[valid] - region["west"]) / res).astype(np.int64)
        inside = (rows >= 0) & (rows < height) & (cols >= 0) & (cols < width)
        if not np.any(inside):
            continue
        rows = rows[inside]
        cols = cols[inside]
        vals = values[valid][inside]

        # Aggregate in the scene's small footprint first.  Writing a local
        # dense window is much faster than random updates into the full
        # continental grid, while retaining the same per-pixel mean.
        row0, row1 = int(rows.min()), int(rows.max())
        col0, col1 = int(cols.min()), int(cols.max())
        local_width = col1 - col0 + 1
        local_height = row1 - row0 + 1
        local_index = (rows - row0) * local_width + (cols - col0)
        local_size = local_width * local_height
        local_sum = np.bincount(local_index, weights=vals, minlength=local_size).astype(np.float32)
        local_count = np.bincount(local_index, minlength=local_size).astype(np.uint32)
        sum_grid[row0:row1 + 1, col0:col1 + 1] += local_sum.reshape(local_height, local_width)
        count_grid[row0:row1 + 1, col0:col1 + 1] += local_count.reshape(local_height, local_width)
        observations += int(vals.size)
        used_modes += 1

    return observations, used_modes


def write_raster(path: Path, data: np.ndarray, region: dict[str, float], nodata: float = 0.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width = data.shape
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(
        str(path), width, height, 1, gdal.GDT_Float32,
        options=["TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=IF_SAFER"],
    )
    if dataset is None:
        raise RuntimeError(f"Cannot create raster: {path}")
    dataset.SetGeoTransform((region["west"], region["grid_resolution_degree"], 0.0,
                             region["north"], 0.0, -region["grid_resolution_degree"]))
    # Keep the WKT self-contained: some production environments do not have
    # the PROJ database installed even though the GeoTIFF driver is available.
    dataset.SetProjection(
        'GEOGCS["WGS 84",DATUM["WGS_1984",'
        'SPHEROID["WGS 84",6378137,298.257223563]],'
        'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
    )
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(nodata)
    band.WriteArray(data.astype(np.float32, copy=False))
    band.FlushCache()
    dataset.FlushCache()
    dataset = None


def parse_date(value: str | None) -> date | None:
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--region-file", type=Path, default=DEFAULT_REGION)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--view", choices=("all", "nadir", "obliq"), default="all")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    region = load_region(args.region_file)
    start, end = parse_date(args.start_date), parse_date(args.end_date)
    if start and end and end < start:
        raise SystemExit("--end-date must not be before --start-date")
    grouped = discover_scenes(args.source_root, start, end)
    if not grouped:
        raise SystemExit("No usable LST scenes found for the requested date range")

    width = int(round((region["east"] - region["west"]) / region["grid_resolution_degree"]))
    height = int(round((region["north"] - region["south"]) / region["grid_resolution_degree"]))
    manifest = {
        "source_root": str(args.source_root),
        "region_file": str(args.region_file),
        "output_root": str(args.output_root),
        "product": "LST",
        "view": args.view,
        "target_crs": "EPSG:4326",
        "bounds_west_east_south_north": [region["west"], region["east"], region["south"], region["north"]],
        "grid_resolution_degree": region["grid_resolution_degree"],
        "width": width,
        "height": height,
        "daily_key": "UTC acquisition date",
        "days": {},
    }
    args.output_root.mkdir(parents=True, exist_ok=True)

    print(f"target grid: {width} x {height}, days: {len(grouped)}")
    for day, scenes in grouped.items():
        output_path = args.output_root / str(day.year) / f"{day:%Y%m%d}_lst_daily.tif"
        count_path = args.output_root / str(day.year) / f"{day:%Y%m%d}_lst_count.tif"
        if output_path.exists() and count_path.exists() and not args.overwrite:
            print(f"skip existing {day}")
            manifest["days"][day.isoformat()] = {"status": "existing"}
            continue

        sums = np.zeros((height, width), dtype=np.float32)
        counts = np.zeros((height, width), dtype=np.uint32)
        used_scenes = 0
        observations = 0
        modes = 0
        print(f"{day}: {len(scenes)} scenes")
        for index, (scene_tif, scene_lst) in enumerate(scenes, start=1):
            n_obs, n_modes = accumulate_scene(scene_tif, scene_lst, sums, counts, region, args.view)
            if n_obs:
                used_scenes += 1
                observations += n_obs
                modes += n_modes
            if index % 20 == 0 or index == len(scenes):
                print(f"  {index}/{len(scenes)} scenes, used={used_scenes}, observations={observations}")

        mosaic = np.zeros_like(sums)
        valid = counts > 0
        mosaic[valid] = sums[valid] / counts[valid]
        write_raster(output_path, mosaic, region)
        write_raster(count_path, counts.astype(np.float32), region)
        manifest["days"][day.isoformat()] = {
            "status": "written",
            "input_scenes": len(scenes),
            "used_scenes": used_scenes,
            "observations": observations,
            "valid_pixels": int(np.count_nonzero(valid)),
            "max_count": int(counts.max()),
            "output": str(output_path),
            "count_output": str(count_path),
        }

    with (args.output_root / "manifest.json").open("w", encoding="utf-8") as fp:
        json.dump(manifest, fp, ensure_ascii=False, indent=2)
    print(f"manifest: {args.output_root / 'manifest.json'}")


if __name__ == "__main__":
    main()
