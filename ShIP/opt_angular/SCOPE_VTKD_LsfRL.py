import numpy as np
from sklearn.linear_model import LinearRegression
from util.util import *

from matplotlib.colors import LogNorm
from util_kdfitting import *
# import seaborn as sns
import pandas as pd

'''
obtain the fitting results, 
but the statisitical result are not here
'''

indir0 = r'F:\ShIP_VTKD_data\\'
outfiletxt = indir0 + 'vtkd_lsfrl.txt'
# time_ = [215.13,215.17,215.21,215.25,215.29,215.33,215.38, 215.42,215.46,215.50,215.54,215.58,215.63,215.67,215.71,215.75]
time__1 = [0.42,0.46,0.50,0.54,0.58,0.63,0.67]
time__2 = [0.41,0.45,0.49,0.54,0.58,0.62,0.66]



bf_ = []
lst_ = []
ndvi_ = []
smc_ = []
vza_ = []
vaa_ = []
XX = np.arange(0.15,0.46,0.1)
YY = np.arange(0.5,3.6,1.0)
ZZ = [80,173,266,356]
# XX = np.asarray([0.25])
# YY = np.asarray([2.3])

ifhot =0

off1 = len(XX)
off2 = len(YY)


obs_all = []
newobsda_all = []
coef_all = []
obsda_all = []
kvol_all = []
khot_all = []
kiso_all = []
kcom_all = []
rmse_ = []
std_ = []
for kdoy in ZZ:
    doy = np.asarray(kdoy)
    time_ = time__1 + doy
    if doy > 200:
        time_ = time__2 + doy

    for ksmc in XX:
        for klai in YY:

            bf_ = np.asarray([])
            vi_ = np.asarray([])
            obs_ = np.asarray([])
            red_ = np.asarray([])
            nir_ = np.asarray([])
            raa_ = np.asarray([])
            vza_ = np.asarray([])
            sza_ = np.asarray([])
            pst_ = np.asarray([])
            kvol_ = np.asarray([])
            khot_ = np.asarray([])
            kiso_ = np.asarray([])
            obsda_ = np.asarray([])
            newobsda_ = np.asarray([])
            case = np.zeros(15)

            for time in time_:
                indir = indir0+'scope_%d_k1\\'%kdoy+'output\hl_2019_LAI%.1f'%klai +'_SMC%.2f'%ksmc
                infile1 = indir+'\Directional\\'+'Temperatures_%.2f'%time +'.dat'
                lst = read_txt_float(infile1)
                infile2 = indir+'\Directional\\'+'Angles_%.2f'%time +'.dat'
                angle = read_txt_float(infile2)
                infile3 = indir+'\Directional\\'+'BRDF_%.2f'%time +'.dat'
                brdf = read_txt_float(infile3)
                if ifhot == 1:
                    # red = brdf[260, 408:].reshape(-1)
                    # nir = brdf[460, 408:].reshape(-1)
                    # green = brdf[160, 408:].reshape(-1)
                    # lst = lst[0,407:414].reshape(-1)
                    # vza = angle[0, 407:414].reshape(-1)
                    # raa = angle[1, 407:414].reshape(-1)
                    # sza = angle[2, 407:414].reshape(-1)
                    # pst = lst*1.0
                    # pst[:] = (time - np.int_(time))*24

                    red = brdf[260, 1:].reshape(-1)
                    nir = brdf[460, 1:].reshape(-1)
                    green = brdf[160,1:].reshape(-1)
                    lst = lst[0, :414].reshape(-1)
                    vza = angle[0, :414].reshape(-1)
                    raa = angle[1, :414].reshape(-1)
                    sza = angle[2, :414].reshape(-1)
                    pst = lst*1.0
                    pst[:] = (time - np.int_(time))*24
                else:
                    red = brdf[260, 1:408].reshape(-1)
                    nir = brdf[460, 1:408].reshape(-1)
                    green = brdf[160, 1:408].reshape(-1)
                    lst = lst[0, :407].reshape(-1)
                    vza = angle[0, :407].reshape(-1)
                    raa = angle[1, :407].reshape(-1)
                    sza = angle[2, :407].reshape(-1)
                    pst = lst*1.0
                    pst[:] = (time - np.int_(time))*24

                ind = (raa == 0)| (raa == 180)
                red = red[ind]
                nir = nir[ind]
                green = green[ind]
                lst = lst[ind]
                vza = vza[ind]
                raa = raa[ind]
                sza = sza[ind]
                pst = pst[ind]

                # bf = (red+nir)/2.0
                # bfref = red[0]+nir[0]
                # bfref = 2.0
                bf = (red+nir)/green-3
                vi = (nir-red)/(nir+red)
                lstda = lst - lst[0]
                print(klai, ksmc, time,sza[0])
                obs_ = np.hstack([obs_,lst])
                obsda_ = np.hstack([obsda_,lstda])
                raa_ = np.hstack([raa_,raa])
                vza_ = np.hstack([vza_,vza])
                sza_ = np.hstack([sza_,sza])
                pst_ = np.hstack([pst_,pst])
                bf_ = np.hstack([bf_,bf])
                vi_ = np.hstack([vi_,vi])
                nir_ = np.hstack([nir_,nir])
                red_ = np.hstack([red_,red])

                thetas = np.deg2rad(sza)
                thetav = np.deg2rad(abs(vza))
                thetaa = np.deg2rad(raa)
                cthetv = np.cos(thetav)
                fhs = np.sqrt((np.power(np.tan(thetas), 2) + np.power(np.tan(thetav), 2) - 2 * np.tan(thetas) * np.tan(thetav) *np.cos(thetaa)))
                fn = np.tan(thetas)
                kLSF = 0.069 * cthetv * cthetv - 0.215 * cthetv + 1.176
                x0 = np.asarray([0.5, 0.5, 0.05, 1.5])
                bnds = ((-100, 100), (-100, 100), (-100, 100), (-10, 10))
                coef_obs = fitting_kernel_RL_min(fun_kernel_RL,lstda, kLSF,fhs,fn,x0,bnds)
                kRL = (np.exp(-coef_obs[3] * fhs) - np.exp(-coef_obs[3] * fn)) / (
                        1.001 - np.exp(-coef_obs[3] * fn))
                newobsda = coef_obs[0] * kLSF + coef_obs[1] * kRL + coef_obs[2]
                newobsda_ = np.hstack([newobsda_,newobsda])

            #SLSQP
            #l-BFGS-b
            #tnc
            thetas = np.deg2rad(sza_)
            thetaa = np.deg2rad(raa_)
            thetav = np.deg2rad(abs(vza_))

            fhs_ = vza_ * 1.0
            kRoss_ = vza_ * 1.0
            kLi_ = vza_ * 1.0
            kRL_ = vza_ * 1.0
            kR_ = vza_ * 1.0
            fn_ = vza_ * 1.0
            kVin_ = vza_ * 1.0
            fhs_[:] = 0
            fn_[:] = 0
            kRoss_[:] = 0
            kLi_[:] = 0
            kRL_[:] = 0
            kR_[:] = 0
            kVin_[:] = 0

            ind = (obs_> 0) * (sza_ < 85)
            az = np.cos(thetas[ind]) * np.cos(thetav[ind]) + \
                 np.sin(thetas[ind]) * np.sin(thetav[ind]) * np.cos(thetaa[ind])
            angle = np.arccos(az)
            fhs_[ind] = np.sqrt(
                (np.power(np.tan(thetas[ind]), 2) + np.power(np.tan(thetav[ind]), 2) - 2 * np.tan(
                    thetas[ind]) * np.tan(thetav[ind]) *
                 np.cos(thetaa[ind])))
            kRoss_[ind] = kernel_RossThick(vza_[ind],sza_[ind],raa_[ind])
            kLi_[ind] = kernel_LiDense(vza_[ind], sza_[ind], raa_[ind])
            fn_[ind] = np.tan(thetas[ind])
            # kLi_[ind] = kernel_LiSparse(vza_[ind], sza_[ind], raa_[ind])

            cthetv = np.cos(np.deg2rad(vza_))
            kLSF_ = 0.069 * cthetv * cthetv - 0.215 * cthetv + 1.176
            kVin_ = 1- cthetv

            ind = (obs_ > 0) * (sza_ < 85) * (np.isnan(kRoss_) == 0) * (np.isnan(kLi_) == 0)

            coef_nir = fitting_ROSSRL_VNIR_min(nir_[ind], kLSF_[ind], fhs_[ind], fn_[ind])
            kRL_[ind] = (np.exp(-coef_nir[3] * fhs_[ind]) - np.exp(-coef_nir[3] * fn_[ind])) / (
                        1.001 - np.exp(-coef_nir[3] * fn_[ind]))
            new_nir_ = coef_nir[0] * kLSF_ + coef_nir[1] * kRL_ + coef_nir[2]

            # coef_red = fitting_lsfrl_VNIR_min(red_[ind],kRoss_[ind],kLi_[ind])
            # new_red_ = coef_red[0]*kRoss_ + coef_red[1] *kLi_ + coef_red[2]

            coef_red = fitting_ROSSRL_VNIR_min(red_[ind], kLSF_[ind], fhs_[ind], fn_[ind])
            kRL_[ind] = (np.exp(-coef_red[3] * fhs_[ind]) - np.exp(-coef_red[3] * fn_[ind])) / (
                        1.001 - np.exp(-coef_red[3] * fn_[ind]))
            new_red_ = coef_red[0] * kLSF_ + coef_red[1] * kRL_ + coef_red[2]

            coef_vi = fitting_ROSSRL_VNIR_min(vi_[ind], kLSF_[ind], fhs_[ind], fn_[ind])
            kRL_[ind] = (np.exp(-coef_vi[3] * fhs_[ind]) - np.exp(-coef_vi[3] * fn_[ind])) / (
                        1.001 - np.exp(-coef_vi[3] * fn_[ind]))
            new_vi_ = coef_vi[0] * kLSF_ + coef_vi[1] * kRL_ + coef_vi[2]



            # ind = (obs_ > 0) * (sza_ < 65) * (np.isnan(kRoss_)==0)*(np.isnan(kLi_)==0)
            # kZ_= np.zeros(np.size(vza_))
            # kZ_[:] = 1.0
            # A = np.asarray([kRoss_[ind],kLi_[ind],kZ_[ind]])
            # A = np.transpose(A)
            # model = LinearRegression(copy_X=True, fit_intercept=True, n_jobs=-1, normalize=False)
            # model.fit(A, nir_[ind])
            # coeffs = model.coef_


            obs_all.append(obs_)
            obsda_all.append(obsda_)
            newobsda_all.append(newobsda_)
            kvol_all.append(kVin_)
            khot_all.append(fhs_)
            kcom_all.append(fn_)
            # kiso_all.append(kiso_)

            case[0] = klai
            case[1] = ksmc
            case[2:6] = coef_red[:4]
            case[6:10] = coef_nir[:4]
            case[10:14] = coef_vi[:4]
            coef_all.append(case)

