"""AHI study-area operations before or after retrieval."""

from base.ahi.ahi_data import AhiDataProduct, SPEC
from base.dual_thermal import merge_sensor_data, merge_sensor_results


def ahi_data_region(input_paths=None, output_path=None, bounds=None) -> None:
    merge_sensor_data(input_paths, output_path, SPEC, AhiDataProduct, bounds)


def ahi_result_region(input_paths=None, output_path=None, bounds=None) -> None:
    merge_sensor_results(input_paths, output_path, SPEC, bounds)
