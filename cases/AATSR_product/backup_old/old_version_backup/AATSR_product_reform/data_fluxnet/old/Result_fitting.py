from utils.old.util import *
from scipy.stats import gaussian_kde
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import warnings
warnings.filterwarnings("ignore")

'''2024.5.22'''
'''尝试将所有结果找一个线性关系拟合过去'''

lsct_name = "0_raw_h5_2002-2012"
base_dir = r"D:\data\AATSR_product\Fluxnet_AATSR\\"
val_dir = base_dir + r"2_val_2002-2012\\" + lsct_name + r"\Merge_csv\\"
lsct_out_dir = base_dir + r"2_val_2002-2012\\" + lsct_name + r"\val_AATST_LSCT-Fluxnet_LSCT\\"
fitting_out_dir = base_dir + r"3_fit\\" + lsct_name + r"\val_Fitting_LSCT\\"
pass_site = ['BR-Sa3','GF-Guy','MY-PSO','AU-Wac','GH-Ank','IT-Tor','RU-Che','US-Syv']
mkdir_if_not_exist(fitting_out_dir)

if_linear_all = 0
if_linear_site = 0
if_linear_type = 0
if_nonlinear_all = 0
if_nonlinear_site = 0
if_nonlinear_type = 1

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

def cal_rmse_r2(data1, data2, tshred=10):
    dif = (data2 - data1)
    ind = np.abs(dif) < tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind] * dif[ind]))
    coef = np.corrcoef(data1[ind], data2[ind])
    r2 = coef[1, 0] * coef[1, 0]
    return bias, rmse, r2

if if_linear_all:
    fileNames = search_file(val_dir, ['.csv'])
    threshold = 9
    alldata = []
    for fileName in fileNames:
        print("--------------------------------------------------------------------------------")
        print(fileName)
        if fileName[:-4] in pass_site: continue
        infile = val_dir + fileName
        data = pd.read_csv(infile)
        data['Local_Time'] = pd.to_datetime(data['Local_Time'])
        start_time = '08:00'
        end_time = '18:00'
        if daynight == 'day':
            mask = (data['Local_Time'].dt.time >= time_min) & (
                        data['Local_Time'].dt.time <= time_max)
        elif daynight == 'night':
            mask = (data['Local_Time'].dt.time >= time_min) + (
                        data['Local_Time'].dt.time <= time_max)
        filtered_data = data[mask]
        alldata.append(filtered_data)

    print("--------------------------------------------------------------------------------")
    print("ALL SITES")
    all_data_concatenated = pd.concat(alldata)
    ts_inv = all_data_concatenated['Ts']
    tv_inv = all_data_concatenated['Tv']
    ts_mea = all_data_concatenated['TS_F_MDS_1']
    ta_mea = all_data_concatenated['TA_F_MDS']
    ind =  (ts_mea > 250) * (ts_mea < 370) * (ts_inv > 250) * (ts_inv < 370)
    invalid_num = sum(np.abs(ts_mea[ind] - ts_inv[ind]) < threshold)
    print("有效点数：%03d" % invalid_num)
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea[ind], ts_inv[ind], threshold)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s))

    # 线性拟合
    ind_filter = (ts_mea > 250) * (ts_inv>250) * (np.abs(ts_inv - ts_mea)<15) * (ts_inv - ts_mea>-10)
    ts_mea_filtered = ts_mea[ind_filter]
    ts_inv_filtered = ts_inv[ind_filter]
    coeffs = np.polyfit(ts_inv_filtered, ts_mea_filtered, 1)
    poly_eq = np.poly1d(coeffs)
    ts_inv_poly_fit = coeffs[0] * ts_inv + coeffs[1]

    ts_mea_fit = np.linspace(250, 350, 100)
    ts_inv_fit = (ts_mea_fit - coeffs[1])/coeffs[0]
    ind = (ts_mea > 250) * (ts_mea < 370) * (ts_inv > 250) * (ts_inv < 370) * (ts_inv != 273.15)

    print("--------------------------------------------------------------------------------")
    print("土壤温度散点密度图")

    # Calculate the point density for soil temperature
    xy_soil = np.vstack([ts_mea[ind], ts_inv[ind]])
    z_soil = gaussian_kde(xy_soil)(xy_soil)

    # Sort the points by density, so that the densest points are plotted last
    idx_soil = z_soil.argsort()
    ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind].iloc[idx_soil], ts_inv[ind].iloc[idx_soil], z_soil[idx_soil]

    plt.figure(figsize=(5, 4))
    sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.plot(ts_mea_fit, ts_inv_fit, color='red', label=f'Fit: y = {coeffs[0]:.2f}x + {coeffs[1]:.2f}')
    plt.xlabel('Measured Soil Temperature')
    plt.ylabel('Inverted Soil Temperature')
    plt.title("Density Scatter Plot of Soil Temperature")
    output_path = fitting_out_dir + "Origin_" + daynight + ".png"
    plt.ylim([250, 340])
    plt.xlim([250, 340])
    plt.savefig(output_path)
    plt.close()

    print("--------------------------------------------------------------------------------")
    print("Poly_fit")
    print(coeffs[0],coeffs[1])
    ind =  (ts_mea > 250) * (ts_mea < 370) * (ts_inv > 250) * (ts_inv < 370)
    invalid_num = sum(np.abs(ts_mea[ind] - ts_inv_poly_fit[ind]) < threshold)
    print("有效点数：%03d" % invalid_num)
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea[ind], ts_inv_poly_fit[ind], threshold)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s))

    print("--------------------------------------------------------------------------------")
    print("Poly_fit 土壤温度散点密度图")
    # Calculate the point density for soil temperature
    xy_soil = np.vstack([ts_mea[ind], ts_inv_poly_fit[ind]])
    z_soil = gaussian_kde(xy_soil)(xy_soil)

    # Sort the points by density, so that the densest points are plotted last
    idx_soil = z_soil.argsort()
    ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind].values[idx_soil], ts_inv_poly_fit[ind].iloc[idx_soil], z_soil[
        idx_soil]

    plt.figure(figsize=(5, 4))
    sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured Soil Temperature')
    plt.ylabel('Inverted Soil Temperature')
    plt.title("Density Scatter Plot of Soil Temperature")
    output_path = fitting_out_dir + "linear_all_" + daynight + ".png"
    plt.ylim([250, 340])
    plt.xlim([250, 340])
    plt.savefig(output_path)
    plt.close()

