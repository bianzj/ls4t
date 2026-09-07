from util.util import *
# from pyhdf.SD import SD, SDC
import netCDF4
import time
import os

'''根据nethdf下载数据文件中读取所需要的数据，并保存为tif文件'''
'''AHI全年的数据进行预处理'''

# os.environ['PROJ_LIB'] = r'C:\ProgramData\Anaconda3\envs\python37\Library\share\proj'
#####################################
### functions


###############################################3
####### Examples
################################################

##############################################
######## from hdf to tif and projected to WGS84
##############################################

indir_raw = r'F:\data\AHI_2022_heihe\ahi_raw\\'
indir_tif = r'F:\data\AHI_2022_heihe\ahi_tif\\'
targetArea = r'D:\data\type\type_heihe_2000_utm47N.tif'
reffile = r'D:\data\base\AHI_vza.tif'
symbol = 'AHI'

indir_med = r'F:\data\AHI_2022_heihe\ahi_med\\'

iffirst = 1

# for kmonth in range(12,13):
#     for kday in range(5,32,1):####！！！！！！！！！！！！

infiles = search_file(indir_raw,'nc')
for k in range(np.size(infiles)):
    fileName = infiles[k]
    kmonth = np.int(fileName[11:13])
    kday = np.int(fileName[13:15])
    khour = np.int(fileName[16:18])
    kmin = np.int(fileName[18:20])


    infile = indir_raw + fileName
    print(k,infile)

    fsize = os.path.getsize(infile)
    if fsize < 90000000: continue

    date_str = fileName[-37:-29]
    time_str = fileName[-28:24]
    year = (np.uint(date_str[0:4]))
    month = (np.uint(date_str[4:6]))
    day = (np.uint(date_str[6:8]))
    doy = date2DOY(year,month,day)



    hh = (np.uint(time_str[0:2]))
    mm = (np.uint(time_str[2:4]))

    # if hh < 13:continue
    # if mm!=30:continue

    outfile8 = indir_tif + symbol + '_%4d' % year + '%03d' % doy + '_%02d' % hh + '%02d' % mm + '_bt1.tif'
    # if os.path.exists(outfile8) == 1:
    #     continue

    ## for day data_satellite
    if hh > 18 or hh < 15:
        dayNight = 'day'
    else:
        dayNight = 'night'

    fileName = infile
    objectName = r'tbb_14'
    ###### test error and file error
    try:
        nf = netCDF4.Dataset(fileName)
    except OSError:
        print(fileName+ ' os error')
        continue
    if (objectName not in nf.variables.keys()): continue
    bt1 = read_image_Nc(fileName, objectName,1)

    fileName = infile
    objectName = r'tbb_15'
    try:
        bt2 = read_image_Nc(fileName, objectName,1)
    except RuntimeError:
        print(fileName + ' run time error')
        continue
    bt2 = read_image_Nc(fileName, objectName, 1)

    nl_temp,ns_temp = np.shape(bt1)

    fileName = infile
    objectName = r'albedo_03'
    red = read_image_Nc(fileName, objectName,1)

    fileName = infile
    objectName = r'albedo_04'
    nir = read_image_Nc(fileName, objectName,1)

    fileName = infile
    objectName = r'SOZ'
    sza = read_image_Nc(fileName, objectName,1)

    fileName = infile
    objectName = r'SOA'
    saa = read_image_Nc(fileName, objectName,1)

    ##### SAA 和 SAZ 数据没用到， 因为是地球同步轨道卫星
    fileName = infile
    objectName = r'SAA'
    vaa = read_image_Nc(fileName, objectName,1)

    fileName = infile
    objectName = r'SAZ'
    vza = read_image_Nc(fileName, objectName,1)


    outfile = indir_med + '\\AHI_bt1.tif'
    write_image_gdal(bt1[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
    outfile = indir_med + '\\AHI_bt2.tif'
    write_image_gdal(bt2[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
    # outfile = indir_med + '\\AHI_vza.tif'
    # write_image_gdal(vza[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
    # outfile = indir_med + '\\AHI_vaa.tif'
    # write_image_gdal(vaa[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)

    if dayNight == 'day':
        outfile = indir_med + '\\AHI_nir.tif'
        write_image_gdal(nir[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
        outfile = indir_med + '\\AHI_red.tif'
        write_image_gdal(red[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
        outfile = indir_med + '\\AHI_sza.tif'
        write_image_gdal(sza[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
        outfile = indir_med + '\\AHI_saa.tif'
        write_image_gdal(saa[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)


    ###########################################################
    ###########
    ###########################################################

    if iffirst ==1:
        dataset = gdal.Open(targetArea)
        if dataset == None:
            print(targetArea + " ")
        ns = dataset.RasterXSize
        nl = dataset.RasterYSize
        im_bands = dataset.RasterCount
        data = dataset.ReadAsArray(0, 0, ns, nl)
        geog = dataset.GetGeoTransform()
        proj = dataset.GetProjection()
        nsi = np.zeros([nl, ns])
        nli = np.zeros([nl, ns])
        for k in range(nl):
            nli[k, :] = k
            nsi[k, :] = np.linspace(0, ns - 1, ns)
        nli = np.reshape(nli, -1)
        nsi = np.reshape(nsi, -1)
        ###
        temp1, temp2 = imagexy2geo(dataset, nli, nsi)
        lon, lat = geo2lonlat(dataset, temp1, temp2)


    infile0 = symbol + '_%4d' % year + '%03d' % doy + '_%02d' % hh + '%02d' % mm + '_'
    outfile0 = symbol + '_%4d' % year + '%03d' % doy + '_%02d' % hh + '%02d' % mm

    print(infile0,time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    ### for day data_satellite
    # if hh > 22 or hh < 11:
    #     dayNight = 'day'
    # else:
    #     dayNight = 'night'

    outfile1 = indir_tif + outfile0  + '_bt1.tif'
    outfile2 = indir_tif + outfile0  + '_bt2.tif'
    outfile3 = indir_tif + outfile0  + '_red.tif'
    outfile4 = indir_tif + outfile0  + '_nir.tif'
    outfile5 = indir_tif + outfile0  + '_sza.tif'
    outfile6 = indir_tif + outfile0  + '_saa.tif'


    if os.path.exists(outfile1) == 1:
        [data1, temp1, temp2, temp3, geog, proj] = read_image_gdal(outfile1)
        [data2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile2)
        if dayNight == 'day':
            [data3, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile3)
            [data4, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile4)
            [data5, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile5)
            [data6, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile6)
          #  [data7, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile7)

    else:
        data1 = np.zeros([nl, ns])
        data2 = np.zeros([nl, ns])
        if dayNight == 'day':
            data3 = np.zeros([nl, ns])
            data4 = np.zeros([nl, ns])
            data5 = np.zeros([nl, ns])
            data6 = np.zeros([nl, ns])
         #   data7 = np.zeros([nl, ns])

    if iffirst == 1:
        infile_ = reffile
        dataset = gdal.Open(infile_)
        if dataset == None:
            print(infile_ + " ")
            continue
        im_width = dataset.RasterXSize
        im_height = dataset.RasterYSize
        im_bands = dataset.RasterCount
        # data_satellite = dataset.ReadAsArray(0, 0, im_width, im_height)
        im_geotrans = dataset.GetGeoTransform()
        im_proj = dataset.GetProjection()
        temp1, temp2 = lonlat2geo(dataset, lon, lat)
        imagex, imagey = geo2imagexy(dataset, temp2, temp1)

        imagex = np.asarray(imagex, int)
        imagey = np.asarray(imagey, int)
        ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
        imagex[imagex < 0] = 0
        imagex[imagex > im_height - 1] = im_height - 1
        imagey[imagey < 0] = 0
        imagey[imagey > im_width - 1] = im_width - 1



        infile = indir_med + r'ahi_bt1.tif'
        if os.path.exists(infile) == 0:
            print(infile + " ")
            continue
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)

        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 200) * ind
        if np.sum(indnew) == 0: continue
        data1 = np.reshape(data1, [-1])
        data1[indnew] = temp[indnew]
        data1 = np.reshape(data1, [nl, ns])
        data1[data1 < 0] = 0
        data1[data1 > 500] = 0
        iffirst = 0
    else:
        infile = indir_med + r'ahi_bt1.tif'

        if os.path.exists(infile) == 0:
            print(infile + " ")
            continue
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 200) * ind
        data1 = np.reshape(data1, [-1])
        data1[indnew] = temp[indnew]
        data1 = np.reshape(data1, [nl, ns])
        data1[data1 < 0] = 0
        data1[data1 > 500] = 0
    #
    infile = indir_med + r'ahi_bt2.tif'
    [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
    temp = data[imagex, imagey]
    indnew = (temp < 500) * (temp > 200) * ind
    data2 = np.reshape(data2, [-1])
    data2[indnew] = temp[indnew]
    data2 = np.reshape(data2, [nl, ns])
    data2[data2 < 0] = 0
    data2[data2 > 500] = 0

    if dayNight =='day':
        infile = indir_med + r'ahi_red.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 0) * ind
        data3 = np.reshape(data3, [-1])
        data3[indnew] = temp[indnew]
        data3 = np.reshape(data3, [nl, ns])
        data3[data3 < 0] = 3
        data3[data3 > 500] = 0
        #
        infile = indir_med + r'ahi_nir.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 0) * ind
        data4 = np.reshape(data4, [-1])
        data4[indnew] = temp[indnew]
        data4 = np.reshape(data4, [nl, ns])
        data4[data4 < 0] = 0
        data4[data4 > 500] = 0

        infile = indir_med + r'ahi_sza.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 0) * ind
        data5 = np.reshape(data5, [-1])
        data5[indnew] = temp[indnew]
        data5 = np.reshape(data5, [nl, ns])
        data5[data5 < 0] = 0
        data5[data5 > 500] = 0

        infile = indir_med + r'ahi_saa.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > -400) * ind
        data6 = np.reshape(data6, [-1])
        data6[indnew] = temp[indnew]
        data6 = np.reshape(data6, [nl, ns])
        data6[data6 < -400] = 0
        data6[data6 > 500] = 0


    write_image_gdal(data1, ns, nl, 1, geog, proj, outfile1)
    write_image_gdal(data2, ns, nl, 1, geog, proj, outfile2)
    if dayNight=='day':
        write_image_gdal(data3, ns, nl, 1, geog, proj, outfile3)
        write_image_gdal(data4, ns, nl, 1, geog, proj, outfile4)
        write_image_gdal(data5, ns, nl, 1, geog, proj, outfile5)
        write_image_gdal(data6, ns, nl, 1, geog, proj, outfile6)


