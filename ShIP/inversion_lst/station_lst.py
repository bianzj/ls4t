from util.myfun import *
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from inversion_lsct.multiple_lsct import *

def doMul(param):
    return inv(param[0], param[1], param[2], param[3], param[4])

def inv(indir, satelliteName, stationName, coeffs_day, viewType):
    '''计算FVC不同策略：ndvi或者lai'''
    fvcType = 'ndvi'
    # fvcType = 'lai'
    G = 0.5
    ndviMin = 0.05
    ndviMax = 0.85

    # for viewType in viewTypes:
    #     for satelliteName in satelliteNames:
    #         for stationName in stationNames:
    indir_station = indir + stationName + '\\'
    indir_bt1 = indir_station + satelliteName + '_bt1_' + viewType + '.tif'
    indir_bt2 = indir_station + satelliteName + '_bt2_' + viewType + '.tif'
    indir_red = indir_station + satelliteName + '_red_' + viewType + '.tif'
    indir_nir = indir_station + satelliteName + '_nir_' + viewType + '.tif'
    indir_vza = indir_station + satelliteName + '_vza_' + viewType + '.tif'
    indir_ci = indir_station + '_ci.tif'
    indir_lai = indir_station + '_lai_Modis_smooth.tif'
    indir_cloud = indir_station + satelliteName + '_cloud_' + viewType + '.tif'
    indir_tcw = indir_station + satelliteName + '_tcw.tif'
    indir_emis1_s = indir_station + '_emis1_s.tif'
    indir_emis2_s = indir_station + '_emis2_s.tif'
    indir_emis1_v = indir_station + '_emis1_v.tif'
    indir_emis2_v = indir_station + '_emis2_v.tif'

    [bt1, ns, nl, nb, geog, proj] = read_image_gdal(indir_bt1)
    [bt2, ns, nl, nb, geog, proj] = read_image_gdal(indir_bt2)
    [vzaAll, ns, nl, nb, geog, proj] = read_image_gdal(indir_vza)
    [cloud, ns, nl, nb, geog, proj] = read_image_gdal(indir_cloud)
    [tcwAll, ns, nl, nb, geog, proj] = read_image_gdal(indir_tcw)
    [emis1_s, ns, nl, nb, geog, proj] = read_image_gdal(indir_emis1_s)
    [emis2_s, ns, nl, nb, geog, proj] = read_image_gdal(indir_emis2_s)
    [emis1_v, ns, nl, nb, geog, proj] = read_image_gdal(indir_emis1_v)
    [emis2_v, ns, nl, nb, geog, proj] = read_image_gdal(indir_emis2_v)

    if fvcType == 'ndvi':
        if viewType == 'nadir':
            [redN, ns, nl, nb, geog, proj] = read_image_gdal(indir_red)
            [nirN, ns, nl, nb, geog, proj] = read_image_gdal(indir_nir)
            ndviN = (nirN - redN) / (nirN + redN)
            ind = np.argwhere(np.isnan(ndviN))
            ndviN[ind] = 0
            ndviN[ndviN < ndviMin] = ndviMin
            ndviN[ndviN > ndviMax] = ndviMax
            fvc = (ndviN - ndviMin) / (ndviMax - ndviMin)
        else:
            [redO, ns, nl, nb, geog, proj] = read_image_gdal(indir_red)
            [nirO, ns, nl, nb, geog, proj] = read_image_gdal(indir_nir)
            ndviO = (nirO - redO) / (nirO + redO)
            ind = np.argwhere(np.isnan(ndviO))
            ndviO[ind] = 0
            ndviO[ndviO < ndviMin] = ndviMin
            ndviO[ndviO > ndviMax] = ndviMax
            fvc = (ndviO - ndviMin) / (ndviMax - ndviMin)

    if fvcType == 'lai':
        [ci, ns, nl, nb, geog, proj] = read_image_gdal(indir_ci)
        [lai, ns, nl, nb, geog, proj] = read_image_gdal(indir_lai)
        u = np.cos(np.deg2rad(vzaAll))
        fvc = 1 - np.exp(-G * lai * ci / u)
        ind = vzaAll == 0
        fvc[ind] = 0

    tcwAll = tcwAll/10.0
    emis1_s = emis1_s/1000.0
    emis2_s = emis2_s/1000.0
    emis1_v = emis1_v/1000.0
    emis2_v = emis2_v/1000.0

    emis1 = emis1_s * (1 - fvc) + emis1_v * fvc
    emis2 = emis2_s * (1 - fvc) + emis2_v * fvc
    emisAll = (emis1 + emis2) / 2
    demisAll = emis1 - emis2

    LST = np.zeros([nb, nl, ns])
    for doyI in range(366):
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
                ind = (tcw >= wvc_[kwvc]) * (tcw < wvc_[kwvc + 1]) * (vza >= vza_[kvza]) * (vza < vza_[kvza + 1]) * (
                        BT8 > 0) * (emis > 0)
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

    outdir_lst = indir + stationName + '_result\\' + satelliteName + '_lst_' + viewType + '.tif'
    write_image_gdal(LST, ns, nl, nb, geog, proj, outdir_lst)
    print(outdir_lst + ' done')

if __name__ == '__main__':
    satelliteNames = ['s3a', 's3b']
    viewTypes = ['nadir', 'oblique']
    indir_geoLocation = r'D:\data\field\geoLocation.xlsx'
    geoLocation = pd.read_excel(indir_geoLocation)
    stationNames = geoLocation['stationName']

    infileSplit = r'd:\data\split\Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt'
    coeffs_day = read_txt_array(infileSplit, 0, 15)
    coeffs_day = coeffs_day[:, 2:10]

    indir = r'D:\mydata\station\\'
    para = []
    for satelliteName in satelliteNames:
        for viewType in viewTypes:
            for stationName in stationNames:
                para.append([indir, satelliteName, stationName, coeffs_day, viewType])

    # doMul(para[0])
    pool = Pool(min(24, cpu_count()))
    for p in para:
        pool.apply_async(doMul, (p,))
    pool.close()
    pool.join()