if if_nonlinear_all:
    fileNames = search_file(val_dir, ['.csv'])
    threshold = 9
    alldata = []
    for fileName in fileNames:
        print("--------------------------------------------------------------------------------")
        print(fileName)
        if fileName[:-4] in pass_site: continue
        infile = val_dir + fileName
        data = pd.read_csv(infile)
        data['Local_Time'] = pd.to_datetime(data['Local_Time'])
        start_time = '08:00'
        end_time = '18:00'
        if daynight == 'day':
            mask = (data['Local_Time'].dt.time >= time_min) & (
                        data['Local_Time'].dt.time <= time_max)
        elif daynight == 'night':
            mask = (data['Local_Time'].dt.time >= time_min) + (
                        data['Local_Time'].dt.time <= time_max)
        filtered_data = data[mask]
        alldata.append(filtered_data)

    print("--------------------------------------------------------------------------------")
    print("ALL SITES")
    all_data_concatenated = pd.concat(alldata)
    time = all_data_concatenated['Local_Time']
    ts_inv = all_data_concatenated['Ts']
    tv_inv = all_data_concatenated['Tv']
    ts_mea = all_data_concatenated['TS_F_MDS_1']
    ta_mea = all_data_concatenated['TA_F_MDS']
    ind = (ts_mea > 250) * (ts_mea < 370) * (ts_inv > 250) * (ts_inv < 370)
    invalid_num = sum(np.abs(ts_mea[ind] - ts_inv[ind]) < threshold)
    print("有效点数：%03d" % invalid_num)
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea[ind], ts_inv[ind], threshold)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s))

    def func(x,t, a, b, c, d, e):
        w = 2 * np.pi / (60*60*24)
        return a + (b * x + c) * np.exp(d) * np.sin(w * t + e -d)

        # Convert Local_Time to seconds
    def convert_to_seconds(time_str):
        # dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dt = time_str
        return dt.hour * 3600 + dt.minute * 60 + dt.second

    time_seconds = np.array([convert_to_seconds(t) for t in time])


    # Perform non-linear curve fitting
    ind_filter = (ts_mea > 250) * (ts_inv>250) * (np.abs(ts_inv - ts_mea)<15) * (ts_inv - ts_mea>-10)
    popt, pcov = curve_fit(lambda t, a, b, c, d, e: func(ts_inv[ind_filter], t, a, b, c, d, e), time_seconds[ind_filter], ts_mea[ind_filter], p0=[290, 0, 0, 0, 0])

    # Print the fitted parameters
    print("Fitted parameters:")
    print("a =", popt[0])
    print("b =", popt[1])
    print("c =", popt[2])
    print("d =", popt[3])
    print("e =", popt[4])

    # Calculate fitted values
    ts_fitted = func(ts_inv, time_seconds, *popt)

    # Evaluate the fit
    bias_fit, rmse_fit, r2_fit = cal_rmse_r2(ts_mea[ind], ts_fitted[ind], threshold)
    invalid_num = sum(np.abs(ts_mea[ind] - ts_fitted[ind]) < threshold)
    print("有效点数：%03d" % invalid_num)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_fit, bias_fit, r2_fit))

    print("--------------------------------------------------------------------------------")
    print("Non-linear 土壤温度散点密度图")
    # Calculate the point density for soil temperature
    xy_soil = np.vstack([ts_mea[ind], ts_fitted[ind]])
    z_soil = gaussian_kde(xy_soil)(xy_soil)

    # Sort the points by density, so that the densest points are plotted last
    idx_soil = z_soil.argsort()
    ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind].values[idx_soil], ts_fitted[ind].iloc[idx_soil], z_soil[
        idx_soil]

    plt.figure(figsize=(5, 4))
    sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured Soil Temperature')
    plt.ylabel('Inverted Soil Temperature')
    plt.title("Density Scatter Plot of Soil Temperature")
    output_path = fitting_out_dir + "Nonlinear_all_" + daynight + ".png"
    plt.ylim([250, 340])
    plt.xlim([250, 340])
    plt.savefig(output_path)
    plt.close()

