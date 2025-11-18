import calendar
from utils.old.util import *
from datetime import datetime


def cal_rmse_r2(data1,data2,tshred=10):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2

'''验证2009年Dahra站点'''
'''先从lsct日图中提取组分温度，再与实测数据匹配'''

indir_type = r'D:\data\type\\'
oudir_composite = r'E:\AATSR\2009\lsct_day\\'
outfile = r'E:\AATSR\2009\Dahra_retrieve.txt'
file_path = 'D:\data\LSCT_Validation\Dahra_2009\Dahra_LST.xlsx'


ifget_from_day_product = 0
ifval = 0

if ifget_from_day_product:
    '''根据坐标找图上坐标'''
    lat_ =np.asarray([15.402])
    lon_ = np.asarray([-15.443])
    type_dir_2000 = indir_type + 'type_world_2000.tif'
    type, ns, nl, nb, geog, proj,dataset = read_image_dataset_gdal(type_dir_2000)
    imagex_,imagey_ = loc2map(lat_,lon_,dataset)

    imagex_ = imagex_
    imagey_ = imagey_

    '''找图上点'''
    year = 2009
    doy_ = []
    time_ = []
    lsct_s_ = []
    lsct_v_ = []
    lst_n_ = []
    lst_f_ = []
    for month in range(7,12):
        daynum = calendar.monthrange(year,month)[1]
        for d in range(daynum):
            day = d + 1
            print(year,month,day)
            lsctdir_day = oudir_composite + '%02d' % int(month) + "//" + '%02d' % int(day) + "//"
            if not os.path.exists(lsctdir_day): continue
            infile_lsct_s = lsctdir_day + "AATSR_" + str(year) + '_%02d' % int(month) + '_%02d' % int(day) + '_lsct_s.tif'
            infile_lsct_v = lsctdir_day + "AATSR_" + str(year) + '_%02d' % int(month) + '_%02d' % int(day) + '_lsct_v.tif'
            infile_lst_n = lsctdir_day + "AATSR_" + str(year) + '_%02d' % int(month) + '_%02d' % int(day) + '_lst_n.tif'
            infile_lst_f = lsctdir_day + "AATSR_" + str(year) + '_%02d' % int(month) + '_%02d' % int(day) + '_lst_f.tif'
            infile_time = lsctdir_day + "AATSR_" + str(year) + '_%02d' % int(month) + '_%02d' % int(day) + '_time.tif'
            if not os.path.exists(infile_lsct_s): continue
            [lsct_s, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lsct_s)
            print(lsct_s[imagex_[0],imagey_[0]])
            if lsct_s[imagex_[0],imagey_[0]] != 0:
                [lsct_v, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lsct_v)
                [lst_n, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lst_n)
                [lst_f, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lst_f)
                [time, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_time)

                # lsct_s_.append(lsct_s[imagex_[0],imagey_[0]])
                # lsct_v_.append(lsct_v[imagex_[0], imagey_[0]])
                # lst_n_.append(lst_n[imagex_[0], imagey_[0]])
                # lst_f_.append(lst_f[imagex_[0], imagey_[0]])

                '''保存平均信息'''
                lsct_s_window = lsct_s[imagex_[0]-1:imagex_[0]+2,imagey_[0]-1:imagey_[0]+2]
                lsct_s_.append(np.sum(lsct_s_window)/np.count_nonzero(lsct_s_window))
                lsct_v_window = lsct_v[imagex_[0]-1:imagex_[0]+2,imagey_[0]-1:imagey_[0]+2]
                lsct_v_.append(np.sum(lsct_v_window)/np.count_nonzero(lsct_v_window))
                lst_f_window = lst_f[imagex_[0]-1:imagex_[0]+2,imagey_[0]-1:imagey_[0]+2]
                lst_f_.append(np.sum(lst_f_window)/np.count_nonzero(lst_f_window))
                lst_n_window = lst_n[imagex_[0] - 1:imagex_[0] + 2, imagey_[0] - 1:imagey_[0] + 2]
                lst_n_.append(np.sum(lst_n_window) / np.count_nonzero(lst_n_window))

                time_.append(time[imagex_[0], imagey_[0]])
                doy_.append(date2DOY(year,month,day))
                print(lsct_v[imagex_[0], imagey_[0]])
                print(date2DOY(year,month,day))
    result = np.vstack([doy_, time_, lst_n_, lst_f_, lsct_s_,lsct_v_])
    result = np.transpose(result)
    np.savetxt(outfile, result, fmt='%.3f')