# newobs_all = np.asarray(newobs_all)
obs_all = np.asarray(obs_all)
obsda_all = np.asarray(obsda_all)
newobsda_all = np.asarray(newobsda_all)
coef_all = np.asarray(coef_all)
kvol_all = np.asarray(kvol_all)
khot_all = np.asarray(khot_all)
kiso_all = np.asarray(kiso_all)
kcom_all = np.asarray(kcom_all)

np.save(indir0+'obs_all_vtkd_lsfrl.npy',arr = obs_all)
np.save(indir0+'obsda_all_vtkd_lsfrl.npy',arr = obsda_all)
np.save(indir0+'kvol_all_vtkd_lsfrl.npy',arr = kvol_all)
np.save(indir0+'khot_all_vtkd_lsfrl.npy',arr = khot_all)
np.save(indir0+'kcom_all_vtkd_lsfrl.npy',arr = kcom_all)
# np.save(indir0+'kiso_all_vtkd.npy',arr = kiso_all)
np.savetxt(outfiletxt,X=coef_all,fmt='%7.3f')


dif = newobsda_all-obsda_all
rmse = np.sqrt(np.average(dif*dif))
print(rmse)

# #### histogram plot

# data1 = np.reshape(std_, -1)
# data2 = np.reshape(rmse_, -1)
# bins = np.arange(0, 0.45, 0.05)
# result = np.transpose(np.stack([data1, data2]))
# plt.figure(figsize=[4.5, 3.6])
# plt.hist(result, bins=bins, histtype="bar", rwidth=0.75, alpha=0.6, density=False)
# ave1 = np.average(data1)
# ave2 = np.average(data2)
# plt.text(0.12, 350, '$Average_{STD}$ = %2.3f' % ave1)
# plt.text(0.12, 320, '$Average_{RMSE}$ = %2.3f' % ave2)
# plt.xlabel("Difference")
# plt.ylabel("Frequency")
# plt.legend(['STD', 'RMSE'], loc="upper right")
# plt.show()

