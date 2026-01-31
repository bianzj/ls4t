import os
import sys
import math
import warnings
import numpy as np
import cv2
from osgeo import gdal

warnings.filterwarnings("ignore")

# -------------------------------------------------
# 项目工具
# -------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from base.util_constant import *
from base.util_file import *
from base.util_data import *

# -------------------------------------------------
# 路径配置
# -------------------------------------------------
indir_raw = r'/Users/bianzj/Downloads/data/slstr_raw/'
indir_tif = r'/Users/bianzj/Downloads/data/slstr_tif/'
mkdir_if_not_exist(indir_tif)

# -------------------------------------------------
# 参数配置
# -------------------------------------------------
s = 'S3'
day_start_hour = 22
day_end_hour   = 10

adjust_xmin_n_g = 0
adjust_xmax_n_g = 96
adjust_xmin_o_g = 36
adjust_xmax_o_g = 95

ifextract_n = 1
ifproj_n    = 1
ifextract_o = 1
ifproj_o    = 1

# -------------------------------------------------
# 通用函数
# -------------------------------------------------
def project_with_geoloc(data_tif, lon_tif, lat_tif, vrt_func, out_tif,
                        resample=gdal.GRIORA_NearestNeighbour):
    """统一的经纬度投影封装"""
    vrtfile = out_tif.replace(".tif", ".vrt")
    vrt_func(vrtfile, data_tif, lon_tif, lat_tif)
    gdal.Warp(out_tif, vrtfile, geoloc=True, resampleAlg=resample)

# -------------------------------------------------
# 搜索数据
# -------------------------------------------------
fileNames = search_dir_rej(indir_raw, ['S3'], 'zip')
fileNames.sort()

