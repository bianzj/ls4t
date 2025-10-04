import glob
from satpy.scene import Scene
from util.util import *
import zipfile
import os
from datetime import datetime
from pyorbital import astronomy
import calendar
from scipy.interpolate import interp1d

import warnings
warnings.filterwarnings("ignore")

'''用于处理MSG的SEVIRI数据'''
'''此脚本用于处理native格式的数据,satpy需要使用python3.8以上版本运行'''
'''提取光学2个和热红外2个以及太阳角度2个'''


indir_zip = r'F:\data\MSG_2017_full-range\zip\\'
indir_raw = r'F:\data\MSG_2017_full-range\native\raw\\'
indir_med = r'F:\data\MSG_2017_full-range\native\med2\\'
indir_tif = r'F:\data\MSG_2017_full-range\native\tif2\Full\\'
# indir_tif = r'F:\data\MSG_2017_full-range\native\tif\Europe\\'
# indir_tif = r'F:\data\MSG_2017_full-range\native\tif\Africa\\'



# type无用
# indir_type = r'D:\data\type\\'
# infile_type = indir_type + "type_MSG_0.03.tif"
year = 2017

# 解压zip文件，并只解压出.nat文件
ifunzip = 0

# 提取需要的数据并保存成tif
ifextract = 0

# 重投影，定义投影方式
ifproj = 1
SpatialRange = (-80.0, -80.0, 80, 80.0)   # 全图
# SpatialRange = (-10, 36, 67, 72)   # 欧洲
# SpatialRange = (-18, -35, 52, 38)   # 非洲

# 用于将结果重投影，静止卫星找去找tif，有很多空洞，未用
ifproj2 = 0

# 用于从nc文件中提取精确时间,流程可不用
iftime = 0

# 用于计算准确的太阳角度
ifcalsun = 1
infile_time = r"D:\data\base\msg_angle\\MSG_time_proj.tif"

if ifunzip:
    for m in range(1,2):
        daynum = calendar.monthrange(year, m + 1)[1]
        for d in range(daynum):
            month = m + 1
            day = d + 1
            indir_zip_day = indir_zip + "/%02d" % month + "/%02d//" % day
            indir_raw_day = indir_raw + "/%02d" % month + "/%02d//" % day
            if not os.path.exists(indir_zip_day): continue
            fileNames = search_file(indir_zip_day, ['.zip'])
            for fileName in fileNames:
                mkdir_if_not_exist(indir_raw_day)
                fName = fileName[:-4] + ".nat"
                print(fName)
                zip_path = indir_zip_day + fileName
                save_path = indir_raw_day

                if os.path.exists(save_path + fName): continue

                # 读取压缩文件
                file = zipfile.ZipFile(zip_path)
                # 解压文件
                file.extract(fName, save_path)
                print(fName + '  unzip successful!')
                # 关闭文件流
                file.close()

