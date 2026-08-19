import rasterio
import numpy as np

from pyresample import geometry, kd_tree
from rasterio.transform import from_bounds
from base.util_data import *

def write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff',
                     nodata_value=None):
    # --- 修正 1: 处理 Rasterio Affine 对象 ---
    # 如果 im_trans 是 rasterio.Affine 类型，需要转为 GDAL 格式
    if hasattr(im_trans, 'to_gdal'):
        im_trans = im_trans.to_gdal()
        # 如果是 [a, b, c, d, e, f] 这种 Affine 序列，gdal 需要的是 [c, a, b, f, d, e]
    # 但 to_gdal() 会自动帮你排好顺序为 (c, a, b, f, d, e)

    # --- 修正 2: 处理 Projection ---
    if isinstance(im_proj, str) and im_proj.startswith('EPSG:'):
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(int(im_proj.split(':')[-1]))
        im_proj = srs.ExportToWkt()

    # 处理输入参数冲突
    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    elif len(im_data.shape) == 2:
        im_data = np.array([im_data])
        im_bands = 1
    else:
        im_data = np.array([im_data])
        im_bands = 1
        im_height, im_width = im_data.shape[1], im_data.shape[2] if im_data.ndim > 2 else im_data.shape[1]

    # 自动检测数据类型
    im_bands = int(im_bands)
    im_height = int(im_height)
    im_width = int(im_width)
    dtype_name = im_data.dtype.name.lower()  # 统一转小写判断

    if 'uint8' in dtype_name or 'int8' in dtype_name:
        datatype = gdal.GDT_Byte
        default_nodata = 255
    elif 'uint16' in dtype_name:  # 修正大小写
        datatype = gdal.GDT_UInt16
        default_nodata = 0
    elif 'int16' in dtype_name:
        datatype = gdal.GDT_Int16
        default_nodata = -32768
    elif 'uint32' in dtype_name:
        datatype = gdal.GDT_UInt32
        default_nodata = 0
    elif 'int32' in dtype_name:
        datatype = gdal.GDT_Int32
        default_nodata = -2147483648
    elif 'float32' in dtype_name:
        datatype = gdal.GDT_Float32
        default_nodata = np.nan
    elif 'float64' in dtype_name:
        datatype = gdal.GDT_Float64
        default_nodata = np.nan
    else:
        datatype = gdal.GDT_Float32
        default_nodata = np.nan

    if nodata_value is None:
        nodata_value = default_nodata

    driver = gdal.GetDriverByName(imageType)
    dataset = driver.Create(path, im_width, im_height, im_bands, datatype
                            ,options=['COMPRESS=LZW', 'PREDICTOR=2', 'TILED=YES'])

    if dataset is not None:
        if im_trans is not None and im_trans != '':
            dataset.SetGeoTransform(im_trans)
        if im_proj is not None and im_proj != '':
            dataset.SetProjection(im_proj)

        for i in range(im_bands):
            band = dataset.GetRasterBand(i + 1)
            band.WriteArray(im_data[i])
            if not (isinstance(nodata_value, float) and np.isnan(nodata_value)):
                band.SetNoDataValue(nodata_value)
            else:
                band.SetNoDataValue(-9999)  # 对于NaN，TIFF通常建议设置一个物理掩码值
            band.FlushCache()
            band.ComputeStatistics(False)
    del dataset
    return 1



def load_tif(file_path):
    with rasterio.open(file_path) as src:
        # 读取数据并转换为 float32，方便处理 NaN
        data = src.read(1).astype(np.float32)
        # 假设 0 或小于 0 的值是太空/无效区域，统一设为 NaN
        # data[data <= 0] = np.nan
        return data

# --- 文件路径 ---
# EURO
infile1_euro = "/Users/bianzj/Downloads/data/msg/euro_tif/2017/07/01/MSG3-SEVI-MSG15-0100-NA-20170701122739.750000000Z-NA.nat_bt8.tif"
infile1_euro = "/Users/bianzj/Downloads/data/msg/Static/MSG_VAA"
infile2_euro = "/Users/bianzj/Downloads/data/msg/Static/EURO_lat.tif"
infile3_euro = "/Users/bianzj/Downloads/data/msg/Static/EURO_lon.tif"


