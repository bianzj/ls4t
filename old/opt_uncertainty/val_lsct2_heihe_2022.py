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
def cal_rmse_r2(data1,data2,tshred=10):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2

'''obain the inversion data'''
infile_lsct = r'D:\data\LSCT_heihe_2022\lsct2.txt'
lsct = read_txt_float(infile_lsct)
idex=np.lexsort([lsct[:,0]])
lsct = lsct[idex, :]
doy_ = lsct[:,0]
pst_ = lsct[:,1]

'''obtain the measurement data'''
indir_forest_tc = r'D:\data\LSCT_heihe_2022\validation\heihe2022\林地#2_冠层\\240305006010100'
# indir_forest_tc = r'D:\data\LSCT_heihe_2022\validation\heihe2022\果园#杏树\\240305006010101'
indir_forest_ts = r'D:\data\LSCT_heihe_2022\validation\heihe2022\林地#2_陇间\\240305006010083'
# indir_forest_ts = r'D:\data\LSCT_heihe_2022\validation\heihe2022\灌渠#2\\240305006010113'
# indir_forest_ts = r'D:\data\LSCT_heihe_2022\validation\heihe2022\灌渠#1\\240305006010114'
# indir_forest_ts = r'D:\data\LSCT_heihe_2022\validation\heihe2022\林地#2_阴影\\240305006010087'
# indir_forest_ts = r'D:\data\LSCT_heihe_2022\validation\heihe2022\道路\\240305006010117'

indir_crop_tc = r'D:\data\LSCT_heihe_2022\validation\heihe2022\玉米#6_冠层\\240305006010099'
indir_crop_ts = r'D:\data\LSCT_heihe_2022\validation\heihe2022\玉米#6_裸土\\240305006010120'
# indir_crop_ts = r'D:\data\LSCT_heihe_2022\validation\heihe2022\玉米#6_阴影\\240305006010103'
# indir_forest_ts = r'D:\data\LSCT_heihe_2022\validation\heihe2022\灌渠#2\\240305006010113'
# indir_crop_ts  = r'D:\data\LSCT_heihe_2022\validation\heihe2022\灌渠#2\\240305006010113'


year = 2022
tempe_min = 10
tempe_max = 70
emis_soil = 0.950
emis_leaf = 0.985

ts_forest_mea = []
tc_forest_mea = []

ts_crop_mea = []
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

    infile_forest_ts = indir_forest_ts + '_%4d-'%year+'%02d-'%month+'%02d.csv'%day
    infile_forest_tc = indir_forest_tc + '_%4d-'%year+'%02d-'%month+'%02d.csv'%day

    infile_crop_ts = indir_crop_ts + '_%4d-'%year+'%02d-'%month+'%02d.csv'%day
    infile_crop_tc = indir_crop_tc + '_%4d-'%year+'%02d-'%month+'%02d.csv'%day

    if(os.path.exists(infile_forest_ts)==0):
        # tsh_forest_mea.append(0)
        ts_forest_mea.append(0)
        tc_forest_mea.append(0)
        ts_crop_mea.append(0)
        tc_crop_mea.append(0)
        continue


    ts_forest_aws = pd.read_csv(infile_forest_ts, encoding="gbk",parse_dates=['数据时间'])
    tc_forest_aws = pd.read_csv(infile_forest_tc, encoding="gbk",parse_dates=['数据时间'])

    ts_crop_aws = pd.read_csv(infile_crop_ts, encoding="gbk",parse_dates=['数据时间'])
    tc_crop_aws = pd.read_csv(infile_crop_tc, encoding="gbk",parse_dates=['数据时间'])

    ind = np.where(ts_forest_aws['数据时间']==specTime)
    print(specTime)
    if(np.size(ind)==0):
        print(specTime)
    ind = ind[0]
    ts_forest = ts_forest_aws._get_column_array(2)[ind][0]
    tc_forest = tc_forest_aws._get_column_array(2)[ind][0]

    ts_crop = ts_crop_aws._get_column_array(2)[ind][0]
    tc_crop = tc_crop_aws._get_column_array(2)[ind][0]

    # tsh_forest_mea.append(tsh_forest)
    ts_forest_mea.append(ts_forest)
    tc_forest_mea.append(tc_forest)
    ts_crop_mea.append(ts_crop)
    tc_crop_mea.append(tc_crop)

ts_forest_mea = np.asarray(ts_forest_mea)
tc_forest_mea  = np.asarray(tc_forest_mea)
ts_crop_mea = np.asarray(ts_crop_mea)
tc_crop_mea  = np.asarray(tc_crop_mea)

ts_forest_mea = remove_emissivity(ts_forest_mea,emis_soil)
tc_forest_mea = remove_emissivity(tc_forest_mea,emis_leaf)
ts_crop_mea = remove_emissivity(ts_crop_mea,emis_soil)
tc_crop_mea = remove_emissivity(tc_crop_mea,emis_leaf)


