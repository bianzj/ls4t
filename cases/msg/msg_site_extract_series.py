#!/usr/bin/env python3
"""Extract site time series from the LSCT archive for a seasonally balanced sample.

The cached ``LSCT_Site_Results_2025.csv`` covers 2018-2020 only and is very
sparse at the site pixels, which limits any validation against ICOS data that
mostly starts in 2020/2021.  This script re-extracts the four LSCT bands at all
in-domain sites from a regular sample of the archive (default: every 4th day,
2018-2025, hours 09-16 UTC) so the validation sample matches the in-situ record.

Differences from the legacy extraction (cases/validation/extract_point_lst_from_msg.py):

* sites outside the product domain are skipped instead of being snapped to the
  nearest grid edge;
* the grid pixel is accepted only if the site is within ``MAX_PIXEL_DIST``
  degrees of the pixel centre;
* only the needed HDF5 chunks are read (fancy indexing on rows/columns) instead
  of the whole 4x3333x2633 array.

Usage:
    PYTHONPATH=. python cases/validation/repro/extract_site_series.py [--step 4]
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

import h5py
import numpy as np
import pandas as pd
import rasterio

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")

PRODUCT_ROOT = "/media/hero/MSG/PRODUCTS/LSCT/MLST_COMPONENT"
SITES_CSV = "/media/hero/MSG/field/sites-2025.csv"
LAT_TIF = "/media/hero/MSG/Static/combined_euro_lat.tif"
LON_TIF = "/media/hero/MSG/Static/combined_euro_lon.tif"

DOMAIN = (-18.0, -35.0, 61.0, 65.0)  # west, south, east, north
MAX_PIXEL_DIST = 0.05                # deg, ~1.5 product pixels
HOURS = range(9, 17)
BANDS = ["ts", "tv", "ts1", "ts2"]


def site_pixels() -> pd.DataFrame:
    with rasterio.open(LAT_TIF) as ds:
        lat = ds.read(1).astype(np.float32) / 100.0
    with rasterio.open(LON_TIF) as ds:
        lon = ds.read(1).astype(np.float32) / 100.0
    sites = pd.read_csv(SITES_CSV)
    w, s, e, n = DOMAIN
    inside = sites[(sites.lon >= w) & (sites.lon <= e) & (sites.lat >= s) & (sites.lat <= n)].copy()
    rows, cols, dist = [], [], []
    for _, r in inside.iterrows():
        d2 = (lat - r.lat) ** 2 + (lon - r.lon) ** 2
        idx = int(np.nanargmin(d2))
        i, j = np.unravel_index(idx, lat.shape)
        rows.append(i)
        cols.append(j)
        dist.append(float(np.sqrt(d2[i, j])))
    inside["row"], inside["col"], inside["pixel_dist_deg"] = rows, cols, dist
    outside = sites[~sites.id.isin(inside.id)]
    print(f"sites: {len(sites)} total, {len(inside)} inside the domain, {len(outside)} skipped")
    print(f"skipped sites: {', '.join(outside.id)}")
    return inside


def day_iter(start: str, end: str, step: int):
    d0 = dt.date.fromisoformat(start)
    d1 = dt.date.fromisoformat(end)
    day = d0
    while day <= d1:
        if (day - d0).days % step == 0:
            yield day
        day += dt.timedelta(days=1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=int, default=15, help="keep every Nth day (default 15)")
    ap.add_argument("--start", default="2018-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--window", type=int, default=2,
                    help="search radius in pixels for a valid sample (legacy used 2 -> 5x5)")
    args = ap.parse_args()
    half = args.window

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sites = site_pixels()
    rows = sites["row"].to_numpy()
    cols = sites["col"].to_numpy()
    names = sites["id"].tolist()

    # This h5py build refuses multi-vector fancy indexing (``ds[:, rows, cols]``
    # and even ``ds[:, r, cols]`` raise "Indexing elements must be in increasing
    # order"), so read the chunks that actually contain a site and pick the
    # pixels locally.  The dataset is chunked as (1, 209, 165).
    with h5py.File(
        os.path.join(PRODUCT_ROOT, "2018", "01", "01", "MSG_LSCT_201801011000.h5"), "r"
    ) as probe:
        chunk = probe["data"].chunks
        shape = probe["data"].shape
    # every chunk touched by a site's search window
    r_lo = np.clip(rows - half, 0, shape[1] - 1)
    r_hi = np.clip(rows + half, 0, shape[1] - 1)
    c_lo = np.clip(cols - half, 0, shape[2] - 1)
    c_hi = np.clip(cols + half, 0, shape[2] - 1)
    site_chunks = []
    for k in range(len(rows)):
        site_chunks.append({
            (rc, cc)
            for rc in range(r_lo[k] // chunk[1], r_hi[k] // chunk[1] + 1)
            for cc in range(c_lo[k] // chunk[2], c_hi[k] // chunk[2] + 1)
        })
    needed = sorted(set().union(*site_chunks))
    chunk_sites = {key: [k for k in range(len(rows)) if key in site_chunks[k]] for key in needed}
    print(f"grid {shape}, chunk {chunk}, site chunks needed: {len(needed)}")
    print(f"valid-pixel search window: {2 * half + 1}x{2 * half + 1} (nearest valid pixel)")

    records = []
    missing_days = 0
    read_days = 0
    for day in day_iter(args.start, args.end, args.step):
        day_files = []
        for hour in HOURS:
            path = os.path.join(
                PRODUCT_ROOT, f"{day:%Y}", f"{day:%m}", f"{day:%d}",
                f"MSG_LSCT_{day:%Y%m%d}{hour:02d}00.h5",
            )
            if os.path.exists(path):
                day_files.append((hour, path))
        if not day_files:
            missing_days += 1
            continue
        read_days += 1
        for hour, path in day_files:
            try:
                with h5py.File(path, "r") as f:
                    dset = f["data"]
                    vals = np.full((4, len(rows)), np.nan, dtype=np.float32)
                    for band in range(4):
                        for key in needed:
                            rc, cc = key
                            r0, c0 = rc * chunk[1], cc * chunk[2]
                            r1 = min(r0 + chunk[1], shape[1])
                            c1 = min(c0 + chunk[2], shape[2])
                            block = dset[band, r0:r1, c0:c1]
                            for k in chunk_sites[key]:
                                rr, ccol = int(rows[k]), int(cols[k])
                                # nearest non-zero sample inside the search window
                                lr0 = max(rr - half - r0, 0)
                                lr1 = min(rr + half - r0 + 1, block.shape[0])
                                lc0 = max(ccol - half - c0, 0)
                                lc1 = min(ccol + half - c0 + 1, block.shape[1])
                                patch = block[lr0:lr1, lc0:lc1]
                                ok = patch > 0
                                if not ok.any():
                                    continue
                                pr, pc = np.nonzero(ok)
                                dr = pr + lr0 - (rr - r0)
                                dc = pc + lc0 - (ccol - c0)
                                best = int(np.argmin(dr * dr + dc * dc))
                                vals[band, k] = patch[pr[best], pc[best]]
            except Exception as exc:  # corrupt file: skip, do not fail the sweep
                print(f"  ! {path}: {exc}")
                continue
            vals /= 100.0
            vals[vals == 0] = np.nan                                          # nodata
            stamp = f"{day:%Y%m%d}{hour:02d}00"
            for k, name in enumerate(names):
                records.append((name, stamp, *vals[:, k]))
        if read_days % 25 == 0:
            print(f"  ...{read_days} days read, {len(records)} site records", flush=True)

    out = pd.DataFrame(records, columns=["Site", "DateTime"] + BANDS)
    out["dt"] = pd.to_datetime(out["DateTime"], format="%Y%m%d%H%M")
    csv_path = os.path.join(OUTPUT_DIR, "site_series_sampled.csv")
    map_path = os.path.join(OUTPUT_DIR, "site_pixel_map.csv")
    out.to_csv(csv_path, index=False)
    sites.to_csv(map_path, index=False)

    print(
        f"\ndays read: {read_days} (skipped without any product: {missing_days}), "
        f"records: {len(out)}, sites: {out['Site'].nunique()}, "
        f"years: {sorted(out['dt'].dt.year.unique())}"
    )
    valid = out[BANDS].notna().mean().round(4).to_dict()
    print(f"valid fraction per band: {valid}")
    print(f"largest site pixel distance: {sites['pixel_dist_deg'].max():.4f} deg")
    print(f"wrote {csv_path}\nwrote {map_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
