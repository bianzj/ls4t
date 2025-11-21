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

'''2024.3.15'''
'''逐站点AATSR与Fluxnet结果验证'''
'''1.从h5提取信息到csv'''
'''2.反演与实测合并成一个csv(时间匹配)'''
'''3.逐站点精度验证 + 总体验证 + 出图'''
'''需要先运行AATSR_extract_site_lsct_h5.py 获取站点附近的h5切片'''

'''2024.3.20'''
'''加入了温度验证'''

# 改这里
lsct_name = "0_raw_h5_2002-2012"
# lsct_name = "0_raw_h5_2009"
# lsct_name = "1_lsct3_h5"


base_dir = r"D:\data\AATSR_product\Fluxnet_AATSR\\"
fluxnet_loc_file = base_dir + r"\base\\FLUXSITE_imagexy.csv"
fluxnet_filter_dir = base_dir + r"0_Fluxnet_csv_2002-2012\\"
h5_dir = base_dir + lsct_name + r"\\"
csv_dir = base_dir + r"2_val_2002-2012\\" + lsct_name + r"\\AATSR_csv\\"
val_dir = base_dir + r"2_val_2002-2012\\" + lsct_name + r"\Merge_csv\\"

lst_out_dir = base_dir + r"2_val_2002-2012\\" + lsct_name + r"\val_AATST_LST-Fluxnet_LST\\"
lsct_out_dir = base_dir + r"2_val_2002-2012\\" + lsct_name + r"\val_AATST_LSCT-Fluxnet_LSCT\\"
lst_soil_out_dir = base_dir + r"2_val_2002-2012\\" + lsct_name + r"\val_AATSR_LST-Fluxnet_soil\\"
soil_lst_dir = base_dir + r"2_val_2002-2012\\" + lsct_name + r"\val_AATSR_soil-Fluxnet_LST\\"

mkdir_if_not_exist(h5_dir)
mkdir_if_not_exist(csv_dir)
mkdir_if_not_exist(val_dir)

ifextract = 0
ifmerge = 1
ifextract_ERA5 = 0

ifval_lst = 0
ifval_lst_soil = 0 # AATSR lst 与 fluxnet 土壤温度比
ifval_lsct = 0
ifval_ts_lst = 0 # AATSR Ts 与 fluxnet lst比

pass_site = ['BR-Sa3','GF-Guy','MY-PSO']

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

