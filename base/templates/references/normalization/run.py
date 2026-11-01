from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag
from pathlib import Path
import hashlib
import os
import numpy as np

# 修改本段和文件末尾 main() 即可；所有科学函数均已复制到本文件。
CASE_ROOT = Path(__file__).resolve().parent
USE_DEMO = True  # 合成演示。真实运行时改 False，并填写下面的 NPZ 文件。
INPUT_FILES = []  # 相对路径以 DATA_ROOT 为基准，也接受绝对路径。
CASE_ID = CASE_ROOT.name  # 多个同名任务时改成不同标识。
DATA_ROOT = Path(os.environ["LS4T_DATA_ROOT"]) / CASE_ID if os.environ.get("LS4T_DATA_ROOT") else None
OUTPUT_DIR = Path(os.environ["LS4T_PRODUCT_ROOT"]) / CASE_ID if os.environ.get("LS4T_PRODUCT_ROOT") else None


# Source snapshot: base/quality.py:10 (QualityFlag)
class QualityFlag(IntFlag):
    GOOD = 0
    INPUT_INVALID = 1 << 0
    CLOUD = 1 << 1
    OUT_OF_RANGE = 1 << 2
    RETRIEVAL_FAILED = 1 << 3
    ILL_CONDITIONED = 1 << 4
    NORMALIZATION_FAILED = 1 << 5
    PROFILE_MISMATCH = 1 << 6
    FUSION_REJECTED = 1 << 7
    LOW_SUPPORT = 1 << 8


# Source snapshot: base/quality.py:23 (INVALID_FLAGS)
INVALID_FLAGS = (
    QualityFlag.INPUT_INVALID
    | QualityFlag.CLOUD
    | QualityFlag.OUT_OF_RANGE
    | QualityFlag.RETRIEVAL_FAILED
    | QualityFlag.NORMALIZATION_FAILED
    | QualityFlag.PROFILE_MISMATCH
    | QualityFlag.LOW_SUPPORT
)


# Source snapshot: base/quality.py:34 (new_flags)
def new_flags(shape: tuple[int, ...]) -> np.ndarray:
    return np.zeros(shape, dtype=np.uint16)


# Source snapshot: base/quality.py:38 (set_flag)
def set_flag(flags: np.ndarray, mask: np.ndarray, flag: QualityFlag) -> None:
    flags[np.asarray(mask, dtype=bool)] |= np.uint16(flag)


# Source snapshot: base/quality.py:42 (usable)
def usable(flags: np.ndarray, reject: QualityFlag = INVALID_FLAGS) -> np.ndarray:
    return (np.asarray(flags, dtype=np.uint16) & np.uint16(reject)) == 0


# Source snapshot: base/normalization/_fit.py:7 (fit_linear)
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


# Source snapshot: base/normalization/_validation.py:7 (quality_flags)
def quality_flags(values):
    """Never turn missing/fractional/out-of-range QA values into GOOD by casting."""
    values = np.asarray(values, dtype=float)
    valid = np.isfinite(values) & (values >= 0) & (values <= 65535) & (values == np.floor(values))
    return np.where(valid, values, int(QualityFlag.INPUT_INVALID)).astype(np.uint16)


# Source snapshot: base/normalization/angle.py:22 (REFERENCE_VIEW_ZENITH_DEG)
REFERENCE_VIEW_ZENITH_DEG = 0.0


# Source snapshot: base/normalization/angle.py:23 (REFERENCE_SOLAR_ZENITH_DEG)
REFERENCE_SOLAR_ZENITH_DEG = 30.0


# Source snapshot: base/normalization/angle.py:24 (REFERENCE_RELATIVE_AZIMUTH_DEG)
REFERENCE_RELATIVE_AZIMUTH_DEG = 0.0


# Source snapshot: base/normalization/angle.py:28 (angular_basis)
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
    valid = (np.isfinite(vza) & (vza >= 0) & (vza < 90)
             & np.isfinite(sza) & (sza >= 0) & (sza <= 180) & np.isfinite(raa))
    basis = np.stack((secant, secant * azimuth, secant * solar), axis=-1)
    return np.where(valid[..., None], basis, np.nan)


