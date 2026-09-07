
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import netCDF4
import time
from base.util_constant import *
from base.util_file import *
from base.util_data import *
import math
import warnings
import shutil
import numpy as np

warnings.filterwarnings("ignore")

'''2025.10.12 ls4t case: （注意python版本不同lonlat2geo输入顺序)'''
'''2023.10.04 增加倾斜方向日夜提取'''
'''2023.7.22 增加垂直方向夜晚提取的部分用于定标'''
'''2023.5.7 slstr_lst 两角度数据提取（重构版）'''
'''只输出了白天的数据，方便后续用于组分温度反演'''
'''注意：不同时区一定要调day_start_hour\day_end_hour'''

'''
slstr_data_nadir.py
从解压后的原始数据中提取相关信息，并根据type文件进行重投影
脚本操作包括：
1. 先提出出来成tif
2. gdal进行投影转换
3. 研究区重采样
'''


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


# 数据输入
indir_raw = r'/media/hero/SLSTR-SouthA-raw/2017-euro/raw/'
indir_tif = r'/media/hero/slstr-euro-lst/2017/tif/'
mkdir_if_not_exist(indir_tif)

s = 'S3'  # 同时处理S3A和S3B数据
day_start_hour = 22  # 研究区白天开始的utm小时（不含）24小时制
day_end_hour = 10  # 研究区白天开始的utm小时（不含）

adjust_xmin_n_g = 0  # 观测几何重采样用的参数
adjust_xmax_n_g = 95 + 1
adjust_xmin_o_g = 36
adjust_xmax_o_g = 94 + 1

# 数据操作
ifextract_n = 1
ifproj_n = 0
ifresample_n = 0

ifextract_o = 1
ifproj_o = 0
ifresample_o = 0


ratioforsimple = 1

