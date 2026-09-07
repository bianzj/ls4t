import json

import numpy as np
import pytest

from base.calibration import save_split_window_model
from base.lst import SplitWindowModel
from ahi.ahi_data import (
    AhiDataProduct,
    read_data_product as read_ahi_data,
    read_native_product as read_ahi_native,
    write_data_product as write_ahi_data,
)
from aster.aster_data import (
    AsterDataProduct,
    read_data_product as read_aster_data,
    read_native_product as read_aster_native,
    write_data_product as write_aster_data,
)
from modis.modis_data import (
    ModisDataProduct,
    read_data_product as read_modis_data,
    read_native_product as read_modis_native,
    write_data_product as write_modis_data,
)
from modis.modis_extract import modis_extract
from modis.modis_lst import retrieve_modis_lst
from modis.modis_merge import modis_merge
from viirs.viirs_data import (
    ViirsDataProduct,
    read_data_product as read_viirs_data,
    read_native_product as read_viirs_native,
    write_data_product as write_viirs_data,
)


SENSORS = (
    ("MODIS", "bt31_k", "bt32_k", ModisDataProduct, read_modis_native, write_modis_data, read_modis_data),
    ("VIIRS", "bt_m15_k", "bt_m16_k", ViirsDataProduct, read_viirs_native, write_viirs_data, read_viirs_data),
    ("AHI", "bt14_k", "bt15_k", AhiDataProduct, read_ahi_native, write_ahi_data, read_ahi_data),
    ("ASTER", "bt13_k", "bt14_k", AsterDataProduct, read_aster_native, write_aster_data, read_aster_data),
)


@pytest.mark.parametrize("sensor,key1,key2,product_type,read_native,write_data,read_data", SENSORS)
def test_prepared_arrays_become_sensor_data_products(
    tmp_path, sensor, key1, key2, product_type, read_native, write_data, read_data
):
    shape = (2, 3)
    prepared = tmp_path / f"{sensor.lower()}_prepared.npz"
    np.savez_compressed(
        prepared,
        metadata=np.asarray(
            json.dumps(
                {
                    "sensor": sensor,
                    "source_product": f"{sensor}-source",
                    "start_time": "2026-01-02T03:04:05Z",
                    "end_time": "2026-01-02T03:09:05Z",
                }
            )
        ),
        **{
            key1: np.full(shape, 300.0),
            key2: np.full(shape, 298.0),
            "view_zenith_deg": np.full(shape, 10.0),
            "latitude_deg": np.broadcast_to(np.arange(2)[:, None], shape),
            "longitude_deg": np.broadcast_to(np.arange(3)[None, :], shape),
            "cloud_mask": np.zeros(shape, dtype=bool),
        },
    )

    item = read_native(prepared)
    assert isinstance(item, product_type)
    assert item.sensor == sensor
    assert item.shape == shape

    output = tmp_path / f"{sensor.lower()}_data.npz"
    write_data(output, item)
    restored = read_data(output)
    assert isinstance(restored, product_type)
    assert restored.source_product == f"{sensor}-source"
    np.testing.assert_allclose(restored.bt1_k, 300.0)
    np.testing.assert_allclose(restored.bt2_k, 298.0)


def test_prepared_product_rejects_wrong_sensor(tmp_path):
    path = tmp_path / "wrong.npz"
    shape = (1, 1)
    np.savez_compressed(
        path,
        metadata=np.asarray(
            json.dumps(
                {
                    "sensor": "VIIRS",
                    "start_time": "2026-01-01T00:00:00Z",
                    "end_time": "2026-01-01T00:01:00Z",
                }
            )
        ),
        bt31_k=np.full(shape, 300.0),
        bt32_k=np.full(shape, 299.0),
        view_zenith_deg=np.zeros(shape),
        latitude_deg=np.zeros(shape),
        longitude_deg=np.zeros(shape),
    )
    with pytest.raises(ValueError, match="does not match"):
        read_modis_native(path)


def _modis_item(value, view_angle, cloud=False):
    shape = (2, 2)
    return ModisDataProduct(
        source_product=f"source-{value}",
        start_time="2026-01-02T03:04:05Z",
        end_time="2026-01-02T03:09:05Z",
        bt1_k=np.full(shape, value),
        bt2_k=np.full(shape, value - 2.0),
        view_zenith_deg=np.full(shape, view_angle),
        latitude_deg=np.broadcast_to(np.arange(2)[:, None], shape).copy(),
        longitude_deg=np.broadcast_to(np.arange(2)[None, :], shape).copy(),
        cloud_mask=np.full(shape, cloud, dtype=bool),
    )


def test_modis_batch_extracts_a_dated_prepared_product(tmp_path):
    input_day = tmp_path / "raw/2026/01/02"
    input_day.mkdir(parents=True)
    prepared = input_day / "scene.npz"
    item = _modis_item(300.0, 10.0)
    np.savez_compressed(
        prepared,
        metadata=np.asarray(
            json.dumps(
                {
                    "sensor": "MODIS",
                    "source_product": item.source_product,
                    "start_time": item.start_time,
                    "end_time": item.end_time,
                }
            )
        ),
        bt31_k=item.bt1_k,
        bt32_k=item.bt2_k,
        view_zenith_deg=item.view_zenith_deg,
        latitude_deg=item.latitude_deg,
        longitude_deg=item.longitude_deg,
        cloud_mask=item.cloud_mask,
    )
    modis_extract(
        indir_raw=tmp_path / "raw",
        outdir_data=tmp_path / "data",
        years=[2026],
        months=[1],
        days=[2],
    )
    result = read_modis_data(tmp_path / "data/2026/01/02/scene.npz")
    np.testing.assert_allclose(result.bt1_k, 300.0)


def test_modis_merge_prefers_clear_lower_view_angle(tmp_path):
    high_angle = tmp_path / "high.npz"
    low_angle = tmp_path / "low.npz"
    output = tmp_path / "merged.npz"
    write_modis_data(high_angle, _modis_item(300.0, 40.0))
    write_modis_data(low_angle, _modis_item(305.0, 5.0))
    modis_merge([high_angle, low_angle], output)
    merged = read_modis_data(output)
    np.testing.assert_allclose(merged.bt1_k, 305.0)
    assert merged.source_product == "source-300.0;source-305.0"


def test_modis_standard_lst_retrieval_uses_versioned_coefficients(tmp_path):
    item = _modis_item(300.0, 10.0)
    shape = item.shape
    item = ModisDataProduct(
        **{
            **item.__dict__,
            "soil_emissivity_1": np.full(shape, 0.96),
            "soil_emissivity_2": np.full(shape, 0.97),
            "vegetation_emissivity_1": np.full(shape, 0.98),
            "vegetation_emissivity_2": np.full(shape, 0.98),
            "lai": np.full(shape, 1.0),
            "tcwv_cm": np.full(shape, 2.0),
        }
    )
    coefficients = np.zeros((2, 1, 8), dtype=float)
    coefficients[:, :, 1] = 1.0
    model = SplitWindowModel(
        np.asarray([0.0, 60.0]),
        np.asarray([0.0, 100.0]),
        coefficients,
    )
    coefficient_file = tmp_path / "modis-coefficients.npz"
    save_split_window_model(
        coefficient_file, model, sensor="MODIS", version="test-v1"
    )
    result = retrieve_modis_lst(item, coefficient_file)
    np.testing.assert_allclose(result.temperature_k, 299.0)
