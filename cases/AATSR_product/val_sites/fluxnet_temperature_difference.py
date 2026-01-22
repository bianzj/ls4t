import sys
import os
import warnings
import pandas as pd
import numpy as np
import gc
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# 添加路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from base.util_lsct import *
from base.util_file import *

warnings.filterwarnings("ignore")

'''2025.12.30'''
'''Random Forest 物理修正版: LST(K)转摄氏度 + 强制日夜温差诊断'''

IGBP_MAP = {
    'ENF': 1, 'EBF': 2, 'DNF': 3, 'DBF': 4, 'MF': 5, 
    'CSH': 6, 'OSH': 7, 'WSA': 8, 'SAV': 9, 'GRA': 10, 
    'WET': 11, 'CRO': 12, 'URB': 13, 'CNV': 14, 'SNO': 15, 
    'BSV': 16, 'WAT': 17
}

# ================= 配置 =================
PREDICT_SITE_ID = 'SN-Dhr'
PREDICT_INPUT_FILE = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/results/Dahra/inv_2c_5w_lai_merge.csv'

# Dahra 物理参数
SITE_LAT = 15.4
SITE_IGBP = 9 # SAV

if __name__ == '__main__':
    base_dir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/'
    infile_fluxnet_xy = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/FLUXSITE_imagexy.xlsx'
    indir_fluxnet = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/Fluxnet_data/'
    
    # 缓存文件 (LST版)
    cache_file = os.path.join(base_dir, 'fluxnet_lst_k_processed.csv')

    # ================= 1. 数据清洗 (LST + Kelvin转换) =================
    if not os.path.exists(cache_file):
        print("Processing raw data (Switching to LST & Kelvin conversion)...")
        data = pd.read_excel(infile_fluxnet_xy)
        fileNames = search_file(indir_fluxnet, '.csv')
        all_data_list = []

        for i, fileName in enumerate(fileNames):
            siteName = fileName.split('_')[0]
            if siteName not in data['SITE_ID'].values: siteName = fileName.split('.')[0]
            if 'Dhr' in siteName: continue 

            if i % 50 == 0: print(f"Processing {i}: {siteName}")
            
            site_info = data[data['SITE_ID'] == siteName]
            if site_info.empty: continue
            lat_val = site_info['LOCATION_LAT'].values[0]
            IGBP_str = site_info['IGBP'].values[0]
            IGBP_code = IGBP_MAP.get(IGBP_str, 0)
            
            infile_mea = os.path.join(indir_fluxnet, fileName)
            try: mea_df = pd.read_csv(infile_mea)
            except: continue
            
            # >>> 关键修改：寻找 LST 列 <<<
            # 优先找 'LST', 如果没有找 'TS_F_MDS_1'
            if 'LST' in mea_df.columns:
                target_surf_col = 'LST'
            elif 'TS_F_MDS_1' in mea_df.columns:
                target_surf_col = 'TS_F_MDS_1'
            else:
                continue # 都没有就跳过

            # 基础过滤
            if 'TA_F' not in mea_df.columns or 'TIMESTAMP_START' not in mea_df.columns: continue
            
            # 去除无效值
            valid_mask = (mea_df[target_surf_col] > -100) & (mea_df['TA_F'] > -100) & (mea_df['LAI'] > -100)
            clean_df = mea_df[valid_mask].copy()
            if clean_df.empty: continue

            # >>> 核心：单位换算与温差计算 <<<
            surf_temp = clean_df[target_surf_col].values
            air_temp = clean_df['TA_F'].values

            # 智能判断单位：如果均值 > 200，说明是 Kelvin，必须减 273.15
            # 如果是 10~30 左右，说明已经是摄氏度
            if np.mean(surf_temp) > 200:
                # print(f"  [Info] Detected Kelvin in {siteName} ({target_surf_col}), converting...")
                surf_temp_c = surf_temp - 273.15
            else:
                surf_temp_c = surf_temp
            
            # 计算温差 (地 - 气)
            clean_df['Delta_T'] = surf_temp_c - air_temp
            
            # 物理过滤 (-30 ~ +40 是合理的LST-Ta范围)
            clean_df = clean_df[(clean_df['Delta_T'] > -30) & (clean_df['Delta_T'] < 40)]
            if clean_df.empty: continue

            # 时间解析 (数字截取法)
            clean_df['ts_int'] = pd.to_numeric(clean_df['TIMESTAMP_START'], errors='coerce')
            clean_df.dropna(subset=['ts_int'], inplace=True)
            clean_df['ts_int'] = clean_df['ts_int'].astype(np.int64)

            # YYYYMMDDHHMM
            clean_df['Year'] = (clean_df['ts_int'] // 100000000).astype(np.int16)
            clean_df['Month'] = ((clean_df['ts_int'] // 1000000) % 100).astype(np.int8)
            clean_df['Day'] = ((clean_df['ts_int'] // 10000) % 100).astype(np.int8)
            clean_df['Hour'] = ((clean_df['ts_int'] // 100) % 100).astype(np.int8)
            clean_df['Minute'] = (clean_df['ts_int'] % 100).astype(np.int8)
            
            clean_df['Latitude'] = lat_val
            clean_df['IGBP_Code'] = IGBP_code

            sel = clean_df[['Latitude', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'IGBP_Code', 'LAI', 'Delta_T']]
            sel = sel.astype({'LAI':'float32', 'Delta_T':'float32', 'Latitude':'float32'})
            all_data_list.append(sel)

        if not all_data_list: sys.exit("No data.")
        final_df = pd.concat(all_data_list, axis=0, ignore_index=True)
        final_df.to_csv(cache_file, index=False)
        print("Cache generated.")
        
        # >>> 诊断 1: 训练集物理逻辑 <<<
        print("\n[Diagnosis] Training Data (Fluxnet):")
        noon_dt = final_df[final_df['Hour'] == 12]['Delta_T'].mean()
        mid_dt = final_df[final_df['Hour'] == 0]['Delta_T'].mean()
        print(f"  > Noon (12:00) Mean Delta_T: {noon_dt:.2f} K")
        print(f"  > Midnight (00:00) Mean Delta_T: {mid_dt:.2f} K")
        if noon_dt > mid_dt:
            print("  ✅ Logic Pass: Day is hotter than Night.")
        else:
            print("  ❌ Logic Fail: Day is cooler? Check timestamps!")
        
        del final_df, all_data_list
        gc.collect()

    # ================= 2. 训练 Random Forest =================
    print("-" * 30)
    print("Training Random Forest...")
    
    # 读缓存
    df_train = pd.read_csv(cache_file)
    features = ['Latitude', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'IGBP_Code', 'LAI']
    target = 'Delta_T'
    
    # 再次诊断，确保读进来也没错
    noon_check = df_train[df_train['Hour'] == 12]['Delta_T'].mean()
    mid_check = df_train[df_train['Hour'] == 0]['Delta_T'].mean()
    print(f"  [Pre-Train Check] Noon: {noon_check:.2f}, Midnight: {mid_check:.2f}")

    X = df_train[features].values
    y = df_train[target].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    rf = RandomForestRegressor(n_estimators=60, max_depth=20, n_jobs=-1, random_state=42, min_samples_leaf=5)
    rf.fit(X_train, y_train)
    
    rmse = np.sqrt(mean_squared_error(y_test, rf.predict(X_test)))
    print(f"Model RMSE: {rmse:.4f}")
    
    del df_train, X, y
    gc.collect()

    # ================= 3. 预测 SN-Dhr =================
    print("-" * 30)
    print(f"Predicting for SN-Dhr...")
    
    df_pred = pd.read_csv(PREDICT_INPUT_FILE)
    
    # 时间解析 (字符串截取，不涉时区)
    # 格式: 2009-05-03 23:00:00...
    df_pred['dt_str'] = df_pred['Time'].astype(str)
    
    df_pred['Year'] = df_pred['dt_str'].str.slice(0, 4).astype(int)
    df_pred['Month'] = df_pred['dt_str'].str.slice(5, 7).astype(int)
    df_pred['Day'] = df_pred['dt_str'].str.slice(8, 10).astype(int)
    df_pred['Hour'] = df_pred['dt_str'].str.slice(11, 13).astype(int)
    df_pred['Minute'] = df_pred['dt_str'].str.slice(14, 16).astype(int)
    
    # 强制赋值物理参数
    df_pred['Latitude'] = SITE_LAT
    df_pred['IGBP_Code'] = SITE_IGBP
    if 'lai' in df_pred.columns: df_pred['LAI'] = df_pred['lai']
    
    X_pred = df_pred[features].values
    X_pred = np.nan_to_num(X_pred, nan=0.0) # 补0防崩
    
    # 预测
    pred_delta = rf.predict(X_pred)
    df_pred['Pred_Delta_T'] = pred_delta
    
    # >>> 诊断 2: 预测结果物理逻辑 <<<
    print("\n[Diagnosis] Prediction Result (SN-Dhr):")
    
    # 筛选 12:00 (中午) 和 00:00 (半夜) 的数据
    day_pred_mean = df_pred[df_pred['Hour'] == 12]['Pred_Delta_T'].mean()
    night_pred_mean = df_pred[df_pred['Hour'] == 0]['Pred_Delta_T'].mean()
    
    print(f"  > Noon (12:00) Predicted Mean Delta_T: {day_pred_mean:.4f} K")
    print(f"  > Midnight (00:00) Predicted Mean Delta_T: {night_pred_mean:.4f} K")
    
    if day_pred_mean > night_pred_mean:
        print("  ✅ Logic Pass: Predicted Day is hotter than Night.")
    else:
        print("  ❌ Logic Fail: Predicted Day is cooler? Model might be confused by input features.")

    # 保存
    output_csv = PREDICT_INPUT_FILE.replace('.csv', '_RF_LST_Predicted.csv')
    orig_cols = pd.read_csv(PREDICT_INPUT_FILE, nrows=1).columns.tolist()
    final_out = df_pred[orig_cols + ['Pred_Delta_T']]
    final_out.to_csv(output_csv, index=False)
    print(f"Saved to: {output_csv}")