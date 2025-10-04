import numpy as np

from normalization_temporal.fitting_DTC import *
import seaborn as sns
import pandas as pd
import matplotlib.pylab as plt
from util.myfun import *
from sklearn.linear_model import LinearRegression

'''
obtain the fitting results, 
but the statisitical result are not here
'''

indir0 = r'F:\ShIP_VTKD_data//'
outfiletxt = indir0 + 'VTKD_lsfrl.txt'


toff = 0
tend = 7
coef_all = np.loadtxt(outfiletxt)

obsda_all = np.load(indir0+'obsda_all_vtkd_lsfrl.npy')
kvol_all = np.load(indir0+'kvol_all_vtkd_lsfrl.npy')
khot_all = np.load(indir0+'khot_all_vtkd_lsfrl.npy')
kcom_all = np.load(indir0+'kcom_all_vtkd_lsfrl.npy')
# kiso_all = np.load(indir0+'kiso_all_vtkd.npy')

bf_ = []
lst_ = []
ndvi_ = []
smc_ = []
vza_ = []
vaa_ = []
XX = np.arange(0.15,0.46,0.1)
YY = np.arange(0.5,3.6,1.0)
ZZ = [80,173,266,356]
# YY = np.asarray([2.3])

time__1 = [0.42,0.46,0.50,0.54,0.58,0.63,0.67]
time__2 = [0.41,0.45,0.49,0.54,0.58,0.62,0.66]

ifhot = 1

numX = len(XX)
numY = len(YY)
numZ = len(ZZ)

rmse_ = []
std_ = []

