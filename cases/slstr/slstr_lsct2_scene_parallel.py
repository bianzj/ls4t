#!/usr/bin/env python3
"""Finish missing scene-first LSCT2 products on the slstr-euro-lst disk.

The retrieval itself is the one of ``slstr_lsct2.py`` (same helper modules, the
same expressions).  Only the driver differs: scenes are discovered on the disk,
grouped by acquisition day and handed to a worker pool, so the global base
rasters and the four-day LAI field are loaded once instead of once per scene.

Two implementation details differ from ``slstr_lsct2.py`` but not the numbers:

* ``loc2map`` reads the whole 36000 x 18000 reference raster per scene without
  ever using it; here only the geotransform is used.
* the LAI field is sampled at the needed pixels before the /1000 conversion, so
  the 648 M element float64 copy is never materialised.

Output layout matches the existing products:
``<root>/<year>/lsct/<scene>/lsct2.tif`` (2 bands, float32, oblique grid).
Scenes without a valid pixel produce no data file, exactly like the original,
but they get a small ``_no_valid_pixel.json`` marker in their scene directory:
without it the discovery keeps finding the same scene in every rerun and the
year never finishes.  Delete the marker (or pass ``--all-scenes``) to retry one.

Only one readable cloud mask is required.  When either ``cloud_nadir.tif`` or
``cloud_obliq.tif`` is missing/corrupt, the readable mask is used for both
views (the cropped nadir grid and the oblique grid have the same shape).  Those
scenes are flagged in the report as ``cloud_fallback``.

usage:
  PYTHONPATH=. python cases/slstr/slstr_lsct2_scene_parallel.py \
      --year 2020 --workers 16 --report cases/slstr/logs/lsct2_2020_report.json

Disks without a ``base/`` of their own (heihe) take the base rasters from
another disk through ``--emis-dir``/``--type-ref`` (both must be on the global
0.01 deg grid of the LAI field):
  PYTHONPATH=. python cases/slstr/slstr_lsct2_scene_parallel.py \
      --root /media/hero/slstr_heihe/heihe --year 2024 --workers 16 \
      --emis-dir /media/hero/rs/emissivity \
      --type-ref /media/hero/rs/land-cover/type/type_world_1000.tif \
      --report cases/slstr/logs/lsct2_heihe_2024.json
"""
from __future__ import annotations

import argparse
import builtins
import json
import os
import sys
import time
import warnings
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import numpy as np

from osgeo import gdal
from scipy.linalg import lstsq
import h5py
from base.files import read_image_gdal, read_txt_array, write_image_gdal
from base.lsct import cal_fvc_from_lai
from base.radiometry import inv_planck, planck
from base.spatial import geo2imagexy, lonlat2geo
from slstr.slstr_scene_skip import is_useless, load_scene_skip
from slstr.slstr_grid import adjust_xmax_no_g, adjust_xmin_no_g, adjust_ymax_no_g

warnings.filterwarnings("ignore")

DEFAULT_ROOT = Path("/media/hero/slstr-euro-lst")
# LAI lives on the slow USB bay and is mirrored to the local NVMe by
# ``cases/auxiliary/rs_mirror_local.py``; prefer the local copy when present.
RS_LOCAL = Path("/home/hero/data/rs")
RS_REMOTE = Path("/media/hero/rs")
LAI_ROOTS = [
    (2002, 2020, "lai/lai_2002-2020_0p01deg"),
    (2021, 2025, "lai/lai_2021-2025_0p01deg"),
]

# honor <scene_root>/_skip/<year>.json written by slstr_scene_coverage.py
SKIP_MARKED_SCENES = True

# written next to a scene whose inversion found no valid pixel, so the scene is
# not rediscovered (and recomputed) on every later run
EMPTY_MARKER = "_no_valid_pixel.json"
CLASSIFIED_EMPTY_REASONS = {
    "water", "non_land", "low_lai", "cloud", "invalid_thermal", "regression",
}
TYPE_REF = "base/type/type_world_1000.tif"

# retrieval settings, verbatim from slstr_lsct2.py
WL = 10.8
SOIL_RADIANCE_VARIANCE = 2
LEAF_RADIANCE_VARIANCE = 1
SENSOR_NOISE = 0.5
# minimum LAI of a pixel that takes part in the component-temperature fit.
# The original implementation used 0.25; 0.05 keeps sparse vegetation
# (grassland, cropland edges, semi-desert) that 0.25 discarded.
LAI_MIN = 0.05

