"""Reusable processing foundation for dual-thermal-channel sensors.

The sensor packages own channel names and public function names.  This module
owns the stable LS4T-DATA representation and the common extraction, projection,
mosaic, region and split-window LST mechanics.  Native HDF/NetCDF decoding is
deliberately outside this module until a sensor reader is validated.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from typing import ClassVar, Iterable, TypeVar

import numpy as np

from .calibration import load_split_window_model
from .files import read_npz_payload, write_npz_atomic
from .lst import DualChannelObservation, SplitWindowResult, retrieve_dual_channel_lst
from .parameters import require_parameters
from .product import ProductLevel, ProductMetadata, TemperatureProduct
from .raster import metadata as raster_metadata
from .raster import read_raster, read_temperature_product, write_raster, write_temperature_product
from .data import read_product
from .spatial import (
    crop_observation,
    crop_temperature_product,
    mosaic_observations,
    mosaic_temperature_products,
    project_observation,
)


SCHEMA = "ls4t.dual-thermal-data/v1"
AUXILIARY_FIELDS = (
    "soil_emissivity_1",
    "soil_emissivity_2",
    "vegetation_emissivity_1",
    "vegetation_emissivity_2",
    "lai",
    "tcwv_cm",
)
DAY_TEMPLATE = "{year:04d}/{month:02d}/{day:02d}"


@dataclass(frozen=True)
class DualThermalSensorSpec:
    """Stable metadata required by a sensor-owned wrapper package."""

    name: str
    channels: tuple[str, str]
    prepared_keys: tuple[tuple[str, ...], tuple[str, ...]]
    native_grid_id: str
    algorithm_version: str
    input_pattern: str = "*.npz"

    def __post_init__(self) -> None:
        if len(self.channels) != 2 or len(self.prepared_keys) != 2:
            raise ValueError("dual-thermal sensor definitions require exactly two channels")


@dataclass(frozen=True)
class DualThermalDataProduct:
    """Canonical decoded observation used by MODIS, VIIRS, AHI and ASTER."""

    sensor: ClassVar[str] = ""
    source_product: str
    start_time: str
    end_time: str
    bt1_k: np.ndarray
    bt2_k: np.ndarray
    view_zenith_deg: np.ndarray
    latitude_deg: np.ndarray
    longitude_deg: np.ndarray
    cloud_mask: np.ndarray
    auxiliary_source: str | None = None
    soil_emissivity_1: np.ndarray | None = None
    soil_emissivity_2: np.ndarray | None = None
    vegetation_emissivity_1: np.ndarray | None = None
    vegetation_emissivity_2: np.ndarray | None = None
    lai: np.ndarray | None = None
    tcwv_cm: np.ndarray | None = None

    @property
    def shape(self) -> tuple[int, ...]:
        return np.asarray(self.bt1_k).shape

    @property
    def has_lst_auxiliary(self) -> bool:
        return all(getattr(self, name) is not None for name in AUXILIARY_FIELDS)

    def validate(self, require_lst_auxiliary: bool = False) -> None:
        if not self.sensor:
            raise ValueError("sensor subclass must define a sensor name")
        if len(self.shape) != 2:
            raise ValueError(f"{self.sensor} arrays must be two-dimensional")
        required = (
            "bt2_k",
            "view_zenith_deg",
            "latitude_deg",
            "longitude_deg",
            "cloud_mask",
        )
        for name in required:
            if np.asarray(getattr(self, name)).shape != self.shape:
                raise ValueError(f"{name} does not match the {self.sensor} grid")
        for name in ("bt1_k", "bt2_k"):
            values = np.asarray(getattr(self, name), dtype=float)
            finite = values[np.isfinite(values)]
            if finite.size and (finite.min() < 100.0 or finite.max() > 500.0):
                raise ValueError(f"{name} must contain brightness temperature in kelvin")
        present = [name for name in AUXILIARY_FIELDS if getattr(self, name) is not None]
        if present and len(present) != len(AUXILIARY_FIELDS):
            raise ValueError(f"{self.sensor} LST auxiliary fields must be supplied together")
        if require_lst_auxiliary and not self.has_lst_auxiliary:
            raise ValueError(f"{self.sensor}-DATA has no LST auxiliary fields")
        for name in present:
            if np.asarray(getattr(self, name)).shape != self.shape:
                raise ValueError(f"{name} does not match the {self.sensor} grid")


ProductType = TypeVar("ProductType", bound=DualThermalDataProduct)


def _metadata(payload: dict[str, np.ndarray], path: Path) -> dict:
    if "metadata" not in payload:
        raise ValueError(
            f"prepared input must contain JSON metadata with start_time/end_time: {path}"
        )
    try:
        return json.loads(str(np.asarray(payload["metadata"]).item()))
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid prepared-input metadata: {path}") from error


def _first(payload: dict[str, np.ndarray], names: Iterable[str], path: Path) -> np.ndarray:
    for name in names:
        if name in payload:
            return np.asarray(payload[name], dtype=float)
    raise KeyError(f"{path} is missing one of: {', '.join(names)}")


def read_prepared_product(
    path: str | Path,
    spec: DualThermalSensorSpec,
    product_type: type[ProductType],
) -> ProductType:
    """Convert reviewed native arrays into a sensor LS4T-DATA object.

    GeoTIFF is the new prepared-input format; NPZ remains readable for legacy
    prepared arrays. Brightness temperatures must already be decoded to kelvin.
    """

    source_path = Path(path)
    if source_path.suffix.lower() in {".tif", ".tiff"}:
        payload, file_metadata = read_raster(source_path)
        if "LS4T_METADATA" not in file_metadata:
            raise ValueError(f"prepared GeoTIFF has no metadata: {source_path}")
        metadata = json.loads(file_metadata["LS4T_METADATA"])
    else:
        payload = read_npz_payload(source_path)
        metadata = _metadata(payload, source_path)
    declared_sensor = str(metadata.get("sensor", spec.name)).upper()
    if declared_sensor != spec.name.upper():
        raise ValueError(
            f"prepared input sensor {declared_sensor!r} does not match {spec.name!r}"
        )
    latitude = _first(payload, ("latitude_deg", "latitude"), source_path)
    longitude = _first(payload, ("longitude_deg", "longitude"), source_path)
    shape = latitude.shape
    cloud = (
        np.asarray(payload["cloud_mask"], dtype=bool)
        if "cloud_mask" in payload
        else np.zeros(shape, dtype=bool)
    )
    item = product_type(
        source_product=str(metadata.get("source_product", source_path)),
        start_time=str(metadata.get("start_time", "")),
        end_time=str(metadata.get("end_time", "")),
        bt1_k=_first(payload, ("bt1_k", *spec.prepared_keys[0]), source_path),
        bt2_k=_first(payload, ("bt2_k", *spec.prepared_keys[1]), source_path),
        view_zenith_deg=_first(
            payload, ("view_zenith_deg", "sensor_zenith_deg"), source_path
        ),
        latitude_deg=latitude,
        longitude_deg=longitude,
        cloud_mask=cloud,
    )
    if not item.start_time or not item.end_time:
        raise ValueError(f"prepared input metadata has no start_time/end_time: {source_path}")
    item.validate()
    return item


def write_data_product(
    path: str | Path,
    item: DualThermalDataProduct,
    spec: DualThermalSensorSpec,
) -> None:
    item.validate()
    if item.sensor.upper() != spec.name.upper():
        raise ValueError(f"cannot write {item.sensor} with the {spec.name} data writer")
    if Path(path).suffix.lower() == ".npz":
        metadata = {
            "schema": SCHEMA,
            "sensor": spec.name.upper(),
            "thermal_channels": list(spec.channels),
            "source_product": item.source_product,
            "start_time": item.start_time,
            "end_time": item.end_time,
            "auxiliary_source": item.auxiliary_source,
        }
        payload = {
            "metadata": np.asarray(json.dumps(metadata, sort_keys=True)),
            "bt1_k": np.asarray(item.bt1_k),
            "bt2_k": np.asarray(item.bt2_k),
            "view_zenith_deg": np.asarray(item.view_zenith_deg),
            "latitude_deg": np.asarray(item.latitude_deg),
            "longitude_deg": np.asarray(item.longitude_deg),
            "cloud_mask": np.asarray(item.cloud_mask, dtype=bool),
        }
        for name in AUXILIARY_FIELDS:
            value = getattr(item, name)
            if value is not None:
                payload[name] = np.asarray(value)
        write_npz_atomic(path, payload)
        return
    fields = {
        "bt1_k": np.asarray(item.bt1_k),
        "bt2_k": np.asarray(item.bt2_k),
        "view_zenith_deg": np.asarray(item.view_zenith_deg),
        "latitude_deg": np.asarray(item.latitude_deg),
        "longitude_deg": np.asarray(item.longitude_deg),
        "cloud_mask": np.asarray(item.cloud_mask, dtype=bool),
    }
    for name in AUXILIARY_FIELDS:
        value = getattr(item, name)
        if value is not None:
            fields[name] = np.asarray(value)
    write_raster(
        path,
        fields,
        raster_metadata(
            SCHEMA,
            sensor=spec.name.upper(),
            thermal_channels=list(spec.channels),
            source_product=item.source_product,
            start_time=item.start_time,
            end_time=item.end_time,
            auxiliary_source=item.auxiliary_source,
        ),
    )


def read_data_product(
    path: str | Path,
    spec: DualThermalSensorSpec,
    product_type: type[ProductType],
) -> ProductType:
    source_path = Path(path)
    if source_path.suffix.lower() in {".tif", ".tiff"}:
        payload, file_metadata = read_raster(source_path)
        if file_metadata.get("LS4T_SCHEMA") != SCHEMA:
            raise ValueError(f"unsupported {spec.name} GeoTIFF data schema")
        metadata = json.loads(file_metadata["LS4T_METADATA"])
    else:
        payload = read_npz_payload(source_path)
        metadata = _metadata(payload, source_path)
    if str(metadata.get("sensor", "")).upper() != spec.name.upper():
        raise ValueError(f"{source_path} is not a {spec.name} data product")
    optional = {
        name: np.asarray(payload[name]).copy() if name in payload else None
        for name in AUXILIARY_FIELDS
    }
    item = product_type(
        source_product=metadata["source_product"],
        start_time=metadata["start_time"],
        end_time=metadata["end_time"],
        bt1_k=np.asarray(payload["bt1_k"]).copy(),
        bt2_k=np.asarray(payload["bt2_k"]).copy(),
        view_zenith_deg=np.asarray(payload["view_zenith_deg"]).copy(),
        latitude_deg=np.asarray(payload["latitude_deg"]).copy(),
        longitude_deg=np.asarray(payload["longitude_deg"]).copy(),
        cloud_mask=np.asarray(payload["cloud_mask"], dtype=bool).copy(),
        auxiliary_source=metadata.get("auxiliary_source"),
        **optional,
    )
    item.validate()
    return item


def add_lst_auxiliary(
    item: ProductType,
    auxiliary_file: str | Path,
) -> ProductType:
    source = Path(auxiliary_file)
    if source.suffix.lower() in {".tif", ".tiff"}:
        auxiliary, _ = read_raster(source)
    else:
        with np.load(source, allow_pickle=False) as bundle:
            auxiliary = {name: bundle[name].copy() for name in bundle.files}
    missing = [name for name in AUXILIARY_FIELDS if name not in auxiliary]
    if missing:
        raise KeyError(f"auxiliary file is missing: {', '.join(missing)}")
    values = {
        name: np.broadcast_to(np.asarray(auxiliary[name], dtype=float), item.shape).copy()
        for name in AUXILIARY_FIELDS
    }
    result = replace(item, auxiliary_source=str(auxiliary_file), **values)
    result.validate(require_lst_auxiliary=True)
    return result


def _day(root, year, month, day) -> Path:
    return Path(root).expanduser() / DAY_TEMPLATE.format(year=year, month=month, day=day)


def extract_sensor_products(
    spec: DualThermalSensorSpec,
    product_type: type[ProductType],
    *,
    indir_raw=None,
    outdir_data=None,
    years=None,
    months=None,
    days=None,
    overwrite=None,
) -> None:
    """Batch-convert prepared native arrays; raw mission readers remain case-owned."""

    require_parameters(indir_raw=indir_raw, outdir_data=outdir_data, years=years)
    months = range(1, 13) if months is None else months
    days = range(1, 32) if days is None else days
    overwrite = False if overwrite is None else bool(overwrite)
    for year in years:
        for month in months:
            for day in days:
                input_day = _day(indir_raw, year, month, day)
                if not input_day.is_dir():
                    continue
                output_day = _day(outdir_data, year, month, day)
                inputs = sorted(input_day.glob("*.tif"))
                if not inputs:
                    inputs = sorted(input_day.glob(spec.input_pattern))
                for index, input_path in enumerate(inputs):
                    output_path = (output_day / input_path.relative_to(input_day)).with_suffix(
                        ".tif" if input_path.suffix.lower() != ".npz" else ".npz"
                    )
                    if output_path.exists() and not overwrite:
                        continue
                    print(
                        f"[{year:04d}-{month:02d}-{day:02d}] "
                        f"{index + 1}/{len(inputs)} 提取 {input_path.name}"
                    )
                    item = read_prepared_product(input_path, spec, product_type)
                    write_data_product(output_path, item, spec)


def project_sensor_products(
    spec: DualThermalSensorSpec,
    product_type: type[ProductType],
    *,
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
    require_parameters(
        indir_data=indir_data,
        outdir_project=outdir_project,
        target_grid_file=target_grid_file,
        years=years,
    )
    months = range(1, 13) if months is None else months
    days = range(1, 32) if days is None else days
    chunk_size = 100_000 if projection_chunk_size is None else int(projection_chunk_size)
    cloud_threshold = (
        0.0 if cloud_fraction_threshold is None else float(cloud_fraction_threshold)
    )
    overwrite = False if overwrite is None else bool(overwrite)
    for year in years:
        for month in months:
            for day in days:
                input_day = _day(indir_data, year, month, day)
                if not input_day.is_dir():
                    continue
                output_day = _day(outdir_project, year, month, day)
                inputs = sorted(input_day.rglob("*.tif"))
                if not inputs:
                    inputs = sorted(input_day.rglob("*.npz"))
                for index, input_path in enumerate(inputs):
                    output_path = (output_day / input_path.relative_to(input_day)).with_suffix(
                        ".tif" if input_path.suffix.lower() != ".npz" else ".npz"
                    )
                    if output_path.exists() and not overwrite:
                        continue
                    print(
                        f"[{year:04d}-{month:02d}-{day:02d}] "
                        f"{index + 1}/{len(inputs)} 投影 {input_path.name}"
                    )
                    item = read_data_product(input_path, spec, product_type)
                    projected = project_observation(
                        item, target_grid_file, chunk_size, cloud_threshold
                    )
                    write_data_product(output_path, projected, spec)


def resolve_paths(value, sensor: str) -> list[Path]:
    if isinstance(value, (str, Path)):
        source = Path(value)
        paths = sorted(source.rglob("*.tif")) if source.is_dir() else [source]
        if source.is_dir() and not paths:
            paths = sorted(source.rglob("*.npz"))
    else:
        paths = [Path(path) for path in value]
    paths = [path for path in paths if path.is_file()]
    if not paths:
        raise FileNotFoundError(f"{sensor} stage has no input data files")
    return paths


def combine_data_products(
    input_paths,
    spec: DualThermalSensorSpec,
    product_type: type[ProductType],
    bounds=None,
) -> ProductType:
    paths = resolve_paths(input_paths, spec.name)
    item = mosaic_observations(
        [read_data_product(path, spec, product_type) for path in paths],
        primary_field="bt1_k",
    )
    if bounds is not None:
        item = crop_observation(item, tuple(bounds))
    return item


def merge_sensor_data(
    input_paths,
    output_path,
    spec: DualThermalSensorSpec,
    product_type: type[ProductType],
    bounds=None,
) -> None:
    require_parameters(input_paths=input_paths, output_path=output_path)
    write_data_product(
        output_path,
        combine_data_products(input_paths, spec, product_type, bounds),
        spec,
    )


def merge_sensor_results(input_paths, output_path, spec: DualThermalSensorSpec, bounds=None) -> None:
    require_parameters(input_paths=input_paths, output_path=output_path)
    paths = resolve_paths(input_paths, spec.name)
    products = [
        read_temperature_product(path)
        if path.suffix.lower() in {".tif", ".tiff"}
        else read_product(path)
        for path in paths
    ]
    product = mosaic_temperature_products(products)
    if product.metadata.sensor.upper() != spec.name.upper():
        raise ValueError(f"result product sensor does not match {spec.name}")
    if bounds is not None:
        product = crop_temperature_product(product, tuple(bounds))
    write_temperature_product(output_path, product)


def retrieve_sensor_lst(
    item: DualThermalDataProduct,
    spec: DualThermalSensorSpec,
    coefficient_file,
) -> SplitWindowResult:
    require_parameters(coefficient_file=coefficient_file)
    if item.sensor.upper() != spec.name.upper():
        raise ValueError(f"cannot retrieve {item.sensor} with the {spec.name} algorithm")
    item.validate(require_lst_auxiliary=True)
    observation = DualChannelObservation(
        item.bt1_k,
        item.bt2_k,
        item.soil_emissivity_1,
        item.soil_emissivity_2,
        item.vegetation_emissivity_1,
        item.vegetation_emissivity_2,
        item.lai,
        item.tcwv_cm,
        item.view_zenith_deg,
        item.cloud_mask,
    )
    return retrieve_dual_channel_lst(
        observation, load_split_window_model(coefficient_file)
    )


def produce_sensor_lst(
    input_path,
    output_path,
    spec: DualThermalSensorSpec,
    product_type: type[ProductType],
    coefficient_file,
    auxiliary_file,
    grid_id=None,
    algorithm_version=None,
    uncertainty_k=None,
) -> None:
    require_parameters(coefficient_file=coefficient_file, auxiliary_file=auxiliary_file)
    item = read_data_product(input_path, spec, product_type)
    if not item.has_lst_auxiliary:
        item = add_lst_auxiliary(item, auxiliary_file)
    uncertainty_k = 1.0 if uncertainty_k is None else float(uncertainty_k)
    if uncertainty_k <= 0:
        raise ValueError("uncertainty_k must be positive")
    result = retrieve_sensor_lst(item, spec, coefficient_file)
    metadata = ProductMetadata(
        ProductLevel.L2LST,
        spec.name.upper(),
        item.start_time,
        item.end_time,
        spec.native_grid_id if grid_id is None else str(grid_id),
        spec.algorithm_version if algorithm_version is None else str(algorithm_version),
        source_products=tuple(
            dict.fromkeys(
                source
                for source in (
                    item.source_product,
                    str(input_path),
                    str(coefficient_file),
                    item.auxiliary_source,
                )
                if source
            )
        ),
        attributes={
            "temperature_variable_names": ["lst"],
            "unit": "K",
            "thermal_channels": list(spec.channels),
        },
    )
    product = TemperatureProduct(
        metadata,
        {
            "lst": result.temperature_k,
            "latitude_deg": item.latitude_deg,
            "longitude_deg": item.longitude_deg,
        },
        result.quality_flag,
        {"lst": np.full(item.shape, uncertainty_k, dtype=float)},
    )
    write_temperature_product(output_path, product)


def retrieve_sensor_years(
    spec: DualThermalSensorSpec,
    product_type: type[ProductType],
    *,
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
    require_parameters(
        indir_data=indir_data,
        outdir_lst=outdir_lst,
        coefficient_file=coefficient_file,
        auxiliary_file=auxiliary_file,
        years=years,
    )
    months = range(1, 13) if months is None else months
    days = range(1, 32) if days is None else days
    overwrite = False if overwrite is None else bool(overwrite)
    for year in years:
        for month in months:
            for day in days:
                input_day = _day(indir_data, year, month, day)
                if not input_day.is_dir():
                    continue
                output_day = _day(outdir_lst, year, month, day)
                inputs = sorted(input_day.rglob("*.tif"))
                if not inputs:
                    inputs = sorted(input_day.rglob("*.npz"))
                for index, input_path in enumerate(inputs):
                    relative = input_path.relative_to(input_day)
                    output_path = (output_day / relative).with_name(
                        relative.stem + ("_lst.tif" if input_path.suffix.lower() != ".npz" else "_lst.npz")
                    )
                    if output_path.exists() and not overwrite:
                        continue
                    print(
                        f"[{year:04d}-{month:02d}-{day:02d}] "
                        f"{index + 1}/{len(inputs)} 反演 {input_path.name}"
                    )
                    produce_sensor_lst(
                        input_path,
                        output_path,
                        spec,
                        product_type,
                        coefficient_file,
                        auxiliary_file,
                        grid_id,
                        algorithm_version,
                        uncertainty_k,
                    )
