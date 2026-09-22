"""Fusion of already compatible L3N fields into another L3N field."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from ...quality import QualityFlag, new_flags, set_flag, usable
from ..pipeline import NormalizationResult
from ..profile import NormalizationProfile


@dataclass(frozen=True)
class FusionResult:
    temperature_k: np.ndarray
    uncertainty_k: np.ndarray
    quality_flag: np.ndarray
    contributing_sensors: np.ndarray
    profile: NormalizationProfile


def fuse_l3n(
    inputs: Sequence[NormalizationResult],
    *,
    innovation_threshold_sigma: float = 4.0,
    minimum_sensors: int = 1,
) -> FusionResult:
    if not inputs:
        raise ValueError("at least one L3N input is required")
    profile = inputs[0].profile
    shape = inputs[0].temperature_k.shape
    sensors = [item.sensor.upper() for item in inputs]
    if len(set(sensors)) != len(sensors):
        raise ValueError("L3N fusion accepts at most one field per sensor")
    for item in inputs[1:]:
        profile.assert_compatible(item.profile)
        if item.temperature_k.shape != shape:
            raise ValueError("all L3N inputs must already share the same grid and shape")
    if innovation_threshold_sigma <= 0 or minimum_sensors < 1 or minimum_sensors > len(inputs):
        raise ValueError("invalid fusion thresholds")

    values = np.stack([item.temperature_k for item in inputs], axis=0)
    errors = np.stack([item.uncertainty_k for item in inputs], axis=0)
    qflags = np.stack([item.quality_flag for item in inputs], axis=0)
    valid = np.isfinite(values) & np.isfinite(errors) & (errors > 0) & usable(qflags)

    preliminary_weights = np.zeros_like(errors)
    np.divide(1.0, errors**2, out=preliminary_weights, where=valid)
    sum_weights = preliminary_weights.sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        preliminary = (preliminary_weights * np.nan_to_num(values)).sum(axis=0) / sum_weights
    innovation = np.abs(values - preliminary)
    accepted = valid & (innovation <= innovation_threshold_sigma * errors)
    # A single available input cannot be an outlier relative to itself.
    accepted |= valid & (valid.sum(axis=0)[None, ...] == 1)
    # If every candidate disagrees, retain the most precise observation and
    # expose the disagreement in FUSION_REJECTED instead of returning no data.
    none_accepted = ~np.any(accepted, axis=0) & np.any(valid, axis=0)
    if np.any(none_accepted):
        ranked_error = np.where(valid, errors, np.inf)
        best = np.argmin(ranked_error, axis=0)
        for sensor_index in range(values.shape[0]):
            accepted[sensor_index] |= none_accepted & (best == sensor_index)
    weights = np.zeros_like(errors)
    np.divide(1.0, errors**2, out=weights, where=accepted)
    sum_weights = weights.sum(axis=0)
    count = accepted.sum(axis=0).astype(np.uint8)
    with np.errstate(divide="ignore", invalid="ignore"):
        fused = (weights * np.nan_to_num(values)).sum(axis=0) / sum_weights
        uncertainty = np.sqrt(1.0 / sum_weights)

    flags = new_flags(shape)
    rejected = np.any(valid & ~accepted, axis=0)
    set_flag(flags, rejected, QualityFlag.FUSION_REJECTED)
    insufficient = count < minimum_sensors
    set_flag(flags, insufficient, QualityFlag.LOW_SUPPORT)
    fused[insufficient] = np.nan
    uncertainty[insufficient] = np.nan
    return FusionResult(fused, uncertainty, flags, count, profile)