for k, granule in enumerate(fileNames):

    fileDir = os.path.join(indir_raw, granule)
    print(f"[{k}] Processing {granule}")

    # =============================
    # 输出目录（核心优化）
    # =============================
    out_root  = os.path.join(indir_tif, granule)
    out_nadir = os.path.join(out_root, "nadir")
    out_obliq = os.path.join(out_root, "obliq")
    out_aux   = os.path.join(out_root, "aux")

    for d in [out_root, out_nadir, out_obliq, out_aux]:
        mkdir_if_not_exist(d)

    # =============================
    # 时间 & 日夜判断
    # =============================
    time_str1 = granule[25:31]
    time_str2 = granule[41:47]
    hh = int(time_str1[0:2])

    if day_end_hour > day_start_hour:
        dayNight = 'day' if day_start_hour < hh < day_end_hour else 'nig'
    else:
        dayNight = 'day' if (hh > day_start_hour or hh < day_end_hour) else 'nig'

    if dayNight == 'nig':
        print("  -> Nighttime, skip")
        continue

    # =============================
    # 文件完整性检查
    # =============================
    required = [
        'S2_radiance_an.nc', 'S3_radiance_an.nc',
        'geodetic_in.nc', 'flags_in.nc',
        'S8_BT_in.nc', 'S9_BT_in.nc'
    ]
    if not all(os.path.exists(os.path.join(fileDir, f)) for f in required):
        print("  -> Missing files, skip")
        continue

    # ============================================================
    # NADIR 提取
    # ============================================================
    if ifextract_n:

        ns, nl = ns_nadir_g, nl_nadir_g

        # ---------- TIR ----------
        BT8 = getDatafromNc(os.path.join(fileDir, 'S8_BT_in.nc'), 'S8_BT_in')[:nl, :]
        BT9 = getDatafromNc(os.path.join(fileDir, 'S9_BT_in.nc'), 'S9_BT_in')[:nl, :]

        write_image_gdal(BT8, ns, nl, 1, '', '',
                         os.path.join(out_nadir, 'bt8.tif'))
        write_image_gdal(BT9, ns, nl, 1, '', '',
                         os.path.join(out_nadir, 'bt9.tif'))

        # ---------- Geometry ----------
        geo = os.path.join(fileDir, 'geometry_tn.nc')
        vza = getDatafromNc(geo, 'sat_zenith_tn')
        vaa = getDatafromNc(geo, 'sat_azimuth_tn')

        vza = cv2.resize(vza[:, adjust_xmin_n_g:adjust_xmax_n_g],
                         (ns, nl), cv2.INTER_NEAREST)
        vaa = cv2.resize(vaa[:, adjust_xmin_n_g:adjust_xmax_n_g],
                         (ns, nl), cv2.INTER_NEAREST)

        write_image_gdal(vza, ns, nl, 1, '', '',
                         os.path.join(out_nadir, 'vza.tif'))
        write_image_gdal(vaa, ns, nl, 1, '', '',
                         os.path.join(out_nadir, 'vaa.tif'))

        # ---------- lon / lat ----------
        lat = getDatafromNc(os.path.join(fileDir, 'geodetic_in.nc'), 'latitude_in')
        lon = getDatafromNc(os.path.join(fileDir, 'geodetic_in.nc'), 'longitude_in')

        write_image_gdal(lat[:nl, :ns], ns, nl, 1, '', '',
                         os.path.join(out_aux, 'lat.tif'))
        write_image_gdal(lon[:nl, :ns], ns, nl, 1, '', '',
                         os.path.join(out_aux, 'lon.tif'))

        # ---------- cloud ----------
        cloud = getDatafromNc(os.path.join(fileDir, 'flags_in.nc'), 'cloud_in')
        write_image_gdal(cloud[:nl, :ns], ns, nl, 1, '', '',
                         os.path.join(out_aux, 'cloud.tif'))

    # ============================================================
    # NADIR 投影
    # ============================================================
    if ifproj_n:
        for var in ['bt8', 'bt9', 'vza', 'vaa']:
            project_with_geoloc(
                data_tif=os.path.join(out_nadir, f'{var}.tif'),
                lon_tif=os.path.join(out_aux, 'lon.tif'),
                lat_tif=os.path.join(out_aux, 'lat.tif'),
                vrt_func=writevrt_nadir,
                out_tif=os.path.join(out_nadir, f'{var}_proj.tif')
            )

        project_with_geoloc(
            data_tif=os.path.join(out_aux, 'cloud.tif'),
            lon_tif=os.path.join(out_aux, 'lon.tif'),
            lat_tif=os.path.join(out_aux, 'lat.tif'),
            vrt_func=writevrt_nadir,
            out_tif=os.path.join(out_aux, 'cloud_proj.tif')
        )

    # ============================================================
    # OBLIQUE（结构与 NADIR 完全一致）
    # ============================================================
    if ifextract_o:

        ns, nl = ns_obliq_g, nl_obliq_g

        BT8 = getDatafromNc(os.path.join(fileDir, 'S8_BT_io.nc'), 'S8_BT_io')[:nl, :]
        BT9 = getDatafromNc(os.path.join(fileDir, 'S9_BT_io.nc'), 'S9_BT_io')[:nl, :]

        write_image_gdal(BT8, ns, nl, 1, '', '',
                         os.path.join(out_obliq, 'bt8.tif'))
        write_image_gdal(BT9, ns, nl, 1, '', '',
                         os.path.join(out_obliq, 'bt9.tif'))

        geo = os.path.join(fileDir, 'geometry_to.nc')
        vza = getDatafromNc(geo, 'sat_zenith_to')
        vaa = getDatafromNc(geo, 'sat_azimuth_to')

        vza = cv2.resize(vza[:, adjust_xmin_o_g:adjust_xmax_o_g],
                         (ns, nl), cv2.INTER_NEAREST)
        vaa = cv2.resize(vaa[:, adjust_xmin_o_g:adjust_xmax_o_g],
                         (ns, nl), cv2.INTER_NEAREST)

        write_image_gdal(vza, ns, nl, 1, '', '',
                         os.path.join(out_obliq, 'vza.tif'))
        write_image_gdal(vaa, ns, nl, 1, '', '',
                         os.path.join(out_obliq, 'vaa.tif'))

        lat = getDatafromNc(os.path.join(fileDir, 'geodetic_io.nc'), 'latitude_io')
        lon = getDatafromNc(os.path.join(fileDir, 'geodetic_io.nc'), 'longitude_io')

        write_image_gdal(lat[:nl, :ns], ns, nl, 1, '', '',
                         os.path.join(out_aux, 'lat_obliq.tif'))
        write_image_gdal(lon[:nl, :ns], ns, nl, 1, '', '',
                         os.path.join(out_aux, 'lon_obliq.tif'))

    if ifproj_o:
        for var in ['bt8', 'bt9', 'vza', 'vaa']:
            project_with_geoloc(
                data_tif=os.path.join(out_obliq, f'{var}.tif'),
                lon_tif=os.path.join(out_aux, 'lon_obliq.tif'),
                lat_tif=os.path.join(out_aux, 'lat_obliq.tif'),
                vrt_func=writevrt_obliq,
                out_tif=os.path.join(out_obliq, f'{var}_proj.tif')
            )

    print("  -> Done\n")
