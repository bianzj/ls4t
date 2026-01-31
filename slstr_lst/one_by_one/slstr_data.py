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

# 数据输入
indir_raw = r'/Users/bianzj/Downloads/data/slstr_raw/'
indir_med = r'/Users/bianzj/Downloads/data/slstr_med/'
indir_tif = r'/Users/bianzj/Downloads/data/slstr_tif/'
mkdir_if_not_exist(indir_med)
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
ifproj_n = 1
ifresample_n = 1


ifextract_o = 1
ifproj_o = 1
ifresample_o = 1



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
    # if day_end_hour > day_start_hour:
    #     if hh > day_start_hour and hh < day_end_hour:
    #         dayNight = 'day'
    #     else:
    #         dayNight = 'nig'
    # else:
    #     if hh >day_start_hour or hh < day_end_hour:
    #         dayNight = 'day'
    #     else:
    #         dayNight = 'nig'


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
        ns_v = ns_nadir_v_g
        nl_v = nl_nadir_v_g



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

        lat_temp = lat[500:501, 500:501]
        lon_temp = lon[500:501, 500:501]




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
                                 (ns, nl), cv2.INTER_NEAREST)
                saa = cv2.resize(saa[:, adjust_xmin_n_g:adjust_xmax_n_g],
                                 (ns, nl), cv2.INTER_NEAREST)
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

        BT8 = BT8[:nl, :]
        BT9 = BT9[:nl, :]

        # outfile = fileDir + '\\bt8.tif'
        outfile = indir_med + 'bt8.tif'
        write_image_gdal(BT8, ns, nl, 1, '', '', outfile)

        # # outfile = fileDir + '\\bt9.tif'
        outfile = indir_med + 'bt9.tif'
        write_image_gdal(BT9, ns, nl, 1, '', '', outfile)

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
                         (ns, nl), cv2.INTER_NEAREST)

        vaa = cv2.resize(vaa[:, adjust_xmin_n_g:adjust_xmax_n_g],
                         (ns, nl), cv2.INTER_NEAREST)

        outfile = indir_med + 'vza.tif'
        write_image_gdal(vza[:nl, :ns], ns, nl, 1, '', '', outfile)
        outfile = indir_med + 'vaa.tif'
        write_image_gdal(vaa[:nl, :ns], ns, nl, 1, '', '', outfile)



        '''cloud'''
        fileName = fileDir + '/flags_in.nc'
        objectName = r'cloud_in'
        cloud = getDatafromNc(fileName, objectName)

        outfile = indir_med + 'cloud.tif'
        write_image_gdal(cloud[:nl, :ns], ns, nl, 1, '', '', outfile)

        '''time'''
        # time = np.zeros([nl,ns])
        # dt = (t2 - t1) / (nl - 1)
        # for i in range(nl):
        #     t = t1 + i * dt
        #     h = math.floor(t)
        #     m = math.floor((t - h) * 60)
        #     s = round(((t - h) * 60 - m) * 60)
        #     if s==60:
        #         s=0
        #         m = m+1
        #     if m ==60:
        #         m=0
        #         h=h+1
        #     time_save = h * 10000 + m * 100 + s
        #     time[i, :] = time_save
        # outfile = indir_med + 'time.tif'
        # write_image_gdal(time[:nl, :ns], ns, nl, 1, '', '', outfile)

    if ifproj_n:
        if dayNight == "day":
            file = 'sza'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            writevrt_nadir(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            file = 'saa'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            writevrt_nadir(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            '''VNIR'''
            file = 'red'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            writevrt_v_nadir(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            file = 'nir'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            writevrt_v_nadir(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''cloud'''
        file = 'cloud'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_nadir(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''TIR'''

        file = 'bt8'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_nadir(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)


        file = 'bt9'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_nadir(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''angle'''
        file = 'vza'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_nadir(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'vaa'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_nadir(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        # file = 'time'
        # datafile = indir_med + file + '.tif'
        # xfile = indir_med + 'lon.tif'
        # yfile = indir_med + 'lat.tif'
        # vrtfile = indir_med + file + '.vrt'
        # write_vrt(vrtfile, datafile, xfile, yfile, 1500, 1200)
        # outfile = indir_med + file + '_proj.tif'
        # dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)
        # dst_ds = None


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
            writevrt_obliq(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            file = 'saa_obliq'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon_obliq.tif'
            yfile = indir_med + 'lat_obliq.tif'
            vrtfile = indir_med + file + '.vrt'
            writevrt_obliq(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            '''VNIR'''
            file = 'red_obliq'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon_obliq.tif'
            yfile = indir_med + 'lat_obliq.tif'
            vrtfile = indir_med + file + '.vrt'
            writevrt_obliq(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            file = 'nir_obliq'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon_obliq.tif'
            yfile = indir_med + 'lat_obliq.tif'
            vrtfile = indir_med + file + '.vrt'
            writevrt_obliq(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''cloud'''
        file = 'cloud_obliq'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon_obliq.tif'
        yfile = indir_med + 'lat_obliq.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_obliq(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''TIR'''

        file = 'bt8_obliq'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon_obliq.tif'
        yfile = indir_med + 'lat_obliq.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_obliq(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)


        file = 'bt9_obliq'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon_obliq.tif'
        yfile = indir_med + 'lat_obliq.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_obliq(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''angle'''
        file = 'vza_obliq'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon_obliq.tif'
        yfile = indir_med + 'lat_obliq.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_obliq(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'vaa_obliq'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon_obliq.tif'
        yfile = indir_med + 'lat_obliq.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_obliq(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)
        dst_ds = None

