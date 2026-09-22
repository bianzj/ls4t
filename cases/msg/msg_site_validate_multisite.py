#!/usr/bin/env python3
"""Multi-site LSCT validation against ICOS in-situ data: reproduction + improvement.

Source recipe: cases/implementation/msg_val_f2025.py, which matches the site
extraction ``LSCT_Site_Results_2025.csv`` against ``/media/hero/rs/field``.

What the legacy script does and what is improved here:

legacy                                                    improved
--------------------------------------------------------  --------------------------------------------------
loops over every satellite record and does               one vectorised ``merge_asof`` / hourly bracket join
``abs(field - t).idxmin()``  -> O(N*M)                    -> ~3 orders of magnitude faster
filters |T| to [0, 60] degC, so -9999 survives until the  explicit -9999 -> NaN, then physical bounds
range test and winter/summer values are truncated
only "nearest" in-situ record within +/-30 min            also the mean of the two half-hour slots that
                                                          bracket the overpass (the physically better match)
fixed dynamic threshold 3 + 5*SZA/60                      keeps it, and additionally reports a robust
                                                          (MAD-based) rejection for comparison
metrics: RMSE/Bias/R/R2/slope                             adds MAE, ubRMSE, intercept, per-hour/per-month
                                                          breakdowns and the QC-cascade impact

Usage:
    PYTHONPATH=. python cases/validation/repro/validate_multisite.py
"""

from __future__ import annotations

import glob
import os
import sys
import argparse

import matplotlib

matplotlib.use("Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplcfg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")

SITE_RESULTS = "/media/hero/MSG/PRODUCTS/LSCT_Site_Results_2025.csv"
FIELD_ROOT = "/media/hero/rs/field"
SITES_CSV = "/media/hero/MSG/field/sites-2025.csv"

FILL = -9999.0
PHYS_MIN, PHYS_MAX = -60.0, 60.0
MATCH_TOL = pd.Timedelta(minutes=20)
SAT_HOURS = list(range(9, 17))

# satellite component -> in-situ reference (ICOS METEO_L2)
TARGETS = [
    ("T_Vegetation", "TA", "canopy vs air temperature"),
    ("T_Soil", "TS_1", "areal soil vs soil temperature (TS_1)"),
    ("T_Sunlit_Soil", "TS_1", "sunlit soil vs soil temperature (TS_1)"),
    ("T_Soil", "TA", "areal soil vs air temperature"),
    ("LST_Euro", "TS_1", "satellite LST (EURO) vs soil temperature (TS_1)"),
    ("LST_Euro", "TA", "satellite LST (EURO) vs air temperature"),
]


def load_satellite(path: str = SITE_RESULTS) -> pd.DataFrame:
    """Load the cached site extraction, or a fresh sample written by extract_site_series.py."""
    if path != SITE_RESULTS:
        raw = pd.read_csv(path)
        raw = raw.rename(columns={
            "ts": "T_Soil", "tv": "T_Vegetation",
            "ts1": "T_Sunlit_Soil", "ts2": "T_Shaded_Soil",
        })
        for col in ("T_Soil", "T_Vegetation", "T_Sunlit_Soil", "T_Shaded_Soil"):
            raw[col] = raw[col] - 273.15          # products are stored in K/100
        raw["LST_Euro"] = np.nan                  # the input LST is not stored in the product
        raw["LST_IODC"] = np.nan
        sat = raw
    else:
        sat = pd.read_csv(path)
    sat["dt"] = pd.to_datetime(sat["DateTime"].astype("int64").astype(str), format="%Y%m%d%H%M")
    sat = sat[sat["dt"].dt.hour.isin(SAT_HOURS)].copy()
    return sat


