from util.util import *
# from pyhdf.SD import SD, SDC
import netCDF4
import time
import os
import pysolar.solar as solar
import datetime

'''用于处理MSG的SEVIRI数据，读取并投影'''
'''
1.ifunzip 用于解压每个文件
2.ifextract 用于提取数据（bt1、bt2、nir、red、saa、sza），然后做成tif（地理坐标WGS84）
3.ifproj 用于投影（KAL->UTM33S,EVO->UTM29N）,并重采样到3km
'''

# indir_zip = r'D:\data\MSG\KAL_2017\zip\\'
# indir_raw = r'D:\data\MSG\KAL_2017\raw\\'
# indir_med = r'D:\data\MSG\KAL_2017\med\\'
# indir_tif = r'D:\data\MSG\KAL_2017\tif\\'

indir_zip = r''
indir_raw = r'D:\data\MSG\KAL_2017\raw\\'
indir_med = r'D:\data\MSG\KAL_2017\med\\'
indir_tif = r'D:\data\MSG\KAL_2017\tif\\'

symbol = 'MSG'
targetArea = r'D:\data\type\type_kal_3000.tif'

ifunzip = 0
ifextract = 1
ifreproj = 1


'''解压'''
if ifunzip:
    fileNames_zip = search_file(indir_zip,['.gz'])
    fileNum_zip = len(fileNames_zip)
    mkdir_if_not_exist(indir_raw)

    for k in range(fileNum_zip):
        fileName = fileNames_zip[k]
        infile = indir_zip + fileName
        outfile = indir_raw + fileName.replace(".gz", "")
        if os.path.exists(infile) and not os.path.exists(outfile):
            un_gz(fileName,indir_zip,indir_raw)

'''提取数据'''
if ifextract:
    # fileNames = search_file(indir_raw, ['.nc'])
    fileNames = search_file(indir_raw, ['201702'])
    fileNum = len(fileNames)

    for k in range(fileNum):
        fileName = fileNames[k]
        infile = indir_raw + fileName
        print(k, infile)

        '''提取时间信息'''
        date_str = fileName[-17:-3]
        year = (np.uint(date_str[0:4]))
        month = (np.uint(date_str[4:6]))
        day = (np.uint(date_str[6:8]))
        time_str = date_str[8:14]
        doy = date2DOY(year, month, day)
        hh = (np.uint(time_str[0:2]))
        mm = (np.uint(time_str[2:4]))
        ss = (np.uint(time_str[4:6]))
        t = datetime.datetime(year, month, day, hh, mm, ss,tzinfo=datetime.timezone.utc)


        '''提取 热红外（10.8,12.0）*2 + 红 + 近红 + 经纬度'''
        fileName = infile
        objectName = r'ch9'
        ###### test error and file error
        try:
            nf = netCDF4.Dataset(fileName)
        except OSError:
            print(fileName + ' os error')
            continue
        # nf.variables.keys()
        if (objectName not in nf.variables.keys()): continue
        r_bt1 = read_image_Nc(fileName, objectName, 1)
        c1 = 1.19104 * 10 ** -5
        c2 = 1.43877
        miu = 10 ** 4 / 10.8
        bt1 = (c2 * miu) / np.log(1 + miu ** 3 * c1 / r_bt1)

        objectName = r'ch10'
        try:
            nf = netCDF4.Dataset(fileName)
        except OSError:
            print(fileName + ' os error')
            continue
        if (objectName not in nf.variables.keys()): continue
        r_bt2 = read_image_Nc(fileName, objectName, 1)
        miu = 10 ** 4 / 12.0
        bt2 = c2 * miu / np.log(1 + miu ** 3 * c1 / r_bt2)

        objectName = r'ch1'
        temp = nf.variables[objectName]
        red = read_image_Nc(fileName, objectName, 1)

        objectName = r'ch2'
        nir = read_image_Nc(fileName, objectName, 1)

        objectName = r'lat'
        lat = read_image_Nc(fileName, objectName, 1)

        objectName = r'lon'
        lon = read_image_Nc(fileName, objectName, 1)

        nl, ns = bt1.shape


        '''计算太阳角度'''
        saa = solar.get_azimuth(lat,lon,t)  # 太阳方位角
        sea = solar.get_altitude(lat,lon,t)  # 太阳高度角
        ind0 = (sea > 0)
        ind1 = (sea < 0)
        sza = sea
        sza[ind0] = 90 - sea[ind0]
        sza[ind1] = -(90 + sea[ind1])


        '''输出位置'''
        common_dir = indir_med

        lat_dir = common_dir + 'lat.tif'
        lon_dir = common_dir + 'lon.tif'

        bt1_dir = common_dir + 'bt1.tif'
        bt2_dir = common_dir + 'bt2.tif'
        red_dir = common_dir + 'red.tif'
        nir_dir = common_dir + 'nir.tif'
        saa_dir = common_dir + 'saa.tif'
        sza_dir = common_dir + 'sza.tif'

        '''写tif文件'''
        # a = type(lat[:nl, :ns])
        write_image_gdal(lat[:nl, :ns].astype(float64), ns, nl, 1, '', '', lat_dir)
        write_image_gdal(lon[:nl, :ns].astype(float64), ns, nl, 1, '', '', lon_dir)
        write_image_gdal(bt1[:nl, :ns], ns, nl, 1, '', '', bt1_dir)
        write_image_gdal(bt2[:nl, :ns], ns, nl, 1, '', '', bt2_dir)
        write_image_gdal(red[:nl, :ns], ns, nl, 1, '', '', red_dir)
        write_image_gdal(nir[:nl, :ns], ns, nl, 1, '', '', nir_dir)
        write_image_gdal(saa[:nl, :ns], ns, nl, 1, '', '', saa_dir)
        write_image_gdal(sza[:nl, :ns], ns, nl, 1, '', '', sza_dir)

        '''定义投影，写vert文件'''
        fileDir = indir_med
        file = 'bt1'
        datafile = common_dir + file + '.tif'
        xfile = common_dir + 'lon.tif'
        yfile = common_dir + 'lat.tif'
        vrtfile = common_dir + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, ns, nl)
        outfile = fileDir + symbol + "_" + str(year) + "_%03d" % doy + "_" + time_str + '_' + file + '.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'bt2'
        datafile = common_dir + file + '.tif'
        xfile = common_dir + 'lon.tif'
        yfile = common_dir + 'lat.tif'
        vrtfile = common_dir + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, ns, nl)
        outfile = fileDir + symbol + "_" + str(year) + "_%03d" % doy + "_" + time_str + '_' + file + '.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'red'
        datafile = common_dir + file + '.tif'
        xfile = common_dir + 'lon.tif'
        yfile = common_dir + 'lat.tif'
        vrtfile = common_dir + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, ns, nl)
        outfile = fileDir + symbol + "_" + str(year) + "_%03d" % doy + "_" + time_str + '_' + file + '.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'nir'
        datafile = common_dir + file + '.tif'
        xfile = common_dir + 'lon.tif'
        yfile = common_dir + 'lat.tif'
        vrtfile = common_dir + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, ns, nl)
        outfile = fileDir + symbol + "_" + str(year) + "_%03d" % doy + "_" + time_str + '_' + file + '.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'saa'
        datafile = common_dir + file + '.tif'
        xfile = common_dir + 'lon.tif'
        yfile = common_dir + 'lat.tif'
        vrtfile = common_dir + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, ns, nl)
        outfile = fileDir + symbol + "_" + str(year) + "_%03d" % doy + "_" + time_str + '_' + file + '.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'sza'
        datafile = common_dir + file + '.tif'
        xfile = common_dir + 'lon.tif'
        yfile = common_dir + 'lat.tif'
        vrtfile = common_dir + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, ns, nl)
        outfile = fileDir + symbol + "_" + str(year) + "_%03d" % doy + "_" + time_str + '_' + file + '.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)


