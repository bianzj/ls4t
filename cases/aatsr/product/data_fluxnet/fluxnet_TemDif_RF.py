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
import glob

warnings.filterwarnings("ignore")

'''
2026.1.22 RF Model for Ts0cm - Ta (Updated)
Updates:
1. Added Longitude as a training feature.
2. Added output for Test Data predictions.
'''

# IGBP 类型映射表
IGBP_MAP = {
    'ENF': 1, 'EBF': 2, 'DNF': 3, 'DBF': 4, 'MF': 5, 
    'CSH': 6, 'OSH': 7, 'WSA': 8, 'SAV': 9, 'GRA': 10, 
    'WET': 11, 'CRO': 12, 'URB': 13, 'CNV': 14, 'SNO': 15, 
    'BSV': 16, 'WAT': 17
}

# ================= 配置 =================
# 输入目录：包含 Ts0cm 反演结果的目录
INPUT_DIR_TS0 = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/Fluxnet_data/'

# 站点元数据文件 (包含经纬度、IGBP类型)
SITE_META_FILE = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/FLUXSITE_imagexy.xlsx'

# 预测配置 (Target Site: SN-Dhr)
PREDICT_SITE_ID = 'SN-Dhr'
PREDICT_INPUT_FILE = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/results/Dahra/inv_2c_5w_lai_merge.csv'
SITE_LAT = 15.4
SITE_LON = -15.43 # 【新增】目标站点的经度 (Dahra, Senegal 约为 -15.43)
SITE_IGBP = 9 # SAV (Savannas)

# 缓存文件路径 (修改文件名以强制重新生成包含Lon的数据)
CACHE_FILE = os.path.join(INPUT_DIR_TS0, 'rf_training_cache_ts0cm_with_lon.csv')
MODEL_FILE = os.path.join(INPUT_DIR_TS0, 'rf_ts0cm_model_with_lon.pkl')
TEST_RESULT_FILE = os.path.join(INPUT_DIR_TS0, 'rf_test_data_results.csv') # 【新增】测试集结果保存路径

# ================= 工具函数 =================

def load_site_metadata(meta_file):
    """加载站点经纬度和类型信息"""
    print("Loading site metadata...")
    df = pd.read_excel(meta_file)
    meta_dict = {}
    for _, row in df.iterrows():
        site_id = row['SITE_ID']
        igbp_str = row['IGBP']
        igbp_code = IGBP_MAP.get(igbp_str, 0) # 默认为0 (未知)
        
        # 【修改】读取经度和纬度
        lat = row['LOCATION_LAT']
        # 假设Excel中经度的列名是 'LOCATION_LONG'，请根据实际情况调整
        lon = row.get('LOCATION_LONG', 0.0) 
        
        meta_dict[site_id] = {'Lat': lat, 'Lon': lon, 'IGBP': igbp_code}
    return meta_dict

