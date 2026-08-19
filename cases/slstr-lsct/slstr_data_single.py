import sys
import os

# 导入自定义路径
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
import cv2
from osgeo import gdal

warnings.filterwarnings("ignore")


# ==========================================
# 核心工具函数 (保持原有逻辑)
# ==========================================

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
    if 'uint8' in dtype_name:
        datatype = gdal.GDT_Byte
    elif 'uint16' in dtype_name:
        datatype = gdal.GDT_UInt16
    elif 'int16' in dtype_name:
        datatype = gdal.GDT_Int16
    else:
        datatype = gdal.GDT_Float32

    if nodata_value is None:
        nodata_value = 0 if 'int' in dtype_name else np.nan

    driver = gdal.GetDriverByName(imageType)
    dataset = driver.Create(path, im_width, im_height, im_bands, datatype)
    if dataset is not None:
        if im_trans: dataset.SetGeoTransform(im_trans)
        if im_proj: dataset.SetProjection(im_proj)
        for i in range(im_bands):
            band = dataset.GetRasterBand(i + 1)
            band.WriteArray(im_data[i])
            band.SetNoDataValue(float(nodata_value))
        dataset.FlushCache()
    del dataset
    return 1


def write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale, data_type="UInt16", nodata_value=0):
    vrt_content = f'''<VRTDataset rasterXSize="{xscale}" rasterYSize="{yscale}">
  <Metadata domain="GEOLOCATION">
    <MDI key="SRS">GEOGCS["WGS 84(DD)",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]</MDI>
    <MDI key="X_DATASET">{xfile}</MDI><MDI key="X_BAND">1</MDI>
    <MDI key="Y_DATASET">{yfile}</MDI><MDI key="Y_BAND">1</MDI>
    <MDI key="PIXEL_OFFSET">0</MDI><MDI key="PIXEL_STEP">1</MDI>
    <MDI key="LINE_OFFSET">0</MDI><MDI key="LINE_STEP">1</MDI>
  </Metadata>
  <VRTRasterBand dataType="{data_type}" band="1"><NoDataValue>{nodata_value}</NoDataValue>
    <SimpleSource><SourceFilename relativeToVRT="1">{datafile}</SourceFilename><SourceBand>1</SourceBand></SimpleSource>
  </VRTRasterBand></VRTDataset>'''
    with open(vrtfile, 'w', encoding='utf-8') as f: f.write(vrt_content)
    return 1


def scale_and_convert_to_uint16(data, scale_factor, clip_range=(0, 65535)):
    scaled = np.nan_to_num(data * scale_factor, nan=0, posinf=0, neginf=0)
    return np.clip(scaled, clip_range[0], clip_range[1]).astype(np.uint16)


# ==========================================
# 数据配置
# ==========================================
kyear = 2020
indir_raw = r'/media/hero/SLSTR_download3/S3A_Euro/2020_tif/%04d/raw/' % kyear
indir_tif = r'/media/hero/SLSTR_download3/S3A_Euro/2020_tif/%04d/tif/' % kyear
mkdir_if_not_exist(indir_tif)


# 几何校正参数
adj_xn_min, adj_xn_max = 0, 96
adj_xo_min, adj_xo_max = 36, 95

# 查找待处理数据
fileNames = search_dir_rej(indir_raw, ['S3'], 'zip')
fileNames = fileNames[:5]
fileNames = sorted(fileNames)
fileNum = len(fileNames)
print(f"Total folders to check: {fileNum}")

