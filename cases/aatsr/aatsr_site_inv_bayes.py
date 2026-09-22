from base.lsct_window import fitting_Nangle_Mcomponent_window
import os
import sys
import time
from multiprocessing import Pool
from multiprocessing import cpu_count
from scipy.linalg import lstsq
import h5py
import numpy as np
from numpy import exp, min
from cases.aatsr.util_aatsr import aatsr_read_crown_data, aatsr_read_sites_angle, aatsr_read_sites_clo, aatsr_read_sites_emis, aatsr_read_sites_loc, aatsr_read_sites_lst, aatsr_read_sites_obs, aatsr_read_sites_time
from base.dates import doy2date
from base.files import mkdir_if_not_exist, read_txt_str, search_dir, search_file, write_h5py_file, write_h5py_item
from base.lsct import constraint_func_Nangle_2component, constraint_func_Nangle_3component, set_weights, set_x0_bnds_Nangle_Mcomponent, set_x0_bnds_Nangle_Mcomponent_night
from base.radiometry import inv_planck, planck

'''2025.10.21'''
'''站点切片组分温度反演 python311'''
'''反演两组分/三组分+lai/NDVI结果，并验证'''
'''2025.11.18'''
'''贝叶斯反演'''

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


# def optimize_LAI(lai, ndviN, ndviF, vzaN, vzaF, CI=1.0, ndvi_max=0.87, ndvi_min=0.04, G=0.5):
#     """
#     优化LAI、CI、NDVI_s和NDVI_v参数
    
#     参数:
#     lai: 初始LAI值 (25个像元的数组)
#     ndviN: 近角度NDVI观测值 (25个像元的数组)
#     ndviF: 远角度NDVI观测值 (25个像元的数组)  
#     CI: 初始聚集指数 (默认1.0)
#     ndvi_max: 初始纯植被NDVI估计 (默认0.87)
#     ndvi_min: 初始纯土壤NDVI估计 (默认0.04)
#     G: 叶倾角分布参数 (固定0.5)
    
#     返回:
#     result: 优化结果字典
#     """
#     initial_CI = CI
#     initial_NDVI_s = ndvi_min
#     initial_NDVI_v = ndvi_max
#     initial_lai = lai

#     # 假设角度信息 (实际应用中需要根据具体数据调整)
#     theta_near = np.radians(vzaN)  # 转换为弧度
#     theta_far = np.radians(vzaF)   # 转换为弧度
    
#     cos_theta_near = np.cos(theta_near)
#     cos_theta_far = np.cos(theta_far)
    
#     def objective_function(params):
#         """
#         目标函数: 最小化所有方程的残差平方和
#         params: 参数向量 [LAI_1, LAI_2, ..., LAI_25, CI, NDVI_s, NDVI_v]
#         """
#         # 提取参数
#         LAI = params[:-3]  # 前25个是LAI值
#         CI_val = params[-3]  # 第26个是CI
#         NDVI_s = params[-2]  # 第27个是NDVI_s
#         NDVI_v = params[-1]  # 第28个是NDVI_v
        
#         # 确保参数在合理范围内
#         CI_val = np.clip(CI_val, 0.5, 1.0)
#         NDVI_s = np.clip(NDVI_s, 0.0, 0.15)  # 土壤NDVI通常较低
#         NDVI_v = np.clip(NDVI_v, 0.80, 0.99)  # 植被NDVI通常较高
        
#         # 确保NDVI_v > NDVI_s
#         if NDVI_s > 0.15 or NDVI_v < 0.80 or CI_val < 0.01 or CI_val > 1.0:
#             # 如果违反约束，返回大值惩罚
#             return 1e10
        
#         # 计算R值 (植被覆盖率)
#         R_near = (ndviN - NDVI_s) / (NDVI_v - NDVI_s)
#         R_far = (ndviF - NDVI_s) / (NDVI_v - NDVI_s)
        
#         # 限制R值在合理范围内，避免数值问题
#         R_near = np.clip(R_near, 0.01, 0.99)
#         R_far = np.clip(R_far, 0.01, 0.99)
        
