import matplotlib.pyplot as plt

from util.myfun_read_save import *
from util.myfun_sci import *
# import mayavi.mlab as mlab
import seaborn as sns
from kernel_RossLi import *
from matplotlib.colors import LogNorm
from kernel_RossLi_ms import *

indir0 = r'F:\ShIP_TVDI_data\\'
time_ = [215.42,215.46,215.50,215.54,215.58,215.63,215.67,215.71,215.75]
saa_ = [100.8,113.9,133.3,164.2,202.2,230.7,248.6,261.9,271.0]
koff = 2
specvaa_ = [0,110,200,250]
specvza_ = [0,40,20,40]
label_ = [ '%.2f'%time for time in time_]

kva = 1

specvaa = specvaa_[kva]
specvza = specvza_[kva]


infile = indir0 + '\line_coeffs.txt'
line_coeffs = read_txt2array(infile)



bf_ = []
lst_ = []
ndvi_ = []
smc_ = []
vza_ = []
vaa_ = []

XX = np.asarray([0.29,0.19])
# YY = np.arange(0.5,3.6,0.2)
# XX = np.asarray([0.15])
YY = np.asarray([2.1])

ifhot = 0

off1 = len(XX)
off2 = len(YY)

rd = 3.1415926/180.0
tvdi_all = []
newtvdi_all = []
rmse_ = []
std_ = []
newsmc = np.zeros([off1,off2])
newlai = np.zeros([off1,off2])
tvdipred = np.zeros([off1,off2])

for kksmc in range(off1):
    for kklai in range(off2):

        ksmc = XX[kksmc]
        klai = YY[kklai]

        k = 0
        tvdi_ = []
        raa_ = []
        vza_ = []
        sza_ = []
        angdis_ = []

        for time in time_:

            fmax = line_coeffs[k+koff,0:2]
            fmin = line_coeffs[k+koff,2:4]
            specraa = np.abs(saa_[k] - specvaa) // 10 * 10
            if specraa > 180: specraa = 360-specraa

            indir = indir0+'output\DM_2012_LAI%.1f'%klai +'_SMC%.2f'%ksmc

            infile1 = indir+'\Directional\\'+'Temperatures_%.2f'%time +'.dat'
            lst = read_txt_float(infile1)
            infile2 = indir+'\Directional\\'+'Angles_%.2f'%time +'.dat'
            angle = read_txt_float(infile2)
            infile3 = indir+'\Directional\\'+'BRDF_%.2f'%time +'.dat'
            brdf = read_txt_float(infile3)
            if ifhot == 1:
                red = brdf[260, 1:].reshape(-1)
                nir = brdf[460, 1:].reshape(-1)
                lst = lst.reshape(-1)
                vza = angle[0, :414].reshape(-1)
                vaa = angle[1, :414].reshape(-1)
                sza = angle[2, :414].reshape(-1)
            else:
                red = brdf[260, 1:408].reshape(-1)
                nir = brdf[460, 1:408].reshape(-1)
                lst = lst[0, :407].reshape(-1)
                vza = angle[0, :407].reshape(-1)
                vaa = angle[1, :407].reshape(-1)
                sza = angle[2, :407].reshape(-1)

            ndvi = (nir - red) / (nir + red)
            bf = (nir+red)/2.0

            smc = lst*1.0
            smc[:] = ksmc.reshape(-1)

            ind = (vza == specvza)*(vaa == specraa)
            ndvi0 = ndvi[ind]
            lst0 = lst[ind]
            sza0 = sza[ind]
            vza0 = vza[ind]
            raa0 = vaa[ind]
            ndvi_plt = [-1, 2]
            lstmax_value_plt = np.polyval(fmax, ndvi_plt)
            lstmin_value_plt = np.polyval(fmin, ndvi_plt)
            Tsmin = np.polyval(fmin, ndvi0)
            Tsmax = np.polyval(fmax, ndvi0)
            tvdi0 = (lst0 - Tsmin) / (Tsmax - Tsmin)
            tvdi_.append(tvdi0[0])
            raa_.append(raa0[0])
            vza_.append(vza0[0])
            sza_.append(sza0[0])

            cosang = np.cos(sza0*rd)*np.cos(vza0*rd) + np.sin(sza0*rd)*np.sin(vza0*rd)*np.cos(specraa*rd)
            ang = np.arccos(cosang)/rd
            if ang > 90: ang = 90
            angdis_.append(ang)
            k = k+1

        tvdi_ = np.asarray(tvdi_).flatten()
        sza_ = np.asarray(sza_).flatten()
        vza_ = np.asarray(vza_).flatten()
        raa_ = np.asarray(raa_).flatten()

        predicted,coeffs,std,rmse,newtvdi_,maxdif = kernels_LSFLI_ms(sza_, vza_, raa_, tvdi_)
        newtvdi_ = np.asarray(newtvdi_)
        std_.append(np.std(tvdi_))
        dif = newtvdi_-tvdi_
        rmse_.append(np.sqrt(np.average(dif*dif)))

        tvdi_all.append(tvdi_)
        newtvdi_all.append(newtvdi_)
        newsmc[kksmc,kklai] = ksmc
        newlai[kksmc,kklai] = klai
        tvdipred[kksmc,kklai] = predicted