if ifval:
    '''读取数据提取的txt数据'''
    data = read_txt_float(outfile)
    idex = np.lexsort([data[:, 0]])
    data = data[idex, :]
    doy_ = data[:, 0]
    secnum_ = data[:, 1]
    lstN_inv = data[:, 2]/100
    lstO_inv = data[:, 3]/100
    lsct_s_inv = data[:, 4]/100
    lsct_v_inv = data[:, 5]/100

    hour_ = secnum_ // 3600
    min_ = (secnum_ - 3600 * hour_)//60
    sec_ = secnum_ % 60
    year = 2009

    '''读入验证数据'''
    df = pd.read_excel(file_path)
    df = df.dropna()
    df['Time'] = pd.to_datetime(df['Time'])

    time_mea = []
    lsct_s_mea = []
    lsct_v_mea = []
    for i in range(len(doy_)):
        month, day = doy2date(year, doy_[i])
        search_time = datetime(year, month, day, int(hour_[i]), int(min_[i]), int(sec_[i]))
        filtered_data = df[(df['Time'] >= search_time - pd.Timedelta(minutes=7.5)) & (df['Time'] <= search_time + pd.Timedelta(minutes=7.5))]
        if filtered_data.empty:
            time_mea.append(0)
            lsct_s_mea.append(0)
            lsct_v_mea.append(0)
        else:
            time_mea.append(filtered_data['Time'].iloc[0])
            lsct_s_mea.append(filtered_data['Tg'].iloc[0]+273.15)
            lsct_v_mea.append(filtered_data['Tc'].iloc[0]+273.15)

    '''剔除异常值'''
    tep_min = 240
    tep_max = 350

    ind = (lsct_s_inv>tep_min)*(lsct_s_inv<tep_max)*(lsct_v_inv>tep_min)*(lsct_s_inv<tep_max)*(np.array(lsct_v_mea)>tep_min)*(np.abs(np.array(lsct_s_mea)-lsct_s_inv)<15)*(np.abs(np.array(lsct_v_mea)-lsct_v_inv)<15)

    '''验证并作图'''

    dif_threshold = 10
    ts_mea,tc_mea,ts_inv,tc_inv = np.array(lsct_s_mea),np.array(lsct_v_mea),lsct_s_inv,lsct_v_inv
    bias_tss, rmse_tss, r2_tss = cal_rmse_r2(ts_mea[ind], ts_inv[ind], dif_threshold)
    bias_tc, rmse_tc, r2_tc = cal_rmse_r2(tc_mea[ind], tc_inv[ind], dif_threshold)
    mea = np.stack([ts_mea[ind], tc_mea[ind]])
    inv = np.stack([ts_inv[ind], tc_inv[ind]])
    bias_all, rmse_all, r2_all = cal_rmse_r2(mea, inv, dif_threshold)
    print("Dahra")
    print("bias:%.2f,%.2f,%.2f" % (bias_tss, bias_tc, bias_all))
    print("r2:%.3f,%.3f,%.3f" % (r2_tss[0], r2_tc[0], r2_all[0]))
    print("rmse:%.2f,%.2f,%.2f" % (rmse_tss, rmse_tc, rmse_all))

    plt.figure(figsize=[4.5, 4], dpi=300)
    plt.plot(ts_mea[ind], ts_inv[ind], 'ro')
    # plt.plot(tsh_forest_mea[ind],tsh_forest_inv[ind],'bo')
    plt.plot(tc_mea[ind], tc_inv[ind], 'go')
    plt.xlim([280, 340])
    plt.ylim([280, 340])
    plt.plot([250, 350], [250, 350], 'k--')
    plt.xlabel('Measured Temperature/K')
    plt.ylabel('Inverted Temperature/K')
    plt.legend(['Soil', 'Canopy'])
    plt.title('Dahra')
    plt.show()