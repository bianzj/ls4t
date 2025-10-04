
from util.util import *
from pyhdf.SD import SD, SDC

import time
import os

'''进行数据处理的时候，发现有缺失，又用该函数进行了读取，是补充'''
'''此文件与AHI_data中的操作相同，可不用'''
'''根据nethdf下载数据文件中读取所需要的数据，并保存为tif文件'''
'''AHI全年的数据进行预处理，得到太阳方位角和天顶角'''

os.environ['PROJ_LIB'] = r'C:\ProgramData\Anaconda3\envs\python37\Library\share\proj'
#####################################
### functions


###############################################3
####### Examples
################################################

##############################################
######## from hdf to tif and projected to WGS84
##############################################

indir_raw = r'm:\ahi_raw\\'
indir_tif0 = r'n:\ahi_tif\\'
targetArea = r'D:\data\type\type_china_2000.tif'
reffile = r'D:\data\lst\base\AHI_vaa.tif'
symbol = 'AHI'

ifunzip = 1
ifproj = 0
ifresample = 0

iffirst = 1

for kmonth in range(5,6):
    for kday in range(1,32,1):

        indir_med = r'd:\data\lst\\ahi_med1\\'

        indir = indir_raw +'2019%02d'%kmonth+'/%02d'%kday+'/'

        indir_tif = indir_tif0 + '%02d' % kmonth + '/%02d'%kday +'/'

        fileNames = search_file(indir, ['H08'])
        fileNum = len(fileNames)
        if fileNum <=0: continue


        for k in range(fileNum):

            fileName = fileNames[k]
            infile = indir + fileName
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


            outfile7 = indir_tif + symbol + '_%4d' % year + '%03d' % doy + '_%02d' % hh + '%02d' % mm + '_saa.tif'
            if os.path.exists(outfile7) == 1:
                continue

            ## for day data_satellite
            if hh > 18 or hh < 15:
                dayNight = 'day'
            else:
                dayNight = 'night'
                continue

            fileName = infile
            objectName = r'SOZ'
            sza = getDatafromNc(fileName, objectName,1)

            fileName = infile
            objectName = r'SOA'
            saa = getDatafromNc(fileName, objectName,1)
            nl_temp, ns_temp = np.shape(saa)


            if dayNight == 'day':
                outfile = indir_med + '\\AHI_sza.tif'
                write_image_gdal(sza[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
                outfile = indir_med + '\\AHI_saa.tif'
                write_image_gdal(saa[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
            else:
                continue

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

            outfile5 = indir_tif + outfile0  + '_sza.tif'
            outfile6 = indir_tif + outfile0  + '_saa.tif'

            if(os.path.exists(outfile5) == 1):continue
            data6 = np.zeros([nl, ns])
            data5 = np.zeros([nl, ns])

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
                temp1, temp2 = lonlat2geo(dataset, lat, lon)
                imagey, imagex = geo2imagexy(dataset, temp1, temp2)

                imagex = np.asarray(imagex, np.int)
                imagey = np.asarray(imagey, np.int)
                ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
                imagex[imagex < 0] = 0
                imagex[imagex > im_height - 1] = im_height - 1
                imagey[imagey < 0] = 0
                imagey[imagey > im_width - 1] = im_width - 1



            if dayNight =='day':
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



            if dayNight=='day':
                write_image_gdal(data5, ns, nl, 1, geog, proj, outfile5)
                write_image_gdal(data6, ns, nl, 1, geog, proj, outfile6)


