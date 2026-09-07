import matplotlib.pyplot as plt
import numpy as np
from base.util_lst import *
from base.util_data import *
from base.util_fitting import *
from base.util_kernel import *
from base.util_file import *
import h5py
import seaborn as sns
import seaborn_image as isns
import pandas as pd
from pvlib import atmosphere
import pvlib
from pvlib.location import Location
from osgeo import gdal
from osgeo import osr
import os
import pyresample as pr
from satpy import Scene
import satpy


def write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff',
                     nodata_value=None):
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


deg2rad = np.pi / 180
NS_PER_HR = 1.e9 * 3600.
elev = 0
altitude = 0
pressure = 1013.25  # 单位：mb
atmos_refract = 0.5667

indir_raw = r"/Users/bianzj/Downloads/data/msg/euro_raw/"
indir_tif = r"/Users/bianzj/Downloads/data/msg/euro_tif/"
indir_lst = r"/Users/bianzj/Downloads/data/msg/euro_lst/"
indir_base = "/Users/bianzj/Downloads/data/msg/Static/"

# 读取经纬度
infile = os.path.join(indir_base, "EURO_lat.tif")
lat0_, ns, nl, nb, geog, proj = read_image_gdal(infile)
infile = os.path.join(indir_base, "EURO_lon.tif")
lon0_, ns, nl, nb, geog, proj = read_image_gdal(infile)

lat0_ = lat0_ / 100.0
lon0_ = lon0_ / 100.0
ns_short = np.int16(ns / 20)
nl_short = np.int16(nl / 20)
lat_ = resize_data(lat0_, nl_short, ns_short)
lon_ = resize_data(lon0_, nl_short, ns_short)

# 修正 NaN 报错
ind = (lat_ < -90) | (lat_ > 90)
lat_[ind] = np.nan
lon_[ind] = np.nan

for kyear in range(2017, 2018):
    for kmonth in range(7, 8):
        for kday in range(1, 2):
            day_str_path = f'{kyear:04d}/{kmonth:02d}/{kday:02d}/'
            indir_temp = os.path.join(indir_raw, day_str_path)
            outdir_temp = os.path.join(indir_tif, day_str_path)

            files = search_file(indir_temp, "nat")
            if len(files) == 0: continue

            mkdir_if_not_exist(outdir_temp)

            for kfile in range(len(files)):
                file = files[kfile]
                infile = os.path.join(indir_temp, file)
                print(f"Processing: {infile}")

                # 解析时间
                date_str = file[-32:-24]
                hh_int = int(file[-24:-22])
                mn_int = int(file[-22:-20])

                # if hh_int <= 3 or hh_int >= 20: continue

                # 优化 Satpy 读取：只实例化一次并批量 load
                scn = Scene(filenames={"seviri_l1b_native": [infile]}, reader_kwargs={'fill_disk': True})

                # 一次性加载所有需要的通道
                channels = ['VIS006', 'VIS008', 'IR_016', 'IR_108', 'IR_120']
                scn.load(['IR_108', 'IR_120'], calibration='brightness_temperature')
                IR108_bt = np.uint16(scn['IR_108'].values * 100)
                IR120_bt = np.uint16(scn['IR_120'].values * 100)

                # 计算太阳角度

                # 保存结果
                write_image_gdal(IR108_bt, ns, nl, 1, "", "", os.path.join(outdir_temp, file + "_bt8.tif"))
                write_image_gdal(IR120_bt, ns, nl, 1, "", "", os.path.join(outdir_temp, file + "_bt9.tif"))
                if (hh_int > 7) & (hh_int < 19):
                    scn.load(['VIS006', 'VIS008', 'IR_016'], calibration='reflectance')
                    VIS006_ref = np.uint16(scn['VIS006'].values * 100)
                    VIS008_ref = np.uint16(scn['VIS008'].values * 100)
                    # IR016_ref = np.uint16(scn['IR_016'].values*100)
                    time_val = pd.to_datetime(f"{date_str} {hh_int:02d}:{mn_int:02d}:00").tz_localize('UTC')
                    site_temp = Location(lat_.flatten(), lon_.flatten(), 'Etc/GMT', altitude, 'None')
                    nloc = len(lat_.flatten())
                    solpos_temp = pvlib.solarposition.get_solarposition(np.repeat(time_val, nloc), site_temp.latitude,
                                                                        site_temp.longitude, site_temp.altitude,
                                                                        method='nrel_numpy')
                    sza_temp = solpos_temp['zenith'].to_numpy().reshape(lat_.shape).astype(np.float32)
                    saa_temp = solpos_temp['azimuth'].to_numpy().reshape(lat_.shape).astype(np.float32)

                    write_image_gdal(sza_temp, ns_short, nl_short, 1, "", "",
                                     os.path.join(outdir_temp, file + "_sza.tif"))
                    write_image_gdal(saa_temp, ns_short, nl_short, 1, "", "",
                                     os.path.join(outdir_temp, file + "_saa.tif"))
                    write_image_gdal(VIS006_ref, ns, nl, 1, "", "", os.path.join(outdir_temp, file + "_red.tif"))
                    write_image_gdal(VIS008_ref, ns, nl, 1, "", "", os.path.join(outdir_temp, file + "_nir.tif"))

