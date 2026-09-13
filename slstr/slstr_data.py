"""SLSTR data preparation, with independent stage APIs.

This module contains only SLSTR data-product responsibilities. It does not
perform temperature retrieval. SLSTR intermediate and result products are
stored as named-band GeoTIFF files.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
import stat
import tempfile
from zipfile import ZipFile, ZipInfo

import numpy as np

EXTRACT_SCHEMA = "ls4t.slstr-extract/v1"
SCHEMA = "ls4t.slstr-data/v1"
TEMPERATURE_SCHEMA = "ls4t.slstr-temperature/v1"
LSCT_INPUT_SCHEMA = "ls4t.slstr-lsct-input/v1"
EXTRACT_FIELD_FILES = {
    "bt8_k": "bt8.tif",
    "bt9_k": "bt9.tif",
    "view_zenith_tie_deg": "vza.tif",
    "latitude_native_deg": "lat.tif",
    "longitude_native_deg": "lon.tif",
    "cloud_native": "cloud.tif",
}
DATA_BAND_NAMES = {
    "bt8_k": "bt8",
    "bt9_k": "bt9",
    "view_zenith_deg": "vza",
    "latitude_deg": "lat",
    "longitude_deg": "lon",
    "cloud_mask": "cloud",
}
DATA_BAND_FIELDS = {value: key for key, value in DATA_BAND_NAMES.items()}
LST_AUXILIARY_FIELDS = (
    "soil_emissivity_s8",
    "soil_emissivity_s9",
    "vegetation_emissivity_s8",
    "vegetation_emissivity_s9",
    "lai",
    "tcwv_cm",
)


@dataclass(frozen=True)
class SlstrExtractedProduct:
    """Native arrays read from one SLSTR view before tie-point reconstruction."""

    source_product: str
    view: str
    start_time: str | None
    end_time: str | None
    bt8_k: np.ndarray
    bt9_k: np.ndarray
    view_zenith_tie_deg: np.ndarray
    latitude_native_deg: np.ndarray
    longitude_native_deg: np.ndarray
    cloud_native: np.ndarray

    def validate(self) -> None:
        if self.view not in {"nadir", "oblique"}:
            raise ValueError("SLSTR view must be 'nadir' or 'oblique'")
        if np.asarray(self.bt8_k).ndim != 2:
            raise ValueError("SLSTR brightness temperature must be two-dimensional")
        if np.asarray(self.bt8_k).shape != np.asarray(self.bt9_k).shape:
            raise ValueError("SLSTR S8 and S9 arrays must share a shape")
        for name in (
            "view_zenith_tie_deg",
            "latitude_native_deg",
            "longitude_native_deg",
            "cloud_native",
        ):
            if np.asarray(getattr(self, name)).ndim != 2:
                raise ValueError(f"{name} must be two-dimensional")


@dataclass(frozen=True)
class SlstrDataProduct:
    """Decoded SLSTR observation and optional LST auxiliary fields."""

    source_product: str
    view: str
    start_time: str | None
    end_time: str | None
    bt8_k: np.ndarray
    bt9_k: np.ndarray
    view_zenith_deg: np.ndarray
    latitude_deg: np.ndarray
    longitude_deg: np.ndarray
    cloud_mask: np.ndarray
    soil_emissivity_s8: np.ndarray | None = None
    soil_emissivity_s9: np.ndarray | None = None
    vegetation_emissivity_s8: np.ndarray | None = None
    vegetation_emissivity_s9: np.ndarray | None = None
    lai: np.ndarray | None = None
    tcwv_cm: np.ndarray | None = None
    auxiliary_source: str | None = None

    @property
    def shape(self) -> tuple[int, ...]:
        return np.asarray(self.bt8_k).shape

    @property
    def has_lst_auxiliary(self) -> bool:
        return all(getattr(self, name) is not None for name in LST_AUXILIARY_FIELDS)

    def validate(self, *, require_lst_auxiliary: bool = False) -> None:
        if self.view not in {"nadir", "oblique"}:
            raise ValueError("SLSTR view must be 'nadir' or 'oblique'")
        if len(self.shape) != 2:
            raise ValueError("SLSTR data arrays must be two-dimensional")
        for name in (
            "bt9_k",
            "view_zenith_deg",
            "latitude_deg",
            "longitude_deg",
            "cloud_mask",
        ):
            shape = np.asarray(getattr(self, name)).shape
            if shape != self.shape:
                raise ValueError(f"{name} shape {shape} does not match {self.shape}")
        for name in ("bt8_k", "bt9_k"):
            value = np.asarray(getattr(self, name), dtype=float)
            finite = value[np.isfinite(value)]
            if finite.size and (finite.min() < 100.0 or finite.max() > 400.0):
                raise ValueError(f"{name} must contain decoded kelvin values")

        present = [name for name in LST_AUXILIARY_FIELDS if getattr(self, name) is not None]
        if present and len(present) != len(LST_AUXILIARY_FIELDS):
            missing = sorted(set(LST_AUXILIARY_FIELDS) - set(present))
            raise ValueError(f"incomplete SLSTR LST auxiliary fields: {', '.join(missing)}")
        if require_lst_auxiliary and not self.has_lst_auxiliary:
            raise ValueError("SLSTR-DATA product has no LST auxiliary fields; run add-aux first")
        if self.has_lst_auxiliary:
            for name in LST_AUXILIARY_FIELDS:
                shape = np.asarray(getattr(self, name)).shape
                if shape != self.shape:
                    raise ValueError(f"{name} shape {shape} does not match {self.shape}")
            for name in LST_AUXILIARY_FIELDS[:4]:
                value = np.asarray(getattr(self, name), dtype=float)
                if np.any(np.isfinite(value) & ((value <= 0.0) | (value > 1.0))):
                    raise ValueError(f"{name} must be in (0, 1]")
            tcwv = np.asarray(self.tcwv_cm, dtype=float)
            if np.any(np.isfinite(tcwv) & (tcwv < 0.0)):
                raise ValueError("tcwv_cm cannot be negative")


def _safe_archive_target(root: Path, member: ZipInfo) -> Path:
    name = PurePosixPath(member.filename)
    windows_name = PureWindowsPath(member.filename)
    if name.is_absolute() or windows_name.drive or windows_name.root or ".." in name.parts:
        raise ValueError(f"unsafe archive member: {member.filename!r}")
    if stat.S_ISLNK(member.external_attr >> 16):
        raise ValueError(f"archive symbolic link is not allowed: {member.filename!r}")
    target = (root / Path(*name.parts)).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"unsafe archive member: {member.filename!r}") from error
    return target


def unpack_archive(archive: str | Path, output_directory: str | Path) -> Path:
    """Unpack one SLSTR archive without overwriting an existing directory."""

    source = Path(archive)
    destination = Path(output_directory)
    if not source.is_file():
        raise FileNotFoundError(f"SLSTR archive does not exist: {source}")
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"unpack destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    with ZipFile(source) as bundle:
        members = bundle.infolist()
        targets = [_safe_archive_target(destination, member) for member in members]
        for member, target in zip(members, targets, strict=True):
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(member) as input_stream, target.open("xb") as output_stream:
                shutil.copyfileobj(input_stream, output_stream)

    products = sorted(path for path in destination.rglob("*.SEN3") if path.is_dir())
    if len(products) > 1:
        raise ValueError(f"archive contains multiple SEN3 products: {source}")
    return products[0] if products else destination


def _read_netcdf(path: Path, variable_name: str) -> np.ndarray:
    try:
        from netCDF4 import Dataset
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "reading native SLSTR data requires netCDF4; install with 'pip install -e .[slstr]'"
        ) from error
    if not path.is_file():
        raise FileNotFoundError(f"required SLSTR file is missing: {path}")
    with Dataset(path) as dataset:
        if variable_name not in dataset.variables:
            raise KeyError(f"{variable_name!r} is missing from {path.name}")
        value = dataset.variables[variable_name][:]
    if np.ma.isMaskedArray(value):
        return np.asarray(value.filled(np.nan))
    return np.asarray(value)


def _resize_nearest(value: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    source = np.asarray(value)
    if source.shape == shape:
        return source
    if source.ndim != 2:
        raise ValueError(f"cannot align non-2D SLSTR field with shape {source.shape}")
    rows = np.rint(np.linspace(0, source.shape[0] - 1, shape[0])).astype(int)
    columns = np.rint(np.linspace(0, source.shape[1] - 1, shape[1])).astype(int)
    return source[np.ix_(rows, columns)]


def _utc_timestamp(value: str) -> str:
    parsed = datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def _coverage_from_name(name: str) -> tuple[str | None, str | None]:
    values = re.findall(r"\d{8}T\d{6}", name)
    if len(values) < 2:
        return None, None
    return _utc_timestamp(values[0]), _utc_timestamp(values[1])


def extract_native_product(
    product_directory: str | Path,
    *,
    view: str = "nadir",
) -> SlstrExtractedProduct:
    """Read native SLSTR arrays without reconstructing them to one grid."""

    product = Path(product_directory)
    if view not in {"nadir", "oblique"}:
        raise ValueError("SLSTR view must be 'nadir' or 'oblique'")
    if not product.is_dir():
        raise NotADirectoryError(f"SLSTR product directory does not exist: {product}")

    image_suffix = "in" if view == "nadir" else "io"
    tie_suffix = "tn" if view == "nadir" else "to"
    bt8 = _read_netcdf(product / f"S8_BT_{image_suffix}.nc", f"S8_BT_{image_suffix}").astype(float)
    bt9 = _read_netcdf(product / f"S9_BT_{image_suffix}.nc", f"S9_BT_{image_suffix}").astype(float)
    if bt8.shape != bt9.shape:
        raise ValueError(f"SLSTR S8/S9 shapes differ: {bt8.shape} and {bt9.shape}")
    latitude = _read_netcdf(
        product / f"geodetic_{image_suffix}.nc", f"latitude_{image_suffix}"
    ).astype(float)
    longitude = _read_netcdf(
        product / f"geodetic_{image_suffix}.nc", f"longitude_{image_suffix}"
    ).astype(float)
    view_zenith = _read_netcdf(
        product / f"geometry_{tie_suffix}.nc", f"sat_zenith_{tie_suffix}"
    ).astype(float)
    cloud_flags = _read_netcdf(
        product / f"flags_{image_suffix}.nc", f"cloud_{image_suffix}"
    )
    start_time, end_time = _coverage_from_name(product.name)
    result = SlstrExtractedProduct(
        source_product=str(product),
        view=view,
        start_time=start_time,
        end_time=end_time,
        bt8_k=bt8,
        bt9_k=bt9,
        view_zenith_tie_deg=view_zenith,
        latitude_native_deg=latitude,
        longitude_native_deg=longitude,
        cloud_native=cloud_flags,
    )
    result.validate()
    return result


def reconstruct_product(item: SlstrExtractedProduct) -> SlstrDataProduct:
    """Align geolocation, cloud and tie-point geometry to the thermal grid."""

    item.validate()
    shape = np.asarray(item.bt8_k).shape
    result = SlstrDataProduct(
        source_product=item.source_product,
        view=item.view,
        start_time=item.start_time,
        end_time=item.end_time,
        bt8_k=np.asarray(item.bt8_k, dtype=float),
        bt9_k=np.asarray(item.bt9_k, dtype=float),
        view_zenith_deg=_resize_nearest(item.view_zenith_tie_deg, shape).astype(float),
        latitude_deg=_resize_nearest(item.latitude_native_deg, shape).astype(float),
        longitude_deg=_resize_nearest(item.longitude_native_deg, shape).astype(float),
        cloud_mask=_resize_nearest(item.cloud_native, shape) != 0,
    )
    result.validate()
    return result


def read_native_product(product_directory: str | Path, *, view: str = "nadir") -> SlstrDataProduct:
    """Compatibility helper for one product; batch jobs use separate stages."""

    return reconstruct_product(extract_native_product(product_directory, view=view))


def add_lst_auxiliary(item: SlstrDataProduct, auxiliary_file: str | Path) -> SlstrDataProduct:
    """Attach grid-aligned emissivity, LAI and TCWV arrays to SLSTR-DATA."""

    auxiliary = read_auxiliary_product(auxiliary_file, item.shape)
    fields = {
        name: np.broadcast_to(np.asarray(auxiliary[name], dtype=float), item.shape).copy()
        for name in LST_AUXILIARY_FIELDS
    }
    result = replace(item, **fields, auxiliary_source=str(auxiliary_file))
    result.validate(require_lst_auxiliary=True)
    return result


def _gdal():
    try:
        from osgeo import gdal
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "SLSTR GeoTIFF I/O requires GDAL; install the GDAL Python bindings"
        ) from error
    gdal.UseExceptions()
    return gdal


def _write_tiff(
    path: str | Path,
    fields: dict[str, np.ndarray],
    metadata: dict[str, str],
    reference_path: str | Path | None = None,
) -> None:
    gdal = _gdal()
    destination = Path(path)
    if destination.suffix.lower() not in {".tif", ".tiff"}:
        raise ValueError(f"SLSTR raster output must be GeoTIFF: {destination}")
    if not fields:
        raise ValueError("GeoTIFF must contain at least one field")
    arrays = {name: np.asarray(value) for name, value in fields.items()}
    shape = next(iter(arrays.values())).shape
    if any(value.ndim != 2 or value.shape != shape for value in arrays.values()):
        raise ValueError("all GeoTIFF fields must be matching two-dimensional arrays")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{destination.name}.", suffix=".tif", dir=destination.parent, delete=False
    ) as temporary_file:
        temporary = Path(temporary_file.name)
    temporary.unlink(missing_ok=True)
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(
        str(temporary),
        int(shape[1]),
        int(shape[0]),
        len(arrays),
        gdal.GDT_Float32,
        options=["COMPRESS=DEFLATE"],
    )
    if dataset is None:
        raise RuntimeError(f"cannot create GeoTIFF: {destination}")
    try:
        if reference_path is not None:
            reference = gdal.Open(str(reference_path), gdal.GA_ReadOnly)
            if reference is None:
                raise FileNotFoundError(f"cannot open GeoTIFF reference: {reference_path}")
            try:
                transform = reference.GetGeoTransform()
                projection = reference.GetProjection()
            finally:
                reference = None
            if transform:
                dataset.SetGeoTransform(transform)
            if projection:
                dataset.SetProjection(projection)
        for index, (name, value) in enumerate(arrays.items(), start=1):
            band = dataset.GetRasterBand(index)
            band.WriteArray(np.asarray(value, dtype=np.float32))
            band.SetDescription(name)
            band.SetMetadataItem("LS4T_FIELD", name)
        for key, value in metadata.items():
            dataset.SetMetadataItem(str(key), str(value))
        dataset.FlushCache()
    finally:
        dataset = None
    try:
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _read_tiff(
    path: str | Path,
    default_field: str | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    gdal = _gdal()
    source = Path(path)
    if source.suffix.lower() not in {".tif", ".tiff"} or not source.is_file():
        raise FileNotFoundError(f"SLSTR GeoTIFF does not exist: {source}")
    dataset = gdal.Open(str(source), gdal.GA_ReadOnly)
    if dataset is None:
        raise ValueError(f"cannot open SLSTR GeoTIFF: {source}")
    try:
        fields = {}
        for index in range(1, dataset.RasterCount + 1):
            band = dataset.GetRasterBand(index)
            name = band.GetDescription() or band.GetMetadataItem("LS4T_FIELD")
            if not name and dataset.RasterCount == 1:
                name = default_field
            if not name:
                raise ValueError(f"GeoTIFF band {index} has no LS4T field name: {source}")
            fields[name] = np.asarray(band.ReadAsArray()).copy()
        metadata = dataset.GetMetadata_Dict()
    finally:
        dataset = None
    return fields, metadata


def _metadata(schema: str, **values: object) -> dict[str, str]:
    return {
        "LS4T_SCHEMA": schema,
        "LS4T_METADATA": json.dumps(values, ensure_ascii=False, sort_keys=True),
    }


def write_auxiliary_product(
    path: str | Path,
    fields: dict[str, np.ndarray],
) -> None:
    """Write the six LST auxiliary fields as a named-band GeoTIFF."""

    missing = [name for name in LST_AUXILIARY_FIELDS if name not in fields]
    if missing:
        raise KeyError(f"auxiliary GeoTIFF is missing: {', '.join(missing)}")
    arrays = {name: np.asarray(fields[name], dtype=float) for name in LST_AUXILIARY_FIELDS}
    _write_tiff(path, arrays, _metadata("ls4t.slstr-auxiliary/v1", fields=list(arrays)))


def read_auxiliary_product(
    path: str | Path,
    shape: tuple[int, int] | None = None,
) -> dict[str, np.ndarray]:
    """Read named LST auxiliary fields from a GeoTIFF."""

    source = Path(path)
    if source.is_dir():
        fields = {}
        for name in LST_AUXILIARY_FIELDS:
            fields_path = source / f"{name}.tif"
            single, _ = _read_tiff(fields_path)
            if name in single:
                fields[name] = single[name]
            elif len(single) == 1:
                fields[name] = next(iter(single.values()))
            else:
                raise KeyError(f"auxiliary GeoTIFF is missing field {name}: {fields_path}")
    else:
        fields, metadata = _read_tiff(source)
        if metadata.get("LS4T_SCHEMA") != "ls4t.slstr-auxiliary/v1":
            raise ValueError(f"not an SLSTR auxiliary GeoTIFF: {path}")
        missing = [name for name in LST_AUXILIARY_FIELDS if name not in fields]
        if missing:
            raise KeyError(f"auxiliary GeoTIFF is missing: {', '.join(missing)}")
    result = {name: np.asarray(fields[name], dtype=float) for name in LST_AUXILIARY_FIELDS}
    if shape is not None and any(value.shape != shape for value in result.values()):
        raise ValueError("auxiliary GeoTIFF fields do not match the SLSTR thermal grid")
    return result


def write_lsct_input(
    path: str | Path,
    observed_radiance: np.ndarray,
    effective_weights: np.ndarray,
    *,
    observation_uncertainty: np.ndarray | None = None,
    latitude_deg: np.ndarray | None = None,
    longitude_deg: np.ndarray | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    """Write multidimensional LSCT input as a named-band GeoTIFF."""

    observed = np.asarray(observed_radiance, dtype=float)
    weights = np.asarray(effective_weights, dtype=float)
    if observed.ndim != 3 or weights.ndim != 4 or weights.shape[:-1] != observed.shape:
        raise ValueError(
            "LSCT input requires radiance (row, col, observation) and weights "
            "(row, col, observation, component)"
        )
    fields = {
        **{
            f"observed_radiance__{index}": observed[..., index]
            for index in range(observed.shape[-1])
        },
        **{
            f"effective_weights__{observation}__{component}": weights[..., observation, component]
            for observation in range(weights.shape[-2])
            for component in range(weights.shape[-1])
        },
    }
    if observation_uncertainty is not None:
        uncertainty = np.broadcast_to(np.asarray(observation_uncertainty, dtype=float), observed.shape)
        fields.update(
            {
                f"observation_uncertainty__{index}": uncertainty[..., index]
                for index in range(observed.shape[-1])
            }
        )
    for name, value in (("latitude_deg", latitude_deg), ("longitude_deg", longitude_deg)):
        if value is not None:
            array = np.asarray(value, dtype=float)
            if array.shape != observed.shape[:2]:
                raise ValueError(f"{name} shape must match LSCT spatial grid")
            fields[name] = array
    values = dict(metadata or {})
    values["observed_shape"] = list(observed.shape)
    values["weights_shape"] = list(weights.shape)
    _write_tiff(path, fields, _metadata(LSCT_INPUT_SCHEMA, **values))


def read_lsct_input(path: str | Path) -> dict[str, np.ndarray | dict[str, object]]:
    """Read named-band multidimensional LSCT input from GeoTIFF."""

    fields, metadata = _read_tiff(path)
    if metadata.get("LS4T_SCHEMA") != LSCT_INPUT_SCHEMA:
        raise ValueError(f"not an SLSTR LSCT input GeoTIFF: {path}")

    values = json.loads(metadata["LS4T_METADATA"])
    observed_shape = tuple(values["observed_shape"])
    weights_shape = tuple(values["weights_shape"])

    def stack(prefix: str, shape: tuple[int, ...]) -> np.ndarray:
        result = np.empty(shape, dtype=float)
        for index in np.ndindex(shape[2:]):
            name = prefix + "__" + "__".join(str(value) for value in index)
            if name not in fields:
                raise ValueError(f"LSCT input is missing field {name}")
            result[(slice(None), slice(None), *index)] = fields[name]
        return result

    result: dict[str, np.ndarray | dict[str, object]] = {
        "observed_radiance": stack("observed_radiance", observed_shape),
        "effective_weights": stack("effective_weights", weights_shape),
        "metadata": values,
    }
    if any(name.startswith("observation_uncertainty__") for name in fields):
        result["observation_uncertainty"] = stack("observation_uncertainty", observed_shape)
    for name in ("latitude_deg", "longitude_deg"):
        if name in fields:
            result[name] = np.asarray(fields[name], dtype=float)
    return result


def write_extracted_product(path: str | Path, item: SlstrExtractedProduct) -> None:
    """Store extraction fields as individual GeoTIFF files in one view directory."""

    item.validate()
    destination = Path(path)
    destination.mkdir(parents=True, exist_ok=True)
    metadata = _metadata(
        EXTRACT_SCHEMA,
        sensor="SLSTR",
        view=item.view,
        source_product=item.source_product,
        start_time=item.start_time,
        end_time=item.end_time,
    )
    for name, value in {
        "bt8_k": item.bt8_k,
        "bt9_k": item.bt9_k,
        "view_zenith_tie_deg": item.view_zenith_tie_deg,
        "latitude_native_deg": item.latitude_native_deg,
        "longitude_native_deg": item.longitude_native_deg,
        "cloud_native": item.cloud_native,
    }.items():
        _write_tiff(destination / EXTRACT_FIELD_FILES[name], {name: value}, metadata)


def read_extracted_product(path: str | Path) -> SlstrExtractedProduct:
    """Load one extraction-stage view directory."""

    source = Path(path)
    required = (
        "bt8_k",
        "bt9_k",
        "view_zenith_tie_deg",
        "latitude_native_deg",
        "longitude_native_deg",
        "cloud_native",
    )
    arrays = {}
    metadata = None
    for name in required:
        fields, current_metadata = _read_tiff(
            source / EXTRACT_FIELD_FILES[name], default_field=name
        )
        if name not in fields:
            raise ValueError(f"GeoTIFF is missing field {name}: {source}")
        arrays[name] = fields[name]
        metadata = current_metadata if metadata is None else metadata
    if metadata and metadata.get("LS4T_SCHEMA") == EXTRACT_SCHEMA:
        values = json.loads(metadata["LS4T_METADATA"])
    else:
        view = source.name if source.name in {"nadir", "oblique"} else "nadir"
        product_name = source.parent.name if source.name in {"nadir", "oblique"} else source.name
        start_time, end_time = _coverage_from_name(product_name)
        values = {
            "source_product": product_name,
            "view": view,
            "start_time": start_time,
            "end_time": end_time,
        }
    item = SlstrExtractedProduct(
        source_product=values["source_product"],
        view=values["view"],
        start_time=values.get("start_time"),
        end_time=values.get("end_time"),
        bt8_k=arrays["bt8_k"],
        bt9_k=arrays["bt9_k"],
        view_zenith_tie_deg=arrays["view_zenith_tie_deg"],
        latitude_native_deg=arrays["latitude_native_deg"],
        longitude_native_deg=arrays["longitude_native_deg"],
        cloud_native=arrays["cloud_native"],
    )
    item.validate()
    return item


def write_data_product(
    path: str | Path,
    item: SlstrDataProduct,
    *,
    reference_path: str | Path | None = None,
) -> None:
    """Store an SLSTR-DATA product as a named-band GeoTIFF."""

    item.validate()
    fields = {
        DATA_BAND_NAMES[name]: np.asarray(getattr(item, name))
        for name in (
            "bt8_k",
            "bt9_k",
            "view_zenith_deg",
            "latitude_deg",
            "longitude_deg",
            "cloud_mask",
        )
    }
    for name in LST_AUXILIARY_FIELDS:
        value = getattr(item, name)
        if value is not None:
            fields[name] = np.asarray(value)
    _write_tiff(
        path,
        fields,
        _metadata(
            SCHEMA,
            sensor="SLSTR",
            view=item.view,
            source_product=item.source_product,
            start_time=item.start_time,
            end_time=item.end_time,
            auxiliary_source=item.auxiliary_source,
            units={"bt8_k": "K", "bt9_k": "K", "view_zenith_deg": "degree", "tcwv_cm": "cm"},
        ),
        reference_path=reference_path,
    )


def read_data_product(path: str | Path) -> SlstrDataProduct:
    """Load and validate an SLSTR-DATA GeoTIFF."""

    fields, metadata = _read_tiff(path)
    if metadata.get("LS4T_SCHEMA") != SCHEMA:
        raise ValueError(f"not an SLSTR-DATA GeoTIFF: {path}")
    required = ("bt8_k", "bt9_k", "view_zenith_deg", "latitude_deg", "longitude_deg", "cloud_mask")
    canonical_fields = {
        DATA_BAND_FIELDS.get(name, name): value for name, value in fields.items()
    }
    missing = [name for name in required if name not in canonical_fields]
    if missing:
        raise ValueError(f"SLSTR-DATA GeoTIFF is missing: {', '.join(missing)}")
    values = json.loads(metadata["LS4T_METADATA"])
    optional = {
        name: np.asarray(canonical_fields[name]).copy() if name in canonical_fields else None
        for name in LST_AUXILIARY_FIELDS
    }
    item = SlstrDataProduct(
        source_product=values["source_product"],
        view=values["view"],
        start_time=values.get("start_time"),
        end_time=values.get("end_time"),
        bt8_k=np.asarray(canonical_fields["bt8_k"], dtype=float),
        bt9_k=np.asarray(canonical_fields["bt9_k"], dtype=float),
        view_zenith_deg=np.asarray(canonical_fields["view_zenith_deg"], dtype=float),
        latitude_deg=np.asarray(canonical_fields["latitude_deg"], dtype=float),
        longitude_deg=np.asarray(canonical_fields["longitude_deg"], dtype=float),
        cloud_mask=np.asarray(canonical_fields["cloud_mask"], dtype=bool),
        auxiliary_source=values.get("auxiliary_source"),
        **optional,
    )
    item.validate()
    return item


def write_lst_product(
    path: str | Path,
    product,
    *,
    reference_path: str | Path | None = None,
) -> None:
    """Store an SLSTR LST product as a named-band GeoTIFF."""

    product.validate()
    fields = {
        f"variable__{name}": np.asarray(value)
        for name, value in product.variables.items()
    }
    fields["quality_flag"] = np.asarray(product.quality_flag)
    fields.update(
        {
            f"uncertainty__{name}": np.asarray(value)
            for name, value in product.uncertainty.items()
        }
    )
    _write_tiff(
        path,
        fields,
        _metadata(TEMPERATURE_SCHEMA, product_metadata=product.metadata.to_dict()),
        reference_path=reference_path,
    )


def read_lst_product(path: str | Path):
    """Load an SLSTR L2LST GeoTIFF."""

    from base.product import ProductMetadata, TemperatureProduct

    fields, metadata = _read_tiff(path)
    if metadata.get("LS4T_SCHEMA") != TEMPERATURE_SCHEMA:
        raise ValueError(f"not an SLSTR temperature GeoTIFF: {path}")
    if "quality_flag" not in fields:
        raise ValueError(f"SLSTR L2LST GeoTIFF has no quality_flag: {path}")
    product_metadata = ProductMetadata.from_dict(
        json.loads(metadata["LS4T_METADATA"])["product_metadata"]
    )
    variables = {
        name.removeprefix("variable__"): np.asarray(value, dtype=float)
        for name, value in fields.items()
        if name.startswith("variable__")
    }
    uncertainty = {
        name.removeprefix("uncertainty__"): np.asarray(value, dtype=float)
        for name, value in fields.items()
        if name.startswith("uncertainty__")
    }
    product = TemperatureProduct(
        product_metadata,
        variables,
        np.asarray(fields["quality_flag"], dtype=np.uint16),
        uncertainty,
    )
    product.validate()
    return product


def describe_data_product(item: SlstrDataProduct) -> dict[str, object]:
    """Return a concise status record for command-line inspection."""

    item.validate()
    return {
        "product": "SLSTR-DATA",
        "source_product": item.source_product,
        "view": item.view,
        "shape": list(item.shape),
        "start_time": item.start_time,
        "end_time": item.end_time,
        "has_lst_auxiliary": item.has_lst_auxiliary,
        "auxiliary_source": item.auxiliary_source,
    }


def slstr_unzip(
    indir_zip=None,
    outdir_raw=None,
    years=None,
    overwrite=None,
    start_index=None,
) -> None:
    """Compatibility wrapper for :mod:`slstr.slstr_unzip`."""

    from slstr.slstr_unzip import slstr_unzip as run_stage

    return run_stage(indir_zip, outdir_raw, years, overwrite, start_index)


def slstr_extract(
    indir_raw=None,
    outdir_extract=None,
    years=None,
    views=None,
    overwrite=None,
) -> None:
    """Compatibility wrapper for :mod:`slstr.slstr_extract`."""

    from slstr.slstr_extract import slstr_extract as run_stage

    return run_stage(indir_raw, outdir_extract, years, views, overwrite)


def slstr_reconstruct(
    indir_extract=None,
    outdir_reconstruct=None,
    years=None,
    overwrite=None,
) -> None:
    """Compatibility wrapper for :mod:`slstr.slstr_reconstruct`."""

    from slstr.slstr_reconstruct import slstr_reconstruct as run_stage

    return run_stage(indir_extract, outdir_reconstruct, years, overwrite)


def slstr_project(
    indir_reconstruct=None,
    outdir_project=None,
    target_grid_file=None,
    years=None,
    projection_chunk_size=None,
    cloud_fraction_threshold=None,
    overwrite=None,
) -> None:
    """Compatibility wrapper for :mod:`slstr.slstr_project`."""

    from slstr.slstr_project import slstr_project as run_stage

    return run_stage(
        indir_reconstruct,
        outdir_project,
        target_grid_file,
        years,
        projection_chunk_size,
        cloud_fraction_threshold,
        overwrite,
    )


def slstr_merge(
    indir_project=None,
    outdir_merge=None,
    years=None,
    overwrite=None,
) -> None:
    """Compatibility wrapper for :mod:`slstr.slstr_merge`."""

    from slstr.slstr_merge import slstr_merge as run_stage

    return run_stage(indir_project, outdir_merge, years, overwrite)
