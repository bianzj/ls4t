import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
import numpy as np
from datetime import datetime, timedelta
import h5py

def seconds_to_datetime(seconds_since_1970):
    if isinstance(seconds_since_1970, int):
        seconds_since_1970 = [seconds_since_1970]
    elif isinstance(seconds_since_1970, np.ndarray):
        seconds_since_1970 = seconds_since_1970.tolist()
    
    result_list = []
    for seconds in seconds_since_1970:
        seconds = int(seconds)
        base_time = datetime(1970, 1, 1, 0, 0, 0)
        time_difference = timedelta(seconds=seconds)
        current_time = base_time + time_difference
        year = current_time.year
        month = current_time.month
        day = current_time.day
        hour = current_time.hour
        minute = current_time.minute
        second = current_time.second
        result_list.append([year, month, day, hour, minute, second])
    return result_list

def process_era5_monthly_data(infile, outdir_h5, variable_names, year):
    """
    处理ERA5月均数据 - 按当地时重组
    """
    # 读取时间信息
    dif_hour = read_image_Nc(infile, 'valid_time', 1)
    time = np.array(seconds_to_datetime(dif_hour))
    
    # 读取经纬度数据
    lat_data = read_image_Nc(infile, 'latitude', 1)
    lon_data = read_image_Nc(infile, 'longitude', 1)
    nl, ns = 721, 1440
    
    # 创建经纬度网格
    lon = np.zeros([nl, ns])
    lat = np.zeros([nl, ns])
    for i in range(ns):
        lon[:, i] = lon_data[i]
    for i in range(nl):
        lat[i, :] = lat_data[i]
    
    # 按月份分组处理
    monthly_data = {}
    for t_idx, time_info in enumerate(time):
        year_val, month_val, day_val, hour_val, minute_val, second_val = time_info
        month_key = month_val
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                'time_indices': [],
                'utc_hours': []
            }
        
        monthly_data[month_key]['time_indices'].append(t_idx)
        monthly_data[month_key]['utc_hours'].append(hour_val)
    
    # 处理每个变量
    for variable_name in variable_names:
        print(f"处理变量: {variable_name}")
        
        # 读取原始数据
        raw_data = read_image_Nc(infile, variable_name, 1)
        
        # 处理异常值
        raw_data[raw_data < 0] = 0
        
        # 处理每个月的数据
        for month_val, month_info in monthly_data.items():
            print(f"处理月份: {month_val:02d}")
            
            time_indices = month_info['time_indices']
            utc_hours = month_info['utc_hours']
            
            # 初始化结果数组: 24个当地时 x 纬度 x 经度
            local_time_data = np.zeros([24, nl, ns])
            
            # 对每个当地时进行处理
            for local_hour in range(24):
                print(f"处理当地时: {local_hour:02d}")
                
                # 初始化这个当地时的数据
                hour_data = np.zeros([nl, ns])
                
                # 对每个时区进行处理
                for i in range(24):
                    lon_center = i * 15
                    lon_min = lon_center - 7.5
                    lon_max = lon_center + 7.5
                    
                    # 计算对应的UTC时间
                    t = local_hour - i
                    if t >= 24: 
                        t = t - 24
                    if t < 0: 
                        t = t + 24
                    
                    # 确定经度范围
                    if lon_min > 0:
                        ind = (lon > lon_min) & (lon <= lon_max)
                    elif lon_min < 0:
                        ind = (lon > lon_min) | (lon <= lon_max)
                    else:  # lon_min == 0
                        ind = (lon > -7.5) | (lon <= 7.5)
                    
                    # 在当前月份的数据中找到对应UTC时间的数据
                    month_utc_hours = np.array(utc_hours)
                    month_time_indices = np.array(time_indices)
                    ind_time_in_month = (month_utc_hours == t)
                    
                    # 如果该UTC时间在当前月份存在数据
                    if np.any(ind_time_in_month):
                        # 使用该月份对应UTC时间的数据
                        data_idx = month_time_indices[ind_time_in_month][0]
                        hour_data[ind] = raw_data[data_idx, :, :][ind]
                
                # 保存这个当地时的数据
                local_time_data[local_hour, :, :] = hour_data
            
            # 调整位置: 太平洋中心->大西洋中心
            data_adjusted = np.zeros([24, nl, ns])
            data_adjusted[:, :, :720] = local_time_data[:, :, 720:]  # 东经部分
            data_adjusted[:, :, 720:] = local_time_data[:, :, :720]  # 西经部分
            
            # 调整经度网格
            lon_adjusted = np.zeros([nl, ns])
            lon_adjusted[:, :720] = lon[:, 720:] - 360  # 东经转为负值
            lon_adjusted[:, 720:] = lon[:, :720]        # 西经保持不变
            
            # 创建输出目录: outdir_h5/年份/月份/
            outdir_month = os.path.join(outdir_h5, str(year), f"{month_val:02d}")
            os.makedirs(outdir_month, exist_ok=True)
            
            # 保存为HDF5文件，包含00-23个时间点
            outfile = os.path.join(outdir_month, f"{variable_name}.h5")
            with h5py.File(outfile, 'w') as f:
                # 保存经纬度
                f.create_dataset('latitude', data=lat)
                f.create_dataset('longitude', data=lon_adjusted)
                
                # 保存每个小时的数据，按时间命名
                for hour in range(24):
                    f.create_dataset(f"{hour:02d}", data=data_adjusted[hour, :, :])
                
                # 保存属性
                f.attrs['variable'] = variable_name
                f.attrs['year'] = year
                f.attrs['month'] = month_val
                f.attrs['description'] = f'ERA5 monthly data with local time 00-23 for month {month_val:02d}'
            
            print(f"已保存: {outfile}")

if __name__ == '__main__':
    indir_raw = r'/media/hero/lsct02/ERA5_month/raw1/'
    outdir_h5 = r'/media/hero/lsct02/ERA5_month/h5/'
    # variable_names = ['skt', 't2m']
    variable_names = ['stl1','stl2','stl3','stl4']
    
    # 确保输出目录存在
    os.makedirs(outdir_h5, exist_ok=True)
    
    # 查找并处理文件
    fileNames = search_file_rej(indir_raw, ['ERA5'], 'txt')
    fileNames.sort()
    
    for fileName in fileNames:
        print(f"处理文件: {fileName}")
        
        # 从文件名提取年份
        try:
            year = int(fileName.split('_')[2][:-3])
        except:
            print(f"无法从文件名 {fileName} 中提取年份，跳过")
            continue
        
        infile = os.path.join(indir_raw, fileName)
        year = fileName.split('_')[2][:-3]
        
        # 处理数据
        process_era5_monthly_data(infile, outdir_h5, variable_names, year)
        
        print(f"完成处理: {fileName}")
    
    print("所有文件处理完成！")