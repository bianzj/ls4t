"""Create/resume the AATSR 0.01-degree daily and monthly statistics.

The input products are the reconstructed AATSR swath files under
``aatsr_lst``, ``aatsr_lsct_v0``, ``aatsr_ang`` and ``aatsr_loc``.  The
script deliberately follows the convention used by
``aatsr_lsct_001deg_simple``:

* global grid: 18000 x 36000, 0.01 degree;
* no cloud or LAI screening;
* 25000 < temperature < 35000 (stored temperature is K x 100);
* day: 0.1 < SZA < 89.9, night: SZA < 0.1 or SZA > 89.9;
* daily and monthly means are rounded to the nearest stored integer;
* ``count`` is the number of source observations contributing to a cell.

Existing daily/monthly files are never overwritten.  A missing monthly file
is rebuilt from the source swaths for the complete calendar month, even when
some daily files in that month already exist.  This makes restarting after an
interrupted run safe and keeps monthly means independent of rounded daily
means.
"""

from __future__ import annotations
from datetime import date, datetime, timedelta
from pathlib import Path
import argparse
import calendar
import h5py
import logging
import numpy as np
from numpy import any

GRID_SHAPE = (18000, 36000)
TEMPERATURE_FIELDS = {
    "Tnadir": "lstN",
    "Tobliq": "lstO",
    "Ts": "Ts",
    "Tv": "Tv",
}
TEMPERATURE_MIN = 25000
TEMPERATURE_MAX = 35000


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid date {value!r}; expected YYYY-MM-DD"
        ) from exc


def month_days(year: int, month: int) -> list[date]:
    first = date(year, month, 1)
    return [first + timedelta(days=i) for i in range(calendar.monthrange(year, month)[1])]


def make_arrays() -> tuple[dict[str, np.ndarray], np.ndarray]:
    # float64 avoids an accumulation-dependent rounding change in long months.
    sums = {
        name: np.zeros(GRID_SHAPE, dtype=np.float64)
        for name in TEMPERATURE_FIELDS
    }
    count = np.zeros(GRID_SHAPE, dtype=np.uint32)
    return sums, count


def source_files(source_root: Path, current: date) -> list[Path]:
    directory = source_root / "aatsr_lsct_v0" / f"{current:%Y/%m/%d}"
    if not directory.is_dir():
        return []
    return sorted(
        p for p in directory.glob("*_lsct.h5") if not p.name.endswith(".aux.xml")
    )


def ancillary_paths(source_root: Path, current: date, lsct_path: Path) -> dict[str, Path]:
    base = lsct_path.name[:-len("_lsct.h5")]
    day_dir = f"{current:%Y/%m/%d}"
    return {
        "lst": source_root / "aatsr_lst" / day_dir / f"{base}_lst.h5",
        "ang": source_root / "aatsr_ang" / day_dir / f"{base}_ang.h5",
        "loc": source_root / "aatsr_loc" / day_dir / f"{base}_loc.h5",
    }


def add_source_file(
    source_root: Path,
    current: date,
    lsct_path: Path,
    day_sums: dict[str, np.ndarray],
    day_count: np.ndarray,
    night_sums: dict[str, np.ndarray],
    night_count: np.ndarray,
    monthly_sums: dict[str, np.ndarray] | None,
    monthly_count: np.ndarray | None,
    error_log: Path,
) -> bool:
    paths = ancillary_paths(source_root, current, lsct_path)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        with error_log.open("a", encoding="utf-8") as stream:
            stream.write(f"{lsct_path}: missing ancillary: {', '.join(missing)}\n")
        return False

    try:
        with h5py.File(paths["lst"], "r") as handle:
            lst_n = handle["lstN"][:]
            lst_o = handle["lstO"][:]
        with h5py.File(lsct_path, "r") as handle:
            ts = handle["Ts"][:]
            tv = handle["Tv"][:]
        with h5py.File(paths["ang"], "r") as handle:
            sza = handle["sza"][:]
        with h5py.File(paths["loc"], "r") as handle:
            row = handle["indx"][:]
            col = handle["indy"][:]
    except (OSError, KeyError, ValueError) as exc:
        with error_log.open("a", encoding="utf-8") as stream:
            stream.write(f"{lsct_path}: {type(exc).__name__}: {exc}\n")
        return False

    shape = lst_n.shape
    if any(array.shape != shape for array in (lst_o, ts, tv, sza, row, col)):
        with error_log.open("a", encoding="utf-8") as stream:
            stream.write(f"{lsct_path}: ancillary shape mismatch\n")
        return False

    valid = (
        (lst_n > TEMPERATURE_MIN)
        & (lst_n < TEMPERATURE_MAX)
        & (lst_o > TEMPERATURE_MIN)
        & (lst_o < TEMPERATURE_MAX)
        & (ts > TEMPERATURE_MIN)
        & (ts < TEMPERATURE_MAX)
        & (tv > TEMPERATURE_MIN)
        & (tv < TEMPERATURE_MAX)
    )

    # SZA is stored as integer degrees x 100.  Comparing in stored units is
    # equivalent to the strict floating-point comparisons in the original run.
    day_mask = valid & (sza > 10) & (sza < 8990)
    night_mask = valid & ((sza < 10) | (sza > 8990))

    def accumulate(
        mask: np.ndarray,
        target_sums: dict[str, np.ndarray],
        target_count: np.ndarray,
    ) -> None:
        if not np.any(mask):
            return
        rows = row[mask].astype(np.int64, copy=False)
        cols = col[mask].astype(np.int64, copy=False)
        inside = (
            (rows >= 0)
            & (rows < GRID_SHAPE[0])
            & (cols >= 0)
            & (cols < GRID_SHAPE[1])
        )
        if not np.any(inside):
            return
        rows = rows[inside]
        cols = cols[inside]
        np.add.at(target_count, (rows, cols), 1)
        values = {"Tnadir": lst_n[mask], "Tobliq": lst_o[mask], "Ts": ts[mask], "Tv": tv[mask]}
        for name, values_array in values.items():
            np.add.at(target_sums[name], (rows, cols), values_array[inside])

    accumulate(day_mask, day_sums, day_count)
    accumulate(night_mask, night_sums, night_count)
    if monthly_sums is not None and monthly_count is not None:
        accumulate(day_mask, monthly_sums["day"], monthly_count["day"])
        accumulate(night_mask, monthly_sums["night"], monthly_count["night"])
    return True


