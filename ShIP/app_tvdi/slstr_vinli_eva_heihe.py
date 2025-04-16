import matplotlib.pyplot as plt
import numpy as np

from normalization_angular.fitting_kernels import *
import pandas as pd
from inversion_tvdi.kdinversion import *
import seaborn as sns
from scipy import stats

'''
得到线性结果
'''

def averoff(array,imagex,imagey,off):
    output = []
    if off == 0:
        output = array[imagex,imagey]
        return output
    for k in range(size(imagex)):
        ioff = imagex[k]-off
        iend = imagex[k]+off+1
        joff = imagey[k]-off
        jend = imagey[k]+off+1
        temp = array[ioff:iend,joff:jend]
        ind = (temp >0.01) * (temp<0.99)
        if np.sum(ind)<1:
            output.append(0)
            continue
        std0 = np.std(temp[ind])
        mean0 = np.mean(temp[ind])
        indd = (temp < (mean0+3*std0)) *(temp > (mean0-3*std0)) *ind
        ave = np.average(temp[indd])
        output.append(ave)
    return np.asarray(output)

def avecoeff(array,imagex,imagey,off):
    output = []
    if off == 0:
        output = array[:,imagex,imagey]
        return output
    for k in range(size(imagex)):
        ioff = imagex[k]-off
        iend = imagex[k]+off+1
        joff = imagey[k]-off
        jend = imagey[k]+off+1
        ave = np.zeros(3)
        for kk in range(3):
            temp = array[kk,ioff:iend,joff:jend]
            ind = (temp >-1000.01) * (temp<1000.99)* (temp!=0)
            if np.sum(ind)<1:
                return np.zeros(3)
            std0 = np.std(temp[ind])
            mean0 = np.mean(temp[ind])
            indd = (temp < (mean0+3*std0)) *(temp > (mean0-3*std0)) *ind
            ave[kk] = np.average(temp[indd])

        return ave


def turnon(coeff,vza):
    # sza0 = np.arange(0, 75, 1)
    # vaa0 = np.arange(0, 181, 1)
    # newsza, newvaa = np.meshgrid(sza0, vaa0)
    # newsza = np.reshape(newsza, -1)
    # newvaa = np.reshape(newvaa, -1)
    # newvza = np.zeros(np.size(newsza))
    # newvza[:] = vza
    Kvin,Kli,kiso = kernel_VinLiDense(np.asarray([0]), np.asarray([45]), np.asarray([0]))

    A = np.asarray([Kvin, Kli,kiso])
    A = np.transpose(A)

    temp = np.dot(A, coeff[:3])
    rd = np.pi/180.0
    # weight = np.sin(newsza*rd) *np.cos(newsza*rd)
    # predicted = np.average(temp*weight)/np.average(weight)
    predicted = temp
    return predicted


def turnhe(coeff,vza):
    sza0 = np.arange(0, 75, 1)
    vaa0 = np.arange(0, 181, 1)
    newsza, newvaa = np.meshgrid(sza0, vaa0)
    newsza = np.reshape(newsza, -1)
    newvaa = np.reshape(newvaa, -1)
    newvza = np.zeros(np.size(newsza))
    newvza[:] = vza
    Kvin,Kli,kiso = kernel_VinLiDense(np.asarray([newvza]), np.asarray([newsza]), np.asarray([newvaa]))

    A = np.asarray([Kvin, Kli,kiso])
    A = np.transpose(A)

    temp = np.dot(A, coeff[:3])
    rd = np.pi/180.0
    weight = np.sin(newsza*rd) *np.cos(newsza*rd)
    predicted = np.average(temp*weight)/np.average(weight)
    return predicted

indir_tvdi = r'E:\SLSTR_Heihe\tvdi\\'
indir_site = r'E:\field\\'
indir_tif = r'E:\SLSTR_heihe\s3a\tif\\'



'''water moisture from field data'''

