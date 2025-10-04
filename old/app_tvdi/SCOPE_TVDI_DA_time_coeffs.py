from util.myfun_read_save import *
from util.myfun_sci import *
# import mayavi.mlab as mlab
import seaborn as sns


indir0 = r'F:\ShIP_TVDI_data\\'
time_ = [215.33, 215.38,215.42,215.46,215.50,215.54,215.58,215.63,215.67,215.71,215.75]
fmin_ = []
fmax_ = []

for time in time_:
    bf_ = []
    lst_ = []
    ndvi_ = []
    smc_ = []

    vza_ = []
    vaa_ = []

    XX = np.arange(0.05,0.42,0.06)
    YY = np.arange(0.3,5.0,0.6)

    ifhot = 0

    off1 = len(XX)
    off2 = len(YY)
    for ksmc in XX:
        for klai in YY:

            indir = indir0+r'output\DM_2012_LAI%.1f'%klai +'_SMC%.2f'%ksmc

            infile1 = indir+'\Directional\\'+'Temperatures_%.2f'%time +'.dat'
            lst = read_txt_float(infile1)
            infile2 = indir+'\Directional\\'+'Angles_%.2f'%time +'.dat'
            angle = read_txt_float(infile2)
            infile3 = indir+'\Directional\\'+'BRDF_%.2f'%time +'.dat'
            brdf = read_txt_float(infile3)
            if ifhot == 1:
                red = brdf[260,1:].reshape(-1)
                nir = brdf[460,1:].reshape(-1)
                lst = lst.reshape(-1)
                vza = angle[0, :414].reshape(-1)
                vaa = angle[1, :414].reshape(-1)
            else:
                red = brdf[260,1:408].reshape(-1)
                nir = brdf[460,1:408].reshape(-1)
                lst = lst[0,:407].reshape(-1)
                vza = angle[0, :407].reshape(-1)
                vaa = angle[1, :407].reshape(-1)

            ndvi = (nir - red) / (nir + red)
            bf = (nir+red)/2.0

            smc = lst*1.0
            smc[:] = ksmc.reshape(-1)

            #
            vza_.append(vza)
            vaa_.append(vaa)
            smc_.append(smc)
            lst_.append(lst)
            ndvi_.append(ndvi)
            bf_.append(bf)

            # ind = (vaa == 0) | (vaa == 180)
            # vza_.append(vza[ind])
            # vaa_.append(vaa[ind])
            # smc_.append(smc[ind])
            # lst_.append(lst[ind])
            # ndvi_.append(ndvi[ind])
            # bf_.append(bf[ind])

    ndvi_ = np.asarray(ndvi_)
    lst_ = np.asarray(lst_)
    smc_ = np.asarray(smc_)
    bf_ = np.asarray(bf_)
    vza_ = np.asarray(vza_)
    vaa_ = np.asarray(vaa_)

    ndvi_value,lstmax_value,fmax,lstmin_value,fmin = find_hot_cold_line_6(ndvi_,lst_)
    ndvi_plt = [-1, 2]
    lstmax_value_plt = np.polyval(fmax, ndvi_plt)
    lstmin_value_plt = np.polyval(fmin, ndvi_plt)
    Tsmin = np.polyval(fmin, ndvi_)
    Tsmax = np.polyval(fmax, ndvi_)


    min1 = 0.2
    max1 = 1.0
    min2 = 275
    max2 = 310
    data1 = ndvi_
    data2 = lst_
    ind = (data1 > -0.1) * (data2 > 250) * (data2 < 345) * (data1 < 1.0)
    plt.scatter(data1[ind], data2[ind], c = smc_[ind],cmap='jet',vmin=0.15,vmax = 0.50)
    plt.plot(ndvi_plt, lstmax_value_plt, 'r-')
    plt.plot(ndvi_plt, lstmin_value_plt, 'b-')
    plt.xlim([min1, max1])
    plt.ylim([min2, max2])
    plt.xlabel(r'NDVI')
    plt.ylabel(r'LST (K)')
    plt.xticks(fontsize = 12)
    plt.yticks(fontsize = 12)
    plt.title(time)
    plt.text(0.5, 297.5,'$LST_{MAX}$ = %.2f'%fmax[0]+'*NDVI+%.2f'%fmax[1],color='r',fontsize = 12)
    plt.text(0.5, 296,'$LST_{MIN}$ = %.2f'%fmin[0]+'*NDVI+%.2f'%fmin[1],color='b',fontsize = 12)
    cb=plt.colorbar()
    cb.set_label('SMC')
    plt.show()

    fmin_.append(fmin)
    fmax_.append(fmax)


fmax_ = np.asarray(fmax_)
fmin_ = np.asarray(fmin_)
result = np.hstack([fmax_,fmin_])
outfile = indir0+r'\line_coeffs_5percent.txt'
np.savetxt(outfile,result,fmt='%.3f',newline='\n')


# ndvi_plt = [-1, 2]
# lstmax_value_plt = np.polyval(fmax, ndvi_plt)
# lstmin_value_plt = np.polyval(fmin, ndvi_plt)
# Tsmin = np.polyval(fmin, ndvi_)
# Tsmax = np.polyval(fmax, ndvi_)
# TVDI_ = (lst_ - Tsmin) / (Tsmax - Tsmin)
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
