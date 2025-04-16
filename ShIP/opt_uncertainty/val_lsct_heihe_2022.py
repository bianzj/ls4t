import os.path

import numpy as np
import pandas as pd
from scipy import interpolate
import matplotlib.mlab as ml
import matplotlib.pyplot as plt
import time
from multiprocessing import Pool
from util.util import *
import warnings
from datetime import datetime
warnings.filterwarnings("ignore")

'''remove the emissivity effect'''
def remove_emissivity(Tobj,emis=0.95,Tsky=240,wl = 10.8):
    Robj = planck(wl,Tobj+273.15)
    Rsky = planck(wl,Tsky)
    Robjn = (Robj-Rsky*(1-emis))/emis
    Tobjn = inv_planck(wl,Robjn)
    return Tobjn-273.15

'''obtain the statistic result'''
def cal_rmse_r2(data1,data2,tshred=100):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2

'''obain the inversion data'''
infile_lsct = r'D:\data\LSCT\lsct3.txt'
lsct = read_txt_float(infile_lsct)
doy_ = lsct[:,0]
pst_ = lsct[:,1]

'''obtain the measurement data'''
indir_forest_tc = r'D:\data\LSCT\validation\heihe2022\林地#2_冠层\\240305006010100'
# indir_forest_tss = r'D:\data\LSCT\validation\heihe2022\林地#2_陇间\\240305006010083'
indir_forest_tss = r'D:\data\LSCT\validation\heihe2022\灌渠#1\\240305006010114'
indir_forest_tsh = r'D:\data\LSCT\validation\heihe2022\林地#2_阴影\\240305006010087'

indir_crop_tc = r'D:\data\LSCT\validation\heihe2022\玉米#6_冠层\\240305006010099'
indir_crop_tss = r'D:\data\LSCT\validation\heihe2022\玉米#6_裸土\\240305006010120'
indir_crop_tsh = r'D:\data\LSCT\validation\heihe2022\玉米#6_阴影\\240305006010103'


year = 2022
tempe_min = 10
tempe_max = 70
emis_soil = 0.950
emis_leaf = 0.985
tsh_forest_mea = []
tss_forest_mea = []
tc_forest_mea = []
tsh_crop_mea = []
tss_crop_mea = []
tc_crop_mea = []
n_data = np.size(doy_)
for k in range(n_data):
    doy = doy_[k]
    pst = pst_[k]



    month,day = doy2date(year,doy)
    hour = pst//10000 + 8
    min = np.round(pst%10000/100)
    if min ==60:
        hour=hour+1
        min = 0
    specTime = datetime(year, month, np.int(day), np.int(hour),np.int(min))

    infile_forest_tsh = indir_forest_tsh + '_%4d-'%year+'%02d-'%month+'%02d.csv'%day
    infile_forest_tss = indir_forest_tss + '_%4d-'%year+'%02d-'%month+'%02d.csv'%day
    infile_forest_tc = indir_forest_tc + '_%4d-'%year+'%02d-'%month+'%02d.csv'%day
    infile_crop_tsh = indir_crop_tsh + '_%4d-'%year+'%02d-'%month+'%02d.csv'%day
    infile_crop_tss = indir_crop_tss + '_%4d-'%year+'%02d-'%month+'%02d.csv'%day
    infile_crop_tc = indir_crop_tc + '_%4d-'%year+'%02d-'%month+'%02d.csv'%day

    if(os.path.exists(infile_forest_tsh)==0):
        tsh_forest_mea.append(0)
        tss_forest_mea.append(0)
        tc_forest_mea.append(0)
        tsh_crop_mea.append(0)
        tss_crop_mea.append(0)
        tc_crop_mea.append(0)
        continue

    tsh_forest_aws = pd.read_csv(infile_forest_tsh, encoding="gbk",parse_dates=['数据时间'])
    tss_forest_aws = pd.read_csv(infile_forest_tss, encoding="gbk",parse_dates=['数据时间'])
    tc_forest_aws = pd.read_csv(infile_forest_tc, encoding="gbk",parse_dates=['数据时间'])
    tsh_crop_aws = pd.read_csv(infile_crop_tsh, encoding="gbk",parse_dates=['数据时间'])
    tss_crop_aws = pd.read_csv(infile_crop_tss, encoding="gbk",parse_dates=['数据时间'])
    tc_crop_aws = pd.read_csv(infile_crop_tc, encoding="gbk",parse_dates=['数据时间'])

    ind = np.where(tsh_forest_aws['数据时间']==specTime)
    print(specTime)
    if(np.size(ind)==0):
        print(specTime)
    ind = ind[0]
    tsh_forest = tsh_forest_aws._get_column_array(2)[ind][0]
    tss_forest = tss_forest_aws._get_column_array(2)[ind][0]
    tc_forest = tc_forest_aws._get_column_array(2)[ind][0]
    tsh_crop = tsh_crop_aws._get_column_array(2)[ind][0]
    tss_crop = tss_crop_aws._get_column_array(2)[ind][0]
    tc_crop = tc_crop_aws._get_column_array(2)[ind][0]

    tsh_forest_mea.append(tsh_forest)
    tss_forest_mea.append(tss_forest)
    tc_forest_mea.append(tc_forest)
    tsh_crop_mea.append(tsh_crop)
    tss_crop_mea.append(tss_crop)
    tc_crop_mea.append(tc_crop)

