import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from cases.AATSR_product.util.util_aatsr import *
from datetime import datetime
import csv
import pytz
from timezonefinder import TimezoneFinder

'''2025.11.11'''
'''提取反演结果'''
'''
1. 提取反演结果到csv
2. 合并站点测量结果
3. 验证、出图
'''

def get_timezone(lat, lon):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if timezone_str:
        return pytz.timezone(timezone_str)
    else:
        return None

def remove_emissivity(Tobj,emis=0.95,Tsky=240,wl = 10.8):
    Robj = planck(wl,Tobj)
    Rsky = planck(wl,Tsky)
    Robjn = (Robj-Rsky*(1-emis))/emis
    Tobjn = inv_planck(wl,Robjn)
    return Tobjn

def plot_density(data1,data2,ind,label1,label2 ,dif_therhold,outfile):
    bias,rmse,r2 = cal_rmse_r2(data1[ind],data2[ind],dif_therhold)
    invalid_num = sum(ind * (np.abs(data2-data1)<dif_therhold))
    print(label2, ': num: %03d' % invalid_num +  ' rmse:%.2f' % rmse +' bias:%.2f' % bias + ' r2:%.2f' % r2[0])

    plt.figure(figsize=(5, 4))
    plt.scatter(data1[ind], data2[ind], label=label2, color='blue')
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    plt.xlabel(label1)
    plt.ylabel(label2)
    ax = plt.gca()
    ax.text(0.99, 0.02,
            f"num = {invalid_num:d} \nr2={r2[0]:.2f} \nBias={bias:.2f} K\nRMSE={rmse:.2f} K",
            fontsize=16, ha='right', va='bottom', transform=ax.transAxes)  # 第三行
    xmin,xmax = np.min(data1[ind]) - 30, np.max(data1[ind]) +30
    plt.ylim([xmin, xmax])
    plt.xlim([xmin, xmax])
    plt.tight_layout()
    plt.savefig(outfile)
    plt.show()
    plt.close()

