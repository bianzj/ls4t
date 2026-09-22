#!/usr/bin/env python3
"""Faithful reproduction of the legacy Evora LST validation.

Source recipe: cases/msg-fit/msg-val-evo.py (committed, but not runnable here):

* it imports ``base.util_lst`` / ``base.util_phys``, which do not exist in this
  worktree, and in the framework ``base/`` has neither module either
  (``planck``/``inv_planck`` live in ``cases/support/util_phys.py``);
* every input/output path points at the author's macOS tree
  (``/Users/bianzj/Downloads/data/msg/...``) instead of the mounted data disk.

This script keeps the recipe identical -- same date window, same hour
selection, same |diff| <= 10 K outlier rule, same emissivity/sky correction,
same reference ``fc * Tcrown + (1 - fc) * Tgrass`` -- and only replaces the two
input paths and the planck helper, so the output can be compared against the
committed ``cases/msg-fit/Validation_Stats_Nadir_vs_Obs.csv``.

Usage:
    PYTHONPATH=. python cases/validation/repro/repro_evora_lst.py
"""

from __future__ import annotations

import os
import sys

import matplotlib

matplotlib.use("Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplcfg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_squared_error

from base.radiometry import inv_planck, planck  # noqa: E402

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")

# ----------------------------------------------------------------------------
# Legacy configuration (msg-val-evo.py, unchanged)
# ----------------------------------------------------------------------------
FITTING_FILE = "/media/hero/MSG/PRODUCTS/SITE/ALL_SITES_LST_FITTING_RESULTS.csv"
MEASURED_FILE = "/media/hero/MSG/field/Evo-2017.csv"
COMMITTED_STATS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "Validation_Stats_Nadir_vs_Obs.csv"
)

TARGET_SITE = "Evora"
START_DATE = "2017-08-01"
END_DATE = "2017-12-31"
SELECT_HOURS = list(range(9, 16))
DIFF_THRESHOLD = 10.0
EMIS_V = 0.985
EMIS_S = 0.975
TSKY = 250.0

TASKS = [
    ("LST_obs_E", "Original LST (Sensor E)"),
    ("LST_obs_I", "Original LST (Sensor I)"),
    ("LST_nadir_DTC", "Nadir DTC"),
    ("LST_nadir_DTCRL", "Nadir DTCRL"),
    ("LST_nadir_DTCLSFRL", "Nadir DTCLSFRL"),
]


def load_satellite() -> pd.DataFrame:
    df_all = pd.read_csv(FITTING_FILE)
    df_inf = df_all[df_all["site"] == TARGET_SITE].copy()
    df_inf["DateTime"] = pd.to_datetime(df_inf["date"]) + pd.to_timedelta(
        df_inf["local_time"], unit="h"
    )
    df_inf["DateTime"] = df_inf["DateTime"].dt.round("1min")
    return df_inf


def load_measured() -> pd.DataFrame:
    df_mea = pd.read_csv(MEASURED_FILE)
    df_mea["DateTime"] = pd.to_datetime(df_mea["Time"], dayfirst=True).dt.round("1min")
    for col in ("Ts", "Tcrown", "Tgrass"):
        if col in df_mea.columns and df_mea[col].mean() < 150:
            df_mea[col] = df_mea[col] + 273.15
    return df_mea


def build_reference(df_merge: pd.DataFrame) -> pd.DataFrame:
    df_merge["fc"] = 1 - np.exp(-0.5 * df_merge["LAI"])
    bg = planck(10.5, df_merge["Ts"])
    bv = planck(10.5, df_merge["Tcrown"])
    bsky = planck(10.5, TSKY)
    df_merge["Ts"] = inv_planck(10.5, (bg - (1 - EMIS_S) * bsky) / EMIS_S)
    df_merge["Tcrown"] = inv_planck(10.5, (bv - (1 - EMIS_V) * bsky) / EMIS_V)
    df_merge["LST_Ref"] = df_merge["fc"] * df_merge["Tcrown"] + (1 - df_merge["fc"]) * df_merge["Tgrass"]
    return df_merge


def wide_table(df_merge: pd.DataFrame) -> pd.DataFrame:
    df_e = df_merge[df_merge["sensor"] == "E"].rename(columns={"LST_obs": "LST_obs_E"})
    df_i = df_merge[df_merge["sensor"] == "I"].rename(columns={"LST_obs": "LST_obs_I"})
    cols_e = [
        "DateTime",
        "LST_Ref",
        "LST_obs_E",
        "LST_nadir_DTC",
        "LST_nadir_DTCRL",
        "LST_nadir_DTCLSFRL",
    ]
    return pd.merge(df_e[cols_e], df_i[["DateTime", "LST_obs_I"]], on="DateTime", how="inner")


