from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

import numpy as np

from .lst import SplitWindowModel


def legacy_split_window_model(
    coefficient_table: np.ndarray,
    view_zenith_nodes_deg: np.ndarray,
    water_vapour_edges: np.ndarray,
    *,
    coefficient_columns: slice = slice(-8, None),
    valid_temperature_range_k: tuple[float, float] = (220.0, 365.0),
) -> SplitWindowModel:
    """Convert the existing VZA-major AATSR/SLSTR text table into a model."""
    table = np.asarray(coefficient_table, dtype=np.float64)
    coefficients = table[:, coefficient_columns]
    n_vza = np.asarray(view_zenith_nodes_deg).size
    n_water = np.asarray(water_vapour_edges).size - 1
    if coefficients.shape != (n_vza * n_water, 8):
        raise ValueError(
            f"legacy coefficient table must yield {(n_vza * n_water, 8)}, "
            f"got {coefficients.shape}"
        )
    return SplitWindowModel(
        np.asarray(view_zenith_nodes_deg, dtype=np.float64),
        np.asarray(water_vapour_edges, dtype=np.float64),
        coefficients.reshape(n_vza, n_water, 8),
        valid_temperature_range_k,
    )


def save_split_window_model(
    path: str | Path,
    model: SplitWindowModel,
    *,
    sensor: str,
    version: str,
) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema": "ls4t.split-window-coefficients/v1",
        "sensor": sensor.upper(),
        "version": version,
        "valid_temperature_range_k": list(model.valid_temperature_range_k),
    }
    with tempfile.NamedTemporaryFile(
        prefix=f".{destination.name}.", suffix=".npz", dir=destination.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        np.savez_compressed(
            temporary_path,
            metadata=np.asarray(json.dumps(metadata, sort_keys=True)),
            view_zenith_nodes_deg=model.view_zenith_nodes_deg,
            water_vapour_edges=model.water_vapour_edges,
            coefficients=model.coefficients,
        )
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def load_split_window_model(path: str | Path) -> SplitWindowModel:
    """Load versioned production coefficients from a non-pickle NPZ bundle."""
    with np.load(path, allow_pickle=False) as bundle:
        metadata = json.loads(str(bundle["metadata"].item()))
        if metadata.get("schema") != "ls4t.split-window-coefficients/v1":
            raise ValueError("unsupported split-window coefficient schema")
        return SplitWindowModel(
            view_zenith_nodes_deg=bundle["view_zenith_nodes_deg"],
            water_vapour_edges=bundle["water_vapour_edges"],
            coefficients=bundle["coefficients"],
            valid_temperature_range_k=tuple(metadata.get("valid_temperature_range_k", (220, 365))),
        )
