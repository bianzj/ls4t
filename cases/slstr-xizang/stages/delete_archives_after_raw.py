#!/usr/bin/env python3
"""Verify processed Xizang raw trees and delete only their replaceable ZIPs."""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter, defaultdict
from pathlib import Path

import netCDF4

ROOT = Path("/media/hero/slstr_heihe/xizang")
REQUIRED = {
    "S2_radiance_an.nc", "S2_quality_an.nc", "S2_radiance_ao.nc", "S2_quality_ao.nc",
    "S3_radiance_an.nc", "S3_quality_an.nc", "S3_radiance_ao.nc", "S3_quality_ao.nc",
    "geometry_tn.nc", "geometry_to.nc", "geodetic_in.nc", "geodetic_io.nc", "met_tx.nc",
    "S8_BT_in.nc", "S8_BT_io.nc", "S9_BT_in.nc", "S9_BT_io.nc", "flags_in.nc", "flags_io.nc",
}


def evenly_spaced(records: list[dict], count: int) -> list[dict]:
    if len(records) <= count:
        return records
    return [records[round(i * (len(records) - 1) / (count - 1))] for i in range(count)]


def audit(records: list[dict], root: Path, sample_per_year: int) -> tuple[list[dict], list[dict]]:
    """Full structural audit plus an evenly distributed full-data read sample."""
    failures = []
    for index, record in enumerate(records, 1):
        raw = root / str(record["year"]) / "raw" / record["scene"]
        for name in sorted(REQUIRED):
            path = raw / name
            if not path.is_file() or path.stat().st_size <= 0:
                failures.append({"scene": record["scene"], "file": str(path),
                                 "reason": "missing_or_empty"})
                continue
        if index % 250 == 0:
            print(f"structural audit {index}/{len(records)}, failures {len(failures)}", flush=True)

    by_year: dict[int, list[dict]] = defaultdict(list)
    for record in records:
        by_year[record["year"]].append(record)
    samples = []
    for year, year_records in sorted(by_year.items()):
        chosen = evenly_spaced(sorted(year_records, key=lambda item: item["scene"]), sample_per_year)
        for record in chosen:
            raw = root / str(year) / "raw" / record["scene"]
            sample = {"year": year, "scene": record["scene"], "files": len(REQUIRED),
                      "bytes_read": 0, "status": "ok"}
            try:
                for name in sorted(REQUIRED):
                    path = raw / name
                    sample["bytes_read"] += path.stat().st_size
                    with netCDF4.Dataset(path) as ds:
                        # Force every stored chunk through HDF5/netCDF checks.
                        for variable in ds.variables.values():
                            if variable.size:
                                variable[...]
            except Exception as exc:  # noqa: BLE001
                sample["status"] = "failed"
                sample["error"] = f"{type(exc).__name__}: {exc}"
                failures.append({"scene": record["scene"], "file": str(path),
                                 "reason": sample["error"], "deep_sample": True})
            samples.append(sample)
            print(f"deep sample {year} {record['scene']} -> {sample['status']}", flush=True)
    return failures, samples


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    os.replace(temporary, path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--sample-per-year", type=int, default=20)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    inventory_path = args.root / "_inventory" / "scene_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    records = [record for record in inventory["records"]
               if record["selected"] and record["source"] == "xizang_archive"]
    records.sort(key=lambda item: (item["year"], item["scene"]))
    targets = []
    for record in records:
        archive = Path(record["canonical_archive"])
        targets.append({"year": record["year"], "scene": record["scene"],
                        "path": str(archive), "bytes": archive.stat().st_size,
                        "raw": str(args.root / str(record["year"]) / "raw" / record["scene"])})

    failures, samples = audit(records, args.root, args.sample_per_year)
    payload = {
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "root": str(args.root), "required_raw_files": sorted(REQUIRED),
        "target_count": len(targets), "target_bytes": sum(item["bytes"] for item in targets),
        "sample_per_year": args.sample_per_year, "samples": samples,
        "failure_count": len(failures), "failures": failures,
        "applied": False, "targets": targets,
    }
    plan = args.root / "_inventory" / "processed_zip_delete_plan.json"
    write_json(plan, payload)
    print(f"audit complete: {len(records)} raw scenes, {len(samples)} deep samples, "
          f"failures {len(failures)}")
    print(f"deletion plan: {len(targets)} ZIPs, "
          f"{payload['target_bytes'] / 2**30:.1f} GiB -> {plan}")
    if failures:
        print("not deleting: raw audit failed")
        return 1
    if not args.apply:
        print("validation only; pass --apply to execute the exact plan")
        return 0

    # Revalidate exact paths and sizes immediately before any unlink.
    for item in targets:
        archive = Path(item["path"])
        if archive.parent.parent != args.root or archive.suffix.lower() != ".zip":
            raise RuntimeError(f"unsafe deletion target: {archive}")
        if not archive.is_file() or archive.stat().st_size != item["bytes"]:
            raise RuntimeError(f"archive changed after audit: {archive}")
    deleted = []
    for index, item in enumerate(targets, 1):
        Path(item["path"]).unlink()
        deleted.append({key: item[key] for key in ("year", "scene", "path", "bytes")})
        if index % 100 == 0 or index == len(targets):
            print(f"deleted {index}/{len(targets)}", flush=True)
    payload["applied"] = True
    payload["deleted"] = deleted
    payload["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_json(plan, payload)
    print(f"deleted {len(deleted)} verified replaceable ZIPs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
