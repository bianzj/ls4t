import os
import glob
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, linregress
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# ================= 全局配置 =================
FIELD_DATA_DIR = "/media/hero/rs/field/"
INVERSION_RESULT_FILE = "/media/hero/MSG/PRODUCTS/LSCT_Site_Results_2018-2025_all.csv"
OUTPUT_DIR = "/media/hero/MSG/PRODUCTS/VALIDATION/"

# ==========【重点：小时筛选配置，按需修改】==========
# TARGET_HOURS = [10]          # 仅10点
# TARGET_HOURS = [10, 11]      # 10点+11点
TARGET_HOURS = list(range(9, 17)) # 9,10,11,12,13,14,15,16 全部整点
# ===================================================

# 质控阈值
TEMP_MIN = 0
TEMP_MAX = 60
TIME_WINDOW = 30
AUTO_RUN = True
MIN_MONTH_SAMPLE = 3

# 统一固定阈值：温差绝对值 > 9 K 剔除
MAX_TEMP_DIFF = 10.0
TOP_K = 50  # 取最优前10站点

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================= 工具函数 =================
def kelvin2celsius(series):
    mask = series > 200
    series.loc[mask] = series.loc[mask] - 273.15
    return series

def read_field_data(site_id, field_dir=FIELD_DATA_DIR):
    pattern = os.path.join(field_dir, f"ICOSETC_{site_id}_METEO_L2/ICOSETC_{site_id}_METEO_L2.csv")
    files = glob.glob(pattern)
    if not files:
        print(f"  警告: 未找到站点 {site_id} 的现场数据")
        return None
    file_path = files[0]
    print(f"  读取现场数据: {os.path.basename(file_path)}")
    try:
        df = pd.read_csv(file_path)
        if 'TIMESTAMP_START' in df.columns:
            df['datetime'] = pd.to_datetime(df['TIMESTAMP_START'], format='%Y%m%d%H%M', errors='coerce')
        elif 'TIMESTAMP_END' in df.columns:
            df['datetime'] = pd.to_datetime(df['TIMESTAMP_END'], format='%Y%m%d%H%M', errors='coerce')
        else:
            print(f"  警告: 未找到时间戳列")
            return None
        df = df.dropna(subset=['datetime']).sort_values('datetime').reset_index(drop=True)
        keep_cols = ['datetime']
        obs_cols = ['TA', 'TS_1', 'TS_2']
        for col in obs_cols:
            if col in df.columns:
                keep_cols.append(col)
        df = df[keep_cols].copy()
        for col in obs_cols:
            if col in df.columns and not df[col].isna().all():
                df[col] = kelvin2celsius(df[col])
        print(f"  成功读取 {len(df)} 条地面观测记录")
        return df
    except Exception as e:
        print(f"  读取站点{site_id}失败: {str(e)}")
        return None

