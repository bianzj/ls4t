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

'''FVC 物理孔隙率计算'''
# if __name__ == '__main__':
#     # satelliteName = 's3a'
#     # indir_lstN = r'D:\mydata\s3a\lst_china\s3a_lst_china/'
#     # indir_lstO = r'D:\mydata\s3a\lst_china\s3a_lst_china/'
#     # indir_lstAhi = r'D:\mydata\s3a\lst_china\ahi_lst_china/'
#     # indir_tif = r'D:\data\s3a_tif/'
#
#     satelliteName = 's3b'
#     indir_tif = r'D:\data\s3b_tif\\'
#     indir_lstN = r'D:\mydata\s3b\lst_china\s3b_lst_china/'
#     indir_lstO = r'D:\mydata\s3b\lst_china\s3b_lst_china/'
#     indir_lstAhi = r'D:\mydata\s3b\lst_china\ahi_lst_china/'
#     indir_tif = r'D:\data\s3b_tif/'
#     # indir_tif_Ahi = r'D:\data\s3b_tif_ahi_red_nir\\'
#
#     indir_fvcN = r'D:\data\fvc\fvc_china\fvc_china_n_' + satelliteName + '//'
#     indir_fvcO = r'D:\data\fvc\fvc_china\fvc_china_o_' + satelliteName + '//'
#     indir_fvcAhi = r'D:\data\fvc\fvc_china\fvc_china_ahi_' + satelliteName + '//'
#     indir_lai = r'D:\data\lai\lai_china/'
#
#     indir_type = 'd:/data/type/'
#     indir_ems = r'D:\data\emis/'
#     infile_soil_emis = indir_ems + 'emis1_polar.tif'
#     infile_type = indir_type + 'type_china_1000.tif'
#     # infile_typeCopy = indir_type + 'type_china_1000copy.tif'
#     infile_veg_emis = indir_ems + 'IGBP_Emi.txt'
#     [emis_s, emis_v, geog, proj] = file2Array_static(infile_soil_emis, infile_veg_emis, infile_type)
#     [type, width, height, bands, geog, proj] = read_image_gdal(infile_type)
#
#     indir_geoLocation = r'D:\data\field\geoLocation.xlsx'
#     geoLocation = pd.read_excel(indir_geoLocation)
#     stationNames = geoLocation['stationName']
#
#     filesName = search_file(indir_lstN, ['day', 'lst', 'nadir'])
#     filesNum = len(filesName)
#
#     outDir = r'D:\mydata\validation\lst\\'
#
#     result = []
#     for fileI in range(filesNum):
#     # for fileI in range(3):
#         startTime = time.time()
#         fileName = filesName[fileI][:-18]
#         doyStr = fileName[-3:]
#         infileLstN = indir_lstN + fileName + '_day_lst_nadir.tif'
#         infileLstO = indir_lstO + fileName + '_day_lst_obliq.tif'
#         infileLstAhi = indir_lstAhi + fileName + '_day_lst.tif'
#         c1 = os.path.exists(infileLstN)
#         c2 = os.path.exists(infileLstO)
#         c3 = os.path.exists(infileLstAhi)
#         if c1 * c2 * c3 == 0:
#             print(fileName + ' lack lst data')
#             continue
#
#         infileVzaN = indir_tif + fileName + '_day_vza_nadir.tif'
#         infileVaaN = indir_tif + fileName + '_day_vaa_nadir.tif'
#         infileVzaO = indir_tif + fileName + '_day_vza_obliq.tif'
#         infileVaaO = indir_tif + fileName + '_day_vaa_obliq.tif'
#         infileVzaAhi = r'D:\data\map\ahi_vza.tif'
#         infileVaaAhi = r'd:\data\map\ahi_vaa.tif'
#         c1 = os.path.exists(infileVzaN)
#         c2 = os.path.exists(infileVaaN)
#         c3 = os.path.exists(infileVzaO)
#         c4 = os.path.exists(infileVaaO)
#         if c1 * c2 * c3 * c4 == 0:
#             print(fileName + ' lack observation angle data')
#             continue
#
#         infileSza = indir_tif + fileName + '_day_sza_nadir.tif'
#         infileSaa = indir_tif + fileName + '_day_saa_nadir.tif'
#         c1 = os.path.exists(infileSza)
#         c2 = os.path.exists(infileSaa)
#         if c1 * c2 == 0:
#             print(fileName + ' lack sun angle data')
#             continue
#
#         infileFvcN = indir_fvcN + '2019_doy' + doyStr + '_fvc.tif'
#         infileFvcO = indir_fvcO + '2019_doy' + doyStr + '_fvc.tif'
#         infileFvcAhi = indir_fvcAhi + '2019_doy' + doyStr + '_fvc.tif'
#         c1 = os.path.exists(infileFvcN)
#         c2 = os.path.exists(infileFvcO)
#         c3 = os.path.exists(infileFvcAhi)
#         if c1 * c2 * c3 == 0:
#             print(fileName + ' lack fvc data')
#             continue
#         [fvcN, width, height, bands, geog, proj] = read_image_gdal(infileFvcN)
#         # [fvcO, width, height, bands, geog, proj] = read_image_gdal(infileFvcO)
#         # [fvcAhi, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileFvcAhi)
#         # fvcAhi = resize_data_near(fvcAhi, height, width)
#
#         infileLai = indir_lai + '2019_doy' + doyStr + '_lai.tif'
#         if os.path.exists(infileLai) == 0:
#             print(fileName + ' lack LAI data')
#             continue
#
#         resultDoy = []
#         for stationName in stationNames:
#             lon = geoLocation[geoLocation['stationName']==stationName]['longitude']
#             lat = geoLocation[geoLocation['stationName']==stationName]['latitude']
#
#             dataset_type = gdal.Open(infile_type)
#             geox, geoy = lonlat2geo(dataset_type, lon, lat)
#             imagex, imagey = geo2imagexy(dataset_type, geox, geoy)
#             imagex = int(np.round(imagex))
#             imagey = int(np.round(imagey))
#
#             emis_s_station = emis_s[imagex, imagey]
#             emis_v_station = emis_v[imagex, imagey]
#
#             fvc_n_station = fvcN[imagex, imagey]
#             # fvc_o_station = fvcO[imagex, imagey]
#             # fvc_Ahi_station = fvcAhi[imagex, imagey]
#
#             emis = emis_v_station * fvc_n_station + emis_s_station * (1 - fvc_n_station)
#             resultDoy.append(emis)
#
#         result.append(resultDoy)
#         print(doyStr + 'done')
#     outFileName = outDir + 'emis_LAI_s3b.txt'
#     np.savetxt(outFileName, result)