_STATE: dict = {}


def has_classified_empty_marker(path: Path) -> bool:
    """True only for a marker written with the reason-aware schema.

    Legacy markers said only ``no valid pixel``.  Those are intentionally
    rediscovered once so cloud, water/non-land and processing failures are no
    longer collapsed into one bucket.
    """
    if not path.is_file():
        return False
    try:
        reason = json.loads(path.read_text()).get("reason")
    except (OSError, ValueError):
        return False
    return reason in CLASSIFIED_EMPTY_REASONS


def doy4(year: int, day: date) -> int:
    return (((day - date(year, 1, 1)).days + 1) // 4) * 4 + 1


def lai_file(year: int, day: date) -> Path | None:
    d4 = doy4(year, day)
    for start, end, subdir in LAI_ROOTS:
        if start <= year <= end:
            for root in (RS_LOCAL, RS_REMOTE):
                for name in (f"LAI_{year}{d4:03d}.h5", f"lai_{year}{d4:03d}.h5"):
                    path = root / subdir / str(year) / name
                    if path.is_file():
                        return path
            return None
    return None


def discover(root: Path, out_root: Path, out_layer: str, year: int, skip_scenes: set[str],
             only_days: set[str] | None = None,
             cloud_fallback_only: bool = False) -> dict[str, list[str]]:
    """Scenes with an LST result but without an LSCT2 output, grouped by day."""
    lst_dir = root / str(year) / "lst"
    lsct_dir = out_root / str(year) / out_layer
    tif_dir = root / str(year) / "tif"
    by_day: dict[str, list[str]] = defaultdict(list)
    if not lst_dir.is_dir():
        return by_day
    # LSCT2 reads the oblique view only, so a scene whose oblique footprint
    # misses the case window is dropped even when its nadir view is useful
    no_land = load_scene_skip(root, year) if SKIP_MARKED_SCENES else {}
    with os.scandir(lst_dir) as entries:
        names = sorted(e.name for e in entries if e.is_dir(follow_symlinks=True))
    for scene in names:
        if not (lst_dir / scene / "lst_nadir.tif").is_file():
            continue
        if (lsct_dir / scene / "lsct2.tif").is_file() or scene in skip_scenes:
            continue
        if has_classified_empty_marker(lsct_dir / scene / EMPTY_MARKER):
            continue
        if is_useless(no_land, scene, ("obliq",)):
            continue
        # the inversion reads the oblique bands of the scene tree; a scene
        # missing any of them can never produce a result and must not be
        # rediscovered on every run
        if not all((tif_dir / scene / f"{band}_obliq.tif").is_file()
                   for band in ("bt8", "bt9", "vza", "lat", "lon")):
            continue
        if cloud_fallback_only:
            scene_tif = tif_dir / scene
            has_nadir = (scene_tif / "cloud_nadir.tif").is_file()
            has_obliq = (scene_tif / "cloud_obliq.tif").is_file()
            if has_nadir == has_obliq:
                continue
        day = scene.split("____")[1][:8]
        if only_days and day not in only_days:
            continue
        by_day[day].append(scene)
    return by_day


def load_state(emis_dir: Path, type_ref: Path,
               window: tuple[int, int, int, int]) -> dict:
    """Load only the case window of the global rasters.

    ``emis_dir``/``type_ref`` default to ``<root>/base/...`` but can be pointed
    at another disk: the heihe root has no ``base/`` of its own, its scenes are
    indexed on the same 0.01 deg grid as ``/media/hero/rs``.
    """
    row0, row1, col0, col1 = window

    def read_window(path: Path, dtype) -> np.ndarray:
        ds = gdal.Open(str(path))
        if ds is None:
            raise OSError(f"cannot open base raster: {path}")
        data = ds.ReadAsArray(col0, row0, col1 - col0, row1 - row0)
        if data is None:
            raise OSError(f"cannot read base raster window: {path}")
        return np.asarray(data, dtype=dtype)

    emis1_s0 = read_window(
        emis_dir / "AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif", np.float32)
    emis1_s0 /= 1000.0
    emis2_s0 = read_window(
        emis_dir / "AG1km.v003.SoilEmi.MODIS.Global.001D_LSE12.tif", np.float32)
    emis2_s0 /= 1000.0
    ref_ds = gdal.Open(str(type_ref))
    if ref_ds is None:
        raise OSError(f"cannot open type reference: {type_ref}")
    grid_shape = (ref_ds.RasterYSize, ref_ds.RasterXSize)
    classif0 = read_window(type_ref, np.uint8)
    return dict(
        emis1_s0=emis1_s0,
        emis2_s0=emis2_s0,
        classif0=classif0,
        grid_shape=grid_shape,
        window=window,
        emis_v=read_txt_array(str(emis_dir / "IGBP_Emi.txt"), 0, 2),
        coeffs_day=read_txt_array(str(emis_dir / "Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt"), 0, 15)[:, 2:10],
        coeffs_night=read_txt_array(str(emis_dir / "Sentinel3A_SLSTR_SW_Seebor_Coef_Night.txt"), 0, 15)[:, 2:10],
    )


def _init_worker(state: dict, root: str, out_root: str, out_layer: str,
                 type_ref: str) -> None:
    _STATE.update(state)
    _STATE["root"] = Path(root)
    _STATE["out_root"] = Path(out_root)
    _STATE["out_layer"] = out_layer
    # loc2map() equivalent: only the geotransform of the reference raster is used
    _STATE["ref_ds"] = gdal.Open(type_ref)
    _STATE["inv_Cm"] = np.linalg.inv(np.diag([SOIL_RADIANCE_VARIANCE, LEAF_RADIANCE_VARIANCE]))
    _STATE["inv_Cd"] = 1.0 / (SENSOR_NOISE ** 2)


def index_map(ref_ds, lat: np.ndarray, lon: np.ndarray):
    """Same indices as loc2map() returns (row index first, then column index)."""
    imagex, imagey = geo2imagexy(ref_ds, *lonlat2geo(ref_ds, lat, lon))
    return np.asarray(imagex, np.int_), np.asarray(imagey, np.int_)


def read_cloud(path: Path) -> np.ndarray | None:
    """Read a cloud mask, treating a missing or corrupt TIFF as unavailable."""
    if not path.is_file():
        return None
    try:
        result = read_image_gdal(str(path))
    except Exception:  # GDAL may raise for a truncated TIFF directory
        return None
    return None if result is None else result[0]


def scene_window(root: Path, year: int, by_day: dict[str, list[str]],
                 days: list[str], type_ref: Path) -> tuple[int, int, int, int]:
    """Return the smallest global-grid window containing this processing batch."""
    ref_ds = gdal.Open(str(type_ref))
    if ref_ds is None:
        raise OSError(f"cannot open type reference: {type_ref}")
    nrow, ncol = ref_ds.RasterYSize, ref_ds.RasterXSize
    row_min, row_max, col_min, col_max = nrow, -1, ncol, -1
    tif_root = root / str(year) / "tif"
    for day in days:
        for scene in by_day[day]:
            try:
                lat, _, _, _, _, _ = read_image_gdal(str(tif_root / scene / "lat_obliq.tif"))
                lon, _, _, _, _, _ = read_image_gdal(str(tif_root / scene / "lon_obliq.tif"))
            except Exception:  # unreadable input is reported by the worker later
                continue
            valid = (np.isfinite(lat) & np.isfinite(lon)
                     & (lat >= -9000) & (lat <= 9000)
                     & (lon >= -18000) & (lon <= 18000))
            if not np.any(valid):
                continue
            rows, cols = index_map(ref_ds, lat[valid] / 100.0, lon[valid] / 100.0)
            valid_grid = ((rows >= 0) & (rows < nrow)
                          & (cols >= 0) & (cols < ncol))
            if not np.any(valid_grid):
                continue
            rows, cols = rows[valid_grid], cols[valid_grid]
            row_min = min(row_min, int(rows.min()))
            row_max = max(row_max, int(rows.max()))
            col_min = min(col_min, int(cols.min()))
            col_max = max(col_max, int(cols.max()))
    if row_max < row_min or col_max < col_min:
        raise RuntimeError("could not derive a valid base-raster window from scene geolocation")
    return max(0, row_min - 1), min(nrow, row_max + 2), \
        max(0, col_min - 1), min(ncol, col_max + 2)


def lsct2_scene(scene: str, year: int, lat: np.ndarray, lon: np.ndarray,
                lai0: np.ndarray, out_file: Path) -> str:
    """Run one scene and return a written/skipped/no-valid reason status.

    ``no_valid_*`` statuses deliberately distinguish water/non-land footprints
    from cloudy land observations.  Water and scenes outside the case are not
    missing land products; cloud and low-LAI statuses are genuine observational
    limitations, while thermal/regression failures remain processing diagnostics.
    """
    root: Path = _STATE["root"]
    tif_dir = root / str(year) / "tif" / scene
    lst_dir = root / str(year) / "lst" / scene
    # slstr_lsct2.py creates the output folder before the input checks, so
    # "attempted but empty" scenes are left as empty folders
    out_file.parent.mkdir(parents=True, exist_ok=True)
    # The retrieval needs both thermal views, but either cloud view is enough:
    # both masks ultimately live on the same cropped/oblique grid.
    needed = [lst_dir / "lst_nadir.tif", lst_dir / "lst_obliq.tif",
              tif_dir / "vza_nadir.tif", tif_dir / "vza_obliq.tif"]
    # NB: build a list first - ``all`` is shadowed by numpy through the
    # ``from cases.support.util_* import *`` imports above.
    if [p for p in needed if not p.is_file()]:
        return "skipped"

    # Cheap pre-check before reading the rest of the scene: the retrieval mask
    # needs ``lai > LAI_MIN``, so a scene whose whole footprint is ocean, ice
    # or bare desert (LAI nodata/0) can never produce an LSCT2 pixel.  Most of
    # the remaining scenes on this disk are polar night passes of that kind.
    indx_lai, indy_lai = index_map(_STATE["ref_ds"], lat / 100.0, lon / 100.0)
    ind = indx_lai > 18000
    if np.sum(ind) > 0:                      # fill values, as in slstr_lsct2.py
        indx_lai[ind] = 17999
    nrow, ncol = _STATE["grid_shape"]
    indx_lai = np.clip(indx_lai, 0, nrow - 1)
    indy_lai = np.clip(indy_lai, 0, ncol - 1)
    row0, _, col0, _ = _STATE["window"]
    indx_lai -= row0
    indy_lai -= col0
    crop_rows, crop_cols = _STATE["classif0"].shape
    indx_lai = np.clip(indx_lai, 0, crop_rows - 1)
    indy_lai = np.clip(indy_lai, 0, crop_cols - 1)
    probe_rows, probe_cols = indx_lai[::2], indy_lai[::2]
    probe = lai0[probe_rows, probe_cols]
    probe_class = _STATE["classif0"][probe_rows, probe_cols]
    probe_land = (probe_class > 0) & (probe_class < 17)
    if not np.any(probe_land):
        water = int(np.count_nonzero(probe_class == 0))
        non_land = int(probe_class.size - water)
        return "no_valid_water" if water >= non_land else "no_valid_non_land"
    # valid vegetation: LAI_MIN < LAI < 10 (the stored uint16 field is LAI*1000,
    # nodata 32767) - exactly the condition used by the mask below
    if not np.any(probe_land & (probe > LAI_MIN * 1000) & (probe < 10000)):
        return "no_valid_low_lai"

    lstN, _, _, _, _, _ = read_image_gdal(str(lst_dir / "lst_nadir.tif"))
    lstO, ns, nl, _, _, _ = read_image_gdal(str(lst_dir / "lst_obliq.tif"))
    vzaN, _, _, _, _, _ = read_image_gdal(str(tif_dir / "vza_nadir.tif"))
    vzaO, _, _, _, _, _ = read_image_gdal(str(tif_dir / "vza_obliq.tif"))
    cldN = read_cloud(tif_dir / "cloud_nadir.tif")
    cldO = read_cloud(tif_dir / "cloud_obliq.tif")
    expected_shape = (nl, ns)
    cldNO = (cldN[0:adjust_ymax_no_g, adjust_xmin_no_g:adjust_xmax_no_g]
             if cldN is not None else None)
    if cldNO is not None and cldNO.shape != expected_shape:
        cldNO = None
    if cldO is not None and cldO.shape != expected_shape:
        cldO = None
    if cldNO is None and cldO is None:
        return "skipped"
    cloud_fallback = cldNO is None or cldO is None
    if cldNO is None:
        cldNO = cldO.copy()
    if cldO is None:
        cldO = cldNO.copy()

    vzaN = vzaN / 100.0
    vzaO = vzaO / 100.0
    lstN = lstN / 100.0
    lstO = lstO / 100.0

    vzaNO = vzaN[0:adjust_ymax_no_g, adjust_xmin_no_g:adjust_xmax_no_g]
    lstNO = lstN[0:adjust_ymax_no_g, adjust_xmin_no_g:adjust_xmax_no_g]
    lai = lai0[indx_lai, indy_lai].astype(np.float64) / 1000.0
    lai[lai > 10] = np.NaN
    lai = np.reshape(lai, [nl, ns])
    lai[lai > 10.01] = 0
    coeff = 0.825
    fvc = 1 - np.exp(-coeff * lai * 0.5)
    fvc = np.reshape(fvc, [nl, ns])
    fvcN = cal_fvc_from_lai(vzaNO, lai)
    fvcO = cal_fvc_from_lai(vzaO, lai)

    classif = _STATE["classif0"][indx_lai, indy_lai]
    classif = np.reshape(classif, [nl, ns])
    classif[classif > 17] = 0

    emis_v = _STATE["emis_v"]
    emis1_v = np.reshape(emis_v[classif, 0] / 1000.0, [nl, ns])
    emis2_v = np.reshape(emis_v[classif, 1] / 1000.0, [nl, ns])
    emis1_s = np.reshape(_STATE["emis1_s0"][indx_lai, indy_lai], [nl, ns])
    emis2_s = np.reshape(_STATE["emis2_s0"][indx_lai, indy_lai], [nl, ns])

    F = 0.05
    C1 = (1 - emis1_s) * emis1_v * F * (1 - fvc)
    emis = emis1_s * (1 - fvc) + emis1_v * fvc + C1
    emis[emis > 0.995] = 0.995

    eevN0 = fvcN * emis1_v + C1
    eesN0 = (1 - fvcN) * emis1_s
    eevO0 = fvcO * emis1_v + C1
    eesO0 = (1 - fvcO) * emis1_s
    eeV0 = np.stack([eevN0, eevO0])
    eeS0 = np.stack([eesN0, eesO0])

    lstNO[lstNO < 100] = np.NaN
    lstO[lstO < 100] = np.NaN
    bN0 = planck(WL, lstNO) * emis
    bO0 = planck(WL, lstO) * emis

    land_ok = (classif > 0) & (classif < 17)
    lai_ok = (lai > LAI_MIN) & (lai < 10.01)
    thermal_ok = (emis > 0) & (bN0 > 5) & (bO0 > 5)
    clear = (cldNO == 0) & (cldO == 0)
    land_lai = land_ok & lai_ok
    candidate = land_lai & thermal_ok
    if not np.any(land_ok):
        water = int(np.count_nonzero(classif == 0))
        non_land = int(classif.size - water)
        return "no_valid_water" if water >= non_land else "no_valid_non_land"
    if not np.any(land_lai):
        return "no_valid_low_lai"
    if not np.any(candidate):
        return "no_valid_invalid_thermal"
    if not np.any(candidate & clear):
        return "no_valid_cloud"
    mask0 = candidate & clear
    indx_p, indy_p = np.where(mask0)

    off = 2
    resultT = np.zeros([2, nl, ns])
    for kp in range(len(indx_p)):
        kl = indx_p[kp]
        ks = indy_p[kp]
        if kl < off or ks < off or kl > nl - off - 1 or ks > ns - off - 1:
            continue
        kl1, kl2 = kl - off, kl + off + 1
        ks1, ks2 = ks - off, ks + off + 1
        eeV = np.reshape(eeV0[:, kl1:kl2, ks1:ks2], -1)
        eeS = np.reshape(eeS0[:, kl1:kl2, ks1:ks2], -1)
        bN = np.reshape(bN0[kl1:kl2, ks1:ks2], -1)
        bO = np.reshape(bO0[kl1:kl2, ks1:ks2], -1)
        mask1 = np.reshape(mask0[kl1:kl2, ks1:ks2], -1)
        mask2 = np.hstack([mask1, mask1])
        ind2 = (eeS > 0.1) * mask2 * (eeS < 0.9)
        if np.sum(ind2) <= 5:
            continue
        bb = np.hstack([bN, bO])[ind2]
        ww = np.stack([eeS[ind2], eeV[ind2]])
        coeffs = np.asarray(lstsq(np.transpose(ww), np.transpose(bb))[0])
        resultT[:, kl, ks] = inv_planck(WL, coeffs)

    if not np.any(resultT > 0):
        return "no_valid_regression"
    write_image_gdal(resultT, nl, ns, 2, '', '', str(out_file))
    return "written_cloud_fallback" if cloud_fallback else "written"


def process_day(task):
    day_str, scenes = task
    year = int(day_str[:4])
    day = date(year, int(day_str[4:6]), int(day_str[6:8]))
    path = lai_file(year, day)
    root: Path = _STATE["root"]
    stats = dict(day=day_str, scenes=len(scenes), written=0, empty=0, skipped=0,
                 error=None, empty_scenes=[], empty_reasons={},
                 cloud_fallback=0, cloud_fallback_scenes=[])
    if path is None:
        stats["error"] = f"no LAI file for {day_str}"
        stats["skipped"] = len(scenes)
        return stats
    # four consecutive days share one LAI file; keep the last one loaded
    if _STATE.get("lai_path") != path:
        row0, row1, col0, col1 = _STATE["window"]
        with h5py.File(str(path), "r") as handle:
            _STATE["lai0"] = np.array(handle["/data"][row0:row1, col0:col1])
        _STATE["lai_path"] = path
    lai0 = _STATE["lai0"]
    out_dir = _STATE["out_root"] / str(year) / _STATE["out_layer"]
    tif_dir = root / str(year) / "tif"
    for scene in scenes:
        lat_file, lon_file = tif_dir / scene / "lat_obliq.tif", tif_dir / scene / "lon_obliq.tif"
        if not lat_file.is_file() or not lon_file.is_file():
            stats["skipped"] += 1
            continue
        try:
            lat, _, _, _, _, _ = read_image_gdal(str(lat_file))
            lon, _, _, _, _, _ = read_image_gdal(str(lon_file))
            status = lsct2_scene(scene, year, lat, lon, lai0, out_dir / scene / "lsct2.tif")
        except Exception as exc:  # noqa: BLE001
            status = "error"
            stats["error"] = f"{scene}: {exc!r}"
        if status.startswith("written"):
            stats["written"] += 1
            if status.endswith("cloud_fallback"):
                stats["cloud_fallback"] += 1
                stats["cloud_fallback_scenes"].append(scene)
        elif status.startswith("no_valid_"):
            stats["empty"] += 1
            stats["empty_scenes"].append(scene)
            reason = status.removeprefix("no_valid_")
            stats["empty_reasons"][reason] = stats["empty_reasons"].get(reason, 0) + 1
            marker = out_dir / scene / EMPTY_MARKER
            try:
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.write_text(json.dumps(
                    {"scene": scene, "year": year, "reason": reason,
                     "classification": "natural_or_surface_mask"
                     if reason in {"water", "non_land", "low_lai", "cloud"}
                     else "processing_diagnostic",
                     "written": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
            except OSError:
                pass
        else:
            stats["skipped"] += 1
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--out-root", type=Path, default=None,
                    help="where the lsct tree is written (default: --root)")
    ap.add_argument("--out-layer", default="lsct",
                    help="year-level output directory name (default: lsct)")
    ap.add_argument("--year", type=int, default=2020)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--days", nargs="*", default=None, help="only these YYYYMMDD days")
    ap.add_argument("--limit-days", type=int, default=None)
    ap.add_argument("--skip-report", type=Path, default=None,
                    help="earlier report; the scenes it found empty are skipped")
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--force-scenes", nargs="*", default=None,
                    help="process exactly these scenes (used for validation)")
    ap.add_argument("--cloud-fallback-only", action="store_true",
                    help="only scenes with exactly one cloud-view file present")
    ap.add_argument("--emis-dir", type=Path, default=None,
                    help="soil emissivity / IGBP_Emi / Seebor coefficient directory "
                         "(default: <root>/base/emis)")
    ap.add_argument("--type-ref", type=Path, default=None,
                    help="IGBP classification on the 0.01 deg grid "
                         "(default: <root>/base/type/type_world_1000.tif)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all-scenes", action="store_true",
                    help="ignore the coverage skip list and read every scene")
    args = ap.parse_args()
    global SKIP_MARKED_SCENES
    SKIP_MARKED_SCENES = not args.all_scenes
    out_root = args.out_root or args.root
    emis_dir = args.emis_dir or (args.root / "base" / "emis")
    type_ref = args.type_ref or (args.root / TYPE_REF)

    skip_scenes: set[str] = set()
    if args.skip_report and args.skip_report.is_file():
        skip_scenes = set(json.loads(args.skip_report.read_text()).get("empty_scenes", []))

    t0 = time.time()
    if args.force_scenes:
        by_day = defaultdict(list)
        for scene in args.force_scenes:
            by_day[scene.split("____")[1][:8]].append(scene)
    else:
        by_day = discover(args.root, out_root, args.out_layer, args.year, skip_scenes,
                          set(args.days) if args.days else None,
                          cloud_fallback_only=args.cloud_fallback_only)
    days = sorted(by_day)
    if args.limit_days:
        days = days[:args.limit_days]
    total = builtins.sum(len(by_day[d]) for d in days)
    print(f"{args.year}: {total} scenes without lsct2 over {len(days)} acquisition days "
          f"({time.time() - t0:.0f}s scan)", flush=True)
    if args.dry_run or not days:
        return

    print("loading base rasters ...", flush=True)
    t0 = time.time()
    window = scene_window(args.root, args.year, by_day, days, type_ref)
    state = load_state(emis_dir, type_ref, window)
    print(f"  base loaded in {time.time() - t0:.0f}s "
          f"(window {window}, type {state['classif0'].shape})", flush=True)

    tasks = [(d, by_day[d]) for d in days]
    report = dict(year=args.year, root=str(args.root), workers=args.workers, scenes=total,
                  days=len(days), days_report=[], empty_scenes=[], empty_reasons={},
                  cloud_fallback=0, cloud_fallback_scenes=[],
                  started=time.strftime("%Y-%m-%dT%H:%M:%S"))
    done = written = empty = skipped = fallback = 0
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init_worker,
                             initargs=(state, str(args.root), str(out_root),
                                       args.out_layer, str(type_ref))) as pool:
        # chunksize 4 keeps consecutive days (same LAI file) on the same worker
        for stats in pool.map(process_day, tasks, chunksize=4):
            done += stats["scenes"]
            written += stats["written"]
            empty += stats["empty"]
            skipped += stats["skipped"]
            fallback += stats["cloud_fallback"]
            report["days_report"].append(
                {k: v for k, v in stats.items()
                 if k not in ("empty_scenes", "cloud_fallback_scenes")})
            report["empty_scenes"].extend(stats["empty_scenes"])
            for reason, count in stats["empty_reasons"].items():
                report["empty_reasons"][reason] = report["empty_reasons"].get(reason, 0) + count
            report["cloud_fallback_scenes"].extend(stats["cloud_fallback_scenes"])
            elapsed = time.time() - t0
            rate = done / elapsed if elapsed else 0
            eta = (total - done) / rate / 60 if rate else 0
            print(f"  {stats['day']}: {stats['scenes']:3d} scenes -> written {stats['written']:3d} "
                  f"empty {stats['empty']:3d} skipped {stats['skipped']:2d}"
                          f"{' (single-cloud fallback ' + str(stats['cloud_fallback']) + ')' if stats['cloud_fallback'] else ''}"
                  f"{'  ERROR: ' + stats['error'] if stats['error'] else ''}"
                  f" | {done}/{total} {rate:.2f} scene/s eta {eta:.0f} min", flush=True)
    report.update(finished=time.strftime("%Y-%m-%dT%H:%M:%S"), written=written, empty=empty,
                  skipped=skipped, cloud_fallback=fallback,
                  seconds=builtins.round(time.time() - t0, 1))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2))
        print("report ->", args.report)
    print(f"done: written {written}, no valid pixel {empty}, skipped {skipped} "
          f"in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
