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
from osgeo import gdal, osr
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

def plot_density_scatter(x, y, xlabel, ylabel, title, outfile, metrics=None):
    """
    绘制密度散点图
    
    Parameters:
    x, y: 数据
    xlabel, ylabel: 坐标轴标签
    title: 图标题
    outfile: 输出文件路径
    metrics: 包含num, rmse, bias, r2的字典
    """
    plt.figure(figsize=(5, 4))
    
    # 使用hexbin绘制密度图
    hb = plt.hexbin(x, y, gridsize=50, cmap='Blues', alpha=0.7, mincnt=1)
    plt.colorbar(hb, label='Point Density')
    
    # 添加1:1线
    min_val = min(np.min(x), np.min(y))
    max_val = max(np.max(x), np.max(y))
    plt.plot([min_val-100, max_val+100], [min_val-100, max_val+100], 'r--', linewidth=2, label='1:1 Line')
    
    # 添加回归线
    if len(x) > 1:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        regression_line = slope * np.array([min_val, max_val]) + intercept
        plt.plot([min_val, max_val], regression_line, 'g-', linewidth=2, label='Regression Line')
    
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.title(title, fontsize=14)
    plt.xlim([min_val,max_val])
    plt.ylim([min_val,max_val])
    
    # 添加统计信息
    if metrics:
        stats_text = f"N = {metrics['num']:,}\nRMSE = {metrics['rmse']:.2f}\nBias = {metrics['bias']:.2f}\nR² = {metrics['r2']:.2f}"
        plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes, 
                fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 保存图片
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Density plot saved: {outfile}")

