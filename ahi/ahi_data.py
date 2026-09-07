"""Himawari AHI LS4T-DATA model for bands 14 and 15."""

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
    name="AHI",
    channels=("14", "15"),
    prepared_keys=(("bt14_k",), ("bt15_k",)),
    native_grid_id="AHI-FULL-DISK",
    algorithm_version="ahi-split-window-v1",
)


@dataclass(frozen=True)
class AhiDataProduct(DualThermalDataProduct):
    sensor: ClassVar[str] = "AHI"


def read_native_product(path):
    return read_prepared_product(path, SPEC, AhiDataProduct)


def write_data_product(path, item) -> None:
    _write_data_product(path, item, SPEC)


def read_data_product(path):
    return _read_data_product(path, SPEC, AhiDataProduct)


def add_lst_auxiliary(item, auxiliary_file):
    return _add_lst_auxiliary(item, auxiliary_file)
