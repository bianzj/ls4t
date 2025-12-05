import sys
import os
from tkinter import W
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from cases.AATSR_product.util.util_aatsr import *
import time
import warnings
warnings.filterwarnings("ignore")

'''2025.12.4'''
'''补充异温方法和对比'''
'''2025.11.18'''
'''贝叶斯反演'''
'''2025.10.21'''
'''站点切片组分温度反演 python311'''
'''反演两组分/三组分+lai/NDVI结果，并验证'''

def inv_lsct2_window(n, m, ws, wl, w, b, mask, lst,ifday = 1):
    off = ws//2 # 窗口偏移量
    weights = set_weights(ws) # 窗口权重
    nl,ns = w.shape[0], w.shape[1]
    result = np.zeros([nl,ns,m])
    for i in range(off,nl-off):
        for j in range(off,ns-off):
            if np.sum(mask[i-off:i+off+1,j-off:j+off+1,:]) >= 10 and np.sum(mask[i,j,:])>= n:
                w_win = w[i-off:i+off+1,j-off:j+off+1,:,:]
                b_win = b[i-off:i+off+1,j-off:j+off+1,:]
                mask_win = mask[i-off:i+off+1,j-off:j+off+1,:]
                lst_win = lst[i-off:i+off+1,j-off:j+off+1,:]

                # 两组分温差约束
                if ifday:
                    d = [-5,30]
                    constraints = {
                        'type': 'ineq',  # 不等式约束
                        'fun': constraint_func_Nangle_2component,
                        'args': (lst_win, d,ws, wl)  # 注意是元组
                    }
                    x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst_win,n,m,ws)
                else:
                    constraints = None
                    x0,bounds = set_x0_bnds_Nangle_Mcomponent_night(lst_win,n,m,ws)
                p = fitting_Nangle_Mcomponent_window(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method='SLSQP')
                result[i,j,:] = p
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    return lsct


def inv_lsct3_window(n, m, ws, wl, w, b, mask, lst):
    off = ws//2 # 窗口偏移量
    weights = set_weights(ws) # 窗口权重
    nl,ns = w.shape[0], w.shape[1]
    result = np.zeros([nl,ns,m])
    for i in range(off,nl-off):
        for j in range(off,ns-off):
            if np.sum(mask[i-off:i+off+1,j-off:j+off+1,:]) >= 10 and np.sum(mask[i,j,:])>= n:
                w_win = w[i-off:i+off+1,j-off:j+off+1,:,:]
                b_win = b[i-off:i+off+1,j-off:j+off+1,:]
                mask_win = mask[i-off:i+off+1,j-off:j+off+1,:]
                lst_win = lst[i-off:i+off+1,j-off:j+off+1,:]

                # 三组分温差约束
                d12 = [5,40] # 光照土壤 阴影土壤温差限制 
                d23 = [-15,15] # 阴影土壤 植被温差限制
                constraints = {
                    'type': 'ineq',  # 不等式约束
                    'fun': constraint_func_Nangle_3component,
                    'args': (lst_win, d12, d23,ws, wl)  # 注意是元组
                }

                x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst_win,n,m,ws)

                p = fitting_Nangle_Mcomponent_window(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method='SLSQP')
                result[i,j,:] = p
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    return lsct


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

        coeffprior = np.asarray(lstsq(ww, bb, rcond=None)[0])

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
        # result[:, kk] = [component_temperature_point[0], component_temperature_point[1]]

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

        coeffprior = np.asarray(lstsq(ww, bb, rcond=None)[0])

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
        # result[:, kk] = [component_temperature_point[0], component_temperature_point[1]]

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
    pool = Pool(min(32,int(cpu_count())))
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

