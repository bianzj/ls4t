import matplotlib.pyplot as plt
import numpy as np

from base.util_kernel import fitting_DTC
from base.util_lst import *
from base.util_data import *
from base.util_fitting import *
from base.util_kernel import *
from base.util_file import *
import h5py
import seaborn as sns
import seaborn_image as isns
from pvlib import atmosphere
#from pvlib.tools import datetime_to_djd, djd_to_datetime
import pvlib
from pvlib.location import Location

from osgeo import gdal
from osgeo import osr
import os
import pyresample as pr
from satpy import Scene




indir0 = r"/Users/bianzj/Downloads/data/msg/output/"
klai = 2.0
ksm = 0.35
indir = indir0 + "F_2025_LAI%.1f"%klai+"_SMC%.2f"%ksm+"/Directional/"

doy1 = 155
doy2 = 156
infiles = search_file(indir,["Temperature"])
infile_temp = indir0 + "F_2025_LAI%.1f"%klai+"_SMC%.2f"%ksm + "/surftemp.dat"
temps = read_txt_array(infile_temp,0,11)

result_ = np.asarray([])
for infile in infiles:
    ktime = np.float_(str(infile).split("_")[1].split(".")[0])+np.float_(str(infile).split("_")[1].split(".")[1])/100.0
    if (ktime > doy2) | (ktime < doy1): continue
    dt1 = read_txt_array(indir+infile,0,2)[0][0]
    dt2 = read_txt_array(indir+infile,0,2)[0][1]
    result = np.asarray([ktime,dt1,dt2])
    if result_.size == 0:
        result_ = np.asarray([ktime,dt1,dt2])
    else:
        result_ = np.vstack([result_,result])



result_ = np.asarray(result_)
print(infiles)

doy1 = 155
doy2 = 156
ind = (result_[:,0] > doy1) & (result_[:,0] < doy2)



plt.plot(result_[ind,0],result_[ind,1],"ko")
plt.plot(result_[ind,0],result_[ind,2],"ro")
plt.legend(["euro","iodc"])
plt.show()

indd = (temps[:,2] > doy1) & (temps[:,2] < doy2)
plt.plot(temps[indd,2],temps[indd,3],"yo")
plt.plot(temps[indd,2],temps[indd,4],"yo")
plt.plot(temps[indd,2],temps[indd,5],"yo")
plt.plot(temps[indd,2],temps[indd,6],"yo")
plt.plot(temps[indd,2],temps[indd,7],"yo")
plt.show()

# y=result_[ind,1]-result_[ind,2]
# x=result_[ind,0]
# plt.plot(x,y,"ko")
# plt.legend(["euro-iodc"])
# plt.show()