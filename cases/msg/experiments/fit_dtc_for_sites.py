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


deg2rad = 3.1415926/180
NS_PER_HR = 1.e9 * 3600.  # nanoseconds per hour
elev = 0
altitude = 0
pressure = 101325 / 100  # pressure must be in millibars for calculation
atmos_refract = 0.5667
line1 = 3712  # 1rst line (start reading from south)
lineN = 0  # last line (northwards)

indir0 = r"/Users/bianzj/Downloads/data/msg/"
indir = indir0 + "/sitedata/"

infiles = search_file(indir,["txt","GobWind"])

n_file = len(infiles)
for kfile in range(n_file):

    infile = indir + infiles[kfile]


    print(infiles[kfile])


    tempdata = read_txt_array(infile,0,16)
    pst = tempdata[:,5]+tempdata[:,6]/60

    bt108 = tempdata[:,14]
    bt120 = tempdata[:,15]
    vis06 = tempdata[:,12]
    vis08 = tempdata[:,13]
    sza = tempdata[:,8]
    saa = tempdata[:,9]
    vza = tempdata[:,10]
    vaa = tempdata[:,11]
    vaa[vaa < 0] = vaa[vaa<0] + 360
    raa = np.abs(vaa - saa)

    RLf = kernel_RLf(vza,sza,saa)
    ksolar = kernel_Solar(vza,sza,raa)
    kli = kernel_LiSparse(vza,sza,raa)

    ind = bt108 < 275
    if(sum(ind)>5):
        print("bad day!")
        continue

    ind = (pst > 6.0) & (pst < 20.0)
    results = fitting_DTC(bt108[ind], pst[ind], Tbase=273.15)
    fitted = model_DTC(results, pst)
    rmse = np.sqrt(np.average((bt108[ind] - fitted[ind])**2))

    if (rmse > 5):
        print("bad day!")
        continue

    plt.plot(pst[ind], fitted[ind], 'b-')
    plt.plot(pst[ind], bt108[ind], 'kx')
    plt.show()


    plt.plot(pst[ind], bt108[ind]-fitted[ind], 'b-')
    plt.show()
    plt.plot(pst[ind], vza[ind], 'b-')
    plt.plot(pst[ind], sza[ind], 'b-')
    plt.plot(pst[ind], raa[ind], 'k-')
    plt.show()






