infile_DM = indir_site+'2019_DM.csv'
aws_dm = pd.read_csv(infile_DM, parse_dates=['TIMESTAMP'],low_memory=False)
infile_AR = indir_site+'2019_AR.csv'
aws_ar = pd.read_csv(infile_AR, parse_dates=['TIMESTAMP'],low_memory=False)
infile_HHL = indir_site+'2019_HHL.csv'
aws_hhl = pd.read_csv(infile_HHL, parse_dates=['TIMESTAMP'],low_memory=False)
infile_HM = indir_site+'2019_HM.csv'
aws_hm = pd.read_csv(infile_HM, parse_dates=['TIMESTAMP'],low_memory=False)
infile_HZZ = indir_site+'2019_HZZ.csv'
aws_hzz = pd.read_csv(infile_HZZ, parse_dates=['TIMESTAMP'],low_memory=False)
infile_SDQ = indir_site+'2019_SDQ.csv'
aws_sdq = pd.read_csv(infile_SDQ, parse_dates=['TIMESTAMP'],low_memory=False)

infile_site_geo = r'E:\field\Heihe_Site_2019.txt'
tempdata = read_txt_str(infile_site_geo,',')
lon = [np.float(tempdata[i][1]) for i in range(np.shape(tempdata)[0])]
lat = [np.float(tempdata[i][2]) for i in range(np.shape(tempdata)[0])]


'''from vza and vaa to geo site position'''
infile_dem = r'E:\type\type_heihe_1000.tif'

dem, ns, nl, nb, geog, proj,dataset = read_image_dataset_gdal(infile_dem)
imagex,imagey = loc2map(lat,lon,dataset)


#
name1 = 'Ms_2cm'
name2 = 'Ms_2cm'
ms_site_ = np.asarray([])
tvdi_site_adj_ = np.asarray([])
tvdi_site_ori_ = np.asarray([])
'''tvdi from remote sensing data'''
kyear = 2019
n_avail = 2
n_pixel = 0
print(n_avail,n_pixel)

offv = 'vinli'

'''得到拟合结果和测量结果'''
doymin = 150
doymax = 300
khour = 12-8
kmin = 0
for kdoy in range(doymin,doymax):
    ### AHI_2019033_0000_lst.tif

    infile_coeffs = indir_tvdi + '2019%03d'%kdoy + '_coeffs_'+offv+'.tif'

    if os.path.exists(infile_coeffs) == 0:
        n_size = np.size(imagex)
        temp = np.zeros(n_size)
        if np.size(tvdi_site_adj_) < 1:
            tvdi_site_adj_ = temp
        else:
            tvdi_site_adj_ = np.vstack([tvdi_site_adj_, temp])

        if np.size(ms_site_) < 1:
            ms_site_ = temp
        else:
            ms_site_ = np.vstack([ms_site_, temp])
        continue

    coeffs,ns,nl,nb,geog,proj = read_image_gdal(infile_coeffs)
    tvdi_adj = np.zeros([nl, ns])
    for kpos in range(1,3):
        x = imagex[kpos]
        y = imagey[kpos]
        for kl in range(x - n_avail, x + n_avail + 1):
            for ks in range(y - n_avail, y + n_avail + 1):
                # coeff = coeffs[:, kl,ks]
                coeff = avecoeff(coeffs, np.asarray([kl]), np.asarray([ks]), 0)
                tvdi_adj[kl, ks] = turnon(coeff, 45)
    #tvdi_site = tvdi[imagex,imagey]
    tvdi_site_adj = averoff(tvdi_adj, imagex, imagey, n_pixel)


    ind = (kdoy-1) * 144 + (khour +8)* 6 + np.int(kmin / 10)

    ms_site1 = np.asarray([aws_ar[name1][ind], aws_dm[name1][ind], aws_hzz[name1][ind],
                          aws_sdq[name1][ind], aws_hhl[name1][ind], aws_hm[name1][ind]])
    ms_site2 = np.asarray([aws_ar[name2][ind], aws_dm[name2][ind], aws_hzz[name2][ind],
                          aws_sdq[name2][ind], aws_hhl[name2][ind], aws_hm[name2][ind]])
    ms_site = ((ms_site1) + (ms_site2))*0.5

    if np.size(tvdi_site_adj_) < 1:
        tvdi_site_adj_ = tvdi_site_adj
    else:
        tvdi_site_adj_= np.vstack([tvdi_site_adj_, tvdi_site_adj])

    if np.size(ms_site_) < 1:
        ms_site_ = ms_site
    else:
        ms_site_ = np.vstack([ms_site_,ms_site])



