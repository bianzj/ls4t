from util.old.util import *
from multiprocessing import Pool,cpu_count
from scipy.optimize import minimize
from util.rt.hom import *
from util.rt.crown import *

def planck(wavelength, Ts):
    '''
    基于planck公式，计算某个波长时候，从温度到辐射的转换
    :param wavelength: 波长，10.5
    :param Ts: 温度，可以是亮温，也可以是摄氏度
    :return: 辐射
    '''
    c1 = planck_c1
    c2 = planck_c2
    if isinstance(Ts * 1.0, float):
        wavelength = np.float(wavelength)
        Ts = np.float(Ts)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    else:
        wavelength = np.float(wavelength)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    return rad

'''发射率'''
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

'''加限制求解方法'''
def fitting_linear_constraint_3angle_3component_window(w,b,deta12,deta23):
    number_component = 3
    number_angle = 3
    number_observation = 3*3
    sunlit_soil_radiance_variance = 10
    shaded_soil_radiance_variance = 5
    leaf_radiance_variance = 5
    sensor_noise = 0.25
    ws = 3

    def constraint_func(x, lstN, deta12_min, deta12_max, deta23_min, deta23_max):
        # 计算每个约束条件的值
        constraint1 = -deta12_min + (x[0] - x[1])
        constraint2 = deta12_max - (x[0] - x[1])
        constraint3 = -deta23_min + (x[1] - x[2])
        constraint4 = deta23_max - (x[1] - x[2])
        return [constraint1, constraint2, constraint3, constraint4]

    def objective_func(x, w, b):
        return np.linalg.norm(np.dot(w, x) - b)
    lstN = inv_planck(10.8,np.max(b))
    deta12_min = planck(10.8,lstN +  deta12[0]/2) -planck(10.8,lstN - deta12[0]/2)
    deta12_max = planck(10.8,lstN + deta12[1]/2) - planck(10.8,lstN- deta12[1]/2)
    deta23_min = planck(10.8,lstN + deta23[0]/2) - planck(10.8,lstN- deta23[0]/2)
    deta23_max = planck(10.8,lstN + deta23[1]/2) - planck(10.8,lstN- deta23[1]/2)

    # 定义约束条件
    constraints = {'type': 'ineq', 'fun': constraint_func,
                   'args': (lstN, deta12_min, deta12_max, deta23_min, deta23_max)}

    x0 = np.array([lstN, lstN-10, lstN])
    x0 = planck(10.8,x0)
    wl = 10.8
    bounds = [[planck(wl, lstN-3), planck(wl, lstN + 30)], [planck(wl, lstN - 20), planck(wl, lstN + 20)],
              [planck(wl, lstN - 20), planck(wl, lstN + 20)]]
    # SLSQP  trust-constr
    result = minimize(objective_func, x0, args=(w, b),constraints=constraints,bounds = bounds,method ='SLSQP')

    p0 = result.x

    # Bayesian 12 13 14
    w_p = w.reshape((ws*ws,number_angle,number_component))
    w_p = np.matrix(w_p[4,:,:])
    w_p = np.transpose(w_p)
    b_p = b.reshape((ws*ws,number_angle))
    b_p = np.matrix(b_p[4,:])
    p0 = np.matrix(p0)
    Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
    Cm = np.diag([sunlit_soil_radiance_variance,shaded_soil_radiance_variance, leaf_radiance_variance])
    pre = np.linalg.inv(np.transpose(w_p) * np.linalg.inv(Cd) * w_p + np.linalg.inv(Cm))
    coeff = pre * (np.transpose(w_p) * np.linalg.inv(Cd) * np.reshape(b_p,(3,1)) + np.linalg.inv(Cm) * np.reshape(p0,(3,1)))
    return coeff


