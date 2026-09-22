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
``<root>/<year>/lsct2/<scene>/lsct2.tif`` (2 bands, float32, oblique grid).
Scenes without a valid pixel produce no file, exactly like the original; they
are listed in the run report so a later run can skip them.

usage:
  PYTHONPATH=. python cases/slstr/implementation/one_by_one/slstr_lsct2_parallel.py \
      --year 2020 --workers 24 --report cases/slstr/logs/lsct2_2020_report.json
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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from cases.slstr.support.util_constant import *          # noqa: F401,F403
from cases.slstr.support.util_file import *              # noqa: F401,F403
from cases.slstr.support.util_data import *              # noqa: F401,F403
from cases.slstr.support.util_lsct import *              # noqa: F401,F403

warnings.filterwarnings("ignore")

DEFAULT_ROOT = Path("/media/hero/slstr-euro-lst")
LAI_ROOTS = [
    (2002, 2020, Path("/media/hero/rs/lai/lai_2002-2020_0p01deg"), "LAI_%04d%03d.h5"),
    (2021, 2025, Path("/media/hero/rs/lai/lai_2021-2025_0p01deg"), "lai_%04d%03d.h5"),
]
TYPE_REF = "base/type/type_world_1000.tif"

# retrieval settings, verbatim from slstr_lsct2.py
WL = 10.8
SOIL_RADIANCE_VARIANCE = 2
LEAF_RADIANCE_VARIANCE = 1
SENSOR_NOISE = 0.5

_STATE: dict = {}


