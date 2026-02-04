import os
import glob
from osgeo import gdal
from base.util_data import *
from base.util_lst import *
from base.util_file import *

# ================= 配置参数 =================
input_dir = '/Users/bianzj/Downloads/MCD15A3H_061-20260204_004754'  # HDF 存放目录
ref_tif = '/Users/bianzj/Downloads/data/map/MCD12C1_2011_0.01.tif'  # 你的 0.01 或 0.001 度参考文件
output_dir = '/Users/bianzj/Downloads/data/lai/'  # 输出结果目录
scale_factor = 0.1  # MODIS LAI 的缩放系数

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 1. 获取参考影像的信息 (坐标系、范围、分辨率)
ref_ds = gdal.Open(ref_tif)
ref_proj = ref_ds.GetProjection()
ref_geotrans = ref_ds.GetGeoTransform()
# 获取分辨率和范围，用于 Warp
x_res = ref_geotrans[1]
y_res = abs(ref_geotrans[5])
width = ref_ds.RasterXSize
height = ref_ds.RasterYSize
extent = [
    ref_geotrans[0],
    ref_geotrans[3] + ref_geotrans[5] * height,
    ref_geotrans[0] + ref_geotrans[1] * width,
    ref_geotrans[3]
]

# 2. 搜索所有 HDF 并按日期 (Year + DOY) 归类
# 文件名示例: MCD15A3H.A2017185.h21v03.006.2017191131234.hdf
all_hdf = glob.glob(os.path.join(input_dir, "*.hdf"))
date_dict = {}

for hdf in all_hdf:
    filename = os.path.basename(hdf)
    date_str = filename.split('.')[1]  # 提取 A2017185
    if date_str not in date_dict:
        date_dict[date_str] = []
    date_dict[date_str].append(hdf)

print(f"找到 {len(date_dict)} 个观测日期。开始处理...")

# 3. 循环处理每个日期
for date_str, hdf_files in sorted(date_dict.items()):
    print(f"\n正在处理日期: {date_str} (共 {len(hdf_files)} 个切片)")

    # 提取所有切片的 LAI 子数据集路径
    subdatasets = []
    for h in hdf_files:
        ds = gdal.Open(h)
        # SDS 0 通常是 Lai_500m
        sub = ds.GetSubDatasets()[1]
        subdatasets.append(sub)

    # a. 创建临时虚拟栅格 (VRT) 进行拼接
    vrt_path = os.path.join(output_dir, f"temp_{date_str}.vrt")
    gdal.BuildVRT(vrt_path, subdatasets)

    # b. 使用 Warp 重投影并对齐到参考网格
    # 如果是 0.001°，文件会非常大，开启压缩和 BIGTIFF
    out_name = f"MODIS_LAI_Global_{date_str}.tif"
    out_path = os.path.join(output_dir, out_name)

    warp_options = gdal.WarpOptions(
        format='GTiff',
        dstSRS=ref_proj,
        outputBounds=extent,
        xRes=x_res,
        yRes=y_res,
        resampleAlg='bilinear',  # 适合 LAI 的平滑插值
        dstNodata=255,  # MODIS 的填充值
        outputType=gdal.GDT_Float32,
        creationOptions=['COMPRESS=DEFLATE', 'TILED=YES', 'BIGTIFF=YES']
    )

    # 执行拼接+重采样
    gdal.Warp(out_path, vrt_path, options=warp_options)

    # c. 应用 Scale Factor (0.1)
    # 直接打开刚才生成的 TIF 进行覆盖计算
    ds_final = gdal.Open(out_path, gdal.GA_Update)
    band = ds_final.GetRasterBand(1)
    data = band.ReadAsArray()

    # 仅处理有效范围 (0-100)，其余设为 NaN
    data = np.where(data <= 100, data * scale_factor, np.nan)

    band.WriteArray(data)
    band.SetNoDataValue(np.nan)
    ds_final = None  # 关闭文件，保存修改

    # 清理临时 VRT
    if os.path.exists(vrt_path):
        os.remove(vrt_path)

    print(f"日期 {date_str} 处理完成，输出至: {out_name}")

print("\n[所有日期处理完毕]")