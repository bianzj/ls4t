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


indir0 = r"/Users/bianzj/Downloads/data/msg/"
indir_site = indir0 + "/sitedata/"
site_ = np.asarray(["LaCrau","Chaal","Gobplane","GobWind","Evora","Faidherbia","Victoria","Botswana","Angola"])
for site in site_:

    infile = indir0 + "/pars/" + site+"_dtcrl_pars.txt"
    data = np.loadtxt(infile)


    k1 = data[:,6]
    k2 = data[:,12]
    k3 = data[:,18]
    k4 = data[:,24]

    plt.title(site)
    plt.plot(k1,k4,"ro")
    plt.plot(k2,k4,"ko")
    plt.plot(k3,k4,"bo")
    plt.xlim([-5,10])
    plt.ylim([-5,10])
    plt.show()