if ifextract:
    for m in range(1,2):
        daynum = calendar.monthrange(year, m + 1)[1]
        for d in range(daynum):
            month = m + 1
            day = d + 1
            indir_raw_day = indir_raw + "/%02d" % month + "/%02d//" % day
            fnames = search_file(indir_raw_day, '.nat')
            for fname in fnames:
                print(fname)

                '''时间信息'''
                time_str = fname[24:36]
                year = int(time_str[0:4])
                month = int(time_str[4:6])
                day = int(time_str[6:8])
                end_hh = int(time_str[8:10])
                end_mm = int(time_str[10:12])
                start_hh = (end_hh * 60 + end_mm - 12) // 60
                start_mm = (end_hh * 60 + end_mm - 12) % 60
                time_str_save = "%04d" % year + "%02d" % month + "%02d" % day + "%02d" % start_hh + "%02d" % start_mm
                MSG_symbol = fname[0:4] + "_"

                indir_med_day = indir_med  + "//%02d" % month + "//%02d//" % day
                mkdir_if_not_exist(indir_med_day)

                '''读取文件'''
                fn = glob.glob(indir_raw_day + r"*" + time_str + "*")
                scn = Scene(fn, reader='seviri_l1b_native')
                # print(scn.available_dataset_names())
                # print(scn.available_dataset_ids())
                scn.load(['VIS006', 'VIS008'], upper_right_corner='NE')

                '''读取经纬度'''
                vis006 = scn["VIS006"]
                lon, lat = vis006.attrs['area'].get_lonlats()

                '''读取可见光和红外'''
                vis006 = scn["VIS006"]
                vis006_meas = vis006.values

                vis008 = scn["VIS008"]
                vis008_meas = vis008.values

                scn.load(['IR_108', 'IR_120'], upper_right_corner='NE')

                ir108 = scn["IR_108"]
                ir108_meas = ir108.values

                ir120 = scn["IR_120"]
                ir120_meas = ir120.values

                '''计算太阳角度'''
                utc_time = datetime(year, month, day, start_hh, start_mm + 6)
                # '''精确时间信息'''
                # [time, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(indir_time)
                # min = start_mm + time // 60
                # sec = time % 60
                # utc_time = datetime(year, month, day, start_hh, min, sec)

                sza = np.zeros([3712, 3712])
                saa = np.zeros([3712, 3712])
                angle = astronomy.get_alt_az(utc_time, lon, lat)
                temp = angle[0] * 180 / np.pi
                ind = angle[0] >= 0
                sza[ind] = 90 - temp[ind]
                ind = angle[0] < 0
                sza[ind] = -90 - temp[ind]

                saa = angle[1] * 180 / np.pi + 360
                saa[saa >= 360] = saa[saa >= 360] - 360

                '''输出'''
                outfile_lon = indir_med + 'lon.tif'
                outfile_lat = indir_med + 'lat.tif'
                if not os.path.exists(outfile_lon):
                    write_image_gdal(lon, 3712, 3712, 1, '', '', outfile_lon)
                    write_image_gdal(lat, 3712, 3712, 1, '', '', outfile_lat)

                outfile_red = indir_med_day + MSG_symbol + time_str_save + "_red.tif"
                outfile_nir = indir_med_day + MSG_symbol + time_str_save + "_nir.tif"
                outfile_bt1 = indir_med_day + MSG_symbol + time_str_save + "_bt1.tif"
                outfile_bt2 = indir_med_day + MSG_symbol + time_str_save + "_bt2.tif"
                outfile_sza = indir_med_day + MSG_symbol + time_str_save + "_sza.tif"
                outfile_saa = indir_med_day + MSG_symbol + time_str_save + "_saa.tif"

                write_image_gdal(vis006_meas, 3712, 3712, 1, '', '', outfile_red)
                write_image_gdal(vis008_meas, 3712, 3712, 1, '', '', outfile_nir)
                write_image_gdal(ir108_meas, 3712, 3712, 1, '', '', outfile_bt1)
                write_image_gdal(ir120_meas, 3712, 3712, 1, '', '', outfile_bt2)
                write_image_gdal(sza, 3712, 3712, 1, '', '', outfile_sza)
                write_image_gdal(saa, 3712, 3712, 1, '', '', outfile_saa)

if ifproj:
    # img_proj = ccrs.Geostationary(satellite_height=35786000)
    outfile_lon = indir_med + 'lon.tif'
    outfile_lat = indir_med + 'lat.tif'
    [lon, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile_lon)
    [lat, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile_lat)

    for m in range(1,2):
        daynum = calendar.monthrange(year, m + 1)[1]
        for d in range(daynum):
            month = m + 1
            day = d + 1
            indir_med_day = indir_med  + "/%02d" % month + "/%02d//" % day
            if not os.path.exists(indir_med_day): continue
            fileNames = search_file_rej(indir_med_day, ['bt1'], '.xml')
            indir_tif_day = indir_tif  + "/%02d" % month + "/%02d//" % day
            for i in range(len(fileNames)):
                '''读取时间信息'''
                fileName = fileNames[i]
                print(fileName)
                MSG_symbol = fileName[0:5]
                time_str = fileName[-20:-8]
                hh = int(time_str[-4:-2])
                mm = int(time_str[-2:])


                '''读取数据并重投影'''
                fn = fileName[:-7]
                infile_bt1 = indir_med_day + fn + "bt1.tif"
                infile_bt2 = indir_med_day + fn + "bt2.tif"
                infile_red = indir_med_day + fn + "red.tif"
                infile_nir = indir_med_day + fn + "nir.tif"
                infile_sza = indir_med_day + fn + "sza.tif"
                infile_saa = indir_med_day + fn + "saa.tif"

                outfile_bt1 = indir_tif_day + fn + "bt1.tif"
                outfile_bt2 = indir_tif_day + fn + "bt2.tif"
                outfile_red = indir_tif_day + fn + "red.tif"
                outfile_nir = indir_tif_day + fn + "nir.tif"
                outfile_sza = indir_tif_day + fn + "sza.tif"
                outfile_saa = indir_tif_day + fn + "saa.tif"

                mkdir_if_not_exist(indir_tif_day)

                # 几何校正
                # 定义空间参考
                cols = 3712
                rows = 3712
                res = 0.03000403165817

                srs = osr.SpatialReference()
                # 定义地球长半轴a=6378137.0m，地球短半轴b=6356752.3m，卫星星下点所在经度0.0，目标空间参考
                srs.ImportFromProj4('+proj=geos +h=35785863 +a=6378137.0 +b=6356752.3 +lon_0=0.0 +no_defs')

                items = ["bt1","bt2","red","nir","sza","saa"]
                for item in items:
                    infile = indir_med_day + fn + item + ".tif"
                    outfile = indir_tif_day + fn + item + ".tif"
                    data = gdal.Open(infile)
                    data.SetProjection(srs.ExportToWkt())
                    # 左上角x坐标， 水平分辨率，旋转参数， 左上角y坐标，旋转参数，竖直分辨率
                    data.SetGeoTransform(
                        [-cols * res * 50000, int(res * 100000), 0, cols * res * 50000, 0, int(-res * 100000)])
                    if os.path.exists(outfile):
                        continue
                    print(outfile)
                    warpDs = gdal.Warp(outfile, data, dstSRS='EPSG:4326', outputBounds=SpatialRange,
                                       xRes=0.03, yRes=0.03)
                    del warpDs