if if_linear_site:
    fileNames = search_file(val_dir, ['.csv'])
    threshold = 9
    alldata = []
    for fileName in fileNames:
        print("--------------------------------------------------------------------------------")
        print(fileName)
        if fileName[:-4] in pass_site: continue
        infile = val_dir + fileName
        data = pd.read_csv(infile)
        data['Local_Time'] = pd.to_datetime(data['Local_Time'])
        start_time = '08:00'
        end_time = '18:00'
        if daynight == 'day':
            mask = (data['Local_Time'].dt.time >= time_min) & (
                        data['Local_Time'].dt.time <= time_max)
        elif daynight == 'night':
            mask = (data['Local_Time'].dt.time >= time_min) + (
                        data['Local_Time'].dt.time <= time_max)
        filtered_data = data[mask]
        data = filtered_data
        ts_inv = data['Ts']
        tv_inv = data['Tv']
        ts_mea = data['TS_F_MDS_1']
        ta_mea = data['TA_F_MDS']
        ind_filter = (ts_mea > 250) * (ts_inv > 250) * (np.abs(ts_inv - ts_mea) < 15) * (ts_inv - ts_mea > -10)
        if sum(ind_filter)<5: continue
        ts_mea_filtered = ts_mea[ind_filter]
        ts_inv_filtered = ts_inv[ind_filter]
        coeffs = np.polyfit(ts_inv_filtered, ts_mea_filtered, 1)
        poly_eq = np.poly1d(coeffs)
        ts_inv_poly_fit = coeffs[0] * ts_inv + coeffs[1]
        data['ts_inv_poly_fit'] = ts_inv_poly_fit
        alldata.append(data)

    all_data_concatenated = pd.concat(alldata)
    ts_inv = all_data_concatenated['Ts']
    tv_inv = all_data_concatenated['Tv']
    ts_mea = all_data_concatenated['TS_F_MDS_1']
    ta_mea = all_data_concatenated['TA_F_MDS']
    ts_inv_poly_fit = all_data_concatenated['ts_inv_poly_fit']
    print("--------------------------------------------------------------------------------")
    print("Poly_fit")
    ind = (ts_mea > 250) * (ts_mea < 370) * (ts_inv > 250) * (ts_inv < 370)
    invalid_num = sum(np.abs(ts_mea[ind] - ts_inv_poly_fit[ind]) < threshold)
    print("有效点数：%03d" % invalid_num)
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea[ind], ts_inv_poly_fit[ind], threshold)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s))

    print("--------------------------------------------------------------------------------")
    print("Poly_fit 土壤温度散点密度图")
    # Calculate the point density for soil temperature
    xy_soil = np.vstack([ts_mea[ind], ts_inv_poly_fit[ind]])
    z_soil = gaussian_kde(xy_soil)(xy_soil)

    # Sort the points by density, so that the densest points are plotted last
    idx_soil = z_soil.argsort()
    ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind].values[idx_soil], ts_inv_poly_fit[ind].iloc[idx_soil], z_soil[
        idx_soil]

    plt.figure(figsize=(5, 4))
    sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured Soil Temperature')
    plt.ylabel('Inverted Soil Temperature')
    plt.title("Density Scatter Plot of Soil Temperature")
    output_path = fitting_out_dir + "Linear_site.png"
    plt.ylim([250, 340])
    plt.xlim([250, 340])
    plt.savefig(output_path)
    plt.close()

