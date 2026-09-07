import os
from osgeo import gdal
import numpy as np
import glob

def aggregate_block(block, factor, method='average'):
    rows, cols = block.shape
    new_rows = int(np.ceil(rows / factor))
    new_cols = int(np.ceil(cols / factor))
    aggregated_block = np.zeros((new_rows, new_cols), dtype=np.float32)

    for i in range(new_rows):
        for j in range(new_cols):
            row_start = i * factor
            row_end = min((i + 1) * factor, rows)
            col_start = j * factor
            col_end = min((j + 1) * factor, cols)
            sub_block = block[row_start:row_end, col_start:col_end]

            valid_values = sub_block[~np.isnan(sub_block)]
            if valid_values.size > 0:
                aggregated_block[i, j] = np.mean(valid_values)
            else:
                aggregated_block[i, j] = np.nan

    return aggregated_block


def aggregate_to_coarser_resolution(input_file, output_file, factor, method='average'):
    # 打开输入文件
    dataset = gdal.Open(input_file)
    band = dataset.GetRasterBand(1)

    # 获取输入图像的尺寸
    rows = band.YSize
    cols = band.XSize

    # 计算输出图像的尺寸
    new_rows = int(np.ceil(rows / factor))
    new_cols = int(np.ceil(cols / factor))

    # 创建输出文件
    driver = gdal.GetDriverByName('GTiff')
    out_dataset = driver.Create(output_file, new_cols, new_rows, 1, gdal.GDT_Float32)
    out_band = out_dataset.GetRasterBand(1)

    # 聚合数据
    block_size = 1024  # 分块大小
    for i in range(0, rows, block_size):
        for j in range(0, cols, block_size):
            row_end = min(i + block_size, rows)
            col_end = min(j + block_size, cols)
            data_block = band.ReadAsArray(j, i, col_end - j, row_end - i).astype(np.float32)
            data_block[data_block == 101] = np.nan

            aggregated_block = aggregate_block(data_block, factor, method)
            out_band.WriteArray(aggregated_block, int(j / factor), int(i / factor))

    # 设置NoData值
    out_band.SetNoDataValue(np.nan)

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
    vrt_options = gdal.BuildVRTOptions(outputBounds=global_bounds, xRes=global_res, yRes=global_res, srcNodata=np.nan,
                                       VRTNodata=np.nan)
    gdal.BuildVRT(vrt_path, input_files, options=vrt_options)

    # 转换VRT为TIFF
    gdal.Translate(output_file, vrt_path, noData=np.nan)
    os.remove(vrt_path)


# 使用示例
input_folder = 'D:\\data\\Veg_para\\Cnopy_height\\area_tif_0.0025'
output_folder = 'D:\\data\\Veg_para\\Cnopy_height\\aggregated_tif_area'
final_output_file = 'D:\\data\\Veg_para\\Cnopy_height\\global_canopy_height.tif'
factor = int(0.01 / 0.00025)  # 聚合因子

# 批量聚合
batch_aggregate(input_folder, output_folder, factor)

# 拼接成全世界的整图
create_mosaic(output_folder, final_output_file)
