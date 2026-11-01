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


# Source snapshot: base/radiometry.py:11 (C1_UM)
C1_UM = 1.191042972e8


# Source snapshot: base/radiometry.py:12 (C2_UM_K)
C2_UM_K = 1.438776877e4


# Source snapshot: base/radiometry.py:15 (planck_radiance)
def planck_radiance(wavelength_um: float, temperature_k: np.ndarray | float) -> np.ndarray:
    wavelength = float(wavelength_um)
    temperature = np.asarray(temperature_k, dtype=np.float64)
    if wavelength <= 0:
        raise ValueError("wavelength_um must be positive")
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        result = C1_UM / (
            wavelength**5 * np.expm1(C2_UM_K / (wavelength * temperature))
        )
    return np.where(temperature > 0, result, np.nan)


# Source snapshot: base/radiometry.py:27 (inverse_planck)
def inverse_planck(wavelength_um: float, radiance: np.ndarray | float) -> np.ndarray:
    wavelength = float(wavelength_um)
    values = np.asarray(radiance, dtype=np.float64)
    if wavelength <= 0:
        raise ValueError("wavelength_um must be positive")
    with np.errstate(divide="ignore", invalid="ignore"):
        result = C2_UM_K / (
            wavelength * np.log1p(C1_UM / (values * wavelength**5))
        )
    return np.where(values > 0, result, np.nan)


# Source snapshot: base/lsct.py:17 (ComponentRetrievalResult)
@dataclass(frozen=True)
class ComponentRetrievalResult:
    temperature_k: np.ndarray
    radiance: np.ndarray
    residual_rms: np.ndarray
    condition_number: np.ndarray
    quality_flag: np.ndarray


# Source snapshot: base/lsct.py:26 (retrieve_components)
def retrieve_components(
    observed_radiance: np.ndarray,
    effective_weights: np.ndarray,
    wavelength_um: float,
    *,
    observation_uncertainty: np.ndarray | None = None,
    ridge: float = 0.0,
    max_condition_number: float = 1.0e6,
    valid_temperature_range_k: tuple[float, float] = (200.0, 380.0),
) -> ComponentRetrievalResult:
    """Solve ``weights @ component_radiance = observed_radiance`` per pixel.

    The last radiance axis is observation/angle and the final weights axes are
    ``(observation, component)``. Invalid observations are omitted per pixel.
    """
    y = np.asarray(observed_radiance, dtype=np.float64)
    matrix = np.asarray(effective_weights, dtype=np.float64)
    if matrix.ndim < 2 or y.shape != matrix.shape[:-1]:
        raise ValueError("effective_weights must have shape (..., observation, component)")
    spatial_shape = y.shape[:-1]
    n_obs, n_components = matrix.shape[-2:]
    if n_obs < n_components:
        raise ValueError("at least as many observations as components are required")
    if ridge < 0:
        raise ValueError("ridge must be non-negative")

    if observation_uncertainty is None:
        sigma = np.ones_like(y)
    else:
        sigma = np.broadcast_to(np.asarray(observation_uncertainty, dtype=np.float64), y.shape)

    flat_y = y.reshape(-1, n_obs)
    flat_a = matrix.reshape(-1, n_obs, n_components)
    flat_sigma = sigma.reshape(-1, n_obs)
    solved = np.full((flat_y.shape[0], n_components), np.nan)
    residual = np.full(flat_y.shape[0], np.nan)
    condition = np.full(flat_y.shape[0], np.nan)
    flags = new_flags((flat_y.shape[0],))

    for index, (values, design, errors) in enumerate(zip(flat_y, flat_a, flat_sigma)):
        valid = (
            np.isfinite(values)
            & np.all(np.isfinite(design), axis=1)
            & np.isfinite(errors)
            & (errors > 0)
        )
        if valid.sum() < n_components:
            flags[index] |= np.uint16(QualityFlag.INPUT_INVALID | QualityFlag.RETRIEVAL_FAILED)
            continue
        weighted_a = design[valid] / errors[valid, None]
        weighted_y = values[valid] / errors[valid]
        condition[index] = np.linalg.cond(weighted_a)
        if not np.isfinite(condition[index]) or condition[index] > max_condition_number:
            flags[index] |= np.uint16(QualityFlag.ILL_CONDITIONED | QualityFlag.RETRIEVAL_FAILED)
            continue
        try:
            if ridge:
                lhs = weighted_a.T @ weighted_a + ridge * np.eye(n_components)
                rhs = weighted_a.T @ weighted_y
                solution = np.linalg.solve(lhs, rhs)
            else:
                solution = np.linalg.lstsq(weighted_a, weighted_y, rcond=None)[0]
        except np.linalg.LinAlgError:
            flags[index] |= np.uint16(QualityFlag.RETRIEVAL_FAILED)
            continue
        if np.any(solution <= 0):
            flags[index] |= np.uint16(QualityFlag.OUT_OF_RANGE | QualityFlag.RETRIEVAL_FAILED)
            continue
        solved[index] = solution
        difference = design[valid] @ solution - values[valid]
        residual[index] = np.sqrt(np.mean(difference**2))

    temperatures = inverse_planck(wavelength_um, solved)
    low, high = valid_temperature_range_k
    bad_temperature = np.any(
        ~np.isfinite(temperatures) | (temperatures < low) | (temperatures > high), axis=1
    )
    set_flag(flags, bad_temperature, QualityFlag.OUT_OF_RANGE)
    temperatures[bad_temperature] = np.nan
    solved[bad_temperature] = np.nan
    return ComponentRetrievalResult(
        temperature_k=temperatures.reshape(spatial_shape + (n_components,)),
        radiance=solved.reshape(spatial_shape + (n_components,)),
        residual_rms=residual.reshape(spatial_shape),
        condition_number=condition.reshape(spatial_shape),
        quality_flag=flags.reshape(spatial_shape),
    )


