from utils.old.util import *
import numpy as np
import csv
from scipy.stats import gaussian_kde
import pandas as pd
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


'''2024.2.27'''
'''验证ChinaFlux0cm的土壤温度'''

base_dir = r'/home/hero/data/AATSR/Validation/ChinaFlux/'
ChinaFlux_dir = r'/home/hero/data/AATSR/Sites/ChinaNet/surface/'

h5_dir = base_dir + r'AATSR_h5/'
csv_dir = base_dir + r"AATSR_csv/"
val_dir = base_dir + r"AATSR_merged/"

# lst_out_dir = base_dir + r"Validation/" + lsct_name + r"/val_AATST_LST-Fluxnet_LST/"
lsct_out_dir = base_dir + r"results/"
# lsct_fit_out_dir = base_dir + r"Validation/" + lsct_name + r"/val_AATST_LSCT-Fluxnet_LSCT_fit/"
# lst_soil_out_dir = base_dir + r"Validation/" + lsct_name + r"/val_AATSR_LST-Fluxnet_soil/"
# soil_lst_dir = base_dir + r"Validation/" + lsct_name + r"/val_AATSR_soil-Fluxnet_LST/"

mkdir_if_not_exist(h5_dir)
mkdir_if_not_exist(csv_dir)
mkdir_if_not_exist(val_dir)
mkdir_if_not_exist(lsct_out_dir)

ifextract = 0
ifmerge = 0
ifval_ts = 1

daynight = 'night'

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

if ifextract:
    siteNames = search_dir(h5_dir, '')
    for siteName in siteNames:
        indir = h5_dir + siteName + r"/"
        outfile = csv_dir + siteName + ".csv"

        if os.path.exists(outfile): continue

        print(outfile)
        h5Files = search_file_rej(indir, ".h5", "enp")
        h5Files.sort()
        for h5File in h5Files:
            infile = indir + h5File
            # if os.path.getsize(infile) < 8000: continue
            year = int(h5File.split('_')[1])
            doy = int(h5File.split('_')[2])
            month, day = doy2date(year, doy)

            '''读取数据'''
            name_list = ["lon", 'lat', "indx", "indy", "ref_indx", "ref_indy", "sec", "ref_time", "type", "emis_s",
                         "emis_v", 'vzaN', 'vzaO', 'vaaN', 'vaaO', 'clo', "lstN", "lstO", "Ts0", "Tv0", "Ts1", "Tv1",
                         "Ts2", "Tv2"]
            lon, lat, indx, indy, ref_indx, ref_indy, sec, ref_time, type, emis_s, emis_v, vzaN, vzaO, vaaN, vaaO, clo, lstN, lstO, Ts0, Tv0, Ts1, Tv1, Ts2, Tv2 = read_h5py_items(
                infile, name_list)
            nl, ns = np.shape(indx)
            checked_items = []
            for item in [lon, lat, indx, indy, ref_indx, ref_indy, sec, ref_time, type, emis_s, emis_v, vzaN, vzaO,
                         vaaN, vaaO, clo, lstN, lstO, Ts0, Tv0, Ts1, Tv1, Ts2, Tv2]:
                if item == []:
                    item = np.zeros([nl, ns])
                checked_items.append(item)
            lon, lat, indx, indy, ref_indx, ref_indy, sec, ref_time, type, emis_s, emis_v, vzaN, vzaO, vaaN, vaaO, clo, lstN, lstO, Ts0, Tv0, Ts1, Tv1, Ts2, Tv2 = checked_items
            mask_x = indx == ref_indx
            mask_y = indy == ref_indy
            ind = np.bitwise_and(mask_x, mask_y)
            if sum(ind) == 0: continue
            if sum(clo[ind]) > 100:
                # print("pass cloud!")
                continue

            if isinstance(sec, np.ndarray) and (sec.size == 1):
                sec = sec
            else:
                sec = int(sec[ind][0])
            h = sec // 3600
            m = (sec - h * 3600) // 60
            s = sec - h * 3600 - m * 60
            if h >= 24: h = h - 24

            # h = ref_time // 10000
            # m = (ref_time - h * 10000) // 100
            # s = ref_time - h * 10000 - m * 100

            time_save = datetime(year, month, day, int(h), int(m), int(s))
            # lai_save = np.average(lai[ind])
            lstN_save = np.average(lstN[ind]) / 100
            lstO_save = np.average(lstO[ind]) / 100
            Ts0_save = np.average(Ts0[ind]) / 100
            Tv0_save = np.average(Tv0[ind]) / 100
            Ts1_save = np.average(Ts1[ind]) / 100
            Tv1_save = np.average(Tv1[ind]) / 100
            Ts2_save = np.average(Ts2[ind]) / 100
            Tv2_save = np.average(Tv2[ind]) / 100

            with open(outfile, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [time_save, lstN_save, lstO_save, Ts0_save, Tv0_save, Ts1_save, Tv1_save, Ts2_save, Tv2_save])

