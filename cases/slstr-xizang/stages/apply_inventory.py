#!/usr/bin/env python3
"""Apply the already-audited Xizang reuse links and exact deletion plan."""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path("/media/hero/slstr_heihe/xizang")
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


def complete(path: Path, required: set[str]) -> bool:
    return path.is_dir() and all((path / name).is_file() for name in required)


def write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    os.replace(tmp, path)


def link_dir(link: Path, target: Path) -> str:
    if link.is_symlink():
        if link.resolve() == target.resolve():
            return "already_linked"
        raise RuntimeError(f"different symlink already exists: {link}")
    if link.exists():
        raise RuntimeError(f"path already exists and will not be replaced: {link}")
    link.symlink_to(target, target_is_directory=True)
    return "linked"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    inventory_path = args.root / "_inventory" / "scene_inventory.json"
    plan_path = args.root / "_inventory" / "duplicate_delete_plan.json"
    inventory = json.loads(inventory_path.read_text())
    plan = json.loads(plan_path.read_text())
    targets = plan["targets"]
    records = inventory["records"]
    planned_paths = {item["path"] for item in targets}
    # A zero-byte Xizang archive can have no canonical archive while the exact
    # scene is nevertheless complete in Heihe.  It is still a safe duplicate
    # deletion and must not be left behind merely because it cannot be opened.
    for record in records:
        if record["source"] != "heihe_reuse":
            continue
        for archive in record.get("archives", []):
            if archive["path"] in planned_paths:
                continue
            targets.append({**archive, "reason": "exact_scene_reused_from_heihe"})
            record.setdefault("delete", []).append(targets[-1])
            planned_paths.add(archive["path"])
    by_archive = {
        item["path"]: record
        for record in records
        for item in record.get("delete", [])
    }

    # Validate the whole plan before changing anything.
    for item in targets:
        path = Path(item["path"])
        record = by_archive.get(item["path"])
        if record is None:
            raise RuntimeError(f"target absent from inventory record: {path}")
        if path.parent.parent != args.root or path.suffix.lower() != ".zip":
            raise RuntimeError(f"unsafe deletion target: {path}")
        if path.exists() and path.stat().st_size != item["bytes"]:
            raise RuntimeError(f"size changed after audit: {path}")
        if item["reason"] == "exact_scene_reused_from_heihe":
            if not complete(Path(record["reuse"]["raw"]), REQUIRED_RAW):
                raise RuntimeError(f"Heihe raw replacement is no longer complete: {path}")
            if not complete(Path(record["reuse"]["tif"]), REQUIRED_TIF):
                raise RuntimeError(f"Heihe tif replacement is no longer complete: {path}")
        elif item["reason"] == "internal_duplicate_or_broken_copy":
            canonical = record.get("canonical_archive")
            if record["source"] != "heihe_reuse" and (not canonical or not Path(canonical).is_file()):
                raise RuntimeError(f"internal duplicate has no surviving canonical archive: {path}")
        else:
            raise RuntimeError(f"unknown deletion reason: {item['reason']}")

    print(f"validated {len(targets)} exact deletion targets "
          f"({sum(i['bytes'] for i in targets) / 2**30:.1f} GiB)")
    if not args.apply:
        print("validation only; pass --apply to create links and delete")
        return 0

    plan["targets"] = targets
    write_json(plan_path, plan)

    for year in inventory["years"]:
        year_dir = args.root / str(year)
        for layer in ("raw", "tif", "lst", "lsct"):
            (year_dir / layer).mkdir(parents=True, exist_ok=True)

    links = defaultdict(int)
    for record in records:
        if not record["selected"] or record["source"] != "heihe_reuse":
            continue
        for layer in ("raw", "tif", "lst", "lsct"):
            target = record["reuse"].get(layer)
            if target:
                status = link_dir(args.root / str(record["year"]) / layer / record["scene"],
                                  Path(target))
                links[f"{layer}_{status}"] += 1
            else:
                links[f"{layer}_target_missing"] += 1

    deleted = list(inventory.get("deleted") or [])
    deleted_paths = {item["path"] for item in deleted}
    for index, item in enumerate(targets, 1):
        path = Path(item["path"])
        if path.exists():
            path.unlink()
            if str(path) not in deleted_paths:
                deleted.append({"path": str(path), "bytes": item["bytes"], "reason": item["reason"]})
                deleted_paths.add(str(path))
        if index % 100 == 0 or index == len(targets):
            print(f"deleted {index}/{len(targets)}", flush=True)
    inventory["deletion_applied"] = True
    inventory["delete_count"] = len(targets)
    inventory["delete_bytes"] = sum(item["bytes"] for item in targets)
    inventory["deleted"] = deleted
    inventory["links"] = dict(links)
    inventory["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_json(inventory_path, inventory)
    print(f"links: {dict(links)}")
    print(f"deleted files: {len(deleted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