# 查找数据文件夹
fileNames = search_dir_rej(indir_raw, ['S3'], 'zip')
fileNames.sort()
fileNum = len(fileNames)
#for k in range(fileNum):
for k in range(fileNum):
    fileName = fileNames[k].strip()
    fileDir = indir_raw + fileName + '/'
    print(k, fileDir)
    symbol = fileName[0:3]
    date_str = fileName[16:8 + 16]
    year = int(uint(date_str[:4]))
    month = int(fileName[20:22])
    day = int(fileName[22:24])
    doy = date2DOY(2019, month, day)
    dayNight = "day"

    ### 测试只处理某一天的数据
    # if doy <= 182: continue

    time_str1 = fileName[25:25 + 6]
    time_str2 = fileName[41:41 + 6]
    hh = int(uint(time_str1[0:2]))
    mm = int(uint(time_str1[2:4]))
    ss = int(uint(time_str2[4:6]))
    # 终止时间
    hh2 = int(uint(time_str2[0:2]))
    mm2 = int(uint(time_str2[2:4]))
    ss2 = int(uint(time_str2[4:6]))
    t1 = hh + mm / 60 + ss / 3600
    t2 = hh2 + mm2 / 60 + ss2 / 3600

    # 创建输出文件夹
    output_folder = os.path.join(indir_tif, fileName)
    mkdir_if_not_exist(output_folder)

    # 创建临时文件夹用于中间文件
    #temp_folder = os.path.join(output_folder, 'temp')
    #mkdir_if_not_exist(temp_folder)
    temp_folder = output_folder

    file = 'vaa_obliq'
    outfile = os.path.join(output_folder, file + '.tif')
    if os.path.exists(outfile):
        print('finished\n')
        continue

    # 判断文件是否齐全
    c1 = os.path.exists(fileDir + r'/S2_radiance_an.nc')
    c2 = os.path.exists(fileDir + r'/S3_radiance_an.nc')
    c3 = os.path.exists(fileDir + r'/geodetic_in.nc')
    c4 = os.path.exists(fileDir + r'/met_tx.nc')
    c5 = os.path.exists(fileDir + r'/S2_radiance_an.nc')
    c6 = os.path.exists(fileDir + r'/S8_BT_in.nc')
    if c1 * c2 * c3 * c4 * c5 * c6 == 0:
        print("File damaged!")
        continue

    if ifextract_n:
        ns = ns_nadir_g  # 1500*1200 热红外一景图大小，可见光为3000*2400
        nl = nl_nadir_g
        ns_v = ns_nadir_v_g
        nl_v = nl_nadir_v_g

        '''lon and lat'''
        fileName_nc = fileDir + '/geodetic_in.nc'
        objectName = r'latitude_in'
        lat = getDatafromNc(fileName_nc, objectName)
        fileName_nc = fileDir + '/geodetic_in.nc'
        objectName = r'longitude_in'
        lon = getDatafromNc(fileName_nc, objectName)
        if not (lat.all() and lon.all()):
            continue
        outfile = os.path.join(temp_folder, 'lat_nadir.tif')
        if (os.path.exists(outfile)):
            continue

        # 经纬度数据保持原样
        lat_uint16 = scale_and_convert_to_uint16(lat[:nl, :ns], 100)
        lon_uint16 = scale_and_convert_to_uint16(lon[:nl, :ns], 100)

        write_image_gdal(lat_uint16[:nl, :ns], ns, nl, 1, '', '', outfile)
        outfile = os.path.join(temp_folder, 'lon_nadir.tif')
        write_image_gdal(lon_uint16[:nl, :ns], ns, nl, 1, '', '', outfile)

        '''读取观测几何和云数据'''
        fileName_nc = fileDir + '/geometry_tn.nc'
        objectName = r'solar_zenith_tn'
        sza = getDatafromNc(fileName_nc, objectName)
        objectName = r'solar_azimuth_tn'
        saa = getDatafromNc(fileName_nc, objectName)

        sza = cv2.resize(sza[:, adjust_xmin_n_g:adjust_xmax_n_g],
                         (ns, nl), cv2.INTER_NEAREST)
        saa = cv2.resize(saa[:, adjust_xmin_n_g:adjust_xmax_n_g],
                         (ns, nl), cv2.INTER_NEAREST)

        sza_temp = np.int_(sza[500, 500])

        if (sza_temp < 85) & (sza_temp >= 0):
            # 角度数据*100并转换为UInt16
            sza_uint16 = scale_and_convert_to_uint16(sza[:nl, :ns], 100)
            saa_uint16 = scale_and_convert_to_uint16(saa[:nl, :ns], 100)

            outfile = os.path.join(temp_folder, 'sza_nadir.tif')
            write_image_gdal(sza_uint16, ns, nl, 1, '', '', outfile )
            outfile = os.path.join(temp_folder, 'saa_nadir.tif')
            write_image_gdal(saa_uint16, ns, nl, 1, '', '', outfile )

            '''提取可见光（红光、近红外）数据'''
            fileName_nc = fileDir + '/S2_radiance_an.nc'
            objectName = r'S2_radiance_an'
            rad_red = getDatafromNc(fileName_nc, objectName)
            fileName_nc = fileDir + '/S2_quality_an.nc'
            objectName = r'S2_solar_irradiance_an'
            sr_red = getDatafromNc(fileName_nc, objectName)

            fileName_nc = fileDir + '/S3_radiance_an.nc'
            objectName = r'S3_radiance_an'
            rad_nir = getDatafromNc(fileName_nc, objectName)
            fileName_nc = fileDir + '/S3_quality_an.nc'
            objectName = r'S3_solar_irradiance_an'
            sr_nir = getDatafromNc(fileName_nc, objectName)

            # 计算红光和近红外反射率
            refl_red = rad_red / (sr_red[0] / np.pi)
            refl_nir = rad_nir / (sr_nir[0] / np.pi)

            refl_red = resize_data(refl_red, nl, ns)
            # 光学数据*10000并转换为UInt16
            refl_red_uint16 = scale_and_convert_to_uint16(refl_red[:nl, :ns], 10000, (0, 10000))
            outfile = os.path.join(temp_folder, 'red_nadir.tif')
            write_image_gdal(refl_red_uint16, ns, nl, 1, '', '', outfile )

            refl_nir = resize_data(refl_nir, nl, ns)
            # 光学数据*10000并转换为UInt16
            refl_nir_uint16 = scale_and_convert_to_uint16(refl_nir[:nl, :ns], 10000, (0, 10000))
            outfile = os.path.join(temp_folder, 'nir_nadir.tif')
            write_image_gdal(refl_nir_uint16, ns, nl, 1, '', '', outfile )
        else:
            dayNight = "Night"

        '''读取热红外数据'''
        fileName_nc = fileDir + '/S8_BT_in.nc'
        objectName = r'S8_BT_in'
        BT8 = getDatafromNc(fileName_nc, objectName)

        fileName_nc = fileDir + '/S9_BT_in.nc'
        objectName = r'S9_BT_in'
        BT9 = getDatafromNc(fileName_nc, objectName)

        if not (BT8.all() and BT9.all()):
            continue

        BT8 = BT8[:nl, :]
        BT9 = BT9[:nl, :]

        # 红外数据*100并转换为UInt16
        BT8_uint16 = scale_and_convert_to_uint16(BT8, 100, (0, 65535))
        BT9_uint16 = scale_and_convert_to_uint16(BT9, 100, (0, 65535))

        outfile = os.path.join(temp_folder, 'bt8_nadir.tif')
        write_image_gdal(BT8_uint16, ns, nl, 1, '', '', outfile)

        outfile = os.path.join(temp_folder, 'bt9_nadir.tif')
        write_image_gdal(BT9_uint16, ns, nl, 1, '', '', outfile)

        '''读取观测几何和云数据'''
        fileName_nc = fileDir + '/geometry_tn.nc'
        objectName = r'sat_zenith_tn'
        vza = getDatafromNc(fileName_nc, objectName)

        objectName = r'sat_azimuth_tn'
        vaa = getDatafromNc(fileName_nc, objectName)

        vza = cv2.resize(vza[:, adjust_xmin_n_g:adjust_xmax_n_g],
                         (ns, nl), cv2.INTER_NEAREST)

        vaa = cv2.resize(vaa[:, adjust_xmin_n_g:adjust_xmax_n_g],
                         (ns, nl), cv2.INTER_NEAREST)

        # 角度数据*100并转换为UInt16
        vza_uint16 = scale_and_convert_to_uint16(vza[:nl, :ns], 100)
        vaa_uint16 = scale_and_convert_to_uint16(vaa[:nl, :ns], 100)

        outfile = os.path.join(temp_folder, 'vza_nadir.tif')
        write_image_gdal(vza_uint16, ns, nl, 1, '', '', outfile)
        outfile = os.path.join(temp_folder, 'vaa_nadir.tif')
        write_image_gdal(vaa_uint16, ns, nl, 1, '', '', outfile )

        '''cloud'''
        fileName_nc = fileDir + '/flags_in.nc'
        objectName = r'cloud_in'
        cloud = getDatafromNc(fileName_nc, objectName)
        # cloud数据不变，直接转换为UInt16
        cloud_uint16 = cloud[:nl, :ns].astype(np.uint16)
        outfile = os.path.join(temp_folder, 'cloud_nadir.tif')
        write_image_gdal(cloud_uint16, ns, nl, 1, '', '', outfile )


    if ifextract_o:
        ns = ns_obliq_g  # 900*1200 热红外一景图大小，可见光为3000*2400
        nl = nl_obliq_g
        if dayNight == "day":
            '''提取可见光（红光、近红外）数据'''
            fileName_nc = fileDir + '/S2_radiance_ao.nc'
            objectName = r'S2_radiance_ao'
            rad_red = getDatafromNc(fileName_nc, objectName)
            fileName_nc = fileDir + '/S2_quality_ao.nc'
            objectName = r'S2_solar_irradiance_ao'
            sr_red = getDatafromNc(fileName_nc, objectName)

            fileName_nc = fileDir + '/S3_radiance_ao.nc'
            objectName = r'S3_radiance_ao'
            rad_nir = getDatafromNc(fileName_nc, objectName)
            fileName_nc = fileDir + '/S3_quality_ao.nc'
            objectName = r'S3_solar_irradiance_ao'
            sr_nir = getDatafromNc(fileName_nc, objectName)

            # 计算红光和近红外反射率
            refl_red = rad_red / (sr_red[0] / np.pi)
            refl_nir = rad_nir / (sr_nir[0] / np.pi)

            refl_red = resize_data(refl_red, nl, ns)
            # 光学数据*10000并转换为UInt16
            refl_red_uint16 = scale_and_convert_to_uint16(refl_red[:nl, :ns], 10000, (0, 10000))
            outfile = os.path.join(temp_folder, 'red_obliq.tif')
            write_image_gdal(refl_red_uint16, ns, nl, 1, '', '', outfile )

            refl_nir = resize_data(refl_nir, nl, ns)
            # 光学数据*10000并转换为UInt16
            refl_nir_uint16 = scale_and_convert_to_uint16(refl_nir[:nl, :ns], 10000, (0, 10000))
            outfile = os.path.join(temp_folder, 'nir_obliq.tif')
            write_image_gdal(refl_nir_uint16, ns, nl, 1, '', '', outfile )

            '''读取观测几何和云数据'''
            fileName_nc = fileDir + '/geometry_to.nc'
            objectName = r'solar_zenith_to'
            sza = getDatafromNc(fileName_nc, objectName)

            objectName = r'solar_azimuth_to'
            saa = getDatafromNc(fileName_nc, objectName)

            sza = cv2.resize(sza[:, adjust_xmin_o_g:adjust_xmax_o_g],
                             (ns_obliq_g, nl_obliq_g), cv2.INTER_NEAREST)
            saa = cv2.resize(saa[:, adjust_xmin_o_g:adjust_xmax_o_g],
                             (ns_obliq_g, nl_obliq_g), cv2.INTER_NEAREST)

            # 角度数据*100并转换为UInt16
            sza_uint16 = scale_and_convert_to_uint16(sza[:nl, :ns], 100)
            saa_uint16 = scale_and_convert_to_uint16(saa[:nl, :ns], 100)

            outfile = os.path.join(temp_folder, 'sza_obliq.tif')
            write_image_gdal(sza_uint16, ns, nl, 1, '', '', outfile )
            outfile = os.path.join(temp_folder, 'saa_obliq.tif')
            write_image_gdal(saa_uint16, ns, nl, 1, '', '', outfile )

        '''读取热红外数据'''
        fileName_nc = fileDir + '/S8_BT_io.nc'
        objectName = r'S8_BT_io'
        BT8 = getDatafromNc(fileName_nc, objectName)

        fileName_nc = fileDir + '/S9_BT_io.nc'
        objectName = r'S9_BT_io'
        BT9 = getDatafromNc(fileName_nc, objectName)

        if not (BT8.all() and BT9.all()):
            continue

        BT8 = BT8[:nl_nadir_g, :]
        BT9 = BT9[:nl_nadir_g, :]

        # 红外数据*100并转换为UInt16
        BT8_uint16 = scale_and_convert_to_uint16(BT8, 100, (0, 65535))
        BT9_uint16 = scale_and_convert_to_uint16(BT9, 100, (0, 65535))

        outfile = os.path.join(temp_folder, 'bt8_obliq.tif')
        write_image_gdal(BT8_uint16, ns_obliq_g, nl_obliq_g, 1, '', '', outfile )

        outfile = os.path.join(temp_folder, 'bt9_obliq.tif')
        write_image_gdal(BT9_uint16, ns_obliq_g, nl_obliq_g, 1, '', '', outfile )

        '''读取观测几何和云数据'''
        fileName_nc = fileDir + '/geometry_to.nc'
        objectName = r'sat_zenith_to'
        vza = getDatafromNc(fileName_nc, objectName)
        objectName = r'sat_azimuth_to'
        vaa = getDatafromNc(fileName_nc, objectName)

        vza = cv2.resize(vza[:, adjust_xmin_o_g:adjust_xmax_o_g],
                         (ns_obliq_g, nl_obliq_g), cv2.INTER_NEAREST)
        vaa = cv2.resize(vaa[:, adjust_xmin_o_g:adjust_xmax_o_g],
                         (ns_obliq_g, nl_obliq_g), cv2.INTER_NEAREST)

        # 角度数据*100并转换为UInt16
        vza_uint16 = scale_and_convert_to_uint16(vza[:nl, :ns], 100)
        vaa_uint16 = scale_and_convert_to_uint16(vaa[:nl, :ns], 100)

        outfile = os.path.join(temp_folder, 'vza_obliq.tif')
        write_image_gdal(vza_uint16, ns, nl, 1, '', '', outfile )

        outfile = os.path.join(temp_folder, 'vaa_obliq.tif')
        write_image_gdal(vaa_uint16, ns, nl, 1, '', '', outfile )

        '''lon and lat'''
        fileName_nc = fileDir + '/geodetic_io.nc'
        objectName = r'latitude_io'
        lat = getDatafromNc(fileName_nc, objectName)

        fileName_nc = fileDir + '/geodetic_io.nc'
        objectName = r'longitude_io'
        lon = getDatafromNc(fileName_nc, objectName)

        if not (lat.all() and lon.all()):
            continue


        lat_uint16 = scale_and_convert_to_uint16(lat[:nl, :ns], 100)
        lon_uint16 = scale_and_convert_to_uint16(lon[:nl, :ns], 100)

        outfile = os.path.join(temp_folder, 'lat_obliq.tif')
        write_image_gdal(lat_uint16[:nl, :ns], ns, nl, 1, '', '', outfile)

        outfile = os.path.join(temp_folder, 'lon_obliq.tif')
        write_image_gdal(lon_uint16[:nl, :ns], ns, nl, 1, '', '', outfile)

        '''cloud'''
        fileName_nc = fileDir + '/flags_io.nc'
        objectName = r'cloud_io'
        cloud = getDatafromNc(fileName_nc, objectName)

        # cloud数据不变，直接转换为UInt16
        cloud_uint16 = cloud[:nl, :ns].astype(np.uint16)
        outfile = os.path.join(temp_folder, 'cloud_obliq.tif')
        write_image_gdal(cloud_uint16, ns, nl, 1, '', '', outfile )


    # 删除临时文件夹中的未投影文件



