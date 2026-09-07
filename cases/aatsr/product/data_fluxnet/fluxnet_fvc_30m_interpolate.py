import pandas as pd
import numpy as np
import os

# ================= 1. 路径配置 =================
site_list_path = '/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/FLUXSITE_imagexy.xlsx'
# 必须使用包含 'FVC_recalc' 和 'NDVI' 列的文件
fvc_file_path = '/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/veg/FLUXNET_FVC_Global_Threshold_2002_2012_recalculated.csv'
flux_source_dir = '/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/Fluxnet_data_Ts0cm'
output_dir = '/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/Fluxnet_data'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# ================= 2. 定义表头 =================
# 根据你提供的标准列名
flux_header = [
    'TIMESTAMP_START', 'TIMESTAMP_END', 'TA_F', 'TA_F_QC', 
    'TS_F_MDS_1', 'TS_F_MDS_1_QC', 'LW_IN_F', 'LW_IN_F_QC', 
    'LW_OUT', 'SWC_F_MDS_1', 'SWC_F_MDS_1_QC', 'fvc', 
    'LAI', 'LST', 'Ts0cm'
]

# ================= 3. 去离群值函数 =================
def remove_outliers(df, col_name='FVC_recalc', window=21, threshold=0.5):
    """
    去除突变低值（深坑），保留正常数据。
    """
    if len(df) < window:
        return df
    # 计算滚动中值
    rolling_median = df[col_name].rolling(window=window, center=True, min_periods=1).median()
    # 标记比中值低 0.5 以上的点为异常
    is_outlier = (rolling_median - df[col_name]) > threshold
    return df[~is_outlier]

# ================= 4. 主程序 =================
print("正在加载数据...")

# A. 读取站点列表
try:
    sites_df = pd.read_excel(site_list_path)
except:
    sites_df = pd.read_csv(site_list_path)

# B. 读取 FVC 数据
if not os.path.exists(fvc_file_path):
    print(f"错误：找不到 FVC 文件 {fvc_file_path}")
    exit()

fvc_df = pd.read_csv(fvc_file_path)
fvc_df['date'] = pd.to_datetime(fvc_df['date'])

# 检查列
if 'NDVI' not in fvc_df.columns:
    print("错误：FVC 文件中缺少 'NDVI' 列，无法过滤。")
    exit()

print("开始处理站点...")
count = 0
error_count = 0
skip_count = 0

# 设置匹配的时间窗口容差 (8天)
tolerance = pd.Timedelta(days=8)

for index, row in sites_df.iterrows():
    site_id = row['SITE_ID']
    try:
        start_year = int(row['start_year'])
        end_year = int(row['end_year'])
    except:
        continue

    filename = f"{site_id}_{start_year}-{end_year}.csv"
    source_path = os.path.join(flux_source_dir, filename)
    target_path = os.path.join(output_dir, filename)

    if not os.path.exists(source_path):
        skip_count += 1
        continue

    try:
        # 1. 读取 Fluxnet 原始数据
        # 跳过第一行 '0,,', 使用标准表头
        df_flux = pd.read_csv(source_path, skiprows=1, header=None, names=flux_header)
        
        # 解析时间列，用于匹配
        df_flux['temp_timestamp'] = pd.to_datetime(df_flux['TIMESTAMP_START'], format='%Y%m%d%H%M', errors='coerce')
        # 确保时间列排序 (merge_asof 要求)
        df_flux = df_flux.sort_values('temp_timestamp')

        # 2. 准备该站点的 FVC 数据
        site_fvc = fvc_df[fvc_df['site_id'] == site_id].copy()

        # === 数据清洗三部曲 ===
        # (1) 过滤无效 NDVI (负值/积雪)
        site_fvc = site_fvc[site_fvc['NDVI'] > 0]

        if site_fvc.empty:
            df_flux['fvc_30'] = np.nan
        else:
            # (2) 时间对齐 (加 10.5 小时)
            site_fvc['datetime'] = site_fvc['date'] + pd.Timedelta(hours=10, minutes=30)
            
            # (3) 排序与去重 (同一时间取平均)
            site_fvc = site_fvc.sort_values('datetime')
            site_fvc = site_fvc.groupby('datetime', as_index=False)['FVC_recalc'].mean()

            # (4) 去除离群值 (防止匹配到错误的深坑值)
            site_fvc = remove_outliers(site_fvc, col_name='FVC_recalc', window=21, threshold=0.5)

            # === 核心逻辑: 最近邻匹配 (带8天限制) ===
            if site_fvc.empty:
                 df_flux['fvc_30'] = np.nan
            else:
                # 仅保留需要的两列用于合并
                fvc_subset = site_fvc[['datetime', 'FVC_recalc']].sort_values('datetime')
                
                # 使用 merge_asof 进行“最近邻”查找
                # direction='nearest': 找前后最近的
                # tolerance=tolerance: 距离不能超过8天
                merged = pd.merge_asof(
                    df_flux, 
                    fvc_subset, 
                    left_on='temp_timestamp', 
                    right_on='datetime', 
                    direction='nearest', 
                    tolerance=tolerance
                )
                
                # 将匹配到的结果赋值给 fvc_30
                df_flux['fvc_30'] = merged['FVC_recalc']

        # 3. 清理保存
        if 'temp_timestamp' in df_flux.columns:
            del df_flux['temp_timestamp']
            
        # 保存带有完整表头的文件
        df_flux.to_csv(target_path, index=False, header=True)
        
        count += 1
        if count % 10 == 0:
            print(f"已处理 {count} 个站点...")

    except Exception as e:
        print(f"处理站点 {site_id} 时出错: {e}")
        error_count += 1

print("-" * 30)
print(f"全部完成！成功: {count}, 失败: {error_count}, 跳过: {skip_count}")
print(f"结果目录: {output_dir}")