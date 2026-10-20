"""SLSTR component-temperature retrieval batch API configured by cases."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from base.lsct import retrieve_components, retrieve_components_window
from base.parameters import require_parameters
from base.product import ProductLevel, ProductMetadata, TemperatureProduct
from base.slstr.slstr_data import read_lsct_input, write_lst_product


# ============================================================================
# 算法默认值；执行参数由 cases 提供
# ============================================================================

SLSTR_LSCT_INPUT_ROOT = None
SLSTR_LSCT_OUTPUT_ROOT = None
INPUT_YEAR_TEMPLATE = "{year}/lsct_input"
OUTPUT_YEAR_TEMPLATE = "{year}/lsct"

YEARS = None
WAVELENGTH_UM = 10.8
COMPONENT_NAMES = ("soil", "vegetation")
WINDOW_SIZE = 5
RIDGE = 0.0
MAX_CONDITION_NUMBER = 1.0e6
GRID_ID = "SLSTR-NATIVE-1KM"
ALGORITHM_VERSION = "slstr-lsct-v1"
OVERWRITE = False


def retrieve_slstr_lsct(
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
    """反演一个准备好的多角度 SLSTR LSCT 输入文件。"""

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

    source = read_lsct_input(input_path)
    observed = source["observed_radiance"]
    weights = source["effective_weights"]
    uncertainty = source.get("observation_uncertainty")
    metadata = source["metadata"]
    geolocation = {
        name: source[name]
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

    names = tuple(component_names)
    if len(names) != result.temperature_k.shape[-1]:
        raise ValueError("COMPONENT_NAMES does not match the retrieved component count")
    variables = {name: result.temperature_k[..., index] for index, name in enumerate(names)}
    variables["residual_rms"] = result.residual_rms
    variables["condition_number"] = result.condition_number
    variables.update(geolocation)
    product_metadata = ProductMetadata(
        level=ProductLevel.L2LSCT,
        sensor="SLSTR",
        start_time=metadata.get("start_time"),
        end_time=metadata.get("end_time"),
        grid_id=grid_id,
        algorithm_version=algorithm_version,
        source_products=(str(input_path),),
        attributes={"temperature_variable_names": list(names), "unit": "K"},
    )
    write_lst_product(
        output_path,
        TemperatureProduct(product_metadata, variables, result.quality_flag),
    )


def slstr_lsct(
    indir_lsct_input=None,
    outdir_lsct=None,
    years=None,
    overwrite=None,
) -> None:
    """按年份批量反演 SLSTR 组分温度。"""

    if indir_lsct_input is None:
        indir_lsct_input = SLSTR_LSCT_INPUT_ROOT
    if outdir_lsct is None:
        outdir_lsct = SLSTR_LSCT_OUTPUT_ROOT
    if years is None:
        years = YEARS
    if overwrite is None:
        overwrite = OVERWRITE

    require_parameters(
        indir_lsct_input=indir_lsct_input,
        outdir_lsct=outdir_lsct,
        years=years,
    )
    for year in years:
        input_year = Path(indir_lsct_input) / INPUT_YEAR_TEMPLATE.format(year=int(year))
        output_year = Path(outdir_lsct) / OUTPUT_YEAR_TEMPLATE.format(year=int(year))
        if not input_year.is_dir():
            print(f"跳过不存在的目录：{input_year}")
            continue
        inputs = sorted(input_year.rglob("*.tif"))
        for index, input_path in enumerate(inputs):
            relative = input_path.relative_to(input_year)
            output_path = (output_year / relative).with_name(relative.stem + "_lsct.tif")
            if output_path.exists() and not overwrite:
                continue
            print(f"[{year}] {index + 1}/{len(inputs)} 组分温度反演 {input_path}")
            retrieve_slstr_lsct(input_path, output_path)
