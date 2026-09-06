import numpy as np

from aatsr.aatsr_data import AatsrDataProduct
from base.product import ProductLevel, ProductMetadata, TemperatureProduct
from base.quality import QualityFlag
from base.spatial import (
    crop_observation,
    crop_temperature_product,
    mosaic_observations,
    mosaic_temperature_products,
)


def _aatsr(value, angle, cloud):
    latitude = np.array([[40.0, 40.0, 40.0], [41.0, 41.0, 41.0]])
    longitude = np.array([[100.0, 101.0, 102.0], [100.0, 101.0, 102.0]])
    shape = latitude.shape
    return AatsrDataProduct(
        source_product=f"scene-{value}",
        view="nadir",
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-01T00:03:00Z",
        bt11_k=np.full(shape, value),
        bt12_k=np.full(shape, value - 2.0),
        view_zenith_deg=np.full(shape, angle),
        latitude_deg=latitude,
        longitude_deg=longitude,
        cloud_mask=np.asarray(cloud, dtype=bool),
    )


def _result(value, uncertainty, cloud_at=None):
    latitude = np.array([[40.0, 40.0, 40.0], [41.0, 41.0, 41.0]])
    longitude = np.array([[100.0, 101.0, 102.0], [100.0, 101.0, 102.0]])
    shape = latitude.shape
    quality = np.zeros(shape, dtype=np.uint16)
    if cloud_at is not None:
        quality[cloud_at] |= np.uint16(QualityFlag.CLOUD)
    metadata = ProductMetadata(
        ProductLevel.L2LST,
        "AATSR",
        "2026-01-01T00:00:00Z",
        "2026-01-01T00:03:00Z",
        "TEST-GRID",
        "test-v1",
        source_products=(f"scene-{value}",),
        attributes={"temperature_variable_names": ["lst"], "unit": "K"},
    )
    return TemperatureProduct(
        metadata,
        {"lst": np.full(shape, value), "latitude_deg": latitude, "longitude_deg": longitude},
        quality,
        {"lst": np.full(shape, uncertainty)},
    )


def test_region_first_prefers_clear_low_angle_scene_and_crops():
    first = _aatsr(300.0, 30.0, np.zeros((2, 3), dtype=bool))
    second_cloud = np.zeros((2, 3), dtype=bool)
    second_cloud[0, 0] = True
    second = _aatsr(310.0, 10.0, second_cloud)
    mosaic = mosaic_observations([first, second], primary_field="bt11_k")
    assert mosaic.bt11_k[0, 0] == 300.0
    assert mosaic.bt11_k[1, 2] == 310.0

    cropped = crop_observation(mosaic, (100.5, 39.5, 102.5, 41.5))
    assert cropped.shape == (2, 2)
    np.testing.assert_array_equal(cropped.longitude_deg[0], [101.0, 102.0])


def test_scene_first_prefers_lower_uncertainty_then_crops():
    first = _result(300.0, 2.0)
    second = _result(310.0, 1.0, cloud_at=(0, 0))
    mosaic = mosaic_temperature_products([first, second])
    assert mosaic.variables["lst"][0, 0] == 300.0
    assert mosaic.variables["lst"][1, 2] == 310.0
    assert mosaic.metadata.attributes["spatial_operation"] == "mosaic"

    cropped = crop_temperature_product(mosaic, (99.5, 39.5, 101.5, 41.5))
    assert cropped.variables["lst"].shape == (2, 2)
    assert cropped.metadata.attributes["spatial_operation"] == "crop"