def fitting_linear_constraint_2angle_3component_window(w,b,deta12,deta23):
    def constraint_func(x, lstN, deta12_min, deta12_max, deta23_min, deta23_max):
        # 计算每个约束条件的值
        constraint1 = -deta12_min + (x[0] - x[1])
        constraint2 = deta12_max - (x[0] - x[1])
        constraint3 = -deta23_min + (x[1] - x[2])
        constraint4 = deta23_max - (x[1] - x[2])
        return [constraint1, constraint2, constraint3, constraint4]

    def objective_func(x, w, b):
        return np.linalg.norm(np.dot(w, x) - b)
    lstN = inv_planck(10.8,np.max(b))
    deta12_min = planck(10.8,lstN +  deta12[0]/2) -planck(10.8,lstN - deta12[0]/2)
    deta12_max = planck(10.8,lstN + deta12[1]/2) - planck(10.8,lstN- deta12[1]/2)
    deta23_min = planck(10.8,lstN + deta23[0]/2) - planck(10.8,lstN- deta23[0]/2)
    deta23_max = planck(10.8,lstN + deta23[1]/2) - planck(10.8,lstN- deta23[1]/2)

    # 定义约束条件
    constraints = {'type': 'ineq', 'fun': constraint_func,
                   'args': (lstN, deta12_min, deta12_max, deta23_min, deta23_max)}

    x0 = np.array([lstN, lstN-10, lstN])
    x0 = planck(10.8,x0)
    wl = 10.8
    bounds = [[planck(wl, lstN-5), planck(wl, lstN + 40)], [planck(wl, lstN - 20), planck(wl, lstN + 20)],
              [planck(wl, lstN - 20), planck(wl, lstN + 20)]]
    # SLSQP  trust-constr
    result = minimize(objective_func, x0, args=(w, b),constraints=constraints,bounds = bounds,method ='SLSQP')

    p0 = result.x
    return p0

def fitting_linear_constraint_2angle_3component_window_weight(w,b,weight, deta12,deta23):
    def constraint_func(x, lstN, deta12_min, deta12_max, deta23_min, deta23_max):
        # 计算每个约束条件的值
        constraint1 = -deta12_min + (x[0] - x[1])
        constraint2 = deta12_max - (x[0] - x[1])
        constraint3 = -deta23_min + (x[1] - x[2])
        constraint4 = deta23_max - (x[1] - x[2])
        return [constraint1, constraint2, constraint3, constraint4]

    def objective_func(x, w, b,weight):
        residuals = np.dot(w, x) - b
        return np.sum(weight*residuals**2)
    lstN = inv_planck(10.8,np.max(b))
    deta12_min = planck(10.8,lstN +  deta12[0]/2) -planck(10.8,lstN - deta12[0]/2)
    deta12_max = planck(10.8,lstN + deta12[1]/2) - planck(10.8,lstN- deta12[1]/2)
    deta23_min = planck(10.8,lstN + deta23[0]/2) - planck(10.8,lstN- deta23[0]/2)
    deta23_max = planck(10.8,lstN + deta23[1]/2) - planck(10.8,lstN- deta23[1]/2)

    # 定义约束条件
    constraints = {'type': 'ineq', 'fun': constraint_func,
                   'args': (lstN, deta12_min, deta12_max, deta23_min, deta23_max)}

    x0 = np.array([lstN, lstN-10, lstN])
    x0 = planck(10.8,x0)
    wl = 10.8
    bounds = [[planck(wl, lstN-5), planck(wl, lstN + 50)], [planck(wl, lstN - 30), planck(wl, lstN + 30)],
              [planck(wl, lstN - 30), planck(wl, lstN + 30)]]
    # SLSQP  trust-constr
    result = minimize(objective_func, x0, args=(w, b,weight),constraints=constraints,bounds = bounds,method ='SLSQP')

    p0 = result.x
    return p0


'''两角度 五像元 多线程—— 两组分'''
'''调用inv_mpl_agl_multiple_2'''
'''多线程两组分温度反演程序：共三个'''
#######中间传递参数函数  两组分
def doMultiple_line_inv_2(param):
    return line_inv_2((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]))

