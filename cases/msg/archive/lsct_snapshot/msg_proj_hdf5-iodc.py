import os
import glob
import numpy as np
import rasterio
import h5py
from osgeo import gdal, osr
from pyresample import geometry, kd_tree
from rasterio.transform import from_bounds

# ================= 配置区域 =================

input_root0 = "/Users/bianzj/Downloads/data/msg/PRODUCTS/MSG-IODC/MLAI/HDF5/"
output_root0 = "/Users/bianzj/Downloads/data/msg/PRODUCTS/MSG-IODC/MLAI/GEOTIFF/"
target_var = 'LST'
input_root0 = "/mnt/h/PRODUCTS/MSG-IODC/MLST/HDF5/"
output_root0 = "/mnt/h/PRODUCTS/MSG-IODC/MLST/GEOTIFF/"


# ！！！重要提示：
# 如果 HDF5 是全圆盘 (3712x3712)，这两个 TIF 也必须是 3712x3712。
# 如果 TIF 是 3201 大小，请更换为全圆盘对应的经纬度文件。
lat_path = "/mnt/h/msg/Static/IODC_Lat.tif"
lon_path = "/mnt/h/msg/Static/IODC_Lon.tif"

def load_static_latlon(lat_p, lon_p):
    """读取静态经纬度并处理翻转"""
    with rasterio.open(lat_p) as src:
        lat = src.read(1).astype(np.float32)
        if np.nanmax(lat) > 90: lat /= 100.0
    with rasterio.open(lon_p) as src:
        lon = src.read(1).astype(np.float32)
        if np.nanmax(lon) > 180: lon /= 100.0
    # 根据用户经验进行上下翻转
    lat = np.flipud(lat)
    return lat, lon

src_lat, src_lon = load_static_latlon(lat_path, lon_path)

# 目标区域 (WGS84)
res = 0.03
area_extent = (-18.0, -35.0, 61.0, 65.0)


# ===========================================

def write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff',
                     nodata_value=None):
    if hasattr(im_trans, 'to_gdal'):
        im_trans = im_trans.to_gdal()

    if isinstance(im_proj, str) and im_proj.startswith('EPSG:'):
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(int(im_proj.split(':')[-1]))
        im_proj = srs.ExportToWkt()

    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    else:
        im_data = np.array([im_data])
        im_bands = 1
        im_height, im_width = im_data.shape[1], im_data.shape[2]

    dtype_name = im_data.dtype.name.lower()
    if 'uint16' in dtype_name:
        datatype = gdal.GDT_UInt16
        default_nodata = 0
    elif 'float32' in dtype_name:
        datatype = gdal.GDT_Float32
        default_nodata = -9999.0
    else:
        datatype = gdal.GDT_Float32
        default_nodata = -9999.0

    if nodata_value is None:
        nodata_value = default_nodata

    driver = gdal.GetDriverByName(imageType)
    dataset = driver.Create(path, im_width, im_height, im_bands, datatype,
                            options=['COMPRESS=LZW', 'PREDICTOR=2', 'TILED=YES'])

    if dataset is not None:
        dataset.SetGeoTransform(im_trans)
        dataset.SetProjection(im_proj)
        for i in range(im_bands):
            band = dataset.GetRasterBand(i + 1)
            band.WriteArray(im_data[i])
            # 处理 NaN 情况
            if isinstance(nodata_value, float) and np.isnan(nodata_value):
                band.SetNoDataValue(-9999.0)
            else:
                band.SetNoDataValue(float(nodata_value))
            band.FlushCache()
    del dataset
    return 1




