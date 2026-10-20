"""VIIRS study-area operations before or after retrieval."""

from base.dual_thermal import merge_sensor_data, merge_sensor_results
from base.viirs.viirs_data import SPEC, ViirsDataProduct


def viirs_data_region(input_paths=None, output_path=None, bounds=None) -> None:
    merge_sensor_data(input_paths, output_path, SPEC, ViirsDataProduct, bounds)


def viirs_result_region(input_paths=None, output_path=None, bounds=None) -> None:
    merge_sensor_results(input_paths, output_path, SPEC, bounds)
