#!/usr/bin/env python3
"""Selectively extract required SLSTR NetCDF members from inventory archives."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path("/media/hero/slstr_heihe/xizang")
INVENTORY = ROOT / "_inventory" / "scene_inventory.json"
REQUIRED = {
    "S2_radiance_an.nc", "S2_quality_an.nc", "S2_radiance_ao.nc", "S2_quality_ao.nc",
    "S3_radiance_an.nc", "S3_quality_an.nc", "S3_radiance_ao.nc", "S3_quality_ao.nc",
    "geometry_tn.nc", "geometry_to.nc", "geodetic_in.nc", "geodetic_io.nc", "met_tx.nc",
    "S8_BT_in.nc", "S8_BT_io.nc", "S9_BT_in.nc", "S9_BT_io.nc", "flags_in.nc", "flags_io.nc",
}


def complete(path: Path) -> bool:
    return path.is_dir() and all((path / name).is_file() for name in REQUIRED)


def extract_one(task: tuple[Path, Path]) -> dict:
    archive, target = task
    if complete(target):
        return {"scene": target.name, "status": "skipped_complete"}
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{target.name}.partial-", dir=target.parent))
    try:
        with zipfile.ZipFile(archive) as zf:
            members = {Path(name).name: name for name in zf.namelist() if Path(name).name in REQUIRED}
            missing = REQUIRED - members.keys()
            if missing:
                raise RuntimeError("archive missing: " + ",".join(sorted(missing)))
            for leaf in sorted(REQUIRED):
                with zf.open(members[leaf]) as src, (temp / leaf).open("wb") as dst:
                    shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)
        if target.exists() or target.is_symlink():
            if complete(target):
                shutil.rmtree(temp)
                return {"scene": target.name, "status": "skipped_race"}
            raise RuntimeError(f"incomplete destination already exists: {target}")
        os.replace(temp, target)
        return {"scene": target.name, "status": "extracted"}
    except Exception as exc:
        shutil.rmtree(temp, ignore_errors=True)
        return {"scene": target.name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--inventory", type=Path, default=INVENTORY)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--scene", nargs="*", default=None)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()
    payload = json.loads(args.inventory.read_text())
    requested = set(args.scene or ())
    tasks = []
    for record in payload["records"]:
        if not record["selected"] or record["source"] != "xizang_archive":
            continue
        if requested and record["scene"] not in requested:
            continue
        archive = Path(record["canonical_archive"])
        if not archive.is_file():
            raise FileNotFoundError(f"inventory archive is absent: {archive}")
        tasks.append((archive, args.root / str(record["year"]) / "raw" / record["scene"]))
    if args.limit:
        tasks = tasks[:args.limit]
    print(f"raw staging: {len(tasks)} scenes, {args.workers} workers", flush=True)
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(extract_one, task): task for task in tasks}
        for index, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            print(f"[{index}/{len(tasks)}] {result['scene']} {result['status']}", flush=True)
    counts = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    report = {"started": started, "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "workers": args.workers, "counts": counts, "results": results}
    report_path = args.report or (args.root / "_inventory" / "raw_stage_report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"raw staging done: {counts}; report -> {report_path}")
    return 1 if counts.get("failed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
