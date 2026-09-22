"""Monthly paired LST / LSCT2 composite.

A pixel enters the monthly mean only when the daily nadir LST *and* both LSCT2
component temperatures are valid on the same acquisition; otherwise the pixel
is dropped for that acquisition.  The monthly LST / Ts / Tv means therefore
share exactly one sample set -- the rule is "if one has a value, both have one,
otherwise neither does".

Input are the daily mosaics written by
``cases/slstr/slstr_daily_mosaic_scene.py``::

    <daily>/lst/<year>/<YYYYMMDD>_lst_nadir_<view>_<tag>_0p01.tif
    <daily>/lsct2/<year>/<YYYYMMDD>_lsct2_obliq_<view>_<tag>_0p01.tif

Output is one 4-band Float32 GeoTIFF per region-month-view::

    band 1  lst_k   monthly mean of the paired nadir LST      (K)
    band 2  ts_k    monthly mean of the LSCT2 soil component  (K)
    band 3  tv_k    monthly mean of the LSCT2 vegetation part (K)
    band 4  count   number of paired acquisitions per pixel

The algorithm takes plain paths; which region, which machine and which years
come from the case (``cases/slstr-*/case.toml``, ``machines/<machine>.toml``).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio

LST_BAND_NAMES = (
    "lst_k monthly mean (paired)",
    "ts_k monthly mean (paired)",
    "tv_k monthly mean (paired)",
    "paired_acquisition_count",
)


def collect_month(daily_root: Path, tag: str, year: int, month: int,
                  view: str) -> list[dict]:
    """The LST / LSCT2 file pairs of one month that can be composited."""
    lst_dir = Path(daily_root) / "lst" / str(year)
    lsct_dir = Path(daily_root) / "lsct2" / str(year)
    if not lst_dir.is_dir():
        raise FileNotFoundError(f"no daily LST directory: {lst_dir}")
    prefix = f"{year}{month:02d}"
    stamps = sorted({entry.name[:8] for entry in lst_dir.iterdir()
                     if entry.name.endswith(".tif") and entry.name[:6] == prefix})
    pairs = []
    for stamp in stamps:
        lst_path = lst_dir / f"{stamp}_lst_nadir_{view}_{tag}_0p01.tif"
        lsct_path = lsct_dir / f"{stamp}_lsct2_obliq_{view}_{tag}_0p01.tif"
        if lst_path.is_file() and lsct_path.is_file():
            pairs.append({"stamp": stamp, "view": view,
                          "lst": lst_path, "lsct2": lsct_path})
    return pairs


def monthly_paired(daily_root: Path, tag: str, year: int, month: int,
                   view: str = "day") -> tuple[np.ndarray, dict, dict]:
    """Mean LST / Ts / Tv of the pixels where LST and LSCT2 are both valid."""
    pairs = collect_month(daily_root, tag, year, month, view)
    if not pairs:
        raise ValueError(f"{year}-{month:02d} {view}: no paired LST/LSCT2 scene")

    lst_sum = ts_sum = tv_sum = None
    count = None
    used: list[str] = []
    profile: dict = {}
    for pair in pairs:
        with rasterio.open(pair["lst"]) as src:
            lst_raw = src.read(1)
            profile = src.profile
        with rasterio.open(pair["lsct2"]) as src:
            lsct = src.read()
        lst_valid = (lst_raw > 0) & (lst_raw < 65535)
        lsct_valid = ((lsct[0] > 0) & np.isfinite(lsct[0]) &
                      (lsct[1] > 0) & np.isfinite(lsct[1]))
        both = lst_valid & lsct_valid
        if not both.any():
            continue
        lst_k = np.where(both, lst_raw.astype("float32") / 100.0, 0.0)
        ts_k = np.where(both, lsct[0], 0.0)
        tv_k = np.where(both, lsct[1], 0.0)
        lst_sum = lst_k if lst_sum is None else lst_sum + lst_k
        ts_sum = ts_k if ts_sum is None else ts_sum + ts_k
        tv_sum = tv_k if tv_sum is None else tv_sum + tv_k
        count = both.astype("int16") if count is None else count + both.astype("int16")
        used.append(f"{pair['stamp']}_{pair['view']}")

    if count is None:
        raise ValueError(f"{year}-{month:02d} {view}: no pixel with both LST and LSCT2")
    divisor = np.maximum(count, 1)
    valid = count > 0
    result = np.zeros((4,) + count.shape, dtype="float32")
    result[0] = np.where(valid, lst_sum / divisor, np.nan)
    result[1] = np.where(valid, ts_sum / divisor, np.nan)
    result[2] = np.where(valid, tv_sum / divisor, np.nan)
    result[3] = count.astype("float32")
    stats = {
        "region_tag": tag,
        "year": year,
        "month": month,
        "view": view,
        "paired_acquisitions": len(used),
        "valid_pixels": int(valid.sum()),
        "observations_per_pixel_mean": float(count[valid].mean()) if valid.any() else 0.0,
        "paired_samples": int(count.astype("int64").sum()),
        "mean_lst_k": float(result[0][valid].mean()) if valid.any() else None,
        "mean_ts_k": float(result[1][valid].mean()) if valid.any() else None,
        "mean_tv_k": float(result[2][valid].mean()) if valid.any() else None,
        "acquisitions": used,
    }
    return result, profile, stats


def write_monthly_paired(out_root: Path, year: int, month: int, tag: str,
                         view: str, array: np.ndarray, profile: dict,
                         stats: dict) -> Path:
    """Write <out_root>/<year>/<YYYYMM>_monthly_paired_<tag>_<view>_0p01.tif."""
    year_root = Path(out_root) / str(year)
    year_root.mkdir(parents=True, exist_ok=True)
    stem = f"{year}{month:02d}_monthly_paired_{tag}_{view}_0p01"
    tif_path = year_root / f"{stem}.tif"
    json_path = year_root / f"{stem}.json"
    profile = dict(profile)
    profile.update(count=4, dtype="float32", compress="lzw", nodata=np.nan,
                   tiled=True, blockxsize=256, blockysize=256)
    with rasterio.open(tif_path, "w", **profile) as dst:
        dst.write(array.astype("float32"))
        for index, description in enumerate(LST_BAND_NAMES, start=1):
            dst.set_band_description(index, description)
    json_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    return tif_path
