from utils.old.util import *
import csv
from datetime import datetime
from timezonefinder import TimezoneFinder
import pytz

'''2024.9.21'''
'''站点数据提取看相关性'''
'''
1.AATSR_stats:逐站点提取，每个站点一个csv
2.Merge_all:逐站点，AATSR + Fluxnet 合并
3.Merge_ind:加入站点干旱指数和植被指数
'''

if __name__ == '__main__':
    base_dir = r'/home/hero/data/Fluxnet/'
    indir_h5 = base_dir + 'AATSR_data/' + r'2_lsct3_h5//'

    indir_Fluxnet = r"/home/hero/data/Fluxnet/Fluxnet_data/"
    infile_site = indir_Fluxnet + r"FLUXSITE.xlsx"
    infile_site_imagexy = indir_Fluxnet + r"FLUXSITE_imagexy.csv"
    indir_Fluxnet_data = indir_Fluxnet + r"Fluxnet_csv_2002-2012/"

    outdir = base_dir + 'Merge/'
    outdir_AATSR_stats = outdir + 'AATSR_stats/'
    outdir_Merge_all = outdir + 'Merge_all/'
    outdir_Merge_ind = outdir + 'Merge_ind/'
    # outdir_Merge_month = outdir + 'Merge_month/'


    if_AATSR_stats = 0
    if_Merge_all = 0
    if_Merge_ind = 1

    if if_AATSR_stats:
        mkdir_if_not_exist(outdir_AATSR_stats)
        siteNames = search_dir(indir_h5, '')
        for siteName in siteNames:
            indir = indir_h5 + siteName + r"/"
            outfile = outdir_AATSR_stats + siteName + ".csv"
            if os.path.exists(outfile): continue
            print(outfile)
            h5Files = search_file_rej(indir, ".h5", "enp")
            h5Files.sort()

            with open(outfile, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Time", "LAI", "LSTN", "LSTO", "Ts", "Tv", "Tsl", "Tsh"])

            for h5File in h5Files:
                infile = indir + h5File
                # if os.path.getsize(infile) < 8000: continue
                year = int(h5File.split('_')[1])
                doy = int(h5File.split('_')[2])
                month, day = doy2date(year, doy)

                '''读取数据'''
                name_list = ["indx", "indy", "ref_indx", "ref_indy", "type", "lai", "sec", "ref_time", "lstN", "lstO",
                             "Ts", "Tv", 'Tsl', 'Tsh', 'clo']
                indx, indy, ref_indx, ref_indy, type, lai, sec, ref_time, lstN, lstO, Ts, Tv, Tsl, Tsh, clo = read_h5py_items(
                    infile, name_list)
                nl, ns = np.shape(indx)
                checked_items = []
                for item in [indx, indy, ref_indx, ref_indy, type, lai, sec, ref_time, lstN, lstO, Ts, Tv, Tsl, Tsh,
                             clo]:
                    if item == []:
                        item = np.zeros([nl, ns])
                    checked_items.append(item)
                indx, indy, ref_indx, ref_indy, type, lai, sec, ref_time, lstN, lstO, Ts, Tv, Tsl, Tsh, clo = checked_items
                mask_x = indx == ref_indx
                mask_y = indy == ref_indy
                ind = np.bitwise_and(mask_x, mask_y)
                if sum(ind) == 0: continue
                if np.average(Tsh[ind]) < 220:
                    continue
                if isinstance(sec, np.ndarray) and (sec.size == 1):
                    sec = sec
                else:
                    sec = int(sec[ind][0])
                h = sec // 3600
                m = (sec - h * 3600) // 60
                s = sec - h * 3600 - m * 60
                if h >= 24: h = h - 24
                time_save = datetime(year, month, day, int(h), int(m), int(s))
                lai_save = np.average(lai[ind])
                lstN_save = np.average(lstN[ind]) / 100
                lstO_save = np.average(lstO[ind]) / 100
                Ts_save = np.average(Ts[ind])
                Tv_save = np.average(Tv[ind])
                Tsl_save = np.average(Tsl[ind])
                Tsh_save = np.average(Tsh[ind])

                with open(outfile, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([time_save, lai_save, lstN_save, lstO_save, Ts_save, Tv_save, Tsl_save, Tsh_save])

    if if_Merge_all:
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

        mkdir_if_not_exist(outdir_Merge_all)
        fluxnet_loc_file = infile_site_imagexy
        fluxnet_locations = read_fluxnet_locations(fluxnet_loc_file)

        fileNames = search_file(outdir_AATSR_stats, ['.csv'])
        for fileName in fileNames:
            site_name = fileName[:-4]
            print(site_name)
            if site_name in fluxnet_locations:
                lat, lon = fluxnet_locations[site_name]
                timezone = get_timezone(lat, lon)
                infile = outdir_AATSR_stats + fileName
                data = []
                with open(infile, newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)
                    for row in reader:
                        utc_time_str = row[0]  # 假设 UTC 时间在第一列
                        utc_time = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
                        local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone)
                        LAI = float(row[1])
                        lstN = float(row[2])
                        lstO = float(row[3])
                        ts = float(row[4])  # 假设 Ts 在第五列
                        tv = float(row[5])  # 假设 Tv 在第六列
                        tsl = float(row[6])  # 假设 Ts 在第五列
                        tsh = float(row[7])  # 假设 Tv 在第六列
                        data.append(
                            [utc_time_str, local_time.strftime('%Y-%m-%d %H:%M:%S'),LAI, lstN, lstO, ts, tv, tsl, tsh])

                df = pd.DataFrame(data, columns=['UTC_Time', 'Local_Time','LAI', 'lstN', 'lstO', 'Ts', 'Tv', 'Tsl', 'Tsh'])

                # 先读取地面数据
                flux_csv = search_file(indir_Fluxnet_data, [site_name])
                if not len(flux_csv):
                    print("Fluxnet no data!")
                    continue
                if len(df) ==0:
                    print("AATSR no data!")
                    continue

                infile = indir_Fluxnet_data + flux_csv[0]
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
                merged_data = merged_data[
                    ['UTC_Time', 'Local_Time', 'TIMESTAMP_START', 'TIMESTAMP_END', 'lstN', 'lstO', 'Ts', 'Tv', 'Tsl',
                     'Tsh','LAI', 'TS_F_MDS_1', 'SWC_F_MDS_1', 'TA_F_MDS', 'lst']]

                # 保存合并后的数据到 CSV 文件
                output_file = outdir_Merge_all + site_name + ".csv"
                merged_data.to_csv(output_file, index=False)

                print("合并后的数据已保存到", output_file)

    if if_Merge_ind:
        mkdir_if_not_exist(outdir_Merge_all)





