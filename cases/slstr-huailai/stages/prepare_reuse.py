#!/usr/bin/env python3
"""Validate Huailai raw scenes and reuse exact Heihe scene products."""
from __future__ import annotations

import json
import os
import time
from collections import Counter
from pathlib import Path

ROOT = Path("/media/hero/slstr_heihe/huailai")
REUSE_ROOT = Path("/media/hero/slstr_heihe/heihe")
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


def files_complete(path: Path, required: set[str]) -> bool:
    return path.is_dir() and all((path / name).is_file() and (path / name).stat().st_size > 0
                                 for name in required)


def reusable(layer: str, path: Path) -> bool:
    if layer == "tif":
        return files_complete(path, THERMAL_TIF) and any(
            (path / f"cloud_{view}.tif").is_file() for view in ("nadir", "obliq"))
    if layer == "lst":
        return path.is_dir() and any(
            (path / f"lst_{view}.tif").is_file() for view in ("nadir", "obliq"))
    return path.is_dir() and ((path / "lsct2.tif").is_file() or
                              (path / "_no_valid_pixel.json").is_file())


def link_dir(link: Path, target: Path) -> str:
    if link.is_symlink():
        if link.resolve() == target.resolve():
            return "already_linked"
        raise RuntimeError(f"different symlink already exists: {link}")
    if link.exists():
        return "local_exists"
    link.symlink_to(target, target_is_directory=True)
    return "linked"


def main() -> int:
    year_root = ROOT / str(YEAR)
    raw_root = year_root / "raw"
    scenes = sorted(p.name for p in raw_root.iterdir() if p.is_dir() and p.name.endswith(".SEN3"))
    failures = []
    for scene in scenes:
        path = raw_root / scene
        if not files_complete(path, REQUIRED_RAW):
            missing = sorted(name for name in REQUIRED_RAW
                             if not (path / name).is_file() or (path / name).stat().st_size == 0)
            failures.append({"scene": scene, "missing_or_empty": missing})
    if failures:
        raise RuntimeError(f"{len(failures)} incomplete raw scenes; first={failures[0]}")

    for layer in ("tif", "lst", "lsct"):
        (year_root / layer).mkdir(parents=True, exist_ok=True)
    counts = Counter(raw_complete=len(scenes))
    reused_scenes = set()
    for scene in scenes:
        if not (REUSE_ROOT / str(YEAR) / "raw" / scene).is_dir():
            continue
        counts["exact_heihe_scene"] += 1
        reused_scenes.add(scene)
        for layer in ("tif", "lst", "lsct"):
            target = REUSE_ROOT / str(YEAR) / layer / scene
            if reusable(layer, target):
                status = link_dir(year_root / layer / scene, target)
                counts[f"{layer}_{status}"] += 1
            else:
                counts[f"{layer}_not_reusable"] += 1

    report = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "root": str(ROOT), "reuse_root": str(REUSE_ROOT), "year": YEAR,
        "counts": dict(counts), "reused_scenes": sorted(reused_scenes),
    }
    out = ROOT / "_inventory" / "reuse_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    os.replace(tmp, out)
    print(json.dumps(report["counts"], ensure_ascii=False, indent=2), flush=True)
    print(f"report -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
