from util.util import *
from util.util_constant import *
from pyhdf.SD import SD, SDC
import time
import os
os.environ['PROJ_LIB'] = r'C:\Users\zzz\anaconda3\envs\patrol\Library\share\proj'
#####################################
### functions

'''
处理modis数据，
与SLSTR数据处理类似，由于单副影像不能完全覆盖研究区，所以会有个中间文件夹，先把数据都存储在改文件夹
再用研究区，对中间文件夹的每个进行匹配
如果满足，就把数据放上
不可避免，如果一天过境两次，会覆盖，但是覆盖后数据会保持一致
'''
'''
1. 先提出出来成tif unzip
2. gdal进行投影转换 proj
3. 研究区重采样 resample
'''

###



##############################################
######## from hdf to tif and projected to WGS84
##############################################

indir_raw = 'D:\data\data_download\MODIS\example\myd_raw\\'
indir_tif = 'D:\data\data_download\MODIS\example\myd_tif\\'
indir_med = 'D:\data\data_download\MODIS\example\myd_med\\'
# indir_lst = 'G:\myd_lst\\'
symbol = 'MYD'

# indir_raw = 'G:\mod_raw\\'
# indir_tif = 'G:\mod_tif\\'
# indir_med = 'G:\mod_med\\'
# indir_lst = 'G:\mod_lst\\'
# symbol = 'MOD'


targetArea = r'D:\data\base\type.tif'
ifproj = 1
ifresample = 1

