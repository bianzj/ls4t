#!/usr/bin/env python3
"""Warp each SLSTR scene with GDAL/PROJ geolocation support, then mosaic.

This is the scene-first version of the South America test.  Each nadir or
oblique scene is exposed as a GDAL VRT with GEOLOCATION metadata, warped to a
regular EPSG:6933 grid with bilinear resampling, and only then accumulated in
the daily mosaic.  Intermediate scene rasters are temporary and are removed
after the daily mosaic is written.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

if os.path.isdir("/usr/share/proj"):
    os.environ["PROJ_LIB"] = "/usr/share/proj"
    os.environ["PROJ_DATA"] = "/usr/share/proj"

from osgeo import gdal
from pyproj import CRS, Transformer

from south_america_daily_mosaic import (
    discover_scenes,
    load_region,
    parse_date,
    read_band,
    scale_geolocation,
)


DEFAULT_REGION = Path(__file__).with_name("south_america_tropical_amazon.geojson")
DEFAULT_ROOT = Path("/media/hero/slstr-southA-lst")
DEFAULT_OUTPUT = Path("/home/hero/work/ls4t/cases/slstr/regions/gdalwarp_daily_daynight")
SCENE_TIME_RE = re.compile(r"RBT____(\d{8})T(\d{6})")


def make_geoloc_vrt(vrt_path: Path, data_path: Path, lon_path: Path, lat_path: Path) -> None:
    data_ds = gdal.Open(str(data_path), gdal.GA_ReadOnly)
    if data_ds is None:
        raise RuntimeError(f"Cannot open {data_path}")
    width, height = data_ds.RasterXSize, data_ds.RasterYSize
    dtype = gdal.GetDataTypeName(data_ds.GetRasterBand(1).DataType)
    data_ds = None
    vrt_path.write_text(
        f'''<VRTDataset rasterXSize="{width}" rasterYSize="{height}">
  <Metadata domain="GEOLOCATION">
    <MDI key="SRS">GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]</MDI>
    <MDI key="X_DATASET">{lon_path}</MDI>
    <MDI key="X_BAND">1</MDI>
    <MDI key="PIXEL_OFFSET">0</MDI>
    <MDI key="PIXEL_STEP">1</MDI>
    <MDI key="Y_DATASET">{lat_path}</MDI>
    <MDI key="Y_BAND">1</MDI>
    <MDI key="LINE_OFFSET">0</MDI>
    <MDI key="LINE_STEP">1</MDI>
  </Metadata>
  <VRTRasterBand dataType="{dtype}" band="1">
    <NoDataValue>0</NoDataValue>
    <SimpleSource>
      <SourceFilename relativeToVRT="0">{data_path}</SourceFilename>
      <SourceBand>1</SourceBand>
    </SimpleSource>
  </VRTRasterBand>
</VRTDataset>
''',
        encoding="utf-8",
    )


def write_geolocation_raster(path: Path, array: np.ndarray) -> None:
    """Materialize the input integer hundredths-of-degree geolocation as Float32."""
    array = np.asarray(array, dtype=np.float32).copy()
    # Invalid geolocation fill values (for example -327.68 degrees) must not
    # be passed to PROJ. NaN lets GDAL skip those source locations cleanly.
    array[~np.isfinite(array)] = np.nan
    array[(array < -180.0) | (array > 180.0)] = np.nan
    driver = gdal.GetDriverByName("GTiff")
    ds = driver.Create(str(path), array.shape[1], array.shape[0], 1, gdal.GDT_Float32)
    if ds is None:
        raise RuntimeError(f"Cannot create temporary geolocation raster {path}")
    ds.GetRasterBand(1).WriteArray(array)
    ds.GetRasterBand(1).FlushCache()
    ds = None


def solar_zenith_deg(when: datetime, latitude: float, longitude: float) -> float:
    """Approximate solar zenith using the NOAA solar position equations."""
    when = when.astimezone(timezone.utc)
    day_of_year = when.timetuple().tm_yday
    hour = when.hour + when.minute / 60.0 + when.second / 3600.0
    gamma = 2.0 * np.pi / 365.0 * (day_of_year - 1 + (hour - 12.0) / 24.0)
    equation_of_time = 229.18 * (
        0.000075 + 0.001868 * np.cos(gamma) - 0.032077 * np.sin(gamma)
        - 0.014615 * np.cos(2 * gamma) - 0.040849 * np.sin(2 * gamma)
    )
    declination = (
        0.006918 - 0.399912 * np.cos(gamma) + 0.070257 * np.sin(gamma)
        - 0.006758 * np.cos(2 * gamma) + 0.000907 * np.sin(2 * gamma)
        - 0.002697 * np.cos(3 * gamma) + 0.001480 * np.sin(3 * gamma)
    )
    true_solar_minutes = hour * 60.0 + equation_of_time + 4.0 * longitude
    hour_angle = np.deg2rad((true_solar_minutes / 4.0) - 180.0)
    lat_rad = np.deg2rad(latitude)
    cos_zenith = (
        np.sin(lat_rad) * np.sin(declination)
        + np.cos(lat_rad) * np.cos(declination) * np.cos(hour_angle)
    )
    return float(np.rad2deg(np.arccos(np.clip(cos_zenith, -1.0, 1.0))))


def classify_scene(
    scene_tif: Path,
    region: dict[str, float],
    day_sza_threshold: float,
) -> tuple[str, float, str] | None:
    """Classify a scene as day/night using its UTC start and nadir footprint."""
    match = SCENE_TIME_RE.search(scene_tif.name)
    if match is None:
        return None
    when = datetime.strptime(match.group(1) + match.group(2), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    lat_path, lon_path = scene_tif / "lat_nadir.tif", scene_tif / "lon_nadir.tif"
    if not lat_path.is_file() or not lon_path.is_file():
        return None
    try:
        lat = scale_geolocation(read_band(lat_path))[::20, ::20]
        lon = scale_geolocation(read_band(lon_path))[::20, ::20]
    except Exception as exc:
        # A source raster can exist yet be unreadable (truncated/partial
        # write).  Skip that scene instead of aborting the whole year.
        print(f"skip unreadable geolocation {scene_tif.name}: {exc}", flush=True)
        return None
    valid = (
        np.isfinite(lat) & np.isfinite(lon)
        & (lon >= region["west"]) & (lon < region["east"])
        & (lat > region["south"]) & (lat <= region["north"])
    )
    if not np.any(valid):
        return None
    center_lat = float(np.median(lat[valid]))
    center_lon = float(np.median(lon[valid]))
    sza = solar_zenith_deg(when, center_lat, center_lon)
    label = "day" if sza < day_sza_threshold else "night"
    return label, sza, when.isoformat().replace("+00:00", "Z")


def scene_bounds(
    scene_tif: Path,
    scene_lst: Path,
    mode: str,
    region: dict[str, float],
    transformer: Transformer,
    grid: tuple[float, float, float, float, float, float, float],
) -> tuple[Path, Path, Path, tuple[int, int, int, int]] | None:
    lat_path = scene_tif / f"lat_{mode}.tif"
    lon_path = scene_tif / f"lon_{mode}.tif"
    value_path = scene_lst / f"lst_{mode}.tif"
    if not lat_path.is_file() or not lon_path.is_file() or not value_path.is_file():
        return None
    lat = scale_geolocation(read_band(lat_path))
    lon = scale_geolocation(read_band(lon_path))
    values = read_band(value_path)
    if lat.shape != values.shape or lon.shape != values.shape:
        return None
    valid = (
        np.isfinite(lat) & np.isfinite(lon) & np.isfinite(values)
        & (values > 0)
        & (lon >= region["west"]) & (lon < region["east"])
        & (lat > region["south"]) & (lat <= region["north"])
    )
    if not np.any(valid):
        return None
    x, y = transformer.transform(lon[valid], lat[valid])
    xmin, xmax, ymin, ymax, resolution, x0, ytop = grid
    # Snap the temporary scene extent to exactly the same daily grid.
    col0 = max(0, int(np.floor((x.min() - x0) / resolution)) - 1)
    col1 = min(int(np.ceil((xmax - x0) / resolution)), int(np.ceil((x.max() - x0) / resolution)) + 1)
    row0 = max(0, int(np.floor((ytop - y.max()) / resolution)) - 1)
    row1 = min(int(np.ceil((ytop - ymin) / resolution)), int(np.ceil((ytop - y.min()) / resolution)) + 1)
    if col1 <= col0 or row1 <= row0:
        return None
    return lat_path, lon_path, value_path, (row0, row1, col0, col1)


def warp_scene(
    vrt_path: Path,
    warp_path: Path,
    bounds: tuple[float, float, float, float],
    width: int,
    height: int,
    target_crs: CRS,
) -> np.ndarray:
    ds = gdal.Warp(
        str(warp_path), str(vrt_path),
        format="GTiff",
        outputBounds=bounds,
        width=width,
        height=height,
        dstSRS=target_crs.to_wkt(),
        geoloc=True,
        srcNodata=0.0,
        dstNodata=0.0,
        outputType=gdal.GDT_Float32,
        workingType=gdal.GDT_Float32,
        resampleAlg=gdal.GRA_Bilinear,
        multithread=True,
        warpMemoryLimit=512,
        creationOptions=["TILED=YES", "COMPRESS=DEFLATE"],
    )
    if ds is None:
        raise RuntimeError(f"GDAL Warp failed for {vrt_path}")
    array = ds.GetRasterBand(1).ReadAsArray().astype(np.float32)
    ds = None
    return array / 100.0


def write_raster(path: Path, data: np.ndarray, crs: CRS, geotransform: tuple[float, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ds = gdal.GetDriverByName("GTiff").Create(
        str(path), data.shape[1], data.shape[0], 1, gdal.GDT_Float32,
        options=["TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=IF_SAFER"],
    )
    if ds is None:
        raise RuntimeError(f"Cannot create {path}")
    ds.SetGeoTransform(geotransform)
    ds.SetProjection(crs.to_wkt())
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(0.0)
    band.WriteArray(data)
    band.FlushCache()
    ds.FlushCache()
    ds = None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--region-file", type=Path, default=DEFAULT_REGION)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--start-date", default="2017-01-18")
    parser.add_argument("--end-date", default="2017-01-18")
    parser.add_argument("--view", choices=("all", "nadir", "obliq"), default="all")
    parser.add_argument("--target-crs", default="EPSG:6933")
    parser.add_argument("--resolution-m", type=float, default=1000.0)
    parser.add_argument("--day-night", choices=("all", "day", "night"), default="all")
    parser.add_argument("--day-sza-threshold", type=float, default=85.0)
    parser.add_argument("--max-scenes", type=int, default=0, help="limit scenes per day for a quick test")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    region = load_region(args.region_file)
    start, end = parse_date(args.start_date), parse_date(args.end_date)
    grouped = discover_scenes(args.source_root, start, end)
    if not grouped:
        raise SystemExit("No usable LST scenes found")

    source_crs = CRS.from_epsg(4326)
    target_crs = CRS.from_user_input(args.target_crs)
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    corner_lon = np.array([region["west"], region["east"], region["west"], region["east"]])
    corner_lat = np.array([region["south"], region["south"], region["north"], region["north"]])
    cx, cy = transformer.transform(corner_lon, corner_lat)
    resolution = float(args.resolution_m)
    xmin, xmax = np.floor(cx.min() / resolution) * resolution, np.ceil(cx.max() / resolution) * resolution
    ymin, ymax = np.floor(cy.min() / resolution) * resolution, np.ceil(cy.max() / resolution) * resolution
    width, height = int(round((xmax - xmin) / resolution)), int(round((ymax - ymin) / resolution))
    grid = (xmin, xmax, ymin, ymax, resolution, xmin, ymax)
    geotransform = (xmin, resolution, 0.0, ymax, 0.0, -resolution)
    args.output_root.mkdir(parents=True, exist_ok=True)

    manifest = {
        "source_crs": source_crs.to_string(),
        "target_crs": target_crs.to_string(),
        "resampling": "GDAL bilinear",
        "scene_first": True,
        "resolution_m": resolution,
        "day_night_rule": f"solar zenith < {args.day_sza_threshold:g} degrees = day",
        "time_rule": "scene start UTC from RBT filename; one daily TIFF per category",
        "bounds_xy": [xmin, xmax, ymin, ymax],
        "width": width,
        "height": height,
        "days": {},
    }
    print(f"scene-first GDAL Warp: {source_crs.to_string()} -> {target_crs.to_string()}", flush=True)
    print(f"daily grid: {width} x {height} at {resolution:g} m; resampling=bilinear", flush=True)

    for day, all_scenes in grouped.items():
        scenes = all_scenes[:args.max_scenes] if args.max_scenes > 0 else all_scenes
        classified = []
        classification_manifest = {}
        for scene_tif, scene_lst in scenes:
            result = classify_scene(scene_tif, region, args.day_sza_threshold)
            if result is None:
                continue
            label, sza, timestamp = result
            classified.append((scene_tif, scene_lst, label))
            classification_manifest[scene_tif.name] = {
                "period": label,
                "solar_zenith_deg": round(sza, 3),
                "scene_start_utc": timestamp,
            }
        periods = ("day", "night") if args.day_night == "all" else (args.day_night,)
        day_results = {"scene_classification": classification_manifest}
        for period in periods:
            period_scenes = [(tif, lst) for tif, lst, label in classified if label == period]
            period_results = {}
            if not period_scenes:
                day_results[period] = {"input_scenes": 0, "status": "no scenes classified"}
                continue
            for mode in (("nadir", "obliq") if args.view == "all" else (args.view,)):
                output_dir = args.output_root / str(day.year) / period / mode
                # Exactly one daily LST TIFF for this day/period/view.
                output_path = output_dir / f"{day:%Y%m%d}_lst_daily.tif"
                count_path = output_dir / f"{day:%Y%m%d}_observation_count.tif"
                if output_path.exists() and count_path.exists() and not args.overwrite:
                    print(f"{day} {period} {mode}: skip existing", flush=True)
                    period_results[mode] = {"output": str(output_path), "status": "existing"}
                    continue
                sums = np.zeros((height, width), dtype=np.float32)
                counts = np.zeros((height, width), dtype=np.uint32)
                used, observations, warped_pixels = 0, 0, 0
                with tempfile.TemporaryDirectory(prefix=f"slstr_{day:%Y%m%d}_{period}_{mode}_") as tmp:
                    tmpdir = Path(tmp)
                    print(f"{day} {period} {mode}: warping {len(period_scenes)} scenes", flush=True)
                    for index, (scene_tif, scene_lst) in enumerate(period_scenes, start=1):
                        info = scene_bounds(scene_tif, scene_lst, mode, region, transformer, grid)
                        if info is None:
                            continue
                        lat_path, lon_path, value_path, (row0, row1, col0, col1) = info
                        vrt_path = tmpdir / f"scene_{index:03d}.vrt"
                        warp_path = tmpdir / f"scene_{index:03d}.tif"
                        # The source geolocation files are Int16 hundredths of a
                        # degree. GDAL's geolocation transformer reads raw band
                        # values, so provide explicitly scaled Float32 arrays.
                        lat_geo_path = tmpdir / f"scene_{index:03d}_lat_float.tif"
                        lon_geo_path = tmpdir / f"scene_{index:03d}_lon_float.tif"
                        write_geolocation_raster(lat_geo_path, scale_geolocation(read_band(lat_path)))
                        write_geolocation_raster(lon_geo_path, scale_geolocation(read_band(lon_path)))
                        make_geoloc_vrt(vrt_path, value_path, lon_geo_path, lat_geo_path)
                        local = warp_scene(
                            vrt_path, warp_path,
                            (xmin + col0 * resolution,
                             ymax - row1 * resolution,
                             xmin + col1 * resolution,
                             ymax - row0 * resolution),
                            col1 - col0, row1 - row0, target_crs,
                        )
                        valid = np.isfinite(local) & (local > 0)
                        if not np.any(valid):
                            continue
                        sums[row0:row1, col0:col1][valid] += local[valid]
                        counts[row0:row1, col0:col1][valid] += 1
                        used += 1
                        observations += int(np.count_nonzero(valid))
                        warped_pixels += int(local.size)
                        if index % 5 == 0 or index == len(period_scenes):
                            print(f"  {index}/{len(period_scenes)} scenes, warped={used}, valid={observations}", flush=True)
                mosaic = np.zeros_like(sums)
                valid = counts > 0
                mosaic[valid] = sums[valid] / counts[valid]
                write_raster(output_path, mosaic, target_crs, geotransform)
                write_raster(count_path, counts.astype(np.float32), target_crs, geotransform)
                period_results[mode] = {
                    "output": str(output_path),
                    "count_output": str(count_path),
                    "input_scenes": len(period_scenes),
                    "warped_scenes": used,
                    "warped_pixels": warped_pixels,
                    "valid_resampled_pixels": observations,
                    "valid_daily_pixels": int(np.count_nonzero(valid)),
                    "max_count": int(counts.max()),
                }
            day_results[period] = period_results
        manifest["days"][day.isoformat()] = day_results

    (args.output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"manifest: {args.output_root / 'manifest.json'}")


if __name__ == "__main__":
    main()