######分行计算的两组分温度结果，为多线程内部函数调用
def line_inv_2(wNLine, wOLine, radNLine, radOLine, maskLine,ns = 1024):
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

    result = np.zeros([number_component,ns])

    off = 2
    for kk in range(off, ns-off):
        maskk = maskLine[2,kk]
        if maskk == 0: continue

        ns1 = kk - off
        ns2 = kk + off + 1
        ###### w1是nadir，w2是oblique
        w1 = wNLine[:,:,ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, :, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))

        bb1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        bb2 = (np.reshape(radOLine[:, ns1:ns2], -1))

        mask = np.reshape(maskLine[:, ns1:ns2], -1)
        ind = (mask == 1) * (np.isnan(w1[0, :]) == 0)

        num_val_point = np.sum(ind)
        if (num_val_point < number_value_threshold): continue
        ns_temp = np.asarray([-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
        nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
        part = 6

        n0 = np.ones(len(ns_temp))
        x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
        w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
        w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

        ww = np.hstack((w11[:, ind], w22[:, ind]))
        bb = np.hstack((bb1[ind], bb2[ind]))

        ###############################################
        ### least-square method
        ###############################################
        ww = np.transpose(ww)

        coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]

        ################################################
        ### first reult with averaing information
        ################################################
        offcenter = np.int(((2 * off + 1) * (2 * off + 1) - 1) / 2)
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
        component_temperature = inv_planck(wl, ctprior)
        #################################################
        ### second result by combining one-point result
        #################################################

        ns1 = kk - off_
        ns2 = kk + off_ + 1
        w1 = wNLine[:, 2, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, 2, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        b1 = (np.reshape(radNLine[2, ns1:ns2], -1))
        b2 = (np.reshape(radOLine[2, ns1:ns2], -1))
        w = np.hstack((w1, w2))
        b = np.hstack((b1, b2))
        w = np.transpose(w)

        #################################################
        ### least-squared method
        #################################################
        # coeffprior = np.asarray(lstsq(w, b))[0]

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

        result[:, kk] = [component_temperature[0], component_temperature[1]]

    return result

####### 多线程计算两组分
####### 输入：nadir和oblique两个角度的地表温度，土壤发射率、植被发射率、nadir和obliqu两个角度的植被覆盖度fvc
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
    for kn in range(off, nl-off):
        ###### 取wN的所有组分的5行，列全部，进行多线程的操作, 5行为多像元反演组分温度时候所用到的
        wNLine = wN[:,kn-off: kn + off + 1, :]
        wOLine = wO[:, kn - off: kn + off + 1, :]

        radNLine = rad_n[kn-off:kn+off+1, : ]
        radOLine = rad_o[kn-off:kn+off+1, : ]

        maskLine = mask[kn-off: kn + off+1, : ]

        para.append([wNLine, wOLine, radNLine, radOLine, maskLine, ns])

    tasks= []
    pool = Pool(min(24,cpu_count()))
    for p in para:
        tasks.append(pool.apply_async(doMultiple_line_inv_2, (p,)))
    pool.close()
    pool.join()
    results = [task.get() for task in tasks]
    end = time.time()
    results = np.asarray(results)
    resultForm = np.asarray([results[:,0,:], results[:,1,:]])
    print('time cost: ', end - start, 's')

    return resultForm


'''两角度 五像元 多线程—— 三组分'''
'''硬解，就认为温度一致'''
'''调用inv_mpl_agl_multiple_3'''
'''多线程两组分温度反演程序：共三个'''
def doMultiple_line_inv_3(param):
    return inv_lsct3_mpl((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]),(param[6]))

# 直接窗口硬解
def inv_lsct3_mpl(wNLine, wOLine, radNLine, radOLine, maskNLine,maskOLine,ns = 1024):
    wl = 10.8
    Tsl_sh_range = [3,30]
    Tsh_v_range = [-10,10]
    window_size = wNLine.shape[1]
    off = int((window_size-1)/2)
    number_component= 3
    result = np.zeros([number_component,ns])
    for kk in range(off, ns-off):
        ns1 = kk - off
        ns2 = kk + off + 1
        ###### w1是nadir，w2是oblique
        maskN = np.reshape(maskNLine[:, ns1:ns2], -1)
        maskO = np.reshape(maskOLine[:, ns1:ns2], -1)
        if maskN[int((window_size*window_size-1)/2)]==0 or maskO[int((window_size*window_size-1)/2)]==0:
            continue

        w1 = wNLine[:, :, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, :, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        w = np.concatenate((w1, w2), axis=1)

        b1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        b2 = (np.reshape(radOLine[:, ns1:ns2], -1))
        b = np.concatenate((b1, b2))

        ind = np.concatenate((maskN, maskO))
        num_val_point = np.sum(ind)

        if num_val_point < 6: continue
        coeff = fitting_linear_constraint_2angle_3component_window(w[:,ind].T,b[ind],Tsl_sh_range,Tsh_v_range)
        component_temperature = inv_planck(wl, coeff)
        result[:, kk] = [component_temperature[0], component_temperature[1], component_temperature[2]]
    return result

# 加组分温度保持二次函数关系,还未完成
def inv_lsct3_mpl_pixel(wNLine, wOLine, radNLine, radOLine, maskNLine,maskOLine,ns = 1024):
    wl = 10.8
    Tsl_sh_range = [3,30]
    Tsh_v_range = [-10,10]
    window_size = wNLine.shape[1]
    off = int((window_size-1)/2)
    number_component= 3
    result = np.zeros([number_component,ns])
    for kk in range(off, ns-off):
        maskk = maskLine[2,kk]
        if maskk == 0: continue

        ns1 = kk - off
        ns2 = kk + off + 1
        ###### w1是nadir，w2是oblique
        w1 = wNLine[:,:,ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, :, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))

        bb1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        bb2 = (np.reshape(radOLine[:, ns1:ns2], -1))

        mask = np.reshape(maskLine[:, ns1:ns2], -1)
        ind = (mask == 1) * (np.isnan(w1[0, :]) == 0)

        num_val_point = np.sum(ind)
        if (num_val_point < number_value_threshold): continue
        ns_temp = np.asarray([-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
        nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
        part = 6

        n0 = np.ones(len(ns_temp))
        x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
        w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
        w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

        ww = np.hstack((w11[:, ind], w22[:, ind]))
        bb = np.hstack((bb1[ind], bb2[ind]))

        ###############################################
        ### least-square method
        ###############################################
        ww = np.transpose(ww)

        coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]

        ################################################
        ### first reult with averaing information
        ################################################
        offcenter = np.int(((2 * off + 1) * (2 * off + 1) - 1) / 2)
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
        component_temperature = inv_planck(wl, ctprior)


'''AATSR'''
'''两角度 五像元 多线程—— 三组分'''
def DT_value(DT):
    deta12, deta23 = [5,20], [-10,10]
    if DT == 1:
        deta12, deta23 = [1,10], [-5,5]
    elif DT == 2:
        deta12, deta23 = [3,15], [-7.5,7.5]
    elif DT == 3:
        deta12, deta23 = [5,20], [-10,10]
    elif DT == 4:
        deta12, deta23 = [10,30], [-12.5,12.5]
    elif DT == 5:
        deta12, deta23 = [15,40], [-15,15]
    return deta12, deta23


def calculate_weights(window_size):
    center = window_size // 2
    weights = np.zeros((window_size, window_size))

    for i in range(window_size):
        for j in range(window_size):
            d_ij = np.sqrt((i - center) ** 2 + (j - center) ** 2)
            if d_ij <= window_size:
                weights[i, j] = (1 - (d_ij / window_size) ** 2) ** 2
            else:
                weights[i, j] = 0
    return weights


def doMultiple_line_inv_3_AATSR(param):
    return inv_lsct3_AATSR_mpl((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]),(param[6]),(param[7]))
def inv_lsct3_AATSR_mpl(wNLine, wOLine, radNLine, radOLine, maskNLine,maskOLine, DTLine,ns = 1024):
    wl = 10.8
    window_size = wNLine.shape[1]
    off = int((window_size-1)/2)
    number_component= 3
    result = np.zeros([number_component,ns])
    for kk in range(off, ns-off):
        ns1 = kk - off
        ns2 = kk + off + 1
        ###### w1是nadir，w2是oblique
        maskN = np.reshape(maskNLine[:, ns1:ns2], -1)
        maskO = np.reshape(maskOLine[:, ns1:ns2], -1)
        if maskN[int((window_size*window_size-1)/2)]==0 or maskO[int((window_size*window_size-1)/2)]==0:
            continue
        DT = DTLine[off, kk]
        delta12, delta23 = DT_value(DT)

        w1 = wNLine[:, :, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, :, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        w = np.concatenate((w1, w2), axis=1)

        b1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        b2 = (np.reshape(radOLine[:, ns1:ns2], -1))
        b = np.concatenate((b1, b2))

        ind = np.concatenate((maskN, maskO))
        num_val_point = np.sum(ind)

        weight = calculate_weights(5)
        weight = np.reshape(weight, -1)
        weight = np.concatenate((weight,weight))

        if num_val_point < 10: continue
        coeff = fitting_linear_constraint_2angle_3component_window_weight(w[:,ind].T,b[ind],weight[ind],delta12, delta23)
        component_temperature = inv_planck(wl, coeff)
        result[:, kk] = [component_temperature[0], component_temperature[1], component_temperature[2]]
    return result