tvdi_all = np.asarray(tvdi_all)
newtvdi_all = np.asarray(newtvdi_all)
std_ = np.asarray(std_)
rmse_  = np.asarray(rmse_)

tvdi_all = np.transpose(tvdi_all)
newtvdi_all = np.transpose(newtvdi_all)

label_ = np.arange(215.416,215.750,0.0416)
angdis_ = np.asarray(angdis_)

# fig,ax1 = plt.subplots(figsize = (5.9,3.5))
fig,ax1 = plt.subplots(figsize = (4.5,3.5))

ax1.plot(label_,tvdi_all[:,0],'o',color='royalblue')
# ax1.plot(label_,tvdi_all[:,1],'o',color='orange')
# ax1.plot(label_,tvdi_all[:,1],'o',color='limegreen')
ax1.plot(label_,tvdi_all[:,1],'o',color='orangered')
ax1.plot(label_,newtvdi_all[:,0],'-',color='royalblue')
# ax1.plot(label_,newtvdi_all[:,1],'-',color='orange')
# ax1.plot(label_,newtvdi_all[:,1],'-',color='limegreen')
ax1.plot(label_,newtvdi_all[:,1],'-',color='orangered')

data1 = newtvdi_all[:,1]
data2 = tvdi_all[:,1]
dif1 = data1-data2
r = np.corrcoef(data1,data2)[0,1]
r21 =r*r
rmse1 = np.sqrt(np.average(dif1*dif1))


data1 = newtvdi_all[:,0]
data2 = tvdi_all[:,0]
dif2 = data1-data2
r = np.corrcoef(newtvdi_all[:,0],tvdi_all[:,0])[0,1]
r22 =r*r
rmse2 = np.sqrt(np.average(dif2*dif2))
print(r21,r22)


plt.legend(['SMC 0.29','SMC 0.19'],loc='upper right', borderaxespad=0.)
plt.xlabel('DOY (Beijing Time)')
plt.ylabel('TVDI')
plt.xlim([215.38,215.8])
plt.ylim([-0.15,1.3])
plt.text(215.4,-0.03,'  0.19:$RMSE$=%3.2f'%rmse1+'   $R^2$=%3.2f'%r21)
plt.text(215.4,-0.13,'  0.29:$RMSE$=%3.2f'%rmse2+'   $R^2$=%3.2f'%r22)


ax2 = ax1.twinx()
ax2.plot(label_,angdis_,'^--',color='black')
plt.ylabel('Angular Distance ($\circ$)')
plt.ylim([-15,110])
plt.legend(['Angle'],bbox_to_anchor=(0.32, 0.93), loc='upper left', borderaxespad=0.)
plt.tight_layout()
plt.show()


# plt.figure(figsize=[4.5, 3.6])
# plt.scatter(newsmc,tvdipred,cmap='jet',c=newlai)
# plt.xlabel('SMC')
# plt.ylabel('TVDI')
# p = plt.colorbar()

