#!/usr/bin/env python3
"""Inventory Xizang archives, remove proven duplicates, and reuse Heihe scenes.

The destructive mode never uses a glob for deletion.  A complete JSON plan is
written first, every target is revalidated, and then each exact path is
unlinked individually.  Source products that have no complete replacement are
never deleted.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import zipfile
from collections import defaultdict
from pathlib import Path

import netCDF4
import numpy as np
import rasterio

YEARS = (2017, 2018)
BOUNDS = (78.0, 26.0, 100.0, 37.0)  # west, south, east, north
ROOT = Path("/media/hero/slstr_heihe/xizang")
REUSE_ROOT = Path("/media/hero/slstr_heihe/heihe")
INVENTORY_DIR = ROOT / "_inventory"
REQUIRED_RAW = {
    "S2_radiance_an.nc", "S2_quality_an.nc", "S2_radiance_ao.nc", "S2_quality_ao.nc",
    "S3_radiance_an.nc", "S3_quality_an.nc", "S3_radiance_ao.nc", "S3_quality_ao.nc",
    "geometry_tn.nc", "geometry_to.nc", "geodetic_in.nc", "geodetic_io.nc", "met_tx.nc",
    "S8_BT_in.nc", "S8_BT_io.nc", "S9_BT_in.nc", "S9_BT_io.nc", "flags_in.nc", "flags_io.nc",
}
REQUIRED_TIF = {
    f"{band}_{view}.tif"
    for band in ("bt8", "bt9", "vza", "lat", "lon", "cloud")
    for view in ("nadir", "obliq")
}
COPY_SUFFIX = re.compile(r"\(\d+\)$")


def canonical_scene(path: Path) -> str:
    return COPY_SUFFIX.sub("", path.stem) + ".SEN3"


def archive_info(path: Path) -> dict:
    info = {"path": str(path), "bytes": path.stat().st_size, "valid": False,
            "members": 0, "error": None}
    if not info["bytes"]:
        info["error"] = "zero_byte"
        return info
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
        leaves = {Path(name).name for name in names}
        info["members"] = len(names)
        missing = sorted(REQUIRED_RAW - leaves)
        if missing:
            info["error"] = "missing_required_members:" + ",".join(missing)
        else:
            info["valid"] = True
    except (OSError, zipfile.BadZipFile, EOFError) as exc:
        info["error"] = type(exc).__name__
    return info


def complete_dir(path: Path, required: set[str]) -> bool:
    return path.is_dir() and all((path / name).is_file() for name in required)


def zip_geo(path: Path) -> tuple[np.ndarray, np.ndarray]:
    lat_blocks, lon_blocks = [], []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        for leaf, lat_name, lon_name in (
            ("geodetic_in.nc", "latitude_in", "longitude_in"),
            ("geodetic_io.nc", "latitude_io", "longitude_io"),
        ):
            member = next(name for name in names if Path(name).name == leaf)
            payload = zf.read(member)
            with netCDF4.Dataset("memory.nc", memory=payload) as ds:
                lat_blocks.append(np.ma.filled(ds.variables[lat_name][::12, ::12], np.nan).ravel())
                lon_blocks.append(np.ma.filled(ds.variables[lon_name][::12, ::12], np.nan).ravel())
    return np.concatenate(lat_blocks), np.concatenate(lon_blocks)


def tif_geo(path: Path) -> tuple[np.ndarray, np.ndarray]:
    lat_blocks, lon_blocks = [], []
    for view in ("nadir", "obliq"):
        with rasterio.open(path / f"lat_{view}.tif") as ds:
            lat = ds.read(1, out_shape=(max(1, ds.height // 12), max(1, ds.width // 12)))
        with rasterio.open(path / f"lon_{view}.tif") as ds:
            lon = ds.read(1, out_shape=(max(1, ds.height // 12), max(1, ds.width // 12)))
        lat_blocks.append(lat.astype(np.float64).ravel() / 100.0)
        lon_blocks.append(lon.astype(np.float64).ravel() / 100.0)
    return np.concatenate(lat_blocks), np.concatenate(lon_blocks)


def intersects(lat: np.ndarray, lon: np.ndarray) -> bool:
    west, south, east, north = BOUNDS
    valid = np.isfinite(lat) & np.isfinite(lon) & (np.abs(lat) <= 90) & (np.abs(lon) <= 180)
    return bool(np.any(valid & (lon >= west) & (lon <= east) & (lat >= south) & (lat <= north)))


def symlink_dir(link: Path, target: Path) -> str:
    if not target.is_dir():
        return "target_missing"
    if link.is_symlink():
        if link.resolve() == target.resolve():
            return "already_linked"
        raise RuntimeError(f"refusing to replace different symlink: {link}")
    if link.exists():
        raise RuntimeError(f"refusing to replace existing path: {link}")
    link.symlink_to(target, target_is_directory=True)
    return "linked"


def prepare_hierarchy(root: Path) -> None:
    for year in YEARS:
        year_dir = root / str(year)
        for layer in ("raw", "tif", "lst", "lsct"):
            (year_dir / layer).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--reuse-root", type=Path, default=REUSE_ROOT)
    ap.add_argument("--delete-duplicates", action="store_true")
    ap.add_argument("--apply", action="store_true", help="create links and execute planned deletions")
    args = ap.parse_args()
    if args.apply and not args.delete_duplicates:
        ap.error("--apply requires --delete-duplicates so the destructive intent is explicit")

    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    groups: dict[tuple[int, str], list[dict]] = defaultdict(list)
    parts = []
    for year in YEARS:
        for path in sorted((args.root / str(year)).glob("*.zip")):
            groups[(year, canonical_scene(path))].append(archive_info(path))
        parts.extend(str(p) for p in sorted((args.root / str(year)).glob("*.part")))

    records, deletion_plan = [], []
    counts = defaultdict(int)
    for (year, scene), archives in sorted(groups.items()):
        good = [item for item in archives if item["valid"]]
        # Prefer the unsuffixed complete archive, then the lowest numbered copy.
        good.sort(key=lambda item: (bool(COPY_SUFFIX.search(Path(item["path"]).stem)), item["path"]))
        canonical = good[0] if good else None
        raw_target = args.reuse_root / str(year) / "raw" / scene
        tif_target = args.reuse_root / str(year) / "tif" / scene
        reusable = complete_dir(raw_target, REQUIRED_RAW) and complete_dir(tif_target, REQUIRED_TIF)

        selected = False
        coverage_error = None
        try:
            if reusable:
                selected = intersects(*tif_geo(tif_target))
            elif canonical:
                selected = intersects(*zip_geo(Path(canonical["path"])))
        except Exception as exc:  # retained as processing failure, never natural absence
            coverage_error = f"{type(exc).__name__}: {exc}"

        delete_items = []
        if canonical:
            for item in archives:
                if item is not canonical:
                    delete_items.append({**item, "reason": "internal_duplicate_or_broken_copy"})
            if reusable:
                delete_items.append({**canonical, "reason": "exact_scene_reused_from_heihe"})
        # No complete archive and no Heihe replacement: retain every artifact.
        if not canonical and not reusable:
            delete_items = []
        deletion_plan.extend(delete_items)

        source = "heihe_reuse" if reusable else ("xizang_archive" if canonical else "unrecoverable")
        counts[source] += 1
        counts["selected" if selected else "outside_or_unreadable"] += 1
        records.append({
            "year": year, "scene": scene, "source": source, "selected": selected,
            "coverage_error": coverage_error, "canonical_archive": canonical["path"] if canonical else None,
            "archives": archives, "delete": delete_items,
            "reuse": {
                "raw": str(raw_target) if raw_target.is_dir() else None,
                "tif": str(tif_target) if tif_target.is_dir() else None,
                "lst": str(args.reuse_root / str(year) / "lst" / scene)
                if (args.reuse_root / str(year) / "lst" / scene).is_dir() else None,
                "lsct": str(args.reuse_root / str(year) / "lsct" / scene)
                if (args.reuse_root / str(year) / "lsct" / scene).is_dir() else None,
            },
        })

    payload = {
        "created": started, "root": str(args.root), "reuse_root": str(args.reuse_root),
        "bounds": BOUNDS, "years": YEARS, "counts": dict(counts), "part_files": parts,
        "deletion_requested": bool(args.delete_duplicates), "deletion_applied": False,
        "delete_count": len(deletion_plan),
        "delete_bytes": sum(item["bytes"] for item in deletion_plan),
        "records": records,
    }
    plan_path = args.root / "_inventory" / "duplicate_delete_plan.json"
    inventory_path = args.root / "_inventory" / "scene_inventory.json"
    write_json(plan_path, {"created": started, "targets": deletion_plan})
    write_json(inventory_path, payload)
    print(f"inventory: {len(records)} unique scenes; selected {counts['selected']}; "
          f"Heihe reuse {counts['heihe_reuse']}; local {counts['xizang_archive']}; "
          f"unrecoverable {counts['unrecoverable']}", flush=True)
    print(f"delete plan: {len(deletion_plan)} files, "
          f"{sum(item['bytes'] for item in deletion_plan) / 2**30:.1f} GiB", flush=True)

    if not args.apply:
        print(f"dry run only; plan -> {plan_path}")
        return 0

    prepare_hierarchy(args.root)
    linked = defaultdict(int)
    for record in records:
        if not record["selected"] or record["source"] != "heihe_reuse":
            continue
        year, scene = record["year"], record["scene"]
        for layer in ("raw", "tif", "lst", "lsct"):
            target_text = record["reuse"].get(layer)
            if not target_text:
                linked[f"{layer}_missing"] += 1
                continue
            linked[f"{layer}_{symlink_dir(args.root / str(year) / layer / scene, Path(target_text))}"] += 1

    deleted = []
    for item in deletion_plan:
        path = Path(item["path"])
        # Exact path, size, and containing root must still match the written plan.
        if path.parent.parent != args.root or path.suffix.lower() != ".zip":
            raise RuntimeError(f"unsafe deletion target: {path}")
        if path.exists():
            if path.stat().st_size != item["bytes"]:
                raise RuntimeError(f"size changed after planning: {path}")
            path.unlink()
            deleted.append({"path": str(path), "bytes": item["bytes"], "reason": item["reason"]})
    payload["deletion_applied"] = True
    payload["deleted"] = deleted
    payload["links"] = dict(linked)
    payload["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_json(inventory_path, payload)
    print(f"applied: deleted {len(deleted)} files, linked {dict(linked)}")
    print(f"inventory -> {inventory_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
