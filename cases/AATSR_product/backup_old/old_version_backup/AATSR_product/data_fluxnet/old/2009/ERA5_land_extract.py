from netCDF4 import Dataset
from utils.old.util import *

'''2024.3.17'''
'''从nc文件中提取值'''
'''从ERA5 land中提取数据到AATSR与fluxnet的csv中'''
'''请先运行AATSR_val_lsct.py'''

def read_data_scale_offset(nc_file, variable_name):
    with Dataset(nc_file, 'r') as nc:
        nc.variables[variable_name].set_auto_maskandscale(False)
        var = nc.variables[variable_name]
        scale_factor = var.scale_factor if hasattr(var, 'scale_factor') else 1.0
        add_offset = var.add_offset if hasattr(var, 'add_offset') else 0.0
        original_data = var[:]
    return original_data, scale_factor, add_offset


ERA5_base_dir = r"H:\ERA5_land\\"
AATSR_val_dir = r"D:\data\AATSR_product\Fluxnet2015\Validation_csv\\"
# ERA5_val_dir = r"D:\data\AATSR_product\Fluxnet2015\Validation_csv_ERA5\\"
site_loc_file = r"D:\data\AATSR_product\Fluxnet2015\\FLUXSITE_imagexy.csv"

'''读取站点经纬度'''
data = pd.read_csv(site_loc_file)
site_id = data["SITE_ID"]
site_lon = data["LOCATION_LONG"]
site_lat = data["LOCATION_LAT"]

# lon lat
vertical_values = np.arange(900, -901, -1)
horizontal_values = np.arange(0, 3600, 1)
lon_map = np.tile(horizontal_values, (len(vertical_values), 1))
lat_map = np.tile(vertical_values, (len(horizontal_values), 1)).T

for year in range(2009,2010):
    ERA5_dir_year = ERA5_base_dir + "%04d//" % year
    for month in range(3,13):
        ERA5_t2m_file = ERA5_dir_year + "2m_temperature//" + "%04d%02d.nc" % (year,month)
        ERA5_skin_file = ERA5_dir_year + "skin_temperature//" + "%04d%02d.nc" % (year, month)
        ERA5_ts1_file = ERA5_dir_year + "soil_temperature_level_1//" + "%04d%02d.nc" % (year, month)
        # t2m = read_image_Nc(ERA5_t2m_file,"t2m",ifscale=1)
        t2m_raw,t2m_scale_factor, t2m_add_offset = read_data_scale_offset(ERA5_t2m_file,"t2m")
        skt_raw, skt_scale_factor, skt_add_offset = read_data_scale_offset(ERA5_skin_file, "skt")
        stl1_raw, stl1_scale_factor, stl1_add_offset = read_data_scale_offset(ERA5_ts1_file, "stl1")

        time = read_image_Nc(ERA5_t2m_file,"time",ifscale=0)
        time_max = np.max(time)
        time_min = np.min(time)

        siteNames = search_file(AATSR_val_dir,['.csv'])
        for fileName in siteNames:
            siteName = fileName[:-4]
            print(siteName)
            infile = AATSR_val_dir + fileName

            '''空间匹配'''
            lon_ = site_lon[site_id==siteName].values
            if lon_ <0 : lon_ = lon_ +360
            lon = int(round(float(lon_),1)*10)
            lat = int(round(float(site_lat[site_id==siteName].values),1)*10)
            mask_lon = lon_map == lon
            mask_lat = lat_map == lat
            ind_spatial = np.bitwise_and(mask_lon ,mask_lat)

            '''时间匹配'''
            data = pd.read_csv(infile)
            times = data['UTC_Time']
            if 't2m_era5' not in data.columns:
                data['t2m_era5'] = None
                data['skt_era5'] = None
                data['stl1_era5'] = None

            # 转换时间戳为小时数
            hours_since_1900 = []
            for time_str in times:
                time_obj = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                delta = time_obj - datetime.datetime(1900, 1, 1, 0, 0, 0)
                hour = delta.total_seconds() / 3600
                # hours_since_1900.append(delta.total_seconds() / 3600)
                hour_start = floor(hour)
                hour_end = ceil(hour)
                f = hour - hour_start
                '''跳过别的时间'''
                if hour_start > time_max: continue
                if hour_end < time_min: continue

                if hour_start == time_max:
                    ind_time1 = time == hour_start
                    ind_time2 = time == hour_start
                elif hour_end == time_min:
                    ind_time1 = time == hour_end
                    ind_time2 = time == hour_end
                else:
                    ind_time1 = time == hour_start
                    ind_time2 = time == hour_end


                save_t2m_1 = t2m_raw[ind_time1, ind_spatial][0] * t2m_scale_factor + t2m_add_offset
                save_t2m_2 = t2m_raw[ind_time2, ind_spatial][0] * t2m_scale_factor + t2m_add_offset
                save_t2m = float(save_t2m_1 *(1-f)+save_t2m_2*f)
                print(save_t2m)

                save_skt_1 = skt_raw[ind_time1, ind_spatial][0] * skt_scale_factor + skt_add_offset
                save_skt_2 = skt_raw[ind_time2, ind_spatial][0] * skt_scale_factor + skt_add_offset
                save_skt = float(save_skt_1 *(1-f)+save_skt_2*f)
                print(save_skt)

                save_stl1_1 = stl1_raw[ind_time1, ind_spatial][0] * stl1_scale_factor + stl1_add_offset
                save_stl1_2 = stl1_raw[ind_time2, ind_spatial][0] * stl1_scale_factor + stl1_add_offset
                save_stl1 = float(save_stl1_1 *(1-f)+save_stl1_2*f)
                print(save_stl1)
                data.loc[(data['UTC_Time'] == time_str), 't2m_era5'] = data.loc[(data['UTC_Time'] == time_str), 't2m_era5'].fillna(save_t2m)
                data.loc[(data['UTC_Time'] == time_str), 'skt_era5'] = data.loc[
                    (data['UTC_Time'] == time_str), 'skt_era5'].fillna(save_skt)
                data.loc[(data['UTC_Time'] == time_str), 'stl1_era5'] = data.loc[
                    (data['UTC_Time'] == time_str), 'stl1_era5'].fillna(save_stl1)

            # outfile = ERA5_val_dir + fileName
            data.to_csv(infile, index=False)