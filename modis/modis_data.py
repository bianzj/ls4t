"""MODIS LS4T-DATA model for thermal bands 31 and 32."""

from dataclasses import dataclass
from typing import ClassVar

from base.dual_thermal import (
    DualThermalDataProduct,
    DualThermalSensorSpec,
    add_lst_auxiliary as _add_lst_auxiliary,
    read_data_product as _read_data_product,
    read_prepared_product,
    write_data_product as _write_data_product,
)


SPEC = DualThermalSensorSpec(
    name="MODIS",
    channels=("31", "32"),
    prepared_keys=(("bt31_k",), ("bt32_k",)),
    native_grid_id="MODIS-NATIVE-1KM",
    algorithm_version="modis-split-window-v1",
)


@dataclass(frozen=True)
class ModisDataProduct(DualThermalDataProduct):
    sensor: ClassVar[str] = "MODIS"


def read_native_product(path):
    return read_prepared_product(path, SPEC, ModisDataProduct)


def write_data_product(path, item) -> None:
    _write_data_product(path, item, SPEC)


def read_data_product(path):
    return _read_data_product(path, SPEC, ModisDataProduct)


def add_lst_auxiliary(item, auxiliary_file):
    return _add_lst_auxiliary(item, auxiliary_file)
