"""VIIRS same-acquisition scene mosaic stage."""

from base.dual_thermal import merge_sensor_data
from viirs.viirs_data import SPEC, ViirsDataProduct


def viirs_merge(input_paths=None, output_path=None, bounds=None) -> None:
    merge_sensor_data(input_paths, output_path, SPEC, ViirsDataProduct, bounds)