def batch_match_inversion_field(site_inv_df, field_df, site_name, time_window=30):
    if site_inv_df is None or len(site_inv_df) == 0 or field_df is None or len(field_df) == 0:
        return None, {}
    filter_stats = {
        "total_raw": len(site_inv_df),
        "hour_filtered": 0,    # 新增：小时筛选剔除数量
        "time_filtered": 0,
        "temp_outlier_filtered": 0,
        "diff_over_10K_filtered": 0,
        "kept": 0
    }
    time_thresh = timedelta(minutes=time_window)
    site_inv_df["inv_datetime"] = pd.to_datetime(site_inv_df["DateTime"], format="%Y%m%d%H%M", errors="coerce")
    inv_valid = site_inv_df.dropna(subset=["inv_datetime"]).copy()

    # ========== 新增：整点时刻筛选 ==========
    hour_mask = inv_valid["inv_datetime"].dt.hour.isin(TARGET_HOURS)
    filter_stats["hour_filtered"] = (~hour_mask).sum()
    inv_valid = inv_valid[hour_mask].copy()
    if len(inv_valid) == 0:
        print(f"  警告：站点{site_name}无{TARGET_HOURS}时刻卫星数据")
        return None, filter_stats
    # =======================================

    sat_list = []
    field_list = []
    time_diff_list = []
    for _, sat_row in inv_valid.iterrows():
        sat_t = sat_row["inv_datetime"]
        dt_abs = abs(field_df["datetime"] - sat_t)
        min_idx = dt_abs.idxmin()
        min_dt = dt_abs.loc[min_idx]
        if min_dt > time_thresh:
            filter_stats["time_filtered"] += 1
            continue
        field_row = field_df.loc[min_idx]
        sat_list.append(sat_row)
        field_list.append(field_row)
        time_diff_list.append(min_dt.total_seconds() / 60)
    if len(sat_list) == 0:
        return None, filter_stats

    sat_df = pd.DataFrame(sat_list).reset_index(drop=True)
    field_match_df = pd.DataFrame(field_list).reset_index(drop=True)
    match_df = pd.DataFrame({
        "site": site_name,
        "sat_datetime": sat_df["inv_datetime"],
        "field_datetime": field_match_df["datetime"],
        "time_diff_min": np.array(time_diff_list),
        "T_Vegetation": sat_df["T_Vegetation"],
        "T_Soil": sat_df["T_Shaded_Soil"],
        "TA_field": field_match_df["TA"],
        "TS1_field": field_match_df["TS_1"]
    })

    # 1. 温度物理范围过滤
    temp_mask = (
        match_df["T_Vegetation"].isna() | match_df["TA_field"].isna() |
        match_df["T_Soil"].isna() | match_df["TS1_field"].isna() |
        (match_df["T_Vegetation"] < TEMP_MIN) | (match_df["T_Vegetation"] > TEMP_MAX) |
        (match_df["TA_field"] < TEMP_MIN) | (match_df["TA_field"] > TEMP_MAX) |
        (match_df["T_Soil"] < TEMP_MIN) | (match_df["T_Soil"] > TEMP_MAX) |
        (match_df["TS1_field"] < TEMP_MIN) | (match_df["TS1_field"] > TEMP_MAX)
    )
    filter_stats["temp_outlier_filtered"] = temp_mask.sum()
    match_temp_ok = match_df[~temp_mask].copy()

    # 2. 统一固定阈值：温差 > 9 K 直接剔除
    veg_diff = np.abs(match_temp_ok["T_Vegetation"] - match_temp_ok["TA_field"])
    soil_diff = np.abs(match_temp_ok["T_Soil"] - match_temp_ok["TS1_field"])
    diff_mask = (veg_diff > MAX_TEMP_DIFF) | (soil_diff > MAX_TEMP_DIFF)
    filter_stats["diff_over_10K_filtered"] = diff_mask.sum()

    final_match = match_temp_ok[~diff_mask].copy()
    filter_stats["kept"] = len(final_match)

    print(f"\n  过滤统计 ({site_name} | 筛选小时:{TARGET_HOURS}):")
    print(f"    原始卫星点: {filter_stats['total_raw']}")
    print(f"    非目标整点剔除: {filter_stats['hour_filtered']}")
    print(f"    时间差>{TIME_WINDOW}min 剔除: {filter_stats['time_filtered']}")
    print(f"    温度异常/越界 剔除: {filter_stats['temp_outlier_filtered']}")
    print(f"    温差>{MAX_TEMP_DIFF}K 剔除: {filter_stats['diff_over_10K_filtered']}")
    print(f"    最终有效瞬时点: {filter_stats['kept']}")

    if len(final_match) > 0:
        final_match["veg_temp_diff"] = veg_diff[~diff_mask]
        final_match["soil_temp_diff"] = soil_diff[~diff_mask]
    return final_match, filter_stats

def calculate_metrics(obs, pred):
    mask = ~(np.isnan(obs) | np.isnan(pred))
    obs_valid = obs[mask]
    pred_valid = pred[mask]
    n = len(obs_valid)
    if n < 3:
        return None
    bias = np.mean(pred_valid - obs_valid)
    rmse = np.sqrt(np.mean((pred_valid - obs_valid) ** 2))
    r, p_value = pearsonr(obs_valid, pred_valid)
    r2 = r ** 2
    slope, intercept, _, _, _ = linregress(obs_valid, pred_valid)
    return {
        "n_sample": n,
        "RMSE": rmse,
        "Bias": bias,
        "R": r,
        "R2": r2,
    }

def calc_monthly_mean(valid_match_df):
    df = valid_match_df.copy()
    df["year"] = df["sat_datetime"].dt.year
    df["month"] = df["sat_datetime"].dt.month
    df["year_month"] = df["sat_datetime"].dt.to_period("M")

    agg_dict = {
        "T_Vegetation": "mean",
        "T_Soil": "mean",
        "TA_field": "mean",
        "TS1_field": "mean",
        "sat_datetime": "count"
    }
    monthly_df = df.groupby(["site", "year", "month", "year_month"]).agg(agg_dict).reset_index()
    monthly_df.rename(columns={"sat_datetime": "month_sample_count"}, inplace=True)
    monthly_valid = monthly_df[monthly_df["month_sample_count"] >= MIN_MONTH_SAMPLE].copy()
    return monthly_valid

def process_single_site(site, full_inversion_df):
    print(f"\n{'=' * 60}")
    print(f"处理站点: {site}")
    print(f"{'=' * 60}")
    site_inv = full_inversion_df[full_inversion_df["Site"] == site].copy()
    if len(site_inv) == 0:
        print(f"  警告: {site} 无卫星反演数据")
        return None
    field_df = read_field_data(site)
    if field_df is None:
        print(f"  错误: 无地面数据")
        return None

    valid_timestep_df, filter_stat = batch_match_inversion_field(site_inv, field_df, site, TIME_WINDOW)
    if valid_timestep_df is None or len(valid_timestep_df) == 0:
        print(f"  ✗ 无有效瞬时点")
        return None

    veg_timestep_metric = calculate_metrics(valid_timestep_df["TA_field"], valid_timestep_df["T_Vegetation"])
    soil_timestep_metric = calculate_metrics(valid_timestep_df["TS1_field"], valid_timestep_df["T_Soil"])

    site_monthly_df = calc_monthly_mean(valid_timestep_df)

    # 本站月度 RMSE
    veg_month_metric = calculate_metrics(site_monthly_df["TA_field"], site_monthly_df["T_Vegetation"])
    soil_month_metric = calculate_metrics(site_monthly_df["TS1_field"], site_monthly_df["T_Soil"])

    site_info = {
        "site": site,
        "n_timestep": len(valid_timestep_df),
        "n_month": len(site_monthly_df),
        "veg_timestep": veg_timestep_metric,
        "soil_timestep": soil_timestep_metric,
        "veg_month": veg_month_metric,
        "soil_month": soil_month_metric,
    }
    return site_info

