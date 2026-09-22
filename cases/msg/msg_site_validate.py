import os
from datetime import datetime, timedelta
from scipy.stats import pearsonr, linregress
import glob
import numpy as np
import pandas as pd
import warnings
from numpy import abs, round

warnings.filterwarnings('ignore')

# ================= 全局配置 =================
FIELD_DATA_DIR = "/media/hero/rs/field/"
INVERSION_RESULT_FILE = "/media/hero/MSG/PRODUCTS/LSCT_Site_Results_2025.csv"
OUTPUT_DIR = "/media/hero/MSG/PRODUCTS/VALIDATION/"

# 质控阈值 (已移除SZA_MIN/SZA_MAX)
TEMP_MIN = 0
TEMP_MAX = 60
TIME_WINDOW = 30
AUTO_RUN = True
TOP_N_BEST = 20  # 选取最优20个站点
SORT_METRIC = "T_Soil"  # 可选 "T_Vegetation" / "T_Soil"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================= 工具函数 =================
def calculate_tsheld(sza_arr):
    sza_norm = np.clip(sza_arr / 60.0, 0, 1)
    tsheld = 3.0 + sza_norm * 5.0
    return tsheld

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
        "time_filtered": 0,
        "temp_filtered": 0,
        "tsheld_filtered": 0,
        "kept": 0
    }
    time_thresh = timedelta(minutes=time_window)
    site_inv_df["inv_datetime"] = pd.to_datetime(site_inv_df["DateTime"], format="%Y%m%d%H%M", errors="coerce")
    inv_valid = site_inv_df.dropna(subset=["inv_datetime"]).copy()
    filter_stats["total_valid_time"] = len(inv_valid)
    inv_sza_ok = inv_valid.copy()
    if len(inv_sza_ok) == 0:
        return None, filter_stats
    sat_list = []
    field_list = []
    time_diff_list = []
    for _, sat_row in inv_sza_ok.iterrows():
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
        "SZA": sat_df["SZA"],
        "time_diff_min": np.array(time_diff_list),
        "T_Vegetation": sat_df["T_Vegetation"],
        "T_Soil": sat_df["T_Shaded_Soil"],
        "T_Sunlit_Soil": sat_df["T_Sunlit_Soil"],
        "T_Shaded_Soil": sat_df["T_Shaded_Soil"],
        "TA_field": field_match_df["TA"],
        "TS1_field": field_match_df["TS_1"]
    })
    sat_temp_cols = ["T_Vegetation", "T_Soil", "T_Sunlit_Soil", "T_Shaded_Soil"]
    field_temp_cols = ["TA_field", "TS1_field"]
    all_temp_cols = sat_temp_cols + field_temp_cols
    temp_mask = pd.Series(False, index=match_df.index)
    for col in all_temp_cols:
        col_na = match_df[col].isna()
        col_out_range = (match_df[col] < TEMP_MIN) | (match_df[col] > TEMP_MAX)
        temp_mask = temp_mask | col_na | col_out_range
    filter_stats["temp_filtered"] = temp_mask.sum()
    match_temp_ok = match_df[~temp_mask].copy()
    if len(match_temp_ok) == 0:
        return None, filter_stats
    tsheld_arr = calculate_tsheld(match_temp_ok["SZA"].values)
    veg_diff = np.abs(match_temp_ok["T_Vegetation"] - match_temp_ok["TA_field"])
    soil_diff = np.abs(match_temp_ok["T_Soil"] - match_temp_ok["TS1_field"])
    tsheld_mask = (veg_diff > tsheld_arr) | (soil_diff > tsheld_arr)
    filter_stats["tsheld_filtered"] = tsheld_mask.sum()
    final_match = match_temp_ok[~tsheld_mask].copy()
    filter_stats["kept"] = len(final_match)
    final_match["veg_temp_diff"] = np.abs(final_match["T_Vegetation"] - final_match["TA_field"])
    final_match["soil_temp_diff"] = np.abs(final_match["T_Soil"] - final_match["TS1_field"])
    final_match["Tsheld"] = calculate_tsheld(final_match["SZA"].values)
    print(f"\n  数据筛选统计 ({site_name}):")
    print(f"    原始卫星记录: {filter_stats['total_raw']}")
    print(f"    时间窗口过滤: {filter_stats['time_filtered']}")
    print(f"    温度极值过滤: {filter_stats['temp_filtered']}")
    print(f"    动态温差阈值过滤: {filter_stats['tsheld_filtered']}")
    print(f"    最终匹配保留: {filter_stats['kept']}")
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
        "slope": slope,
        "intercept": intercept,
        "p_value": p_value
    }