def write_product(
    path: Path,
    period: str,
    sums: dict[str, np.ndarray],
    count: np.ndarray,
    current: date | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as handle:
        for name, summed in sums.items():
            values = np.zeros(GRID_SHAPE, dtype=np.uint16)
            valid = count > 0
            values[valid] = np.rint(summed[valid] / count[valid]).astype(np.uint16)
            dataset = handle.create_dataset(name, data=values, compression="gzip", compression_opts=4)
            dataset.attrs["missing_value"] = 0
            dataset.attrs["scale_factor"] = 0.01
        dataset = handle.create_dataset("count", data=count, compression="gzip", compression_opts=4)
        dataset.attrs["missing_value"] = 0
        handle.attrs["period"] = period
        handle.attrs["grid"] = "0.01 degree"
        handle.attrs["cloud_rule"] = "not applied"
        handle.attrs["missing_value"] = 0
        handle.attrs["scale_factor"] = 0.01
        if current is not None:
            handle.attrs["date"] = current.isoformat()
        else:
            handle.attrs["year"] = path.stem[:4]
            handle.attrs["month"] = path.stem[4:6]


def process_month(source_root: Path, output_root: Path, year: int, month: int, start: date, end: date, error_log: Path) -> None:
    days = month_days(year, month)
    in_requested_range = [current for current in days if start <= current <= end]
    if not in_requested_range:
        return

    daily_dir = output_root / "daily"
    monthly_dir = output_root / "monthly"
    missing_monthly = {
        "day": monthly_dir / f"{year:04d}{month:02d}_day.h5",
        "night": monthly_dir / f"{year:04d}{month:02d}_night.h5",
    }
    need_monthly = any(not path.is_file() for path in missing_monthly.values())
    monthly_sums = monthly_count = None
    if need_monthly:
        monthly_sums = {"day": make_arrays()[0], "night": make_arrays()[0]}
        monthly_count = {"day": make_arrays()[1], "night": make_arrays()[1]}

    logging.info("processing %04d-%02d%s", year, month, " (monthly rebuild)" if need_monthly else "")
    for current in days:
        day_paths = {
            "day": daily_dir / f"{current:%Y%m%d}_day.h5",
            "night": daily_dir / f"{current:%Y%m%d}_night.h5",
        }
        need_daily = any(current in in_requested_range and not path.is_file() for path in day_paths.values())
        source = source_files(source_root, current)
        if not source:
            continue
        if not need_daily and not need_monthly:
            continue
        day_sums, day_count = make_arrays()
        night_sums, night_count = make_arrays()
        successful = 0
        for lsct_path in source:
            if add_source_file(
                source_root, current, lsct_path,
                day_sums, day_count, night_sums, night_count,
                monthly_sums, monthly_count, error_log,
            ):
                successful += 1
        logging.info("%s: %d/%d source files", current.isoformat(), successful, len(source))
        if need_daily and current in in_requested_range:
            if day_count.any() and not day_paths["day"].is_file():
                write_product(day_paths["day"], "daily", day_sums, day_count, current)
            if night_count.any() and not day_paths["night"].is_file():
                write_product(day_paths["night"], "daily", night_sums, night_count, current)

    if need_monthly and monthly_sums is not None and monthly_count is not None:
        if monthly_count["day"].any() and not missing_monthly["day"].is_file():
            write_product(missing_monthly["day"], "monthly", monthly_sums["day"], monthly_count["day"])
        if monthly_count["night"].any() and not missing_monthly["night"].is_file():
            write_product(missing_monthly["night"], "monthly", monthly_sums["night"], monthly_count["night"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path("/media/hero/lsct04"))
    parser.add_argument("--output-root", type=Path, default=Path("/media/hero/lsct04/aatsr_lsct_001deg_simple"))
    parser.add_argument("--start-date", type=parse_date, default=date(2003, 10, 18))
    parser.add_argument("--end-date", type=parse_date, default=date(2012, 12, 31))
    parser.add_argument("--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING"))
    args = parser.parse_args()
    if args.start_date > args.end_date:
        parser.error("--start-date must not be later than --end-date")

    output_root = args.output_root
    error_log = output_root / "errors.txt"
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s %(message)s")
    cursor = date(args.start_date.year, args.start_date.month, 1)
    last_month = date(args.end_date.year, args.end_date.month, 1)
    while cursor <= last_month:
        process_month(args.source_root, output_root, cursor.year, cursor.month, args.start_date, args.end_date, error_log)
        cursor = date(cursor.year + (cursor.month == 12), 1 if cursor.month == 12 else cursor.month + 1, 1)


if __name__ == "__main__":
    main()
