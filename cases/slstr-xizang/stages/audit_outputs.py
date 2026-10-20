#!/usr/bin/env python3
"""Audit Xizang scene-layer completion and separate natural empty outcomes."""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
from pathlib import Path

ROOT = Path("/media/hero/slstr_heihe/xizang")
REQUIRED_RAW = {
    "S2_radiance_an.nc", "S2_quality_an.nc", "S2_radiance_ao.nc", "S2_quality_ao.nc",
    "S3_radiance_an.nc", "S3_quality_an.nc", "S3_radiance_ao.nc", "S3_quality_ao.nc",
    "geometry_tn.nc", "geometry_to.nc", "geodetic_in.nc", "geodetic_io.nc", "met_tx.nc",
    "S8_BT_in.nc", "S8_BT_io.nc", "S9_BT_in.nc", "S9_BT_io.nc", "flags_in.nc", "flags_io.nc",
}
THERMAL_TIF = {
    f"{band}_{view}.tif"
    for band in ("bt8", "bt9", "vza", "lat", "lon")
    for view in ("nadir", "obliq")
}
NATURAL = {"water", "non_land", "low_lai", "cloud"}


def all_files(path: Path, names: set[str]) -> bool:
    return path.is_dir() and all((path / name).is_file() for name in names)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()
    inventory = json.loads((args.root / "_inventory" / "scene_inventory.json").read_text())
    coverage = {}
    for year in inventory["years"]:
        path = args.root / "_skip" / f"{year}.json"
        if path.is_file():
            coverage[year] = json.loads(path.read_text()).get("scenes", {})
        else:
            coverage[year] = {}

    counts = Counter()
    failures = []
    natural = Counter()
    diagnostics = Counter()
    for record in inventory["records"]:
        if not record["selected"]:
            continue
        year, scene = record["year"], record["scene"]
        base = args.root / str(year)
        raw, tif = base / "raw" / scene, base / "tif" / scene
        lst, lsct = base / "lst" / scene, base / "lsct" / scene
        counts["selected"] += 1
        if not all_files(raw, REQUIRED_RAW):
            failures.append({"year": year, "scene": scene, "stage": "raw", "reason": "missing_inputs"})
            counts["failed_raw"] += 1
            continue
        counts["raw_complete"] += 1
        cloud_ok = (tif / "cloud_nadir.tif").is_file() or (tif / "cloud_obliq.tif").is_file()
        if not all_files(tif, THERMAL_TIF) or not cloud_ok:
            failures.append({"year": year, "scene": scene, "stage": "tif", "reason": "missing_inputs"})
            counts["failed_tif"] += 1
            continue
        counts["tif_complete"] += 1

        info = coverage[year].get(scene, {})
        useless = set(info.get("useless_views") or ())
        if {"nadir", "obliq"} <= useless:
            natural[f"coverage_{info.get('reason', 'outside_or_no_land')}"] += 1
            counts["coverage_natural_skip"] += 1
            continue

        lst_views = [view for view in ("nadir", "obliq") if (lst / f"lst_{view}.tif").is_file()]
        if not lst_views:
            failures.append({"year": year, "scene": scene, "stage": "lst", "reason": "no_view_output"})
            counts["failed_lst"] += 1
            continue
        counts["lst_complete_any_view"] += 1

        if "obliq" in useless:
            natural[f"coverage_{info.get('reason', 'outside_or_no_land')}"] += 1
            counts["lsct_natural_skip"] += 1
            continue
        if (lsct / "lsct2.tif").is_file():
            counts["lsct_complete"] += 1
            continue
        marker = lsct / "_no_valid_pixel.json"
        if marker.is_file():
            try:
                reason = json.loads(marker.read_text()).get("reason", "unknown")
            except (OSError, ValueError):
                reason = "unreadable_marker"
            (natural if reason in NATURAL else diagnostics)[reason] += 1
            counts["lsct_empty_classified"] += 1
            continue
        failures.append({"year": year, "scene": scene, "stage": "lsct", "reason": "no_output_or_marker"})
        counts["failed_lsct"] += 1

    report = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "root": str(args.root), "counts": dict(counts),
        "natural_absence": dict(natural), "processing_diagnostics": dict(diagnostics),
        "failure_count": len(failures), "failures": failures,
    }
    path = args.report or (args.root / "_inventory" / "final_audit.json")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    os.replace(tmp, path)
    print(json.dumps({k: report[k] for k in ("counts", "natural_absence",
                                             "processing_diagnostics", "failure_count")},
                     ensure_ascii=False, indent=2))
    print(f"report -> {path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
