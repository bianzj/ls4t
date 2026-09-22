from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np

from ..retrieval.components import ComponentRetrievalResult
from ..retrieval.lst import SplitWindowResult
from .levels import ProductLevel
from .model import ProductMetadata, TemperatureProduct


def lst_product(
    result: SplitWindowResult,
    uncertainty_k: np.ndarray,
    *,
    sensor: str,
    start_time: str,
    end_time: str,
    grid_id: str,
    algorithm_version: str,
    source_products: Sequence[str] = (),
) -> TemperatureProduct:
    metadata = ProductMetadata(
        ProductLevel.L2LST,
        sensor,
        start_time,
        end_time,
        grid_id,
        algorithm_version,
        source_products=tuple(source_products),
        attributes={"temperature_variable_names": ["lst"], "unit": "K"},
    )
    return TemperatureProduct(
        metadata,
        {"lst": result.temperature_k},
        result.quality_flag,
        {"lst": np.broadcast_to(np.asarray(uncertainty_k), result.temperature_k.shape)},
    )


def component_temperature_product(
    result: ComponentRetrievalResult,
    component_names: Sequence[str],
    *,
    sensor: str,
    start_time: str,
    end_time: str,
    grid_id: str,
    algorithm_version: str,
    source_products: Sequence[str] = (),
    component_uncertainty_k: Mapping[str, np.ndarray] | None = None,
) -> TemperatureProduct:
    names = tuple(component_names)
    if len(names) != result.temperature_k.shape[-1] or len(set(names)) != len(names):
        raise ValueError("component_names must uniquely label the final temperature axis")
    variables = {name: result.temperature_k[..., index] for index, name in enumerate(names)}
    variables["residual_rms"] = result.residual_rms
    variables["condition_number"] = result.condition_number
    metadata = ProductMetadata(
        ProductLevel.L2LSCT,
        sensor,
        start_time,
        end_time,
        grid_id,
        algorithm_version,
        source_products=tuple(source_products),
        attributes={"temperature_variable_names": list(names), "unit": "K"},
    )
    return TemperatureProduct(
        metadata,
        variables,
        result.quality_flag,
        dict(component_uncertainty_k or {}),
    )