'''重投影到局部坐标系'''
if ifreproj:
    print("Reproject starts")
    [data, ns, nl, nb, geog_type, proj_type] = read_image_gdal(targetArea)
    dataset_type = gdal.Open(targetArea)
    fileNames = search_file(indir_med, ['_bt1', 'tif'])
    fileNum = len(fileNames)
    n = 0
    for file in fileNames:
        infile_str = file[:-7]

        '''输入位置'''
        indir_bt1 = indir_med + infile_str + 'bt1.tif'
        indir_bt2 = indir_med + infile_str + 'bt2.tif'
        indir_red = indir_med + infile_str + 'red.tif'
        indir_nir = indir_med + infile_str + 'nir.tif'
        indir_saa = indir_med + infile_str + 'saa.tif'
        indir_sza = indir_med + infile_str + 'sza.tif'
        print(n , indir_bt1)
        n +=1

        '''输出位置'''
        outdir_bt1 = indir_tif + infile_str + 'bt1.tif'
        outdir_bt2 = indir_tif + infile_str + 'bt2.tif'
        outdir_red = indir_tif + infile_str + 'red.tif'
        outdir_nir = indir_tif + infile_str + 'nir.tif'
        outdir_saa = indir_tif + infile_str + 'saa.tif'
        outdir_sza = indir_tif + infile_str + 'sza.tif'

        '''重投影+重采样'''
        [bt1, im_width, im_height, im_bands, geotrans, proj] = read_image_gdal(indir_bt1)

        srcSRS = proj
        dstSRS= proj_type
        xRes = 3000
        yRes = 3000
        resample_method = gdal.GRIORA_NearestNeighbour

        infile = indir_bt1
        dataset = gdal.Open(infile)
        gdal.Warp(outdir_bt1, dataset, format='GTiff', srcSRS = srcSRS, dstSRS= dstSRS ,xRes=xRes,yRes=yRes,resampleAlg=resample_method)

        infile = indir_bt2
        dataset = gdal.Open(infile)
        gdal.Warp(outdir_bt2, dataset, format='GTiff', srcSRS = srcSRS, dstSRS= dstSRS ,xRes=xRes,yRes=yRes,resampleAlg=resample_method)

        infile = indir_red
        dataset = gdal.Open(infile)
        gdal.Warp(outdir_red, dataset, format='GTiff', srcSRS = srcSRS, dstSRS= dstSRS ,xRes=xRes,yRes=yRes,resampleAlg=resample_method)

        infile = indir_nir
        dataset = gdal.Open(infile)
        gdal.Warp(outdir_nir, dataset, format='GTiff', srcSRS = srcSRS, dstSRS= dstSRS ,xRes=xRes,yRes=yRes,resampleAlg=resample_method)

        infile = indir_saa
        dataset = gdal.Open(infile)
        gdal.Warp(outdir_saa, dataset, format='GTiff', srcSRS = srcSRS, dstSRS= dstSRS ,xRes=xRes,yRes=yRes,resampleAlg=resample_method)

        infile = indir_sza
        dataset = gdal.Open(infile)
        gdal.Warp(outdir_sza, dataset, format='GTiff', srcSRS = srcSRS, dstSRS= dstSRS ,xRes=xRes,yRes=yRes,resampleAlg=resample_method)


