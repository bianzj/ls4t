#!/usr/bin/env python3
"""Render separate nadir and oblique previews for the PROJ test output."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from osgeo import gdal


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "proj_test_output" / "2017"
DATE = "20170118"


def read(mode: str):
    path = OUT / mode / f"{DATE}_lst_daily_{mode}.tif"
    ds = gdal.Open(str(path), gdal.GA_ReadOnly)
    if ds is None:
        raise RuntimeError(f"Cannot open {path}")
    data = ds.GetRasterBand(1).ReadAsArray().astype(np.float32)
    gt = ds.GetGeoTransform()
    ds = None
    data[data <= 0] = np.nan
    return data, gt


layers = {mode: read(mode) for mode in ("nadir", "obliq")}
valid = np.concatenate([data[np.isfinite(data)] for data, _ in layers.values()])
vmin, vmax = np.percentile(valid, [2, 98])

fig, axes = plt.subplots(1, 2, figsize=(14, 7), dpi=160, constrained_layout=True)
for ax, mode in zip(axes, ("nadir", "obliq")):
    data, gt = layers[mode]
    height, width = data.shape
    # Decimate only for the PNG preview; the GeoTIFFs remain full 1 km output.
    preview = np.ma.masked_invalid(data[::4, ::4])
    extent = (gt[0] / 1000, (gt[0] + width * gt[1]) / 1000,
              (gt[3] + height * gt[5]) / 1000, gt[3] / 1000)
    image = ax.imshow(preview, extent=extent, origin="upper", cmap="inferno",
                      vmin=vmin, vmax=vmax, interpolation="nearest")
    ax.set_title(f"{mode} — {DATE} — EPSG:6933")
    ax.set_xlabel("Easting (km)")
    ax.set_ylabel("Northing (km)")
    ax.grid(color="white", alpha=0.25, linewidth=0.5)
fig.colorbar(image, ax=axes, label="LST (K)", shrink=0.85)
fig.savefig(OUT / f"{DATE}_lst_daily_proj_comparison.png", facecolor="white")
print(OUT / f"{DATE}_lst_daily_proj_comparison.png")