tsunlit_ = []
tsl_ = []
fvin_ = []
fli_ = []
lai_ = []
smc_ = []
kvol_all_new = []
khot_all_new = []
kiso_all_new = []
kcom_all_new = []
kvol_all_new1 = []
khot_all_new1 = []
kiso_all_new1 = []
kcom_all_new1 = []
kvol_all_new2 = []
khot_all_new2 = []
kiso_all_new2 = []
kcom_all_new2 = []
ta_all = []
sm_all = []
lai_all = []
rads_all = []
kstep = 0
ind = np.arange(0,16,1)
for kdoy in range(numZ):
    for ksmc in range(numX):
        for klai in range(numY):

            indir = indir0 + 'scope_%d\\' % ZZ[kdoy] + 'output\hl_2019_LAI%.1f' % YY[klai] + '_SMC%.2f' % XX[ksmc]
            infile2 = indir + '/' + 'surftemp.dat'
            coef22 = np.loadtxt(infile2)[ind, :]
            infile3 = indir + '/' + 'radiation.dat'
            coef33 = np.loadtxt(infile3)

            ktimestep = 0
            kcom_all_temp = kcom_all[kstep,:]*1.0
            kvol_all_temp = kvol_all[kstep,:]*1.0
            khot_all_temp = khot_all[kstep,:]*1.0
            kiso_all_temp = khot_all[kstep,:]*1.0
            kiso_all_temp[:] = 1.0

            kvol_all_temp1 = kvol_all[kstep,:]*1.0
            kcom_all_temp1 = kcom_all[kstep,:]*1.0
            khot_all_temp1 = khot_all[kstep,:]*1.0
            kiso_all_temp1 = khot_all[kstep,:]*1.0
            kiso_all_temp1[:] = 1.0

            kvol_all_temp2 = kvol_all[kstep,:]*1.0
            kcom_all_temp2 = kcom_all[kstep,:]*1.0
            khot_all_temp2 = khot_all[kstep,:]*1.0
            kiso_all_temp2 = khot_all[kstep,:]*1.0
            kiso_all_temp2[:] = 1.0

            ta_all_temp = kiso_all_temp1 * 1.0
            rads_all_temp = kiso_all_temp1 * 1.0
            sm_all_temp = kiso_all_temp1 * 1.0
            lai_all_temp = kiso_all_temp1 * 1.0

            num = 407
            num = 22

            for ktime in range(toff,tend):

                # fvc = 1-np.exp(-0.5*YY[klai])


                coef2 = coef22[ktime+7,:]
                coef3 = coef33[ktime+7,:]

                pst = coef2[2]*1.0
                pst = (pst - np.int_(pst))*24
                ta = coef2[3]*1.0
                rads = coef3[3]*1.0
                radl = coef3[4]*1.0
                ta1 = rads
                ta2 = ta1
                ta3 = ta2

                off =0
                # kcom_all_temp[ktimestep * num:(ktimestep + 1) * num] = kvol_all[kstep,ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 2 + off] * (rads)
                krl = np.exp(
                    -khot_all[kstep, ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 5 + off]) - np.exp(
                    -kcom_all[kstep, ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 5 + off])
                krl = krl / (1.001 - np.exp(-kcom_all[kstep, ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 5 + off]))
                kvol_all_temp[ktimestep * num:(ktimestep+1)*num] = kvol_all[kstep,ktimestep*num:(ktimestep+1)*num]    *  coef_all[kstep,2+off]
                khot_all_temp[ktimestep * num:(ktimestep + 1) * num] =  krl*coef_all[kstep, 3 + off]
                kiso_all_temp[ktimestep * num:(ktimestep + 1) * num] = kiso_all_temp[ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 4+off]
                off = 4
                # kcom_all_temp1[ktimestep * num:(ktimestep + 1) * num] = kvol_all[kstep,ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 2 + off] * (ta1)
                krl = np.exp(
                    -khot_all[kstep, ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 5 + off]) - np.exp(
                    -kcom_all[kstep, ktimestep * num:(ktimestep + 1) * num]* coef_all[kstep, 5 + off])
                krl = krl / (1.001 - np.exp(-kcom_all[kstep, ktimestep * num:(ktimestep + 1) * num]* coef_all[kstep, 5 + off]))
                kvol_all_temp1[ktimestep*num:(ktimestep+1)*num] = kvol_all[kstep,ktimestep*num:(ktimestep+1)*num] * coef_all[kstep,2+off]
                khot_all_temp1[ktimestep * num:(ktimestep + 1) * num] = krl* coef_all[kstep, 3 + off]
                kiso_all_temp1[ktimestep * num:(ktimestep + 1) * num] = kiso_all_temp1[ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 4+off]
                print(pst)


                # off =0
                # # kcom_all_temp[ktimestep * num:(ktimestep + 1) * num] = kvol_all[kstep,ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 2 + off] * (rads)
                # krl = np.exp(
                #     -khot_all[kstep, ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 5 + off]) - np.exp(
                #     -kcom_all[kstep, ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 5 + off])
                # krl = krl / (1.001 - np.exp(-kcom_all[kstep, ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 5 + off]))
                # kvol_all_temp[ktimestep * num:(ktimestep+1)*num] = kvol_all[kstep,ktimestep*num:(ktimestep+1)*num]    *  coef_all[kstep,2+off]*(ta3)
                # khot_all_temp[ktimestep * num:(ktimestep + 1) * num] =  krl*coef_all[kstep, 3 + off]*(ta3)
                # kiso_all_temp[ktimestep * num:(ktimestep + 1) * num] = kiso_all_temp[ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 4+off] * (ta3)
                # off = 4
                # # kcom_all_temp1[ktimestep * num:(ktimestep + 1) * num] = kvol_all[kstep,ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 2 + off] * (ta1)
                # krl = np.exp(
                #     -khot_all[kstep, ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 5 + off]) - np.exp(
                #     -kcom_all[kstep, ktimestep * num:(ktimestep + 1) * num]* coef_all[kstep, 5 + off])
                # krl = krl / (1.001 - np.exp(-kcom_all[kstep, ktimestep * num:(ktimestep + 1) * num]* coef_all[kstep, 5 + off]))
                # kvol_all_temp1[ktimestep*num:(ktimestep+1)*num] = kvol_all[kstep,ktimestep*num:(ktimestep+1)*num] * coef_all[kstep,2+off]*(ta1)
                # khot_all_temp1[ktimestep * num:(ktimestep + 1) * num] = krl* coef_all[kstep, 3 + off]*(ta2)
                # kiso_all_temp1[ktimestep * num:(ktimestep + 1) * num] = kiso_all_temp1[ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 4+off] * (ta3)
                # print(pst)

                # off =4
                # # kcom_all_temp[ktimestep * num:(ktimestep + 1) * num] = kvol_all[kstep,ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 2 + off] * (rads)
                # krl = np.exp(
                #     -khot_all[kstep, ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 5 + off]) - np.exp(
                #     -kcom_all[kstep, ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 5 + off])
                # krl = krl / (1.001 - np.exp(-kcom_all[kstep, ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 5 + off]))
                # kvol_all_temp[ktimestep * num:(ktimestep+1)*num] = kvol_all[kstep,ktimestep*num:(ktimestep+1)*num]    *  coef_all[kstep,2+off]*(rads)
                # khot_all_temp[ktimestep * num:(ktimestep + 1) * num] =  krl*coef_all[kstep, 3 + off]*(rads)
                # kiso_all_temp[ktimestep * num:(ktimestep + 1) * num] = kiso_all_temp[ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 4+off] * (rads)
                # off = 4
                # # kcom_all_temp1[ktimestep * num:(ktimestep + 1) * num] = kvol_all[kstep,ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 2 + off] * (ta1)
                # krl = np.exp(
                #     -khot_all[kstep, ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 5 + off]) - np.exp(
                #     -kcom_all[kstep, ktimestep * num:(ktimestep + 1) * num]* coef_all[kstep, 5 + off])
                # krl = krl / (1.001 - np.exp(-kcom_all[kstep, ktimestep * num:(ktimestep + 1) * num]* coef_all[kstep, 5 + off]))
                # kvol_all_temp1[ktimestep*num:(ktimestep+1)*num] = kvol_all[kstep,ktimestep*num:(ktimestep+1)*num] * coef_all[kstep,2+off]*(ta1)
                # khot_all_temp1[ktimestep * num:(ktimestep + 1) * num] = krl* coef_all[kstep, 3 + off]*(ta2)
                # kiso_all_temp1[ktimestep * num:(ktimestep + 1) * num] = kiso_all_temp1[ktimestep * num:(ktimestep + 1) * num] * coef_all[kstep, 4+off] * (ta3)

                # dsu = np.abs(coef2[5] -coef2[9])
                # dsd = np.abs(coef2[9]-coef2[4])
                # ds = np.abs(coef2[5] -coef2[4])
                # dvu = np.abs(coef2[6] -coef2[8])
                # dvd = np.abs(coef2[8]-coef2[7])
                # dv = np.abs(coef2[6] -coef2[7])

                ta_all_temp[ktimestep * num:(ktimestep + 1) * num] = ta
                rads_all_temp[ktimestep * num:(ktimestep + 1) * num] = rads
                lai_all_temp[ktimestep * num:(ktimestep + 1) * num] = YY[klai]
                sm_all_temp[ktimestep * num:(ktimestep + 1) * num] = XX[ksmc]

                ktimestep = ktimestep + 1

            kvol_all_new.append(kvol_all_temp)
            khot_all_new.append(khot_all_temp)
            kiso_all_new.append(kiso_all_temp)
            # kcom_all_new.append(kcom_all_temp)
            kvol_all_new1.append(kvol_all_temp1)
            khot_all_new1.append(khot_all_temp1)
            kiso_all_new1.append(kiso_all_temp1)
            # kcom_all_new1.append(kcom_all_temp1)
            kvol_all_new2.append(kvol_all_temp2)
            khot_all_new2.append(khot_all_temp2)
            kiso_all_new2.append(kiso_all_temp2)
            # kcom_all_new2.append(kcom_all_temp2)
            ta_all.append(ta_all_temp)
            rads_all.append(rads_all_temp)
            lai_all.append(lai_all_temp)
            sm_all.append(sm_all_temp)
            kstep = kstep +1

