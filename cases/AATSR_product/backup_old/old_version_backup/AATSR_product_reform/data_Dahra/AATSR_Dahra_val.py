import csv
from timezonefinder import TimezoneFinder
import pytz
from utils.old.util import *
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

'''2024.3.18'''
'''脚本用于验证Dahra站点的结果'''
'''首先提取成csv，再验证出图'''
'''h5文件来源于 \data_fluxnet\AATSR_extract_site_lsct_h5.py的切片h5'''

base_dir = r"D:\data\AATSR_product\Dahra_2009\\"
mea_file = r'D:\data\AATSR_product\Dahra_2009\Dahra_LST.xlsx'
h5_file_dir = r"D:\data\AATSR_product\Dahra_2009\SN-Dhr_lsct3\\"
extract_file = base_dir + "AATSR_lsct3.csv"
merge_file = base_dir + "AATSR_merge_lsct3.csv"

ifextract = 1
ifmerge = 1
ifval = 1

if ifextract:
    indir = h5_file_dir
    if os.path.exists(extract_file): os.remove(extract_file)
    h5Files = search_file_rej(indir,".h5","enp")
    for h5File in h5Files:
        infile = indir + h5File
        year = int(h5File.split('_')[1])
        doy = int(h5File.split('_')[2])
        month,day = doy2date(year,doy)

        '''读取数据'''
        name_list = ["indx", "indy", "ref_indx", "ref_indy", "type", "lai", "sec", "ref_tmie", "lstN", "lstO", "Ts","Tv",'Tsl','Tsh','Psoil','fvc']
        indx,indy,ref_indx,ref_indy,type,lai,sec,ref_time,lstN,lstO,Ts,Tv,Tsl,Tsh,Psoil,fvc = read_h5py_items(infile,name_list)
        mask_x = indx==ref_indx
        mask_y = indy==ref_indy
        ind = np.bitwise_and(mask_x,mask_y)
        if sum(ind) == 0: continue

        h = sec // 3600
        m = (sec - h *3600) // 60
        s = sec - h*3600 - m*60
        if h >= 24: h=h-24
        time_save = datetime(year,month,day,int(h),int(m),int(s))
        lai_save = np.average(lai[ind])
        lstN_save = np.average(lstN[ind])/100
        lstO_save = np.average(lstO[ind])/100
        Ts_save = np.average(Ts[ind])
        Tv_save = np.average(Tv[ind])
        Tsl_save = np.average(Tsl[ind])
        Tsh_save = np.average(Tsh[ind])
        Psoil_save = np.average(Psoil[ind])
        fvc_save = np.average(fvc[ind])

        with open(extract_file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([time_save, lai_save, lstN_save, lstO_save, Ts_save, Tv_save,Tsl_save,Tsh_save,Psoil_save,fvc_save])


def get_timezone(lat, lon):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if timezone_str:
        return pytz.timezone(timezone_str)
    else:
        return None

if ifmerge:
    if os.path.exists(merge_file): os.remove(merge_file)
    lon = -15.443
    lat = 15.402
    timezone = get_timezone(lat, lon)
    infile = extract_file
    data = []
    with open(infile, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            utc_time_str = row[0]  # 假设 UTC 时间在第一列
            utc_time = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
            local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone)
            lstN = float(row[2])  # 假设 Ts 在第五列
            lstO = float(row[3])  # 假设 Tv 在第六列
            ts = float(row[4])  # 假设 Ts 在第五列
            tv = float(row[5])  # 假设 Tv 在第六列
            tsl = float(row[6])
            tsh = float(row[7])
            Psoil = float(row[8])
            fvc = float(row[9])
            data.append([utc_time_str, local_time.strftime('%Y-%m-%d %H:%M:%S'), lstN,lstO,ts, tv,tsl,tsh,Psoil,fvc])

    df = pd.DataFrame(data, columns=['UTC_Time', 'Local_Time','lstN','lstO', 'Ts', 'Tv','Tsl_inv','Tsh_inv','Psoil','fvc'])

    # 先读取地面数据
    ground_data = pd.read_excel(mea_file)

    # 将地面数据的时间列转换为 datetime 对象
    ground_data['Time'] = pd.to_datetime(ground_data['Time'], format='%Y/%m/%d %H:%M')

    # 将 df 中的时间列也转换为 datetime 对象
    df['Local_Time'] = pd.to_datetime(df['Local_Time'])

    # 合并数据，选择 df 中在地面数据时间范围内的行
    merged_data = pd.DataFrame()
    for idx, row in df.iterrows():
        local_time = row['Local_Time']
        filtered_ground_data = ground_data[(ground_data['Time'] <= local_time + pd.Timedelta(minutes=7.5)) &
                                           (ground_data['Time'] >= local_time - pd.Timedelta(minutes=7.5))]  # 选择30分钟内的数据

        if not filtered_ground_data.empty:
            merged_row = row.to_frame().T.assign(**filtered_ground_data.iloc[0])
            merged_row['Tg'] += 273.15
            merged_row['Tc'] += 273.15
            merged_row['Tsh'] += 273.15
            merged_data = pd.concat([merged_data, merged_row], axis=0)

    merged_data = merged_data[
        ['UTC_Time', 'Local_Time', 'Time','lstN','lstO', 'Ts', 'Tv', 'Tsl_inv','Tsh_inv','Tsh', 'Tg', 'Tc','Psoil','fvc']]

    # 保存合并后的数据到 CSV 文件
    merged_data.to_csv(merge_file, index=False)

    print("合并后的数据已保存到", merge_file)


def cal_rmse_r2(data1,data2,tshred=10):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2


if ifval:
    therhold = 7.5
    infile = merge_file
    data = pd.read_csv(infile)
    data['Local_Time'] = pd.to_datetime(data['Local_Time'], format='%Y/%m/%d %H:%M')
    data = data[(data['Local_Time'].dt.hour >= 8) & (data['Local_Time'].dt.hour < 18)]
    data['UTC_Time'] = pd.to_datetime(data['UTC_Time'], format='%Y/%m/%d %H:%M')
    data['YearDay'] = data['UTC_Time'].dt.strftime('%j').astype(int)

    tsl_inv = data['Tsl_inv']
    tv_inv = data['Tv']
    tsl_mea = data['Tg']
    tv_mea = data['Tc']
    tsh_mea = data['Tsh']
    tsh_inv = data['Tsh_inv']
    ts_inv = data['Ts']
    Psoil = data['Psoil']
    fvc = data['fvc']

    tsl_mea_ = np.zeros(shape(tsl_mea))
    tsh_mea_ = np.zeros(shape(tsh_mea))
    tsl_mea_[tsl_mea>tsh_mea] = tsl_mea[tsl_mea>tsh_mea]
    tsl_mea_[tsl_mea < tsh_mea] = tsh_mea[tsl_mea < tsh_mea]
    tsh_mea_[tsl_mea > tsh_mea] = tsh_mea[tsl_mea > tsh_mea]
    tsh_mea_[tsl_mea < tsh_mea] = tsl_mea[tsl_mea < tsh_mea]
    tsl_mea = tsl_mea_
    tsh_mea = tsh_mea_

    ts_mea = inv_planck(10.8, Psoil * planck(10.8, tsl_mea) + (1 - Psoil) * planck(10.8, tsh_mea))
    lst_mea = inv_planck(10.8, fvc * planck(10.8, tv_mea) + (1 - fvc) * planck(10.8, ts_mea))
    lst_inv = inv_planck(10.8, fvc * planck(10.8, tv_inv) + (1 - fvc) * planck(10.8, ts_inv))

    invalid_num = sum(np.abs(tsl_mea - tsl_inv) < therhold)
    print("--------------------------------------------------------------------------------")
    # print("Dahra")
    bias_s, rmse_s, r2_s = cal_rmse_r2(ts_mea, ts_inv, therhold)
    bias_sl, rmse_sl, r2_sl = cal_rmse_r2(tsl_mea, tsl_inv, therhold)
    bias_sh, rmse_sh, r2_sh = cal_rmse_r2(tsh_mea[tsh_mea<tsl_mea], tsh_inv[tsh_mea<tsl_mea], therhold)
    bias_v, rmse_v, r2_v = cal_rmse_r2(tv_mea, tv_inv, therhold)
    bias, rmse, r2 = cal_rmse_r2(lst_mea, lst_inv, therhold)
    print("光照土壤 RMSE/Bias/R2/num: %.3f/%.3f/%.3f/%03d" % (rmse_sl, bias_sl, r2_sl[0],sum(np.abs(tsl_mea - tsl_inv) < therhold)))
    print("阴影土壤 RMSE/Bias/R2/num: %.3f/%.3f/%.3f/%03d" % (rmse_sh, bias_sh, r2_sh[0],sum(np.abs(tsh_mea[tsh_mea<tsl_mea] - tsh_inv[tsh_mea<tsl_mea]) < therhold)))
    print("土壤 RMSE/Bias/R2/num: %.3f/%.3f/%.3f/%03d" % (rmse_s, bias_s, r2_s[0],sum(np.abs(ts_mea - ts_inv) < therhold)))
    print("植被 RMSE/Bias/R2/num: %.3f/%.3f/%.3f/%03d" % (rmse_v, bias_v, r2_v[0],sum(np.abs(tv_mea - tv_inv) < therhold)))
    print("lst RMSE/Bias/R2/num: %.3f/%.3f/%.3f/%03d" % (rmse, bias, r2[0], sum(np.abs(lst_mea - lst_inv) < therhold)))

    # 绘制散点图
    plt.rc('font', family='Times New Roman', size=12)
    ind = (tsl_mea > 220) * (tsl_mea < 370) * (tsl_inv > 220) * (tsl_inv < 370) * (tsl_inv != 273.15)
    ind_ts = ind * (np.abs(ts_inv - ts_mea) < therhold)
    ind_tsl = ind * (np.abs(tsl_inv-tsl_mea)<therhold)
    ind_tsh = ind * (np.abs(tsh_inv - tsh_mea) < therhold) * (tsl_mea>tsh_mea)
    ind_tv = ind * (np.abs(tv_inv - tv_mea) < therhold)
    ind_lst = ind * (np.abs(lst_inv - lst_mea) < therhold)
    plt.figure(figsize=(4.5, 4.5),dpi=600)
    # plt.scatter(tsl_mea[ind_tsl], tsl_inv[ind_tsl], label='Sunlit Soil', color='red',s=40)
    # plt.scatter(tsh_mea[ind_tsh], tsh_inv[ind_tsh], label='Shaded Soil',color = 'blue',s=40)
    plt.scatter(ts_mea[ind_ts], ts_inv[ind_ts], label='soil', color='red',s=40)
    plt.scatter(tv_mea[ind_tv], tv_inv[ind_tv], label='Vegetation', color='green',s=40)
    plt.scatter(lst_mea[ind_lst], lst_inv[ind_lst], label='lst', color='black', s=40)
    plt.plot([220, 370], [220, 370], color='black', linestyle='--')  # 添加1:1线
    # plt.plot([220, 370], [215, 365], color='grey', linestyle='--')  # 添加y=x-5线
    # plt.plot([220, 370], [225, 375], color='grey', linestyle='--')  # 添加y=x+5线
    # plt.plot([220, 370], [210, 360], color='grey', linestyle='--')  # 添加y=x-10线
    # plt.plot([220, 370], [230, 380], color='grey', linestyle='--')  # 添加y=x+10线
    plt.ylim([280,340])
    plt.xlim([280,340])
    plt.xlabel('Measured')
    plt.ylabel('Inversion')
    # plt.title("Dahra")
    plt.legend()
    plt.show()

    #
    # 绘制折线图
    ind_tsl = ind * (np.abs(tsl_inv-tsl_mea)<therhold+5)
    ind_tsh = ind * (np.abs(tsh_inv - tsh_mea) < therhold+5) * (tsl_mea>tsh_mea)
    ind_tv = ind * (np.abs(tv_inv - tv_mea) < therhold +5)
    doy = data['YearDay']
    plt.figure(figsize=(6, 4.5))
    # plt.plot(doy[ind_tsl], tsl_inv[ind_tsl], label='Tsl_inv', color='red')
    # plt.plot(doy[ind_tsh], tsh_inv[ind_tsh], label='Tsh_inv', color=
    plt.plot(doy[ind_lst], lst_inv[ind_lst], label='lst_inv', color='black')
    plt.plot(doy[ind_ts], ts_inv[ind_ts], label='Ts_inv', color='red')
    plt.plot(doy[ind_tv], tv_inv[ind_tv], label='Tv_inv', color='green')

    # plt.scatter(doy[ind_tsl], tsl_mea[ind_tsl], label='Tsl_mea', color='orange')
    # plt.scatter(doy[ind_tsh], tsh_mea[ind_tsh], label='Tsh_mea', color='purple')
    plt.scatter(doy[ind_lst], lst_mea[ind_lst], label='lst_mea', color='black')
    plt.scatter(doy[ind_ts], ts_mea[ind_ts], label='Ts_mea', color='red')
    plt.scatter(doy[ind_tv], tv_mea[ind_tv], label='Tv_mea', color='grey')

    plt.xlabel('Year Day')
    plt.ylabel('Temperature (K)')
    plt.title('Temperature Variation')
    plt.legend()
    plt.ylim(290,340)
    plt.ylim(290,340)
    plt.grid(True)
    plt.show()
    #
    # # 绘制折线图
    # doy = data['YearDay']
    # plt.figure(figsize=(4.5, 3))
    # plt.plot(doy[ind_tsl], tsl_inv[ind_tsl], label='Tsl_inv', color='red')
    # plt.scatter(doy[ind_tsl], tsl_mea[ind_tsl], label='Tsl_mea', color='orange')
    # # plt.xlabel('Year Day')
    # plt.ylabel('Tsl (K)')
    # # plt.legend()
    # plt.ylim(300,340)
    # plt.grid(True)
    # plt.tight_layout()
    # plt.show()
    #
    # # 绘制折线图
    # doy = data['YearDay']
    # plt.figure(figsize=(4.5, 3))
    # plt.plot(doy[ind_tsh], tsh_inv[ind_tsh], label='Tsh_inv', color='blue')
    # plt.scatter(doy[ind_tsh], tsh_mea[ind_tsh], label='Tsh_mea', color='purple')
    # # plt.xlabel('Year Day')
    # plt.ylabel('Tsh (K)')
    # # plt.legend()
    # plt.ylim(290,330)
    # plt.ylim(290,330)
    # plt.grid(True)
    # plt.tight_layout()
    # plt.show()
    #
    # # 绘制折线图
    # doy = data['YearDay']
    # plt.figure(figsize=(4.5,3))
    # plt.plot(doy[ind_tv], tv_inv[ind_tv], label='Tv_inv', color='green')
    # plt.scatter(doy[ind_tv], tv_mea[ind_tv], label='Tv_mea', color='grey')
    # plt.xlabel('Year Day')
    # plt.ylabel('Tv (K)')
    # # plt.legend()
    # plt.ylim(290,330)
    # plt.ylim(290,330)
    # plt.grid(True)
    # plt.tight_layout()
    # plt.show()