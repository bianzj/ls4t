from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

import numpy as np

from ..products.model import ProductMetadata, TemperatureProduct

_VARIABLE_PREFIX = "variable__"
_UNCERTAINTY_PREFIX = "uncertainty__"


def write_product(path: str | Path, product: TemperatureProduct) -> None:
    product.validate()
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, np.ndarray] = {
        "metadata": np.asarray(json.dumps(product.metadata.to_dict(), sort_keys=True)),
        "quality_flag": np.asarray(product.quality_flag, dtype=np.uint16),
    }
    payload.update({_VARIABLE_PREFIX + key: np.asarray(value) for key, value in product.variables.items()})
    payload.update(
        {_UNCERTAINTY_PREFIX + key: np.asarray(value) for key, value in product.uncertainty.items()}
    )
    with tempfile.NamedTemporaryFile(
        prefix=f".{destination.name}.", suffix=".npz", dir=destination.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        np.savez_compressed(temporary_path, **payload)
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def read_product(path: str | Path) -> TemperatureProduct:
    with np.load(path, allow_pickle=False) as bundle:
        metadata = ProductMetadata.from_dict(json.loads(str(bundle["metadata"].item())))
        variables = {
            key.removeprefix(_VARIABLE_PREFIX): bundle[key].copy()
            for key in bundle.files
            if key.startswith(_VARIABLE_PREFIX)
        }
        uncertainty = {
            key.removeprefix(_UNCERTAINTY_PREFIX): bundle[key].copy()
            for key in bundle.files
            if key.startswith(_UNCERTAINTY_PREFIX)
        }
        product = TemperatureProduct(metadata, variables, bundle["quality_flag"].copy(), uncertainty)
    product.validate()
    return product