# Source snapshot: base/normalization/angle.py:48 (normalize_directional)
def normalize_directional(
    temperature_k: np.ndarray,
    view_zenith_deg: np.ndarray,
    solar_zenith_deg: np.ndarray,
    relative_azimuth_deg: np.ndarray,
    coefficients_k: np.ndarray,
    *,
    reference_view_zenith_deg: float | None = None,
    reference_solar_zenith_deg: float | None = None,
    reference_relative_azimuth_deg: float | None = None,
) -> np.ndarray:
    """Move observed temperature to a common geometry using calibrated kernels."""
    if reference_view_zenith_deg is None:
        reference_view_zenith_deg = REFERENCE_VIEW_ZENITH_DEG
    if reference_solar_zenith_deg is None:
        reference_solar_zenith_deg = REFERENCE_SOLAR_ZENITH_DEG
    if reference_relative_azimuth_deg is None:
        reference_relative_azimuth_deg = REFERENCE_RELATIVE_AZIMUTH_DEG
    observed = angular_basis(view_zenith_deg, solar_zenith_deg, relative_azimuth_deg)
    reference = angular_basis(
        reference_view_zenith_deg,
        reference_solar_zenith_deg,
        reference_relative_azimuth_deg,
    )
    if not np.isfinite(reference).all():
        raise ValueError("invalid reference geometry")
    coeff = np.asarray(coefficients_k, dtype=np.float64)
    if coeff.ndim == 0 or coeff.shape[-1] != 3:
        raise ValueError("directional coefficients must end with three kernel coefficients")
    correction = np.sum((reference - observed) * coeff, axis=-1)
    temperature = np.asarray(temperature_k, dtype=np.float64)
    result = temperature + correction
    valid = np.isfinite(temperature) & (temperature >= 150) & (temperature <= 400)
    return np.where(valid & np.isfinite(result) & (result >= 150) & (result <= 400), result, np.nan)


# Source snapshot: base/normalization/time.py:20 (REFERENCE_LOCAL_SOLAR_TIME_HOUR)
REFERENCE_LOCAL_SOLAR_TIME_HOUR = 13.5


# Source snapshot: base/normalization/time.py:24 (diurnal_anomaly)
def diurnal_anomaly(
    local_solar_time_hour: np.ndarray | float,
    amplitude_k: np.ndarray | float,
    peak_hour: np.ndarray | float,
) -> np.ndarray:
    time, amplitude, peak = np.broadcast_arrays(
        np.asarray(local_solar_time_hour, dtype=np.float64),
        np.asarray(amplitude_k, dtype=np.float64),
        np.asarray(peak_hour, dtype=np.float64),
    )
    valid = (np.isfinite(time) & (time >= 0) & (time < 24)
             & np.isfinite(amplitude) & (amplitude >= 0)
             & np.isfinite(peak) & (peak >= 0) & (peak < 24))
    return np.where(valid, amplitude * np.cos(2.0 * np.pi * (time - peak) / 24.0), np.nan)


# Source snapshot: base/normalization/time.py:40 (normalize_local_solar_time)
def normalize_local_solar_time(
    temperature_k: np.ndarray,
    local_solar_time_hour: np.ndarray,
    amplitude_k: np.ndarray,
    peak_hour: np.ndarray,
    *,
    reference_hour: float | None = None,
) -> np.ndarray:
    if reference_hour is None:
        reference_hour = REFERENCE_LOCAL_SOLAR_TIME_HOUR
    if not np.isfinite(reference_hour) or not 0 <= reference_hour < 24:
        raise ValueError("reference hour must be in [0, 24)")
    observed = diurnal_anomaly(local_solar_time_hour, amplitude_k, peak_hour)
    reference = diurnal_anomaly(reference_hour, amplitude_k, peak_hour)
    temperature = np.asarray(temperature_k, dtype=np.float64)
    result = temperature + reference - observed
    valid = np.isfinite(temperature) & (temperature >= 150) & (temperature <= 400)
    return np.where(valid & np.isfinite(result) & (result >= 150) & (result <= 400), result, np.nan)


# Source snapshot: base/normalization/downscale.py:17 (DownscaleResult)
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


# Source snapshot: base/normalization/downscale.py:29 (tsharp_cover_fraction)
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


# Source snapshot: base/normalization/downscale.py:43 (downscale_temperature)
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


# Source snapshot: base/normalization/downscale.py:144 (downscale_tsharp)
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

