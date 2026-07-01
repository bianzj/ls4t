from utils.old.util import *
import matplotlib.pyplot as plt
from multiprocessing import Pool, freeze_support

'''脚本用于计算整图的相关系数'''

def cal_rmse_r2(data1,data2,tshred=10):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2

'''2009年1月和7月土壤温度和平均温度散点图'''

indir_ERA5_utc11 = r"E:\ERA5_land_2002-2012\Monthly_Average_Hour\tif_loc_11\\"
indir_ERA5_loc11 = r"E:\ERA5_land_2002-2012\Monthly_Average_Hour\tif_utc_11\\"
indir_ERA5_day = r"E:\ERA5_land_2002-2012\Monthly_Average_Day\tif\\"
indir_ERA5 = indir_ERA5_loc11
indir_AATSR = r"E:\AATSR\\"

Ts_inv_ = []
Ts_era_ = []
num_ = 0

for year in range(2009,2013):
    for month in range(1,13):
        print(year,month)
        infile_ERA5 = indir_ERA5 + "%04d\\ERA5_land_%04d%02d.tif" %(year,year,month)

        infile_AATSR = indir_AATSR + r"%04d\lsct_month\%02d\\" % (year,month)
        infile_ts = infile_AATSR + "AATSR_%04d_%02d_lsct_s.tif" % (year,month)
        infile_tv = infile_AATSR + "AATSR_%04d_%02d_lsct_v.tif" % (year, month)

        if not os.path.exists(infile_ts):
            print("lack inv!")
            continue

        '''读取'''
        [Ts, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_ts)
        [T_ERA5, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile_ERA5)
        # [Tv, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_tv)
        T_era = np.zeros([1800,3600])
        Ts_era = T_ERA5[1,:1800,:]
        Ts = resize_data(Ts,nl-1,ns)
        x = Ts.reshape(-1)/100
        y = Ts_era.reshape(-1)/100
        ind = x == 0
        y[ind] = 0
        ind = y==0
        x[ind] = 0
        Ts_inv_.append(x)
        Ts_era_.append(y)
        num_ = num_+1

Ts_inv_ = np.reshape(Ts_inv_,[num_,1800,3600])
Ts_era_ = np.reshape(Ts_era_,[num_,1800,3600])

'''计算相关系数'''
tshred = 10
dif = (Ts_inv_-Ts_era_)
ind = np.abs(dif)<tshred

# 将数据集展平以便于向量化操作
flat_data_set1 = Ts_inv_.reshape((num_, -1))
flat_data_set2 = Ts_era_.reshape((num_, -1))

correlation_coefficients = np.zeros((flat_data_set1.shape[1],))

# 定义函数以计算相关系数
def calculate_correlation(i):
    pixel_set1 = flat_data_set1[:, i]
    pixel_set2 = flat_data_set2[:, i]

    if np.any(np.isnan(pixel_set1)) or np.any(np.isnan(pixel_set2)):
        return np.nan
    else:
        ind = (pixel_set1!=0) * (pixel_set2!=0) * (np.abs(pixel_set1-pixel_set2)<15)
        return np.corrcoef(pixel_set1[ind], pixel_set2[ind])[0, 1]

if __name__ == '__main__':
    # 在 Windows 上使用 multiprocessing 时需要加上 freeze_support()
    freeze_support()

    # 使用多进程计算相关系数
    with Pool() as pool:
        correlation_coefficients = pool.map(calculate_correlation, range(flat_data_set1.shape[1]))

    # 将相关系数重塑回图像大小
    correlation_coefficients = np.array(correlation_coefficients).reshape((1800, 3600))

    # 绘制相关系数图
    plt.rc('font', family='Times New Roman')
    plt.imshow(correlation_coefficients, cmap='viridis')
    plt.colorbar()
    plt.title('Correlation Coefficient Map')
    plt.show()
    coff_save = np.zeros([nl,ns])
    coff_save[0:-1,:]=correlation_coefficients
    outfile = indir_AATSR + r"\\cor.tif"
    write_image_gdal(coff_save, ns, nl, 1, geog_type, proj_type,outfile)
