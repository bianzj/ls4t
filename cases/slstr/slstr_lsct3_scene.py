from osgeo import gdal
from numpy import reshape
from base.dates import date2DOY
from base.files import mkdir_if_not_exist, read_h5py_item, read_image_gdal, read_txt_array, search_dir, write_image_gdal
from base.lsct import cal_fvc_from_lai, ndvi_max_g, ndvi_min_g
from base.radiometry import inv_planck, planck
from base.rt.hotspot import hotspot_layer
from base.spatial import loc2map
from slstr.slstr_grid import adjust_xmax_no_g, adjust_xmin_no_g, adjust_ymax_no_g

import sys
import os

import numpy as np

import time
import math
import warnings
warnings.filterwarnings("ignore")

'''
SLSTR lst反演
1. determine the study area for each image;
2. obtian the emis, type, tcwv, and lai;
3. calculate the lst
'''
from sklearn.linear_model import Ridge
def fitting_with_ridge(bb, ww):
    # alpha 是正则化强度，需要根据数据噪声调优，通常尝试 0.01, 0.1, 1.0
    reg = Ridge(alpha=0.01, fit_intercept=False)
    reg.fit(ww.T, bb.T)  # 注意你的维度是 (3, N) 还是 (N, 3)，需要保持一致
    return reg.coef_



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

    indir_tif0 = r'/media/hero/slstr-euro/'
    indir_lst0 = r'/media/hero/slstr-euro/'
    indir_lsct0 = r'/media/hero/slstr-euro/'
    mkdir_if_not_exist(indir_lsct0)

    # indir_fvc = r"D:\data\lai\MCD_TIF\fvc\\"

    indir_emis = r'/media/hero/slstr-euro/0_base/emis/'
    indir_type =r'/media/hero/slstr-euro/0_base/type/'
    indir_split = r'/media/hero/slstr-euro/0_base/base/'
    indir_tcw = r'/media/hero/earth/ERA5_Daily_H5/'
    indir_lai = r'/media/hero/rs/veg/lai_2021-2025_0.01/'

    # indir_fvc = r'/home/hero/data/LSCT3/LSCT_dm_2022/2_fvc(lai)/'

    infile10 = indir_emis + 'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
    infile11 = indir_emis + 'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
    infile13 = indir_emis + r'IGBP_Emi.txt'
    infile12 = indir_type + 'type_world_1000.tif'

    [emis1_s0, ns, nl, nb, geog, proj] = read_image_gdal(infile10)
    emis1_s0 = emis1_s0 / 1000.0
    [emis2_s0, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile11)
    emis2_s0 = emis2_s0 / 1000.0
    [classif0, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile12)
    classif0 = np.asarray(classif0, int)
    emis_v = read_txt_array(infile13, 0, 2)

    n, m = 2, 2
    ws = 5
    hspot = 0.5
    wl = 10.8
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.5  # 0.05
    inv_Cm = np.linalg.inv(np.diag([soil_radiance_variance, leaf_radiance_variance]))
    inv_Cd = 1.0 / (sensor_noise ** 2)


    # 查找对应坐标
    infile_lai_ref = '/media/hero/rs/type/type_world_1000.tif'
    infile_tcw_ref = '/media/hero/rs/type/MCD12C1_2011_0.25.tif'
    dataset_emis = gdal.Open(infile10)
    dataset_lai = gdal.Open(infile_lai_ref)
    dataset_tcw = gdal.Open(infile_tcw_ref)
    dataset_type = gdal.Open(infile12)


    for kyear in range(2025,2026):
        indir_tif_temp = indir_tif0 + "/%04d/"%kyear + "/tif/"
        indir_lst_temp = indir_lst0 + "/%04d/"%kyear + "/lst/"
        indir_lsct_temp = indir_lsct0 + "/%04d/"%kyear + "/lsct3/"
        indir_lai_temp = indir_lai + "/%04d/"%kyear
        indir_tcw_temp = indir_tcw + "/%04d/"%kyear

        for kmonth in range(7,8):
            for kday in range(3,4):

                #S3A_SL_1_RBT____20250101T072403_20250101T072703_20250102T172419_0179_121_049_2340_PS1_O_NT_004.SEN3
                timestr_target = "RBT____%04d"%kyear + "%02d"%kmonth + "%02d"%kday
                dirnames = search_dir(indir_lst_temp,[timestr_target])

                num_dir = len(dirnames)

                if (num_dir <= 0): continue

                kdoy = date2DOY(kyear, kmonth, kday)

                kdoy4 = (kdoy // 4)*4 + 1

                infile_lai = indir_lai_temp + "lai_%04d"%kyear + "%03d.h5"%kdoy4
                lai0 = read_h5py_item(infile_lai, "/data")
                lai0 = lai0/1000.0
                lai0[lai0>10] = np.NaN
                for kdir in range(num_dir):

                    dirname = dirnames[kdir]
                    passtime = int(dirname[25:31])

                    if passtime != 100120: continue


                    filepath_tif = indir_tif_temp + dirname + '/'
                    filepath_lst = indir_lst_temp + dirname + '/'
                    filepath_output = indir_lsct_temp + dirname + '/'
                    mkdir_if_not_exist(filepath_output)




                    outfile = filepath_output  + 'lsct3.tif'

                    infile_lstN = filepath_lst + 'lst_nadir.tif'
                    infile_lstO = filepath_lst + 'lst_obliq.tif'
                    infile_vzaN = filepath_tif + 'vza_nadir.tif'
                    infile_vzaO = filepath_tif + 'vza_obliq.tif'
                    infile_lat = filepath_tif + 'lat_obliq.tif'
                    infile_lon = filepath_tif + 'lon_obliq.tif'
                    infile_cldN = filepath_tif + 'cloud_nadir.tif'
                    infile_cldO = filepath_tif + 'cloud_obliq.tif'
                    infile_vaaN = filepath_tif + 'vaa_nadir.tif'
                    infile_vaaO = filepath_tif + 'vaa_obliq.tif'
                    infile_szaO = filepath_tif + 'sza_obliq.tif'
                    infile_saaO = filepath_tif + 'saa_obliq.tif'

                    if os.path.exists(outfile) == 1: continue
                    #if os.path.exists(filepath_output) == 1: continue
                    if os.path.exists(infile_lstN) == 0: continue
                    if os.path.exists(infile_lat) == 0: continue
                    if os.path.exists(infile_szaO) == 0: continue

                    [lstN, ns, nl, nb, geog, proj] = read_image_gdal(infile_lstN)
                    [lstO, ns, nl, temp3, temp4, temp5] = read_image_gdal(infile_lstO)
                    [vzaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vzaN)
                    [vzaO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vzaO)
                    [lat, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lat)
                    [lon, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lon)
                    [cldN, ns, nl, nb, geog, proj] = read_image_gdal(infile_cldN)
                    [cldO, ns, nl, temp3, temp4, temp5] = read_image_gdal(infile_cldO)
                    [vaaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaaN)
                    [vaaO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaaO)
                    [szaO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_szaO)
                    [saaO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_saaO)

                    lat = lat/100.0
                    lon = lon/100.0
                    vzaN = vzaN/100.0
                    vzaO = vzaO/100.0
                    lstN = lstN/100.0
                    lstO = lstO/100.0
                    vaaN = vaaN/100.0
                    vaaO = vaaO/100.0
                    szaO = szaO/100.0
                    saaO = saaO/100.0

                    lat[lat >= 90] = -(lat[lat >= 90] - 90)
                    lon[lon >= 180] = -(lon[lon >= 180] - 180)

                    vzaNO = vzaN[0:adjust_ymax_no_g,adjust_xmin_no_g:adjust_xmax_no_g]
                    lstNO = lstN[0:adjust_ymax_no_g,adjust_xmin_no_g:adjust_xmax_no_g]
                    cldNO = cldN[0:adjust_ymax_no_g,adjust_xmin_no_g:adjust_xmax_no_g]
                    vaaNO = vaaN[0:adjust_ymax_no_g,adjust_xmin_no_g:adjust_xmax_no_g]


                    indx_lai,indy_lai = loc2map(lat,lon,dataset_lai)
                    # indx_emis,indy_emis = loc2map(lat,lon,dataset_emis)
                    # indx_type,indy_type = loc2map(lat,lon,dataset_type)

                    indx_type = indx_lai
                    indx_emis = indx_lai
                    indy_type = indy_lai
                    indy_emis = indy_lai

                    ind = indx_lai > 18000
                    if np.sum(ind)>0:
                        indx_lai[ind] = 17999
                        indx_emis[ind] = 17999
                        indx_type[ind] = 17999



                    lai = lai0[indx_lai,indy_lai]
                    lai = np.reshape(lai,[nl,ns])
                    lai[lai > 10.01] = 0
                    coeff = 0.825
                    fvc = 1 - np.exp(-coeff * lai * 0.5)
                    fvc = np.reshape(fvc,[nl,ns])



                    fvcN = cal_fvc_from_lai(vzaNO,lai)
                    fvcO = cal_fvc_from_lai(vzaO,lai)

                    vsaO = np.abs(vaaO - saaO)
                    vsaNO = np.abs(vaaNO - saaO)
                    # pssO = hotspot_analytical(lai,hspot,vzaO,szaO,vsaO)
                    # pssNO = hotspot_analytical(lai,hspot,vzaNO,szaO,vsaNO)

                    pssO = hotspot_layer(lai,hspot,vzaO,szaO,vsaO)
                    pssNO = hotspot_layer(lai,hspot,vzaNO,szaO,vsaNO)

                    classif = classif0[indx_type,indy_type]
                    classif = np.reshape(classif, [nl, ns])


                    khour = math.floor(passtime / 10000)
                    kmin = math.floor((passtime - khour * 10000) / 100)
                    sec = passtime % 100
                    kmin_sec = kmin + sec / 60


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
                    emis1_ss_o = emis1_s *  pssO
                    emis1_sh_o = emis1_s * (1-fvcO-pssO)
                    emis1_ss_no = emis1_s * pssNO
                    emis1_sh_no = emis1_s * (1-fvcN-pssNO)

                    F = 0.05  # 地形因子
                    C1 = (1 - emis1_s) * emis1_v * F * (1 - fvc)  # 多次散射项
                    emis = emis1_s * (1 - fvc) + emis1_v * fvc + C1
                    emis[emis > 0.999] = 0.999

                    w = np.zeros([nl, ns, n, m])

                    eevN0 = fvcN * emis1_v
                    eessN0 = emis1_ss_no
                    eeshN0 = emis1_sh_no

                    eevO0 = fvcO * emis1_v
                    eessO0 = emis1_ss_o
                    eeshO0 = emis1_sh_o

                    eeV0 = np.stack([eevN0,eevO0])
                    eeSS0 = np.stack([eessN0,eessO0])
                    eeSH0 = np.stack([eeshN0, eeshO0])

                    lstNO[lstNO<100] = np.NaN
                    lstO[lstO<100] = np.NaN
                    bN0 = planck(wl,lstNO) * emis
                    bO0 = planck(wl,lstO) * emis

                    mask0 = (cldNO == 0) * (lai > 0.25) * (cldO == 0) * (lai < 10.01) * (emis > 0) * (bN0 > 5) * (bO0 > 5)
                    indx,indy = np.where(mask0)

                    num_p = len(indx)
                    if (num_p ==0 ):continue
                    off = 1

                    resultT = np.zeros([3,nl,ns])
                    for kp in range(num_p):

                        kl = indx[kp]
                        ks = indy[kp]
                        if kl < off: continue
                        if ks < off: continue
                        if kl > nl-off-1:continue
                        if ks > ns-off-1:continue

                        kl1 = kl -off
                        kl2 = kl + off +1
                        ks1 = ks - off
                        ks2 = ks + off + 1
                        lai_temp = lai[kl,ks]
                        eeV = np.reshape(eeV0[:,kl1:kl2,ks1:ks2],-1)
                        eeSS = np.reshape(eeSS0[:,kl1:kl2,ks1:ks2],-1)
                        eeSH = np.reshape(eeSH0[:,kl1:kl2,ks1:ks2],-1)
                        bN = np.reshape(bN0[kl1:kl2,ks1:ks2],-1)
                        bO = np.reshape(bO0[kl1:kl2,ks1:ks2],-1)
                        mask1 = np.reshape(mask0[kl1:kl2,ks1:ks2],-1)
                        mask2 = np.hstack([mask1,mask1])

                        ind2 = ((eeSH+eeSS) > 0.1) * mask2 * ((eeSS + eeSH) < 0.9)
                        if(np.sum(ind2)<=5):continue
                        bb = np.hstack([bN,bO])
                        ww = np.stack([eeSS[ind2],eeSH[ind2],eeV[ind2]])
                        bb = bb[ind2]
                        coeffs = np.asarray(fitting_with_ridge(bb, ww))
                        temp = inv_planck(wl,coeffs)
                        resultT[:,kl,ks] = temp

                        a = 10

                    print(outfile)
                    write_image_gdal(resultT,nl,ns,3,'','',outfile)

                    a = 10