#
# data1 = np.reshape(std_, -1)
# data2 = np.reshape(rmse_, -1)
# data3 = data1 - data2
# bins = np.arange(0, 0.35, 0.03)
# result = np.transpose(np.stack([data3]))
# plt.figure(figsize=[4.5, 3.6])
# plt.hist(result, bins=bins, histtype="bar", rwidth=0.75, alpha=0.6, density=False)
# plt.xlabel("Difference")
# plt.ylabel("Frequency")
# plt.legend(['STD-RMSE'], loc="upper right")
# plt.show()
#
# #### scatter plot
# ind = (obs_all > 250) *(newobs_all > 250)
# data1 = obs_all[ind]
# data2 = newobs_all[ind]
# dif = data2 - data1
# bias = np.mean(dif)
# rmse = np.sqrt(np.mean(dif*dif))
# r = np.corrcoef(data1,data2)[0,1]
# r2 =r*r
# plt.figure(figsize=[4.5, 3.5])
# xmin,xmax,ymin,ymax = 290,320,290,320
# plt.hist2d(data1, data2, bins=50, norm=LogNorm(), cmap='jet')
# plt.plot([xmin, xmax], [ymin, ymax], 'k--')
# plt.xlabel("SCOPE LST")
# plt.ylabel("Fitted LST")
# plt.xlim([xmin,xmax])
# plt.ylim([ymin,ymax])
# plt.colorbar()
# plt.text(307, 302, 'RMSE = %2.3f' % rmse)
# plt.text(307, 300, '$R^2$ = %2.3f' % r2)
# plt.text(307, 298, 'Bias = %2.3f' % bias)
# plt.show()

# plt.figure(figsize=[4.5, 3.6])
# data1 = np.reshape(tvdi_all, -1)
# data2 = np.reshape(newtvdi_all, -1)
# data3 = np.reshape(case_all, -1)
# plt.scatter(data1,data2,'o',cmap='jet',c=case_all)
# plt.xlabel("TVDI")
# plt.ylabel("Fitted TVDI")
# # plt.legend(['angle1', 'angle2', 'angle2', 'angle2'], loc="upper right")
# plt.show()


