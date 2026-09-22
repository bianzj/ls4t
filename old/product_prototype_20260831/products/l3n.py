from __future__ import annotations

from dataclasses import asdict
from typing import Sequence

from ..normalization.fusion import FusionResult
from ..normalization.pipeline import NormalizationResult
from ..normalization.profile import NormalizationProfile
from .levels import ProductLevel
from .model import ProductMetadata, TemperatureProduct


def normalized_product(
    result: NormalizationResult,
    *,
    start_time: str,
    end_time: str,
    algorithm_version: str,
    source_products: Sequence[str] = (),
) -> TemperatureProduct:
    metadata = ProductMetadata(
        level=ProductLevel.L3N,
        sensor=result.sensor,
        start_time=start_time,
        end_time=end_time,
        grid_id=result.profile.grid_id,
        algorithm_version=algorithm_version,
        normalization_profile=result.profile.profile_id,
        source_products=tuple(source_products),
        attributes={"normalization_profile_definition": asdict(result.profile), "fusion": False},
    )
    return TemperatureProduct(
        metadata,
        {"lst": result.temperature_k},
        result.quality_flag,
        {"lst": result.uncertainty_k},
    )


def fused_product(
    result: FusionResult,
    *,
    start_time: str,
    end_time: str,
    algorithm_version: str,
    source_products: Sequence[str] = (),
) -> TemperatureProduct:
    metadata = ProductMetadata(
        level=ProductLevel.L3N,
        sensor="MULTI",
        start_time=start_time,
        end_time=end_time,
        grid_id=result.profile.grid_id,
        algorithm_version=algorithm_version,
        normalization_profile=result.profile.profile_id,
        source_products=tuple(source_products),
        attributes={"normalization_profile_definition": asdict(result.profile), "fusion": True},
    )
    return TemperatureProduct(
        metadata,
        {"lst": result.temperature_k, "contributing_sensors": result.contributing_sensors},
        result.quality_flag,
        {"lst": result.uncertainty_k},
    )


def profile_from_product(product: TemperatureProduct) -> NormalizationProfile:
    definition = product.metadata.attributes.get("normalization_profile_definition")
    if not isinstance(definition, dict):
        raise ValueError("L3N product lacks normalization_profile_definition metadata")
    profile = NormalizationProfile(**definition)
    if profile.profile_id != product.metadata.normalization_profile:
        raise ValueError("normalization profile metadata is inconsistent")
    return profile
