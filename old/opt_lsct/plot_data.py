import numpy as np
from scipy import interpolate
import matplotlib.mlab as ml
import matplotlib.pyplot as plt
import time
from util.util import *
from util_lsct import *
from multiprocessing import Pool
import warnings
import matplotlib.pyplot as plt

file_dir = r"D:\data\LSCT_heihe_2022\\lst.txt"
data = read_txt_float(file_dir)
idex=np.lexsort([data[:,0]])
sorted_data = data[idex, :]
doy = sorted_data[:,0]
time = sorted_data[:,1]/100
lst_n = sorted_data[:,2]
lst_o = sorted_data[:,3]
lst_a = sorted_data[:,4]
sza = sorted_data[:,5]
saa = sorted_data[:,6]
vza_n = sorted_data[:,7]
vaa_n = sorted_data[:,8]
vza_o = sorted_data[:,9]
vaa_o = sorted_data[:,10]
vza_a = sorted_data[:,11]
vaa_a = sorted_data[:,12]
pgn = sorted_data[:,13]
pgo = sorted_data[:,14]
pga = sorted_data[:,15]
fvc_n = sorted_data[:,16]
fvc_o = sorted_data[:,17]
fvc_a = sorted_data[:,18]
bt_n = sorted_data[:,19]
bt_o = sorted_data[:,20]
bt_a = sorted_data[:,21]

plt.figure()
plt.subplot(3,1,1)
time = time // 100  + time % 100/60 +8
plt.plot(doy,time,color = 'black')
plt.legend(labels = ["time"],fontsize=10)
plt.ylim(0,24)
y_major_locator=MultipleLocator(4)
ax=plt.gca()
ax.yaxis.set_major_locator(y_major_locator)
plt.xlabel("doy")
plt.ylabel("time/h")

# plt.subplot(5,1,2)
ind = (vza_o!=0)
# plt.plot(doy,vza_n)
# # vza_o[vza_o==0]=vza_o[0]
# plt.plot(doy[ind],vza_o[ind])
# plt.plot(doy[ind],vza_a[ind])
# plt.plot(doy[ind],sza[ind])
# plt.legend(labels = ["vza_n","vza_o","vza_a","sza"],fontsize=6)
# plt.xlabel("doy")
# plt.ylabel("VZA")

plt.subplot(3,1,2)
plt.plot(doy[ind],fvc_n[ind],color = 'r')
plt.plot(doy[ind],fvc_o[ind],color = 'dodgerblue')
plt.plot(doy[ind],fvc_a[ind],color = 'limegreen')
plt.legend(labels = ["fvc_n","fvc_o","fvc_a"],fontsize=10)
y_major_locator=MultipleLocator(0.1)
ax=plt.gca()
ax.yaxis.set_major_locator(y_major_locator)
plt.ylim(0,1)
plt.xlabel("doy")
plt.ylabel("FVC")

plt.subplot(3,1,3)
ind = (lst_n>280)*(lst_o>280)*(lst_a>280)
diff_o = lst_n[ind]-lst_o[ind]
diff_a = lst_n[ind]-lst_a[ind]
# diff_o = bt_n[ind]-bt_o[ind]
# diff_a = bt_n[ind]-bt_a[ind]
diff_o[abs(diff_o)>30]=0
diff_a[abs(diff_a)>30]=0
# plt.plot(doy[ind],diff_o,'-o')
# plt.plot(doy[ind],diff_a,'-o')
plt.plot(doy[ind],lst_n[ind])
plt.plot(doy[ind],lst_o[ind])
plt.plot(doy[ind],lst_a[ind])
plt.ylim(270,330)
# plt.axhline(0,color = 'black')
# plt.legend(labels = ["lst_n-lst_o","lst_n-lst_a"],fontsize=6)
plt.legend(labels = ["SLSTR_nadir","SlSTR_oblique","AHI"],fontsize=10)
plt.xlabel("doy")
plt.ylabel("LST/K")


def cal_solar_distance(sza,saa,vza,vaa):
    rd = np.pi/180.0
    tanthetav = np.tan(vza*rd)
    tanthetas = np.tan(sza * rd)
    cosfai = np.cos((saa-vaa)*rd)
    f = np.sqrt(np.power(tanthetas,2)+np.power(tanthetav,2)-2*tanthetas*tanthetav*cosfai)
    return f

# plt.subplot(5,1,5)
f_n= cal_solar_distance(sza[ind],saa[ind],vza_n[ind],vaa_n[ind])
# f_o= cal_solar_distance(sza[ind],saa[ind],vza_o[ind],vaa_o[ind])
# f_a= cal_solar_distance(sza[ind],saa[ind],vza_a[ind],vaa_a[ind])
# plt.plot(doy[ind],f_n,color = 'r')
# plt.plot(doy[ind],f_o,color = 'dodgerblue')
# plt.plot(doy[ind],f_a,color = 'limegreen')
# plt.legend(labels = ["f_n","f_o","f_a"],fontsize=6)
# plt.xlabel("doy")
# plt.ylabel("Solar distance")

# plt.subplot(5,1,5)
# plt.plot(doy,pgn,color = 'r')
# plt.plot(doy,pgo,color = 'dodgerblue')
# plt.plot(doy,pga,color = 'limegreen')
# plt.legend(labels = ["pgn","pgo","pga"],fontsize=6)
# plt.xlabel("doy")
# plt.ylabel("Pg")



plt.show()

