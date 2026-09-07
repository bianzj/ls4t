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

from old.opt_temporal.fitting_DTC import fitting_ROSSRL_VNIR

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
    vis06 = tempdata[:,12]/1000.0
    vis08 = tempdata[:,13]/1000.0
    sza = tempdata[:,8]
    saa = tempdata[:,9]
    vza = tempdata[:,10]
    vaa = tempdata[:,11]
    vaa[vaa < 0] = vaa[vaa<0] + 360
    raa = np.abs(vaa - saa)
    sza[sza > 89] = 89

    fhs = kernel_RLf(vza,sza,raa)
    fn = np.tan(sza*deg2rad)
    ksolar = kernel_Solar(vza,sza,raa)
    kli = kernel_LiSparse(vza,sza,raa)
    kross = kernel_RossThick(vza,sza,raa)
    kvin = kernel_Vin(sza)

    csca = np.cos(sza * deg2rad) * np.cos(vza * deg2rad) + \
           np.sin(sza * deg2rad) * np.sin(vza * deg2rad) * \
           np.cos(raa * deg2rad)
    csca = np.int_(csca * 100000) / 100000

    ind = bt108 < 275
    if(sum(ind)>5):
        print("bad day!")
        continue

    ind = (pst > 7.0) & (pst < 19.0)

    #### using fmin
    results_r = fitting_R(vis06[ind],fhs[ind])
    fitted_r = model_R(results_r,fhs)
    rmse_r = np.sqrt(np.average((vis06[ind] - fitted_r[ind])**2))


    results_rossr = fitting_VolR(vis06[ind],kross[ind],fhs[ind])
    fitted_rossr = model_VolR(results_rossr,kross,fhs)
    rmse_rossr = np.sqrt(np.average((vis06[ind] - fitted_rossr[ind])**2))

    results_rossrl = fitting_VolRL(vis06[ind],kross[ind],fhs[ind],fn[ind])
    fitted_rossrl = model_VolRL(results_rossr,kross,fhs,fn)
    rmse_rossrl = np.sqrt(np.average((vis06[ind] - fitted_rossrl[ind])**2))

    results_vinr = fitting_VolR(vis06[ind],kvin[ind],fhs[ind])
    fitted_vinr = model_VolR(results_rossr,kvin,fhs)
    rmse_vinr = np.sqrt(np.average((vis06[ind] - fitted_vinr[ind])**2))

    y = vis06[ind]
    iso = np.ones(np.shape(y)[0])
    A = np.vstack([kross[ind],iso])
    A = np.transpose(A)

    result_ross=np.asarray(lstsq(A, y)[0])
    fitted_ross = result_ross[0]*kross+result_ross[1]
    rmse_ross = np.sqrt(np.average((vis06[ind] - fitted_ross[ind]) ** 2))

    results_rl = fitting_RL(vis06[ind],fhs[ind],fn[ind])
    fitted_rl = model_RL(results_rl,fhs,fn)
    rmse_rl = np.sqrt(np.average((vis06[ind] - fitted_rl[ind])**2))

    results_dtc = fitting_DTC(vis06[ind], pst[ind], Tbase=0)
    fitted_dtc = model_DTC(results_dtc, pst)
    rmse_dtc = np.sqrt(np.average((vis06[ind] - fitted_dtc[ind]) ** 2))

    results_dtcr = fitting_DTCR(vis06[ind], pst[ind], fhs[ind],x0=np.asarray([0,0.05,14,6,0.05,0.5]))
    fitted_dtcr = model_DTCR(results_dtcr, pst, fhs)
    rmse_dtcr = np.sqrt(np.average((vis06[ind] - fitted_dtcr[ind]) ** 2))


    results_dtcrl = fitting_DTCRL(vis06[ind], pst[ind], fhs[ind],fn[ind],x0=np.asarray([0,0.05,14,6,0.05,0.5]))
    fitted_dtcrl = model_DTCRL(results_dtcrl, pst, fhs,fn)
    rmse_dtcrl = np.sqrt(np.average((vis06[ind] - fitted_dtcrl[ind]) ** 2))

    # results_dtcrl = fitting_DTCRL(vis06[ind], pst[ind],fhs[ind],fn[ind], Tbase=0)
    # fitted_dtcrl = model_DTCRL(results_dtcrl, pst,fhs,fn)
    # rmse_dtcrl = np.sqrt(np.average((vis06[ind] - fitted_dtcrl[ind])**2))

    print(rmse_r,rmse_dtc)


    # plt.plot(pst[ind], fitted_r[ind], 'b-')
    # plt.plot(pst[ind], fitted_rl[ind], 'b-')
    plt.plot(pst[ind], fitted_dtcr[ind], 'r-')
    plt.plot(pst[ind], fitted_rossr[ind], 'k-')
    plt.plot(pst[ind], fitted_dtcrl[ind], 'g-')
    plt.plot(pst[ind], vis06[ind], 'kx')
    plt.show()
























