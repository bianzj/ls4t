import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import csv
import pytz
from timezonefinder import TimezoneFinder
import warnings

# 假设这些路径在您的环境中是存在的，如果不在同一目录下请调整
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 引入自定义模块
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from cases.AATSR_product.util.util_aatsr import *

warnings.filterwarnings("ignore")

'''2025.11.11'''
'''提取反演结果'''
'''
1. 提取反演结果到csv
2. 合并站点测量结果
3. 验证、出图 (修改为合并Ts和Tv在一张图)
'''

def get_timezone(lat, lon):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if timezone_str:
        return pytz.timezone(timezone_str)
    else:
        return None

def remove_emissivity(Tobj, emis=0.95, Tsky=240, wl=10.8):
    Robj = planck(wl, Tobj)
    Rsky = planck(wl, Tsky)
    Robjn = (Robj - Rsky * (1 - emis)) / emis
    Tobjn = inv_planck(wl, Robjn)
    return Tobjn

# --- 修改后的绘图函数：Ts和Tv在一张图上 ---
def plot_combined_density(ts_mea, ts_inv, ind_ts, label_ts, dif_ts,
                          tv_mea, tv_inv, ind_tv, label_tv, dif_tv,
                          outfile):
    """
    绘制Ts和Tv的合并散点密度图
    左上角写Ts参数，右下角写Tv参数
    """
    # 计算 Ts 统计参数
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea[ind_ts], ts_inv[ind_ts], dif_ts)
    num_s = sum(ind_ts * (np.abs(ts_inv - ts_mea) < dif_ts))
    print(f'{label_ts}: num: {num_s:03d} rmse:{rmse_s:.2f} bias:{bias_s:.2f} r2:{r2_s[0]:.2f}')

    # 计算 Tv 统计参数
    bias_v, rmse_v, r2_v = cal_rmse_r2(tv_mea[ind_tv], tv_inv[ind_tv], dif_tv)
    num_v = sum(ind_tv * (np.abs(tv_inv - tv_mea) < dif_tv))
    print(f'{label_tv}: num: {num_v:03d} rmse:{rmse_v:.2f} bias:{bias_v:.2f} r2:{r2_v[0]:.2f}')

    plt.figure(figsize=(5, 5), dpi=300)
    
    # 绘制散点
    # Ts 使用红色，Tv 使用绿色 (也可以根据喜好调整颜色，如 'tab:red', 'tab:green')
    plt.scatter(ts_mea[ind_ts], ts_inv[ind_ts], label='Ts', color='red', alpha=0.6, s=60, edgecolors='none')
    plt.scatter(tv_mea[ind_tv], tv_inv[ind_tv], label='Tv', color='green', alpha=0.6, s=60, edgecolors='none')
    
    # 添加1:1线
    plt.plot([220, 370], [220, 370], color='black', linestyle='--', linewidth=1)
    
    plt.xlabel('Measured (K)')
    plt.ylabel('Inverted (K)')
    plt.legend(loc='upper right', frameon=False) # 图例放在右上角或其他不遮挡的地方
    
    ax = plt.gca()
    
    # 左上角写 Ts 参数
    ts_text = f"Ts:\nN = {num_s:d}\n$R^2$={r2_s[0]:.2f}\nBias={bias_s:.2f} K\nRMSE={rmse_s:.2f} K"
    ax.text(0.02, 0.98, ts_text, fontsize=11, ha='left', va='top', transform=ax.transAxes,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.6, edgecolor='gray'))
    
    # 右下角写 Tv 参数
    tv_text = f"Tv:\nN = {num_v:d}\n$R^2$={r2_v[0]:.2f}\nBias={bias_v:.2f} K\nRMSE={rmse_v:.2f} K"
    ax.text(0.98, 0.02, tv_text, fontsize=11, ha='right', va='bottom', transform=ax.transAxes,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.6, edgecolor='gray'))
    
    # 动态设置坐标轴范围
    valid_data = np.concatenate([ts_mea[ind_ts], ts_inv[ind_ts], tv_mea[ind_tv], tv_inv[ind_tv]])
    if len(valid_data) > 0:
        d_min, d_max = np.min(valid_data) - 15, np.max(valid_data) + 15
        plt.ylim([d_min, d_max])
        plt.xlim([d_min, d_max])
    else:
        # 默认范围防止报错
        plt.ylim([280, 330])
        plt.xlim([280, 330])

    plt.tight_layout()
    plt.savefig(outfile)
    # plt.show() # 批量处理时建议注释掉show
    plt.close()

