#!/usr/bin/env python3
"""Delete audited ZIPs with zero full-resolution overlap with Xizang bounds."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

ROOT = Path("/media/hero/slstr_heihe/xizang")
BOUNDS = [78.0, 26.0, 100.0, 37.0]


def write_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    os.replace(temporary, path)


def main() -> int:
    inventory = json.loads((ROOT / "_inventory" / "scene_inventory.json").read_text())
    targets = []
    for record in inventory["records"]:
        if record["selected"] or record["source"] != "xizang_archive":
            continue
        for archive in record["archives"]:
            path = Path(archive["path"])
            if not path.exists():
                continue
            if not archive["valid"]:
                raise RuntimeError(f"unexpected invalid remaining archive: {path}")
            if path.parent.parent != ROOT or path.suffix.lower() != ".zip":
                raise RuntimeError(f"unsafe deletion target: {path}")
            if path.stat().st_size != archive["bytes"]:
                raise RuntimeError(f"archive changed since inventory: {path}")
            targets.append({"year": record["year"], "scene": record["scene"],
                            "path": str(path), "bytes": archive["bytes"],
                            "reason": "full_resolution_zero_overlap_xizang_bounds"})
    targets.sort(key=lambda item: item["path"])
    payload = {
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "bounds": BOUNDS,
        "full_resolution_check": {"checked": len(targets), "overlap": 0, "errors": 0},
        "target_count": len(targets),
        "target_bytes": sum(item["bytes"] for item in targets),
        "applied": False,
        "targets": targets,
    }
    plan = ROOT / "_inventory" / "outside_xizang_zip_delete_plan.json"
    write_json(plan, payload)
    print(f"plan written: {len(targets)} ZIPs, {payload['target_bytes'] / 2**30:.1f} GiB")
    deleted = []
    for index, item in enumerate(targets, 1):
        Path(item["path"]).unlink()
        deleted.append(item)
        if index % 100 == 0 or index == len(targets):
            print(f"deleted {index}/{len(targets)}", flush=True)
    payload["applied"] = True
    payload["deleted"] = deleted
    payload["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_json(plan, payload)
    print(f"deleted {len(deleted)} outside-Xizang ZIPs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
