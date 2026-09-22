from pathlib import Path
import h5py
import xarray as xr

def grib_to_daily_h5(input_grib, output_root):
    """
    读取 ERA5 GRIB 格式的小时数据，
    将经度从 0-360 转换为 -180 到 180（重排数据），
    按天存为 H5，不保存经纬度坐标。
    """
    print(f"正在尝试打开文件: {input_grib}")

    # 1. 使用 cfgrib 引擎打开
    try:
        ds = xr.open_dataset(
            input_grib,
            engine='cfgrib',
            backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface', 'shortName': 'tcwv'}}
        )
    except Exception as e:
        print(f"读取失败: {e}")
        return

    # 2. 经度转换：从 0-360 转换为 -180 到 180
    print("正在进行经度重排 (0~360 -> -180~180)...")

    # 将 0~360 的数值映射到 -180~180
    ds.coords['longitude'] = (ds.coords['longitude'] + 180) % 360 - 180

    # 关键步骤：根据转换后的经度重新排序数据（否则数据在 0 度经线处会断开）
    # 这会将原始数据右半部分（180-360）移到左边
    ds = ds.sortby('longitude')

    # 3. 按日期分组
    print("开始按天处理数据...")
    groups = ds.tcwv.groupby('time.date')

    for date, daily_data in groups:
        year_str = str(date.year)
        date_str = date.strftime('%Y%m%d')

        # 4. 建立年份目录
        year_dir = Path(output_root) / year_str
        year_dir.mkdir(parents=True, exist_ok=True)

        save_path = year_dir / f"tcwv_{date_str}.h5"

        # 5. 提取数值 (24, lat, lon)
        # 注意：此时的 values 已经是重排后的矩阵
        vals = daily_data.values

        if vals.shape[0] != 24:
            print(f"注意: {date_str} 只有 {vals.shape[0]} 个小时的数据")

        # 6. 保存为 H5 (不保存 lat/lon 数据集)
        with h5py.File(save_path, 'w') as f:
            # 创建数据集并开启压缩
            f.create_dataset('data', data=vals, compression="gzip", compression_opts=4)

            # 添加元数据属性
            f.attrs['date'] = date_str
            f.attrs['unit'] = 'kg m**-2'
            f.attrs['variable'] = 'tcwv'
            f.attrs['longitude_range'] = '-180 to 180'
            f.attrs['dimension_order'] = 'time, latitude, longitude'

        print(f"成功保存: {save_path}")

    ds.close()
    print("所有任务处理完成！")


# --- 运行配置 ---
if __name__ == "__main__":
    # 你的文件路径
    grib_file = "/media/hero/MSG/temp/raw/79c04d6f8667cf7ab5317b4526015ab.grib"
    # 保存结果的根目录
    output_folder = "/media/hero/rs/tcwv"

    grib_to_daily_h5(grib_file, output_folder)
