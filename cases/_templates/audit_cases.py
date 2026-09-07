"""Audit registered LS4T cases without importing or executing their science code."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path


CASES_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_STATUS = {"draft", "migrated", "active", "paused", "complete"}
ALLOWED_MODES = {"study-area-first", "scene-first", "fixed-grid", "temporal-composite"}


def load(path: Path) -> dict:
    with path.open("rb") as source:
        return tomllib.load(source)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-paths", action="store_true", help="also require machine data paths")
    args = parser.parse_args()

    catalog = load(CASES_ROOT / "catalog.toml")
    errors: list[str] = []
    registered: set[Path] = set()
    for record in catalog.get("case", []):
        relative = Path(record["path"])
        case_dir = CASES_ROOT / relative
        registered.add(case_dir.resolve())
        metadata_path = case_dir / "case.toml"
        if not metadata_path.is_file():
            errors.append(f"{relative}: missing case.toml")
            continue
        metadata = load(metadata_path)
        case = metadata.get("case", {})
        if case.get("id") != record.get("id"):
            errors.append(f"{relative}: case id differs from catalog")
        if case.get("sensor") != record.get("sensor"):
            errors.append(f"{relative}: sensor differs from catalog")
        if case.get("status") not in ALLOWED_STATUS:
            errors.append(f"{relative}: invalid status {case.get('status')!r}")
        if case.get("spatial_mode") not in ALLOWED_MODES:
            errors.append(f"{relative}: invalid spatial mode {case.get('spatial_mode')!r}")
        for entrypoint in record.get("entrypoints", []):
            if not (case_dir / entrypoint).is_file():
                errors.append(f"{relative}: missing entrypoint {entrypoint}")
        machine_files = sorted((case_dir / "machines").glob("*.toml"))
        if not machine_files:
            errors.append(f"{relative}: no machine profiles")
        for machine_file in machine_files:
            machine = load(machine_file)
            if "machine" not in machine or "paths" not in machine:
                errors.append(f"{relative}: incomplete machine profile {machine_file.name}")
            if args.strict_paths:
                for name, value in machine.get("paths", {}).items():
                    if not Path(value).expanduser().exists():
                        errors.append(f"{relative}: {machine_file.name} path missing: {name}={value}")
        print(
            f"{record['id']}: {case.get('status')} / {case.get('spatial_mode')} "
            f"({len(machine_files)} machine profile(s))"
        )

    for metadata_path in CASES_ROOT.rglob("case.toml"):
        if metadata_path.relative_to(CASES_ROOT).parts[0].startswith("_"):
            continue
        if metadata_path.parent.resolve() not in registered:
            errors.append(f"unregistered case: {metadata_path.parent.relative_to(CASES_ROOT)}")

    if errors:
        print("\nAudit failures:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"\nOK: {len(registered)} registered cases")


if __name__ == "__main__":
    main()
