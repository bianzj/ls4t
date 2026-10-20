"""Convert monthly ERA5 NetCDF data into STREAM's daily forcing layout."""

from __future__ import annotations

import calendar
from contextlib import ExitStack
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np


HOURLY = {
    "skt.h5": "skt",
    "ta.h5": "t2m",
    "ea.h5": "d2m",
    "p.h5": "sp",
    "rin.h5": "ssrd",
    "rli.h5": "strd",
    "stl.h5": "stl1",
    "cvl.h5": "cvl",
    "cvh.h5": "cvh",
}
DAILY = {"sm.h5": "swvl1", "lai_hv.h5": "lai_hv", "lai_lv.h5": "lai_lv"}
FILES = ("t.txt", "u.h5", "lai.h5", *HOURLY, *DAILY)


def forcing_day(output_root: Path, day: date) -> Path:
    return output_root / "force" / str(day.year) / f"{day.timetuple().tm_yday:03d}"


def _variable(dataset, name: str, first: int, last: int) -> np.ndarray:
    if name not in dataset.variables:
        raise ValueError(f"missing ERA5 variable: {name}")
    values = dataset.variables[name][first:last]
    if np.ma.isMaskedArray(values):
        values = values.filled(np.nan)
    return np.asarray(values, dtype=np.float32)


def _orient(data: np.ndarray, longitude_order: str) -> np.ndarray:
    if longitude_order == "0-360":
        if data.shape[-1] % 2:
            raise ValueError("longitude rotation requires an even grid width")
        return np.roll(data, data.shape[-1] // 2, axis=-1)
    if longitude_order == "-180-180":
        return data
    raise ValueError(f"unknown longitude order: {longitude_order}")


def _write_h5(path: Path, data: np.ndarray, longitude_order: str) -> None:
    import h5py

    with h5py.File(path, "w") as output:
        output.create_dataset("data", data=_orient(data, longitude_order), dtype="f4", compression="gzip")


def _validate_month(instant, accumulated, year: int, month: int, longitude_order: str) -> tuple[int, int]:
    days = calendar.monthrange(year, month)[1]
    for dataset in (instant, accumulated):
        time_name = next((name for name in ("valid_time", "time") if name in dataset.variables), None)
        if time_name is None or len(dataset.variables[time_name]) != days * 24:
            raise ValueError(f"expected {days * 24} hourly time values for {year}-{month:02d}")
    instant_time = instant.variables[next(name for name in ("valid_time", "time") if name in instant.variables)][:]
    accumulated_time = accumulated.variables[next(name for name in ("valid_time", "time") if name in accumulated.variables)][:]
    if not np.array_equal(instant_time, accumulated_time):
        raise ValueError("instantaneous and accumulated ERA5 times differ")
    grid = instant.variables.get("skt")
    if grid is None or len(grid.shape) != 3 or grid.shape[0] != days * 24:
        raise ValueError("skt must be hourly (time, latitude, longitude)")
    height, width = grid.shape[1:]
    if longitude_order == "0-360" and "longitude" in instant.variables:
        longitude = instant.variables["longitude"][:]
        if longitude.ndim != 1 or len(longitude) != width or longitude[0] < -1 or longitude[-1] <= 180:
            raise ValueError("longitude grid is not 0..360; choose --longitude-order -180-180")
    for name in ("u10", "v10", *HOURLY.values(), *DAILY.values()):
        dataset = accumulated if name in ("ssrd", "strd") else instant
        variable = dataset.variables.get(name)
        if variable is None or variable.shape != (days * 24, height, width):
            raise ValueError(f"missing or mismatched ERA5 variable: {name}")
    return height, width


def _write_day(instant, accumulated, output_root: Path, day: date, longitude_order: str) -> Path:
    target = forcing_day(output_root, day)
    if target.exists():
        raise FileExistsError(f"forcing day already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    first = (day.day - 1) * 24
    last = first + 24
    with TemporaryDirectory(prefix=f".{target.name}-", dir=target.parent) as temporary:
        staging = Path(temporary)
        np.savetxt(staging / "t.txt", np.arange(24) / 24, fmt="%.6f")
        for file_name, variable in HOURLY.items():
            dataset = accumulated if variable in ("ssrd", "strd") else instant
            values = _variable(dataset, variable, first, last)
            if file_name == "p.h5":
                values /= 100.0
            elif file_name in ("rin.h5", "rli.h5"):
                values /= 3600.0
            _write_h5(staging / file_name, values, longitude_order)
        u10 = _variable(instant, "u10", first, last)
        v10 = _variable(instant, "v10", first, last)
        _write_h5(staging / "u.h5", np.hypot(u10, v10), longitude_order)
        for file_name, variable in DAILY.items():
            values = _variable(instant, variable, first + 12, first + 13)[0]
            _write_h5(staging / file_name, values, longitude_order)
        high = _variable(instant, "lai_hv", first + 12, first + 13)[0]
        low = _variable(instant, "lai_lv", first + 12, first + 13)[0]
        _write_h5(staging / "lai.h5", high + low, longitude_order)
        staging.rename(target)
    return target


def extract_month(source: Path, output_root: Path, year: int, month: int, *,
                  accumulated_source: Path | None = None, longitude_order: str = "0-360") -> list[Path]:
    """Read a single monthly NetCDF, or split instant/accumulation files."""
    import netCDF4

    if not source.is_file():
        raise FileNotFoundError(source)
    if accumulated_source is not None and not accumulated_source.is_file():
        raise FileNotFoundError(accumulated_source)
    if longitude_order not in ("0-360", "-180-180"):
        raise ValueError(f"unknown longitude order: {longitude_order}")
    days = calendar.monthrange(year, month)[1]
    targets = [forcing_day(output_root, date(year, month, number)) for number in range(1, days + 1)]
    existing = [target for target in targets if target.exists()]
    if existing:
        raise FileExistsError(f"forcing day already exists: {existing[0]}")
    with ExitStack() as stack:
        instant = stack.enter_context(netCDF4.Dataset(source))
        accumulated = stack.enter_context(netCDF4.Dataset(accumulated_source)) if accumulated_source else instant
        _validate_month(instant, accumulated, year, month, longitude_order)
        return [_write_day(instant, accumulated, output_root, date(year, month, number), longitude_order)
                for number in range(1, days + 1)]


def check_day(output_root: Path, day: date) -> list[str]:
    """Return missing/corrupt forcing-file names; never modify the output."""
    import h5py

    directory = forcing_day(output_root, day)
    issues = []
    shape = None
    for name in FILES:
        path = directory / name
        if not path.is_file():
            issues.append(name)
            continue
        try:
            if name == "t.txt":
                if np.loadtxt(path).shape != (24,):
                    issues.append(name)
                continue
            with h5py.File(path) as source:
                data = source["data"]
                expected_dimension = 2 if name in (*DAILY, "lai.h5") else 3
                if data.ndim != expected_dimension or (data.ndim == 3 and data.shape[0] != 24):
                    issues.append(name)
                elif shape is None:
                    shape = data.shape[-2:]
                elif data.shape[-2:] != shape:
                    issues.append(name)
        except (OSError, KeyError, ValueError):
            issues.append(name)
    return issues
