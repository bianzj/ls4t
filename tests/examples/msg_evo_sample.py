"""Extract and run the real 10x10 EVO MSG sample; no external data needed to run."""

from __future__ import annotations

import argparse
import calendar
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

import numpy as np
from osgeo import gdal, osr

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from base.lsct import retrieve_components_window
from base.radiometry import planck_radiance
from base.rt.hotspot import hotspot_layer

SAMPLE = ROOT / "tests/data/msg_evo_201710_10x10"
SITE = {"id": "EVO", "name": "Evora", "latitude_deg": 38.5411, "longitude_deg": -8.0033}
SIZE = 10
WAVELENGTH_UM = 10.5


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_stack(path, arrays, names, transform, projection, unit="", **metadata):
    """GeoTIFF bands are ordered exactly as their manifest time/field axis."""
    gdal.UseExceptions()
    arrays = np.asarray(arrays)
    if arrays.ndim != 3 or arrays.shape[0] != len(names):
        raise ValueError("expected (band, row, col) and one name per band")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dataset = gdal.GetDriverByName("GTiff").Create(
        str(path), arrays.shape[2], arrays.shape[1], arrays.shape[0],
        gdal.GDT_Float32, options=["COMPRESS=DEFLATE", "PREDICTOR=3"],
    )
    dataset.SetGeoTransform(transform)
    dataset.SetProjection(projection)
    dataset.SetMetadata({key: str(value) for key, value in metadata.items()})
    for number, (name, array) in enumerate(zip(names, arrays), 1):
        band = dataset.GetRasterBand(number)
        band.SetDescription(name)
        band.SetNoDataValue(float("nan"))
        if unit:
            band.SetUnitType(unit)
        band.WriteArray(np.asarray(array, dtype=np.float32))
    dataset.FlushCache()
    dataset = None


def read_stack(path: Path):
    gdal.UseExceptions()
    dataset = gdal.Open(str(path), gdal.GA_ReadOnly)
    array = np.asarray(dataset.ReadAsArray(), dtype=np.float64)
    if array.ndim == 2:
        array = array[None]
    names = [dataset.GetRasterBand(i).GetDescription() for i in range(1, dataset.RasterCount + 1)]
    transform, projection = dataset.GetGeoTransform(), dataset.GetProjection()
    dataset = None
    return array, names, transform, projection


def source_crop(path: Path, window, transform, projection):
    dataset = gdal.Open(str(path), gdal.GA_ReadOnly)
    if not np.allclose(dataset.GetGeoTransform(), transform, rtol=0, atol=1e-10):
        raise ValueError(f"source grid differs: {path}")
    srs = osr.SpatialReference(wkt=dataset.GetProjection())
    reference = osr.SpatialReference(wkt=projection)
    if not srs.IsSame(reference):
        raise ValueError(f"source CRS differs: {path}")
    raw = dataset.GetRasterBand(1).ReadAsArray(*window)
    nodata = dataset.GetRasterBand(1).GetNoDataValue()
    if raw.shape != (SIZE, SIZE):
        raise ValueError(f"source crop is not 10x10: {path}")
    record = {
        "path": str(path), "size_bytes": path.stat().st_size,
        "window_raw_sha256": hashlib.sha256(np.ascontiguousarray(raw).tobytes()).hexdigest(),
        "raw_dtype": str(raw.dtype), "projected_nodata": nodata,
    }
    dataset = None
    return raw, nodata, record


def copy_product_window(source: Path, target: Path, window, raw):
    """Keep the production GeoTIFF encoding; only crop its spatial extent."""
    target.parent.mkdir(parents=True, exist_ok=True)
    dataset = gdal.Translate(
        str(target), str(source), srcWin=list(window), format="GTiff",
        creationOptions=["COMPRESS=LZW", "PREDICTOR=2", "TILED=YES"],
    )
    dataset = None
    check = gdal.Open(str(target))
    actual = check.ReadAsArray()
    if actual.dtype != raw.dtype or not np.array_equal(actual, raw):
        raise ValueError(f"raw crop changed during export: {target}")
    check = None