if __name__ == '__main__':
    ###  反演参数设置
    n, m, ws = 2, 3, 5 # n 角度， m组分， ws窗口大小
    ndvi_max, ndvi_min, k = 0.87, 0.15, 1 # ndvi 参数
    lst_min, lst_max = 250, 350 # 范围参数
    hspot, wl = 0.2, 10.8 # 结构参数
    # 反演方法
    method_effective_emissivity = 'lai' # lai / ndvi
    method_mpl_pixel = 'winquad' # point / winconst / winquad
    method_solve = 'none' # bayesian / nobayesian / none
    # 反演站点设置
    if_Dahra = 1 # 只反演Dahra站点
    if_PureSites = 0 # 只反演纯站点
    if_daynight = 'all' # day/night/all

    label = 'inv_%01dc_' % m + method_effective_emissivity + '_' + method_mpl_pixel + '_' + method_solve

    # 输入输出位置
    indir_h5_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/0_raw_h5/'
    infile_pure_soil_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/soil_sites.txt'
    infile_pure_veg_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/veg_sites.txt'
    outdir_h5_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/' + label + '/'
    mkdir_if_not_exist(outdir_h5_sites)
    angle_error_file = indir_h5_sites + r'Angle_error.txt'

    siteNames = search_dir(indir_h5_sites,'')
    for i, siteName in enumerate(siteNames):
        if if_Dahra == 1:
            if siteName != 'SN-Dhr': continue
        if if_PureSites == 1:
            soil_sites_list = np.array(read_txt_str(infile_pure_soil_sites,'\n'))[:,0]
            veg_sites_list = np.array(read_txt_str(infile_pure_veg_sites,'\n'))[:,0]
            soil_sites_list = soil_sites_list.tolist()
            soil_sites_list.append('SN-Dhr')
            if siteName not in soil_sites_list and siteName not in veg_sites_list: continue
        print(i,siteName)
        indir_site = indir_h5_sites + siteName + '/'
        outdir_site = outdir_h5_sites + siteName + '/'
        mkdir_if_not_exist(outdir_site)
        fileNames = search_file(indir_site, ['h5'])
        fileNames.sort()
        wl = 10.8
        for i, fileName in enumerate(fileNames):
            year = int(fileName.split('_')[1])
            doy = int(fileName.split('_')[2])
            month,day = doy2date(year,doy)
            if year != 2009: continue
            if doy < 120: continue
            # if fileName != 'AATSR_2009_260_210219.h5': continue

            ### 0. 读取数据
            print(i,fileName)
            start_time = time.time()
            infile = indir_site + fileName
            outfile = outdir_site + fileName
            if os.path.exists(outfile):
                os.remove(outfile)

            ndviN, ndviF = aatsr_read_sites_obs(infile, ifNDVI=1)
            cloN_mask, cloF_mask = aatsr_read_sites_clo(infile)
            lstN,lstF = aatsr_read_sites_lst(infile)
            vzaN,vzaF,vaaN,vaaF,sza,saa = aatsr_read_sites_angle(infile)
            emisS,emisV,type,lai = aatsr_read_sites_emis(infile)
            indx,indy,ref_indx,ref_indy,lat,lon = aatsr_read_sites_loc(infile)
            utc_time = aatsr_read_sites_time(infile)

            # 筛选控制 
            if np.average(sza) > 89: dn = 'night'
            else: dn = 'day'
            if if_daynight != 'all' and if_daynight != dn: 
                print('Pass day/night')
                continue

            if np.average(vzaF) > 60 or np.average(vzaF) < 50:  # 极少部分数据vzaF值异常
                print('Angle error')
                with open(angle_error_file,'a') as f:
                    f.write(siteName + ' ' + fileName + '\n')
                continue
            if np.mean(lstN) == 0: continue

            nl,ns = lstN.shape
            if nl != 31 or ns != 31: continue

            ### 1.计算有效发射率矩阵 w
            off = ws//2
            if method_effective_emissivity == 'lai':
                vza = np.stack((vzaN, vzaF), axis=2)
                vaa = np.stack((vaaN, vaaF), axis=2)
                
                w = cal_effective_emissivity_hom(lai,hspot, wl, emisS,emisV,vza,sza,vaa,saa,n,m)
                w2 = cal_effective_emissivity_hom(lai,hspot, wl, emisS,emisV,vza,sza,vaa,saa,n,2) # FVC,后面可能有用

                if m == 3:
                    psoil = cal_psoil_hom(lai,sza)
                cloN_mask = cloN_mask * (lai>0.01)

            elif method_effective_emissivity == 'ndvi':
                fvcN = cal_fvc_from_ndvi(ndviN,ndvi_min,ndvi_max)  # nl*ns
                fvcF = cal_fvc_from_ndvi(ndviF,ndvi_min,ndvi_max)  # nl*ns
                fvcN[cloN_mask == 0] = 0
                fvcF[cloF_mask == 0] = 0
                wN = np.stack([emisS * (1-fvcN), emisV * fvcN], axis=-1)  # 形状: (nl, ns, m)
                wF = np.stack([emisS * (1-fvcF), emisV * fvcF], axis=-1)  # 形状: (nl, ns, m)
                w = np.stack([wN, wF], axis=2) # 形状: (nl, ns, m, 2)
            
            ### 2.计算观测亮度矩阵 b
            lst = np.stack((lstN,lstF),axis=2)
            if method_effective_emissivity == 'lai': # lai反演0
                bN = cal_rad_from_lst(lstN,wl,lai,vzaN,emisS,emisV)
                bF = cal_rad_from_lst(lstF,wl,lai,vzaF,emisS,emisV)
                b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2) # 形状: (nl, ns, m)
            elif method_effective_emissivity == 'ndvi':
                bN = cal_rad_from_lst_fvc(lstN,wl,fvcN,emisS,emisV)
                bF = cal_rad_from_lst_fvc(lstF,wl,fvcF,emisS,emisV)
                b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2)

            ### 3. 求解
            mask = np.concatenate([cloN_mask[:,:,np.newaxis], cloF_mask[:,:,np.newaxis]], axis=2)
            if method_mpl_pixel == 'point':
                lsct = inv_lsct_point(w,b,mask,n,m,wl,method='ls')

            elif method_mpl_pixel == 'winconst':
                if m == 2:
                    lsct = inv_lsct2_winconst(w, b, mask, lst,n, m=2, ws=5, wl=10.8,method = 'SLSQP')
                elif m == 3:
                    lsct = inv_lsct3_winconst(w, b, mask, lst, psoil, n, m=3, ws=5, wl=10.8,method = 'SLSQP')
            
            elif method_mpl_pixel == 'winquad':
                if m == 2:
                    if method_solve == 'bayesian': if_bayesian = 1
                    else: if_bayesian = 0
                    lsct = inv_lsct2_winquad(w, b, mask,n, m=2, ws=5,wl=10.8,if_bayesian = if_bayesian)
                elif m == 3:
                    if method_solve == 'bayesian': if_bayesian = 1
                    else: if_bayesian = 0
                    lsct = inv_lsct3_winquad(w2, w, b, mask,psoil,n, m=2, ws=5,wl=10.8,if_bayesian = if_bayesian)

            
            ### -1. 保存结果
            name_list = ['lstN','lstF','lai','indx','indy','ref_indx','ref_indy','cloN_mask','cloF_mask']
            data_list = [lstN,lstF,lai,indx,indy,ref_indx,ref_indy,cloN_mask,cloF_mask]
            dtype_list = np.full_like(name_list,'f')
            write_h5py_file(outfile,name_list,data_list,dtype_list,compression=None,ifcover = 1)
            write_h5py_item(outfile,'utc_time',utc_time.isoformat(),dtype=h5py.string_dtype())

            if m == 2:
                write_h5py_item(outfile,'Ts',lsct[:,:,0],'f',if_overwrite=1)
                write_h5py_item(outfile,'Tv',lsct[:,:,1],'f',if_overwrite=1)
            if m == 3:
                write_h5py_item(outfile,'Tsl',lsct[:,:,0],'f',if_overwrite=1)
                write_h5py_item(outfile,'Tsh',lsct[:,:,1],'f',if_overwrite=1)
                write_h5py_item(outfile,'Ts',lsct[:,:,2],'f',if_overwrite=1)
                write_h5py_item(outfile,'Tv',lsct[:,:,3],'f',if_overwrite=1)
            
            end_time = time.time()
            print(f"总执行时间: {end_time - start_time:.4f}秒\n")