"""ASTER same-acquisition scene mosaic stage."""

from base.aster.aster_data import AsterDataProduct, SPEC
from base.dual_thermal import merge_sensor_data


def aster_merge(input_paths=None, output_path=None, bounds=None) -> None:
    merge_sensor_data(input_paths, output_path, SPEC, AsterDataProduct, bounds)