'''得到原始结果'''
#
indir_lst = r'E:\SLSTR_heihe\s3a\lst\\'
indir_tif = r'E:\SLSTR_heihe\s3a\tif\\'
indir_tvdi = r'E:\SLSTR_heihe\s3a\tvdi\\'



files = search_file(indir_tvdi,['S3A','nadir'])
num_files = np.size(files)
tvdi_s3a_nadir0 = []
doy_s3a_nadir0 = []
for kfile in range(num_files):
    file = files[kfile]
    infile = indir_tvdi+file
    doy = file[8:11]
    doy_s3a_nadir0.append(doy)
    [tvdi,ns,nl,nb,geog,proj] = read_image_gdal(infile)
    temp = averoff(tvdi, imagex, imagey, n_pixel)
    tvdi_s3a_nadir0.append(temp)
doy_s3a_nadir0 = np.asarray(doy_s3a_nadir0, dtype=np.int16)
tvdi_s3a_nadir0 = np.asarray(tvdi_s3a_nadir0)


files = search_file(indir_tvdi,['S3A','obliq'])
num_files = np.size(files)
tvdi_s3a_obliq0 = []
doy_s3a_obliq0 = []
for kfile in range(num_files):
    file = files[kfile]
    infile = indir_tvdi+file
    doy = file[8:11]
    doy_s3a_obliq0.append(doy)
    [tvdi,ns,nl,nb,geog,proj] = read_image_gdal(infile)
    temp = averoff(tvdi,imagex,imagey,n_pixel)
    tvdi_s3a_obliq0.append(temp)
doy_s3a_obliq0 = np.asarray(doy_s3a_obliq0, dtype=np.int16)
tvdi_s3a_obliq0 = np.asarray(tvdi_s3a_obliq0)

indir_lst = r'E:\SLSTR_heihe\s3b\lst\\'
indir_tif = r'E:\SLSTR_heihe\s3b\tif\\'
indir_tvdi = r'E:\SLSTR_heihe\s3b\tvdi\\'


files = search_file(indir_tvdi,['S3B','nadir'])
num_files = np.size(files)
tvdi_s3b_nadir0 = []
doy_s3b_nadir0 = []
for kfile in range(num_files):
    file = files[kfile]
    infile = indir_tvdi+file
    doy = file[8:11]
    doy_s3b_nadir0.append(doy)
    [tvdi,ns,nl,nb,geog,proj] = read_image_gdal(infile)
    temp = averoff(tvdi,imagex,imagey,n_pixel)
    tvdi_s3b_nadir0.append(temp)
doy_s3b_nadir0 = np.asarray(doy_s3b_nadir0, dtype=np.int16)
tvdi_s3b_nadir0 = np.asarray(tvdi_s3b_nadir0)


files = search_file(indir_tvdi,['S3B','obliq',offv])
num_files = np.size(files)
tvdi_s3b_obliq0 = []
doy_s3b_obliq0 = []
for kfile in range(num_files):
    file = files[kfile]
    infile = indir_tvdi+file
    doy = file[8:11]
    doy_s3b_obliq0.append(doy)
    [tvdi,ns,nl,nb,geog,proj] = read_image_gdal(infile)
    temp = averoff(tvdi, imagex, imagey, n_pixel)
    tvdi_s3b_obliq0.append(temp)

