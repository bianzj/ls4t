
import sys
import os

from base.util_file import read_image_dataset_gdal
from old.data_satellite.match_SLSTR_using_AHI import indir_slstr_tif

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import netCDF4
import time
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from base.rt.gap import *
import math
import warnings
import shutil
import numpy as np
# os.environ['PROJ_LIB'] =  r"/home/hero/anaconda3/envs/env_311/share/proj/"
warnings.filterwarnings("ignore")




'''
input dir
'''
indir_slstr_tif = ""
indir_slstr_lst = ""
indir_lai0 = ""
indir_tcw = ""
indir_emis = ""
indir_type = ""
indir_split = ""

'''
emis
'''
infile_emis1 = indir_emis + "emis1.tif"
infile_emis2 = indir_emis + "emis2.tif"
infile_type = indir_type + "type.tif"
infile_emisv = indir_emis + "IGBP.txt"
[emis1_s, ns, nl, nb, geog, proj,dataset_all] = read_image_dataset_gdal(infile_emis1)
emis1_s0 = emis1_s / 1000.0
[emis2_s, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_emis2)
emis2_s0 = emis2_s / 1000.0
[classif, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_type)
classif = np.asarray(classif, int)
emis_v = read_txt_array(infile_emisv, 0, 2)

'''
coefficients
'''
infile14 = indir_split + 'Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt'
infile15 = indir_split + 'Sentinel3A_SLSTR_SW_Seebor_Coef_Night.txt'

coeffs_day = read_txt_array(infile14, 0, 15)
coeffs_day = coeffs_day[:, 2:10]
coeffs_night = read_txt_array(infile15, 0, 15)
coeffs_night = coeffs_night[:, 2:10]



def invert_lst(indir,infile_bt8,infile_bt9,infile_vza):
    bt8, ns, nl, nb, geog, proj = read_image_gdal(infile_bt8)
    bt9, ns, nl, nb, geog, proj = read_image_gdal(infile_bt9)
    vza, nss, nll, nbb, geog, proj, dataset = read_image_dataset_gdal(infile_vza)

    nsi = np.zeros([nll, nss])
    nli = np.zeros([nll, nss])
    for k in range(nll):
        nli[k, :] = k
        nsi[k, :] = np.linspace(0, nss - 1, nss)
    nli = np.reshape(nli, -1)
    nsi = np.reshape(nsi, -1)
    temp1, temp2 = imagexy2geo(dataset, nli, nsi)
    lon, lat = geo2lonlat(dataset, temp1, temp2)
    lon = np.reshape(lon, [nll, nss])
    lat = np.reshape(lat, [nll, nss])
    indx, indy = loc2map(lat, lon, dataset_all)

    lai = lai0[indx, indy]

    emis2_s = emis2_s0[indx, indy]
    emis1_s = emis1_s0[indx, indy]
    ind0 = (classif < 17) * (classif > 0)
    classif[classif == 255] = 17
    emis1_v = emis_v[classif, 0] / 1000.0
    emis2_v = emis_v[classif, 1] / 1000.0

    timeid = indir[10:20]
    khour = int(timeid[10:12])
    kmin = timeid[10:12]
    tcw = tcw0[khour, indx, indy]

    fvc = gap_probability_hom_analytical(lai, vza)

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
    x2 = (bt8 + bt9) / 2.0
    ind = emis != 0
    x3[ind] = (1 - emis[ind]) / emis[ind] * x2[ind]
    x4[ind] = demis[ind] / (emis[ind] * emis[ind]) * x2[ind]
    x5 = (bt8 - bt9) / 2
    x6[ind] = (1 - emis[ind]) / emis[ind] * x5[ind]
    x7[ind] = demis[ind] / (emis[ind] * emis[ind]) * x5[ind]
    x8 = (bt8 - bt9) * (bt8 - bt9)

    wvc_ = np.asarray([0, 1.25, 2.25, 3.25, 4.25, 5.25, 100])
    vza_ = np.asarray([0, 3, 14.9, 38.6, 44.5, 51.2, 58, 65, 70, 75, 80])

    LST = np.zeros([nl, ns])
    for kwvc in range(len(wvc_) - 1):
        for kvza in range(len(vza_) - 1):

            ind = (tcw >= wvc_[kwvc]) * (tcw < wvc_[kwvc + 1]) * (vza >= vza_[kvza]) * (vza < vza_[kvza + 1]) * (
                    bt8 > 0) * (emis8 > 0) * ind0
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
    LST[ind] = 365
    ind = LST < 220
    LST[ind] = 0
    LST = LST * 100
    lstN = LST


isfirt = True
for kyear in range(2022,2023):
    indir_lai = indir_lai0 + str(kyear) +"/"
    for kmonth in range(1,13):
        for kday in range(1,32):

            fileid = "%04d"%kyear +"%02d"%kmonth +"%02d"%kday
            indirs = search_dir(indir_slstr_tif,fileid)
            n_dir = len(indirs)

            if n_dir == 0:continue


            kdoy = date2DOY(kyear,kmonth,kday)
            if(isfirt == True | (kdoy%4==1)):
                infile_lai = indir_lai + "/lai_%04d"%kyear +"%03d"%kdoy + ".h5"
                lai0 = read_h5py_item(infile_lai,"lai")


            infile_tcw = indir_tcw + "/tcw_" + fileid + ".h5"
            tcw0 = read_h5py_item(infile_tcw, "tcw")


            for kdir in range(0,n_dir):
                
                indir = indirs[kdir]

                outdir =  indir_slstr_tif

                ''''
                for nadir
                '''

                infile_bt8 = indir_slstr_tif + indirs[kdir] + "/bt8_nadir_proj.tif"
                infile_bt9 = indir_slstr_tif +indirs[kdir] + "/bt9_nadir_proj.tif"
                infile_vza = indir_slstr_tif +indirs[kdir] + "/vza_nadir_proj.tif"
                lstn = invert_lst(indir,infile_bt8,infile_bt9,infile_vza)


                infile_bt8 = indir_slstr_tif + indirs[kdir] + "/bt8_obliq_proj.tif"
                infile_bt9 = indir_slstr_tif +indirs[kdir] + "/bt9_obliq_proj.tif"
                infile_vza = indir_slstr_tif +indirs[kdir] + "/vza_obliq_proj.tif"
                lsto = invert_lst(indir,infile_bt8,infile_bt9,infile_vza)

                outfile = indir_slstr_tif  + 'lst_nadir.tif'
                write_image_gdal(lstn, ns, nl, 1, geog, proj, outfile)

                outfile = indir_slstr_tif  + 'lst_obliq.tif'
                write_image_gdal(lstn, ns, nl, 1, geog, proj, outfile)
