# Source snapshot: base/lsct.py:115 (retrieve_components_window)
def retrieve_components_window(
    observed_radiance: np.ndarray,
    effective_weights: np.ndarray,
    wavelength_um: float,
    *,
    window_size: int = 5,
    observation_uncertainty: np.ndarray | None = None,
    ridge: float = 0.0,
    max_condition_number: float = 1.0e6,
    valid_temperature_range_k: tuple[float, float] = (200.0, 380.0),
) -> ComponentRetrievalResult:
    """Window LSCT for cases with fewer angles than components.

    Component radiances are assumed locally constant inside each moving window,
    while effective-emissivity weights may vary by pixel and angle. This is the
    production baseline corresponding to the legacy 5x5 constant-window solves.
    """
    values = np.asarray(observed_radiance, dtype=np.float64)
    weights = np.asarray(effective_weights, dtype=np.float64)
    if values.ndim != 3 or weights.ndim != 4 or weights.shape[:-1] != values.shape:
        raise ValueError(
            "window retrieval requires radiance (row, col, observation) and weights "
            "(row, col, observation, component)"
        )
    if window_size < 1 or window_size % 2 == 0:
        raise ValueError("window_size must be a positive odd integer")
    if observation_uncertainty is None:
        errors = np.ones_like(values)
    else:
        errors = np.broadcast_to(np.asarray(observation_uncertainty, dtype=np.float64), values.shape)

    rows, columns, _ = values.shape
    n_components = weights.shape[-1]
    radius = window_size // 2
    padded_values = np.pad(values, ((radius, radius), (radius, radius), (0, 0)), constant_values=np.nan)
    padded_weights = np.pad(
        weights,
        ((radius, radius), (radius, radius), (0, 0), (0, 0)),
        constant_values=np.nan,
    )
    padded_errors = np.pad(errors, ((radius, radius), (radius, radius), (0, 0)), constant_values=np.nan)
    temperature = np.full((rows, columns, n_components), np.nan)
    radiance = np.full_like(temperature, np.nan)
    residual = np.full((rows, columns), np.nan)
    condition = np.full((rows, columns), np.nan)
    flags = new_flags((rows, columns))

    for row in range(rows):
        for column in range(columns):
            window = (slice(row, row + window_size), slice(column, column + window_size))
            local_values = padded_values[window].reshape(-1)
            local_weights = padded_weights[window].reshape(-1, n_components)
            local_errors = padded_errors[window].reshape(-1)
            result = retrieve_components(
                local_values,
                local_weights,
                wavelength_um,
                observation_uncertainty=local_errors,
                ridge=ridge,
                max_condition_number=max_condition_number,
                valid_temperature_range_k=valid_temperature_range_k,
            )
            temperature[row, column] = result.temperature_k
            radiance[row, column] = result.radiance
            residual[row, column] = result.residual_rms
            condition[row, column] = result.condition_number
            flags[row, column] = result.quality_flag
    return ComponentRetrievalResult(temperature, radiance, residual, condition, flags)

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
    weights = np.array([[.8, .2], [.3, .7]])
    return dict(observed_radiance=weights @ planck_radiance(11., [300., 310.]),
                effective_weights=weights, wavelength_um=11.)


def main():
    for name, data, source in inputs():
        # 输入是已完成大气校正、与有效权重一致的观测辐亮度。
        # 三组分双角度需自行改用本文件的 retrieve_components_window。
        result = retrieve_components(data["observed_radiance"], data["effective_weights"],
                                     float(data["wavelength_um"]),
                                     observation_uncertainty=data.get("observation_uncertainty"))
        save_result(name, source, temperature_k=result.temperature_k,
                    radiance=result.radiance, quality_flag=result.quality_flag,
                    residual_rms=result.residual_rms, condition_number=result.condition_number)


if __name__ == "__main__":
    main()
