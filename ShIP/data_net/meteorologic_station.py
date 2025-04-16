import numpy as np
from util.util import *
import time
from datetime import datetime
import csv



'''
将气象站数据输出成为X,Y
'''
wl = 10.5
start =time.clock()
dataDir = r'D:\Data\lstSimulate\2012\\'
infile1 = dataDir+'AWS_01.csv'
infile2 = dataDir+'LAI_01.dat'
dataDir = r'D:\Data\lstSimulate\\'
outfile1 = dataDir+'inputX_2012_01.csv'
outfile2 = dataDir+'inputY_2012_01.csv'


wl = 10.5
aws = pd.read_csv(infile1, parse_dates=['Time'])

low = datetime(2012, 6, 15, 0)
high = datetime(2012, 9, 6, 0)
aws = aws[aws['Time'] >= low]
aws = aws[aws['Time'] <= high]

Time_aws = aws['Time']
doy = Time_aws.apply(lambda x:x.dayofyear)
hour = Time_aws.apply(lambda x:x.hour)
minute = Time_aws.apply(lambda x:x.minute)
t_aws = np.asarray(doy+ hour/24.0 + minute/60.0/24.0,dtype=np.float)

Ms_aws = np.asarray(aws['Ms_2cm'].values,dtype=np.float)
Ta_aws = np.asarray(aws['Ta_5m'].values,dtype=np.float)
Ws_aws = np.asarray(aws['WS_10m'].values,dtype=np.float)
Rh_aws = np.asarray(aws['RH_5m'].values,dtype=np.float)
Dl_aws = np.asarray(aws['DLR_Cor'].values,dtype=np.float)
Ds_aws = np.asarray(aws['DR'].values,dtype=np.float)
Ul_aws = np.asarray(aws['ULR_Cor'].values,dtype=np.float)
Us_aws = np.asarray(aws['UR'].values,dtype=np.float)
Ir1_aws = np.asarray(aws['IRT_1'].values,dtype=np.float)
Ir2_aws = np.asarray(aws['IRT_2'].values,dtype=np.float)
# Pa_aws = np.asarray(aws['Press'].values,dtype=np.float)
Ir_aws = (Ir1_aws+Ir2_aws)/2.0
Pa_aws = np.asarray(aws['Press'].values,dtype=np.float)
Ms_aws = Ms_aws/100.0
Dl_aws[Dl_aws < 0] = 0
Ds_aws[Ds_aws < 0] = 0
Pa_aws[:] = 880
Ms_aws[Ms_aws<0] =0.25
Ea_aws = vp(Ta_aws,Rh_aws)

# doy = Time_aws.apply(lambda x:x.dayofyear)
# hour = Time_aws.apply(lambda x:x.hour)
# minute = Time_aws.apply(lambda x:x.minute)
# year_aws = Time_aws.apply(lambda x:x.year)
# size_data = np.size(t_aws)
# timeSeries = np.arange(size_data)
# ind = np.asarray(( timeSeries % 3 ) == 0,dtype=np.bool)  ### ( timeSeries % 3 ) == 0  ;;; ( timeSeries % 3 ) >= 0

'''
输出数据结构
'''

size_data = np.size(t_aws)
mark=np.zeros(size_data)
ind = (hour > 6) * (hour < 18)
mark[:] = 2
mark[ind] = 1

timeSeries = np.arange(size_data)
ind = np.asarray(( timeSeries % 3 ) == 0,dtype=np.bool)  ### ( timeSeries % 3 ) == 0  ;;; ( timeSeries % 3 ) >= 0
input1 = np.stack([Ms_aws[ind],Ta_aws[ind],Ws_aws[ind],Rh_aws[ind],
                   Ds_aws[ind],Dl_aws[ind],Us_aws[ind],Ul_aws[ind],mark[ind]],axis=1)
# output1 = np.stack([Ir_aws,Ts_mea,Tv_mea],axis = 1)
output1 = np.transpose(np.stack([Ir_aws[ind]]))

# np.savetxt(outfile,result,fmt='%f')

'''
写成CSV
'''
out = open(outfile1,'w', newline='')
csv_write = csv.writer(out)
csv_write.writerows(input1)

out = open(outfile2,'w', newline='')
csv_write = csv.writer(out)
csv_write.writerows(output1)


end = time.clock()
print('Running time: %s Seconds'%(end-start))

'''
写成TXT
'''
# np.savetxt(outdir+'ea_.dat',Ea_aws[ind],fmt='%.3f')
# np.savetxt(outdir+'p_.dat',Pa_aws[ind],fmt='%.3f')
# np.savetxt(outdir+'Ta_.dat',Ta_aws[ind],fmt='%.3f')
# np.savetxt(outdir+'u_.dat',Ws_aws[ind],fmt='%.3f')
# np.savetxt(outdir+'Rin_.dat',Ds_aws[ind],fmt='%.3f')
# np.savetxt(outdir+'Rli_.dat',Dl_aws[ind],fmt='%.3f')
# np.savetxt(outdir+'t_.dat',t_aws[ind],fmt= '%.3f')
# np.savetxt(outdir+'year_.dat',year_aws[ind],fmt= '%d')
# np.savetxt(outdir+'Irt_.dat',Ir_aws[ind],fmt = "%.3f")
# np.savetxt(outdir+'SMC_.dat',Ms_aws[ind],fmt = "%.3f")
# np.savetxt(outdir+'uRin_.dat',Us_aws[ind],fmt='%.3f')
# np.savetxt(outdir+'uRli_.dat',Ul_aws[ind],fmt='%.3f')