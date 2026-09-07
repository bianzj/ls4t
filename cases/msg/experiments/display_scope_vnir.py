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
klai = 0.5
ksm = 0.35
indir = indir0 + "F_2025_LAI%.1f"%klai+"_SMC%.2f"%ksm + "/Directional/"


infiles = search_file(indir,["BRDF"])

doy1 = 155
doy2 = 156
redwl = 655
nirwl = 865
result_ = np.asarray([])
for infile in infiles:
    ktime = np.float_(str(infile).split("_")[1].split(".")[0])+np.float_(str(infile).split("_")[1].split(".")[1])/100.0
    if (ktime > doy2) | (ktime < doy1): continue
    temp = read_txt_array(indir+infile,0,3)
    wl = temp[:,0]
    ind1 = where(wl == redwl)[0]
    ind2 = where(wl == nirwl)[0]
    red1 = temp[ind1,1][0]
    nir1 = temp[ind2,1][0]
    red2 = temp[ind1,2][0]
    nir2 = temp[ind2,2][0]
    result = np.asarray([ktime,red1,nir1,red2,nir2])
    if result_.size == 0:
        result_ = np.asarray([ktime,red1,nir1,red2,nir2])
    else:
        result_ = np.vstack([result_,result])



result_ = np.asarray(result_)
print(infiles)


ind = (result_[:,0] > doy1) & (result_[:,0] < doy2)

plt.plot(result_[ind,0],result_[ind,1],"ko")
plt.plot(result_[ind,0],result_[ind,3],"ro")
plt.legend(["euro","iodc"])
plt.show()

plt.plot(result_[ind,0],result_[ind,2],"ko")
plt.plot(result_[ind,0],result_[ind,4],"ro")
plt.legend(["euro","iodc"])
plt.show()



# y=result_[ind,1]-result_[ind,2]
# x=result_[ind,0]
# plt.plot(x,y,"ko")
# plt.legend(["euro-iodc"])
# plt.show()