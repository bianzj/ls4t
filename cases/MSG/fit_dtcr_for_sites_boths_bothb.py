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

#from old.opt_temporal.fitting_DTC import fitting_ROSSRL_VNIR

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
outdir = indir0 + "/pars/"
site = "Faidherbia"

# LaCrau,43.558889,4.8642
# Chaal,34.62444,10.292778
# Gobplane,-23.5194,15.0833
# GobWind,-23.5508,15.0514
# Evora,38.5411,-8.0033
# Faidherbia,-16.45357, 14.49581
# Victoria,32.86667,-0.86667
# Botswana,22.965,-21.798
# Angola,17.296, -7.754

site_ = np.asarray(["LaCrau","Chaal","Gobplane","GobWind","Evora","Faidherbia","Victoria","Botswana","Angola"])
for site in site_:
    result_ = np.asarray([])
    for kdoy in range(183,306):


        infile1 = indir + site + "_euro_2024_%03d.txt" % kdoy
        infile2 = indir + site + "_iodc_2024_%03d.txt" % kdoy


        if os.path.exists(infile1)==0 or os.path.exists(infile2)==0:
            continue

        tempdata1 = read_txt_array(infile1,0,17)
        tempdata2 = read_txt_array(infile2, 0, 17)


        pst1 = tempdata1[:,5]+tempdata1[:,6]/60
        bt1081 = tempdata1[:,15]
        bt1201 = tempdata1[:,16]
        vis061 = tempdata1[:,12]/1000.0
        vis081 = tempdata1[:,13]/1000.0
        ir0161 = tempdata1[:, 14] / 1000.0
        sza1 = tempdata1[:,8]
        saa1 = tempdata1[:,9]
        vza1 = tempdata1[:,10]
        vaa1 = tempdata1[:,11]
        vaa1[vaa1 < 0] = vaa1[vaa1<0] + 360
        raa1 = np.abs(vaa1 - saa1)
        sza1[sza1 > 89] = 89

        pst2 = tempdata2[:, 5] + tempdata2[:, 6] / 60
        bt1082 = tempdata2[:, 15]
        bt1202 = tempdata2[:, 16]
        vis062 = tempdata2[:, 12] / 1000.0
        vis082 = tempdata2[:, 13] / 1000.0
        ir0162 = tempdata2[:, 14] / 1000.0
        sza2 = tempdata2[:, 8]
        saa2 = tempdata2[:, 9]
        vza2 = tempdata2[:, 10]
        vaa2 = tempdata2[:, 11]
        vaa2[vaa2 < 0] = vaa2[vaa2 < 0] + 360
        raa2 = np.abs(vaa2 - saa2)
        sza2[sza2 > 89] = 89


        vza = np.hstack((vza1, vza2))
        sza = np.hstack((sza1, sza2))
        raa = np.hstack((raa1, raa2))
        vis06 = np.hstack((vis061, vis062))
        vis08 = np.hstack((vis081, vis082))
        ir016 = np.hstack([ir0161, ir0162])
        bt108 = np.hstack((bt1081, bt1082))
        bt120 = np.hstack((bt1201, bt1202))
        pst = np.hstack((pst1, pst2))



        fhs = kernel_RLf(vza,sza,raa)
        fhs1 = kernel_RLf(vza1,sza1,raa1)
        fhs2 = kernel_RLf(vza2,sza2,raa2)
        fn = np.tan(sza*deg2rad)
        fn1 = np.tan(sza1*deg2rad)
        fn2 = np.tan(sza2*deg2rad)
        ksolar = kernel_Solar(vza,sza,raa)
        kli = kernel_LiSparse(vza,sza,raa)
        kross = kernel_RossThick(vza,sza,raa)
        kvin = kernel_Vin(sza)

        csca = np.cos(sza * deg2rad) * np.cos(vza * deg2rad) + \
               np.sin(sza * deg2rad) * np.sin(vza * deg2rad) * \
               np.cos(raa * deg2rad)
        csca = np.int_(csca * 100000) / 100000


        csca1 = np.cos(sza1 * deg2rad) * np.cos(vza1 * deg2rad) + \
               np.sin(sza1 * deg2rad) * np.sin(vza1 * deg2rad) * \
               np.cos(raa1 * deg2rad)
        csca1 = np.int_(csca1 * 100000) / 100000

        csca2 = np.cos(sza2 * deg2rad) * np.cos(vza2 * deg2rad) + \
               np.sin(sza2 * deg2rad) * np.sin(vza2 * deg2rad) * \
               np.cos(raa2 * deg2rad)
        csca2 = np.int_(csca2 * 100000) / 100000

        ind = bt108 < 275
        if(sum(ind) > 5):
            continue

        ind = (pst > 3.0) & (pst < 19.0)
        ind1 = (pst1 > 3.0) & (pst1 < 19.0)
        ind2 = (pst2 > 3.0) & (pst2 < 19.0)

        # obs = bt108
        # x0 = np.asarray([273.15,15,14,6,5,0.5])
        # results_dtcr_bt108 = fitting_DTCR(obs[ind], pst[ind], fhs[ind],x0=x0)
        # fitted_dtcr = model_DTCR(results_dtcr_bt108, pst, fhs)
        # rmse_dtcr_bt108 = np.sqrt(np.average((obs[ind] - fitted_dtcr[ind]) ** 2))
        # obs = vis06
        # x0 = np.asarray([0,0.05,12,6,0.05,0.5])
        # results_dtcr_vis06 = fitting_DTCR(obs[ind], pst[ind], fhs[ind],x0=x0)
        # fitted_dtcr = model_DTCR(results_dtcr_vis06, pst, fhs)
        # rmse_dtcr_vis06 = np.sqrt(np.average((obs[ind] - fitted_dtcr[ind]) ** 2))
        # obs = vis08
        # results_dtcr_vis08= fitting_DTCR(obs[ind], pst[ind], fhs[ind],x0=x0)
        # fitted_dtcr = model_DTCR(results_dtcr_vis08, pst, fhs)
        # rmse_dtcr_vis08 = np.sqrt(np.average((obs[ind] - fitted_dtcr[ind]) ** 2))
        # obs = ir016
        # results_dtcr_ir016 = fitting_DTCR(obs[ind], pst[ind], fhs[ind],x0=x0)
        # fitted_dtcr = model_DTCR(results_dtcr_ir016, pst, fhs)
        # rmse_dtcr_ir016 = np.sqrt(np.average((obs[ind] - fitted_dtcr[ind]) ** 2))



        # - 'Nelder-Mead': ref:`(see here) < optimize.minimize - neldermead > `
        # - 'Powell': ref:`(see here) < optimize.minimize - powell > `
        # - 'CG': ref:`(see here) < optimize.minimize - cg > `
        # - 'BFGS': ref:`(see here) < optimize.minimize - bfgs > `
        # - 'Newton-CG': ref:`(see here) < optimize.minimize - newtoncg > `
        # - 'L-BFGS-B': ref:`(see here) < optimize.minimize - lbfgsb > `
        # - 'TNC': ref:`(see here) < optimize.minimize - tnc > `
        # - 'COBYLA': ref:`(see here) < optimize.minimize - cobyla > `
        # - 'SLSQP': ref:`(see here) < optimize.minimize - slsqp > `
        # - 'trust-constr': ref:`(see here) < optimize.minimize - trustconstr > `
        # - 'dogleg': ref:`(see here) < optimize.minimize - dogleg > `
        # - 'trust-ncg': ref:`(see here) < optimize.minimize - trustncg > `
        # - 'trust-exact': ref:`(see here) < optimize.minimize - trustexact > `
        # - 'trust-krylov': ref:`(see here) < optimize.minimize - trustkrylov > `

        method = "Nelder-Mead"
        obs = bt108
        x0 = np.asarray([273.15,15,14,6,5,1.5])
        bnds = np.asarray([[273.15 - 20, 273.15 + 50], [0, 30], [9, 16], [3, 9], [0, 10], [-10, 10]])
        results_dtcr_bt108 = fitting_kernel_DTCR_min(cost_kernel_DTCR,obs[ind], pst[ind], fhs[ind],x0,bnds,method)
        fitted_dtcr = model_DTCR(results_dtcr_bt108, pst, fhs)
        rmse_dtcr_bt108 = np.sqrt(np.average((obs[ind] - fitted_dtcr[ind]) ** 2))
        obs = vis06
        x0 = np.asarray([0,0.05,12,6,0.05,1.5])
        bnds = np.asarray([[-20, 50], [0, 30], [9, 16], [3, 9], [0, 10], [-10, 10]])
        results_dtcr_vis06 = fitting_kernel_DTCR_min(cost_kernel_DTCR,obs[ind], pst[ind], fhs[ind],x0,bnds,method)
        fitted_dtcr = model_DTCR(results_dtcr_vis06, pst, fhs)
        rmse_dtcr_vis06 = np.sqrt(np.average((obs[ind] - fitted_dtcr[ind]) ** 2))
        obs = vis08
        results_dtcr_vis08= fitting_kernel_DTCR_min(cost_kernel_DTCR,obs[ind], pst[ind], fhs[ind],x0,bnds,method)
        fitted_dtcr = model_DTCR(results_dtcr_vis08, pst, fhs)
        rmse_dtcr_vis08 = np.sqrt(np.average((obs[ind] - fitted_dtcr[ind]) ** 2))
        obs = ir016
        results_dtcr_ir016 = fitting_kernel_DTCR_min(cost_kernel_DTCR,obs[ind], pst[ind], fhs[ind],x0,bnds,method)
        fitted_dtcr = model_DTCR(results_dtcr_ir016, pst, fhs)
        rmse_dtcr_ir016 = np.sqrt(np.average((obs[ind] - fitted_dtcr[ind]) ** 2))



        if(rmse_dtcr_bt108 > 2.5):
            continue
        if(rmse_dtcr_vis06 > 0.5):
            continue
        if(rmse_dtcr_vis08 > 0.5):
            continue
        if(rmse_dtcr_ir016 > 0.5):
            continue

        result = np.hstack([kdoy,results_dtcr_vis06,results_dtcr_vis08,results_dtcr_ir016,results_dtcr_bt108])


        if np.size(result_)==0:
            result_ = result
        else:
            result_ = np.vstack([result_,result])

    outfile = outdir + "/"+site+"_dtcr_pars.txt"
    np.savetxt(outfile, result_, delimiter=" ",fmt="%10.5f")
















