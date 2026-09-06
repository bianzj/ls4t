"""AATSR component-temperature retrieval run manually by date range."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from base.lsct import retrieve_components, retrieve_components_window
from base.product import ProductLevel, ProductMetadata, TemperatureProduct
from base.product_io import write_product


# ============================================================================
# 手动运行参数
# ============================================================================

AATSR_LSCT_INPUT_ROOT = Path("/home/hero/data/ls4t/aatsr/lsct_input")
AATSR_LSCT_OUTPUT_ROOT = Path("/home/hero/data/ls4t/aatsr/lsct")
DAY_TEMPLATE = "{year:04d}/{month:02d}/{day:02d}"
YEARS = range(2003, 2012)
MONTHS = range(1, 13)
DAYS = range(1, 32)
WAVELENGTH_UM = 10.8
COMPONENT_NAMES = ("soil", "vegetation")
WINDOW_SIZE = 5
RIDGE = 0.0
MAX_CONDITION_NUMBER = 1.0e6
GRID_ID = "AATSR-NATIVE-1KM"
ALGORITHM_VERSION = "aatsr-lsct-v1"
OVERWRITE = False


def retrieve_aatsr_lsct(
    input_path,
    output_path,
    wavelength_um=None,
    component_names=None,
    window_size=None,
    ridge=None,
    max_condition_number=None,
    grid_id=None,
    algorithm_version=None,
) -> None:
    if wavelength_um is None:
        wavelength_um = WAVELENGTH_UM
    if component_names is None:
        component_names = COMPONENT_NAMES
    if window_size is None:
        window_size = WINDOW_SIZE
    if ridge is None:
        ridge = RIDGE
    if max_condition_number is None:
        max_condition_number = MAX_CONDITION_NUMBER
    if grid_id is None:
        grid_id = GRID_ID
    if algorithm_version is None:
        algorithm_version = ALGORITHM_VERSION
    with np.load(input_path, allow_pickle=False) as source:
        observed = source["observed_radiance"]
        weights = source["effective_weights"]
        uncertainty = source["observation_uncertainty"] if "observation_uncertainty" in source else None
        metadata = json.loads(str(source["metadata"].item()))
        geolocation = {
            name: source[name].copy()
            for name in ("latitude_deg", "longitude_deg")
            if name in source
        }
    if len(geolocation) == 1:
        raise ValueError("LSCT input must provide latitude_deg and longitude_deg together")
    if observed.ndim == 3 and weights.ndim == 4 and weights.shape[-2] < weights.shape[-1]:
        result = retrieve_components_window(
            observed,
            weights,
            float(wavelength_um),
            window_size=int(window_size),
            observation_uncertainty=uncertainty,
            ridge=float(ridge),
            max_condition_number=float(max_condition_number),
        )
    else:
        result = retrieve_components(
            observed,
            weights,
            float(wavelength_um),
            observation_uncertainty=uncertainty,
            ridge=float(ridge),
            max_condition_number=float(max_condition_number),
        )
    component_names = tuple(component_names)
    if result.temperature_k.shape[-1] != len(component_names):
        raise ValueError("COMPONENT_NAMES does not match the retrieved component count")
    variables = {
        name: result.temperature_k[..., index]
        for index, name in enumerate(component_names)
    }
    variables["residual_rms"] = result.residual_rms
    variables["condition_number"] = result.condition_number
    variables.update(geolocation)
    product_metadata = ProductMetadata(
        ProductLevel.L2LSCT,
        "AATSR",
        metadata["start_time"],
        metadata["end_time"],
        grid_id,
        algorithm_version,
        source_products=(str(input_path),),
        attributes={"temperature_variable_names": list(component_names), "unit": "K"},
    )
    write_product(output_path, TemperatureProduct(product_metadata, variables, result.quality_flag))


def aatsr_lsct(
    indir_lsct_input=None,
    outdir_lsct=None,
    years=None,
    months=None,
    days=None,
    overwrite=None,
) -> None:
    if indir_lsct_input is None:
        indir_lsct_input = AATSR_LSCT_INPUT_ROOT
    if outdir_lsct is None:
        outdir_lsct = AATSR_LSCT_OUTPUT_ROOT
    if years is None:
        years = YEARS
    if months is None:
        months = MONTHS
    if days is None:
        days = DAYS
    if overwrite is None:
        overwrite = OVERWRITE
    for year in years:
        for month in months:
            for day in days:
                input_day = Path(indir_lsct_input) / DAY_TEMPLATE.format(year=year, month=month, day=day)
                if not input_day.is_dir():
                    continue
                output_day = Path(outdir_lsct) / DAY_TEMPLATE.format(year=year, month=month, day=day)
                inputs = sorted(input_day.rglob("*.npz"))
                for input_path in inputs:
                    relative = input_path.relative_to(input_day)
                    output_path = (output_day / relative).with_name(relative.stem + "_lsct.npz")
                    if output_path.exists() and not overwrite:
                        continue
                    retrieve_aatsr_lsct(input_path, output_path)


if __name__ == "__main__":
    aatsr_lsct()
