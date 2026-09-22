import os
import glob
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, linregress
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# ================= 路径配置 =================
FIELD_DATA_DIR = "/media/hero/rs/field/"
INVERSION_RESULT_FILE = "/media/hero/MSG/PRODUCTS/LSCT_Site_Results_2018-2025_all.csv"
OUTPUT_DIR = "/media/hero/MSG/PRODUCTS/VALIDATION/"

# 小时筛选
TARGET_HOURS = list(range(11, 17))
TARGET_YEARS = list(range(2018, 2026))
# 质控参数
TEMP_MIN = 0
TEMP_MAX = 60
TIME_WINDOW = 30
MIN_MONTH_SAMPLE = 3
MAX_TEMP_DIFF = 10.0  # 这次正常使用

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================= 工具函数 =================
def kelvin2celsius(series):
    mask = series > 200
    series.loc[mask] = series.loc[mask] - 273.15
    return series

def read_field_data(site_id):
    pattern = os.path.join(FIELD_DATA_DIR, f"ICOSETC_{site_id}_METEO_L2/ICOSETC_{site_id}_METEO_L2.csv")
    files = glob.glob(pattern)
    if not files:
        return None
    file_path = files[0]
    try:
        df = pd.read_csv(file_path)
        if 'TIMESTAMP_START' in df.columns:
            df['datetime'] = pd.to_datetime(df['TIMESTAMP_START'], format='%Y%m%d%H%M', errors='coerce')
        elif 'TIMESTAMP_END' in df.columns:
            df['datetime'] = pd.to_datetime(df['TIMESTAMP_END'], format='%Y%m%d%H%M', errors='coerce')
        else:
            return None
        df = df.dropna(subset=['datetime']).sort_values('datetime').reset_index(drop=True)
        keep = ['datetime', 'TA', 'TS_1']
        df = df[[c for c in keep if c in df.columns]].copy()
        for c in ['TA', 'TS_1']:
            if c in df.columns:
                df[c] = kelvin2celsius(df[c])
        return df
    except:
        return None

def batch_match(site_inv_df, field_df, site_name):
    site_inv_df["inv_datetime"] = pd.to_datetime(site_inv_df["DateTime"], format="%Y%m%d%H%M", errors="coerce")
    inv_valid = site_inv_df.dropna(subset=["inv_datetime"]).copy()
    inv_valid = inv_valid[inv_valid["inv_datetime"].dt.hour.isin(TARGET_HOURS)].copy()
    inv_valid = inv_valid[inv_valid["inv_datetime"].dt.year.isin(TARGET_YEARS)].copy()
    if inv_valid.empty or field_df is None:
        return None

    sat_list, field_list = [], []
    for _, row in inv_valid.iterrows():
        dt = abs(field_df["datetime"] - row["inv_datetime"])
        idx = dt.idxmin()
        if dt.loc[idx] > timedelta(minutes=TIME_WINDOW):
            continue
        sat_list.append(row)
        field_list.append(field_df.loc[idx])

    if not sat_list:
        return None

    sat_df = pd.DataFrame(sat_list).reset_index(drop=True)
    f_df = pd.DataFrame(field_list).reset_index(drop=True)
    match = pd.DataFrame({
        "site": site_name,
        "sat_datetime": sat_df["inv_datetime"],
        "T_Vegetation": sat_df["T_Vegetation"],
        "T_Soil": sat_df["T_Shaded_Soil"],
        "LST_Euro": sat_df["LST_Euro"],
        "TA": f_df["TA"],
        "TS1": f_df["TS_1"]
    })

    # 1. 温度物理范围过滤
    mask_temp = (
        match["T_Vegetation"].isna() | match["TA"].isna() |
        match["T_Soil"].isna() | match["TS1"].isna() |
        match["LST_Euro"].isna() |
        (match["T_Vegetation"] < TEMP_MIN) | (match["T_Vegetation"] > TEMP_MAX) |
        (match["T_Soil"] < TEMP_MIN) | (match["T_Soil"] > TEMP_MAX) |
        (match["LST_Euro"] < TEMP_MIN) | (match["LST_Euro"] > TEMP_MAX) |
        (match["TA"] < TEMP_MIN) | (match["TA"] > TEMP_MAX) |
        (match["TS1"] < TEMP_MIN) | (match["TS1"] > TEMP_MAX)
    )
    match = match[~mask_temp].copy()

    # 2. 温差 >10K 剔除（你要的 MAX_TEMP_DIFF）
    veg_diff = np.abs(match["T_Vegetation"] - match["TA"])
    soil_diff = np.abs(match["T_Soil"] - match["TS1"])
    mask_diff = (veg_diff > MAX_TEMP_DIFF) | (soil_diff > MAX_TEMP_DIFF)
    match = match[~mask_diff].copy()

    return match if not match.empty else None

def calc_monthly(match_df):
    df = match_df.copy()
    df["year"] = df["sat_datetime"].dt.year
    df["month"] = df["sat_datetime"].dt.month
    m_df = df.groupby(["site", "year", "month"]).agg({
        "T_Vegetation": "mean",
        "T_Soil": "mean",
        "LST_Euro": "mean",
        "TA": "mean",
        "TS1": "mean",
        "sat_datetime": "count"
    }).rename(columns={"sat_datetime": "n"}).reset_index()
    return m_df[m_df["n"] >= MIN_MONTH_SAMPLE].copy()

def rmse(obs, pred):
    m = ~(np.isnan(obs) | np.isnan(pred))
    if m.sum() < 3:
        return np.nan
    return np.sqrt(np.mean((pred[m] - obs[m])**2))

# ================= 主程序 =================
def main():
    full_inv = pd.read_csv(INVERSION_RESULT_FILE)
    sites = sorted(full_inv["Site"].unique())
    results = []

    for site in sites:
        print("处理站点:", site)
        inv = full_inv[full_inv["Site"] == site].copy()
        field = read_field_data(site)
        match = batch_match(inv, field, site)
        if match is None:
            continue

        monthly = calc_monthly(match)
        if monthly is None or monthly.empty:
            continue

        # 月度 4 组 RMSE
        rmse_veg_ta  = rmse(monthly["TA"],  monthly["T_Vegetation"])
        rmse_lst_ta  = rmse(monthly["TA"],  monthly["LST_Euro"])
        rmse_soil_ts = rmse(monthly["TS1"], monthly["T_Soil"])
        rmse_lst_ts  = rmse(monthly["TS1"], monthly["LST_Euro"])

        results.append({
            "Site": site,
            "RMSE_Month_TA_Vegetation": round(rmse_veg_ta, 3),
            "RMSE_Month_TA_LST_Euro":   round(rmse_lst_ta, 3),
            "RMSE_Month_TS_Soil":       round(rmse_soil_ts, 3),
            "RMSE_Month_TS_LST_Euro":   round(rmse_lst_ts, 3),
            "Valid_Months": len(monthly)
        })

    out_df = pd.DataFrame(results)
    out_path = os.path.join(OUTPUT_DIR, "monthly_rmse_4_groups.csv")
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print("\n==== 最终月度 RMSE 结果 ====")
    print(out_df.to_string(index=False))
    print(f"\n文件已保存：{out_path}")

if __name__ == "__main__":
    main()