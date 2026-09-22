#!/usr/bin/env python3
"""Evora component-temperature (LSCT) validation: reproduction + improvement.

Source recipe: cases/implementation/display-dtc-eva.py

Part 1 -- reproduction.  The committed script cannot run as written:

* inputs/outputs point at ``/Users/bianzj/Downloads/data/msg/...``;
* it converts the in-situ ``Ts``/``Tcrown`` from degC to K while
  ``LSCT_Site_Results.csv`` stores the inverted components in degC, so the
  ``|inf - mea| <= 10`` rule rejects every sample and both panels end up empty;
* it then fixes the axis with ``ax.set_ylim(290, 340)`` (K) on top of degC data.

The cached table ``/media/hero/MSG/PRODUCTS/LSCT_Validation_Stats_Evora.csv``
belongs to an earlier revision.  Auditing it against the data that ships with
the case shows it is only half reproducible:

* row "(a) Soil Temperature" is exactly ``T_Sunlit_Soil`` vs the in-situ
  **Tgrass** column, December 2017 only, hours 10-16, ``|diff| <= 10``
  (deviation 0.000 degC, identical sample counts);
* row "(b) Vegetation Temperature" cannot be reproduced from any column of
  ``Evo-2017.csv`` (nor from any other CSV in ``/media/hero/MSG/field``): its
  reference series (18.2-21.7 degC) exists in none of them.

Part 2 -- improvement.  Validate the components against the in-situ variables
they physically correspond to (sunlit/shaded soil vs Ts, canopy vs Tcrown),
over the full August-December record, in consistent units, and report
RMSE/ubRMSE/bias/MAE/R/R2/slope together with the legacy comparison.

Usage:
    PYTHONPATH=. python cases/validation/repro/repro_evora_lsct.py
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

from base.radiometry import inv_planck, planck  # noqa: E402

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")

INFERRED_FILE = "/media/hero/MSG/PRODUCTS/LSCT_Site_Results.csv"
MEASURED_FILE = "/media/hero/MSG/field/Evo-2017.csv"
CACHED_STATS = "/media/hero/MSG/PRODUCTS/LSCT_Validation_Stats_Evora.csv"

TARGET_SITE = "Evora"
DIFF_THRESHOLD = 10.0
TSKY = 250.0
CACHED_HOURS = list(range(10, 17))

# legacy pairing that reproduces the cached "(a)" row exactly
LEGACY_PAIR = ("T_Sunlit_Soil", "Tgrass")
LEGACY_LABEL = "(a) Soil Temperature"
LEGACY_MONTH = 12

# improved, physically matched pairings (in-situ reference columns)
PAIRS = [
    ("T_Sunlit_Soil", "Ts", "sunlit soil vs Ts"),
    ("T_Shaded_Soil", "Ts", "shaded soil vs Ts"),
    ("T_Soil", "Ts", "areal soil vs Ts"),
    ("T_Vegetation", "Tcrown", "canopy vs Tcrown"),
]


def load_evora() -> dict:
    inv = pd.read_csv(INFERRED_FILE)
    inv = inv[inv["Site"] == TARGET_SITE].copy()
    inv["DateTime"] = pd.to_datetime(
        inv["DateTime"].astype("int64").astype(str), format="%Y%m%d%H%M"
    )
    mea = pd.read_csv(MEASURED_FILE)
    mea["DateTime"] = pd.to_datetime(mea["Time"], dayfirst=True)
    merged = pd.merge(inv, mea, on="DateTime")
    merged["Hour"] = merged["DateTime"].dt.hour
    return {"inv": inv, "mea": mea, "merged": merged}


def corrected(frame: pd.DataFrame, col: str, emis: float) -> pd.Series:
    """Emissivity/sky correction of the legacy recipe, kept in degC."""
    bsky = planck(10.5, TSKY)
    k = inv_planck(10.5, (planck(10.5, frame[col]) - (1 - emis) * bsky) / emis)
    return k - 273.15


def hourly(frame: pd.DataFrame, inf_col: str, mea_col: str, thr: float | None) -> pd.DataFrame:
    sub = frame[frame[inf_col].notna() & frame[mea_col].notna()].copy()
    if thr is not None:
        sub = sub[np.abs(sub[inf_col] - sub[mea_col]) <= thr]
    if sub.empty:
        return pd.DataFrame()
    g = sub.groupby("Hour")
    return pd.DataFrame(
        {
            "Hour": sorted(sub["Hour"].unique()),
            "inf_mean": g[inf_col].mean().values,
            "inf_sd": g[inf_col].std().values,
            "mea_mean": g[mea_col].mean().values,
            "mea_sd": g[mea_col].std().values,
            "count": g[inf_col].count().values,
        }
    ).sort_values("Hour")


def metrics(obs, pred) -> dict:
    obs = np.asarray(obs, float)
    pred = np.asarray(pred, float)
    err = pred - obs
    out = {
        "N": int(len(obs)),
        "Bias": float(np.mean(err)),
        "RMSE": float(np.sqrt(np.mean(err**2))),
        "MAE": float(np.mean(np.abs(err))),
        "ubRMSE": float(np.sqrt(np.mean((err - err.mean()) ** 2))),
    }
    if len(obs) > 2 and np.std(obs) > 0 and np.std(pred) > 0:
        r, _ = stats.pearsonr(obs, pred)
        lr = stats.linregress(obs, pred)
        out.update(R=float(r), R2=float(r**2), slope=float(lr.slope), intercept=float(lr.intercept))
    else:
        out.update(R=np.nan, R2=np.nan, slope=np.nan, intercept=np.nan)
    return out


def main() -> int:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = load_evora()
    merged = data["merged"]
    print(
        f"Evora: {len(data['inv'])} inverted records, {len(data['mea'])} in-situ records, "
        f"{len(merged)} exact timestamp matches "
        f"({merged['DateTime'].min()} to {merged['DateTime'].max()})"
    )

    # ---------------------------------------------------------------- part 1
    print("\n=== part 1: reproduction of the cached diurnal table ===")
    dec = merged[merged["DateTime"].dt.month == LEGACY_MONTH].copy()
    dec = dec[dec["Hour"].isin(CACHED_HOURS)]
    repro = hourly(dec, *LEGACY_PAIR, thr=DIFF_THRESHOLD)
    print(
        f"legacy setting: {LEGACY_PAIR[0]} vs {LEGACY_PAIR[1]}, December 2017, "
        f"hours {CACHED_HOURS[0]}-{CACHED_HOURS[-1]}, |diff| <= {DIFF_THRESHOLD:g} degC"
    )
    if os.path.exists(CACHED_STATS):
        cached = pd.read_csv(CACHED_STATS)
        ca = cached[cached["Variable"] == LEGACY_LABEL].set_index("Hour").sort_index()
        rp = repro.set_index("Hour").sort_index()
        cmp = pd.DataFrame(
            {
                "cached_inf": ca["inf_mean"],
                "repro_inf": rp["inf_mean"],
                "cached_mea": ca["mea_mean"],
                "repro_mea": rp["mea_mean"],
                "cached_n": ca["count"],
                "repro_n": rp["count"],
            }
        )
        cmp["abs_err"] = np.nanmax(
            np.abs(
                cmp[["cached_inf", "cached_mea"]].values - cmp[["repro_inf", "repro_mea"]].values
            ),
            axis=1,
        )
        print(cmp.round(3).to_string())
        print(f"-> maximum deviation from the cached row: {cmp['abs_err'].max():.3e} degC (exact)")

    veg = merged[merged["Hour"].isin(CACHED_HOURS)]
    veg_dec = veg[veg["DateTime"].dt.month == LEGACY_MONTH]
    print(
        "-> cached vegetation row reference means are 18.2-21.7 degC; December in-situ "
        f"hourly means are Ts {[round(v, 2) for v in veg_dec.groupby('Hour')['Ts'].mean()]}, "
        f"Tcrown {[round(v, 2) for v in veg_dec.groupby('Hour')['Tcrown'].mean()]}, "
        f"Tgrass {[round(v, 2) for v in veg_dec.groupby('Hour')['Tgrass'].mean()]} "
        "-> no column matches, the row is not reproducible from this data"
    )

    # ---------------------------------------------------------------- part 2
    print("\n=== part 2: improved validation (physical pairings, full record) ===")
    window = merged[merged["Hour"].isin(CACHED_HOURS)].copy()
    rows = []
    for inf_col, mea_col, label in PAIRS:
        valid = window[window[inf_col].notna() & window[mea_col].notna()]
        m = metrics(valid[mea_col], valid[inf_col])
        m.update(Component=inf_col, Reference=mea_col, Pairing=label, N_all=len(valid))
        qc = valid[np.abs(valid[inf_col] - valid[mea_col]) <= DIFF_THRESHOLD]
        m["N_qc"] = len(qc)
        m["RMSE_qc"] = float(np.sqrt(np.mean((qc[inf_col] - qc[mea_col]) ** 2))) if len(qc) else np.nan
        rows.append(m)
    table = pd.DataFrame(rows)[
        ["Component", "Reference", "Pairing", "N", "N_qc", "Bias", "RMSE", "RMSE_qc", "MAE",
         "ubRMSE", "R", "R2", "slope", "intercept"]
    ]
    stats_path = os.path.join(OUTPUT_DIR, "LSCT_Validation_Evora_improved.csv")
    table.to_csv(stats_path, index=False)
    print(table.round(3).to_string(index=False))

    # ---------------------------------------------------------------- figures
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 120,
        }
    )
    fig = plt.figure(figsize=(15.5, 9.5))
    gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3)
    pairs_plot = [(PAIRS[0], "(a) sunlit soil"), (PAIRS[3], "(b) canopy")]

    for i, ((inf_col, mea_col, _label), title) in enumerate(pairs_plot):
        ax = fig.add_subplot(gs[0, i])
        h = hourly(window, inf_col, mea_col, thr=DIFF_THRESHOLD)
        ax.errorbar(h["Hour"] - 0.08, h["mea_mean"], yerr=h["mea_sd"].fillna(0), fmt="o-",
                    color="#1f77b4", mfc="white", mew=1.5, capsize=3, ms=7,
                    label=f"in-situ {mea_col}")
        ax.errorbar(h["Hour"] + 0.08, h["inf_mean"], yerr=h["inf_sd"].fillna(0), fmt="s-",
                    color="#d62728", mfc="white", mew=1.5, capsize=3, ms=6, label=inf_col)
        for _, r in h.iterrows():
            ax.annotate(f"{int(r['count'])}", (r["Hour"], r["mea_mean"]),
                        textcoords="offset points", xytext=(0, -15), ha="center",
                        fontsize=7, color="0.45")
        sub = window[np.abs(window[inf_col] - window[mea_col]) <= DIFF_THRESHOLD]
        bias = (sub[inf_col] - sub[mea_col]).mean()
        rmse = np.sqrt(((sub[inf_col] - sub[mea_col]) ** 2).mean())
        ax.set_title(f"{title}\nbias {bias:+.2f} K, RMSE {rmse:.2f} K, n={len(sub)}")
        ax.set_xticks(CACHED_HOURS)
        ax.set_xlabel("Hour (UTC)")
        ax.set_ylabel("Temperature (degC)")
        ax.grid(axis="y", ls="--", alpha=0.5)
        ax.legend(frameon=False, fontsize=9)

        ax2 = fig.add_subplot(gs[1, i])
        valid = window[window[inf_col].notna() & window[mea_col].notna()]
        keep = np.abs(valid[inf_col] - valid[mea_col]) <= DIFF_THRESHOLD
        hb = ax2.hexbin(valid.loc[keep, mea_col], valid.loc[keep, inf_col], gridsize=28,
                        cmap="viridis", mincnt=1)
        ax2.scatter(valid.loc[~keep, mea_col], valid.loc[~keep, inf_col], s=14,
                    facecolors="none", edgecolors="crimson", lw=0.8,
                    label=f"rejected n={int((~keep).sum())}")
        lo = min(valid[mea_col].min(), valid[inf_col].min()) - 2
        hi = max(valid[mea_col].max(), valid[inf_col].max()) + 2
        ax2.plot([lo, hi], [lo, hi], "r--", lw=1.2)
        ax2.set_xlim(lo, hi)
        ax2.set_ylim(lo, hi)
        r = stats.pearsonr(valid.loc[keep, mea_col], valid.loc[keep, inf_col])[0]
        ax2.set_title(f"{inf_col} vs {mea_col}: R = {r:.3f}, n = {int(keep.sum())}")
        ax2.set_xlabel("In-situ (degC)")
        ax2.set_ylabel("MSG LSCT (degC)")
        ax2.legend(frameon=False, fontsize=8, loc="upper left")
        fig.colorbar(hb, ax=ax2, shrink=0.85, label="counts")

    ax = fig.add_subplot(gs[:, 2])
    improved_soil = table[table["Component"] == "T_Sunlit_Soil"].iloc[0]
    legacy_sub = dec[np.abs(dec[LEGACY_PAIR[0]] - dec[LEGACY_PAIR[1]]) <= DIFF_THRESHOLD]
    legacy_m = metrics(legacy_sub[LEGACY_PAIR[1]], legacy_sub[LEGACY_PAIR[0]])
    comp = pd.DataFrame(
        [
            ["legacy: Dec only, vs Tgrass", legacy_m["N"], legacy_m["Bias"], legacy_m["RMSE"], legacy_m["R"]],
            ["improved: Aug-Dec, vs Ts", improved_soil["N"], improved_soil["Bias"],
             improved_soil["RMSE"], improved_soil["R"]],
        ],
        columns=["sunlit soil", "N", "Bias (K)", "RMSE (K)", "R"],
    )
    ax.axis("off")
    ax.set_title("legacy vs improved assessment", fontsize=12)
    tbl = ax.table(cellText=comp.round(3).values, colLabels=comp.columns,
                   loc="upper center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.0, 1.6)
    ax.text(0.0, 0.62,
            "Why the two differ:\n"
            "- the legacy row compares the inverted sunlit-soil\n"
            "  temperature with the in-situ GRASS temperature,\n"
            "  not with the soil surface temperature;\n"
            "- it keeps December only (17 samples per hour);\n"
            "- its |diff| <= 10 K rule removes the warm August\n"
            "  samples that carry most of the information.\n\n"
            "The improved rows use the physically matching\n"
            "reference (Ts for soil, Tcrown for canopy) over the\n"
            "full August-December record.",
            transform=ax.transAxes, fontsize=9, color="0.25", va="top")

    fig.suptitle(
        f"Evora LSCT component validation -- {TARGET_SITE}, August-December 2017, "
        f"hours {CACHED_HOURS[0]}-{CACHED_HOURS[-1]} UTC",
        fontsize=14,
    )
    fig_path = os.path.join(OUTPUT_DIR, "fig_evora_lsct_validation.png")
    fig.savefig(fig_path, dpi=200, bbox_inches="tight")
    print(f"\nwrote {stats_path}\nwrote {fig_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
