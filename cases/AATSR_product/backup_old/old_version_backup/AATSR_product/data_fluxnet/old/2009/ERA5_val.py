from utils.old.util import *
from scipy.stats import gaussian_kde

'''2024.3.18'''
'''脚本用于验证'''

val_dir = r"D:\data\AATSR_product\Fluxnet2015\Validation_csv_ERA5\\"
graph_dir = r"D:\data\AATSR_product\Fluxnet2015\graph\ERA5_LSCT\\"

ifval = 1

def cal_rmse_r2(data1,data2,tshred=10):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2

if ifval:
    fileNames = search_file(val_dir, ['.csv'])
    therhold = 10
    alldata = []
    for fileName in fileNames:
        infile = val_dir + fileName
        data = pd.read_csv(infile)
        alldata.append(data)
        ts_inv = data['Ts']
        tv_inv = data['Tv']
        ts_mea = data['TS_F_MDS_1']
        ta_mea = data['TA_F_MDS']
        lst_mea = data['lst']
        ts_era5 = data['stl1_era5']
        ta_era5 = data['t2m_era5']
        lst_era5 = data['skt_era5']
        invalid_num = sum(np.abs(ts_mea - ts_era5) < 10)
        print("--------------------------------------------------------------------------------")
        print(fileName)
        print("有效点数：%03d" % invalid_num)
        if invalid_num == 0:
            continue
        ind_s = np.abs(ts_mea - ts_inv) < 10
        ind_v = np.abs(ta_mea - ts_inv) < 10
        inv_l = np.abs(lst_mea - lst_era5) < 10
        bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea[ind_s], ts_era5[ind_s], therhold)
        bias_v, rmse_v, r2_v = cal_rmse_r2(ta_mea[ind_v], ta_era5[ind_v], therhold)
        bias_l, rmse_l, r2_l = cal_rmse_r2(lst_mea[ind_v], lst_era5[ind_v], therhold)
        print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s[0]))
        print("植被 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))
        print("LST RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_l, bias_l, r2_l[0]))

        # 绘制散点图
        ind = (ts_mea > 220) * (ts_mea < 370) * (ts_inv > 220) * (ts_inv < 370) * (ts_inv != 273.15)
        plt.figure(figsize=(6, 6))
        plt.scatter(ts_mea[ind], ts_era5[ind], label='Soil', color='red')
        plt.scatter(ta_mea[ind], ta_era5[ind], label='Vegetation', color='green')
        plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
        plt.plot([220, 370], [215, 365], color='grey', linestyle='--')  # 添加y=x-5线
        plt.plot([220, 370], [225, 375], color='grey', linestyle='--')  # 添加y=x+5线
        plt.plot([220, 370], [210, 360], color='grey', linestyle='--')  # 添加y=x-10线
        plt.plot([220, 370], [230, 380], color='grey', linestyle='--')  # 添加y=x+10线
        plt.xlabel('Measured')
        plt.ylabel('Inversion')
        plt.title(fileName[:-4])
        plt.legend()

        # 保存图表
        output_path = graph_dir + fileName[:-4] + ".png"
        plt.savefig(output_path)
        plt.close()

    print("--------------------------------------------------------------------------------")
    print("ALL SITES")
    all_data_concatenated = pd.concat(alldata)
    ts_inv = all_data_concatenated['Ts']
    tv_inv = all_data_concatenated['Tv']
    ts_mea = all_data_concatenated['TS_F_MDS_1']
    ta_mea = all_data_concatenated['TA_F_MDS']
    ts_era5 = all_data_concatenated['stl1_era5']
    ta_era5 = all_data_concatenated['t2m_era5']
    invalid_num = sum(np.abs(ts_mea - ts_era5) < 10)
    print("有效点数：%03d" % invalid_num)
    ind_s = np.abs(ts_mea - ts_inv) < 10
    ind_v = np.abs(ta_mea - ts_inv) < 10
    ind_l = np.abs(lst_mea - lst_era5) < 10
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea[ind_s], ts_era5[ind_s], therhold)
    bias_v, rmse_v, r2_v = cal_rmse_r2(ta_mea[ind_v], ta_era5[ind_v], therhold)
    bias_l, rmse_l, r2_l = cal_rmse_r2(lst_mea[ind_v], lst_era5[ind_v], therhold)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s[0]))
    print("植被 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))
    print("LST RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_l, bias_l, r2_l[0]))
    # 绘制散点图
    ind = (ts_mea > 220) * (ts_mea < 370) * (ts_inv > 220) * (ts_inv < 370) * (ts_inv != 273.15)

    print("--------------------------------------------------------------------------------")
    print("土壤温度散点密度图")
    # Calculate the point density for soil temperature
    xy_soil = np.vstack([ts_mea[ind], ts_era5[ind]])
    z_soil = gaussian_kde(xy_soil)(xy_soil)

    # Sort the points by density, so that the densest points are plotted last
    idx_soil = z_soil.argsort()
    ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind].iloc[idx_soil], ts_era5[ind].iloc[idx_soil], z_soil[idx_soil]

    plt.figure(figsize=(8, 6))
    sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured Soil Temperature')
    plt.ylabel('Inverted Soil Temperature')
    plt.title("Density Scatter Plot of Soil Temperature")
    output_path = graph_dir + "ALL_SITES_Soil_Temperature_Scatter_Density.png"
    plt.savefig(output_path)
    plt.close()

    print("--------------------------------------------------------------------------------")
    print("植被温度散点密度图")
    # Calculate the point density for vegetation temperature
    # Calculate the point density for vegetation temperature
    xy_vegetation = np.vstack([ta_mea[ind], ta_era5[ind]])
    z_vegetation = gaussian_kde(xy_vegetation)(xy_vegetation)

    # Sort the points by density, so that the densest points are plotted last
    idx_vegetation = z_vegetation.argsort()
    ta_mea_vegetation, tv_inv_vegetation, z_vegetation = ta_mea[ind].iloc[idx_vegetation], ta_era5[ind].iloc[
        idx_vegetation], z_vegetation[idx_vegetation]

    plt.figure(figsize=(8, 6))
    sc = plt.scatter(ta_mea_vegetation, tv_inv_vegetation, c=z_vegetation, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured Vegetation Temperature')
    plt.ylabel('Inverted Vegetation Temperature')
    plt.title("Density Scatter Plot of Vegetation Temperature")
    output_path = graph_dir + "ALL_SITES_Vegetation_Temperature_Scatter_Density.png"
    plt.savefig(output_path)
    plt.close()

    print("散点密度图已保存到", r"D:\data\AATSR_product\Fluxnet2015\graph 文件夹中")