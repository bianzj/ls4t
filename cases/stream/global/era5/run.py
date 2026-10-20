"""Download, extract or check ERA5 daily forcing for STREAM."""

from __future__ import annotations

import argparse
import calendar
import sys
import tomllib
from datetime import date
from pathlib import Path


CASE_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = CASE_DIR.parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from base.stream_era5 import check_day, extract_month, forcing_day


VARIABLES = (
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "2m_dewpoint_temperature",
    "2m_temperature",
    "surface_pressure",
    "skin_temperature",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
    "soil_temperature_level_1",
    "volumetric_soil_water_layer_1",
    "high_vegetation_cover",
    "leaf_area_index_high_vegetation",
    "leaf_area_index_low_vegetation",
    "low_vegetation_cover",
)


def download_month(destination: Path, year: int, month: int) -> Path:
    import cdsapi

    target = destination / str(year) / f"{year}{month:02d}.nc"
    if target.exists():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    request = {
        "product_type": ["reanalysis"],
        "variable": list(VARIABLES),
        "year": [str(year)],
        "month": [f"{month:02d}"],
        "day": [f"{day:02d}" for day in range(1, calendar.monthrange(year, month)[1] + 1)],
        "time": [f"{hour:02d}:00" for hour in range(24)],
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    cdsapi.Client().retrieve("reanalysis-era5-single-levels", request).download(str(target))
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="hero", help="machines/<profile>.toml (default: hero)")
    parser.add_argument("--output-root", type=Path, help="STREAM input root, containing force/<year>/<doy>")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("download", "extract", "check"):
        command = commands.add_parser(name)
        command.add_argument("--year", type=int, required=True)
        command.add_argument("--month", type=int, required=True)
    commands.choices["download"].add_argument("--download-root", type=Path)
    extraction = commands.choices["extract"]
    extraction.add_argument("--source", type=Path, required=True, help="monthly NC or instantaneous NC")
    extraction.add_argument("--accumulated-source", type=Path, help="separate accumulated NC, if present")
    extraction.add_argument("--longitude-order", choices=("0-360", "-180-180"), default="0-360")
    args = parser.parse_args()

    calendar.monthrange(args.year, args.month)
    profile_path = CASE_DIR / "machines" / f"{args.profile}.toml"
    with profile_path.open("rb") as source:
        paths = tomllib.load(source)["paths"]
    output_root = args.output_root or Path(paths["output_root"])

    if args.command == "download":
        destination = args.download_root or Path(paths["download_root"])
        print(download_month(destination, args.year, args.month))
    elif args.command == "extract":
        for path in extract_month(args.source, output_root, args.year, args.month,
                                  accumulated_source=args.accumulated_source,
                                  longitude_order=args.longitude_order):
            print(path)
    else:
        missing = False
        for number in range(1, calendar.monthrange(args.year, args.month)[1] + 1):
            day = date(args.year, args.month, number)
            issues = check_day(output_root, day)
            if issues:
                missing = True
                print(f"{forcing_day(output_root, day)}: {', '.join(issues)}")
        if missing:
            raise SystemExit(1)
        print(f"OK: {args.year}-{args.month:02d}")


if __name__ == "__main__":
    main()
