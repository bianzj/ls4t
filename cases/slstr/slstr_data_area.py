from osgeo import gdal
import cv2
import numpy as np
from numpy import round, uint
from base.dates import date2DOY
from base.files import getDatafromNc, mkdir_if_not_exist, read_image_gdal, search_dir_rej, write_image_gdal
from base.raster import write_vrt
from base.spatial import geo2imagexy, geo2lonlat, imagexy2geo, lonlat2geo, resize_data
from base.slstr.slstr_grid import nl_nadir_g, nl_obliq_g, ns_nadir_g, ns_obliq_g

import sys
import os
import netCDF4
import time
import math
import warnings
warnings.filterwarnings("ignore")

'''2025.10.12 ls4t case: （注意python版本不同lonlat2geo输入顺序)'''
'''2023.10.04 增加倾斜方向日夜提取'''
'''2023.7.22 增加垂直方向夜晚提取的部分用于定标'''
'''2023.5.7 slstr 两角度数据提取（重构版）'''
'''只输出了白天的数据，方便后续用于组分温度反演'''
'''注意：不同时区一定要调day_start_hour\day_end_hour'''

'''
slstr_data_single.py
从解压后的原始数据中提取相关信息，并根据type文件进行重投影
脚本操作包括：
1. 先提出出来成tif
2. gdal进行投影转换
3. 研究区重采样
'''

# 数据输入
indir_raw = r'/home/hero/data/SLSTR_heihe/raw/'
indir_med = r'/home/hero/data/SLSTR_heihe/med/'
indir_tif = r'/home/hero/data/SLSTR_heihe/tif/'
mkdir_if_not_exist(indir_med)
mkdir_if_not_exist(indir_tif)

targetArea = r'/home/hero/data/type/type_heihe_1000_utm47N.tif'

s = 'S3'  # 同时处理S3A和S3B数据
day_start_hour = 22  # 研究区白天开始的utm小时（不含）24小时制
day_end_hour = 10  # 研究区白天开始的utm小时（不含）

adjust_xmin_n_g = 0  # 观测几何重采样用的参数
adjust_xmax_n_g = 95 + 1
adjust_xmin_o_g = 36
adjust_xmax_o_g = 94 + 1

# 数据操作
ifextract_n = 1
ifproj_n = 1
ifresample_n = 1


ifextract_o = 1
ifproj_o = 1
ifresample_o = 1


# 读取type数据
dataset = gdal.Open(targetArea)
if dataset == None:
    print(targetArea + " ")
ns_type = dataset.RasterXSize
nl_type = dataset.RasterYSize
im_bands = dataset.RasterCount
data = dataset.ReadAsArray(0, 0, ns_type, nl_type)
geog_type = dataset.GetGeoTransform()
proj_type = dataset.GetProjection()
nsi = np.zeros([nl_type, ns_type])
nli = np.zeros([nl_type, ns_type])
for k in range(nl_type):
    nli[k, :] = k
    nsi[k, :] = np.linspace(0, ns_type - 1, ns_type)
nli = np.reshape(nli,-1)
nsi = np.reshape(nsi,-1)
temp1,temp2= imagexy2geo(dataset,nli,nsi)
lon_type,lat_type = geo2lonlat(dataset,temp1,temp2)
dataset = None

