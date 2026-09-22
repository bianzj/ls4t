#!/usr/bin/env python3
"""Create scene-first projected daily nadir, LSCT, and overpass-time TIFFs.

For each UTC date and day/night class, scenes are ordered by acquisition start
time.  Valid pixels from later scenes overwrite earlier pixels; no averaging
or count raster is produced.  Temperature TIFFs are UInt16 values in K*100,
and time TIFFs are UInt32 HHMMSS values.
"""

from __future__ import annotations

import argparse
import json
import re
import os
import tempfile
from datetime import date
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
from south_america_daily_mosaic_gdalwarp import (
    classify_scene,
    make_geoloc_vrt,
    solar_zenith_deg,
    write_geolocation_raster,
)


DEFAULT_ROOT = Path("/media/hero/slstr-southA-lst")
DEFAULT_REGION = Path(__file__).with_name("south_america_tropical_amazon.geojson")
DEFAULT_OUTPUT = Path("/media/hero/slstr-southA-lst/south_america_tropical_nadir_lsct_time")
SCENE_TIME_RE = re.compile(r"RBT____(\d{8})T(\d{6})")


def make_multiband_geoloc_vrt(
    vrt_path: Path, data_path: Path, lon_path: Path, lat_path: Path, bands: int
) -> None:
    ds = gdal.Open(str(data_path), gdal.GA_ReadOnly)
    if ds is None:
        raise RuntimeError(f"Cannot open {data_path}")
    width, height = ds.RasterXSize, ds.RasterYSize
    dtype = gdal.GetDataTypeName(ds.GetRasterBand(1).DataType)
    ds = None
    band_xml = []
    for band in range(1, bands + 1):
        band_xml.append(
            f'''  <VRTRasterBand dataType="{dtype}" band="{band}">
    <NoDataValue>0</NoDataValue>
    <SimpleSource>
      <SourceFilename relativeToVRT="0">{data_path}</SourceFilename>
      <SourceBand>{band}</SourceBand>
    </SimpleSource>
  </VRTRasterBand>'''
        )
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
{chr(10).join(band_xml)}
</VRTDataset>
''',
        encoding="utf-8",
    )


def projected_scene_bounds(
    lat_path: Path,
    lon_path: Path,
    data_path: Path,
    region: dict[str, float],
    transformer: Transformer,
    grid: tuple[float, float, float, float, float, float, float],
) -> tuple[Path, Path, Path, tuple[int, int, int, int]] | None:
    if not lat_path.is_file() or not lon_path.is_file() or not data_path.is_file():
        return None
    try:
        lat = scale_geolocation(read_band(lat_path))
        lon = scale_geolocation(read_band(lon_path))
        data_ds = gdal.Open(str(data_path), gdal.GA_ReadOnly)
    except Exception as exc:
        # Unreadable (but present) source rasters must not abort the year.
        print(f"skip unreadable raster {data_path.name} for {data_path.parent.name}: {exc}", flush=True)
        return None
    if data_ds is None:
        return None
    data_height, data_width = data_ds.RasterYSize, data_ds.RasterXSize
    data_ds = None
    if lat.shape != (data_height, data_width) or lon.shape != (data_height, data_width):
        return None
    valid = (
        np.isfinite(lat) & np.isfinite(lon)
        & (lon >= region["west"]) & (lon < region["east"])
        & (lat > region["south"]) & (lat <= region["north"])
    )
    if not np.any(valid):
        return None
    x, y = transformer.transform(lon[valid], lat[valid])
    xmin, xmax, ymin, ymax, resolution, x0, ytop = grid
    col0 = max(0, int(np.floor((x.min() - x0) / resolution)) - 1)
    col1 = min(int(np.ceil((xmax - x0) / resolution)), int(np.ceil((x.max() - x0) / resolution)) + 1)
    row0 = max(0, int(np.floor((ytop - y.max()) / resolution)) - 1)
    row1 = min(int(np.ceil((ytop - ymin) / resolution)), int(np.ceil((ytop - y.min()) / resolution)) + 1)
    if col1 <= col0 or row1 <= row0:
        return None
    return lat_path, lon_path, data_path, (row0, row1, col0, col1)


def warp_scene(
    vrt_path: Path,
    output_path: Path,
    bounds: tuple[float, float, float, float],
    width: int,
    height: int,
    target_crs: CRS,
    bands: int = 1,
) -> np.ndarray:
    ds = gdal.Warp(
        str(output_path), str(vrt_path),
        format="GTiff", outputBounds=bounds, width=width, height=height,
        dstSRS=target_crs.to_wkt(), geoloc=True,
        srcNodata=0.0, dstNodata=0.0, outputType=gdal.GDT_Float32,
        workingType=gdal.GDT_Float32, resampleAlg=gdal.GRA_Bilinear,
        multithread=True, warpMemoryLimit=512,
        creationOptions=["TILED=YES", "COMPRESS=DEFLATE"],
    )
    if ds is None:
        raise RuntimeError(f"GDAL Warp failed for {vrt_path}")
    result = ds.GetRasterBand(1).ReadAsArray().astype(np.float32)
    if bands > 1:
        result = np.stack([
            ds.GetRasterBand(index).ReadAsArray().astype(np.float32)
            for index in range(1, bands + 1)
        ])
    ds = None
    return result


def write_temperature(path: Path, data_kelvin: np.ndarray, crs: CRS, geotransform: tuple[float, ...]) -> None:
    encoded = np.zeros(data_kelvin.shape, dtype=np.uint16)
    valid = np.isfinite(data_kelvin) & (data_kelvin > 0)
    encoded[valid] = np.clip(np.rint(data_kelvin[valid] * 100.0), 0, 65535).astype(np.uint16)
    path.parent.mkdir(parents=True, exist_ok=True)
    ds = gdal.GetDriverByName("GTiff").Create(
        str(path), encoded.shape[-1], encoded.shape[-2],
        1 if encoded.ndim == 2 else encoded.shape[0], gdal.GDT_UInt16,
        options=["TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=IF_SAFER"],
    )
    ds.SetGeoTransform(geotransform)
    ds.SetProjection(crs.to_wkt())
    for index in range(1 if encoded.ndim == 2 else encoded.shape[0]):
        band = ds.GetRasterBand(index + 1)
        band.SetNoDataValue(0)
        band.WriteArray(encoded if encoded.ndim == 2 else encoded[index])
        band.FlushCache()
    ds.FlushCache()
    ds = None


def write_time(path: Path, data: np.ndarray, crs: CRS, geotransform: tuple[float, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ds = gdal.GetDriverByName("GTiff").Create(
        str(path), data.shape[1], data.shape[0], 1, gdal.GDT_UInt32,
        options=["TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=IF_SAFER"],
    )
    ds.SetGeoTransform(geotransform)
    ds.SetProjection(crs.to_wkt())
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(0)
    band.WriteArray(data.astype(np.uint32, copy=False))
    band.FlushCache()
    ds.FlushCache()
    ds = None


def scene_timestamp(scene_name: str) -> tuple[str, int] | None:
    match = SCENE_TIME_RE.search(scene_name)
    if match is None:
        return None
    hhmmss = match.group(2)
    return f"{match.group(1)}T{hhmmss[:2]}:{hhmmss[2:4]}:{hhmmss[4:]}Z", int(hhmmss)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--region-file", type=Path, default=DEFAULT_REGION)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--start-date", default="2017-01-01")
    parser.add_argument("--end-date", default="2017-12-31")
    parser.add_argument("--target-crs", default="EPSG:6933")
    parser.add_argument("--resolution-m", type=float, default=1000.0)
    parser.add_argument("--day-sza-threshold", type=float, default=85.0)
    parser.add_argument("--max-scenes", type=int, default=0,
                        help="limit scenes per day for a quick test")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    region = load_region(args.region_file)
    start, end = parse_date(args.start_date), parse_date(args.end_date)
    grouped = discover_scenes(args.source_root, start, end)
    if not grouped:
        raise SystemExit("No usable LST scenes found")
    source_crs, target_crs = CRS.from_epsg(4326), CRS.from_user_input(args.target_crs)
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
        "source_crs": source_crs.to_string(), "target_crs": target_crs.to_string(),
        "scene_first": True, "resampling": "GDAL bilinear",
        "overwrite_rule": "later valid scene pixels overwrite earlier pixels; no average",
        "temperature_encoding": "UInt16 = Kelvin * 100",
        "time_encoding": "UInt32 = UTC HHMMSS from scene start timestamp",
        "day_night_rule": f"solar zenith < {args.day_sza_threshold:g} degrees = day",
        "resolution_m": resolution, "bounds_xy": [xmin, xmax, ymin, ymax],
        "width": width, "height": height, "days": {},
    }
    print(f"scene-first nadir/LSCT/time: {len(grouped)} days", flush=True)

    for day, all_scenes in grouped.items():
        scenes = sorted(all_scenes, key=lambda pair: pair[0].name)
        if args.max_scenes > 0:
            scenes = scenes[:args.max_scenes]
        classified = []
        class_manifest = {}
        for scene_tif, scene_lst in scenes:
            result = classify_scene(scene_tif, region, args.day_sza_threshold)
            stamp = scene_timestamp(scene_tif.name)
            if result is None or stamp is None:
                continue
            period, sza, _ = result
            timestamp, hhmmss = stamp
            classified.append((scene_tif, scene_lst, period, timestamp, hhmmss))
            class_manifest[scene_tif.name] = {
                "period": period, "solar_zenith_deg": round(sza, 3),
                "scene_start_utc": timestamp,
            }
        day_manifest = {"scene_classification": class_manifest}
        for period in ("day", "night"):
            period_scenes = [item for item in classified if item[2] == period]
            if not period_scenes:
                day_manifest[period] = {"status": "no scenes"}
                continue
            output_dir = args.output_root / str(day.year) / period
            output_paths = {
                "nadir": output_dir / f"{day:%Y%m%d}_nadir.tif",
                "lsct": output_dir / f"{day:%Y%m%d}_lsct.tif",
                "time": output_dir / f"{day:%Y%m%d}_time.tif",
            }
            if all(path.exists() for path in output_paths.values()) and not args.overwrite:
                day_manifest[period] = {"status": "existing", **{key: str(value) for key, value in output_paths.items()}}
                continue
            nadir = np.zeros((height, width), dtype=np.float32)
            lsct = np.zeros((2, height, width), dtype=np.float32)
            time_grid = np.zeros((height, width), dtype=np.uint32)
            used_nadir = used_lsct = 0
            with tempfile.TemporaryDirectory(prefix=f"slstr_{day:%Y%m%d}_{period}_") as tmp:
                tmpdir = Path(tmp)
                for index, (scene_tif, scene_lst, _, timestamp, hhmmss) in enumerate(period_scenes, start=1):
                    # Nadir LST uses nadir geolocation.
                    lst_path = scene_lst / "lst_nadir.tif"
                    info = projected_scene_bounds(
                        scene_tif / "lat_nadir.tif", scene_tif / "lon_nadir.tif",
                        lst_path, region, transformer, grid,
                    ) if lst_path.is_file() else None
                    if info is not None:
                        lat_path, lon_path, data_path, (row0, row1, col0, col1) = info
                        lat_float = tmpdir / f"{index:04d}_n_lat.tif"
                        lon_float = tmpdir / f"{index:04d}_n_lon.tif"
                        write_geolocation_raster(lat_float, scale_geolocation(read_band(lat_path)))
                        write_geolocation_raster(lon_float, scale_geolocation(read_band(lon_path)))
                        vrt = tmpdir / f"{index:04d}_n.vrt"
                        warp = tmpdir / f"{index:04d}_n.tif"
                        try:
                            make_geoloc_vrt(vrt, data_path, lon_float, lat_float)
                            local = warp_scene(
                                vrt, warp,
                                (xmin + col0 * resolution, ymax - row1 * resolution,
                                 xmin + col1 * resolution, ymax - row0 * resolution),
                                col1 - col0, row1 - row0, target_crs,
                            ) / 100.0
                        except Exception as exc:
                            print(f"skip nadir Warp {scene_tif.name}: {exc}", flush=True)
                            local = None
                        if local is not None:
                            valid = np.isfinite(local) & (local > 0)
                            if np.any(valid):
                                nadir[row0:row1, col0:col1][valid] = local[valid]
                                time_grid[row0:row1, col0:col1][valid] = hhmmss
                                used_nadir += 1

                    # LSCT is stored on the oblique 900x1200 geolocation grid.
                    lsct_path = args.source_root / str(day.year) / "lsct2" / scene_tif.name / "lsct2.tif"
                    info = projected_scene_bounds(
                        scene_tif / "lat_obliq.tif", scene_tif / "lon_obliq.tif",
                        lsct_path, region, transformer, grid,
                    ) if lsct_path.is_file() else None
                    if info is not None:
                        lat_path, lon_path, data_path, (row0, row1, col0, col1) = info
                        lat_float = tmpdir / f"{index:04d}_o_lat.tif"
                        lon_float = tmpdir / f"{index:04d}_o_lon.tif"
                        write_geolocation_raster(lat_float, scale_geolocation(read_band(lat_path)))
                        write_geolocation_raster(lon_float, scale_geolocation(read_band(lon_path)))
                        vrt = tmpdir / f"{index:04d}_o.vrt"
                        warp = tmpdir / f"{index:04d}_o.tif"
                        try:
                            make_multiband_geoloc_vrt(vrt, data_path, lon_float, lat_float, 2)
                            local = warp_scene(
                                vrt, warp,
                                (xmin + col0 * resolution, ymax - row1 * resolution,
                                 xmin + col1 * resolution, ymax - row0 * resolution),
                                col1 - col0, row1 - row0, target_crs, bands=2,
                            )
                        except Exception as exc:
                            print(f"skip LSCT Warp {scene_tif.name}: {exc}", flush=True)
                            local = None
                        if local is not None:
                            valid = np.isfinite(local) & (local > 0)
                            if np.any(valid):
                                for band in range(2):
                                    lsct[band, row0:row1, col0:col1][valid[band]] = local[band][valid[band]]
                                # Later valid scene pixels overwrite earlier
                                # pixels, including their matching overpass time.
                                lsct_time = valid.any(axis=0)
                                time_grid[row0:row1, col0:col1][lsct_time] = hhmmss
                                used_lsct += 1
                    if index % 10 == 0 or index == len(period_scenes):
                        print(f"{day} {period}: {index}/{len(period_scenes)} scenes", flush=True)
            write_temperature(output_paths["nadir"], nadir, target_crs, geotransform)
            write_temperature(output_paths["lsct"], lsct, target_crs, geotransform)
            write_time(output_paths["time"], time_grid, target_crs, geotransform)
            day_manifest[period] = {
                "status": "written", "input_scenes": len(period_scenes),
                "used_nadir_scenes": used_nadir, "used_lsct_scenes": used_lsct,
                **{key: str(value) for key, value in output_paths.items()},
            }
        manifest["days"][day.isoformat()] = day_manifest

    (args.output_root / str(start.year) / "manifest.json").parent.mkdir(parents=True, exist_ok=True)
    (args.output_root / str(start.year) / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"manifest: {args.output_root / str(start.year) / 'manifest.json'}", flush=True)


if __name__ == "__main__":
    main()