# TVDI_std = np.zeros([off1,off2])
# TVDI_dif =  np.zeros([off1,off2])
# k = 0
# for ksmc in range(off1):
#     for klai in range(off2):
#         k = ksmc*off2+klai
#         TVDI_std[ksmc,klai]=( np.std(TVDI_[k,:]))
#         TVDI_dif[ksmc,klai]=(np.max(TVDI_[k,:])-np.min(TVDI_[k,:]))
#         k = k +1
# TVDI_std = np.zeros([off1,off2])
# TVDI_dif =  np.zeros([off1,off2])
# k = 0
#
# for ksmc in range(off1):
#     for klai in range(off2):
#         k = ksmc*off2+klai
#         TVDI_std[ksmc,klai]=( np.std(TVDI_[k,:]))
#         TVDI_dif[ksmc,klai]=(np.max(TVDI_[k,:])-np.min(TVDI_[k,:]))
#         k = k +1
#
# #### DA MAX - MIN
# f, ax = plt.subplots(figsize = (12,7))
# sns.heatmap(TVDI_dif, linewidths = 0.05,  annot=True, vmax=0.5, vmin=0, cmap='rainbow',fmt=".2f")
# ax.set_title(r'$TVDI_{max} - TVDI_{min}$')
# labelx_ = []
# labely_ = []
# for xx in XX:
#     labelx_.append('%.2f'%xx)
# for yy in YY:
#     labely_.append('%.2f'%yy)
# ax.set_xticklabels(labely_,fontsize=8)
# ax.set_yticklabels(labelx_,fontsize=8)
# ax.set_xlabel('LAI')
# ax.set_ylabel('SMC')
# plt.show()
#
# #### DA INDEX
# f, ax = plt.subplots(figsize = (12,7))
# sns.heatmap(TVDI_std, linewidths = 0.05,  annot=True, vmax=0.35, vmin=0, cmap='rainbow',fmt=".2f")
# ax.set_title(r'$\sigma (TVDI)$')
# labelx_ = []
# labely_ = []
# for xx in XX:
#     labelx_.append('%.2f'%xx)
# for yy in YY:
#     labely_.append('%.2f'%yy)
# ax.set_xticklabels(labely_,fontsize=8)
# ax.set_yticklabels(labelx_,fontsize=8)
# ax.set_xlabel('LAI')
# ax.set_ylabel('SMC')
# plt.show()
#
#
# #######  LST--- NDVI SPACE
# min1 = 0.2
# max1 = 1.0
# min2 = 295
# max2 = 310
# data1 = ndvi_
# data2 = lst_
# ind = (data1 > -0.1) * (data2 > 250) * (data2 < 345) * (data1 < 1.0)
# plt.scatter(data1[ind], data2[ind], c = smc_[ind],cmap='jet',vmin=0.15,vmax = 0.50)
# plt.plot(ndvi_plt, lstmax_value_plt, 'r-')
# plt.plot(ndvi_plt, lstmin_value_plt, 'b-')
# plt.xlim([min1, max1])
# plt.ylim([min2, max2])
# plt.xlabel(r'NDVI')
# plt.ylabel(r'LST (K)')
# plt.xticks(fontsize = 12)
# plt.yticks(fontsize = 12)
# plt.text(0.5, 297.5,'$LST_{MAX}$ = %.2f'%fmax[0]+'*NDVI+%.2f'%fmax[1],color='r',fontsize = 12)
# plt.text(0.5, 296,'$LST_{MIN}$ = %.2f'%fmin[0]+'*NDVI+%.2f'%fmin[1],color='b',fontsize = 12)
# cb=plt.colorbar()
# cb.set_label('SMC')
# plt.show()
#
# ###############  LST---BF SPACE
# data1 = bf_
# data2 = lst_
# ind = (data1 > 0) * (data2 > 250) * (data2 < 345) * (data1 < 1.0)
# plt.scatter(data1[ind], data2[ind], c = smc_[ind],cmap='jet',vmin=0.25,vmax = 0.50)
# plt.xlim([0.12, 0.32])
# plt.ylim([min2, max2])
# plt.xlabel(r'BF')
# plt.ylabel(r'LST (K)')
#
# cb = plt.colorbar()
# cb.set_label('SMC')
# plt.show()
#
# ### display 3D results
# data1 = ndvi_
# data2 = bf_
# data3 = lst_
# ind = (data1 > 0.03) * (data3 > 250) * (data3 < 345) * (data1 < 1.0)
# pl = mlab.points3d(data1[ind]*10,data2[ind]*100,data3[ind],colormap='jet')
# mlab.outline()
# mlab.colorbar()
# mlab.axes(xlabel='ndvi', ylabel='bf', zlabel='lst')
# mlab.show()
