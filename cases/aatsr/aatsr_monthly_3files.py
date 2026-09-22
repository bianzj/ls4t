"""Build three time-stacked 0.01-degree AATSR monthly products.

The source monthly products contain separate day/night means for Ts, Tv,
Tnadir and Tobliq, plus an observation count.  This script combines day and
night with the count as weight and writes one time-stacked file for each
requested analysis variable:

* ``Ts``: count-weighted soil temperature;
* ``Tv``: count-weighted vegetation temperature;
* ``T``: count-weighted mean of the valid nadir and oblique LST estimates.

Values remain uint16 with scale_factor=0.01 and missing_value=0, matching the
source products.  The script is intentionally configured at the top so it
can be run directly and resumed/rebuilt by changing the parameters below.
"""

from __future__ import annotations
from pathlib import Path
import h5py
import logging
import numpy as np
from numpy import any, min, sum

# ------------------------------- parameters -------------------------------
SOURCE_MONTHLY_DIR = Path("/media/hero/lsct04/aatsr_lsct_001deg_simple/monthly")
OUTPUT_DIR = Path(
    "/media/hero/lsct04/aatsr_lsct_001deg_simple/monthly_2003_2011_3files"
)
START_YEAR = 2003
END_YEAR = 2011
ROW_BLOCK = 141  # aligned with the source HDF5 row chunk
COMPRESSION_LEVEL = 4
OVERWRITE = False
REQUIRE_ALL_MONTHS = True
# ---------------------------------------------------------------------------


GRID_SHAPE = (18000, 36000)
SOURCE_FIELDS = ("Ts", "Tv", "Tnadir", "Tobliq")


def month_ids() -> list[int]:
    return [
        year * 100 + month
        for year in range(START_YEAR, END_YEAR + 1)
        for month in range(1, 13)
    ]


def source_paths(month_id: int) -> tuple[Path, Path]:
    stem = f"{month_id:06d}"
    return SOURCE_MONTHLY_DIR / f"{stem}_day.h5", SOURCE_MONTHLY_DIR / f"{stem}_night.h5"


def check_sources(months: list[int]) -> None:
    missing = [str(path) for month_id in months for path in source_paths(month_id) if not path.is_file()]
    if missing and REQUIRE_ALL_MONTHS:
        raise FileNotFoundError("Missing monthly source products:\n" + "\n".join(missing[:50]))
    if missing:
        logging.warning("%d source files are missing; those months will be empty", len(missing))


def create_output(path: Path, dataset_name: str, months: list[int]) -> h5py.File:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not OVERWRITE:
        raise FileExistsError(f"Output exists and OVERWRITE=False: {path}")
    handle = h5py.File(path, "w")
    handle.create_dataset("time", data=np.asarray(months, dtype=np.int32))
    handle["time"].attrs["format"] = "YYYYMM"
    handle.create_dataset(
        "latitude",
        data=(89.995 - 0.01 * np.arange(GRID_SHAPE[0], dtype=np.float32)),
    )
    handle.create_dataset(
        "longitude",
        data=(-179.995 + 0.01 * np.arange(GRID_SHAPE[1], dtype=np.float32)),
    )
    data = handle.create_dataset(
        dataset_name,
        shape=(len(months), *GRID_SHAPE),
        dtype=np.uint16,
        chunks=(1, ROW_BLOCK, 1024),
        compression="gzip",
        compression_opts=COMPRESSION_LEVEL,
        fillvalue=0,
    )
    data.attrs["scale_factor"] = 0.01
    data.attrs["missing_value"] = 0
    data.attrs["units"] = "K"
    data.attrs["grid"] = "0.01 degree global; latitude north-to-south"
    handle.attrs["period"] = "monthly"
    handle.attrs["start_month"] = f"{months[0]:06d}"
    handle.attrs["end_month"] = f"{months[-1]:06d}"
    handle.attrs["source"] = str(SOURCE_MONTHLY_DIR)
    handle.attrs["day_night_merge"] = "count-weighted"
    handle.attrs["created_by"] = "aatsr_monthly_3files.py"
    return handle


def read_block(handle: h5py.File, field: str, row0: int, row1: int) -> np.ndarray:
    return handle[field][row0:row1, :]


