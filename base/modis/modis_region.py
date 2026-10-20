"""MODIS study-area operations before or after retrieval."""

from base.dual_thermal import merge_sensor_data, merge_sensor_results
from base.modis.modis_data import ModisDataProduct, SPEC


def modis_data_region(input_paths=None, output_path=None, bounds=None) -> None:
    merge_sensor_data(input_paths, output_path, SPEC, ModisDataProduct, bounds)


def modis_result_region(input_paths=None, output_path=None, bounds=None) -> None:
    merge_sensor_results(input_paths, output_path, SPEC, bounds)
