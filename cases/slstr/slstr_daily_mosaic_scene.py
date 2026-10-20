#!/usr/bin/env python3
"""Daily scene-first LST / LSCT2 mosaics for one LS4T SLSTR case.

One implementation for every region: the case directory supplies the window,
the product list, the day/night rule and the cloud policy (``case.toml`` plus
``machines/<machine>.toml``), this script does the work.  Every scene is
**warped to the case grid first** (GDAL geolocation VRT -> ``gdal.Warp`` with
the per-scene ``lat_*/lon_*.tif`` pair as geolocation) and only then composited
into a daily raster.  Each scene is classified as day or night from its UTC
acquisition time and footprint centre, so every day can produce up to four
files:

    <out>/lst/<year>/<YYYYMMDD>_lst_nadir_{day,night}_<region>_0p01.tif
    <out>/lsct/<year>/<YYYYMMDD>_lsct2_obliq_{day,night}_<region>_0p01.tif
    <out>/time/<year>/<YYYYMMDD>_{day,night}_time_<region>_0p01.tif

Within a class, scenes are ordered by acquisition time and later scenes
overwrite earlier ones where they overlap.  Cloudy retrievals are dropped by
default (the scene cloud flag travels through the same warp); ``--no-cloud-mask``
composites every retrieval, which is what the first EURO product did.

usage:
  PYTHONPATH=. python cases/slstr/slstr_daily_mosaic_scene.py \
      --case cases/slstr-heihe --year 2020 --workers 16
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import warnings
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from base.slstr.slstr_scene_skip import is_useless, load_scene_skip

os.environ.setdefault("PROJ_LIB", "/usr/share/proj")
from osgeo import gdal
from pyproj import CRS
from rasterio.transform import from_origin

gdal.UseExceptions()
warnings.filterwarnings("ignore")

PRODUCTS = {
    "lst": dict(subdir="lst", file="lst_nadir.tif", view="nadir", bands=1,
                dtype=np.uint16, gdal_type=gdal.GDT_UInt16, label="lst_nadir"),
    "lsct": dict(subdir="lsct", file="lsct2.tif", view="obliq", bands=2,
                 dtype=np.float32, gdal_type=gdal.GDT_Float32, label="lsct2_obliq"),
}

# case.toml -> PRODUCTS keys
CASE_PRODUCTS = {"lst_nadir": "lst", "lsct": "lsct"}
SCENE_TIME_RE = re.compile(r"RBT____(\d{8})T(\d{6})")


def load_case(case_dir: Path, machine: str) -> dict:
    """Read one case: grid window from case.toml, roots from the machine profile."""
    import tomllib

    case_dir = Path(case_dir).resolve()
    case = tomllib.loads((case_dir / "case.toml").read_text())
    profile = tomllib.loads((case_dir / "machines" / f"{machine}.toml").read_text())
    grid = case.get("grid", {})
    processing = case.get("processing", {})
    west, south, east, north = (float(v) for v in grid["bounds"])
    res = float(grid.get("resolution_degree", 0.01))
    products = []
    for name in processing.get("products", ["lst_nadir", "lsct"]):
        key = CASE_PRODUCTS.get(name)
        if key and key not in products:
            products.append(key)
    return dict(
        case_id=case["case"]["id"],
        region=case["case"].get("region", "region"),
        source_root=Path(profile["paths"]["scene_root"]),
        output_root=Path(profile["paths"]["output_root"]),
        window=dict(west=west, east=east, south=south, north=north, res=res),
        products=products,
        years=[int(y) for y in case.get("period", {}).get("years", [])],
        sza_threshold=float(processing.get("day_solar_zenith_threshold", 90.0)),
        cloud_mask=bool(processing.get("mosaic_cloud_mask", True)),
    )


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def load_window(path: Path) -> dict:
    data = json.loads(path.read_text())
    return dict(west=float(data["west"]), east=float(data["east"]),
                south=float(data["south"]), north=float(data["north"]),
                res=float(data["grid_resolution_degree"]))


def scene_day(scene: str) -> str:
    return scene.split("____")[1][:8]


def scene_hhmmss(scene: str) -> int:
    """Acquisition start time of the granule as HHMMSS (the time of every pixel
    it contributes; the disk has no per-pixel time band)."""
    t = scene.split("____")[1][9:15]
    return int(t)


def day_scenes(root: Path, year: int, product: str) -> dict[str, list[str]]:
    spec = PRODUCTS[product]
    base = root / str(year) / spec["subdir"]
    by_day: dict[str, list[str]] = defaultdict(list)
    if not base.is_dir():
        return by_day
    # scenes the coverage audit discarded for this product's view are skipped
    # before their geolocation pair is read again
    no_land = load_scene_skip(root, year)
    with os.scandir(base) as entries:
        names = [e.name for e in entries if e.is_dir(follow_symlinks=True)]
    for scene in names:
        if is_useless(no_land, scene, (spec["view"],)):
            continue
        if (base / scene / spec["file"]).is_file():
            by_day[scene_day(scene)].append(scene)
    for day in by_day:
        by_day[day].sort(key=lambda s: s.split("____")[1][9:15])
    return by_day


def make_geoloc_vrt(vrt_path: Path, lon_path: Path, lat_path: Path,
                    sources: list[tuple[Path, int]]) -> None:
    """VRT of ``sources`` ((path, band) pairs) with the lon/lat pair as geolocation.

    The cloud flag travels through the same VRT as the product band, so one
    ``gdal.Warp`` reads the data and its mask and the two cannot drift apart.
    """
    first = gdal.Open(str(sources[0][0]), gdal.GA_ReadOnly)
    if first is None:
        raise RuntimeError(f"cannot open {sources[0][0]}")
    width, height = first.RasterXSize, first.RasterYSize
    first = None
    bands_xml = []
    for index, (path, band) in enumerate(sources, 1):
        ds = gdal.Open(str(path), gdal.GA_ReadOnly)
        if ds is None:
            raise RuntimeError(f"cannot open {path}")
        gdal_type = gdal.GetDataTypeName(ds.GetRasterBand(band).DataType)
        ds = None
        bands_xml.append(f'''  <VRTRasterBand dataType="{gdal_type}" band="{index}">
    <NoDataValue>0</NoDataValue>
    <SimpleSource>
      <SourceFilename relativeToVRT="0">{path}</SourceFilename>
      <SourceBand>{band}</SourceBand>
    </SimpleSource>
  </VRTRasterBand>''')
    band_xml = "\n".join(bands_xml)
    xml = f'''<VRTDataset rasterXSize="{width}" rasterYSize="{height}">
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
{band_xml}
</VRTDataset>
'''
    if str(vrt_path).startswith("/vsimem/"):
        gdal.FileFromMemBuffer(str(vrt_path), xml.encode("utf-8"))
    else:
        vrt_path.write_text(xml, encoding="utf-8")


def write_geolocation_raster(path: Path, array: np.ndarray, limit: float) -> None:
    """Materialise integer hundredths-of-degree geolocation as Float32 degrees.

    GDAL reads the geolocation arrays as plain degrees, so the x100 storage has
    to be unpacked first; invalid fill values become NaN.
    """
    array = np.asarray(array, dtype=np.float32) / 100.0
    array[(array < -limit) | (array > limit)] = np.nan
    driver = gdal.GetDriverByName("GTiff")
    ds = driver.Create(str(path), array.shape[1], array.shape[0], 1, gdal.GDT_Float32,
                       options=["TILED=NO"])
    if ds is None:
        raise RuntimeError(f"cannot create {path}")
    ds.GetRasterBand(1).WriteArray(array)
    ds.GetRasterBand(1).FlushCache()
    ds = None


def write_array_raster(path: Path, array: np.ndarray, gdal_type: int) -> None:
    """In-memory copy of a scene band (used for the cropped LST window)."""
    driver = gdal.GetDriverByName("GTiff")
    ds = driver.Create(str(path), array.shape[1], array.shape[0], 1, gdal_type)
    if ds is None:
        raise RuntimeError(f"cannot create {path}")
    ds.GetRasterBand(1).WriteArray(array)
    ds.GetRasterBand(1).FlushCache()
    ds = None


def read_full(path: Path) -> np.ndarray:
    ds = gdal.Open(str(path), gdal.GA_ReadOnly)
    if ds is None:
        raise RuntimeError(f"cannot open {path}")
    array = ds.GetRasterBand(1).ReadAsArray()
    ds = None
    return array


def read_rows(path: Path, rows=None) -> np.ndarray:
    # NB: gdal.Dataset has no context-manager protocol in this GDAL build
    ds = gdal.Open(str(path), gdal.GA_ReadOnly)
    if ds is None:
        raise RuntimeError(f"cannot open {path}")
    height, width = ds.RasterYSize, ds.RasterXSize
    if rows is None:                      # enough rows to bracket a slanted swath
        rows = list(range(0, height, 100)) + [height - 1]
    out = []
    for r in rows:
        r = height - 1 if r < 0 else r
        out.append(ds.GetRasterBand(1).ReadAsArray(0, r, width, 1)[0])
    ds = None
    return np.concatenate(out).astype("float32") / 100.0


def footprint_box(root: Path, year: int, scene: str, view: str):
    tif = root / str(year) / "tif" / scene
    lon_path, lat_path = tif / f"lon_{view}.tif", tif / f"lat_{view}.tif"
    if not lon_path.is_file() or not lat_path.is_file():
        return None, lon_path, lat_path
    try:
        lon, lat = read_rows(lon_path), read_rows(lat_path)
    except Exception:
        return None, lon_path, lat_path
    ok = np.isfinite(lon) & np.isfinite(lat) & (np.abs(lon) <= 360) & (np.abs(lat) <= 90.5)
    if not ok.any():
        return None, lon_path, lat_path
    return (float(lon[ok].min()), float(lon[ok].max()),
            float(lat[ok].min()), float(lat[ok].max()), lon, lat, ok), lon_path, lat_path


def solar_zenith_deg(when: datetime, lat, lon):
    """Solar zenith angle (deg) - same formulas as the South America case."""
    day = (when - datetime(when.year, 1, 1, tzinfo=timezone.utc)).total_seconds() / 86400.0
    hour = when.hour + when.minute / 60.0 + when.second / 3600.0
    gamma = 2.0 * math.pi / 365.0 * (day + (hour - 12.0) / 24.0)
    eqtime = 229.18 * (0.000075 + 0.001868 * np.cos(gamma) - 0.032077 * np.sin(gamma)
                       - 0.014615 * np.cos(2 * gamma) - 0.040849 * np.sin(2 * gamma))
    decl = (0.006918 - 0.399912 * np.cos(gamma) + 0.070257 * np.sin(gamma)
            - 0.006758 * np.cos(2 * gamma) + 0.000907 * np.sin(2 * gamma)
            - 0.002697 * np.cos(3 * gamma) + 0.00148 * np.sin(3 * gamma))
    time_offset = eqtime + 4.0 * np.asarray(lon) - 60.0 * when.utcoffset().total_seconds() / 3600.0
    tst = (hour * 60.0 + time_offset) / 60.0
    ha = np.radians((tst - 12.0) * 15.0)
    latr = np.radians(np.asarray(lat))
    cosz = np.sin(latr) * np.sin(decl) + np.cos(latr) * np.cos(decl) * np.cos(ha)
    return np.degrees(np.arccos(np.clip(cosz, -1.0, 1.0)))


def scene_is_day(scene: str, box, win: dict, threshold: float) -> bool:
    """Day when the median solar zenith angle of the footprint is below the threshold."""
    lon0, lon1, lat0, lat1, lon, lat, ok = box
    match = SCENE_TIME_RE.search(scene)
    if match is None:
        return True
    when = datetime.strptime(match.group(1) + match.group(2), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    inside = ok & (lon >= win["west"]) & (lon <= win["east"]) & (lat >= win["south"]) & (lat <= win["north"])
    if inside.sum() < 50:
        # a scene that barely clips the window: classify it at its own centre
        # instead of defaulting to day, which used to leak evening granules in
        sza = solar_zenith_deg(when, np.asarray([np.nanmedian(lat[ok])]),
                               np.asarray([np.nanmedian(lon[ok])]))
        return bool(np.nanmedian(sza) < threshold)
    sza = solar_zenith_deg(when, lat[inside][::25], lon[inside][::25])
    return bool(np.nanmedian(sza) < threshold)


def warp_block(root: Path, year: int, scene: str, spec: dict, lon_path: Path,
               lat_path: Path, data_path: Path, window_box, tmpdir: Path,
               cloud_path: Path | None = None) -> np.ndarray | None:
    """Warp one scene onto the requested sub-grid; returns the warped block.

    With ``cloud_path`` the scene cloud flag is warped alongside the product and
    any pixel that is not clear (``cloud != 0``) is dropped.
    """
    west, south, east, north, width, height = window_box
    # keep the temporary geolocation rasters in memory (/vsimem): writing them
    # to the data disk was the dominant cost of the first version
    # everything temporary lives in /vsimem: thousands of tiny VRT files on the
    # data disk made the HDD thrash without transferring anything
    vrt = Path(f"/vsimem/{scene}.vrt")
    lon_deg = Path(f"/vsimem/{scene}.lon.tif")
    lat_deg = Path(f"/vsimem/{scene}.lat.tif")
    cropped = Path(f"/vsimem/{scene}.{spec['label']}.tif")
    created = []
    try:
        write_geolocation_raster(lon_deg, read_full(lon_path), 360.0)
        write_geolocation_raster(lat_deg, read_full(lat_path), 90.5)
        created += [lon_deg, lat_deg]
        if spec.get("crop"):
            crop = spec["crop"]
            block_in = read_full(data_path)[crop]
            write_array_raster(cropped, block_in, gdal.GDT_UInt16)
            created.append(cropped)
            data_src = cropped
        else:
            data_src = data_path
        sources = [(data_src, band) for band in range(1, spec["bands"] + 1)]
        if cloud_path is not None:
            sources.append((cloud_path, 1))
        make_geoloc_vrt(vrt, lon_deg, lat_deg, sources)
        created.append(vrt)
        try:
            ds = gdal.Warp(
                "", str(vrt), format="MEM", outputBounds=(west, south, east, north),
                width=width, height=height, dstSRS="EPSG:4326", geoloc=True,
                srcNodata=0.0, dstNodata=0.0, outputType=spec["gdal_type"],
                workingType=gdal.GDT_Float32,
                resampleAlg=gdal.GRA_NearestNeighbour, multithread=True,
                warpMemoryLimit=256,
            )
        except RuntimeError:
            # e.g. a scene whose geolocation is entirely fill values: the warp
            # cannot be built, the scene is simply skipped
            return None
    finally:
        for path in created:
            try:
                if str(path).startswith("/vsimem/"):
                    gdal.Unlink(str(path))
                else:
                    path.unlink()
            except Exception:
                pass
    if ds is None:
        return None
    array = ds.ReadAsArray()
    ds = None
    if cloud_path is None:
        return array
    data, cloud = array[:spec["bands"]], array[spec["bands"]]
    data = np.where(cloud == 0, data, 0)
    return data if spec["bands"] > 1 else data[0]


def composite_day(task) -> dict:
    (year, day, scenes_by_product, root, out_root, win, products, sza_threshold,
     overwrite, write_time, cloud_mask, region) = task
    # a day that is already finished is not read again on a resume
    marker = out_root / "_done" / str(year) / f"{day}.json"
    if marker.exists() and not overwrite:
        try:
            return json.loads(marker.read_text())
        except Exception:
            pass
    ny = int(round((win["north"] - win["south"]) / win["res"]))
    nx = int(round((win["east"] - win["west"]) / win["res"]))
    acc, used, pixels, skipped = {}, {}, {}, {}
    for product in products:
        spec = PRODUCTS[product]
        shape = (spec["bands"], ny, nx) if spec["bands"] > 1 else (ny, nx)
        acc[product] = {"day": np.zeros(shape, dtype=spec["dtype"]),
                        "night": np.zeros(shape, dtype=spec["dtype"])}
        used[product] = {"day": 0, "night": 0}
        pixels[product] = {"day": 0, "night": 0}
        skipped[product] = []
    # one overpass-time raster per day and class, shared by every product:
    # all products of a day come from the same observations
    times = {"day": np.zeros((ny, nx), dtype=np.uint32),
             "night": np.zeros((ny, nx), dtype=np.uint32)}
    tmpdir = Path("/vsimem")          # only used to derive unique temp names

    for product in products:
        spec = PRODUCTS[product]
        for scene in scenes_by_product[product]:
            try:
                data_path = root / str(year) / spec["subdir"] / scene / spec["file"]
                box, lon_path, lat_path = footprint_box(root, year, scene, spec["view"])
                if box is None or not data_path.is_file():
                    continue
            except Exception as exc:      # unreadable geolocation
                skipped[product].append(f"{scene}: {exc}")
                continue
            lon0, lon1, lat0, lat1 = box[0], box[1], box[2], box[3]
            if lon1 < win["west"] or lon0 > win["east"] or lat1 < win["south"] or lat0 > win["north"]:
                continue
            col0 = max(0, int(math.floor((lon0 - win["west"]) / win["res"])))
            col1 = min(nx, int(math.ceil((lon1 - win["west"]) / win["res"])) + 1)
            row0 = max(0, int(math.floor((win["north"] - lat1) / win["res"])))
            row1 = min(ny, int(math.ceil((win["north"] - lat0) / win["res"])) + 1)
            if col1 <= col0 or row1 <= row0:
                continue
            west = win["west"] + col0 * win["res"]
            north = win["north"] - row0 * win["res"]
            east = win["west"] + col1 * win["res"]
            south = win["north"] - row1 * win["res"]
            cls = "day" if scene_is_day(scene, box, win, sza_threshold) else "night"
            stamp = scene_hhmmss(scene)
            cloud_path = None
            if cloud_mask:
                candidate = root / str(year) / "tif" / scene / f"cloud_{spec['view']}.tif"
                cloud_path = candidate if candidate.is_file() else None
            try:
                block = warp_block(root, year, scene, spec, lon_path, lat_path, data_path,
                                   (west, south, east, north, col1 - col0, row1 - row0),
                                   tmpdir, cloud_path)
            except Exception as exc:
                # a zero byte or truncated product must not kill the whole year
                skipped[product].append(f"{scene}: {exc}")
                continue
            if block is None:
                skipped[product].append(scene)
                continue
            view = acc[product][cls]
            if spec["bands"] == 1:
                target = view[row0:row1, col0:col1]
                valid = block > 0
                target[valid] = block[valid]
                pixels[product][cls] += int(valid.sum())
                if write_time:
                    times[cls][row0:row1, col0:col1][valid] = stamp
            else:
                first = None
                for b in range(spec["bands"]):
                    target = view[b][row0:row1, col0:col1]
                    valid = block[b] > 0
                    target[valid] = block[b][valid]
                    if first is None:
                        first = valid
                        pixels[product][cls] += int(valid.sum())
                if write_time and first is not None:
                    times[cls][row0:row1, col0:col1][first] = stamp
            used[product][cls] += 1

    out = dict(day=day, scenes={p: len(scenes_by_product[p]) for p in products},
               skipped=skipped, files={p: {} for p in products})
    time_paths = {}
    for cls in ("day", "night"):
        if write_time and (times[cls] > 0).any():
            path = out_root / "time" / str(year) / f"{day}_{cls}_time_{region}_0p01.tif"
            path.parent.mkdir(parents=True, exist_ok=True)
            time_paths[cls] = str(path)
            if overwrite or not path.exists():
                write_raster(path, times[cls], gdal.GDT_UInt32, win["res"], False, win)
        else:
            time_paths[cls] = None
    for product in products:
        spec = PRODUCTS[product]
        out_dir = out_root / product / str(year)
        out_dir.mkdir(parents=True, exist_ok=True)
        for cls in ("day", "night"):
            entry = dict(used=used[product][cls], pixels=pixels[product][cls],
                         written=False, path=None, time_path=time_paths[cls],
                         skipped=len(skipped[product]))
            out["files"][product][cls] = entry
            if used[product][cls] == 0 or pixels[product][cls] == 0:
                continue
            path = out_dir / f"{day}_{spec['label']}_{cls}_{region}_0p01.tif"
            entry.update(written=True, path=str(path))
            if not overwrite and path.exists():
                continue
            write_raster(path, acc[product][cls], spec["gdal_type"], win["res"],
                         spec["gdal_type"] == gdal.GDT_UInt16, win)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps(out, indent=1))
    return out


def write_raster(path: Path, array: np.ndarray, gdal_type: int, res: float,
                 uint16_predictor: bool, win: dict) -> None:
    driver = gdal.GetDriverByName("GTiff")
    bands = 1 if array.ndim == 2 else array.shape[0]
    options = ["TILED=YES", "COMPRESS=DEFLATE"]
    if uint16_predictor:
        options.append("PREDICTOR=2")
    ds = driver.Create(str(path), array.shape[-1], array.shape[-2], bands, gdal_type,
                       options=options)
    ds.SetGeoTransform((win["west"], res, 0.0, win["north"], 0.0, -res))
    ds.SetProjection(CRS.from_epsg(4326).to_wkt())
    for b in range(bands):
        band = ds.GetRasterBand(b + 1)
        band.SetNoDataValue(0)
        band.WriteArray(array if array.ndim == 2 else array[b])
        band.FlushCache()
        try:
            band.ComputeStatistics(False)
        except RuntimeError:
            # an all-nodata band (e.g. a day whose lsct2 has no valid pixel in
            # one band) has no statistics; the file itself is fine
            pass
    ds = None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", type=Path, required=True,
                    help="case directory (cases/slstr-<region>)")
    ap.add_argument("--machine", default="hero")
    ap.add_argument("--source-root", type=Path, default=None)
    ap.add_argument("--output-root", type=Path, default=None)
    ap.add_argument("--product", choices=("lst", "lsct", "both"), default=None,
                    help="default: the products listed in case.toml")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--start-date", default=None)
    ap.add_argument("--end-date", default=None)
    ap.add_argument("--sza-threshold", type=float, default=None,
                    help="day when the footprint median solar zenith angle is below this")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--limit-days", type=int, default=None)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--no-time", action="store_true",
                    help="do not write the companion overpass-time rasters")
    ap.add_argument("--no-cloud-mask", dest="cloud_mask", action="store_false",
                    help="keep retrievals of cloud-flagged pixels (the EUR mosaic "
                         "behaviour); by default only clear pixels are composited")
    ap.set_defaults(cloud_mask=None)
    ap.add_argument("--index", type=Path, default=None)
    args = ap.parse_args()

    case = load_case(args.case, args.machine)
    win = case["window"]
    source_root = args.source_root or case["source_root"]
    output_root = args.output_root or case["output_root"]
    sza_threshold = case["sza_threshold"] if args.sza_threshold is None else args.sza_threshold
    cloud_mask = case["cloud_mask"] if args.cloud_mask is None else args.cloud_mask
    products = tuple(case["products"]) if args.product is None else \
        {"lst": ("lst",), "lsct": ("lsct",), "both": ("lst", "lsct")}[args.product]
    print(f"case {case['case_id']} ({case['region']}): window "
          f"{win['west']}..{win['east']} E, {win['south']}..{win['north']} N at {win['res']} deg, "
          f"products {products}, sza<{sza_threshold:g} day, cloud mask {cloud_mask}", flush=True)
    per_product = {p: day_scenes(source_root, args.year, p) for p in products}
    days = sorted(set().union(*[set(d) for d in per_product.values()]))
    if args.start_date:
        days = [d for d in days if d >= args.start_date.replace("-", "")]
    if args.end_date:
        days = [d for d in days if d <= args.end_date.replace("-", "")]
    if args.limit_days:
        days = days[:args.limit_days]
    print(f"{args.year}: {len(days)} days, products {products}, "
          f"{sum(len(per_product[p].get(d, [])) for d in days for p in products)} scene reads",
          flush=True)
    if not days:
        return
    tasks = [(args.year, d, {p: per_product[p].get(d, []) for p in products},
              source_root, output_root, win, products,
              sza_threshold, args.overwrite, not args.no_time,
              cloud_mask, case["region"]) for d in days]
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i, res in enumerate(pool.map(composite_day, tasks, chunksize=1), 1):
            rows.append(res)
            if i % 10 == 0 or i == len(tasks):
                written = sum(1 for r in rows for p in r["files"]
                              for f in r["files"][p].values() if f["written"])
                print(f"   {i}/{len(tasks)} days, mosaics written {written}, "
                      f"{time.time() - t0:.0f}s", flush=True)
    index = args.index or (output_root / "index" / f"{args.year}.json")
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text(json.dumps(dict(year=args.year, products=list(products), window=win,
                                     case=case["case_id"], region=case["region"],
                                     sza_threshold=sza_threshold,
                                     cloud_mask=cloud_mask, days=rows), indent=2))
    for product in products:
        day_files = sum(1 for r in rows if r["files"][product]["day"]["written"])
        night_files = sum(1 for r in rows if r["files"][product]["night"]["written"])
        print(f"  -> {product}: day {day_files} 天, night {night_files} 天", flush=True)
    print(f"  index {index}", flush=True)


if __name__ == "__main__":
    main()
