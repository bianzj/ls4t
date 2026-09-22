#!/usr/bin/env python3
"""Scene-first SLSTR LST retrieval for a scene-per-directory disk.

The retrieval is the one of ``slstr_lst.py``: the same helper modules, the same
expressions and the same constants (Seebor split-window tables, LAI based
vegetation fraction, IGBP vegetation emissivity, MODIS soil emissivity, ERA5
TCWV).  Only the driver differs: scenes are discovered on the disk, grouped by
acquisition day, and the global base rasters, the four-day LAI field and the
hourly TCWV cube are loaded once per worker instead of once per scene.

Three implementation details differ from ``slstr_lst.py`` but not the numbers:

* ``loc2map`` reads the whole 18000 x 36000 reference raster per scene and only
  keeps the geotransform; here the indices are computed straight from the two
  regular global grids (0.01 deg LAI/type/emissivity, 0.25 deg TCWV).
* the base rasters stay in their stored integer types and are divided by 1000
  after sampling, so the float64 copies of the 648 M element rasters are never
  materialised.
* the TCWV files of this machine keep the hourly cube as ``/data`` in kg m**-2
  on the 0.25 deg grid (24 x 721 x 1440, north to south), where
  ``slstr_lst.py`` expects ``/tcw``; the ``/ 10`` to cm is unchanged.

Output layout: ``<out-root>/<year>/lst/<scene>/lst_nadir.tif`` and
``lst_obliq.tif`` - one band, uint16, LST * 100, on the grid of the input
brightness temperatures.  Scenes with an existing output are skipped, so the
script can be re-run to fill gaps.

usage:
  PYTHONPATH=. python cases/slstr/implementation/one_by_one/slstr_lst_parallel.py \
      --root /media/hero/slstr_heihe/heihe --year 2025 --workers 24 \
      --report cases/slstr/logs/lst_heihe_2025_report.json
"""

from __future__ import annotations
from base.files import read_image_gdal, read_txt_array, write_image_gdal
from slstr.slstr_scene_skip import is_useless, load_scene_skip

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

import h5py
import numpy as np


warnings.filterwarnings("ignore")

DEFAULT_ROOT = Path("/media/hero/slstr_heihe/heihe")
# auxiliary data live in the local NVMe mirror (cases/auxiliary/rs_mirror_local.py);
# the USB bay keeps the same layout and is the fallback
RS_LOCAL = Path("/home/hero/data/rs")
RS_REMOTE = Path("/media/hero/rs")
# NB: the heihe study-area base is a UTM 47N crop of the same rasters and does
# NOT share the 0.01 deg grid of the LAI/type fields, so it cannot be indexed
# with them; the global rasters are required here.
DEFAULT_BASE = RS_LOCAL / "emissivity"
DEFAULT_TYPE_REF = RS_LOCAL / "land-cover" / "type" / "type_world_1000.tif"
DEFAULT_TCWV_ROOT = RS_LOCAL / "tcwv"

LAI_ROOTS = [
    (2002, 2020, "lai/lai_2002-2020_0p01deg", "LAI_%04d%03d.h5"),
    (2021, 2025, "lai/lai_2021-2025_0p01deg", "lai_%04d%03d.h5"),
]
SOIL_EMISSIVITY = ("AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif",
                   "AG1km.v003.SoilEmi.MODIS.Global.001D_LSE12.tif")

# grid geometry of the global reference rasters
LAI_GRID = (18000, 36000, 0.01)       # type / LAI / soil emissivity
TCWV_GRID = (721, 1440, 0.25)         # hourly TCWV cube, row 0 = +90 N

# retrieval settings, verbatim from slstr_lst.py
FVC_COEFF = 0.825
SCATTERING_F = 0.05
VIEW_ZENITH_NODES = np.asarray([0, 3, 14.9, 38.6, 44.5, 51.2, 58, 65, 70, 75, 80])
WATER_VAPOUR_EDGES = np.asarray([0, 1.25, 2.25, 3.25, 4.25, 5.25, 100])
LST_MIN_K, LST_MAX_K = 220.0, 365.0

# honor <scene_root>/_skip/<year>.json written by slstr_scene_coverage.py:
# scenes whose footprint has no pixel inside the case window on a land class
# cannot produce a value, and reading them again is pure I/O
SKIP_MARKED_SCENES = True

_STATE: dict = {}


