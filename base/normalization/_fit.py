"""Small, rank-checked least-squares helper for empirical normalization."""
from __future__ import annotations

import numpy as np


def fit_linear(design, target, weights):
    """Require residual degrees of freedom and an identifiable weighted model."""
    if len(target) <= design.shape[1]:
        raise ValueError("insufficient samples for an identifiable model with residual degrees of freedom")
    root = np.sqrt(weights / np.max(weights))
    matrix = design * root[:, None]
    scale = np.linalg.norm(matrix, axis=0)
    if np.any(scale == 0):
        raise ValueError("rank deficient model: predictors do not identify coefficients")
    matrix = matrix / scale
    solution, _, rank, singular = np.linalg.lstsq(matrix, target * root, rcond=None)
    if rank < design.shape[1] or singular[0] / singular[-1] > 1e10:
        raise ValueError("rank deficient or ill-conditioned model")
    coefficients = solution / scale
    residual = target - design @ coefficients
    rmse = float(np.sqrt(np.average(residual**2, weights=weights)))
    return coefficients, rmse
