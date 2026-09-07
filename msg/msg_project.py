"""Project decoded MSG images to one analysis grid when required."""

from pathlib import Path

from base.spatial import project_observation
from base.parameters import require_parameters
from msg.msg_data import read_data_product, write_data_product


MSG_DATA_ROOT = None
MSG_PROJECT_ROOT = None
TARGET_GRID_FILE = None
DAY_TEMPLATE = "{year:04d}/{month:02d}/{day:02d}"
YEARS = None
MONTHS = range(1, 13)
DAYS = range(1, 32)
PROJECTION_CHUNK_SIZE = 100_000
CLOUD_FRACTION_THRESHOLD = 0.0
OVERWRITE = False


def project_msg_product(
    item,
    target_grid_file=None,
    projection_chunk_size=None,
    cloud_fraction_threshold=None,
):
    if target_grid_file is None:
        target_grid_file = TARGET_GRID_FILE
    if projection_chunk_size is None:
        projection_chunk_size = PROJECTION_CHUNK_SIZE
    if cloud_fraction_threshold is None:
        cloud_fraction_threshold = CLOUD_FRACTION_THRESHOLD
    require_parameters(target_grid_file=target_grid_file)
    return project_observation(
        item,
        target_grid_file,
        int(projection_chunk_size),
        float(cloud_fraction_threshold),
    )


def msg_project(
    indir_data=None,
    outdir_project=None,
    target_grid_file=None,
    years=None,
    months=None,
    days=None,
    projection_chunk_size=None,
    cloud_fraction_threshold=None,
    overwrite=None,
) -> None:
    if indir_data is None:
        indir_data = MSG_DATA_ROOT
    if outdir_project is None:
        outdir_project = MSG_PROJECT_ROOT
    if target_grid_file is None:
        target_grid_file = TARGET_GRID_FILE
    if years is None:
        years = YEARS
    if months is None:
        months = MONTHS
    if days is None:
        days = DAYS
    if projection_chunk_size is None:
        projection_chunk_size = PROJECTION_CHUNK_SIZE
    if cloud_fraction_threshold is None:
        cloud_fraction_threshold = CLOUD_FRACTION_THRESHOLD
    if overwrite is None:
        overwrite = OVERWRITE

    require_parameters(
        indir_data=indir_data,
        outdir_project=outdir_project,
        target_grid_file=target_grid_file,
        years=years,
    )
    for year in years:
        for month in months:
            for day in days:
                input_day = Path(indir_data) / DAY_TEMPLATE.format(
                    year=year, month=month, day=day
                )
                if not input_day.is_dir():
                    continue
                output_day = Path(outdir_project) / DAY_TEMPLATE.format(
                    year=year, month=month, day=day
                )
                inputs = sorted(input_day.rglob("*.npz"))
                for index, input_path in enumerate(inputs):
                    output_path = output_day / input_path.relative_to(input_day)
                    if output_path.exists() and not overwrite:
                        continue
                    print(
                        f"[{year:04d}-{month:02d}-{day:02d}] "
                        f"{index + 1}/{len(inputs)} 投影 {input_path}"
                    )
                    write_data_product(
                        output_path,
                        project_msg_product(
                            read_data_product(input_path),
                            target_grid_file,
                            projection_chunk_size,
                            cloud_fraction_threshold,
                        ),
                    )