'''FVC NDVI计算'''
if __name__ == '__main__':
    satelliteName = 's3a'

    indir_tif = r'D:\data\s3a_tif\\'
    indir_lstN = r'D:\mydata\s3a\lst_china\s3a_lst_china/'
    indir_lstO = r'D:\mydata\s3a\lst_china\s3a_lst_china/'
    indir_lstAhi = r'D:\mydata\s3a\lst_china\ahi_lst_china/'
    indir_tif = r'D:\data\s3a_tif/'
    indir_tif_Ahi = r'D:\data\s3a_tif_ahi_red_nir\\'

    # indir_tif = r'D:\data\s3b_tif\\'
    # indir_lstN = r'D:\mydata\s3b\lst_china\s3b_lst_china/'
    # indir_lstO = r'D:\mydata\s3b\lst_china\s3b_lst_china/'
    # indir_lstAhi = r'D:\mydata\s3b\lst_china\ahi_lst_china/'
    # indir_tif = r'D:\data\s3b_tif/'
    # # indir_tif_Ahi = r'D:\data\s3b_tif_ahi_red_nir\\'


    indir_fvcN = r'D:\data\fvc\fvc_china\fvc_china_n_' + satelliteName + '//'
    indir_fvcO = r'D:\data\fvc\fvc_china\fvc_china_o_' + satelliteName + '//'
    indir_fvcAhi = r'D:\data\fvc\fvc_china\fvc_china_ahi_' + satelliteName + '//'
    indir_lai = r'D:\data\lai\lai_china/'

    indir_type = 'd:/data/type/'
    indir_ems = r'D:\data\emis/'
    infile_soil_emis = indir_ems + 'emis1_polar.tif'
    infile_type = indir_type + 'type_china_1000.tif'
    # infile_typeCopy = indir_type + 'type_china_1000copy.tif'
    infile_veg_emis = indir_ems + 'IGBP_Emi.txt'
    [emis_s, emis_v, geog, proj] = file2Array_static(infile_soil_emis, infile_veg_emis, infile_type)
    [type, width, height, bands, geog, proj] = read_image_gdal(infile_type)

    indir_geoLocation = r'D:\data\field\geoLocation.xlsx'
    geoLocation = pd.read_excel(indir_geoLocation)
    stationNames = geoLocation['stationName']

    filesName = search_file(indir_lstN, ['day', 'lst', 'nadir'])
    filesNum = len(filesName)

    outDir = r'D:\mydata\validation\lst\\'

    result = []
    for fileI in range(filesNum):
    # for fileI in range(3):
        startTime = time.time()
        fileName = filesName[fileI][:-18]
        doyStr = fileName[-3:]
        infileLstN = indir_lstN + fileName + '_day_lst_nadir.tif'
        infileLstO = indir_lstO + fileName + '_day_lst_obliq.tif'
        infileLstAhi = indir_lstAhi + fileName + '_day_lst.tif'
        c1 = os.path.exists(infileLstN)
        c2 = os.path.exists(infileLstO)
        c3 = os.path.exists(infileLstAhi)
        if c1 * c2 * c3 == 0:
            print(fileName + ' lack lst data')
            continue

        infileNir0 = indir_tif + fileName + '_day_nir_nadir.tif'
        infileRed0 = indir_tif + fileName + '_day_red_nadir.tif'
        c1 = os.path.exists(infileNir0)
        c2 = os.path.exists(infileRed0)
        if c1 * c2 == 0:
            print(fileName + ' lack red and nir data')
            continue

        infileNir0_Ahi = indir_tif_Ahi + fileName + '_day_nir.tif'
        infileRed0_Ahi = indir_tif_Ahi + fileName + '_day_red.tif'
        c1 = os.path.exists(infileNir0_Ahi)
        c2 = os.path.exists(infileRed0_Ahi)
        if c1 * c2 == 0:
            print(fileName + ' lack Ahi red and nir data')
            continue

        infileVzaN = indir_tif + fileName + '_day_vza_nadir.tif'
        infileVaaN = indir_tif + fileName + '_day_vaa_nadir.tif'
        infileVzaO = indir_tif + fileName + '_day_vza_obliq.tif'
        infileVaaO = indir_tif + fileName + '_day_vaa_obliq.tif'
        infileVzaAhi = r'D:\data\map\ahi_vza.tif'
        infileVaaAhi = r'd:\data\map\ahi_vaa.tif'
        c1 = os.path.exists(infileVzaN)
        c2 = os.path.exists(infileVaaN)
        c3 = os.path.exists(infileVzaO)
        c4 = os.path.exists(infileVaaO)
        if c1 * c2 * c3 * c4 == 0:
            print(fileName + ' lack observation angle data')
            continue

        infileSza = indir_tif + fileName + '_day_sza_nadir.tif'
        infileSaa = indir_tif + fileName + '_day_saa_nadir.tif'
        c1 = os.path.exists(infileSza)
        c2 = os.path.exists(infileSaa)
        if c1 * c2 == 0:
            print(fileName + ' lack sun angle data')
            continue

        infileFvcN = indir_fvcN + '2019_doy' + doyStr + '_fvc.tif'
        infileFvcO = indir_fvcO + '2019_doy' + doyStr + '_fvc.tif'
        infileFvcAhi = indir_fvcAhi + '2019_doy' + doyStr + '_fvc.tif'
        c1 = os.path.exists(infileFvcN)
        c2 = os.path.exists(infileFvcO)
        c3 = os.path.exists(infileFvcAhi)
        if c1 * c2 * c3 == 0:
            print(fileName + ' lack fvc data')
            continue

        [red, width, height, bands, geog, proj] = read_image_gdal(infileRed0)
        [nir, width, height, bands, geog, proj] = read_image_gdal(infileNir0)
        [red_Ahi, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileRed0_Ahi)
        [nir_Ahi, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileNir0_Ahi)
        red_Ahi = resize_data_near(red_Ahi, height, width)
        nir_Ahi = resize_data_near(nir_Ahi, height, width)

        infileLai = indir_lai + '2019_doy' + doyStr + '_lai.tif'
        if os.path.exists(infileLai) == 0:
            print(fileName + ' lack LAI data')
            continue

        resultDoy = []
        ndvi_min = 0.05
        ndvi_max = 0.95

        for stationName in stationNames:
            lon = geoLocation[geoLocation['stationName']==stationName]['longitude']
            lat = geoLocation[geoLocation['stationName']==stationName]['latitude']

            dataset_type = gdal.Open(infile_type)
            geox, geoy = lonlat2geo(dataset_type, lon, lat)
            imagex, imagey = geo2imagexy(dataset_type, geox, geoy)
            imagex = int(np.round(imagex))
            imagey = int(np.round(imagey))

            emis_s_station = emis_s[imagex, imagey]
            emis_v_station = emis_v[imagex, imagey]

            # NDVI = (nir[imagex, imagey] - red[imagex, imagey])/(nir[imagex, imagey] + red[imagex, imagey])
            # fvc_n_station = (NDVI - ndvi_min)/(ndvi_max - ndvi_min)
            # emis = emis_v_station * fvc_n_station + emis_s_station * (1 - fvc_n_station)

            NDVI = (nir_Ahi[imagex, imagey] - red_Ahi[imagex, imagey]) / (nir_Ahi[imagex, imagey] + red_Ahi[imagex, imagey])
            fvc_n_station = (NDVI - ndvi_min) / (ndvi_max - ndvi_min)
            emis = emis_v_station * fvc_n_station + emis_s_station * (1 - fvc_n_station)

            resultDoy.append(emis)

        result.append(resultDoy)
        print(doyStr + 'done')
    outFileName = outDir + 'emis_NDVI_s3a_AHI.txt'
    np.savetxt(outFileName, result)