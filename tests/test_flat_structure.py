import inspect
from pathlib import Path

import numpy as np
import pytest

from aatsr.aatsr_data import aatsr_extract, aatsr_unzip
from aatsr.aatsr_project import aatsr_project
from aatsr.aatsr_region import aatsr_data_region, aatsr_result_region
from ahi.ahi_extract import ahi_extract
from ahi.ahi_merge import ahi_merge
from ahi.ahi_project import ahi_project
from ahi.ahi_region import ahi_data_region, ahi_result_region
from aster.aster_extract import aster_extract
from aster.aster_merge import aster_merge
from aster.aster_project import aster_project
from aster.aster_region import aster_data_region, aster_result_region
from applications import tvdi_years
from composite import composite_years
from msg.msg_data import msg_extract
from msg.msg_project import msg_project
from msg.msg_region import msg_data_region, msg_result_region
from modis.modis_extract import modis_extract
from modis.modis_merge import modis_merge
from modis.modis_project import modis_project
from modis.modis_region import modis_data_region, modis_result_region
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
from viirs.viirs_extract import viirs_extract
from viirs.viirs_merge import viirs_merge
from viirs.viirs_project import viirs_project
from viirs.viirs_region import viirs_data_region, viirs_result_region


def test_runtime_tree_is_flat():
    source = Path(__file__).resolve().parents[1]
    assert not (source / "src").exists()
    for name in (
        "base",
        "aatsr",
        "slstr",
        "msg",
        "modis",
        "viirs",
        "ahi",
        "aster",
        "normalization",
        "composite",
        "applications",
    ):
        assert (source / name).is_dir()
    assert (source / "cases").is_dir()


def test_core_has_no_machine_paths_or_direct_execution():
    root = Path(__file__).resolve().parents[1]
    core_directories = (
        "base",
        "aatsr",
        "slstr",
        "msg",
        "modis",
        "viirs",
        "ahi",
        "aster",
        "normalization",
        "composite",
        "applications",
    )
    for directory in core_directories:
        for path in (root / directory).rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            assert "/home/" not in source, path
            assert "/media/" not in source, path
            assert 'if __name__ == "__main__"' not in source, path


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
        modis_extract,
        modis_project,
        modis_merge,
        modis_data_region,
        modis_result_region,
        viirs_extract,
        viirs_project,
        viirs_merge,
        viirs_data_region,
        viirs_result_region,
        ahi_extract,
        ahi_project,
        ahi_merge,
        ahi_data_region,
        ahi_result_region,
        aster_extract,
        aster_project,
        aster_merge,
        aster_data_region,
        aster_result_region,
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


@pytest.mark.parametrize(
    "function",
    (
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
        modis_extract,
        modis_project,
        modis_merge,
        modis_data_region,
        modis_result_region,
        viirs_extract,
        viirs_project,
        viirs_merge,
        viirs_data_region,
        viirs_result_region,
        ahi_extract,
        ahi_project,
        ahi_merge,
        ahi_data_region,
        ahi_result_region,
        aster_extract,
        aster_project,
        aster_merge,
        aster_data_region,
        aster_result_region,
        angle_normalize_years,
        time_normalize_years,
        space_normalize_years,
        sensor_normalize_years,
        fusion_years,
        composite_years,
        tvdi_years,
    ),
)
def test_batch_execution_requires_case_parameters(function):
    with pytest.raises(ValueError, match="cases/"):
        function()


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
