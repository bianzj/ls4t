#!/usr/bin/env python3
"""Project LSASAF MSG HDF5 products to the shared Europe/Africa grid."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, timedelta
import glob
import os
from pathlib import Path

if not (Path(os.environ.get("PROJ_LIB", "")) / "proj.db").is_file():
    if Path("/usr/share/proj/proj.db").is_file():
        os.environ["PROJ_LIB"] = "/usr/share/proj"

AREA_EXTENT = (-18.0, -35.0, 61.0, 65.0)
RESOLUTION_DEGREE = 0.03


@dataclass(frozen=True)
class Product:
    input_relative: str
    output_relative: str
    variable: str
    latitude_name: str
    longitude_name: str


PRODUCTS = {
    "euro-lst": Product(
        "PRODUCTS/MSG/MLST/HDF5",
        "PRODUCTS/MSG/MLST/GEOTIFF",
        "LST",
        "EURO_Lat.tif",
        "EURO_Lon.tif",
    ),
    "iodc-lst": Product(
        "PRODUCTS/MSG-IODC/MLST/HDF5",
        "PRODUCTS/MSG-IODC/MLST/GEOTIFF",
        "LST",
        "IODC_Lat.tif",
        "IODC_Lon.tif",
    ),
    "euro-lai": Product(
        "PRODUCTS/MSG/MDLAI/HDF5",
        "PRODUCTS/MSG/MDLAI/GEOTIFF",
        "LAI",
        "EURO_Lat.tif",
        "EURO_Lon.tif",
    ),
}


def parse_hours(value: str | None) -> set[int] | None:
    if value is None or not value.strip():
        return None
    hours = {int(item) for item in value.split(",") if item.strip()}
    if not hours or any(hour < 0 or hour > 23 for hour in hours):
        raise argparse.ArgumentTypeError("hours must be comma-separated values from 0 to 23")
    return hours


def iter_dates(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def load_static_latlon(latitude_path: Path, longitude_path: Path):
    import numpy as np
    import rasterio

    with rasterio.open(latitude_path) as source:
        latitude = source.read(1).astype(np.float32)
        if np.nanmax(latitude) > 90:
            latitude /= 100.0
    with rasterio.open(longitude_path) as source:
        longitude = source.read(1).astype(np.float32)
        if np.nanmax(longitude) > 180:
            longitude /= 100.0
    return np.flipud(latitude), longitude


def write_image(path: Path, data: np.ndarray, transform, projection: str) -> None:
    from osgeo import gdal, osr

    spatial_reference = osr.SpatialReference()
    spatial_reference.ImportFromEPSG(int(projection.split(":")[-1]))
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(
        str(path),
        data.shape[1],
        data.shape[0],
        1,
        gdal.GDT_UInt16,
        options=["COMPRESS=LZW", "PREDICTOR=2", "TILED=YES"],
    )
    if dataset is None:
        raise RuntimeError(f"cannot create output: {path}")
    dataset.SetGeoTransform(transform.to_gdal())
    dataset.SetProjection(spatial_reference.ExportToWkt())
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)
    band.SetNoDataValue(0)
    band.FlushCache()
    dataset = None


def project_directory(
    input_directory: Path,
    output_directory: Path,
    variable: str,
    source_latitude: np.ndarray,
    source_longitude: np.ndarray,
    hours: set[int] | None = None,
    overwrite: bool = False,
) -> dict[str, int]:
    import h5py
    import numpy as np
    from pyresample import geometry, kd_tree
    from rasterio.transform import from_bounds

    width = int((AREA_EXTENT[2] - AREA_EXTENT[0]) / RESOLUTION_DEGREE)
    height = int((AREA_EXTENT[3] - AREA_EXTENT[1]) / RESOLUTION_DEGREE)
    target_area = geometry.AreaDefinition(
        "common_area",
        "Lat-Lon Grid",
        "wgs84",
        {"proj": "longlat", "datum": "WGS84"},
        width,
        height,
        AREA_EXTENT,
    )
    transform = from_bounds(*AREA_EXTENT, width, height)
    source_swath = geometry.SwathDefinition(lons=source_longitude, lats=source_latitude)
    counts = {"found": 0, "written": 0, "existing": 0, "filtered": 0, "failed": 0}

    for input_path_string in sorted(glob.glob(str(input_directory / "HDF5*"))):
        input_path = Path(input_path_string)
        if not input_path.is_file():
            continue
        counts["found"] += 1
        timestamp = input_path.stem.split("_")[-1]
        if len(timestamp) != 12 or not timestamp.isdigit() or not timestamp.endswith("00"):
            counts["filtered"] += 1
            continue
        if hours is not None and int(timestamp[8:10]) not in hours:
            counts["filtered"] += 1
            continue
        output_directory.mkdir(parents=True, exist_ok=True)
        output_path = output_directory / f"{input_path.stem}.tif"
        if output_path.exists() and not overwrite:
            counts["existing"] += 1
            continue
        try:
            with h5py.File(input_path, "r") as source:
                if variable not in source:
                    raise KeyError(f"dataset {variable!r} is absent")
                dataset = source[variable]
                raw_data = dataset[:]
                missing_value = dataset.attrs.get("MISSING_VALUE", -8000)
            clean_data = raw_data.astype(np.float32)
            clean_data[raw_data == missing_value] = np.nan
            if clean_data.shape != source_latitude.shape:
                raise ValueError(
                    f"shape mismatch: {clean_data.shape} != {source_latitude.shape}"
                )
            resampled = kd_tree.resample_nearest(
                source_swath,
                clean_data,
                target_area,
                radius_of_influence=5000,
                fill_value=np.nan,
            )
            final_data = np.nan_to_num(resampled, nan=0).astype(np.uint16)
            write_image(output_path, final_data, transform, "EPSG:4326")
            counts["written"] += 1
            print(f"written {output_path}", flush=True)
        except Exception as error:
            counts["failed"] += 1
            print(f"failed {input_path}: {error}", flush=True)
    return counts


def build_parser(default_product: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--product",
        choices=sorted(PRODUCTS),
        default=default_product,
        required=default_product is None,
    )
    parser.add_argument("--msg-root", type=Path, default=Path("/media/hero/MSG"))
    parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    parser.add_argument("--end-date", type=date.fromisoformat)
    parser.add_argument("--hours", type=parse_hours)
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--latitude", type=Path)
    parser.add_argument("--longitude", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(default_product: str | None = None) -> None:
    args = build_parser(default_product).parse_args()
    end_date = args.end_date or args.start_date
    if end_date < args.start_date:
        raise SystemExit("--end-date must not be earlier than --start-date")
    product = PRODUCTS[args.product]
    input_root = args.input_root or args.msg_root / product.input_relative
    output_root = args.output_root or args.msg_root / product.output_relative
    latitude_path = args.latitude or args.msg_root / "Static" / product.latitude_name
    longitude_path = args.longitude or args.msg_root / "Static" / product.longitude_name

    for path in (input_root, latitude_path, longitude_path):
        if not path.exists():
            raise SystemExit(f"required input is missing: {path}")
    print(
        f"{args.product}: {args.start_date}..{end_date}, hours={args.hours or 'all'}, "
        f"input={input_root}, output={output_root}",
        flush=True,
    )
    if args.dry_run:
        return

    source_latitude, source_longitude = load_static_latlon(latitude_path, longitude_path)
    total = {"found": 0, "written": 0, "existing": 0, "filtered": 0, "failed": 0}
    for current_date in iter_dates(args.start_date, end_date):
        relative = Path(f"{current_date:%Y}") / f"{current_date:%m}" / f"{current_date:%d}"
        counts = project_directory(
            input_root / relative,
            output_root / relative,
            product.variable,
            source_latitude,
            source_longitude,
            args.hours,
            args.overwrite,
        )
        for key, value in counts.items():
            total[key] += value
    print(f"complete: {total}", flush=True)
    if total["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