def metrics(y_true: pd.Series, y_pred: pd.Series) -> dict:
    bias = float(np.mean(y_pred - y_true))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r_val, _ = stats.pearsonr(y_true, y_pred)
    return {"Bias": bias, "RMSE": rmse, "R": float(r_val), "N": int(len(y_true))}


def main() -> int:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df_merge = pd.merge(load_satellite(), load_measured(), on="DateTime")
    df_merge = build_reference(df_merge)
    df_merge = df_merge[(df_merge["DateTime"] >= START_DATE) & (df_merge["DateTime"] <= END_DATE)]
    df_merge = df_merge[df_merge["DateTime"].dt.hour.isin(SELECT_HOURS)]
    if df_merge.empty:
        print("no overlap between satellite and in-situ data")
        return 1

    df_plot = wide_table(df_merge)
    print(f"matched rows: {len(df_plot)} (satellite x in-situ, both sensors)")

    rows = []
    for col, title in TASKS:
        y_true = df_plot["LST_Ref"]
        y_pred = df_plot[col]
        mask = np.isfinite(y_true) & np.isfinite(y_pred)
        valid = mask & (np.abs(y_true - y_pred) <= DIFF_THRESHOLD)
        y_t, y_p = y_true[valid], y_pred[valid]
        if len(y_t) < 5:
            continue
        row = {"Task": title}
        row.update(metrics(y_t, y_p))
        rows.append(row)

    repro = pd.DataFrame(rows)[["Task", "RMSE", "Bias", "R", "N"]]
    repro_path = os.path.join(OUTPUT_DIR, "Validation_Stats_Nadir_vs_Obs_repro.csv")
    repro.to_csv(repro_path, index=False)

    print("\nreproduced statistics")
    print(repro.to_string(index=False))

    if os.path.exists(COMMITTED_STATS):
        committed = pd.read_csv(COMMITTED_STATS)
        cmp = committed.merge(repro, on="Task", suffixes=("_committed", "_repro"))
        print("\ncommitted vs reproduced (deltas should be ~0)")
        print(
            cmp.assign(
                dRMSE=cmp["RMSE_repro"] - cmp["RMSE_committed"],
                dBias=cmp["Bias_repro"] - cmp["Bias_committed"],
                dR=cmp["R_repro"] - cmp["R_committed"],
                dN=cmp["N_repro"] - cmp["N_committed"],
            )[
                ["Task", "RMSE_committed", "RMSE_repro", "dRMSE", "dBias", "dR", "dN"]
            ].to_string(index=False)
        )

    # publication-style agreement figure
    fig, axes = plt.subplots(2, 3, figsize=(15, 9.5))
    axes = axes.ravel()
    for ax, (col, title) in zip(axes, TASKS):
        y_true, y_pred = df_plot["LST_Ref"], df_plot[col]
        mask = np.isfinite(y_true) & np.isfinite(y_pred)
        valid = mask & (np.abs(y_true - y_pred) <= DIFF_THRESHOLD)
        y_t, y_p = y_true[valid], y_pred[valid]
        hb = ax.hexbin(y_t, y_p, gridsize=35, cmap="viridis", mincnt=1, linewidths=0.2)
        lo = min(y_t.min(), y_p.min()) - 2
        hi = max(y_t.max(), y_p.max()) + 2
        ax.plot([lo, hi], [lo, hi], "r--", lw=1.2)
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_xlabel("Reference LST (K)")
        ax.set_ylabel("Satellite LST (K)")
        m = metrics(y_t, y_p)
        ax.set_title(title)
        ax.text(
            0.04,
            0.78,
            f"N = {m['N']}\nRMSE = {m['RMSE']:.2f} K\nBias = {m['Bias']:+.2f} K\nR = {m['R']:.3f}",
            transform=ax.transAxes,
            fontsize=10,
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="0.7"),
        )
        fig.colorbar(hb, ax=ax, shrink=0.8, label="counts")
    axes[-1].axis("off")
    fig.suptitle(
        f"Evora LST validation, {START_DATE} to {END_DATE}, "
        f"hours {SELECT_HOURS[0]}-{SELECT_HOURS[-1]} (legacy recipe)",
        fontsize=14,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig_path = os.path.join(OUTPUT_DIR, "fig_evora_lst_agreement.png")
    fig.savefig(fig_path, dpi=200, bbox_inches="tight")
    print(f"\nwrote {repro_path}\nwrote {fig_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
