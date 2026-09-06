from pathlib import Path

import numpy as np

from base.product import ProductLevel, ProductMetadata, TemperatureProduct, product_filename
from base.product_io import read_product, write_product


def test_l3n_product_round_trip(tmp_path: Path):
    metadata = ProductMetadata(
        ProductLevel.L3N,
        "AATSR",
        "2026-01-01T00:00:00Z",
        "2026-01-01T23:59:59Z",
        "G001",
        "normalization-v1",
        normalization_profile="OPS-1",
        attributes={"temperature_variable_names": ["lst"]},
    )
    product = TemperatureProduct(
        metadata,
        {"lst": np.array([[300.0]])},
        np.zeros((1, 1), dtype=np.uint16),
        {"lst": np.ones((1, 1))},
    )
    path = tmp_path / "product.npz"
    write_product(path, product)
    restored = read_product(path)
    np.testing.assert_array_equal(restored.variables["lst"], product.variables["lst"])
    assert restored.metadata.normalization_profile == "OPS-1"
    assert product_filename(restored.metadata).startswith("LS4T_AATSR_L3N_")


def test_l2lst_requires_uncertainty():
    metadata = ProductMetadata(
        ProductLevel.L2LST,
        "SLSTR",
        "2026-01-01T00:00:00Z",
        "2026-01-01T00:03:00Z",
        "SLSTR-NATIVE",
        "v1",
    )
    product = TemperatureProduct(
        metadata,
        {"lst": np.array([300.0])},
        np.zeros(1, dtype=np.uint16),
    )
    try:
        product.validate()
    except ValueError as error:
        assert "uncertainty" in str(error)
    else:
        raise AssertionError("L2LST without uncertainty must fail validation")