def calibration(path: Path, variable: str, stamp: str):
    import h5py

    with h5py.File(path, "r") as source:
        acquisition = source.attrs["IMAGE_ACQUISITION_TIME"]
        if isinstance(acquisition, bytes):
            acquisition = acquisition.decode()
        if str(acquisition)[:12] != stamp:
            raise ValueError(f"source acquisition time disagrees with filename: {path}")
        attrs = source[variable].attrs
        unit = attrs["UNITS"]
        if isinstance(unit, bytes):
            unit = unit.decode()
        result = {
            "hdf5_path": str(path), "variable": variable, "source_unit": str(unit),
            "scaling_factor": float(attrs["SCALING_FACTOR"]),
            "offset": float(attrs["OFFSET"]), "missing_value": int(attrs["MISSING_VALUE"]),
        }
        if variable == "LST" and "cels" not in result["source_unit"].lower():
            raise ValueError(f"expected source Celsius LST: {result}")
        return result


def decode(raw, nodata, information, variable):
    # The projected UInt16 rasters contain signed Int16 source bit patterns.
    signed = raw.view(np.int16) if raw.dtype == np.uint16 else raw.astype(np.int16)
    valid = signed != information["missing_value"]
    if nodata is not None:
        valid &= raw != nodata
    result = signed.astype(np.float64) / information["scaling_factor"] + information["offset"]
    if variable == "LST":
        result += 273.15
        valid &= (result >= 200) & (result <= 380)
    else:
        valid &= (result >= 0) & (result <= 10)
    return np.where(valid, result, np.nan)


def sample_auxiliary(path, latitude, longitude):
    """Sample each ancillary with its own CRS/affine, without reading a global image."""
    dataset = gdal.Open(str(path), gdal.GA_ReadOnly)
    source_srs = osr.SpatialReference()
    source_srs.ImportFromEPSG(4326)
    target_srs = osr.SpatialReference(wkt=dataset.GetProjection())
    for srs in (source_srs, target_srs):
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    conversion = osr.CoordinateTransformation(source_srs, target_srs)
    points = np.asarray(conversion.TransformPoints(np.column_stack([longitude.ravel(), latitude.ravel()])))
    inverse = gdal.InvGeoTransform(dataset.GetGeoTransform())
    column = np.floor(inverse[0] + inverse[1] * points[:, 0] + inverse[2] * points[:, 1]).astype(int)
    row = np.floor(inverse[3] + inverse[4] * points[:, 0] + inverse[5] * points[:, 1]).astype(int)
    if np.any((row < 0) | (row >= dataset.RasterYSize) | (column < 0) | (column >= dataset.RasterXSize)):
        raise ValueError(f"ancillary coverage does not contain sample: {path}")
    x, y = int(column.min()), int(row.min())
    block = dataset.GetRasterBand(1).ReadAsArray(x, y, int(column.max()) - x + 1, int(row.max()) - y + 1)
    result = block[row - y, column - x].reshape(latitude.shape).astype(float)
    record = {
        "path": str(path), "sample_sha256": hashlib.sha256(result.tobytes()).hexdigest(),
        "source_projection_wkt": dataset.GetProjection(),
        "sampling": "nearest source cell; each source CRS and affine used independently",
    }
    dataset = None
    return result, record


