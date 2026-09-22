"""L4 application: temperature vegetation dryness index."""

from __future__ import annotations

import numpy as np


def tvdi(
    normalized_temperature_k: np.ndarray,
    vegetation_index: np.ndarray,
    dry_edge_coefficients: tuple[float, float],
    wet_edge_coefficients: tuple[float, float],
) -> np.ndarray:
    temperature, vegetation = np.broadcast_arrays(
        np.asarray(normalized_temperature_k, dtype=np.float64),
        np.asarray(vegetation_index, dtype=np.float64),
    )
    dry = dry_edge_coefficients[0] + dry_edge_coefficients[1] * vegetation
    wet = wet_edge_coefficients[0] + wet_edge_coefficients[1] * vegetation
    with np.errstate(divide="ignore", invalid="ignore"):
        result = (temperature - wet) / (dry - wet)
    valid = np.isfinite(temperature) & np.isfinite(vegetation) & (dry > wet)
    return np.where(valid, np.clip(result, 0.0, 1.0), np.nan)

