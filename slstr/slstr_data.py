"""SLSTR data preparation, with independent stage APIs.

This module contains only SLSTR data-product responsibilities.  It does not
perform temperature retrieval.  The stored NPZ is the explicit boundary
between ``slstr-data`` and downstream products such as ``slstr-lst``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
from zipfile import ZipFile, ZipInfo

import numpy as np

EXTRACT_SCHEMA = "ls4t.slstr-extract/v1"
SCHEMA = "ls4t.slstr-data/v1"
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
    if name.is_absolute() or ".." in name.parts:
        raise ValueError(f"unsafe archive member: {member.filename!r}")
    if stat.S_ISLNK(member.external_attr >> 16):
        raise ValueError(f"archive symbolic link is not allowed: {member.filename!r}")
    return root.joinpath(*name.parts)


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

    with np.load(auxiliary_file, allow_pickle=False) as auxiliary:
        missing = [name for name in LST_AUXILIARY_FIELDS if name not in auxiliary.files]
        if missing:
            raise KeyError(f"auxiliary NPZ is missing: {', '.join(missing)}")
        fields = {
            name: np.broadcast_to(np.asarray(auxiliary[name], dtype=float), item.shape).copy()
            for name in LST_AUXILIARY_FIELDS
        }
    result = replace(item, **fields, auxiliary_source=str(auxiliary_file))
    result.validate(require_lst_auxiliary=True)
    return result


def _write_atomic(path: Path, payload: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{path.name}.", suffix=".npz", dir=path.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        np.savez_compressed(temporary_path, **payload)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def write_extracted_product(path: str | Path, item: SlstrExtractedProduct) -> None:
    """Store the output of the extraction stage."""

    item.validate()
    metadata = {
        "schema": EXTRACT_SCHEMA,
        "sensor": "SLSTR",
        "view": item.view,
        "source_product": item.source_product,
        "start_time": item.start_time,
        "end_time": item.end_time,
    }
    _write_atomic(
        Path(path),
        {
            "metadata": np.asarray(json.dumps(metadata, sort_keys=True)),
            "bt8_k": np.asarray(item.bt8_k),
            "bt9_k": np.asarray(item.bt9_k),
            "view_zenith_tie_deg": np.asarray(item.view_zenith_tie_deg),
            "latitude_native_deg": np.asarray(item.latitude_native_deg),
            "longitude_native_deg": np.asarray(item.longitude_native_deg),
            "cloud_native": np.asarray(item.cloud_native),
        },
    )


def read_extracted_product(path: str | Path) -> SlstrExtractedProduct:
    """Load one extraction-stage product."""

    with np.load(path, allow_pickle=False) as source:
        metadata = json.loads(str(source["metadata"].item()))
        if metadata.get("schema") != EXTRACT_SCHEMA:
            raise ValueError(f"not an SLSTR extraction product: {path}")
        item = SlstrExtractedProduct(
            source_product=metadata["source_product"],
            view=metadata["view"],
            start_time=metadata.get("start_time"),
            end_time=metadata.get("end_time"),
            bt8_k=source["bt8_k"].copy(),
            bt9_k=source["bt9_k"].copy(),
            view_zenith_tie_deg=source["view_zenith_tie_deg"].copy(),
            latitude_native_deg=source["latitude_native_deg"].copy(),
            longitude_native_deg=source["longitude_native_deg"].copy(),
            cloud_native=source["cloud_native"].copy(),
        )
    item.validate()
    return item


def write_data_product(path: str | Path, item: SlstrDataProduct) -> None:
    """Store an SLSTR-DATA product as a non-pickle, atomic NPZ file."""

    item.validate()
    metadata = {
        "schema": SCHEMA,
        "sensor": "SLSTR",
        "view": item.view,
        "source_product": item.source_product,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "auxiliary_source": item.auxiliary_source,
        "units": {"bt8_k": "K", "bt9_k": "K", "view_zenith_deg": "degree", "tcwv_cm": "cm"},
    }
    payload = {
        "metadata": np.asarray(json.dumps(metadata, sort_keys=True)),
        **{
            name: np.asarray(getattr(item, name))
            for name in (
                "bt8_k",
                "bt9_k",
                "view_zenith_deg",
                "latitude_deg",
                "longitude_deg",
                "cloud_mask",
            )
        },
    }
    for name in LST_AUXILIARY_FIELDS:
        value = getattr(item, name)
        if value is not None:
            payload[name] = np.asarray(value)
    _write_atomic(Path(path), payload)


def read_data_product(path: str | Path) -> SlstrDataProduct:
    """Load and validate an SLSTR-DATA product."""

    with np.load(path, allow_pickle=False) as source:
        metadata = json.loads(str(source["metadata"].item()))
        if metadata.get("schema") != SCHEMA:
            raise ValueError(f"not an SLSTR-DATA product: {path}")
        optional = {
            name: source[name].copy() if name in source.files else None
            for name in LST_AUXILIARY_FIELDS
        }
        item = SlstrDataProduct(
            source_product=metadata["source_product"],
            view=metadata["view"],
            start_time=metadata.get("start_time"),
            end_time=metadata.get("end_time"),
            bt8_k=source["bt8_k"].copy(),
            bt9_k=source["bt9_k"].copy(),
            view_zenith_deg=source["view_zenith_deg"].copy(),
            latitude_deg=source["latitude_deg"].copy(),
            longitude_deg=source["longitude_deg"].copy(),
            cloud_mask=source["cloud_mask"].copy(),
            auxiliary_source=metadata.get("auxiliary_source"),
            **optional,
        )
    item.validate()
    return item


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
