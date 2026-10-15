"""MSG/SEVIRI extraction batch API configured by cases."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import re

import numpy as np

from base.parameters import require_parameters
from base.raster import metadata as raster_metadata
from base.raster import read_raster, write_raster


# ============================================================================
# 算法默认值；执行参数由 cases 提供
# ============================================================================

MSG_RAW_ROOT = None
MSG_DATA_ROOT = None
MSG_STATIC_FILE = None
RAW_DAY_TEMPLATE = "{year:04d}/{month:02d}/{day:02d}"
DATA_DAY_TEMPLATE = "{year:04d}/{month:02d}/{day:02d}"
YEARS = None
MONTHS = range(1, 13)
DAYS = range(1, 32)
RAW_FILE_PATTERN = "*.nat"
OVERWRITE = False


SCHEMA = "ls4t.msg-data/v1"
AUXILIARY_SCHEMA = "ls4t.msg-auxiliary/v1"
DATA_BAND_NAMES = {
    "bt8": "bt8",
    "bt9": "bt9",
    "view_zenith_deg": "vza",
    "latitude_deg": "lat",
    "longitude_deg": "lon",
    "cloud_mask": "cloud",
}
DATA_BAND_FIELDS = {
    **{value: key for key, value in DATA_BAND_NAMES.items()},
    "bt108": "bt8",
    "bt120": "bt9",
    "bt108_k": "bt8",
    "bt120_k": "bt9",
}
AUXILIARY_FIELDS = (
    "soil_emissivity_108",
    "soil_emissivity_120",
    "vegetation_emissivity_108",
    "vegetation_emissivity_120",
    "lai",
    "tcwv_cm",
)


@dataclass(frozen=True)
class MsgDataProduct:
    source_product: str
    start_time: str
    end_time: str
    bt8: np.ndarray
    bt9: np.ndarray
    view_zenith_deg: np.ndarray
    latitude_deg: np.ndarray
    longitude_deg: np.ndarray
    cloud_mask: np.ndarray
    soil_emissivity_108: np.ndarray | None = None
    soil_emissivity_120: np.ndarray | None = None
    vegetation_emissivity_108: np.ndarray | None = None
    vegetation_emissivity_120: np.ndarray | None = None
    lai: np.ndarray | None = None
    tcwv_cm: np.ndarray | None = None

    @property
    def shape(self) -> tuple[int, ...]:
        return np.asarray(self.bt8).shape

    @property
    def has_lst_auxiliary(self) -> bool:
        return all(getattr(self, name) is not None for name in AUXILIARY_FIELDS)

    def validate(self, require_lst_auxiliary: bool = False) -> None:
        if len(self.shape) != 2:
            raise ValueError("MSG arrays must be two-dimensional")
        for name in ("bt9", "view_zenith_deg", "latitude_deg", "longitude_deg", "cloud_mask"):
            if np.asarray(getattr(self, name)).shape != self.shape:
                raise ValueError(f"{name} does not match the MSG grid")
        present = [name for name in AUXILIARY_FIELDS if getattr(self, name) is not None]
        if present and len(present) != len(AUXILIARY_FIELDS):
            raise ValueError("MSG LST auxiliary fields must be supplied together")
        if require_lst_auxiliary and not self.has_lst_auxiliary:
            raise ValueError("MSG-DATA has no LST auxiliary fields")
        if self.has_lst_auxiliary:
            for name in AUXILIARY_FIELDS:
                if np.asarray(getattr(self, name)).shape != self.shape:
                    raise ValueError(f"{name} does not match the MSG grid")


def _time_from_name(name: str) -> str:
    matches = re.findall(r"\d{12,14}", name)
    if not matches:
        raise ValueError(f"cannot read MSG time from filename: {name}")
    value = matches[-1][:14].ljust(14, "0")
    parsed = datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def read_native_product(input_path: str | Path, static_file=None) -> MsgDataProduct:
    """使用 Satpy 读取一个 SEVIRI native 文件。"""

    if static_file is None:
        static_file = MSG_STATIC_FILE
    require_parameters(static_file=static_file)
    try:
        from satpy import Scene
    except ModuleNotFoundError as error:
        raise RuntimeError("读取 MSG native 数据需要安装 satpy") from error
    scene = Scene(
        filenames={"seviri_l1b_native": [str(input_path)]},
        reader_kwargs={"fill_disk": True},
    )
    scene.load(["IR_108", "IR_120"], calibration="brightness_temperature")
    bt8 = np.asarray(scene["IR_108"].values, dtype=float)
    bt9 = np.asarray(scene["IR_120"].values, dtype=float)
    static_fields, _ = read_raster(static_file)
    canonical_static = {
        DATA_BAND_FIELDS.get(name, name): value for name, value in static_fields.items()
    }
    required_static = ("latitude_deg", "longitude_deg", "view_zenith_deg")
    missing = [name for name in required_static if name not in canonical_static]
    if missing:
        raise KeyError(f"MSG static GeoTIFF is missing: {', '.join(missing)}")
    latitude = np.asarray(canonical_static["latitude_deg"], dtype=float)
    longitude = np.asarray(canonical_static["longitude_deg"], dtype=float)
    view_zenith = np.asarray(canonical_static["view_zenith_deg"], dtype=float)
    cloud = np.asarray(canonical_static.get("cloud_mask", np.zeros(bt8.shape)), dtype=bool)
    stamp = _time_from_name(Path(input_path).name)
    item = MsgDataProduct(
        str(input_path), stamp, stamp, bt8, bt9, view_zenith, latitude, longitude, cloud
    )
    item.validate()
    return item


def add_lst_auxiliary(item: MsgDataProduct, auxiliary_file: str | Path) -> MsgDataProduct:
    auxiliary, metadata = read_raster(auxiliary_file)
    if metadata.get("LS4T_SCHEMA") not in {AUXILIARY_SCHEMA, None}:
        raise ValueError(f"not an MSG auxiliary GeoTIFF: {auxiliary_file}")
    missing = [name for name in AUXILIARY_FIELDS if name not in auxiliary]
    if missing:
        raise KeyError(f"MSG auxiliary GeoTIFF is missing: {', '.join(missing)}")
    values = {
        name: np.broadcast_to(np.asarray(auxiliary[name], float), item.shape).copy()
        for name in AUXILIARY_FIELDS
    }
    result = replace(item, **values)
    result.validate(require_lst_auxiliary=True)
    return result


def write_auxiliary_product(path: str | Path, fields: dict[str, np.ndarray]) -> None:
    missing = [name for name in AUXILIARY_FIELDS if name not in fields]
    if missing:
        raise KeyError(f"MSG auxiliary GeoTIFF is missing: {', '.join(missing)}")
    write_raster(
        path,
        {name: np.asarray(fields[name], dtype=float) for name in AUXILIARY_FIELDS},
        raster_metadata(AUXILIARY_SCHEMA, fields=list(AUXILIARY_FIELDS)),
    )


def write_data_product(
    path: str | Path,
    item: MsgDataProduct,
    *,
    reference_path: str | Path | None = None,
) -> None:
    item.validate()
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = {
        DATA_BAND_NAMES[name]: np.asarray(getattr(item, name))
        for name in (
            "bt8",
            "bt9",
            "view_zenith_deg",
            "latitude_deg",
            "longitude_deg",
            "cloud_mask",
        )
    }
    for name in AUXILIARY_FIELDS:
        if getattr(item, name) is not None:
            fields[name] = np.asarray(getattr(item, name))
    write_raster(
        destination,
        fields,
        raster_metadata(
            SCHEMA,
            source_product=item.source_product,
            start_time=item.start_time,
            end_time=item.end_time,
        ),
        reference_path,
    )


def read_data_product(path: str | Path) -> MsgDataProduct:
    fields, file_metadata = read_raster(path)
    if file_metadata.get("LS4T_SCHEMA") != SCHEMA:
        raise ValueError(f"not an MSG-DATA GeoTIFF: {path}")
    canonical = {DATA_BAND_FIELDS.get(name, name): value for name, value in fields.items()}
    required = ("bt8", "bt9", "view_zenith_deg", "latitude_deg", "longitude_deg", "cloud_mask")
    missing = [name for name in required if name not in canonical]
    if missing:
        raise ValueError(f"MSG-DATA GeoTIFF is missing: {', '.join(missing)}")
    values = json.loads(file_metadata["LS4T_METADATA"])
    optional = {
        name: canonical[name].copy() if name in canonical else None for name in AUXILIARY_FIELDS
    }
    item = MsgDataProduct(
        source_product=values["source_product"],
        start_time=values["start_time"],
        end_time=values["end_time"],
        bt8=np.asarray(canonical["bt8"]).copy(),
        bt9=np.asarray(canonical["bt9"]).copy(),
        view_zenith_deg=np.asarray(canonical["view_zenith_deg"]).copy(),
        latitude_deg=np.asarray(canonical["latitude_deg"]).copy(),
        longitude_deg=np.asarray(canonical["longitude_deg"]).copy(),
        cloud_mask=np.asarray(canonical["cloud_mask"]).copy(),
        **optional,
    )
    item.validate()
    return item


def msg_extract(
    indir_raw=None,
    outdir_data=None,
    static_file=None,
    years=None,
    months=None,
    days=None,
    overwrite=None,
) -> None:
    if indir_raw is None:
        indir_raw = MSG_RAW_ROOT
    if outdir_data is None:
        outdir_data = MSG_DATA_ROOT
    if static_file is None:
        static_file = MSG_STATIC_FILE
    if years is None:
        years = YEARS
    if months is None:
        months = MONTHS
    if days is None:
        days = DAYS
    if overwrite is None:
        overwrite = OVERWRITE
    require_parameters(
        indir_raw=indir_raw,
        outdir_data=outdir_data,
        static_file=static_file,
        years=years,
    )
    for year in years:
        for month in months:
            for day in days:
                input_day = Path(indir_raw) / RAW_DAY_TEMPLATE.format(year=year, month=month, day=day)
                if not input_day.is_dir():
                    continue
                output_day = Path(outdir_data) / DATA_DAY_TEMPLATE.format(year=year, month=month, day=day)
                inputs = sorted(input_day.glob(RAW_FILE_PATTERN))
                for index, input_path in enumerate(inputs):
                    output_path = output_day / f"{input_path.name}.tif"
                    if output_path.exists() and not overwrite:
                        continue
                    print(f"[{year:04d}-{month:02d}-{day:02d}] {index + 1}/{len(inputs)} {input_path.name}")
                    write_data_product(output_path, read_native_product(input_path, static_file))