doy_s3b_obliq0 = np.asarray(doy_s3b_obliq0, dtype=np.int16)
tvdi_s3b_obliq0 = np.asarray(tvdi_s3b_obliq0)




pos = 1
kpos = 1
data10 = ms_site_[:,pos]
data20 = tvdi_site_adj_[:, pos]

ind = (tvdi_s3a_nadir0[:, kpos] > 0.01) *(tvdi_s3a_nadir0[:, kpos]<1.05)
doy_s3a_nadir = doy_s3a_nadir0[ind]
tvdi_s3a_nadir = tvdi_s3a_nadir0[ind, kpos]
indd = (doy_s3a_nadir > doymin) * (doy_s3a_nadir < doymax)
ind = (doy_s3a_nadir[indd] - doymin-1)
data1 = data10[ind]
data2 = data20[ind]
data3 = tvdi_s3a_nadir[indd]
inds = (data1 > 1) * (data1 < 62) * (data2 > 0.01) * (data2 < 1.05)* (data3 > 0.01) * (data3 < 1.05)


data = {'original':data3[inds],'normalized':data2[inds],'measured':data1[inds]/100.0}
# df = pd.DataFrame(data)
#
sns.set_theme(style="white")
# cmap = sns.cubehelix_palette(rot=-.1, as_cmap=True)
# g = sns.relplot(x='fVin',y='Tsl',hue='SMC',size ='LAI',palette = cmap,data = df)
# g.set(xscale="linear",yscale = "linear")
# # g.ax.xaxis.grid(True, "minor", linewidth=.25)
# # g.ax.yaxis.grid(True, "minor", linewidth=.25)
# # g.despine(left=True, bottom=True)
# g.set(xlabel ="fVin",ylabel = "Tsl")
# g.set()
# plt.show()

slope, intercept, r_value2, p_value, std_err = stats.linregress(data2[inds],data1[inds])


# kz = np.ones(np.sum(inds))
# A = np.asarray([data3[inds],kz])
# A = np.transpose(A)
# clf = Ridge(alpha=0.001, fit_intercept=False)
# clf.fit(A, data1[inds])
# x = clf.coef_

y1 = data1[inds]
ypred2 = data2[inds] * slope + intercept
# ypred2 = data2[inds] * x[0] + x[1]
dif = (y1 - ypred2)/100.0
ind = np.abs(dif) < 0.15
rmse2 = np.sqrt(np.average(dif[ind] * dif[ind]))
print(slope, intercept, r_value2, p_value, std_err, rmse2)


slope, intercept, r_value3, p_value, std_err = stats.linregress(data3[inds],data1[inds])
y1 = data1[inds]
ypred3 = data3[inds] * slope + intercept
dif = (y1 - ypred3)/100.0
ind = np.abs(dif) < 0.15
rmse3 = np.sqrt(np.average(dif[ind] * dif[ind]))
print(slope, intercept, r_value3, p_value, std_err, rmse3)

print(np.min(y1),np.max(y1))
df = pd

plt.figure(figsize=[4,3.2])
ax = sns.regplot(x=data2[inds],y=data1[inds]/100.0,ci=95,label='normalized')
ax = sns.regplot(x=data3[inds],y=data1[inds]/100.0,ci=95,label='original')
plt.legend()
# plt.ylabel('SMC ($m^3/m^3$)')
# plt.xlabel('TVDI')
plt.ylim([0.19,0.4])
plt.xlim([0.0,0.5])
plt.text(0.03,0.38,'$R_N$ = %.3f'%r_value2)
plt.text(0.03,0.36,'$R_O$ = %.3f'%r_value3)
plt.show()


