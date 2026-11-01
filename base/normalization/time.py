from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

import numpy as np

from base.files import read_npz_payload, write_npz_atomic
from base.parameters import require_parameters
from base.quality import usable
from ._fit import fit_linear
from ._validation import quality_flags


# Execution paths and years are supplied by cases.
TIME_INPUT_ROOT = None
TIME_OUTPUT_ROOT = None
YEAR_TEMPLATE = "{year}"
YEARS = None
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
    valid = (np.isfinite(time) & (time >= 0) & (time < 24)
             & np.isfinite(amplitude) & (amplitude >= 0)
             & np.isfinite(peak) & (peak >= 0) & (peak < 24))
    return np.where(valid, amplitude * np.cos(2.0 * np.pi * (time - peak) / 24.0), np.nan)


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
    if not np.isfinite(reference_hour) or not 0 <= reference_hour < 24:
        raise ValueError("reference hour must be in [0, 24)")
    observed = diurnal_anomaly(local_solar_time_hour, amplitude_k, peak_hour)
    reference = diurnal_anomaly(reference_hour, amplitude_k, peak_hour)
    temperature = np.asarray(temperature_k, dtype=np.float64)
    result = temperature + reference - observed
    valid = np.isfinite(temperature) & (temperature >= 150) & (temperature <= 400)
    return np.where(valid & np.isfinite(result) & (result >= 150) & (result <= 400), result, np.nan)


@dataclass(frozen=True)
class DiurnalFit:
    mean_k: float
    amplitude_k: float
    peak_hour: float
    rmse_k: float
    sample_count: int


def fit_diurnal_cycle(temperature_k, local_solar_time_hour, *, weights=1.,
                      quality_flag=0, minimum_span_hours=6.) -> DiurnalFit:
    """Fit one 24-hour harmonic to one site's/day's geometry-normalized samples.

    Hours must use the same local solar time convention as the target. The
    minimum circular time coverage prevents fitting a narrow overpass cluster.
    This empirical baseline does not model clouds or asymmetric day/night DTC.
    """
    if not np.isfinite(minimum_span_hours) or not 0 < minimum_span_hours < 24:
        raise ValueError("minimum time coverage must be in (0, 24)")
    t, hour, w, flags = np.broadcast_arrays(*[np.asarray(x) for x in
        (temperature_k, local_solar_time_hour, weights, quality_flag)])
    valid = (np.isfinite(t) & (t >= 150) & (t <= 400) & np.isfinite(hour)
             & (hour >= 0) & (hour < 24) & np.isfinite(w) & (w > 0) & usable(quality_flags(flags)))
    t, hour, w = t[valid], hour[valid], w[valid]
    if len(t) < 4:
        raise ValueError("at least four valid diurnal samples are required")
    ordered = np.sort(hour)
    span = 24 - np.max(np.diff(np.r_[ordered, ordered[0] + 24]))
    if span < minimum_span_hours:
        raise ValueError("insufficient time span / coverage for a diurnal fit")
    phase = 2*np.pi*hour/24
    design = np.column_stack((np.ones(len(t)), np.cos(phase), np.sin(phase)))
    coefficients, rmse = fit_linear(design, t, w)
    mean, cosine, sine = coefficients
    amplitude = float(np.hypot(cosine, sine))
    peak = float((np.arctan2(sine, cosine)*24/(2*np.pi)) % 24) if amplitude > 1e-10 else 0.
    return DiurnalFit(float(mean), amplitude, peak, rmse, len(t))


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
    require_parameters(indir_angle=indir_angle, outdir_time=outdir_time, years=years)
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
