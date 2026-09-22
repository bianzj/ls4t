"""SLSTR-LST product: retrieve and store SLSTR land-surface temperature."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..calibration import legacy_split_window_model, load_split_window_model, save_split_window_model
from ..io import write_product
from ..products import lst_product
from ..retrieval.lst import SplitWindowResult
from ..sensors import DualChannelObservation, retrieve_dual_channel_lst
from .slstr_data import SlstrDataProduct, read_data_product


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


def retrieve_slstr_lst(item: SlstrDataProduct, coefficient_file: str | Path) -> SplitWindowResult:
    """Run the SLSTR split-window algorithm on a complete SLSTR-DATA product."""

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
    coefficient_file: str | Path,
    output_path: str | Path,
    *,
    grid_id: str,
    algorithm_version: str,
    uncertainty_k: float,
    start_time: str | None = None,
    end_time: str | None = None,
) -> None:
    """Produce one validated LS4T SLSTR L2LST product."""

    item = read_data_product(input_path)
    actual_start = start_time or item.start_time
    actual_end = end_time or item.end_time
    if not actual_start or not actual_end:
        raise ValueError("start_time and end_time are required when absent from SLSTR-DATA metadata")
    if uncertainty_k <= 0:
        raise ValueError("uncertainty_k must be positive")
    result = retrieve_slstr_lst(item, coefficient_file)
    product = lst_product(
        result,
        uncertainty_k=np.full(item.shape, uncertainty_k, dtype=float),
        sensor="SLSTR",
        start_time=actual_start,
        end_time=actual_end,
        grid_id=grid_id,
        algorithm_version=algorithm_version,
        source_products=(item.source_product, str(input_path), str(coefficient_file)),
    )
    write_product(output_path, product)
