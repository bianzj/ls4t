import os
import numpy as np
import h5py
from osgeo import gdal
import glob
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")

# 基础路径配置
base_dir = "/media/hero/earth/ERA5_Daily_H5"
output_base_dir = "/media/hero/earth/ERA5_Daily_H5_Reorganized"  # 输出目录

# 年份范围
start_year = 2002
end_year = 2017

# 创建输出目录
os.makedirs(output_base_dir, exist_ok=True)


def read_tiff(file_path):
    """读取 TIFF 文件并返回 numpy 数组"""
    ds = gdal.Open(file_path)
    if ds is None:
        return None
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    ds = None
    return data


def get_files_for_day(year, day_of_year):
    """获取某一天的所有小时文件路径"""
    # 文件格式: ERA5_tcw_{year}_{doy:03d}_{hour:02d}.tif
    hour_files = []
    for hour in range(24):
        file_pattern = f"ERA5_tcw_{year}_{day_of_year:03d}_{hour:02d}.tif"
        file_path = os.path.join(base_dir, str(year), f"{day_of_year:03d}", file_pattern)
        if os.path.exists(file_path):
            hour_files.append(file_path)
        else:
            # 尝试补零格式
            file_pattern_alt = f"ERA5_tcw_{year}_{day_of_year:03d}_{hour:02d}_00.tif"
            file_path_alt = os.path.join(base_dir, str(year), f"{day_of_year:03d}", file_pattern_alt)
            if os.path.exists(file_path_alt):
                hour_files.append(file_path_alt)
    return hour_files


def get_year_days(year):
    """获取某年的总天数（考虑闰年）"""
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        return 366
    return 365


def process_year(year):
    """处理一年的数据"""
    print(f"\n开始处理 {year} 年...")

    year_dir = os.path.join(base_dir, str(year))
    if not os.path.exists(year_dir):
        print(f"  警告: {year} 年目录不存在，跳过")
        return

    # 获取该年的天数
    total_days = get_year_days(year)

    # 创建年份输出目录
    output_year_dir = os.path.join(output_base_dir, str(year))
    os.makedirs(output_year_dir, exist_ok=True)

    # 先读取第一天的第一个文件获取经纬度信息
    first_day_files = get_files_for_day(year, 1)
    if not first_day_files:
        print(f"  错误: 无法读取 {year} 年的数据，跳过")
        return

    # 读取第一个文件获取尺寸
    sample_data = read_tiff(first_day_files[0])
    if sample_data is None:
        print(f"  错误: 无法读取样本文件 {first_day_files[0]}")
        return

    rows, cols = sample_data.shape
    print(f"  数据尺寸: {rows} x {cols}")

    success_count = 0

    # 逐天处理
    for doy in range(1, total_days + 1):
        # 获取当天的小时文件
        hour_files = get_files_for_day(year, doy)

        # 如果当天没有文件，跳过
        if not hour_files:
            continue

        # 读取所有小时数据
        daily_data = []
        valid_hours = 0

        for hour_file in hour_files:
            data = read_tiff(hour_file)
            if data is not None:
                daily_data.append(data)
                valid_hours += 1

        # 如果没有任何有效数据，跳过
        if valid_hours == 0:
            continue

        # 将小时数据堆叠为 3D 数组 (时间, 行, 列)
        # 如果有24小时，shape = (24, rows, cols)
        # 如果不足24小时，也保持实际数量
        daily_array = np.stack(daily_data, axis=0)

        # 计算日期字符串 (YYYYMMDD)
        date = datetime(year, 1, 1) + timedelta(days=doy - 1)
        date_str = date.strftime('%Y%m%d')

        # 输出文件名
        outfile = os.path.join(output_year_dir, f"tcwv_{date_str}.h5")

        # 写入 HDF5
        with h5py.File(outfile, 'w') as f:
            # 存储数据
            f.create_dataset('tcw', data=daily_array, compression='gzip')

            # 添加属性
            f['tcw'].attrs['variable'] = 'Total Column Water Vapour'
            f['tcw'].attrs['unit'] = 'kg/m^2'
            f['tcw'].attrs['date'] = date_str
            f['tcw'].attrs['year'] = year
            f['tcw'].attrs['day_of_year'] = doy
            f['tcw'].attrs['hours'] = valid_hours
            f['tcw'].attrs['dimensions'] = f"time({valid_hours}) x rows({rows}) x cols({cols})"

            # 可选：保存地理信息（如果可以从 GDAL 获取）
            ds = gdal.Open(hour_files[0])
            if ds:
                # 保存地理变换参数
                geo_transform = ds.GetGeoTransform()
                if geo_transform:
                    f['tcw'].attrs['geo_transform'] = geo_transform
                # 保存投影信息
                projection = ds.GetProjection()
                if projection:
                    f['tcw'].attrs['projection'] = projection
                ds = None

        success_count += 1

        # 进度显示
        if success_count % 30 == 0 or success_count == total_days:
            print(f"  已处理: {success_count}/{total_days} 天")

    print(f"  完成 {year} 年，成功处理 {success_count} 天")


# 主程序
def main():
    print("=" * 60)
    print("开始重组 ERA5 TCWV 数据 (从小时 TIFF 到每日 HDF5)")
    print(f"输入目录: {base_dir}")
    print(f"输出目录: {output_base_dir}")
    print(f"年份范围: {start_year} - {end_year}")
    print("=" * 60)

    # 处理所有年份
    for year in range(start_year, end_year + 1):
        process_year(year)

    print("\n" + "=" * 60)
    print("所有年份处理完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()