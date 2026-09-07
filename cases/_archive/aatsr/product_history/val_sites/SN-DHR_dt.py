import sys
import os
import pandas as pd
import numpy as np
import xgboost as xgb
from datetime import datetime

# ================= 配置路径 =================
# 站点名称 (需与 FLUXSITE_imagexy.xlsx 中的 SITE_ID 一致)
# 注意：Fluxnet中 Dahra 通常是 'SD-Dhr' 或 'SN-Dhr'，请确保 Excel 里有这个 ID
SITE_ID = 'SN-Dhr' 

base_dir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/'
metadata_file = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/FLUXSITE_imagexy.xlsx'
model_path = os.path.join(base_dir, 'xgb_delta_t_model_high_precision.json')

# 待预测的输入文件
input_csv = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/results/Dahra/inv_2c_5w_lai_merge.csv'
# 输出文件路径
output_csv = input_csv.replace('.csv', '_predicted.csv')

# ================= IGBP 映射 (必须与训练时一致) =================
IGBP_MAP = {
    'ENF': 1, 'EBF': 2, 'DNF': 3, 'DBF': 4, 'MF': 5, 
    'CSH': 6, 'OSH': 7, 'WSA': 8, 'SAV': 9, 'GRA': 10, 
    'WET': 11, 'CRO': 12, 'URB': 13, 'CNV': 14, 'SNO': 15, 
    'BSV': 16, 'WAT': 17
}

def load_site_metadata(site_id, meta_path):
    """从Excel读取站点的静态信息 (ImageX, ImageY, IGBP)"""
    print(f"Loading metadata for site: {site_id}...")
    try:
        df_meta = pd.read_excel(meta_path)
        site_info = df_meta[df_meta['SITE_ID'] == site_id]
        
        if site_info.empty:
            # 尝试模糊匹配，比如 Dahra 可能是 SD-Dhr
            print(f"Warning: Exact match for '{site_id}' not found. Searching for partial match 'Dhr'...")
            site_info = df_meta[df_meta['SITE_ID'].str.contains('Dhr', case=False, na=False)]
            if site_info.empty:
                raise ValueError(f"Site {site_id} not found in metadata file.")
            else:
                print(f"Found match: {site_info.iloc[0]['SITE_ID']}")

        # 提取信息
        image_x = site_info.iloc[0]['IMAGEX']
        image_y = site_info.iloc[0]['IMAGEY']
        igbp_str = site_info.iloc[0]['IGBP']
        igbp_code = IGBP_MAP.get(igbp_str, 0) # 默认为0
        
        if igbp_code == 0:
            print(f"Warning: Unknown IGBP type '{igbp_str}', defaulting to 0.")
            
        print(f"Metadata loaded: X={image_x}, Y={image_y}, IGBP={igbp_str}({igbp_code})")
        return image_x, image_y, igbp_code

    except Exception as e:
        print(f"Error loading metadata: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # 1. 加载模型
    print("-" * 30)
    print(f"Loading model from {model_path}...")
    if not os.path.exists(model_path):
        print("Error: Model file not found. Please run the training script first.")
        sys.exit(1)
        
    model = xgb.Booster()
    model.load_model(model_path)

    # 2. 读取输入数据
    print(f"Reading input data: {input_csv}")
    df = pd.read_csv(input_csv)
    
    # 3. 获取站点静态元数据
    # 注意：如果 Excel 里 Dahra 的 ID 是 SD-Dhr，这里会自动匹配或你需要修改上面的 SITE_ID
    static_x, static_y, static_igbp = load_site_metadata(SITE_ID, metadata_file)

    # 4. 特征工程 (必须与训练逻辑完全一致)
    print("Feature engineering...")
    
    # 解析时间
    # 假设格式类似 '2009-05-03 23:00:00+00:00'
    df['dt'] = pd.to_datetime(df['Time'])
    
    # 构造基础时间特征
    df['Year'] = df['dt'].dt.year
    df['Month'] = df['dt'].dt.month
    df['Day'] = df['dt'].dt.day
    df['Hour'] = df['dt'].dt.hour
    df['Minute'] = df['dt'].dt.minute

    # 构造循环编码特征 (Sin/Cos)
    df['Hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 24.0)
    df['Hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 24.0)
    df['Month_sin'] = np.sin(2 * np.pi * df['Month'] / 12.0)
    df['Month_cos'] = np.cos(2 * np.pi * df['Month'] / 12.0)

    # 填充静态特征
    df['ImageX'] = static_x
    df['ImageY'] = static_y
    df['IGBP_Code'] = static_igbp
    
    # 映射 LAI (输入是 'lai', 模型需要 'LAI')
    if 'lai' in df.columns:
        df['LAI'] = df['lai']
    elif 'LAI' not in df.columns:
        print("Error: Column 'lai' or 'LAI' not found in input CSV.")
        sys.exit(1)

    # 5. 准备预测数据矩阵
    # 严格按照训练时的特征顺序
    feature_cols = [
        'ImageX', 'ImageY', 'Year', 'Day', 'Minute', 'IGBP_Code', 'LAI',
        'Month_sin', 'Month_cos', 'Hour_sin', 'Hour_cos'
    ]
    
    # 检查是否有缺失值 (LAI 可能有空值)
    # 如果 LAI 是空的，模型无法预测，需要处理
    missing_count = df[feature_cols].isnull().any(axis=1).sum()
    if missing_count > 0:
        print(f"Warning: {missing_count} rows contain NaNs (likely in LAI). Predictions for these rows will be unreliable.")
    
    # 转为 float32
    X_pred = df[feature_cols].values.astype(np.float32)
    
    # 转换为 DMatrix
    dpred = xgb.DMatrix(X_pred, feature_names=feature_cols)

    # 6. 执行预测
    print("Predicting Delta_T...")
    # 预测结果：y = Ts - Ta
    pred_delta_t = model.predict(dpred)
    
    # 将预测结果写入 DataFrame
    # 结果列名：Pred_Delta_T (预测的温差)
    df['Pred_Delta_T'] = pred_delta_t
    
    # 可选：如果你想直接算出预测的土壤温度 (Pred_Ts = Ta + Pred_Delta_T)
    # 但前提是你输入文件里有 Ta (空气温度)。
    # 你的前三行里看起来没有 Ta 列 (有 lstN, lstF, Tsky 等)，所以我只输出 Delta_T。
    
    # 7. 保存结果
    print(f"Saving results to: {output_csv}")
    # 只保存原始列 + 预测列，去掉中间生成的 sin/cos 辅助列保持整洁
    cols_to_save = [c for c in df.columns if c not in [
        'dt', 'Year', 'Month', 'Day', 'Hour', 'Minute', 
        'Hour_sin', 'Hour_cos', 'Month_sin', 'Month_cos', 
        'ImageX', 'ImageY', 'IGBP_Code', 'LAI' # LAI是重复的lai
    ]]
    # 确保 'Pred_Delta_T' 在里面 (上面列表生成式可能会把它排除如果没处理好，不如直接指定)
    # 简单点，保存所有列，或者只保存原始列 + Pred_Delta_T
    
    # 恢复干净的输出：原始数据 + 预测值
    original_cols = pd.read_csv(input_csv, nrows=1).columns.tolist()
    final_df = df[original_cols + ['Pred_Delta_T']]
    
    final_df.to_csv(output_csv, index=False)
    print("Done.")