plt.figure(figsize=[4.0, 3.2])
ax = plt.plot(y1/100.0, ypred2/100.0, 'ro')
ax = plt.plot(y1/100.0, ypred3/100.0, 'bo')
plt.xlim([0.15, 0.35])
plt.ylim([0.15, 0.35])
# plt.xlabel('Measured SMC ($m^3/m^3$)')
# plt.ylabel('Estimated SMC ($m^3/m^3$)')
plt.plot([0.01, 0.45], [0.01, 0.45], 'k--')
plt.legend(['Normalized','Original'])
plt.text(0.24,0.19,'$RMSE_N$ = %.3f'%rmse2)
plt.text(0.24,0.17,'$RMSE_O$ = %.3f'%rmse3)
plt.tight_layout()
plt.show()

ind = (tvdi_s3b_nadir0[:, kpos] > 0.01)*(tvdi_s3b_nadir0[:, kpos]<1.05)
doy_s3b_nadir = doy_s3b_nadir0[ind]
tvdi_s3b_nadir = tvdi_s3b_nadir0[ind, kpos]
indd = (doy_s3b_nadir > doymin) * (doy_s3b_nadir < doymax)
ind = (doy_s3b_nadir[indd] - doymin-1)
data11 = data10[ind]
data22 = data20[ind]
data33 = tvdi_s3b_nadir[indd]
indss = (data11 > 1) * (data11 < 62) * (data22 > 0.01) * (data22 < 1.05) * (data33 > 0.01) * (data33 < 1.05)
slope, intercept, r_value22, p_value, std_err = stats.linregress(data22[indss],data11[indss])
y11 = data11[indss]
ypred22 = data22[indss] * slope + intercept
dif = (y11 - ypred22)/100.0
ind = np.abs(dif) < 0.15
rmse22 = np.sqrt(np.average(dif[ind] * dif[ind]))
print(slope, intercept, r_value22, p_value, std_err, rmse22)
slope, intercept, r_value33, p_value, std_err = stats.linregress(data33[indss],data11[indss])
y11 = data11[indss]
ypred33 = data33[indss] * slope + intercept
dif = (y11 - ypred33)/100.0
ind = np.abs(dif) < 0.15
rmse33 = np.sqrt(np.average(dif[ind] * dif[ind]))
print(slope, intercept, r_value33, p_value, std_err, rmse33)
print(np.min(y11),np.max(y11))


plt.figure(figsize=[4,3.2])
ax = sns.regplot(x=data22[indss],y=data11[indss]/100.0,ci=95,label='normalized')
ax = sns.regplot(x=data33[indss],y=data11[indss]/100.0,ci=95,label='original')
plt.legend()
# plt.ylabel('SMC ($m^3/m^3$)')
# plt.xlabel('TVDI')
plt.ylim([0.19,0.4])
plt.xlim([0.0,0.5])
plt.text(0.03,0.38,'$R_N$ = %.3f'%r_value22)
plt.text(0.03,0.36,'$R_O$ = %.3f'%r_value33)
plt.show()

plt.figure(figsize=[4.0, 3.2])
ax = plt.plot(y11/100.0, ypred22/100.0, 'ro')
ax = plt.plot(y11/100.0, ypred33/100.0, 'bo')
plt.xlim([0.15, 0.35])
plt.ylim([0.15, 0.35])
# plt.xlabel('Measured SMC ($m^3/m^3$)')
# plt.ylabel('Estimated SMC ($m^3/m^3$)')
plt.plot([0.01, 0.45], [0.01, 0.45], 'k--')
plt.legend(['Normalized','Original'])
plt.text(0.24,0.19,'$RMSE_N$ = %.3f'%rmse22)
plt.text(0.24,0.17,'$RMSE_O$ = %.3f'%rmse33)
plt.tight_layout()
plt.show()

print( ' s3a: ', np.sum(inds),  ' s3b: ', np.sum(indss))

