"""L4 applications; temperature retrieval and normalization do not belong here."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from base.files import read_npz_payload, write_npz_atomic
from base.parameters import require_parameters


# ============================================================================
# 算法默认值；执行参数由 cases 提供
# ============================================================================

L3_INPUT_ROOT = None
L4_OUTPUT_ROOT = None
YEARS = None
DRY_EDGE_COEFFICIENTS = (330.0, -10.0)
WET_EDGE_COEFFICIENTS = (290.0, -2.0)
OVERWRITE = False


def tvdi(
    normalized_temperature_k: np.ndarray,
    vegetation_index: np.ndarray,
    dry_edge_coefficients: tuple[float, float],
    wet_edge_coefficients: tuple[float, float],
) -> np.ndarray:
    temperature, vegetation = np.broadcast_arrays(
        np.asarray(normalized_temperature_k, dtype=np.float64),
        np.asarray(vegetation_index, dtype=np.float64),
    )
    dry = dry_edge_coefficients[0] + dry_edge_coefficients[1] * vegetation
    wet = wet_edge_coefficients[0] + wet_edge_coefficients[1] * vegetation
    with np.errstate(divide="ignore", invalid="ignore"):
        result = (temperature - wet) / (dry - wet)
    valid = np.isfinite(temperature) & np.isfinite(vegetation) & (dry > wet)
    return np.where(valid, np.clip(result, 0.0, 1.0), np.nan)


def tvdi_years(
    indir_l3=None,
    outdir_l4=None,
    years=None,
    dry_edge_coefficients=None,
    wet_edge_coefficients=None,
    overwrite=None,
) -> None:
    """按年份手工计算 TVDI，不调用其他 L4 应用。"""
    if indir_l3 is None:
        indir_l3 = L3_INPUT_ROOT
    if outdir_l4 is None:
        outdir_l4 = L4_OUTPUT_ROOT
    if years is None:
        years = YEARS
    if dry_edge_coefficients is None:
        dry_edge_coefficients = DRY_EDGE_COEFFICIENTS
    if wet_edge_coefficients is None:
        wet_edge_coefficients = WET_EDGE_COEFFICIENTS
    if overwrite is None:
        overwrite = OVERWRITE
    require_parameters(indir_l3=indir_l3, outdir_l4=outdir_l4, years=years)
    for year in years:
        input_year = Path(indir_l3) / str(year)
        output_year = Path(outdir_l4) / str(year)
        for input_path in sorted(input_year.rglob("*.npz")) if input_year.is_dir() else []:
            output_path = output_year / input_path.relative_to(input_year)
            if output_path.exists() and not overwrite:
                continue
            payload = read_npz_payload(input_path)
            write_npz_atomic(
                output_path,
                {
                    "tvdi": tvdi(
                        payload["temperature_k"],
                        payload["vegetation_index"],
                        tuple(dry_edge_coefficients),
                        tuple(wet_edge_coefficients),
                    )
                },
            )
