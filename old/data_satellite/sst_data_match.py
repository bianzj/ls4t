import gdal
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde
from util.util import *
import warnings
warnings.filterwarnings("ignore")

os.environ['PROJ_LIB'] = r'C:\Users\Y\anaconda3\envs\python37\Lib\site-packages\osgeo\data\proj'
os.environ['GDAL_DATA'] = r'C:\Users\Y\anaconda3\envs\python37\Lib\site-packages\osgeo\data\gdal'
os.environ['PYTHONIOENCODING'] = 'utf-8'
plt.rc('font', family='Times New Roman')

'''2023.12.23'''
'''MODIS 与 GF 交叉验证（1000M）'''

def cal_rmse_r2(data1,data2,tshred=5):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2

def density_scatter( x , y,  ax = None, is_cbar=False, **kwargs ) :
    if ax is None :
        fig , ax = plt.subplots()
    xy = np.vstack([x,y])
    z = gaussian_kde(xy)(xy)
    idx = z.argsort()
    x, y, z = x[idx], y[idx], z[idx]
    ax.scatter(x, y,c=z,cmap='Spectral_r',s=2)
    if is_cbar:
        norm = Normalize(vmin = np.min(z), vmax = np.max(z))
        cbar = plt.colorbar(cm.ScalarMappable(norm = norm,cmap='Spectral_r'), ax=ax)
        cbar.ax.set_ylabel('Density')

    return ax



indir_GF = r"D:\data\other\SST\GF\\"
indir_GF_1km = r"D:\data\other\SST\GF_1000\\"
outdir_out = r"D:\data\other\SST\MODIS\out\\"
mkdir_if_not_exist(indir_GF_1km)
mkdir_if_not_exist(outdir_out)

fileNames = search_file_rej(indir_GF_1km, ['.tif'],'enp')
fileNum = len(fileNames)


GF = []
Modis = []
dif_threshold = 5
print("threshold:%02d" % dif_threshold)
for fileName in fileNames:
    infile = indir_GF_1km + fileName
    time_str = fileName[23:31]
    print(time_str)
    monthday = time_str[4:8]
    [data_GF, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile)

    fileNames_mod = search_file_rej(outdir_out, [time_str], 'enp')
    for fileName_mod in fileNames_mod:
        outfile_mod = outdir_out + fileName_mod
        [data_mod, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile_mod)
        if temp1!=ns:
            print("Not match!")
            continue
        ind = (np.abs(data_mod - data_GF) < dif_threshold) * (data_GF<340)*(data_GF>250)
        if sum(ind)==0:
            print("No data avilable!")
            continue

        fig = plt.figure(figsize=[4.5, 4], dpi=300)
        plt.plot(data_mod[ind], data_GF[ind], 'bo')

        min = np.min(data_GF[ind])
        max = np.max(data_mod[ind])

        plt.plot([min-10, max+10], [min-10, max+10], 'k--')
        plt.xlabel('Modis SST/K')
        plt.ylabel('GF SST/K')
        plt.legend(['SST'])
        plt.title(time_str)
        save_fig = r'D:\data\other\SST\Cross Validation\\thresold_%02d\\' % dif_threshold + time_str +".png"
        plt.savefig(save_fig)
        plt.show()

        bias, rmse, r2 = cal_rmse_r2(data_mod[ind], data_GF[ind], dif_threshold)
        print("num:%04d" % sum(ind))
        print("bias:%.2f,r2:%.3f,rmse:%.2f" % (bias,r2[0],rmse))

        GF_data_save = np.zeros([100,100])
        mod_data_save = np.zeros([100,100])
        GF_data_save[:nl,:ns]=data_GF
        mod_data_save[:nl, :ns] = data_mod

        GF.append(np.reshape(GF_data_save,(1,-1)))
        Modis.append(np.reshape(mod_data_save,(1,-1)))

GF = np.array(GF)
Modis = np.array(Modis)
ind = (np.abs(Modis - GF) < dif_threshold) * (GF<340)*(GF>250)

fig = plt.figure(figsize=[4.5, 4], dpi=300)
ax = fig.add_subplot(111)
density_scatter(x=Modis[ind],y=GF[ind],ax=ax,is_cbar=False)
plt.plot([250, 340], [250, 340], 'k--',label='1:1 line')
plt.xlabel('Modis SST/K')
plt.ylabel('GF SST/K')
plt.legend()
plt.title('Corss Validation')
save_fig = r'D:\data\other\SST\Cross Validation\\thresold_%02d\\overall_acuracy_%02d.png' % (dif_threshold,dif_threshold)
plt.savefig(save_fig)
plt.show()

print("Overall accuracy:")
print("num:%04d" % sum(ind))
bias, rmse, r2 = cal_rmse_r2(GF[ind], Modis[ind], dif_threshold)
print("bias:%.2f,r2:%.3f,rmse:%.2f" % (bias, r2[0], rmse))