def process_single_site(site, full_inversion_df):
    print(f"\n{'=' * 60}")
    print(f"处理站点: {site}")
    print(f"{'=' * 60}")
    site_inv = full_inversion_df[full_inversion_df["Site"] == site].copy()
    if len(site_inv) == 0:
        print(f"  警告: {site} 无卫星反演数据，跳过")
        return None
    field_df = read_field_data(site)
    if field_df is None:
        print(f"  错误: 站点 {site} 无有效地面观测数据，跳过")
        return None
    print(f"  该站点卫星反演记录: {len(site_inv)}")
    print(f"  地面观测记录: {len(field_df)}")
    match_df, filter_stat = batch_match_inversion_field(site_inv, field_df, site, TIME_WINDOW)
    del field_df
    if match_df is None or len(match_df) == 0:
        print(f"  ✗ 无有效匹配样本")
        return None
    print(f"\n  ✓ 成功匹配 {len(match_df)} 条样本")
    veg_metric = calculate_metrics(match_df["TA_field"].values, match_df["T_Vegetation"].values)
    soil_metric = calculate_metrics(match_df["TS1_field"].values, match_df["T_Soil"].values)
    print(f"\n  {'='*50} 验证指标 {site} {'='*50}")
    if veg_metric:
        print(f"【植被温度 T_Vegetation vs TA_field】 n={veg_metric['n_sample']}")
        print(f"    RMSE={veg_metric['RMSE']:.4f}℃ | Bias={veg_metric['Bias']:.4f}℃")
        print(f"    R={veg_metric['R']:.4f} | R²={veg_metric['R2']:.4f} | Slope={veg_metric['slope']:.4f}")
    else:
        print("【植被温度】有效样本不足3个，无法统计")
    if soil_metric:
        print(f"【土壤温度 T_Soil vs TS1_field】 n={soil_metric['n_sample']}")
        print(f"    RMSE={soil_metric['RMSE']:.4f}℃ | Bias={soil_metric['Bias']:.4f}℃")
        print(f"    R={soil_metric['R']:.4f} | R²={soil_metric['R2']:.4f} | Slope={soil_metric['slope']:.4f}")
    else:
        print("【土壤温度】有效样本不足3个，无法统计")
    print(f"  {'='*50}")
    save_path = os.path.join(OUTPUT_DIR, f"{site}_matched_dataset.csv")
    match_df.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"  站点匹配数据已保存: {os.path.basename(save_path)}")
    return {
        "site": site,
        "match_count": len(match_df),
        "veg_metric": veg_metric,
        "soil_metric": soil_metric,
        "match_file": save_path
    }

