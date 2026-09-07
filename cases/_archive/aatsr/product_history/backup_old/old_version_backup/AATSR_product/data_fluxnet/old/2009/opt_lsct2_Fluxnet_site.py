from opt_lsct.multiple_lsct import *
from utils.old.util_lsct import *
import warnings
warnings.filterwarnings("ignore")
from utils.old.util_constant import *
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime, timedelta

'''2024.4.16'''
'''重跑Fluxnet站点组分温度'''
'''2024.1.16'''
'''1.加入植被结构改善部分'''

def get_timezone(lat, lon):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if timezone_str:
        return pytz.timezone(timezone_str)
    else:
        return None

def cal_fvc_from_lai(thetav,lai):
    G = 0.5
    rd = np.pi / 180.0
    costhetanv = np.cos(thetav * rd)
    fvc = 1 - exp(-G*lai/costhetanv)
    fvc[fvc>1] = 1
    fvc[fvc<0] = 0
    return fvc

def line_inv_2_s(wNLine, wOLine, radNLine, radOLine, maskLine,nl = 1024):
    '''
    this is for the sample rec
    '''
    wl = 10.8
    off_ = 0
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.05
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    number_component = 2
    number_angle = 2
    number_value_threshold = 12

    result = np.zeros([number_component,nl])
    result_point = np.zeros([number_component, nl])

    off = 2
    for kk in range(off, nl-off):
        maskk = maskLine[kk,2]
        if maskk == 0: continue

        nl1 = kk - off
        nl2 = kk + off + 1
        ###### w1是nadir，w2是oblique
        w1 = wNLine[:,nl1:nl2,:]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, nl1:nl2, :]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))

        bb1 = (np.reshape(radNLine[nl1:nl2, :], -1))
        bb2 = (np.reshape(radOLine[nl1:nl2, :], -1))

        mask = np.reshape(maskLine[nl1:nl2, :], -1)
        ind = (mask == 1) * (np.isnan(w1[0, :]) == 0)

        num_val_point = np.sum(ind)
        if (num_val_point < number_value_threshold): continue
        ns_temp = np.asarray([-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
        nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
        part = 6

        n0 = np.ones(len(ns_temp))
        x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
        w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])  # 25*6
        w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

        ww = np.hstack((w11[:, ind], w22[:, ind]))
        bb = np.hstack((bb1[ind], bb2[ind]))

        ###############################################
        ### least-square method
        ###############################################
        ww = np.transpose(ww)

        coeffprior = np.asarray(lstsq(ww, bb)[0])
        # coeffprior = np.asarray(lstsq(ww, bb, rcond=None)[0])

        ################################################
        ### first reult with averaing information
        ################################################
        offcenter = np.int_(((2 * off + 1) * (2 * off + 1) - 1) / 2)
        fd = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
        fd = np.reshape(fd, -1) * 1.0

        coeffprior = np.asarray(coeffprior)
        ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
        ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
        indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                 (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold)
        apoint = np.sum(indnew)
        if (apoint <= 1):
            cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
            cd2 = np.sum(coeffprior[part:] * x[:, offcenter])
            ctprior = np.transpose(np.matrix([cd1, cd2]))
        else:
            fd[indnew] = fd[indnew] / np.sum(fd[indnew])

            cd1new = np.sum(ct1[indnew] * fd[indnew])
            cd2new = np.sum(ct2[indnew] * fd[indnew])
            ctprior = np.transpose(np.matrix([cd1new, cd2new]))
        # component_temperature = inv_planck(wl, ctprior)
        #################################################
        ### second result by combining one-point result
        #################################################

        nl1 = kk - off_
        nl2 = kk + off_ + 1
        w1 = wNLine[:,nl1:nl2, 2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,nl1:nl2, 2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        b1 = (np.reshape(radNLine[nl1:nl2,2], -1))
        b2 = (np.reshape(radOLine[nl1:nl2,2], -1))
        w = np.hstack((w1, w2))
        b = np.hstack((b1, b2))
        w = np.transpose(w)

        #################################################
        ### least-squared method
        #################################################
        # coeffprior = np.asarray(lstsq(w, b)[0])
        # coeffprior_point = np.asarray(lstsq(w, b)[0])
        # component_temperature_point = inv_planck(wl, coeffprior_point)
        # result_point[:, kk] = [component_temperature_point[0], component_temperature_point[1]]

        #################################################
        ### Bayes method
        #################################################

        w = np.matrix(w)
        b = np.matrix(b)
        b = np.transpose(b)

        Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
        Cm = np.diag([soil_radiance_variance, leaf_radiance_variance])
        pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
        coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * b + np.linalg.inv(Cm) * ctprior)
        ### another solution for using priori information
        # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
        component_radiance = np.asarray(coeff)

        if (np.min(component_radiance) < radiance_min_threshold): continue
        if (np.max(component_radiance) > radiance_max_threshold): continue

        component_temperature = inv_planck(wl, component_radiance)

        result[:, kk] = [component_temperature[0][0], component_temperature[1][0]]

    return result

