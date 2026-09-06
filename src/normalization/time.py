from __future__ import annotations

from pathlib import Path

import numpy as np

from base.files import read_npz_payload, write_npz_atomic


# 手动运行参数
TIME_INPUT_ROOT = Path("/home/hero/data/ls4t/l3n_angle")
TIME_OUTPUT_ROOT = Path("/home/hero/data/ls4t/l3n_time")
YEAR_TEMPLATE = "{year}"
YEARS = range(2003, 2026)
REFERENCE_LOCAL_SOLAR_TIME_HOUR = 13.5
OVERWRITE = False


def diurnal_anomaly(
    local_solar_time_hour: np.ndarray | float,
    amplitude_k: np.ndarray | float,
    peak_hour: np.ndarray | float,
) -> np.ndarray:
    time, amplitude, peak = np.broadcast_arrays(
        np.asarray(local_solar_time_hour, dtype=np.float64),
        np.asarray(amplitude_k, dtype=np.float64),
        np.asarray(peak_hour, dtype=np.float64),
    )
    return amplitude * np.cos(2.0 * np.pi * (time - peak) / 24.0)


def normalize_local_solar_time(
    temperature_k: np.ndarray,
    local_solar_time_hour: np.ndarray,
    amplitude_k: np.ndarray,
    peak_hour: np.ndarray,
    *,
    reference_hour: float | None = None,
) -> np.ndarray:
    if reference_hour is None:
        reference_hour = REFERENCE_LOCAL_SOLAR_TIME_HOUR
    observed = diurnal_anomaly(local_solar_time_hour, amplitude_k, peak_hour)
    reference = diurnal_anomaly(reference_hour, amplitude_k, peak_hour)
    return np.asarray(temperature_k, dtype=np.float64) + reference - observed


def time_normalize_years(
    indir_angle=None,
    outdir_time=None,
    years=None,
    overwrite=None,
) -> None:
    """按年份手工执行地方太阳时归一化。"""
    if indir_angle is None:
        indir_angle = TIME_INPUT_ROOT
    if outdir_time is None:
        outdir_time = TIME_OUTPUT_ROOT
    if years is None:
        years = YEARS
    if overwrite is None:
        overwrite = OVERWRITE
    for year in years:
        input_year = Path(indir_angle) / YEAR_TEMPLATE.format(year=year)
        output_year = Path(outdir_time) / YEAR_TEMPLATE.format(year=year)
        for input_path in sorted(input_year.rglob("*.npz")) if input_year.is_dir() else []:
            output_path = output_year / input_path.relative_to(input_year)
            if output_path.exists() and not overwrite:
                continue
            payload = read_npz_payload(input_path)
            payload["temperature_k"] = normalize_local_solar_time(
                payload["temperature_k"],
                payload["local_solar_time_hour"],
                payload["diurnal_amplitude_k"],
                payload["diurnal_peak_hour"],
            )
            write_npz_atomic(output_path, payload)


if __name__ == "__main__":
    time_normalize_years()