if ifproj ==1:
    fileNames = search_file(indir_raw,['1KM'])
    fileNum = len(fileNames)

    for k in range(fileNum):

        fileName = fileNames[k]
        infile = indir_raw + fileName
        print(k,infile)
        date_str = fileName[-34:-27]
        time_str = fileName[-26:-22]

        file = SD(infile)
        datasets_dic = file.datasets()

        # check the datasets in hdf
        # for idx, sds in enumerate(datasets_dic.keys()):
        #     print(idx, sds)

        sds_obj = file.select('EV_1KM_Emissive')  # select sds
        tir = sds_obj.get()  # get sds data_satellite
        scales = sds_obj.attributes()['radiance_scales']
        offsets = sds_obj.attributes()['radiance_offsets']
        rad31 = (tir[10,:,:]-offsets[10])*scales[10]
        rad32 = (tir[11,:,:]-offsets[11])*scales[11]
        nl,ns = np.shape(rad31)

        sds_obj = file.select('EV_250_Aggr1km_RefSB')  # select sds
        vnir = sds_obj.get()  # get sds data_satellite
        scales = sds_obj.attributes()['reflectance_scales']
        offsets = sds_obj.attributes()['reflectance_offsets']
        red = (vnir[0,:,:]-offsets[0])*scales[0]
        nir = (vnir[1,:,:]-offsets[1])*scales[1]

        sds_obj = file.select('SensorZenith')  # select sds
        vza = sds_obj.get()  # get sds data_satellite
        scale = sds_obj.attributes()['scale_factor']
        vza = vza*scale

        sds_obj = file.select('SolarZenith')  # select sds
        sza = sds_obj.get()  # get sds data_satellite
        scale = sds_obj.attributes()['scale_factor']
        sza = sza*scale

        sds_obj = file.select('SensorAzimuth')  # select sds
        vaa = sds_obj.get()  # get sds data_satellite
        scale = sds_obj.attributes()['scale_factor']
        vaa = vaa*scale

        sds_obj = file.select('SolarAzimuth')  # select sds
        saa = sds_obj.get()  # get sds data_satellite
        scale = sds_obj.attributes()['scale_factor']
        saa = saa*scale

        psi = np.abs(vaa-saa)
        psi[psi > 180] = 360 - psi[psi > 180]

        sds_obj = file.select('Latitude')  # select sds
        lat = sds_obj.get()  # get sds data_satellite

        sds_obj = file.select('Longitude')  # select sds
        lon = sds_obj.get()  # get sds data_satellite

        # psi = resize_data(psi,5)
        # vza = resize_data(vza, 5)
        # sza = resize_data(sza, 5)
        # lat = resize_data(lat,5)
        # lon = resize_data(lon,5)
        bt31 = inv_planck(band31_modis, rad31)
        bt32 = inv_planck(band32_modis, rad32)

        outfile = indir_med + '\\lat.tif'
        write_image_gdal(lat[:nl, :ns], ns, nl, 1, '', '', outfile)
        outfile = indir_med + '\\lon.tif'
        write_image_gdal(lon[:nl, :ns], ns, nl, 1, '', '', outfile)

        outfile = indir_med + '\\vza.tif'
        write_image_gdal(vza[:nl, :ns], ns, nl, 1, '', '', outfile)
        outfile = indir_med + '\\sza.tif'
        write_image_gdal(sza[:nl, :ns], ns, nl, 1, '', '', outfile)
        outfile = indir_med + '\\psi.tif'
        write_image_gdal(psi[:nl, :ns], ns, nl, 1, '', '', outfile)
        outfile = indir_med + '\\bt1.tif'
        write_image_gdal(bt31[:nl, :ns], ns, nl, 1, '', '', outfile)
        outfile = indir_med + '\\bt2.tif'
        write_image_gdal(bt32[:nl, :ns], ns, nl, 1, '', '', outfile)
        outfile = indir_med + '\\nir.tif'
        write_image_gdal(nir[:nl, :ns], ns, nl, 1, '', '', outfile)
        outfile = indir_med + '\\red.tif'
        write_image_gdal(red[:nl, :ns], ns, nl, 1, '', '', outfile)

        fileDir = indir_med

        file = 'psi'
        datafile = fileDir+'\\'+file+'.tif'
        xfile = fileDir+'\\lon.tif'
        yfile = fileDir+'\\lat.tif'
        vrtfile = fileDir+'\\'+file+'.vrt'
        write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
        outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_Cubic)

        file = 'sza'
        datafile = fileDir+'\\'+file+'.tif'
        xfile = fileDir+'\\lon.tif'
        yfile = fileDir+'\\lat.tif'
        vrtfile = fileDir+'\\'+file+'.vrt'
        write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
        outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_Cubic)

        file = 'vza'
        datafile = fileDir+'\\'+file+'.tif'
        xfile = fileDir+'\\lon.tif'
        yfile = fileDir+'\\lat.tif'
        vrtfile = fileDir+'\\'+file+'.vrt'
        write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
        outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_Cubic)

        file = 'bt1'
        datafile = fileDir+'\\'+file+'.tif'
        xfile = fileDir+'\\lon.tif'
        yfile = fileDir+'\\lat.tif'
        vrtfile = fileDir+'\\'+file+'.vrt'
        write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
        outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_Cubic)

        file = 'bt2'
        datafile = fileDir+'\\'+file+'.tif'
        xfile = fileDir+'\\lon.tif'
        yfile = fileDir+'\\lat.tif'
        vrtfile = fileDir+'\\'+file+'.vrt'
        write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
        outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_Cubic)


        file = 'red'
        datafile = fileDir+'\\'+file+'.tif'
        xfile = fileDir+'\\lon.tif'
        yfile = fileDir+'\\lat.tif'
        vrtfile = fileDir+'\\'+file+'.vrt'
        write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
        outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_Cubic)

        file = 'nir'
        datafile = fileDir+'\\'+file+'.tif'
        xfile = fileDir+'\\lon.tif'
        yfile = fileDir+'\\lat.tif'
        vrtfile = fileDir+'\\'+file+'.vrt'
        write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
        outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_Cubic)



###############################
### projected images to target dataset
###############################

