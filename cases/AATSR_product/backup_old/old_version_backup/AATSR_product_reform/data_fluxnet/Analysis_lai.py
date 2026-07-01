from utils.old.util import *
import csv
from datetime import datetime
from timezonefinder import TimezoneFinder
import pytz

'''2024.10.14'''
'''站点上分析LAI影响'''
'''采用Li的方法，对Fluxnet站点附近数据进行计算，假设LST\植被\土壤温度只与LAI有关，在5*5窗口内，选择斜率中位数作为斜率'''

'''
具体实现：
1.读取站点所有h5
2.计算周围5*5所有像元与中心像元 delta lst/ delta lai
3.取中位数
4.保存 站点名称 经度 纬度 年月日 当地时 地表类型 dlst/dlai dTs/dlai dTv/dLAI dTsl/dlai dTsh/dlai
'''

indir = r"/home/hero/data/Fluxnet/AATSR_data/2_lsct3_h5/"
site_names = search_dir(indir,'')
site_names.sort()
indir_Fluxnet = r"/home/hero/data/Fluxnet/Fluxnet_data/"
infile_site_imagexy = indir_Fluxnet + r"FLUXSITE_imagexy.csv"
# outfile = indir_Fluxnet + r"dlai_median.csv"
outfile = indir_Fluxnet + r"dlai_ave.csv"


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

fluxnet_loc_file = infile_site_imagexy
fluxnet_locations = read_fluxnet_locations(fluxnet_loc_file)

for site_name in site_names:
    print(site_name)
    indir_site = indir + site_name + r"/"
    filenames = search_file(indir_site,['h5'])
    filenames.sort()
    lat, lon = fluxnet_locations[site_name]
    timezone = get_timezone(lat, lon)

    for filename in filenames:
        print(filename)
        infile = indir_site + filename
        year = int(filename.split('_')[1])
        doy = int(filename.split('_')[2])
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

        mask_x, mask_y = np.argwhere(np.bitwise_and(indx == ref_indx, indy == ref_indy))[0][0], \
        np.argwhere(np.bitwise_and(indx == ref_indx, indy == ref_indy))[0][1]

        lstN_w = lstN[mask_x-2:mask_x+3, mask_y-2:mask_y+3]/100
        lstO_w = lstO[mask_x-2:mask_x+3, mask_y-2:mask_y+3]/100
        Ts_w = Ts[mask_x-2:mask_x+3, mask_y-2:mask_y+3]/100
        Tv_w = Tv[mask_x-2:mask_x+3, mask_y-2:mask_y+3]/100
        Tsl_w = Tsl[mask_x-2:mask_x+3, mask_y-2:mask_y+3]/100
        Tsh_w = Tsh[mask_x-2:mask_x+3, mask_y-2:mask_y+3]/100
        lai_w = lai[mask_x-2:mask_x+3, mask_y-2:mask_y+3]
        lai_w[lai_w > 10] = lai_w[lai_w>10] / 1000
        type_w = type[mask_x-2:mask_x+3, mask_y-2:mask_y+3]
        clo_w = clo[mask_x-2:mask_x+3, mask_y-2:mask_y+3]

        if len(type_w.flatten()) == 0: continue
        mask_w = (type_w == type_w[2,2]) * (Ts_w != 0) * (lstN_w != 0)
        dlai = lai_w - lai_w[2,2]
        mask_w = mask_w * (np.abs(dlai) > 0.1)
        if mask_w.sum() < 5: continue
        # dlstN = np.median((lstN_w - lstN_w[2,2])[mask_w]/dlai[mask_w])
        # dlstO = np.median((lstO_w - lstO_w[2, 2])[mask_w] / dlai[mask_w])
        # dTs = np.median((Ts_w - Ts_w[2, 2])[mask_w] / dlai[mask_w])
        # dTv = np.median((Tv_w - Tv_w[2, 2])[mask_w] / dlai[mask_w])
        # dTsl = np.median((Tsl_w - Tsl_w[2, 2])[mask_w] / dlai[mask_w])
        # dTsh = np.median((Tsh_w - Tsh_w[2, 2])[mask_w] / dlai[mask_w]).
        dlstN = np.average((lstN_w - lstN_w[2,2])[mask_w]/dlai[mask_w])
        dlstO = np.average((lstO_w - lstO_w[2, 2])[mask_w] / dlai[mask_w])
        dTs = np.average((Ts_w - Ts_w[2, 2])[mask_w] / dlai[mask_w])
        dTv = np.average((Tv_w - Tv_w[2, 2])[mask_w] / dlai[mask_w])
        dTsl = np.average((Tsl_w - Tsl_w[2, 2])[mask_w] / dlai[mask_w])
        dTsh = np.average((Tsh_w - Tsh_w[2, 2])[mask_w] / dlai[mask_w])

        if isnan(dlstN):
            print('stop')

        print(dlstN,dlstO,dTs,dTv,dTsl,dTsh)

        if isinstance(sec, np.ndarray) and (sec.size == 1):
            sec = sec
        else:
            sec = int(sec[mask_x, mask_y])
        h = sec // 3600
        m = (sec - h * 3600) // 60
        s = sec - h * 3600 - m * 60
        if h >= 24: h = h - 24
        time_save = datetime(year, month, day, int(h), int(m), int(s))
        local_time = time_save.replace(tzinfo=pytz.utc).astimezone(timezone)

        columns = ['site_name','lon','lat','date','time','type','dlstN/dlai','dlstO/dlai', 'dTs/dlai', 'dTv/dlai', 'dTsl/dlai', 'dTsh/dlai']
        with open(outfile, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # 写入表头（如果文件是空的）
            if csvfile.tell() == 0:
                writer.writerow(columns)

            # 写入一行数据
            writer.writerow([
                site_name, lon, lat, local_time.strftime('%Y-%m-%d'), local_time.strftime('%H:%M:%S'),
                type_w[2, 2], dlstN,dlstO, dTs, dTv, dTsl, dTsh
            ])