tsh_forest_mea = np.asarray(tsh_forest_mea)
tss_forest_mea = np.asarray(tss_forest_mea)
tc_forest_mea  = np.asarray(tc_forest_mea)
tsh_crop_mea = np.asarray(tsh_crop_mea)
tss_crop_mea = np.asarray(tss_crop_mea)
tc_crop_mea  = np.asarray(tc_crop_mea)

tsh_forest_mea = remove_emissivity(tsh_forest_mea,emis_soil)
tss_forest_mea = remove_emissivity(tss_forest_mea,emis_soil)
tc_forest_mea = remove_emissivity(tc_forest_mea,emis_leaf)
tsh_crop_mea = remove_emissivity(tsh_crop_mea,emis_soil)
tss_crop_mea = remove_emissivity(tss_crop_mea,emis_soil)
tc_crop_mea = remove_emissivity(tc_crop_mea,emis_leaf)


cloud_forest_inv = np.asarray(lsct[:,2])
cloud_crop_inv = np.asarray(lsct[:,6])
tsh_forest_inv = np.asarray(lsct[:,4])-273.15
tss_forest_inv = np.asarray(lsct[:,3])-273.15
tc_forest_inv  = np.asarray(lsct[:,5])-273.15
tsh_crop_inv = np.asarray(lsct[:,8])-273.15
tss_crop_inv = np.asarray(lsct[:,7])-273.15
tc_crop_inv  = np.asarray(lsct[:,9])-273.15


ind = (cloud_forest_inv==0)*(np.isnan(tsh_forest_mea)==0)*(np.isnan(tss_forest_mea)==0)*(np.isnan(tc_forest_mea)==0)*\
        (tc_forest_inv<tempe_max)*(tc_forest_inv>tempe_min)* \
        (tsh_forest_inv<tempe_max)*(tsh_forest_inv>tempe_min)*\
        (tss_forest_inv<tempe_max)*(tss_forest_inv>tempe_min)

dif_threshold = 10
bias_tss,rmse_tss,r2_tss = cal_rmse_r2(tss_forest_mea[ind],tss_forest_inv[ind],dif_threshold)
bias_tsh,rmse_tsh,r2_tsh = cal_rmse_r2(tsh_forest_mea[ind],tsh_forest_inv[ind],dif_threshold)
bias_tc,rmse_tc,r2_tc = cal_rmse_r2(tc_forest_mea[ind],tc_forest_inv[ind],dif_threshold)
print(rmse_tss,rmse_tsh,rmse_tc)

plt.figure(figsize=[4.5,4])
plt.plot(tss_forest_mea[ind],tss_forest_inv[ind],'ro')
plt.plot(tsh_forest_mea[ind],tsh_forest_inv[ind],'bo')
plt.plot(tc_forest_mea[ind],tc_forest_inv[ind],'go')
plt.xlim([15,60])
plt.ylim([15,60])
plt.plot([0,100],[0,100],'k--')
plt.xlabel('Measured')
plt.ylabel('Inverted')
plt.legend(['Sunlit Soil','Shaded Soil','Canopy'])
plt.title('Forest')
plt.show()


ind = (cloud_crop_inv==0)*(np.isnan(tsh_crop_mea)==0)*(np.isnan(tss_crop_mea)==0)*(np.isnan(tc_crop_mea)==0)*\
        (tc_crop_inv<tempe_max)*(tc_crop_inv>tempe_min)* \
        (tsh_crop_inv<tempe_max)*(tsh_crop_inv>tempe_min)*\
        (tss_crop_inv<tempe_max)*(tss_crop_inv>tempe_min)


bias_tss,rmse_tss,r2_tss = cal_rmse_r2(tss_crop_mea[ind],tss_crop_inv[ind],dif_threshold)
bias_tsh,rmse_tsh,r2_tsh = cal_rmse_r2(tsh_crop_mea[ind],tsh_crop_inv[ind],dif_threshold)
bias_tc,rmse_tc,r2_tc = cal_rmse_r2(tc_crop_mea[ind],tc_crop_inv[ind],dif_threshold)
print(rmse_tss,rmse_tsh,rmse_tc)

plt.figure(figsize=[4.5,4])
plt.plot(tss_crop_mea[ind],tss_crop_inv[ind],'ro')
plt.plot(tsh_crop_mea[ind],tsh_crop_inv[ind],'bo')
plt.plot(tc_crop_mea[ind],tc_crop_inv[ind],'go')
plt.xlim([15,60])
plt.ylim([15,60])
plt.plot([0,100],[0,100],'k--')
plt.xlabel('Measured')
plt.ylabel('Inverted')
plt.legend(['Sunlit Soil','Shaded Soil','Canopy'])
plt.title('Crop')
plt.show()
