"""Directional temperature normalization extracted from ShIP angular work."""

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
ANGLE_INPUT_ROOT = None
ANGLE_OUTPUT_ROOT = None
YEAR_TEMPLATE = "{year}"
YEARS = None
REFERENCE_VIEW_ZENITH_DEG = 0.0
REFERENCE_SOLAR_ZENITH_DEG = 30.0
REFERENCE_RELATIVE_AZIMUTH_DEG = 0.0
OVERWRITE = False


def angular_basis(
    view_zenith_deg: np.ndarray | float,
    solar_zenith_deg: np.ndarray | float,
    relative_azimuth_deg: np.ndarray | float,
) -> np.ndarray:
    vza, sza, raa = np.broadcast_arrays(
        np.asarray(view_zenith_deg, dtype=np.float64),
        np.asarray(solar_zenith_deg, dtype=np.float64),
        np.asarray(relative_azimuth_deg, dtype=np.float64),
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        secant = 1.0 / np.cos(np.deg2rad(vza)) - 1.0
    azimuth = np.cos(np.deg2rad(raa))
    solar = np.cos(np.deg2rad(sza))
    valid = (np.isfinite(vza) & (vza >= 0) & (vza < 90)
             & np.isfinite(sza) & (sza >= 0) & (sza <= 180) & np.isfinite(raa))
    basis = np.stack((secant, secant * azimuth, secant * solar), axis=-1)
    return np.where(valid[..., None], basis, np.nan)


def normalize_directional(
    temperature_k: np.ndarray,
    view_zenith_deg: np.ndarray,
    solar_zenith_deg: np.ndarray,
    relative_azimuth_deg: np.ndarray,
    coefficients_k: np.ndarray,
    *,
    reference_view_zenith_deg: float | None = None,
    reference_solar_zenith_deg: float | None = None,
    reference_relative_azimuth_deg: float | None = None,
) -> np.ndarray:
    """Move observed temperature to a common geometry using calibrated kernels."""
    if reference_view_zenith_deg is None:
        reference_view_zenith_deg = REFERENCE_VIEW_ZENITH_DEG
    if reference_solar_zenith_deg is None:
        reference_solar_zenith_deg = REFERENCE_SOLAR_ZENITH_DEG
    if reference_relative_azimuth_deg is None:
        reference_relative_azimuth_deg = REFERENCE_RELATIVE_AZIMUTH_DEG
    observed = angular_basis(view_zenith_deg, solar_zenith_deg, relative_azimuth_deg)
    reference = angular_basis(
        reference_view_zenith_deg,
        reference_solar_zenith_deg,
        reference_relative_azimuth_deg,
    )
    if not np.isfinite(reference).all():
        raise ValueError("invalid reference geometry")
    coeff = np.asarray(coefficients_k, dtype=np.float64)
    if coeff.ndim == 0 or coeff.shape[-1] != 3:
        raise ValueError("directional coefficients must end with three kernel coefficients")
    correction = np.sum((reference - observed) * coeff, axis=-1)
    temperature = np.asarray(temperature_k, dtype=np.float64)
    result = temperature + correction
    valid = np.isfinite(temperature) & (temperature >= 150) & (temperature <= 400)
    return np.where(valid & np.isfinite(result) & (result >= 150) & (result <= 400), result, np.nan)


@dataclass(frozen=True)
class DirectionalFit:
    coefficients_k: np.ndarray
    rmse_k: float
    sample_count: int


def fit_directional_coefficients(
    temperature_k, reference_temperature_k, view_zenith_deg, solar_zenith_deg,
    relative_azimuth_deg, *, reference_view_zenith_deg=0.,
    reference_solar_zenith_deg=30., reference_relative_azimuth_deg=0.,
    weights=1., quality_flag=0,
) -> DirectionalFit:
    """Calibrate one three-kernel model from matched same-time reference pairs.

    Supply co-located, same-state reference temperatures at the stated reference
    geometry. Mixing unrelated dates/land covers can confound geometry and LST.
    rmse_k is an in-sample diagnostic, not independent retrieval accuracy.
    """
    t, ref, v, s, a, w, flags = np.broadcast_arrays(
        *[np.asarray(x) for x in (temperature_k, reference_temperature_k,
          view_zenith_deg, solar_zenith_deg, relative_azimuth_deg, weights, quality_flag)]
    )
    reference = angular_basis(reference_view_zenith_deg, reference_solar_zenith_deg,
                              reference_relative_azimuth_deg)
    if not np.isfinite(reference).all():
        raise ValueError("invalid reference geometry")
    design = angular_basis(v, s, a) - reference
    valid = (np.isfinite(design).all(axis=-1) & np.isfinite(t) & np.isfinite(ref)
             & (t >= 150) & (t <= 400) & (ref >= 150) & (ref <= 400)
             & np.isfinite(w) & (w > 0) & usable(quality_flags(flags)))
    coefficients, rmse = fit_linear(design[valid], (t-ref)[valid], w[valid])
    return DirectionalFit(coefficients, rmse, int(valid.sum()))


def angle_normalize_years(
    indir_temperature=None,
    outdir_angle=None,
    years=None,
    overwrite=None,
) -> None:
    """按年份手工执行角度归一化，不调用时间或空间归一化。"""
    if indir_temperature is None:
        indir_temperature = ANGLE_INPUT_ROOT
    if outdir_angle is None:
        outdir_angle = ANGLE_OUTPUT_ROOT
    if years is None:
        years = YEARS
    if overwrite is None:
        overwrite = OVERWRITE
    require_parameters(
        indir_temperature=indir_temperature,
        outdir_angle=outdir_angle,
        years=years,
    )
    for year in years:
        input_year = Path(indir_temperature) / YEAR_TEMPLATE.format(year=year)
        output_year = Path(outdir_angle) / YEAR_TEMPLATE.format(year=year)
        for input_path in sorted(input_year.rglob("*.npz")) if input_year.is_dir() else []:
            output_path = output_year / input_path.relative_to(input_year)
            if output_path.exists() and not overwrite:
                continue
            payload = read_npz_payload(input_path)
            payload["temperature_k"] = normalize_directional(
                payload["temperature_k"],
                payload["view_zenith_deg"],
                payload["solar_zenith_deg"],
                payload["relative_azimuth_deg"],
                payload["directional_coefficients_k"],
            )
            write_npz_atomic(output_path, payload)