if __name__ == '__main__':
    if_resample = 0
    if_month = 0
    if_pixel = 1

    label = 'v2'
    indir_aatsr_raw = r'/media/hero/lsct04/aatsr_lsct_month_' + label + '/'
    indir_aatsr_25km = r'/media/hero/lsct04/aatsr_lsct_month_' + label + '_0.25/'
    indir_era5 = r'/media/hero/lsct02/ERA5_month/h5/'
    outdir = r'/home/hero/data/AATSR/aatsr_validation/cross_validation/' + label + '/'
    mkdir_if_not_exist(outdir)
    infile_ref = r'/media/hero/lsct04/0_base/ref_world_0.25.tif'

    if if_resample:
        '''重采样AATSR到25km，使用参考文件确保投影和分辨率一致'''
        # 确保输出目录存在
        mkdir_if_not_exist(indir_aatsr_25km)
        
        type,ns,nl,bands,type_geos,type_proj = read_image_gdal(infile_ref)
        
        for year in range(2002, 2013):
            for month in range(1, 13):
                infile_aatsr_day = indir_aatsr_raw + 'aatsr_%04d_%02d_day.tif' % (year, month)
                infile_aatsr_night = indir_aatsr_raw + 'aatsr_%04d_%02d_night.tif' % (year, month)
                if not os.path.exists(infile_aatsr_day) and not os.path.exists(infile_aatsr_night): continue

                outfile_aatsr_day = indir_aatsr_25km + 'aatsr_%04d_%02d_day.h5' % (year, month)
                outfile_aatsr_night = indir_aatsr_25km + 'aatsr_%04d_%02d_night.h5' % (year, month)

                print(f"{year}-{month:02d}")

                # day
                infile = infile_aatsr_day
                Tnadir = gdal.Open(f'HDF5:"{infile}"://Tnadir', gdal.GA_ReadOnly).ReadAsArray()
                Tobliq = gdal.Open(f'HDF5:"{infile}"://Tobliq', gdal.GA_ReadOnly).ReadAsArray()
                Ts = gdal.Open(f'HDF5:"{infile}"://Ts', gdal.GA_ReadOnly).ReadAsArray()
                Tv = gdal.Open(f'HDF5:"{infile}"://Tv', gdal.GA_ReadOnly).ReadAsArray()

                Tnadir_save = resize_data(Tnadir,nl,ns,cv2.INTER_AREA)
                Tobliq_save = resize_data(Tobliq,nl,ns,cv2.INTER_AREA)
                Ts_save = resize_data(Ts,nl,ns,cv2.INTER_AREA)
                Tv_save = resize_data(Tv,nl,ns,cv2.INTER_AREA)

                name_list = ['Tnadir','Tobliq','Ts','Tv']
                data_list = [Tnadir_save,Tobliq_save,Ts_save,Tv_save]
                dtype_list = np.full_like(name_list,'uint16')
                write_h5py_file(outfile_aatsr_day,name_list,data_list,dtype_list,ifcover=1)

                # night
                infile = infile_aatsr_night
                Tnadir = gdal.Open(f'HDF5:"{infile}"://Tnadir', gdal.GA_ReadOnly).ReadAsArray()
                Tobliq = gdal.Open(f'HDF5:"{infile}"://Tobliq', gdal.GA_ReadOnly).ReadAsArray()
                Ts = gdal.Open(f'HDF5:"{infile}"://Ts', gdal.GA_ReadOnly).ReadAsArray()
                Tv = gdal.Open(f'HDF5:"{infile}"://Tv', gdal.GA_ReadOnly).ReadAsArray()
                
                Tnadir_save = resize_data(Tnadir,nl,ns,cv2.INTER_AREA)
                Tobliq_save = resize_data(Tobliq,nl,ns,cv2.INTER_AREA)
                Ts_save = resize_data(Ts,nl,ns,cv2.INTER_AREA)
                Tv_save = resize_data(Tv,nl,ns,cv2.INTER_AREA)

                name_list = ['Tnadir','Tobliq','Ts','Tv']
                data_list = [Tnadir_save,Tobliq_save,Ts_save,Tv_save]
                dtype_list = np.full_like(name_list,'uint16')
                write_h5py_file(outfile_aatsr_night,name_list,data_list,dtype_list,ifcover=1)

    if if_month:
        '''计算每个月数据（Ts-stl1，Tv-Ta）的r2、bias、rmse'''
        for year in range(2009, 2010):
            for month in range(7, 8):
                print(f"{year:04d}-{month:02d}")
                infile_aatsr_day = indir_aatsr_25km + 'aatsr_%04d_%02d_day.h5' % (year, month)
                infile_aatsr_night = indir_aatsr_25km + 'aatsr_%04d_%02d_night.h5' % (year, month)

                indir_ERA5_month = indir_era5 + '%04d/%02d/' % (year, month)
                infile_era5_skt = indir_ERA5_month + 'skt.h5'
                infile_era5_t2m = indir_ERA5_month + 't2m.h5'
                infile_era5_stl1 = indir_ERA5_month + 'stl1.h5'

                # day
                Tnadir,Tobliq,Ts,Tv = read_h5py_items(infile_aatsr_day,['Tnadir','Tobliq','Ts','Tv'])
                Tnadir,Tobliq,Ts,Tv = Tobliq/100.0,Tnadir/100.0,Ts/100.0,Tv/100.0
                Tnadir = np.nan_to_num(Tnadir,0)
                Tobliq = np.nan_to_num(Tobliq,0)
                Ts = np.nan_to_num(Ts,0)
                Tv = np.nan_to_num(Tv,0)

                t = 10
                skt = read_h5py_items(infile_era5_skt,['%02d'% t])[0][:-1,:]
                t2m = read_h5py_items(infile_era5_t2m,['%02d'% t])[0][:-1,:]
                stl1 = read_h5py_items(infile_era5_stl1,['%02d'% t])[0][:-1,:]
                skt = np.nan_to_num(skt,0)
                t2m = np.nan_to_num(t2m,0)
                stl1 = np.nan_to_num(stl1,0)

                ind = (Ts > 240)*(Ts < 350) * (Tv > 240)*(Tv < 350)* (np.abs(Tnadir - skt)< 15)* (np.abs(Tobliq - skt)< 15)
                
                # Tnadir-skt day
                bias,rmse,r2 = cal_rmse_r2_3sigma(skt[ind],Tnadir[ind])
                num = np.sum(ind)
                print(f"Tnadir-skt day: bias={bias:.2f}, rmse={rmse:.2f}, r2={r2:.2f}, num={num}")
                metrics = {'num': num, 'rmse': rmse, 'bias': bias, 'r2': r2}
                plot_density_scatter(
                    skt[ind], Tnadir[ind], 
                    'ERA5 SKT (K)', 'AATSR Tnadir (K)', 
                    f'Tnadir vs SKT (Day) - {year}-{month:02d}',
                    f'{outdir}Tnadir_skt_day_{year}_{month:02d}.png',
                    metrics
                )

                # Tobliq-skt day
                bias,rmse,r2 = cal_rmse_r2_3sigma(skt[ind],Tobliq[ind])
                num = np.sum(ind)
                print(f"Tobliq-skt day: bias={bias:.2f}, rmse={rmse:.2f}, r2={r2:.2f}, num={num}")
                metrics = {'num': num, 'rmse': rmse, 'bias': bias, 'r2': r2}
                plot_density_scatter(
                    skt[ind], Tobliq[ind], 
                    'ERA5 SKT (K)', 'AATSR Tobliq (K)', 
                    f'Tobliq vs SKT (Day) - {year}-{month:02d}',
                    f'{outdir}Tobliq_skt_day_{year}_{month:02d}.png',
                    metrics
                )

                # Ts-skt day
                bias,rmse,r2 = cal_rmse_r2_3sigma(skt[ind],Ts[ind])
                num = np.sum(ind)
                print(f"Ts-skt day: bias={bias:.2f}, rmse={rmse:.2f}, r2={r2:.2f}, num={num}")
                metrics = {'num': num, 'rmse': rmse, 'bias': bias, 'r2': r2}
                plot_density_scatter(
                    skt[ind], Ts[ind], 
                    'ERA5 SKT (K)', 'AATSR Ts (K)', 
                    f'Ts vs SKT (Day) - {year}-{month:02d}',
                    f'{outdir}Ts_skt_day_{year}_{month:02d}.png',
                    metrics
                )

                # Ts-stl1 day
                bias,rmse,r2 = cal_rmse_r2_3sigma(stl1[ind],Ts[ind])
                num = np.sum(ind)
                print(f"Ts-stl1 day: bias={bias:.2f}, rmse={rmse:.2f}, r2={r2:.2f}, num={num}")
                metrics = {'num': num, 'rmse': rmse, 'bias': bias, 'r2': r2}
                plot_density_scatter(
                    stl1[ind], Ts[ind], 
                    'ERA5 STL1 (K)', 'AATSR Ts (K)', 
                    f'Ts vs STL1 (Day) - {year}-{month:02d}',
                    f'{outdir}Ts_stl1_day_{year}_{month:02d}.png',
                    metrics
                )

                # Tv-t2m day
                bias,rmse,r2 = cal_rmse_r2_3sigma(t2m[ind],Tv[ind])
                num = np.sum(ind)
                print(f"Tv-t2m day: bias={bias:.2f}, rmse={rmse:.2f}, r2={r2:.2f}, num={num}")
                metrics = {'num': num, 'rmse': rmse, 'bias': bias, 'r2': r2}
                plot_density_scatter(
                    t2m[ind], Tv[ind], 
                    'ERA5 T2M (K)', 'AATSR Tv (K)', 
                    f'Tv vs T2M (Day) - {year}-{month:02d}',
                    f'{outdir}Tv_t2m_day_{year}_{month:02d}.png',
                    metrics
                )

                print()  # 空行分隔

                # night
                Tnadir,Tobliq,Ts,Tv = read_h5py_items(infile_aatsr_night,['Tnadir','Tobliq','Ts','Tv'])
                Tnadir,Tobliq,Ts,Tv = Tobliq/100.0,Tnadir/100.0,Ts/100.0,Tv/100.0
                Tnadir = np.nan_to_num(Tnadir,0)
                Tobliq = np.nan_to_num(Tobliq,0)
                Ts = np.nan_to_num(Ts,0)
                Tv = np.nan_to_num(Tv,0)

                t = 22
                skt = read_h5py_items(infile_era5_skt,['%02d'% t])[0][:-1,:]
                t2m = read_h5py_items(infile_era5_t2m,['%02d'% t])[0][:-1,:]
                stl1 = read_h5py_items(infile_era5_stl1,['%02d'% t])[0][:-1,:]
                skt = np.nan_to_num(skt,0)
                t2m = np.nan_to_num(t2m,0)
                stl1 = np.nan_to_num(stl1,0)

                ind = (Ts > 240)*(Ts < 350) * (Tv > 240)*(Tv < 350) * (np.abs(Tnadir - skt)< 15)* (np.abs(Tobliq - skt)< 15)

                # Tnadir-skt night
                bias,rmse,r2 = cal_rmse_r2_3sigma(skt[ind],Tnadir[ind])
                num = np.sum(ind)
                print(f"Tnadir-skt night: bias={bias:.2f}, rmse={rmse:.2f}, r2={r2:.2f}, num={num}")
                metrics = {'num': num, 'rmse': rmse, 'bias': bias, 'r2': r2}
                plot_density_scatter(
                    skt[ind], Tnadir[ind], 
                    'ERA5 SKT (K)', 'AATSR Tnadir (K)', 
                    f'Tnadir vs SKT (Night) - {year}-{month:02d}',
                    f'{outdir}Tnadir_skt_night_{year}_{month:02d}.png',
                    metrics
                )

                # Tobliq-skt night
                bias,rmse,r2 = cal_rmse_r2_3sigma(skt[ind],Tobliq[ind])
                num = np.sum(ind)
                print(f"Tobliq-skt night: bias={bias:.2f}, rmse={rmse:.2f}, r2={r2:.2f}, num={num}")
                metrics = {'num': num, 'rmse': rmse, 'bias': bias, 'r2': r2}
                plot_density_scatter(
                    skt[ind], Tobliq[ind], 
                    'ERA5 SKT (K)', 'AATSR Tobliq (K)', 
                    f'Tobliq vs SKT (Night) - {year}-{month:02d}',
                    f'{outdir}Tobliq_skt_night_{year}_{month:02d}.png',
                    metrics
                )

                # Ts-skt night
                bias,rmse,r2 = cal_rmse_r2_3sigma(skt[ind],Ts[ind])
                num = np.sum(ind)
                print(f"Ts-skt night: bias={bias:.2f}, rmse={rmse:.2f}, r2={r2:.2f}, num={num}")
                metrics = {'num': num, 'rmse': rmse, 'bias': bias, 'r2': r2}
                plot_density_scatter(
                    skt[ind], Ts[ind], 
                    'ERA5 SKT (K)', 'AATSR Ts (K)', 
                    f'Ts vs SKT (Night) - {year}-{month:02d}',
                    f'{outdir}Ts_skt_night_{year}_{month:02d}.png',
                    metrics
                )

                # Ts-stl1 night
                bias,rmse,r2 = cal_rmse_r2_3sigma(stl1[ind],Ts[ind])
                num = np.sum(ind)
                print(f"Ts-stl1 night: bias={bias:.2f}, rmse={rmse:.2f}, r2={r2:.2f}, num={num}")
                metrics = {'num': num, 'rmse': rmse, 'bias': bias, 'r2': r2}
                plot_density_scatter(
                    stl1[ind], Ts[ind], 
                    'ERA5 STL1 (K)', 'AATSR Ts (K)', 
                    f'Ts vs STL1 (Night) - {year}-{month:02d}',
                    f'{outdir}Ts_stl1_night_{year}_{month:02d}.png',
                    metrics
                )

                # Tv-t2m night
                bias,rmse,r2 = cal_rmse_r2_3sigma(t2m[ind],Tv[ind])
                num = np.sum(ind)
                print(f"Tv-t2m night: bias={bias:.2f}, rmse={rmse:.2f}, r2={r2:.2f}, num={num}")
                metrics = {'num': num, 'rmse': rmse, 'bias': bias, 'r2': r2}
                plot_density_scatter(
                    t2m[ind], Tv[ind], 
                    'ERA5 T2M (K)', 'AATSR Tv (K)', 
                    f'Tv vs T2M (Night) - {year}-{month:02d}',
                    f'{outdir}Tv_t2m_night_{year}_{month:02d}.png',
                    metrics
                )

    if if_pixel:
        '''计算每个像元2003-2012年的r2、bias、rmse'''
        print("开始计算每个像元的统计指标...")
        
        # 初始化累积数组
        years = list(range(2003, 2012))  # 2003-2012
        months = list(range(1, 13))
        
        # 获取参考文件的尺寸
        ref_data, ns, nl, bands, ref_geotrans, ref_proj = read_image_gdal(infile_ref)
        
        # 初始化存储所有时间序列数据的列表
        all_ts_day = []
        all_stl1_day = []
        all_tv_day = []
        all_t2m_day = []
        
        all_ts_night = []
        all_stl1_night = []
        all_tv_night = []
        all_t2m_night = []
        
        # 读取所有年份和月份的数据
        for year in years:
            for month in months:
                # 跳过2012年4月之后的数据
                if year == 2012 and month > 4:
                    continue
                    
                print(f"读取 {year}-{month:02d}")
                
                # 白天数据
                infile_aatsr_day = indir_aatsr_25km + 'aatsr_%04d_%02d_day.h5' % (year, month)
                if os.path.exists(infile_aatsr_day):
                    Ts_day, Tv_day = read_h5py_items(infile_aatsr_day, ['Ts', 'Tv'])
                    Ts_day, Tv_day = Ts_day/100.0, Tv_day/100.0
                    all_ts_day.append(Ts_day)
                    all_tv_day.append(Tv_day)
                
                # 夜间数据
                infile_aatsr_night = indir_aatsr_25km + 'aatsr_%04d_%02d_night.h5' % (year, month)
                if os.path.exists(infile_aatsr_night):
                    Ts_night, Tv_night = read_h5py_items(infile_aatsr_night, ['Ts', 'Tv'])
                    Ts_night, Tv_night = Ts_night/100.0, Tv_night/100.0
                    all_ts_night.append(Ts_night)
                    all_tv_night.append(Tv_night)
                
                # ERA5数据
                indir_ERA5_month = indir_era5 + '%04d/%02d/' % (year, month)
                infile_era5_stl1 = indir_ERA5_month + 'stl1.h5'
                infile_era5_t2m = indir_ERA5_month + 't2m.h5'
                
                # 白天ERA5数据 (10点)
                if os.path.exists(infile_era5_stl1):
                    stl1_day = read_h5py_items(infile_era5_stl1, ['10'])[0][:-1,:]
                    all_stl1_day.append(stl1_day)
                
                if os.path.exists(infile_era5_t2m):
                    t2m_day = read_h5py_items(infile_era5_t2m, ['10'])[0][:-1,:]
                    all_t2m_day.append(t2m_day)
                
                # 夜间ERA5数据 (22点)
                if os.path.exists(infile_era5_stl1):
                    stl1_night = read_h5py_items(infile_era5_stl1, ['22'])[0][:-1,:]
                    all_stl1_night.append(stl1_night)
                
                if os.path.exists(infile_era5_t2m):
                    t2m_night = read_h5py_items(infile_era5_t2m, ['22'])[0][:-1,:]
                    all_t2m_night.append(t2m_night)
        
        # 转换为numpy数组
        all_ts_day = np.array(all_ts_day)
        all_stl1_day = np.array(all_stl1_day)
        all_tv_day = np.array(all_tv_day)
        all_t2m_day = np.array(all_t2m_day)
        
        all_ts_night = np.array(all_ts_night)
        all_stl1_night = np.array(all_stl1_night)
        all_tv_night = np.array(all_tv_night)
        all_t2m_night = np.array(all_t2m_night)
        
        print(f"数据形状 - 白天: {all_ts_day.shape}, 夜间: {all_ts_night.shape}")
        
        # 初始化结果数组
        r2_ts_stl1_day = np.full((nl, ns), np.nan)
        bias_ts_stl1_day = np.full((nl, ns), np.nan)
        rmse_ts_stl1_day = np.full((nl, ns), np.nan)
        
        r2_tv_t2m_day = np.full((nl, ns), np.nan)
        bias_tv_t2m_day = np.full((nl, ns), np.nan)
        rmse_tv_t2m_day = np.full((nl, ns), np.nan)
        
        r2_ts_stl1_night = np.full((nl, ns), np.nan)
        bias_ts_stl1_night = np.full((nl, ns), np.nan)
        rmse_ts_stl1_night = np.full((nl, ns), np.nan)
        
        r2_tv_t2m_night = np.full((nl, ns), np.nan)
        bias_tv_t2m_night = np.full((nl, ns), np.nan)
        rmse_tv_t2m_night = np.full((nl, ns), np.nan)
        
        # 计算每个像元的统计指标
        print("计算每个像元的统计指标...")
        for i in range(nl):
            for j in range(ns):
                # 白天 Ts-STL1
                ts_day_vals = all_ts_day[:, i, j]
                stl1_day_vals = all_stl1_day[:, i, j]
                
                # 应用有效值掩码
                mask_day = (ts_day_vals > 240) & (ts_day_vals < 350) & (stl1_day_vals > 240) & (stl1_day_vals < 350)
                
                if np.sum(mask_day) > 10:  # 至少需要10个有效点
                    bias, rmse, r2 = cal_rmse_r2_3sigma(stl1_day_vals[mask_day], ts_day_vals[mask_day])
                    r2_ts_stl1_day[i, j] = r2
                    bias_ts_stl1_day[i, j] = bias
                    rmse_ts_stl1_day[i, j] = rmse
                
                # 白天 Tv-T2M
                tv_day_vals = all_tv_day[:, i, j]
                t2m_day_vals = all_t2m_day[:, i, j]
                
                mask_day_tv = (tv_day_vals > 240) & (tv_day_vals < 350) & (t2m_day_vals > 240) & (t2m_day_vals < 350)
                
                if np.sum(mask_day_tv) > 10:
                    bias, rmse, r2 = cal_rmse_r2_3sigma(t2m_day_vals[mask_day_tv], tv_day_vals[mask_day_tv])
                    r2_tv_t2m_day[i, j] = r2
                    bias_tv_t2m_day[i, j] = bias
                    rmse_tv_t2m_day[i, j] = rmse
                
                # 夜间 Ts-STL1
                ts_night_vals = all_ts_night[:, i, j]
                stl1_night_vals = all_stl1_night[:, i, j]
                
                mask_night = (ts_night_vals > 240) & (ts_night_vals < 350) & (stl1_night_vals > 240) & (stl1_night_vals < 350)
                
                if np.sum(mask_night) > 10:
                    bias, rmse, r2 = cal_rmse_r2_3sigma(stl1_night_vals[mask_night], ts_night_vals[mask_night])
                    r2_ts_stl1_night[i, j] = r2
                    bias_ts_stl1_night[i, j] = bias
                    rmse_ts_stl1_night[i, j] = rmse
                
                # 夜间 Tv-T2M
                tv_night_vals = all_tv_night[:, i, j]
                t2m_night_vals = all_t2m_night[:, i, j]
                
                mask_night_tv = (tv_night_vals > 240) & (tv_night_vals < 350) & (t2m_night_vals > 240) & (t2m_night_vals < 350)
                
                if np.sum(mask_night_tv) > 10:
                    bias, rmse, r2 = cal_rmse_r2_3sigma(t2m_night_vals[mask_night_tv], tv_night_vals[mask_night_tv])
                    r2_tv_t2m_night[i, j] = r2
                    bias_tv_t2m_night[i, j] = bias
                    rmse_tv_t2m_night[i, j] = rmse
            
            if i % 100 == 0:
                print(f"进度: {i}/{nl}")
        
        # 保存结果为HDF5文件
        print("保存结果到HDF5文件...")
        
        # 白天 Ts-STL1
        name_list = ['r2', 'bias', 'rmse']
        data_list = [r2_ts_stl1_day, bias_ts_stl1_day, rmse_ts_stl1_day]
        dtype_list = ['float32', 'float32', 'float32']
        write_h5py_file(f"{outdir}/stats_ts_stl1_day_2003_2012.h5", name_list, data_list, dtype_list, ifcover=1)
        
        # 白天 Tv-T2M
        name_list = ['r2', 'bias', 'rmse']
        data_list = [r2_tv_t2m_day, bias_tv_t2m_day, rmse_tv_t2m_day]
        dtype_list = ['float32', 'float32', 'float32']
        write_h5py_file(f"{outdir}/stats_tv_t2m_day_2003_2012.h5", name_list, data_list, dtype_list, ifcover=1)
        
        # 夜间 Ts-STL1
        name_list = ['r2', 'bias', 'rmse']
        data_list = [r2_ts_stl1_night, bias_ts_stl1_night, rmse_ts_stl1_night]
        dtype_list = ['float32', 'float32', 'float32']
        write_h5py_file(f"{outdir}/stats_ts_stl1_night_2003_2012.h5", name_list, data_list, dtype_list, ifcover=1)
        
        # 夜间 Tv-T2M
        name_list = ['r2', 'bias', 'rmse']
        data_list = [r2_tv_t2m_night, bias_tv_t2m_night, rmse_tv_t2m_night]
        dtype_list = ['float32', 'float32', 'float32']
        write_h5py_file(f"{outdir}/stats_tv_t2m_night_2003_2012.h5", name_list, data_list, dtype_list, ifcover=1)
        
        print("每个像元的统计指标计算完成！")