def find_base_file(base: Path, name: str) -> Path:
    """The case keeps its auxiliary files in emis/, type/ and base/ subfolders."""
    for candidate in (base / "emis" / name, base / "type" / name,
                      base / "base" / name, base / name):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"{name} not found under {base}")


def doy4(year: int, day: date) -> int:
    return (((day - date(year, 1, 1)).days + 1) // 4) * 4 + 1


def lai_file(year: int, day: date) -> Path | None:
    for start, end, relative, pattern in LAI_ROOTS:
        if start <= year <= end:
            for base in (RS_LOCAL, RS_REMOTE):
                # the USB bay and the local mirror do not agree on the case of
                # the file name (LAI_2022001.h5 vs lai_2022001.h5), so accept
                # either before giving up on a year
                head, _, tail = pattern.partition("%")
                for prefix in {head, head.upper(), head.lower()}:
                    name = (prefix + "%" + tail) % (year, doy4(year, day))
                    path = base / relative / str(year) / name
                    if path.is_file():
                        return path
            return None
    return None


def tcwv_file(tcwv_root: Path, day_str: str) -> Path | None:
    path = tcwv_root / day_str[:4] / f"tcwv_{day_str}.h5"
    return path if path.is_file() else None


def discover(root: Path, year: int) -> dict[str, list[str]]:
    """Scene directories of one year that still lack an LST result, by day."""
    tif_dir = root / str(year) / "tif"
    lst_dir = root / str(year) / "lst"
    by_day: dict[str, list[str]] = defaultdict(list)
    if not tif_dir.is_dir():
        return by_day
    # scenes the coverage audit found useless for this case (ocean / polar /
    # outside the window) never produce a pixel here, so they are left alone
    no_land = load_scene_skip(root, year) if SKIP_MARKED_SCENES else {}
    with os.scandir(tif_dir) as entries:
        names = sorted(e.name for e in entries if e.is_dir(follow_symlinks=False))
    for scene in names:
        if is_useless(no_land, scene, ("nadir", "obliq")):
            continue
        # a scene is finished when every view it *can* produce has been
        # produced: a scene whose oblique input files are missing keeps its
        # nadir result and is not retried for ever
        produced = {view: (lst_dir / scene / f"lst_{view}.tif").is_file()
                    for view in ("nadir", "obliq")}
        if all(produced.values()):
            continue
        tif_scene = tif_dir / scene
        possible = {view: all((tif_scene / f"{band}_{view}.tif").is_file()
                              for band in ("bt8", "bt9", "vza", "lat", "lon"))
                    for view in ("nadir", "obliq")}
        if not any(possible.values()):
            continue
        if all(produced[view] or not possible[view] for view in possible):
            continue
        by_day[scene.split("____")[1][:8]].append(scene)
    return by_day


def load_state(root: Path, base: Path, type_ref: Path, emis_pair: tuple[str, str]) -> dict:
    """Global base rasters; inherited by the workers through fork."""
    emis1, _, _, _, _, _ = read_image_gdal(str(find_base_file(base, emis_pair[0])))
    emis2, _, _, _, _, _ = read_image_gdal(str(find_base_file(base, emis_pair[1])))
    classif, _, _, _, _, _ = read_image_gdal(str(type_ref))
    return dict(
        emis1_s0=emis1,
        emis2_s0=emis2,
        classif0=np.asarray(classif, np.int16),
        emis_v=read_txt_array(str(find_base_file(base, "IGBP_Emi.txt")), 0, 2),
        coeffs_day=read_txt_array(
            str(find_base_file(base, "Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt")), 0, 15)[:, 2:10],
    )


def _init_worker(state: dict, root: str, out_root: str, tcwv_root: str) -> None:
    _STATE.update(state)
    _STATE["root"] = Path(root)
    _STATE["out_root"] = Path(out_root)
    _STATE["tcwv_root"] = Path(tcwv_root)


def grid_index(lat: np.ndarray, lon: np.ndarray, nrow: int, ncol: int,
               res: float) -> tuple[np.ndarray, np.ndarray]:
    """Row/column of a global north-to-south, -180..180 regular grid."""
    row = np.rint((90.0 - lat) / res).astype(np.int32)
    col = np.rint((lon + 180.0) / res).astype(np.int32)
    np.clip(row, 0, nrow - 1, out=row)
    np.clip(col, 0, ncol - 1, out=col)
    return row, col


def lst_view(view: str, tif_dir: Path, out_file: Path, lai0: np.ndarray,
             tcw_day: np.ndarray, hour: int, overwrite: bool) -> str:
    """LST for one view of one scene: 'written', 'empty' or 'skipped'."""
    if out_file.is_file() and not overwrite:
        return "skipped"
    bt8_file = tif_dir / f"bt8_{view}.tif"
    bt9_file = tif_dir / f"bt9_{view}.tif"
    vza_file = tif_dir / f"vza_{view}.tif"
    lat_file = tif_dir / f"lat_{view}.tif"
    lon_file = tif_dir / f"lon_{view}.tif"
    for path in (bt8_file, bt9_file, vza_file, lat_file, lon_file):
        if not path.is_file():
            return "skipped"

    BT8, ns, nl, _, geog, proj = read_image_gdal(str(bt8_file))
    BT9, _, _, _, _, _ = read_image_gdal(str(bt9_file))
    vza, _, _, _, _, _ = read_image_gdal(str(vza_file))
    lat, _, _, _, _, _ = read_image_gdal(str(lat_file))
    lon, _, _, _, _, _ = read_image_gdal(str(lon_file))

    # int16 encodings used by the extraction step
    BT8 = BT8 / 100.0
    BT9 = BT9 / 100.0
    vza = vza / 100.0
    lat = lat / 100.0
    lon = lon / 100.0

    iy_lai, ix_lai = grid_index(lat, lon, LAI_GRID[0], LAI_GRID[1], LAI_GRID[2])
    iy_tcw, ix_tcw = grid_index(lat, lon, TCWV_GRID[0], TCWV_GRID[1], TCWV_GRID[2])

    lai = lai0[iy_lai, ix_lai].astype(np.float64) / 1000.0
    lai[lai > 10.01] = 0
    fvc = 1 - np.exp(-FVC_COEFF * lai * 0.5)
    fvc = np.reshape(fvc, [nl, ns])

    classif = _STATE["classif0"][iy_lai, ix_lai].astype(np.int64)
    classif = np.reshape(classif, [nl, ns])
    classif[classif > 17] = 0
    ind0 = (classif < 17) * (classif > 0)

    emis_v = _STATE["emis_v"]
    emis1_v = np.reshape(emis_v[classif, 0] / 1000.0, [nl, ns])
    emis2_v = np.reshape(emis_v[classif, 1] / 1000.0, [nl, ns])
    emis1_s = np.reshape(_STATE["emis1_s0"][iy_lai, ix_lai] / 1000.0, [nl, ns])
    emis2_s = np.reshape(_STATE["emis2_s0"][iy_lai, ix_lai] / 1000.0, [nl, ns])

    C1 = (1 - emis1_s) * emis1_v * SCATTERING_F * (1 - fvc)
    C2 = (1 - emis2_s) * emis2_v * SCATTERING_F * (1 - fvc)
    emis8 = emis1_s * (1 - fvc) + emis1_v * fvc + C1
    emis9 = emis2_s * (1 - fvc) + emis2_v * fvc + C2
    emis8[emis8 > 0.995] = 0.995
    emis9[emis9 > 0.995] = 0.995

    emis = (emis8 + emis9) * 0.5
    demis = emis8 - emis9
    x3 = np.zeros([nl, ns])
    x4 = np.zeros([nl, ns])
    x6 = np.zeros([nl, ns])
    x7 = np.zeros([nl, ns])
    x1 = 1
    x2 = (BT8 + BT9) / 2.0
    ind = emis != 0
    x3[ind] = (1 - emis[ind]) / emis[ind] * x2[ind]
    x4[ind] = demis[ind] / (emis[ind] * emis[ind]) * x2[ind]
    x5 = (BT8 - BT9) / 2
    x6[ind] = (1 - emis[ind]) / emis[ind] * x5[ind]
    x7[ind] = demis[ind] / (emis[ind] * emis[ind]) * x5[ind]
    x8 = (BT8 - BT9) * (BT8 - BT9)

    tcw = tcw_day[hour, iy_tcw, ix_tcw]
    tcw = np.reshape(tcw, [nl, ns])

    coeffs_day = _STATE["coeffs_day"]
    LST = np.zeros([nl, ns])
    for kwvc in range(len(WATER_VAPOUR_EDGES) - 1):
        for kvza in range(len(VIEW_ZENITH_NODES) - 1):
            ind = ((tcw >= WATER_VAPOUR_EDGES[kwvc]) * (tcw < WATER_VAPOUR_EDGES[kwvc + 1]) *
                   (vza >= VIEW_ZENITH_NODES[kvza]) * (vza < VIEW_ZENITH_NODES[kvza + 1]) *
                   (BT8 > 0) * (emis8 > 0) * ind0)
            if not np.any(ind):
                continue
            coeff1 = coeffs_day[kvza * 6 + kwvc, :]
            coeff2 = coeffs_day[(kvza + 1) * 6 + kwvc, :]
            vzatemp = vza[ind]
            prop2 = (vzatemp - VIEW_ZENITH_NODES[kvza]) / \
                (VIEW_ZENITH_NODES[kvza + 1] - VIEW_ZENITH_NODES[kvza])
            prop1 = 1 - prop2
            c = prop1[:, None] * coeff1[None, :] + prop2[:, None] * coeff2[None, :]
            LST[ind] = (x1 * c[:, 0] + x2[ind] * c[:, 1] + x3[ind] * c[:, 2] +
                        x4[ind] * c[:, 3] + x5[ind] * c[:, 4] + x6[ind] * c[:, 5] +
                        x7[ind] * c[:, 6] + x8[ind] * c[:, 7])

    LST[(LST > LST_MAX_K) | (LST < LST_MIN_K)] = 0
    LST_uint16 = (LST * 100.0)[:nl, :ns].astype(np.uint16)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    write_image_gdal(LST_uint16, ns, nl, 1, geog, proj, str(out_file))
    return "written" if np.any(LST_uint16) else "empty"


def process_day(task) -> dict:
    day_str, scenes = task
    year = int(day_str[:4])
    day = date(year, int(day_str[4:6]), int(day_str[6:8]))
    stats = dict(day=day_str, scenes=len(scenes), written=0, empty=0, skipped=0,
                 error=None, empty_scenes=[])

    lai_path = lai_file(year, day)
    tcw_path = tcwv_file(_STATE["tcwv_root"], day_str)
    if lai_path is None or tcw_path is None:
        stats["error"] = f"missing {'LAI' if lai_path is None else 'TCWV'} input"
        stats["skipped"] = len(scenes)
        return stats
    # four consecutive days share one LAI file; keep the last one loaded
    if _STATE.get("lai_path") != lai_path:
        with h5py.File(str(lai_path), "r") as handle:
            _STATE["lai0"] = np.array(handle["/data"])
        _STATE["lai_path"] = lai_path
    if _STATE.get("tcw_path") != tcw_path:
        with h5py.File(str(tcw_path), "r") as handle:
            field = handle["/data"]
            if field.ndim != 3:
                raise ValueError(f"{tcw_path.name}: TCWV cube is {field.shape}, "
                                 f"expected hours x lat x lon")
            # rs-h5 v1 (2026-09): /data is uint16 kg m**-2 * 100 with
            # scale_factor = 0.01; the coefficient table wants cm
            cube = np.asarray(field[...], dtype=np.float32) * \
                float(field.attrs.get("scale_factor", 1.0))
        cube = cube / 10.0
        if cube.max() > 20.0:
            raise ValueError(f"{tcw_path.name}: TCWV reaches {cube.max():.1f} cm, "
                             f"scale is wrong")
        _STATE["tcw_day"] = cube
        _STATE["tcw_path"] = tcw_path
    lai0, tcw_day = _STATE["lai0"], _STATE["tcw_day"]

    tif_dir = _STATE["root"] / str(year) / "tif"
    lst_dir = _STATE["out_root"] / str(year) / "lst"
    for scene in scenes:
        try:
            hour = int(scene.split("____")[1][9:11])
        except (IndexError, ValueError):
            stats["skipped"] += 1
            continue
        view_stats = []
        for view in ("nadir", "obliq"):
            out_file = lst_dir / scene / f"lst_{view}.tif"
            try:
                view_stats.append(lst_view(view, tif_dir / scene, out_file, lai0,
                                           tcw_day, hour, _STATE["overwrite"]))
            except Exception as exc:  # noqa: BLE001
                view_stats.append("error")
                stats["error"] = f"{scene} {view}: {exc!r}"
        if "written" in view_stats:
            stats["written"] += 1
        elif "error" in view_stats:
            stats["skipped"] += 1
        else:
            stats["empty"] += 1
            stats["empty_scenes"].append(scene)
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                    help="scene tree: <root>/<year>/tif/<scene>/")
    ap.add_argument("--out-root", type=Path, default=None,
                    help="where the lst tree is written (default: --root)")
    ap.add_argument("--base", type=Path, default=DEFAULT_BASE,
                    help="case auxiliary tree with emis/, type/, base/")
    ap.add_argument("--type-ref", type=Path, default=DEFAULT_TYPE_REF)
    ap.add_argument("--tcwv-root", type=Path, default=DEFAULT_TCWV_ROOT)
    ap.add_argument("--emis-pair", choices=["11,12", "11,11"], default="11,12",
                    help="soil emissivity bands for S8,S9 (slstr_lst.py reuses LSE11)")
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--days", nargs="*", default=None, help="only these YYYYMMDD days")
    ap.add_argument("--limit-days", type=int, default=None)
    ap.add_argument("--force-scenes", nargs="*", default=None,
                    help="process exactly these scenes (used for validation)")
    ap.add_argument("--overwrite", action="store_true",
                    help="recompute scenes that already have an output")
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all-scenes", action="store_true",
                    help="ignore the coverage skip list and read every scene")
    args = ap.parse_args()
    global SKIP_MARKED_SCENES
    SKIP_MARKED_SCENES = not args.all_scenes
    out_root = args.out_root or args.root

    t0 = time.time()
    if args.force_scenes:
        by_day = defaultdict(list)
        for scene in args.force_scenes:
            by_day[scene.split("____")[1][:8]].append(scene)
    else:
        by_day = discover(args.root, args.year)
    days = sorted(by_day)
    if args.days:
        days = [d for d in days if d in set(args.days)]
    if args.limit_days:
        days = days[:args.limit_days]
    total = builtins.sum(len(by_day[d]) for d in days)
    print(f"{args.year}: {total} scenes without LST over {len(days)} acquisition days "
          f"({time.time() - t0:.0f}s scan)", flush=True)
    if args.dry_run or not days:
        return

    print("loading base rasters ...", flush=True)
    t0 = time.time()
    emis_pair = ((SOIL_EMISSIVITY[0], SOIL_EMISSIVITY[1]) if args.emis_pair == "11,12"
                 else (SOIL_EMISSIVITY[0], SOIL_EMISSIVITY[0]))
    state = load_state(args.root, args.base, args.type_ref, emis_pair)
    state["overwrite"] = args.overwrite
    print(f"  base loaded in {time.time() - t0:.0f}s "
          f"(type {state['classif0'].shape}, emis {emis_pair[0][-8:-4]}/"
          f"{emis_pair[1][-8:-4]})", flush=True)

    tasks = [(d, by_day[d]) for d in days]
    report = dict(year=args.year, root=str(args.root), out_root=str(out_root),
                  workers=args.workers, emis_pair=[p for p in emis_pair],
                  scenes=total, days=len(days), days_report=[], empty_scenes=[],
                  started=time.strftime("%Y-%m-%dT%H:%M:%S"))
    done = written = empty = skipped = 0
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init_worker,
                             initargs=(state, str(args.root), str(out_root),
                                       str(args.tcwv_root))) as pool:
        # chunksize 4 keeps consecutive days (same LAI file) on the same worker
        for stats in pool.map(process_day, tasks, chunksize=4):
            done += stats["scenes"]
            written += stats["written"]
            empty += stats["empty"]
            skipped += stats["skipped"]
            report["days_report"].append({k: v for k, v in stats.items() if k != "empty_scenes"})
            report["empty_scenes"].extend(stats["empty_scenes"])
            elapsed = time.time() - t0
            rate = done / elapsed if elapsed else 0
            eta = (total - done) / rate / 60 if rate else 0
            print(f"  {stats['day']}: {stats['scenes']:3d} scenes -> written {stats['written']:3d} "
                  f"empty {stats['empty']:3d} skipped {stats['skipped']:2d}"
                  f"{'  ERROR: ' + stats['error'] if stats['error'] else ''}"
                  f" | {done}/{total} {rate:.2f} scene/s eta {eta:.0f} min", flush=True)
    report.update(finished=time.strftime("%Y-%m-%dT%H:%M:%S"), written=written, empty=empty,
                  skipped=skipped, seconds=builtins.round(time.time() - t0, 1))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2))
        print("report ->", args.report)
    print(f"done: written {written}, empty {empty}, skipped {skipped} "
          f"in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