kvol_all_new = np.asarray(kvol_all_new)
khot_all_new = np.asarray(khot_all_new)
kiso_all_new = np.asarray(kiso_all_new)
kcom_all_new = np.asarray(kcom_all_new)
kcom_all_new = np.transpose(kcom_all_new)
kvol_all_new = np.transpose(kvol_all_new)
khot_all_new = np.transpose(khot_all_new)
kiso_all_new = np.transpose(kiso_all_new)
ta_all = np.asarray(ta_all)
rads_all = np.asarray(rads_all)
lai_all = np.asarray(lai_all)
sm_all = np.asarray(sm_all)

kvol_all_new1 = np.asarray(kvol_all_new1)
khot_all_new1 = np.asarray(khot_all_new1)
kiso_all_new1 = np.asarray(kiso_all_new1)
kcom_all_new1 = np.asarray(kcom_all_new1)
kcom_all_new1 = np.transpose(kcom_all_new1)
kvol_all_new1 = np.transpose(kvol_all_new1)
khot_all_new1 = np.transpose(khot_all_new1)
kiso_all_new1 = np.transpose(kiso_all_new1)


kvol_all_new2 = np.asarray(kvol_all_new2)
khot_all_new2 = np.asarray(khot_all_new2)
kiso_all_new2 = np.asarray(kiso_all_new2)
kcom_all_new2 = np.asarray(kcom_all_new2)
kcom_all_new2 = np.transpose(kcom_all_new2)
kvol_all_new2 = np.transpose(kvol_all_new2)
khot_all_new2 = np.transpose(khot_all_new2)
kiso_all_new2 = np.transpose(kiso_all_new2)

