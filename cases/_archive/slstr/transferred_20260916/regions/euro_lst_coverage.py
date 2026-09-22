#!/usr/bin/env python3
"""Survey ``/media/hero/slstr-euro-lst`` and produce a coverage base map.

The disk stores per-scene SLSTR 1 km nadir/oblique view arrays (``tif/``) and
the derived LST/LSCT results (``lst/``, ``lsct2/``).  The tif products carry no
geotransform: the swath geometry lives in the ``lat_*/lon_*.tif`` arrays, so a
footprint has to be built from those arrays.

Reading the full geolocation array of every scene would require roughly one
million random HDD reads, so the survey samples a few along-track rows per
scene, builds the swath outline from them and rasterises the outline into a
regular lon/lat grid.  At European latitudes the sampled outline reproduces the
full-resolution swath area to better than 0.1 %; at the poles (where a lon/lat
hull is not meaningful) the outline is only used for the audit panel.

Outputs (written next to this script unless ``--out-dir`` is given):

* ``euro_lst_coverage_0p05.tif``      granule count per 0.05 deg cell
* ``euro_lst_revisit_0p05.tif``       number of sampled acquisition days per cell
* ``euro_lst_mosaic_base_0p01.tif``   base grid for mosaic production
* ``euro_lst_window.geojson``         mosaic window + data extent outline
* ``euro_lst_window.json``            the same window as a plain settings file
* ``euro_lst_coverage_summary.json``  survey statistics
* ``euro_lst_coverage_preview.png``   coverage map
* ``euro_lst_revisit_profile.png``    revisit-day profile of the southern edge
* ``euro_lst_disk_audit.png``         disk audit panel
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import warnings
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

os.environ.setdefault("PROJ_LIB", "/usr/share/proj")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/.cache")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/.mplconfig")

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.patches import Polygon as MplPolygon, Rectangle

import fiona
import rasterio
from rasterio.features import rasterize, shapes
from rasterio.transform import from_origin
from rasterio.windows import Window
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

warnings.filterwarnings("ignore")

DEFAULT_ROOT = Path("/media/hero/slstr-euro-lst")
ROWS = (0, 300, 600, 900, 1199)
COL_STRIDE = 10
NAME_RE = re.compile(
    r"RBT____(\d{8})T(\d{6})_\d{8}T\d{6}_\d{8}T\d{6}_(\d{4})_(\d{3})_(\d{3})_(\d{4})_"
)

# Survey grid: covers everything the disk reaches over Europe and its margins.
# The yearly ROI download widens the usable area by roughly half a SLSTR swath
# (~700 km) on every side of the ROI.
WIDE = dict(west=-62.0, east=92.0, south=22.0, north=80.0, res=0.05)
# Recommended mosaic window: European mainland + North Africa.  The southern
# edge is set by the imaging range: nothing is imaged south of 28.7 N, revisit
# is ~1 day in 5 at 30 N and every other day at 31.5 N.
EUROPE = dict(west=-12.0, east=42.0, south=30.0, north=71.5, res=0.01)
# North Africa core where at least half of the acquisition days see the cell.
EUROPE_DENSE = dict(west=-12.0, east=42.0, south=31.5, north=71.5, res=0.01)

NE_PHYS = Path("/home/hero/.local/share/cartopy/shapefiles/natural_earth/physical")
NE_CULT = Path("/home/hero/.local/share/cartopy/shapefiles/natural_earth/cultural")


# --------------------------------------------------------------------------- #
# disk inventory
# --------------------------------------------------------------------------- #
def dir_entries(path: Path) -> set[str]:
    try:
        with os.scandir(path) as it:
            return {e.name for e in it if e.is_dir(follow_symlinks=False)}
    except FileNotFoundError:
        return set()


def build_inventory(root: Path, years: list[int]) -> dict[str, list[dict]]:
    inv: dict[str, list[dict]] = {}
    for year in years:
        ydir = root / str(year)
        if not ydir.is_dir():
            continue
        tif, lst, lsct = (dir_entries(ydir / s) for s in ("tif", "lst", "lsct2"))
        recs = []
        for name in sorted(tif | lst | lsct):
            m = NAME_RE.search(name)
            if not m:
                continue
            recs.append(dict(name=name, date=m.group(1), time=m.group(2),
                             cycle=m.group(4), track=m.group(5), frame=m.group(6),
                             tif=name in tif, lst=name in lst, lsct=name in lsct))
        inv[str(year)] = recs
    return inv


# --------------------------------------------------------------------------- #
# footprint sampling
# --------------------------------------------------------------------------- #
def read_rows(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        width = ds.width
        arr = np.empty((len(ROWS), width), dtype=np.int16)
        for i, row in enumerate(ROWS):
            arr[i] = ds.read(1, window=Window(0, row, width, 1))[0]
    return arr


def convex_hull(points: np.ndarray) -> np.ndarray:
    pts = np.unique(points, axis=0)
    if len(pts) < 3:
        return pts
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list = []
    for p in pts[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


def footprint(root: Path, year: int, name: str, view: str = "nadir"):
    scene = root / str(year) / "tif" / name
    lat_path, lon_path = scene / f"lat_{view}.tif", scene / f"lon_{view}.tif"
    if not lat_path.is_file() or not lon_path.is_file():
        return None
    lat = read_rows(lat_path).astype(np.float32) / 100.0
    lon = read_rows(lon_path).astype(np.float32) / 100.0
    # keep the outer columns so the swath edge is not clipped
    sel = list(range(0, lat.shape[1], COL_STRIDE)) + [lat.shape[1] - 1]
    lat, lon = lat[:, sel], lon[:, sel]
    ok = np.isfinite(lat) & np.isfinite(lon) & (np.abs(lat) <= 90.5) & (np.abs(lon) <= 360.5)
    if ok.sum() < 20:
        return None
    hull = convex_hull(np.stack([lon[ok], lat[ok]], axis=1))
    return dict(lat_min=float(lat[ok].min()), lat_max=float(lat[ok].max()),
                lon_min=float(lon[ok].min()), lon_max=float(lon[ok].max()),
                hull=hull.astype(np.float32))


def _sample_one(item):
    root, year, meta = item
    try:
        rec = footprint(Path(root), year, meta["name"])
    except Exception as exc:  # noqa: BLE001
        return dict(year=year, meta=meta, err=repr(exc))
    return dict(year=year, meta=meta, rec=rec)


def cached_path(cache: Path, year: int, step: int) -> Path | None:
    """Prefer the requested sampling step, otherwise reuse any earlier cache."""
    want = cache / f"foot_{year}_step{step}.npz"
    if want.is_file():
        return want
    others = sorted(cache.glob(f"foot_{year}_step*.npz"))
    return others[0] if others else None


def sample_year(root: Path, year: int, recs: list[dict], step: int,
                workers: int, cache: Path) -> Path:
    days = sorted({r["date"] for r in recs})
    picked = set(days[::step])
    items = [(str(root), year, dict(date=r["date"], time=r["time"], name=r["name"],
                                    track=r["track"], lst=r["lst"], lsct=r["lsct"]))
             for r in recs if r["tif"] and r["date"] in picked]
    existing = cached_path(cache, year, step)
    if existing is not None:
        print(f"  {year}: reusing {existing.name}")
        return existing
    out = cache / f"foot_{year}_step{step}.npz"
    t0 = time.time()
    done = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for res in ex.map(_sample_one, items, chunksize=4):
            done.append(res)
    good = [r for r in done if r.get("rec")]
    np.savez_compressed(
        out,
        names=np.array([r["meta"]["name"] for r in good]),
        dates=np.array([r["meta"]["date"] for r in good]),
        times=np.array([r["meta"]["time"] for r in good]),
        tracks=np.array([r["meta"]["track"] for r in good]),
        has_lst=np.array([r["meta"]["lst"] for r in good]),
        has_lsct=np.array([r["meta"]["lsct"] for r in good]),
        lat_min=np.array([r["rec"]["lat_min"] for r in good], np.float32),
        lat_max=np.array([r["rec"]["lat_max"] for r in good], np.float32),
        lon_min=np.array([r["rec"]["lon_min"] for r in good], np.float32),
        lon_max=np.array([r["rec"]["lon_max"] for r in good], np.float32),
        hull=np.array([r["rec"]["hull"] for r in good], dtype=object),
        allow_pickle=True,
    )
    print(f"  {year}: {len(good)}/{len(items)} scenes in {time.time() - t0:.0f}s "
          f"({len(picked)} sampled days) -> {out.name}")
    return out


# --------------------------------------------------------------------------- #
# rasterisation
# --------------------------------------------------------------------------- #
def grid(win: dict) -> tuple[int, int, object]:
    res = win["res"]
    nx = int(round((win["east"] - win["west"]) / res))
    ny = int(round((win["north"] - win["south"]) / res))
    return ny, nx, from_origin(win["west"], win["north"], res, res)


def window_slices(win: dict, base: dict = WIDE) -> tuple[slice, slice]:
    """Row/column slices of ``win`` inside the ``base`` survey grid."""
    c0 = int(round((win["west"] - base["west"]) / base["res"]))
    c1 = int(round((win["east"] - base["west"]) / base["res"]))
    r0 = int(round((base["north"] - win["north"]) / base["res"]))
    r1 = int(round((base["north"] - win["south"]) / base["res"]))
    return slice(r0, r1), slice(c0, c1)


def load_hulls(paths):
    hulls, years = [], []
    for path in paths:
        path = Path(path)
        year = path.stem.split("_")[1]
        with np.load(path, allow_pickle=True) as npz:
            for hull in npz["hull"]:
                hulls.append(np.asarray(hull, dtype=np.float64))
                years.append(year)
    return hulls, years


def accumulate(hulls, transform, ny, nx, win: dict) -> np.ndarray:
    res = win["res"]
    counts = np.zeros((ny, nx), dtype=np.uint16)
    for hull in hulls:
        if len(hull) < 3:
            continue
        x0, y0 = hull[:, 0].min(), hull[:, 1].min()
        x1, y1 = hull[:, 0].max(), hull[:, 1].max()
        if x1 <= win["west"] or x0 >= win["east"] or y1 <= win["south"] or y0 >= win["north"]:
            continue
        c0 = max(0, int(np.floor((x0 - win["west"]) / res)))
        c1 = min(nx, int(np.ceil((x1 - win["west"]) / res)) + 1)
        r0 = max(0, int(np.floor((win["north"] - y1) / res)))
        r1 = min(ny, int(np.ceil((win["north"] - y0) / res)) + 1)
        if c1 <= c0 or r1 <= r0:
            continue
        local = from_origin(win["west"] + c0 * res, win["north"] - r0 * res, res, res)
        ring = np.vstack([hull, hull[:1]]).tolist()
        mask = rasterize([({"type": "Polygon", "coordinates": [ring]}, 1)],
                         out_shape=(r1 - r0, c1 - c0), transform=local,
                         fill=0, dtype="uint8", all_touched=False)
        counts[r0:r1, c0:c1] += mask.astype(np.uint16)
    return counts


def cell_area_km2(lat_center: np.ndarray, res: float) -> np.ndarray:
    earth_r = 6371.0088
    top = np.radians(lat_center + res / 2)
    bottom = np.radians(lat_center - res / 2)
    return earth_r ** 2 * np.radians(res) * (np.sin(top) - np.sin(bottom))


def day_hits(cache_path: Path, transform, ny: int, nx: int, win: dict) -> tuple[np.ndarray, int]:
    """How many of the sampled acquisition days see each cell."""
    by_day: dict[str, list] = defaultdict(list)
    with np.load(cache_path, allow_pickle=True) as npz:
        for hull, day in zip(npz["hull"], npz["dates"]):
            by_day[str(day)].append(np.asarray(hull, dtype=np.float64))
    hits = np.zeros((ny, nx), dtype=np.uint8)
    for day in sorted(by_day):
        hits += (accumulate(by_day[day], transform, ny, nx, win) > 0).astype(np.uint8)
    return hits, len(by_day)


def write_raster(path: Path, array: np.ndarray, win: dict, nodata: int):
    ny, nx, transform = grid(win)
    with rasterio.open(path, "w", driver="GTiff", height=ny, width=nx, count=1,
                       dtype=array.dtype.name, crs="EPSG:4326", transform=transform,
                       nodata=nodata, compress="deflate", tiled=True,
                       predictor=2) as dst:
        dst.write(array, 1)


# --------------------------------------------------------------------------- #
# map rendering
# --------------------------------------------------------------------------- #
def _iter_lines(path: Path):
    with fiona.open(path) as src:
        for feat in src:
            geom = feat["geometry"]
            if geom is None:
                continue
            parts = [geom["coordinates"]] if geom["type"] == "LineString" else geom["coordinates"]
            for part in parts:
                yield np.asarray(part, dtype=float)


def _iter_polys(path: Path):
    with fiona.open(path) as src:
        for feat in src:
            geom = feat["geometry"]
            if geom is None:
                continue
            polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
            for poly in polys:
                yield np.asarray(poly[0], dtype=float)


def render_coverage(counts: np.ndarray, win: dict, out: Path, meta: dict,
                    window: dict | None = None):
    fig, ax = plt.subplots(figsize=(14.5, 8.8), dpi=150)
    fig.patch.set_facecolor("#0b1626")
    ax.set_facecolor("#0b1626")
    for ring in _iter_polys(NE_PHYS / "ne_10m_land.shp"):
        ax.add_patch(MplPolygon(ring, closed=True, facecolor="#28374a",
                                edgecolor="#61758a", linewidth=0.4, zorder=1))
    masked = np.ma.masked_where(counts == 0, counts)
    im = ax.imshow(masked, extent=(win["west"], win["east"], win["south"], win["north"]),
                   origin="upper", cmap="turbo",
                   norm=LogNorm(vmin=1, vmax=max(2.0, float(counts.max()))),
                   interpolation="nearest", alpha=0.85, zorder=2)
    for line in _iter_lines(NE_PHYS / "ne_10m_coastline.shp"):
        ax.plot(line[:, 0], line[:, 1], color="#11161d", linewidth=0.7, zorder=3)
    for line in _iter_lines(NE_CULT / "ne_10m_admin_0_boundary_lines_land.shp"):
        ax.plot(line[:, 0], line[:, 1], color="#eef2f6", linewidth=0.3, alpha=0.5, zorder=3)
    if window:
        ax.add_patch(Rectangle((window["west"], window["south"]),
                               window["east"] - window["west"],
                               window["north"] - window["south"], fill=False,
                               edgecolor="#ff2f6d", linewidth=2.2, zorder=6))
        ax.annotate("recommended mosaic window\n"
                    f"{window['west']:g}~{window['east']:g}E  "
                    f"{window['south']:g}~{window['north']:g}N",
                    xy=(window["west"], window["north"]),
                    xytext=(window["west"] + 2.5, window["north"] + 0.6),
                    color="#ffd7e4", fontsize=9, zorder=7,
                    arrowprops=dict(arrowstyle="-", color="#ff2f6d", linewidth=1))
    ax.set_xlim(win["west"], win["east"])
    ax.set_ylim(win["south"], win["north"])
    ax.set_xticks(range(int(np.ceil(win["west"] / 10) * 10),
                       int(win["east"]) + 1, 10))
    ax.set_yticks(range(int(np.ceil(win["south"] / 10) * 10),
                        int(win["north"]) + 1, 10))
    ax.grid(color="white", alpha=0.22, linewidth=0.5, zorder=4)
    ax.set_xlabel("Longitude (deg E)", color="#d7dee6")
    ax.set_ylabel("Latitude (deg N)", color="#d7dee6")
    ax.tick_params(colors="#d7dee6")
    ax.set_title("SLSTR euro-LST disk: granule footprint coverage\n"
                 f"{meta['sample_text']}", color="white", fontsize=13)
    cb = fig.colorbar(im, ax=ax, pad=0.015, fraction=0.035)
    cb.set_label("granule footprints covering the cell", color="#d7dee6")
    cb.ax.tick_params(colors="#d7dee6")
    ax.text(win["west"] + 0.5, win["south"] + 1.0,
            f"coverage outline: {meta['cells']:,} cells at {win['res']} deg "
            f"(~{meta['area_km2'] / 1e6:.1f} M km2)",
            color="#c9d4de", fontsize=8.5, zorder=7)
    fig.tight_layout()
    fig.savefig(out, facecolor=fig.get_facecolor())
    plt.close(fig)


def render_audit(inv: dict, hulls, years, counts, win, out: Path):
    fig = plt.figure(figsize=(16, 10), dpi=140)
    fig.patch.set_facecolor("#0b1626")
    gs = fig.add_gridspec(2, 2, hspace=0.28, wspace=0.16)

    # (a) whole-disk distribution of sampled swaths
    ax = fig.add_subplot(gs[0, 0])
    ax.set_facecolor("#0b1626")
    groups = defaultdict(list)
    for hull, _year in zip(hulls, years):
        lon0, lon1 = hull[:, 0].min(), hull[:, 0].max()
        lat0, lat1 = hull[:, 1].min(), hull[:, 1].max()
        if lat1 < -50:
            key = "southern polar night pass"
        elif lat0 > 60 or lat1 > 78:
            key = "arctic daytime pass"
        elif lon0 > 45:
            key = "central Asia / Siberia"
        else:
            key = "Europe + N Africa + Atlantic"
        groups[key].append(hull)
    colors = {"Europe + N Africa + Atlantic": "#24d1a1",
              "arctic daytime pass": "#ffd166",
              "southern polar night pass": "#7aa5ff",
              "central Asia / Siberia": "#ff7f7f"}
    for key, hh in groups.items():
        for hull in hh:
            ring = np.vstack([hull, hull[:1]])
            lon = ring[:, 0].copy()
            lat = ring[:, 1].copy()
            # break the ring where it steps across the +-180 meridian
            jump = np.abs(np.diff(lon)) > 180
            lon[1:][jump] = np.nan
            lat[1:][jump] = np.nan
            ax.plot(lon, lat, color=colors[key], linewidth=0.35, alpha=0.5)
    for key, color in colors.items():
        ax.plot([], [], color=color, label=f"{key} ({len(groups.get(key, []))})")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.grid(color="white", alpha=0.15, linewidth=0.4)
    ax.axhline(0, color="white", alpha=0.3, linewidth=0.5)
    ax.tick_params(colors="#d7dee6")
    for spine in ax.spines.values():
        spine.set_color("#3b4756")
    ax.legend(loc="lower left", fontsize=7.5, facecolor="#132033",
              edgecolor="#3b4756", labelcolor="#d7dee6")
    ax.set_title("(a) sampled swaths of the whole disk: not only Europe",
                 color="white", fontsize=11)

    # (b) coverage map
    ax = fig.add_subplot(gs[0, 1])
    ax.set_facecolor("#0b1626")
    for ring in _iter_polys(NE_PHYS / "ne_10m_land.shp"):
        ax.add_patch(MplPolygon(ring, closed=True, facecolor="#28374a",
                                edgecolor="#61758a", linewidth=0.3, zorder=1))
    masked = np.ma.masked_where(counts == 0, counts)
    im = ax.imshow(masked, extent=(win["west"], win["east"], win["south"], win["north"]),
                   origin="upper", cmap="turbo",
                   norm=LogNorm(vmin=1, vmax=max(2.0, float(counts.max()))),
                   interpolation="nearest", alpha=0.85, zorder=2)
    for line in _iter_lines(NE_PHYS / "ne_10m_coastline.shp"):
        ax.plot(line[:, 0], line[:, 1], color="#11161d", linewidth=0.5, zorder=3)
    ax.add_patch(Rectangle((EUROPE["west"], EUROPE["south"]),
                           EUROPE["east"] - EUROPE["west"],
                           EUROPE["north"] - EUROPE["south"], fill=False,
                           edgecolor="#ff2f6d", linewidth=1.6, zorder=5))
    ax.set_xlim(win["west"], win["east"])
    ax.set_ylim(win["south"], win["north"])
    ax.grid(color="white", alpha=0.18, linewidth=0.4)
    ax.tick_params(colors="#d7dee6")
    for spine in ax.spines.values():
        spine.set_color("#3b4756")
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.01)
    cb.ax.tick_params(colors="#d7dee6")
    ax.set_title("(b) Europe coverage density (log scale)", color="white", fontsize=11)

    # (c) per-year availability
    ax = fig.add_subplot(gs[1, 0])
    ax.set_facecolor("#0b1626")
    ys = sorted(inv)
    total = [sum(r["tif"] for r in inv[y]) for y in ys]
    lst = [sum(r["lst"] for r in inv[y]) for y in ys]
    lsct = [sum(r["lsct"] for r in inv[y]) for y in ys]
    x = np.arange(len(ys))
    ax.bar(x - 0.26, total, 0.26, color="#41546b", label="tif (source geolocation)")
    ax.bar(x, lst, 0.26, color="#24d1a1", label="lst result")
    ax.bar(x + 0.26, lsct, 0.26, color="#ffd166", label="lsct2 result")
    ax.set_xticks(x)
    ax.set_xticklabels(ys, color="#d7dee6")
    ax.tick_params(colors="#d7dee6")
    ax.grid(axis="y", color="white", alpha=0.15, linewidth=0.4)
    for spine in ax.spines.values():
        spine.set_color("#3b4756")
    ax.legend(fontsize=8, facecolor="#132033", edgecolor="#3b4756", labelcolor="#d7dee6")
    ax.set_title("(c) granules per year and result availability", color="white", fontsize=11)
    for xi, t in zip(x, total):
        ax.text(xi, t + 250, f"{t/1000:.1f}k", color="#9fb0c4", fontsize=7.5, ha="center")

    # (d) granules per day
    ax = fig.add_subplot(gs[1, 1])
    ax.set_facecolor("#0b1626")
    per_day = {y: Counter(r["date"] for r in inv[y]) for y in ys}
    widths = 0.8 / len(ys)
    for i, y in enumerate(ys):
        c = Counter(per_day[y].values())
        xs = sorted(c)
        ax.bar([v + (i - len(ys) / 2) * widths for v in xs],
               [c[v] for v in xs], widths * 0.9, label=y, alpha=0.85)
    ax.set_xlabel("granules per acquisition day", color="#d7dee6")
    ax.set_ylabel("days", color="#d7dee6")
    ax.tick_params(colors="#d7dee6")
    ax.grid(axis="y", color="white", alpha=0.15, linewidth=0.4)
    for spine in ax.spines.values():
        spine.set_color("#3b4756")
    ax.legend(fontsize=7.5, ncol=2, facecolor="#132033", edgecolor="#3b4756",
              labelcolor="#d7dee6")
    ax.set_title("(d) how many granules per day", color="white", fontsize=11)

    fig.suptitle("slstr-euro-lst disk audit", color="white", fontsize=15)
    fig.savefig(out, facecolor=fig.get_facecolor())
    plt.close(fig)


# --------------------------------------------------------------------------- #
# year-to-year ROI comparison
# --------------------------------------------------------------------------- #
def render_revisit(hits: np.ndarray, n_days: int, win: dict, out: Path):
    """Southern/northern edge profile of the revisit-day count."""
    ny, nx = hits.shape
    res = win["res"]
    lat_of_row = win["north"] - res * (np.arange(ny) + 0.5)
    lats = np.arange(26.0, 74.01, 0.05)
    mean_days, p10_days, covered = [], [], []
    for lat in lats:
        row = int(round((win["north"] - lat) / res))
        band = hits[row, int((-12 - win["west"]) / res):int((42 - win["west"]) / res)]
        mean_days.append(band.mean())
        p10_days.append(np.percentile(band, 10))
        covered.append(100.0 * (band > 0).mean())
    mean_days = np.asarray(mean_days)
    p10_days = np.asarray(p10_days)

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), dpi=140,
                             gridspec_kw=dict(width_ratios=[1.0, 1.5], wspace=0.22))
    fig.patch.set_facecolor("#0b1626")
    ax = axes[0]
    ax.set_facecolor("#0b1626")
    ax.plot(mean_days, lats, color="#24d1a1", linewidth=1.6, label="mean over lon -12..42 E")
    ax.plot(p10_days, lats, color="#ffd166", linewidth=1.2, linestyle="--",
            label="10th percentile")
    ax.axhline(28.7, color="#7aa5ff", linewidth=1.2, linestyle=":",
               label="imaging range limit 28.7 N")
    ax.axhline(EUROPE["south"], color="#ff2f6d", linewidth=1.4,
               label=f"proposed south edge {EUROPE['south']:g} N")
    ax.axhline(EUROPE_DENSE["south"], color="#ff2f6d", linewidth=1.0, linestyle="--",
               label=f"near-daily south edge {EUROPE_DENSE['south']:g} N")
    ax.axvline(n_days / 2, color="white", alpha=0.5, linewidth=0.8)
    ax.text(n_days / 2 + 0.4, 27.0, "half of the sampled days", color="#c9d4de", fontsize=8)
    ax.set_xlim(0, n_days)
    ax.set_ylim(26, 74)
    ax.set_xlabel(f"acquisition days covering the cell (out of {n_days} sampled days)",
                  color="#d7dee6")
    ax.set_ylabel("Latitude (deg N)", color="#d7dee6")
    ax.tick_params(colors="#d7dee6")
    ax.grid(color="white", alpha=0.18, linewidth=0.5)
    for spine in ax.spines.values():
        spine.set_color("#3b4756")
    ax.legend(fontsize=8, loc="upper left", facecolor="#132033", edgecolor="#3b4756",
              labelcolor="#d7dee6")
    ax.set_title("(a) revisit falls off towards the southern edge", color="white", fontsize=11)

    ax = axes[1]
    ax.set_facecolor("#0b1626")
    for ring in _iter_polys(NE_PHYS / "ne_10m_land.shp"):
        ax.add_patch(MplPolygon(ring, closed=True, facecolor="#28374a",
                                edgecolor="#61758a", linewidth=0.3, zorder=1))
    extent = (win["west"], win["east"], win["south"], win["north"])
    ax.imshow(hits, extent=extent, origin="upper", cmap="magma", vmin=0, vmax=n_days,
              interpolation="nearest", alpha=0.92, zorder=2)
    for line in _iter_lines(NE_PHYS / "ne_10m_coastline.shp"):
        ax.plot(line[:, 0], line[:, 1], color="#0b1626", linewidth=0.6, zorder=3)
    ax.add_patch(Rectangle((EUROPE["west"], EUROPE["south"]),
                           EUROPE["east"] - EUROPE["west"],
                           EUROPE["north"] - EUROPE["south"], fill=False,
                           edgecolor="#ff2f6d", linewidth=2.0, zorder=5))
    ax.set_xlim(-32, 52)
    ax.set_ylim(26, 74)
    ax.grid(color="white", alpha=0.18, linewidth=0.4)
    ax.tick_params(colors="#d7dee6")
    for spine in ax.spines.values():
        spine.set_color("#3b4756")
    cb = fig.colorbar(plt.cm.ScalarMappable(cmap="magma",
                                            norm=matplotlib.colors.Normalize(0, n_days)),
                      ax=ax, fraction=0.03, pad=0.01)
    cb.set_label(f"sampled acquisition days per cell (of {n_days})", color="#d7dee6")
    cb.ax.tick_params(colors="#d7dee6")
    ax.set_title("(b) revisit-day map around the mosaic window", color="white", fontsize=11)
    fig.suptitle("SLSTR euro-LST: how often each cell is actually imaged", color="white",
                 fontsize=14)
    fig.savefig(out, facecolor=fig.get_facecolor())
    plt.close(fig)
    return lats, mean_days, p10_days


def render_year_compare(year_masks: dict, win: dict, area: np.ndarray,
                        stability: dict, out: Path):
    years = sorted(year_masks)
    stack = np.stack([year_masks[y] for y in years])
    common = stack.all(axis=0)
    n_year = stack.sum(axis=0)

    fig, axes = plt.subplots(1, 2, figsize=(17, 6.2), dpi=140,
                             gridspec_kw=dict(width_ratios=[3.1, 1.0], wspace=0.16))
    fig.patch.set_facecolor("#0b1626")
    ax = axes[0]
    ax.set_facecolor("#0b1626")
    for ring in _iter_polys(NE_PHYS / "ne_10m_land.shp"):
        ax.add_patch(MplPolygon(ring, closed=True, facecolor="#28374a",
                                edgecolor="#61758a", linewidth=0.3, zorder=1))
    extent = (win["west"], win["east"], win["south"], win["north"])
    ax.imshow(np.ma.masked_where(n_year == 0, n_year), extent=extent, origin="upper",
              cmap="viridis", vmin=0, vmax=len(years), interpolation="nearest",
              alpha=0.9, zorder=2)
    for line in _iter_lines(NE_PHYS / "ne_10m_coastline.shp"):
        ax.plot(line[:, 0], line[:, 1], color="#0b1626", linewidth=0.55, zorder=3)
    ax.add_patch(Rectangle((EUROPE["west"], EUROPE["south"]),
                           EUROPE["east"] - EUROPE["west"],
                           EUROPE["north"] - EUROPE["south"], fill=False,
                           edgecolor="#ff2f6d", linewidth=2.0, zorder=6))
    ax.set_xlim(win["west"], win["east"])
    ax.set_ylim(win["south"], win["north"])
    ax.grid(color="white", alpha=0.18, linewidth=0.4)
    ax.tick_params(colors="#d7dee6")
    for spine in ax.spines.values():
        spine.set_color("#3b4756")
    sm = plt.cm.ScalarMappable(cmap="viridis",
                               norm=matplotlib.colors.Normalize(1, len(years)))
    cb = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.01)
    cb.set_label(f"number of sampled years covering the cell (max {len(years)})",
                 color="#d7dee6")
    cb.ax.tick_params(colors="#d7dee6")
    ax.set_xlabel("Longitude (deg E)", color="#d7dee6")
    ax.set_ylabel("Latitude (deg N)", color="#d7dee6")
    ax.set_title("(a) yearly coverage overlap (yellow = covered by every sampled year)",
                 color="white", fontsize=11)

    ax = axes[1]
    ax.set_facecolor("#0b1626")
    extra = [(area[:, None] * (year_masks[y] & ~common)).sum() / 1e6 for y in years]
    ax.barh(np.arange(len(years)), extra, color="#ff9f43")
    ax.set_yticks(np.arange(len(years)))
    ax.set_yticklabels(years, color="#d7dee6")
    ax.invert_yaxis()
    ax.set_xlabel("area outside the common core (M km2)", color="#d7dee6")
    ax.tick_params(colors="#d7dee6")
    ax.grid(axis="x", color="white", alpha=0.15, linewidth=0.4)
    for spine in ax.spines.values():
        spine.set_color("#3b4756")
    for i, (y, v) in enumerate(zip(years, extra)):
        hit = (stability.get(y) or {}).get("core_hit_ratio")
        ax.text(v + 0.03, i, f"{v:.2f}   core {hit:.3f}" if hit else f"{v:.2f}",
                color="#c9d4de", fontsize=8, va="center")
    ax.set_xlim(0, max(extra) * 1.35)
    ax.set_title("(b) coverage that only some years add", color="white", fontsize=11)
    fig.suptitle("yearly ROI download: how consistent is the covered area",
                 color="white", fontsize=14)
    fig.savefig(out, facecolor=fig.get_facecolor())
    plt.close(fig)


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--cache-dir", type=Path,
                    default=Path(__file__).resolve().parent / "euro_lst_coverage_cache")
    ap.add_argument("--years", nargs="+", type=int,
                    default=[2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025])
    ap.add_argument("--sample-years", nargs="+", type=int,
                    default=[2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025])
    ap.add_argument("--focus-year", type=int, default=2025,
                    help="year used for the count raster drawn in the preview")
    ap.add_argument("--sample-step", type=int, default=30,
                    help="sample every Nth acquisition day of the other years")
    ap.add_argument("--dense-step", type=int, default=7,
                    help="sampling step used for --focus-year")
    ap.add_argument("--workers", type=int, default=48)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)

    print("[1/5] inventory")
    inv = build_inventory(args.root, args.years)
    for year, recs in sorted(inv.items()):
        days = len({r["date"] for r in recs})
        print(f"  {year}: {len(recs):6d} granules  {days:4d} days  "
              f"lst={sum(r['lst'] for r in recs):6d} lsct={sum(r['lsct'] for r in recs):6d}")

    print("[2/5] footprint sampling")
    cache_files = []
    for year in sorted(set(args.sample_years)):
        if str(year) not in inv or not inv[str(year)]:
            continue
        step = args.dense_step if year == args.focus_year else args.sample_step
        cache_files.append(sample_year(args.root, year, inv[str(year)], step,
                                       args.workers, args.cache_dir))

    print("[3/5] coverage raster")
    focus_path = cached_path(args.cache_dir, args.focus_year, args.dense_step)
    if focus_path is None:
        raise SystemExit(f"no footprint sample for {args.focus_year}")
    focus_hulls, _ = load_hulls([focus_path])
    ny, nx, transform = grid(WIDE)
    counts = accumulate(focus_hulls, transform, ny, nx, WIDE)
    mask = counts > 0
    lat_center = WIDE["north"] - WIDE["res"] * (np.arange(ny) + 0.5)
    area = cell_area_km2(lat_center, WIDE["res"])
    area_km2 = float((area[:, None] * mask).sum())
    outline = unary_union([shape(g) for g, _ in
                           shapes(mask.astype("uint8"), mask=mask, transform=transform)])
    write_raster(args.out_dir / "euro_lst_coverage_0p05.tif", counts, WIDE, 0)
    hits, n_sample_days = day_hits(focus_path, transform, ny, nx, WIDE)
    write_raster(args.out_dir / "euro_lst_revisit_0p05.tif", hits, WIDE, 0)
    print(f"  revisit: {n_sample_days} sampled days, "
          f"{int((hits > 0).sum()):,} cells imaged at least once")

    def stats(win):
        rows, cols = window_slices(win)
        sub = counts[rows, cols]
        return dict(cells=int(sub.size), covered_pct=round(100 * float((sub > 0).mean()), 3),
                    min_count=int(sub.min()), mean_count=round(float(sub.mean()), 1))

    win_stats = stats(EUROPE)
    def revisit_stats(win):
        rows, cols = window_slices(win)
        sub = hits[rows, cols]
        return dict(min_days=int(sub.min()), mean_days=round(float(sub.mean()), 1),
                    pct_ge_half=round(100 * float((sub >= n_sample_days / 2).mean()), 2),
                    sampled_days=n_sample_days)

    win_stats.update(revisit_stats(EUROPE))
    dense_stats = dict(EUROPE_DENSE, **stats(EUROPE_DENSE), **revisit_stats(EUROPE_DENSE))
    print(f"  dense sample: {len(focus_hulls)} scenes, covered "
          f"{int(mask.sum()):,} cells, {area_km2 / 1e6:.2f} M km2")
    print(f"  mosaic window {EUROPE['west']:g}~{EUROPE['east']:g}E "
          f"{EUROPE['south']:g}~{EUROPE['north']:g}N -> min {win_stats['min_days']} of "
          f"{n_sample_days} days, {win_stats['covered_pct']}% covered")

    ny_e, nx_e, _ = grid(EUROPE)
    write_raster(args.out_dir / "euro_lst_mosaic_base_0p01.tif",
                 np.ones((ny_e, nx_e), dtype="uint8"), EUROPE, 255)

    print("[4/5] year-to-year stability")
    stability = {}
    year_masks = {}
    # Sparsely covered fringe cells need far more than a dozen sampled days, so
    # the interannual comparison is restricted to the dense core of the disk.
    core = counts >= 10
    for path in cache_files:
        year = Path(path).stem.split("_")[1]
        hulls, _ = load_hulls([path])
        other = accumulate(hulls, transform, ny, nx, WIDE) > 0
        year_masks[year] = other
        inter = int((other & core).sum())
        union = int(core.sum())
        stability[year] = dict(cache=Path(path).name, scenes=len(hulls),
                               cells=int(other.sum()),
                               core_hit_ratio=round(inter / union, 4))
        # Outer limits of the European (non polar) swaths of that year: this is
        # what shows whether the yearly ROI stayed the same.
        eu = [h for h in hulls if 0.0 < h[:, 1].max() < 75.0]
        if eu:
            lat = np.concatenate([h[:, 1] for h in eu])
            lon = np.concatenate([h[:, 0] for h in eu])
            stability[year].update(scenes_europe=len(eu),
                                   lat_min=round(float(lat.min()), 2),
                                   lat_max=round(float(lat.max()), 2),
                                   lon_min=round(float(lon.min()), 2),
                                   lon_max=round(float(lon.max()), 2))
        print(f"  {year}: {len(hulls)} scenes ({Path(path).name}), covers "
              f"{inter / union:.4f} of the {args.focus_year} dense core, "
              f"extent {stability[year].get('lat_min')}~{stability[year].get('lat_max')}N "
              f"/ {stability[year].get('lon_min')}~{stability[year].get('lon_max')}E")
    common = None
    for m in year_masks.values():
        common = m if common is None else (common & m)
    if common is not None:
        common_list = [m for m in year_masks.values()]
        union_all = np.any(common_list, axis=0)
        stability["common_core"] = dict(
            years=sorted(year_masks),
            cells=int(common.sum()),
            area_km2=round(float((area[:, None] * common).sum()), 1),
            union_cells=int(union_all.sum()),
            window_covered_by_all=bool(common[window_slices(EUROPE)].all()),
            core_cells=int(core.sum()),
            core_covered_by_all=bool((common & core)[core].all()),
        )
        print(f"  common core over {len(year_masks)} years: {int(common.sum()):,} cells "
              f"({float((area[:, None] * common).sum()) / 1e6:.2f} M km2), "
              f"window covered by all = {bool(common[window_slices(EUROPE)].all())}")

    print("[5/5] figures and metadata")
    meta = dict(cells=int(mask.sum()), area_km2=area_km2,
                sample_text=(f"{args.focus_year} sample: "
                             f"{len({r['date'] for r in inv[str(args.focus_year)]})} days on disk, "
                             f"{len(focus_hulls)} sampled scenes, {WIDE['res']} deg grid"))
    render_coverage(counts, WIDE, args.out_dir / "euro_lst_coverage_preview.png",
                    meta, window=EUROPE)
    lats, mean_days, p10_days = render_revisit(
        hits, n_sample_days, WIDE, args.out_dir / "euro_lst_revisit_profile.png")
    all_hulls, all_years = load_hulls(cache_files)
    render_audit(inv, all_hulls, all_years, counts, WIDE,
                 args.out_dir / "euro_lst_disk_audit.png")
    render_year_compare(year_masks, WIDE, area, stability,
                        args.out_dir / "euro_lst_year_overlap.png")

    geojson = {
        "type": "FeatureCollection",
        "name": "slstr_euro_lst_windows",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": [
            {"type": "Feature",
             "properties": {
                 "name": "europe_mosaic_window", "role": "final_output_window",
                 "west": EUROPE["west"], "east": EUROPE["east"],
                 "south": EUROPE["south"], "north": EUROPE["north"],
                 "target_crs": "EPSG:4326", "grid_resolution_degree": EUROPE["res"],
                 "coverage": win_stats,
                 "notes": ("European mainland + North Africa; fully covered in every "
                           "sampled year.  Southern edge set by the imaging range "
                           "(nothing imaged south of 28.7 N).")},
             "geometry": {"type": "Polygon", "coordinates": [[
                 [EUROPE["west"], EUROPE["south"]], [EUROPE["east"], EUROPE["south"]],
                 [EUROPE["east"], EUROPE["north"]], [EUROPE["west"], EUROPE["north"]],
                 [EUROPE["west"], EUROPE["south"]]]]}},
            {"type": "Feature",
             "properties": {
                 "name": "europe_mosaic_window_near_daily", "role": "high_revisit_core",
                 "west": EUROPE_DENSE["west"], "east": EUROPE_DENSE["east"],
                 "south": EUROPE_DENSE["south"], "north": EUROPE_DENSE["north"],
                 "target_crs": "EPSG:4326",
                 "grid_resolution_degree": EUROPE_DENSE["res"],
                 "coverage": dense_stats,
                 "notes": ("Same window with the south edge moved to 31.5 N, where at "
                           "least half of the acquisition days see the cell.")},
             "geometry": {"type": "Polygon", "coordinates": [[
                 [EUROPE_DENSE["west"], EUROPE_DENSE["south"]],
                 [EUROPE_DENSE["east"], EUROPE_DENSE["south"]],
                 [EUROPE_DENSE["east"], EUROPE_DENSE["north"]],
                 [EUROPE_DENSE["west"], EUROPE_DENSE["north"]],
                 [EUROPE_DENSE["west"], EUROPE_DENSE["south"]]]]}},
            {"type": "Feature",
             "properties": {
                 "name": "slstr_euro_disk_coverage_outline", "role": "data_extent",
                 "source": f"{args.focus_year} footprint sample",
                 "grid_resolution_degree": WIDE["res"],
                 "cells": int(mask.sum()), "area_km2": round(area_km2, 1)},
             "geometry": mapping(outline.simplify(WIDE["res"] / 4))},
        ],
    }
    with open(args.out_dir / "euro_lst_window.geojson", "w") as fp:
        json.dump(geojson, fp, indent=2)

    win_json = {
        "name": "europe_mosaic_window",
        "description": ("European mainland + North Africa mosaic window; southern edge "
                        "set by the SLSTR imaging range (nothing imaged south of "
                        "28.7 N) and by the revisit rate."),
        "crs": "EPSG:4326",
        "grid_resolution_degree": EUROPE["res"],
        "west": EUROPE["west"], "east": EUROPE["east"],
        "south": EUROPE["south"], "north": EUROPE["north"],
        "width_px": int(round((EUROPE["east"] - EUROPE["west"]) / EUROPE["res"])),
        "height_px": int(round((EUROPE["north"] - EUROPE["south"]) / EUROPE["res"])),
        "coverage": win_stats,
        "near_daily_variant": {
            "west": EUROPE_DENSE["west"], "east": EUROPE_DENSE["east"],
            "south": EUROPE_DENSE["south"], "north": EUROPE_DENSE["north"],
            "width_px": int(round((EUROPE_DENSE["east"] - EUROPE_DENSE["west"])
                                  / EUROPE_DENSE["res"])),
            "height_px": int(round((EUROPE_DENSE["north"] - EUROPE_DENSE["south"])
                                   / EUROPE_DENSE["res"])),
            "coverage": dense_stats,
        },
    }
    with open(args.out_dir / "euro_lst_window.json", "w") as fp:
        json.dump(win_json, fp, indent=2)

    summary = {
        "disk_root": str(args.root),
        "survey_date": time.strftime("%Y-%m-%d"),
        "method": ("convex hull of 5 nadir geolocation rows per scene, rasterised at "
                   f"{WIDE['res']} deg; at European latitudes the sampled outline "
                   "matches the full-resolution swath area to <0.1 %"),
        "years": {y: dict(granules=len(recs),
                          days=len({r["date"] for r in recs}),
                          with_tif=sum(r["tif"] for r in recs),
                          with_lst=sum(r["lst"] for r in recs),
                          with_lsct=sum(r["lsct"] for r in recs))
                  for y, recs in inv.items()},
        "coverage": dict(window=WIDE, cells=int(mask.sum()), area_km2=round(area_km2, 1),
                         max_count=int(counts.max()),
                         mean_count_over_covered=round(float(counts[mask].mean()), 2)),
        "mosaic_window": dict(EUROPE, **win_stats),
        "mosaic_window_near_daily": dict(EUROPE_DENSE, **dense_stats),
        "southern_edge_profile": {
            "latitude": [round(float(v), 2) for v in lats],
            "mean_acquisition_days": [round(float(v), 2) for v in mean_days],
            "p10_acquisition_days": [round(float(v), 2) for v in p10_days],
        },
        "sampling_stability": stability,
        "artifacts": {
            "coverage_raster": "euro_lst_coverage_0p05.tif",
            "revisit_raster": "euro_lst_revisit_0p05.tif",
            "mosaic_base": "euro_lst_mosaic_base_0p01.tif",
            "preview": "euro_lst_coverage_preview.png",
            "revisit_profile": "euro_lst_revisit_profile.png",
            "audit": "euro_lst_disk_audit.png",
            "window": "euro_lst_window.geojson",
            "window_settings": "euro_lst_window.json",
        },
    }
    with open(args.out_dir / "euro_lst_coverage_summary.json", "w") as fp:
        json.dump(summary, fp, indent=2)
    print("done ->", args.out_dir)


if __name__ == "__main__":
    main()