#         # 计算模型预测值
#         pred_near = 1 - np.exp(-LAI * G * CI_val / cos_theta_near)
#         pred_far = 1 - np.exp(-LAI * G * CI_val / cos_theta_far)
        
#         # 添加正则化项 - 对CI、NDVI_s和NDVI_v的变化施加惩罚
#         # 使用较小的权重让这些参数变化更小
#         residual_near = np.abs(pred_near - R_near)
#         residual_far = np.abs(pred_far - R_far)
#         residual_sum = residual_near**2 + residual_far**2
#         reg_CI = 0.1 * (CI_val - initial_CI)**2
#         reg_NDVI_s = 10 * (NDVI_s - initial_NDVI_s)**2
#         reg_NDVI_v = 10 * (NDVI_v - initial_NDVI_v)**2
#         reg_lai = 0.1 * (np.average(np.abs(LAI-initial_lai)))**2
        
#         # 总目标函数 = 残差平方和 + 正则化项
#         total_objective = np.sum(residual_sum) + reg_CI + reg_NDVI_s + reg_NDVI_v + reg_lai
        
#         return total_objective
    
#     # 初始参数向量
#     x0 = np.concatenate([lai, [CI, ndvi_min, ndvi_max]])
    
#     # 参数边界
#     bounds = []
#     # LAI边界 (0到10)
#     for i in range(len(lai)):
#         bounds.append((0.01, 10.0))
#     # CI边界 (0.01到1.0)
#     bounds.append((0.5, 1.0))
#     # NDVI_s边界 (0.0到0.5)
#     bounds.append((0.0, 0.15))
#     # NDVI_v边界 (0.5到1.0)
#     bounds.append((0.8, 0.99))
    
#     # 优化选项
#     options = {
#         'maxiter': 1000,
#         'ftol': 1e-6,
#         'disp': True
#     }
    
#     # 执行优化
#     result = minimize(
#         objective_function,
#         x0,
#         method='L-BFGS-B',  # 适合有边界约束的问题
#         bounds=bounds,
#         options=options
#     )
    
#     # 提取优化结果
#     optimized_LAI = result.x[:-3]
#     optimized_CI = result.x[-3]
#     optimized_NDVI_s = result.x[-2]
#     optimized_NDVI_v = result.x[-1]
    
#     # 计算最终残差
#     final_residual = result.fun
    
#     # 输出结果摘要
#     print(f"优化完成!")
#     print(f"初始残差: {objective_function(x0):.6f}")
#     print(f"最终残差: {final_residual:.6f}")
#     print(f"优化CI: {optimized_CI:.4f}")
#     print(f"优化NDVI_s: {optimized_NDVI_s:.4f}")
#     print(f"优化NDVI_v: {optimized_NDVI_v:.4f}")
#     print(f"LAI范围: [{optimized_LAI.min():.3f}, {optimized_LAI.max():.3f}]")
#     print(f"LAI变化: [{np.average(optimized_LAI-lai):.3f}]")
#     print(f"优化状态: {result.message}")
    
#     # 返回完整结果
#     return {
#         'success': result.success,
#         'optimized_LAI': optimized_LAI,
#         'optimized_CI': optimized_CI,
#         'optimized_NDVI_s': optimized_NDVI_s,
#         'optimized_NDVI_v': optimized_NDVI_v,
#         'initial_residual': objective_function(x0),
#         'final_residual': final_residual,
#         'n_iterations': result.nit,
#         'message': result.message,
#         'result_object': result
#     }


