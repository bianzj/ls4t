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

#
satelliteNames = ['s3a', 's3b']

for satelliteName in satelliteNames:
    if satelliteName == 's3a':
        indir_lstN = r'D:\mydata\s3a\lst_china\s3a_lst_china/'
        indir_tif = r'D:\data\s3a_tif/'
    if satelliteName == 's3b':
        indir_lstN = r'D:\mydata\s3b\lst_china\s3b_lst_china/'
        indir_tif = r'D:\data\s3b_tif/'

    indir_lai = r'D:\data\lai\lai_china/'
    indir_ci = r'D:\data\clumping\ci_china/'
    indir_type = 'd:/data/type/'
    indir_ems = r'D:\data\emis/'
    infile_soil1_emis = indir_ems + 'emis1_polar.tif'
    infile_soil2_emis = indir_ems + 'emis2_polar.tif'
    [emis1_s, width, height, bands, geog, proj] = read_image_gdal(infile_soil1_emis)
    [emis2_s, width, height, bands, geog, proj] = read_image_gdal(infile_soil2_emis)

    infile_type = indir_type + 'type_china_1000.tif'
    infile_veg_emis = indir_ems + 'IGBP_Emi.txt'
    [type, width, height, bands, geog, proj] = read_image_gdal(infile_type)
    typeData = np.asarray(type, np.int)
    emis_v = read_txt_array(infile_veg_emis, 0, 2)
    emis1_v = emis_v[typeData, 0]
    emis2_v = emis_v[typeData, 1]

    indir_geoLocation = r'D:\data\field\geoLocation.xlsx'
    geoLocation = pd.read_excel(indir_geoLocation)
    stationNames = geoLocation['stationName'][24:]
    # stationNames = ['TPS']

    filesName = search_file(indir_lstN, ['day', 'lst', 'nadir'])
    filesNum = len(filesName)

    outDir = r'D:\mydata\station\\'
    stationNum = len(stationNames)
    result_vza_n = np.zeros([stationNum, 366, 11, 11])
    result_vaa_n = np.zeros([stationNum, 366, 11, 11])
    result_vza_o = np.zeros([stationNum, 366, 11, 11])
    result_vaa_o = np.zeros([stationNum, 366, 11, 11])
    result_sza = np.zeros([stationNum, 366, 11, 11])
    result_saa = np.zeros([stationNum, 366, 11, 11])
    result_LAI = np.zeros([stationNum, 366, 11, 11])
    result_rad = np.zeros([stationNum, 366, 11, 11])
    result_tcw = np.zeros([stationNum, 366, 11, 11])
    result_emis1_s = np.zeros([stationNum, 366, 11, 11])
    result_emis2_s = np.zeros([stationNum, 366, 11, 11])
    result_type = np.zeros([stationNum, 366, 11, 11])
    result_emis1_v = np.zeros([stationNum, 366, 11, 11])
    result_emis2_v = np.zeros([stationNum, 366, 11, 11])
    result_ci = np.zeros([stationNum, 366, 11, 11])

    windowSize = 5

    for fileI in range(filesNum):
    # for fileI in range(1):
        fileName = filesName[fileI][:-18]
        doyStr = fileName[-3:]
        doy = int(doyStr)
        month = doy2date(2019, doy)[0]
        infileCI = indir_ci + '2019_month%02d' %month + '.tif'
        [ci, ns, nl, nb, goeg, proj] = read_image_gdal(infileCI)

        infileVzaN = indir_tif + fileName + '_day_vza_nadir.tif'
        infileVaaN = indir_tif + fileName + '_day_vaa_nadir.tif'
        infileVzaO = indir_tif + fileName + '_day_vza_obliq.tif'
        infileVaaO = indir_tif + fileName + '_day_vaa_obliq.tif'
        c1 = os.path.exists(infileVzaN)
        c2 = os.path.exists(infileVaaN)
        c3 = os.path.exists(infileVzaO)
        c4 = os.path.exists(infileVaaO)
        if c1 * c2 * c3 * c4 == 0:
            print(fileName + ' lack observation angle data')
            continue
        [vza_n, ns, nl, nb, geog, proj] = read_image_gdal(infileVzaN)
        [vaa_n, ns, nl, nb, geog, proj] = read_image_gdal(infileVaaN)
        [vza_o, ns, nl, nb, geog, proj] = read_image_gdal(infileVzaO)
        [vaa_o, ns, nl, nb, geog, proj] = read_image_gdal(infileVaaO)

        infileSza = indir_tif + fileName + '_day_sza_nadir.tif'
        infileSaa = indir_tif + fileName + '_day_saa_nadir.tif'
        c1 = os.path.exists(infileSza)
        c2 = os.path.exists(infileSaa)
        if c1 * c2 == 0:
            print(fileName + ' lack sun angle data')
            continue
        [sza, ns, nl, nb, geog, proj] = read_image_gdal(infileSza)
        [saa, ns, nl, nb, geog, proj] = read_image_gdal(infileSaa)

        infileLai = indir_lai + '2019_doy' + doyStr + '_lai.tif'
        if os.path.exists(infileLai) == 0:
            print(fileName + ' lack LAI data')
            continue
        [lai, ns, nl, nb, geog, proj] = read_image_gdal(infileLai)

        infileRad = indir_tif + fileName + '_day_rad.tif'
        infileTcw = indir_tif + fileName + '_day_tcw.tif'
        c1 = os.path.exists(infileRad)
        c2 = os.path.exists(infileTcw)
        if c1 * c2 == 0:
            print(fileName + ' lack rad or tcw data')
            continue
        [rad, ns, nl, nb, geog, proj] = read_image_gdal(infileRad)
        [tcw, ns, nl, nb, geog, proj] = read_image_gdal(infileTcw)
        rad = resize_data_near(rad, height, width)
        tcw = resize_data_near(tcw, height, width)

        stationI = 0
        dataset_type = gdal.Open(infile_type)
        for stationName in stationNames:
            lon = geoLocation[geoLocation['stationName'] == stationName]['longitude']
            lat = geoLocation[geoLocation['stationName'] == stationName]['latitude']

            geox, geoy = lonlat2geo(dataset_type, lon, lat)
            imagex, imagey = geo2imagexy(dataset_type, geox, geoy)
            imagex = int(np.round(imagex))
            imagey = int(np.round(imagey))

            ci_window = ci[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            result_ci[stationI, doy, :, :] = ci_window

            emis1_s_window = emis1_s[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            emis2_s_window = emis2_s[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            emis_type_window = typeData[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            emis1_v_window = emis1_v[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            emis2_v_window = emis2_v[imagex - windowSize:imagex + windowSize + 1,
                             imagey - windowSize:imagey + windowSize + 1]
            result_emis1_s[stationI, doy, :, :] = emis1_s_window
            result_emis2_s[stationI, doy, :, :] = emis2_s_window
            result_type[stationI, doy, :, :] = emis_type_window
            result_emis1_v[stationI, doy, :, :] = emis1_v_window
            result_emis2_v[stationI, doy, :, :] = emis2_v_window

            vza_n_window = vza_n[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            vaa_n_window = vaa_n[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            vza_o_window = vza_o[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            vaa_o_window = vaa_o[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            sza_window = sza[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            saa_window = saa[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            result_vza_n[stationI, doy, :, :] = vza_n_window
            result_vaa_n[stationI, doy, :, :] = vaa_n_window
            result_vza_o[stationI, doy, :, :] = vza_o_window
            result_vaa_o[stationI, doy, :, :] = vaa_o_window
            result_sza[stationI, doy, :, :] = sza_window
            result_saa[stationI, doy, :, :] = saa_window

            lai_window = lai[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            result_LAI[stationI, doy, :, :] = lai_window

            rad_window = rad[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            result_rad[stationI, doy, :, :] = rad_window
            tcw_window = tcw[imagex - windowSize:imagex + windowSize + 1, imagey - windowSize:imagey + windowSize + 1]
            result_tcw[stationI, doy, :, :] = tcw_window

            stationI = stationI + 1
        print(doyStr + ' done')

    stationI = 0
    for stationName in stationNames:
        # stationName = stationNames[stationI]
        outfileResultDir = outDir + stationName + '//'
        if os.path.exists(outfileResultDir):
            print(outDir + stationName + '// exists')
        else:
            os.mkdir(outfileResultDir)

        outFileName = outfileResultDir + '_emis1_s.tif'
        write_image_gdal(result_emis1_s[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + '_emis2_s.tif'
        write_image_gdal(result_emis2_s[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + '_type.tif'
        write_image_gdal(result_type[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + '_emis1_v.tif'
        write_image_gdal(result_emis1_v[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + '_emis2_v.tif'
        write_image_gdal(result_emis2_v[stationI], 11, 11, 365, geog, proj, outFileName)

        outFileName = outfileResultDir + satelliteName + '_vza_nadir.tif'
        write_image_gdal(result_vza_n[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_vaa_nadir.tif'
        write_image_gdal(result_vaa_n[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_vza_oblique.tif'
        write_image_gdal(result_vza_o[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_vaa_oblique.tif'
        write_image_gdal(result_vaa_o[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_sza.tif'
        write_image_gdal(result_sza[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_saa.tif'
        write_image_gdal(result_saa[stationI], 11, 11, 365, geog, proj, outFileName)

        outFileName = outfileResultDir + satelliteName + '_LAI.tif'
        write_image_gdal(result_LAI[stationI], 11, 11, 365, geog, proj, outFileName)

        outFileName = outfileResultDir + satelliteName + '_rad.tif'
        write_image_gdal(result_rad[stationI], 11, 11, 365, geog, proj, outFileName)
        outFileName = outfileResultDir + satelliteName + '_tcw.tif'
        write_image_gdal(result_tcw[stationI], 11, 11, 365, geog, proj, outFileName)

        outFileName = outfileResultDir + '_ci.tif'
        write_image_gdal(result_ci[stationI], 11, 11, 365, geog, proj, outFileName)

        stationI = stationI + 1