# IODC
infile1_iodc = "/Users/bianzj/Downloads/data/msg/iodc_tif/2017/07/01/MSG1-SEVI-MSG15-0100-NA-20170701122743.677000000Z-NA.nat_bt8.tif"
infile1_iodc = "/Users/bianzj/Downloads/data/msg/Static/MSG_VAA"
infile2_iodc = "/Users/bianzj/Downloads/data/msg/Static/IODC_lat.tif"
infile3_iodc = "/Users/bianzj/Downloads/data/msg/Static/IODC_lon.tif"

outfile = "/Users/bianzj/Downloads/data/msg/Static/combined_euro_vaa.tif"
outfile1 = "/Users/bianzj/Downloads/data/msg/Static/combined_iodc_vaa.tif"

# --- 1. 读取并预处理数据 ---
print("读取数据中...")
euro_bt = load_tif(infile1_euro)
euro_lat = load_tif(infile2_euro) / 100.0
euro_lon = load_tif(infile3_euro) / 100.0

iodc_bt = load_tif(infile1_iodc)
iodc_lat = load_tif(infile2_iodc) / 100.0
iodc_lon = load_tif(infile3_iodc) / 100.0


# iodc_lon = np.fliplr(iodc_lon)
# euro_lon = np.fliplr(euro_lon)
iodc_lat = np.flipud(iodc_lat)
euro_lat = np.flipud(euro_lat)

# --- 2. 定义几何形状 ---
euro_swath = geometry.SwathDefinition(lons=euro_lon, lats=euro_lat)
iodc_swath = geometry.SwathDefinition(lons=iodc_lon, lats=iodc_lat)

# --- 3. 定义目标区域 (WGS84) ---
res = 0.03  # 设置你想要的分辨率（单位：度）。0.03度约等于 3.3km
area_extent = (-18.0, -35.0, 61.0, 65.0) # (西, 南, 东, 北)

# 根据范围和分辨率计算宽度和高度
width = int((area_extent[2] - area_extent[0]) / res)
height = int((area_extent[3] - area_extent[1]) / res)

print(f"目标图像尺寸: 宽 {width}, 高 {height}")

target_area = geometry.AreaDefinition(
    'common_area', 'Lat-Lon Grid', 'wgs84',
    {'proj': 'longlat', 'datum': 'WGS84'},
    width, height, area_extent
)

# --- 4. 重采样 ---
print("正在重采样 EURO...")
euro_resampled = kd_tree.resample_nearest(
    euro_swath, euro_bt, target_area,
    radius_of_influence=5000, fill_value=np.nan
)

print("正在重采样 IODC...")
iodc_resampled = kd_tree.resample_nearest(
    iodc_swath, iodc_bt, target_area,
    radius_of_influence=5000, fill_value=np.nan
)

# --- 5. 合并图像 ---
print("正在合并图像...")
# 使用 fmax 可以忽略 NaN，在重叠区取两者的最大值（或者用 np.where 选其一）
# combined = np.where(~np.isnan(euro_resampled), euro_resampled, iodc_resampled)

# 准备写入的数据：三个波段 (1.合并结果, 2.EURO原文, 3.IODC原文)
result = np.array([euro_resampled, iodc_resampled], dtype=np.int16)

# --- 6. 保存结果 ---
transform = from_bounds(*area_extent, width, height)

# 2. 转换 Transform：将 rasterio 的 Affine 对象转为 GDAL 的 6 参数元组
# transform.to_gdal() 返回顺序为: (c, a, b, f, d, e)，即 (左上x, 分辨率x, 旋转x, 左上y, 旋转y, 分辨率y)
gdal_trans = transform.to_gdal()

# 3. 转换 Projection：将 'EPSG:4326' 字符串转为 GDAL 要求的 WKT 格式
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)
gdal_proj = srs.ExportToWkt()

# with rasterio.open(
#     outfile, 'w',
#     driver='GTiff',
#     height=height,
#     width=width,
#     count=2,             # 修正为 2
#     dtype='uint16',      # 修正字符串格式
#     crs='EPSG:4326',     # 推荐使用 EPSG 编码更稳定
#     transform=transform,
#     nodata=0             # uint16 必须用整数作为 nodata（常用 0 或 65535）
# ) as dst:
#     dst.write(result.astype('uint16'))
#
# print(f"完成！结果已保存至: {outfile}")




write_image_gdal(euro_resampled.astype('int16'),width,height,1,gdal_trans,gdal_proj,outfile)
write_image_gdal(iodc_resampled.astype('int16'),width,height,1,gdal_trans,gdal_proj,outfile1)