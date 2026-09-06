from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Mapping

import numpy as np


class ProductLevel(str, Enum):
    L1O = "L1O"
    L2LST = "L2LST"
    L2LSCT = "L2LSCT"
    L3N = "L3N"
    L3C = "L3C"
    L4A = "L4A"


@dataclass(frozen=True)
class ProductMetadata:
    level: ProductLevel
    sensor: str
    start_time: str
    end_time: str
    grid_id: str
    algorithm_version: str
    normalization_profile: str | None = None
    source_products: tuple[str, ...] = ()
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.sensor or not self.grid_id or not self.algorithm_version:
            raise ValueError("sensor, grid_id and algorithm_version are required")
        start = datetime.fromisoformat(self.start_time.replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.end_time.replace("Z", "+00:00"))
        if start.utcoffset() is None or end.utcoffset() is None:
            raise ValueError("start_time and end_time must include a UTC offset")
        if start.utcoffset().total_seconds() != 0 or end.utcoffset().total_seconds() != 0:
            raise ValueError("start_time and end_time must be UTC")
        if start > end:
            raise ValueError("start_time must not be after end_time")
        if self.level == ProductLevel.L3N and not self.normalization_profile:
            raise ValueError("L3N products require a normalization_profile")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["level"] = self.level.value
        result["source_products"] = list(self.source_products)
        return result

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ProductMetadata":
        data = dict(value)
        data["level"] = ProductLevel(data["level"])
        data["source_products"] = tuple(data.get("source_products", ()))
        return cls(**data)


@dataclass
class TemperatureProduct:
    metadata: ProductMetadata
    variables: dict[str, np.ndarray]
    quality_flag: np.ndarray
    uncertainty: dict[str, np.ndarray] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.variables:
            raise ValueError("product must contain at least one variable")
        if self.metadata.level in {ProductLevel.L2LST, ProductLevel.L3N, ProductLevel.L3C}:
            if "lst" not in self.variables:
                raise ValueError(f"{self.metadata.level.value} product requires an lst variable")
        if self.metadata.level in {ProductLevel.L2LST, ProductLevel.L3N} and "lst" not in self.uncertainty:
            raise ValueError(f"{self.metadata.level.value} product requires lst uncertainty")
        shape = np.asarray(self.quality_flag).shape
        temperature_names = set(self.metadata.attributes.get("temperature_variable_names", ()))
        for name, values in self.variables.items():
            array = np.asarray(values)
            if array.shape != shape:
                raise ValueError(f"{name} shape {array.shape} does not match quality_flag {shape}")
            if name in temperature_names or name.startswith("temperature") or name in {"lst", "soil", "vegetation"}:
                finite = array[np.isfinite(array)]
                if finite.size and (finite.min() < 150.0 or finite.max() > 400.0):
                    raise ValueError(f"{name} must use kelvin internally")
        for name, values in self.uncertainty.items():
            uncertainty = np.asarray(values)
            if uncertainty.shape != shape:
                raise ValueError(f"uncertainty {name} does not match product shape")
            if np.any(np.isfinite(uncertainty) & (uncertainty <= 0)):
                raise ValueError(f"uncertainty {name} must be positive where finite")


def product_filename(metadata: ProductMetadata, extension: str = "npz") -> str:
    """Create the stable LS4T product name without owning directory layout."""

    def stamp(value: str) -> str:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%Y%m%dT%H%M%S")

    def slug(value: str) -> str:
        return re.sub(r"[^A-Z0-9.-]+", "-", value.upper()).strip("-")

    return (
        f"LS4T_{slug(metadata.sensor)}_{metadata.level.value}_{stamp(metadata.start_time)}_"
        f"{stamp(metadata.end_time)}_{slug(metadata.grid_id)}_"
        f"{slug(metadata.algorithm_version)}.{extension.lstrip('.')}"
    )
