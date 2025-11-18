from opt_lsct.multiple_lsct import *
from utils.old.util_lsct import *
import warnings
warnings.filterwarnings("ignore")
from utils.old.util_constant import *
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime, timedelta
import pysolar.solar as Sun

'''2024.4.18'''
'''Fluxnet站点三组分组分温度'''

def sample_crown_Emis(lai, hspot,stand,rcr,hcr,wavelength, emissivity_soil, emissivity_leaf,vza, sza, raa):
    '''1.initial'''
    crown = Crown()
    '''2.set variables'''
    crown.set_structure(lai, hspot, stand, hcr, rcr)
    crown.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    crown.set_angle(vza, sza, raa)
    ''''3.run'''
    emis = crown.run_emis()
    vza[raa == 180] = vza[raa == 180] * -1
    return emis

def sample_hom_Emis(lai, hspot,wavelength, emissivity_soil, emissivity_leaf,vza, sza, raa):
    '''1.initial'''
    hom = Hom()
    '''2.set variables'''
    hom.set_structure(lai, hspot)
    hom.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    hom.set_angle(vza, sza, raa)
    ''''3.run'''
    emis = hom.run_emis()
    vza[raa == 180] = vza[raa == 180] * -1
    return emis

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


def fitting_linear_constrain_3component(w,b):
    def constraint_func(x, lstN, deta12_min, deta12_max, deta23_min, deta23_max):
        # 计算每个约束条件的值
        constraint1 = -deta12_min + (x[0] - x[1])
        constraint2 = deta12_max - (x[0] - x[1])
        constraint3 = -deta23_min + (x[1] - x[2])
        constraint4 = deta23_max - (x[1] - x[2])
        return [constraint1, constraint2, constraint3, constraint4]

    def objective_func(x, w, b):
        return np.linalg.norm(np.dot(w, x) - b)
    delta_Ts_range = np.array([[1,5],[3,10],[5,20],[10,30],[15,40]])
    delta_Tsv_range = np.array([[-2, 2], [-4, 4], [-6, 6], [-8, 8], [-10, 10]])
    lstN = inv_planck(10.8,np.max(b))

    if lstN<= 275: deta12,deta23 = delta_Ts_range[0],delta_Tsv_range[0]
    elif lstN > 275 and lstN <= 290: deta12,deta23 = delta_Ts_range[1],delta_Tsv_range[1]
    elif lstN > 290 and lstN <= 305: deta12, deta23 = delta_Ts_range[2], delta_Tsv_range[2]
    elif lstN > 305 and lstN <= 320: deta12, deta23 = delta_Ts_range[3], delta_Tsv_range[3]
    elif lstN > 320: deta12, deta23 = delta_Ts_range[4], delta_Tsv_range[4]

    deta12_min = planck(10.8,lstN +  deta12[0]/2) -planck(10.8,lstN - deta12[0]/2)
    deta12_max = planck(10.8,lstN + deta12[1]/2) - planck(10.8,lstN- deta12[1]/2)
    deta23_min = planck(10.8,lstN + deta23[0]/2) - planck(10.8,lstN- deta23[0]/2)
    deta23_max = planck(10.8,lstN + deta23[1]/2) - planck(10.8,lstN- deta23[1]/2)

    # 定义约束条件
    constraints = {'type': 'ineq', 'fun': constraint_func,
                   'args': (lstN, deta12_min, deta12_max, deta23_min, deta23_max)}

    x0 = np.array([lstN+5, lstN-10, lstN+5])
    x0 = planck(10.8,x0)
    # SLSQP  trust-constr
    result = minimize(objective_func, x0, args=(w, b),constraints=constraints,method ='SLSQP')
    return result.x

def line_inv_3_s(wNLine, wOLine, radNLine, radOLine, maskLine,nl = 1024):
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
    number_component = 3
    number_angle = 2
    number_value_threshold = 3

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

        ww = np.hstack((w1[:, ind], w2[:, ind]))
        bb = np.hstack((bb1[ind], bb2[ind]))

        ###############################################
        ### least-square method
        ###############################################
        ww = np.transpose(ww)

        # coeffprior = np.asarray(lstsq(ww, bb)[0])
        coeffprior = fitting_linear_constrain_3component(ww,bb)
        component_temperature = inv_planck(wl, coeffprior)

        result[:, kk] = [component_temperature[0], component_temperature[1], component_temperature[2]]

    return result

