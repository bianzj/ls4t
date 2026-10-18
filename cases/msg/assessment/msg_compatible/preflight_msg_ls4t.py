"""核查本机 MSG 配套网格、UTC 文件配对与完整日历覆盖；不修改输入。"""
from pathlib import Path
import argparse
import calendar
import datetime as dt
import json
import os
import time

import numpy as np
from osgeo import gdal, osr

ROOTS = {
    "lst_e": Path("E:/PRODUCTS/MSG/MLST/GEOTIFF"),
    "lst_i": Path("E:/PRODUCTS/MSG-IODC/MLST/GEOTIFF"),
    "lai": Path("E:/PRODUCTS/MSG/MDLAI/GEOTIFF"),
}
PREFIX = {
    "lst_e": "HDF5_LSASAF_MSG_LST_MSG-Disk_",
    "lst_i": "HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_",
    "lai": "HDF5_LSASAF_MSG_LAI_MSG-Disk_",
}


def months(start, end):
    year, month = int(start[:4]), int(start[4:])
    while f"{year:04d}{month:02d}" <= end:
        yield year, month
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def inspect_grid(path, reference):
    ds = gdal.Open(str(path))
    if ds is None:
        raise ValueError(f"Cannot read {path}")
    shape = [ds.RasterYSize, ds.RasterXSize]
    transform = list(ds.GetGeoTransform())
    projection = ds.GetProjection()
    srs = osr.SpatialReference(wkt=projection)
    ref_srs = osr.SpatialReference(wkt=reference["projection"])
    assert shape == reference["shape"], f"Grid shape differs: {path}"
    assert np.allclose(transform, reference["geotransform"], rtol=0, atol=1e-9), path
    assert srs.IsSame(ref_srs), f"Grid CRS differs: {path}"
    band = ds.GetRasterBand(1)
    return {"path": str(path), "shape": shape, "geotransform": transform,
            "datatype": gdal.GetDataTypeName(band.DataType),
            "nodata": band.GetNoDataValue(), "scale": band.GetScale(),
            "offset": band.GetOffset(), "unit": band.GetUnitType()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-month", default="201708")
    parser.add_argument("--end-month", default="202512")
    parser.add_argument("--hours", nargs="+", type=int, default=list(range(10, 17)))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("input_preflight.json"))
    args = parser.parse_args()
    assert args.start_month <= args.end_month
    assert len(args.hours) == len(set(args.hours)) and all(10 <= h <= 16 for h in args.hours)
    gdal.UseExceptions()
    reference_path = Path("E:/Static/combined_euro_vza.tif")
    ds = gdal.Open(str(reference_path))
    reference = {"path": str(reference_path), "shape": [ds.RasterYSize, ds.RasterXSize],
                 "geotransform": list(ds.GetGeoTransform()), "projection": ds.GetProjection()}
    started = time.monotonic()
    available, missing, month_counts, samples = [], [], {}, []
    for year, month in months(args.start_month, args.end_month):
        month_key = f"{year:04d}{month:02d}"
        month_counts[month_key] = {"paired_scenes": 0, "missing_scenes": 0}
        checked = False
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            day_key = f"{year:04d}/{month:02d}/{day:02d}"
            listing = {}
            for key, root in ROOTS.items():
                folder = root / day_key
                listing[key] = set(os.listdir(folder)) if folder.is_dir() else set()
            for hour in args.hours:
                stamp = f"{year:04d}{month:02d}{day:02d}{hour:02d}00"
                paths = {key: root / day_key / (PREFIX[key] + (stamp[:8] + "0000" if key == "lai" else stamp) + ".tif")
                         for key, root in ROOTS.items()}
                absent = [key for key, path in paths.items() if path.name not in listing[key]]
                if absent:
                    missing.append({"timestamp_UTC": stamp, "missing_inputs": absent})
                    month_counts[month_key]["missing_scenes"] += 1
                else:
                    available.append(stamp)
                    month_counts[month_key]["paired_scenes"] += 1
                    if not checked:
                        samples.append({"timestamp_UTC": stamp,
                                        "inputs": {key: inspect_grid(path, reference) for key, path in paths.items()}})
                        checked = True
        print(month_key, month_counts[month_key], flush=True)
    report = {"status": "passed", "checked_UTC": dt.datetime.now(dt.timezone.utc).isoformat(),
              "start_month": args.start_month, "end_month": args.end_month, "hours_UTC": args.hours,
              "reference_grid": reference, "calendar_scenes": len(available) + len(missing),
              "paired_scenes": len(available), "missing_scenes": len(missing), "paired_timestamps": available,
              "missing_inputs": missing, "month_counts": month_counts, "monthly_grid_samples": samples,
              "seconds": round(time.monotonic() - started, 1),
              "grid_check_scope": "First available triple per calendar month; producer checks every actual scene."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix(".json.partial")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, args.output)
    print(json.dumps({key: report[key] for key in ["status", "calendar_scenes", "paired_scenes", "missing_scenes", "seconds"]}))


if __name__ == "__main__":
    main()
