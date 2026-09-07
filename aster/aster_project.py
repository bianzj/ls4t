"""ASTER projection to an explicit target grid."""

from aster.aster_data import AsterDataProduct, SPEC
from base.dual_thermal import project_sensor_products
from base.parameters import require_parameters
from base.spatial import project_observation


def project_aster_product(
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


def aster_project(
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
        AsterDataProduct,
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
