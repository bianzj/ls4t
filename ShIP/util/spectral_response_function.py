

import numpy as np
from util.myfun import *
from scipy import interpolate


'''
Tau2 光谱响应函数处理，
1）从ENVI得到光谱响应函数点信息；
2）从点信息得到光谱响应函数；
'''

infile = r'D:\BaiduNetdiskWorkspace\document\设备杂\tau_spectral_response_function.txt'
mydata = read_txt_float(infile)

xscale = (15-6.5)/1062
yscale = (1.0-0)/527
band_ = []
response_ = []
for k in range(1062):
    ind = (mydata[:,1] == k)
    if np.sum(ind)==0:continue
    temp = mydata[ind,2]
    indd = (temp > 3) *(temp < 527)
    ydata = np.mean(temp[indd])
    if np.sum(indd)==0:continue
    band_.append(k*xscale+6.5)
    response_.append(1-ydata * yscale)

result = np.stack([band_,response_])
outfile = r'D:\BaiduNetdiskWorkspace\document\设备杂\tau_spectral_response_function_finished.txt'
np.savetxt(outfile,result,fmt='%5.4f')

