import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from util.util_aatsr import *
from datetime import datetime
import csv
import pytz
from timezonefinder import TimezoneFinder
from scipy.stats import gaussian_kde
import warnings
warnings.filterwarnings("ignore")

'''2025.10.24'''
'''验证站点反演结果'''
'''
1. 提取反演结果到csv
2. 合并站点测量结果
3. 验证、出图
'''

def get_timezone(lat, lon):
    """获取时区信息"""
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=lat, lng=lon)
    return pytz.timezone(timezone_str)

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
    plt.ylim([230, 340])
    plt.xlim([230, 340])
    plt.tight_layout()
    plt.savefig(outfile)
    plt.show()
    plt.close()



if __name__ == '__main__':
    m = 2
    ws = 5
    if_ndvi = 0 # 0 用lai反演； 1 用NDVI反演 
    label = 'inv_%01dc_%01dw_' % (m,ws) + ('ndvi' if if_ndvi == 1 else 'lai')
    base_dir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/'
    indir_h5_sites = base_dir + label + r'/'
    infile_fluxnet_xy = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/FLUXSITE_imagexy.xlsx'
    indir_fluxnet = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/Fluxnet_data/'
    
    outdir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/results/' + label + '/aatsr_inv/'
    mkdir_if_not_exist(outdir)
    outdir_merge = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/results/' + label + '/aatsr_merge/'
    mkdir_if_not_exist(outdir_merge)
    outdir_result = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/results/' + label + '/aatsr_result/'
    mkdir_if_not_exist(outdir_result)

    ifextract = 0
    ifmerge = 0
    ifval = 1


    if ifextract:
        siteNames = search_dir(indir_h5_sites,'')
        for i, siteName in enumerate(siteNames):

            '''站点筛选'''
            # if siteName != 'AU-Wom': continue

            print(i,siteName)
            indir_site = indir_h5_sites + siteName + '/'
            fileNames = search_file(indir_site, ['h5'])
            fileNames.sort()
            outfile = outdir + siteName + '.csv'
            if os.path.exists(outfile): os.remove(outfile)

            with open(outfile,'a',newline='') as f:
                f = csv.writer(f)
                f.writerow(['time', 'cloN', 'cloF', 'lai','lstN', 'lstF', 'lsct2_Ts_lai', 'lsct2_Tv_lai'])

            for i, fileName in enumerate(fileNames):
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

                if m == 2 and if_ndvi == 0:
                    items=['lsct2_Ts_lai','lsct2_Tv_lai']
                    lsct2_Ts_lai,lsct2_Tv_lai = read_h5py_items(infile,items)
                
                lstN_save = np.nanmean(lstN[ind])
                lstF_save = np.nanmean(lstF[ind])
                if lstN_save <250 or lstF_save < 250: continue
                lsct2_Ts_lai_save = np.nanmean(lsct2_Ts_lai[ind])
                lsct2_Tv_lai_save = np.nanmean(lsct2_Tv_lai[ind])
                cloN_mask_save = np.nanmean(cloN_mask[ind])
                cloF_mask_save = np.nanmean(cloF_mask[ind])
                lai_save = np.nanmean(lai[ind])

                with open(outfile,'a',newline='') as f:
                    f = csv.writer(f)
                    f.writerow([time_save, cloN_mask_save,cloF_mask_save,lai_save,lstN_save, lstF_save, lsct2_Ts_lai_save, lsct2_Tv_lai_save])

    if ifmerge:
        data = pd.read_excel(infile_fluxnet_xy)

        fileNames = search_file(outdir,'.csv')

        for i, fileName in enumerate(fileNames):
            siteName = fileName.split('.')[0]
            
            # if siteName != 'AT-Neu': continue

            print(i,siteName)
            infile_site = outdir + siteName + '.csv'
            outfile_site = outdir_merge + siteName + '.csv'
            meafile = search_file(indir_fluxnet,[siteName])[0]
            infile_mea = indir_fluxnet + meafile
            if os.path.exists(outfile_site): os.remove(outfile_site)
            lon = data[data['SITE_ID']==siteName]['LOCATION_LONG'].values[0]
            lat = data[data['SITE_ID']==siteName]['LOCATION_LAT'].values[0]
            timezone = get_timezone(lat,lon)
            print(timezone)
            
            # 读取AATSR反演结果
            aatsr_df = pd.read_csv(infile_site)
            
            # 重命名lai列为lai_aatsr
            aatsr_df = aatsr_df.rename(columns={'lai': 'lai_aatsr'})
            
            # 读取站点测量数据
            mea_df = pd.read_csv(infile_mea)
            
            # 将AATSR的UTC时间转换为标准本地时间
            aatsr_df['time_local'] = pd.to_datetime(aatsr_df['time']).dt.tz_localize('UTC').dt.tz_convert(timezone)
            
            # 将测量数据的时间戳转换为当地时区，处理夏令时问题
            # 有些时间在夏令时切换时是不存在的（NonExistentTimeError），为稳健处理使用非严格策略
            mea_df['start_time_local'] = pd.to_datetime(mea_df['TIMESTAMP_START'], format='%Y%m%d%H%M').dt.tz_localize(
                timezone, ambiguous='NaT', nonexistent='shift_forward')
            mea_df['end_time_local'] = pd.to_datetime(mea_df['TIMESTAMP_END'], format='%Y%m%d%H%M').dt.tz_localize(
                timezone, ambiguous='NaT', nonexistent='shift_forward')

            # 创建匹配条件 - 直接匹配整点或半点
            matched_indices = []
            for idx, aatsr_time in enumerate(aatsr_df['time_local']):
                # 将AATSR时间匹配到对应的整点或半点
                minute = aatsr_time.minute
                if minute < 30:
                    # 0-29分钟匹配到整点
                    target_time = aatsr_time.replace(minute=0, second=0, microsecond=0)
                else:
                    # 30-59分钟匹配到半点
                    target_time = aatsr_time.replace(minute=30, second=0, microsecond=0)
                
                # 寻找测量数据中start_time_local等于目标时间的行
                mask = mea_df['start_time_local'] == target_time
                if mask.any():
                    matched_indices.append((idx, mea_df[mask].index[0]))
                
            # 合并匹配的数据
            if matched_indices:
                # 提取匹配的AATSR数据和测量数据
                aatsr_indices, mea_indices = zip(*matched_indices)
                matched_aatsr = aatsr_df.iloc[list(aatsr_indices)].reset_index(drop=True)
                matched_mea = mea_df.iloc[list(mea_indices)].reset_index(drop=True)
                
                # 合并数据
                merged_df = pd.concat([matched_aatsr, matched_mea], axis=1)
                
                # 保存合并结果
                merged_df.to_csv(outfile_site, index=False)
                print(f"成功合并 {len(merged_df)} 条数据到 {outfile_site}")
            else:
                print(f"警告: 站点 {siteName} 没有找到匹配的数据")

    if ifval:
        indir = outdir_merge
        fileNames = search_file(indir,'.csv')
        fileNames.sort()

        lstN_all = []
        lstF_all = []
        Ts_all = []
        Tv_all = []
        lst_all = []
        fvc_all = []
        all_site_stats = []
        invalid_site = 0
        
        for i, fileName in enumerate(fileNames):
            siteName = fileName.split('.')[0]
            print(i,siteName)

            if siteName == 'US-WPT': continue  # wet 站点


            data = pd.read_csv(indir + fileName)
            fvc = data['fvc'].values / 100
            lstN = data['lstN'].values
            lstF = data['lstF'].values
            cloN = data['cloN'].values
            cloF = data['cloF'].values
            if m == 2:
                Ts_label = 'lsct%01d_Ts_' % m + 'lai' if not if_ndvi else 'ndvi'
                Tv_label = 'lsct%01d_Tv_' % m + 'lai' if not if_ndvi else 'ndvi'
                Ts = data[Ts_label].values
                Tv = data[Tv_label].values
            lst = data['LST'].values
            local_time = data['time_local'].values

            ind = (cloN == 1) * (cloF == 1) * (lst > 200)
            ind_soil = ind * (fvc < 5) * (fvc > 0)
            ind_veg = ind * (fvc > 95) * (fvc < 100)

            # 输出
            dif_therhold = 9
            if np.sum(ind_soil * (np.abs(lst-Ts)<dif_therhold)) < 5 and np.sum(ind_veg * (np.abs(lst - Tv)<dif_therhold)) < 5:
                continue
            outdir_site = outdir_result + siteName + '/'
            mkdir_if_not_exist(outdir_site)


            outfile = outdir_site + 'lstN.png'
            plot_density(lst,lstN,ind,'lst_mea','lstN',9,outfile)

            outfile = outdir_site + 'lstF.png'
            plot_density(lst,lstF,ind,'lst_mea','lstF',9,outfile)
            if np.sum(ind_soil * (np.abs(lst-Ts)<dif_therhold)) > 0:
                outfile = outdir_site + 'Ts.png'
                plot_density(lst,Ts,ind_soil,'lst_mea','Ts',9,outfile)
            if np.sum(ind_veg * (np.abs(lst - Tv<dif_therhold)))> 0:
                outfile = outdir_site + 'Tv.png'
                plot_density(lst,Tv,ind_veg,'lst_mea','Tv',9,outfile)
            
            lstN_all.append(lstN[ind])
            lstF_all.append(lstF[ind])
            Ts_all.append(Ts[ind])
            Tv_all.append(Tv[ind])
            lst_all.append(lst[ind])
            invalid_site += 1
            fvc_all.append(fvc[ind])
            

        print(f"有效站点数量: {invalid_site}")

        if len(lstN_all) > 0:
            lstN_all = np.concatenate([arr for arr in lstN_all if len(arr) > 0])
        else:
            lstN_all = np.array([])

        if len(lstF_all) > 0:
            lstF_all = np.concatenate([arr for arr in lstF_all if len(arr) > 0])
        else:
            lstF_all = np.array([])

        if len(Ts_all) > 0:
            Ts_all = np.concatenate([arr for arr in Ts_all if len(arr) > 0])
        else:
            Ts_all = np.array([])

        if len(Tv_all) > 0:
            Tv_all = np.concatenate([arr for arr in Tv_all if len(arr) > 0])
        else:
            Tv_all = np.array([])

        if len(lst_all) > 0:
            lst_all = np.concatenate([arr for arr in lst_all if len(arr) > 0])
        else:
            lst_all = np.array([])

        if len(fvc_all) > 0:
            fvc_all = np.concatenate([arr for arr in fvc_all if len(arr) > 0])
        else:
            fvc_all = np.array([])

        # 转换为numpy数组
        ind = np.ones_like(Ts_all, dtype=bool)
        outfile = outdir_result+ 'lstN.png'
        plot_density(lst_all,lstN_all,ind,'lst_mea','lstN',dif_therhold,outfile)

        outfile = outdir_result + 'lstF.png'
        plot_density(lst_all,lstF_all,ind,'lst_mea','lstF',dif_therhold,outfile)

        ind_soil = ind * (fvc_all < 5) * (fvc_all > 0)
        ind_veg = ind * (fvc_all > 95) * (fvc_all < 100)

        outfile = outdir_result + 'Ts.png'
        plot_density(lst_all,Ts_all,ind_soil,'lst_mea','Ts',dif_therhold,outfile)

        outfile = outdir_result + 'Tv.png'
        plot_density(lst_all,Tv_all,ind_veg,'lst_mea','Tv',dif_therhold,outfile)