def extract(source_root: Path, output: Path = SAMPLE, year=2017, month=10):
    """Only source reads; write small, portable arrays and their provenance below tests/."""
    import pandas as pd
    import pvlib

    gdal.UseExceptions()
    osr.UseExceptions()
    output.mkdir(parents=True, exist_ok=True)
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    hours = [start + timedelta(hours=i) for i in range(calendar.monthrange(year, month)[1] * 24)]
    stamps = [time.strftime("%Y%m%d%H%M") for time in hours]
    dates = sorted({stamp[:8] for stamp in stamps})
    first = source_root / f"PRODUCTS/MSG/MLST/GEOTIFF/{year}/{month:02d}/01/HDF5_LSASAF_MSG_LST_MSG-Disk_{stamps[12]}.tif"
    reference = gdal.Open(str(first), gdal.GA_ReadOnly)
    transform, projection = reference.GetGeoTransform(), reference.GetProjection()
    inverse = gdal.InvGeoTransform(transform)
    col = int(np.floor(inverse[0] + inverse[1] * SITE["longitude_deg"] + inverse[2] * SITE["latitude_deg"]))
    row = int(np.floor(inverse[3] + inverse[4] * SITE["longitude_deg"] + inverse[5] * SITE["latitude_deg"]))
    window = (col - SIZE // 2, row - SIZE // 2, SIZE, SIZE)
    if min(window[:2]) < 0 or window[0] + SIZE > reference.RasterXSize or window[1] + SIZE > reference.RasterYSize:
        raise ValueError("station window falls outside the reference grid")
    crop_transform = (
        transform[0] + window[0] * transform[1] + window[1] * transform[2],
        transform[1], transform[2],
        transform[3] + window[0] * transform[4] + window[1] * transform[5],
        transform[4], transform[5],
    )
    reference = None
    yy, xx = np.indices((SIZE, SIZE))
    longitude = crop_transform[0] + (xx + .5) * crop_transform[1] + (yy + .5) * crop_transform[2]
    latitude = crop_transform[3] + (xx + .5) * crop_transform[4] + (yy + .5) * crop_transform[5]
    static = {"latitude_deg": latitude, "longitude_deg": longitude}
    records, missing = [], []
    for view in ("euro", "iodc"):
        for angle in ("vza", "vaa"):
            path = source_root / f"Static/combined_{view}_{angle}.tif"
            raw, nodata, record = source_crop(path, window, transform, projection)
            relative = path.relative_to(source_root)
            copy_product_window(path, output / relative, window, raw)
            record["sample_path"] = relative.as_posix()
            records.append(record)
    land, land_record = sample_auxiliary(source_root / "map/MCD12C1_2011_0.01.tif", latitude, longitude)
    soil, soil_record = sample_auxiliary(source_root / "lse/AG1km.v003.SoilEmi.ABI.Global.001D_LSE11.tif", latitude, longitude)
    table_path = source_root / "lse/IGBP_Emi.txt"
    table = np.loadtxt(table_path)
    land_valid = np.isfinite(land) & (land > 0) & (land <= 17)
    vegetation = np.full(land.shape, np.nan)
    vegetation[land_valid] = table[land[land_valid].astype(int), 0] / 1000.
    soil = soil / 1000.
    static.update(land_cover_class=land, soil_emissivity=np.where((soil > 0) & (soil <= 1), soil, np.nan), vegetation_emissivity=vegetation)
    records.extend([land_record, soil_record, {"path": str(table_path), "sha256": sha256(table_path)}])
    static_names = list(static)
    write_stack(output / "AUXILIARY/static.tif", np.stack(list(static.values())), static_names, crop_transform, projection)

    products = {
        "lst_euro": ("MSG", "MLST", "LST", "MSG-Disk", stamps),
        "lst_iodc": ("MSG-IODC", "MLST", "LST", "IODC-Disk", stamps),
        "lai": ("MSG", "MDLAI", "LAI", "MSG-Disk", [day + "0000" for day in dates]),
    }
    for label, (sensor, family, variable, disk, product_stamps) in products.items():
        for index, stamp in enumerate(product_stamps):
            stem = f"HDF5_LSASAF_{sensor}_{variable}_{disk}_{stamp}"
            day = Path(stamp[:4]) / stamp[4:6] / stamp[6:8]
            base = source_root / "PRODUCTS" / sensor / family
            path, hdf = base / "GEOTIFF" / day / (stem + ".tif"), base / "HDF5" / day / stem
            if not path.is_file() or not hdf.is_file():
                missing.append({"product": label, "timestamp_utc": stamp, "path": str(path), "hdf5_path": str(hdf)})
                continue
            raw, nodata, record = source_crop(path, window, transform, projection)
            information = calibration(hdf, variable, stamp)
            relative = path.relative_to(source_root)
            copy_product_window(path, output / relative, window, raw)
            records.append({**record, "sample_path": relative.as_posix(),
                            "calibration": information, "product": label, "timestamp_utc": stamp})
            if index % 100 == 0:
                print(f"{label}: {index + 1}/{len(product_stamps)}", flush=True)

    # Solar geometry is calculated, not a measured satellite variable. Store it
    # so running the packaged example needs neither pvlib nor the source drive.
    times = pd.DatetimeIndex(np.repeat(hours, SIZE * SIZE))
    solar = pvlib.solarposition.get_solarposition(
        times, np.tile(latitude.ravel(), len(hours)), np.tile(longitude.ravel(), len(hours)),
        altitude=0., method="nrel_numpy",
    )
    for field, column in (("solar_zenith_deg", "zenith"), ("solar_azimuth_deg", "azimuth")):
        write_stack(output / "AUXILIARY" / (field + ".tif"), np.asarray(solar[column]).reshape(len(hours), SIZE, SIZE),
                    stamps, crop_transform, projection, unit="degree", METHOD="pvlib nrel_numpy geometric solar position; altitude 0 m")
    source_manifest = output / "sources.json"
    write_json(source_manifest, {"window_xywh": list(window), "records": records, "missing_sources": missing})
    files = {}
    for folder in ("PRODUCTS", "Static", "AUXILIARY"):
        for path in sorted((output / folder).rglob("*.tif")):
            files[path.relative_to(output).as_posix()] = {"sha256": sha256(path), "size_bytes": path.stat().st_size}
    files[source_manifest.name] = {"sha256": sha256(source_manifest), "size_bytes": source_manifest.stat().st_size}
    write_json(output / "manifest.json", {
        "schema": "ls4t.real-msg-test-sample/v2", "synthetic": False, "site": SITE,
        "input_format": "production projected GeoTIFF; one acquisition per single-band file; original UInt16 values and NoData=0",
        "calibration_source": "Per-file original HDF5 attributes copied into sources.json; applied only at load time",
        "site_coordinate_source": str(source_root / "field/sites.txt"),
        "period": f"{year}-{month:02d}", "timezone": "UTC", "shape": [SIZE, SIZE],
        "timestamps_utc": stamps, "lai_dates_utc": dates, "static_fields": static_names,
        "source_window_xywh": list(window), "station_source_row_col": [row, col],
        "station_sample_row_col": [SIZE // 2, SIZE // 2],
        "geotransform": list(crop_transform), "projection_wkt": projection,
        "stored_encoding": {"LST": "signed Int16 Celsius x 100 bit patterns stored as UInt16", "LAI": "signed Int16 LAI x 1000 bit patterns stored as UInt16", "Static": "Int16 degrees x 100"},
        "decoded_units": {"lst_euro": "K", "lst_iodc": "K", "lai": "m2 m-2", "angles": "degree"},
        "source_record_count": len(records), "missing_source_count": len(missing), "files": files,
        "solar_geometry": {"method": "pvlib nrel_numpy geometric zenith/azimuth", "pvlib_version": importlib.metadata.version("pvlib"), "altitude_m": 0},
        "limitations": [
            "Projected zero is NoData; valid source zero Celsius/zero LAI cannot be recovered and is excluded.",
            "2017 static EURO/IODC viewing angles are retained; this fixture does not validate orbital geometry provenance.",
            "Land-cover source has an unspecified Clarke 1866 datum; its geographic transformation has uncertain accuracy.",
            "Spatial reference solver assumes component radiances constant over each 5x5 neighborhood; it is not the constrained regional production algorithm.",
            "This is a real-input integration test, not a validation of component temperatures against ground observations.",
        ],
    })
    print(f"extracted {len(stamps)} hourly times, {len(dates)} LAI dates, missing sources={len(missing)}", flush=True)


def load_sample(sample: Path = SAMPLE):
    manifest = json.loads((sample / "manifest.json").read_text(encoding="utf-8"))
    if manifest["schema"] != "ls4t.real-msg-test-sample/v2":
        raise ValueError("re-extract the sample using the production-layout v2 format")
    sources = json.loads((sample / "sources.json").read_text(encoding="utf-8"))
    indexed = {(r["product"], r["timestamp_utc"]): r for r in sources["records"] if "product" in r}
    data = {name: read_stack(sample / "AUXILIARY" / (name + ".tif"))[0] for name in (
        "solar_zenith_deg", "solar_azimuth_deg",
    )}
    for product in ("lst_euro", "lst_iodc", "lai"):
        stamps = ([day + "0000" for day in manifest["lai_dates_utc"]]
                  if product == "lai" else manifest["timestamps_utc"])
        values = np.full((len(stamps), *manifest["shape"]), np.nan)
        for index, stamp in enumerate(stamps):
            record = indexed.get((product, stamp))
            if record is None:
                continue  # An absent acquisition stays missing; never fill it.
            dataset = gdal.Open(str(sample / record["sample_path"]))
            band = dataset.GetRasterBand(1)
            info = record["calibration"]
            values[index] = decode(band.ReadAsArray(), band.GetNoDataValue(), info, info["variable"])
            band = dataset = None
        data[product] = values
    static, names, _, _ = read_stack(sample / "AUXILIARY/static.tif")
    data["static"] = dict(zip(names, static))
    for view in ("euro", "iodc"):
        for angle in ("vza", "vaa"):
            dataset = gdal.Open(str(sample / f"Static/combined_{view}_{angle}.tif"))
            band = dataset.GetRasterBand(1)
            raw, nodata = band.ReadAsArray(), band.GetNoDataValue()
            valid = raw != nodata if nodata is not None else np.ones_like(raw, bool)
            value = raw.astype(float) / 100.
            data["static"][f"{angle}_{view}_deg"] = np.where(valid, value % 360 if angle == "vaa" else value, np.nan)
            band = dataset = None
    return manifest, data


def prepare_frame(manifest, data, index, components=2):
    """Decode already-calibrated LST to emissivity-weighted radiance, not brightness temperature."""
    stamp = manifest["timestamps_utc"][index]
    lai = data["lai"][manifest["lai_dates_utc"].index(stamp[:8])]
    static = data["static"]
    zenith, azimuth = data["solar_zenith_deg"][index], data["solar_azimuth_deg"][index]
    daylight_zenith = np.where((zenith >= 0) & (zenith < 90), zenith, np.nan)
    es, ev = static["soil_emissivity"], static["vegetation_emissivity"]
    views = []
    for view in ("euro", "iodc"):
        vza, vaa = static[f"vza_{view}_deg"], static[f"vaa_{view}_deg"]
        gap = np.exp(-.5 * lai / np.cos(np.radians(vza)))
        if components == 2:
            weights = np.stack([es * gap, ev * (1. - gap)], axis=-1)
        elif components == 3:
            relative = np.abs((azimuth - vaa + 180.) % 360. - 180.)
            sunlit = hotspot_layer(lai, .25, vza, daylight_zenith, relative)
            weights = np.stack([es * sunlit, es * (gap - sunlit), ev * (1. - gap)], axis=-1)
        else:
            raise ValueError("components must be 2 or 3")
        views.append(weights)
    weights = np.stack(views, axis=-2)
    lst = np.stack([data["lst_euro"][index], data["lst_iodc"][index]], axis=-1)
    observed = planck_radiance(WAVELENGTH_UM, lst) * weights.sum(axis=-1)
    valid = np.isfinite(lst).all(-1) & (lst >= 250).all(-1) & (lst <= 350).all(-1)
    valid &= np.isfinite(lai) & (lai >= .05) & (lai <= 10) & (zenith >= 0) & (zenith < 90)
    valid &= np.isfinite(weights).all(axis=(-1, -2)) & (weights >= 0).all(axis=(-1, -2))
    valid &= (static["land_cover_class"] > 0) & (static["land_cover_class"] <= 17)
    for view in ("euro", "iodc"):
        valid &= (static[f"vza_{view}_deg"] >= 0) & (static[f"vza_{view}_deg"] < 90)
    observed[~valid] = np.nan
    weights[~valid] = np.nan
    return observed, weights, valid


def run_sample(sample: Path = SAMPLE, output: Path | None = None, components=2):
    """Run each instant independently; never combine different acquisition times."""
    manifest, data = load_sample(sample)
    names = ("soil", "vegetation") if components == 2 else ("sunlit_soil", "shaded_soil", "vegetation")
    times = manifest["timestamps_utc"]
    temperature = np.full((len(times), SIZE, SIZE, components), np.nan)
    quality = np.full((len(times), SIZE, SIZE), 1, dtype=np.uint16)
    residual = np.full((len(times), SIZE, SIZE), np.nan)
    counts, rows = [], []
    for index, stamp in enumerate(times):
        # No thermal sunlit/shaded interpretation at night.
        if np.any(data["solar_zenith_deg"][index] < 90):
            observed, weights, valid = prepare_frame(manifest, data, index, components)
            if valid.any():
                result = retrieve_components_window(
                    observed, weights, WAVELENGTH_UM, window_size=5,
                    max_condition_number=1.e6, valid_temperature_range_k=(250., 350.),
                )
                keep = valid & np.isfinite(result.temperature_k).all(-1)
                temperature[index, keep] = result.temperature_k[keep]
                residual[index, keep] = result.residual_rms[keep]
                quality[index] = result.quality_flag
                quality[index, ~valid] |= 1
        good = np.isfinite(temperature[index]).all(-1)
        counts.append(int(good.sum()))
        row = {"timestamp_utc": stamp, "valid_pixels": counts[-1]}
        row.update({f"center_{name}_k": float(temperature[index, 5, 5, number]) for number, name in enumerate(names)})
        rows.append(row)
    good = np.isfinite(temperature).all(-1)
    summary = {
        "sample_period": manifest["period"], "shape": [len(times), SIZE, SIZE, components],
        "component_names": list(names), "wavelength_um": WAVELENGTH_UM, "window_size": 5,
        "method": "base.lsct.retrieve_components_window; simultaneous dual-view spatial least squares",
        "observation_validity": "common finite dual view; daylight; LAI >= 0.05; LST and output 250-350 K",
        "total_hourly_times": len(times), "times_with_retrieval": int(np.any(good, axis=(1, 2)).sum()),
        "valid_pixel_times": int(good.sum()), "valid_center_times": int(good[:, 5, 5].sum()),
        "temperature_min_k": float(np.nanmin(temperature)) if good.any() else None,
        "temperature_max_k": float(np.nanmax(temperature)) if good.any() else None,
        "validation": "real-data integration only; no ground accuracy claim",
    }
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        gt, pr = manifest["geotransform"], manifest["projection_wkt"]
        for number, name in enumerate(names):
            write_stack(output / (name + ".tif"), temperature[..., number], times, gt, pr, unit="K")
        write_stack(output / "quality_flag.tif", quality, times, gt, pr, unit="bitmask")
        write_stack(output / "residual_rms.tif", residual, times, gt, pr, unit="W m-2 sr-1 um-1")
        with (output / "center_timeseries.csv").open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        write_json(output / "summary.json", summary)
    return summary, temperature, quality


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    extraction = commands.add_parser("extract")
    extraction.add_argument("--source-root", type=Path, required=True)
    extraction.add_argument("--output", type=Path, default=SAMPLE)
    extraction.add_argument("--year", type=int, default=2017)
    extraction.add_argument("--month", type=int, default=10)
    run = commands.add_parser("run")
    run.add_argument("--sample", type=Path, default=SAMPLE)
    run.add_argument("--output", type=Path, default=ROOT / "tests/outputs/msg_evo_201710_10x10")
    run.add_argument("--components", type=int, choices=(2, 3), default=2)
    args = parser.parse_args()
    if args.command == "extract":
        extract(args.source_root, args.output, args.year, args.month)
    else:
        summary, _, _ = run_sample(args.sample, args.output, args.components)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if not summary["valid_pixel_times"]:
            raise SystemExit("no valid component retrievals")


if __name__ == "__main__":
    main()
