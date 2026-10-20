from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pytest

from base.calibration import save_split_window_model
from base.lst import SplitWindowModel
from base.slstr.slstr_data import (
    SlstrDataProduct,
    add_lst_auxiliary,
    read_data_product,
    read_lst_product,
    unpack_archive,
    write_auxiliary_product,
    write_data_product,
)
from base.slstr.slstr_lst import produce_slstr_lst
from base.slstr.slstr_merge import _merge_products


def observation() -> SlstrDataProduct:
    shape = (2, 2)
    return SlstrDataProduct(
        source_product="S3A_SL_1_RBT____20260101T010000_20260101T010300_test.SEN3",
        view="nadir",
        start_time="2026-01-01T01:00:00Z",
        end_time="2026-01-01T01:03:00Z",
        bt8_k=np.full(shape, 300.0),
        bt9_k=np.full(shape, 298.0),
        view_zenith_deg=np.full(shape, 30.0),
        latitude_deg=np.full(shape, 40.0),
        longitude_deg=np.full(shape, 100.0),
        cloud_mask=np.zeros(shape, dtype=bool),
    )


def test_slstr_data_archive_rejects_parent_traversal(tmp_path: Path):
    archive = tmp_path / "unsafe.zip"
    with ZipFile(archive, "w") as bundle:
        bundle.writestr("../outside.txt", "bad")
    with pytest.raises(ValueError, match="unsafe archive member"):
        unpack_archive(archive, tmp_path / "unpacked")


def test_slstr_data_archive_rejects_windows_drive_relative_path(tmp_path: Path):
    archive = tmp_path / "unsafe-drive-relative.zip"
    with ZipFile(archive, "w") as bundle:
        bundle.writestr(r"C:..\outside.txt", "bad")
    with pytest.raises(ValueError, match="unsafe archive member"):
        unpack_archive(archive, tmp_path / "unpacked")


def test_slstr_data_and_lst_are_separate_products(tmp_path: Path):
    pytest.importorskip("osgeo")
    decoded_path = tmp_path / "slstr-decoded.tif"
    complete_path = tmp_path / "slstr-data.tif"
    auxiliary_path = tmp_path / "auxiliary.tif"
    coefficient_path = tmp_path / "slstr-coefficients.npz"
    output_path = tmp_path / "slstr-l2lst.tif"

    write_data_product(decoded_path, observation())
    restored = read_data_product(decoded_path)
    assert not restored.has_lst_auxiliary

    write_auxiliary_product(
        auxiliary_path,
        {
            "soil_emissivity_s8": np.full((2, 2), 0.98),
            "soil_emissivity_s9": np.full((2, 2), 0.97),
            "vegetation_emissivity_s8": np.full((2, 2), 0.99),
            "vegetation_emissivity_s9": np.full((2, 2), 0.98),
            "lai": np.full((2, 2), 1.5),
            "tcwv_cm": np.full((2, 2), 2.0),
        },
    )
    write_data_product(complete_path, add_lst_auxiliary(restored, auxiliary_path))
    assert read_data_product(complete_path).has_lst_auxiliary

    coefficients = np.zeros((2, 1, 8))
    coefficients[..., 1] = 1.0
    model = SplitWindowModel(np.array([0.0, 60.0]), np.array([0.0, 5.0]), coefficients)
    save_split_window_model(coefficient_path, model, sensor="SLSTR", version="test-v1")

    produce_slstr_lst(
        decoded_path,
        output_path,
        coefficient_path,
        auxiliary_path,
        grid_id="SLSTR-NATIVE-1KM",
        algorithm_version="slstr-test-v1",
        uncertainty_k=1.0,
    )
    product = read_lst_product(output_path)
    assert product.metadata.sensor == "SLSTR"
    assert product.metadata.level.value == "L2LST"
    np.testing.assert_allclose(product.variables["lst"], 299.0)


def test_slstr_merge_prefers_clear_lower_angle_scene():
    first = observation()
    second = SlstrDataProduct(
        **{
            **first.__dict__,
            "source_product": "lower-angle",
            "bt8_k": np.full(first.shape, 310.0),
            "bt9_k": np.full(first.shape, 308.0),
            "view_zenith_deg": np.full(first.shape, 5.0),
        }
    )
    merged = _merge_products([first, second])
    np.testing.assert_allclose(merged.bt8_k, 310.0)
    np.testing.assert_allclose(merged.view_zenith_deg, 5.0)
