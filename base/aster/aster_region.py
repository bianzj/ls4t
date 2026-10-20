"""ASTER study-area operations before or after retrieval."""

from base.aster.aster_data import AsterDataProduct, SPEC
from base.dual_thermal import merge_sensor_data, merge_sensor_results


def aster_data_region(input_paths=None, output_path=None, bounds=None) -> None:
    merge_sensor_data(input_paths, output_path, SPEC, AsterDataProduct, bounds)


def aster_result_region(input_paths=None, output_path=None, bounds=None) -> None:
    merge_sensor_results(input_paths, output_path, SPEC, bounds)
