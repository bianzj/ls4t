"""Independent GeoTIFF normalization stages with explicit auxiliary inputs."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from base.quality import QualityFlag, usable
from base.raster import _gdal, write_raster
from .angle import normalize_directional
from .time import normalize_local_solar_time
from .downscale import downscale_temperature
from ._validation import quality_flags


def _band_number(dataset, selector):
    names = [dataset.GetRasterBand(i).GetDescription() for i in range(1, dataset.RasterCount+1)]
    if selector is None:
        selector = next((name for name in ("temperature_k", "variable__lst", "lst") if name in names), None)
        if selector is None and dataset.RasterCount == 1:
            selector = 1
    if isinstance(selector, str) and selector in names:
        return names.index(selector) + 1
    if isinstance(selector, int) and 1 <= selector <= dataset.RasterCount:
        return selector
    raise ValueError(f"missing or ambiguous raster band: {selector!r}; available: {names}")


def _read(path, band=None, *, scale=None, offset=None):
    gdal = _gdal()
    ds = gdal.Open(str(path), gdal.GA_ReadOnly)
    if ds is None:
        raise FileNotFoundError(path)
    try:
        source = ds.GetRasterBand(_band_number(ds, band))
        raw = np.asarray(source.ReadAsArray(), dtype=float)
        valid = np.isfinite(raw) & (source.GetMaskBand().ReadAsArray() != 0)
        nodata = source.GetNoDataValue()
        if nodata is not None:
            valid &= raw != nodata
        scale = source.GetScale() if scale is None else scale
        offset = source.GetOffset() if offset is None else offset
        decoded = raw * (1. if scale is None else scale) + (0. if offset is None else offset)
        grid = (raw.shape, ds.GetGeoTransform(can_return_null=True), ds.GetProjection())
        if grid[1] is None or not grid[2]:
            raise ValueError(f"raster requires an explicit CRS and georeferenced grid: {path}")
        return np.where(valid, decoded, np.nan), grid, ds.GetMetadata_Dict()
    finally:
        ds = None


def _same_grid(first, second, *, nested=False):
    from osgeo import osr
    shape, transform, projection = first
    other_shape, other_transform, other_projection = second
    crs, other_crs = osr.SpatialReference(), osr.SpatialReference()
    crs.ImportFromWkt(projection)
    other_crs.ImportFromWkt(other_projection)
    if not crs.IsSame(other_crs):
        raise ValueError("raster grids must share a CRS; reproject explicitly first")
    expected = np.array(transform, dtype=float)
    if nested:
        if (other_shape[0] % shape[0] or other_shape[1] % shape[1]
                or other_shape[0] < shape[0] or other_shape[1] < shape[1]):
            raise ValueError("fine grid must be an integer subdivision")
        if transform[2] != 0 or transform[4] != 0 or transform[1] <= 0 or transform[5] >= 0:
            raise ValueError("downscaling requires a north-up grid")
        expected[1] *= shape[1]/other_shape[1]
        expected[5] *= shape[0]/other_shape[0]
    elif shape != other_shape:
        raise ValueError("auxiliary raster grid shape does not match")
    tolerance = min(abs(expected[1]), abs(expected[5])) * 1e-7
    if not np.allclose(expected, other_transform, rtol=0, atol=tolerance):
        raise ValueError("raster grid alignment/extent mismatch; align explicitly first")


def _field(value, grid):
    if isinstance(value, dict):
        if set(value) - {"path", "band", "scale", "offset"}:
            raise ValueError("unknown raster field option")
        array, other_grid, _ = _read(**value)
        _same_grid(grid, other_grid)
        return array
    if not np.isscalar(value):
        raise ValueError("a raster field must be a scalar or {path, band, scale, offset}")
    return np.full(grid[0], float(value))


def _protect(output, values):
    for value in values:
        if isinstance(value, dict) and Path(value["path"]).resolve() == Path(output).resolve():
            raise ValueError("output must not overwrite an auxiliary input source")


def _prepare(input_path, output_path, stage, *, temperature_band, quality_band,
             temperature_scale, temperature_offset, overwrite):
    if Path(input_path).resolve() == Path(output_path).resolve():
        raise ValueError("output must not overwrite input source")
    if Path(output_path).exists() and not overwrite:
        raise FileExistsError(output_path)
    values, grid, metadata = _read(input_path, temperature_band, scale=temperature_scale, offset=temperature_offset)
    provenance = json.loads(metadata.get("LS4T_NORMALIZATION", '{"history": []}'))
    if any(step["stage"] == stage for step in provenance["history"]):
        raise ValueError(f"input has already undergone {stage} normalization")
    if quality_band is None:
        ds = _gdal().Open(str(input_path))
        names = [ds.GetRasterBand(i).GetDescription() for i in range(1, ds.RasterCount+1)]
        quality_band = "quality_flag" if "quality_flag" in names else None
        ds = None
    flags = np.zeros(values.shape, dtype=np.uint16)
    if quality_band is not None:
        quality, _, _ = _read(input_path, quality_band, scale=1., offset=0.)
        flags = quality_flags(quality)
    invalid = ~np.isfinite(values) | (values < 150) | (values > 400)
    flags[invalid] |= np.uint16(QualityFlag.INPUT_INVALID)
    values = np.where(usable(flags), values, np.nan)
    return values, flags, grid, provenance


def _save(output, reference, values, flags, provenance, stage, input_path, parameters, extra=None):
    provenance = {**provenance, "unit": "K", "history": [*provenance["history"], {
        "stage": stage, "source": str(Path(input_path).resolve()), "parameters": parameters,
    }]}
    fields = {"temperature_k": values, "quality_flag": flags}
    fields.update(extra or {})
    write_raster(output, fields, {
        "LS4T_SCHEMA": "NORMALIZATION_STAGE_V1",
        "LS4T_NORMALIZATION": json.dumps(provenance, ensure_ascii=False, default=str, allow_nan=False),
    }, reference_path=reference, nodata=np.nan)
    return Path(output)


def angle_normalize_raster(
    input_path, output_path, *, view_zenith_deg, solar_zenith_deg,
    relative_azimuth_deg, coefficients_k, reference_view_zenith_deg=0.,
    reference_solar_zenith_deg=30., reference_relative_azimuth_deg=0.,
    temperature_band=None, quality_band=None, temperature_scale=None,
    temperature_offset=None, overwrite=False,
):
    """Normalize one source to explicit reference geometry; coefficients are required."""
    if len(coefficients_k) != 3:
        raise ValueError("supply three directional coefficients")
    _protect(output_path, [view_zenith_deg, solar_zenith_deg, relative_azimuth_deg, *coefficients_k])
    values, flags, grid, history = _prepare(input_path, output_path, "angle",
        temperature_band=temperature_band, quality_band=quality_band,
        temperature_scale=temperature_scale, temperature_offset=temperature_offset, overwrite=overwrite)
    geometry = dict(view_zenith_deg=view_zenith_deg, solar_zenith_deg=solar_zenith_deg,
                    relative_azimuth_deg=relative_azimuth_deg)
    reference = dict(reference_view_zenith_deg=reference_view_zenith_deg,
                     reference_solar_zenith_deg=reference_solar_zenith_deg,
                     reference_relative_azimuth_deg=reference_relative_azimuth_deg)
    result = normalize_directional(values, **{key: _field(value, grid) for key, value in geometry.items()},
        coefficients_k=np.stack([_field(value, grid) for value in coefficients_k], axis=-1), **reference)
    flags[np.isfinite(values) & ~np.isfinite(result)] |= np.uint16(QualityFlag.NORMALIZATION_FAILED)
    return _save(output_path, input_path, result, flags, history, "angle", input_path,
        {**geometry, **reference, "coefficients_k": coefficients_k,
         "temperature_band": temperature_band, "quality_band": quality_band,
         "temperature_scale": temperature_scale, "temperature_offset": temperature_offset},
        {"correction_k": result-values})


def time_normalize_raster(
    input_path, output_path, *, local_solar_time_hour, amplitude_k, peak_hour,
    reference_hour=13.5, temperature_band=None, quality_band=None,
    temperature_scale=None, temperature_offset=None, overwrite=False,
):
    """Normalize one source to a common local solar hour using supplied DTC parameters."""
    _protect(output_path, [local_solar_time_hour, amplitude_k, peak_hour])
    values, flags, grid, history = _prepare(input_path, output_path, "time",
        temperature_band=temperature_band, quality_band=quality_band,
        temperature_scale=temperature_scale, temperature_offset=temperature_offset, overwrite=overwrite)
    parameters = dict(local_solar_time_hour=local_solar_time_hour, amplitude_k=amplitude_k, peak_hour=peak_hour)
    result = normalize_local_solar_time(values, **{key: _field(value, grid) for key, value in parameters.items()},
                                        reference_hour=reference_hour)
    flags[np.isfinite(values) & ~np.isfinite(result)] |= np.uint16(QualityFlag.NORMALIZATION_FAILED)
    return _save(output_path, input_path, result, flags, history, "time", input_path,
        {**parameters, "reference_hour": reference_hour, "temperature_band": temperature_band,
         "quality_band": quality_band, "temperature_scale": temperature_scale,
         "temperature_offset": temperature_offset}, {"correction_k": result-values})


def downscale_raster(
    input_path, output_path, *, predictors, fine_quality_flag=0, fine_weights=None,
    minimum_coverage=1., temperature_band=None, quality_band=None,
    temperature_scale=None, temperature_offset=None, overwrite=False, method="linear",
):
    """Sharpen to the first predictor's grid; method=tsharp takes one NDVI band."""
    if method not in ("linear", "tsharp"):
        raise ValueError("downscale method must be linear or tsharp")
    if not predictors or not all(isinstance(item, dict) and "path" in item for item in predictors):
        raise ValueError("predictors must be a nonempty list of raster field descriptors")
    if method == "tsharp" and len(predictors) != 1:
        raise ValueError("TsHARP requires exactly one NDVI predictor")
    _protect(output_path, [*predictors, fine_quality_flag, fine_weights])
    values, flags, grid, history = _prepare(input_path, output_path, "downscale",
        temperature_band=temperature_band, quality_band=quality_band,
        temperature_scale=temperature_scale, temperature_offset=temperature_offset, overwrite=overwrite)
    _, fine_grid, _ = _read(**predictors[0])
    _same_grid(grid, fine_grid, nested=True)
    arrays = np.stack([_field(item, fine_grid) for item in predictors], axis=-1)
    fine_flags = quality_flags(_field(fine_quality_flag, fine_grid))
    if fine_weights is None:
        from osgeo import osr
        crs = osr.SpatialReference()
        crs.ImportFromWkt(fine_grid[2])
        weights = np.ones(fine_grid[0])
        if crs.IsGeographic():
            transform = fine_grid[1]
            edges = transform[3] + np.arange(fine_grid[0][0]+1)*transform[5]
            if np.any(np.abs(edges) > 90):
                raise ValueError("geographic grid latitude outside [-90, 90]")
            weights *= np.abs(np.diff(np.sin(np.deg2rad(edges))))[:, None]
    else:
        weights = _field(fine_weights, fine_grid)
    result = downscale_temperature(values, arrays, coarse_quality_flag=flags,
        fine_quality_flag=fine_flags, fine_weights=weights, minimum_coverage=minimum_coverage,
        method=method)
    ry, rx = fine_grid[0][0]//grid[0][0], fine_grid[0][1]//grid[0][1]
    extra = {"coarse_coverage": np.repeat(np.repeat(result.coarse_coverage, ry, 0), rx, 1)}
    return _save(output_path, predictors[0]["path"], result.temperature_k, result.quality_flag,
        history, "downscale", input_path, {"predictors": predictors, "method": result.method,
        "predictor_transform": "1-(1-NDVI)**0.625" if method == "tsharp" else "identity",
        "coarse_predictor_order": "area-weighted mean NDVI, then cover transform" if method == "tsharp" else "area-weighted predictor means",
        "residual_definition": "coarse temperature minus area-weighted fine prediction mean",
        "minimum_coverage": minimum_coverage, "fine_quality_flag": fine_quality_flag,
        "fine_weights": fine_weights, "coefficients": result.coefficients.tolist(),
        "training_rmse_k": result.training_rmse_k, "training_count": result.training_count,
        "closure": "area-weighted temperature mean (K), not radiance",
        "temperature_band": temperature_band, "quality_band": quality_band,
        "temperature_scale": temperature_scale, "temperature_offset": temperature_offset}, extra)
