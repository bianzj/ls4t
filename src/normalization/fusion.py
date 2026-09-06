"""Fusion of already compatible L3N fields into another L3N field."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

from base.quality import QualityFlag, new_flags, set_flag, usable
from base.files import read_npz_payload, write_npz_atomic
from .profile import NormalizationProfile


# 手动运行参数
FUSION_INPUT_ROOTS = (
    Path("/home/hero/data/ls4t/aatsr/l3n"),
    Path("/home/hero/data/ls4t/slstr/l3n"),
    Path("/home/hero/data/ls4t/msg/l3n"),
)
FUSION_OUTPUT_ROOT = Path("/home/hero/data/ls4t/fusion/l3n")
YEARS = range(2003, 2026)
INNOVATION_THRESHOLD_SIGMA = 4.0
MINIMUM_SENSORS = 1
OVERWRITE = False


@dataclass(frozen=True)
class NormalizedField:
    """One already normalized field supplied to the fusion operation."""

    sensor: str
    temperature_k: np.ndarray
    uncertainty_k: np.ndarray
    quality_flag: np.ndarray
    profile: NormalizationProfile


@dataclass(frozen=True)
class FusionResult:
    temperature_k: np.ndarray
    uncertainty_k: np.ndarray
    quality_flag: np.ndarray
    contributing_sensors: np.ndarray
    profile: NormalizationProfile


def fuse_l3n(
    inputs: Sequence[NormalizedField],
    *,
    innovation_threshold_sigma: float | None = None,
    minimum_sensors: int | None = None,
) -> FusionResult:
    if innovation_threshold_sigma is None:
        innovation_threshold_sigma = INNOVATION_THRESHOLD_SIGMA
    if minimum_sensors is None:
        minimum_sensors = MINIMUM_SENSORS
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


def fusion_years(
    input_roots=None,
    output_root=None,
    years=None,
    innovation_threshold_sigma=None,
    minimum_sensors=None,
    overwrite=None,
) -> None:
    """按相同年份和相对文件名融合多个已归一化传感器目录。"""
    if input_roots is None:
        input_roots = FUSION_INPUT_ROOTS
    if output_root is None:
        output_root = FUSION_OUTPUT_ROOT
    if years is None:
        years = YEARS
    if innovation_threshold_sigma is None:
        innovation_threshold_sigma = INNOVATION_THRESHOLD_SIGMA
    if minimum_sensors is None:
        minimum_sensors = MINIMUM_SENSORS
    if overwrite is None:
        overwrite = OVERWRITE
    roots = tuple(Path(root) for root in input_roots)
    for year in years:
        relative_names = set()
        for root in roots:
            year_root = root / str(year)
            if year_root.is_dir():
                relative_names.update(path.relative_to(year_root) for path in year_root.rglob("*.npz"))
        for relative in sorted(relative_names):
            output_path = Path(output_root) / str(year) / relative
            if output_path.exists() and not overwrite:
                continue
            fields = []
            for root in roots:
                input_path = root / str(year) / relative
                if not input_path.is_file():
                    continue
                payload = read_npz_payload(input_path)
                profile = NormalizationProfile(
                    str(payload["profile_name"].item()),
                    str(payload["profile_version"].item()),
                    str(payload["grid_id"].item()),
                    str(payload["temporal_interval"].item()),
                )
                fields.append(
                    NormalizedField(
                        str(payload["sensor"].item()),
                        payload["temperature_k"],
                        payload["uncertainty_k"],
                        payload["quality_flag"],
                        profile,
                    )
                )
            if not fields:
                continue
            result = fuse_l3n(
                fields,
                innovation_threshold_sigma=float(innovation_threshold_sigma),
                minimum_sensors=int(minimum_sensors),
            )
            write_npz_atomic(
                output_path,
                {
                    "temperature_k": result.temperature_k,
                    "uncertainty_k": result.uncertainty_k,
                    "quality_flag": result.quality_flag,
                    "contributing_sensors": result.contributing_sensors,
                    "sensor": np.asarray("MULTI"),
                    "profile_name": np.asarray(result.profile.name),
                    "profile_version": np.asarray(result.profile.version),
                    "grid_id": np.asarray(result.profile.grid_id),
                    "temporal_interval": np.asarray(result.profile.temporal_interval),
                },
            )


if __name__ == "__main__":
    fusion_years()
