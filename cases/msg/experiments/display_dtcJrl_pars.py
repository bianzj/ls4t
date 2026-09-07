import matplotlib.pyplot as plt
import numpy as np

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


indir0 = r"/Users/bianzj/Downloads/data/msg/"
indir_site = indir0 + "/sitedata/"
site_ = np.asarray(["LaCrau","Chaal","Gobplane","GobWind","Evora","Faidherbia","Victoria","Botswana","Angola"])


data1_ = np.asarray([])
data2_ = np.asarray([])
for site in site_:

    infile = indir0 + "/pars/" + site+"_dtcrl_pars.txt"
    data1 = np.loadtxt(infile)
    infile = indir0 + "/pars/" + site+"_dtcrl_pars.txt"
    data2 = np.loadtxt(infile)

    if data1_.size == 0:
        data1_ = data1
        data2_ = data2
    else:
        data1_ = np.vstack((data1_,data1))
        data2_ = np.vstack((data2_,data2))

    doy2 = data2[:,0]
    doy1 = data1[:,0]
    k1 = data1[:,6]
    k2 = data1[:,12]
    k3 = data1[:,18]
    k4 = data2[:,24]

    plt.title(site)
    plt.plot(doy2,k4,"r.")
    plt.plot(doy1,k1,"b.")
    plt.legend(["k in TIR","k in Red"])
    plt.show()









