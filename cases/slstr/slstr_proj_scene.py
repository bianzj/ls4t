from osgeo import gdal
from base.lsct import ndvi_max_g, ndvi_min_g
from base.slstr.slstr_grid import nl_nadir_g, nl_obliq_g, ns_nadir_g, ns_obliq_g

import sys
import os

import numpy as np

import time
import math
import warnings
warnings.filterwarnings("ignore")

def write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff',
                     nodata_value=None):
    '''
    保存数据，输出成tif格式
    :param im_data: 数组
    :param im_width: 列数
    :param im_height: 行数
    :param im_bands: 波段数
    :param im_trans: 地理坐标
    :param im_proj: 投影坐标
    :param path: 路径
    :param imageType: 输出格式（字符串，如'GTiff'）
    :param nodata_value: nodata值（可选）
    :return: 无
    '''
    # 处理输入参数冲突
    if len(im_data.shape) == 3:
        # 如果输入是3D数组，忽略输入的im_bands, im_height, im_width参数
        im_bands, im_height, im_width = im_data.shape
    elif len(im_data.shape) == 2:
        # 如果输入是2D数组，转换为3D
        im_data = np.array([im_data])
        im_bands = 1
        # 使用输入的尺寸参数
    else:
        # 1D数组或其他情况
        im_data = np.array([im_data])
        im_bands = 1
        im_height, im_width = im_data.shape[1], im_data.shape[2] if im_data.ndim > 2 else im_data.shape[1]

    # 自动检测数据类型
    dtype_name = im_data.dtype.name
    if 'uint8' in dtype_name or 'int8' in dtype_name:
        datatype = gdal.GDT_Byte
        default_nodata = 255
    elif 'Uint16' in dtype_name:
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
        # 默认使用Float32
        datatype = gdal.GDT_Float32
        default_nodata = np.nan

    # 设置nodata值
    if nodata_value is None:
        nodata_value = default_nodata

    # 创建数据集
    driver = gdal.GetDriverByName(imageType)
    dataset = driver.Create(path, im_width, im_height, im_bands, datatype)

    if dataset is not None:
        # 设置地理信息和投影
        if im_trans is not None and im_trans != '':
            dataset.SetGeoTransform(im_trans)
        if im_proj is not None and im_proj != '':
            dataset.SetProjection(im_proj)

        # 写入数据并设置nodata值
        for i in range(im_bands):
            band = dataset.GetRasterBand(i + 1)
            band.WriteArray(im_data[i])

            # 设置nodata值
            if not (isinstance(nodata_value, float) and np.isnan(nodata_value)):
                band.SetNoDataValue(nodata_value)
            else:
                # 对于NaN，需要特殊处理
                band.SetNoDataValue(nodata_value)

            # 可选：设置统计信息
            band.FlushCache()
            band.ComputeStatistics(False)

    # 清理
    del dataset
    return 1


def writevrt_nadir(infile, datafile, xfile, yfile, data_type="UInt16", nodata_value=0):
    write_vrt(infile, datafile, xfile, yfile, ns_nadir_g, nl_nadir_g,
              data_type=data_type, nodata_value=nodata_value)
    return 1


def writevrt_obliq(infile, datafile, xfile, yfile, data_type="UInt16", nodata_value=0):
    write_vrt(infile, datafile, xfile, yfile, ns_obliq_g, nl_obliq_g,
              data_type=data_type, nodata_value=nodata_value)
    return 1


