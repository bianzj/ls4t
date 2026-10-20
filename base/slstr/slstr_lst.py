"""SLSTR-LST product: retrieve and store SLSTR land-surface temperature."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from base.calibration import (
    legacy_split_window_model,
    load_split_window_model,
    save_split_window_model,
)
from base.lst import DualChannelObservation, SplitWindowResult, retrieve_dual_channel_lst
from base.parameters import require_parameters
from base.product import ProductLevel, ProductMetadata, TemperatureProduct
from base.slstr.slstr_data import SlstrDataProduct, add_lst_auxiliary, read_data_product, write_lst_product


# ============================================================================
# 算法默认值；执行参数由 cases 提供
# ============================================================================

SLSTR_DATA_ROOT = None
SLSTR_LST_ROOT = None
DATA_YEAR_TEMPLATE = "{year}/reconstruct"
LST_YEAR_TEMPLATE = "{year}/lst"

YEARS = None
COEFFICIENT_FILE = None
AUXILIARY_FILE = None
GRID_ID = "SLSTR-NATIVE-1KM"
ALGORITHM_VERSION = "slstr-split-window-v1"
UNCERTAINTY_K = 1.0
OVERWRITE = False


SLSTR_VIEW_ZENITH_NODES_DEG = np.asarray([0, 3, 14.9, 38.6, 44.5, 51.2, 58, 65, 70, 75, 80])
SLSTR_WATER_VAPOUR_EDGES_CM = np.asarray([0, 1.25, 2.25, 3.25, 4.25, 5.25, 100])


def import_legacy_coefficients(
    table_path: str | Path,
    output_path: str | Path,
    *,
    version: str,
) -> None:
    """Convert the reviewed 15-column SLSTR table into a versioned model."""

    table = np.loadtxt(table_path)
    model = legacy_split_window_model(
        table,
        SLSTR_VIEW_ZENITH_NODES_DEG,
        SLSTR_WATER_VAPOUR_EDGES_CM,
        coefficient_columns=slice(2, 10),
    )
    save_split_window_model(output_path, model, sensor="SLSTR", version=version)


def retrieve_slstr_lst(item: SlstrDataProduct, coefficient_file=None) -> SplitWindowResult:
    """Run the SLSTR split-window algorithm on a complete SLSTR-DATA product."""

    if coefficient_file is None:
        coefficient_file = COEFFICIENT_FILE
    require_parameters(coefficient_file=coefficient_file)
    item.validate(require_lst_auxiliary=True)
    model = load_split_window_model(coefficient_file)
    observation = DualChannelObservation(
        bt1_k=item.bt8_k,
        bt2_k=item.bt9_k,
        soil_emissivity1=item.soil_emissivity_s8,
        soil_emissivity2=item.soil_emissivity_s9,
        vegetation_emissivity1=item.vegetation_emissivity_s8,
        vegetation_emissivity2=item.vegetation_emissivity_s9,
        lai=item.lai,
        water_vapour=item.tcwv_cm,
        view_zenith_deg=item.view_zenith_deg,
        cloud_mask=item.cloud_mask,
    )
    return retrieve_dual_channel_lst(observation, model)


def produce_slstr_lst(
    input_path: str | Path,
    output_path: str | Path,
    coefficient_file=None,
    auxiliary_file=None,
    *,
    grid_id: str,
    algorithm_version: str,
    uncertainty_k: float,
    start_time: str | None = None,
    end_time: str | None = None,
) -> None:
    """Produce one validated LS4T SLSTR L2LST product."""

    if coefficient_file is None:
        coefficient_file = COEFFICIENT_FILE
    if auxiliary_file is None:
        auxiliary_file = AUXILIARY_FILE
    require_parameters(coefficient_file=coefficient_file, auxiliary_file=auxiliary_file)
    item = read_data_product(input_path)
    if not item.has_lst_auxiliary:
        item = add_lst_auxiliary(item, auxiliary_file)
    actual_start = start_time or item.start_time
    actual_end = end_time or item.end_time
    if not actual_start or not actual_end:
        raise ValueError("start_time and end_time are required when absent from SLSTR-DATA metadata")
    if uncertainty_k <= 0:
        raise ValueError("uncertainty_k must be positive")
    result = retrieve_slstr_lst(item, coefficient_file)
    metadata = ProductMetadata(
        level=ProductLevel.L2LST,
        sensor="SLSTR",
        start_time=actual_start,
        end_time=actual_end,
        grid_id=grid_id,
        algorithm_version=algorithm_version,
        source_products=tuple(
            source
            for source in (
                item.source_product,
                str(input_path),
                str(coefficient_file),
                item.auxiliary_source,
            )
            if source
        ),
        attributes={"temperature_variable_names": ["lst"], "unit": "K"},
    )
    product = TemperatureProduct(
        metadata=metadata,
        variables={
            "lst": result.temperature_k,
            "latitude_deg": item.latitude_deg,
            "longitude_deg": item.longitude_deg,
        },
        quality_flag=result.quality_flag,
        uncertainty={"lst": np.full(item.shape, uncertainty_k, dtype=float)},
    )
    write_lst_product(output_path, product, reference_path=input_path)


def slstr_lst(
    indir_data=None,
    outdir_lst=None,
    coefficient_file=None,
    auxiliary_file=None,
    years=None,
    grid_id=None,
    algorithm_version=None,
    uncertainty_k=None,
    overwrite=None,
    input_year_template=None,
) -> None:
    """按年份处理重建后的 SLSTR-DATA 文件。"""

    if indir_data is None:
        indir_data = SLSTR_DATA_ROOT
    if outdir_lst is None:
        outdir_lst = SLSTR_LST_ROOT
    if coefficient_file is None:
        coefficient_file = COEFFICIENT_FILE
    if auxiliary_file is None:
        auxiliary_file = AUXILIARY_FILE
    if years is None:
        years = YEARS
    if grid_id is None:
        grid_id = GRID_ID
    if algorithm_version is None:
        algorithm_version = ALGORITHM_VERSION
    if uncertainty_k is None:
        uncertainty_k = UNCERTAINTY_K
    if overwrite is None:
        overwrite = OVERWRITE
    if input_year_template is None:
        input_year_template = DATA_YEAR_TEMPLATE

    require_parameters(
        indir_data=indir_data,
        outdir_lst=outdir_lst,
        coefficient_file=coefficient_file,
        auxiliary_file=auxiliary_file,
        years=years,
    )
    for year in years:
        input_year = Path(indir_data) / input_year_template.format(year=int(year))
        output_year = Path(outdir_lst) / LST_YEAR_TEMPLATE.format(year=int(year))
        if not input_year.is_dir():
            print(f"跳过不存在的目录：{input_year}")
            continue
        inputs = sorted(input_year.rglob("*.tif"))
        for index, input_path in enumerate(inputs):
            relative = input_path.relative_to(input_year)
            output_path = (output_year / relative).with_name(relative.stem + "_lst.tif")
            if output_path.exists() and not overwrite:
                continue
            print(f"[{year}] {index + 1}/{len(inputs)} 反演 {input_path}")
            produce_slstr_lst(
                input_path,
                output_path,
                coefficient_file,
                auxiliary_file,
                grid_id=grid_id,
                algorithm_version=algorithm_version,
                uncertainty_k=float(uncertainty_k),
            )
