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

infiles = search_file(indir,["txt","Gobplane"])

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
    sza[sza > 85] = 85

    fhs = kernel_RLf(vza,sza,raa)
    fn = np.tan(sza*deg2rad)
    ksolar = kernel_Solar(vza,sza,raa)
    kli = kernel_LiSparse(vza,sza,raa)

    csca = np.cos(sza * deg2rad) * np.cos(vza * deg2rad) + \
           np.sin(sza * deg2rad) * np.sin(vza * deg2rad) * \
           np.cos(raa * deg2rad)
    csca = np.int_(csca * 100000) / 100000

    ind = bt108 < 275
    if(sum(ind)>5):
        print("bad day!")
        continue

    ind = (pst > 6.0) & (pst < 20.0)

    #### using fmin
    results_dtcrl = fitting_DTCRL(bt108[ind], pst[ind],fhs[ind],fn[ind], [6+273.15,16,14,6,1,0.5])
    fitted_dtcrl = model_DTCRL(results_dtcrl, pst,fhs,fn)
    rmse_dtcrl = np.sqrt(np.average((bt108[ind] - fitted_dtcrl[ind])**2))

    results_dtc = fitting_DTC(bt108[ind], pst[ind], Tbase=273.15)
    fitted_dtc = model_DTC(results_dtc, pst)
    rmse_dtc = np.sqrt(np.average((bt108[ind] - fitted_dtc[ind]) ** 2))

    results_dtcr = fitting_DTCR(bt108[ind], pst[ind],fhs[ind], [6+273.15,16,14,6,1,0.5])
    fitted_dtcr = model_DTCR(results_dtcr, pst,fhs)
    rmse_dtcr = np.sqrt(np.average((bt108[ind] - fitted_dtcr[ind])**2))


    print(rmse_dtcrl,rmse_dtc)




    #### using minimize func
    # Tbase = 273.15
    # x0 = np.asarray([Tbase + 10,16,14,6,1,0.5])
    # bnds = np.asarray([[Tbase-20,Tbase+50],[0,30],[10,16],[3,9],[0,10],[0,10]])
    # ####默认为powell，还有slsqp，L - BFGS - B，TNC，
    # results_dtcrl = fitting_kernel_DTCRL_min(cost_kernel_DTCRL,bt108[ind], pst[ind], fhs[ind], fn[ind],x0,bnds,"slsqp")
    # fitted_dtcrl = model_DTCRL(results_dtcrl, pst, fhs, fn)
    # rmse_dtcrl = np.sqrt(np.average((bt108[ind] - fitted_dtcrl[ind]) ** 2))
    # x0 = np.asarray([Tbase + 10,16,14,6])
    # bnds = np.asarray([[Tbase-20,Tbase+50],[0,30],[10,16],[3,9]])
    # results_dtc = fitting_kernel_DTC_min(cost_kernel_DTC,bt108[ind], pst[ind],x0,bnds,"slsqp")
    # fitted_dtc = model_DTC(results_dtc, pst)
    # rmse_dtc = np.sqrt(np.average((bt108[ind] - fitted_dtc[ind]) ** 2))
    # print(rmse_dtcrl, rmse_dtc)

    plt.plot(pst[ind], fitted_dtc[ind], 'b-')
    plt.plot(pst[ind], fitted_dtcrl[ind], 'r-')
    plt.plot(pst[ind], fitted_dtcr[ind], 'g-')
    plt.plot(pst[ind], bt108[ind], 'kx')
    plt.show()


    # plt.plot(pst[ind], bt108[ind]-fitted[ind], 'b-')
    # plt.show()
    # plt.plot(pst[ind], fhs[ind], 'b-')
    # plt.plot(pst[ind], csca[ind], 'b-')
    # plt.show()






















