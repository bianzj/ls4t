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

for satelliteName in satelliteNames:
    if satelliteName == 's3a':
        indir_lstN = r'D:\mydata\s3a\lst_china\s3a_lst_china/'
        indir_tif = r'D:\data\s3a_tif/'
    if satelliteName == 's3b':
        indir_lstN = r'D:\mydata\s3b\lst_china\s3b_lst_china/'
        indir_tif = r'D:\data\s3b_tif/'


    indir_type = 'd:/data/type/'
    indir_ems = r'D:\data\emis/'
    infile_soil_emis = indir_ems + 'emis1_polar.tif'
    infile_type = indir_type + 'type_china_1000.tif'
    infile_veg_emis = indir_ems + 'IGBP_Emi.txt'
    [emis_s, emis_v, geog, proj] = file2Array_static(infile_soil_emis, infile_veg_emis, infile_type)
    [type, width, height, bands, geog, proj] = read_image_gdal(infile_type)

    indir_geoLocation = r'D:\data\field\geoLocation.xlsx'
    geoLocation = pd.read_excel(indir_geoLocation)
    stationNames = geoLocation['stationName'][24:]

    filesName = search_file(indir_lstN, ['day', 'lst', 'nadir'])
    filesNum = len(filesName)

    outDir = r'D:\mydata\station\\'
    stationNum = len(stationNames)
    result_bt1_n = np.zeros([stationNum, 366, 11, 11])
    result_bt1_o = np.zeros([stationNum, 366, 11, 11])
    result_bt2_n = np.zeros([stationNum, 366, 11, 11])
    result_bt2_o = np.zeros([stationNum, 366, 11, 11])
    result_cloud_n = np.zeros([stationNum, 366, 11, 11])
    result_cloud_o = np.zeros([stationNum, 366, 11, 11])
    result_time = np.zeros([stationNum, 366, 11, 11])
    result_red_n = np.zeros([stationNum, 366, 11, 11])
    result_red_o = np.zeros([stationNum, 366, 11, 11])
    result_nir_n = np.zeros([stationNum, 366, 11, 11])
    result_nir_o = np.zeros([stationNum, 366, 11, 11])
    windowSize = 5

    for fileI in range(filesNum):
    # for fileI in range(1):
        fileName = filesName[fileI][:-18]
        doyStr = fileName[-3:]
        doy = int(doyStr)
        infileBt1N = indir_tif + fileName + '_day_bt1_nadir.tif'
        infileBt1O = indir_tif + fileName + '_day_bt1_obliq.tif'
        infileBt2N = indir_tif + fileName + '_day_bt2_nadir.tif'
        infileBt2O = indir_tif + fileName + '_day_bt2_obliq.tif'
        c1 = os.path.exists(infileBt1N)
        c2 = os.path.exists(infileBt1O)
        c3 = os.path.exists(infileBt2N)
        c4 = os.path.exists(infileBt2O)
        if c1 * c2 * c3 * c4 == 0:
            print(fileName + ' lack bt data')
            continue
        [bt1N, width, height, bands, geog, proj] = read_image_gdal(infileBt1N)
        [bt1O, width, height, bands, geog, proj] = read_image_gdal(infileBt1O)
        [bt2N, width, height, bands, geog, proj] = read_image_gdal(infileBt2N)
        [bt2O, width, height, bands, geog, proj] = read_image_gdal(infileBt2O)

        infileCloudN = indir_tif + fileName + '_day_cloud_nadir.tif'
        infileCloudO = indir_tif + fileName + '_day_cloud_obliq.tif'
        infileTime = indir_tif + fileName + '_day_time.tif'
        c1 = os.path.exists(infileCloudN)
        c2 = os.path.exists(infileCloudO)
        c3 = os.path.exists(infileTime)
        if c1 * c2 * c3 == 0:
            print(fileName + ' lack cloud or time data')
            continue
        [cloudN, ns, nl, nb, geog, proj] = read_image_gdal(infileCloudN)
        [cloudO, ns, nl, nb, geog, proj] = read_image_gdal(infileCloudO)
        [Time, ns, nl, nb, geog, proj] = read_image_gdal(infileTime)

        infileRedN = indir_tif + fileName + '_day_red_nadir.tif'
        infileRedO = indir_tif + fileName + '_day_red_obliq.tif'
        infileNirN = indir_tif + fileName + '_day_nir_nadir.tif'
        infileNirO = indir_tif + fileName + '_day_nir_obliq.tif'
        c1 = os.path.exists(infileRedN)
        c2 = os.path.exists(infileRedO)
        c3 = os.path.exists(infileNirN)
        c4 = os.path.exists(infileNirO)
        if c1 * c2 * c3 * c4 == 0:
            print(fileName + ' lack red or nir data')
            continue
        [redN, ns, nl, nb, geog, proj] = read_image_gdal(infileRedN)
        [redO, ns, nl, nb, geog, proj] = read_image_gdal(infileRedO)
        [nirN, ns, nl, nb, geog, proj] = read_image_gdal(infileNirN)
        [nirO, ns, nl, nb, geog, proj] = read_image_gdal(infileNirO)

        stationI = 0
        dataset_type = gdal.Open(infile_type)
        for stationName in stationNames:
            lon = geoLocation[geoLocation['stationName'] == stationName]['longitude']
            lat = geoLocation[geoLocation['stationName'] == stationName]['latitude']

            geox, geoy = lonlat2geo(dataset_type, lon, lat)
            imagex, imagey = geo2imagexy(dataset_type, geox, geoy)
            imagex = int(np.round(imagex))
            imagey = int(np.round(imagey))

            bt1N_window = bt1N[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            bt1O_window = bt1O[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            bt2N_window = bt2N[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            bt2O_window = bt2O[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            result_bt1_n[stationI, doy, :, :] = bt1N_window
            result_bt1_o[stationI, doy, :, :] = bt1O_window
            result_bt2_n[stationI, doy, :, :] = bt2N_window
            result_bt2_o[stationI, doy, :, :] = bt2O_window

            cloud_n_window = cloudN[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            cloud_o_window = cloudO[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            time_window = Time[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            result_cloud_n[stationI, doy, :, :] = cloud_n_window
            result_cloud_o[stationI, doy, :, :] = cloud_o_window
            result_time[stationI, doy, :, :] = time_window

            result_red_n[stationI, doy, :, :] = redN[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            result_red_o[stationI, doy, :, :] = redO[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            result_nir_n[stationI, doy, :, :] = nirN[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            result_nir_o[stationI, doy, :, :] = nirO[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]

            stationI = stationI + 1
        print(doyStr + ' done')

    stationI = 0
    for stationName in stationNames:
        outfileResultDir = outDir + stationName + '//'
        if os.path.exists(outfileResultDir):
            print(stationName + ' exists')
        else:
            os.mkdir(outfileResultDir)

        outFileName = outfileResultDir + satelliteName + '_bt1_nadir.tif'
        write_image_gdal(result_bt1_n[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_bt1_oblique.tif'
        write_image_gdal(result_bt1_o[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_bt2_nadir.tif'
        write_image_gdal(result_bt2_n[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_bt2_oblique.tif'
        write_image_gdal(result_bt2_o[stationI], 11, 11, 365, geog, proj, outFileName)

        outFileName = outfileResultDir + satelliteName + '_cloud_nadir.tif'
        write_image_gdal(result_cloud_n[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_cloud_oblique.tif'
        write_image_gdal(result_cloud_o[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_time.tif'
        write_image_gdal(result_time[stationI], 11, 11, 365, geog, proj, outFileName)

        outFileName = outfileResultDir + satelliteName + '_red_nadir.tif'
        write_image_gdal(result_red_n[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_nir_nadir.tif'
        write_image_gdal(result_nir_n[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_red_oblique.tif'
        write_image_gdal(result_red_o[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_nir_oblique.tif'
        write_image_gdal(result_nir_o[stationI], 11, 11, 365, geog, proj, outFileName)

        stationI = stationI +1


