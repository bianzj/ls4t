from util.myfun import *
import pandas as pd
import time
from datetime import datetime
import seaborn as sns

'''
使用地表观测数据对模拟的结果进行验证
'''
wl = 11.2
start =time.clock()
dataDir = r'E:\field\\'
infile1 = dataDir+'2019_DM.csv'


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
col = 5
ifirt =0
emis = 0.975

symbol = 'AHI'
# method = 'direct'
methods = ['o','DTC','DVT']

method = methods[0]
infile_lst = r'E:\ShIP_DVT\\'+'lst_'+method+'.txt'
print(infile_lst)
mydata = read_txt_array(infile_lst,0,38)
doy = mydata[:,0]
hh = mydata[:,1]//10000
mm = (mydata[:,1]%10000)//100
inv3 = mydata[:,col]
cloud = mydata[:,col+9]
ind = doy < 365
doy = doy[ind]
hh = hh[ind]
mm = mm[ind]
inv3 = inv3[ind]
ind1 = np.asarray((doy-1) * 144 + (hh+8) * 6 + mm // 10,dtype=np.int32)
ind2 = np.asarray((doy-1) * 144 + (hh+8) * 6 + mm // 10+1,dtype=np.int32)
rate = (mm % 10)/ 10.0
if ifirt ==1:
    mea = (1-rate)*(Ir_aws[ind1] + 273.15) + rate *(Ir_aws[ind2] + 273.15)
    rad = planck(wl,mea)
    rad = rad -(1-emis) * planck(wl,250)
    rad = rad/emis
    mea = inv_planck(wl,rad)
else:
    netrad = Ul_aws - (1-emis) * Dl_aws
    netrad = netrad /(5.67* 1e-8 * emis)
    netrad = (1-rate) * netrad[ind1] + rate * netrad[ind2]
    mea = np.power(netrad,0.25)

method = methods[1]
infile_lst = r'E:\ShIP_DVT\\'+'lst_'+method+'.txt'
print(infile_lst)
mydata = read_txt_array(infile_lst,0,38)
doy = mydata[:,0]
inv1 = mydata[:,col]
ind = doy < 365
doy = doy[ind]
hh = hh[ind]
mm = mm[ind]
inv1 = inv1[ind]

method = methods[2]
infile_lst = r'E:\ShIP_DVT\\'+'lst_'+method+'.txt'
print(infile_lst)
mydata = read_txt_array(infile_lst,0,38)
doy = mydata[:,0]
inv2 = mydata[:,col]
ind = doy < 365
doy = doy[ind]
hh = hh[ind]
mm = mm[ind]
inv2 = inv2[ind]

dif_threshold = 7.5
ind = (mea > 100) *(inv1 > 100) *\
      (np.abs(mea-inv3)<dif_threshold) *((hh + 8) % 24 >= 9)*((hh+8)%24 <= 16) *(cloud==0)*\
      (inv2>100)*(inv3>100)*(np.abs(mea-inv2)<dif_threshold)*(np.abs(mea-inv1)<dif_threshold)

# data1 = mea[ind]
# data3 = inv3[ind]
# data1 = inv1[ind]
# data2 = inv2[ind]
num = np.sum(ind)

data2 = inv1[ind]
data1 = mea[ind]
dif = data2 - data1
bias = np.mean(dif)
rmse = np.sqrt(np.mean(dif * dif))
rr = np.corrcoef(data1, data2)
r2 = rr[1, 0] * rr[1, 0]
print("num=", num, "rmse=", rmse, "bias=", bias, "r2=", r2)




data2 = inv2[ind]
data1 = mea[ind]
dif = data2 - data1
bias = np.mean(dif)
rmse = np.sqrt(np.mean(dif * dif))
rr = np.corrcoef(data1, data2)
r2 = rr[1, 0] * rr[1, 0]
print("num=", num, "rmse=", rmse, "bias=", bias, "r2=", r2)

sns.set_theme(style="white")
fig = plt.figure(figsize=(5.0,4.3))
xmin, xmax, ymin, ymax = 280, 320, 280, 320
# plt.hist2d(data1, data2, bins=50, norm=LogNorm(), cmap='jet')
df = pd.DataFrame({'SCOPE LST (K)': data1, 'Fitted LST (K)': data2})
g = sns.histplot(x='SCOPE LST (K)', y='Fitted LST (K)',data=df, bins=10,cbar=True,cmap="Spectral_r")
# g = sns.jointplot(x='SCOPE LST (K)', y='Fitted LST (K)', data=df, kind='hex',dropna=False,palette='red')
plt.plot([xmin, xmax], [ymin, ymax], '--')

g.set(xlabel='Measured LST (K)',ylabel='Normalized LST (K)')
# plt.xlabel("SCOPE LST")
# plt.ylabel("Fitted LST")
plt.xlim([xmin, xmax])
plt.ylim([ymin, ymax])
plt.text(300, 298-8, 'RMSE = %2.2f' % rmse)
plt.text(300, 295-8, '$R^2$ = %2.2f' % r2)
plt.text(300, 292-8, 'Bias = %2.2f' % bias)
plt.show()


data2 = inv3[ind]
data1 = mea[ind]
dif = data2 - data1
bias = np.mean(dif)
rmse = np.sqrt(np.mean(dif * dif))
rr = np.corrcoef(data1, data2)
r2 = rr[1, 0] * rr[1, 0]
print("num=", num, "rmse=", rmse, "bias=", bias, "r2=", r2)