def process_monthly_hdf5_to_tif(input_root, output_root):
    # 1. 设置目标区域几何信息

    # 3. 递归遍历 HDF5 文件
    # 匹配所有 HDF5 开头的文件
    h5_files = sorted(glob.glob(os.path.join(input_root, "HDF5*"), recursive=False))
    print(f"找到 {len(h5_files)} 个 HDF5 文件，开始处理整点数据...")

    width = int((area_extent[2] - area_extent[0]) / res)
    height = int((area_extent[3] - area_extent[1]) / res)
    target_area = geometry.AreaDefinition(
        'common_area', 'Lat-Lon Grid', 'wgs84',
        {'proj': 'longlat', 'datum': 'WGS84'},
        width, height, area_extent
    )
    transform = from_bounds(*area_extent, width, height)
    proj_wgs84 = 'EPSG:4326'

    # 2. 加载源经纬度

    src_swath = geometry.SwathDefinition(lons=src_lon, lats=src_lat)
    print(f"源经纬度加载完成，形状: {src_lat.shape}")



    for h5_path in h5_files:
        filename = os.path.basename(h5_path)

        # 过滤整点数据：文件名倒数第4,5位是00 (或者后缀前是00)
        # 示例: ..._201708100400.h5
        name_part = os.path.splitext(filename)[0]
        if not name_part.endswith("00"):
            continue

        try:
            # 提取日期以创建文件夹: 201708100400 -> 10 (日)
            timestamp = name_part.split('_')[-1]
            day_str = timestamp[6:8]
        except:
            continue

        out_folder = os.path.join(output_root)
        os.makedirs(out_folder, exist_ok=True)
        out_tif_path = os.path.join(out_folder, name_part + ".tif")

        if os.path.exists(out_tif_path):
            continue

        # 4. 读取 HDF5 数据
        try:
            with h5py.File(h5_path, 'r') as f:
                # 获取 LST 变量
                if target_var not in f:
                    print(f"跳过 {filename}: 未找到 LST 变量")
                    continue

                ds_lst = f[target_var]
                raw_data = ds_lst[:]  # 原始数据通常是 int16

                # 获取元数据 (LSA SAF 规范)
                missing_val = ds_lst.attrs.get('MISSING_VALUE', -8000)
                # 如果你想保存物理值(Kelvin)，需要乘 SCALING_FACTOR (通常是 0.1)
                # 如果想保存 int16 (Kelvin*10) 以节省空间，则直接处理空值

                # 处理无效值：将 -8000 转为 0，方便保存为 uint16
                raw_data_clean = raw_data.astype(np.float32)
                raw_data_clean[raw_data == missing_val] = np.nan

            # 形状检查
            if raw_data_clean.shape != src_lat.shape:
                print(f"跳过 {filename}: 形状不匹配 ({raw_data_clean.shape} vs {src_lat.shape})")
                continue

            # 5. 重采样
            print(f"正在重采样: {filename}")
            # 使用 float32 重采样以处理 NaN
            resampled = kd_tree.resample_nearest(
                src_swath, raw_data_clean, target_area,
                radius_of_influence=5000, fill_value=np.nan
            )

            # 6. 保存结果
            # 方案 A: 如果你想保存 Kelvin*10 整数 (省空间)
            # 将 NaN 转回 0，转为 uint16
            final_data = np.nan_to_num(resampled, nan=0).astype(np.uint16)
            save_nodata = 0

            # 方案 B: 如果你想保存 物理开尔文温度 (带小数)
            # final_data = resampled.astype(np.float32)
            # save_nodata = np.nan

            write_image_gdal(
                im_data=final_data,
                im_width=width,
                im_height=height,
                im_bands=1,
                im_trans=transform,
                im_proj=proj_wgs84,
                path=out_tif_path,
                nodata_value=save_nodata
            )

        except Exception as e:
            print(f"处理文件 {filename} 失败: {e}")

    print("所有整点数据处理完成！")


if __name__ == "__main__":

    for kyear in range(2017, 2018):
        for kmonth in range(1, 13):
            for kday in range(1, 32):

                if (kyear, kmonth, kday) > (2022, 6, 1):
                    continue

                input_root = input_root0 + "/%04d/" % kyear + "/%02d/" % kmonth + "/%02d/" % kday
                output_root = output_root0 + "/%04d/" % kyear + "/%02d/" % kmonth + "/%02d/" % kday
                print(input_root)
                process_monthly_hdf5_to_tif(input_root,output_root)