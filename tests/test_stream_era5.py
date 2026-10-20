from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import h5py
import numpy as np
import pytest

from base.stream_era5 import _validate_month, check_day, extract_month, forcing_day


class Dataset:
    def __init__(self, variables):
        self.variables = variables

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def example_month(year=2024, month=2):
    hours = calendar.monthrange(year, month)[1] * 24
    values = np.tile(np.arange(4, dtype=np.float32), (hours, 2, 1))
    instant = {name: values.copy() for name in (
        "skt", "t2m", "d2m", "sp", "stl1", "cvl", "cvh", "swvl1", "lai_hv", "lai_lv",
        "u10", "v10",
    )}
    instant["time"] = np.arange(hours)
    instant["longitude"] = np.array([0, 90, 180, 270])
    accumulated = {"time": np.arange(hours), "ssrd": values.copy(), "strd": values.copy()}
    return Dataset(instant), Dataset(accumulated)


def test_prepare_split_era5_for_stream(tmp_path: Path, monkeypatch):
    instant, accumulated = example_month()
    sources = {str(tmp_path / "instant.nc"): instant, str(tmp_path / "accum.nc"): accumulated}
    for source in sources:
        Path(source).touch()
    monkeypatch.setitem(__import__("sys").modules, "netCDF4",
                        SimpleNamespace(Dataset=lambda source: sources[str(source)]))

    days = extract_month(tmp_path / "instant.nc", tmp_path / "stream", 2024, 2,
                         accumulated_source=tmp_path / "accum.nc")
    assert len(days) == 29
    assert days[0] == forcing_day(tmp_path / "stream", date(2024, 2, 1))
    assert days[-1].name == "060"
    assert check_day(tmp_path / "stream", date(2024, 2, 1)) == []
    assert (days[0] / "t.txt").read_text().splitlines()[-1] == "0.958333"
    with h5py.File(days[0] / "sm.h5") as source:
        np.testing.assert_array_equal(source["data"][0], [2, 3, 0, 1])
    with h5py.File(days[0] / "lai.h5") as source:
        np.testing.assert_array_equal(source["data"][0], [4, 6, 0, 2])
    with h5py.File(days[0] / "ea.h5") as source:
        np.testing.assert_array_equal(source["data"][0, 0], [2, 3, 0, 1])
    with h5py.File(days[0] / "u.h5") as source:
        np.testing.assert_allclose(source["data"][0, 0], np.sqrt(2) * np.array([2, 3, 0, 1]))
    with h5py.File(days[0] / "p.h5") as source:
        np.testing.assert_allclose(source["data"][0, 0], [0.02, 0.03, 0, 0.01])
    with h5py.File(days[0] / "rin.h5") as source:
        np.testing.assert_allclose(source["data"][0, 0], [2 / 3600, 3 / 3600, 0, 1 / 3600])
    with pytest.raises(FileExistsError):
        extract_month(tmp_path / "instant.nc", tmp_path / "stream", 2024, 2,
                      accumulated_source=tmp_path / "accum.nc")
    (days[0] / "ea.h5").unlink()
    assert check_day(tmp_path / "stream", date(2024, 2, 1)) == ["ea.h5"]


def test_validate_incomplete_and_mismatched_months():
    instant, accumulated = example_month()
    instant.variables["time"] = instant.variables["time"][:-1]
    with pytest.raises(ValueError, match="hourly time"):
        _validate_month(instant, accumulated, 2024, 2, "0-360")
    instant.variables["time"] = np.arange(29 * 24)
    accumulated.variables["time"][0] = -1
    with pytest.raises(ValueError, match="times differ"):
        _validate_month(instant, accumulated, 2024, 2, "0-360")
    accumulated.variables["time"][0] = 0
    del instant.variables["d2m"]
    with pytest.raises(ValueError, match="d2m"):
        _validate_month(instant, accumulated, 2024, 2, "0-360")


def test_reject_wrong_longitude_order():
    instant, accumulated = example_month()
    instant.variables["longitude"] = np.array([-180, -90, 0, 90])
    with pytest.raises(ValueError, match="longitude grid"):
        _validate_month(instant, accumulated, 2024, 2, "0-360")
    assert _validate_month(instant, accumulated, 2024, 2, "-180-180") == (2, 4)
