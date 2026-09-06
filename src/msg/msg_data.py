"""MSG/SEVIRI extraction run manually by date range."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile

import numpy as np


# ============================================================================
# 手动运行参数
# ============================================================================

MSG_RAW_ROOT = Path("/home/hero/data/ls4t/msg/raw")
MSG_DATA_ROOT = Path("/home/hero/data/ls4t/msg/data")
MSG_STATIC_FILE = Path("/home/hero/data/ls4t/msg/base/msg_static.npz")
RAW_DAY_TEMPLATE = "{year:04d}/{month:02d}/{day:02d}"
DATA_DAY_TEMPLATE = "{year:04d}/{month:02d}/{day:02d}"
YEARS = range(2017, 2026)
MONTHS = range(1, 13)
DAYS = range(1, 32)
RAW_FILE_PATTERN = "*.nat"
OVERWRITE = False


SCHEMA = "ls4t.msg-data/v1"
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
    bt108_k: np.ndarray
    bt120_k: np.ndarray
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
        return np.asarray(self.bt108_k).shape

    @property
    def has_lst_auxiliary(self) -> bool:
        return all(getattr(self, name) is not None for name in AUXILIARY_FIELDS)

    def validate(self, require_lst_auxiliary: bool = False) -> None:
        if len(self.shape) != 2:
            raise ValueError("MSG arrays must be two-dimensional")
        for name in ("bt120_k", "view_zenith_deg", "latitude_deg", "longitude_deg", "cloud_mask"):
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
    try:
        from satpy import Scene
    except ModuleNotFoundError as error:
        raise RuntimeError("读取 MSG native 数据需要安装 satpy") from error
    scene = Scene(
        filenames={"seviri_l1b_native": [str(input_path)]},
        reader_kwargs={"fill_disk": True},
    )
    scene.load(["IR_108", "IR_120"], calibration="brightness_temperature")
    bt108 = np.asarray(scene["IR_108"].values, dtype=float)
    bt120 = np.asarray(scene["IR_120"].values, dtype=float)
    with np.load(static_file, allow_pickle=False) as static:
        latitude = np.asarray(static["latitude_deg"], dtype=float)
        longitude = np.asarray(static["longitude_deg"], dtype=float)
        view_zenith = np.asarray(static["view_zenith_deg"], dtype=float)
        cloud = np.asarray(static["cloud_mask"], dtype=bool) if "cloud_mask" in static else np.zeros(bt108.shape, bool)
    stamp = _time_from_name(Path(input_path).name)
    item = MsgDataProduct(
        str(input_path), stamp, stamp, bt108, bt120, view_zenith, latitude, longitude, cloud
    )
    item.validate()
    return item


def add_lst_auxiliary(item: MsgDataProduct, auxiliary_file: str | Path) -> MsgDataProduct:
    with np.load(auxiliary_file, allow_pickle=False) as auxiliary:
        missing = [name for name in AUXILIARY_FIELDS if name not in auxiliary]
        if missing:
            raise KeyError(f"MSG auxiliary file is missing: {', '.join(missing)}")
        values = {
            name: np.broadcast_to(np.asarray(auxiliary[name], float), item.shape).copy()
            for name in AUXILIARY_FIELDS
        }
    result = replace(item, **values)
    result.validate(require_lst_auxiliary=True)
    return result


def write_data_product(path: str | Path, item: MsgDataProduct) -> None:
    item.validate()
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema": SCHEMA,
        "source_product": item.source_product,
        "start_time": item.start_time,
        "end_time": item.end_time,
    }
    payload = {
        "metadata": np.asarray(json.dumps(metadata, sort_keys=True)),
        "bt108_k": np.asarray(item.bt108_k),
        "bt120_k": np.asarray(item.bt120_k),
        "view_zenith_deg": np.asarray(item.view_zenith_deg),
        "latitude_deg": np.asarray(item.latitude_deg),
        "longitude_deg": np.asarray(item.longitude_deg),
        "cloud_mask": np.asarray(item.cloud_mask),
    }
    for name in AUXILIARY_FIELDS:
        if getattr(item, name) is not None:
            payload[name] = np.asarray(getattr(item, name))
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".npz", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        np.savez_compressed(temporary_path, **payload)
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def read_data_product(path: str | Path) -> MsgDataProduct:
    with np.load(path, allow_pickle=False) as source:
        metadata = json.loads(str(source["metadata"].item()))
        optional = {name: source[name].copy() if name in source else None for name in AUXILIARY_FIELDS}
        item = MsgDataProduct(
            source_product=metadata["source_product"],
            start_time=metadata["start_time"],
            end_time=metadata["end_time"],
            bt108_k=source["bt108_k"].copy(),
            bt120_k=source["bt120_k"].copy(),
            view_zenith_deg=source["view_zenith_deg"].copy(),
            latitude_deg=source["latitude_deg"].copy(),
            longitude_deg=source["longitude_deg"].copy(),
            cloud_mask=source["cloud_mask"].copy(),
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
    for year in years:
        for month in months:
            for day in days:
                input_day = Path(indir_raw) / RAW_DAY_TEMPLATE.format(year=year, month=month, day=day)
                if not input_day.is_dir():
                    continue
                output_day = Path(outdir_data) / DATA_DAY_TEMPLATE.format(year=year, month=month, day=day)
                inputs = sorted(input_day.glob(RAW_FILE_PATTERN))
                for index, input_path in enumerate(inputs):
                    output_path = output_day / f"{input_path.name}.npz"
                    if output_path.exists() and not overwrite:
                        continue
                    print(f"[{year:04d}-{month:02d}-{day:02d}] {index + 1}/{len(inputs)} {input_path.name}")
                    write_data_product(output_path, read_native_product(input_path, static_file))


if __name__ == "__main__":
    msg_extract()