# 查找数据文件夹
fileNames = search_dir_rej(indir_raw,['S3'],'zip')
fileNames.sort()
fileNum = len(fileNames)
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

    ### 测试只处理某一天的数据
    # if doy <= 182: continue

    time_str1 = fileName[25:25 + 6]
    time_str2 = fileName[41:41+6]
    hh = int(uint(time_str1[0:2]))
    mm = int(uint(time_str1[2:4]))
    ss = int(uint(time_str2[4:6]))
    # 终止时间
    hh2 = int(uint(time_str2[0:2]))
    mm2 = int(uint(time_str2[2:4]))
    ss2 = int(uint(time_str2[4:6]))
    t1 = hh + mm / 60 + ss / 3600
    t2 = hh2 + mm2 / 60 + ss2 / 3600


    # 判断日夜
    if day_end_hour > day_start_hour:
        if hh > day_start_hour and hh < day_end_hour:
            dayNight = 'day'
        else:
            dayNight = 'nig'
    else:
        if hh >day_start_hour or hh < day_end_hour:
            dayNight = 'day'
        else:
            dayNight = 'nig'

    if dayNight == 'nig':
        print("Pass nig!")
        continue  # 不输入晚上的结果

    # 判断文件是否齐全
    c1 = os.path.exists(fileDir + r'/S2_radiance_an.nc')
    c2 = os.path.exists(fileDir + r'/S3_radiance_an.nc')
    c3 = os.path.exists(fileDir + r'/geodetic_in.nc')
    c4 = os.path.exists(fileDir + r'/met_tx.nc')
    c5 = os.path.exists(fileDir + r'/S6_radiance_an.nc')
    c6 = os.path.exists(fileDir + r'/S8_BT_in.nc')
    if c1*c2*c3*c4*c5*c6 == 0:
        print("File damaged!")
        continue

    if ifextract_n:
        ns = ns_nadir_g  # 1500*1200 热红外一景图大小，可见光为3000*2400
        nl = nl_nadir_g

        if dayNight == "day":
            if dayNight == "day":
                '''提取可见光（红光、近红外）数据'''
                fileName = fileDir + '/S2_radiance_an.nc'
                objectName = r'S2_radiance_an'
                rad_red = getDatafromNc(fileName, objectName)
                fileName = fileDir + '/S2_quality_an.nc'
                objectName = r'S2_solar_irradiance_an'
                sr_red = getDatafromNc(fileName, objectName)

                fileName = fileDir + '/S3_radiance_an.nc'
                objectName = r'S3_radiance_an'
                rad_nir = getDatafromNc(fileName, objectName)
                fileName = fileDir + '/S3_quality_an.nc'
                objectName = r'S3_solar_irradiance_an'
                sr_nir = getDatafromNc(fileName, objectName)

                # 计算红光和近红外反射率
                refl_red = rad_red / (sr_red[0] / np.pi)
                refl_nir = rad_nir / (sr_nir[0] / np.pi)

                refl_red = resize_data(refl_red, nl, ns)
                outfile = indir_med + 'red.tif'
                write_image_gdal(refl_red[:nl, :ns], ns, nl, 1, '', '', outfile)

                refl_nir = resize_data(refl_nir, nl, ns)
                outfile = indir_med + 'nir.tif'
                write_image_gdal(refl_nir[:nl, :ns], ns, nl, 1, '', '', outfile)

                '''读取观测几何和云数据'''
                fileName = fileDir + '/geometry_tn.nc'
                objectName = r'solar_zenith_tn'
                sza = getDatafromNc(fileName, objectName)
                objectName = r'solar_azimuth_tn'
                saa = getDatafromNc(fileName, objectName)

                sza = cv2.resize(sza[:, adjust_xmin_n_g:adjust_xmax_n_g],
                                 (ns_nadir_g, nl_nadir_g), cv2.INTER_NEAREST)
                saa = cv2.resize(saa[:, adjust_xmin_n_g:adjust_xmax_n_g],
                                 (ns_nadir_g, nl_nadir_g), cv2.INTER_NEAREST)
                outfile = indir_med + 'sza.tif'
                write_image_gdal(sza[:nl, :ns], ns, nl, 1, '', '', outfile)
                outfile = indir_med + 'saa.tif'
                write_image_gdal(saa[:nl, :ns], ns, nl, 1, '', '', outfile)

        '''读取热红外数据'''
        fileName = fileDir + '/S8_BT_in.nc'
        objectName = r'S8_BT_in'
        BT8 = getDatafromNc(fileName, objectName)

        fileName = fileDir + '/S9_BT_in.nc'
        objectName = r'S9_BT_in'
        BT9 = getDatafromNc(fileName, objectName)

        if not (BT8.all() and BT9.all()):
            continue

        BT8 = BT8[:nl_nadir_g, :]
        BT9 = BT9[:nl_nadir_g, :]

        # outfile = fileDir + '\\bt8.tif'
        outfile = indir_med + 'bt8.tif'
        write_image_gdal(BT8, ns_nadir_g, nl_nadir_g, 1, '', '', outfile)

        # # outfile = fileDir + '\\bt9.tif'
        outfile = indir_med + 'bt9.tif'
        write_image_gdal(BT9, ns_nadir_g, nl_nadir_g, 1, '', '', outfile)

        '''读取观测几何和云数据'''
        fileName = fileDir + '/geometry_tn.nc'
        objectName = r'sat_zenith_tn'
        vza = getDatafromNc(fileName, objectName)

        objectName = r'sat_azimuth_tn'
        vaa = getDatafromNc(fileName, objectName)

        # psi = np.abs(vaa - saa)
        # if not (vza.any() and sza.all() and vaa.all() and saa.all()):
        #     continue
        vza = cv2.resize(vza[:, adjust_xmin_n_g:adjust_xmax_n_g],
                         (ns_nadir_g, nl_nadir_g), cv2.INTER_NEAREST)

        vaa = cv2.resize(vaa[:, adjust_xmin_n_g:adjust_xmax_n_g],
                         (ns_nadir_g, nl_nadir_g), cv2.INTER_NEAREST)


        # psi = resizefromSmall2Image(1, psi)
        # psi[psi > 180] = 360 - psi[psi > 180]

        outfile = indir_med + 'vza.tif'
        write_image_gdal(vza[:nl, :ns], ns, nl, 1, '', '', outfile)


        outfile = indir_med + 'vaa.tif'
        write_image_gdal(vaa[:nl, :ns], ns, nl, 1, '', '', outfile)


        '''lon and lat'''
        fileName = fileDir + '/geodetic_in.nc'
        objectName = r'latitude_in'
        lat = getDatafromNc(fileName, objectName)

        fileName = fileDir + '/geodetic_in.nc'
        objectName = r'longitude_in'
        lon = getDatafromNc(fileName, objectName)

        if not (lat.all() and lon.all()):
            continue
        outfile = indir_med + 'lat.tif'
        write_image_gdal(lat[:nl, :ns], ns, nl, 1, '', '', outfile)

        outfile = indir_med + 'lon.tif'
        write_image_gdal(lon[:nl, :ns], ns, nl, 1, '', '', outfile)

        '''cloud'''
        fileName = fileDir + '/flags_in.nc'
        objectName = r'cloud_in'
        cloud = getDatafromNc(fileName, objectName)

        outfile = indir_med + 'cloud.tif'
        write_image_gdal(cloud[:nl, :ns], ns, nl, 1, '', '', outfile)

        '''time'''
        time = np.zeros([nl,ns])
        dt = (t2 - t1) / (nl - 1)
        for i in range(nl):
            t = t1 + i * dt
            h = math.floor(t)
            m = math.floor((t - h) * 60)
            s = round(((t - h) * 60 - m) * 60)
            if s==60:
                s=0
                m = m+1
            if m ==60:
                m=0
                h=h+1
            time_save = h * 10000 + m * 100 + s
            time[i, :] = time_save
        outfile = indir_med + 'time.tif'
        write_image_gdal(time[:nl, :ns], ns, nl, 1, '', '', outfile)

    if ifproj_n:
        if dayNight == "day":
            file = 'sza'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            file = 'saa'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            '''VNIR'''
            file = 'red'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            file = 'nir'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''cloud'''
        file = 'cloud'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''TIR'''

        file = 'bt8'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)


        file = 'bt9'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''angle'''
        file = 'vza'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'vaa'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'time'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)
        dst_ds = None

    if ifresample_n:
        ns = ns_type
        nl = nl_type
        geog = geog_type
        proj = proj_type

        outfile0 = symbol + '_%4d_' % year + '%03d' % doy + "_"

        outfile1 = indir_tif + outfile0 + dayNight +'_bt1_nadir.tif'
        outfile2 = indir_tif + outfile0 + dayNight +'_bt2_nadir.tif'
        outfile3 = indir_tif + outfile0 + dayNight +'_red_nadir.tif'
        outfile4 = indir_tif + outfile0 + dayNight +'_nir_nadir.tif'
        outfile5 = indir_tif + outfile0 + dayNight +'_vza_nadir.tif'
        outfile6 = indir_tif + outfile0 + dayNight +'_sza_nadir.tif'
        outfile8 = indir_tif + outfile0 + dayNight +'_time.tif'
        outfile9 = indir_tif + outfile0 + dayNight +'_vaa_nadir.tif'
        outfile10 = indir_tif + outfile0 + dayNight +'_saa_nadir.tif'
        outfile11 = indir_tif + outfile0 + dayNight +'_cloud_nadir.tif'

        if os.path.exists(outfile1) == 1:
            [data1, temp1, temp2, temp3, geog, proj] = read_image_gdal(outfile1)
            [data2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile2)
            [data5, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile5)
            [data8, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile8)
            [data11, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile11)
            [data9, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile9)

            if dayNight == "day":
                [data3, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile3)
                [data4, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile4)
                [data6, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile6)
                [data10, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile10)

        else:
            data1 = np.zeros([nl, ns])
            data2 = np.zeros([nl, ns])
            data5 = np.zeros([nl, ns])
            data11 = np.zeros([nl, ns])
            data8 = np.zeros([nl, ns])
            data3 = np.zeros([nl, ns])
            data4 = np.zeros([nl, ns])
            data6 = np.zeros([nl, ns])
            data9 = np.zeros([nl, ns])
            data10 = np.zeros([nl, ns])

        '''类重采样'''
        # BT8
        infile = indir_med + r'bt8_proj.tif'
        dataset = gdal.Open(infile)
        if dataset == None:
            print(infile + " ")
            continue
        im_width = dataset.RasterXSize * 1
        im_height = dataset.RasterYSize * 1
        im_bands = dataset.RasterCount * 1
        data = dataset.ReadAsArray(0, 0, im_width, im_height)
        im_geotrans = dataset.GetGeoTransform()
        im_proj = dataset.GetProjection()
        temp1, temp2 = lonlat2geo(dataset, lon_type, lat_type)
        imagex, imagey = geo2imagexy(dataset, temp1, temp2)
        print(imagex,imagey)
        dataset = None

        imagex = np.asarray(imagex, int)
        imagey = np.asarray(imagey, int)
        ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
        imagex[imagex < 0] = 0
        imagex[imagex > (im_height - 1)] = im_height - 1
        imagey[imagey < 0] = 0
        imagey[imagey > (im_width - 1)] = im_width - 1
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 200) * ind
        if np.sum(indnew) == 0: continue

        data1 = np.reshape(data1, [-1])
        data1[indnew] = temp[indnew]
        data1 = np.reshape(data1, [nl, ns])
        data1[data1 < 0] = 0
        data1[data1 > 500] = 0

        if dayNight == "day":
            # red
            infile = indir_med + r'red_proj.tif'
            [data_satellite, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            data_satellite = resize_data(data_satellite, im_height, im_width, 0)
            temp = data_satellite[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data3 = np.reshape(data3, [-1])
            data3[indnew] = temp[indnew]
            data3 = np.reshape(data3, [nl, ns])
            data3[data3 < 0] = 0
            data3[data3 > 500] = 0

            # nir
            infile = indir_med + r'nir_proj.tif'
            [data_satellite, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            data_satellite = resize_data(data_satellite, im_height, im_width)
            temp = data_satellite[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data4 = np.reshape(data4, [-1])
            data4[indnew] = temp[indnew]
            data4 = np.reshape(data4, [nl, ns])
            data4[data4 < 0] = 0
            data4[data4 > 500] = 0

            # sza
            infile = indir_med + r'sza_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data6 = np.reshape(data6, [-1])
            data6[indnew] = temp[indnew]
            data6 = np.reshape(data6, [nl, ns])
            data6[data6 < 0] = 0
            data6[data6 > 500] = 0

            # saa
            infile = indir_med + r'saa_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data10 = np.reshape(data10, [-1])
            data10[indnew] = temp[indnew]
            data10 = np.reshape(data10, [nl, ns])
            data10[data10 < 0] = 0
            data10[data10 > 500] = 0

            write_image_gdal(data3, ns, nl, 1, geog, proj, outfile3)
            write_image_gdal(data4, ns, nl, 1, geog, proj, outfile4)
            write_image_gdal(data6, ns, nl, 1, geog, proj, outfile6)
            write_image_gdal(data10, ns, nl, 1, geog, proj, outfile10)

        # BT9
        infile = indir_med + r'bt9_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 200) * ind
        data2 = np.reshape(data2, [-1])
        data2[indnew] = temp[indnew]
        data2 = np.reshape(data2, [nl, ns])
        data2[data2 < 0] = 0
        data2[data2 > 500] = 0

        # time
        # data8 = np.reshape(data8, [-1])
        # temp[:] = np.int(np.uint(time_str))
        # data8[indnew] = temp[indnew]
        # data8 = np.reshape(data8, [nl, ns])
        infile = indir_med + r'time_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp > 0) * ind * (temp != 65535)
        data8 = np.reshape(data8, [-1])
        data8[indnew] = temp[indnew]
        data8 = np.reshape(data8, [nl, ns])

        # vza
        infile = indir_med + r'vza_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 0) * ind
        data5 = np.reshape(data5, [-1])
        data5[indnew] = temp[indnew]
        data5 = np.reshape(data5, [nl, ns])
        data5[data5 < 0] = 0
        data5[data5 > 500] = 0

        # cloud
        infile = indir_med + r'cloud_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 0) * ind
        data11 = np.reshape(data11, [-1])
        data11[indnew] = temp[indnew]
        data11 = np.reshape(data11, [nl, ns])
        data11[data11 < 0] = 0
        data11[data11 > 500] = 0


        # vaa
        infile = indir_med + r'vaa_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 0) * ind
        data9 = np.reshape(data9, [-1])
        data9[indnew] = temp[indnew]
        data9 = np.reshape(data9, [nl, ns])
        data9[data9 < 0] = 0
        data9[data9 > 500] = 0



        write_image_gdal(data1, ns, nl, 1, geog, proj, outfile1)
        write_image_gdal(data2, ns, nl, 1, geog, proj, outfile2)
        write_image_gdal(data5, ns, nl, 1, geog, proj, outfile5)
        write_image_gdal(data8, ns, nl, 1, geog, proj, outfile8)
        write_image_gdal(data11, ns, nl, 1, geog, proj, outfile11)
        write_image_gdal(data9, ns, nl, 1, geog, proj, outfile9)


    if ifextract_o:
        ns = ns_obliq_g  # 900*1200 热红外一景图大小，可见光为3000*2400
        nl = nl_obliq_g
        if dayNight == "day":
            '''提取可见光（红光、近红外）数据'''
            fileName = fileDir + '/S2_radiance_ao.nc'
            objectName = r'S2_radiance_ao'
            rad_red = getDatafromNc(fileName, objectName)
            fileName = fileDir + '/S2_quality_ao.nc'
            objectName = r'S2_solar_irradiance_ao'
            sr_red = getDatafromNc(fileName, objectName)

            fileName = fileDir + '/S3_radiance_ao.nc'
            objectName = r'S3_radiance_ao'
            rad_nir = getDatafromNc(fileName, objectName)
            fileName = fileDir + '/S3_quality_ao.nc'
            objectName = r'S3_solar_irradiance_ao'
            sr_nir = getDatafromNc(fileName, objectName)

            # 计算红光和近红外反射率
            refl_red = rad_red / (sr_red[0] / np.pi)
            refl_nir = rad_nir / (sr_nir[0] / np.pi)

            refl_red = resize_data(refl_red, nl, ns)
            outfile = indir_med + 'red_obliq.tif'
            write_image_gdal(refl_red[:nl, :ns], ns, nl, 1, '', '', outfile)

            refl_nir = resize_data(refl_nir, nl, ns)
            outfile = indir_med + 'nir_obliq.tif'
            write_image_gdal(refl_nir[:nl, :ns], ns, nl, 1, '', '', outfile)

            '''读取观测几何和云数据'''
            fileName = fileDir + '/geometry_to.nc'
            objectName = r'solar_zenith_to'
            sza = getDatafromNc(fileName, objectName)

            objectName = r'solar_azimuth_to'
            saa = getDatafromNc(fileName, objectName)

            sza = cv2.resize(sza[:, adjust_xmin_o_g:adjust_xmax_o_g],
                             (ns_obliq_g, nl_obliq_g), cv2.INTER_NEAREST)
            saa = cv2.resize(saa[:, adjust_xmin_o_g:adjust_xmax_o_g],
                         (ns_obliq_g, nl_obliq_g), cv2.INTER_NEAREST)
            outfile = indir_med + 'sza_obliq.tif'
            write_image_gdal(sza[:nl, :ns], ns, nl, 1, '', '', outfile)
            outfile = indir_med + 'saa_obliq.tif'
            write_image_gdal(saa[:nl, :ns], ns, nl, 1, '', '', outfile)

        '''读取热红外数据'''
        fileName = fileDir + '/S8_BT_io.nc'
        objectName = r'S8_BT_io'
        BT8 = getDatafromNc(fileName, objectName)

        fileName = fileDir + '/S9_BT_io.nc'
        objectName = r'S9_BT_io'
        BT9 = getDatafromNc(fileName, objectName)

        if not (BT8.all() and BT9.all()):
            continue

        BT8 = BT8[:nl_nadir_g, :]
        BT9 = BT9[:nl_nadir_g, :]

        # outfile = fileDir + '\\bt8.tif'
        outfile = indir_med + 'bt8_obliq.tif'
        write_image_gdal(BT8, ns_nadir_g, nl_nadir_g, 1, '', '', outfile)

        # # outfile = fileDir + '\\bt9.tif'
        outfile = indir_med + 'bt9_obliq.tif'
        write_image_gdal(BT9, ns_nadir_g, nl_nadir_g, 1, '', '', outfile)

        '''读取观测几何和云数据'''
        fileName = fileDir + '/geometry_to.nc'
        objectName = r'sat_zenith_to'
        vza = getDatafromNc(fileName, objectName)
        objectName = r'sat_azimuth_to'
        vaa = getDatafromNc(fileName, objectName)

        # psi = np.abs(vaa - saa)
        # if not (vza.any() and sza.all() and vaa.all() and saa.all()):
        #     continue
        vza = cv2.resize(vza[:, adjust_xmin_o_g:adjust_xmax_o_g],
                         (ns_obliq_g, nl_obliq_g), cv2.INTER_NEAREST)
        vaa = cv2.resize(vaa[:, adjust_xmin_o_g:adjust_xmax_o_g],
                         (ns_obliq_g, nl_obliq_g), cv2.INTER_NEAREST)

        # psi = resizefromSmall2Image(1, psi)
        # psi[psi > 180] = 360 - psi[psi > 180]

        outfile = indir_med + 'vza_obliq.tif'
        write_image_gdal(vza[:nl, :ns], ns, nl, 1, '', '', outfile)

        outfile = indir_med + 'vaa_obliq.tif'
        write_image_gdal(vaa[:nl, :ns], ns, nl, 1, '', '', outfile)

        '''lon and lat'''
        fileName = fileDir + '/geodetic_io.nc'
        objectName = r'latitude_io'
        lat = getDatafromNc(fileName, objectName)

        fileName = fileDir + '/geodetic_io.nc'
        objectName = r'longitude_io'
        lon = getDatafromNc(fileName, objectName)

        if not (lat.all() and lon.all()):
            continue
        outfile = indir_med + 'lat_obliq.tif'
        write_image_gdal(lat[:nl, :ns], ns, nl, 1, '', '', outfile)

        outfile = indir_med + 'lon_obliq.tif'
        write_image_gdal(lon[:nl, :ns], ns, nl, 1, '', '', outfile)

        '''cloud'''
        fileName = fileDir + '/flags_io.nc'
        objectName = r'cloud_io'
        cloud = getDatafromNc(fileName, objectName)

        outfile = indir_med + 'cloud_obliq.tif'
        write_image_gdal(cloud[:nl, :ns], ns, nl, 1, '', '', outfile)

    if ifproj_o:
        if dayNight == "day":
            file = 'sza_obliq'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon_obliq.tif'
            yfile = indir_med + 'lat_obliq.tif'
            vrtfile = indir_med + file + '.vrt'
            write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            file = 'saa_obliq'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon_obliq.tif'
            yfile = indir_med + 'lat_obliq.tif'
            vrtfile = indir_med + file + '.vrt'
            write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            '''VNIR'''
            file = 'red_obliq'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon_obliq.tif'
            yfile = indir_med + 'lat_obliq.tif'
            vrtfile = indir_med + file + '.vrt'
            write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            file = 'nir_obliq'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon_obliq.tif'
            yfile = indir_med + 'lat_obliq.tif'
            vrtfile = indir_med + file + '.vrt'
            write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''cloud'''
        file = 'cloud_obliq'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon_obliq.tif'
        yfile = indir_med + 'lat_obliq.tif'
        vrtfile = indir_med + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''TIR'''

        file = 'bt8_obliq'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon_obliq.tif'
        yfile = indir_med + 'lat_obliq.tif'
        vrtfile = indir_med + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)


        file = 'bt9_obliq'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon_obliq.tif'
        yfile = indir_med + 'lat_obliq.tif'
        vrtfile = indir_med + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''angle'''
        file = 'vza_obliq'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon_obliq.tif'
        yfile = indir_med + 'lat_obliq.tif'
        vrtfile = indir_med + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'vaa_obliq'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon_obliq.tif'
        yfile = indir_med + 'lat_obliq.tif'
        vrtfile = indir_med + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)
        dst_ds = None

    if ifresample_o:
        ns = ns_type
        nl = nl_type
        geog = geog_type
        proj = proj_type

        outfile0 = symbol + '_%4d_' % year + '%03d' % doy+ "_"

        outfile1 = indir_tif + outfile0 + dayNight+ '_bt1_obliq.tif'
        outfile2 = indir_tif + outfile0 + dayNight+ '_bt2_obliq.tif'
        outfile3 = indir_tif + outfile0 + dayNight+ '_red_obliq.tif'
        outfile4 = indir_tif + outfile0 + dayNight+ '_nir_obliq.tif'
        outfile5 = indir_tif + outfile0 + dayNight+ '_vza_obliq.tif'
        outfile6 = indir_tif + outfile0 + dayNight+ '_sza_obliq.tif'
        outfile8 = indir_tif + outfile0 + dayNight+ '_time_obliq.tif'
        outfile9 = indir_tif + outfile0 + dayNight+ '_vaa_obliq.tif'
        outfile10 = indir_tif + outfile0 + dayNight+ '_saa_obliq.tif'
        outfile11 = indir_tif + outfile0 + dayNight+ '_cloud_obliq.tif'

        if os.path.exists(outfile1) == 1:
            [data1, temp1, temp2, temp3, geog, proj] = read_image_gdal(outfile1)
            [data2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile2)
            [data5, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile5)
            # [data8, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile8)
            [data9, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile9)
            [data11, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile11)
            if dayNight == "day":
                [data3, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile3)
                [data4, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile4)
                [data6, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile6)
                [data10, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile10)
        else:
            data1 = np.zeros([nl, ns])
            data2 = np.zeros([nl, ns])
            data5 = np.zeros([nl, ns])
            data11 = np.zeros([nl, ns])
            data8 = np.zeros([nl, ns])
            data3 = np.zeros([nl, ns])
            data4 = np.zeros([nl, ns])
            data6 = np.zeros([nl, ns])
            data9 = np.zeros([nl, ns])
            data10 = np.zeros([nl, ns])
        '''类重采样'''
        # BT8
        infile = indir_med + r'bt8_obliq_proj.tif'
        dataset = gdal.Open(infile)
        if dataset == None:
            print(infile + " ")
            continue
        im_width = dataset.RasterXSize * 1
        im_height = dataset.RasterYSize * 1
        im_bands = dataset.RasterCount * 1
        data = dataset.ReadAsArray(0, 0, im_width, im_height)
        im_geotrans = dataset.GetGeoTransform()
        im_proj = dataset.GetProjection()
        temp1, temp2 = lonlat2geo(dataset, lon_type, lat_type)
        imagex, imagey = geo2imagexy(dataset, temp1, temp2)
        dataset = None

        imagex = np.asarray(imagex, int)
        imagey = np.asarray(imagey, int)
        ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
        imagex[imagex < 0] = 0
        imagex[imagex > (im_height - 1)] = im_height - 1
        imagey[imagey < 0] = 0
        imagey[imagey > (im_width - 1)] = im_width - 1
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 200) * ind
        if np.sum(indnew) == 0: continue

        data1 = np.reshape(data1, [-1])
        data1[indnew] = temp[indnew]
        data1 = np.reshape(data1, [nl, ns])
        data1[data1 < 0] = 0
        data1[data1 > 500] = 0

        # BT9
        infile = indir_med + r'bt9_obliq_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 200) * ind
        data2 = np.reshape(data2, [-1])
        data2[indnew] = temp[indnew]
        data2 = np.reshape(data2, [nl, ns])
        data2[data2 < 0] = 0
        data2[data2 > 500] = 0

        # # time
        # data8 = np.reshape(data8, [-1])
        # temp[:] = np.int(np.uint(time_str))
        # data8[indnew] = temp[indnew]
        # data8 = np.reshape(data8, [nl, ns])

        # vza
        infile = indir_med + r'vza_obliq_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 0) * ind
        data5 = np.reshape(data5, [-1])
        data5[indnew] = temp[indnew]
        data5 = np.reshape(data5, [nl, ns])
        data5[data5 < 0] = 0
        data5[data5 > 500] = 0

        # vaa
        infile = indir_med + r'vaa_obliq_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500.0) * (temp > 0.0) * ind
        data9 = np.reshape(data9, [-1])
        data9[indnew] = temp[indnew]
        data9 = np.reshape(data9, [nl, ns])
        data9[data9 < 0.0] = 0
        data9[data9 > 500.0] = 0

        # cloud
        infile = indir_med + r'cloud_obliq_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 0) * ind
        data11 = np.reshape(data11, [-1])
        data11[indnew] = temp[indnew]
        data11 = np.reshape(data11, [nl, ns])
        data11[data11 < 0] = 0
        data11[data11 > 500] = 0



        if dayNight == "day":
            # red
            infile = indir_med + r'red_obliq_proj.tif'
            [data_satellite, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            data_satellite = resize_data(data_satellite, im_height, im_width, 0)
            temp = data_satellite[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data3 = np.reshape(data3, [-1])
            data3[indnew] = temp[indnew]
            data3 = np.reshape(data3, [nl, ns])
            data3[data3 < 0] = 0
            data3[data3 > 500] = 0

            # nir
            infile = indir_med + r'nir_obliq_proj.tif'
            [data_satellite, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            data_satellite = resize_data(data_satellite, im_height, im_width)
            temp = data_satellite[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data4 = np.reshape(data4, [-1])
            data4[indnew] = temp[indnew]
            data4 = np.reshape(data4, [nl, ns])
            data4[data4 < 0] = 0
            data4[data4 > 500] = 0

            # sza
            infile = indir_med + r'sza_obliq_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data6 = np.reshape(data6, [-1])
            data6[indnew] = temp[indnew]
            data6 = np.reshape(data6, [nl, ns])
            data6[data6 < 0] = 0
            data6[data6 > 500] = 0

            # saa
            infile = indir_med + r'saa_obliq_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data10 = np.reshape(data10, [-1])
            data10[indnew] = temp[indnew]
            data10 = np.reshape(data10, [nl, ns])
            data10[data10 < 0] = 0
            data10[data10 > 500] = 0

            write_image_gdal(data3, ns, nl, 1, geog, proj, outfile3)
            write_image_gdal(data4, ns, nl, 1, geog, proj, outfile4)
            write_image_gdal(data6, ns, nl, 1, geog, proj, outfile6)
            write_image_gdal(data10, ns, nl, 1, geog, proj, outfile10)


        write_image_gdal(data1, ns, nl, 1, geog, proj, outfile1)
        write_image_gdal(data2, ns, nl, 1, geog, proj, outfile2)
        write_image_gdal(data5, ns, nl, 1, geog, proj, outfile5)
        # write_image_gdal(data8, ns, nl, 1, geog, proj, outfile8)
        write_image_gdal(data9, ns, nl, 1, geog, proj, outfile9)
        write_image_gdal(data11, ns, nl, 1, geog, proj, outfile11)