if ifproj2:
    # 效果不好，未采纳
    outfile_lon = indir_med + 'lon.tif'
    outfile_lat = indir_med + 'lat.tif'
    [lon, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile_lon)
    [lat, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile_lat)

    '''找投影位置'''
    [classif, ns, nl, nb, geog, proj] = read_image_gdal(infile_type)
    dataset = gdal.Open(infile_type)
    indx, indy = loc2map(lat, lon, dataset)
    ind = (indx > 0) * (indx < nl - 1) * (indy > 0) * (indy < ns - 1)
    indx[indx < 0] = 0
    indx[indx > (nl - 1)] = nl - 1
    indy[indy < 0] = 0
    indy[indy > (ns - 1)] = ns - 1


    for m in range(12):
        daynum =  calendar.monthrange(year,m+1)[1]
        for d in range(daynum):
            month = m + 1
            day = d + 1
            indir_med_day = indir_med + "/%04d" % year + "/%02d" % month + "/%02d//" % day
            if not os.path.exists(indir_med_day): continue
            fileNames = search_file_rej(indir_med_day,['bt1'],'enp')
            indir_tif_day = indir_tif + "/%04d" % year + "/%02d" % month + "/%02d//" % day
            for i in range(len(fileNames)):

                '''读取时间信息'''
                fileName = fileNames[i]
                MSG_symbol = fileName[0:5]
                time_str = fileName[-20:-8]
                end_hh = int(time_str[-4:-2])
                end_mm = int(time_str[-2:])
                start_hh = (end_hh * 60 + end_mm - 12) //60
                start_mm = (end_hh * 60 + end_mm - 12) % 60

                '''读取数据并重投影'''
                fn = fileName[:-7]
                infile_bt1 = indir_med_day + fn + "bt1.tif"
                infile_bt2 = indir_med_day + fn + "bt2.tif"
                infile_red = indir_med_day + fn + "red.tif"
                infile_nir = indir_med_day + fn + "nir.tif"
                infile_sza = indir_med_day + fn + "sza.tif"
                infile_saa = indir_med_day + fn + "saa.tif"

                [bt1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_bt1)
                [bt2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_bt2)
                [red, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_red)
                [nir, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_nir)
                [sza, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_sza)
                [saa, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_saa)

                fn_save = MSG_symbol + "%04d" % year + "%02d" % month + "%02d" %day + "%02d" % start_hh + "%02d" % start_mm
                mkdir_if_not_exist(indir_tif_day)
                indx = np.reshape(indx,[3712,3712])
                indy = np.reshape(indy, [3712, 3712])
                outfile_bt1 = indir_tif_day + fn_save + "_bt1.tif"
                bt1_save = np.zeros([nl,ns])
                bt1_save[indx,indy] = bt1
                write_image_gdal(bt1_save,ns,nl, nb, geog, proj, outfile_bt1)

