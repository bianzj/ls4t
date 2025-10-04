from util.myfun import *
import pandas as pd
import time
from datetime import datetime
import seaborn as sns

'''
使用地表观测数据对模拟的结果进行验证
'''

start =time.clock()
days_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

indir_lst_mea0 = r'E:\AHI_heihe\lst\\'
indir_tif_mea0 = r'E:\AHI_heihe\tif\\'
indir_lst_sim10 = r'E:\ShIP_DVT\LST_dtc_heihe\\'
indir_lst_sim20 = r'E:\ShIP_DVT\LST_dvt_heihe\\'
symbol = 'AHI'

lst_mea_ = np.asarray([])
lst_sim1_ = np.asarray([])
lst_sim2_ = np.asarray([])
for kmonth0 in range(8, 9):
    thedoy = (kmonth0 - 1) * 30 + 16
    for kday0 in range(1, 31):
        kstep = 0
        for khour0 in range(9 - 8, 16 - 8):
            indir_lst_mea = indir_lst_mea0 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'
            indir_tif_mea = indir_tif_mea0 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'
            indir_lst_sim1 = indir_lst_sim10 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'
            indir_lst_sim2 = indir_lst_sim20 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'
            kdoy0 = date2DOY(2019, kmonth0, kday0)

            kdoy = kdoy0 + 0
            khour = khour0
            if khour0 < 0:
                kdoy = kdoy - 1
                khour = khour0 + 24
                if kday0 == 1:
                    indir_lst_mea = indir_lst_mea0 + r'\%02d' % (kmonth0 - 1) + r'\%02d' % days_of_month[kmonth0 - 2] + '\\'
                    indir_tif_mea = indir_tif_mea0 + r'\%02d' % (kmonth0 - 1) + r'\%02d' % days_of_month[kmonth0 - 2] + '\\'
                    indir_lst_sim1 = indir_lst_sim10 + r'\%02d' % (kmonth0 - 1) + r'\%02d' % days_of_month[kmonth0 - 2] + '\\'
                    indir_lst_sim2 = indir_lst_sim20 + r'\%02d' % (kmonth0 - 1) + r'\%02d' % days_of_month[kmonth0 - 2] + '\\'
                else:
                    indir_lst_mea = indir_lst_mea0 + r'\%02d' % (kmonth0) + r'\%02d' % (kday0 - 1) + '\\'
                    indir_tif_mea = indir_tif_mea0 + r'\%02d' % (kmonth0) + r'\%02d' % (kday0 - 1) + '\\'
                    indir_lst_sim1 = indir_lst_sim10 + r'\%02d' % (kmonth0) + r'\%02d' % (kday0 - 1) + '\\'
                    indir_lst_sim2 = indir_lst_sim20 + r'\%02d' % (kmonth0) + r'\%02d' % (kday0 - 1) + '\\'

            for kmin in range(0, 4, 3):
                infile_lst_mea = indir_lst_mea + symbol + '_2019%03d' % (kdoy) + '_%02d' % khour + '%1d0' % kmin + '_lst.tif'
                infile_lst_sim1 = indir_lst_sim1 + symbol + '_2019%03d' % (kdoy) + '_%02d' % khour + '%1d0' % kmin + '_lst.tif'
                infile_lst_sim2 = indir_lst_sim2 + symbol + '_2019%03d' % (
                    kdoy) + '_%02d' % khour + '%1d0' % kmin + '_lst.tif'
                infile_cloud = indir_tif_mea + symbol + '_2019%03d' % (kdoy) + '_%02d' % khour + '%1d0' % kmin + '_tcc.tif'

                print(infile_lst_mea)
                if ((os.path.exists(infile_lst_mea) == 1)&(os.path.exists(infile_lst_sim1) == 1)&(os.path.exists(infile_lst_sim2) == 1)):
                    [lst_mea, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst_mea)
                    [lst_sim1, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst_sim1)
                    [lst_sim2, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst_sim2)
                    [cloud, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud)
                    cloud = resize_data_near(cloud, nl, ns)

                    ind = (lst_mea > 275) *(lst_sim1>275)  *(lst_sim2>275) *(cloud <0.01) *(lst_sim1 != 273.15)*(lst_sim2 != 273.15)
                    if sum(ind)>0:
                        lst_mea_ = np.hstack([lst_mea_,lst_mea[ind]])
                        lst_sim1_ = np.hstack([lst_sim1_,lst_sim1[ind]])
                        lst_sim2_ = np.hstack([lst_sim2_,lst_sim2[ind]])

data1 = lst_mea_
data2 = lst_sim1_
data3 = lst_sim2_
ind = (np.abs(data1-data2)<7.5) *(np.abs(data1-data3)<7.5)
num = np.sum(ind)
if np.sum(num)<1:print('bad bad bad')
data1 = data1[ind]
data2 = data2[ind]
data3 = data3[ind]

dif = data2 - data1
bias = np.mean(dif)
rmse = np.sqrt(np.mean(dif * dif))
rr = np.corrcoef(data1, data2)
r2 = rr[1, 0] * rr[1, 0]
print("DTC num=", num, "rmse=", rmse, "bias=", bias, "r2=", r2)

dif = data3 - data1
bias = np.mean(dif)
rmse = np.sqrt(np.mean(dif * dif))
rr = np.corrcoef(data1, data3)
r2 = rr[1, 0] * rr[1, 0]
print("VT num=", num, "rmse=", rmse, "bias=", bias, "r2=", r2)

###
# df = pd.DataFrame({'Dif (K)': dif})
# sns.histplot(data=df,x=dif)
# plt.show()

### scattering plot
df = pd.DataFrame({'AHI LST (K)': data1, 'Fitted LST (K)': data3})
sns.set_theme(style="white")
# fig = plt.figure(figsize=(6.5,6.5))
xmin, xmax, ymin, ymax = 275, 325, 275, 325
# plt.hist2d(data1, data2, bins=50, norm=LogNorm(), cmap='jet')
g = sns.jointplot(x='AHI LST (K)', y='Fitted LST (K)', data=df, kind='hex')
plt.plot([xmin, xmax], [ymin, ymax], '--')
# g=sns.histplot(x=data1, y=data2,bins=30,norm=LogNorm(),log_scale=(False, False))
# g.set(xlabel='SCOPE LST (K)',ylabel='Fitted LST (K)')
# plt.xlabel("SCOPE LST")
# plt.ylabel("Fitted LST")
plt.xlim([xmin, xmax])
plt.ylim([ymin, ymax])
# plt.colorbar()
plt.text(300, 298 - 10, 'RMSE = %2.3f' % rmse)
plt.text(300, 295 - 10, '$R^2$ = %2.3f' % r2)
plt.text(300, 292 - 10, 'Bias = %2.3f' % bias)
plt.show()