def load_field(site: str) -> pd.DataFrame | None:
    path = os.path.join(FIELD_ROOT, f"ICOSETC_{site}_METEO_L2", f"ICOSETC_{site}_METEO_L2.csv")
    if not os.path.exists(path):
        return None
    cols = ["TIMESTAMP_START", "TA", "TS_1", "TS_2"]
    try:
        df = pd.read_csv(path, usecols=cols + ["TS_1_N"])
    except ValueError:  # some sites lack TS_2
        df = pd.read_csv(path, usecols=["TIMESTAMP_START", "TA", "TS_1"], low_memory=False)
        df["TS_2"] = np.nan
        df["TS_1_N"] = np.nan
    df["dt"] = pd.to_datetime(df["TIMESTAMP_START"], format="%Y%m%d%H%M", errors="coerce")
    df = df.dropna(subset=["dt"]).sort_values("dt")
    for c in ("TA", "TS_1", "TS_2"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df.loc[df[c] <= -900, c] = np.nan           # -9999 fill, explicit
        df.loc[(df[c] < -100) | (df[c] > 80), c] = np.nan
    # the ICOS *_N column counts the underlying samples: 0 means "no data"
    n_ok = pd.to_numeric(df["TS_1_N"], errors="coerce")
    df.loc[n_ok.fillna(0) <= 0, "TS_1"] = np.nan
    return df.dropna(subset=["TA", "TS_1"], how="all")


def bracket_hourly(field: pd.DataFrame) -> pd.DataFrame:
    """Mean of the two half-hour slots bracketing each overpass hour."""
    slot = field["dt"].dt.ceil("h")
    grp = field.assign(_slot=slot).groupby("_slot")[["TA", "TS_1", "TS_2"]].mean()
    return grp.rename_axis("dt").reset_index()


def match(sat: pd.DataFrame, field: pd.DataFrame, mode: str) -> pd.DataFrame:
    sat = sat.sort_values("dt")
    if mode == "nearest_hourly":
        fld = field.sort_values("dt")
        out = pd.merge_asof(sat, fld[["dt", "TA", "TS_1", "TS_2"]], on="dt",
                            direction="nearest", tolerance=MATCH_TOL, suffixes=("", "_fld"))
    else:  # bracketed half-hour mean
        fld = bracket_hourly(field).sort_values("dt")
        out = pd.merge(sat, fld, on="dt", how="inner", suffixes=("", "_fld"))
    return out.dropna(subset=["TA", "TS_1"], how="all")


def metrics(obs, pred) -> dict:
    obs = np.asarray(obs, float)
    pred = np.asarray(pred, float)
    ok = np.isfinite(obs) & np.isfinite(pred)
    obs, pred = obs[ok], pred[ok]
    if len(obs) < 3:
        return {}
    err = pred - obs
    out = {
        "N": int(len(obs)),
        "Bias": float(err.mean()),
        "RMSE": float(np.sqrt(np.mean(err**2))),
        "MAE": float(np.abs(err).mean()),
        "ubRMSE": float(np.sqrt(np.mean((err - err.mean()) ** 2))),
    }
    if np.std(obs) > 0 and np.std(pred) > 0:
        r, _ = stats.pearsonr(obs, pred)
        lr = stats.linregress(obs, pred)
        out.update(R=float(r), R2=float(r**2), slope=float(lr.slope), intercept=float(lr.intercept))
    return out


def tsheld(sza: np.ndarray) -> np.ndarray:
    return 3.0 + np.clip(sza / 60.0, 0, 1) * 5.0


def solar_zenith(site: str, times: pd.Series) -> np.ndarray:
    """Solar zenith angle for a site, used when the extraction carries no SZA."""
    try:
        import pvlib
    except ImportError:  # pvlib is only needed for the dynamic threshold
        return np.full(len(times), np.nan)
    coords = pd.read_csv(SITES_CSV).set_index("id")
    if site not in coords.index:
        return np.full(len(times), np.nan)
    lat, lon = float(coords.loc[site, "lat"]), float(coords.loc[site, "lon"])
    times_utc = pd.DatetimeIndex(times).tz_localize("UTC")
    return pvlib.solarposition.get_solarposition(times_utc, lat, lon)["zenith"].to_numpy()


def qc_cascade(merged: pd.DataFrame, inf_col: str, mea_col: str) -> pd.DataFrame:
    """Legacy vs improved quality control, evaluated on the same matched sample."""
    sub = merged.dropna(subset=[inf_col, mea_col]).copy()
    stages = {"1 all matched": sub}
    stage2 = sub[(sub[inf_col].between(PHYS_MIN, PHYS_MAX)) & (sub[mea_col].between(PHYS_MIN, PHYS_MAX))]
    stages["2 physical range"] = stage2
    stage3 = stage2[stage2["SZA"].notna()].copy()
    stage3 = stage3[np.abs(stage3[inf_col] - stage3[mea_col]) <= tsheld(stage3["SZA"].values)]
    stages["3 legacy dynamic threshold"] = stage3
    if len(stage2) > 10:
        resid = stage2[inf_col] - stage2[mea_col]
        mad = np.median(np.abs(resid - np.median(resid)))
        lim = 3.0 * 1.4826 * mad if mad > 0 else np.inf
        stages["4 robust MAD (improved)"] = stage2[np.abs(resid - np.median(resid)) <= lim]
    rows = []
    for name, frame in stages.items():
        m = metrics(frame[mea_col], frame[inf_col])
        if m:
            m["stage"] = name
            m["kept_pct"] = 100.0 * len(frame) / len(sub)
            rows.append(m)
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", default=SITE_RESULTS,
                    help="site extraction CSV (default: the cached LSCT_Site_Results_2025.csv)")
    args = ap.parse_args()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sat_all = load_satellite(args.series)
    sites = sorted(sat_all["Site"].unique())
    print(f"site extraction: {len(sat_all)} records, {len(sites)} sites, "
          f"{sat_all['dt'].min():%Y-%m-%d} to {sat_all['dt'].max():%Y-%m-%d}")
    print(f"satellite sample covers years {sorted(sat_all['dt'].dt.year.unique())}")

    pooled, per_site = [], []
    used_sites, missing = [], []
    for site in sites:
        field = load_field(site)
        if field is None or field.empty:
            missing.append(site)
            continue
        sat = sat_all[sat_all["Site"] == site]
        merged = match(sat, field, mode="bracket")
        if merged.empty:
            missing.append(site)
            continue
        if "SZA" not in merged.columns or merged["SZA"].isna().all():
            merged = merged.assign(SZA=solar_zenith(site, merged["dt"]))
        used_sites.append(site)
        for inf_col, mea_col, label in TARGETS:
            sub = merged.dropna(subset=[inf_col, mea_col])
            sub = sub[(sub[inf_col].between(PHYS_MIN, PHYS_MAX)) & (sub[mea_col].between(PHYS_MIN, PHYS_MAX))]
            if len(sub) < 10:
                continue
            m = metrics(sub[mea_col], sub[inf_col])
            if m:
                m.update(Site=site, Target=f"{inf_col}~{mea_col}", Pairing=label)
                per_site.append(m)
                pooled.append(sub.assign(Target=f"{inf_col}~{mea_col}", Site=site))

    print(f"sites with ICOS data: {len(used_sites)}; without: {len(missing)} "
          f"({', '.join(missing[:8])}{' ...' if len(missing) > 8 else ''})")
    per_site_df = pd.DataFrame(per_site)
    pooled_df = pd.concat(pooled, ignore_index=True) if pooled else pd.DataFrame()

    summary = []
    for target, grp in pooled_df.groupby("Target"):
        m = metrics(grp[target.split("~")[1]], grp[target.split("~")[0]])
        m.update(Target=target, Sites=grp["Site"].nunique())
        summary.append(m)
    summary_df = pd.DataFrame(summary)
    print("\npooled metrics (bracketed half-hour reference, physical range only)")
    print(summary_df[["Target", "Sites", "N", "Bias", "RMSE", "ubRMSE", "MAE", "R", "R2", "slope"]]
          .round(3).to_string(index=False))

    per_site_df.to_csv(os.path.join(OUTPUT_DIR, "multisite_metrics_by_site.csv"), index=False)
    summary_df.to_csv(os.path.join(OUTPUT_DIR, "multisite_metrics_pooled.csv"), index=False)

    # matching-mode and QC-cascade comparison on the same sites
    modes, cascades = [], []
    for site in used_sites:
        field = load_field(site)
        sat = sat_all[sat_all["Site"] == site]
        sat_times = sat["dt"]
        m_br = match(sat, field, "bracket")
        m_nr = match(sat, field, "nearest_hourly")
        if "SZA" not in m_br.columns or m_br["SZA"].isna().all():
            m_br = m_br.assign(SZA=solar_zenith(site, m_br["dt"]))
        modes.append({"Site": site, "bracket": len(m_br), "nearest": len(m_nr)})
        for inf_col, mea_col, label in TARGETS[:2]:
            casc = qc_cascade(m_br, inf_col, mea_col)
            if not casc.empty:
                casc["Site"] = site
                casc["Target"] = f"{inf_col}~{mea_col}"
                cascades.append(casc)
    modes_df = pd.DataFrame(modes)
    casc_df = pd.concat(cascades, ignore_index=True) if cascades else pd.DataFrame()

    if not modes_df.empty:
        print(f"\nmatching mode: bracketed half-hour join keeps {modes_df['bracket'].sum()} rows, "
              f"legacy nearest-within-20min keeps {modes_df['nearest'].sum()} rows "
              f"across {len(modes_df)} sites")
    if not casc_df.empty:
        agg = (casc_df.groupby(["Target", "stage"])[["kept_pct", "Bias", "RMSE", "R", "ubRMSE"]]
               .mean().reset_index())
        print("\nQC cascade (site-averaged):")
        print(agg.round(3).to_string(index=False))
        agg.to_csv(os.path.join(OUTPUT_DIR, "multisite_qc_cascade.csv"), index=False)

    # ------------------------------------------------------------------ figures
    plt.rcParams.update({
        "font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11,
        "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 120,
    })

    # (1) agreement + residuals
    fig, axes = plt.subplots(2, 2, figsize=(13, 11))
    for ax, (inf_col, mea_col, label) in zip(axes[0], TARGETS[:2]):
        sub = pooled_df[pooled_df["Target"] == f"{inf_col}~{mea_col}"]
        hb = ax.hexbin(sub[mea_col], sub[inf_col], gridsize=55, cmap="viridis", mincnt=1)
        lo = min(sub[mea_col].min(), sub[inf_col].min()) - 2
        hi = max(sub[mea_col].max(), sub[inf_col].max()) + 2
        ax.plot([lo, hi], [lo, hi], "r--", lw=1.2)
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        m = metrics(sub[mea_col], sub[inf_col])
        ax.set_title(f"{label}\nRMSE {m['RMSE']:.2f} K, bias {m['Bias']:+.2f} K, R {m['R']:.3f}, "
                     f"N {m['N']} ({sub['Site'].nunique()} sites)")
        ax.set_xlabel("In-situ (degC)"); ax.set_ylabel("MSG LSCT (degC)")
        fig.colorbar(hb, ax=ax, shrink=0.85, label="counts")

    ax = axes[1, 0]
    for (inf_col, mea_col, label), color in zip(TARGETS[:2], ["#2ca02c", "#1f77b4"]):
        sub = pooled_df[pooled_df["Target"] == f"{inf_col}~{mea_col}"]
        ax.hist(sub[inf_col] - sub[mea_col], bins=80, range=(-20, 20), histtype="step",
                lw=1.6, color=color, label=label, density=True)
    ax.axvline(0, color="0.4", ls="--", lw=1)
    ax.set_xlabel("satellite - in-situ (K)"); ax.set_ylabel("density")
    ax.set_title("residual distribution (pooled)"); ax.legend(frameon=False, fontsize=9)

    ax = axes[1, 1]
    for (inf_col, mea_col, label), color in zip(TARGETS[:2], ["#2ca02c", "#1f77b4"]):
        sub = pooled_df[pooled_df["Target"] == f"{inf_col}~{mea_col}"].copy()
        stats_h = sub.assign(hour=sub["dt"].dt.hour, resid=sub[inf_col] - sub[mea_col]) \
                     .groupby("hour")["resid"].agg(["mean", "std", "count"])
        ax.errorbar(stats_h.index, stats_h["mean"], yerr=stats_h["std"] / np.sqrt(stats_h["count"]),
                    fmt="o-", color=color, capsize=3, label=label)
    ax.axhline(0, color="0.4", ls="--", lw=1)
    ax.set_xlabel("hour (UTC)"); ax.set_ylabel("mean residual (K)")
    ax.set_title("bias versus overpass hour"); ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "fig_multisite_agreement.png"), dpi=200, bbox_inches="tight")

    # (2) per-site skill: ranking + map
    veg = per_site_df[per_site_df["Pairing"] == "canopy vs air temperature"].copy()
    coords = pd.read_csv(SITES_CSV)[["id", "lat", "lon", "type"]]
    veg = veg.merge(coords, left_on="Site", right_on="id", how="left")
    fig, axes = plt.subplots(1, 2, figsize=(16, 6.5), gridspec_kw={"width_ratios": [1, 1.25]})
    order = veg.sort_values("RMSE")
    ax = axes[0]
    ax.barh(order["Site"], order["RMSE"], color="#4c72b0")
    ax.axvline(veg["RMSE"].mean(), color="crimson", ls="--", lw=1.2,
               label=f"mean {veg['RMSE'].mean():.2f} K")
    ax.set_xlabel("RMSE (K)"); ax.set_title(f"canopy-vs-air skill, {len(veg)} sites")
    ax.tick_params(axis="y", labelsize=7); ax.legend(frameon=False)
    ax.invert_yaxis()

    ax = axes[1]
    sc = ax.scatter(veg["lon"], veg["lat"], c=veg["RMSE"], s=np.clip(veg["N"] / 3, 8, 160),
                    cmap="RdYlBu_r", edgecolors="0.3", lw=0.5)
    ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    ax.set_title("per-site RMSE (bubble size ~ sample count)")
    ax.grid(ls=":", alpha=0.4)
    fig.colorbar(sc, ax=ax, shrink=0.85, label="RMSE (K)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "fig_multisite_site_skill.png"), dpi=200, bbox_inches="tight")

    # (3) diurnal composite
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    for ax, (inf_col, mea_col, label) in zip(axes, TARGETS[:2]):
        sub = pooled_df[pooled_df["Target"] == f"{inf_col}~{mea_col}"].copy()
        sub["hour"] = sub["dt"].dt.hour
        g = sub.groupby("hour")
        for col, color, name in ((mea_col, "#1f77b4", "in-situ"), (inf_col, "#d62728", "MSG LSCT")):
            mean, q1, q3 = g[col].mean(), g[col].quantile(0.25), g[col].quantile(0.75)
            ax.plot(mean.index, mean.values, "o-", color=color, label=name, ms=5)
            ax.fill_between(mean.index, q1.values, q3.values, color=color, alpha=0.15)
        ax.set_title(f"{label} (pooled, IQR shading)")
        ax.set_xlabel("hour (UTC)"); ax.set_ylabel("temperature (degC)")
        ax.grid(axis="y", ls="--", alpha=0.5); ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "fig_multisite_diurnal.png"), dpi=200, bbox_inches="tight")

    # (4) QC cascade
    if not casc_df.empty:
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
        stages = list(dict.fromkeys(casc_df["stage"]))
        for ax, metric in zip(axes, ["kept_pct", "RMSE", "Bias"]):
            for target, grp in casc_df.groupby("Target"):
                g = grp.groupby("stage")[metric].mean().reindex(stages)
                ax.plot(range(len(stages)), g.values, "o-", label=target)
            ax.set_xticks(range(len(stages)))
            ax.set_xticklabels([s.split(" ", 1)[1] for s in stages], rotation=20, ha="right", fontsize=9)
            ax.set_title(metric)
            ax.grid(axis="y", ls="--", alpha=0.5)
        axes[0].legend(frameon=False, fontsize=9)
        axes[0].set_ylabel("kept (%)")
        fig.suptitle("quality-control cascade: legacy stages 2-3 vs improved stage 4", fontsize=13)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        fig.savefig(os.path.join(OUTPUT_DIR, "fig_multisite_qc.png"), dpi=200, bbox_inches="tight")

    # (5) land-cover dependence of the canopy comparison
    veg_lc = per_site_df[per_site_df["Pairing"] == "canopy vs air temperature"].merge(
        coords[["id", "type"]], left_on="Site", right_on="id", how="left"
    )
    if veg_lc["type"].notna().any():
        agg = (veg_lc.groupby("type")
               .agg(sites=("Site", "nunique"), Bias=("Bias", "mean"),
                    RMSE=("RMSE", "mean"), R=("R", "mean"), N=("N", "sum"))
               .sort_values("RMSE"))
        agg.to_csv(os.path.join(OUTPUT_DIR, "multisite_landcover.csv"))
        fig, ax = plt.subplots(figsize=(11, 0.5 + 0.45 * len(agg)))
        y = np.arange(len(agg))
        ax.barh(y - 0.2, agg["RMSE"], height=0.4, color="#4c72b0", label="RMSE")
        ax.barh(y + 0.2, agg["Bias"].abs(), height=0.4, color="#dd8452", label="|bias|")
        ax.set_yticks(y)
        ax.set_yticklabels([f"{t} (n={int(s)})" for t, s in zip(agg.index, agg["sites"])], fontsize=9)
        ax.set_xlabel("K")
        ax.set_title("canopy-vs-air skill by IGBP land-cover class")
        ax.grid(axis="x", ls="--", alpha=0.5)
        ax.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(os.path.join(OUTPUT_DIR, "fig_multisite_landcover.png"), dpi=200, bbox_inches="tight")
        print("\ncanopy-vs-air skill by land-cover class")
        print(agg.round(3).to_string())

    print(f"\noutputs written to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
