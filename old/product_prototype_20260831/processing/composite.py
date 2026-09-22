from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..quality import QualityFlag, new_flags, set_flag, usable


@dataclass(frozen=True)
class CompositeResult:
    temperature_k: np.ndarray
    uncertainty_k: np.ndarray
    quality_flag: np.ndarray
    observation_count: np.ndarray


def temporal_composite(
    temperature_k: np.ndarray,
    uncertainty_k: np.ndarray,
    quality_flag: np.ndarray,
    *,
    minimum_observations: int = 1,
) -> CompositeResult:
    """Create L3C from a time-first stack of L3N fields."""
    values = np.asarray(temperature_k, dtype=np.float64)
    errors = np.asarray(uncertainty_k, dtype=np.float64)
    flags_in = np.asarray(quality_flag, dtype=np.uint16)
    if values.ndim < 1 or values.shape != errors.shape or values.shape != flags_in.shape:
        raise ValueError("temperature, uncertainty and flags must share a time-first shape")
    valid = np.isfinite(values) & np.isfinite(errors) & (errors > 0) & usable(flags_in)
    weights = np.zeros_like(errors)
    np.divide(1.0, errors**2, out=weights, where=valid)
    total_weight = weights.sum(axis=0)
    count = valid.sum(axis=0).astype(np.uint16)
    with np.errstate(divide="ignore", invalid="ignore"):
        composite = (weights * np.nan_to_num(values)).sum(axis=0) / total_weight
        uncertainty = np.sqrt(1.0 / total_weight)
    output_flags = new_flags(values.shape[1:])
    insufficient = count < minimum_observations
    set_flag(output_flags, insufficient, QualityFlag.LOW_SUPPORT)
    composite[insufficient] = np.nan
    uncertainty[insufficient] = np.nan
    return CompositeResult(composite, uncertainty, output_flags, count)
