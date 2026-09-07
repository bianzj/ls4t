import pandas as pd
import numpy as np

# 1. 设置文件路径 (请确认文件名是否需要修改)
# 假设你从GEE下载的文件名是 FLUXNET_FVC_Global_Threshold_2002_2012.csv
file_path = '/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/veg/FLUXNET_FVC_Global_Threshold_2002_2012.csv'

# 2. 读取数据
print(f"正在读取文件: {file_path} ...")
df = pd.read_csv(file_path)

# 3. 筛选数据用于计算阈值
# 逻辑：只使用 NDVI > 0 的数据来统计分位数，排除积雪和水体的影响
valid_pixels = df[df['NDVI'] > 0]['NDVI']

# 4. 计算新的全局阈值
new_ndvi_soil = valid_pixels.quantile(0.05)
new_ndvi_veg = valid_pixels.quantile(0.95)

print("-" * 30)
print(f"统计样本量: {len(valid_pixels)} (原数据量: {len(df)})")
print(f"旧的阈值 (可能含负数): 查看原文件中的 ndvi_min 列")
print(f"【新计算】裸土阈值 (NDVI_soil, 5%): {new_ndvi_soil:.4f}")
print(f"【新计算】全植被阈值 (NDVI_veg, 95%): {new_ndvi_veg:.4f}")
print("-" * 30)

# 5. 重新计算 FVC
# 使用新的公式：FVC = (NDVI - new_ndvi_soil) / (new_ndvi_veg - new_ndvi_soil)
# 并截断在 0-1 之间

def calculate_new_fvc(ndvi, soil, veg):
    # 分母防止为0
    if veg - soil == 0:
        return 0
    fvc = (ndvi - soil) / (veg - soil)
    # 截断
    return np.clip(fvc, 0, 1)

# 应用计算 (注意：这里对所有原始数据计算，不仅是大于0的)
# 小于0的NDVI会自动变成FVC=0，符合逻辑
df['ndvi_min_recalc'] = new_ndvi_soil
df['ndvi_max_recalc'] = new_ndvi_veg
df['FVC_recalc'] = df['NDVI'].apply(lambda x: calculate_new_fvc(x, new_ndvi_soil, new_ndvi_veg))

# 6. 保存结果
output_path = file_path.replace('.csv', '_recalculated.csv')
df.to_csv(output_path, index=False)
print(f"处理完成！结果已保存至: {output_path}")