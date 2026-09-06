"""SLSTR study-area operations for region-first and scene-first processing.

Inputs must already be projected to the same target grid.  Do not mix nadir
and oblique views or unrelated overpasses in one input group.
"""

from pathlib import Path

from base.product_io import read_product, write_product
from base.spatial import (
    crop_observation,
    crop_temperature_product,
    mosaic_observations,
    mosaic_temperature_products,
)
from slstr.slstr_data import read_data_product, write_data_product


DATA_INPUT = Path("/home/hero/data/ls4t/slstr/project/one_group")
DATA_OUTPUT = Path("/home/hero/data/ls4t/slstr/region/data.npz")
RESULT_INPUT = Path("/home/hero/data/ls4t/slstr/scene_result/one_group")
RESULT_OUTPUT = Path("/home/hero/data/ls4t/slstr/region/result.npz")
STUDY_BOUNDS = None  # (west, south, east, north)
INPUT_PATTERN = "*.npz"


def _resolve_inputs(value):
    if isinstance(value, (str, Path)):
        path = Path(value)
        paths = sorted(path.rglob(INPUT_PATTERN)) if path.is_dir() else [path]
    else:
        paths = [Path(path) for path in value]
    paths = [path for path in paths if path.is_file()]
    if not paths:
        raise FileNotFoundError("SLSTR region stage has no input NPZ files")
    return paths


def slstr_data_region(
    input_paths=None,
    output_path=None,
    bounds=None,
) -> None:
    """Mode 1: form one study-area data product before retrieval."""

    if input_paths is None:
        input_paths = DATA_INPUT
    if output_path is None:
        output_path = DATA_OUTPUT
    if bounds is None:
        bounds = STUDY_BOUNDS
    paths = _resolve_inputs(input_paths)
    item = mosaic_observations(
        [read_data_product(path) for path in paths], primary_field="bt8_k"
    )
    if bounds is not None:
        item = crop_observation(item, bounds)
    write_data_product(output_path, item)


def slstr_result_region(
    input_paths=None,
    output_path=None,
    bounds=None,
) -> None:
    """Mode 2: form one study-area result after scene-by-scene retrieval."""

    if input_paths is None:
        input_paths = RESULT_INPUT
    if output_path is None:
        output_path = RESULT_OUTPUT
    if bounds is None:
        bounds = STUDY_BOUNDS
    paths = _resolve_inputs(input_paths)
    product = mosaic_temperature_products([read_product(path) for path in paths])
    if bounds is not None:
        product = crop_temperature_product(product, bounds)
    write_product(output_path, product)


if __name__ == "__main__":
    # 每次只保留所选处理方式；逐景反演后处理时改为 slstr_result_region()。
    slstr_data_region()
