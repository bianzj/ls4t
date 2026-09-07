import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))  # datapro/
parent_dir = os.path.dirname(current_dir)                 # 项目根目录/

sys.path.append(parent_dir)

from base.util_data import *
from base.util_file import *
import xarray as xr
import cfgrib
import h5py
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")

def left2right2d(data):
    """
    将数据从0-360经度范围转换为-180到180（或反之）
    假设数据列数为1440（0.25°分辨率）
    """
    ncols = data.shape[1]
    half = ncols // 2
    datanew = np.zeros_like(data)
    datanew[:, :half] = data[:, half:]
    datanew[:, half:] = data[:, :half]
    return datanew

def left2right3d(data):
    """
    3D版本的经度翻转
    """
    ncols = data.shape[2]
    half = ncols // 2
    datanew = np.zeros_like(data)
    datanew[:, :, :half] = data[:, :, half:]
    datanew[:, :, half:] = data[:, :, :half]
    return datanew

def read_grib_variable(ds, var_name):
    """
    从xarray Dataset中安全读取变量
    """
    try:
        # 处理不同的变量名映射
        var_mapping = {
            'skt': 'skt',           # skin temperature
            'u10': 'u10',           # 10m u-component of wind
            'v10': 'v10',           # 10m v-component of wind
            't2m': 't2m',           # 2m temperature
            'd2m': 'd2m',           # 2m dewpoint temperature
            'lai_hv': 'lai_hv',     # leaf area index high vegetation
            'lai_lv': 'lai_lv',     # leaf area index low vegetation
            'stl1': 'stl1',         # soil temperature level 1
            'sp': 'sp',             # surface pressure
            'ssrd': 'ssrd',         # surface solar radiation downwards
            'strd': 'strd',         # surface thermal radiation downwards
            'cvl': 'cvl',           # low vegetation cover
            'cvh': 'cvh',           # high vegetation cover
            'swvl1': 'swvl1',       # volumetric soil water layer 1
        }
        
        var_name_grib = var_mapping.get(var_name, var_name)
        
        if var_name_grib in ds.variables:
            return ds[var_name_grib].values
        else:
            # 尝试查找类似变量
            for key in ds.variables.keys():
                if var_name_grib in key.lower() or var_name.lower() in key.lower():
                    print(f"找到类似变量: {key} -> {var_name}")
                    return ds[key].values
            print(f"警告: 变量 {var_name} 不存在")
            return None
            
    except Exception as e:
        print(f"读取变量 {var_name} 失败: {e}")
        return None

