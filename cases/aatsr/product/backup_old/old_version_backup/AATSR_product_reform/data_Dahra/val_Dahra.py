import csv
from utils.old.util import *
from datetime import datetime

'''2025.2.8'''
'''Dahra validation'''

def cal_rmse_r2(data1,data2,tshred=10):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2

base_dir = r"/home/hero/data/AATSR/Dahra/"
indir_h5 = r'/home/hero/data/AATSR/Dahra/SN-Dhr/'
extract_file = base_dir + 'extract.csv'
merge_file = base_dir + 'merge.csv'
measure_file = base_dir + 'Dahra_LST_Apogee_forMatchup_extend.xlsx'

if_extract = 1
if_merge = 1

if if_extract:
    if os.path.exists(extract_file): os.remove(extract_file)
    h5Files = search_file_rej(indir_h5, ".h5", "enp")
    h5Files.sort()
    for h5File in h5Files:
        infile = indir_h5 + h5File
        # if os.path.getsize(infile) < 8000: continue
        print(h5File)
        year = int(h5File.split('_')[1])
        doy = int(h5File.split('_')[2])
        month, day = doy2date(year, doy)

        '''读取数据'''
        name_list = ["lon", 'lat', "indx", "indy", "ref_indx", "ref_indy", "sec", "ref_time", "type", "emis_s",
                     "emis_v", 'vzaN', 'vzaO', 'vaaN', 'vaaO', 'clo', "lstN", "lstO", "Ts0", "Tv0", "Ts1", "Tv1", "Ts2",
                     "Tv2"]
        lon, lat, indx, indy, ref_indx, ref_indy, sec, ref_time, type, emis_s, emis_v, vzaN, vzaO, vaaN, vaaO, clo, lstN, lstO, Ts0, Tv0, Ts1, Tv1, Ts2, Tv2 = read_h5py_items(
            infile, name_list)
        nl, ns = np.shape(indx)
        checked_items = []
        for item in [lon, lat, indx, indy, ref_indx, ref_indy, sec, ref_time, type, emis_s, emis_v, vzaN, vzaO, vaaN,
                     vaaO, clo, lstN, lstO, Ts0, Tv0, Ts1, Tv1, Ts2, Tv2]:
            if item == []:
                item = np.zeros([nl, ns])
            checked_items.append(item)
        lon, lat, indx, indy, ref_indx, ref_indy, sec, ref_time, type, emis_s, emis_v, vzaN, vzaO, vaaN, vaaO, clo, lstN, lstO, Ts0, Tv0, Ts1, Tv1, Ts2, Tv2 = checked_items
        mask_x = indx == ref_indx
        mask_y = indy == ref_indy -1
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

        with open(extract_file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [time_save, lstN_save, lstO_save, Ts0_save, Tv0_save, Ts1_save, Tv1_save, Ts2_save, Tv2_save])

if if_merge == 1:
    if os.path.exists(merge_file): os.remove(merge_file)
    infile = measure_file
    df = pd.read_excel(infile, skiprows=[0, 2, 3], index_col=0, parse_dates=True,
                       date_parser=lambda x: pd.to_datetime(x, format='%Y/%m/%d %H:%M:%S'))
    df_selected = df.loc[:, ['Apogee grass', 'apogee  crown', 'apogee shade']]

    extract_df = pd.read_csv(extract_file, parse_dates=[0], header=None,
                             names=['Time', 'lstN', 'lstO', 'Ts0', 'Tv0', 'Ts1', 'Tv1', 'Ts2', 'Tv2'])

    merged_data = []
    for _, row in extract_df.iterrows():
        search_time = row['Time']
        filtered_data = df_selected[(df_selected.index >= search_time - pd.Timedelta(minutes=7.5)) &
                                    (df_selected.index <= search_time + pd.Timedelta(minutes=7.5))]

        if filtered_data.empty:
            merged_data.append([search_time, row['lstN'], row['lstO'], row['Ts0'], row['Tv0'],
                                row['Ts1'], row['Tv1'], row['Ts2'], row['Tv2'], 0, 0, 0])
        else:
            nearest_row = filtered_data.iloc[0]
            merged_data.append([search_time, row['lstN'], row['lstO'], row['Ts0'], row['Tv0'],
                                row['Ts1'], row['Tv1'], row['Ts2'], row['Tv2'],
                                nearest_row['Apogee grass'] + 273.15,
                                nearest_row['apogee  crown'] + 273.15,
                                nearest_row['apogee shade'] + 273.15])

    merged_df = pd.DataFrame(merged_data, columns=['Time', 'lstN', 'lstO', 'Ts0', 'Tv0', 'Ts1', 'Tv1', 'Ts2', 'Tv2',
                                                   'Tg', 'Tc', 'Tshade'])
    merged_df.to_csv(merge_file, index=False)

    lstN_inv, lstO_inv = merged_df['lstN'], merged_df['lstO']
    Ts_inv, Tv_inv = merged_df['Ts2'], merged_df['Tv2']
    Ts_mea, Tv_mea = merged_df['Tg'], merged_df['Tc']
    ind = (Ts_mea > 250) * (Ts_mea < 350) * (Ts_inv > 250) * (Ts_inv < 350) * (Ts_inv != 273.15)

    threshold = 9
    bias_s, rmse_s, r2_s = cal_rmse_r2(Ts_mea[ind], Ts_inv[ind], threshold)
    bias_v, rmse_v, r2_v = cal_rmse_r2(Tv_mea[ind], Tv_inv[ind], threshold)
    print('有效点数： %d, %d' %(sum(np.abs(Ts_mea[ind]-Ts_inv[ind])<threshold), sum(np.abs(Tv_mea[ind]-Tv_inv[ind])<threshold)))
    print("土壤 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_s, bias_s, r2_s[0]))
    print("植被 RMSE/Bias/R2: %.3f/%.3f/%.3f" % (rmse_v, bias_v, r2_v[0]))

    # 绘制散点图
    plt.figure(figsize=(4.5, 4))
    plt.scatter(Ts_mea[ind], Ts_inv[ind], label='Soil', color='red')
    plt.scatter(Tv_mea[ind], Tv_inv[ind], label='Vegetation', color='green')
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.plot([220, 370], [215, 365], color='grey', linestyle='--')  # 添加y=x-5线
    plt.plot([220, 370], [225, 375], color='grey', linestyle='--')  # 添加y=x+5线
    plt.plot([220, 370], [210, 360], color='grey', linestyle='--')  # 添加y=x-10线
    plt.plot([220, 370], [230, 380], color='grey', linestyle='--')  # 添加y=x+10线
    plt.xlim(np.min(Ts_inv[Ts_inv > 200]) - 10, np.max(Ts_inv[ind] + 10))
    plt.ylim(np.min(Ts_inv[Ts_inv > 200]) - 10, np.max(Ts_inv[ind] + 10))
    plt.xlabel('Measured')
    plt.ylabel('Inversion')
    # plt.title(fileName[:-4])
    plt.legend()
    plt.show()