if ifextract:
    siteNames = search_dir(h5_dir,'')
    for siteName in siteNames:
        indir = h5_dir + siteName + r"\\"
        outfile = csv_dir + siteName + ".csv"

        if os.path.exists(outfile): continue

        print(outfile)
        h5Files = search_file_rej(indir,".h5","enp")

        for h5File in h5Files:
            infile = indir + h5File
            # if os.path.getsize(infile) < 8000: continue
            year = int(h5File.split('_')[1])
            doy = int(h5File.split('_')[2])
            month,day = doy2date(year,doy)

            '''读取数据'''
            name_list = ["indx", "indy", "ref_indx", "ref_indy", "type", "lai", "sec", "ref_time", "lstN", "lstO", "Ts","Tv",'Tsl','Tsh','clo']
            indx,indy,ref_indx,ref_indy,type,lai,sec,ref_time,lstN,lstO,Ts,Tv,Tsl,Tsh,clo = read_h5py_items(infile,name_list)
            nl,ns = np.shape(indx)
            checked_items = []
            for item in [indx, indy, ref_indx, ref_indy, type, lai, sec, ref_time, lstN, lstO, Ts, Tv, Tsl, Tsh,clo]:
                if item == []:
                    item = np.zeros([nl, ns])
                checked_items.append(item)
            indx, indy, ref_indx, ref_indy, type, lai, sec, ref_time, lstN, lstO, Ts, Tv, Tsl, Tsh,clo = checked_items
            mask_x = indx==ref_indx
            mask_y = indy==ref_indy
            ind = np.bitwise_and(mask_x,mask_y)
            if sum(ind) == 0: continue
            if sum(clo[ind]) > 100:
                # print("pass cloud!")
                continue
            if isinstance(sec,np.ndarray) and (sec.size==1): sec = sec
            else: sec = int(sec[ind][0])
            h = sec // 3600
            m = (sec - h *3600) // 60
            s = sec - h*3600 - m*60
            if h >= 24: h=h-24
            time_save = datetime(year,month,day,int(h),int(m),int(s))
            lai_save = np.average(lai[ind])
            lstN_save = np.average(lstN[ind])/100
            lstO_save = np.average(lstO[ind])/100
            Ts_save = np.average(Ts[ind])
            Tv_save = np.average(Tv[ind])
            Tsl_save = np.average(Tsl[ind])
            Tsh_save = np.average(Tsh[ind])


            with open(outfile, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([time_save, lai_save, lstN_save, lstO_save, Ts_save, Tv_save,Tsl_save,Tsh_save])

def read_fluxnet_locations(file_path):
    locations = {}
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
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
    # 读取 FLUXSITE_imagexy.csv 文件
    fluxnet_loc_file = r"D:\data\AATSR_product\Fluxnet2015\FLUXSITE_imagexy.csv"
    fluxnet_locations = read_fluxnet_locations(fluxnet_loc_file)

    # 假设 fileNames 是你搜索到的文件名列表
    fileNames = search_file(csv_dir, ['.csv'])
    for fileName in fileNames:
        site_name = fileName[:-4]
        if site_name in fluxnet_locations:
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
                    lstN = float(row[2])
                    lstO = float(row[3])
                    ts = float(row[4])  # 假设 Ts 在第五列
                    tv = float(row[5])  # 假设 Tv 在第六列
                    tsl = float(row[6])  # 假设 Ts 在第五列
                    tsh = float(row[7])  # 假设 Tv 在第六列
                    data.append([utc_time_str, local_time.strftime('%Y-%m-%d %H:%M:%S'),lstN,lstO, ts, tv,tsl,tsh])

            df = pd.DataFrame(data, columns=['UTC_Time', 'Local_Time', 'lstN','lstO','Ts', 'Tv','Tsl','Tsh'])

            # 先读取地面数据
            flux_csv = search_file(fluxnet_filter_dir, [site_name])
            if not len(flux_csv): continue
            infile = fluxnet_filter_dir + flux_csv[0]
            ground_data = pd.read_csv(infile)

            # 将地面数据的时间列转换为 datetime 对象
            ground_data['TIMESTAMP_START'] = pd.to_datetime(ground_data['TIMESTAMP_START'], format='%Y%m%d%H%M')
            ground_data['TIMESTAMP_END'] = pd.to_datetime(ground_data['TIMESTAMP_END'], format='%Y%m%d%H%M')

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
                    merged_row['TA_F_MDS'] += 273.15
                    merged_row['TS_F_MDS_1'] += 273.15
                    merged_data = pd.concat([merged_data, merged_row], axis=0)

            # 选择需要的列
            merged_data = merged_data[['UTC_Time', 'Local_Time','TIMESTAMP_START','TIMESTAMP_END', 'lstN','lstO','Ts', 'Tv','Tsl','Tsh', 'TS_F_MDS_1','SWC_F_MDS_1','TA_F_MDS','lst']]

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

if ifval_lst:
    mkdir_if_not_exist(lst_out_dir)
    fileNames = search_file(val_dir, ['.csv'])
    therhold = 9
    alldata = []
    for fileName in fileNames:
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
        lstN_inv = data['lstN']
        lstO_inv = data['lstO']
        lst_mea = data['lst']
        invalid_num = sum(np.abs(lstN_inv - lst_mea) < therhold)
        print("--------------------------------------------------------------------------------")
        print(fileName)
        print("有效点数：%03d" % invalid_num)
        if invalid_num == 0:
            continue
        bias_s, rmse_s, r2_s = cal_rmse_r2(lst_mea, lstN_inv, therhold)
        bias_v, rmse_v, r2_v = cal_rmse_r2(lst_mea, lstO_inv, therhold)
        print("lstN RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s[0]))
        print("lstO RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))

        # 绘制散点图
        plt.rc('font', family='Times New Roman', size=12)
        ind = (lstN_inv > 220) * (lstN_inv < 370) * (lstO_inv > 220) * (lstO_inv < 370) * (lst_mea > 220 ) * (lst_mea <370 )
        plt.figure(figsize=(4.5, 4))
        plt.scatter(lst_mea[ind], lstN_inv[ind], label='lstN', color='red')
        plt.scatter(lst_mea[ind], lstO_inv[ind], label='lstO', color='blue')
        plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
        plt.plot([220, 370], [215, 365], color='grey', linestyle='--')  # 添加y=x-5线
        plt.plot([220, 370], [225, 375], color='grey', linestyle='--')  # 添加y=x+5线
        plt.plot([220, 370], [210, 360], color='grey', linestyle='--')  # 添加y=x-10线
        plt.plot([220, 370], [230, 380], color='grey', linestyle='--')  # 添加y=x+10线
        plt.xlim(np.min(lst_mea) -10 , np.max(lst_mea + 10))
        plt.ylim(np.min(lst_mea) -10 , np.max(lst_mea + 10))
        plt.xlabel('Measured')
        plt.ylabel('Inversion')
        plt.title(fileName[:-4])
        plt.legend()

        # 保存图表
        output_path = lst_out_dir + fileName[:-4] + ".png"
        plt.savefig(output_path)
        plt.close()

    print("--------------------------------------------------------------------------------")
    print("ALL SITES")
    all_data_concatenated = pd.concat(alldata)
    lstN_inv = all_data_concatenated['lstN']
    lstO_inv = all_data_concatenated['lstO']
    lst_mea = all_data_concatenated['lst']
    invalid_num = sum(np.abs(lstN_inv - lst_mea) < therhold)
    print("有效点数：%03d" % invalid_num)
    ind = (lstN_inv > 270) * (lstN_inv < 370) * (lstO_inv > 270) * (lstO_inv < 370) * (lst_mea > 270) * (lst_mea < 370)
    bias_s, rmse_s, r2_s = cal_rmse_r2(lst_mea[ind],lstN_inv[ind], therhold)
    bias_v, rmse_v, r2_v = cal_rmse_r2(lst_mea[ind], lstO_inv[ind], therhold)
    print("lstN RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s[0]))
    print("lstO RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))
    # 绘制散点图
    ind = (lstN_inv > 270) * (lstN_inv < 370) * (lstO_inv > 270) * (lstO_inv < 370) * (lst_mea > 270 ) * (lst_mea <370)

    print("--------------------------------------------------------------------------------")
    print("Nadir温度散点密度图")
    # Calculate the point density for soil temperature


    xy_soil = np.vstack([lst_mea[ind], lstN_inv[ind]])
    z_soil = gaussian_kde(xy_soil)(xy_soil)

    # Sort the points by density, so that the densest points are plotted last
    idx_soil = z_soil.argsort()
    ts_mea_soil, ts_inv_soil, z_soil = lst_mea[ind].iloc[idx_soil], lstN_inv[ind].iloc[idx_soil], z_soil[idx_soil]

    plt.figure(figsize=(5, 4))
    sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([260, 330], [260, 330], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured  lst')
    plt.ylabel('Inverted lstN')
    plt.title("Density Scatter Plot of lstN")
    output_path = lst_out_dir + "ALL_SITES_lstN_Scatter_Density.png"
    plt.xlim(260,330)
    plt.ylim(260,330)
    plt.savefig(output_path)
    plt.close()

    print("--------------------------------------------------------------------------------")
    print("Oblique温度散点密度图")
    # Calculate the point density for vegetation temperature
    # Calculate the point density for vegetation temperature
    xy_vegetation = np.vstack([lst_mea[ind], lstO_inv[ind]])
    z_vegetation = gaussian_kde(xy_vegetation)(xy_vegetation)

    # Sort the points by density, so that the densest points are plotted last
    idx_vegetation = z_vegetation.argsort()
    ta_mea_vegetation, tv_inv_vegetation, z_vegetation = lst_mea[ind].iloc[idx_vegetation], lstO_inv[ind].iloc[
        idx_vegetation], z_vegetation[idx_vegetation]

    plt.figure(figsize=(5, 4))
    sc = plt.scatter(ta_mea_vegetation, tv_inv_vegetation, c=z_vegetation, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([260, 330], [260, 330], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured  lst')
    plt.ylabel('Inverted lstO')
    plt.title("Density Scatter Plot of lstO")
    output_path = lst_out_dir + "ALL_SITES_lstO_Scatter_Density.png"
    plt.xlim(260,330)
    plt.ylim(260,330)
    plt.savefig(output_path)
    plt.close()

if ifval_lst_soil:
    mkdir_if_not_exist(lst_soil_out_dir)
    # AATSR_lst 与 fluxnet soil
    fileNames = search_file(val_dir, ['.csv'])
    therhold = 10
    alldata = []
    for fileName in fileNames:
        infile = val_dir + fileName
        data = pd.read_csv(infile)
        alldata.append(data)
        lstN_inv = data['lstN']
        lstO_inv = data['lstO']
        lst_mea = data['TS_F_MDS_1']
        invalid_num = sum(np.abs(lstN_inv - lst_mea) < therhold)
        print("--------------------------------------------------------------------------------")
        print(fileName)
        print("有效点数：%03d" % invalid_num)
        if invalid_num == 0:
            continue
        bias_s, rmse_s, r2_s = cal_rmse_r2(lst_mea,lstN_inv, therhold)
        bias_v, rmse_v, r2_v = cal_rmse_r2(lst_mea,lstO_inv, therhold)
        print("lstN RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s[0]))
        print("lstO RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))

        # 绘制散点图
        ind = (lstN_inv > 220) * (lstN_inv < 370) * (lstO_inv > 220) * (lstO_inv < 370) * (lst_mea > 220 ) * (lst_mea <370 )
        plt.figure(figsize=(6, 6))
        plt.scatter(lst_mea[ind], lstN_inv[ind], label='lstN', color='red')
        plt.scatter(lst_mea[ind], lstO_inv[ind], label='lstO', color='green')
        plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
        plt.plot([220, 370], [215, 365], color='grey', linestyle='--')  # 添加y=x-5线
        plt.plot([220, 370], [225, 375], color='grey', linestyle='--')  # 添加y=x+5线
        plt.plot([220, 370], [210, 360], color='grey', linestyle='--')  # 添加y=x-10线
        plt.plot([220, 370], [230, 380], color='grey', linestyle='--')  # 添加y=x+10线
        plt.xlabel('Measured Ts')
        plt.ylabel('Inversion LST')
        plt.title(fileName[:-4])
        plt.legend()

        # 保存图表
        output_path = lst_soil_out_dir + fileName[:-4] + ".png"
        plt.savefig(output_path)
        plt.close()

    print("--------------------------------------------------------------------------------")
    print("ALL SITES")
    all_data_concatenated = pd.concat(alldata)
    lstN_inv = all_data_concatenated['lstN']
    lstO_inv = all_data_concatenated['lstO']
    lst_mea = all_data_concatenated['TS_F_MDS_1']
    invalid_num = sum(np.abs(lstN_inv - lst_mea) < therhold)
    print("有效点数：%03d" % invalid_num)
    bias_s, rmse_s, r2_s = cal_rmse_r2(lst_mea,lstN_inv, therhold)
    bias_v, rmse_v, r2_v = cal_rmse_r2(lst_mea,lstO_inv, therhold)
    print("lstN RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s[0]))
    print("lstO RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))
    # 绘制散点图
    ind = (lstN_inv > 220) * (lstN_inv < 370) * (lstO_inv > 220) * (lstO_inv < 370) * (lst_mea > 220 ) * (lst_mea <370 )

    print("--------------------------------------------------------------------------------")
    print("Nadir温度散点密度图")
    # Calculate the point density for soil temperature
    xy_soil = np.vstack([lst_mea[ind], lstN_inv[ind]])
    z_soil = gaussian_kde(xy_soil)(xy_soil)

    # Sort the points by density, so that the densest points are plotted last
    idx_soil = z_soil.argsort()
    ts_mea_soil, ts_inv_soil, z_soil = lst_mea[ind].iloc[idx_soil], lstN_inv[ind].iloc[idx_soil], z_soil[idx_soil]

    plt.figure(figsize=(8, 6))
    sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured  Ts')
    plt.ylabel('Inverted lstN')
    plt.title("Density Scatter Plot of lstN")
    output_path = lst_soil_out_dir + "ALL_SITES_lstN_Scatter_Density.png"
    plt.savefig(output_path)
    plt.close()

    print("--------------------------------------------------------------------------------")
    print("Oblique温度散点密度图")
    # Calculate the point density for vegetation temperature
    # Calculate the point density for vegetation temperature
    xy_vegetation = np.vstack([lst_mea[ind], lstO_inv[ind]])
    z_vegetation = gaussian_kde(xy_vegetation)(xy_vegetation)

    # Sort the points by density, so that the densest points are plotted last
    idx_vegetation = z_vegetation.argsort()
    ta_mea_vegetation, tv_inv_vegetation, z_vegetation = lst_mea[ind].iloc[idx_vegetation], lstO_inv[ind].iloc[
        idx_vegetation], z_vegetation[idx_vegetation]

    plt.figure(figsize=(8, 6))
    sc = plt.scatter(ta_mea_vegetation, tv_inv_vegetation, c=z_vegetation, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured  Ts')
    plt.ylabel('Inverted lstO')
    plt.title("Density Scatter Plot of lstO")
    output_path = lst_soil_out_dir + "ALL_SITES_lstO_Scatter_Density.png"
    plt.savefig(output_path)
    plt.close()

if ifval_lsct:
    mkdir_if_not_exist(lsct_out_dir)
    fileNames = search_file(val_dir,['.csv'])
    threshold = 9
    alldata = []
    for fileName in fileNames:
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
        data = filtered_data
        ts_inv = data['Ts']
        tv_inv = data['Tv']
        ts_mea = data['TS_F_MDS_1']
        ta_mea = data['TA_F_MDS']
        invalid_num = sum(np.abs(ts_mea-ts_inv)<threshold)
        print("--------------------------------------------------------------------------------")
        print(fileName)
        print("有效点数/总点数：%03d/%03d" % (invalid_num,sum(ts_inv!=0)))
        if invalid_num == 0:
            continue
        bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea,ts_inv,threshold)
        bias_v, rmse_v, r2_v = cal_rmse_r2(ta_mea, tv_inv, threshold)
        print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f"%(rmse_s, bias_s,  r2_s[0]))
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
        plt.xlim(np.min(ts_inv[ts_inv>200]) - 20 , np.max(ts_inv + 20))
        plt.ylim(np.min(ts_inv[ts_inv>200]) - 20, np.max(ts_inv + 20))
        plt.xlabel('Measured')
        plt.ylabel('Inversion')
        plt.title(fileName[:-4])
        plt.legend()

        # 保存图表
        output_path = lsct_out_dir + fileName[:-4] + ".png"
        plt.savefig(output_path)
        plt.close()

    print("--------------------------------------------------------------------------------")
    print("ALL SITES")
    all_data_concatenated = pd.concat(alldata)
    ts_inv = all_data_concatenated['Ts']
    tv_inv = all_data_concatenated['Tv']
    ts_mea = all_data_concatenated['TS_F_MDS_1']
    ta_mea = all_data_concatenated['TA_F_MDS']
    invalid_num = sum(np.abs(ts_mea - ts_inv) < threshold)
    print("有效点数：%03d" % invalid_num)
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea, ts_inv, threshold)
    bias_v, rmse_v, r2_v = cal_rmse_r2(ta_mea, tv_inv, threshold)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s[0]))
    print("植被 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))
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
    output_path = lsct_out_dir + "ALL_SITES_Soil_Temperature_Scatter_Density.png"
    plt.ylim([250, 340])
    plt.xlim([250, 340])
    plt.savefig(output_path)
    plt.close()

    print("--------------------------------------------------------------------------------")
    print("植被温度散点密度图")
    ind = (ta_mea > 270) * (ta_mea < 350) * (tv_inv > 270) * (tv_inv < 370) * (tv_inv != 273.15) * (ta_mea-tv_inv<20)
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
    plt.plot([270, 370], [270, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured Vegetation Temperature')
    plt.ylabel('Inverted Vegetation Temperature')
    # plt.title("Density Scatter Plot of Vegetation Temperature")
    plt.ylim([250, 340])
    plt.xlim([250, 340])
    output_path = lsct_out_dir + "ALL_SITES_Vegetation_Temperature_Scatter_Density.png"
    plt.savefig(output_path)
    plt.close()

    print("散点密度图已保存到", r"D:\data\AATSR_product\Fluxnet2015\graph 文件夹中")

    # print("--------------------------------------------------------------------------------")
    # print("土壤温度散点密度图")
    # plt.figure(figsize=(8, 6))
    #
    # # Calculate the point density
    # xy_soil = np.vstack([ts_mea[ind], ts_inv[ind]])  # 将两个维度的数据叠加
    # z_soil = gaussian_kde(xy_soil)(xy_soil)  # 建立概率密度分布，并计算每个样本点的概率密度
    #
    # # Sort the points by density, so that the densest points are plotted last
    # idx_soil = z_soil.argsort()
    # ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind][idx_soil], ts_inv[ind][idx_soil], z_soil[idx_soil]
    #
    # # Plot the scatter plot with density colors
    # plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    #
    # # Add colorbar
    # plt.colorbar()
    #
    # # Add auxiliary lines
    # plt.axhline(y=np.mean(ts_inv[ind]) - 5, color='grey', linestyle='--', linewidth=1)
    # plt.axhline(y=np.mean(ts_inv[ind]) + 5, color='grey', linestyle='--', linewidth=1)
    # plt.axhline(y=np.mean(ts_inv[ind]) - 10, color='grey', linestyle='--', linewidth=1)
    # plt.axhline(y=np.mean(ts_inv[ind]) + 10, color='grey', linestyle='--', linewidth=1)
    #
    # plt.xlabel('Measured Soil Temperature')
    # plt.ylabel('Inverted Soil Temperature')
    # plt.title("Density Scatter Plot of Soil Temperature")
    # output_path = r"D:\data\AATSR_product\Fluxnet2015\graph\\" + "ALL_SITES_Soil_Temperature_Scatter_Density.png"
    # plt.savefig(output_path)
    # plt.close()
    #
    # print("--------------------------------------------------------------------------------")
    # print("植被温度散点密度图")
    # plt.figure(figsize=(8, 6))
    #
    # # Calculate the point density
    # xy_vegetation = np.vstack([ta_mea[ind], tv_inv[ind]])  # 将两个维度的数据叠加
    # z_vegetation = gaussian_kde(xy_vegetation)(xy_vegetation)  # 建立概率密度分布，并计算每个样本点的概率密度
    #
    # # Sort the points by density, so that the densest points are plotted last
    # idx_vegetation = z_vegetation.argsort()
    # ta_mea_vegetation, tv_inv_vegetation, z_vegetation = ta_mea[ind][idx_vegetation], tv_inv[ind][idx_vegetation], \
    # z_vegetation[idx_vegetation]
    #
    # # Plot the scatter plot with density colors
    # plt.scatter(ta_mea_vegetation, tv_inv_vegetation, c=z_vegetation, s=20, cmap='Spectral')  # c表示标记的颜色
    #
    # # Add colorbar
    # plt.colorbar()
    #
    # # Add auxiliary lines
    # plt.axhline(y=np.mean(tv_inv[ind]) - 5, color='grey', linestyle='--', linewidth=1)
    # plt.axhline(y=np.mean(tv_inv[ind]) + 5, color='grey', linestyle='--', linewidth=1)
    # plt.axhline(y=np.mean(tv_inv[ind]) - 10, color='grey', linestyle='--', linewidth=1)
    # plt.axhline(y=np.mean(tv_inv[ind]) + 10, color='grey', linestyle='--', linewidth=1)
    #
    # plt.xlabel('Measured Vegetation Temperature')
    # plt.ylabel('Inverted Vegetation Temperature')
    # plt.title("Density Scatter Plot of Vegetation Temperature")
    # output_path = r"D:\data\AATSR_product\Fluxnet2015\graph\\" + "ALL_SITES_Vegetation_Temperature_Scatter_Density.png"
    # plt.savefig(output_path)
    # plt.close()
    #
    # print("散点密度图已保存到", r"D:\data\AATSR_product\Fluxnet2015\graph 文件夹中")

    # print("--------------------------------------------------------------------------------")
    # print("土壤温度散点密度图")
    # plt.figure(figsize=(6, 6))
    # sns.jointplot(x=ts_mea[ind], y=ts_inv[ind], kind='kde', color='red')
    # plt.xlabel('Measured Soil Temperature')
    # plt.ylabel('Inverted Soil Temperature')
    # plt.title("Density Scatter Plot of Soil Temperature")
    # output_path = r"D:\data\AATSR_product\Fluxnet2015\graph\\" + "ALL_SITES_Soil_Temperature_Scatter_Density.png"
    # plt.savefig(output_path)
    # plt.close()
    #
    # print("--------------------------------------------------------------------------------")
    # print("植被温度散点密度图")
    # plt.figure(figsize=(6, 6))
    # sns.jointplot(x=ta_mea[ind], y=tv_inv[ind], kind='kde', color='green')
    # plt.xlabel('Measured Vegetation Temperature')
    # plt.ylabel('Inverted Vegetation Temperature')
    # plt.title("Density Scatter Plot of Vegetation Temperature")
    # output_path = r"D:\data\AATSR_product\Fluxnet2015\graph\\" + "ALL_SITES_Vegetation_Temperature_Scatter_Density.png"
    # plt.savefig(output_path)
    # plt.close()

    # print("--------------------------------------------------------------------------------")
    # print("土壤温度密度图")
    # plt.figure(figsize=(7, 6))
    # sns.histplot(ts_mea[ind], kde=True, color='red', label='Measured Soil Temperature')
    # sns.histplot(ts_inv[ind], kde=True, color='blue', label='Inverted Soil Temperature')
    # plt.xlabel('Temperature')
    # plt.ylabel('Density')
    # plt.title("Soil Temperature Density")
    # plt.legend()
    # output_path = r"D:\data\AATSR_product\Fluxnet2015\graph\\" + "ALL_SITES_Soil_Temperature_Density.png"
    # plt.savefig(output_path)
    # plt.close()
    #
    # print("--------------------------------------------------------------------------------")
    # print("植被温度密度图")
    # plt.figure(figsize=(7, 6))
    # sns.histplot(ta_mea[ind], kde=True, color='green', label='Measured Vegetation Temperature')
    # sns.histplot(tv_inv[ind], kde=True, color='purple', label='Inverted Vegetation Temperature')
    # plt.xlabel('Temperature')
    # plt.ylabel('Density')
    # plt.title("Vegetation Temperature Density")
    # plt.legend()
    # output_path = r"D:\data\AATSR_product\Fluxnet2015\graph\\" + "ALL_SITES_Vegetation_Temperature_Density.png"
    # plt.savefig(output_path)
    # plt.close()

if ifval_ts_lst:
    mkdir_if_not_exist(soil_lst_dir)
    fileNames = search_file(val_dir,['.csv'])
    therhold = 10
    alldata = []
    for fileName in fileNames:
        infile = val_dir + fileName
        data = pd.read_csv(infile)
        alldata.append(data)
        ts_inv = data['Tsh']
        tv_inv = data['Tv']
        ts_mea = data['lst']
        ta_mea = data['TA_F_MDS']
        invalid_num = sum(np.abs(ts_mea-ts_inv)<therhold)
        print("--------------------------------------------------------------------------------")
        print(fileName)
        print("有效点数/总点数：%03d/%03d" % (invalid_num,sum(ts_inv!=0)))
        if invalid_num == 0:
            continue
        bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea,ts_inv,therhold)
        bias_v, rmse_v, r2_v = cal_rmse_r2(ta_mea, tv_inv, therhold)
        print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f"%(rmse_s, bias_s,  r2_s[0]))
        print("植被 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))

        # 绘制散点图
        ind = (ts_mea > 270) * (ts_mea < 320) * (ts_inv > 270) * (ts_inv < 320) * (ts_inv != 273.15)
        plt.figure(figsize=(6, 6))
        plt.scatter(ts_mea[ind], ts_inv[ind], label='Soil', color='red')
        # plt.scatter(ta_mea[ind], tv_inv[ind], label='Vegetation', color='green')
        plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
        plt.plot([220, 370], [215, 365], color='grey', linestyle='--')  # 添加y=x-5线
        plt.plot([220, 370], [225, 375], color='grey', linestyle='--')  # 添加y=x+5线
        plt.plot([220, 370], [210, 360], color='grey', linestyle='--')  # 添加y=x-10线
        plt.plot([220, 370], [230, 380], color='grey', linestyle='--')  # 添加y=x+10线
        plt.xlabel('Measured')
        plt.ylabel('Inversion')
        plt.title(fileName[:-4])
        plt.ylim([270,320])
        plt.xlim([270,320])
        plt.legend()

        # 保存图表
        output_path = soil_lst_dir + fileName[:-4] + ".png"
        plt.savefig(output_path)
        plt.close()

    print("--------------------------------------------------------------------------------")
    print("ALL SITES")
    all_data_concatenated = pd.concat(alldata)
    ts_inv = all_data_concatenated['Tsh']
    tv_inv = all_data_concatenated['Tv']
    ts_mea = all_data_concatenated['lst']
    ta_mea = all_data_concatenated['TA_F_MDS']
    invalid_num = sum(np.abs(ts_mea - ts_inv) < therhold)
    print("有效点数：%03d" % invalid_num)
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea, ts_inv, therhold)
    bias_v, rmse_v, r2_v = cal_rmse_r2(ta_mea, tv_inv, therhold)
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s[0]))
    print("植被 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))
    # 绘制散点图
    ind = (ts_mea > 220) * (ts_mea < 370) * (ts_inv > 220) * (ts_inv < 370) * (ts_inv != 273.15)

    print("--------------------------------------------------------------------------------")
    print("土壤温度散点密度图")
    # Calculate the point density for soil temperature
    xy_soil = np.vstack([ts_mea[ind], ts_inv[ind]])
    z_soil = gaussian_kde(xy_soil)(xy_soil)

    # Sort the points by density, so that the densest points are plotted last
    idx_soil = z_soil.argsort()
    ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind].iloc[idx_soil], ts_inv[ind].iloc[idx_soil], z_soil[idx_soil]

    plt.figure(figsize=(8, 6))
    sc = plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured Soil Temperature')
    plt.ylabel('Inverted Soil Temperature')
    plt.title("Density Scatter Plot of Soil Temperature")
    output_path = soil_lst_dir + "ALL_SITES_Soil_Temperature_Scatter_Density.png"
    plt.savefig(output_path)
    plt.close()

    print("--------------------------------------------------------------------------------")
    print("植被温度散点密度图")
    # Calculate the point density for vegetation temperature
    # Calculate the point density for vegetation temperature
    xy_vegetation = np.vstack([ta_mea[ind], tv_inv[ind]])
    z_vegetation = gaussian_kde(xy_vegetation)(xy_vegetation)

    # Sort the points by density, so that the densest points are plotted last
    idx_vegetation = z_vegetation.argsort()
    ta_mea_vegetation, tv_inv_vegetation, z_vegetation = ta_mea[ind].iloc[idx_vegetation], tv_inv[ind].iloc[
        idx_vegetation], z_vegetation[idx_vegetation]

    plt.figure(figsize=(8, 6))
    sc = plt.scatter(ta_mea_vegetation, tv_inv_vegetation, c=z_vegetation, s=20, cmap='Spectral')  # c表示标记的颜色
    plt.colorbar(sc)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel('Measured Vegetation Temperature')
    plt.ylabel('Inverted Vegetation Temperature')
    plt.title("Density Scatter Plot of Vegetation Temperature")
    output_path = soil_lst_dir + "ALL_SITES_Vegetation_Temperature_Scatter_Density.png"
    plt.savefig(output_path)
    plt.close()

    print("散点密度图已保存到", r"D:\data\AATSR_product\Fluxnet2015\graph 文件夹中")

    # print("--------------------------------------------------------------------------------")
    # print("土壤温度散点密度图")
    # plt.figure(figsize=(8, 6))
    #
    # # Calculate the point density
    # xy_soil = np.vstack([ts_mea[ind], ts_inv[ind]])  # 将两个维度的数据叠加
    # z_soil = gaussian_kde(xy_soil)(xy_soil)  # 建立概率密度分布，并计算每个样本点的概率密度
    #
    # # Sort the points by density, so that the densest points are plotted last
    # idx_soil = z_soil.argsort()
    # ts_mea_soil, ts_inv_soil, z_soil = ts_mea[ind][idx_soil], ts_inv[ind][idx_soil], z_soil[idx_soil]
    #
    # # Plot the scatter plot with density colors
    # plt.scatter(ts_mea_soil, ts_inv_soil, c=z_soil, s=20, cmap='Spectral')  # c表示标记的颜色
    #
    # # Add colorbar
    # plt.colorbar()
    #
    # # Add auxiliary lines
    # plt.axhline(y=np.mean(ts_inv[ind]) - 5, color='grey', linestyle='--', linewidth=1)
    # plt.axhline(y=np.mean(ts_inv[ind]) + 5, color='grey', linestyle='--', linewidth=1)
    # plt.axhline(y=np.mean(ts_inv[ind]) - 10, color='grey', linestyle='--', linewidth=1)
    # plt.axhline(y=np.mean(ts_inv[ind]) + 10, color='grey', linestyle='--', linewidth=1)
    #
    # plt.xlabel('Measured Soil Temperature')
    # plt.ylabel('Inverted Soil Temperature')
    # plt.title("Density Scatter Plot of Soil Temperature")
    # output_path = r"D:\data\AATSR_product\Fluxnet2015\graph\\" + "ALL_SITES_Soil_Temperature_Scatter_Density.png"
    # plt.savefig(output_path)
    # plt.close()
    #
    # print("--------------------------------------------------------------------------------")
    # print("植被温度散点密度图")
    # plt.figure(figsize=(8, 6))
    #
    # # Calculate the point density
    # xy_vegetation = np.vstack([ta_mea[ind], tv_inv[ind]])  # 将两个维度的数据叠加
    # z_vegetation = gaussian_kde(xy_vegetation)(xy_vegetation)  # 建立概率密度分布，并计算每个样本点的概率密度
    #
    # # Sort the points by density, so that the densest points are plotted last
    # idx_vegetation = z_vegetation.argsort()
    # ta_mea_vegetation, tv_inv_vegetation, z_vegetation = ta_mea[ind][idx_vegetation], tv_inv[ind][idx_vegetation], \
    # z_vegetation[idx_vegetation]
    #
    # # Plot the scatter plot with density colors
    # plt.scatter(ta_mea_vegetation, tv_inv_vegetation, c=z_vegetation, s=20, cmap='Spectral')  # c表示标记的颜色
    #
    # # Add colorbar
    # plt.colorbar()
    #
    # # Add auxiliary lines
    # plt.axhline(y=np.mean(tv_inv[ind]) - 5, color='grey', linestyle='--', linewidth=1)
    # plt.axhline(y=np.mean(tv_inv[ind]) + 5, color='grey', linestyle='--', linewidth=1)
    # plt.axhline(y=np.mean(tv_inv[ind]) - 10, color='grey', linestyle='--', linewidth=1)
    # plt.axhline(y=np.mean(tv_inv[ind]) + 10, color='grey', linestyle='--', linewidth=1)
    #
    # plt.xlabel('Measured Vegetation Temperature')
    # plt.ylabel('Inverted Vegetation Temperature')
    # plt.title("Density Scatter Plot of Vegetation Temperature")
    # output_path = r"D:\data\AATSR_product\Fluxnet2015\graph\\" + "ALL_SITES_Vegetation_Temperature_Scatter_Density.png"
    # plt.savefig(output_path)
    # plt.close()
    #
    # print("散点密度图已保存到", r"D:\data\AATSR_product\Fluxnet2015\graph 文件夹中")

    # print("--------------------------------------------------------------------------------")
    # print("土壤温度散点密度图")
    # plt.figure(figsize=(6, 6))
    # sns.jointplot(x=ts_mea[ind], y=ts_inv[ind], kind='kde', color='red')
    # plt.xlabel('Measured Soil Temperature')
    # plt.ylabel('Inverted Soil Temperature')
    # plt.title("Density Scatter Plot of Soil Temperature")
    # output_path = r"D:\data\AATSR_product\Fluxnet2015\graph\\" + "ALL_SITES_Soil_Temperature_Scatter_Density.png"
    # plt.savefig(output_path)
    # plt.close()
    #
    # print("--------------------------------------------------------------------------------")
    # print("植被温度散点密度图")
    # plt.figure(figsize=(6, 6))
    # sns.jointplot(x=ta_mea[ind], y=tv_inv[ind], kind='kde', color='green')
    # plt.xlabel('Measured Vegetation Temperature')
    # plt.ylabel('Inverted Vegetation Temperature')
    # plt.title("Density Scatter Plot of Vegetation Temperature")
    # output_path = r"D:\data\AATSR_product\Fluxnet2015\graph\\" + "ALL_SITES_Vegetation_Temperature_Scatter_Density.png"
    # plt.savefig(output_path)
    # plt.close()

    # print("--------------------------------------------------------------------------------")
    # print("土壤温度密度图")
    # plt.figure(figsize=(7, 6))
    # sns.histplot(ts_mea[ind], kde=True, color='red', label='Measured Soil Temperature')
    # sns.histplot(ts_inv[ind], kde=True, color='blue', label='Inverted Soil Temperature')
    # plt.xlabel('Temperature')
    # plt.ylabel('Density')
    # plt.title("Soil Temperature Density")
    # plt.legend()
    # output_path = r"D:\data\AATSR_product\Fluxnet2015\graph\\" + "ALL_SITES_Soil_Temperature_Density.png"
    # plt.savefig(output_path)
    # plt.close()
    #
    # print("--------------------------------------------------------------------------------")
    # print("植被温度密度图")
    # plt.figure(figsize=(7, 6))
    # sns.histplot(ta_mea[ind], kde=True, color='green', label='Measured Vegetation Temperature')
    # sns.histplot(tv_inv[ind], kde=True, color='purple', label='Inverted Vegetation Temperature')
    # plt.xlabel('Temperature')
    # plt.ylabel('Density')
    # plt.title("Vegetation Temperature Density")
    # plt.legend()
    # output_path = r"D:\data\AATSR_product\Fluxnet2015\graph\\" + "ALL_SITES_Vegetation_Temperature_Density.png"
    # plt.savefig(output_path)
    # plt.close()