if iftime:
    indir_raw = r"F:\data\MSG_2017_full-range\nc\raw\\"
    indir_med = r"F:\data\MSG_2017_full-range\nc\med\\"
    indir_tif = r"F:\data\MSG_2017_full-range\nc\tif\\"

    fileNames = search_file(indir_raw,".nc")
    for filename in fileNames:
        print(filename)
        indir_file = indir_raw + filename
        time_origin = read_image_Nc(indir_file,'channel_data_visir_data_l10_line_mean_acquisition_msec',1)
        time_origin = ((time_origin/1000) % 3600) % 900
        data = read_image_Nc(indir_file, 'ch1', 1)
        time = np.zeros([3712,3712])
        # 线性插值，x是11，y是时间，插到3712*3712
        for i in range(3712):
            x = np.array([0,1,2,3,4,5,6,7,8,9,10])/10*3712
            y = time_origin[i]
            if y.all() == 0: continue
            data_ = data[i]
            ind = data_>0
            n = np.sum(data_>0)
            f1 = interp1d(x,y,kind='linear')
            xnew = np.linspace(0, n-1, num=n)/(n-1)*3712
            time_interpolate = f1(xnew)
            time[i,ind] = time_interpolate

        # 几何校正
        # 定义空间参考
        cols = 3712
        rows = 3712
        res = 0.03000403165817

        srs = osr.SpatialReference()
        # 定义地球长半轴a=6378137.0m，地球短半轴b=6356752.3m，卫星星下点所在经度0.0，目标空间参考
        srs.ImportFromProj4('+proj=geos +h=35785863 +a=6378137.0 +b=6356752.3 +lon_0=0.0 +no_defs')

        item = 'time'
        outfile_med = indir_med + filename[:-3] + "_time.tif"
        write_image_gdal(time,3712,3712,1,'','',outfile_med)

        outfile_tif = indir_tif + filename[:-3] + "_time.tif"
        data = gdal.Open(outfile_med)
        data.SetProjection(srs.ExportToWkt())
        # 左上角x坐标， 水平分辨率，旋转参数， 左上角y坐标，旋转参数，竖直分辨率
        data.SetGeoTransform(
            [-cols * res * 50000, int(res * 100000), 0, cols * res * 50000, 0, int(-res * 100000)])
        # if os.path.exists(outdir_tif):
        #     continue
        print(outfile_tif)
        warpDs = gdal.Warp(outfile_tif, data, dstSRS='EPSG:4326', outputBounds=SpatialRange,
                           xRes=0.03, yRes=0.03)
        del warpDs

