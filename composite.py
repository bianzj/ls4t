"""L3C temporal compositing, independent from sensor retrieval files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from base.quality import QualityFlag, new_flags, set_flag, usable
from base.files import write_npz_atomic


# ============================================================================
# 手动运行参数
# ============================================================================

INPUT_ROOT = Path("/home/hero/data/ls4t/l3n")
OUTPUT_ROOT = Path("/home/hero/data/ls4t/l3c")
YEARS = range(2003, 2026)
MINIMUM_OBSERVATIONS = 1
OVERWRITE = False


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
    """Create one L3C field from a time-first L3N stack."""

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


def composite_years(
    indir_l3n=None,
    outdir_l3c=None,
    years=None,
    minimum_observations=None,
    overwrite=None,
) -> None:
    """Composite NPZ stacks already grouped by year by the operator."""

    if indir_l3n is None:
        indir_l3n = INPUT_ROOT
    if outdir_l3c is None:
        outdir_l3c = OUTPUT_ROOT
    if years is None:
        years = YEARS
    if minimum_observations is None:
        minimum_observations = MINIMUM_OBSERVATIONS
    if overwrite is None:
        overwrite = OVERWRITE
    for year in years:
        input_year = Path(indir_l3n) / str(year)
        output_path = Path(outdir_l3c) / str(year) / f"LS4T_L3C_{year}.npz"
        if output_path.exists() and not overwrite:
            continue
        inputs = sorted(input_year.glob("*.npz")) if input_year.is_dir() else []
        if not inputs:
            continue
        temperatures, uncertainties, flags = [], [], []
        for input_path in inputs:
            with np.load(input_path, allow_pickle=False) as source:
                temperatures.append(source["temperature_k"])
                uncertainties.append(source["uncertainty_k"])
                flags.append(source["quality_flag"])
        result = temporal_composite(
            np.stack(temperatures),
            np.stack(uncertainties),
            np.stack(flags),
            minimum_observations=int(minimum_observations),
        )
        write_npz_atomic(
            output_path,
            {
                "temperature_k": result.temperature_k,
                "uncertainty_k": result.uncertainty_k,
                "quality_flag": result.quality_flag,
                "observation_count": result.observation_count,
            },
        )


if __name__ == "__main__":
    composite_years()
