import mpl_scatter_density
from utils.old.util import *

def cal_rmse_r2(data1,data2,tshred=10):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2

def plot_taylor_diagram(ref, model, title='Taylor Diagram'):
    """
    Plot Taylor diagram.
    :param ref: Reference dataset
    :param model: Model dataset
    :param title: Title of the plot
    """
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='polar')

    # 计算标准偏差和相关系数
    std_model = np.std(model)
    std_ref = np.std(ref)
    correlation = np.corrcoef(ref, model)[0, 1]

    # 计算Taylor图上的点坐标
    theta = np.arccos(correlation)
    r = std_model / std_ref

    # 画参考线和点
    ax.plot([0, theta], [0, r], marker='o', markersize=10, color='b', label='Model')
    ax.plot([0, np.pi], [0, 1], linestyle='--', color='k', label='Reference')

    # 设置图形属性
    ax.set_ylim(0, 2)
    ax.set_yticklabels([])
    ax.set_xticklabels(['', '0.2', '0.4', '0.6', '0.8', '1.0'])

    # 添加标题和图例
    plt.title(title, va='bottom')
    plt.legend(loc='upper right')

    plt.show()

'''2009年1月和7月土壤温度和平均温度散点图'''

indir_ERA5_utc11 = r"E:\ERA5_land_2002-2012\Monthly_Average_Hour\tif_loc_11\\"
indir_ERA5_loc11 = r"E:\ERA5_land_2002-2012\Monthly_Average_Hour\tif_utc_11\\"
indir_ERA5_day = r"E:\ERA5_land_2002-2012\Monthly_Average_Day\tif\\"
indir_ERA5 = indir_ERA5_loc11
indir_AATSR = r"E:\AATSR\\"

r2 = []
rmse = []
for year in range(2009,2010):
    for month in range(1,13):
        infile_ERA5 = indir_ERA5 + "%04d\\ERA5_land_%04d%02d.tif" %(year,year,month)

        infile_AATSR = indir_AATSR + r"%04d\lsct_month\%02d\\" % (year,month)
        infile_ts = infile_AATSR + "AATSR_%04d_%02d_lsct_s.tif" % (year,month)
        infile_tv = infile_AATSR + "AATSR_%04d_%02d_lsct_v.tif" % (year, month)
        infile_lst = infile_AATSR + "AATSR_%04d_%02d_lst_n.tif" % (year, month)

        '''读取'''
        [Ts, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_ts)
        [T_ERA5, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile_ERA5)
        [Tv, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_tv)
        [lst, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lst)
        Ts = lst
        T_era = np.zeros([1800,3600])
        Ts_era = T_ERA5[1,:1800,:]
        Ts = resize_data(Ts,nl-1,ns)
        x = Ts.reshape(-1)/100
        y = Ts_era.reshape(-1)/100
        ind = x == 0
        y[ind] = 0


        '''画图'''
        '''定义colormap和字体'''
        from matplotlib.colors import ListedColormap
        Spectral_r = mpl.cm.get_cmap('Spectral_r', 256)
        newcolors = Spectral_r(np.linspace(0, 1, 256))
        white = np.array([256 / 256, 256 / 256, 256 / 256, 1])
        newcolors[:2, :] = white
        newcmp = ListedColormap(newcolors)
        plt.rc('font', family='Times New Roman')

        '''定义图'''
        msk = (x>240) * (x < 360)
        fig = plt.figure(figsize = (6,5))
        ax = fig.add_subplot(1, 1, 1, projection='scatter_density')
        density = ax.scatter_density(x[msk], y[msk], cmap=newcmp)
        tem_min = 250
        tem_max = 330
        ax.set_xlim(tem_min, tem_max)
        ax.set_ylim(tem_min, tem_max)
        fig.colorbar(density, label='Number of points per pixel')
        ax.plot((0, 1), (0, 1), transform=ax.transAxes, ls='--', c='k', label="1:1 line")
        plt.title("%04d%02d" % (year,month))
        plt.xlabel("Ts_inv /k")
        plt.ylabel("Ts level1 /k")
        # a, b = np.polyfit(x[msk], y[msk], deg=1)
        # print(a, b)
        # x_ = np.linspace(250, 350, 5)
        # y_ = x_ * a + b
        # plt.plot(x_, y_, ls='-', c='b', label="y = %.6f x + %.6f" % (a, b))
        plt.legend()
        # plt.show()

        dif_threshold = 10
        bias_tss, rmse_tss, r2_tss = cal_rmse_r2(x[msk], y[msk], dif_threshold)
        print("%04d%02d" % (year, month))
        print("bias,r2,rmse:%.2f,%.3f,%.2f" % (bias_tss,r2_tss[0],rmse_tss))
        rmse.append(rmse_tss)
        r2.append(r2)

rmse = np.array(rmse)
r2 = np.array(r2)

