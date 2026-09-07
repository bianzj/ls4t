import h5py
import numpy as np
import os
import glob
from datetime import datetime, timedelta
import shutil

# ================= 配置路径 =================
AATSR_ROOT = "/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/0_raw_h5"
ERA5_ROOT = "/media/hero/lsct02/ERA5_reanalysis/ERA5_reanaysis"
OUTPUT_ROOT = "/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/0_raw_h5_Ta"

# 处理的时间范围
YEARS = range(2002, 2013) 

# ================= 辅助函数 =================

def read_h5py_items(infile, items):
    """
    读取h5文件中指定的数据集
    自动处理标量和数组的差异
    """
    data_list = []
    with h5py.File(infile, 'r') as f:
        for item in items:
            if item in f:
                ds = f[item]
                # 关键：如果是标量，用 [()] 读取值；如果是数组，用 [:]
                if ds.shape == ():
                    data_list.append(ds[()]) 
                else:
                    data_list.append(ds[:])
            else:
                data_list.append(None)
                # print(f"Warning: {item} not found in {infile}")
    return data_list

def aatsr_read_sites_time(infile):
    """计算切片的UTC时间"""
    items_time = ['ref_time', 'sec']
    [ref_time, sec] = read_h5py_items(infile, items_time)
    
    try:
        # 文件名格式: AATSR_YYYY_DOY_TIME.h5
        filename = os.path.basename(infile)
        parts = filename.split('_')
        ref_time_str = f"{parts[1]}_{parts[2]}" # YYYY_DOY
        
        base_time = datetime.strptime(ref_time_str, '%Y_%j')
        
        # 确保 sec 是一个普通的 python float/int 用于计算
        offset_sec = float(sec) if np.isscalar(sec) else float(np.mean(sec))
        
        utc_time = base_time + timedelta(seconds=int(offset_sec))
        return utc_time
    except Exception as e:
        print(f"Error parsing time for {infile}: {e}")
        return None

def get_era5_path(year, doy):
    """路径结构: Year/DOY/ta.h5"""
    return os.path.join(ERA5_ROOT, f"{year:04d}", f"{doy:03d}", "ta.h5")

# ================= 主程序 =================

if __name__ == "__main__":
    print("Start processing Ta matching (Scalar Support)...")

    for year in YEARS:
        # 判断闰年
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        total_days = 366 if is_leap else 365
        
        for doy in range(1, total_days + 1):
            
            # 1. 寻找当天所有的AATSR切片文件
            search_pattern = os.path.join(AATSR_ROOT, "*", f"AATSR_{year:04d}_{doy:03d}_*.h5")
            aatsr_files = glob.glob(search_pattern)
            
            if not aatsr_files:
                continue 
            
            print(f"Found {len(aatsr_files)} files for Year {year} DOY {doy}")
            
            # 2. 读取当天的 ERA5 数据
            era5_file = get_era5_path(year, doy)
            
            if not os.path.exists(era5_file):
                continue
                
            try:
                with h5py.File(era5_file, 'r') as f_era:
                    if 'data' in f_era:
                        era5_data = f_era['data'][:] 
                    else:
                        continue
            except Exception as e:
                print(f"Error reading ERA5 {era5_file}: {e}")
                continue

            # 3. 循环处理当天的每个 AATSR 文件
            for aatsr_path in aatsr_files:
                try:
                    # --- 准备输出路径 ---
                    rel_path = os.path.relpath(aatsr_path, AATSR_ROOT)
                    out_path = os.path.join(OUTPUT_ROOT, rel_path)
                    out_dir = os.path.dirname(out_path)
                    # if rel_path[:6]!='CN-Ha2': continue
                    
                    if not os.path.exists(out_dir):
                        os.makedirs(out_dir)
                    
                    # --- 计算观测时间 ---
                    utc_time = aatsr_read_sites_time(aatsr_path)
                    if utc_time is None:
                        continue
                    
                    hour_idx = utc_time.hour
                    minute_fraction = utc_time.minute / 60.0
                    
                    idx_t0 = hour_idx
                    idx_t1 = min(hour_idx + 1, 23) 
                    
                    # --- 读取 AATSR 空间信息 (标量) ---
                    [ref_indx, ref_indy] = read_h5py_items(aatsr_path, ['ref_indx', 'ref_indy'])
                    
                    if ref_indx is None or ref_indy is None:
                        continue
                        
                    # --- 空间匹配计算 ---
                    # 即使是标量，整除运算也是可以的
                    # ref_indx: 0.01 deg, ERA5: 0.25 deg -> Ratio 25
                    era_row = int(ref_indy // 25)
                    era_col = int(ref_indx // 25)
                    
                    # 边界保护
                    era_row = max(0, min(era_row, 1439))
                    era_col = max(0, min(era_col, 719))
                    
                    # --- 提取并插值 Ta ---
                    # 直接用标量索引提取，结果 ta_t0 也是标量
                    ta_t0 = era5_data[idx_t0, era_col, era_row]
                    ta_t1 = era5_data[idx_t1, era_col, era_row]
                    
                    if idx_t0 == idx_t1:
                        ta_final = ta_t0
                    else:
                        ta_final = ta_t0 * (1 - minute_fraction) + ta_t1 * minute_fraction
                    
                    # --- 写入新文件 ---
                    shutil.copyfile(aatsr_path, out_path)
                    
                    with h5py.File(out_path, 'r+') as f_out:
                        if 'Ta' in f_out:
                            del f_out['Ta']
                        
                        # === 关键修改 ===
                        # 判断 data 是否为标量。如果是标量，不使用压缩。
                        if np.isscalar(ta_final) or ta_final.ndim == 0:
                            f_out.create_dataset('Ta', data=ta_final)
                        else:
                            # 只有是数组时才压缩
                            f_out.create_dataset('Ta', data=ta_final, compression="gzip", compression_opts=4)
                        
                        # 写入属性
                        f_out['Ta'].attrs['description'] = 'ERA5 Air Temperature interpolated'
                        f_out['Ta'].attrs['source_time'] = utc_time.strftime('%Y-%m-%d %H:%M:%S UTC')
                        
                except Exception as e:
                    print(f"Failed processing {aatsr_path}: {e}")

    print("All processing done.")