if __name__ == '__main__':
    indir_h5_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/0_raw_h5/'
    infile_pure_soil_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/soil_sites.txt'
    infile_pure_veg_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/veg_sites.txt'

    n, m, ws = 2, 2, 5 # n 角度， m组分， ws窗口大小
    ndvi_max, ndvi_min, k = 0.87, 0.15, 1
    lst_min, lst_max = 250, 350
    hspot, wl = 0.2, 10.8

    if_Dahra = 0 # 只反演Dahra站点
    if_PureSites = 1 # 只反演纯站点
    if_ndvi = 0 # 0 用lai反演； 1 用NDVI反演 
    if_bayesian = 1 # bayesian 方法反演
    if_crown = 0  # 用森林假设反演

    # outdir_h5_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/inv_%01dc_%01dw_' % (m,ws) + ('ndvi' if if_ndvi == 1 else 'lai') + r'/'
    outdir_h5_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/inv_%01dc_%01dw_' % (m,ws) + 'bayesian' + r'/'
    mkdir_if_not_exist(outdir_h5_sites)
    angle_error_file = indir_h5_sites + r'Angle_error.txt'

    if if_crown:
        indir_veg_path = r'/media/hero/lsct04/0_base/Veg_para/'
        std_gl, tcc_gl, hcr_gl = aatsr_read_crown_data(indir_veg_path)

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

            # if fileName != 'AATSR_2009_150_101541.h5': continue


            year = int(fileName.split('_')[1])
            doy = int(fileName.split('_')[2])

            # if year != 2009: continue
            # if doy < 120: continue

            print(i,fileName)
            month,day = doy2date(year,doy)
            # print(month,day)

            start_time = time.time()
            infile = indir_site + fileName
            outfile = outdir_site + fileName

            if os.path.exists(outfile):
                # continue
                os.remove(outfile)

            # 读取数据
            ndviN, ndviF = aatsr_read_sites_obs(infile, ifNDVI=1)
            cloN_mask, cloF_mask = aatsr_read_sites_clo(infile)
            lstN,lstF = aatsr_read_sites_lst(infile)
            vzaN,vzaF,vaaN,vaaF,sza,saa = aatsr_read_sites_angle(infile)
            emisS,emisV,type,lai = aatsr_read_sites_emis(infile)
            indx,indy,ref_indx,ref_indy,lat,lon = aatsr_read_sites_loc(infile)
            utc_time = aatsr_read_sites_time(infile)


            if np.average(vzaF) > 60 or np.average(vzaF) < 50:  # 极少部分数据vzaF值异常
                print('Angle error')
                with open(angle_error_file,'a') as f:
                    f.write(siteName + ' ' + fileName + '\n')
                continue

            nl,ns = lstN.shape

            if nl != 31 or ns != 31:
                continue

            # 1.计算有效发射率矩阵
            ws = 5
            off = ws//2

            # for i in range(16 , 16+1):
            #     for j in range(15 , 16):
            #         lai_w = lai[i-off:i+off+1,j-off:j+off+1]
            #         ndviN_w = ndviN[i-off:i+off+1,j-off:j+off+1]
            #         ndviF_w = ndviF[i-off:i+off+1,j-off:j+off+1]
            #         vzaN_w = vzaN[i-off:i+off+1,j-off:j+off+1]
            #         vzaF_w = vzaF[i-off:i+off+1,j-off:j+off+1]
            #         cloN_mask_w = cloN_mask[i-off:i+off+1,j-off:j+off+1]
            #         cloF_mask_w = cloF_mask[i-off:i+off+1,j-off:j+off+1]
            #         mask = cloN_mask_w * cloF_mask_w
            #         optimize_LAI(lai_w[mask],ndviN_w[mask],ndviF_w[mask],vzaN_w[mask],vzaF_w[mask],CI=0.8)


            # if if_ndvi == 0: # lai反演
            #     w = np.zeros([nl,ns,n,m])
            #     for i in range(nl):
            #         for j in range(ns):
            #             w[i,j,:,:] = cal_effective_emissivity_hom(float(lai[i,j]),
            #                                                       hspot,
            #                                                       wl,
            #                                                       float(emisS[i,j]),
            #                                                       float(emisV[i,j]),
            #                                                       [float(vzaN[i,j]),float(vzaF[i,j])],
            #                                                       float(sza[i,j]),
            #                                                       [float(vaaN[i,j]),float(vaaF[i,j])],
            #                                                       float(saa[i,j]),
            #                                                       n,
            #                                                       m)
            # else: # ndvi反演
            #     fvcN = (ndviN - ndvi_min)/(ndvi_max - ndvi_min)  # nl*ns
            #     fvcF = (ndviF - ndvi_min)/(ndvi_max - ndvi_min)  # nl*ns
            #     fvcN[fvcN < 0] = 0
            #     fvcN[fvcN > 1] = 1
            #     fvcF[fvcF < 0] = 0
            #     fvcF[fvcF > 1] = 1
            #     fvcN[cloN_mask == 0] = 0
            #     fvcF[cloF_mask == 0] = 0
            #     wN = np.stack([emisS * (1-fvcN), emisV * fvcN], axis=-1)  # 形状: (nl, ns, m)
            #     wF = np.stack([emisS * (1-fvcF), emisV * fvcF], axis=-1)  # 形状: (nl, ns, m)
            #     w = np.stack([wN, wF], axis=2)
            
            if if_bayesian:
                ## LAI 版本
                fvc_n = cal_fvc_from_lai(vzaN, lai)
                fvc_o = cal_fvc_from_lai(vzaF, lai)
                # print(lai[16,16])

                fvcN = fvc_n
                fvcF = fvc_o

                ## NDVI 版本
                # fvcN = (ndviN - ndvi_min)/(ndvi_max - ndvi_min)  # nl*ns
                # fvcF = (ndviF - ndvi_min)/(ndvi_max - ndvi_min)  # nl*ns
                # fvcN[fvcN < 0] = 0
                # fvcN[fvcN > 1] = 1
                # fvcF[fvcF < 0] = 0
                # fvcF[fvcF > 1] = 1
                # fvcN[cloN_mask == 0] = 0
                # fvcF[cloF_mask == 0] = 0
                # if np.isnan(fvcN[16,16]): continue
                # print(ndviN[16,16],ndviF[16,16])

                # # 森林版本
                # indx,indy = indx.astype(int),indy.astype(int)
                # std,tcc,hcr = std_gl[indx,indy], tcc_gl[indx,indy], hcr_gl[indx,indy]
                # hcr[hcr<0.5] = 0.5
                # rcr = hcr / 3.0
                # fvcN = proportion_bidirectional_crown_one(lai, std, hspot, hcr,rcr, vzaN, sza, np.abs(vaaN-saa))
                # fvcF = proportion_bidirectional_crown_one(lai, std, hspot, hcr,rcr, vzaN, sza, np.abs(vaaF-saa))
                
                fvcN[fvcN>1.0] = 1.0
                fvcF[fvcF>1.0]  = 1.0
                fvcN[fvcN<0.0]  = 0.0
                fvcF[fvcF<0.0]  = 0.0

            print(fvcF[16,16],fvcN[16,16])
            print(fvcF[16,16]-fvcN[16,16])
            # # break

            # 2.计算有效发射率矩阵
            # if if_ndvi == 0: # lai反演0
            #     bN = cal_rad_from_lst(lstN,wl,lai,vzaN,emisS,emisV)
            #     bF = cal_rad_from_lst(lstF,wl,lai,vzaF,emisS,emisV)
            #     b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2)
            # else:
            #     bN = cal_rad_from_lst_fvc(lstN,wl,fvcN,emisS,emisV)
            #     bF = cal_rad_from_lst_fvc(lstF,wl,fvcF,emisS,emisV)
            #     b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2)


            # 3.求解
            nl,ns = lstN.shape
            lsct = np.zeros([nl,ns,2]) 
            lsct[:,2:ns-2,:] = inv_mpl_agl_multiple_2(lstN, lstF, emisS, emisV, fvcN, fvcF, wl=10.8)
            print(lsct.shape)

            inv_start_time = time.time()
            lst = np.concatenate([lstN[:,:,np.newaxis], lstF[:,:,np.newaxis]], axis=2)
            if if_ndvi == 0: # lai反演
                cloN_mask = cloN_mask * (lai > 0)
                cloF_mask = cloF_mask * (lai > 0)
            mask = np.concatenate([cloN_mask[:,:,np.newaxis], cloF_mask[:,:,np.newaxis]], axis=2)
            mask = mask * (lst>lst_min)*(lst<lst_max) # 只保留合理范围内的LST
            off = ws//2

            # if m ==2:
            #     lsct = inv_lsct2_window(n, m, ws, wl, w, b, mask, lst)

            # elif m ==3:
            #     lsct = np.full([nl,ns,4],np.nan)  # 4维：Tsl,Tsh,Ts,Tv 夜晚 前两者均为Ts

            #     day_mask = sza < 89
            #     mask_day = mask * day_mask[:,:,np.newaxis]
            #     mask_night = mask * (~day_mask[:,:,np.newaxis])

            #     if np.sum(mask_day) > 0:
            #         lsct_day = inv_lsct3_window(n, m, ws, wl, w, b, mask_day, lst)
            #         psoil = cal_psoil_hom(lai,sza)
            #         Tsl, Tsh,Tv = lsct_day[:,:,0], lsct_day[:,:,1], lsct_day[:,:,2]
            #         Ts = inv_planck(wl, psoil * planck(wl,Tsl) + (1-psoil) *planck(wl,Tsh))
            #         lsct[:,:,0], lsct[:,:,1], lsct[:,:,2], lsct[:,:,3] = Tsl, Tsh, Ts,Tv
            #     elif np.sum(mask_night) > 0:
            #         w2 = np.zeros([nl,ns,n,2])
            #         w2[:,:,:,0] = w[:,:,:,0] + w[:,:,:,1]
            #         w2[:,:,:,1] = w[:,:,:,2]
            #         lsct_night = inv_lsct2_window(n, 2, ws, wl, w2, b, mask_night, lst,ifday = 0)
            #         lsct[~day_mask,0] = lsct_night[~day_mask,0]
            #         lsct[~day_mask,1] = lsct_night[~day_mask,0]
            #         lsct[~day_mask,2] = lsct_night[~day_mask,0]
            #         lsct[~day_mask,3] = lsct_night[~day_mask,1]


            # 保存结果
            name_list = ['lstN','lstF','lai','indx','indy','ref_indx','ref_indy','cloN_mask','cloF_mask']
            data_list = [lstN,lstF,lai,indx,indy,ref_indx,ref_indy,cloN_mask,cloF_mask]
            dtype_list = np.full_like(name_list,'f')
            write_h5py_file(outfile,name_list,data_list,dtype_list,compression=None,ifcover = 1)
            write_h5py_item(outfile,'utc_time',utc_time.isoformat(),dtype=h5py.string_dtype())

            if m == 2:
                if if_ndvi == 0:
                    write_h5py_item(outfile,'lsct2_Ts_lai',lsct[:,:,0],'f',if_overwrite=1)
                    write_h5py_item(outfile,'lsct2_Tv_lai',lsct[:,:,1],'f',if_overwrite=1)
                if if_ndvi == 1:
                    write_h5py_item(outfile,'lsct2_Ts_ndvi',lsct[:,:,0],'f',if_overwrite=1)
                    write_h5py_item(outfile,'lsct2_Tv_ndvi',lsct[:,:,1],'f',if_overwrite=1)
                if if_bayesian:
                    write_h5py_item(outfile,'lsct2_Ts_bayesian',lsct[:,:,0],'f',if_overwrite=1)
                    write_h5py_item(outfile,'lsct2_Tv_bayesian',lsct[:,:,1],'f',if_overwrite=1)
            if m == 3:
                if if_ndvi == 0:
                    write_h5py_item(outfile,'lsct3_Tsl_lai',lsct[:,:,0],'f',if_overwrite=1)
                    write_h5py_item(outfile,'lsct3_Tsh_lai',lsct[:,:,1],'f',if_overwrite=1)
                    write_h5py_item(outfile,'lsct3_Ts_lai',lsct[:,:,2],'f',if_overwrite=1)
                    write_h5py_item(outfile,'lsct3_Tv_lai',lsct[:,:,3],'f',if_overwrite=1)
                if if_ndvi == 1:
                    write_h5py_item(outfile,'lsct3_Tsl_ndvi',lsct[:,:,0],'f',if_overwrite=1)
                    write_h5py_item(outfile,'lsct3_Tsh_ndvi',lsct[:,:,1],'f',if_overwrite=1)
                    write_h5py_item(outfile,'lsct3_Ts_lai',lsct[:,:,2],'f',if_overwrite=1)
                    write_h5py_item(outfile,'lsct3_Tv_ndvi',lsct[:,:,3],'f',if_overwrite=1)
            
            end_time = time.time()
            print(f"总执行时间: {end_time - start_time:.4f}秒\n")
