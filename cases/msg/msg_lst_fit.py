#!/usr/bin/env python3
"""Retrieve MSG/SEVIRI LST from native IR_108 and IR_120 observations."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import os
from pathlib import Path
import re

if not (Path(os.environ.get("PROJ_LIB", "")) / "proj.db").is_file():
    if Path("/usr/share/proj/proj.db").is_file():
        os.environ["PROJ_LIB"] = "/usr/share/proj"

import h5py
import numpy as np


VIEW_ZENITH_NODES = np.asarray(
    [0, 3, 14.9, 38.6, 44.5, 51.2, 58, 65, 70, 75, 80], dtype=np.float32
)
WATER_VAPOUR_EDGES = np.asarray(
    [0, 1.25, 2.25, 3.25, 4.25, 5.25, 100], dtype=np.float32
)
GLOBAL_FINE_GRID = (18000, 36000, 0.01)
GLOBAL_TCWV_GRID = (721, 1440, 0.25)
FVC_COEFFICIENT = 0.825
SCATTERING_FACTOR = 0.05
LST_RANGE_K = (220.0, 365.0)


@dataclass(frozen=True)
class DiskProfile:
    product_name: str
    output_relative: str
    latitude_name: str
    longitude_name: str
    view_zenith_name: str
    lai_relative: str


DISKS = {
    "euro": DiskProfile(
        "MSG-Disk",
        "PRODUCTS/LS4T/MSG/MLST/HDF5",
        "EURO_Lat.tif",
        "EURO_Lon.tif",
        "MSG_VZA.tif",
        "PRODUCTS/MSG/MDLAI/HDF5",
    ),
    "iodc": DiskProfile(
        "IODC-Disk",
        "PRODUCTS/LS4T/MSG-IODC/MLST/HDF5",
        "IODC_Lat.tif",
        "IODC_Lon.tif",
        "IODC/HDF5_LSASAF_MSG_VZA_IODC-Disk_202406041200",
        "PRODUCTS/MSG-IODC/MDLAI/HDF5",
    ),
}


def parse_hours(value: str | None) -> set[int] | None:
    if value is None or not value.strip():
        return None
    hours = {int(item) for item in value.split(",") if item.strip()}
    if not hours or any(hour < 0 or hour > 23 for hour in hours):
        raise argparse.ArgumentTypeError("hours must be comma-separated values from 0 to 23")
    return hours


def timestamp_from_name(path: Path) -> datetime:
    matches = re.findall(r"(?<!\d)(\d{12,14})(?!\d)", path.name)
    if not matches:
        raise ValueError(f"cannot read YYYYMMDDHHMM timestamp from {path.name}")
    return datetime.strptime(matches[-1][:12], "%Y%m%d%H%M").replace(tzinfo=timezone.utc)


def grid_index(
    latitude: np.ndarray,
    longitude: np.ndarray,
    rows: int,
    columns: int,
    resolution: float,
) -> tuple[np.ndarray, np.ndarray]:
    safe_latitude = np.nan_to_num(latitude, nan=90.0, posinf=90.0, neginf=-90.0)
    safe_longitude = np.nan_to_num(longitude, nan=-180.0, posinf=180.0, neginf=-180.0)
    row = np.rint((90.0 - safe_latitude) / resolution).astype(np.int32)
    column = np.rint((safe_longitude + 180.0) / resolution).astype(np.int32)
    np.clip(row, 0, rows - 1, out=row)
    np.clip(column, 0, columns - 1, out=column)
    return row, column


def read_raster(path: Path, scale: float = 1.0) -> np.ndarray:
    from osgeo import gdal

    dataset = gdal.Open(str(path))
    if dataset is None:
        raise FileNotFoundError(path)
    band = dataset.GetRasterBand(1)
    values = band.ReadAsArray().astype(np.float32)
    nodata = band.GetNoDataValue()
    if nodata is not None:
        values[values == nodata] = np.nan
    return values / scale


def sample_global_raster(
    path: Path,
    row_index: np.ndarray,
    column_index: np.ndarray,
    scale: float = 1.0,
    dtype=np.float32,
) -> np.ndarray:
    from osgeo import gdal

    dataset = gdal.Open(str(path))
    if dataset is None:
        raise FileNotFoundError(path)
    band = dataset.GetRasterBand(1)
    source = band.ReadAsArray()
    sampled = source[row_index, column_index]
    nodata = band.GetNoDataValue()
    if nodata is not None:
        sampled = sampled.astype(np.float32, copy=False)
        invalid = ~np.isfinite(sampled) if np.isnan(nodata) else sampled == nodata
        sampled[invalid] = np.nan
    return (sampled.astype(dtype, copy=False) / scale).copy()


def load_coefficients(path: Path) -> np.ndarray:
    table = np.asarray(np.loadtxt(path), dtype=np.float32)
    coefficients = table if table.shape[1] == 8 else table[:, 2:10]
    expected = (len(VIEW_ZENITH_NODES) * (len(WATER_VAPOUR_EDGES) - 1), 8)
    if coefficients.shape != expected:
        raise ValueError(f"{path}: coefficients must have shape {expected}, got {coefficients.shape}")
    return coefficients


def load_lai(path: Path) -> np.ndarray:
    with h5py.File(path, "r") as handle:
        field = handle["LAI"]
        raw = np.asarray(field[...])
        missing = field.attrs.get("MISSING_VALUE", -10)
        divisor = float(field.attrs.get("SCALING_FACTOR", 1000.0))
    lai = raw.astype(np.float32) / divisor
    lai[raw == missing] = np.nan
    lai[(lai < 0) | (lai > 10)] = np.nan
    return lai


def tcwv_path(root: Path, timestamp: datetime) -> Path:
    return root / f"{timestamp:%Y}" / f"tcwv_{timestamp:%Y%m%d}.h5"


def load_tcwv_slice(root: Path, timestamp: datetime) -> np.ndarray:
    path = tcwv_path(root, timestamp)
    with h5py.File(path, "r") as handle:
        field = handle["data"]
        raw = np.asarray(field[timestamp.hour], dtype=np.float32)
        fill_value = float(field.attrs.get("_FillValue", 65535))
        scale_factor = float(field.attrs.get("scale_factor", 1.0))
    raw[raw == fill_value] = np.nan
    first = raw * scale_factor / 10.0
    if timestamp.minute == 0:
        return first

    next_timestamp = timestamp + timedelta(hours=1)
    next_path = tcwv_path(root, next_timestamp)
    with h5py.File(next_path, "r") as handle:
        field = handle["data"]
        raw_next = np.asarray(field[next_timestamp.hour], dtype=np.float32)
        fill_value = float(field.attrs.get("_FillValue", 65535))
        scale_factor = float(field.attrs.get("scale_factor", 1.0))
    raw_next[raw_next == fill_value] = np.nan
    second = raw_next * scale_factor / 10.0
    fraction = timestamp.minute / 60.0
    return first * (1.0 - fraction) + second * fraction


def solar_day_mask(timestamp: datetime, latitude: np.ndarray, longitude: np.ndarray) -> np.ndarray:
    day_of_year = timestamp.timetuple().tm_yday
    decimal_hour = timestamp.hour + timestamp.minute / 60.0
    gamma = 2.0 * np.pi / 365.0 * (day_of_year - 1 + (decimal_hour - 12.0) / 24.0)
    equation_of_time = 229.18 * (
        0.000075
        + 0.001868 * np.cos(gamma)
        - 0.032077 * np.sin(gamma)
        - 0.014615 * np.cos(2.0 * gamma)
        - 0.040849 * np.sin(2.0 * gamma)
    )
    declination = (
        0.006918
        - 0.399912 * np.cos(gamma)
        + 0.070257 * np.sin(gamma)
        - 0.006758 * np.cos(2.0 * gamma)
        + 0.000907 * np.sin(2.0 * gamma)
        - 0.002697 * np.cos(3.0 * gamma)
        + 0.00148 * np.sin(3.0 * gamma)
    )
    true_solar_minutes = (decimal_hour * 60.0 + equation_of_time + 4.0 * longitude) % 1440.0
    hour_angle = np.deg2rad(true_solar_minutes / 4.0 - 180.0)
    latitude_radians = np.deg2rad(latitude)
    cosine_zenith = (
        np.sin(latitude_radians) * np.sin(declination)
        + np.cos(latitude_radians) * np.cos(declination) * np.cos(hour_angle)
    )
    return cosine_zenith > 0.0


def retrieve_lst(
    bt108: np.ndarray,
    bt120: np.ndarray,
    view_zenith: np.ndarray,
    tcwv_cm: np.ndarray,
    soil_emissivity108: np.ndarray,
    soil_emissivity120: np.ndarray,
    vegetation_emissivity108: np.ndarray,
    vegetation_emissivity120: np.ndarray,
    lai: np.ndarray,
    land_mask: np.ndarray,
    day_mask: np.ndarray,
    coefficients_day: np.ndarray,
    coefficients_night: np.ndarray,
) -> np.ndarray:
    fvc = 1.0 - np.exp(-FVC_COEFFICIENT * lai * 0.5)
    fvc = np.clip(fvc, 0.0, 1.0)
    scattering108 = (
        (1.0 - soil_emissivity108)
        * vegetation_emissivity108
        * SCATTERING_FACTOR
        * (1.0 - fvc)
    )
    scattering120 = (
        (1.0 - soil_emissivity120)
        * vegetation_emissivity120
        * SCATTERING_FACTOR
        * (1.0 - fvc)
    )
    emissivity108 = np.minimum(
        soil_emissivity108 * (1.0 - fvc) + vegetation_emissivity108 * fvc + scattering108,
        0.995,
    )
    emissivity120 = np.minimum(
        soil_emissivity120 * (1.0 - fvc) + vegetation_emissivity120 * fvc + scattering120,
        0.995,
    )
    mean_emissivity = (emissivity108 + emissivity120) * 0.5
    delta_emissivity = emissivity108 - emissivity120
    mean_bt = (bt108 + bt120) * 0.5
    delta_bt = (bt108 - bt120) * 0.5
    with np.errstate(divide="ignore", invalid="ignore"):
        features = (
            np.ones_like(mean_bt),
            mean_bt,
            (1.0 - mean_emissivity) / mean_emissivity * mean_bt,
            delta_emissivity / mean_emissivity**2 * mean_bt,
            delta_bt,
            (1.0 - mean_emissivity) / mean_emissivity * delta_bt,
            delta_emissivity / mean_emissivity**2 * delta_bt,
            (bt108 - bt120) ** 2,
        )
    valid = (
        land_mask
        & np.isfinite(bt108)
        & np.isfinite(bt120)
        & np.isfinite(view_zenith)
        & np.isfinite(tcwv_cm)
        & np.isfinite(mean_emissivity)
        & (bt108 > 0)
        & (bt120 > 0)
        & (mean_emissivity > 0)
    )
    result = np.full(bt108.shape, np.nan, dtype=np.float32)
    water_bins = len(WATER_VAPOUR_EDGES) - 1
    for water_index in range(water_bins):
        for view_index in range(len(VIEW_ZENITH_NODES) - 1):
            selection = (
                valid
                & (tcwv_cm >= WATER_VAPOUR_EDGES[water_index])
                & (tcwv_cm < WATER_VAPOUR_EDGES[water_index + 1])
                & (view_zenith >= VIEW_ZENITH_NODES[view_index])
                & (view_zenith < VIEW_ZENITH_NODES[view_index + 1])
            )
            if not np.any(selection):
                continue
            fraction = (
                view_zenith[selection] - VIEW_ZENITH_NODES[view_index]
            ) / (VIEW_ZENITH_NODES[view_index + 1] - VIEW_ZENITH_NODES[view_index])
            row0 = view_index * water_bins + water_index
            row1 = (view_index + 1) * water_bins + water_index
            selected_day = day_mask[selection]
            coefficients0 = np.where(
                selected_day[:, None], coefficients_day[row0], coefficients_night[row0]
            )
            coefficients1 = np.where(
                selected_day[:, None], coefficients_day[row1], coefficients_night[row1]
            )
            coefficients = coefficients0 * (1.0 - fraction[:, None]) + coefficients1 * fraction[:, None]
            result[selection] = sum(
                features[index][selection] * coefficients[:, index] for index in range(8)
            )
    result[(result < LST_RANGE_K[0]) | (result > LST_RANGE_K[1])] = np.nan
    return result


def find_lai_file(lai_root: Path, timestamp: datetime) -> Path:
    day_root = lai_root / f"{timestamp:%Y/%m/%d}"
    candidates = sorted(day_root.glob(f"HDF5*{timestamp:%Y%m%d}0000*"))
    if not candidates:
        raise FileNotFoundError(f"daily LAI is missing under {day_root}")
    return candidates[0]


def read_native_brightness_temperatures(path: Path) -> tuple[np.ndarray, np.ndarray]:
    try:
        from satpy import Scene
    except ModuleNotFoundError as error:
        raise RuntimeError("reading MSG native files requires satpy") from error
    scene = Scene(
        filenames={"seviri_l1b_native": [str(path)]},
        reader_kwargs={"fill_disk": True},
    )
    scene.load(["IR_108", "IR_120"], calibration="brightness_temperature")
    return (
        np.asarray(scene["IR_108"].values, dtype=np.float32),
        np.asarray(scene["IR_120"].values, dtype=np.float32),
    )


def read_brightness_temperatures(
    path: Path, input_format: str
) -> tuple[np.ndarray, np.ndarray]:
    is_geotiff = input_format == "geotiff" or (
        input_format == "auto" and path.name.endswith("_bt8.tif")
    )
    if not is_geotiff:
        return read_native_brightness_temperatures(path)
    if not path.name.endswith("_bt8.tif"):
        raise ValueError("GeoTIFF input must be the *_bt8.tif member of a bt8/bt9 pair")
    bt120_path = path.with_name(path.name.removesuffix("_bt8.tif") + "_bt9.tif")
    if not bt120_path.is_file():
        raise FileNotFoundError(bt120_path)
    return read_raster(path, 100.0), read_raster(bt120_path, 100.0)


def write_product(path: Path, lst: np.ndarray, timestamp: datetime, source: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stored = np.nan_to_num(lst * 100.0, nan=0.0).astype(np.uint16)
    with h5py.File(path, "w") as handle:
        field = handle.create_dataset(
            "LST",
            data=stored,
            compression="gzip",
            compression_opts=4,
            shuffle=True,
            chunks=(256, 256),
        )
        field.attrs["SCALING_FACTOR"] = 100.0
        field.attrs["MISSING_VALUE"] = 0
        field.attrs["UNITS"] = "K"
        handle.attrs["algorithm"] = "LS4T MSG generalized split-window"
        handle.attrs["source_product"] = str(source)
        handle.attrs["time_utc"] = timestamp.isoformat().replace("+00:00", "Z")


def build_static_inputs(args, profile: DiskProfile) -> dict[str, np.ndarray]:
    latitude_path = args.latitude or args.msg_root / "Static" / profile.latitude_name
    longitude_path = args.longitude or args.msg_root / "Static" / profile.longitude_name
    view_zenith_path = args.view_zenith or args.msg_root / "Static" / profile.view_zenith_name
    latitude = read_raster(latitude_path, 100.0)
    longitude = read_raster(longitude_path, 100.0)
    view_zenith = read_raster(view_zenith_path, 100.0)
    if not (latitude.shape == longitude.shape == view_zenith.shape):
        raise ValueError("latitude, longitude and view zenith grids do not match")
    valid_geo = (
        np.isfinite(latitude)
        & np.isfinite(longitude)
        & (latitude >= -90)
        & (latitude <= 90)
        & (longitude >= -180)
        & (longitude <= 180)
    )
    fine_row, fine_column = grid_index(
        latitude, longitude, GLOBAL_FINE_GRID[0], GLOBAL_FINE_GRID[1], GLOBAL_FINE_GRID[2]
    )
    class_path = args.land_cover or args.msg_root / "map/MCD12C1_2011_0.01.tif"
    soil108_path = args.soil_emissivity108 or args.msg_root / "lse/AG1km.v003.SoilEmi.ABI.Global.001D_LSE11.tif"
    soil120_path = args.soil_emissivity120 or args.msg_root / "lse/AG1km.v003.SoilEmi.ABI.Global.001D_LSE12.tif"
    land_class = sample_global_raster(class_path, fine_row, fine_column)
    soil108 = sample_global_raster(soil108_path, fine_row, fine_column, 1000.0)
    soil120 = sample_global_raster(soil120_path, fine_row, fine_column, 1000.0)
    vegetation_table = np.asarray(np.loadtxt(args.vegetation_emissivity, usecols=(0, 1)))
    class_index = np.nan_to_num(land_class, nan=0).astype(np.int16)
    class_index[(class_index < 0) | (class_index >= len(vegetation_table))] = 0
    vegetation108 = vegetation_table[class_index, 0].astype(np.float32) / 1000.0
    vegetation120 = vegetation_table[class_index, 1].astype(np.float32) / 1000.0
    return {
        "latitude": latitude,
        "longitude": longitude,
        "view_zenith": view_zenith,
        "land_mask": valid_geo & (class_index > 0) & (class_index < 17),
        "soil108": soil108,
        "soil120": soil120,
        "vegetation108": vegetation108,
        "vegetation120": vegetation120,
    }


def process_file(path: Path, args, profile: DiskProfile, static: dict, coefficients) -> Path:
    timestamp = timestamp_from_name(path)
    relative = Path(f"{timestamp:%Y/%m/%d}")
    output_name = f"HDF5_LS4T_MSG_LST_{profile.product_name}_{timestamp:%Y%m%d%H%M}"
    output_path = args.output_root / relative / output_name
    if output_path.exists() and not args.overwrite:
        print(f"existing {output_path}", flush=True)
        return output_path
    lai_root = args.lai_root or args.msg_root / profile.lai_relative
    lai = load_lai(find_lai_file(lai_root, timestamp))
    if lai.shape != static["latitude"].shape:
        raise ValueError(f"LAI shape {lai.shape} does not match native grid {static['latitude'].shape}")
    tcwv_grid = load_tcwv_slice(args.tcwv_root, timestamp)
    tcwv_row, tcwv_column = grid_index(
        static["latitude"],
        static["longitude"],
        GLOBAL_TCWV_GRID[0],
        GLOBAL_TCWV_GRID[1],
        GLOBAL_TCWV_GRID[2],
    )
    tcwv_cm = tcwv_grid[tcwv_row, tcwv_column]
    bt108, bt120 = read_brightness_temperatures(path, args.input_format)
    if bt108.shape != static["latitude"].shape:
        raise ValueError(f"native data shape {bt108.shape} does not match static grid")
    day_mask = solar_day_mask(timestamp, static["latitude"], static["longitude"])
    lst = retrieve_lst(
        bt108,
        bt120,
        static["view_zenith"],
        tcwv_cm,
        static["soil108"],
        static["soil120"],
        static["vegetation108"],
        static["vegetation120"],
        lai,
        static["land_mask"],
        day_mask,
        coefficients[0],
        coefficients[1],
    )
    write_product(output_path, lst, timestamp, path)
    print(f"written {output_path}: valid={np.count_nonzero(np.isfinite(lst))}", flush=True)
    return output_path


def discover(args) -> list[Path]:
    if args.input_root.is_file():
        paths = [args.input_root]
    else:
        paths = []
        if args.input_format in {"auto", "native"}:
            paths.extend(args.input_root.rglob("*.nat"))
        if args.input_format in {"auto", "geotiff"}:
            paths.extend(args.input_root.rglob("*_bt8.tif"))
        paths = sorted(paths)
    selected = []
    end_date = args.end_date or args.start_date
    for path in paths:
        try:
            timestamp = timestamp_from_name(path)
        except ValueError:
            continue
        if not (args.start_date <= timestamp.date() <= end_date):
            continue
        if args.hours is not None and timestamp.hour not in args.hours:
            continue
        selected.append(path)
    return selected[: args.limit] if args.limit else selected


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disk", choices=sorted(DISKS), default="euro")
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--input-format", choices=("auto", "native", "geotiff"), default="auto")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    parser.add_argument("--end-date", type=date.fromisoformat)
    parser.add_argument("--hours", type=parse_hours)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--msg-root", type=Path, default=Path("/media/hero/MSG"))
    parser.add_argument("--tcwv-root", type=Path, default=Path("/home/hero/data/rs/tcwv"))
    parser.add_argument("--coefficient-day", type=Path, required=True)
    parser.add_argument("--coefficient-night", type=Path, required=True)
    parser.add_argument("--lai-root", type=Path)
    parser.add_argument("--latitude", type=Path)
    parser.add_argument("--longitude", type=Path)
    parser.add_argument("--view-zenith", type=Path)
    parser.add_argument("--land-cover", type=Path)
    parser.add_argument("--soil-emissivity108", type=Path)
    parser.add_argument("--soil-emissivity120", type=Path)
    parser.add_argument(
        "--vegetation-emissivity",
        type=Path,
        default=Path("/media/hero/MSG/lse/IGBP_Emi.txt"),
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parsed = parser.parse_args()
    if parsed.end_date is not None and parsed.end_date < parsed.start_date:
        parser.error("--end-date must not be earlier than --start-date")
    return parsed


def main() -> None:
    args = parse_args()
    profile = DISKS[args.disk]
    if args.disk == "iodc" and any(
        path is None for path in (args.latitude, args.longitude, args.view_zenith)
    ):
        raise SystemExit(
            "IODC geometry changed during the archive; provide --latitude, "
            "--longitude and --view-zenith for the requested period"
        )
    if args.output_root is None:
        args.output_root = args.msg_root / profile.output_relative
    latitude_path = args.latitude or args.msg_root / "Static" / profile.latitude_name
    longitude_path = args.longitude or args.msg_root / "Static" / profile.longitude_name
    view_zenith_path = args.view_zenith or args.msg_root / "Static" / profile.view_zenith_name
    lai_root = args.lai_root or args.msg_root / profile.lai_relative
    land_cover = args.land_cover or args.msg_root / "map/MCD12C1_2011_0.01.tif"
    soil108 = args.soil_emissivity108 or args.msg_root / "lse/AG1km.v003.SoilEmi.ABI.Global.001D_LSE11.tif"
    soil120 = args.soil_emissivity120 or args.msg_root / "lse/AG1km.v003.SoilEmi.ABI.Global.001D_LSE12.tif"
    required = (
        args.input_root,
        args.tcwv_root,
        args.coefficient_day,
        args.coefficient_night,
        args.vegetation_emissivity,
        latitude_path,
        longitude_path,
        view_zenith_path,
        lai_root,
        land_cover,
        soil108,
        soil120,
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("missing required inputs:\n" + "\n".join(missing))
    files = discover(args)
    print(
        f"MSG LS4T LST: disk={args.disk}, files={len(files)}, "
        f"dates={args.start_date}..{args.end_date or args.start_date}, "
        f"hours={args.hours or 'all'}, output={args.output_root}",
        flush=True,
    )
    if args.dry_run:
        return
    if not files:
        raise SystemExit("no native MSG files matched the requested interval")
    coefficients = (
        load_coefficients(args.coefficient_day),
        load_coefficients(args.coefficient_night),
    )
    print("loading MSG static and global emissivity inputs...", flush=True)
    static = build_static_inputs(args, profile)
    failed = 0
    for path in files:
        try:
            process_file(path, args, profile, static, coefficients)
        except Exception as error:
            failed += 1
            print(f"failed {path}: {error}", flush=True)
    if failed:
        raise SystemExit(f"{failed} file(s) failed")


if __name__ == "__main__":
    main()