if if_nonlinear_site:
    fileNames = search_file(val_dir, ['.csv'])
    threshold = 9
    alldata = []
    for fileName in fileNames:
        print("--------------------------------------------------------------------------------")
        print(fileName)

        if fileName[:-4] in pass_site: continue
        infile = val_dir + fileName
        data = pd.read_csv(infile)
        data['Local_Time'] = pd.to_datetime(data['Local_Time'])
        start_time = '08:00'
        end_time = '18:00'
        if daynight == 'day':
            mask = (data['Local_Time'].dt.time >= time_min) & (
                        data['Local_Time'].dt.time <= time_max)
        elif daynight == 'night':
            mask = (data['Local_Time'].dt.time >= time_min) + (
                        data['Local_Time'].dt.time <= time_max)
        filtered_data = data[mask]
        data = filtered_data

        time = data['Local_Time']
        ts_inv = data['Ts']
        tv_inv = data['Tv']
        ts_mea = data['TS_F_MDS_1']
        ta_mea = data['TA_F_MDS']
        def func(x, t, a, b, c, d, e):
            w = 2 * np.pi / (60 * 60 * 24)
            return a + (b * x + c) * np.exp(d) * np.sin(w * t + e - d)
        def convert_to_seconds(time_str):
            # dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            dt = time_str
            return dt.hour * 3600 + dt.minute * 60 + dt.second

        time_seconds = np.array([convert_to_seconds(t) for t in time])

        ind_filter = (ts_mea > 250) * (ts_inv > 250) * (np.abs(ts_inv - ts_mea) < 15) * (ts_inv - ts_mea > -10)
        if sum(ind_filter)<10: continue
        popt, pcov = curve_fit(lambda t, a, b, c, d, e: func(ts_inv[ind_filter], t, a, b, c, d, e),
                               time_seconds[ind_filter], ts_mea[ind_filter], p0=[290, 0, 0, -0.2, 0],maxfev=5000)

        # Calculate fitted values
        ts_fitted = func(ts_inv, time_seconds, *popt)
        data['ts_inv_poly_fit'] = ts_fitted
        alldata.append(data)

    all_data_concatenated = pd.concat(alldata)
    ts_inv = all_data_concatenated['Ts']
    tv_inv = all_data_concatenated['Tv']
    ts_mea = all_data_concatenated['TS_F_MDS_1']
    ta_mea = all_data_concatenated['TA_F_MDS']
    ts_inv_poly_fit = all_data_concatenated['ts_inv_poly_fit']
    print("--------------------------------------------------------------------------------")
    print("Poly_fit")
    ind = (ts_mea > 250) * (ts_mea < 370) * (ts_inv > 250) * (ts_inv < 370)
    invalid_num = sum(np.abs(ts_mea[ind] - ts_inv_poly_fit[ind]) < threshold)
    print("有效点数：%03d" % invalid_num)
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea[ind], ts_inv_poly_fit[ind], threshold)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s))

    print("--------------------------------------------------------------------------------")
    print("Poly_fit 土壤温度散点密度图")
    # Calculate the point density for soil temperature
    xy_soil = np.vstack([ts_mea[ind], ts_inv_poly_fit[ind]])
    z_soil = gaussian_kde(xy_soil)(xy_soil)

    # Sort the points by density, so that the densest points are plotted last
    idx_soil = z_soil.argsort()
    ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind].values[idx_soil], ts_inv_poly_fit[ind].iloc[idx_soil], z_soil[
        idx_soil]

    plt.figure(figsize=(5, 4))
    sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured Soil Temperature')
    plt.ylabel('Inverted Soil Temperature')
    plt.title("Density Scatter Plot of Soil Temperature")
    output_path = fitting_out_dir + "Nonlinear_site.png"
    plt.ylim([250, 340])
    plt.xlim([250, 340])
    plt.savefig(output_path)
    plt.close()

