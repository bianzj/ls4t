"""Create a case directory from the reviewed LS4T case template."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
TOKENS = {
    "{{CASE_ID}}": "case_id",
    "{{SENSOR}}": "sensor",
    "{{REGION}}": "region",
    "{{SPATIAL_MODE}}": "spatial_mode",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sensor", choices=("aatsr", "msg", "slstr", "modis", "viirs", "ahi"))
    parser.add_argument("region", help="lower-case region slug, for example heihe")
    parser.add_argument("case_id", help="lower-case case slug, for example summer-2022")
    parser.add_argument(
        "--mode",
        dest="spatial_mode",
        choices=("study-area-first", "scene-first", "fixed-grid", "temporal-composite"),
        required=True,
    )
    return parser.parse_args()


def validate_slug(name: str, value: str) -> None:
    if not SLUG.fullmatch(value):
        raise SystemExit(f"{name} must match {SLUG.pattern!r}: {value!r}")


def main() -> None:
    args = parse_args()
    validate_slug("region", args.region)
    validate_slug("case_id", args.case_id)

    templates_root = Path(__file__).resolve().parent
    repository_root = templates_root.parents[1]
    source = templates_root / "case"
    target = repository_root / "cases" / args.sensor / args.region / args.case_id
    if target.exists():
        raise SystemExit(f"refusing to overwrite existing case: {target}")

    shutil.copytree(source, target)
    values = vars(args)
    for path in target.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".toml", ".py"}:
            continue
        content = path.read_text(encoding="utf-8")
        for token, key in TOKENS.items():
            content = content.replace(token, values[key])
        path.write_text(content, encoding="utf-8")
    print(target.relative_to(repository_root))


if __name__ == "__main__":
    main()