# data13 = np.hstack([data1[inds],data11[indss]])
# data23 = np.hstack([data2[inds],data22[indss]])
# data33 = np.hstack([data3[inds],data33[indss]])
# ax = sns.regplot(data13,data23,ci=95)
# ax = sns.regplot(data13,data33,ci=95)
# plt.legend(['original','normalized'])
# plt.xlabel('SMC')
# plt.ylabel('TVDI')
# plt.xlim([18,38])
# plt.ylim([0.0,0.5])
# plt.show()
#
# rr = np.corrcoef(data13, data23)
# r2 = rr[1, 0] * rr[1, 0]
# rr = np.corrcoef(data13, data33)
# r23 = rr[1, 0] * rr[1, 0]
# print(np.sum(indss)+np.sum(inds), r2, r23)

pos = 2
kpos = 2
data10 = ms_site_[:,pos]
data20 = tvdi_site_adj_[:, pos]

ind = (tvdi_s3a_nadir0[:, kpos] > 0.01) *(tvdi_s3a_nadir0[:, kpos]<1.05)
doy_s3a_nadir = doy_s3a_nadir0[ind]
tvdi_s3a_nadir = tvdi_s3a_nadir0[ind, kpos]
indd = (doy_s3a_nadir > doymin) * (doy_s3a_nadir < doymax)
ind = (doy_s3a_nadir[indd] - doymin-1)
data1 = data10[ind]
data2 = data20[ind]
data3 = tvdi_s3a_nadir[indd]
inds = (data1 > 1) * (data1 < 62) * (data2 > 0.01) * (data2 < 1.05)* (data3 > 0.01) * (data3 < 1.05)
slope, intercept, r_value2, p_value, std_err = stats.linregress(data2[inds],data1[inds])
y1 = data1[inds]
ypred2 = data2[inds] * slope + intercept
dif = (y1 - ypred2)/100.0
ind = np.abs(dif) < 0.15
rmse2 = np.sqrt(np.average(dif[ind] * dif[ind]))
print(slope, intercept, r_value2, p_value, std_err, rmse2)
slope, intercept, r_value3, p_value, std_err = stats.linregress(data3[inds],data1[inds])
y1 = data1[inds]
ypred3 = data3[inds] * slope + intercept
dif = (y1 - ypred3)/100.0
ind = np.abs(dif) < 0.15
rmse3 = np.sqrt(np.average(dif[ind] * dif[ind]))
print(slope, intercept, r_value3, p_value, std_err, rmse3)
print(np.min(y1),np.max(y1))

plt.figure(figsize=[4,3.2])
ax = sns.regplot(x=data2[inds],y=data1[inds]/100.0,ci=95,label='normalized')
ax = sns.regplot(x=data3[inds],y=data1[inds]/100.0,ci=95,label='original')
plt.legend()
# plt.ylabel('SMC ($m^3/m^3$)')
# plt.xlabel('TVDI')
plt.text(0.12,0.055,'$R_N$ = %.3f'%r_value2)
plt.text(0.12,0.035,'$R_O$ = %.3f'%r_value3)
plt.ylim([0.02,0.20])
plt.xlim([0.0,1.0])
plt.show()

plt.figure(figsize=[4.0, 3.2])
ax = plt.plot(y1/100.0, ypred2/100.0, 'ro')
ax = plt.plot(y1/100.0, ypred3/100.0, 'bo')
plt.xlim([0.01, 0.25])
plt.ylim([0.01, 0.25])
# plt.xlabel('Measured SMC ($m^3/m^3$)')
# plt.ylabel('Estimated SMC ($m^3/m^3$)')
plt.plot([0.01, 0.45], [0.01, 0.45], 'k--')
plt.legend(['Normalized','Original'])
plt.text(0.12,0.05,'$RMSE_N$ = %.3f'%rmse2)
plt.text(0.12,0.03,'$RMSE_O$ = %.3f'%rmse3)
plt.tight_layout()
plt.show()


