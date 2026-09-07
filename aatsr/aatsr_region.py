"""AATSR study-area operations for the two supported processing modes.

Mode 1 uses :func:`aatsr_data_region` after scene projection and before LST or
LSCT retrieval.  Mode 2 uses :func:`aatsr_result_region` after every scene has
already been retrieved.  Each input group must contain only neighbouring
scenes from one acquisition and one AATSR view.
"""

from pathlib import Path

from aatsr.aatsr_data import read_data_product, write_data_product
from base.product_io import read_product, write_product
from base.spatial import (
    crop_observation,
    crop_temperature_product,
    mosaic_observations,
    mosaic_temperature_products,
)


DATA_INPUT = Path("/home/hero/data/ls4t/aatsr/project/one_group")
DATA_OUTPUT = Path("/home/hero/data/ls4t/aatsr/region/data.npz")
RESULT_INPUT = Path("/home/hero/data/ls4t/aatsr/scene_result/one_group")
RESULT_OUTPUT = Path("/home/hero/data/ls4t/aatsr/region/result.npz")
STUDY_BOUNDS = None  # (west, south, east, north), e.g. (97.0, 37.0, 102.0, 43.0)
INPUT_PATTERN = "*.npz"


def _resolve_inputs(value):
    if isinstance(value, (str, Path)):
        path = Path(value)
        paths = sorted(path.rglob(INPUT_PATTERN)) if path.is_dir() else [path]
    else:
        paths = [Path(path) for path in value]
    paths = [path for path in paths if path.is_file()]
    if not paths:
        raise FileNotFoundError("AATSR region stage has no input NPZ files")
    return paths


def aatsr_data_region(
    input_paths=None,
    output_path=None,
    bounds=None,
) -> None:
    """Mode 1: mosaic/crop projected data before retrieval."""

    if input_paths is None:
        input_paths = DATA_INPUT
    if output_path is None:
        output_path = DATA_OUTPUT
    if bounds is None:
        bounds = STUDY_BOUNDS
    paths = _resolve_inputs(input_paths)
    item = mosaic_observations(
        [read_data_product(path) for path in paths], primary_field="bt11_k"
    )
    if bounds is not None:
        item = crop_observation(item, bounds)
    write_data_product(output_path, item)


def aatsr_result_region(
    input_paths=None,
    output_path=None,
    bounds=None,
) -> None:
    """Mode 2: mosaic/crop LST or LSCT products retrieved scene by scene."""

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
    # 每次只保留所选处理方式；逐景反演后处理时改为 aatsr_result_region()。
    aatsr_data_region()
