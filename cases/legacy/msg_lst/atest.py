import xarray as xr
import rioxarray
import numpy as np
import os
from rasterio.transform import from_origin

indir = '/Users/bianzj/Downloads/data/lai/20172/'
outdir = '/Users/bianzj/Downloads/data/lai/2017/'

if not os.path.exists(outdir):
    os.makedirs(outdir)

# --- 1. 定义标准全球 0.01° 网格参数 ---
# 维度: 18000 (行/纬度) x 36000 (列/经度)
# 范围: 西经180~东经180, 北纬90~南纬-90
# 计算像素中心点坐标 (中心对齐)
lats = np.linspace(90 - 0.005, -90 + 0.005, 18000)
lons = np.linspace(-180 + 0.005, 180 - 0.005, 36000)

# 填充值通常是 int16 的最小值 -32768 (你提到的 3**** 可能是指这个)
FILL_VALUE = -32768

for fn in os.listdir(indir):
    if fn.endswith('.h5'):
        h5_path = os.path.join(indir, fn)
        out_path = os.path.join(outdir, fn.replace('.h5', '.tif'))

        try:
            # 使用 netcdf4 引擎打开，绕过部分 H5 兼容性问题
            ds = xr.open_dataset(h5_path, engine='netcdf4')

            # 获取数据 (假设 key 是 'data')
            # 使用 .load() 确保数据完全读入内存进行操作
            data_array = ds['data'].load()

            # 降维：[1, 18000, 36000] -> [18000, 36000]
            if data_array.ndim == 3:
                data_array = data_array.squeeze()

            # 检查大小是否真的是 18000x36000
            if data_array.shape != (18000, 36000):
                # 如果是 (36000, 18000)，说明数据是转置存储的
                if data_array.shape == (36000, 18000):
                    data_array = data_array.T
                else:
                    raise ValueError(f"尺寸不符: {data_array.shape}, 期望 (18000, 36000)")

            # --- 核心修复：手动赋予正确的维度名和坐标值 ---
            # 放弃 H5 内部的 dim_0/dim_1，强制改为 y 和 x
            data_array = xr.DataArray(
                data_array.values,
                coords={'y': lats, 'x': lons},
                dims=['y', 'x'],
                name='LAI'
            )

            # 设置坐标系和空间属性
            data_array.rio.write_crs("EPSG:4326", inplace=True)

            # 处理填充值（Nodata）
            # 强制设为 int16 格式，防止自动转成 float64 浪费空间
            data_array = data_array.astype(np.int16)
            data_array.rio.write_nodata(FILL_VALUE, inplace=True)

            # 导出 TIF
            data_array.rio.to_raster(
                out_path,
                driver="GTiff",
                compress='lzw',  # 必须压缩
                tiled=True,  # 分块存储提高读取效率
                blockxsize=256,
                blockysize=256,
                dtype=np.int16  # 确保输出也是 int16，节省一半空间
            )

            print(f"--- [成功] {fn} ---")
            ds.close()

        except Exception as e:
            print(f"!!! [失败] {fn}: {e}")

print("\n处理结束！")