import os
import glob
import re
import numpy as np
import h5py
from osgeo import gdal
from pathlib import Path

# ================= 参数 =================
INPUT_DIR = "/mnt/d/downloads/gcb2025"      # MODIS HDF 文件夹
OUTPUT_ROOT = "/mnt/d/modis_lai/"           # 输出目录
RES = 0.008333333333333                     # 1km 分辨率 (1/120 deg)

gdal.UseExceptions()


# ================= 获取 LAI 子数据集 =================
def get_lai_subset_path(hdf_file):
    """返回包含 'Lai_500m' 的子数据集路径"""
    try:
        ds = gdal.Open(hdf_file)
        if ds is None:
            return None

        for sub in ds.GetSubDatasets():
            if "Lai_500m" in sub[0]:
                return sub[0]

    except Exception as e:
        print(f"子数据集读取失败: {hdf_file} -> {e}")

    return None


# ================= 主处理函数 =================
def process_lai_mosaic_standard_cycle():

    all_hdf_files = glob.glob(os.path.join(INPUT_DIR, "*.hdf"))

    if not all_hdf_files:
        print(f"错误: 未发现 HDF 文件 -> {INPUT_DIR}")
        return

    # 自动识别所有年份
    available_years = sorted(list(set([
        re.search(r'A(\d{4})', os.path.basename(f)).group(1)
        for f in all_hdf_files
        if re.search(r'A(\d{4})', os.path.basename(f))
    ])))

    print("检测到年份:", available_years)

    # 标准 4 天周期
    standard_doys = [f"{d:03d}" for d in range(1, 367, 4)]

    # ================= 按年循环 =================
    for year_str in ["2022"]:

        print(f"\n========== 开始处理年份 {year_str} ==========")

        year_dir = Path(OUTPUT_ROOT) / year_str
        year_dir.mkdir(parents=True, exist_ok=True)

        # ================= 按 DOY 循环 =================
        for doy_str in ["057"]:

            date_key = f"{year_str}{doy_str}"
            output_h5 = year_dir / f"lai_{date_key}.h5"

            if output_h5.exists():
                print(f"跳过已存在: {output_h5.name}")
                continue

            pattern = os.path.join(INPUT_DIR, f"*A{date_key}*.hdf")
            current_tiles = glob.glob(pattern)

            if not current_tiles:
                continue

            print(f"\n--- 拼接 {date_key} | 瓦片数: {len(current_tiles)} ---")

            # 获取所有 LAI 子数据集
            subsets = []
            for f in current_tiles:
                sub_path = get_lai_subset_path(f)
                if sub_path:
                    subsets.append(sub_path)

            if not subsets:
                print(f"警告: {date_key} 未找到 Lai_500m")
                continue

            try:
                # 使用临时 VRT 文件避免内存暴涨
                vrt_path = "/vsimem/temp.vrt"

                gdal.Warp(
                    vrt_path,
                    subsets,
                    format='VRT',
                    dstSRS='EPSG:4326',
                    outputBounds=[-180, -90, 180, 90],
                    xRes=RES,
                    yRes=RES,
                    resampleAlg=gdal.GRA_Bilinear,
                    srcNodata=255,
                    dstNodata=255,
                    multithread=True
                )

                vrt = gdal.Open(vrt_path)
                data = vrt.ReadAsArray()

                # 保存 H5
                with h5py.File(output_h5, 'w') as f_h5:

                    dset = f_h5.create_dataset(
                        'data',
                        data=data,
                        compression="gzip",
                        compression_opts=4,
                        dtype='uint8'
                    )

                    # 元数据
                    f_h5.attrs['product'] = "MCD15A3H/A2H Standard 4-day Cycle"
                    f_h5.attrs['date_yyyydoy'] = date_key
                    f_h5.attrs['resolution'] = "1km (0.00833 deg)"
                    f_h5.attrs['scale_factor'] = 0.1
                    f_h5.attrs['longitude_range'] = "-180 to 180"
                    f_h5.attrs['shape'] = data.shape

                print(f"成功保存: {output_h5.name}")

                # 释放内存
                vrt = None
                data = None
                gdal.Unlink(vrt_path)

            except Exception as e:
                print(f"拼接失败 {date_key}: {e}")


# ================= 运行 =================
if __name__ == "__main__":
    process_lai_mosaic_standard_cycle()