if if_linear_type:
    infile_site_igbp = r"D:\data\AATSR_product\Fluxnet2015\\FLUXSITE.xlsx"
    site_igbp_df = pd.read_excel(infile_site_igbp)
    classification = {
        "Forest": ['EBF', 'ENF', 'DNF', 'DBF', 'MF'],
        "Savanna": ['WSA', 'SAV'],
        "Shrub": ['CSH', 'OSH'],
        'Grass': ['GRA'],
        "Crop": ['CRO', 'CVM'],
        'Other': ['BSV', 'WET', 'URB', 'SNO', 'WAT']
    }
    fileNames = search_file(val_dir, ['.csv'])
    threshold = 9
    alldata = {key: [] for key in classification.keys()}  # Initialize dictionary to store data by land type

    for fileName in fileNames:
        print("--------------------------------------------------------------------------------")
        print(fileName)
        if fileName[:-4] in pass_site: continue
        site_id = fileName[:-4]
        IGBP = site_igbp_df[site_igbp_df['SITE_ID'] == site_id]['IGBP'].values[0]
        infile = os.path.join(val_dir, fileName)
        data = pd.read_csv(infile)
        data['Local_Time'] = pd.to_datetime(data['Local_Time'])

        if daynight == 'day':
            mask = (data['Local_Time'].dt.time >= time_min) & (data['Local_Time'].dt.time <= time_max)
        elif daynight == 'night':
            mask = (data['Local_Time'].dt.time >= time_min) | (data['Local_Time'].dt.time <= time_max)

        filtered_data = data[mask]

        for land_type, igbp_codes in classification.items():
            if IGBP in igbp_codes:
                alldata[land_type].append(filtered_data)
                break

    adata = []
    for land_type, data_list in alldata.items():
        if data_list:
            combined_data = pd.concat(data_list, ignore_index=True)
            data = combined_data
            ts_inv = data['Ts']
            tv_inv = data['Tv']
            ts_mea = data['TS_F_MDS_1']
            ta_mea = data['TA_F_MDS']
            ind_filter = (ts_mea > 250) * (ts_inv > 250) * (np.abs(ts_inv - ts_mea) < 15) * (ts_inv - ts_mea > -10)
            if sum(ind_filter) < 5: continue
            ts_mea_filtered = ts_mea[ind_filter]
            ts_inv_filtered = ts_inv[ind_filter]
            coeffs = np.polyfit(ts_inv_filtered, ts_mea_filtered, 1)
            poly_eq = np.poly1d(coeffs)
            ts_inv_poly_fit = coeffs[0] * ts_inv + coeffs[1]
            data['ts_inv_poly_fit'] = ts_inv_poly_fit
            print(coeffs[0],coeffs[1])
            adata.append(data)

    all_data_concatenated = pd.concat(adata)
    ts_inv = all_data_concatenated['Ts']
    tv_inv = all_data_concatenated['Tv']
    ts_mea = all_data_concatenated['TS_F_MDS_1']
    ta_mea = all_data_concatenated['TA_F_MDS']
    ts_inv_poly_fit = all_data_concatenated['ts_inv_poly_fit']
    print("--------------------------------------------------------------------------------")
    print("Poly_fit")
    ind = (ts_mea > 250) * (ts_mea < 370) * (ts_inv > 250) * (ts_inv < 370)
    invalid_num = sum(np.abs(ts_mea[ind] - ts_inv_poly_fit[ind]) < threshold)
    print("有效点数：%03d" % invalid_num)
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea[ind], ts_inv_poly_fit[ind], threshold)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s))

    print("--------------------------------------------------------------------------------")
    print("Poly_fit 土壤温度散点密度图")
    # Calculate the point density for soil temperature
    xy_soil = np.vstack([ts_mea[ind], ts_inv_poly_fit[ind]])
    z_soil = gaussian_kde(xy_soil)(xy_soil)

    # Sort the points by density, so that the densest points are plotted last
    idx_soil = z_soil.argsort()
    ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind].values[idx_soil], ts_inv_poly_fit[ind].iloc[idx_soil], z_soil[
        idx_soil]

    plt.figure(figsize=(5, 4))
    sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured Soil Temperature')
    plt.ylabel('Inverted Soil Temperature')
    plt.title("Density Scatter Plot of Soil Temperature")
    output_path = fitting_out_dir + "Linear_site_" + daynight + "_type.png"
    plt.ylim([250, 340])
    plt.xlim([250, 340])
    plt.savefig(output_path)
    print(output_path)
    plt.close()

