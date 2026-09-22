from __future__ import annotations

import numpy as np


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
