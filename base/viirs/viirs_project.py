"""VIIRS projection to an explicit target grid."""

from base.dual_thermal import project_sensor_products
from base.parameters import require_parameters
from base.spatial import project_observation
from base.viirs.viirs_data import SPEC, ViirsDataProduct


def project_viirs_product(
    item,
    target_grid_file=None,
    projection_chunk_size=None,
    cloud_fraction_threshold=None,
):
    require_parameters(target_grid_file=target_grid_file)
    return project_observation(
        item,
        target_grid_file,
        100_000 if projection_chunk_size is None else int(projection_chunk_size),
        0.0 if cloud_fraction_threshold is None else float(cloud_fraction_threshold),
    )


def viirs_project(
    indir_extract=None,
    outdir_project=None,
    target_grid_file=None,
    years=None,
    months=None,
    days=None,
    projection_chunk_size=None,
    cloud_fraction_threshold=None,
    overwrite=None,
) -> None:
    project_sensor_products(
        SPEC,
        ViirsDataProduct,
        indir_data=indir_extract,
        outdir_project=outdir_project,
        target_grid_file=target_grid_file,
        years=years,
        months=months,
        days=days,
        projection_chunk_size=projection_chunk_size,
        cloud_fraction_threshold=cloud_fraction_threshold,
        overwrite=overwrite,
    )