if if_nonlinear_type:
    infile_site_igbp = r"D:\data\AATSR_product\Fluxnet2015\\FLUXSITE.xlsx"
    site_igbp_df = pd.read_excel(infile_site_igbp)
    classification = {
        "Forest": ['EBF', 'ENF', 'DNF', 'DBF', 'MF'],
        "Savanna": ['WSA', 'SAV'],
        "Shrub": ['CSH', 'OSH'],
        'Grass': ['GRA'],
        "Crop": ['CRO', 'CVM'],
        'Other': ['BSV', 'WET', 'URB', 'SNO', 'WAT']
    }
    fileNames = search_file(val_dir, ['.csv'])
    threshold = 9
    alldata = {key: [] for key in classification.keys()}  # Initialize dictionary to store data by land type

    for fileName in fileNames:
        print("--------------------------------------------------------------------------------")
        print(fileName)
        if fileName[:-4] in pass_site: continue
        site_id = fileName[:-4]
        IGBP = site_igbp_df[site_igbp_df['SITE_ID'] == site_id]['IGBP'].values[0]
        infile = os.path.join(val_dir, fileName)
        data = pd.read_csv(infile)
        data['Local_Time'] = pd.to_datetime(data['Local_Time'])

        if daynight == 'day':
            mask = (data['Local_Time'].dt.time >= time_min) & (data['Local_Time'].dt.time <= time_max)
        elif daynight == 'night':
            mask = (data['Local_Time'].dt.time >= time_min) | (data['Local_Time'].dt.time <= time_max)

        filtered_data = data[mask]

        for land_type, igbp_codes in classification.items():
            if IGBP in igbp_codes:
                alldata[land_type].append(filtered_data)
                break

    adata = []
    for land_type, data_list in alldata.items():
        if data_list:
            combined_data = pd.concat(data_list, ignore_index=True)
            data = combined_data
            time = data['Local_Time']
            ts_inv = data['Ts']
            tv_inv = data['Tv']
            ts_mea = data['TS_F_MDS_1']
            ta_mea = data['TA_F_MDS']


            def func(x, t, a, b, c, d, e):
                w = 2 * np.pi / (60 * 60 * 24)
                return a + (b * x + c) * np.exp(d) * np.sin(w * t + e - d)


            def convert_to_seconds(time_str):
                # dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                dt = time_str
                return dt.hour * 3600 + dt.minute * 60 + dt.second


            time_seconds = np.array([convert_to_seconds(t) for t in time])

            ind_filter = (ts_mea > 250) * (ts_inv > 250) * (np.abs(ts_inv - ts_mea) < 15) * (ts_inv - ts_mea > -10)
            if sum(ind_filter) < 10: continue
            popt, pcov = curve_fit(lambda t, a, b, c, d, e: func(ts_inv[ind_filter], t, a, b, c, d, e),
                                   time_seconds[ind_filter], ts_mea[ind_filter], p0=[290, 0, 0, -0.2, 0], maxfev=5000)
            # Calculate fitted values
            ts_fitted = func(ts_inv, time_seconds, *popt)
            data['ts_inv_poly_fit'] = ts_fitted
            ts_inv_poly_fit = ts_fitted
            adata.append(data)

            print("--------------------------------------------------------------------------------")
            print(land_type)
            ind = (ts_mea > 250) * (ts_mea < 370) * (ts_inv > 250) * (ts_inv < 370)
            invalid_num = sum(np.abs(ts_mea[ind] - ts_inv_poly_fit[ind]) < threshold)
            print("有效点数：%03d" % invalid_num)
            bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea[ind], ts_inv_poly_fit[ind], threshold)
            print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s))

            xy_soil = np.vstack([ts_mea[ind], ts_fitted[ind]])
            z_soil = gaussian_kde(xy_soil)(xy_soil)
            # Sort the points by density, so that the densest points are plotted last
            idx_soil = z_soil.argsort()
            ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind].values[idx_soil], ts_inv_poly_fit[ind].iloc[idx_soil], \
            z_soil[
                idx_soil]
            plt.figure(figsize=(5, 4))
            sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
            plt.colorbar(sc)
            plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
            plt.xlabel('Measured Soil Temperature')
            plt.ylabel('Inverted Soil Temperature')
            plt.title(land_type + "_" + daynight)
            output_path = fitting_out_dir + "\\Nonlinear_site_type_" + daynight + "\\" + land_type + '.png'
            mkdir_if_not_exist(fitting_out_dir + "\\Nonlinear_site_type_" + daynight + "\\")
            plt.ylim([250, 340])
            plt.xlim([250, 340])
            plt.savefig(output_path)
            print(output_path)
            plt.close()

    all_data_concatenated = pd.concat(adata)
    ts_inv = all_data_concatenated['Ts']
    tv_inv = all_data_concatenated['Tv']
    ts_mea = all_data_concatenated['TS_F_MDS_1']
    ta_mea = all_data_concatenated['TA_F_MDS']
    ts_inv_poly_fit = all_data_concatenated['ts_inv_poly_fit']
    print("--------------------------------------------------------------------------------")
    print("Poly_fit")
    ind = (ts_mea > 250) * (ts_mea < 370) * (ts_inv > 250) * (ts_inv < 370)
    invalid_num = sum(np.abs(ts_mea[ind] - ts_inv_poly_fit[ind]) < threshold)
    print("有效点数：%03d" % invalid_num)
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea[ind], ts_inv_poly_fit[ind], threshold)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s))

    print("--------------------------------------------------------------------------------")
    print("Poly_fit 土壤温度散点密度图")
    # Calculate the point density for soil temperature
    xy_soil = np.vstack([ts_mea[ind], ts_inv_poly_fit[ind]])
    z_soil = gaussian_kde(xy_soil)(xy_soil)

    # Sort the points by density, so that the densest points are plotted last
    idx_soil = z_soil.argsort()
    ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind].values[idx_soil], ts_inv_poly_fit[ind].iloc[idx_soil], z_soil[
        idx_soil]

    plt.figure(figsize=(5, 4))
    sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured Soil Temperature')
    plt.ylabel('Inverted Soil Temperature')
    # plt.title("Density Scatter Plot of Soil Temperature")
    output_path = fitting_out_dir + "Nonlinear_site_type_" + daynight + ".png"
    plt.ylim([250, 340])
    plt.xlim([250, 340])
    plt.savefig(output_path)
    print(output_path)
    plt.close()