def prepare_training_data(input_dir, meta_dict, cache_path):
    """读取所有站点的 Ts0cm 数据并清洗"""
    if os.path.exists(cache_path):
        print(f"Loading training data from cache: {cache_path}")
        return pd.read_csv(cache_path)

    print("Processing raw csv files to build training dataset...")
    all_files = glob.glob(os.path.join(input_dir, "*.csv"))
    data_list = []

    for i, f in enumerate(all_files):
        site_name = os.path.basename(f).split('_')[0]
        
        # 跳过预测目标站点 (防止数据泄露)
        if PREDICT_SITE_ID in site_name: 
            continue

        # 获取站点元数据
        if site_name not in meta_dict:
            continue
        
        site_info = meta_dict[site_name]
        
        try:
            df = pd.read_csv(f, na_values=['-9999', '-9999.0', -9999])
            
            # 必须包含的列
            if 'Ts0cm' not in df.columns or 'TA_F' not in df.columns or 'LAI' not in df.columns:
                continue
                
            # 去除无效值
            df.dropna(subset=['Ts0cm', 'TA_F', 'LAI', 'TIMESTAMP_START'], inplace=True)
            
            # 基础清洗: LAI 修正
            if df['LAI'].max() > 50:
                df['LAI'] = df['LAI'] / 1000.0
            
            # 计算目标变量: Ts0cm - Ta
            df['Delta_T'] = df['Ts0cm'] - df['TA_F']
            df = df[(df['Delta_T'] > -20) & (df['Delta_T'] < 50)]
            
            if df.empty: continue

            # 时间解析
            ts = df['TIMESTAMP_START'].astype(np.int64)
            df['Month'] = ((ts // 1000000) % 100).astype(np.int8)
            df['Day'] = ((ts // 10000) % 100).astype(np.int8)
            df['Hour'] = ((ts // 100) % 100).astype(np.int8)
            
            # 添加静态特征
            df['Latitude'] = site_info['Lat']
            df['Longitude'] = site_info['Lon'] # 【新增】经度特征
            df['IGBP_Code'] = site_info['IGBP']
            
            # 选择需要的列
            # 【修改】加入了 Longitude
            cols = ['TA_F', 'LAI', 'Latitude', 'Longitude', 'IGBP_Code', 'Month', 'Day', 'Hour', 'Delta_T']
            data_list.append(df[cols].astype(np.float32))
            
        except Exception as e:
            continue
            
        if i % 20 == 0:
            print(f"  Processed {i}/{len(all_files)} files...")

    if not data_list:
        sys.exit("No valid training data found.")

    final_df = pd.concat(data_list, ignore_index=True)
    final_df.to_csv(cache_path, index=False)
    print(f"Cache saved to {cache_path}. Total samples: {len(final_df)}")
    return final_df

# ================= 主程序 =================

if __name__ == '__main__':
    
    # 1. 准备数据
    meta_data = load_site_metadata(SITE_META_FILE)
    df_train = prepare_training_data(INPUT_DIR_TS0, meta_data, CACHE_FILE)
    
    # 2. 物理逻辑诊断
    print("\n[Diagnosis] Training Data Logic Check:")
    noon_dt = df_train[df_train['Hour'] == 11]['Delta_T'].mean()
    night_dt = df_train[df_train['Hour'] == 22]['Delta_T'].mean()
    print(f"  > Mean Delta_T (Noon):  {noon_dt:.2f} K")
    print(f"  > Mean Delta_T (Night): {night_dt:.2f} K")
    if noon_dt > night_dt:
        print("  ✅ Logic Pass: Day > Night")
    else:
        print("  ❌ Logic Warning: Day <= Night? Check data quality.")

    # 3. 训练模型
    print("-" * 40)
    print("Training Random Forest Regressor...")
    
    # 【修改】特征列表中加入 Longitude
    features = ['TA_F', 'LAI', 'Latitude', 'Longitude', 'IGBP_Code', 'Month', 'Day', 'Hour']
    target = 'Delta_T'
    
    X = df_train[features].values
    y = df_train[target].values
    
    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 初始化 RF
    rf = RandomForestRegressor(n_estimators=100, max_depth=25, min_samples_split=5, 
                               min_samples_leaf=2, n_jobs=-1, random_state=42)
    rf.fit(X_train, y_train)
    
    # 评估
    y_pred_test = rf.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    r2 = r2_score(y_test, y_pred_test)
    print(f"Model Evaluation -> RMSE: {rmse:.4f}, R2: {r2:.4f}")

    # ================= 【新增】保存测试集结果 =================
    print("-" * 40)
    print("Saving Test Data Results...")
    
    # 将测试集特征转回 DataFrame
    df_test_results = pd.DataFrame(X_test, columns=features)
    # 添加真实值和预测值
    df_test_results['True_Delta_T'] = y_test
    df_test_results['Pred_Delta_T'] = y_pred_test
    # 算出具体的误差
    df_test_results['Error'] = df_test_results['Pred_Delta_T'] - df_test_results['True_Delta_T']
    
    df_test_results.to_csv(TEST_RESULT_FILE, index=False)
    print(f"Test results saved to: {TEST_RESULT_FILE}")
    print(df_test_results.head())
    # ========================================================
    
    # 保存模型
    joblib.dump(rf, MODEL_FILE)
    print(f"Model saved to: {MODEL_FILE}")
    
    # 4. 预测新站点 (SN-Dhr)
    print("-" * 40)
    print(f"Predicting for target site: {PREDICT_SITE_ID}")
    
    if os.path.exists(PREDICT_INPUT_FILE):
        df_pred = pd.read_csv(PREDICT_INPUT_FILE)
        
        # 构造特征
        if 'TA_F' in df_pred.columns:
            df_pred['Ta_for_pred'] = df_pred['TA_F']
        elif 'Ta' in df_pred.columns:
            df_pred['Ta_for_pred'] = df_pred['Ta']
        else:
            print("Error: Target file missing Air Temperature (TA_F or Ta)")
            sys.exit()

        if 'lai' in df_pred.columns: 
             df_pred['LAI_for_pred'] = df_pred['lai']
        elif 'LAI' in df_pred.columns:
             df_pred['LAI_for_pred'] = df_pred['LAI']
        else:
             df_pred['LAI_for_pred'] = 0.5
             
        # 添加静态参数
        df_pred['Latitude'] = SITE_LAT
        df_pred['Longitude'] = SITE_LON # 【新增】
        df_pred['IGBP_Code'] = SITE_IGBP
        
        # 时间特征
        df_pred['dt_str'] = df_pred['Time'].astype(str)
        df_pred['Month'] = df_pred['dt_str'].str.slice(5, 7).astype(int)
        df_pred['Day'] = df_pred['dt_str'].str.slice(8, 10).astype(int)
        df_pred['Hour'] = df_pred['dt_str'].str.slice(11, 13).astype(int)
        
        # 提取 X_pred (注意列顺序必须与训练时 features 一致)
        pred_cols = ['Ta_for_pred', 'LAI_for_pred', 'Latitude', 'Longitude', 'IGBP_Code', 'Month', 'Day', 'Hour']
        pred_data = df_pred[pred_cols].values
        pred_data = np.nan_to_num(pred_data, nan=0.0)
        
        # 预测 Delta_T
        pred_delta_t = rf.predict(pred_data)
        
        df_pred['Pred_Delta_T_RF'] = pred_delta_t
        df_pred['Pred_Ts0cm_RF'] = df_pred['Ta_for_pred'] + pred_delta_t
        
        out_file = PREDICT_INPUT_FILE.replace('.csv', '_RF_Predicted_with_Lon.csv')
        df_pred.to_csv(out_file, index=False)
        print(f"Prediction saved to: {out_file}")
        
    else:
        print(f"Target file not found: {PREDICT_INPUT_FILE}")