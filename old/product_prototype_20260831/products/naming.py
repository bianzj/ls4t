from __future__ import annotations

from datetime import datetime
import re

from .model import ProductMetadata


def _stamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.strftime("%Y%m%dT%H%M%S")


def product_filename(metadata: ProductMetadata, extension: str = "npz") -> str:
    def slug(value: str) -> str:
        return re.sub(r"[^A-Z0-9.-]+", "-", value.upper()).strip("-")

    sensor = slug(metadata.sensor)
    grid = slug(metadata.grid_id)
    version = slug(metadata.algorithm_version)
    return (
        f"LS4T_{sensor}_{metadata.level.value}_{_stamp(metadata.start_time)}_"
        f"{_stamp(metadata.end_time)}_{grid}_{version}.{extension.lstrip('.')}"
    )