def read_fluxnet_locations(file_path):
    df = pd.read_excel(file_path, engine='openpyxl')  # 指定 Excel 解析引擎
    locations = {}
    for _, row in df.iterrows():
        site_name = row['SITE_ID']
        lat = float(row['LOCATION_LAT'])
        lon = float(row['LOCATION_LONG'])
        locations[site_name] = (lat, lon)
    return locations


def get_timezone(lat, lon):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if timezone_str:
        return pytz.timezone(timezone_str)
    else:
        return None

if ifmerge:
    fluxnet_loc_file = r"/home/hero/data/AATSR/Sites/ChinaNet/ChinaFlux.xlsx"
    fluxnet_locations = read_fluxnet_locations(fluxnet_loc_file)
    # 假设 fileNames 是你搜索到的文件名列表
    fileNames = search_file(csv_dir, ['.csv'])
    for fileName in fileNames:
        site_name = fileName[:-4]
        if site_name in fluxnet_locations:
            print(site_name)
            lat, lon = fluxnet_locations[site_name]
            timezone = get_timezone(lat, lon)
            infile = csv_dir + fileName
            data = []
            with open(infile, newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    utc_time_str = row[0]  # 假设 UTC 时间在第一列
                    utc_time = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
                    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone)
                    lstN = float(row[1])
                    lstO = float(row[2])
                    ts0 = float(row[3])
                    tv0 = float(row[4])
                    ts1 = float(row[5])
                    tv1 = float(row[6])
                    ts2 = float(row[7])
                    tv2 = float(row[8])
                    data.append(
                        [utc_time_str, local_time.strftime('%Y-%m-%d %H:%M:%S'), lstN, lstO, ts0, tv0, ts1, tv1, ts2,
                         tv2])

            df = pd.DataFrame(data,
                              columns=['UTC_Time', 'Local_Time', 'lstN', 'lstO', 'Ts0', 'Tv0', 'Ts1', 'Tv1', 'Ts2',
                                       'Tv2'])

            flux_csv = search_file(ChinaFlux_dir + site_name[3:] + '_M_30min/', ['2005'])
            if not len(flux_csv): continue
            infile = ChinaFlux_dir + site_name[3:] + '_M_30min/' + flux_csv[0]
            print(infile)
            ground_data = pd.read_excel(infile,skiprows = [1])
            ground_data['TIMESTAMP_START'] = pd.to_datetime(
                ground_data[['年', '月', '日', '时', '分', '秒']].rename(
                    columns={'年': 'year', '月': 'month', '日': 'day', '时': 'hour', '分': 'minute', '秒': 'second'})
            )

            ground_data['TIMESTAMP_END'] = ground_data['TIMESTAMP_START'] + pd.Timedelta(minutes=30)

            # 将 df 中的时间列也转换为 datetime 对象
            df['Local_Time'] = pd.to_datetime(df['Local_Time'])

            # 合并数据，选择 df 中在地面数据时间范围内的行
            merged_data = pd.DataFrame()
            for idx, row in df.iterrows():
                local_time = row['Local_Time']
                filtered_ground_data = ground_data[(ground_data['TIMESTAMP_START'] <= local_time) &
                                                   (ground_data['TIMESTAMP_END'] >= local_time)]
                if not filtered_ground_data.empty:
                    merged_row = row.to_frame().T.assign(**filtered_ground_data.iloc[0])
                    # merged_row['TA_F_MDS'] += 273.15
                    # merged_row['TS_F_MDS_1'] += 273.15
                    merged_data = pd.concat([merged_data, merged_row], axis=0)

            # 选择需要的列
            merged_data = merged_data[
                ['UTC_Time', 'Local_Time', 'TIMESTAMP_START', 'TIMESTAMP_END', 'lstN', 'lstO', 'Ts0', 'Tv0', 'Ts1',
                 'Tv1', 'Ts2', 'Tv2', '一层土壤温度', '近地面空气温度',	'冠层上方空气温度','T_skin']]

            # 保存合并后的数据到 CSV 文件
            output_file = val_dir + site_name + ".csv"
            merged_data.to_csv(output_file, index=False)

            print("合并后的数据已保存到", output_file)


def cal_rmse_r2(data1,data2,tshred=10):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2

