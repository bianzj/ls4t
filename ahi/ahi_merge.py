"""AHI segment or same-time image mosaic stage."""

from ahi.ahi_data import AhiDataProduct, SPEC
from base.dual_thermal import merge_sensor_data


def ahi_merge(input_paths=None, output_path=None, bounds=None) -> None:
    merge_sensor_data(input_paths, output_path, SPEC, AhiDataProduct, bounds)
