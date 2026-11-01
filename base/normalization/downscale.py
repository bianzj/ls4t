"""Auxiliary-variable thermal sharpening with coarse temperature-mean closure.

Pure arrays: callers must align CRS, extent and integer nested pixel grids.
Closure is in kelvin, not emitted radiance or energy. No fine-scale uncertainty
is inferred from the coarse-grid training residuals.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from base.quality import QualityFlag, usable
from ._fit import fit_linear
from ._validation import quality_flags


@dataclass(frozen=True)
class DownscaleResult:
    temperature_k: np.ndarray
    quality_flag: np.ndarray
    coarse_coverage: np.ndarray
    coarse_residual_k: np.ndarray
    coefficients: np.ndarray  # intercept, slopes; TsHARP slope is K per cover fraction
    training_rmse_k: float
    training_count: int
    method: str = "linear"


def tsharp_cover_fraction(ndvi) -> np.ndarray:
    """Agam simplified fractional cover: 1 - (1 - NDVI)**0.625.

    NDVI is decoded, dimensionless and in [0,1]. Outside-domain values become
    NaN, never clipped into bare soil. Water/snow masks belong in the supplied
    quality flags; NDVI alone is not a water classifier. Endmembers are the
    fixed 0/1 standard, not scene-specific extrema fitted from invalid pixels.
    """
    values = np.asarray(ndvi, dtype=float)
    valid = np.isfinite(values) & (values >= 0) & (values <= 1)
    safe = np.where(valid, values, np.nan)
    return 1. - (1. - safe)**.625


def downscale_temperature(
    coarse_temperature_k, fine_predictors, *, coarse_quality_flag=0,
    fine_quality_flag=0, fine_weights=None, minimum_coverage=1., method="linear",
) -> DownscaleResult:
    """Regress on coarse predictor means, predict fine LST, restore coarse means.

    fine_predictors: (fine_rows, fine_cols[, features]); NaN marks no coverage.
    fine_weights: positive pixel areas, default equal areas. Coverage counts
    invalid predictor/quality pixels in the denominator. Partial coverage is
    opt-in and closure then refers only to the surviving fine pixels.
    Invalid/cloudy coarse pixels never receive predictions. Insufficient or
    rank-deficient training raises ValueError instead of inventing detail.

    method='linear': arbitrary auxiliary-variable multivariate linear model.
    method='tsharp': exactly ONE decoded NDVI field; first aggregate NDVI,
    then transform coarse and fine NDVI with 1-(1-NDVI)**0.625. Fit coarse
    T = intercept + slope * cover. Residual correction uses the aggregated
    FINE predictions, guaranteeing temperature-mean closure despite the
    nonlinear NDVI transform. This is not a radiance/energy closure.
    """
    if method not in ("linear", "tsharp"):
        raise ValueError("downscale method must be linear or tsharp")
    coarse = np.asarray(coarse_temperature_k, dtype=float)
    predictors = np.asarray(fine_predictors, dtype=float)
    if predictors.ndim == 2:
        predictors = predictors[..., None]
    if (coarse.ndim != 2 or 0 in coarse.shape or predictors.ndim != 3
            or 0 in predictors.shape):
        raise ValueError("require nonempty coarse 2D and fine 2D/3D arrays")
    rows, cols = coarse.shape
    height, width, features = predictors.shape
    if method == "tsharp":
        if features != 1:
            raise ValueError("TsHARP requires exactly one NDVI predictor")
        # Mask before aggregation, but transform only AFTER aggregation.
        predictors = np.where(np.isfinite(tsharp_cover_fraction(predictors)), predictors, np.nan)
    if height % rows or width % cols or height < rows or width < cols or (height, width) == (rows, cols):
        raise ValueError("fine grid must be a finer integer subdivision of the coarse grid")
    if not np.isfinite(minimum_coverage) or not 0 < minimum_coverage <= 1:
        raise ValueError("minimum_coverage must be in (0, 1]")
    ry, rx = height//rows, width//cols
    weights = np.ones((height, width)) if fine_weights is None else np.broadcast_to(
        np.asarray(fine_weights, dtype=float), (height, width))
    if not np.all(np.isfinite(weights) & (weights > 0)):
        raise ValueError("fine weights must be finite positive pixel areas")
    coarse_flags = np.broadcast_to(quality_flags(coarse_quality_flag), coarse.shape)
    fine_flags = np.broadcast_to(quality_flags(fine_quality_flag), (height, width))
    valid_fine = np.isfinite(predictors).all(axis=-1) & usable(fine_flags)
    active_weights = np.where(valid_fine, weights, 0.)

    def sum_blocks(values):
        return values.reshape(rows, ry, cols, rx, *values.shape[2:]).sum(axis=(1, 3))

    def expand(values):
        return np.repeat(np.repeat(values, ry, axis=0), rx, axis=1)

    support = sum_blocks(active_weights)
    coverage = support / sum_blocks(weights)
    coarse_predictors = np.full((*coarse.shape, features), np.nan)
    numerator = sum_blocks(np.where(valid_fine[..., None], predictors, 0.) * active_weights[..., None])
    np.divide(numerator, support[..., None], out=coarse_predictors, where=support[..., None] > 0)
    valid_coarse = np.isfinite(coarse) & (coarse >= 150) & (coarse <= 400) & usable(coarse_flags)
    supported = (support > 0) & (coverage >= minimum_coverage - 1e-12)
    train = valid_coarse & supported
    if method == "tsharp":
        x = tsharp_cover_fraction(coarse_predictors[train])
        prediction_features = tsharp_cover_fraction(predictors)
    else:
        x = coarse_predictors[train]
        prediction_features = predictors
    if len(x) <= features + 1:
        raise ValueError("insufficient coarse samples for downscaling")
    # Center predictors to keep intercept identifiable with large-valued DEMs.
    center = x.mean(axis=0)
    scale = x.std(axis=0)
    if np.any(scale <= 0):
        raise ValueError("rank deficient predictors: no coarse spatial variation")
    design = np.column_stack((np.ones(len(x)), (x-center)/scale))
    beta, rmse = fit_linear(design, coarse[train], np.ones(len(x)))
    slopes = beta[1:] / scale
    coefficients = np.r_[beta[0] - center @ slopes, slopes]
    predicted = coefficients[0] + prediction_features @ slopes
    coarse_predicted = np.zeros(coarse.shape)
    np.divide(sum_blocks(np.where(valid_fine, predicted, 0.)*active_weights),
              support, out=coarse_predicted, where=support > 0)
    residual = np.where(train, coarse - coarse_predicted, np.nan)
    output = np.where(valid_fine & expand(train), predicted + expand(residual), np.nan)
    flags = (fine_flags | expand(coarse_flags)).copy()
    flags[~valid_fine] |= np.uint16(QualityFlag.INPUT_INVALID)
    flags[expand(~valid_coarse)] |= np.uint16(QualityFlag.INPUT_INVALID)
    flags[expand(~supported)] |= np.uint16(QualityFlag.LOW_SUPPORT)
    # Dropping only an implausible subpixel would destroy closure. Reject its
    # whole parent cell and expose that loss, rather than clipping temperature.
    out_of_range = np.isfinite(output) & ((output < 150) | (output > 400))
    bad_parent = sum_blocks(out_of_range.astype(int)) > 0
    flags[expand(bad_parent)] |= np.uint16(QualityFlag.OUT_OF_RANGE)
    output[expand(bad_parent)] = np.nan
    residual[bad_parent] = np.nan
    return DownscaleResult(output, flags, coverage, residual, coefficients, rmse, int(train.sum()), method)


def downscale_tsharp(
    coarse_temperature_k, fine_ndvi, *, coarse_quality_flag=0,
    fine_quality_flag=0, fine_weights=None, minimum_coverage=1.,
) -> DownscaleResult:
    """TsHARP convenience entry; coefficients are [intercept_K, slope_K_per_fc]."""
    return downscale_temperature(
        coarse_temperature_k, fine_ndvi, method="tsharp",
        coarse_quality_flag=coarse_quality_flag, fine_quality_flag=fine_quality_flag,
        fine_weights=fine_weights, minimum_coverage=minimum_coverage,
    )
