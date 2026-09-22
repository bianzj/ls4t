from __future__ import annotations

import numpy as np


def vegetation_fraction_from_lai(
    lai: np.ndarray | float,
    view_zenith_deg: np.ndarray | float,
    projection_g: float = 0.5,
) -> np.ndarray:
    lai_values, vza = np.broadcast_arrays(
        np.asarray(lai, dtype=np.float64),
        np.asarray(view_zenith_deg, dtype=np.float64),
    )
    cosine = np.cos(np.deg2rad(vza))
    valid = (lai_values >= 0) & (np.abs(vza) < 89.0) & (cosine > 0)
    with np.errstate(over="ignore", invalid="ignore"):
        fraction = 1.0 - np.exp(-projection_g * lai_values / cosine)
    return np.where(valid, np.clip(fraction, 0.0, 1.0), np.nan)


def effective_emissivity(
    soil_emissivity: np.ndarray | float,
    vegetation_emissivity: np.ndarray | float,
    vegetation_fraction: np.ndarray | float,
    *,
    scattering_factor: float = 0.75,
    maximum: float = 0.995,
) -> np.ndarray:
    soil, vegetation, fraction = np.broadcast_arrays(
        np.asarray(soil_emissivity, dtype=np.float64),
        np.asarray(vegetation_emissivity, dtype=np.float64),
        np.asarray(vegetation_fraction, dtype=np.float64),
    )
    scattering = (1.0 - soil) * vegetation * scattering_factor * (1.0 - fraction)
    result = soil * (1.0 - fraction) + vegetation * fraction + scattering
    valid = (
        (soil > 0)
        & (soil <= 1)
        & (vegetation > 0)
        & (vegetation <= 1)
        & (fraction >= 0)
        & (fraction <= 1)
    )
    return np.where(valid, np.clip(result, 0.0, maximum), np.nan)