# if ifreproj:
#     '''读入目标投影数据'''
#     [data, ns, nl, nb, geog, proj] = read_image_gdal(targetArea)
#     nsi = np.zeros([nl, ns])
#     nli = np.zeros([nl, ns])
#     for k in range(nl):
#         nli[k, :] = k
#         nsi[k, :] = np.linspace(0, ns - 1, ns)
#     nli = np.reshape(nli,-1)
#     nsi = np.reshape(nsi,-1)
#     dataset = gdal.Open(targetArea)
#     temp1, temp2 = imagexy2geo(dataset, nli, nsi)
#     lon, lat = geo2lonlat(dataset, temp1, temp2)
#
#     fileNames = search_file(indir_med, ['_bt1', 'tif'])
#     fileNum = len(fileNames)
#     for file in fileNames:
#         infile_str = file[:-7]
#         '''读入待重投影数据'''
#         indir_bt1 = indir_med + infile_str + 'bt1.tif'
#         indir_bt2 = indir_med + infile_str + 'bt2.tif'
#         indir_red = indir_med + infile_str + 'red.tif'
#         indir_nir = indir_med + infile_str + 'nir.tif'
#         indir_saa = indir_med + infile_str + 'saa.tif'
#         indir_sza = indir_med + infile_str + 'sza.tif'
#         [bt1, im_width, im_height, im_bands, im_geotrans, im_proj] = read_image_gdal(indir_bt1)
#         [bt2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(indir_bt2)
#         [red, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(indir_red)
#         [nir, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(indir_nir)
#         [saa, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(indir_saa)
#         [sza, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(indir_sza)
#
#         infile = indir_bt1
#         dataset = gdal.Open(infile)
#         temp1, temp2 = lonlat2geo(dataset, lat, lon)
#         imagex, imagey = geo2imagexy(dataset, temp1, temp2)
#         imagex = np.asarray(imagex, int)
#         imagey = np.asarray(imagey, int)
#         ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
#         imagex[imagex < 0] = 0
#         imagex[imagex > im_height - 1] = im_height - 1
#         imagey[imagey < 0] = 0
#         imagey[imagey > im_width - 1] = im_width - 1
#
#         bt1_out = np.reshape(bt1[imagex,imagey],[nl, ns])
#         bt2_out = np.reshape(bt2[imagex, imagey], [nl, ns])
#         red_out = np.reshape(red[imagex, imagey], [nl, ns])
#         nir_out = np.reshape(nir[imagex, imagey], [nl, ns])
#         saa_out = np.reshape(saa[imagex, imagey], [nl, ns])
#         sza_out = np.reshape(saa[imagex, imagey], [nl, ns])
#
#         '''输出'''
#         outdir_bt1 = indir_tif + infile_str + 'bt1.tif'
#         outdir_bt2 = indir_tif + infile_str + 'bt2.tif'
#         outdir_red = indir_tif + infile_str + 'red.tif'
#         outdir_nir = indir_tif + infile_str + 'nir.tif'
#         outdir_saa = indir_tif + infile_str + 'saa.tif'
#         outdir_sza = indir_tif + infile_str + 'sza.tif'
#
#         write_image_gdal(bt1_out, ns, nl, 1, geog, proj, outdir_bt1)
#         write_image_gdal(bt2_out, ns, nl, 1, geog, proj, outdir_bt2)
#         write_image_gdal(red_out, ns, nl, 1, geog, proj, outdir_red)
#         write_image_gdal(nir_out, ns, nl, 1, geog, proj, outdir_nir)
#         write_image_gdal(saa_out, ns, nl, 1, geog, proj, outdir_saa)
#         write_image_gdal(sza_out, ns, nl, 1, geog, proj, outdir_sza)


