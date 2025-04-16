from util.myfun import *
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

satelliteNames = ['s3a', 's3b']

'''计算FVC不同策略：ndvi或者lai'''
fvcType = 'ndvi'
# fvcType = 'lai'
G = 0.5
ndviMin = 0.05
ndviMax = 0.85

indir_geoLocation = r'D:\data\field\geoLocation.xlsx'
geoLocation = pd.read_excel(indir_geoLocation)
stationNames = geoLocation['stationName']
# stationNames = ['AR']

indir = r'D:\mydata\station\\'
infileSplit  = r'd:\data\split\\Himawari8_AHI_SW_Seebor_Coef_Day.txt'
coeffs_day = read_txt_array(infileSplit, 0, 15)
coeffs_day = coeffs_day[:, 2:10]

for satelliteName in satelliteNames:
    for stationName in stationNames:
        indir_station = indir + stationName + '\\'
        indir_bt1 = indir_station + satelliteName + '_Ahi_bt1.tif'
        indir_bt2 = indir_station + satelliteName + '_Ahi_bt2.tif'
        indir_tcw = indir_station + satelliteName + '_tcw.tif'
        indir_red = indir_station + satelliteName + '_Ahi_red.tif'
        indir_nir = indir_station + satelliteName + '_Ahi_nir.tif'
        indir_emis1_s = indir_station + '_emis1_s.tif'
        indir_emis2_s = indir_station + '_emis2_s.tif'
        indir_emis1_v = indir_station + '_emis1_v.tif'
        indir_emis2_v = indir_station + '_emis2_v.tif'
        indir_vza = indir_station + '_Ahi_vza.tif'

        [bt1, ns, nl, nb, geog, proj] = read_image_gdal(indir_bt1)
        [bt2, ns, nl, nb, geog, proj] = read_image_gdal(indir_bt2)
        [tcwAll, ns, nl, nb, geog, proj] = read_image_gdal(indir_tcw)
        [red, ns, nl, nb, geog, proj] = read_image_gdal(indir_red)
        [nir, ns, nl, nb, geog, proj] = read_image_gdal(indir_nir)
        [emis1_s, ns, nl, nb, geog, proj] = read_image_gdal(indir_emis1_s)
        [emis2_s, ns, nl, nb, geog, proj] = read_image_gdal(indir_emis2_s)
        [emis1_v, ns, nl, nb, geog, proj] = read_image_gdal(indir_emis1_v)
        [emis2_v, ns, nl, nb, geog, proj] = read_image_gdal(indir_emis2_v)
        [vzaAll, ns, nl, nb, geog, proj] = read_image_gdal(indir_vza)

        ndvi = (nir - red) / (nir + red)
        ind = np.argwhere(np.isnan(ndvi))
        ndvi[ind] = 0
        ndvi[ndvi < ndviMin] = ndviMin
        ndvi[ndvi > ndviMax] = ndviMax
        fvc = (ndvi - ndviMin) / (ndviMax - ndviMin)

        tcwAll = tcwAll / 10.0
        emis1_s = emis1_s / 1000.0
        emis2_s = emis2_s / 1000.0
        emis1_v = emis1_v / 1000.0
        emis2_v = emis2_v / 1000.0

        emis1 = emis1_s * (1 - fvc) + emis1_v * fvc
        emis2 = emis2_s * (1 - fvc) + emis2_v * fvc
        emisAll = (emis1 + emis2) / 2
        demisAll = emis1 - emis2

        LST = np.zeros([nb, nl, ns])
        for doyI in range(366):
        # for doyI in range(1):
            x3 = np.zeros([nl, ns])
            x4 = np.zeros([nl, ns])
            x6 = np.zeros([nl, ns])
            x7 = np.zeros([nl, ns])

            BT8 = bt1[doyI, :, :]
            BT9 = bt2[doyI, :, :]
            emis = emisAll[doyI, :, :]
            demis = demisAll[doyI, :, :]
            tcw = tcwAll[doyI, :, :]
            vza = vzaAll[doyI, :, :]

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

            lst = np.zeros([nl, ns])
            for kwvc in range(len(wvc_) - 1):
                for kvza in range(len(vza_) - 1):

                    ind = (tcw >= wvc_[kwvc]) * (tcw < wvc_[kwvc + 1]) * (vza >= vza_[kvza]) * (
                                vza < vza_[kvza + 1]) * (BT8 > 0) * (emis > 0)
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

                    lst[ind] = LSTtemp
            ind = lst > 365
            lst[ind] = 365
            ind = lst < 220
            lst[ind] = 0
            LST[doyI, :, :] = lst

        outfileResultDir = indir + stationName + '_result\\'
        if os.path.exists(outfileResultDir):
            print(stationName + '_result// exists')
        else:
            print(stationName + '_result// created')
            os.mkdir(outfileResultDir)
        outdir_lst = indir + stationName + '_result\\' + satelliteName + '_Ahi_lst.tif'
        write_image_gdal(LST, ns, nl, nb, geog, proj, outdir_lst)
        print(satelliteName + '_Ahi_lst.tif' + ' done')