obsda_all = np.transpose(obsda_all)
kvol_all = np.transpose(kvol_all)
khot_all = np.transpose(khot_all)
ta_all = np.transpose(ta_all)
rads_all = np.transpose(rads_all)
lai_all = np.transpose(lai_all)
sm_all = np.transpose(sm_all)

# kcom_all = np.asarray(kcom_all).flatten()
kvol_all = np.asarray(kvol_all).flatten()
khot_all = np.asarray(khot_all).flatten()
kvol_all_new = np.asarray(kvol_all_new).flatten()
khot_all_new = np.asarray(khot_all_new).flatten()
kiso_all_new = np.asarray(kiso_all_new).flatten()
kcom_all_new = np.asarray(kcom_all_new).flatten()
kvol_all_new1 = np.asarray(kvol_all_new1).flatten()
khot_all_new1 = np.asarray(khot_all_new1).flatten()
kiso_all_new1 = np.asarray(kiso_all_new1).flatten()
kcom_all_new1 = np.asarray(kcom_all_new1).flatten()
kvol_all_new2 = np.asarray(kvol_all_new2).flatten()
khot_all_new2 = np.asarray(khot_all_new2).flatten()
kiso_all_new2 = np.asarray(kiso_all_new2).flatten()
kcom_all_new2 = np.asarray(kcom_all_new2).flatten()
obsda_all = np.asarray(obsda_all).flatten()
ta_all = np.asarray(ta_all).flatten()
rads_all = np.asarray(rads_all).flatten()
lai_all = np.asarray(lai_all).flatten()
sm_all = np.asarray(sm_all).flatten()
### flt


ind = (kvol_all !=0)*(khot_all!=0)*(np.isnan(kvol_all_new)==0)*(np.isnan(khot_all_new)==0) *(obsda_all!=0)*(np.isnan(kvol_all_new1)==0)*(np.isnan(khot_all_new1)==0)


### plot
# plt.figure(figsize=[4.5,4.0])
# plt.hist2d(kvol_all_new[ind],obsda_all[ind], bins=60, norm=LogNorm(), cmap='jet')
# # plt.xlabel('$fRoss × fRoss × Ta$ in Red')
# plt.xlabel('$kRoss × fRoss × Rads$ ')
# plt.ylabel('LST DA')
# # plt.plot(kvol_all_new[ind],obsda_all[ind],'.')
# plt.show()
# plt.figure(figsize=[4.5,4.0])
# plt.hist2d(khot_all_new[ind],obsda_all[ind], bins=60, norm=LogNorm(), cmap='jet')
# plt.xlabel('$kRL × fRL × Rads$')
# plt.ylabel('LST DA')
# # plt.plot(khot_all_new[ind],obsda_all[ind],'.')
# plt.show()
# plt.figure(figsize=[4.5,4.0])
# plt.hist2d(kiso_all_new[ind],obsda_all[ind], bins=60, norm=LogNorm(), cmap='jet')
# plt.xlabel('$fIso × kIso × Ta$ in Red')
# plt.ylabel('LST DA')
# # plt.plot(khot_all_new[ind],obsda_all[ind],'.')
# plt.show()


### fitting

model = LinearRegression(copy_X=True, fit_intercept=True, n_jobs=-1, normalize=False)


# A = np.asarray([kvol_all_new[ind],khot_all_new[ind],kiso_all_new[ind],
#                 kvol_all_new1[ind],khot_all_new1[ind],kiso_all_new1[ind]])
A = np.asarray([kvol_all_new[ind],khot_all_new[ind],kiso_all_new[ind],
                kvol_all_new1[ind],khot_all_new1[ind],kiso_all_new1[ind],
                ta_all[ind],rads_all[ind]])

