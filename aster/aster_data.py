"""ASTER LS4T-DATA model for the configurable 13/14 split-window route."""

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
    name="ASTER",
    channels=("13", "14"),
    prepared_keys=(("bt13_k",), ("bt14_k",)),
    native_grid_id="ASTER-NATIVE-90M",
    algorithm_version="aster-split-window-v1",
)


@dataclass(frozen=True)
class AsterDataProduct(DualThermalDataProduct):
    sensor: ClassVar[str] = "ASTER"


def read_native_product(path):
    return read_prepared_product(path, SPEC, AsterDataProduct)


def write_data_product(path, item) -> None:
    _write_data_product(path, item, SPEC)


def read_data_product(path):
    return _read_data_product(path, SPEC, AsterDataProduct)


def add_lst_auxiliary(item, auxiliary_file):
    return _add_lst_auxiliary(item, auxiliary_file)
