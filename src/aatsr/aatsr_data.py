"""AATSR data preparation; unzip and extraction are run independently."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

import numpy as np


# ============================================================================
# 手动运行参数
# ============================================================================

AATSR_ZIP_ROOT = Path("/home/hero/data/ls4t/aatsr/zip")
AATSR_RAW_ROOT = Path("/home/hero/data/ls4t/aatsr/raw")
AATSR_EXTRACT_ROOT = Path("/home/hero/data/ls4t/aatsr/extract")

ZIP_DAY_TEMPLATE = "{year:04d}/{month:02d}/{day:02d}/ats_toa_1p"
RAW_DAY_TEMPLATE = "{year:04d}/{month:02d}/{day:02d}"
EXTRACT_DAY_TEMPLATE = "{year:04d}/{month:02d}/{day:02d}"

YEARS = range(2003, 2012)
MONTHS = range(1, 13)
DAYS = range(1, 32)
VIEWS = ("nadir", "forward")
RAW_FILE_PATTERN = "*ATS_TOA*"
OVERWRITE = False


SCHEMA = "ls4t.aatsr-data/v1"
AUXILIARY_FIELDS = (
    "soil_emissivity_11",
    "soil_emissivity_12",
    "vegetation_emissivity_11",
    "vegetation_emissivity_12",
    "lai",
    "tcwv_cm",
)


@dataclass(frozen=True)
class AatsrDataProduct:
    source_product: str
    view: str
    start_time: str | None
    end_time: str | None
    bt11_k: np.ndarray
    bt12_k: np.ndarray
    view_zenith_deg: np.ndarray
    latitude_deg: np.ndarray
    longitude_deg: np.ndarray
    cloud_mask: np.ndarray
    soil_emissivity_11: np.ndarray | None = None
    soil_emissivity_12: np.ndarray | None = None
    vegetation_emissivity_11: np.ndarray | None = None
    vegetation_emissivity_12: np.ndarray | None = None
    lai: np.ndarray | None = None
    tcwv_cm: np.ndarray | None = None

    @property
    def shape(self) -> tuple[int, ...]:
        return np.asarray(self.bt11_k).shape

    @property
    def has_lst_auxiliary(self) -> bool:
        return all(getattr(self, name) is not None for name in AUXILIARY_FIELDS)

    def validate(self, require_lst_auxiliary: bool = False) -> None:
        if self.view not in {"nadir", "forward"}:
            raise ValueError("AATSR view must be 'nadir' or 'forward'")
        if len(self.shape) != 2:
            raise ValueError("AATSR arrays must be two-dimensional")
        for name in ("bt12_k", "view_zenith_deg", "latitude_deg", "longitude_deg", "cloud_mask"):
            if np.asarray(getattr(self, name)).shape != self.shape:
                raise ValueError(f"{name} does not match the AATSR thermal grid")
        present = [name for name in AUXILIARY_FIELDS if getattr(self, name) is not None]
        if present and len(present) != len(AUXILIARY_FIELDS):
            raise ValueError("AATSR LST auxiliary fields must be supplied together")
        if require_lst_auxiliary and not self.has_lst_auxiliary:
            raise ValueError("AATSR-DATA has no LST auxiliary fields")
        if self.has_lst_auxiliary:
            for name in AUXILIARY_FIELDS:
                if np.asarray(getattr(self, name)).shape != self.shape:
                    raise ValueError(f"{name} does not match the AATSR thermal grid")


def _atomic_npz(path: Path, payload: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".npz", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        np.savez_compressed(temporary_path, **payload)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _coverage_from_name(name: str) -> tuple[str | None, str | None]:
    values = re.findall(r"\d{8}T?\d{6}", name)
    if not values:
        return None, None
    parsed = datetime.strptime(values[0].replace("T", ""), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    stamp = parsed.isoformat().replace("+00:00", "Z")
    return stamp, stamp


def unzip_gzip(input_path: str | Path, output_path: str | Path, overwrite: bool = False) -> Path:
    """解压一个 AATSR gzip 文件。"""

    source = Path(input_path)
    output = Path(output_path)
    if output.exists() and not overwrite:
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(source, "rb") as input_stream, output.open("wb") as output_stream:
        shutil.copyfileobj(input_stream, output_stream)
    return output


def read_native_product(input_path: str | Path, view: str = "nadir") -> AatsrDataProduct:
    """使用 ESA EPR 读取一个 AATSR N1 产品。"""

    try:
        import epr
    except ModuleNotFoundError as error:
        raise RuntimeError("读取 AATSR N1 需要安装 ESA EPR Python 绑定") from error
    if view not in {"nadir", "forward"}:
        raise ValueError("AATSR view must be 'nadir' or 'forward'")
    suffix = "nadir" if view == "nadir" else "fward"
    product = epr.Product(str(input_path))
    try:
        bt11 = product.get_band(f"btemp_{suffix}_1100").read_as_array().astype(float)
        bt12 = product.get_band(f"btemp_{suffix}_1200").read_as_array().astype(float)
        elevation = product.get_band(f"view_elev_{suffix}").read_as_array().astype(float)
        cloud = product.get_band(f"cloud_flags_{suffix}").read_as_array()
        latitude = product.get_band("latitude").read_as_array().astype(float)
        longitude = product.get_band("longitude").read_as_array().astype(float)
    finally:
        product.close()
    shape = bt11.shape
    if latitude.shape != shape or longitude.shape != shape:
        raise ValueError("AATSR geolocation and thermal grids do not match")
    start_time, end_time = _coverage_from_name(Path(input_path).name)
    item = AatsrDataProduct(
        source_product=str(input_path),
        view=view,
        start_time=start_time,
        end_time=end_time,
        bt11_k=bt11,
        bt12_k=bt12,
        view_zenith_deg=90.0 - elevation,
        latitude_deg=latitude,
        longitude_deg=longitude,
        cloud_mask=np.asarray(cloud != 0, dtype=bool),
    )
    item.validate()
    return item


def add_lst_auxiliary(item: AatsrDataProduct, auxiliary_file: str | Path) -> AatsrDataProduct:
    with np.load(auxiliary_file, allow_pickle=False) as auxiliary:
        missing = [name for name in AUXILIARY_FIELDS if name not in auxiliary]
        if missing:
            raise KeyError(f"AATSR auxiliary file is missing: {', '.join(missing)}")
        values = {
            name: np.broadcast_to(np.asarray(auxiliary[name], dtype=float), item.shape).copy()
            for name in AUXILIARY_FIELDS
        }
    result = replace(item, **values)
    result.validate(require_lst_auxiliary=True)
    return result


def write_data_product(path: str | Path, item: AatsrDataProduct) -> None:
    item.validate()
    metadata = {
        "schema": SCHEMA,
        "source_product": item.source_product,
        "view": item.view,
        "start_time": item.start_time,
        "end_time": item.end_time,
    }
    payload = {
        "metadata": np.asarray(json.dumps(metadata, sort_keys=True)),
        "bt11_k": np.asarray(item.bt11_k),
        "bt12_k": np.asarray(item.bt12_k),
        "view_zenith_deg": np.asarray(item.view_zenith_deg),
        "latitude_deg": np.asarray(item.latitude_deg),
        "longitude_deg": np.asarray(item.longitude_deg),
        "cloud_mask": np.asarray(item.cloud_mask),
    }
    for name in AUXILIARY_FIELDS:
        if getattr(item, name) is not None:
            payload[name] = np.asarray(getattr(item, name))
    _atomic_npz(Path(path), payload)


def read_data_product(path: str | Path) -> AatsrDataProduct:
    with np.load(path, allow_pickle=False) as source:
        metadata = json.loads(str(source["metadata"].item()))
        if metadata.get("schema") != SCHEMA:
            raise ValueError(f"not an AATSR-DATA product: {path}")
        optional = {name: source[name].copy() if name in source else None for name in AUXILIARY_FIELDS}
        item = AatsrDataProduct(
            source_product=metadata["source_product"],
            view=metadata["view"],
            start_time=metadata.get("start_time"),
            end_time=metadata.get("end_time"),
            bt11_k=source["bt11_k"].copy(),
            bt12_k=source["bt12_k"].copy(),
            view_zenith_deg=source["view_zenith_deg"].copy(),
            latitude_deg=source["latitude_deg"].copy(),
            longitude_deg=source["longitude_deg"].copy(),
            cloud_mask=source["cloud_mask"].copy(),
            **optional,
        )
    item.validate()
    return item


def aatsr_unzip(
    indir_zip=None,
    outdir_raw=None,
    years=None,
    months=None,
    days=None,
    overwrite=None,
) -> None:
    if indir_zip is None:
        indir_zip = AATSR_ZIP_ROOT
    if outdir_raw is None:
        outdir_raw = AATSR_RAW_ROOT
    if years is None:
        years = YEARS
    if months is None:
        months = MONTHS
    if days is None:
        days = DAYS
    if overwrite is None:
        overwrite = OVERWRITE

    for year in years:
        for month in months:
            for day in days:
                input_day = Path(indir_zip) / ZIP_DAY_TEMPLATE.format(year=year, month=month, day=day)
                if not input_day.is_dir():
                    continue
                output_day = Path(outdir_raw) / RAW_DAY_TEMPLATE.format(year=year, month=month, day=day)
                files = sorted(input_day.glob("*.gz"))
                for index, input_path in enumerate(files):
                    output_path = output_day / input_path.stem
                    print(f"[{year:04d}-{month:02d}-{day:02d}] {index + 1}/{len(files)} {input_path.name}")
                    unzip_gzip(input_path, output_path, overwrite=bool(overwrite))


def aatsr_extract(
    indir_raw=None,
    outdir_extract=None,
    years=None,
    months=None,
    days=None,
    views=None,
    overwrite=None,
) -> None:
    if indir_raw is None:
        indir_raw = AATSR_RAW_ROOT
    if outdir_extract is None:
        outdir_extract = AATSR_EXTRACT_ROOT
    if years is None:
        years = YEARS
    if months is None:
        months = MONTHS
    if days is None:
        days = DAYS
    if views is None:
        views = VIEWS
    if overwrite is None:
        overwrite = OVERWRITE

    for year in years:
        for month in months:
            for day in days:
                input_day = Path(indir_raw) / RAW_DAY_TEMPLATE.format(year=year, month=month, day=day)
                if not input_day.is_dir():
                    continue
                output_day = Path(outdir_extract) / EXTRACT_DAY_TEMPLATE.format(
                    year=year, month=month, day=day
                )
                files = sorted(path for path in input_day.glob(RAW_FILE_PATTERN) if path.is_file())
                for index, input_path in enumerate(files):
                    for view in views:
                        output_path = output_day / input_path.name / f"{view}.npz"
                        if output_path.exists() and not overwrite:
                            continue
                        print(f"[{year:04d}-{month:02d}-{day:02d}] {index + 1}/{len(files)} {view}")
                        write_data_product(output_path, read_native_product(input_path, view=view))


if __name__ == "__main__":
    aatsr_extract()
