"""Run one standard LS4T sensor stage using this case's explicit configuration."""

from __future__ import annotations

import argparse
import importlib
import inspect
import sys
import tomllib
from pathlib import Path


CASE_DIR = Path(__file__).resolve().parent


def find_repository_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise SystemExit("cannot locate LS4T repository root (pyproject.toml)")


REPOSITORY_ROOT = find_repository_root(CASE_DIR)
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

STAGES = {
    "aatsr": {
        "unzip": ("aatsr.aatsr_data", "aatsr_unzip"),
        "extract": ("aatsr.aatsr_data", "aatsr_extract"),
        "project": ("aatsr.aatsr_project", "aatsr_project"),
        "lst": ("aatsr.aatsr_lst", "aatsr_lst"),
        "lsct": ("aatsr.aatsr_lsct", "aatsr_lsct"),
    },
    "msg": {
        "extract": ("msg.msg_data", "msg_extract"),
        "project": ("msg.msg_project", "msg_project"),
        "lst": ("msg.msg_lst", "msg_lst"),
        "lsct": ("msg.msg_lsct", "msg_lsct"),
    },
    "slstr": {
        "unzip": ("slstr.slstr_unzip", "slstr_unzip"),
        "extract": ("slstr.slstr_extract", "slstr_extract"),
        "reconstruct": ("slstr.slstr_reconstruct", "slstr_reconstruct"),
        "project": ("slstr.slstr_project", "slstr_project"),
        "merge": ("slstr.slstr_merge", "slstr_merge"),
        "lst": ("slstr.slstr_lst", "slstr_lst"),
        "lsct": ("slstr.slstr_lsct", "slstr_lsct"),
    },
    "modis": {
        "extract": ("modis.modis_extract", "modis_extract"),
        "project": ("modis.modis_project", "modis_project"),
        "merge": ("modis.modis_merge", "modis_merge"),
        "lst": ("modis.modis_lst", "modis_lst"),
    },
    "viirs": {
        "extract": ("viirs.viirs_extract", "viirs_extract"),
        "project": ("viirs.viirs_project", "viirs_project"),
        "merge": ("viirs.viirs_merge", "viirs_merge"),
        "lst": ("viirs.viirs_lst", "viirs_lst"),
    },
    "ahi": {
        "extract": ("ahi.ahi_extract", "ahi_extract"),
        "project": ("ahi.ahi_project", "ahi_project"),
        "merge": ("ahi.ahi_merge", "ahi_merge"),
        "lst": ("ahi.ahi_lst", "ahi_lst"),
    },
    "aster": {
        "extract": ("aster.aster_extract", "aster_extract"),
        "project": ("aster.aster_project", "aster_project"),
        "merge": ("aster.aster_merge", "aster_merge"),
        "lst": ("aster.aster_lst", "aster_lst"),
    },
}

PATH_ARGUMENTS = {
    "indir_zip": "zip_root",
    "outdir_raw": "raw_root",
    "indir_raw": "raw_root",
    "outdir_extract": "extract_root",
    "outdir_data": "extract_root",
    "indir_extract": "extract_root",
    "outdir_reconstruct": "reconstruct_root",
    "indir_reconstruct": "reconstruct_root",
    "indir_data": "retrieval_input_root",
    "outdir_project": "project_root",
    "indir_project": "project_root",
    "outdir_merge": "merge_root",
    "outdir_lst": "lst_root",
    "indir_lsct_input": "lsct_input_root",
    "outdir_lsct": "lsct_root",
    "target_grid_file": "target_grid_file",
    "static_file": "static_file",
    "coefficient_file": "coefficient_file",
    "auxiliary_file": "auxiliary_file",
    "input_paths": "merge_input_root",
    "output_path": "merge_output_file",
}


def load_toml(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"missing configuration: {path}")
    with path.open("rb") as source:
        return tomllib.load(source)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", nargs="?")
    parser.add_argument("--machine", default="local")
    parser.add_argument("--list", action="store_true")
    return parser.parse_args()


def stage_arguments(function, case: dict, machine: dict) -> dict:
    period = case.get("period", {})
    processing = case.get("processing", {})
    grid = case.get("grid", {})
    provenance = case.get("provenance", {})
    paths = machine.get("paths", {})
    available = {
        "years": period.get("years"),
        "months": period.get("months"),
        "days": period.get("days"),
        "views": processing.get("views"),
        "overwrite": processing.get("overwrite", False),
        "projection_chunk_size": processing.get("projection_chunk_size"),
        "cloud_fraction_threshold": processing.get("cloud_fraction_threshold"),
        "uncertainty_k": processing.get("uncertainty_k"),
        "grid_id": grid.get("id"),
        "algorithm_version": provenance.get("algorithm_version"),
        "bounds": grid.get("bounds"),
    }
    for argument, path_key in PATH_ARGUMENTS.items():
        if path_key in paths:
            available[argument] = str(Path(paths[path_key]).expanduser())
    accepted = inspect.signature(function).parameters
    return {name: value for name, value in available.items() if name in accepted and value is not None}


def main() -> None:
    args = parse_args()
    case = load_toml(CASE_DIR / "case.toml")
    sensor = case.get("case", {}).get("sensor")
    if sensor not in STAGES:
        raise SystemExit(f"no standard runner for sensor {sensor!r}; use case-specific stages/")
    available = STAGES[sensor]
    if args.list:
        print("\n".join(available))
        return
    if args.stage not in available:
        raise SystemExit(f"choose one stage: {', '.join(available)}")

    machine = load_toml(CASE_DIR / "machines" / f"{args.machine}.toml")
    module_name, function_name = available[args.stage]
    function = getattr(importlib.import_module(module_name), function_name)
    kwargs = stage_arguments(function, case, machine)
    print(f"case={case['case']['id']} machine={args.machine} stage={args.stage}")
    function(**kwargs)


if __name__ == "__main__":
    main()