cloud_forest_inv = np.asarray(lsct[:,2])
cloud_crop_inv = np.asarray(lsct[:,5])
ts_forest_inv = np.asarray(lsct[:,3])-273.15
tc_forest_inv  = np.asarray(lsct[:,4])-273.15
ts_crop_inv = np.asarray(lsct[:,6])-273.15
tc_crop_inv  = np.asarray(lsct[:,7])-273.15


ind = (cloud_forest_inv==0)*(np.isnan(ts_forest_mea)==0)*(np.isnan(tc_forest_mea)==0)*\
        (tc_forest_inv<tempe_max)*(tc_forest_inv>tempe_min)* \
        (ts_forest_inv<tempe_max)*(ts_forest_inv>tempe_min)*(ts_forest_mea>5)

dif_threshold = 10
bias_tss,rmse_tss,r2_tss = cal_rmse_r2(ts_forest_mea[ind],ts_forest_inv[ind],dif_threshold)
bias_tc,rmse_tc,r2_tc = cal_rmse_r2(tc_forest_mea[ind],tc_forest_inv[ind],dif_threshold)
print("Forest")
print("bias:",bias_tss,bias_tc)
print("r2:",r2_tss[0],r2_tc[0])
print("rmse:",rmse_tss,rmse_tc)

plt.figure(figsize=[4.5,4])
plt.plot(ts_forest_mea[ind]+273.15,ts_forest_inv[ind]+273.15,'ro')
# plt.plot(tsh_forest_mea[ind],tsh_forest_inv[ind],'bo')
plt.plot(tc_forest_mea[ind]+273.15,tc_forest_inv[ind]+273.15,'go')
plt.xlim([15+273.15,50+273.15])
plt.ylim([15+273.15,50+273.15])
plt.plot([250,350],[250,350],'k--')
plt.xlabel('Measured Temperature/K')
plt.ylabel('Inverted Temperature/K')
plt.legend(['Soil','Canopy'])
plt.title('Forest')
plt.show()

# plt.plot(doy_[ind],ts_forest_mea[ind])
# plt.plot(doy_[ind],tc_forest_mea[ind])
# plt.plot(doy_[ind],ts_forest_inv[ind],'bo')
# plt.plot(doy_[ind],tc_forest_inv[ind],'ro')
# plt.show()


ind = (cloud_crop_inv==0)*(np.isnan(ts_crop_mea)==0)*(np.isnan(tc_crop_mea)==0)*\
        (tc_crop_inv<tempe_max)*(tc_crop_inv>tempe_min)*\
        (ts_crop_mea<tempe_max)*(ts_crop_mea>tempe_min)*\
        (tc_crop_mea<tempe_max)*(tc_crop_mea>tempe_min)*\
        (ts_crop_inv<tempe_max)*(ts_crop_inv>tempe_min)

dif_threshold = 10
ts1 = ts_crop_mea[ind]
ts2 = ts_crop_inv[ind]
bias_tss,rmse_tss,r2_tss = cal_rmse_r2(ts_crop_mea[ind],ts_crop_inv[ind],dif_threshold)
# bias_tsh,rmse_tsh,r2_tsh = cal_rmse_r2(tsh_crop_mea[ind],tsh_crop_inv[ind],dif_threshold)
bias_tc,rmse_tc,r2_tc = cal_rmse_r2(tc_crop_mea[ind],tc_crop_inv[ind],dif_threshold)
print("Crop")
print("bias:",bias_tss,bias_tc)
print("r2:",r2_tss[0],r2_tc[0])
print("rmse:",rmse_tss,rmse_tc)

plt.figure(figsize=[4.5,4])
plt.plot(ts_crop_mea[ind]+273.15,ts_crop_inv[ind]+273.15,'ro')
plt.plot(tc_crop_mea[ind]+273.15,tc_crop_inv[ind]+273.15,'go')
plt.xlim([15+273.15,50+273.15])
plt.ylim([15+273.15,50+273.15])
plt.plot([250,350],[250,350],'k--')
plt.xlabel('Measured Temperature/K')
plt.ylabel('Inverted Temperature/K')
plt.legend(['Soil','Canopy'])
plt.title('Crop')
plt.show()

plt.plot(doy_[ind],ts_crop_mea[ind]+273.15)
plt.plot(doy_[ind],tc_crop_mea[ind]+273.15)
plt.plot(doy_[ind],ts_forest_mea[ind]+273.15)
plt.plot(doy_[ind],tc_forest_mea[ind]+273.15)
plt.legend(['Forest_Soil','Forest_Canopy','Crop_Soil','Crop_Canopy'])
plt.xlabel('DOY')
plt.ylabel('Measured Temperature/K')
# plt.title('Measurement')

plt.show()

