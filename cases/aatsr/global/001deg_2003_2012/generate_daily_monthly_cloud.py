"""Generate cloud-screened daily and monthly AATSR LSCT products.

The input products are the swath-level HDF5 files under ``aatsr_lsct_v0``.
The aggregation follows ``aatsr_monthAve.py`` but keeps the cloud filter
enabled and writes real HDF5 files with a ``.h5`` suffix.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
from pathlib import Path

import h5py
import numpy as np


FIELDS = ("Ts", "Tv", "Tnadir", "Tobliq")
MIN_VALUE = 25300
MAX_VALUE = 35000
SCALE = 0.01


def cloud_free(clo: np.ndarray) -> np.ndarray:
    """Return the valid land/no-cloud mask from the raw AATSR flag."""
    clo = np.asarray(clo)
    return ((clo & 0b01) != 0) & ((clo & 0b10) == 0)


def read_dataset(path: Path, name: str) -> np.ndarray:
    with h5py.File(path, "r") as h5f:
        if name not in h5f:
            raise KeyError(f"{path}: missing dataset {name!r}")
        return np.asarray(h5f[name][:])


def add_scene(
    sums: dict[str, np.ndarray],
    counts: np.ndarray,
    scene: dict[str, np.ndarray],
    valid: np.ndarray,
    row: np.ndarray,
    col: np.ndarray,
    height: int,
    width: int,
) -> int:
    valid = valid & (row >= 0) & (row < height) & (col >= 0) & (col < width)
    if not np.any(valid):
        return 0

    flat_index = (row[valid].astype(np.int64) * width + col[valid]).ravel()
    np.add.at(counts.ravel(), flat_index, 1)
    for field in FIELDS:
        np.add.at(sums[field].ravel(), flat_index, scene[field][valid].astype(np.float32))
    return int(valid.sum())


def new_accumulator(height: int, width: int) -> tuple[dict[str, np.ndarray], np.ndarray]:
    shape = (height, width)
    return {field: np.zeros(shape, dtype=np.float32) for field in FIELDS}, np.zeros(shape, dtype=np.uint32)


def write_product(path: Path, sums: dict[str, np.ndarray], counts: np.ndarray, attrs: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as h5f:
        for key, value in attrs.items():
            h5f.attrs[key] = value
        h5f.attrs["scale_factor"] = SCALE
        h5f.attrs["missing_value"] = 0
        h5f.create_dataset("count", data=counts, compression="gzip", dtype=np.uint32)
        valid = counts > 0
        for field in FIELDS:
            out = np.zeros(counts.shape, dtype=np.uint16)
            average = np.zeros(counts.shape, dtype=np.float32)
            np.divide(sums[field], counts, out=average, where=valid)
            average = np.rint(average)
            average = np.clip(average, 1, np.iinfo(np.uint16).max - 1)
            out[valid] = average[valid].astype(np.uint16)
            dataset = h5f.create_dataset(field, data=out, compression="gzip", dtype=np.uint16)
            dataset.attrs["scale_factor"] = SCALE
            dataset.attrs["missing_value"] = 0


def scene_paths(source_root: Path, year: int, month: int, day: int) -> list[Path]:
    directory = source_root / "aatsr_lsct_v0" / f"{year:04d}" / f"{month:02d}" / f"{day:02d}"
    return sorted(directory.glob("*_lsct.h5"))


def process_scene(
    lsct_path: Path,
    source_root: Path,
    day_sums: dict[str, np.ndarray],
    day_counts: dict[str, np.ndarray],
    night_sums: dict[str, np.ndarray],
    night_counts: np.ndarray,
    month_sums: dict[str, np.ndarray],
    month_counts: np.ndarray,
    month_night_sums: dict[str, np.ndarray],
    month_night_counts: np.ndarray,
    height: int,
    width: int,
) -> tuple[int, int]:
    stem = lsct_path.name.removesuffix("_lsct.h5")
    date_dir = lsct_path.parent.relative_to(source_root / "aatsr_lsct_v0")
    ancillary = {
        "lst": source_root / "aatsr_lst" / date_dir / f"{stem}_lst.h5",
        "clo": source_root / "aatsr_clo" / date_dir / f"{stem}_clo.h5",
        "loc": source_root / "aatsr_loc" / date_dir / f"{stem}_loc.h5",
        "ang": source_root / "aatsr_ang" / date_dir / f"{stem}_ang.h5",
    }
    missing = [str(path) for path in ancillary.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("missing ancillary files: " + ", ".join(missing))

    scene = {field: read_dataset(lsct_path, field) for field in ("Ts", "Tv")}
    scene.update({"Tnadir": read_dataset(ancillary["lst"], "lstN")})
    scene.update({"Tobliq": read_dataset(ancillary["lst"], "lstO")})
    clo_n = read_dataset(ancillary["clo"], "cloN")
    clo_o = read_dataset(ancillary["clo"], "cloF")
    indx = read_dataset(ancillary["loc"], "indx")
    indy = read_dataset(ancillary["loc"], "indy")
    solar_zenith = 90.0 - read_dataset(ancillary["ang"], "sza") / 100.0

    shapes = {array.shape for array in (*scene.values(), clo_n, clo_o, indx, indy, solar_zenith)}
    if len(shapes) != 1:
        raise ValueError(f"shape mismatch in {lsct_path}: {sorted(shapes)}")

    row = indx.astype(np.int64) // 5
    col = indy.astype(np.int64) // 5
    valid_cloud = cloud_free(clo_n) & cloud_free(clo_o)
    valid_temperature = np.ones(solar_zenith.shape, dtype=bool)
    for values in scene.values():
        valid_temperature &= np.isfinite(values) & (values > MIN_VALUE) & (values < MAX_VALUE)

    day = valid_cloud & valid_temperature & (solar_zenith > 0.1) & (solar_zenith < 89.9)
    night = valid_cloud & valid_temperature & ((solar_zenith >= 89.9) | (solar_zenith <= 0.1))

    day_count = add_scene(day_sums, day_counts["day"], scene, day, row, col, height, width)
    night_count = add_scene(night_sums, night_counts, scene, night, row, col, height, width)
    add_scene(month_sums, month_counts, scene, day, row, col, height, width)
    add_scene(month_night_sums, month_night_counts, scene, night, row, col, height, width)
    return day_count, night_count


def zero_accumulator(height: int, width: int) -> tuple[dict[str, np.ndarray], np.ndarray]:
    return new_accumulator(height, width)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path("/media/hero/lsct04"))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/media/hero/lsct04/aatsr_lsct_cloud_v1"),
    )
    parser.add_argument("--height", type=int, default=3600)
    parser.add_argument("--width", type=int, default=7200)
    parser.add_argument("--year", type=int, nargs="*")
    parser.add_argument("--month", type=int, nargs="*")
    parser.add_argument("--day", type=int, nargs="*")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    source_root = args.source_root.resolve()
    output_root = args.output_root.resolve()
    years = args.year or sorted(int(path.name) for path in (source_root / "aatsr_lsct_v0").iterdir() if path.name.isdigit())
    months = set(args.month or range(1, 13))
    selected_days = set(args.day or [])
    error_log = output_root / "errors.txt"
    output_root.mkdir(parents=True, exist_ok=True)

    for year in years:
        for month in sorted(months):
            if month < 1 or month > 12:
                raise ValueError(f"invalid month: {month}")
            month_sums, month_counts_array = new_accumulator(args.height, args.width)
            month_night_sums, month_night_counts_array = new_accumulator(args.height, args.width)
            month_has_scene = False

            first = dt.date(year, month, 1)
            next_month = dt.date(year + (month == 12), 1 if month == 12 else month + 1, 1)
            day = first
            while day < next_month:
                if selected_days and day.day not in selected_days:
                    day += dt.timedelta(days=1)
                    continue
                paths = scene_paths(source_root, day.year, day.month, day.day)
                day_sums, day_counts_array = new_accumulator(args.height, args.width)
                day_night_sums, day_night_counts_array = new_accumulator(args.height, args.width)
                day_has_scene = False
                for path in paths:
                    try:
                        day_count, night_count = process_scene(
                            path,
                            source_root,
                            day_sums,
                            {"day": day_counts_array},
                            day_night_sums,
                            day_night_counts_array,
                            month_sums,
                            month_counts_array,
                            month_night_sums,
                            month_night_counts_array,
                            args.height,
                            args.width,
                        )
                        day_has_scene |= (day_count + night_count) > 0
                        month_has_scene |= (day_count + night_count) > 0
                        logging.info("%s: cloud-screened day=%d night=%d", path.name, day_count, night_count)
                    except Exception as exc:
                        logging.error("%s: %s", path, exc)
                        with error_log.open("a", encoding="utf-8") as log:
                            log.write(f"{path}: {exc}\n")

                if day_has_scene:
                    for label, sums, counts in (
                        ("day", day_sums, day_counts_array),
                        ("night", day_night_sums, day_night_counts_array),
                    ):
                        if np.any(counts):
                            outfile = output_root / "daily" / f"{day:%Y%m%d}_{label}.h5"
                            if args.overwrite or not outfile.exists():
                                write_product(outfile, sums, counts, {"period": "daily", "date": day.isoformat(), "cloud_rule": "land and no cloud in cloN and cloF"})
                day += dt.timedelta(days=1)

            if month_has_scene:
                for label, sums, counts in (
                    ("day", month_sums, month_counts_array),
                    ("night", month_night_sums, month_night_counts_array),
                ):
                    if np.any(counts):
                        outfile = output_root / "monthly" / f"{year:04d}{month:02d}_{label}.h5"
                        if args.overwrite or not outfile.exists():
                            write_product(outfile, sums, counts, {"period": "monthly", "year": str(year), "month": f"{month:02d}", "cloud_rule": "land and no cloud in cloN and cloF"})


if __name__ == "__main__":
    main()