A = np.transpose(A)
Y = obsda_all[ind]
Y = np.transpose(Y)
model.fit(A,Y)
coef = model.coef_
y0 = model.intercept_
YY = model.predict(A)
dif = YY - Y
dai = np.std(Y)
aai = np.sqrt(np.mean((Y*Y)))
rmse = np.sqrt(np.mean(dif*dif))
print(dai,aai,rmse)
plt.figure(figsize=[4.5,4.0])
plt.hist2d(YY,Y, bins=60, norm=LogNorm(), cmap='jet')
plt.xlabel('fitted LST DA ($\circ$C)')
plt.ylabel('simulated LST DA ($\circ$C)')
plt.text(0.5,-1.5,'RMSE = %4.3f'%rmse,fontsize = 14)
plt.xlim([-2.5,3.5])
plt.ylim([-2.5,3.5])
# plt.grid('True')
# plt.plot(khot_all_new[ind],obsda_all[ind],'.')
plt.show()


### other

# kvol_all = np.asarray(kvol_all).flatten()
# khot_all = np.asarray(khot_all).flatten()
# kvol_all_new = np.asarray(kvol_all_new).flatten()
# khot_all_new = np.asarray(khot_all_new).flatten()
# obsda_all = np.asarray(obsda_all).flatten()
#
# ind = (kvol_all != 0) * (khot_all != 0) * (np.isnan(kvol_all_new) == 0) * (np.isnan(khot_all_new) == 0)
# data = {'fRoss × kRoss':kvol_all[ind],'fLi × kLi':khot_all[ind],'LST DA':obsda_all[ind]}
# df = pd.DataFrame(data)
#
# sns.set_theme(style="whitegrid")
# sns.regplot(x='fRoss × kRoss',y='LST DA',data=df,ci = 0.5,
#            scatter_kws={"s": 10, "alpha": 0.1}, line_kws={"color": "C1"})
# # plt.xlim([-0.2,0.5])
# # plt.ylim([-2,2])
# plt.show()


### cour line
# sns.set_theme(style="whitegrid")
# sns.kdeplot(x='fRoss × kRoss',y='LST DA',data=df,
#             fill = True,
#             thresh=0.05, levels=5,
#            height = 5,
#            palette="muted",scatter_kws={"s": 10, "alpha": 0.5})
# plt.xlim([-0.2,0.3])
# plt.ylim([-2,2])
# plt.show()


# fvin_ = np.asarray(fvin_).flatten()
# fli_ = np.asarray(fli_).flatten()
# tsunlit_ = np.asarray(tsunlit_).flatten()
# tsl_ = np.asarray(tsl_).flatten()
# lai_ =np.asarray(lai_).flatten()
# smc_ = np.asarray(smc_).flatten()
#
#
# data = {'SMC':np.round(smc_,2),'LAI':np.round(lai_,2),'Tsl':tsl_,'Tsunlit':tsunlit_,'fVin':fvin_,'fLi':fli_}
# df = pd.DataFrame(data)
#
# sns.set_theme(style="whitegrid")
# cmap = sns.cubehelix_palette(rot=-.1, as_cmap=True)
# g = sns.relplot(x='fVin',y='Tsl',hue='SMC',size ='LAI',palette = cmap,data = df)
# g.set(xscale="linear",yscale = "linear")
# # g.ax.xaxis.grid(True, "minor", linewidth=.25)
# # g.ax.yaxis.grid(True, "minor", linewidth=.25)
# # g.despine(left=True, bottom=True)
# g.set(xlabel ="fVin",ylabel = "Tsl")
# g.set()
# plt.show()
#
#
# sns.set_theme(style="whitegrid")
# cmap = sns.cubehelix_palette(rot=-.1, as_cmap=True)
# g = sns.relplot(x='fLi',y='Tsunlit',hue='SMC',size ='LAI',palette = cmap,data = df)
# g.set(xscale="linear",yscale = "linear")
# # g.ax.xaxis.grid(True, "minor", linewidth=.25)
# # g.ax.yaxis.grid(True, "minor", linewidth=.25)
# # g.despine(left=True, bottom=True)
# g.set(xlabel ="fLi",ylabel = "Tsunlit")
# g.set()
# plt.show()