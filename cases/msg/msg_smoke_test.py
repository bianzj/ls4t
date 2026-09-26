#!/usr/bin/env python3
"""Rebuild one MSG timestamp in isolation and compare it with the archive."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from cases.msg.msg_project_hdf5 import PRODUCTS, load_static_latlon, project_directory


REPO_ROOT = Path(__file__).resolve().parents[2]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def projected_filename(product_name: str, stamp: str) -> str:
    if product_name == "euro-lst":
        return f"HDF5_LSASAF_MSG_LST_MSG-Disk_{stamp}.tif"
    if product_name == "iodc-lst":
        return f"HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_{stamp}.tif"
    return f"HDF5_LSASAF_MSG_LAI_MSG-Disk_{stamp}.tif"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    parser.add_argument("--hour", type=int, required=True, choices=range(24))
    parser.add_argument("--msg-root", type=Path, default=Path("/media/hero/MSG"))
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stamp = f"{args.date:%Y%m%d}{args.hour:02d}00"
    lai_stamp = f"{args.date:%Y%m%d}0000"
    work_root = args.work_root or Path("/home/hero/data/msg_e2e_test") / stamp
    projected_root = work_root / "projected"
    lsct_root = work_root / "lsct"
    logs_root = work_root / "logs"
    logs_root.mkdir(parents=True, exist_ok=True)

    projection_records = []
    for product_name, selected_hours in (
        ("euro-lst", {args.hour}),
        ("iodc-lst", {args.hour}),
        ("euro-lai", {0}),
    ):
        product = PRODUCTS[product_name]
        relative = Path(f"{args.date:%Y}") / f"{args.date:%m}" / f"{args.date:%d}"
        input_directory = args.msg_root / product.input_relative / relative
        output_directory = projected_root / product.output_relative / relative
        latitude, longitude = load_static_latlon(
            args.msg_root / "Static" / product.latitude_name,
            args.msg_root / "Static" / product.longitude_name,
        )
        counts = project_directory(
            input_directory,
            output_directory,
            product.variable,
            latitude,
            longitude,
            selected_hours,
            args.overwrite,
        )
        if counts["failed"] or counts["written"] + counts["existing"] != 1:
            raise SystemExit(f"projection failed for {product_name}: {counts}")
        product_stamp = lai_stamp if product_name == "euro-lai" else stamp
        filename = projected_filename(product_name, product_stamp)
        generated = output_directory / filename
        archived = args.msg_root / product.output_relative / relative / filename
        projection_records.append((product_name, generated, archived, counts))

    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO_ROOT)
    environment["PROJ_LIB"] = "/usr/share/proj"
    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[variable] = "1"
    command = [
        sys.executable,
        str(REPO_ROOT / "cases/msg/msg_lsct_iter.py"),
        "--start-date",
        args.date.isoformat(),
        "--hours",
        str(args.hour),
        "--msg-root",
        str(args.msg_root),
        "--euro-lst-root",
        str(projected_root / PRODUCTS["euro-lst"].output_relative),
        "--iodc-lst-root",
        str(projected_root / PRODUCTS["iodc-lst"].output_relative),
        "--lai-root",
        str(projected_root / PRODUCTS["euro-lai"].output_relative),
        "--output-root",
        str(lsct_root),
    ]
    if args.overwrite:
        command.append("--overwrite")
    completed = subprocess.run(command, env=environment, text=True, capture_output=True)
    (logs_root / "lsct.stdout.log").write_text(completed.stdout, encoding="utf-8")
    (logs_root / "lsct.stderr.log").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode:
        raise SystemExit(f"LSCT failed with exit code {completed.returncode}")

    relative = Path(f"{args.date:%Y}") / f"{args.date:%m}" / f"{args.date:%d}"
    generated_lsct = lsct_root / relative / f"MSG_LSCT_{stamp}.h5"
    archived_lsct = args.msg_root / "PRODUCTS/LSCT/MLST_COMPONENT" / relative / generated_lsct.name
    comparisons = []
    for name, generated, archived, counts in projection_records:
        comparisons.append(
            {
                "product": name,
                "generated": str(generated),
                "archived": str(archived),
                "generated_sha256": file_hash(generated),
                "archived_sha256": file_hash(archived),
                "counts": counts,
            }
        )
    comparisons.append(
        {
            "product": "formal-lsct",
            "generated": str(generated_lsct),
            "archived": str(archived_lsct),
            "generated_sha256": file_hash(generated_lsct),
            "archived_sha256": file_hash(archived_lsct),
        }
    )
    for comparison in comparisons:
        comparison["match"] = (
            comparison["generated_sha256"] == comparison["archived_sha256"]
        )
    report = {
        "date": args.date.isoformat(),
        "hour": args.hour,
        "work_root": str(work_root),
        "comparisons": comparisons,
        "all_match": all(item["match"] for item in comparisons),
    }
    report_path = work_root / "result.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    if not report["all_match"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
