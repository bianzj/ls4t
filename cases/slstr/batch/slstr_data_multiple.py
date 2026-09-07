import sys
import os
import time
import math
import warnings
import shutil
import numpy as np
import cv2
from osgeo import gdal
from concurrent.futures import ProcessPoolExecutor, as_completed

# --- 原始导入部分保持不变 ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from base.util_constant import *
from base.util_file import *
from base.util_data import *

warnings.filterwarnings("ignore")


# ==============================================================================
# 1. 原始工具函数 (保持原封不动)
# ==============================================================================

def write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff',
                     nodata_value=None):
    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    elif len(im_data.shape) == 2:
        im_data = np.array([im_data])
        im_bands = 1
    else:
        im_data = np.array([im_data])
        im_bands = 1
        im_height, im_width = im_data.shape[1], im_data.shape[2] if im_data.ndim > 2 else im_data.shape[1]

    dtype_name = im_data.dtype.name
    if 'uint8' in dtype_name or 'int8' in dtype_name:
        datatype = gdal.GDT_Byte
        default_nodata = 255
    elif 'Uint16' in dtype_name or 'uint16' in dtype_name:
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
    dataset = driver.Create(path, im_width, im_height, im_bands, datatype)

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
                band.SetNoDataValue(nodata_value)
            band.FlushCache()
            band.ComputeStatistics(False)
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
    type_info = {
        "Byte": {"range": (0, 255), "default_nodata": 255},
        "UInt16": {"range": (0, 65535), "default_nodata": 0},
        "UInt32": {"range": (0, 4294967295), "default_nodata": 0},
        "Int16": {"range": (-32768, 32767), "default_nodata": -32768},
        "Int32": {"range": (-2147483648, 2147483647), "default_nodata": -2147483648},
        "Float32": {"range": None, "default_nodata": "nan"},
        "Float64": {"range": None, "default_nodata": "nan"}
    }
    if nodata_value is None:
        nodata_str = "nan" if data_type in ["Float32", "Float64"] else str(type_info[data_type]["default_nodata"])
    else:
        nodata_str = str(nodata_value)

    vrt_content = [
        f'<VRTDataset rasterXSize="{xscale}" rasterYSize="{yscale}">',
        '  <Metadata domain="GEOLOCATION">',
        '    <MDI key="SRS">GEOGCS["WGS 84(DD)",DATUM["WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AXIS["Long",EAST],AXIS["Lat",NORTH]]</MDI>',
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
    with open(vrtfile, 'w', encoding='utf-8') as f:
        f.write('\n'.join(vrt_content))
    return 1


def scale_and_convert_to_uint16(data, scale_factor, clip_range=(0, 65535)):
    scaled_data = data * scale_factor
    scaled_data = np.where(np.isnan(scaled_data), 0, scaled_data)
    scaled_data = np.where(np.isinf(scaled_data), 0, scaled_data)
    scaled_data = np.clip(scaled_data, clip_range[0], clip_range[1])
    return scaled_data.astype(np.uint16)


# ==============================================================================
# 2. 单个文件处理函数 (将原 for 循环内部逻辑整体迁移至此)
# ==============================================================================

def process_single_scene(k, fileName, indir_raw, indir_tif, cfg):
    """
    k: 索引
    fileName: 文件名
    indir_raw: 输入根目录
    indir_tif: 输出根目录
    cfg: 包含所有 ifextract_n, ratioforsimple 等开关的配置字典
    """
    # 子进程内部环境：每个子进程只用一个核心，由主进程控制并行数
    gdal.SetConfigOption('GDAL_NUM_THREADS', '1')

    fileName = fileName.strip()
    fileDir = indir_raw + fileName + '/'
    symbol = fileName[0:3]
    date_str = fileName[16:8 + 16]
    year_val = int(uint(date_str[:4]))
    month = int(fileName[20:22])
    day = int(fileName[22:24])
    doy = date2DOY(year_val, month, day)
    dayNight = "day"

    time_str1 = fileName[25:25 + 6]
    time_str2 = fileName[41:41 + 6]
    hh = int(uint(time_str1[0:2]))
    mm = int(uint(time_str1[2:4]))
    ss = int(uint(time_str1[4:6]))
    hh2 = int(uint(time_str2[0:2]))
    mm2 = int(uint(time_str2[2:4]))
    ss2 = int(uint(time_str2[4:6]))

    # 创建输出文件夹
    output_folder = os.path.join(indir_tif, fileName)
    if os.path.exists(output_folder + r'/bt8_nadir_proj.tif'):
        return f"SKIP: {fileName}"

    mkdir_if_not_exist(output_folder)
    temp_folder = os.path.join(output_folder, 'temp')
    mkdir_if_not_exist(temp_folder)

    try:
        # 文件完整性判断
        c1 = os.path.exists(fileDir + r'/S2_radiance_an.nc')
        c2 = os.path.exists(fileDir + r'/S3_radiance_an.nc')
        c3 = os.path.exists(fileDir + r'/geodetic_in.nc')
        c4 = os.path.exists(fileDir + r'/met_tx.nc')
        c6 = os.path.exists(fileDir + r'/S8_BT_in.nc')
        if c1 * c2 * c3 * c4 * c6 == 0:
            return f"DAMAGED: {fileName}"

        # --- Nadir 处理部分 ---
        if cfg['ifextract_n']:
            ns, nl = ns_nadir_g, nl_nadir_g

            # 经纬度
            lat = getDatafromNc(fileDir + '/geodetic_in.nc', 'latitude_in')
            lon = getDatafromNc(fileDir + '/geodetic_in.nc', 'longitude_in')
            if not (lat.all() and lon.all()): return f"ERR_LATLON: {fileName}"
            write_image_gdal(lat[:nl, :ns], ns, nl, 1, '', '', os.path.join(temp_folder, 'lat_nadir.tif'))
            write_image_gdal(lon[:nl, :ns], ns, nl, 1, '', '', os.path.join(temp_folder, 'lon_nadir.tif'))

            # 观测几何
            sza = getDatafromNc(fileDir + '/geometry_tn.nc', 'solar_zenith_tn')
            saa = getDatafromNc(fileDir + '/geometry_tn.nc', 'solar_azimuth_tn')
            saa[saa < 0] += 360;
            saa[saa > 360] -= 360
            sza = cv2.resize(sza[:, cfg['adj_xn']:cfg['adj_xm_n']], (ns, nl), cv2.INTER_NEAREST)
            saa = cv2.resize(saa[:, cfg['adj_xn']:cfg['adj_xm_n']], (ns, nl), cv2.INTER_NEAREST)

            if (sza[500, 500] < 85) & (sza[500, 500] >= 0):
                # 白天：提取可见光
                for b, nc, obj in [('red', 'S2_radiance_an.nc', 'S2_radiance_an'),
                                   ('nir', 'S3_radiance_an.nc', 'S3_radiance_an')]:
                    rad = getDatafromNc(fileDir + nc, obj)
                    nc_q = nc.replace('radiance', 'quality')
                    sr = getDatafromNc(fileDir + nc_q, obj.replace('radiance', 'solar_irradiance'))
                    refl = resize_data(rad / (sr[0] / np.pi), nl, ns)
                    u16 = scale_and_convert_to_uint16(refl[:nl, :ns], 10000, (0, 10000))
                    write_image_gdal(u16, ns, nl, 1, '', '', os.path.join(temp_folder, f'{b}_nadir.tif'))
                write_image_gdal(scale_and_convert_to_uint16(sza[:nl, :ns], 100), ns, nl, 1, '', '',
                                 os.path.join(temp_folder, 'sza_nadir.tif'))
                write_image_gdal(scale_and_convert_to_uint16(saa[:nl, :ns], 100), ns, nl, 1, '', '',
                                 os.path.join(temp_folder, 'saa_nadir.tif'))
            else:
                dayNight = "Night"

            # 热红外 BT8/BT9
            bt8 = getDatafromNc(fileDir + '/S8_BT_in.nc', 'S8_BT_in')[:nl, :]
            bt9 = getDatafromNc(fileDir + '/S9_BT_in.nc', 'S9_BT_in')[:nl, :]
            write_image_gdal(scale_and_convert_to_uint16(bt8, 100), ns, nl, 1, '', '',
                             os.path.join(temp_folder, 'bt8_nadir.tif'))
            write_image_gdal(scale_and_convert_to_uint16(bt9, 100), ns, nl, 1, '', '',
                             os.path.join(temp_folder, 'bt9_nadir.tif'))

            # 卫星角度和云掩膜
            vza = getDatafromNc(fileDir + '/geometry_tn.nc', 'sat_zenith_tn')
            vaa = getDatafromNc(fileDir + '/geometry_tn.nc', 'sat_azimuth_tn')
            vaa[vaa < 0] += 360;
            vaa[vaa > 360] -= 360
            vza = cv2.resize(vza[:, cfg['adj_xn']:cfg['adj_xm_n']], (ns, nl), cv2.INTER_NEAREST)
            vaa = cv2.resize(vaa[:, cfg['adj_xn']:cfg['adj_xm_n']], (ns, nl), cv2.INTER_NEAREST)
            write_image_gdal(scale_and_convert_to_uint16(vza[:nl, :ns], 100), ns, nl, 1, '', '',
                             os.path.join(temp_folder, 'vza_nadir.tif'))
            write_image_gdal(scale_and_convert_to_uint16(vaa[:nl, :ns], 100), ns, nl, 1, '', '',
                             os.path.join(temp_folder, 'vaa_nadir.tif'))
            cloud = getDatafromNc(fileDir + '/flags_in.nc', 'cloud_in')[:nl, :ns].astype(np.uint16)
            write_image_gdal(cloud, ns, nl, 1, '', '', os.path.join(temp_folder, 'cloud_nadir.tif'))

        if cfg['ifproj_n']:
            proj_items = ['bt8_nadir', 'bt9_nadir', 'cloud_nadir', 'vza_nadir', 'vaa_nadir']
            if dayNight == "day": proj_items += ['sza_nadir', 'saa_nadir', 'red_nadir', 'nir_nadir']
            for item in proj_items:
                df = os.path.join(temp_folder, item + '.tif')
                if os.path.exists(df):
                    vrt = os.path.join(temp_folder, item + '.vrt')
                    writevrt_nadir(vrt, df, os.path.join(temp_folder, 'lon_nadir.tif'),
                                   os.path.join(temp_folder, 'lat_nadir.tif'))
                    gdal.Warp(os.path.join(output_folder, item + '_proj.tif'), vrt, geoloc=True,
                              resampleAlg=gdal.GRIORA_NearestNeighbour)

        # --- Oblique 处理部分 ---
        if cfg['ifextract_o']:
            ns_o, nl_o = ns_obliq_g, nl_obliq_g
            if dayNight == "day":
                # 可见光 Oblique
                for b, nc, obj in [('red', 'S2_radiance_ao.nc', 'S2_radiance_ao'),
                                   ('nir', 'S3_radiance_ao.nc', 'S3_radiance_ao')]:
                    rad = getDatafromNc(fileDir + nc, obj)
                    nc_q = nc.replace('radiance', 'quality')
                    sr = getDatafromNc(fileDir + nc_q, obj.replace('radiance', 'solar_irradiance'))
                    refl = resize_data(rad / (sr[0] / np.pi), nl_o, ns_o)
                    u16 = scale_and_convert_to_uint16(refl[:nl_o, :ns_o], 10000, (0, 10000))
                    write_image_gdal(u16, ns_o, nl_o, 1, '', '', os.path.join(temp_folder, f'{b}_obliq.tif'))
                # 太阳角度 Oblique
                sza_o = getDatafromNc(fileDir + '/geometry_to.nc', 'solar_zenith_to')
                saa_o = getDatafromNc(fileDir + '/geometry_to.nc', 'solar_azimuth_to')
                sza_o = cv2.resize(sza_o[:, cfg['adj_xo']:cfg['adj_xm_o']], (ns_o, nl_o), cv2.INTER_NEAREST)
                saa_o = cv2.resize(saa_o[:, cfg['adj_xo']:cfg['adj_xm_o']], (ns_o, nl_o), cv2.INTER_NEAREST)
                saa_o[saa_o < 0] += 360;
                saa_o[saa_o > 360] -= 360
                write_image_gdal(scale_and_convert_to_uint16(sza_o[:nl_o, :ns_o], 100), ns_o, nl_o, 1, '', '',
                                 os.path.join(temp_folder, 'sza_obliq.tif'))
                write_image_gdal(scale_and_convert_to_uint16(saa_o[:nl_o, :ns_o], 100), ns_o, nl_o, 1, '', '',
                                 os.path.join(temp_folder, 'saa_obliq.tif'))

            # 热红外 Oblique
            bt8_o = getDatafromNc(fileDir + '/S8_BT_io.nc', 'S8_BT_io')[:nl_nadir_g, :]
            bt9_o = getDatafromNc(fileDir + '/S9_BT_io.nc', 'S9_BT_io')[:nl_nadir_g, :]
            write_image_gdal(scale_and_convert_to_uint16(bt8_o, 100), ns_nadir_g, nl_nadir_g, 1, '', '',
                             os.path.join(temp_folder, 'bt8_obliq.tif'))
            write_image_gdal(scale_and_convert_to_uint16(bt9_o, 100), ns_nadir_g, nl_nadir_g, 1, '', '',
                             os.path.join(temp_folder, 'bt9_obliq.tif'))

            # 卫星角度和云掩膜 Oblique
            vza_o = getDatafromNc(fileDir + '/geometry_to.nc', 'sat_zenith_to')
            vaa_o = getDatafromNc(fileDir + '/geometry_to.nc', 'sat_azimuth_to')
            vaa_o[vaa_o < 0] += 360;
            vaa_o[vaa_o > 360] -= 360
            vza_o = cv2.resize(vza_o[:, cfg['adj_xo']:cfg['adj_xm_o']], (ns_o, nl_o), cv2.INTER_NEAREST)
            vaa_o = cv2.resize(vaa_o[:, cfg['adj_xo']:cfg['adj_xm_o']], (ns_o, nl_o), cv2.INTER_NEAREST)
            write_image_gdal(scale_and_convert_to_uint16(vza_o[:nl_o, :ns_o], 100), ns_o, nl_o, 1, '', '',
                             os.path.join(temp_folder, 'vza_obliq.tif'))
            write_image_gdal(scale_and_convert_to_uint16(vaa_o[:nl_o, :ns_o], 100), ns_o, nl_o, 1, '', '',
                             os.path.join(temp_folder, 'vaa_obliq.tif'))

            lat_o = getDatafromNc(fileDir + '/geodetic_io.nc', 'latitude_io')[:nl_o, :ns_o]
            lon_o = getDatafromNc(fileDir + '/geodetic_io.nc', 'longitude_io')[:nl_o, :ns_o]
            write_image_gdal(lat_o, ns_o, nl_o, 1, '', '', os.path.join(temp_folder, 'lat_obliq.tif'))
            write_image_gdal(lon_o, ns_o, nl_o, 1, '', '', os.path.join(temp_folder, 'lon_obliq.tif'))

            cloud_o = getDatafromNc(fileDir + '/flags_io.nc', 'cloud_io')[:nl_o, :ns_o].astype(np.uint16)
            write_image_gdal(cloud_o, ns_o, nl_o, 1, '', '', os.path.join(temp_folder, 'cloud_obliq.tif'))

        if cfg['ifproj_o']:
            proj_items_o = ['bt8_obliq', 'bt9_obliq', 'cloud_obliq', 'vza_obliq', 'vaa_obliq']
            if dayNight == "day": proj_items_o += ['sza_obliq', 'saa_obliq', 'red_obliq', 'nir_obliq']
            for item in proj_items_o:
                df = os.path.join(temp_folder, item + '.tif')
                if os.path.exists(df):
                    vrt = os.path.join(temp_folder, item + '.vrt')
                    writevrt_obliq(vrt, df, os.path.join(temp_folder, 'lon_obliq.tif'),
                                   os.path.join(temp_folder, 'lat_obliq.tif'))
                    gdal.Warp(os.path.join(output_folder, item + '_proj.tif'), vrt, geoloc=True,
                              resampleAlg=gdal.GRIORA_NearestNeighbour)

        # 清理
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
        return f"SUCCESS: {fileName}"

    except Exception as e:
        return f"ERROR: {fileName} -> {str(e)}"


# ==============================================================================
# 3. 主程序入口
# ==============================================================================

if __name__ == '__main__':
    # 配置
    year = 2021
    indir_raw = r'/media/hero/SLSTR_download3/S3A_Euro/2021_tif/%04d/raw/' % year
    indir_tif = r'/media/hero/SLSTR_download3/S3A_Euro/2021_tif/%04d/tif/' % year
    mkdir_if_not_exist(indir_tif)

    config_params = {
        'adj_xn': 0, 'adj_xm_n': 96,
        'adj_xo': 36, 'adj_xm_o': 95,
        'ifextract_n': 1, 'ifproj_n': 1,
        'ifextract_o': 1, 'ifproj_o': 1,
        'ratioforsimple': 1
    }

    # 扫描文件
    fileNames = search_dir_rej(indir_raw, ['S3'], 'zip')
    # fileNames = fileNames[1:5]
    fileNames.sort()
    fileNum = len(fileNames)

    print(f"WSL2 + Threadripper 并行启动...")
    print(f"待处理总景数: {fileNum}")
    print(f"使用进程数: 128")

    # 开启 48 核并行池
    # 256GB 内存完全足以支撑 48 个子进程并行读写 Sentinel-3 数据
    with ProcessPoolExecutor(max_workers=64) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(process_single_scene, k, fileNames[k], indir_raw, indir_tif, config_params): fileNames[k]
            for k in range(fileNum)
        }

        # 实时打印结果
        for count, future in enumerate(as_completed(future_to_file), 1):
            res = future.result()
            print(f"[{count}/{fileNum}] {res}")

    print("--- 所有任务处理完毕 ---")