def doMultiple_line_inv_2_s(param):
    return line_inv_2_s((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]))

def inv_mpl_agl_multiple_2(lst_n, lst_o,emis_s, emis_v, fvcN, fvcO, wl=10.8):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    # sensor_noise = 0.05
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
    number_component = 2
    number_angle = 2
    number_value_threshold = 12
    off = 2
    off_ = 0

    start = time.time()
    [nl, ns] = np.shape(lst_n)
    result = np.zeros([2,nl,ns])

    ###### fvc LAI 根据LAI计算得到的fvc，为此函数的输入项
    fvc_n = fvcN * 1.0
    fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold

    fvc_o = fvcO * 1.0
    fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold

    ###### the radiance 根据fvc和植被土壤的发射率计算像元的有效发射率，加上反演得到的地表温度计算像元的能量
    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

    ###### component effective emissivity matrix 组分有效发射率，分别对应光土壤，植被
    wN = np.asarray([emis_s * (1 - fvc_n) , emis_v * (fvc_n)])
    wO = np.asarray([emis_s * (1 - fvc_o) , emis_v * (fvc_o)])

    mask = np.zeros([nl,ns])
    ind0 = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
           (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
           (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind0] = 1

    para = []
    # for kn in range(off, nl-off):
    #     ###### 取wN的所有组分的5行，列全部，进行多线程的操作, 5行为多像元反演组分温度时候所用到的
    #     wNLine = wN[:,kn-off: kn + off + 1, :]
    #     wOLine = wO[:, kn - off: kn + off + 1, :]
    #     radNLine = rad_n[kn-off:kn+off+1, : ]
    #     radOLine = rad_o[kn-off:kn+off+1, : ]
    #     maskLine = mask[kn-off: kn + off+1, : ]
    #     para.append([wNLine, wOLine, radNLine, radOLine, maskLine, ns])

    for kn in range(off, ns-off):
        ###### 取wN的所有组分的5行，列全部，进行多线程的操作, 5行为多像元反演组分温度时候所用到的
        wNLine = wN[:,:,kn-off: kn + off + 1]
        wOLine = wO[:,:, kn - off: kn + off + 1]
        radNLine = rad_n[:,kn-off:kn+off+1 ]
        radOLine = rad_o[:,kn-off:kn+off+1]
        maskLine = mask[:,kn-off: kn + off+1 ]
        para.append([wNLine, wOLine, radNLine, radOLine, maskLine, nl])

    tasks= []
    pool = Pool(min(64,int(cpu_count())))
    print('cpu_count',cpu_count())
    for p in para:
        tasks.append(pool.apply_async(doMultiple_line_inv_2_s, (p,)))
    pool.close()
    pool.join()
    results = [task.get() for task in tasks]
    end = time.time()
    results = np.asarray(results)
    resultForm = np.asarray([results[:,0,:], results[:,1,:]])
    resultForm = np.transpose(resultForm)
    print('time cost: ', end - start, 's')
    return resultForm

def inv_agl_multiple_2(lst_n, lst_o,emis_s, emis_v, fvcN, fvcO, wl=10.8):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    off = 2
    off_ = 0

    start = time.time()
    [nl, ns] = np.shape(lst_n)
    result = np.zeros([2,nl,ns])

    ###### fvc LAI 根据LAI计算得到的fvc，为此函数的输入项
    fvc_n = fvcN * 1.0
    fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold

    fvc_o = fvcO * 1.0
    fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold

    ###### the radiance 根据fvc和植被土壤的发射率计算像元的有效发射率，加上反演得到的地表温度计算像元的能量
    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

    ###### component effective emissivity matrix 组分有效发射率，分别对应光土壤，植被
    wN = np.asarray([emis_s * (1 - fvc_n) , emis_v * (fvc_n)])
    wO = np.asarray([emis_s * (1 - fvc_o) , emis_v * (fvc_o)])

    mask = np.zeros([nl,ns])
    ind0 = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
           (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
           (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind0] = 1

    for kn in range(off, ns-off):
        ###### 取wN的所有组分的5行，列全部，进行多线程的操作, 5行为多像元反演组分温度时候所用到的
        wNLine = wN[:,:,kn-off: kn + off + 1]
        wOLine = wO[:,:, kn - off: kn + off + 1]
        radNLine = rad_n[:,kn-off:kn+off+1 ]
        radOLine = rad_o[:,kn-off:kn+off+1]
        maskLine = mask[:,kn-off: kn + off+1 ]
        lsct_line = line_inv_2_s(wNLine, wOLine, radNLine, radOLine, maskLine,nl)
        result[:,:,kn] = lsct_line
    end = time.time()
    print('time cost: ', end - start, 's')
    return result


if __name__ == '__main__':
    raw_dir = r"D:\data\AATSR_product\Fluxnet2015\AATSR_h5\\"
    out_dir = r"D:\data\AATSR_product\Fluxnet2015\2.Veg_filter\AATSR_h5\\"
    site_names = search_dir(raw_dir,'')
    infile_site_info_xls = r"D:\data\AATSR_product\Fluxnet2015\\FLUXSITE.xlsx"
    sites_info = pd.read_excel(infile_site_info_xls)
    filtered_site_names = r"D:\data\AATSR_product\Fluxnet2015\2.Veg_filter\filtered_site.txt"
    data = read_txt_str(filtered_site_names,'\n')
    filtered_list = []
    for i in range(len(data)): filtered_list.append(data[i][0])
    for site_name in site_names:
        print(site_name)
        if (site_name not in filtered_list): continue
        site_dir = os.path.join(raw_dir, site_name)
        site_out_dir = os.path.join(out_dir, site_name)
        mkdir_if_not_exist(site_out_dir)

        # 读取IGBP 分类
        # 1.常绿针叶 ENF 2.常绿阔叶 EBF 3.落叶针叶 DNF 4.落叶阔叶 DBF 5.混交林 MF 6.封闭灌木 CSH
        # 7.开阔灌木 OSH 8.木质稀疏草原 WSA 9. 稀疏草原 SAV 10.草原 GRA 11.永久湿地 WET
        # 12.农田 CRO 13.城市和建筑 URB 14.农田、自然植被 CVM 15.永久冰雪 SNO
        # 16.裸地 BSV 17.水体 WAT
        site_info= sites_info[sites_info["SITE_ID"] == site_name]
        IGBP = site_info['IGBP'].iloc[0]
        lon = site_info['LOCATION_LONG'].iloc[0]
        lat = site_info['LOCATION_LAT'].iloc[0]
        timezone = get_timezone(lat, lon)


        if IGBP in ['WET', 'WAT', 'SNO', 'URB', 'BSV']:
            print("IGBP type:", IGBP, ", continue!")
            continue
        if IGBP in ['ENF', 'EBF','DNF','DBF','MF','WSA','SAV']:
            mode = 'Tall Crown'
            rcr,hcr,sLAI = 1,2,5
        if IGBP in ['CSH','OSH','CRO','CVM']:
            mode = 'Short Crown'
            rcr,hcr,sLAI = 1,0.2,5
        if IGBP in ['GRA']:
            mode = 'Hom'

        fileNames = search_file(site_dir,['h5'])
        for fileName in fileNames:
            print(fileName)
            infile = os.path.join(site_dir, fileName)
            outfile = os.path.join(site_out_dir, fileName)

            '''读取数据'''
            items = ['lstN','lstO','lai','vzaN','vzaO','indx','indy','ref_indx','ref_indy','ref_tmie','sec','type','emis_s',"emis_v"]
            lstN_,lstO_,lai_,vzaN_,vzaO_,indx_,indy_,ref_indx_,ref_indy_,ref_time_,sec_,type_,emis_s_,emis_v_ = read_h5py_items(infile,items)
            ref_time_str = fileName[6:-10]
            utc_time = datetime.strptime(ref_time_str, '%Y_%j') + timedelta(seconds=int(sec_))
            local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone)
            print(local_time)
            if local_time.hour < 6 or local_time.hour >= 18:
                print("Pass Night!")
                continue

            ifcenter = 0
            if ifcenter == 1:
                id = (indx_ == ref_indx_) * (indy_ == ref_indy_)
                if sum(id) == 0:
                    print("No Data!")
                    continue
                '''提取中心像元'''
                neighborhood_indices = np.where(id)  # 找到符合条件的像元索引
                center_index = (neighborhood_indices[0][0], neighborhood_indices[1][0])  # 中心像元索引

                row_min = max(0, center_index[0] - 2)
                row_max = min(indx_.shape[0] - 1, center_index[0] + 2)
                col_min = max(0, center_index[1] - 2)
                col_max = min(indx_.shape[1] - 1, center_index[1] + 2)

                lstN = lstN_[row_min:row_max + 1, col_min:col_max + 1]
                lstO = lstO_[row_min:row_max + 1, col_min:col_max + 1]
                lai = lai_[row_min:row_max + 1, col_min:col_max + 1]
                vzaN = vzaN_[row_min:row_max + 1, col_min:col_max + 1]
                vzaO = vzaO_[row_min:row_max + 1, col_min:col_max + 1]
                type = type_[row_min:row_max + 1, col_min:col_max + 1]
                emis_s = emis_s_[row_min:row_max + 1, col_min:col_max + 1]
                emis_v = emis_v_[row_min:row_max + 1, col_min:col_max + 1]
            else:
                lstN = lstN_
                lstO = lstO_
                lai = lai_
                vzaN = vzaN_
                vzaO = vzaO_
                type = type_
                emis_s = emis_s_
                emis_v = emis_v_

            lstN = lstN / 100
            lstO = lstO / 100
            vzaN = 90 - (vzaN / 100)
            vzaO = 90 - (vzaO / 100)

            if mode == 'Hom':
                fvcN = cal_fvc_from_lai(vzaN, lai)
                fvcO = cal_fvc_from_lai(vzaO, lai)

            elif mode == 'Tall Crown' or mode == 'Short Crown':
                std = (lai/(np.pi*rcr*rcr*sLAI))
                Psoil,fvcN = proprotion_directional_crown_one(lai,std,hcr,rcr,vzaN, G = 0.5)
                Psoil, fvcO = proprotion_directional_crown_one(lai, std, hcr, rcr, vzaO, G=0.5)

            fvcN[fvcN > 1] = 1
            fvcN[fvcN < 0] = 0
            fvcO[fvcO > 1] = 1
            fvcO[fvcO < 0] = 0

            nl,ns = shape(lstN)
            Ts = np.zeros([nl,ns])
            Tv = np.zeros([nl,ns])
            # lsct = inv_mpl_agl_multiple_2(lstN, lstO, emis_s, emis_v, fvcN, fvcO, wl=10.8)
            # Ts[:,2:-2] = lsct[:,:,0]
            # Tv[:,2:-2] = lsct[:,:,1]
            lsct = inv_agl_multiple_2(lstN, lstO, emis_s, emis_v, fvcN, fvcO, wl=10.8)
            Ts = lsct[0,:,:]
            Tv = lsct[1,:,:]

            name_list = ['lstN','lstO','lai','vzaN','vzaO','indx','indy','ref_indx','ref_indy','ref_tmie','sec','type','emis_s',"emis_v",'Ts','Tv']

            data = [lstN_,lstO_,lai_,vzaN_,vzaO_,indx_,indy_,ref_indx_,ref_indy_,ref_time_,sec_,type_,emis_s_,emis_v_,Ts,Tv]

            write_h5py_file(outfile, name_list, data_list=data,
                            dtype_list=['f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f'],
                            compression=None, ifcover=1)