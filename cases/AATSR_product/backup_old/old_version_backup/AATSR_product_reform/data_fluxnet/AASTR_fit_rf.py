from utils.old.util import *
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

'''2024.1.14'''
'''RF 用于fit'''

# 改这里
lsct_name = "4_lsct2_h5_2002-2012"

base_dir = r"/home/hero/data/AATSR/Sites/Fluxnet/"
fluxnet_loc_file = base_dir + r"Fluxnet_data/"
fluxnet_filter_dir = base_dir + r"Fluxnet_data/Fluxnet_csv_2002-2012/"
h5_dir = base_dir + r"AATSR_data/" + lsct_name + r'/'
csv_dir = base_dir + r"Validation/" + lsct_name + r"/AATSR_csv/"
val_dir = base_dir + r"Validation/" + lsct_name + r"/Merge_csv/"

def cal_rmse_r2(data1,data2,tshred = 10):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2

if_fit_rf= 1

pass_site = ['BR-Sa3','GF-Guy','MY-PSO','AU-Wac','US-Syv']

daynight = 'day'

if daynight == 'day':
    start_time = '08:00'
    end_time = '18:00'
    time_min = pd.to_datetime(start_time).time()
    time_max = pd.to_datetime(end_time).time()
elif daynight =='night':
    start_time = '18:00'
    end_time = '8:00'
    time_min = pd.to_datetime(start_time).time()
    time_max = pd.to_datetime(end_time).time()

plt.rc('font', family='Times New Roman', size=12)