def weighted_field(
    day: h5py.File,
    night: h5py.File,
    field: str,
    row0: int,
    row1: int,
) -> np.ndarray:
    day_values = read_block(day, field, row0, row1)
    night_values = read_block(night, field, row0, row1)
    day_count = read_block(day, "count", row0, row1)
    night_count = read_block(night, "count", row0, row1)
    day_weight = np.where(day_values > 0, day_count, 0).astype(np.float64)
    night_weight = np.where(night_values > 0, night_count, 0).astype(np.float64)
    denominator = day_weight + night_weight
    numerator = (
        day_values.astype(np.float64) * day_weight
        + night_values.astype(np.float64) * night_weight
    )
    result = np.zeros(denominator.shape, dtype=np.uint16)
    valid = denominator > 0
    result[valid] = np.rint(numerator[valid] / denominator[valid]).clip(0, 65535).astype(np.uint16)
    return result


def composite_temperature(
    day: h5py.File,
    night: h5py.File,
    row0: int,
    row1: int,
) -> np.ndarray:
    values = []
    weights = []
    for field, handle in (("Tnadir", day), ("Tobliq", day), ("Tnadir", night), ("Tobliq", night)):
        value = read_block(handle, field, row0, row1)
        count = read_block(handle, "count", row0, row1)
        weight = np.where(value > 0, count, 0).astype(np.float64)
        values.append(value.astype(np.float64))
        weights.append(weight)
    denominator = sum(weights)
    numerator = sum(value * weight for value, weight in zip(values, weights))
    result = np.zeros(denominator.shape, dtype=np.uint16)
    valid = denominator > 0
    result[valid] = np.rint(numerator[valid] / denominator[valid]).clip(0, 65535).astype(np.uint16)
    return result


def build() -> None:
    months = month_ids()
    check_sources(months)
    outputs = {
        "Ts": OUTPUT_DIR / f"aatsr_monthly_{START_YEAR}_{END_YEAR}_Ts.h5",
        "T": OUTPUT_DIR / f"aatsr_monthly_{START_YEAR}_{END_YEAR}_T.h5",
        "Tv": OUTPUT_DIR / f"aatsr_monthly_{START_YEAR}_{END_YEAR}_Tv.h5",
    }
    if not OVERWRITE and any(path.exists() for path in outputs.values()):
        raise FileExistsError("One or more requested outputs already exist; set OVERWRITE=True to rebuild")

    # Write .part files and rename only after all three files are complete.
    part_paths = {name: path.with_suffix(path.suffix + ".part") for name, path in outputs.items()}
    if not OVERWRITE and any(path.exists() for path in part_paths.values()):
        raise FileExistsError("Partial output exists; inspect or remove .part files before rerunning")
    handles = {
        "Ts": create_output(part_paths["Ts"], "Ts", months),
        "T": create_output(part_paths["T"], "T", months),
        "Tv": create_output(part_paths["Tv"], "Tv", months),
    }
    try:
        for index, month_id in enumerate(months):
            day_path, night_path = source_paths(month_id)
            if not day_path.is_file() or not night_path.is_file():
                logging.warning("%s: missing source; leaving this month as fill value", month_id)
                continue
            logging.info("%s: reading day/night monthly products", month_id)
            with h5py.File(day_path, "r") as day, h5py.File(night_path, "r") as night:
                for row0 in range(0, GRID_SHAPE[0], ROW_BLOCK):
                    row1 = min(row0 + ROW_BLOCK, GRID_SHAPE[0])
                    handles["Ts"]["Ts"][index, row0:row1, :] = weighted_field(day, night, "Ts", row0, row1)
                    handles["Tv"]["Tv"][index, row0:row1, :] = weighted_field(day, night, "Tv", row0, row1)
                    handles["T"]["T"][index, row0:row1, :] = composite_temperature(day, night, row0, row1)
            for handle in handles.values():
                handle.flush()
            logging.info("%s: complete (%d/%d)", month_id, index + 1, len(months))
    finally:
        for handle in handles.values():
            handle.close()

    for name, part_path in part_paths.items():
        part_path.replace(outputs[name])
    logging.info("created %s", OUTPUT_DIR)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    build()
