import matplotlib.pyplot as plt
import numpy as np

from util.util import *
import warnings
from datetime import datetime
warnings.filterwarnings("ignore")

'''脚本用于画实测的组分温度图'''

'''remove the emissivity effect'''
def remove_emissivity(Tobj,emis=0.95,Tsky=240,wl = 10.8):
    Robj = planck(wl,Tobj+273.15)
    Rsky = planck(wl,Tsky)
    Robjn = (Robj-Rsky*(1-emis))/emis
    Tobjn = inv_planck(wl,Robjn)
    return Tobjn-273.15


indir_forest_tc = r'D:\data\LSCT_heihe_2022\validation\heihe2022\林地#2_冠层\\240305006010100'
indir_forest_ts = r'D:\data\LSCT_heihe_2022\validation\heihe2022\林地#2_陇间\\240305006010083'
indir_crop_tc = r'D:\data\LSCT_heihe_2022\validation\heihe2022\玉米#6_冠层\\240305006010099'
indir_crop_ts = r'D:\data\LSCT_heihe_2022\validation\heihe2022\玉米#6_裸土\\240305006010120'

ts_forest_mea = []
tc_forest_mea = []
ts_crop_mea = []
tc_crop_mea = []
time_ = []

emis_soil = 0.950
emis_leaf = 0.985

year = 2022
# 162-212
# 187-192
start_doy = 187
end_doy = 192
doy_range = range(start_doy,end_doy)

for doy in doy_range:
    month,day = doy2date(year,doy)
    print("day/month:"+str(day)+r"/"+str(month) + " doy:"+str(doy))
    infile_forest_ts = indir_forest_ts + '_%4d-' % year + '%02d-' % month + '%02d.csv' % day
    infile_forest_tc = indir_forest_tc + '_%4d-' % year + '%02d-' % month + '%02d.csv' % day
    infile_crop_ts = indir_crop_ts + '_%4d-' % year + '%02d-' % month + '%02d.csv' % day
    infile_crop_tc = indir_crop_tc + '_%4d-' % year + '%02d-' % month + '%02d.csv' % day

    if(os.path.exists(infile_forest_ts)==0):
        continue
    # if doy!=201:continue
    ts_forest_aws = pd.read_csv(infile_forest_ts, encoding="gbk", parse_dates=['数据时间'])
    tc_forest_aws = pd.read_csv(infile_forest_tc, encoding="gbk", parse_dates=['数据时间'])
    ts_crop_aws = pd.read_csv(infile_crop_ts, encoding="gbk", parse_dates=['数据时间'])
    tc_crop_aws = pd.read_csv(infile_crop_tc, encoding="gbk", parse_dates=['数据时间'])

    ts_forest = ts_forest_aws._get_column_array(2)
    tc_forest = tc_forest_aws._get_column_array(2)
    ts_crop = ts_crop_aws._get_column_array(2)
    tc_crop = tc_crop_aws._get_column_array(2)
    # time = tc_crop_aws._get_column_array(1)

    c1 = len(ts_forest) == 1440
    c2 = len(tc_forest) == 1440
    c3 = len(ts_crop) == 1440
    c4 = len(tc_crop) == 1440
    if not c1: print(doy,1)
    if not c2: print(doy, 2)
    if not c3: print(doy, 3)
    if not c4: print(doy, 4)


    ts_forest_mea = np.hstack((ts_forest_mea,ts_forest))
    tc_forest_mea = np.hstack((tc_forest_mea, tc_forest))
    ts_crop_mea = np.hstack((ts_crop_mea, ts_crop))
    tc_crop_mea = np.hstack((tc_crop_mea, tc_crop))
    # time_.append(time)

ts_forest_mea = remove_emissivity(ts_forest_mea,emis_soil)+273.15
tc_forest_mea = remove_emissivity(tc_forest_mea,emis_leaf)+273.15
ts_crop_mea = remove_emissivity(ts_crop_mea,emis_soil)+273.15
tc_crop_mea = remove_emissivity(tc_crop_mea,emis_leaf)+273.15

num = range(len(ts_forest_mea))
plt.figure(figsize=(14, 7),dpi=300)
plt.plot(num,ts_forest_mea,'orange')
plt.plot(num,tc_forest_mea,'g')
plt.plot(num,ts_crop_mea,'r')
plt.plot(num,tc_crop_mea,'b')
x_label = ['00:00','06:00','12:00','18:00','00:00','06:00','12:00','18:00','00:00','06:00','12:00','18:00','00:00','06:00','12:00','18:00','00:00','06:00','12:00','18:00','00:00']
ticks= [0,360,720,1080,1440,1800,2160,2520,2880,3240,3600,3960,4320,4680,5040,5400,5760,6120,6480,6840,7200]
plt.xticks(ticks=ticks,labels=x_label,rotation=30,fontsize=12)
plt.yticks(fontsize=12)
plt.legend(['Forest_Soil','Forest_Canopy','Crop_Soil','Crop_Canopy'],loc = 'upper center',ncol=4,fontsize=14)
plt.xlabel('time',fontsize=14)
plt.ylabel('Measured Temperature/K',fontsize=14)
plt.vlines([1440, 2880,4320,5760], 0, 500, linestyles='dashed', colors='black')
plt.ylim(281,320)
plt.xlim(0,len(ts_forest_mea))
plt.show()

# num = np.arange(start_doy,end_doy,(end_doy-start_doy)/len(ts_forest_mea))
# plt.figure(figsize=(20, 7),dpi=300)
# # plt.plot(num,ts_forest_mea,'orange')
# plt.plot(num,tc_forest_mea,'g')
# # plt.plot(num,ts_crop_mea,'r')
# # plt.plot(num,tc_crop_mea,'b')
# # plt.legend(['Forest_Soil','Forest_Canopy','Crop_Soil','Crop_Canopy'],loc = 'upper center',ncol=4,fontsize=14)
# plt.xlabel('time',fontsize=14)
# plt.ylabel('Measured Temperature/K',fontsize=14)
# plt.xticks(np.arange(start_doy,end_doy,1),rotation=60)
# # plt.vlines([1440, 2880,4320,5760], 0, 500, linestyles='dashed', colors='black')
# plt.ylim(280,320)
# # plt.xlim(0,len(ts_forest_mea))
# plt.show()