if if_fit_rf:
    lsct_fit_out_dir = base_dir + r"Validation/" + lsct_name + r"/val_AATST_LSCT-Fluxnet_LSCT_RFfit/"
    mkdir_if_not_exist(lsct_fit_out_dir)

    fileNames = search_file(val_dir, ['.csv'])
    fileNames_train = fileNames[10:]
    fileNames_test = fileNames[:10]
    fileNum = len(fileNames_train)
    print(fileNum)
    threshold = 9
    alldata = []
    for fileName in fileNames_train:
        if fileName[:-4] in pass_site: continue
        infile = val_dir + fileName
        data = pd.read_csv(infile)
        data['Local_Time'] = pd.to_datetime(data['Local_Time'])
        if daynight == 'day':
            mask = (data['Local_Time'].dt.time >= time_min) & (
                    data['Local_Time'].dt.time <= time_max)
        elif daynight == 'night':
            mask = (data['Local_Time'].dt.time >= time_min) + (
                    data['Local_Time'].dt.time <= time_max)
        filtered_data = data[mask]
        alldata.append(filtered_data)

    print("--------------------------------------------------------------------------------")
    print("Fit")
    all_data_concatenated = pd.concat(alldata)
    ts_inv = all_data_concatenated['Ts2']
    tv_inv = all_data_concatenated['Tv2']
    lstN_inv = all_data_concatenated['lstN']
    ts_mea = all_data_concatenated['TS_F_MDS_1']
    lst_mea = all_data_concatenated['lst']
    ta_mea = all_data_concatenated['TA_F_MDS']
    lai = all_data_concatenated['MCD15A3H_061_Lai_500m']
    swc = all_data_concatenated['SWC_F_MDS_1']
    local_time = all_data_concatenated['Local_Time']
    doy = local_time.dt.dayofyear
    hours_float = local_time.dt.hour + local_time.dt.minute / 60 + local_time.dt.second / 3600
    invalid_num = sum(np.abs(ts_mea - ts_inv) < threshold)
    print('Before fit:')
    print("有效点数：%03d" % invalid_num)
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea, ts_inv, threshold)
    bias_v, rmse_v, r2_v = cal_rmse_r2(ta_mea, tv_inv, threshold)
    bias_f, rmse_f, r2_f = cal_rmse_r2(lst_mea, ts_mea, threshold)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s[0]))
    print("植被 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))
    print("Fluxnet Ts lst RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_f, bias_f, r2_f[0]))

    # # 绘制散点图
    # ind_plot = (ts_mea > 230) * (ts_mea < 370) * (ts_inv > 230) * (ts_inv < 370) * (ts_inv != 273.15)
    #
    # xy_soil = np.vstack([ts_mea[ind_plot], ts_inv[ind_plot]])
    # z_soil = gaussian_kde(xy_soil)(xy_soil)
    # # Sort the points by density, so that the densest points are plotted last
    # idx_soil = z_soil.argsort()
    # ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind_plot].iloc[idx_soil], ts_inv[ind_plot].iloc[idx_soil], z_soil[
    #     idx_soil]
    #
    # plt.figure(figsize=(5, 4))
    # sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    # plt.colorbar(sc)
    # plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    # plt.xlabel('Measured Soil Temperature')
    # plt.ylabel('Inverted Soil Temperature')
    # ax = plt.gca()
    # ax.text(0.99, 0.02,
    #         f"num = {invalid_num:d} \nr2={r2_s[0]:.2f} \nBias={bias_s:.2f} K\nRMSE={rmse_s:.2f} K",
    #         fontsize=16, ha='right', va='bottom', transform=ax.transAxes)  # 第三行
    # # plt.title("Density Scatter Plot of Soil Temperature")
    # plt.ylim([230, 340])
    # plt.xlim([230, 340])
    # plt.tight_layout()
    # output_path = lsct_fit_out_dir + daynight + '/' + "ALL_SITES_ori_Scatter_Density.png"
    # mkdir_if_not_exist(lsct_fit_out_dir + daynight + '/')
    # plt.savefig(output_path)
    # plt.show()
    # plt.close()
    ts_inv_ = ts_inv

    fit_limit = 30

    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split

    '''
    Fit ts_mea with ts_inv / lai / swc using Random Forest
    '''
    ts_inv = ts_inv_
    print("\nFit with Ts_inv and lai / swc using Random Forest:")

    # 筛选符合条件的样本
    ind = (np.abs(ts_inv - ts_mea) < fit_limit) & (~lai.isna()) & (lai > 0) & (~swc.isna()) & (swc > 0)

    X = np.vstack([
        ts_inv[ind],
        lstN_inv[ind],
        lai[ind],
        swc[ind],
        doy[ind],
        hours_float[ind],
    ]).T

    y = ts_mea[ind]

    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=100)
    #
    # 初始化随机森林回归模型
    model = RandomForestRegressor(n_estimators=1000, random_state=100)

    # 训练模型
    model.fit(X_train, y_train)

    # 输出特征重要性
    print("\nFeature importances:", model.feature_importances_)

    # 在测试集上预测
    y_pred_test = model.predict(X_test)

    # 打印测试集性能
    bias_test, rmse_test, r2_test = cal_rmse_r2(y_test, y_pred_test, threshold)
    print("\nRandom Forest Regression Results (Test Set):")
    print(f"RMSE: {rmse_test:.3f}, Bias: {bias_test:.3f}, R²: {r2_test[0]:.3f}")

    # # 可选：打印训练集性能（用于检查是否过拟合）
    # y_pred_train = model.predict(X_train)
    # bias_train, rmse_train, r2_train = cal_rmse_r2(y_train, y_pred_train, threshold)
    # print("\nRandom Forest Regression Results (Train Set):")
    # print(f"RMSE: {rmse_train:.3f}, Bias: {bias_train:.3f}, R²: {r2_train[0]:.3f}")

    '''不同fileName'''
    alldata = []
    for fileName in fileNames_test:
        if fileName[:-4] in pass_site: continue
        infile = val_dir + fileName
        data = pd.read_csv(infile)
        data['Local_Time'] = pd.to_datetime(data['Local_Time'])
        if daynight == 'day':
            mask = (data['Local_Time'].dt.time >= time_min) & (
                    data['Local_Time'].dt.time <= time_max)
        elif daynight == 'night':
            mask = (data['Local_Time'].dt.time >= time_min) + (
                    data['Local_Time'].dt.time <= time_max)
        filtered_data = data[mask]
        alldata.append(filtered_data)
    all_data_concatenated = pd.concat(alldata)
    ts_inv = all_data_concatenated['Ts2']
    lstN_inv = all_data_concatenated['lstN']
    tv_inv = all_data_concatenated['Tv2']
    ts_mea = all_data_concatenated['TS_F_MDS_1']
    lst_mea = all_data_concatenated['lst']
    ta_mea = all_data_concatenated['TA_F_MDS']
    lai = all_data_concatenated['MCD15A3H_061_Lai_500m']
    swc = all_data_concatenated['SWC_F_MDS_1']
    local_time = all_data_concatenated['Local_Time']
    doy = local_time.dt.dayofyear
    hours_float = local_time.dt.hour + local_time.dt.minute / 60 + local_time.dt.second / 3600

    # 筛选符合条件的样本
    ind = (np.abs(ts_inv - ts_mea) < fit_limit) & (~lai.isna()) & (lai > 0) & (~swc.isna()) & (swc > 0)

    X = np.vstack([
        ts_inv[ind],
        lstN_inv[ind],
        lai[ind],
        swc[ind],
        doy[ind],
        hours_float[ind],
    ]).T

    y = ts_mea[ind]

    y_pred = model.predict(X)

    bias_train, rmse_train, r2_train = cal_rmse_r2(y, y_pred, threshold)
    print("\nRandom Forest Regression Results:")
    print(f"RMSE: {rmse_train:.3f}, Bias: {bias_train:.3f}, R²: {r2_train[0]:.3f}")

