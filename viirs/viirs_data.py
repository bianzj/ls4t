"""VIIRS LS4T-DATA model for M15 and M16."""

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
    name="VIIRS",
    channels=("M15", "M16"),
    prepared_keys=(("bt_m15_k", "bt15_k"), ("bt_m16_k", "bt16_k")),
    native_grid_id="VIIRS-M-NATIVE",
    algorithm_version="viirs-split-window-v1",
)


@dataclass(frozen=True)
class ViirsDataProduct(DualThermalDataProduct):
    sensor: ClassVar[str] = "VIIRS"


def read_native_product(path):
    return read_prepared_product(path, SPEC, ViirsDataProduct)


def write_data_product(path, item) -> None:
    _write_data_product(path, item, SPEC)


def read_data_product(path):
    return _read_data_product(path, SPEC, ViirsDataProduct)


def add_lst_auxiliary(item, auxiliary_file):
    return _add_lst_auxiliary(item, auxiliary_file)