# --- 主循环 (单线程) ---
for k in range(fileNum):
    fileName = fileNames[k].strip()
    fileDir = os.path.join(indir_raw, fileName) + '/'
    output_folder = os.path.join(indir_tif, fileName)

    # 直接判断：如果文件夹已存在，说明之前审计通过了或者是成功的，跳过
    if os.path.exists(output_folder):
        continue

    print(f"[{k + 1}/{fileNum}] Processing: {fileName}")

    # 初始化
    mkdir_if_not_exist(output_folder)
    temp_folder = os.path.join(output_folder, 'temp')
    mkdir_if_not_exist(temp_folder)
    dayNight = "day"

    try:
        # --- 1. NADIR (垂直) 提取 ---
        ns, nl = ns_nadir_g, nl_nadir_g

        # 经纬度
        lat = getDatafromNc(fileDir + 'geodetic_in.nc', 'latitude_in')[:nl, :ns]
        lon = getDatafromNc(fileDir + 'geodetic_in.nc', 'longitude_in')[:nl, :ns]
        lat_f = os.path.join(temp_folder, 'lat_nadir.tif')
        lon_f = os.path.join(temp_folder, 'lon_nadir.tif')
        write_image_gdal(lat, ns, nl, 1, '', '', lat_f)
        write_image_gdal(lon, ns, nl, 1, '', '', lon_f)

        # 太阳角度
        sza = getDatafromNc(fileDir + 'geometry_tn.nc', 'solar_zenith_tn')
        sza = cv2.resize(sza[:, adj_xn_min:adj_xn_max], (ns, nl), cv2.INTER_NEAREST)

        if sza[500, 500] < 85:
            # 白天数据
            saa = getDatafromNc(fileDir + 'geometry_tn.nc', 'solar_azimuth_tn')
            saa = cv2.resize(saa[:, adj_xn_min:adj_xn_max], (ns, nl), cv2.INTER_NEAREST)
            saa[saa < 0] += 360;
            saa[saa > 360] -= 360
            write_image_gdal(scale_and_convert_to_uint16(sza, 100), ns, nl, 1, '', '',
                             os.path.join(temp_folder, 'sza_nadir.tif'))
            write_image_gdal(scale_and_convert_to_uint16(saa, 100), ns, nl, 1, '', '',
                             os.path.join(temp_folder, 'saa_nadir.tif'))

            # VNIR 反射率
            for b, nc, obj in [('red', 'S2_radiance_an.nc', 'S2_radiance_an'),
                               ('nir', 'S3_radiance_an.nc', 'S3_radiance_an')]:
                rad = getDatafromNc(fileDir + nc, obj)
                nc_q = nc.replace('radiance', 'quality')
                sr = getDatafromNc(fileDir + nc_q, obj.replace('radiance', 'solar_irradiance'))
                refl = resize_data(rad / (sr[0] / np.pi), nl, ns)
                write_image_gdal(scale_and_convert_to_uint16(refl[:nl, :ns], 10000), ns, nl, 1, '', '',
                                 os.path.join(temp_folder, f'{b}_nadir.tif'))
        else:
            dayNight = "Night"

        # TIR 热红外
        bt8 = getDatafromNc(fileDir + 'S8_BT_in.nc', 'S8_BT_in')[:nl, :]
        bt9 = getDatafromNc(fileDir + 'S9_BT_in.nc', 'S9_BT_in')[:nl, :]
        write_image_gdal(scale_and_convert_to_uint16(bt8, 100), ns, nl, 1, '', '',
                         os.path.join(temp_folder, 'bt8_nadir.tif'))
        write_image_gdal(scale_and_convert_to_uint16(bt9, 100), ns, nl, 1, '', '',
                         os.path.join(temp_folder, 'bt9_nadir.tif'))

        # 卫星角度
        vza = getDatafromNc(fileDir + 'geometry_tn.nc', 'sat_zenith_tn')
        vaa = getDatafromNc(fileDir + 'geometry_tn.nc', 'sat_azimuth_tn')
        vza = cv2.resize(vza[:, adj_xn_min:adj_xn_max], (ns, nl), cv2.INTER_NEAREST)
        vaa = cv2.resize(vaa[:, adj_xn_min:adj_xn_max], (ns, nl), cv2.INTER_NEAREST)
        vaa[vaa < 0] += 360;
        vaa[vaa > 360] -= 360
        write_image_gdal(scale_and_convert_to_uint16(vza, 100), ns, nl, 1, '', '',
                         os.path.join(temp_folder, 'vza_nadir.tif'))
        write_image_gdal(scale_and_convert_to_uint16(vaa, 100), ns, nl, 1, '', '',
                         os.path.join(temp_folder, 'vaa_nadir.tif'))

        # 云掩膜
        cloud = getDatafromNc(fileDir + 'flags_in.nc', 'cloud_in')[:nl, :ns].astype(np.uint16)
        write_image_gdal(cloud, ns, nl, 1, '', '', os.path.join(temp_folder, 'cloud_nadir.tif'))

        # Nadir 投影
        proj_list = ['bt8_nadir', 'bt9_nadir', 'cloud_nadir', 'vza_nadir', 'vaa_nadir']
        if dayNight == "day": proj_list += ['sza_nadir', 'saa_nadir', 'red_nadir', 'nir_nadir']
        for item in proj_list:
            df = os.path.join(temp_folder, item + '.tif')
            if os.path.exists(df):
                vrt = os.path.join(temp_folder, item + '.vrt')
                write_vrt(vrt, df, lon_f, lat_f, ns, nl)
                gdal.Warp(os.path.join(output_folder, item + '_proj.tif'), vrt, geoloc=True,
                          resampleAlg=gdal.GRIORA_NearestNeighbour)

        # --- 2. OBLIQUE (倾斜) 提取 ---
        ns_o, nl_o = ns_obliq_g, nl_obliq_g
        lato = getDatafromNc(fileDir + 'geodetic_io.nc', 'latitude_io')[:nl_o, :ns_o]
        lono = getDatafromNc(fileDir + 'geodetic_io.nc', 'longitude_io')[:nl_o, :ns_o]
        lato_f = os.path.join(temp_folder, 'lat_obliq.tif')
        lono_f = os.path.join(temp_folder, 'lon_obliq.tif')
        write_image_gdal(lato, ns_o, nl_o, 1, '', '', lato_f)
        write_image_gdal(lono, ns_o, nl_o, 1, '', '', lono_f)

        if dayNight == "day":
            for b, nc, obj in [('red', 'S2_radiance_ao.nc', 'S2_radiance_ao'),
                               ('nir', 'S3_radiance_ao.nc', 'S3_radiance_ao')]:
                rad = getDatafromNc(fileDir + nc, obj)
                nc_q = nc.replace('radiance', 'quality')
                sr = getDatafromNc(fileDir + nc_q, obj.replace('radiance', 'solar_irradiance'))
                refl = resize_data(rad / (sr[0] / np.pi), nl_o, ns_o)
                write_image_gdal(scale_and_convert_to_uint16(refl[:nl_o, :ns_o], 10000), ns_o, nl_o, 1, '', '',
                                 os.path.join(temp_folder, f'{b}_obliq.tif'))

            szao = getDatafromNc(fileDir + 'geometry_to.nc', 'solar_zenith_to')
            szao = cv2.resize(szao[:, adj_xo_min:adj_xo_max], (ns_o, nl_o), cv2.INTER_NEAREST)
            saao = getDatafromNc(fileDir + 'geometry_to.nc', 'solar_azimuth_to')
            saao = cv2.resize(saao[:, adj_xo_min:adj_xo_max], (ns_o, nl_o), cv2.INTER_NEAREST)
            saao[saao < 0] += 360;
            saao[saao > 360] -= 360
            write_image_gdal(scale_and_convert_to_uint16(szao, 100), ns_o, nl_o, 1, '', '',
                             os.path.join(temp_folder, 'sza_obliq.tif'))
            write_image_gdal(scale_and_convert_to_uint16(saao, 100), ns_o, nl_o, 1, '', '',
                             os.path.join(temp_folder, 'saa_obliq.tif'))

        bt8o = getDatafromNc(fileDir + 'S8_BT_io.nc', 'S8_BT_io')[:nl_o, :]
        bt9o = getDatafromNc(fileDir + 'S9_BT_io.nc', 'S9_BT_io')[:nl_o, :]
        write_image_gdal(scale_and_convert_to_uint16(bt8o, 100), ns_o, nl_o, 1, '', '',
                         os.path.join(temp_folder, 'bt8_obliq.tif'))
        write_image_gdal(scale_and_convert_to_uint16(bt9o, 100), ns_o, nl_o, 1, '', '',
                         os.path.join(temp_folder, 'bt9_obliq.tif'))

        vzao = getDatafromNc(fileDir + 'geometry_to.nc', 'sat_zenith_to')
        vaao = getDatafromNc(fileDir + 'geometry_to.nc', 'sat_azimuth_to')
        vzao = cv2.resize(vzao[:, adj_xo_min:adj_xo_max], (ns_o, nl_o), cv2.INTER_NEAREST)
        vaao = cv2.resize(vaao[:, adj_xo_min:adj_xo_max], (ns_o, nl_o), cv2.INTER_NEAREST)
        vaao[vaao < 0] += 360;
        vaao[vaao > 360] -= 360
        write_image_gdal(scale_and_convert_to_uint16(vzao, 100), ns_o, nl_o, 1, '', '',
                         os.path.join(temp_folder, 'vza_obliq.tif'))
        write_image_gdal(scale_and_convert_to_uint16(vaao, 100), ns_o, nl_o, 1, '', '',
                         os.path.join(temp_folder, 'vaa_obliq.tif'))

        cloo = getDatafromNc(fileDir + 'flags_io.nc', 'cloud_io')[:nl_o, :ns_o].astype(np.uint16)
        write_image_gdal(cloo, ns_o, nl_o, 1, '', '', os.path.join(temp_folder, 'cloud_obliq.tif'))

        # Oblique 投影
        proj_o_list = ['bt8_obliq', 'bt9_obliq', 'cloud_obliq', 'vza_obliq', 'vaa_obliq']
        if dayNight == "day": proj_o_list += ['sza_obliq', 'saa_obliq', 'red_obliq', 'nir_obliq']
        for item in proj_o_list:
            df = os.path.join(temp_folder, item + '.tif')
            if os.path.exists(df):
                vrt = os.path.join(temp_folder, item + '.vrt')
                write_vrt(vrt, df, lono_f, lato_f, ns_o, nl_o)
                gdal.Warp(os.path.join(output_folder, item + '_proj.tif'), vrt, geoloc=True,
                          resampleAlg=gdal.GRIORA_NearestNeighbour)

        # 清理
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)

    except Exception as e:
        print(f"Error on {fileName}: {e}")
        # 出错后删除坏文件夹，防止干扰下次运行
        if os.path.exists(output_folder): shutil.rmtree(output_folder)

print("Batch Processing Finished.")