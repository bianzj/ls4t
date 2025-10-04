from util.myfun import *
from util.myfun2 import *
from util.myfun_read_save import *
from matplotlib.colors import LogNorm
from normalization_temporal.fitting_DTC import *
import seaborn as sns
import pandas as pd
from kdmodel import *

'''
obtain the fitting results, 
but the statisitical result are not here
'''

indir0 = r'F:\ShIP_VTKD_data\\'
outfiletxt = indir0 + 'KDTC_srosslis_coeffs.txt'
# time_ = [215.13,215.17,215.21,215.25,215.29,215.33,215.38, 215.42,215.46,215.50,215.54,215.58,215.63,215.67,215.71,215.75]
# time_ = [215.21,215.25,215.29,215.33,215.38, 215.42,215.46,215.50,215.54,215.58,215.63,215.67,215.71]
time__1 = [0.33,0.38,0.42,0.46,0.50,0.54,0.58,0.63,0.67]
time__2 = [0.33,0.37,0.41,0.45,0.49,0.54,0.58,0.62,0.66]


bf_ = []
lst_ = []
ndvi_ = []
smc_ = []
vza_ = []
vaa_ = []
XX = np.arange(0.15,0.46,0.1)
YY = np.arange(0.5,3.6,1.0)
ZZ = [80,173,266,356]

ifhot = 0

off1 = len(XX)
off2 = len(YY)


obs_all = []
newobs_all = []
coef_all = []
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
            raa_ = np.asarray([])
            vza_ = np.asarray([])
            sza_ = np.asarray([])
            pst_ = np.asarray([])
            case = np.zeros(11)

            for time in time_:
                indir = indir0 + 'scope_%d\\' % kdoy + 'output\hl_2019_LAI%.1f' % klai + '_SMC%.2f' % ksmc
                infile1 = indir+'\Directional\\'+'Temperatures_%.2f'%time +'.dat'
                lst = read_txt_float(infile1)
                infile2 = indir+'\Directional\\'+'Angles_%.2f'%time +'.dat'
                angle = read_txt_float(infile2)
                infile3 = indir+'\Directional\\'+'BRDF_%.2f'%time +'.dat'
                brdf = read_txt_float(infile3)
                if ifhot == 1:
                    # red = brdf[260, 1:].reshape(-1)
                    # nir = brdf[460, 1:].reshape(-1)
                    # lst = lst[0,407:414].reshape(-1)
                    # vza = angle[0, 407:414].reshape(-1)
                    # raa = angle[1, 407:414].reshape(-1)
                    # sza = angle[2, 407:414].reshape(-1)
                    # pst = lst*1.0
                    # pst[:] = (time - np.int_(time))*24

                    red = brdf[260, 1:].reshape(-1)
                    green = brdf[90, 1:].reshape(-1)
                    nir = brdf[460, 1:].reshape(-1)
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

                bfref = red[0] + nir[0]
                bfref = 2.0
                bf = (red + nir) / green
                vi = (nir - red) / (nir + red)

                obs_ = np.hstack([obs_,lst])
                raa_ = np.hstack([raa_,raa])
                vza_ = np.hstack([vza_,vza])
                sza_ = np.hstack([sza_,sza])
                pst_ = np.hstack([pst_,pst])
                bf_ = np.hstack([bf_, bf])
                vi_ = np.hstack([vi_, vi])


            # coef = fitting_KDTC_VinLi_min(obs_,pst_,vza_,sza_,raa_,method = 'SLSQP',Tbase= 290)
            # newobs_ = model_KDTC_VinLi(coef,vza_,sza_,raa_,pst_)
            # #
            kross = kernel_RossThick(vza_,sza_,raa_)
            klis = kernel_LiSparse(vza_,sza_,raa_)
            coef = fitting_ROSSLi_VNIR_min(vi_,kross,klis)

            newvi_ = model_RossThickLiSparse(coef,vza_,sza_,raa_)

            ### BFGS
            # coef = fitting_KDTC_TSA_LSFLI_min(obs_,pst_,vza_,sza_,raa_,klai,method = 'Powell',Tbase= 290)
            # newobs_ = model_KDTC_srossli(coef,vza_,sza_,raa_,pst_,klai)


            dif = newvi_ - vi_
            ind = (np.abs(dif) < 20)*(pst_>9)*(pst_<17)
            rmse = (np.sqrt(np.average(dif[ind]*dif[ind])))
            obs_all.append(vi_)
            newobs_all.append(newvi_)
            std = np.std(vi_)
            print(klai, ksmc, rmse,std)
            case[0] = klai
            case[1] = ksmc
            case[2] = rmse
            case[3:6] = coef
            coef_all.append(case)

newobs_all = np.asarray(newobs_all)
obs_all = np.asarray(obs_all)
coef_all = np.asarray(coef_all)




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


# plt.figure(figsize=[4.5, 3.6])
# data1 = np.reshape(tvdi_all, -1)
# data2 = np.reshape(newtvdi_all, -1)
# data3 = np.reshape(case_all, -1)
# plt.scatter(data1,data2,'o',cmap='jet',c=case_all)
# plt.xlabel("TVDI")
# plt.ylabel("Fitted TVDI")
# # plt.legend(['angle1', 'angle2', 'angle2', 'angle2'], loc="upper right")
# plt.show()

ind = (obs_all > 0) *(newobs_all > 0)
data1 = obs_all[ind]
data2 = newobs_all[ind]
dif = data2 - data1
bias = np.mean(dif)
rmse = np.sqrt(np.mean(dif*dif))
r = np.corrcoef(data1,data2)[0,1]
r2 =r*r
plt.figure(figsize=[4.5, 3.5])
xmin,xmax,ymin,ymax = 0,1,0,1
plt.hist2d(data1, data2, bins=50, norm=LogNorm(), cmap='jet')
plt.plot([xmin, xmax], [ymin, ymax], 'k--')
plt.xlabel("SCOPE LST")
plt.ylabel("Fitted LST")
plt.xlim([xmin,xmax])
plt.ylim([ymin,ymax])
plt.colorbar()
plt.text(0.5, 0.5, 'RMSE = %2.3f' % rmse)
# plt.text(307, 300, '$R^2$ = %2.3f' % r2)
# plt.text(307, 298, 'Bias = %2.3f' % bias)
plt.show()