# ================= 主程序 =================
def main():
    print("=" * 60)
    print("LSCT地表温度反演验证 | 移除SZA过滤 + 输出全部站点 + 筛选TOP20最优站点")
    print("=" * 60)
    print("核心逻辑：")
    print("  1. 一次性读取完整反演文件，按站点整体切片")
    print("  2. for site 循环内实时读取对应站点地面数据，不预加载所有站点")
    print("  3. 无SZA范围过滤，保留时间/温度/Tsheld筛选")
    print("  4. 输出全部站点汇总；按RMSE选出最优20站点并单独导出")
    print(f"\n质控参数：")
    print(f"  温度区间: {TEMP_MIN} ~ {TEMP_MAX} ℃")
    print(f"  时间匹配窗口: {TIME_WINDOW} min")
    print(f"  动态温差阈值Tsheld: 3 ~ 8 ℃")
    print(f"  最优站点排序依据: {SORT_METRIC} RMSE升序(误差越小越优)")
    print(f"  选取最优站点数量: {TOP_N_BEST}")
    print(f"  自动运行模式: {'开启' if AUTO_RUN else '关闭(手动回车切换站点)'}")

    # Step1 读取反演总表
    print("\n[1/4] 一次性读取完整反演数据集")
    if not os.path.exists(INVERSION_RESULT_FILE):
        print(f"错误：反演文件不存在 {INVERSION_RESULT_FILE}")
        return
    full_inversion_df = pd.read_csv(INVERSION_RESULT_FILE)
    all_sites = sorted(full_inversion_df["Site"].unique())
    print(f"  总反演记录: {len(full_inversion_df)}")
    print(f"  待处理站点列表: {', '.join(all_sites)}")

    # Step2 逐站点处理
    print("\n[2/4] 逐站点批量处理")
    summary_list = []
    for site in all_sites:
        site_result = process_single_site(site, full_inversion_df)
        if site_result is not None:
            summary_list.append(site_result)
        print("\n" + "-" * 60)
        if not AUTO_RUN:
            input("按下Enter处理下一个站点...")

    if len(summary_list) == 0:
        print("无任何站点产出有效匹配样本，验证结束")
        return

    # Step3 构建全站点汇总表
    print("\n[3/4] 生成全部站点汇总结果并打印")
    summary_rows = []
    for item in summary_list:
        site = item["site"]
        n_match = item["match_count"]
        vm = item["veg_metric"]
        sm = item["soil_metric"]
        if vm:
            summary_rows.append({
                "Site": site,
                "Variable": "T_Vegetation",
                "Match_Samples": n_match,
                "RMSE": round(vm["RMSE"],4),
                "Bias": round(vm["Bias"],4),
                "R": round(vm["R"],4),
                "R2": round(vm["R2"],4),
                "Slope": round(vm["slope"],4),
                "Intercept": round(vm["intercept"],4),
                "P_value": round(vm["p_value"],4),
                "MatchDataFile": item["match_file"]
            })
        if sm:
            summary_rows.append({
                "Site": site,
                "Variable": "T_Soil",
                "Match_Samples": n_match,
                "RMSE": round(sm["RMSE"],4),
                "Bias": round(sm["Bias"],4),
                "R": round(sm["R"],4),
                "R2": round(sm["R2"],4),
                "Slope": round(sm["slope"],4),
                "Intercept": round(sm["intercept"],4),
                "P_value": round(sm["p_value"],4),
                "MatchDataFile": item["match_file"]
            })
    all_site_df = pd.DataFrame(summary_rows)
    all_csv = os.path.join(OUTPUT_DIR, "validation_all_sites_summary.csv")
    all_site_df.to_csv(all_csv, index=False, encoding="utf-8-sig")

    # 打印全部站点汇总
    print("\n" + "="*90)
    print("【全部站点验证指标汇总表】")
    print("="*90)
    print(f"{'站点':<12}{'变量':<16}{'样本数':<8}{'RMSE(℃)':<10}{'Bias(℃)':<10}{'R':<8}{'R²':<8}")
    print("-"*90)
    for _, row in all_site_df.iterrows():
        print(f"{row['Site']:<12}{row['Variable']:<16}{row['Match_Samples']:<8}{row['RMSE']:<10.4f}{row['Bias']:<10.4f}{row['R']:<8.4f}{row['R2']:<8.4f}")
    print(f"\n全部站点汇总文件保存至：{all_csv}")

    # Step4 筛选最优20个站点
    print(f"\n[4/4] 筛选TOP {TOP_N_BEST} 最优站点（按{SORT_METRIC} RMSE升序）")
    # 只保留目标变量数据
    top_df_raw = all_site_df[all_site_df["Variable"] == SORT_METRIC].copy()
    # 过滤有效RMSE
    top_df_valid = top_df_raw.dropna(subset=["RMSE"]).copy()
    if len(top_df_valid) == 0:
        print("无有效站点可筛选最优样本")
        return
    # RMSE从小到大排序（误差越小越好）
    top_df_sorted = top_df_valid.sort_values("RMSE", ascending=True).reset_index(drop=True)
    # 取前20
    top_n_df = top_df_sorted.head(TOP_N_BEST).copy()
    top_csv = os.path.join(OUTPUT_DIR, f"validation_top{TOP_N_BEST}_best_sites_{SORT_METRIC}.csv")
    top_n_df.to_csv(top_csv, index=False, encoding="utf-8-sig")

    # 打印最优20站点表格
    print("\n" + "="*90)
    print(f"【TOP {TOP_N_BEST} 最优站点 - 按{SORT_METRIC}误差从小到大】")
    print("="*90)
    print(f"{'排名':<6}{'站点':<12}{'变量':<16}{'样本数':<8}{'RMSE(℃)':<10}{'Bias(℃)':<10}{'R':<8}{'R²':<8}")
    print("-"*90)
    for idx, row in top_n_df.iterrows():
        rank = idx + 1
        print(f"{rank:<6}{row['Site']:<12}{row['Variable']:<16}{row['Match_Samples']:<8}{row['RMSE']:<10.4f}{row['Bias']:<10.4f}{row['R']:<8.4f}{row['R2']:<8.4f}")
    print(f"\nTOP{TOP_N_BEST}最优站点文件保存至：{top_csv}")

    print("\n===== 全部验证流程执行完成 =====")
    print(f"输出文件目录：{OUTPUT_DIR}")
    print(f"1. validation_all_sites_summary.csv  全部站点指标")
    print(f"2. validation_top{TOP_N_BEST}_best_sites_{SORT_METRIC}.csv  最优20站点指标")
    print(f"3. [site]_matched_dataset.csv 每个站点原始匹配数据集")

if __name__ == "__main__":
    main()