def inv_agl_multiple_3(lst_n, lst_o,wN, wO, wl=10.8):
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
    result = np.zeros([3, nl, ns])

    ###### the radiance 根据fvc和植被土壤的发射率计算像元的有效发射率，加上反演得到的地表温度计算像元的能量
    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (np.sum(wN,axis=0))
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (np.sum(wO,axis=0))

    mask = np.zeros([nl, ns])
    ind0 = (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
           (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind0] = 1

    for kn in range(off, ns - off):
        ###### 取wN的所有组分的5行，列全部，进行多线程的操作, 5行为多像元反演组分温度时候所用到的
        wNLine = wN[:, :, kn - off: kn + off + 1]
        wOLine = wO[:, :, kn - off: kn + off + 1]
        radNLine = rad_n[:, kn - off:kn + off + 1]
        radOLine = rad_o[:, kn - off:kn + off + 1]
        maskLine = mask[:, kn - off: kn + off + 1]
        lsct_line = line_inv_3_s(wNLine, wOLine, radNLine, radOLine, maskLine, nl)
        result[:, :, kn] = lsct_line
    end = time.time()
    print('time cost: ', end - start, 's')
    return result



if __name__ == '__main__':
    raw_dir = r"D:\data\AATSR_product\Dahra_2009\SN-Dhr\\"
    out_dir = r"D:\data\AATSR_product\Dahra_2009\SN-Dhr_lsct3\\"
    site_names = search_dir(raw_dir,'')
    infile_site_info_xls = r"D:\data\AATSR_product\Fluxnet2015\\FLUXSITE.xlsx"
    sites_info = pd.read_excel(infile_site_info_xls)

    # data = read_txt_str(filtered_site_names,'\n')
    # filtered_list = []
    # for i in range(len(data)): filtered_list.append(data[i][0])

    for site_name in site_names:
        print("--------------------------------------------------------------------------------")
        print(site_name)
        # if (site_name not in filtered_list): continue
        site_dir = os.path.join(raw_dir, site_name)
        site_out_dir = os.path.join(out_dir, site_name)
        mkdir_if_not_exist(site_out_dir)

        # 读取IGBP 分类
        # 1.常绿针叶 ENF 2.常绿阔叶 EBF 3.落叶针叶 DNF 4.落叶阔叶 DBF 5.混交林 MF 6.封闭灌木 CSH
        # 7.开阔灌木 OSH 8.木质稀疏草原 WSA 9. 稀疏草原 SAV 10.草原 GRA 11.永久湿地 WET
        # 12.农田 CRO 13.城市和建筑 URB 14.农田、自然植被 CVM 15.永久冰雪 SNO
        # 16.裸地 BSV 17.水体 WAT
        site_info= sites_info[sites_info["SITE_ID"] == site_name]
        IGBP = 'SAV'
        lon = site_info['LOCATION_LONG'].iloc[0]
        lat = site_info['LOCATION_LAT'].iloc[0]
        timezone = get_timezone(lat, lon)


        if IGBP in ['WET', 'WAT', 'SNO', 'URB', 'BSV']:
            print("IGBP type:", IGBP, ", continue!")
            continue
        if IGBP in ['ENF', 'EBF','DNF','DBF','MF','WSA','SAV']:
            mode = 'Tall Crown'
            rcr,hcr,sLAI = 5,2.5,5
        if IGBP in ['CSH','OSH','CRO','CVM']:
            mode = 'Short Crown'
            rcr,hcr,sLAI = 1,0.2,5
        if IGBP in ['GRA']:
            mode = 'Hom'

        fileNames = search_file(site_dir,['h5'])
        for fileName in fileNames:
            print("----------------------------------")
            print(fileName)
            infile = os.path.join(site_dir, fileName)
            outfile = os.path.join(site_out_dir, fileName)

            '''读取数据'''
            items = ['lon','lat','lstN','lstO','lai','vzaN','vzaO','vaaN','vaaO','sza','saa','indx','indy','ref_indx','ref_indy','ref_time','sec','type','emis_s',"emis_v",'clo']
            lon_,lat_,lstN_,lstO_,lai_,vzaN_,vzaO_,vaaN_,vaaO_,sza_,saa_,indx_,indy_,ref_indx_,ref_indy_,ref_time_,sec_,type_,emis_s_,emis_v_,clo_ = read_h5py_items(infile,items)
            ref_time_str = fileName[6:-10]
            utc_time = datetime.strptime(ref_time_str, '%Y_%j') + timedelta(seconds=int(sec_))
            local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone)
            print(local_time)
            if local_time.hour < 6 or local_time.hour >= 18:
                print("Pass Night!")
                continue

            id = (indx_ == ref_indx_) * (indy_ == ref_indy_)
            if sum(id) == 0:
                print("No Data!")
                continue
            neighborhood_indices = np.where(id)  # 找到符合条件的像元索引
            center_index = (neighborhood_indices[0][0], neighborhood_indices[1][0])

            if clo_ != []:
                if clo_[center_index[0],center_index[1]] > 100:
                    print("Pass Cloud!")
                    print("Cloud:%d" % clo_[center_index[0],center_index[1]])
                    continue

            ifcenter = 0
            if ifcenter == 1:
                '''提取中心像元'''
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
                lstN,lstO = lstN_,lstO_
                lai = lai_
                vzaN,vzaO,vaaN,vaaO,sza,saa = vzaN_,vzaO_,vaaN_,vaaO_,sza_,saa_
                type = type_
                emis_s = emis_s_
                emis_v = emis_v_

            '''格式转化'''
            lstN = lstN / 100
            lstO = lstO / 100
            vzaN = 90 - (vzaN / 100)
            vzaO = 90 - (vzaO / 100)

            nl,ns = np.shape(lstN)
            if sza != []:
                sza = (sza / 100)
            else:
                sza_ = 90 - Sun.get_altitude(lat, lon, local_time)
                saa_ = Sun.get_azimuth(lat, lon, local_time) *100
                sza = np.full([nl,ns],sza_)
                saa = np.full([nl,ns],saa_)

            def Azimuth_angle_transform(xaa):
                xaa = xaa / 100
                xaa[xaa<0] = xaa[xaa<0] + 360
                return xaa

            vaaN = Azimuth_angle_transform(vaaN)
            vaaO = Azimuth_angle_transform(vaaO)
            saa = Azimuth_angle_transform(saa)
            raaN = np.abs(vaaN-saa)
            raaO = np.abs(vaaO-saa)

            '''有效发发射率'''
            hspot = 0.2
            wavelength = 10.8
            emisN = np.zeros([4, shape(lai)[0], shape(lai)[1]])
            emisO = np.zeros([4, shape(lai)[0], shape(lai)[1]])
            Psoil = np.zeros([shape(lai)[0], shape(lai)[1]])
            if mode == 'Hom':
                for i in range(shape(lai)[0]):
                    for j in range(shape(lai)[1]):
                        emisN[:, i, j] = np.reshape(
                            sample_hom_Emis(lai[i, j], hspot, wavelength, emis_s[i, j], emis_v[i, j], [vzaN[i, j]],
                                            [sza[i, j]], [raaN[i, j]]), -1)
                        emisO[:, i, j] = np.reshape(
                            sample_hom_Emis(lai[i, j], hspot, wavelength, emis_s[i, j], emis_v[i, j], [vzaO[i, j]],
                                            [sza[i, j]], [raaO[i, j]]), -1)
                        Psoil[i,j] = gap_probability_hom_analytical(lai[i, j], [sza[i, j]], G=0.5)


            elif mode == 'Tall Crown' or mode == 'Short Crown':
                std = (lai/(np.pi*rcr*rcr*sLAI))
                for i in range(shape(lai)[0]):
                    for j in range(shape(lai)[1]):
                        emisN[:, i, j] = np.reshape(
                            sample_crown_Emis(lai[i, j], hspot,std[i,j],rcr,hcr, wavelength, emis_s[i, j], emis_v[i, j], [vzaN[i, j]],
                                            [sza[i, j]], [raaN[i, j]]), -1)
                        emisO[:, i, j] = np.reshape(
                            sample_crown_Emis(lai[i, j], hspot,std[i,j],rcr,hcr, wavelength, emis_s[i, j], emis_v[i, j], [vzaO[i, j]],
                                            [sza[i, j]], [raaO[i, j]]), -1)
                        Psoil[i,j] = gap_probability_crown_analytical(lai[i, j], std[i,j], hcr, rcr, [sza[i, j]], G=0.5)

            nl,ns = shape(lstN)
            Tsl = np.zeros([nl,ns])
            Tsh = np.zeros([nl,ns])
            Ts = np.zeros([nl,ns])
            Tv = np.zeros([nl,ns])
            wN = np.zeros([3,nl,ns])
            wO = np.zeros([3,nl,ns])
            wN[:2,:,:], wO[:2,:,:] = emisN[:2,:,:],emisO[:2,:,:]
            wN[2,:,:],wO[2,:,:] = emisN[2,:,:] + emisN[3,:,:] ,emisO[2,:,:] + emisO[3,:,:]


            # lsct = inv_mpl_agl_multiple_2(lstN, lstO, emis_s, emis_v, fvcN, fvcO, wl=10.8)
            # Ts[:,2:-2] = lsct[:,:,0]
            # Tv[:,2:-2] = lsct[:,:,1]
            # lsct = inv_agl_multiple_2(lstN, lstO, emis_s, emis_v, fvcN, fvcO, wl=10.8)
            # Ts = lsct[0,:,:]
            # Tv = lsct[1,:,:]
            lsct = inv_agl_multiple_3(lstN, lstO,  wN, wO, wl=10.8)
            Tsl = lsct[0,:,:]
            Tsh = lsct[1,:,:]
            Tv = lsct[2,:,:]
            Ts = inv_planck(10.8, Psoil * planck(10.8, Tsl) + (1 - Psoil) * planck(10.8, Tsh))


            name_list = ['lstN','lstO','lai','vzaN','vzaO','indx','indy','ref_indx','ref_indy','ref_tmie','sec','type','emis_s',"emis_v",'Ts','Tv','Tsl','Tsh','clo']

            data = [lstN_,lstO_,lai_,vzaN_,vzaO_,indx_,indy_,ref_indx_,ref_indy_,ref_time_,sec_,type_,emis_s_,emis_v_,Ts,Tv,Tsl,Tsh,clo_]

            write_h5py_file(outfile, name_list, data_list=data,
                            dtype_list=['f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f','f','f','f'],
                            compression=None, ifcover=1)