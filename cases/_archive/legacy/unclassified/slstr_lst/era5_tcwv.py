import sys
import os
import numpy as np
import xarray as xr

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from base.util_data import *
from base.util_file import *



# ==================== 配置 ====================
infile = r"C:\Users\jiank\Downloads\Compressed\a387e2440d5dd06c30c39e0f8f929408\data.grib"
outdir = r"C:\Users\jiank\Downloads\Compressed\a387e2440d5dd06c30c39e0f8f929408\era5_daily_H5\2020"
os.makedirs(outdir, exist_ok=True)

# ==================== 核心函数 ====================

def shift_longitude(ds):
    """
    将经度从 0-360 转换为 -180-180
    相当于将图像左右互换
    """
    # 检查经度范围
    lon = ds.longitude.values
    
    if lon.min() >= 0 and lon.max() <= 360:
        print(f"原始经度范围: {lon.min():.1f}° - {lon.max():.1f}° (0-360格式)")
        
        # 方法1: 使用 xarray 的 roll 方法
        # 找到 180° 经度的位置
        idx_180 = np.argmin(np.abs(lon - 180))
        
        # 滚动经度，使 0° 经度在中间
        ds_shifted = ds.roll(longitude=-idx_180, roll_coords=True)
        
        # 重新赋值经度坐标
        new_lon = np.concatenate([lon[idx_180:] - 360, lon[:idx_180]])
        ds_shifted = ds_shifted.assign_coords(longitude=new_lon)
        
        # 按经度排序
        ds_shifted = ds_shifted.sortby('longitude')
        
        print(f"转换后经度范围: {ds_shifted.longitude.values.min():.1f}° - {ds_shifted.longitude.values.max():.1f}° (-180-180格式)")
        
        return ds_shifted
    else:
        print(f"经度已经是 -180-180 格式: {lon.min():.1f}° - {lon.max():.1f}°")
        return ds

def shift_longitude_simple(ds):
    """
    更简单的方法：直接拆分和拼接
    """
    lon = ds.longitude.values
    
    if lon.min() >= 0 and lon.max() <= 360:
        # 分割点: 180°
        split_idx = np.argmin(np.abs(lon - 180))
        
        # 获取变量名
        var_name = list(ds.data_vars)[0]
        
        # 拆分数据
        data = ds[var_name]
        data_part1 = data.isel(longitude=slice(split_idx, None))  # 180°-360°
        data_part2 = data.isel(longitude=slice(0, split_idx))     # 0°-180°
        
        # 合并: 先放 180-360，再放 0-180
        data_shifted = xr.concat([data_part1, data_part2], dim='longitude')
        
        # 更新经度坐标
        new_lon = np.concatenate([lon[split_idx:] - 360, lon[:split_idx]])
        data_shifted = data_shifted.assign_coords(longitude=new_lon)
        
        # 重建数据集
        ds_shifted = xr.Dataset({var_name: data_shifted})
        ds_shifted = ds_shifted.assign_coords({
            'longitude': new_lon,
            'latitude': ds.latitude.values
        })
        
        if 'time' in ds.dims:
            ds_shifted = ds_shifted.assign_coords({'time': ds.time.values})
        
        return ds_shifted
    
    return ds

def process_and_save(ds, var_name, outdir):
    """处理并保存每日数据"""
    
    # 获取数据
    data = ds[var_name]
    
    # 如果有高度层，选择第一层
    if 'level' in data.dims:
        data = data.isel(level=0)
    elif 'isobaricInhPa' in data.dims:
        data = data.isel(isobaricInhPa=0)
    
    # 获取时间
    time_vals = pd.to_datetime(data.time.values)
    unique_dates = time_vals.normalize().unique()
    
    print(f"总天数: {len(unique_dates)}")
    
    # 获取经度纬度
    lats = data.latitude.values
    lons = data.longitude.values
    
    # 逐天处理
    for i, date in enumerate(unique_dates, 1):
        # 选择当天数据
        day_mask = time_vals.normalize() == date
        day_data = data.isel(time=day_mask)
        
        # 转换为数组
        arr = day_data.values
        
        # 如果只有一层时间，添加时间维度
        if arr.ndim == 2:
            arr = arr[np.newaxis, ...]
        
        # 生成日期字符串
        date_str = date.strftime('%Y%m%d')
        
        # 输出文件
        outfile = os.path.join(outdir, f"tcwv_{date_str}.h5")
        
        # 保存为 HDF5
        with h5py.File(outfile, 'w') as f:
            f.create_dataset('tcw', data=arr, compression='gzip', compression_opts=9)
            
            # 添加属性
            f['tcw'].attrs['variable'] = 'Total Column Water Vapour'
            f['tcw'].attrs['unit'] = 'kg/m^2'
            f['tcw'].attrs['date'] = date_str
            f['tcw'].attrs['longitude_range'] = f"{lons.min():.1f}° to {lons.max():.1f}°"
            f['tcw'].attrs['latitude_range'] = f"{lats.min():.1f}° to {lats.max():.1f}°"
            
            # 保存坐标
            f.create_dataset('latitude', data=lats)
            f.create_dataset('longitude', data=lons)
            
            # 保存时间
            if 'time' in day_data.dims:
                time_strs = [str(t) for t in day_data.time.values]
                f.create_dataset('time', data=time_strs)
        
        if i % 30 == 0 or i == len(unique_dates):
            print(f"进度: {i}/{len(unique_dates)} 天")

# ==================== 主程序 ====================

def main():
    print("=" * 70)
    print("ERA5 TCWV 数据转换 - 经度重映射 (0-360 → -180-180)")
    print("=" * 70)
    
    # 1. 读取数据
    print(f"读取文件: {infile}")
    ds = xr.open_dataset(infile, engine='cfgrib')
    
    # 显示原始信息
    print(f"原始经度范围: {ds.longitude.values.min():.1f}° - {ds.longitude.values.max():.1f}°")
    print(f"原始纬度范围: {ds.latitude.values.min():.1f}° - {ds.latitude.values.max():.1f}°")
    
    # 2. 经度重映射
    print("\n正在转换经度格式...")
    ds_shifted = shift_longitude(ds)
    
    # 3. 获取变量名
    var_name = list(ds_shifted.data_vars)[0]
    print(f"处理变量: {var_name}")
    
    # 4. 显示转换后的信息
    print(f"转换后经度范围: {ds_shifted.longitude.values.min():.1f}° - {ds_shifted.longitude.values.max():.1f}°")
    
    # 5. 处理并保存
    print("\n开始处理每日数据...")
    process_and_save(ds_shifted, var_name, outdir)
    
    print("\n" + "=" * 70)
    print("处理完成!")
    print(f"输出目录: {outdir}")
    print("=" * 70)

if __name__ == "__main__":
    main()