#!/usr/bin/env python3
"""Mark SLSTR scenes that cannot contribute to a case window.

A scene-first disk carries whole orbit segments: scenes over open ocean, over
the polar night or simply on the far side of the swath have no pixel that is
both inside the case window and on a land-cover class the retrieval accepts
(``0 < class < 17``).  Retrieving them costs a full scene of I/O and produces
nothing, and every later rerun pays it again.

This script reads the geolocation pair of every scene, keeps three sample bands
(top / middle / bottom, so only ~20 % of each raster is touched), and writes the
useless scenes to ``<scene_root>/_skip/<year>.json``.  The retrieval scripts and
the daily mosaic read that file and leave those scenes alone.

    PYTHONPATH=. python cases/slstr/slstr_scene_coverage.py \
        --case cases/slstr-america --machine hero --year 2018 --write

Nadir and oblique views are judged separately: the LST retrieval needs both, the
LSCT2 retrieval only uses oblique, so a scene can be pointless for one product
and useful for the other.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rasterio.windows import Window  # noqa: E402
import rasterio  # noqa: E402

VIEWS = ("nadir", "obliq")
NODATA = -32768
REQUIRED_BANDS = ("bt8", "bt9", "vza", "lat", "lon")
# Three row bands of 400 rows tile a 1200 row scene exactly, so the decision
# uses every pixel of the geolocation pair.  Cheaper sweeps (3 bands of 80
# rows) were measured against this and marked scenes that really carry up to
# 90 % of the window: a scene whose overlap sits between the sampled bands is
# dropped for no reason, so the full read is what this script does.
SAMPLE_ROWS = 400
SAMPLINGS = ((SAMPLE_ROWS, 3),)


def load_case(case_dir: Path, machine: str) -> dict:
    import tomllib

    case_dir = Path(case_dir).resolve()
    case = tomllib.loads((case_dir / "case.toml").read_text())
    profile = tomllib.loads((case_dir / "machines" / f"{machine}.toml").read_text())
    grid = case["grid"]
    west, south, east, north = (float(v) for v in grid["bounds"])
    paths = profile["paths"]
    return dict(
        case_id=case["case"]["id"],
        region=case["case"].get("region", "region"),
        source_root=Path(paths["scene_root"]),
        window=dict(west=west, east=east, south=south, north=north,
                    res=float(grid.get("resolution_degree", 0.01))),
        type_reference=Path(paths["type_reference"]),
    )


def sample_geo(path: Path, sample_rows: int = SAMPLE_ROWS, bands: int = 3) -> np.ndarray:
    """``bands`` evenly spaced row bands of a geolocation band, in degrees.

    The nodata value is *kept*: latitude and longitude have to be filtered with
    one shared mask, otherwise the two arrays shrink by different amounts and
    stop being pixel aligned.
    """
    with rasterio.open(path) as ds:
        height, width = ds.height, ds.width
        rows = min(sample_rows, max(1, height // bands))
        if bands < 2:
            starts = [0]
        else:
            step = (height - rows) / (bands - 1)
            starts = [int(round(i * step)) for i in range(bands)]
        blocks = [ds.read(1, window=Window(0, y, width, min(rows, height - y)))
                  for y in starts]
    return np.concatenate([b.ravel() for b in blocks]).astype(np.float64) / 100.0


def classify_scene(root: Path, year: int, scene: str, window: dict,
                   classif0: np.ndarray, res: float,
                   sample_rows: int = SAMPLE_ROWS, bands: int = 3) -> dict:
    """Which views of this scene can touch the window on a valid land class.

    ``useless`` lists the views that cannot: no sampled pixel both inside the
    window and on a land-cover class the retrieval keeps (``0 < class < 17``).
    """
    result = {"useful": [], "useless": [], "missing_inputs": False,
              "land_samples": 0, "inside_samples": 0, "reason": None}
    tif_dir = root / str(year) / "tif" / scene
    needed = [tif_dir / f"{band}_{view}.tif" for view in VIEWS for band in ("lat", "lon")]
    if any(not p.is_file() for p in needed):
        result["missing_inputs"] = True
        result["reason"] = "missing_inputs"
        return result

    inside_total = land_total = 0
    for view in VIEWS:
        lat = sample_geo(tif_dir / f"lat_{view}.tif", sample_rows, bands)
        lon = sample_geo(tif_dir / f"lon_{view}.tif", sample_rows, bands)
        if lat.size != lon.size or lat.size == 0:
            result["useless"].append(view)
            continue
        valid = ((lat != NODATA / 100.0) & (lon != NODATA / 100.0) &
                 (np.abs(lat) <= 90.0) & (np.abs(lon) <= 180.0))
        lat, lon = lat[valid], lon[valid]
        if lat.size == 0:
            result["useless"].append(view)
            continue
        inside = ((lon >= window["west"]) & (lon <= window["east"]) &
                  (lat >= window["south"]) & (lat <= window["north"]))
        inside_total += int(inside.sum())
        if not inside.any():
            result["useless"].append(view)
            continue
        row = np.rint((90.0 - lat[inside]) / res).astype(np.int64)
        col = np.rint((lon[inside] + 180.0) / res).astype(np.int64)
        np.clip(row, 0, classif0.shape[0] - 1, out=row)
        np.clip(col, 0, classif0.shape[1] - 1, out=col)
        klass = classif0[row, col]
        land = int(((klass > 0) & (klass < 17)).sum())
        land_total += land
        (result["useful"] if land else result["useless"]).append(view)

    result["land_samples"] = land_total
    result["inside_samples"] = inside_total
    if result["useless"]:
        result["reason"] = "no_land_in_window" if inside_total else "outside_window"
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", type=Path, required=True)
    ap.add_argument("--machine", default="hero")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--write", action="store_true",
                    help="write <scene_root>/_skip/<year>.json (default: report only)")
    ap.add_argument("--limit", type=int, default=None, help="only the first N scenes")
    ap.add_argument("--scene", nargs="*", default=None,
                    help="classify exactly these scenes and print every decision")
    ap.add_argument("--sample-rows", type=int, default=SAMPLE_ROWS,
                    help=f"rows read at the top/middle/bottom of each band "
                         f"(default {SAMPLE_ROWS})")
    ap.add_argument("--skip-out", type=Path, default=None,
                    help="where to write the list (default <scene_root>/_skip/<year>.json)")
    ap.add_argument("--inputs-only", action="store_true",
                    help="do not read the geolocation: only record the scenes whose "
                         "retrieval input files are incomplete, and merge that into "
                         "the existing skip list.  A scene like that can never be "
                         "retrieved from this disk, so without the entry the "
                         "retrieval keeps finding it and never finishes the year.")
    args = ap.parse_args()

    case = load_case(args.case, args.machine)
    root = case["source_root"]
    t0 = time.time()
    from base.files import read_image_gdal

    classif, *_ = read_image_gdal(str(case["type_reference"]))
    classif0 = np.asarray(classif, np.int16)
    print(f"land-cover reference {case['type_reference'].name} {classif0.shape} "
          f"in {time.time() - t0:.0f}s", flush=True)

    tif_dir = root / str(args.year) / "tif"
    scenes = sorted(e.name for e in os.scandir(tif_dir) if e.is_dir(follow_symlinks=False))
    if args.scene:
        scenes = [s for s in scenes if s in set(args.scene)]
    if args.limit:
        scenes = scenes[:args.limit]

    if args.inputs_only:
        out = args.skip_out or (root / "_skip" / f"{args.year}.json")
        payload = json.loads(out.read_text()) if out.is_file() else dict(
            year=args.year, case=case["case_id"], region=case["region"],
            window=case["window"], views=list(VIEWS), counts={}, scenes={})
        payload.setdefault("scenes", {})
        payload.setdefault("counts", {})
        added = 0
        for scene in scenes:
            try:
                names = {e.name for e in os.scandir(tif_dir / scene)
                         if e.is_file(follow_symlinks=False)}
            except OSError:
                names = set()
            useless = [view for view in VIEWS
                       if any(f"{band}_{view}.tif" not in names for band in REQUIRED_BANDS)]
            if not useless or scene in payload["scenes"]:
                continue
            payload["scenes"][scene] = {"reason": "missing_inputs",
                                        "useless_views": useless,
                                        "land_samples": 0, "inside_samples": 0}
            added += 1
        payload["counts"]["missing_inputs"] = payload["counts"].get("missing_inputs", 0) + added
        payload["inputs_checked"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=1))
        print(f"{case['case_id']} {args.year}: {len(scenes)} scenes checked, "
              f"{added} added as incomplete-input -> {out}")
        return

    counts: dict[str, int] = {}
    skip: dict[str, dict] = {}
    samplings = ((args.sample_rows, 3),) if args.sample_rows != SAMPLE_ROWS else SAMPLINGS
    t0 = time.time()
    for i, scene in enumerate(scenes, 1):
        info = None
        for sample_rows, bands in samplings:
            info = classify_scene(root, args.year, scene, case["window"], classif0,
                                  case["window"]["res"], sample_rows, bands)
            # the cheap sampling already sees a usable pixel, or the scene is
            # not readable at all: nothing to gain from sampling it again
            if info["useful"] or info["missing_inputs"]:
                break
        info["sampling"] = f"{sample_rows}x{bands}"
        counts[info["reason"] or "keep"] = counts.get(info["reason"] or "keep", 0) + 1
        if info["useless"] and not info["missing_inputs"]:
            skip[scene] = {"reason": info["reason"], "useless_views": info["useless"],
                           "land_samples": info["land_samples"],
                           "inside_samples": info["inside_samples"],
                           "sampling": info["sampling"]}
        if args.scene:
            print(f"  {scene[16:32]} -> {info}", flush=True)
        if i % 500 == 0:
            rate = i / max(time.time() - t0, 1e-9)
            print(f"  {i}/{len(scenes)} scenes, {rate:.1f} scene/s, {counts}", flush=True)

    print(f"{case['case_id']} {args.year}: {len(scenes)} scenes -> {counts} "
          f"in {(time.time() - t0) / 60:.1f} min", flush=True)
    payload = dict(year=args.year, case=case["case_id"], region=case["region"],
                   window=case["window"], views=list(VIEWS),
                   samplings=[f"{rows}x{bands}" for rows, bands in samplings],
                   rule="no sampled pixel both inside the case window and on a land class "
                        "(0 < class < 17); useless_views lists the views that cannot "
                        "contribute, a scene with both views listed is dead for the case",
                   generated=time.strftime("%Y-%m-%dT%H:%M:%S"),
                   counts=counts, scenes=skip)
    if args.write:
        out = args.skip_out or (root / "_skip" / f"{args.year}.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=1))
        print("skip list ->", out)
    else:
        print("(report only; add --write to store the list)")


if __name__ == "__main__":
    main()