if ifresample==1:

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
    nli = np.reshape(nli,-1)
    nsi = np.reshape(nsi,-1)
    ###
    temp1,temp2= imagexy2geo(dataset,nli,nsi)
    lon,lat = geo2lonlat(dataset,temp1,temp2)

    dataTimeold = 0
    imageTimeold = 0
    fileNames = search_file(indir_med,['vza','tif'])
    fileNum = len(fileNames)
    for k in range(fileNum):
        fileName = fileNames[k]
        fileDir = indir_med +  fileName + r'\\'
        print(k, fileName)
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        ### dataTime and imageTime
        print(k, fileName)
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

        year = np.int(np.uint(fileName[4:8]))
        doy = np.int(np.uint(fileName[8:11]))
        time_str = fileName[12:12 + 4]
        hh = np.int(np.uint(time_str[0:2]))
        mm = np.int(np.uint(time_str[2:4]))
        infile0 = symbol + '_%4d' % year + '%03d' % doy + '_%02d' % hh + '%02d' % mm + '_'
        outfile0 = symbol + '_%4d' % year + '%03d' % doy + '_'

        ### for day data_satellite
        if hh > 22 or hh < 11:
            dayNight = 'day'
        else:
            dayNight = 'night'

        outfile1 = indir_tif + outfile0 + dayNight + '_bt1.tif'
        outfile2 = indir_tif + outfile0 + dayNight + '_bt2.tif'
        outfile3 = indir_tif + outfile0 + dayNight + '_red.tif'
        outfile4 = indir_tif + outfile0 + dayNight + '_nir.tif'
        outfile5 = indir_tif + outfile0 + dayNight + '_vza.tif'
        outfile6 = indir_tif + outfile0 + dayNight + '_sza.tif'
        outfile7 = indir_tif + outfile0 + dayNight + '_psi.tif'
        outfile8 = indir_tif + outfile0 + dayNight + '_time.tif'

        if os.path.exists(outfile1) == 1:
            [data1, temp1, temp2, temp3, geog, proj] = read_image_gdal(outfile1)
            [data2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile2)
            [data5, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile5)
            [data8, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile8)
            if dayNight == 'day':
                [data3, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile3)
                [data4, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile4)
                [data6, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile6)
                [data7, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile7)
        else:
            data1 = np.zeros([nl, ns])
            data2 = np.zeros([nl, ns])
            data3 = np.zeros([nl, ns])
            data4 = np.zeros([nl, ns])
            data5 = np.zeros([nl, ns])
            data6 = np.zeros([nl, ns])
            data7 = np.zeros([nl, ns])
            data8 = np.zeros([nl, ns])

        infile = indir_med + infile0 + r'bt1_proj.tif'
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
        temp1, temp2 = lonlat2geo(dataset, lat, lon)
        imagey, imagex = geo2imagexy(dataset, temp1, temp2)

        imagex = np.asarray(imagex, np.int)
        imagey = np.asarray(imagey, np.int)
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

        infile = indir_med + infile0 + r'bt2_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 200) * ind
        data2 = np.reshape(data2, [-1])
        data2[indnew] = temp[indnew]
        data2 = np.reshape(data2, [nl, ns])
        data2[data2 < 0] = 0
        data2[data2 > 500] = 0

        data8 = np.reshape(data8, [-1])
        temp[:] = np.int(np.uint(time_str))
        data8[indnew] = temp[indnew]
        data8 = np.reshape(data8, [nl, ns])
        #
        #
        if dayNight == 'day':
            infile = indir_med + infile0 + r'red_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            data = resize_data_ls(data, im_height, im_width)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data3 = np.reshape(data3, [-1])
            data3[indnew] = temp[indnew]
            data3 = np.reshape(data3, [nl, ns])
            data3[data3 < 0] = 0
            data3[data3 > 500] = 0

            infile = indir_med + infile0 + r'nir_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            data = resize_data_ls(data, im_height, im_width)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data4 = np.reshape(data4, [-1])
            data4[indnew] = temp[indnew]
            data4 = np.reshape(data4, [nl, ns])
            data4[data4 < 0] = 0
            data4[data4 > 500] = 0

        infile = indir_med + infile0 + r'vza_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 0) * ind
        data5 = np.reshape(data5, [-1])
        data5[indnew] = temp[indnew]
        data5 = np.reshape(data5, [nl, ns])
        data5[data5 < 0] = 0
        data5[data5 > 500] = 0

        if dayNight == 'day':
            infile = indir_med + infile0 + r'sza_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data6 = np.reshape(data6, [-1])
            data6[indnew] = temp[indnew]
            data6 = np.reshape(data6, [nl, ns])
            data6[data6 < 0] = 0
            data6[data6 > 500] = 0

            infile = indir_med + infile0 + r'psi_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data7 = np.reshape(data7, [-1])
            data7[indnew] = temp[indnew]
            data7 = np.reshape(data7, [nl, ns])
            data7[data7 < 0] = 0
            data7[data7 > 500] = 0

        write_image_gdal(data1, ns, nl, 1, geog, proj, outfile1)
        write_image_gdal(data2, ns, nl, 1, geog, proj, outfile2)
        write_image_gdal(data5, ns, nl, 1, geog, proj, outfile5)
        write_image_gdal(data8, ns, nl, 1, geog, proj, outfile8)
        if dayNight == 'day':
            write_image_gdal(data3, ns, nl, 1, geog, proj, outfile3)
            write_image_gdal(data4, ns, nl, 1, geog, proj, outfile4)
            write_image_gdal(data6, ns, nl, 1, geog, proj, outfile6)
            write_image_gdal(data7, ns, nl, 1, geog, proj, outfile7)

