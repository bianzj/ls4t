"""Small file helpers shared by manually run batch functions."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

import numpy as np


def read_npz_payload(path: str | Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as source:
        return {name: source[name].copy() for name in source.files}


def write_npz_atomic(path: str | Path, payload: dict[str, np.ndarray]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".npz", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        np.savez_compressed(temporary_path, **payload)
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)
