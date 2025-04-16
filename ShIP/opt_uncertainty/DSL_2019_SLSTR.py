from util.myfun import *
import pandas as pd
import time
from datetime import datetime

'''
使用地表观测数据对模拟的结果进行验证
'''
wl = 11.2
start =time.clock()
dataDir = r'E:\field\\'
infile1 = dataDir+'2019_DSL.csv'


aws = pd.read_csv(infile1, parse_dates=['TIMESTAMP'])

low = datetime(2019, 1, 1, 0)
high = datetime(2019, 12, 31, 23)
aws = aws[aws['TIMESTAMP'] >= low]
aws = aws[aws['TIMESTAMP'] <= high]

Time_aws = aws['TIMESTAMP']
doy = Time_aws.apply(lambda x:x.dayofyear)
hour = Time_aws.apply(lambda x:x.hour)
minute = Time_aws.apply(lambda x:x.minute)
t_aws = np.asarray(doy+ hour/24.0 + minute/60.0/24.0,dtype=np.float)

# Ms_aws = np.asarray((aws['Ms_2cm'].values+aws['Ms_4cm'].values)*0.5,dtype=np.float)
# Ta_aws = np.asarray(aws['Ta_10m'].values,dtype=np.float)
# Ws_aws = np.asarray(aws['WS_10m'].values,dtype=np.float)
# Rh_aws = np.asarray(aws['RH_5m'].values,dtype=np.float)
Dl_aws = np.asarray(aws['DLR_Cor'].values,dtype=np.float)
Ds_aws = np.asarray(aws['DR'].values,dtype=np.float)
Ul_aws = np.asarray(aws['ULR_Cor'].values,dtype=np.float)
Us_aws = np.asarray(aws['UR'].values,dtype=np.float)
Ir1_aws = np.asarray(aws['IRT_1'].values,dtype=np.float)
Ir2_aws = np.asarray(aws['IRT_2'].values,dtype=np.float)
# Pa_aws = np.asarray(aws['Press'].values,dtype=np.float)
Ir_aws = (Ir1_aws+Ir2_aws)/2.0

# AR DSL YSL DM HZZ SD SDQ HHL HM
col = 3
ifirt = 1
emis = 0.985

symbol = 's3b'
# method = 'direct'
methods = ['origin','Ermida','step','step_vt_nir','direct','direct_vt_nir']

for method in methods:
    infile_lst = r'E:\ShIP_VNIR\\'+symbol+'_lst_day_nadir_'+method+'.txt'

    infile_lst = r'E:\ShIP_KDTC\\'+'lst_'+method+'.txt'

    # infile_lst = r'E:\ShIP_VNIR\s3b_lst_day_nadir_Ermida.txt'
    # infile_lst = r'E:\ShIP_VNIR\s3b_lst_day_nadir_step_vt_nir.txt'
    # infile_lst = r'E:\ShIP_VNIR\s3b_lst_day_nadir_step_vt_red.txt'

    print(infile_lst)
    mydata = read_txt_array(infile_lst,0,38)
    doy = mydata[:,0]
    hh = mydata[:,1]//10000
    mm = (mydata[:,1]%10000)//100
    inv = mydata[:,col]
    cloud = mydata[:,col+9]
    ind = doy < 365
    doy = doy[ind]
    hh = hh[ind]
    mm = mm[ind]
    inv = inv[ind]
    ind1 = np.asarray((doy-1) * 144 + (hh+8) * 6 + mm // 10,dtype=np.int32)
    ind2 = np.asarray((doy-1) * 144 + (hh+8) * 6 + mm // 10+1,dtype=np.int32)
    rate = (mm % 10)/ 10.0
    if ifirt ==1:
        mea = (1-rate)*(Ir_aws[ind1] + 273.15) + rate *(Ir_aws[ind2] + 273.15)
        rad = planck(wl,mea)
        # rad = rad -(1-emis) * Dl_aws[ind2]
        rad = rad/emis
        mea = inv_planck(wl,rad)
    else:
        netrad = Ul_aws - (1-emis) * Dl_aws
        netrad = netrad /(5.67* 1e-8 * emis)
        netrad = (1-rate) * netrad[ind1] + rate * netrad[ind2]
        mea = np.power(netrad,0.25)

    ind = (mea > 100) *(inv > 100) *(np.abs(mea-inv)<7.5) *((hh + 8) % 24 > 6)*((hh+8)%24 < 18)*(cloud < 0.1)
    data1 = mea[ind]
    data2 = inv[ind]
    num = np.sum(ind)
    dif = data2 - data1
    bias = np.mean(dif)
    rmse = np.sqrt(np.mean(dif * dif))
    rr = np.corrcoef(data1, data2)
    r2 = rr[1, 0] * rr[1, 0]
    print(num,rmse,bias,r2)

    # AR DSL YSL DM HZZ SD SDQ HHL HM
    # col = 2
    infile_lst = r'E:\ShIP_VNIR\\'+symbol+'_lst_day_obliq_'+method+'.txt'
    # infile_lst = r'E:\ShIP_VNIR\s3b_lst_day_obliq_Ermida.txt'
    # infile_lst = r'E:\ShIP_VNIR\s3b_lst_day_obliq_step_vt_nir.txt'
    # infile_lst = r'E:\ShIP_VNIR\s3b_lst_day_obliq_step_vt_red.txt'

    mydata = read_txt_array(infile_lst, 0, 38)
    doy = mydata[:, 0]
    hh = mydata[:, 1] // 10000
    mm = (mydata[:, 1] % 10000) // 100
    inv = mydata[:, col]
    ind = doy < 365
    doy = doy[ind]
    hh = hh[ind]
    mm = mm[ind]
    inv = inv[ind]
    ind1 = np.asarray((doy - 1) * 144 + (hh + 8) * 6 + mm // 10, dtype=np.int32)
    ind2 = np.asarray((doy - 1) * 144 + (hh + 8) * 6 + mm // 10 + 1, dtype=np.int32)
    rate = (mm % 10) / 10.0
    if ifirt == 1:
        mea = (1 - rate) * (Ir_aws[ind1] + 273.15) + rate * (Ir_aws[ind2] + 273.15)
        rad = planck(wl, mea)
        rad = rad / emis
        mea = inv_planck(wl, rad)
    else:
        netrad = Ul_aws - (1 - emis) * Dl_aws
        netrad = netrad / (5.67 * 1e-8)
        mea = np.power(netrad, 0.25)
        mea = (1 - rate) * mea[ind1] + rate * mea[ind2]
    ind = (mea > 100) * (inv > 100) * (np.abs(mea - inv) < 7.5) * ((hh + 8) % 24 > 6) * ((hh + 8) % 24 < 18)
    data1 = mea[ind]
    data2 = inv[ind]
    num = np.sum(ind)
    dif = data2 - data1
    bias = np.mean(dif)
    rmse = np.sqrt(np.mean(dif * dif))
    rr = np.corrcoef(data1, data2)
    r2 = rr[1, 0] * rr[1, 0]
    print(num, rmse, bias, r2)