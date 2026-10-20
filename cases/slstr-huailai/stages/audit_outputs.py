#!/usr/bin/env python3
"""Audit Huailai outputs and separate natural absences from failures."""
from __future__ import annotations

import json
import os
import time
from collections import Counter
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path("/media/hero/slstr_heihe/huailai")
YEAR = 2024
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


def complete(path: Path, names: set[str]) -> bool:
    return path.is_dir() and all((path / name).is_file() for name in names)


def source_thermal_missing(tif: Path) -> bool:
    """True when every extracted S8/S9 view contains only source fill/zero."""
    for band in ("bt8", "bt9"):
        for view in ("nadir", "obliq"):
            path = tif / f"{band}_{view}.tif"
            if not path.is_file():
                return False
            with rasterio.open(path) as ds:
                if np.any(ds.read(1) > 0):
                    return False
    return True


def main() -> int:
    base = ROOT / str(YEAR)
    coverage_path = ROOT / "_skip" / f"{YEAR}.json"
    coverage = json.loads(coverage_path.read_text()).get("scenes", {}) \
        if coverage_path.is_file() else {}
    scenes = sorted(p.name for p in (base / "raw").iterdir()
                    if p.is_dir() and p.name.endswith(".SEN3"))
    counts = Counter(selected=len(scenes))
    natural = Counter()
    diagnostics = Counter()
    failures = []
    for scene in scenes:
        raw, tif = base / "raw" / scene, base / "tif" / scene
        lst, lsct = base / "lst" / scene, base / "lsct" / scene
        if not complete(raw, REQUIRED_RAW):
            failures.append({"scene": scene, "stage": "raw", "reason": "missing_inputs"})
            counts["failed_raw"] += 1
            continue
        counts["raw_complete"] += 1
        cloud_ok = any((tif / f"cloud_{view}.tif").is_file()
                       for view in ("nadir", "obliq"))
        if not complete(tif, THERMAL_TIF) or not cloud_ok:
            failures.append({"scene": scene, "stage": "tif", "reason": "missing_inputs"})
            counts["failed_tif"] += 1
            continue
        counts["tif_complete"] += 1

        info = coverage.get(scene, {})
        useless = set(info.get("useless_views") or ())
        if {"nadir", "obliq"} <= useless:
            natural[f"coverage_{info.get('reason', 'outside_or_no_land')}"] += 1
            counts["coverage_natural_skip"] += 1
            continue
        views = [view for view in ("nadir", "obliq") if (lst / f"lst_{view}.tif").is_file()]
        if not views:
            failures.append({"scene": scene, "stage": "lst", "reason": "no_view_output"})
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
            if reason == "invalid_thermal" and source_thermal_missing(tif):
                natural["source_missing_thermal"] += 1
            else:
                (natural if reason in NATURAL else diagnostics)[reason] += 1
            counts["lsct_empty_classified"] += 1
            continue
        failures.append({"scene": scene, "stage": "lsct", "reason": "no_output_or_marker"})
        counts["failed_lsct"] += 1

    report = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "root": str(ROOT),
        "year": YEAR, "counts": dict(counts), "natural_absence": dict(natural),
        "processing_diagnostics": dict(diagnostics), "failure_count": len(failures),
        "failures": failures,
    }
    out = ROOT / "_inventory" / "final_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    os.replace(tmp, out)
    print(json.dumps({k: report[k] for k in ("counts", "natural_absence",
                                             "processing_diagnostics", "failure_count")},
                     ensure_ascii=False, indent=2))
    print(f"report -> {out}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
