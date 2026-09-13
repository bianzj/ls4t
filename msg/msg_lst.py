"""MSG land-surface temperature retrieval batch API configured by cases."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from base.calibration import load_split_window_model
from base.lst import DualChannelObservation, retrieve_dual_channel_lst
from base.parameters import require_parameters
from base.product import ProductLevel, ProductMetadata, TemperatureProduct
from base.raster import write_temperature_product
from msg.msg_data import MsgDataProduct, add_lst_auxiliary, read_data_product


# ============================================================================
# 算法默认值；执行参数由 cases 提供
# ============================================================================

MSG_DATA_ROOT = None
MSG_LST_ROOT = None
DAY_TEMPLATE = "{year:04d}/{month:02d}/{day:02d}"
YEARS = None
MONTHS = range(1, 13)
DAYS = range(1, 32)
COEFFICIENT_FILE = None
AUXILIARY_FILE = None
GRID_ID = "MSG-NATIVE"
ALGORITHM_VERSION = "msg-split-window-v1"
UNCERTAINTY_K = 1.0
OVERWRITE = False


def retrieve_msg_lst(item: MsgDataProduct, coefficient_file=None):
    if coefficient_file is None:
        coefficient_file = COEFFICIENT_FILE
    require_parameters(coefficient_file=coefficient_file)
    item.validate(require_lst_auxiliary=True)
    observation = DualChannelObservation(
        item.bt8,
        item.bt9,
        item.soil_emissivity_108,
        item.soil_emissivity_120,
        item.vegetation_emissivity_108,
        item.vegetation_emissivity_120,
        item.lai,
        item.tcwv_cm,
        item.view_zenith_deg,
        item.cloud_mask,
    )
    return retrieve_dual_channel_lst(observation, load_split_window_model(coefficient_file))


def produce_msg_lst(
    input_path,
    output_path,
    coefficient_file=None,
    auxiliary_file=None,
    grid_id=None,
    algorithm_version=None,
    uncertainty_k=None,
) -> None:
    if coefficient_file is None:
        coefficient_file = COEFFICIENT_FILE
    if auxiliary_file is None:
        auxiliary_file = AUXILIARY_FILE
    if grid_id is None:
        grid_id = GRID_ID
    if algorithm_version is None:
        algorithm_version = ALGORITHM_VERSION
    if uncertainty_k is None:
        uncertainty_k = UNCERTAINTY_K
    require_parameters(coefficient_file=coefficient_file, auxiliary_file=auxiliary_file)
    item = read_data_product(input_path)
    auxiliary_source = None
    if not item.has_lst_auxiliary:
        item = add_lst_auxiliary(item, auxiliary_file)
        auxiliary_source = str(auxiliary_file)
    result = retrieve_msg_lst(item, coefficient_file)
    sources = [item.source_product, str(input_path), str(coefficient_file)]
    if auxiliary_source:
        sources.append(auxiliary_source)
    metadata = ProductMetadata(
        ProductLevel.L2LST,
        "MSG",
        item.start_time,
        item.end_time,
        grid_id,
        algorithm_version,
        source_products=tuple(sources),
        attributes={"temperature_variable_names": ["lst"], "unit": "K"},
    )
    product = TemperatureProduct(
        metadata,
        {
            "lst": result.temperature_k,
            "latitude_deg": item.latitude_deg,
            "longitude_deg": item.longitude_deg,
        },
        result.quality_flag,
        {"lst": np.full(item.shape, float(uncertainty_k))},
    )
    write_temperature_product(output_path, product, reference_path=input_path)


def msg_lst(
    indir_data=None,
    outdir_lst=None,
    coefficient_file=None,
    auxiliary_file=None,
    years=None,
    months=None,
    days=None,
    overwrite=None,
) -> None:
    if indir_data is None:
        indir_data = MSG_DATA_ROOT
    if outdir_lst is None:
        outdir_lst = MSG_LST_ROOT
    if coefficient_file is None:
        coefficient_file = COEFFICIENT_FILE
    if auxiliary_file is None:
        auxiliary_file = AUXILIARY_FILE
    if years is None:
        years = YEARS
    if months is None:
        months = MONTHS
    if days is None:
        days = DAYS
    if overwrite is None:
        overwrite = OVERWRITE
    require_parameters(
        indir_data=indir_data,
        outdir_lst=outdir_lst,
        coefficient_file=coefficient_file,
        auxiliary_file=auxiliary_file,
        years=years,
    )
    for year in years:
        for month in months:
            for day in days:
                input_day = Path(indir_data) / DAY_TEMPLATE.format(year=year, month=month, day=day)
                if not input_day.is_dir():
                    continue
                output_day = Path(outdir_lst) / DAY_TEMPLATE.format(year=year, month=month, day=day)
                inputs = sorted(input_day.rglob("*.tif"))
                for input_path in inputs:
                    relative = input_path.relative_to(input_day)
                    output_path = (output_day / relative).with_name(relative.stem + "_lst.tif")
                    if output_path.exists() and not overwrite:
                        continue
                    produce_msg_lst(
                        input_path,
                        output_path,
                        coefficient_file,
                        auxiliary_file,
                    )
