import inspect
from pathlib import Path

import numpy as np

from aatsr.aatsr_data import aatsr_extract, aatsr_unzip
from aatsr.aatsr_project import aatsr_project
from aatsr.aatsr_region import aatsr_data_region, aatsr_result_region
from applications import tvdi_years
from composite import composite_years
from msg.msg_data import msg_extract
from msg.msg_project import msg_project
from msg.msg_region import msg_data_region, msg_result_region
from normalization.angle import angle_normalize_years
from normalization.fusion import fusion_years
from normalization.sensor import sensor_normalize_years
from normalization.space import space_normalize_years
from normalization.time import time_normalize_years
from slstr.slstr_data import (
    SlstrExtractedProduct,
    reconstruct_product,
)
from slstr.slstr_extract import slstr_extract
from slstr.slstr_merge import slstr_merge
from slstr.slstr_project import slstr_project
from slstr.slstr_reconstruct import slstr_reconstruct
from slstr.slstr_region import slstr_data_region, slstr_result_region
from slstr.slstr_unzip import slstr_unzip


def test_runtime_tree_is_flat():
    source = Path(__file__).resolve().parents[1]
    assert not (source / "src").exists()
    for name in ("base", "aatsr", "slstr", "msg", "normalization"):
        assert (source / name).is_dir()
    assert (source / "cases").is_dir()


def test_manual_batch_parameters_default_to_none():
    functions = (
        aatsr_unzip,
        aatsr_extract,
        aatsr_project,
        aatsr_data_region,
        aatsr_result_region,
        slstr_unzip,
        slstr_extract,
        slstr_reconstruct,
        slstr_project,
        slstr_merge,
        slstr_data_region,
        slstr_result_region,
        msg_extract,
        msg_project,
        msg_data_region,
        msg_result_region,
        angle_normalize_years,
        time_normalize_years,
        space_normalize_years,
        sensor_normalize_years,
        fusion_years,
        composite_years,
        tvdi_years,
    )
    for function in functions:
        for parameter in inspect.signature(function).parameters.values():
            assert parameter.default is None, f"{function.__name__}.{parameter.name}"


def test_slstr_extraction_and_reconstruction_are_separate():
    extracted = SlstrExtractedProduct(
        source_product="sample.SEN3",
        view="nadir",
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-01T00:03:00Z",
        bt8_k=np.full((4, 4), 300.0),
        bt9_k=np.full((4, 4), 298.0),
        view_zenith_tie_deg=np.array([[0.0, 10.0], [20.0, 30.0]]),
        latitude_native_deg=np.array([[40.0, 41.0], [42.0, 43.0]]),
        longitude_native_deg=np.array([[100.0, 101.0], [102.0, 103.0]]),
        cloud_native=np.array([[0, 1], [0, 0]]),
    )
    reconstructed = reconstruct_product(extracted)
    assert reconstructed.shape == (4, 4)
    assert reconstructed.view_zenith_deg.shape == reconstructed.shape
    assert reconstructed.cloud_mask.dtype == np.bool_