if ifval_ts:
    mkdir_if_not_exist(lsct_out_dir)
    fileNames = search_file(val_dir, ['.csv'])
    threshold = 9
    alldata = []
    for fileName in fileNames:
        infile = val_dir + fileName
        data = pd.read_csv(infile)

        local_time = pd.to_datetime(data['Local_Time'])
        if daynight == 'day':
            mask = (local_time.dt.time >= time_min) & (
                    local_time.dt.time <= time_max)
        elif daynight == 'night':
            mask = (local_time.dt.time >= time_min) + (
                    local_time.dt.time <= time_max)
        filtered_data = data[mask]
        alldata.append(filtered_data)
        data = filtered_data
        ts_inv = data['Ts2']
        tv_inv = data['Tv2']
        ts_mea = data['一层土壤温度'] +273.15
        ta_mea = data['近地面空气温度'] +273.15
        invalid_num = sum(np.abs(ts_mea - ts_inv) < threshold)
        print("--------------------------------------------------------------------------------")
        print(fileName)
        print("有效点数/总点数：%03d/%03d" % (invalid_num, sum(ts_inv != 0)))
        if invalid_num == 0:
            continue
        bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea, ts_inv, threshold)
        bias_v, rmse_v, r2_v = cal_rmse_r2(ta_mea, tv_inv, threshold)
        print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s[0]))
        print("植被 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))

        # 绘制散点图
        ind = (ts_mea > 250) * (ts_mea < 320) * (ts_inv > 250) * (ts_inv < 320) * (ts_inv != 273.15)
        plt.figure(figsize=(4.5, 4))
        plt.scatter(ts_mea[ind], ts_inv[ind], label='Soil', color='red')
        # plt.scatter(ta_mea[ind], tv_inv[ind], label='Vegetation', color='green')
        plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
        plt.plot([220, 370], [215, 365], color='grey', linestyle='--')  # 添加y=x-5线
        plt.plot([220, 370], [225, 375], color='grey', linestyle='--')  # 添加y=x+5线
        plt.plot([220, 370], [210, 360], color='grey', linestyle='--')  # 添加y=x-10线
        plt.plot([220, 370], [230, 380], color='grey', linestyle='--')  # 添加y=x+10线
        plt.xlim(np.min(ts_inv[ts_inv > 200]) - 20, np.max(ts_inv + 20))
        plt.ylim(np.min(ts_inv[ts_inv > 200]) - 20, np.max(ts_inv + 20))
        plt.xlabel('Measured')
        plt.ylabel('Inversion')
        plt.title(fileName[:-4])
        plt.legend()

        # 保存图表
        output_path = lsct_out_dir + daynight + '/' + fileName[:-4] + ".png"
        mkdir_if_not_exist(lsct_out_dir + daynight + '/')
        plt.savefig(output_path)
        plt.close()

    print("--------------------------------------------------------------------------------")
    print("ALL SITES")
    all_data_concatenated = pd.concat(alldata)
    ts_inv = all_data_concatenated['lstN']
    tv_inv = all_data_concatenated['Tv2']
    ts_mea = all_data_concatenated['一层土壤温度'] +273.15
    # lst_mea = all_data_concatenated['lst']
    ta_mea = all_data_concatenated['近地面空气温度'] +273.15
    invalid_num = sum(np.abs(ts_mea - ts_inv) < threshold)
    print("有效点数：%03d" % invalid_num)
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea, ts_inv, threshold)
    bias_v, rmse_v, r2_v = cal_rmse_r2(ta_mea, tv_inv, threshold)
    # bias_f, rmse_f, r2_f = cal_rmse_r2(lst_mea, ts_mea, threshold)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s[0]))
    print("植被 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))
    # print("Fluxnet Ts lst RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_f, bias_f, r2_f[0]))
    # 绘制散点图
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
    plt.xlabel('Measured Soil Temperature')
    plt.ylabel('Inverted Soil Temperature')
    # plt.title("Density Scatter Plot of Soil Temperature")
    output_path = lsct_out_dir + daynight + '/' "ALL_SITES_Soil_Temperature_Scatter_Density.png"
    plt.ylim([250, 340])
    plt.xlim([250, 340])
    plt.savefig(output_path)
    plt.close()

    print("--------------------------------------------------------------------------------")
    print("植被温度散点密度图")
    ind = (ta_mea > 270) * (ta_mea < 350) * (tv_inv > 270) * (tv_inv < 370) * (tv_inv != 273.15) * (
                ta_mea - tv_inv < 20)
    # Calculate the point density for vegetation temperature
    # Calculate the point density for vegetation temperature
    xy_vegetation = np.vstack([ta_mea[ind], tv_inv[ind]])
    z_vegetation = gaussian_kde(xy_vegetation)(xy_vegetation)

    # Sort the points by density, so that the densest points are plotted last
    idx_vegetation = z_vegetation.argsort()
    ta_mea_vegetation, tv_inv_vegetation, z_vegetation = ta_mea[ind].iloc[idx_vegetation], tv_inv[ind].iloc[
        idx_vegetation], z_vegetation[idx_vegetation]

    plt.figure(figsize=(5, 4))
    sc = plt.scatter(ta_mea_vegetation, tv_inv_vegetation, c=z_vegetation, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([250, 370], [250, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured Vegetation Temperature')
    plt.ylabel('Inverted Vegetation Temperature')
    # plt.title("Density Scatter Plot of Vegetation Temperature")
    plt.ylim([250, 340])
    plt.xlim([250, 340])
    output_path = lsct_out_dir + daynight + '/' "ALL_SITES_Vegetation_Temperature_Scatter_Density.png"
    print(output_path)
    plt.savefig(output_path)
    plt.close()

    print("散点密度图已保存")