from __future__ import annotations

from pathlib import Path

import numpy as np

from base.files import read_npz_payload, write_npz_atomic
from base.parameters import require_parameters
from base.quality import QualityFlag, set_flag, usable


# Execution paths and years are supplied by cases.
SPACE_INPUT_ROOT = None
SPACE_OUTPUT_ROOT = None
YEAR_TEMPLATE = "{year}"
YEARS = None
TARGET_SHAPE = (3600, 7200)
OVERWRITE = False


def _aggregate_flags(
    flags: np.ndarray,
    row_index: np.ndarray,
    column_index: np.ndarray,
    target_shape: tuple[int, int],
    valid_mask: np.ndarray,
) -> np.ndarray:
    flags, row, column, valid = np.broadcast_arrays(
        np.asarray(flags, dtype=np.uint16),
        row_index,
        column_index,
        valid_mask,
    )
    flags = flags.ravel()
    row = np.asarray(row, dtype=np.int64).ravel()
    column = np.asarray(column, dtype=np.int64).ravel()
    valid = np.asarray(valid, dtype=bool).ravel()
    inside = (
        valid
        & (row >= 0)
        & (row < target_shape[0])
        & (column >= 0)
        & (column < target_shape[1])
    )
    linear = row[inside] * target_shape[1] + column[inside]
    result = np.zeros(target_shape[0] * target_shape[1], dtype=np.uint16)
    np.bitwise_or.at(result, linear, flags[inside])
    return result.reshape(target_shape)


def aggregate_to_grid(
    values: np.ndarray,
    row_index: np.ndarray,
    column_index: np.ndarray,
    target_shape: tuple[int, int],
    *,
    weights: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Aggregate irregular/duplicate source samples without hiding out-of-grid indices."""
    value, row, column = np.broadcast_arrays(values, row_index, column_index)
    source_shape = value.shape
    if weights is None:
        weight = np.ones(source_shape, dtype=np.float64)
    else:
        weight = np.broadcast_to(np.asarray(weights, dtype=np.float64), source_shape)
    value = np.asarray(value, dtype=np.float64).ravel()
    row = np.asarray(row, dtype=np.int64).ravel()
    column = np.asarray(column, dtype=np.int64).ravel()
    weight = np.asarray(weight, dtype=np.float64).ravel()
    inside = (
        (row >= 0)
        & (row < target_shape[0])
        & (column >= 0)
        & (column < target_shape[1])
    )
    if np.any(~inside & np.isfinite(value)):
        raise IndexError(f"{np.sum(~inside & np.isfinite(value))} samples fall outside target grid")
    valid = inside & np.isfinite(value) & np.isfinite(weight) & (weight > 0)
    linear = row[valid] * target_shape[1] + column[valid]
    total = np.zeros(target_shape[0] * target_shape[1], dtype=np.float64)
    support = np.zeros_like(total)
    np.add.at(total, linear, value[valid] * weight[valid])
    np.add.at(support, linear, weight[valid])
    with np.errstate(divide="ignore", invalid="ignore"):
        output = total / support
    output[support == 0] = np.nan
    return output.reshape(target_shape), support.reshape(target_shape)


def space_normalize_years(
    indir_time=None,
    outdir_space=None,
    years=None,
    target_shape=None,
    overwrite=None,
) -> None:
    """按年份把温度和不确定度聚合到目标网格。"""
    if indir_time is None:
        indir_time = SPACE_INPUT_ROOT
    if outdir_space is None:
        outdir_space = SPACE_OUTPUT_ROOT
    if years is None:
        years = YEARS
    if target_shape is None:
        target_shape = TARGET_SHAPE
    if overwrite is None:
        overwrite = OVERWRITE
    require_parameters(indir_time=indir_time, outdir_space=outdir_space, years=years)
    target_shape = tuple(target_shape)
    for year in years:
        input_year = Path(indir_time) / YEAR_TEMPLATE.format(year=year)
        output_year = Path(outdir_space) / YEAR_TEMPLATE.format(year=year)
        for input_path in sorted(input_year.rglob("*.npz")) if input_year.is_dir() else []:
            output_path = output_year / input_path.relative_to(input_year)
            if output_path.exists() and not overwrite:
                continue
            payload = read_npz_payload(input_path)
            values = np.asarray(payload["temperature_k"], dtype=float)
            errors = np.asarray(payload["uncertainty_k"], dtype=float)
            input_flags = np.asarray(
                payload.get("quality_flag", np.zeros(values.shape, dtype=np.uint16)),
                dtype=np.uint16,
            )
            if values.shape != errors.shape or values.shape != input_flags.shape:
                raise ValueError(f"temperature, uncertainty and quality_flag shapes differ: {input_path}")
            source_valid = (
                usable(input_flags)
                & np.isfinite(values)
                & np.isfinite(errors)
                & (errors > 0)
            )
            row = payload["target_row_index"]
            column = payload["target_column_index"]
            temperature, support = aggregate_to_grid(
                np.where(source_valid, values, np.nan), row, column, target_shape
            )
            uncertainty, _ = aggregate_to_grid(
                np.where(source_valid, errors, np.nan), row, column, target_shape
            )
            flags = _aggregate_flags(input_flags, row, column, target_shape, source_valid)
            set_flag(flags, support == 0, QualityFlag.LOW_SUPPORT)
            payload["temperature_k"] = temperature
            payload["uncertainty_k"] = uncertainty
            payload["quality_flag"] = flags
            payload["support"] = support
            payload.pop("target_row_index", None)
            payload.pop("target_column_index", None)
            write_npz_atomic(output_path, payload)