def doy4(year: int, day: date) -> int:
    return (((day - date(year, 1, 1)).days + 1) // 4) * 4 + 1


def lai_file(year: int, day: date) -> Path | None:
    for start, end, root, pattern in LAI_ROOTS:
        if start <= year <= end:
            path = root / str(year) / (pattern % (year, doy4(year, day)))
            return path if path.is_file() else None
    return None


def discover(root: Path, year: int, skip_scenes: set[str],
             only_days: set[str] | None = None) -> dict[str, list[str]]:
    """Scenes with an LST result but without an LSCT2 output, grouped by day."""
    lst_dir = root / str(year) / "lst"
    lsct_dir = root / str(year) / "lsct2"
    by_day: dict[str, list[str]] = defaultdict(list)
    if not lst_dir.is_dir():
        return by_day
    with os.scandir(lst_dir) as entries:
        names = sorted(e.name for e in entries if e.is_dir(follow_symlinks=False))
    for scene in names:
        if not (lst_dir / scene / "lst_nadir.tif").is_file():
            continue
        if (lsct_dir / scene / "lsct2.tif").is_file() or scene in skip_scenes:
            continue
        day = scene.split("____")[1][:8]
        if only_days and day not in only_days:
            continue
        by_day[day].append(scene)
    return by_day


def load_state(root: Path) -> dict:
    """Global base rasters; inherited by the workers through fork."""
    emis_dir = root / "base" / "emis"
    emis1_s0, _, _, _, _, _ = read_image_gdal(str(emis_dir / "AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif"))
    emis2_s0, _, _, _, _, _ = read_image_gdal(str(emis_dir / "AG1km.v003.SoilEmi.MODIS.Global.001D_LSE12.tif"))
    classif0, _, _, _, _, _ = read_image_gdal(str(root / TYPE_REF))
    return dict(
        emis1_s0=emis1_s0 / 1000.0,
        emis2_s0=emis2_s0 / 1000.0,
        classif0=np.asarray(classif0, int),
        emis_v=read_txt_array(str(emis_dir / "IGBP_Emi.txt"), 0, 2),
        coeffs_day=read_txt_array(str(emis_dir / "Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt"), 0, 15)[:, 2:10],
        coeffs_night=read_txt_array(str(emis_dir / "Sentinel3A_SLSTR_SW_Seebor_Coef_Night.txt"), 0, 15)[:, 2:10],
    )


def _init_worker(state: dict, root: str, out_root: str) -> None:
    _STATE.update(state)
    _STATE["root"] = Path(root)
    _STATE["out_root"] = Path(out_root)
    # loc2map() equivalent: only the geotransform of the reference raster is used
    _STATE["ref_ds"] = gdal.Open(str(Path(root) / TYPE_REF))
    _STATE["inv_Cm"] = np.linalg.inv(np.diag([SOIL_RADIANCE_VARIANCE, LEAF_RADIANCE_VARIANCE]))
    _STATE["inv_Cd"] = 1.0 / (SENSOR_NOISE ** 2)


def index_map(ref_ds, lat: np.ndarray, lon: np.ndarray):
    """Same indices as loc2map() returns (row index first, then column index)."""
    imagex, imagey = geo2imagexy(ref_ds, *lonlat2geo(ref_ds, lat, lon))
    return np.asarray(imagex, np.int_), np.asarray(imagey, np.int_)


def lsct2_scene(scene: str, year: int, lat: np.ndarray, lon: np.ndarray,
                lai0: np.ndarray, out_file: Path) -> str:
    """LSCT2 for one scene: 'written', 'no_valid_pixel' or 'skipped'."""
    root: Path = _STATE["root"]
    tif_dir = root / str(year) / "tif" / scene
    lst_dir = root / str(year) / "lst" / scene
    # slstr_lsct2.py creates the output folder before the input checks, so
    # "attempted but empty" scenes are left as empty folders
    out_file.parent.mkdir(parents=True, exist_ok=True)
    needed = [lst_dir / "lst_nadir.tif", lst_dir / "lst_obliq.tif",
              tif_dir / "vza_nadir.tif", tif_dir / "vza_obliq.tif",
              tif_dir / "cloud_nadir.tif", tif_dir / "cloud_obliq.tif"]
    # NB: build a list first - ``all`` is shadowed by numpy through the
    # ``from cases.slstr.support.util_* import *`` imports above.
    if [p for p in needed if not p.is_file()]:
        return "skipped"

    # Cheap pre-check before reading the rest of the scene: the retrieval mask
    # needs ``lai > 0.25``, so a scene whose whole footprint is ocean, ice or
    # desert (LAI nodata/0) can never produce an LSCT2 pixel.  Most of the
    # remaining scenes on this disk are polar night passes of that kind.
    indx_lai, indy_lai = index_map(_STATE["ref_ds"], lat / 100.0, lon / 100.0)
    ind = indx_lai > 18000
    if np.sum(ind) > 0:                      # fill values, as in slstr_lsct2.py
        indx_lai[ind] = 17999
    nrow, ncol = _STATE["classif0"].shape
    indx_lai = np.clip(indx_lai, 0, nrow - 1)
    indy_lai = np.clip(indy_lai, 0, ncol - 1)
    probe = lai0[indx_lai[::2], indy_lai[::2]]
    # valid vegetation: 0.25 < LAI < 10 (250/10000 in the uint16 field, nodata
    # is 32767) - exactly the condition used by the mask below
    if not np.any((probe > 250) & (probe < 10000)):
        return "no_valid_pixel"

    lstN, _, _, _, _, _ = read_image_gdal(str(lst_dir / "lst_nadir.tif"))
    lstO, ns, nl, _, _, _ = read_image_gdal(str(lst_dir / "lst_obliq.tif"))
    vzaN, _, _, _, _, _ = read_image_gdal(str(tif_dir / "vza_nadir.tif"))
    vzaO, _, _, _, _, _ = read_image_gdal(str(tif_dir / "vza_obliq.tif"))
    cldN, _, _, _, _, _ = read_image_gdal(str(tif_dir / "cloud_nadir.tif"))
    cldO, _, _, _, _, _ = read_image_gdal(str(tif_dir / "cloud_obliq.tif"))

    vzaN = vzaN / 100.0
    vzaO = vzaO / 100.0
    lstN = lstN / 100.0
    lstO = lstO / 100.0

    vzaNO = vzaN[0:adjust_ymax_no_g, adjust_xmin_no_g:adjust_xmax_no_g]
    lstNO = lstN[0:adjust_ymax_no_g, adjust_xmin_no_g:adjust_xmax_no_g]
    cldNO = cldN[0:adjust_ymax_no_g, adjust_xmin_no_g:adjust_xmax_no_g]

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

    mask0 = ((cldNO == 0) * (lai > 0.25) * (cldO == 0) * (lai < 10.01)
             * (emis > 0) * (bN0 > 5) * (bO0 > 5))
    indx_p, indy_p = np.where(mask0)
    if len(indx_p) == 0:
        return "no_valid_pixel"

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

    write_image_gdal(resultT, nl, ns, 2, '', '', str(out_file))
    return "written"


def process_day(task):
    day_str, scenes = task
    year = int(day_str[:4])
    day = date(year, int(day_str[4:6]), int(day_str[6:8]))
    path = lai_file(year, day)
    root: Path = _STATE["root"]
    stats = dict(day=day_str, scenes=len(scenes), written=0, empty=0, skipped=0,
                 error=None, empty_scenes=[])
    if path is None:
        stats["error"] = f"no LAI file for {day_str}"
        stats["skipped"] = len(scenes)
        return stats
    # four consecutive days share one LAI file; keep the last one loaded
    if _STATE.get("lai_path") != path:
        with h5py.File(str(path), "r") as handle:
            _STATE["lai0"] = np.array(handle["/data"])
        _STATE["lai_path"] = path
    lai0 = _STATE["lai0"]
    out_dir = _STATE["out_root"] / str(year) / "lsct2"
    tif_dir = root / str(year) / "tif"
    for scene in scenes:
        lat_file, lon_file = tif_dir / scene / "lat_obliq.tif", tif_dir / scene / "lon_obliq.tif"
        if not lat_file.is_file() or not lon_file.is_file():
            stats["skipped"] += 1
            continue
        lat, _, _, _, _, _ = read_image_gdal(str(lat_file))
        lon, _, _, _, _, _ = read_image_gdal(str(lon_file))
        try:
            status = lsct2_scene(scene, year, lat, lon, lai0, out_dir / scene / "lsct2.tif")
        except Exception as exc:  # noqa: BLE001
            status = "error"
            stats["error"] = f"{scene}: {exc!r}"
        if status == "written":
            stats["written"] += 1
        elif status == "no_valid_pixel":
            stats["empty"] += 1
            stats["empty_scenes"].append(scene)
        else:
            stats["skipped"] += 1
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--out-root", type=Path, default=None,
                    help="where the lsct2 tree is written (default: --root)")
    ap.add_argument("--year", type=int, default=2020)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--days", nargs="*", default=None, help="only these YYYYMMDD days")
    ap.add_argument("--limit-days", type=int, default=None)
    ap.add_argument("--skip-report", type=Path, default=None,
                    help="earlier report; the scenes it found empty are skipped")
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--force-scenes", nargs="*", default=None,
                    help="process exactly these scenes (used for validation)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    out_root = args.out_root or args.root

    skip_scenes: set[str] = set()
    if args.skip_report and args.skip_report.is_file():
        skip_scenes = set(json.loads(args.skip_report.read_text()).get("empty_scenes", []))

    t0 = time.time()
    if args.force_scenes:
        by_day = defaultdict(list)
        for scene in args.force_scenes:
            by_day[scene.split("____")[1][:8]].append(scene)
    else:
        by_day = discover(args.root, args.year, skip_scenes,
                          set(args.days) if args.days else None)
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
    state = load_state(args.root)
    print(f"  base loaded in {time.time() - t0:.0f}s (type {state['classif0'].shape})", flush=True)

    tasks = [(d, by_day[d]) for d in days]
    report = dict(year=args.year, root=str(args.root), workers=args.workers, scenes=total,
                  days=len(days), days_report=[], empty_scenes=[],
                  started=time.strftime("%Y-%m-%dT%H:%M:%S"))
    done = written = empty = skipped = 0
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init_worker,
                             initargs=(state, str(args.root), str(out_root))) as pool:
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
    print(f"done: written {written}, no valid pixel {empty}, skipped {skipped} "
          f"in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
