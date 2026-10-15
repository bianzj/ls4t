import sys
import os

import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
from base.util_constant import *
from base.util_file import *
from base.util_data import *
import math
import warnings
warnings.filterwarnings("ignore")

'''
SLSTR lst反演
1. determine the study area for each image;
2. obtian the emis, type, tcwv, and lai;
3. calculate the lst
'''




# os.environ['PROJ_LIB'] = r'C:\Users\zzz\anaconda3\envs\patrol\Library\share\proj'
############################
### functions
##############################
if __name__ == '__main__':
    ndvi_min = ndvi_min_g
    ndvi_max = ndvi_max_g


    # indir_tif = r'd:\data\S3A_tif_heihe\\'
    # indir_lst = r'D:\mydata\s3a_lst_heihe_n_ndvi\\'
    #
    # indir_emis = r'd:\data\emis\\'
    # indir_fvc = r'D:\data\fvc\fvc_heihe_n//'
    # indir_type =r'd:\data\type\\'
    # indir_split = r'd:\data\split\\'
    #
    # infile10 = indir_emis + 'emis1_polar_heihe.tif'
    # infile11 = indir_emis + 'emis2_polar_heihe.tif'
    # infile13 = indir_emis + r'IGBP_Emi.txt'
    # infile12 = indir_type + 'type_heihe_1000.tif'
    # infile14 = indir_split + 'Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt'
    # infile15 = indir_split + 'Sentinel3A_SLSTR_SW_Seebor_Coef_Night.txt'

    indir_tif0 = r'/media/hero/slstr-southA-lst/'
    indir_lst0 = r'/media/hero/slstr-southA-lst/'
    indir_lsct0 = r'/media/hero/slstr-southA-lst/'
    mkdir_if_not_exist(indir_lst0)

    # indir_fvc = r"D:\data\lai\MCD_TIF\fvc\\"

    indir_emis = indir_tif0 + r'/base/emis/'
    indir_type = indir_tif0 + r'/base/type/'
    indir_tcw = r'/media/hero/rs/atm/tcwv_2017-2025/'
    indir_lai = r'/media/hero/rs/veg/lai_2021-2025_0.01/'
    indir_lai = r'/media/hero/rs/veg/lai_2002-2020_0.01/'

    # indir_fvc = r'/home/hero/data/LSCT3/LSCT_dm_2022/2_fvc(lai)/'

    infile10 = indir_emis + 'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
    infile11 = indir_emis + 'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
    infile13 = indir_emis + r'IGBP_Emi.txt'
    infile12 = indir_type + 'type_world_1000.tif'
    infile14 = indir_emis + 'Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt'
    infile15 = indir_emis + 'Sentinel3A_SLSTR_SW_Seebor_Coef_Night.txt'


    coeffs_day = read_txt_array(infile14, 0, 15)
    coeffs_day = coeffs_day[:, 2:10]
    coeffs_night = read_txt_array(infile15, 0, 15)
    coeffs_night = coeffs_night[:, 2:10]

    [emis1_s0, ns, nl, nb, geog, proj] = read_image_gdal(infile10)
    emis1_s0 = emis1_s0 / 1000.0
    [emis2_s0, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile11)
    emis2_s0 = emis2_s0 / 1000.0
    [classif0, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile12)
    classif0 = np.asarray(classif0, int)
    emis_v = read_txt_array(infile13, 0, 2)

    ifnadir = 1
    ifobliq = 1

    # 查找对应坐标
    infile_lai_ref = '/media/hero/rs/type/type_world_1000.tif'
    infile_tcw_ref = '/media/hero/rs/type/MCD12C1_2011_0.25.tif'
    dataset_emis = gdal.Open(infile10)
    dataset_lai = gdal.Open(infile_lai_ref)
    dataset_tcw = gdal.Open(infile_tcw_ref)
    dataset_type = gdal.Open(infile12)


    for kyear in range(2018,2019):
        indir_tif_temp = indir_tif0 + "/%04d/"%kyear + "/tif/"
        indir_lst_temp = indir_lst0 + "/%04d/"%kyear + "/lst/"
        indir_lai_temp = indir_lai + "/%04d/"%kyear
        indir_tcw_temp = indir_tcw + "/%04d/"%kyear

        for kmonth in range(3,13):
            for kday in range(1,32):

                #S3A_SL_1_RBT____20250101T072403_20250101T072703_20250102T172419_0179_121_049_2340_PS1_O_NT_004.SEN3
                timestr_target = "RBT____%04d"%kyear + "%02d"%kmonth + "%02d"%kday
                dirnames = search_dir(indir_tif_temp,[timestr_target])



                num_dir = len(dirnames)

                if (num_dir <= 0):continue

                kdoy = date2DOY(kyear, kmonth, kday)

                kdoy4 = (kdoy // 4)*4 + 1

                infile_lai = indir_lai_temp + "LAI_%04d"%kyear + "%03d.h5"%kdoy4
                lai0 = read_h5py_item(infile_lai, "/data")
                lai0 = lai0/1000.0
                infile_tcw = indir_tcw_temp + "tcwv_%04d"%kyear + "%02d"%kmonth + "%02d.h5"%kday
                tcw0 = read_h5py_item(infile_tcw,"/tcw")   ### TCWV TCW DATA
                tcw0 = tcw0/10.0
                for kdir in range(num_dir):

                    dirname = dirnames[kdir]
                    passtime = int(dirname[25:31])


                    filepath = indir_tif_temp + dirname + '/'
                    filepath_output = indir_lst_temp + dirname + '/'
                    mkdir_if_not_exist(filepath_output)


                    if ifnadir:

                        outfile = filepath_output  + 'lst_nadir.tif'



                        infile_bt1 = filepath + 'bt8_nadir.tif'
                        infile_bt2 = filepath + 'bt9_nadir.tif'
                        infile_vza = filepath + 'vza_nadir.tif'
                        infile_lat = filepath + 'lat_nadir.tif'
                        infile_lon = filepath + 'lon_nadir.tif'

                        if os.path.exists(outfile) == 1: continue
                        if os.path.exists(infile_bt1) == 0: continue
                        if os.path.exists(infile_lat) == 0: continue

                        [BT8, ns, nl, nb, geog, proj] = read_image_gdal(infile_bt1)
                        [BT9, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_bt2)
                        # [tcw, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile5)
                        [vza, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vza)
                        # [fvcN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile4)
                        [lat, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lat)
                        [lon, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lon)
                        lat = lat/100.0
                        lon = lon/100.0
                        vza = vza/100.0
                        BT8 = BT8/100.0
                        BT9 = BT9/100.0


                        indx_tcw,indy_tcw = loc2map(lat,lon,dataset_tcw)
                        indx_lai,indy_lai = loc2map(lat,lon,dataset_lai)
                        #indx_emis,indy_emis = loc2map(lat,lon,dataset_emis)
                        #indx_type,indy_type = loc2map(lat,lon,dataset_type)

                        indx_type = indx_lai
                        indx_emis = indx_lai
                        indy_type = indy_lai
                        indy_emis = indy_lai

                        ind = indx_lai > 18000
                        if np.sum(ind)>0:
                            indx_lai[ind] = 17999
                            indx_emis[ind] = 17999
                            indx_type[ind] = 17999
                            ind = indx_tcw > 720
                            indx_tcw[ind] = 719
                        indy_tcw[indy_tcw >= 1440] = 1439

                        lai = lai0[indx_lai,indy_lai]
                        lai = np.reshape(lai, [nl, ns])
                        lai[lai > 10.01] = 0
                        coeff = 0.825
                        fvc = 1 - np.exp(-coeff * lai * 0.5)
                        fvc = np.reshape(fvc,[nl,ns])

                        classif = classif0[indx_type,indy_type]
                        classif = np.reshape(classif, [nl, ns])


                        khour = math.floor(passtime / 10000)
                        kmin = math.floor((passtime - khour * 10000) / 100)
                        sec = passtime % 100
                        kmin_sec = kmin + sec / 60



                        tcw = tcw0[khour,indx_tcw, indy_tcw]
                        tcw = np.reshape(tcw, [nl, ns])



                        # tcw = tcw / 10.0
                        # tcw = resize_data_near(tcw,nl0,ns0)
                        # tcw = np.zeros([nl,ns])
                        # tcw[:] = 1.0

                        ind = (classif > 17)
                        classif[ind] = 0

                        ind0 = (classif < 17) *(classif > 0)

                        emis1_v = emis_v[classif, 0] / 1000.0
                        emis2_v = emis_v[classif, 1] / 1000.0
                        emis1_v = np.reshape(emis1_v, [nl, ns])
                        emis2_v = np.reshape(emis2_v, [nl, ns])
                        emis1_s = emis1_s0[indx_emis, indy_emis]
                        emis2_s = emis2_s0[indx_emis, indy_emis]
                        emis1_s = reshape(emis1_s,[nl,ns])
                        emis2_s = reshape(emis2_s,[nl,ns])

                        F = 0.05  # 地形因子
                        C1 = (1 - emis1_s) * emis1_v * F * (1 - fvc)  # 多次散射项
                        C2 = (1 - emis2_s) * emis2_v * F * (1 - fvc)  # 多次散射项
                        emis8 = emis1_s * (1 - fvc) + emis1_v * fvc + C1
                        emis9 = emis2_s * (1 - fvc) + emis2_v * fvc + C2
                        emis8[emis8 > 0.995] = 0.995
                        emis9[emis9 > 0.995] = 0.995


                        emis = (emis8 + emis9) * 0.5
                        demis = emis8 - emis9
                        x3 = np.zeros([nl, ns])
                        x4 = np.zeros([nl, ns])
                        x6 = np.zeros([nl, ns])
                        x7 = np.zeros([nl, ns])
                        x1 = 1
                        x2 = (BT8 + BT9) / 2.0
                        ind = emis != 0
                        x3[ind] = (1 - emis[ind]) / emis[ind] * x2[ind]
                        x4[ind] = demis[ind] / (emis[ind] * emis[ind]) * x2[ind]
                        x5 = (BT8 - BT9) / 2
                        x6[ind] = (1 - emis[ind]) / emis[ind] * x5[ind]
                        x7[ind] = demis[ind] / (emis[ind] * emis[ind]) * x5[ind]
                        x8 = (BT8 - BT9) * (BT8 - BT9)

                        wvc_ = np.asarray([0, 1.25, 2.25, 3.25, 4.25, 5.25, 100])
                        vza_ = np.asarray([0, 3, 14.9, 38.6, 44.5, 51.2, 58, 65, 70, 75, 80])

                        LST = np.zeros([nl, ns])
                        for kwvc in range(len(wvc_) - 1):
                            for kvza in range(len(vza_) - 1):

                                ind = (tcw >= wvc_[kwvc]) * (tcw < wvc_[kwvc + 1]) * (vza >= vza_[kvza]) * (vza < vza_[kvza + 1]) * (
                                        BT8 > 0) * (emis8 > 0) * ind0
                                if (np.sum(ind) <= 0): continue

                                ##########################################
                                ### the normal result
                                ##########################################

                                ind1 = kvza * 6 + kwvc
                                ind2 = (kvza + 1) * 6 + kwvc
                                coeff1 = coeffs_day[ind1, :]
                                coeff2 = coeffs_day[ind2, :]
                                vzatemp = vza[ind]
                                prop2 = (vzatemp - vza_[kvza]) / (vza_[kvza + 1] - vza_[kvza])
                                prop1 = 1 - prop2
                                LSTtemp = x1 * (prop1 * coeff1[0] + coeff2[0] * prop2) + x2[ind] * (
                                        prop1 * coeff1[1] + coeff2[1] * prop2) + \
                                          x3[ind] * (prop1 * coeff1[2] + coeff2[2] * prop2) + x4[ind] * (
                                                  prop1 * coeff1[3] + coeff2[3] * prop2) + \
                                          x5[ind] * (prop1 * coeff1[4] + coeff2[4] * prop2) + x6[ind] * (
                                                  prop1 * coeff1[5] + coeff2[5] * prop2) + \
                                          x7[ind] * (prop1 * coeff1[6] + coeff2[6] * prop2) + x8[ind] * (
                                                  prop1 * coeff1[7] + coeff2[7] * prop2)

                                LST[ind] = LSTtemp

                        ind = LST > 365
                        LST[ind] = 0
                        ind = LST < 220
                        LST[ind] = 0
                        LST = LST * 100.0
                        LST_uint16 = LST[:nl, :ns].astype(np.uint16)
                        write_image_gdal(LST_uint16, ns, nl, 1, geog, proj, outfile)

                    if ifobliq:

                        outfile = filepath_output  + 'lst_obliq.tif'



                        infile_bt1 = filepath + 'bt8_obliq.tif'
                        infile_bt2 = filepath + 'bt9_obliq.tif'
                        infile_vza = filepath + 'vza_obliq.tif'
                        infile_lat = filepath + 'lat_obliq.tif'
                        infile_lon = filepath + 'lon_obliq.tif'

                        if os.path.exists(outfile) == 1: continue
                        if os.path.exists(infile_bt1) == 0: continue
                        if os.path.exists(infile_lat) == 0: continue

                        [BT8, ns, nl, nb, geog, proj] = read_image_gdal(infile_bt1)
                        [BT9, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_bt2)
                        # [tcw, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile5)
                        [vza, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vza)
                        # [fvcN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile4)
                        [lat, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lat)
                        [lon, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lon)
                        lat = lat/100.0
                        lon = lon/100.0
                        vza = vza/100.0
                        BT8 = BT8/100.0
                        BT9 = BT9/100.0

                        lat[lat >= 90] = -(lat[lat >= 90] - 90)
                        lon[lon >= 180] = -(lon[lon >= 180] - 180)

                        indx_tcw,indy_tcw = loc2map(lat,lon,dataset_tcw)
                        indx_lai,indy_lai = loc2map(lat,lon,dataset_lai)
                        #indx_emis,indy_emis = loc2map(lat,lon,dataset_emis)
                        #indx_type,indy_type = loc2map(lat,lon,dataset_type)

                        indx_type = indx_lai
                        indx_emis = indx_lai
                        indy_type = indy_lai
                        indy_emis = indy_lai

                        ind = indx_lai > 18000
                        if np.sum(ind)>0:
                            indx_lai[ind] = 17999
                            indx_emis[ind] = 17999
                            indx_type[ind] = 17999
                            ind = indx_tcw > 720
                            indx_tcw[ind] = 719
                        indy_tcw[indy_tcw >= 1440] = 1439

                        lai = lai0[indx_lai,indy_lai]
                        lai[lai > 10.01] = 0
                        coeff = 0.825
                        fvc = 1-np.exp(-coeff * lai * 0.5)
                        fvc = np.reshape(fvc,[nl,ns])

                        classif = classif0[indx_type,indy_type]
                        classif = np.reshape(classif, [nl, ns])


                        khour = math.floor(passtime / 10000)
                        kmin = math.floor((passtime - khour * 10000) / 100)
                        sec = passtime % 100
                        kmin_sec = kmin + sec / 60


                        tcw = tcw0[khour,indx_tcw, indy_tcw]
                        tcw = np.reshape(tcw, [nl, ns])



                        # tcw = tcw / 10.0
                        # tcw = resize_data_near(tcw,nl0,ns0)
                        # tcw = np.zeros([nl,ns])
                        # tcw[:] = 1.0

                        ind = (classif > 17)
                        classif[ind] = 0

                        ind0 = (classif < 17) *(classif > 0)

                        emis1_v = emis_v[classif, 0] / 1000.0
                        emis2_v = emis_v[classif, 1] / 1000.0
                        emis1_v = np.reshape(emis1_v, [nl, ns])
                        emis2_v = np.reshape(emis2_v, [nl, ns])
                        emis1_s = emis1_s0[indx_emis, indy_emis]
                        emis2_s = emis2_s0[indx_emis, indy_emis]
                        emis1_s = reshape(emis1_s,[nl,ns])
                        emis2_s = reshape(emis2_s,[nl,ns])

                        F = 0.05  # 地形因子
                        C1 = (1 - emis1_s) * emis1_v * F * (1 - fvc)  # 多次散射项
                        C2 = (1 - emis2_s) * emis2_v * F * (1 - fvc)  # 多次散射项
                        emis8 = emis1_s * (1 - fvc) + emis1_v * fvc + C1
                        emis9 = emis2_s * (1 - fvc) + emis2_v * fvc + C2
                        emis8[emis8 > 0.995] = 0.995
                        emis9[emis9 > 0.995] = 0.995


                        emis = (emis8 + emis9) * 0.5
                        demis = emis8 - emis9
                        x3 = np.zeros([nl, ns])
                        x4 = np.zeros([nl, ns])
                        x6 = np.zeros([nl, ns])
                        x7 = np.zeros([nl, ns])
                        x1 = 1
                        x2 = (BT8 + BT9) / 2.0
                        ind = emis != 0
                        x3[ind] = (1 - emis[ind]) / emis[ind] * x2[ind]
                        x4[ind] = demis[ind] / (emis[ind] * emis[ind]) * x2[ind]
                        x5 = (BT8 - BT9) / 2
                        x6[ind] = (1 - emis[ind]) / emis[ind] * x5[ind]
                        x7[ind] = demis[ind] / (emis[ind] * emis[ind]) * x5[ind]
                        x8 = (BT8 - BT9) * (BT8 - BT9)

                        wvc_ = np.asarray([0, 1.25, 2.25, 3.25, 4.25, 5.25, 100])
                        vza_ = np.asarray([0, 3, 14.9, 38.6, 44.5, 51.2, 58, 65, 70, 75, 80])

                        LST = np.zeros([nl, ns])
                        for kwvc in range(len(wvc_) - 1):
                            for kvza in range(len(vza_) - 1):

                                ind = (tcw >= wvc_[kwvc]) * (tcw < wvc_[kwvc + 1]) * (vza >= vza_[kvza]) * (vza < vza_[kvza + 1]) * (
                                        BT8 > 0) * (emis8 > 0) * ind0
                                if (np.sum(ind) <= 0): continue

                                ##########################################
                                ### the normal result
                                ##########################################

                                ind1 = kvza * 6 + kwvc
                                ind2 = (kvza + 1) * 6 + kwvc
                                coeff1 = coeffs_day[ind1, :]
                                coeff2 = coeffs_day[ind2, :]
                                vzatemp = vza[ind]
                                prop2 = (vzatemp - vza_[kvza]) / (vza_[kvza + 1] - vza_[kvza])
                                prop1 = 1 - prop2
                                LSTtemp = x1 * (prop1 * coeff1[0] + coeff2[0] * prop2) + x2[ind] * (
                                        prop1 * coeff1[1] + coeff2[1] * prop2) + \
                                          x3[ind] * (prop1 * coeff1[2] + coeff2[2] * prop2) + x4[ind] * (
                                                  prop1 * coeff1[3] + coeff2[3] * prop2) + \
                                          x5[ind] * (prop1 * coeff1[4] + coeff2[4] * prop2) + x6[ind] * (
                                                  prop1 * coeff1[5] + coeff2[5] * prop2) + \
                                          x7[ind] * (prop1 * coeff1[6] + coeff2[6] * prop2) + x8[ind] * (
                                                  prop1 * coeff1[7] + coeff2[7] * prop2)

                                LST[ind] = LSTtemp

                        ind = LST > 365
                        LST[ind] = 0
                        ind = LST < 220
                        LST[ind] = 0
                        LST = LST * 100.0
                        LST_uint16 = LST[:nl, :ns].astype(np.uint16)
                        write_image_gdal(LST_uint16, ns, nl, 1, geog, proj, outfile)