if __name__ == '__main__':
    ###  反演参数设置
    n, m, ws = 2, 2, 5 # n 角度， m组分， ws窗口大小
    ndvi_max, ndvi_min, k = 0.87, 0.15, 1 # ndvi 参数
    lst_min, lst_max = 250, 350 # 范围参数
    hspot, wl = 0.2, 10.8 # 结构参数
    # 反演方法
    method_effective_emissivity = 'lai' # lai / ndvi
    method_mpl_pixel = 'winconst' # point / winconst / winquad
    method_solve = 'ls' # bayesian / nobayesian / none

    label = 'inv_%01dc_' % m + method_effective_emissivity + '_' + method_mpl_pixel + '_' + method_solve

    base_dir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/'
    indir_h5_sites = base_dir + label + r'/'
    outdir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/results/Dahra/'
    mkdir_if_not_exist(outdir)

    mea_dir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Dahra/'
    mea_file = mea_dir + 'Dahra_LST_Apogee_forMatchup_val.xlsx'
    
    ifextract = 1
    ifmerge = 1
    ifval = 1

    if ifextract:
        siteNames = search_dir(indir_h5_sites,['SN-Dhr'])
        siteName = siteNames[0]
        print(siteName)

        indir_site = indir_h5_sites + siteName + '/'
        fileNames = search_file(indir_site, ['h5'])
        fileNames.sort()
        outfile = outdir + label + '_extract.csv'
        if os.path.exists(outfile): os.remove(outfile)

        if m == 2:
            with open(outfile,'a',newline='') as f:
                f = csv.writer(f)
                f.writerow(['time', 'cloN', 'cloF', 'lai','lstN', 'lstF', 'Ts_inv', 'Tv_inv'])
        elif m == 3:
            with open(outfile,'a',newline='') as f:
                f = csv.writer(f)
                f.writerow(['time', 'cloN', 'cloF', 'lai','lstN', 'lstF', 'Ts_inv', 'Tv_inv','Tsl_inv','Tsh_inv'])

        for i, fileName in enumerate(fileNames):
            # print(fileName)
            year = int(fileName.split('_')[1])
            doy = int(fileName.split('_')[2])
            month, day = doy2date(year,doy)

            '''时间筛选'''
            # if year!=2009:continue

            infile = indir_site + fileName
            name_list = ["indx", "indy", "ref_indx", "ref_indy",'utc_time','lai']
            indx,indy,ref_indx,ref_indy,utc_time,lai = read_h5py_items(infile,name_list)
            mask_x = indx == ref_indx
            mask_y = indy == ref_indy
            ind = np.bitwise_and(mask_x,mask_y)

            if sum(ind) == 0:
                print('no valid pixel')
                continue
            time_save = utc_time.item().decode('utf-8')
            name_list = ["lstN", "lstF", "cloN_mask", "cloF_mask"]
            lstN,lstF,cloN_mask,cloF_mask = read_h5py_items(infile,name_list)

            if m == 2:
                items=['Ts','Tv']
                Ts,Tv = read_h5py_items(infile,items)
            
            elif m == 3:
                items=['Tsl','Tsh','Ts','Tv']
                Tsl,Tsh, Ts,Tv = read_h5py_items(infile,items)
            
            lstN_save = np.nanmean(lstN[ind])
            lstF_save = np.nanmean(lstF[ind])
            if lstN_save <250 or lstF_save < 250: continue
            Ts_save = np.nanmean(Ts[ind])
            Tv_save = np.nanmean(Tv[ind])
            cloN_mask_save = np.nanmean(cloN_mask[ind])
            cloF_mask_save = np.nanmean(cloF_mask[ind])
            lai_save = np.nanmean(lai[ind])

            if m == 2:
                with open(outfile,'a',newline='') as f:
                    f = csv.writer(f)
                    f.writerow([time_save, cloN_mask_save,cloF_mask_save,lai_save,lstN_save, lstF_save, Ts_save, Tv_save])
            elif m == 3:
                Tsl_save = np.nanmean(Tsl[ind])
                Tsh_save = np.nanmean(Tsh[ind])
                with open(outfile,'a',newline='') as f:
                    f = csv.writer(f)
                    f.writerow([time_save, cloN_mask_save,cloF_mask_save,lai_save,lstN_save, lstF_save, Ts_save, Tv_save,Tsl_save,Tsh_save])

    if ifmerge:
        merge_file = outdir + label + '_merge.csv'
        if os.path.exists(merge_file): os.remove(merge_file)
        lon = -15.443
        lat = 15.402
        timezone = get_timezone(lat, lon)
        infile = outdir + label + '_extract.csv'
        data = []

        inv_data = pd.read_csv(infile)
        inv_data['UTC_Time'] = pd.to_datetime(inv_data['time']).dt.tz_localize('UTC')
        inv_data['Local_Time'] = inv_data['UTC_Time'].dt.tz_convert(timezone) + pd.Timedelta(minutes=0)

        ground_data = pd.read_excel(mea_file,skiprows=4)
        ground_data['Time'] = pd.to_datetime(ground_data['Time'], format='%Y/%m/%d %H:%M').dt.tz_localize(timezone)

        merged_data = pd.DataFrame()
        for idx, row in inv_data.iterrows():
            local_time = row['Local_Time']
            filtered_ground_data = ground_data[(ground_data['Time'] <= local_time + pd.Timedelta(minutes=7.5)) &
                                            (ground_data['Time'] >= local_time - pd.Timedelta(minutes=7.5))]  # 选择30分钟内的数据

            if not filtered_ground_data.empty:
                merged_row = row.to_frame().T.assign(**filtered_ground_data.iloc[0])
                merged_row['Tg'] += 273.15
                merged_row['Tc'] += 273.15
                merged_row['Tsh'] += 273.15
                merged_row['Tsky'] += 273.15
                merged_data = pd.concat([merged_data, merged_row], axis=0)
        
        if m == 2:
            merged_data = merged_data[
        ['UTC_Time', 'Local_Time', 'Time', 'cloN', 'cloF', 'lai','lstN', 'lstF', 'Ts_inv', 'Tv_inv','Tsh', 'Tg', 'Tc', 'Tsky','emis' ]]
        elif m == 3:
            merged_data = merged_data[
        ['UTC_Time', 'Local_Time', 'Time', 'cloN', 'cloF', 'lai','lstN', 'lstF', 'Ts_inv', 'Tv_inv','Tsl_inv','Tsh_inv','Tsh', 'Tg', 'Tc', 'Tsky','emis' ]]
        
        # 保存合并后的数据到 CSV 文件
        merged_data.to_csv(merge_file, index=False)

        print("合并后的数据已保存到", merge_file)

    if ifval:
        merge_file = outdir + label + '_merge.csv'
        data = pd.read_csv(merge_file)

        # 观测数据 去除大气影响
        Ts_mea = data['Tg']
        Tv_mea = data['Tc']
        Tsh_mea = data['Tsh']
        Tsky_mea = data['Tsky']
        emis_mea = data['emis']

        Ts_mea = remove_emissivity(Ts_mea, emis_mea, Tsky_mea,wl = 10.55)
        Tv_mea = remove_emissivity(Tv_mea, emis_mea, Tsky_mea,wl = 10.55)
        Tsh_mea = remove_emissivity(Tsh_mea, emis_mea, Tsky_mea,wl = 10.55)

        # 反演数据
        cloN = data['cloN']
        cloF = data['cloF']
        lai = data['lai']
        lstN = data['lstN']
        lstF = data['lstF']
        Ts_inv = data['Ts_inv']
        Tv_inv = data['Tv_inv']

        if m == 2 and method_effective_emissivity == 'lai':  # 两组分 LAI
            # 总误差筛选条件
            ind = (cloN == 1) * (cloF == 1) * (Ts_mea - lstN > -5)
            ind_Ts = ind * (Ts_mea.isna() == False) * (Ts_inv.isna() == False) * (np.abs(Ts_mea - Ts_inv) < 15)
            ind_Tv = ind * (Tv_mea.isna() == False) * (Tv_inv.isna() == False) * (np.abs(Tv_mea - Tv_inv) < 15)
            
            outfile_total = outdir + label + '_Ts_Tv.png'
            
            # 计算阈值
            dif_s = (Ts_mea[ind_Ts]-Ts_inv[ind_Ts])
            dif_s = 3*1.4826*np.median(np.abs(dif_s-np.median(dif_s)))
            dif_v = (Tv_mea[ind_Tv]-Tv_inv[ind_Tv])
            dif_v = 3*1.4826*np.median(np.abs(dif_v-np.median(dif_v)))
            print(f"Thresholds - Ts: {dif_s:.2f}, Tv: {dif_v:.2f}")

            # 绘制总图
            plot_combined_density(Ts_mea, Ts_inv, ind_Ts, 'Ts', dif_s,
                                  Tv_mea, Tv_inv, ind_Tv, 'Tv', dif_v,
                                  outfile_total)

            # 分白天晚上
            local_time = pd.to_datetime(data['Local_Time'])
            ind_day = (local_time.dt.hour >= 8) * (local_time.dt.hour <= 18)
            ind_night = (local_time.dt.hour < 8) + (local_time.dt.hour > 18)

            ind_Ts_day = ind_Ts * ind_day
            ind_Ts_night = ind_Ts * ind_night
            ind_Tv_day = ind_Tv * ind_day
            ind_Tv_night = ind_Tv * ind_night

            outfile_day = outdir + label + '_Ts_Tv_day.png'
            outfile_night = outdir + label + '_Ts_Tv_night.png'

            # 绘制白天
            plot_combined_density(Ts_mea, Ts_inv, ind_Ts_day, 'Ts', dif_s,
                                  Tv_mea, Tv_inv, ind_Tv_day, 'Tv', dif_v,
                                  outfile_day)
            
            # 绘制晚上
            plot_combined_density(Ts_mea, Ts_inv, ind_Ts_night, 'Ts', dif_s,
                                  Tv_mea, Tv_inv, ind_Tv_night, 'Tv', dif_v,
                                  outfile_night)

        elif method_effective_emissivity == 'ndvi' and m == 2:  # 两组分 NDVI
            ind = (cloN == 1) * (cloF == 1)
            ind_Ts = ind * (Ts_mea.isna() == False) * (Ts_inv.isna() == False) * (np.abs(Ts_mea - Ts_inv) < 15)
            ind_Tv = ind * (Tv_mea.isna() == False) * (Tv_inv.isna() == False) * (np.abs(Tv_mea - Tv_inv) < 15)
            
            # 晚上的值跳过，只取白天
            local_time = pd.to_datetime(data['Local_Time'])
            ind_day = (local_time.dt.hour >= 8) * (local_time.dt.hour <= 18)
            
            ind_Ts_day = ind_Ts * ind_day
            ind_Tv_day = ind_Tv * ind_day

            outfile_day = outdir + label + '_Ts_Tv_day.png'

            dif_s_day = (Ts_mea[ind_Ts_day]-Ts_inv[ind_Ts_day])
            dif_s_day = 3*1.4826*np.median(np.abs(dif_s_day-np.median(dif_s_day)))
            dif_v_day = (Tv_mea[ind_Tv_day]-Tv_inv[ind_Tv_day])
            dif_v_day = 3*1.4826*np.median(np.abs(dif_v_day-np.median(dif_v_day)))

            print(f"Thresholds Day - Ts: {dif_s_day:.2f}, Tv: {dif_v_day:.2f}")
            
            plot_combined_density(Ts_mea, Ts_inv, ind_Ts_day, 'Ts', dif_s_day,
                                  Tv_mea, Tv_inv, ind_Tv_day, 'Tv', dif_v_day,
                                  outfile_day)

        elif m == 3 and method_effective_emissivity == 'lai':  # 三组分 LAI
            # 总误差
            ind = (cloN == 1) * (cloF == 1)* (Ts_mea - lstN > -5)
            ind_Ts = ind * (Ts_mea.isna() == False) * (Ts_inv.isna() == False) * (np.abs(Ts_mea - Ts_inv) < 15)
            ind_Tv = ind * (Tv_mea.isna() == False) * (Tv_inv.isna() == False) * (np.abs(Tv_mea - Tv_inv) < 15)
            
            outfile_total = outdir + label + '_Ts_Tv.png'
            
            dif_s = (Ts_mea[ind_Ts]-Ts_inv[ind_Ts])
            dif_s = 3*1.4826*np.median(np.abs(dif_s-np.median(dif_s)))
            dif_v = (Tv_mea[ind_Tv]-Tv_inv[ind_Tv])
            dif_v = 3*1.4826*np.median(np.abs(dif_v-np.median(dif_v)))
            print(f"Thresholds - Ts: {dif_s:.2f}, Tv: {dif_v:.2f}")

            plot_combined_density(Ts_mea, Ts_inv, ind_Ts, 'Ts', dif_s,
                                  Tv_mea, Tv_inv, ind_Tv, 'Tv', dif_v,
                                  outfile_total)

            # 分白天晚上
            local_time = pd.to_datetime(data['Local_Time'])
            ind_day = (local_time.dt.hour >= 8) * (local_time.dt.hour <= 18)
            ind_night = (local_time.dt.hour < 8) + (local_time.dt.hour > 18)

            ind_Ts_day = ind_Ts * ind_day
            ind_Ts_night = ind_Ts * ind_night
            ind_Tv_day = ind_Tv * ind_day
            ind_Tv_night = ind_Tv * ind_night

            outfile_day = outdir + label + '_Ts_Tv_day.png'
            outfile_night = outdir + label + '_Ts_Tv_night.png'
            
            # 绘制白天
            plot_combined_density(Ts_mea, Ts_inv, ind_Ts_day, 'Ts', dif_s,
                                  Tv_mea, Tv_inv, ind_Tv_day, 'Tv', dif_v,
                                  outfile_day)
            
            # 绘制晚上
            plot_combined_density(Ts_mea, Ts_inv, ind_Ts_night, 'Ts', dif_s,
                                  Tv_mea, Tv_inv, ind_Tv_night, 'Tv', dif_v,
                                  outfile_night)