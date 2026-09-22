"""Directional temperature normalization extracted from ShIP angular work."""

from __future__ import annotations

import numpy as np


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
    return np.stack((secant, secant * azimuth, secant * solar), axis=-1)


def normalize_directional(
    temperature_k: np.ndarray,
    view_zenith_deg: np.ndarray,
    solar_zenith_deg: np.ndarray,
    relative_azimuth_deg: np.ndarray,
    coefficients_k: np.ndarray,
    *,
    reference_view_zenith_deg: float,
    reference_solar_zenith_deg: float,
    reference_relative_azimuth_deg: float,
) -> np.ndarray:
    """Move observed temperature to a common geometry using calibrated kernels."""
    observed = angular_basis(view_zenith_deg, solar_zenith_deg, relative_azimuth_deg)
    reference = angular_basis(
        reference_view_zenith_deg,
        reference_solar_zenith_deg,
        reference_relative_azimuth_deg,
    )
    coeff = np.asarray(coefficients_k, dtype=np.float64)
    if coeff.shape[-1] != 3:
        raise ValueError("directional coefficients must end with three kernel coefficients")
    correction = np.sum((reference - observed) * coeff, axis=-1)
    return np.asarray(temperature_k, dtype=np.float64) + correction