def write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale,
              bandnumber=1, data_type="UInt16",
              pixel_offset=0, pixel_step=1, line_offset=0, line_step=1,
              nodata_value=0, use_nan_for_float=False):
    '''
    智能处理nodatavalue的VRT生成函数

    :param nodata_value: 显式指定nodata值，如果为None则自动选择
    :param use_nan_for_float: 浮点类型是否使用NaN作为nodata
    :return: 成功返回1
    '''

    # 数据类型映射
    type_info = {
        "Byte": {"range": (0, 255), "default_nodata": 255},
        "UInt16": {"range": (0, 65535), "default_nodata": 0},
        "UInt32": {"range": (0, 4294967295), "default_nodata": 0},
        "Int16": {"range": (-32768, 32767), "default_nodata": -32768},
        "Int32": {"range": (-2147483648, 2147483647), "default_nodata": -2147483648},
        "Float32": {"range": None, "default_nodata": "nan"},
        "Float64": {"range": None, "default_nodata": "nan"}
    }

    # 验证数据类型
    if data_type not in type_info:
        raise ValueError(f"不支持的数据类型: {data_type}")

    # 智能选择nodata值
    if nodata_value is None:
        if data_type in ["Float32", "Float64"] and use_nan_for_float:
            nodata_str = "nan"
        else:
            nodata_str = str(type_info[data_type]["default_nodata"])
    else:
        nodata_str = str(nodata_value)

    # 构建VRT内容
    vrt_content = [
        f'<VRTDataset rasterXSize="{xscale}" rasterYSize="{yscale}">',
        '  <Metadata domain="GEOLOCATION">',
        '    <MDI key="SRS">GEOGCS["WGS 84(DD)",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AXIS["Long",EAST],AXIS["Lat",NORTH]]</MDI>',
        f'    <MDI key="X_DATASET">{xfile}</MDI>',
        '    <MDI key="X_BAND">1</MDI>',
        f'    <MDI key="PIXEL_OFFSET">{pixel_offset}</MDI>',
        f'    <MDI key="PIXEL_STEP">{pixel_step}</MDI>',
        f'    <MDI key="Y_DATASET">{yfile}</MDI>',
        '    <MDI key="Y_BAND">1</MDI>',
        f'    <MDI key="LINE_OFFSET">{line_offset}</MDI>',
        f'    <MDI key="LINE_STEP">{line_step}</MDI>',
        '  </Metadata>',
        f'  <VRTRasterBand dataType="{data_type}" band="{bandnumber}">',
        '    <ColorInterp>Gray</ColorInterp>',
        f'    <NoDataValue>{nodata_str}</NoDataValue>',
        '    <SimpleSource>',
        f'      <SourceFilename relativeToVRT="1">{datafile}</SourceFilename>',
        '      <SourceBand>1</SourceBand>',
        '    </SimpleSource>',
        '  </VRTRasterBand>',
        '</VRTDataset>'
    ]

    # 写入文件
    with open(vrtfile, 'w', encoding='utf-8') as f:
        f.write('\n'.join(vrt_content))

    return 1


def scale_and_convert_to_uint16(data, scale_factor, clip_range=(0, 65535)):
    """
    缩放数据并转换为UInt16
    :param data: 输入数据
    :param scale_factor: 缩放因子
    :param clip_range: 裁剪范围
    :return: UInt16数据
    """
    scaled_data = data * scale_factor

    # 处理NaN和无效值
    scaled_data = np.where(np.isnan(scaled_data), 0, scaled_data)
    scaled_data = np.where(np.isinf(scaled_data), 0, scaled_data)

    # 裁剪到UInt16范围
    scaled_data = np.clip(scaled_data, clip_range[0], clip_range[1])

    # 转换为UInt16
    return scaled_data.astype(np.uint16)



if __name__ == '__main__':
    ndvi_min = ndvi_min_g
    ndvi_max = ndvi_max_g


    temp_folder1 = '/media/hero/slstr-euro/2021/tif/S3A_SL_1_RBT____20210101T214029_20210101T214329_20210103T042231_0180_067_016_0540_LN2_O_NT_004.SEN3/'
    temp_folder2 = '/media/hero/slstr-euro/2021/tif/S3A_SL_1_RBT____20210101T214029_20210101T214329_20210103T042231_0180_067_016_0540_LN2_O_NT_004.SEN3/'
    output_folder = temp_folder2

    file = 'bt8_nadir'
    datafile = os.path.join(temp_folder2, file + '.tif')
    xfile = os.path.join(temp_folder1, 'lon_nadir.tif')
    yfile = os.path.join(temp_folder1, 'lat_nadir.tif')
    vrtfile = os.path.join(temp_folder2, file + '.vrt')
    writevrt_nadir(vrtfile, datafile, xfile, yfile, data_type="UInt16", nodata_value=0)
    outfile = os.path.join(output_folder, file + '_proj.tif')
    dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True,
                       resampleAlg=gdal.GRIORA_NearestNeighbour)
