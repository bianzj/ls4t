"""MODIS same-acquisition scene mosaic stage."""

from base.dual_thermal import merge_sensor_data
from base.modis.modis_data import ModisDataProduct, SPEC


def modis_merge(input_paths=None, output_path=None, bounds=None) -> None:
    """Merge one explicit group; cases decide which scenes belong together."""

    merge_sensor_data(input_paths, output_path, SPEC, ModisDataProduct, bounds)