def process_single_month_grib(kyear, kmonth):
    """
    处理单个ERA5 GRIB月度数据
    """
    # 构建输入文件路径
    # infile = f'/media/hero/新加卷/ERA5_reanalysis/{kyear:04d}/{kyear:04d}{kmonth:02d}.grib'
    infile = r"C:\Users\jiank\Downloads\Compressed\49482092eb5776bb142b15fcfcc23eb5/data.grib"
    # 尝试其他扩展名
    if not os.path.exists(infile):
        alt_extensions = ['.grb', '.grib2', '.grb2']
        found = False
        for ext in alt_extensions:
            alt_file = infile.replace('.grib', ext)
            if os.path.exists(alt_file):
                infile = alt_file
                found = True
                break
        if not found:
            print(f"错误: 文件不存在 - {infile}")
            return False
    
    print(f"=" * 60)
    print(f"开始处理: {infile}")
    print(f"=" * 60)
    
    # 确定月份天数
    days_in_month = {
        1: 31, 2: 29 if (kyear % 4 == 0 and (kyear % 100 != 0 or kyear % 400 == 0)) else 28,
        3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }
    ndays = days_in_month.get(kmonth, 31)
    print(f"月份天数: {ndays} 天")
    
    try:
        # 使用cfgrib读取GRIB文件
        ds = xr.open_dataset(infile, engine='cfgrib')
        print(f"成功读取GRIB文件")
        print(f"变量列表: {list(ds.variables.keys())}")
        
        # 获取维度信息
        if 'longitude' in ds.coords:
            lon = ds.longitude.values
            lat = ds.latitude.values
            nlon = len(lon)
            nlat = len(lat)
        elif 'lon' in ds.coords:
            lon = ds.lon.values
            lat = ds.lat.values
            nlon = len(lon)
            nlat = len(lat)
        else:
            # 尝试从变量中获取
            first_var = list(ds.variables.keys())[0]
            if len(ds[first_var].dims) == 3:
                nlat = ds[first_var].shape[1]
                nlon = ds[first_var].shape[2]
            else:
                print("错误: 无法获取维度信息")
                ds.close()
                return False
        
        # 检查时间维度
        time_steps = 24 * ndays
        if 'time' in ds.coords:
            times = ds.time.values
            actual_steps = len(times)
            if actual_steps != time_steps:
                print(f"警告: 时间步数 {actual_steps} 与预期 {time_steps} 不符")
                time_steps = actual_steps
            else:
                print(f"时间步数: {time_steps}")
        else:
            print(f"使用时间步数: {time_steps}")
        
        print(f"数据维度: 时间={time_steps}, 纬度={nlat}, 经度={nlon}")
        
    except Exception as e:
        print(f"错误: 读取GRIB文件失败 - {e}")
        return False
    
    # 输出目录
    outdir00 = 'd:/media/stream_input_backup/'
    outdir0 = f'{outdir00}{kyear:04d}/'
    os.makedirs(outdir0, exist_ok=True)
    print(f"输出目录: {outdir0}")
    
    # 处理每一天
    processed_days = 0
    for kday in range(1, ndays + 1):
        doy = date2DOY(kyear, kmonth, kday)
        outdir = f'{outdir0}{doy:03d}/'
        os.makedirs(outdir, exist_ok=True)
        
        # 检查是否已处理
        if os.path.exists(f'{outdir}skt.h5'):
            print(f"跳过第 {kday} 天 (已处理): {outdir}")
            continue
        
        print(f"\n处理第 {kday} 天 (DOY={doy})...")
        
        karray_start = 24 * (kday - 1)
        karray_end = min(karray_start + 24, time_steps)
        karray_count = karray_end - karray_start
        
        if karray_count < 1:
            print(f"警告: 第 {kday} 天没有数据")
            break
        
        # 读取所有需要的变量
        var_names = ['skt', 'u10', 'v10', 't2m', 'd2m', 'lai_hv', 'lai_lv', 
                     'stl1', 'sp', 'ssrd', 'strd', 'cvl', 'cvh', 'swvl1']
        
        variables = {}
        for var_name in var_names:
            data = read_grib_variable(ds, var_name)
            if data is not None:
                if len(data.shape) == 3:  # (time, lat, lon)
                    variables[var_name] = data[karray_start:karray_end, :, :]
                elif len(data.shape) == 2:  # (lat, lon) 静态变量
                    variables[var_name] = data
                else:
                    print(f"警告: 变量 {var_name} 形状异常: {data.shape}")
                    variables[var_name] = None
            else:
                # 创建空数据
                variables[var_name] = np.zeros((karray_count, nlat, nlon))
                print(f"警告: 变量 {var_name} 使用零值填充")
        
        # 检查关键变量
        if variables.get('skt') is None or np.all(variables['skt'] == 0):
            print(f"错误: 关键变量 skt 缺失，跳过第 {kday} 天")
            continue
        
        # 计算风速大小
        u10 = variables.get('u10')
        v10 = variables.get('v10')
        if u10 is not None and v10 is not None:
            u_wind = np.sqrt(u10**2 + v10**2)
        else:
            u_wind = np.zeros((karray_count, nlat, nlon))
            print("警告: 风速数据缺失，使用零值")
        
        # 处理LAI（取第13小时，如果有的话）
        lai_hv_data = variables.get('lai_hv')
        lai_lv_data = variables.get('lai_lv')
        
        if lai_hv_data is not None and len(lai_hv_data.shape) == 3:
            lai_hv_ = lai_hv_data[12 if karray_count > 12 else 0, :, :]
        else:
            lai_hv_ = lai_hv_data if lai_hv_data is not None else np.zeros((nlat, nlon))
        
        if lai_lv_data is not None and len(lai_lv_data.shape) == 3:
            lai_lv_ = lai_lv_data[12 if karray_count > 12 else 0, :, :]
        else:
            lai_lv_ = lai_lv_data if lai_lv_data is not None else np.zeros((nlat, nlon))
        
        lai_ = lai_hv_ + lai_lv_
        
        # 土壤水分取第13小时
        swvl1_data = variables.get('swvl1')
        if swvl1_data is not None and len(swvl1_data.shape) == 3:
            swvl1_ = swvl1_data[12 if karray_count > 12 else 0, :, :]
        else:
            swvl1_ = swvl1_data if swvl1_data is not None else np.zeros((nlat, nlon))
        
        # 经度翻转
        print("  执行经度翻转...")
        lai_hv = left2right2d(lai_hv_)
        lai_lv = left2right2d(lai_lv_)
        lai = left2right2d(lai_)
        
        skt = left2right3d(variables.get('skt', np.zeros((karray_count, nlat, nlon))))
        u = left2right3d(u_wind)
        t2m = left2right3d(variables.get('t2m', np.zeros((karray_count, nlat, nlon))))
        d2m = left2right3d(variables.get('d2m', np.zeros((karray_count, nlat, nlon))))
        ssrd = left2right3d(variables.get('ssrd', np.zeros((karray_count, nlat, nlon))))
        strd = left2right3d(variables.get('strd', np.zeros((karray_count, nlat, nlon))))
        sp = left2right3d(variables.get('sp', np.zeros((karray_count, nlat, nlon))))
        swvl1 = left2right2d(swvl1_)
        
        # 处理其他变量
        stl1_data = variables.get('stl1')
        if stl1_data is not None:
            if len(stl1_data.shape) == 3:
                stl1 = left2right3d(stl1_data)
            else:
                stl1 = stl1_data
        else:
            stl1 = np.zeros((karray_count, nlat, nlon))
        
        cvl_data = variables.get('cvl')
        if cvl_data is not None:
            if len(cvl_data.shape) == 3:
                cvl = left2right3d(cvl_data)
            else:
                cvl = cvl_data
        else:
            cvl = np.zeros((karray_count, nlat, nlon))
        
        cvh_data = variables.get('cvh')
        if cvh_data is not None:
            if len(cvh_data.shape) == 3:
                cvh = left2right3d(cvh_data)
            else:
                cvh = cvh_data
        else:
            cvh = np.zeros((karray_count, nlat, nlon))
        
        # 保存时间标签
        t = np.arange(karray_count)
        np.savetxt(f'{outdir}t.txt', t, delimiter='\n', fmt='%.0f')
        
        # 保存所有变量为HDF5
        data_dict = {
            'skt': skt, 
            'u': u, 
            'ta': t2m, 
            'ea': d2m,
            'rin': ssrd, 
            'rli': strd, 
            'p': sp,
            'lai': lai, 
            'sm': swvl1, 
            'stl': stl1,
            'cvl': cvl, 
            'cvh': cvh,
            'lai_hv': lai_hv, 
            'lai_lv': lai_lv
        }
        
        print("  保存HDF5文件...")
        for name, data in data_dict.items():
            outfile = f'{outdir}{name}.h5'
            try:
                with h5py.File(outfile, 'w') as f:
                    f.create_dataset('data', data=data, dtype='f', compression='gzip')
            except Exception as e:
                print(f"  错误: 保存 {name} 失败 - {e}")
        
        processed_days += 1
        print(f"  完成第 {kday} 天处理 (数据形状: {skt.shape})")
    
    ds.close()
    
    print(f"\n" + "=" * 60)
    print(f"处理完成: {infile}")
    print(f"成功处理 {processed_days}/{ndays} 天")
    print("=" * 60)
    
    return True

def main():
    """
    主函数 - 处理单个月份
    """
    # ========== 在这里修改要处理的年份和月份 ==========
    kyear = 2025      # 年份
    kmonth = 9        # 月份 (1-12)
    # ===============================================
    
    print("ERA5 GRIB 数据处理")
    print(f"处理目标: {kyear}年{kmonth:02d}月")
    print("-" * 60)
    
    # 处理单个月份
    success = process_single_month_grib(kyear, kmonth)
    
    if success:
        print("\n✅ 数据处理成功完成！")
    else:
        print("\n❌ 数据处理失败！")

if __name__ == '__main__':
    main()