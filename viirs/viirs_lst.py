"""VIIRS generalized split-window LST retrieval."""

from base.dual_thermal import produce_sensor_lst, retrieve_sensor_lst, retrieve_sensor_years
from viirs.viirs_data import SPEC, ViirsDataProduct


def retrieve_viirs_lst(item, coefficient_file=None):
    return retrieve_sensor_lst(item, SPEC, coefficient_file)


def produce_viirs_lst(
    input_path=None,
    output_path=None,
    coefficient_file=None,
    auxiliary_file=None,
    grid_id=None,
    algorithm_version=None,
    uncertainty_k=None,
) -> None:
    produce_sensor_lst(
        input_path, output_path, SPEC, ViirsDataProduct, coefficient_file, auxiliary_file,
        grid_id, algorithm_version, uncertainty_k,
    )


def viirs_lst(
    indir_data=None,
    outdir_lst=None,
    coefficient_file=None,
    auxiliary_file=None,
    years=None,
    months=None,
    days=None,
    grid_id=None,
    algorithm_version=None,
    uncertainty_k=None,
    overwrite=None,
) -> None:
    retrieve_sensor_years(
        SPEC, ViirsDataProduct, indir_data=indir_data, outdir_lst=outdir_lst,
        coefficient_file=coefficient_file, auxiliary_file=auxiliary_file, years=years,
        months=months, days=days, grid_id=grid_id, algorithm_version=algorithm_version,
        uncertainty_k=uncertainty_k, overwrite=overwrite,
    )
