import os
from osgeo import gdal
import numpy as np
import glob


def aggregate_to_coarser_resolution(input_file, output_file, factor, method='average'):
    # 打开输入文件
    dataset = gdal.Open(input_file)
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()

    # 获取输入图像的尺寸
    rows, cols = data.shape

    # 计算输出图像的尺寸
    new_rows = int(np.ceil(rows / factor))
    new_cols = int(np.ceil(cols / factor))

    # 初始化输出数据
    aggregated_data = np.zeros((new_rows, new_cols), dtype=np.float32)

    # 聚合数据
    for i in range(new_rows):
        for j in range(new_cols):
            row_start = i * factor
            row_end = min((i + 1) * factor, rows)
            col_start = j * factor
            col_end = min((j + 1) * factor, cols)
            block = data[row_start:row_end, col_start:col_end]

            if method == 'average':
                aggregated_data[i, j] = np.mean(block)
            else:
                raise ValueError(f"Unsupported method: {method}")

    # 创建输出文件
    driver = gdal.GetDriverByName('GTiff')
    out_dataset = driver.Create(output_file, new_cols, new_rows, 1, band.DataType)
    out_band = out_dataset.GetRasterBand(1)
    out_band.WriteArray(aggregated_data)

    # 设置地理参考
    geotransform = list(dataset.GetGeoTransform())
    geotransform[1] *= factor
    geotransform[5] *= factor
    out_dataset.SetGeoTransform(geotransform)
    out_dataset.SetProjection(dataset.GetProjection())

    # 关闭数据集
    dataset = None
    out_dataset = None
    print(f"Aggregation completed. Output saved to {output_file}")


def batch_aggregate(input_folder, output_folder, factor):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    input_files = glob.glob(os.path.join(input_folder, "*.tif"))

    for input_file in input_files:
        output_file = os.path.join(output_folder, os.path.basename(input_file))
        aggregate_to_coarser_resolution(input_file, output_file, factor)


def create_mosaic(input_folder, output_file):
    input_files = glob.glob(os.path.join(input_folder, "*.tif"))
    vrt_path = os.path.join(input_folder, "mosaic.vrt")

    # 设置全球范围
    global_bounds = [-180, -90, 180, 90]  # [min_longitude, min_latitude, max_longitude, max_latitude]
    global_res = 0.01  # 输出分辨率

    # 计算全球范围内的行列数
    x_res = int((global_bounds[2] - global_bounds[0]) / global_res)
    y_res = int((global_bounds[3] - global_bounds[1]) / global_res)

    # 创建虚拟文件（VRT）
    vrt_options = gdal.BuildVRTOptions(outputBounds=global_bounds, xRes=global_res, yRes=global_res)
    gdal.BuildVRT(vrt_path, input_files, options=vrt_options)

    # 转换VRT为TIFF
    gdal.Translate(output_file, vrt_path)
    os.remove(vrt_path)


# 使用示例
input_folder = 'D:\\data\\Veg_para\\Tree_cover(TCC)\\tif_area'
output_folder = 'D:\\data\\Veg_para\\Tree_cover(TCC)\\aggregated_tif_area'
final_output_file = 'D:\\data\\Veg_para\\Tree_cover(TCC)\\global_treecover.tif'
factor = int(0.01 / 0.00025)  # 聚合因子

# 批量聚合
# batch_aggregate(input_folder, output_folder, factor)

# 拼接成全世界的整图
create_mosaic(output_folder, final_output_file)