ind = (tvdi_s3b_nadir0[:, kpos] > 0.01)*(tvdi_s3b_nadir0[:, kpos]<1.05)
doy_s3b_nadir = doy_s3b_nadir0[ind]
tvdi_s3b_nadir = tvdi_s3b_nadir0[ind, kpos]
indd = (doy_s3b_nadir > doymin) * (doy_s3b_nadir < doymax)
ind = (doy_s3b_nadir[indd] - doymin-1)
data11 = data10[ind]
data22 = data20[ind]
data33 = tvdi_s3b_nadir[indd]
indss = (data11 > 1) * (data11 < 62) * (data22 > 0.01) * (data22 < 1.05) * (data33 > 0.01) * (data33 < 1.05)
slope, intercept, r_value22, p_value, std_err = stats.linregress(data22[indss],data11[indss])
y11 = data11[indss]
ypred22 = data22[indss] * slope + intercept
dif = (y11 - ypred22)/100.0
ind = np.abs(dif) < 0.25
rmse22 = np.sqrt(np.average(dif[ind] * dif[ind]))
print(slope, intercept, r_value22, p_value, std_err, rmse22)
slope, intercept, r_value33, p_value, std_err = stats.linregress(data33[indss],data11[indss])
y11 = data11[indss]
ypred33 = data33[indss] * slope + intercept
dif = (y11 - ypred33)/100.0
ind = np.abs(dif) < 0.25
rmse33 = np.sqrt(np.average(dif[ind] * dif[ind]))
print(slope, intercept, r_value33, p_value, std_err, rmse33)
print(np.min(y11),np.max(y11))


plt.figure(figsize=[4,3.2])
ax = sns.regplot(x=data22[indss],y=data11[indss]/100.0,ci=95,label='normalized')
ax = sns.regplot(x=data33[indss],y=data11[indss]/100.0,ci=95,label='original')
plt.legend()
# plt.ylabel('SMC ($m^3/m^3$)')
# plt.xlabel('TVDI')
plt.text(0.12,0.055,'$R_N$ = %.3f'%r_value22)
plt.text(0.12,0.035,'$R_O$ = %.3f'%r_value33)
plt.ylim([0.02,0.20])
plt.xlim([0.0,1.0])
plt.show()

plt.figure(figsize=[4.0, 3.2])
ax = plt.plot(y11/100.0, ypred22/100.0, 'ro')
ax = plt.plot(y11/100.0, ypred33/100.0, 'bo')
plt.xlim([0.01, 0.25])
plt.ylim([0.01, 0.25])
# plt.xlabel('Measured SMC ($m^3/m^3$)')
# plt.ylabel('Estimated SMC ($m^3/m^3$)')
plt.plot([0.01, 0.45], [0.01, 0.45], 'k--')
plt.legend(['Normalized','Original'])
plt.text(0.12,0.05,'$RMSE_N$ = %.3f'%rmse22)
plt.text(0.12,0.03,'$RMSE_O$ = %.3f'%rmse33)
plt.tight_layout()
plt.show()

# data13 = np.hstack([data1[inds],data11[indss]])
# data23 = np.hstack([data2[inds],data22[indss]])
# data33 = np.hstack([data3[inds],data33[indss]])
# ax = sns.regplot(data13,data23,ci=95)
# ax = sns.regplot(data13,data33,ci=95)
# plt.legend(['original','normalized'])
# plt.xlabel('SMC')
# plt.ylabel('TVDI')
# plt.xlim([3,20])
# plt.ylim([0.0,1.0])
# plt.show()
#
# rr = np.corrcoef(data13, data23)
# r2 = rr[1, 0] * rr[1, 0]
# rr = np.corrcoef(data13, data33)
# r23 = rr[1, 0] * rr[1, 0]
# print(np.sum(indss)+np.sum(inds), r2, r23)