# ================= 主程序 =================
def main():
    print("=" * 70)
    print(f"当前筛选整点小时：{TARGET_HOURS}")
    print("简化剔除规则：温差 > 9K 剔除 + 输出RMSE最优前10站点")
    print("=" * 70)
    print(f"过滤规则：目标整点筛选 + 温度异常值 + 时间差>{TIME_WINDOW}min + |ΔT|>{MAX_TEMP_DIFF}K 剔除")

    if not os.path.exists(INVERSION_RESULT_FILE):
        print(f"文件不存在：{INVERSION_RESULT_FILE}")
        return
    full_inv_df = pd.read_csv(INVERSION_RESULT_FILE)
    all_sites = sorted(full_inv_df["Site"].unique())

    site_results = []
    for site in all_sites:
        info = process_single_site(site, full_inv_df)
        if info:
            site_results.append(info)
        print("-" * 60)

    # 组装全站点结果表
    rows = []
    for r in site_results:
        s = r["site"]
        vt = r["veg_timestep"]
        st = r["soil_timestep"]
        vm = r["veg_month"]
        sm = r["soil_month"]

        rows.append({
            "Site": s,
            "Veg_RMSE_timestep": round(vt["RMSE"],3) if vt else np.nan,
            "Veg_RMSE_monthly": round(vm["RMSE"],3) if vm else np.nan,
            "Soil_RMSE_timestep": round(st["RMSE"],3) if st else np.nan,
            "Soil_RMSE_monthly": round(sm["RMSE"],3) if sm else np.nan,
            "Valid_timesteps": r["n_timestep"],
            "Valid_months": r["n_month"]
        })

    df_all = pd.DataFrame(rows)
    full_csv = os.path.join(OUTPUT_DIR, "site_validation_rmse_timestep_monthly.csv")
    df_all.to_csv(full_csv, index=False, encoding="utf-8-sig")

    # ===== 筛选最优前10站点（RMSE越小越优）=====
    # 1. 植被瞬时最优前10
    df_veg_ts = df_all.dropna(subset=["Veg_RMSE_timestep"]).sort_values("Veg_RMSE_timestep").head(TOP_K)
    # 2. 土壤瞬时最优前10
    df_soil_ts = df_all.dropna(subset=["Soil_RMSE_timestep"]).sort_values("Soil_RMSE_timestep").head(TOP_K)
    # 3. 植被月度最优前10
    df_veg_mo = df_all.dropna(subset=["Veg_RMSE_monthly"]).sort_values("Veg_RMSE_monthly").head(TOP_K)
    # 4. 土壤月度最优前10
    df_soil_mo = df_all.dropna(subset=["Soil_RMSE_monthly"]).sort_values("Soil_RMSE_monthly").head(TOP_K)

    # 保存TOP10文件
    df_veg_ts.to_csv(os.path.join(OUTPUT_DIR, "top10_veg_timestep_best.csv"), index=False, encoding="utf-8-sig")
    df_soil_ts.to_csv(os.path.join(OUTPUT_DIR, "top10_soil_timestep_best.csv"), index=False, encoding="utf-8-sig")
    df_veg_mo.to_csv(os.path.join(OUTPUT_DIR, "top10_veg_monthly_best.csv"), index=False, encoding="utf-8-sig")
    df_soil_mo.to_csv(os.path.join(OUTPUT_DIR, "top10_soil_monthly_best.csv"), index=False, encoding="utf-8-sig")

    # 控制台打印结果
    print("\n" + "="*80)
    print(f"【植被瞬时RMSE 最优前{TOP_K}站点】")
    print(df_veg_ts.to_string(index=False))

    print("\n" + "="*80)
    print(f"【土壤瞬时RMSE 最优前{TOP_K}站点】")
    print(df_soil_ts.to_string(index=False))

    print("\n" + "="*80)
    print(f"【植被月度RMSE 最优前{TOP_K}站点】")
    print(df_veg_mo.to_string(index=False))

    print("\n" + "="*80)
    print(f"【土壤月度RMSE 最优前{TOP_K}站点】")
    print(df_soil_mo.to_string(index=False))

    print("\n✅ 全部结果保存完成：")
    print("1. site_validation_rmse_timestep_monthly.csv  全站点结果")
    print("2. top10_veg_timestep_best.csv               植被瞬时最优10站")
    print("3. top10_soil_timestep_best.csv              土壤瞬时最优10站")
    print("4. top10_veg_monthly_best.csv                植被月度最优10站")
    print("5. top10_soil_monthly_best.csv               土壤月度最优10站")

if __name__ == "__main__":
    main()