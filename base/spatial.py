"""Stable spatial operations shared by sensor-owned processing stages.

The functions here do not traverse product directories.  Sensor modules keep
their own file naming and grouping rules, while this module only projects,
crops, or mosaics already decoded in-memory products.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from pathlib import Path
from typing import Iterable

import numpy as np

from .product import TemperatureProduct
from .quality import QualityFlag, usable


Bounds = tuple[float, float, float, float]
COORDINATE_FIELDS = {"latitude_deg", "longitude_deg"}


def bounds_mask(latitude, longitude, bounds: Bounds) -> np.ndarray:
    """Return pixels inside ``(west, south, east, north)`` lon/lat bounds."""

    latitude = np.asarray(latitude, dtype=float)
    longitude = np.asarray(longitude, dtype=float)
    if latitude.ndim != 2 or latitude.shape != longitude.shape:
        raise ValueError("latitude and longitude must be matching two-dimensional arrays")
    west, south, east, north = (float(value) for value in bounds)
    if south >= north:
        raise ValueError("study-area south bound must be below north bound")
    if not (-90.0 <= south <= 90.0 and -90.0 <= north <= 90.0):
        raise ValueError("study-area latitude bounds must be within [-90, 90]")
    longitude_inside = (
        (longitude >= west) & (longitude <= east)
        if west <= east
        else (longitude >= west) | (longitude <= east)
    )
    return (
        np.isfinite(latitude)
        & np.isfinite(longitude)
        & longitude_inside
        & (latitude >= south)
        & (latitude <= north)
    )


def study_area_window(latitude, longitude, bounds: Bounds):
    """Return a minimal rectangular window and its exact in-bounds mask."""

    mask = bounds_mask(latitude, longitude, bounds)
    rows, columns = np.nonzero(mask)
    if rows.size == 0:
        raise ValueError(f"study area {tuple(bounds)} does not intersect the product")
    row_slice = slice(int(rows.min()), int(rows.max()) + 1)
    column_slice = slice(int(columns.min()), int(columns.max()) + 1)
    return row_slice, column_slice, mask[row_slice, column_slice]


def _array_fields(item):
    if not is_dataclass(item):
        raise TypeError("observation product must be a dataclass instance")
    shape = tuple(item.shape)
    for definition in fields(item):
        value = getattr(item, definition.name)
        if isinstance(value, np.ndarray) and value.shape == shape:
            yield definition.name, value


def crop_observation(item, bounds: Bounds):
    """Crop an AATSR, SLSTR, or MSG data product to lon/lat bounds."""

    row_slice, column_slice, inside = study_area_window(
        item.latitude_deg, item.longitude_deg, bounds
    )
    updates = {}
    for name, value in _array_fields(item):
        cropped = np.asarray(value)[row_slice, column_slice].copy()
        if name == "cloud_mask":
            cropped = np.asarray(cropped, dtype=bool)
            cropped[~inside] = True
        elif name not in COORDINATE_FIELDS:
            cropped = np.asarray(cropped, dtype=float)
            cropped[~inside] = np.nan
        updates[name] = cropped
    result = replace(item, **updates)
    result.validate()
    return result


def _pick(stack: np.ndarray, selected: np.ndarray) -> np.ndarray:
    return np.take_along_axis(stack, selected[np.newaxis, ...], axis=0)[0]


def _first_finite(stack: np.ndarray) -> np.ndarray:
    finite = np.isfinite(stack)
    selected = np.argmax(finite, axis=0)
    result = _pick(stack, selected)
    result[~np.any(finite, axis=0)] = np.nan
    return result


def mosaic_observations(
    items: Iterable[object],
    primary_field: str,
    angle_field: str = "view_zenith_deg",
):
    """Mosaic same-grid decoded scenes, preferring clear low-view-angle pixels."""

    items = list(items)
    if not items:
        raise ValueError("at least one observation product is required")
    for item in items:
        item.validate()
    first = items[0]
    shape = tuple(first.shape)
    if any(tuple(item.shape) != shape or type(item) is not type(first) for item in items):
        raise ValueError("observation mosaics require one product type and one target-grid shape")
    if hasattr(first, "view") and any(item.view != first.view for item in items):
        raise ValueError("nadir/oblique or nadir/forward views must be mosaicked separately")

    angle = np.stack(
        [np.abs(np.asarray(getattr(item, angle_field), dtype=float)) for item in items]
    )
    valid = np.stack(
        [
            ~np.asarray(item.cloud_mask, dtype=bool)
            & np.isfinite(np.asarray(getattr(item, primary_field), dtype=float))
            for item in items
        ]
    ) & np.isfinite(angle)
    score = np.where(valid, angle, np.inf)
    selected = np.argmin(score, axis=0)
    has_valid = np.any(valid, axis=0)

    updates = {}
    for definition in fields(first):
        name = definition.name
        values = [getattr(item, name) for item in items]
        present = [isinstance(value, np.ndarray) for value in values]
        if any(present) and not all(present):
            raise ValueError(f"all mosaic scenes must agree on optional field {name}")
        if not all(present) or any(value.shape != shape for value in values):
            continue
        stack = np.stack(values)
        if name == "cloud_mask":
            updates[name] = ~has_valid
        elif name in COORDINATE_FIELDS:
            updates[name] = _first_finite(np.asarray(stack, dtype=float))
        else:
            chosen = _pick(np.asarray(stack), selected)
            if not np.issubdtype(chosen.dtype, np.floating):
                chosen = chosen.astype(float)
            chosen[~has_valid] = np.nan
            updates[name] = chosen

    if hasattr(first, "source_product"):
        updates["source_product"] = ";".join(item.source_product for item in items)
    starts = [getattr(item, "start_time", None) for item in items]
    ends = [getattr(item, "end_time", None) for item in items]
    starts = [value for value in starts if value]
    ends = [value for value in ends if value]
    if starts:
        updates["start_time"] = min(starts)
    if ends:
        updates["end_time"] = max(ends)
    if hasattr(first, "auxiliary_source"):
        sources = [item.auxiliary_source for item in items if item.auxiliary_source]
        updates["auxiliary_source"] = ";".join(sources) or None

    result = replace(first, **updates)
    result.validate()
    return result


def target_grid_indices(
    longitude,
    latitude,
    target_grid_file: str | Path,
    chunk_size: int = 100_000,
):
    """Map source longitude/latitude to row/column indices of a GDAL raster."""

    if int(chunk_size) <= 0:
        raise ValueError("chunk_size must be positive")
    try:
        from osgeo import gdal, osr
    except ModuleNotFoundError as error:
        raise RuntimeError("projection requires the GDAL Python bindings") from error
    dataset = gdal.Open(str(target_grid_file))
    if dataset is None:
        raise FileNotFoundError(f"cannot open target grid: {target_grid_file}")
    target_shape = (dataset.RasterYSize, dataset.RasterXSize)
    transform = dataset.GetGeoTransform()
    target_srs = osr.SpatialReference()
    target_srs.ImportFromWkt(dataset.GetProjection())
    source_srs = osr.SpatialReference()
    source_srs.ImportFromEPSG(4326)
    if hasattr(source_srs, "SetAxisMappingStrategy"):
        source_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    coordinate_transform = osr.CoordinateTransformation(source_srs, target_srs)

    longitude = np.asarray(longitude, dtype=float).ravel()
    latitude = np.asarray(latitude, dtype=float).ravel()
    valid_index = np.flatnonzero(np.isfinite(longitude) & np.isfinite(latitude))
    x = np.full(longitude.shape, np.nan)
    y = np.full(latitude.shape, np.nan)
    for start in range(0, valid_index.size, int(chunk_size)):
        selected = valid_index[start : start + int(chunk_size)]
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
            raise ValueError(f"target-grid transform is not invertible: {target_grid_file}")
        inverse = inverse[1]
    column = inverse[0] + inverse[1] * x + inverse[2] * y
    row = inverse[3] + inverse[4] * x + inverse[5] * y
    row_index = np.full(row.shape, -1, dtype=np.int64)
    column_index = np.full(column.shape, -1, dtype=np.int64)
    finite = np.isfinite(row) & np.isfinite(column)
    row_index[finite] = np.floor(row[finite]).astype(np.int64)
    column_index[finite] = np.floor(column[finite]).astype(np.int64)
    return row_index, column_index, target_shape


def _project_field(values, row, column, target_shape):
    values = np.asarray(values).ravel()
    inside = (
        (row >= 0)
        & (row < target_shape[0])
        & (column >= 0)
        & (column < target_shape[1])
        & np.isfinite(values)
    )
    flat_index = row[inside] * target_shape[1] + column[inside]
    size = target_shape[0] * target_shape[1]
    count = np.bincount(flat_index, minlength=size)
    total = np.bincount(flat_index, weights=values[inside], minlength=size)
    result = np.full(size, np.nan, dtype=float)
    np.divide(total, count, out=result, where=count > 0)
    return result.reshape(target_shape)


def project_observation(
    item,
    target_grid_file: str | Path,
    chunk_size: int = 100_000,
    cloud_fraction_threshold: float = 0.0,
):
    """Project every same-shape array in a decoded observation product."""

    if not 0.0 <= float(cloud_fraction_threshold) <= 1.0:
        raise ValueError("cloud_fraction_threshold must be in [0, 1]")
    item.validate()
    row, column, target_shape = target_grid_indices(
        item.longitude_deg, item.latitude_deg, target_grid_file, chunk_size
    )
    updates = {}
    cloud_fraction = None
    for name, value in _array_fields(item):
        if name == "cloud_mask":
            cloud_fraction = _project_field(
                np.asarray(value, dtype=float), row, column, target_shape
            )
        else:
            updates[name] = _project_field(value, row, column, target_shape)
    if cloud_fraction is None:
        raise ValueError("observation product has no cloud_mask")
    primary_names = [
        name for name in ("bt1_k", "bt8_k", "bt11_k", "bt108_k", "bt8") if name in updates
    ]
    if not primary_names:
        raise ValueError("cannot identify a primary thermal field for projection")
    updates["cloud_mask"] = (
        np.isnan(updates[primary_names[0]])
        | np.isnan(cloud_fraction)
        | (cloud_fraction > float(cloud_fraction_threshold))
    )
    result = replace(item, **updates)
    result.validate()
    return result


def crop_temperature_product(product: TemperatureProduct, bounds: Bounds) -> TemperatureProduct:
    """Crop an LST/LSCT result carrying latitude and longitude variables."""

    product.validate()
    if not COORDINATE_FIELDS.issubset(product.variables):
        raise ValueError("result product must contain latitude_deg and longitude_deg")
    row_slice, column_slice, inside = study_area_window(
        product.variables["latitude_deg"], product.variables["longitude_deg"], bounds
    )
    variables = {}
    for name, value in product.variables.items():
        cropped = np.asarray(value)[row_slice, column_slice].copy()
        if name not in COORDINATE_FIELDS:
            cropped = np.asarray(cropped, dtype=float)
            cropped[~inside] = np.nan
        variables[name] = cropped
    quality = np.asarray(product.quality_flag, dtype=np.uint16)[row_slice, column_slice].copy()
    quality[~inside] |= np.uint16(QualityFlag.INPUT_INVALID)
    uncertainty = {}
    for name, value in product.uncertainty.items():
        cropped = np.asarray(value, dtype=float)[row_slice, column_slice].copy()
        cropped[~inside] = np.nan
        uncertainty[name] = cropped
    attributes = dict(product.metadata.attributes)
    attributes.update({"spatial_operation": "crop", "study_bounds": list(map(float, bounds))})
    result = TemperatureProduct(
        replace(product.metadata, attributes=attributes), variables, quality, uncertainty
    )
    result.validate()
    return result


def mosaic_temperature_products(
    products: Iterable[TemperatureProduct],
) -> TemperatureProduct:
    """Mosaic same-grid scene results, selecting the best valid overlap pixel."""

    products = list(products)
    if not products:
        raise ValueError("at least one result product is required")
    for product in products:
        product.validate()
    first = products[0]
    shape = np.asarray(first.quality_flag).shape
    compatibility = (
        first.metadata.sensor,
        first.metadata.level,
        first.metadata.grid_id,
        first.metadata.algorithm_version,
    )
    for product in products[1:]:
        current = (
            product.metadata.sensor,
            product.metadata.level,
            product.metadata.grid_id,
            product.metadata.algorithm_version,
        )
        if current != compatibility or np.asarray(product.quality_flag).shape != shape:
            raise ValueError("result mosaics require matching sensor, level, grid and algorithm")
        if set(product.variables) != set(first.variables):
            raise ValueError("result mosaics require matching variables")
        if set(product.uncertainty) != set(first.uncertainty):
            raise ValueError("result mosaics require matching uncertainty fields")

    temperature_names = list(first.metadata.attributes.get("temperature_variable_names", ()))
    if "lst" in first.variables:
        primary_name = "lst"
    else:
        candidates = [name for name in temperature_names if name in first.variables]
        if not candidates:
            candidates = [name for name in first.variables if name not in COORDINATE_FIELDS]
        if not candidates:
            raise ValueError("result product has no field suitable for mosaic selection")
        primary_name = candidates[0]
    quality_stack = np.stack([np.asarray(product.quality_flag, dtype=np.uint16) for product in products])
    valid = usable(quality_stack) & np.stack(
        [np.isfinite(np.asarray(product.variables[primary_name], dtype=float)) for product in products]
    )
    if primary_name in first.uncertainty:
        uncertainty_score = np.stack(
            [np.asarray(product.uncertainty[primary_name], dtype=float) for product in products]
        )
        valid &= np.isfinite(uncertainty_score) & (uncertainty_score > 0)
        order = np.arange(len(products), dtype=float).reshape(
            (len(products),) + (1,) * len(shape)
        )
        score = np.where(
            np.isfinite(uncertainty_score), uncertainty_score, 1.0e30 + order
        )
    else:
        order = np.arange(len(products), dtype=float).reshape(
            (len(products),) + (1,) * len(shape)
        )
        score = np.broadcast_to(
            order,
            (len(products),) + shape,
        )
    score = np.where(valid, score, np.inf)
    selected = np.argmin(score, axis=0)
    has_valid = np.any(valid, axis=0)

    variables = {}
    for name in first.variables:
        stack = np.stack([np.asarray(product.variables[name]) for product in products])
        if name in COORDINATE_FIELDS:
            variables[name] = _first_finite(np.asarray(stack, dtype=float))
        else:
            chosen = _pick(stack, selected)
            if not np.issubdtype(chosen.dtype, np.floating):
                chosen = chosen.astype(float)
            chosen[~has_valid] = np.nan
            variables[name] = chosen

    quality = _pick(quality_stack, selected).astype(np.uint16)
    rejected = np.bitwise_or.reduce(quality_stack, axis=0)
    quality[~has_valid] = rejected[~has_valid] | np.uint16(QualityFlag.INPUT_INVALID)
    uncertainty = {}
    for name in first.uncertainty:
        stack = np.stack(
            [np.asarray(product.uncertainty[name], dtype=float) for product in products]
        )
        chosen = _pick(stack, selected)
        chosen[~has_valid] = np.nan
        uncertainty[name] = chosen

    starts = [product.metadata.start_time for product in products]
    ends = [product.metadata.end_time for product in products]
    sources = []
    for product in products:
        sources.extend(product.metadata.source_products)
    attributes = dict(first.metadata.attributes)
    attributes.update({"spatial_operation": "mosaic", "scene_count": len(products)})
    metadata = replace(
        first.metadata,
        start_time=min(starts),
        end_time=max(ends),
        source_products=tuple(dict.fromkeys(sources)),
        attributes=attributes,
    )
    result = TemperatureProduct(metadata, variables, quality, uncertainty)
    result.validate()
    return result
