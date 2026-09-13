"""SLSTR map projection stage."""

from pathlib import Path

import numpy as np

from base.parameters import require_parameters
from normalization.space import aggregate_to_grid
from slstr.slstr_data import LST_AUXILIARY_FIELDS, SlstrDataProduct, read_data_product, write_data_product


# Execution paths and years are supplied by cases.
SLSTR_RECONSTRUCT_ROOT = None
SLSTR_PROJECT_ROOT = None
RECONSTRUCT_YEAR_TEMPLATE = "{year}/reconstruct"
PROJECT_YEAR_TEMPLATE = "{year}/project"
YEARS = None
TARGET_GRID_FILE = None
PROJECTION_CHUNK_SIZE = 100_000
CLOUD_FRACTION_THRESHOLD = 0.0
OVERWRITE = False


def _year_directory(root, template, year):
    return Path(root).expanduser() / template.format(year=int(year))


def _target_grid_indices(item, target_grid_file, projection_chunk_size):
    """Return target row/column indices for valid source longitude/latitude."""

    try:
        from osgeo import gdal, osr
    except ModuleNotFoundError as error:
        raise RuntimeError("SLSTR 投影需要安装 GDAL Python 绑定") from error
    dataset = gdal.Open(str(target_grid_file))
    if dataset is None:
        raise FileNotFoundError(f"无法打开目标网格：{target_grid_file}")
    shape = (dataset.RasterYSize, dataset.RasterXSize)
    transform = dataset.GetGeoTransform()
    target_srs = osr.SpatialReference()
    target_srs.ImportFromWkt(dataset.GetProjection())
    source_srs = osr.SpatialReference()
    source_srs.ImportFromEPSG(4326)
    if hasattr(source_srs, "SetAxisMappingStrategy"):
        source_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    coordinate_transform = osr.CoordinateTransformation(source_srs, target_srs)
    longitude = np.asarray(item.longitude_deg, dtype=float).ravel()
    latitude = np.asarray(item.latitude_deg, dtype=float).ravel()
    valid = np.isfinite(longitude) & np.isfinite(latitude)
    x = np.full(longitude.shape, np.nan)
    y = np.full(latitude.shape, np.nan)
    valid_index = np.flatnonzero(valid)
    for start in range(0, valid_index.size, projection_chunk_size):
        selected = valid_index[start : start + projection_chunk_size]
        transformed = np.asarray(
            coordinate_transform.TransformPoints(
                list(zip(longitude[selected], latitude[selected], strict=True))
            )
        )
        x[selected] = transformed[:, 0]
        y[selected] = transformed[:, 1]
    inverse = gdal.InvGeoTransform(transform)
    if len(inverse) == 2 and isinstance(inverse[0], (bool, int)):
        if not inverse[0]:
            raise ValueError(f"目标网格仿射变换不可逆：{target_grid_file}")
        inverse = inverse[1]
    column = inverse[0] + inverse[1] * x + inverse[2] * y
    row = inverse[3] + inverse[4] * x + inverse[5] * y
    row_index = np.full(row.shape, -1, dtype=np.int64)
    column_index = np.full(column.shape, -1, dtype=np.int64)
    finite = np.isfinite(row) & np.isfinite(column)
    row_index[finite] = np.floor(row[finite]).astype(np.int64)
    column_index[finite] = np.floor(column[finite]).astype(np.int64)
    return row_index, column_index, shape


def _project_field(values, row, column, target_shape):
    values = np.asarray(values).ravel()
    inside = (
        (row >= 0)
        & (row < target_shape[0])
        & (column >= 0)
        & (column < target_shape[1])
        & np.isfinite(values)
    )
    return aggregate_to_grid(values[inside], row[inside], column[inside], target_shape)[0]


def project_product(
    item,
    target_grid_file,
    projection_chunk_size=None,
    cloud_fraction_threshold=None,
) -> SlstrDataProduct:
    """Project one reconstructed product to the target raster grid."""

    item.validate()
    if projection_chunk_size is None:
        projection_chunk_size = PROJECTION_CHUNK_SIZE
    if cloud_fraction_threshold is None:
        cloud_fraction_threshold = CLOUD_FRACTION_THRESHOLD
    row, column, target_shape = _target_grid_indices(
        item, target_grid_file, int(projection_chunk_size)
    )
    fields = {
        name: _project_field(getattr(item, name), row, column, target_shape)
        for name in ("bt8_k", "bt9_k", "view_zenith_deg", "latitude_deg", "longitude_deg")
    }
    cloud_fraction = _project_field(item.cloud_mask.astype(float), row, column, target_shape)
    optional = {
        name: None if getattr(item, name) is None else _project_field(
            getattr(item, name), row, column, target_shape
        )
        for name in LST_AUXILIARY_FIELDS
    }
    result = SlstrDataProduct(
        source_product=item.source_product,
        view=item.view,
        start_time=item.start_time,
        end_time=item.end_time,
        cloud_mask=np.isnan(cloud_fraction) | (cloud_fraction > cloud_fraction_threshold),
        auxiliary_source=item.auxiliary_source,
        **fields,
        **optional,
    )
    result.validate()
    return result


def slstr_project(
    indir_reconstruct=None,
    outdir_project=None,
    target_grid_file=None,
    years=None,
    projection_chunk_size=None,
    cloud_fraction_threshold=None,
    overwrite=None,
) -> None:
    """Project reconstructed products to the selected target grid."""

    if indir_reconstruct is None:
        indir_reconstruct = SLSTR_RECONSTRUCT_ROOT
    if outdir_project is None:
        outdir_project = SLSTR_PROJECT_ROOT
    if target_grid_file is None:
        target_grid_file = TARGET_GRID_FILE
    if years is None:
        years = YEARS
    if projection_chunk_size is None:
        projection_chunk_size = PROJECTION_CHUNK_SIZE
    if cloud_fraction_threshold is None:
        cloud_fraction_threshold = CLOUD_FRACTION_THRESHOLD
    if overwrite is None:
        overwrite = OVERWRITE

    require_parameters(
        indir_reconstruct=indir_reconstruct,
        outdir_project=outdir_project,
        target_grid_file=target_grid_file,
        years=years,
    )
    for year in years:
        input_year = _year_directory(indir_reconstruct, RECONSTRUCT_YEAR_TEMPLATE, year)
        output_year = _year_directory(outdir_project, PROJECT_YEAR_TEMPLATE, year)
        if not input_year.is_dir():
            continue
        inputs = sorted(input_year.rglob("*.tif"))
        for index, input_path in enumerate(inputs):
            output_path = output_year / input_path.relative_to(input_year)
            if output_path.exists() and not overwrite:
                continue
            print(f"[{year}] {index + 1}/{len(inputs)} 投影 {input_path}")
            write_data_product(
                output_path,
                project_product(
                    read_data_product(input_path),
                    target_grid_file,
                    projection_chunk_size,
                    cloud_fraction_threshold,
                ),
                reference_path=target_grid_file,
            )
