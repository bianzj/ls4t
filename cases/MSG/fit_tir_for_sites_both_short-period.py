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

site = "Angola"

# LaCrau,43.558889,4.8642
# Chaal,34.62444,10.292778
# Gobplane,-23.5194,15.0833
# GobWind,-23.5508,15.0514
# Evora,38.5411,-8.0033
# Faidherbia,-16.45357, 14.49581
# Victoria,32.86667,-0.86667
# Botswana,22.965,-21.798
# Angola,17.296, -7.754


for kdoy in range(259,260):


    infile1 = indir + site + "_msg_2024_%03d.txt" % kdoy
    infile2 = indir + site + "_iodc_2024_%03d.txt" % kdoy



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
    ir016 = np.hstack([ir0161,ir0162])
    bt108 = np.hstack((bt1081, bt1082))
    bt120 = np.hstack((bt1201, bt1202))
    pst = np.hstack((pst1, pst2))

    obs = vis06
    obs1 = vis061
    obs2 = vis062

    # obs = vis08
    # obs1 = vis081
    # obs2 = vis082

    # obs = ir016
    # obs1 = ir0161
    # obs2 = ir0162

    obs = (vis08-vis06)/(vis08+vis06)
    obs1 = (vis081-vis061)/(vis081+vis061)
    obs2 = (vis082-vis062)/(vis082+vis062)

    fhs = kernel_RLf(vza, sza, raa)
    fhs1 = kernel_RLf(vza1, sza1, raa1)
    fhs2 = kernel_RLf(vza2, sza2, raa2)
    fn = np.tan(sza * deg2rad)
    fn1 = np.tan(sza1 * deg2rad)
    fn2 = np.tan(sza2 * deg2rad)
    ksolar = kernel_Solar(vza, sza, raa)
    kli = kernel_LiSparse(vza, sza, raa)
    kross = kernel_RossThick(vza, sza, raa)
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
    if(sum(ind)>5):
        print("bad day!")
        continue

    pst_start = 10
    pst_end = 15

    ind = (pst > pst_start) & (pst < pst_end)
    ind1 = (pst1 > pst_start) & (pst1 < pst_end)
    ind2 = (pst2 > pst_start) & (pst2 < pst_end)



    #### using fmin
    results_r = fitting_R(obs[ind],fhs[ind])
    fitted_r = model_R(results_r,fhs)
    rmse_r = np.sqrt(np.average((obs[ind] - fitted_r[ind])**2))


    results_rossr = fitting_VolR(obs[ind],kross[ind],fhs[ind])
    fitted_rossr = model_VolR(results_rossr,kross,fhs)
    rmse_rossr = np.sqrt(np.average((obs[ind] - fitted_rossr[ind])**2))

    results_rossrl = fitting_VolRL(obs[ind],kross[ind],fhs[ind],fn[ind])
    fitted_rossrl = model_VolRL(results_rossr,kross,fhs,fn)
    rmse_rossrl = np.sqrt(np.average((obs[ind] - fitted_rossrl[ind])**2))

    results_vinr = fitting_VolR(obs[ind],kvin[ind],fhs[ind])
    fitted_vinr = model_VolR(results_rossr,kvin,fhs)
    rmse_vinr = np.sqrt(np.average((obs[ind] - fitted_vinr[ind])**2))

    y = obs[ind]
    iso = np.ones(np.shape(y)[0])
    A = np.vstack([kross[ind],iso])
    A = np.transpose(A)

    result_ross=np.asarray(lstsq(A, y)[0])
    fitted_ross = result_ross[0]*kross+result_ross[1]
    rmse_ross = np.sqrt(np.average((obs[ind] - fitted_ross[ind]) ** 2))

    results_rl = fitting_RL(obs[ind],fhs[ind],fn[ind])
    fitted_rl = model_RL(results_rl,fhs,fn)
    rmse_rl = np.sqrt(np.average((obs[ind] - fitted_rl[ind])**2))

    results_dtc = fitting_DTC(obs[ind], pst[ind], Tbase=0)
    fitted_dtc = model_DTC(results_dtc, pst)
    rmse_dtc = np.sqrt(np.average((obs[ind] - fitted_dtc[ind]) ** 2))

    x0 = np.asarray([0,0.05,12,1,0.05,0.5])
    results_dtcr = fitting_DTCR(obs[ind], pst[ind], fhs[ind],x0= x0)
    fitted_dtcr = model_DTCR(results_dtcr, pst, fhs)
    fitted_dtcr1 = model_DTCR(results_dtcr, pst1, fhs1)
    fitted_dtcr2 = model_DTCR(results_dtcr, pst2, fhs2)
    rmse_dtcr = np.sqrt(np.average((obs[ind] - fitted_dtcr[ind]) ** 2))


    results_dtcrl = fitting_DTCRL(obs[ind], pst[ind], fhs[ind],fn[ind],x0=x0)
    fitted_dtcrl = model_DTCRL(results_dtcrl, pst, fhs,fn)
    fitted_dtcrl1 = model_DTCRL(results_dtcrl, pst1, fhs1,fn1)
    fitted_dtcrl2 = model_DTCRL(results_dtcrl, pst2, fhs2,fn2)
    rmse_dtcrl = np.sqrt(np.average((obs[ind] - fitted_dtcrl[ind]) ** 2))

    # results_dtcrl = fitting_DTCRL(vis06[ind], pst[ind],fhs[ind],fn[ind], Tbase=0)
    # fitted_dtcrl = model_DTCRL(results_dtcrl, pst,fhs,fn)
    # rmse_dtcrl = np.sqrt(np.average((vis06[ind] - fitted_dtcrl[ind])**2))

    print(rmse_dtc,rmse_dtcr,rmse_dtcrl)
    print(results_dtcr,results_dtcrl)

    pst_start = 3
    pst_end = 19
    ind = (pst > pst_start) & (pst < pst_end)
    ind1 = (pst1 > pst_start) & (pst1 < pst_end)
    ind2 = (pst2 > pst_start) & (pst2 < pst_end)

    fig, ax1 = plt.subplots(figsize=(7, 5))
    # 第一个Y轴的数据（主要观测和拟合）
    ax1.plot(pst1[ind1], fitted_dtcr1[ind1], 'r-', linewidth=2, label='DTC-R')
    ax1.plot(pst1[ind1], fitted_dtcrl1[ind1], 'g-', linewidth=2, label='DTC-RL')
    ax1.plot(pst2[ind2], fitted_dtcr2[ind2], 'r-', linewidth=2)
    ax1.plot(pst2[ind2], fitted_dtcrl2[ind2], 'g-', linewidth=2)
    ax1.plot(pst1[ind1], obs1[ind1], 'kx', markersize=6, markeredgewidth=1.5, label='EURO')
    ax1.plot(pst2[ind2], obs2[ind2], marker="o", color="black",
             markerfacecolor="white", markeredgewidth=1.5, markersize=6,
             linestyle="none", label='IODC')

    # 设置第一个Y轴
    ax1.set_xlabel('Local Time (h)', fontsize=12)
    ax1.set_ylabel('DTC/DRC', fontsize=12, color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    plt.ylim(0,1)
    # 第二个Y轴的数据（CSCA）
    ax2 = ax1.twinx()
    ax2.plot(pst1[ind1], csca1[ind1], 'k--', linewidth=1.5, label='CSCA (EURO)')
    ax2.plot(pst2[ind2], csca2[ind2], 'k--', linewidth=1.5, label='CSCA (IODC)')

    # 设置第二个Y轴
    ax2.set_ylabel('CSCA', fontsize=12, color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               loc='best',  # 或者 'best'
               ncol=3,  # 三列布局
               frameon=True, fancybox=True, shadow=True,
               fontsize=10)

    plt.title(f"{site} --- DOY{kdoy:03d}", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

