if ifcalsun:
    infile_time = r"D:\data\base\msg_angle\\MSG_time.tif"
    [time, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile_time)
    outfile_lon = indir_med + 'lon.tif'
    outfile_lat = indir_med + 'lat.tif'
    [lon, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile_lon)
    [lat, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile_lat)

    for m in range(1,2):
        daynum = calendar.monthrange(year, m + 1)[1]
        for d in range(daynum):
            month = m + 1
            day = d + 1
            indir_tif_day = indir_tif + "/%02d" % month + "/%02d//" % day
            indir_med_day = indir_med + "/%02d" % month + "/%02d//" % day
            if  not os.path.exists(indir_tif_day): continue
            fnames = search_file_rej(indir_tif_day, ['bt1.tif'],'enp')
            for fname in fnames:
                print(fname)
                MSG_symbol = fname[0:5]
                time_str = fname[-20:-8]
                year = int(time_str[0:4])
                month = int(time_str[4:6])
                day = int(time_str[6:8])
                hh = int(time_str[-4:-2])
                mm = int(time_str[-2:])
                fn = fname[:-7]
                outfile_sza = indir_tif_day + fn + "sza.tif"
                outfile_saa = indir_tif_day + fn + "saa.tif"

                if (hh > 9)*(hh< 15):
                    sza = np.zeros([nl, ns])
                    saa = np.zeros([nl,ns])
                    for i in range(0, np.int_(nl), 1):
                        # print(i)
                        ind = time[i] != 0
                        if np.sum(ind) ==0: continue
                        t0 = time[i,ind][0]
                        mm_p = int(mm + t0 // 60)
                        ss_p = int(t0 % 60)
                        utc_time = datetime(year, month, day, hh, np.int_(mm_p), np.int_(ss_p))
                        angle = astronomy.get_alt_az(utc_time, lon[i,ind], lat[i,ind])

                        # f = 0
                        # ind2 = time[i+2] != 0
                        # if not np.sum(ind2) == 0:
                        #     t2 = time[i + 2, ind2][0]
                        #     if t2 == t0:
                        #         f = 2
                        #
                        # ind1 = time[i + 1] != 0
                        # if not np.sum(ind1) == 0:
                        #     t1 = time[i + 1, ind1][0]
                        #     if t1 == t0:
                        #         f = 1

                        angle = astronomy.get_alt_az(utc_time, lon[i,ind], lat[i,ind])
                        sza[i,ind] = angle[0]
                        saa[i,ind] = angle[1]

                    sza[sza!=0] = sza[sza!=0] * 180 / np.pi
                    ind = sza > 0
                    sza[ind] = 90 - sza[ind]
                    ind = sza < 0
                    sza[ind] = -90 - sza[ind]

                    saa[saa!=0] = saa[saa!=0] * 180 / np.pi + 360
                    saa[saa >= 360] = saa[saa >= 360] - 360

                    '''提取'''
                    outfile_sza = indir_med_day + fn + "sza.tif"
                    outfile_saa = indir_med_day + fn + "saa.tif"
                    write_image_gdal(sza, 3712, 3712, 1, '', '', outfile_sza)
                    write_image_gdal(saa, 3712, 3712, 1, '', '', outfile_saa)

                    '''投影'''
                    cols = 3712
                    rows = 3712
                    res = 0.03000403165817
                    srs = osr.SpatialReference()
                    # 定义地球长半轴a=6378137.0m，地球短半轴b=6356752.3m，卫星星下点所在经度0.0，目标空间参考
                    srs.ImportFromProj4('+proj=geos +h=35785863 +a=6378137.0 +b=6356752.3 +lon_0=0.0 +no_defs')
                    items = ["sza", "saa"]
                    for item in items:
                        infile = indir_med_day + fn + item + ".tif"
                        outfile = indir_tif_day + fn + item + ".tif"
                        data = gdal.Open(infile)
                        data.SetProjection(srs.ExportToWkt())
                        # 左上角x坐标， 水平分辨率，旋转参数， 左上角y坐标，旋转参数，竖直分辨率
                        data.SetGeoTransform(
                            [-cols * res * 50000, int(res * 100000), 0, cols * res * 50000, 0, int(-res * 100000)])
                        # if os.path.exists(outfile):
                        #     continue
                        print(outfile)
                        warpDs = gdal.Warp(outfile, data, dstSRS='EPSG:4326', outputBounds=SpatialRange,
                                           xRes=0.03, yRes=0.03)
                        del warpDs

                # if (hh > 9)*(hh< 15):
                #     sza = np.zeros([nl,ns])
                #     saa = np.zeros([nl,ns])
                #     for i in range(ns):
                #         print(i)
                #         for j in range(nl):
                #             t = time[i,j]
                #             if t == 0: continue
                #             mm_p = int(mm + t // 60)
                #             ss_p = int(t % 60)
                #             utc_time = datetime(year, month, day, hh, np.int_(mm_p), np.int_(ss_p))
                #             angle = astronomy.get_alt_az(utc_time, lon[i,j], lat[i,j])
                #             sza[i,j] = angle[0]
                #             saa[i,j] = angle[1]
                #
                #     sza[sza!=0] = sza[sza!=0] * 180 / np.pi
                #     ind = sza= 0
                #     sza[ind] = 90 - sza[ind]
                #     ind = sza < 0
                #     sza[ind] = -90 - sza[ind]
                #
                #     saa[saa!=0] = saa[saa!=0] * 180 / np.pi + 360
                #     saa[saa >= 360] = saa[saa >= 360] - 360
                #
                #     write_image_gdal(sza,ns, nl, nb, geog_type, proj_type,outfile_sza)
                #     write_image_gdal(saa,ns, nl, nb, geog_type, proj_type,outfile_sza)
















# # create a VII scene from the selected granule(s)
# # scn = Scene(filenames=fileNames, reader='seviri_l1b_native')
#
# # print available dataset names for this scene
# print(scn.available_dataset_names())
#
# # load the datasets of interest
# # NOTE: only radiances are supported for test data
# scn.load(["vii_668"], calibration="radiance")
#
# # resample the scene to a specified area (e.g. "eurol1" for Europe in 1km resolution)
# eur = scn.resample("eurol", resampler='nearest', radius_of_influence=5000)
#
# # save the resampled data to disk
# eur.save_dataset("vii_668", filename='./vii_668_eur.png')