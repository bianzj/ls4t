from osgeo import gdal
import os

# 输入文件和输出文件路径
input_file = r"D:\data\Veg_para\Tree_density(STD)\raw\Crowther_Nature_Files_Revision_01_WGS84_GeoTiff\Crowther_Nature_Files_Revision_01_WGS84_GeoTiff\Crowther_Nature_Biome_Revision_01_WGS84_GeoTiff.tif"
output_file = r"D:\data\Veg_para\Tree_density(STD)\global_TreeDensity_0.01.tif"

# 打开输入文件
src_ds = gdal.Open(input_file)
src_proj = src_ds.GetProjection()

# 定义输出的范围和分辨率
dst_res = 0.01
xmin, ymin, xmax, ymax = -180.0, -90.0, 180.0, 90.0
dst_width = int((xmax - xmin) / dst_res)
dst_height = int((ymax - ymin) / dst_res)

# 创建输出文件
driver = gdal.GetDriverByName('GTiff')
dst_ds = driver.Create(output_file, dst_width, dst_height, 1, gdal.GDT_Float32)
dst_ds.SetGeoTransform([xmin, dst_res, 0, ymax, 0, -dst_res])
dst_ds.SetProjection(src_proj)

# 执行重采样
gdal.ReprojectImage(src_ds, dst_ds, src_proj, src_proj, gdal.GRA_Average)

# 关闭数据集
src_ds = None
dst_ds = None

print("重采样完成并保存到:", output_file)