if __name__ == '__main__':
    m = 3
    ws = 5
    if_ndvi = 0 # 0 用lai反演； 1 用NDVI反演 
    if_bayesian = 1

    label = 'inv_%01dc_%01dw_' % (m,ws) + ('ndvi' if if_ndvi == 1 else 'lai')
    if if_bayesian: label  = 'inv_%01dc_%01dw_' % (m,ws) + 'bayesian'
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

        if m ==2:
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
            mask_x = indx==ref_indx
            mask_y = indy==ref_indy
            ind = np.bitwise_and(mask_x,mask_y)
            if sum(ind) == 0:
                print('no valid pixel')
                continue
            time_save = utc_time.item().decode('utf-8')
            name_list = ["lstN", "lstF", "cloN_mask", "cloF_mask"]
            lstN,lstF,cloN_mask,cloF_mask = read_h5py_items(infile,name_list)

            if m == 2 and if_ndvi == 0 and if_bayesian == 0:
                items=['lsct2_Ts_lai','lsct2_Tv_lai']
                Ts,Tv = read_h5py_items(infile,items)
            elif m == 2 and if_ndvi == 1 and if_bayesian == 0:
                items = ['lsct2_Ts_ndvi', 'lsct2_Tv_ndvi']
                Ts, Tv = read_h5py_items(infile, items)
            elif m == 2 and if_bayesian == 1:
                items = ['lsct2_Ts_bayesian', 'lsct2_Tv_bayesian']
                Ts, Tv = read_h5py_items(infile, items)
            elif m == 3 and if_ndvi == 0:
                items=['lsct3_Ts_lai','lsct3_Tv_lai','lsct3_Tsl_lai','lsct3_Tsh_lai']
                Ts,Tv,Tsl,Tsh = read_h5py_items(infile,items)
            elif m == 3 and if_ndvi == 1:
                items = ['lsct2_Ts_ndvi', 'lsct2_Tv_ndvi','lsct3_Tsl_ndvi','lsct3_Tsh_ndvi']
                Ts, Tv,Tsl,Tsh = read_h5py_items(infile, items)
            
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

        ind =  (data['cloN'] == 1) * (data['cloF'] == 1)

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

        if m ==2 and if_ndvi == 0:  # 两组分 LAI
            # 总误差
            ind = (cloN == 1) * (cloF == 1) * (Ts_mea - lstN > -5)
            ind_Ts = ind * (Ts_mea.isna() == False) * (Ts_inv.isna() == False) * (np.abs(Ts_mea - Ts_inv) < 15)
            ind_Tv = ind * (Tv_mea.isna() == False) * (Tv_inv.isna() == False) * (np.abs(Tv_mea - Tv_inv) < 15)
            outfile_ts = outdir + label + '_Ts.png'
            outfile_tv = outdir + label + '_Tv.png'
            
            dif_s = (Ts_mea[ind_Ts]-Ts_inv[ind_Ts])
            dif_s = 3*1.4826*np.median(np.abs(dif_s-np.median(dif_s)))
            dif_v = (Tv_mea[ind_Tv]-Tv_inv[ind_Tv])
            dif_v = 3*1.4826*np.median(np.abs(dif_v-np.median(dif_v)))
            print(dif_s,dif_v)

            plot_density(Ts_mea,Ts_inv,ind_Ts,'Tg_mea','Ts_inv',dif_s,outfile_ts)
            plot_density(Tv_mea,Tv_inv,ind_Tv,'Tc_mea','Tv_inv',dif_v,outfile_tv)

            # 分白天晚上
            local_time = pd.to_datetime(data['Local_Time'])
            ind_day = (local_time.dt.hour >= 8) * (local_time.dt.hour <= 18)
            ind_night = (local_time.dt.hour < 8) + (local_time.dt.hour > 18)

            ind_Ts_day = ind_Ts * ind_day
            ind_Ts_night = ind_Ts * ind_night
            ind_Tv_day = ind_Tv * ind_day
            ind_Tv_night = ind_Tv * ind_night

            outfile_ts_day = outdir + label + '_Ts_day.png'
            outfile_ts_night = outdir + label + '_Ts_night.png'
            outfile_tv_day = outdir + label + '_Tv_day.png'
            outfile_tv_night = outdir + label + '_Tv_night.png'

            dif_s_day = (Ts_mea[ind_Ts_day]-Ts_inv[ind_Ts_day])
            dif_s_day = 3*1.4826*np.median(np.abs(dif_s_day-np.median(dif_s_day)))
            dif_s_night = (Ts_mea[ind_Ts_night]-Ts_inv[ind_Ts_night])
            dif_s_night = 3*1.4826*np.median(np.abs(dif_s_night-np.median(dif_s_night)))
            dif_v_day = (Tv_mea[ind_Tv_day]-Tv_inv[ind_Tv_day])
            dif_v_day = 3*1.4826*np.median(np.abs(dif_v_day-np.median(dif_v_day)))
            dif_v_night = (Tv_mea[ind_Tv_night]-Tv_inv[ind_Tv_night])
            dif_v_night = 3*1.4826*np.median(np.abs(dif_v_night-np.median(dif_v_night)))

            # print(dif_s_day,dif_s_night,dif_v_day,dif_v_night)
            # plot_density(Ts_mea,Ts_inv,ind_Ts_day,'Tg_mea','Ts_inv',dif_s_day,outfile_ts_day)
            # plot_density(Ts_mea,Ts_inv,ind_Ts_night,'Tg_mea','Ts_inv',dif_s_night,outfile_ts_night)
            # plot_density(Tv_mea,Tv_inv,ind_Tv_day,'Tc_mea','Tv_inv',dif_v_day,outfile_tv_day)
            # plot_density(Tv_mea,Tv_inv,ind_Tv_night,'Tc_mea','Tv_inv',dif_v_night,outfile_tv_night)
            print(dif_s_day,dif_s_night,dif_v_day,dif_v_night)
            plot_density(Ts_mea,Ts_inv,ind_Ts_day,'Tg_mea','Ts_inv',dif_s,outfile_ts_day)
            plot_density(Ts_mea,Ts_inv,ind_Ts_night,'Tg_mea','Ts_inv',dif_s,outfile_ts_night)
            plot_density(Tv_mea,Tv_inv,ind_Tv_day,'Tc_mea','Tv_inv',dif_v,outfile_tv_day)
            plot_density(Tv_mea,Tv_inv,ind_Tv_night,'Tc_mea','Tv_inv',dif_v,outfile_tv_night)


        elif if_ndvi == 1 and m == 2:  # 两组分 NDVI
            ind = (cloN == 1) * (cloF == 1)
            ind_Ts = ind * (Ts_mea.isna() == False) * (Ts_inv.isna() == False) * (np.abs(Ts_mea - Ts_inv) < 15)
            ind_Tv = ind * (Tv_mea.isna() == False) * (Tv_inv.isna() == False) * (np.abs(Tv_mea - Tv_inv) < 15)
            # 晚上的值跳过
            local_time = pd.to_datetime(data['Local_Time'])
            ind_day = (local_time.dt.hour >= 8) * (local_time.dt.hour <= 18)
            ind_night = (local_time.dt.hour < 8) + (local_time.dt.hour > 18)

            ind_Ts_day = ind_Ts * ind_day
            ind_Tv_day = ind_Tv * ind_day

            outfile_ts_day = outdir + label + '_Ts_day.png'
            outfile_tv_day = outdir + label + '_Tv_day.png'

            dif_s_day = (Ts_mea[ind_Ts_day]-Ts_inv[ind_Ts_day])
            dif_s_day = 3*1.4826*np.median(np.abs(dif_s_day-np.median(dif_s_day)))
            dif_v_day = (Tv_mea[ind_Tv_day]-Tv_inv[ind_Tv_day])
            dif_v_day = 3*1.4826*np.median(np.abs(dif_v_day-np.median(dif_v_day)))

            print(dif_s_day,dif_v_day)
            plot_density(Ts_mea,Ts_inv,ind_Ts_day,'Tg_mea','Ts_inv',dif_s_day,outfile_ts_day)
            plot_density(Tv_mea,Tv_inv,ind_Tv_day,'Tc_mea','Tv_inv',dif_v_day,outfile_tv_day)

        elif m == 3 and if_ndvi == 0:  # 三组分 LAI
            # 总误差
            ind = (cloN == 1) * (cloF == 1)
            ind_Ts = ind * (Ts_mea.isna() == False) * (Ts_inv.isna() == False) * (np.abs(Ts_mea - Ts_inv) < 15)
            ind_Tv = ind * (Tv_mea.isna() == False) * (Tv_inv.isna() == False) * (np.abs(Tv_mea - Tv_inv) < 15)
            outfile_ts = outdir + label + '_Ts.png'
            outfile_tv = outdir + label + '_Tv.png'
            
            dif_s = (Ts_mea[ind_Ts]-Ts_inv[ind_Ts])
            dif_s = 3*1.4826*np.median(np.abs(dif_s-np.median(dif_s)))
            dif_v = (Tv_mea[ind_Tv]-Tv_inv[ind_Tv])
            dif_v = 3*1.4826*np.median(np.abs(dif_v-np.median(dif_v)))
            print(dif_s,dif_v)

            plot_density(Ts_mea,Ts_inv,ind_Ts,'Tg_mea','Ts_inv',dif_s,outfile_ts)
            plot_density(Tv_mea,Tv_inv,ind_Tv,'Tc_mea','Tv_inv',dif_v,outfile_tv)

            # 分白天晚上
            local_time = pd.to_datetime(data['Local_Time'])
            ind_day = (local_time.dt.hour >= 8) * (local_time.dt.hour <= 18)
            ind_night = (local_time.dt.hour < 8) + (local_time.dt.hour > 18)

            ind_Ts_day = ind_Ts * ind_day
            ind_Ts_night = ind_Ts * ind_night
            ind_Tv_day = ind_Tv * ind_day
            ind_Tv_night = ind_Tv * ind_night

            outfile_ts_day = outdir + label + '_Ts_day.png'
            outfile_ts_night = outdir + label + '_Ts_night.png'
            outfile_tv_day = outdir + label + '_Tv_day.png'
            outfile_tv_night = outdir + label + '_Tv_night.png'

            dif_s_day = (Ts_mea[ind_Ts_day]-Ts_inv[ind_Ts_day])
            dif_s_day = 3*1.4826*np.median(np.abs(dif_s_day-np.median(dif_s_day)))
            dif_s_night = (Ts_mea[ind_Ts_night]-Ts_inv[ind_Ts_night])
            dif_s_night = 3*1.4826*np.median(np.abs(dif_s_night-np.median(dif_s_night)))
            dif_v_day = (Tv_mea[ind_Tv_day]-Tv_inv[ind_Tv_day])
            dif_v_day = 3*1.4826*np.median(np.abs(dif_v_day-np.median(dif_v_day)))
            dif_v_night = (Tv_mea[ind_Tv_night]-Tv_inv[ind_Tv_night])
            dif_v_night = 3*1.4826*np.median(np.abs(dif_v_night-np.median(dif_v_night)))

            print(dif_s_day,dif_s_night,dif_v_day,dif_v_night)
            plot_density(Ts_mea,Ts_inv,ind_Ts_day,'Tg_mea','Ts_inv',dif_s_day,outfile_ts_day)
            plot_density(Ts_mea,Ts_inv,ind_Ts_night,'Tg_mea','Ts_inv',dif_s_night,outfile_ts_night)
            plot_density(Tv_mea,Tv_inv,ind_Tv_day,'Tc_mea','Tv_inv',dif_v_day,outfile_tv_day)
            plot_density(Tv_mea,Tv_inv,ind_Tv_night,'Tc_mea','Tv_inv',dif_v_night,outfile_tv_night)