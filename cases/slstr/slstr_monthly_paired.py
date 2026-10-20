#!/usr/bin/env python3
"""Monthly paired LST / LSCT2 composites for one SLSTR daily-mosaic case.

Every region-month-view of the case period becomes one 4-band GeoTIFF (mean
paired LST, soil component, vegetation component and the paired acquisition
count) plus a JSON statistics file.  A pixel is only kept when the daily nadir
LST and both LSCT2 components are valid in the same acquisition.

The daily input root, the monthly output root and the region tag come from the
case itself, so the run is driven entirely by ``cases/slstr-<region>``:

    PYTHONPATH=. python cases/slstr/slstr_monthly_paired.py \
        --case cases/slstr-america --machine hero --start-year 2023 --end-year 2023

Months without paired acquisitions are skipped, finished months are reused
unless ``--force`` is given, and the batch keeps going after a failing month.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import rasterio  # noqa: E402

from base.composite.monthly_paired import monthly_paired, write_monthly_paired  # noqa: E402


def load_case(case_dir: Path, machine: str) -> dict:
    import tomllib

    case_dir = Path(case_dir).resolve()
    case = tomllib.loads((case_dir / "case.toml").read_text())
    profile = tomllib.loads((case_dir / "machines" / f"{machine}.toml").read_text())
    paths = profile["paths"]
    if "monthly_output_root" not in paths:
        raise SystemExit(f"{case_dir}/machines/{machine}.toml has no monthly_output_root")
    return dict(
        case_id=case["case"]["id"],
        region=case["case"].get("region", "region"),
        daily_root=Path(paths["output_root"]),
        monthly_root=Path(paths["monthly_output_root"]),
        years=[int(y) for y in case.get("period", {}).get("years", [])],
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", type=Path, required=True,
                    help="case directory, e.g. cases/slstr-america")
    ap.add_argument("--machine", default="hero")
    ap.add_argument("--start-year", type=int, default=None)
    ap.add_argument("--end-year", type=int, default=None)
    ap.add_argument("--views", default="day,night")
    ap.add_argument("--force", action="store_true", help="recompute finished months")
    ap.add_argument("--log", type=Path, default=None)
    ap.add_argument("--progress", type=Path, default=None)
    args = ap.parse_args()

    case = load_case(args.case, args.machine)
    views = [v.strip() for v in args.views.split(",") if v.strip()]
    if not views:
        raise SystemExit("--views must name at least one of day / night")
    years = case["years"] or []
    start = args.start_year or (min(years) if years else 0)
    end = args.end_year or (max(years) if years else 0)
    if not start or not end:
        raise SystemExit("give --start-year/--end-year or set [period].years in case.toml")

    log_path = args.log or Path(f"/tmp/slstr_monthly_{case['region']}.log")
    progress_path = args.progress or Path(f"/tmp/slstr_monthly_{case['region']}.progress.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(text: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {text}"
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    plan = [(year, month, view) for year in range(start, end + 1)
            for month in range(1, 13) for view in views]
    log(f"{case['case_id']}: {len(plan)} region-month-view tasks "
        f"({start}-{end}, views={','.join(views)})")
    log(f"daily {case['daily_root']} -> monthly {case['monthly_root']}")

    started = time.time()
    done = skipped = failed = 0
    for index, (year, month, view) in enumerate(plan, start=1):
        target = (case["monthly_root"] / str(year) /
                  f"{year}{month:02d}_monthly_paired_{case['region']}_{view}_0p01.tif")
        if target.is_file() and not args.force:
            skipped += 1
            continue
        t0 = time.time()
        try:
            array, profile, stats = monthly_paired(case["daily_root"], case["region"],
                                                   year, month, view)
        except (FileNotFoundError, ValueError, rasterio.errors.RasterioIOError) as error:
            skipped += 1
            log(f"{index}/{len(plan)} {year}-{month:02d} {view}: skipped ({error})")
            continue
        except Exception as error:  # noqa: BLE001 - keep the batch alive
            failed += 1
            log(f"{index}/{len(plan)} {year}-{month:02d} {view}: failed ({error})")
            log(traceback.format_exc().strip().splitlines()[-1])
            continue
        tif_path = write_monthly_paired(case["monthly_root"], year, month,
                                        case["region"], view, array, profile, stats)
        done += 1
        log(f"{index}/{len(plan)} {year}-{month:02d} {view}: paired "
            f"{stats['paired_acquisitions']} acquisitions, {stats['valid_pixels']:,} pixels, "
            f"LST {stats['mean_lst_k']:.2f} K / Ts {stats['mean_ts_k']:.2f} K / "
            f"Tv {stats['mean_tv_k']:.2f} K ({time.time() - t0:.1f}s) -> {tif_path.name}")
        progress_path.write_text(json.dumps({
            "done": done, "skipped": skipped, "failed": failed, "total": len(plan),
            "elapsed_seconds": round(time.time() - started, 1),
            "last": f"{year}-{month:02d} {view}",
        }, ensure_ascii=False), encoding="utf-8")

    log(f"finished: {done} written, {skipped} skipped, {failed} failed "
        f"in {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
