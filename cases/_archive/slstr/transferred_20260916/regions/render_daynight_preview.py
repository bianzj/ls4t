#!/usr/bin/env python3
"""Render the four day/night and nadir/oblique daily products."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from osgeo import gdal


ROOT = Path(__file__).resolve().parent / "gdalwarp_daily_daynight" / "2017"
DATE = "20170118"
keys = (("day", "nadir"), ("day", "obliq"), ("night", "nadir"), ("night", "obliq"))


def load(period: str, mode: str):
    path = ROOT / period / mode / f"{DATE}_lst_daily.tif"
    ds = gdal.Open(str(path), gdal.GA_ReadOnly)
    if ds is None:
        raise RuntimeError(path)
    data = ds.GetRasterBand(1).ReadAsArray().astype(np.float32)
    gt = ds.GetGeoTransform()
    ds = None
    data[data <= 0] = np.nan
    return data, gt


layers = {key: load(*key) for key in keys}
valid = np.concatenate([data[np.isfinite(data)] for data, _ in layers.values()])
vmin, vmax = np.percentile(valid, [2, 98])
fig, axes = plt.subplots(2, 2, figsize=(14, 12), dpi=160, constrained_layout=True)
for ax, (period, mode) in zip(axes.flat, keys):
    data, gt = layers[(period, mode)]
    height, width = data.shape
    preview = np.ma.masked_invalid(data[::4, ::4])
    extent = (gt[0] / 1000, (gt[0] + width * gt[1]) / 1000,
              (gt[3] + height * gt[5]) / 1000, gt[3] / 1000)
    image = ax.imshow(preview, extent=extent, origin="upper", cmap="inferno",
                      vmin=vmin, vmax=vmax, interpolation="nearest")
    ax.set_title(f"{period} — {mode} — {DATE} — EPSG:6933")
    ax.set_xlabel("Easting (km)")
    ax.set_ylabel("Northing (km)")
    ax.grid(color="white", alpha=0.25, linewidth=0.5)
fig.colorbar(image, ax=axes, label="LST (K)", shrink=0.75)
output = ROOT / f"{DATE}_lst_daily_daynight_comparison.png"
fig.savefig(output, facecolor="white")
print(output)