# ---------- 案例自己的读写与批次；不调用仓库流程 ----------
def validate_storage():
    if DATA_ROOT is None or OUTPUT_DIR is None:
        raise ValueError("Set LS4T_DATA_ROOT and LS4T_PRODUCT_ROOT, or edit DATA_ROOT/OUTPUT_DIR explicitly")
    # 独立副本只识别目录边界，不导入或调用 LS4T 仓库。
    code_root = CASE_ROOT
    for parent in (CASE_ROOT, *CASE_ROOT.parents):
        if (parent / "base").is_dir() and (parent / "cases").is_dir():
            code_root = parent
            break
    code, data, product = code_root.resolve(), DATA_ROOT.resolve(), OUTPUT_DIR.resolve()
    def overlap(left, right):
        return left.is_relative_to(right) or right.is_relative_to(left)
    if overlap(code, data) or overlap(code, product):
        raise ValueError("Data and products must be outside the code directory")
    if overlap(data, product):
        raise ValueError("Data and products must use separate non-overlapping directories")


def inputs():
    validate_storage()
    if USE_DEMO:
        yield "demo", demo_input(), "synthetic demonstration"
        return
    if not INPUT_FILES:
        raise ValueError("Set INPUT_FILES before running real data")
    paths = [(DATA_ROOT / Path(p)).resolve() for p in INPUT_FILES]
    if any(not p.is_relative_to(DATA_ROOT.resolve()) for p in paths):
        raise ValueError("Inputs must stay within DATA_ROOT")
    if len({p.stem for p in paths}) != len(paths):
        raise ValueError("Input stems must be unique within this batch")
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
        if (OUTPUT_DIR / (path.stem + ".npz")).exists():
            raise FileExistsError("Refusing to overwrite: " + path.stem)
    for path in paths:
        with np.load(path, allow_pickle=False) as data:
            yield path.stem, dict(data), str(path.resolve())


def save_result(name, source, **arrays):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / (name + ".npz")
    # Exclusive creation: repeated runs cannot silently replace an earlier result.
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays, synthetic_demo=USE_DEMO,
                            input_source=source,
                            execution_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    print(path)

def demo_input():
    ndvi = np.linspace(.1, .85, 48).reshape(6, 8)
    coarse_ndvi = ndvi.reshape(3, 2, 4, 2).mean((1, 3))
    target = 310. - 10. * tsharp_cover_fraction(coarse_ndvi)
    coefficients = np.array([2., .5, .3])
    observed = target + angular_basis(35., 30., 60.) @ coefficients
    observed = observed + diurnal_anomaly(10., 5., 14.) - diurnal_anomaly(13.5, 5., 14.)
    return dict(temperature_k=observed, view_zenith_deg=35., solar_zenith_deg=30.,
                relative_azimuth_deg=60., directional_coefficients_k=coefficients,
                local_solar_time_hour=10., amplitude_k=5., peak_hour=14., fine_ndvi=ndvi,
                coarse_quality_flag=np.zeros((3, 4), dtype=np.uint16),
                fine_quality_flag=np.zeros((6, 8), dtype=np.uint16))


def main():
    for name, data, source in inputs():
        # 1. QA 过滤；角度/时间参数应来自可比较样本的独立标定。
        coarse_flags = quality_flags(data["coarse_quality_flag"])
        observed = np.where(usable(coarse_flags), data["temperature_k"], np.nan)
        # 2. 角度归一化：参考天顶 0 度、太阳天顶 30 度、相对方位 0 度。
        angular = normalize_directional(observed, data["view_zenith_deg"],
                    data["solar_zenith_deg"], data["relative_azimuth_deg"],
                    data["directional_coefficients_k"])
        # 3. 地方太阳时归一化；这里采用 24 小时单谐波基线。
        normalized = normalize_local_solar_time(angular, data["local_solar_time_hour"],
                    data["amplitude_k"], data["peak_hour"], reference_hour=13.5)
        # 4. TsHARP：须预先同 CRS、同范围、整数嵌套网格；均值闭合以 K 计。
        result = downscale_tsharp(normalized, data["fine_ndvi"],
                    coarse_quality_flag=coarse_flags,
                    fine_quality_flag=data["fine_quality_flag"],
                    fine_weights=data.get("fine_weights"))
        save_result(name, source, temperature_k=result.temperature_k,
                    normalized_coarse_k=normalized, angular_temperature_k=angular,
                    quality_flag=result.quality_flag, coarse_coverage=result.coarse_coverage,
                    coarse_residual_k=result.coarse_residual_k, coefficients=result.coefficients,
                    training_rmse_k=result.training_rmse_k, training_count=result.training_count)


if __name__ == "__main__":
    main()
