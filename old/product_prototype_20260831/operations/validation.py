from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..products.model import TemperatureProduct
from ..quality import usable


@dataclass(frozen=True)
class ValidationReport:
    valid_pixels: int
    total_pixels: int
    valid_fraction: float
    variable_ranges: dict[str, tuple[float, float] | None]


def validate_product(product: TemperatureProduct) -> ValidationReport:
    product.validate()
    valid = usable(product.quality_flag)
    ranges: dict[str, tuple[float, float] | None] = {}
    for name, value in product.variables.items():
        finite = np.asarray(value)[np.isfinite(value) & valid]
        ranges[name] = None if finite.size == 0 else (float(finite.min()), float(finite.max()))
    count = int(valid.sum())
    total = int(valid.size)
    return ValidationReport(count, total, count / total if total else 0.0, ranges)
