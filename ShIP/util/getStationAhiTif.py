import numpy as np
from scipy import interpolate
import matplotlib.mlab as ml
import matplotlib.pyplot as plt
import time
from inversion_lsct.myfun import *
from inversion_lsct.multiple_lsct import *
from multiprocessing import Pool
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

satelliteNames = ['s3a', 's3b']
satelliteNames = ['s3a']

infile_type = 'd:/data/type/type_china_1000.tif'
[type, width, height, bands, geog, proj] = read_image_gdal(infile_type)

infile_vza = r'd:\data\map\\ahi_vza_china.tif'
[vzaAll, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vza)

infile_vaa = r'd:\data\map\\ahi_vaa_china.tif'
[vaaAll, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaa)

for satelliteName in satelliteNames:
    if satelliteName == 's3a':
        indir_tif = r'D:\mydata\s3a\ahi_tif_china/'
    if satelliteName == 's3b':
        indir_tif = r'D:\mydata\s3b\ahi_tif_china/'

    indir_geoLocation = r'D:\data\field\geoLocation.xlsx'
    geoLocation = pd.read_excel(indir_geoLocation)
    stationNames = geoLocation['stationName']

    stationNum = len(stationNames)

    Size = 11
    result_bt1 = np.zeros([stationNum, 366, Size, Size])
    result_bt2 = np.zeros([stationNum, 366, Size, Size])
    result_red = np.zeros([stationNum, 366, Size, Size])
    result_nir = np.zeros([stationNum, 366, Size, Size])
    result_saa = np.zeros([stationNum, 366, Size, Size])
    result_sza = np.zeros([stationNum, 366, Size, Size])
    result_vaa = np.zeros([stationNum, 366, Size, Size])
    result_vza = np.zeros([stationNum, 366, Size, Size])

    windowSize = 5
    for doy in range(366):
    # for doy in range(1):
        infile_bt1 = indir_tif + satelliteName + '_2019%03d'%doy + '_day_bt1.tif'
        infile_bt2 = indir_tif + satelliteName + '_2019%03d'%doy + '_day_bt2.tif'
        infile_red = indir_tif + satelliteName + '_2019%03d'%doy + '_day_red.tif'
        infile_nir = indir_tif + satelliteName + '_2019%03d'%doy + '_day_nir.tif'
        infile_saa = indir_tif + satelliteName + '_2019%03d'%doy + '_day_saa.tif'
        infile_sza = indir_tif + satelliteName + '_2019%03d'%doy + '_day_sza.tif'

        c1 = os.path.exists(infile_bt1)
        c2 = os.path.exists(infile_bt2)
        c3 = os.path.exists(infile_red)
        c4 = os.path.exists(infile_nir)
        c5 = os.path.exists(infile_saa)
        c6 = os.path.exists(infile_sza)
        if c1 * c2 * c3 * c4 * c5 * c6 == 0:
            print(str(doy) + ' lack data')
            continue

        [bt1, ns, nl, nb, geog, proj] = read_image_gdal(infile_bt1)
        [bt2, ns, nl, nb, geog, proj] = read_image_gdal(infile_bt2)
        [red, ns, nl, nb, geog, proj] = read_image_gdal(infile_red)
        [nir, ns, nl, nb, geog, proj] = read_image_gdal(infile_nir)
        [saa, ns, nl, nb, geog, proj] = read_image_gdal(infile_saa)
        [sza, ns, nl, nb, geog, proj] = read_image_gdal(infile_sza)

        bt1 = resize_data_near(bt1, height, width)
        bt2 = resize_data_near(bt2, height, width)
        red = resize_data_near(red, height, width)
        nir = resize_data_near(nir, height, width)
        saa = resize_data_near(saa, height, width)
        sza = resize_data_near(sza, height, width)
        vaa = resize_data_near(vaaAll, height, width)
        vza = resize_data_near(vzaAll, height, width)

        stationI = 0
        dataset_type = gdal.Open(infile_type)
        for stationName in stationNames:
            lon = geoLocation[geoLocation['stationName'] == stationName]['longitude']
            lat = geoLocation[geoLocation['stationName'] == stationName]['latitude']

            geox, geoy = lonlat2geo(dataset_type, lon, lat)
            imagex, imagey = geo2imagexy(dataset_type, geox, geoy)
            imagex = int(np.round(imagex))
            imagey = int(np.round(imagey))

            bt1_window = bt1[imagex - windowSize:imagex + windowSize + 1,
                         imagey - windowSize:imagey + windowSize + 1]
            bt2_window = bt2[imagex - windowSize:imagex + windowSize + 1,
                         imagey - windowSize:imagey + windowSize + 1]
            red_window = red[imagex - windowSize:imagex + windowSize + 1,
                         imagey - windowSize:imagey + windowSize + 1]
            nir_window = nir[imagex - windowSize:imagex + windowSize + 1,
                         imagey - windowSize:imagey + windowSize + 1]
            saa_window = saa[imagex - windowSize:imagex + windowSize + 1,
                         imagey - windowSize:imagey + windowSize + 1]
            sza_window = sza[imagex - windowSize:imagex + windowSize + 1,
                         imagey - windowSize:imagey + windowSize + 1]
            vaa_window = vaa[imagex - windowSize:imagex + windowSize + 1,
                         imagey - windowSize:imagey + windowSize + 1]
            vza_window = vza[imagex - windowSize:imagex + windowSize + 1,
                         imagey - windowSize:imagey + windowSize + 1]

            result_bt1[stationI, doy, :, :] = bt1_window
            result_bt2[stationI, doy, :, :] = bt2_window
            result_red[stationI, doy, :, :] = red_window
            result_nir[stationI, doy, :, :] = nir_window
            result_saa[stationI, doy, :, :] = saa_window
            result_sza[stationI, doy, :, :] = sza_window
            result_vaa[stationI, doy, :, :] = vaa_window
            result_vza[stationI, doy, :, :] = vza_window

            stationI = stationI + 1
        print(satelliteName + str(doy) + ' done')

    stationI = 0
    outDir = r'D:\mydata\station\\'
    for stationName in stationNames:
        outfileResultDir = outDir + stationName + '//'
        if os.path.exists(outfileResultDir):
            print(outDir + stationName + '// exists')
        else:
            os.mkdir(outfileResultDir)

        outFileName = outfileResultDir + satelliteName + '_Ahi_bt1.tif'
        write_image_gdal(result_bt1[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_Ahi_bt2.tif'
        write_image_gdal(result_bt2[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_Ahi_red.tif'
        write_image_gdal(result_red[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_Ahi_nir.tif'
        write_image_gdal(result_nir[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_Ahi_saa.tif'
        write_image_gdal(result_saa[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_Ahi_sza.tif'
        write_image_gdal(result_sza[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + '_Ahi_vaa.tif'
        write_image_gdal(result_vaa[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + '_Ahi_vza.tif'
        write_image_gdal(result_vza[stationI], 11, 11, 365, geog, proj, outFileName)