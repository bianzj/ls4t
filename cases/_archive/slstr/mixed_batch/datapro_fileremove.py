import sys
import os
import numpy as np
import xarray as xr
import h5py
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

infile = "/home/hero/下载/2020-era5-tcwv/data.grib"
outdir = "/media/hero/rs/tcwv/era5_daily_H5/2020/"
os.makedirs(outdir, exist_ok=True)

# 读取 GRIB 文件
print("正在读取 GRIB 文件...")
ds = xr.open_dataset(infile, engine='cfgrib')

# 获取 TCWV 变量名
tcwv_var = None
for var in ds.data_vars:
    if 'tcwv' in var.lower() or 'tcw' in var.lower():
        tcwv_var = var
        break

if tcwv_var is None:
    possible_names = ['tcwv', 'tcw', 'total_column_water_vapour']
    for name in possible_names:
        if name in ds.data_vars:
            tcwv_var = name
            break

if tcwv_var is None:
    print("可用变量:", list(ds.data_vars))
    tcwv_var = list(ds.data_vars)[0]

print(f"处理变量: {tcwv_var}")

# 获取数据
data = ds[tcwv_var]

# 如果有高度层，选择第一层
if len(data.dims) >= 4:
    data = data.isel(level=0)

# 获取时间
time_vals = data.time.values

# 按天分组 - 修正方法
unique_dates = []
for t in time_vals:
    # 转换为 datetime 对象
    if hasattr(t, 'astype'):
        dt = t.astype('datetime64[D]')
        dt_obj = dt.astype(datetime)
    else:
        dt_obj = t
    if dt_obj not in unique_dates:
        unique_dates.append(dt_obj)

print(f"总天数: {len(unique_dates)}")

for i, date in enumerate(unique_dates, 1):
    # 选择当天数据
    mask = []
    for t in time_vals:
        if hasattr(t, 'astype'):
            dt = t.astype('datetime64[D]').astype(datetime)
        else:
            dt = t
        mask.append(dt == date)

    day_data = data.isel(time=mask)

    # 转换为数组
    arr = day_data.values

    # 生成文件名: tcwv_YYYYMMDD.h5
    date_str = date.strftime('%Y%m%d')
    outfile = os.path.join(outdir, f"tcwv_{date_str}.h5")

    # 写入 HDF5
    with h5py.File(outfile, 'w') as f:
        f.create_dataset('tcw', data=arr, compression='gzip')
        f['tcw'].attrs['date'] = date_str
        f['tcw'].attrs['variable'] = 'Total Column Water Vapour'
        f['tcw'].attrs['unit'] = 'kg/m^2'

        # 保存经纬度
        if 'latitude' in ds.coords:
            f.create_dataset('latitude', data=ds.latitude.values)
        if 'longitude' in ds.coords:
            f.create_dataset('longitude', data=ds.longitude.values)

    if i % 30 == 0 or i == len(unique_dates):
        print(f"进度: {i}/{len(unique_dates)} - 已生成: {os.path.basename(outfile)}")

print("全部完成！")