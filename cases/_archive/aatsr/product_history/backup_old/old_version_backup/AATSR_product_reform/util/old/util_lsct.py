from utils.old.util_old import *
from multiprocessing import Pool,cpu_count


'''

组分温度反演的策略：
0. 多角度算法计算土壤和植被的温度；
1. 双角度算法计算土壤和植被的温度；
2. 双角度算法+多像元计算土壤和植被的温度；
3. 三角度算法+多像元计算光照土壤和阴影土壤和植被的温度；

执行的时候会有：
a. 简单站点执行；
b. 多线程全图执行；


!!! 多线程的时候，不能开独立运行窗口！！！
'''

def cal_hotspot(laiWindow, vzaWindow, vaaWindow, szaWindow, saaWindow):
    G = 0.5
    rd = np.pi / 180.0
    h = 1.0
    hs = 0.05
    d = h * hs

    ind = laiWindow > 5.1
    laiWindow[ind] = 5.1

    raa = np.abs(saaWindow - vaaWindow)
    costhetanv = np.cos(vzaWindow * rd)
    costhetas = np.cos(szaWindow * rd)
    costhetavn2 = np.power(costhetanv, 2)
    costhetas2 = np.power(costhetas, 2)
    gap_n = np.exp(-G * laiWindow / costhetanv)
    sinthetas = np.sin(szaWindow * rd)
    sinthetanv = np.sin(vzaWindow * rd)
    cosalpha = costhetas * costhetanv + sinthetas * sinthetanv * np.cos(raa * rd)
    sigma_n = np.sqrt(1 / costhetas2 + 1 / costhetavn2 - 2 * cosalpha / costhetas / costhetanv)
    w_n = d / (h * sigma_n) * (1 - np.exp(-h * sigma_n / d))

    pg_n = np.exp(-(G / costhetanv + G / costhetas - w_n * np.sqrt(G * G / costhetanv / costhetas)) * laiWindow) / gap_n

    ind = (laiWindow > 0)
    return pg_n,ind


def readImages_obs(infile_lst, infile_red, infile_nir):
    '''
    读取数据，相对动态的，即每个图像都会变化的部分
    :param infile_lst: 温度的路径
    :param infile_red: 红光路径
    :param infile_nir: 近红外路径
    :return: 数据和投影信息
    '''

    [lst, ns, nl, nb, geog, proj] = read_image_gdal(infile_lst)
    [red, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_red)
    [nir, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_nir)
    # lst = resize_data_ls(lst,nl/2,ns/2)
    # red = resize_data_ls(red,nl/2,ns/2)
    # nir = resize_data_ls(nir,nl/2,ns/2)
    ndvi = red*1.0
    ind = (red >0) *(nir >0)
    ndvi[ind] = (nir[ind]-red[ind])/(nir[ind]+red[ind])

    return lst,ndvi,geog,proj


def readImages_emis(infile_emis_s, infile_emis_v, infile_classif, number_colume_emis = 2):
    '''
    读取数据，这里读取相对稳定的数据，发射率和类别
    :param infile_emis_s: 土壤发射率路径 tif
    :param infile_emis_v: 植被发射率路径 txt
    :param infile_classif: 地表类型 tif
    :return: 发射率和投影信息
    '''
    time_emissivity = 1000.0
    # get soil emissivity
    [emis_s, ns, nl, nb, geog, proj] = read_image_gdal(infile_emis_s)
   # emis_s = resize_data_line(emis_s,nl/2,ns/2)
    if np.average(emis_s[emis_s>0])>1.0:
        emis_s = emis_s / time_emissivity
    [classif, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_classif)
    #classif = resize_data_near(classif,nl/2,ns/2)
    classif = np.asarray(classif, np.int)

    emis_v = read_txt_array(infile_emis_v, 0, number_colume_emis)
    emis_v = emis_v[classif, 0] / time_emissivity
    return emis_s,emis_v,geog,proj


def readImages_angle(infile_lai, infile_vza_n, infile_vaa_n, infile_sza, infile_saa, resample=1):
    '''
    读取角度数据和结构数据，并计算透过率和热点
    :param infile_lai:叶面积指数
    :param infile_vza_n: 观测角度
    :param infile_vaa_n: 观测方位角
    :param infile_sza:太阳天顶角
    :param infile_saa:太阳方位角
    :param resample: 采样间隔
    :return: 透过率和反射率
    '''
    G = 0.5
    rd = np.pi/180.0
    h = 3.2 # 1.0
    hs = 2  # 0.2
    d = h*hs

    [lai, ns, nl, nb, geog, proj] = read_image_gdal(infile_lai)
    lai = resize_data(lai,nl/resample,ns/resample)
    [sza, ns, nl, nb, geog, proj] = read_image_gdal(infile_sza)
    [vza_n, ns, nl ,nb, geog, proj] = read_image_gdal(infile_vza_n)
    # [vza_o, ns, nl ,nb, geog, proj] = read_image_gdal(infile_vza_o)
    [vaa_n, ns, nl ,nb, geog, proj] = read_image_gdal(infile_vaa_n)
    # [vaa_o, ns, nl ,nb, geog, proj] = read_image_gdal(infile_vaa_o)
    [saa, ns, nl ,nb, geog, proj] = read_image_gdal(infile_saa)
    sza = resize_data(sza,nl/resample,ns/resample)
    saa = resize_data(saa,nl/resample,ns/resample)
    vza_n = resize_data(vza_n, nl/resample, ns/resample)
    vaa_n = resize_data(vaa_n, nl/resample, ns/resample)

    raa_n = np.abs(saa-vaa_n)
    costhetanv = np.cos(vza_n*rd)
    costhetas = np.cos(sza*rd)
    costhetavn2 = np.power(costhetanv,2)
    costhetas2 = np.power(costhetas,2)
    gap_n = np.exp(-G*lai/costhetanv)

    sinthetas = np.sin(sza * rd)
    sinthetanv = np.sin(vza_n*rd)
    cosalpha = costhetas * costhetanv + sinthetas * sinthetanv * np.cos(raa_n*rd)
    sigma_n = np.sqrt(1/costhetas2+1/costhetavn2-2*cosalpha/costhetas/costhetanv)
    w_n = d/(h*sigma_n)*(1-np.exp(-h*sigma_n/d))

    pg_n = np.exp(-(G/costhetanv+G/costhetas-w_n*np.sqrt(G*G/costhetanv/costhetas))*lai)/gap_n

    return pg_n

'''
反演3组分
'''

def lsct3_inv(wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine,ns = 1024):
    """
    用于反演三组分组分温度
    :param wNLine: 窗口垂直方向组分有效发射率
    :param wOLine: 窗口倾斜方向组分有效发射率
    :param wALine: 窗口AHI组分有效发射率
    :param radNLine: 窗口垂直方向能量
    :param radOLine: 窗口倾斜方向能量
    :param radAhiLine: 窗口AHI能量
    :param maskLine:判断了fvc和能量是否有值，有值为1，无则为0
    :param ns: 列号，长度
    :return:
    """
    wl = 10.8
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.10
    number_component = 3
    number_angle = 3
    number_value_threshold = 12
    result = np.zeros([3, ns])
    result_point = np.zeros([3, ns])
    result_window = np.zeros([3, ns])

    ###
    off_inv = 2
    off_inv2 = 0

    for kk in range(off_inv, ns-off_inv):
        ## maskk 窗口中心像元，并判断不为0进行反演
        maskk = maskLine[2, kk]
        if maskk == 0: continue

        ### ns1和ns2为5*5窗口的左右界
        ns1 = kk - off_inv
        ns2 = kk + off_inv + 1
        ### w1为垂直窗口有效发射率，提取5*5窗口，同理w2为倾斜结果，并将3*5*5展平成 3（组分）*25（像元）
        w1 = wNLine[:,:, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,:, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        ### 将像元能量同样操作，由于一个像元对应一个能量，所以1*5*5，展成1*25
        bb1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        bb2 = (np.reshape(radOLine[:, ns1:ns2], -1))
        mask = np.reshape(maskLine[:, ns1:ns2],-1)

        ind = (mask==1) * (np.isnan(w1[0,:])==0)
        ### 判断mask为1且有效发射率不为0，统计像元个数->方程个数。要解3*6=18个未知数，如果只用两个角度至少需要9个像元才有解，这里设置比较大为12个
        num_val_point = np.sum(ind)
        if (num_val_point < number_value_threshold): continue

        ### w1 for nadir and w2 for oblique
        ### ns_temp为距离窗口中心的列号，nl_temp为距离窗口中心的行号
        ns_temp = np.asarray([-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
        nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
        part = 6

        n0 = np.ones(len(ns_temp))
        ### x矩阵为多像元算法中的各项像元行列号值，从上到下每一行分别为：常数项（1）；行号；列号；行号平方；列号平方；行列号乘积（6*25）
        x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
        ### w11为3个组分有效发射率乘上x系数阵,18*25，w22同理
        w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
        w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
        ### ww是将垂直和倾斜方向的方程联立，bb代表能量
        ww = np.hstack((w11[:, ind], w22[:, ind]))
        bb = np.hstack((bb1[ind], bb2[ind]))

        ###############################################
        ### least-square method
        ###############################################
        ww = np.transpose(ww)
        ### coffprior为第一次最小二乘的初解，得到的解为每个组分的6个参数，一共18个参数值
        coeffprior = fitting_unknown_linear_sklearn(bb,ww,method='ridge')
        # coeffprior = fitting_unknown_linear_sparse(bb,ww)

        # print(kk)
        # coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ###############################################
        ### Bayes method with priori information
        ###############################################
        # bbb = sorted(b)
        # halfpoint = np.int(num_point / 2)
        # rleaf = np.average(bbb[0])
        # rsoil = np.average(bbb[1])
        # coeffprior = np.transpose(np.matrix([rsoil, 0, 0, 0, 0, 0, rleaf, 0, 0, 0, 0, 0]))
        # bb = np.transpose(np.matrix(bb))
        # ww = np.transpose(ww)
        # Cd = np.matrix(np.diag(np.ones(num_point * 2)) * Cdvaluep)
        # Cm = np.matrix(np.diag(np.ones(2 * part)))
        # Cm[0, 0] = 15.0
        # Cm[part, part] = 10.0
        # pre = np.linalg.inv(np.transpose(ww) * np.linalg.inv(Cd) * ww + np.linalg.inv(Cm))
        # ctprior = pre * (np.transpose(ww) * np.linalg.inv(Cd) * bb + np.linalg.inv(Cm) * coeffprior)

        #################################################
        ### first result without averaging information
        #################################################
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ################################################
        ### first reult with averaing information
        ################################################
        offcenter = np.int(((2 * off_inv + 1) * (2 * off_inv + 1) - 1) / 2)
        ### 这个fd是归一化的F矩阵，代表权重值
        fd = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
        fd = np.reshape(fd, -1) * 1.0
        ### 计算了三个组分的刚求解的系数和六种像元行列号的乘积，每个像元不同，这个乘积实际就是各个像元如果是纯像元发射的能量
        coeffprior = np.asarray(coeffprior)
        ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
        ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
        ct3 = np.asarray([np.sum(coeffprior[2 * part:3 * part] * x[:part, j]) for j in range(25)])
        indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                 (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold) * \
                 (ct3 > radiance_min_threshold) * (ct3 < radiance_max_threshold)
        apoint = np.sum(indnew)
        if (apoint <= 1):
            cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
            cd2 = np.sum(coeffprior[part:2 * part] * x[:, offcenter])
            cd3 = np.sum(coeffprior[2 * part:3 * part] * x[:, offcenter])
            ctprior = np.transpose(np.matrix([cd1, cd2, cd3]))

        else:
            fd[indnew] = fd[indnew] / np.sum(fd[indnew])

            # inver-distance weight but not used
            # bb0 = bb1[offcenter]
            # fdnew = np.zeros(25)
            # dismax = max(abs(bb1[indnew] - bb0))
            # if dismax != 0:
            #     fdnew[indnew] = 1.0 - abs(1.0 * bb1[indnew] - bb0) / dismax
            # else:
            #     fdnew[:] = 1
            # fdnew[indnew] = fdnew[indnew] / np.sum(fdnew[indnew])
            # fd[indnew] = (fdnew[indnew] * fd[indnew]) / np.sum(fdnew[indnew] * fd[indnew])

            cd1new = np.sum(ct1[indnew] * fd[indnew])
            cd2new = np.sum(ct2[indnew] * fd[indnew])
            cd3new = np.sum(ct3[indnew] * fd[indnew])
            ctprior = np.transpose(np.matrix([cd1new, cd2new, cd3new]))
        coeffprior_window = ctprior
        # if (np.min(coeffprior_window) < radiance_min_threshold): continue
        # if (np.max(coeffprior_window) > radiance_max_threshold): continue
        #
        # component_temperature_window = inv_planck(wl, coeffprior_window)
        # result_window[:, kk] = [component_temperature_window[0], component_temperature_window[1],
        #                         component_temperature_window[2]]
        ### 得到多像元+两角度 5*5窗口 的 组分温度
        component_temperature = inv_planck(wl, ctprior)
        #################################################
        ### second result by combining one-point result
        #################################################
        ### 第二个结果是单像元反演的结果
        ns1 = kk - off_inv2
        ns2 = kk + off_inv2 + 1
        # k22 = np.uint16(kk / 2)
        w1 = wNLine[:, 2, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,2, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        w3 = wALine[:,2, ns1:ns2]
        w3 = np.asarray(np.reshape(w3, (number_component, -1)))

        b1 = np.reshape(radNLine[2, ns1:ns2], -1)
        b2 = np.reshape(radOLine[2, ns1:ns2], -1)
        b3 = np.reshape(radAhiLine[2, ns1:ns2], -1)
        w = np.hstack((w1, w2, w3))
        b = np.hstack((b1, b2, b3))
        w = np.transpose(w)

        #################################################
        ### least-squared method
        #################################################
        # coeffprior_point = np.asarray(lstsq(w, b))[0]
        # if (np.min(coeffprior_point) < radiance_min_threshold): continue
        # if (np.max(coeffprior_point) > radiance_max_threshold): continue
        #
        # component_temperature_point = inv_planck(wl, coeffprior_point)
        # result_point[:, kk] = [component_temperature_point[0], component_temperature_point[1], component_temperature_point[2]]

        #################################################
        ### Bayes method
        #################################################

        w = np.matrix(w)
        b = np.matrix(b)
        b = np.transpose(b)

        ### Cd是实测和模拟观测的协方差阵，Cm是测量和先验辐射的方差阵
        Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
        Cm = np.diag([soil_radiance_variance, soil_radiance_variance, leaf_radiance_variance])

        pre = np.linalg.inv(w * Cm * np.transpose(w) + Cd)
        ### b为观测的
        coeff = ctprior + (Cm * np.transpose(w) * pre) * (b - w * ctprior)

        # coeff = ctprior + Cm * w.H * (
        #     lsqr(w * Cm * w.H + Cd, b - w * ctprior, iter_lim=400)[0]
        # )
        component_radiance = np.asarray(coeff)

        if (np.min(component_radiance) < radiance_min_threshold): continue
        if (np.max(component_radiance) > radiance_max_threshold): continue

        component_temperature = inv_planck(wl, component_radiance)
        # rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
        # temperature_soil = inv_planck(wl, rad_soil)

        result[:, kk] = [component_temperature[0], component_temperature[1], component_temperature[2]]

    # result[result < temperature_min_threshold] = default_nan_temperature
    # result[result > temperature_max_threshold] = default_nan_temperature
    #
    return result

def doMultiple_lsct3_inv(param):
    '''
    组分温度反演回归的中间件
    :param param:参数/变量
    :return: 组分温度结果
    '''
    return lsct3_inv((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]),param[6],param[7])

def inv_mpl_agl_multiple(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pg_n, pg_o, pg_ahi, wl=10.8):
    '''
    多角度，多像元的反演方法
    :param lst_n: 垂直方向
    :param lst_o: 倾斜方向
    :param lst_ahi: 静止方向
    :param emis_s: 发射率
    :param emis_v: 发射率
    :param fvcN: 覆盖度
    :param fvcO: 覆盖度
    :param fvcAhi: 覆盖度
    :param pg_n: 光照比例
    :param pg_o: 光照比例
    :param pg_ahi: 光照比例
    :param wl: 参考波长
    :return: 组分温度
    '''

    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    pure_soil_threshold = 0.05
    pure_leaf_threshold = 0.95
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    off_inv = 2  ## 反演的边界对应5*5
    off_avi = 2  ## 感兴趣点反演的宽度，有效数据缓冲区
    start = time.time()
    [nl, ns] = np.shape(lst_n)
    result = np.zeros([4, nl, ns])

    ######### FVC_NDVI
    # fvc_n = (ndvi_n - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    # fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold
    # fvc_o = (ndvi_o - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    # fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold
    # fvc_ahi = (ndvi_ahi - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    # fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ######### FVC LAI
    fvc_n = fvcN * 1.0
    fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold
    fvc_o = fvcO * 1.0
    fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold
    fvc_ahi = fvcAhi * 1.0
    fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ####### The radiance
    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

    rad_ahi = planck(wl,lst_ahi)
    # emisd2_v = resize_data(emis_v,nl/2,(ns+1)/2,method=cv2.INTER_NEAREST)
    # emisd2_s = resize_data(emis_s,nl/2,(ns+1)/2,method=cv2.INTER_NEAREST)
    # emisd2_v = resize_data_near(emis_v, nl / 2,  ns/ 2)
    # emisd2_s = resize_data_near(emis_s, nl / 2, ns / 2)
    emisd2_v = resize_data(emis_v, nl / 2, (ns + 1) / 2)
    emisd2_s = resize_data(emis_s, nl / 2, (ns + 1) / 2)
    fvc_ahi = resize_data(fvcAhi, nl / 2, (ns + 1) / 2)
    rad_ahiData = rad_ahi *(fvc_ahi*emisd2_v + (1-fvc_ahi)*emisd2_s)
    rad_ahi = resize_data(rad_ahiData, nl, ns,method=cv2.INTER_NEAREST)

    # component effective emissivity matrix
    wN = np.asarray([emis_s * (1 - fvc_n)*pg_n, emis_s * (1 - fvc_n)*(1-pg_n), emis_v * (fvc_n)])
    wO = np.asarray([emis_s * (1 - fvc_o)*pg_o, emis_s * (1 - fvc_o)*(1-pg_o), emis_v * (fvc_o)])

    pg_ahi = resize_data(pg_ahi,nl/2, (ns+1)/2,method=cv2.INTER_NEAREST)
    wAhiData= np.asarray([emisd2_s * (1 - fvc_ahi)*pg_ahi, emisd2_s * (1 - fvc_ahi)*(1-pg_ahi), emisd2_v * (fvc_ahi)])
    wAhi = np.asarray([resize_data(wAhiData[0], nl, ns,method=cv2.INTER_NEAREST),
                       resize_data(wAhiData[1],nl,ns,method=cv2.INTER_NEAREST),
                       resize_data(wAhiData[2],nl,ns,method=cv2.INTER_NEAREST)])

    mask = np.zeros([nl, ns])
    ind0 = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
          (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
          (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind0] = 1

    para = []
    for kn in range(off_inv, nl-off_inv):
        wNLine = wN[:,kn-off_inv:kn+off_inv+1,:]
        wOLine = wO[:,kn-off_inv:kn+off_inv+1,:]
        wALine = wAhi[:, kn - off_inv:kn + off_inv+1, :]
        radNLine = rad_n[kn-off_inv:kn+off_inv+1,:]
        radOLine = rad_o[kn - off_inv:kn + off_inv+1, :]
        radAhiLine = rad_ahi[kn - off_inv:kn + off_inv+1, :]
        maskLine = mask[kn-off_inv:kn+off_inv+1,:]
        para.append([wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine, ns])


    # doMultiple_line_inv(para[0])
    tasks = []
    pool = Pool(min(24, cpu_count()))
    for p in para:
        tasks.append(pool.apply_async(doMultiple_lsct3_inv, (p,)))
    pool.close()
    pool.join()
    results = [task.get() for task in tasks]
    end = time.time()
    results = np.asarray(results)
    ### for ns/nl consistent
    lsct = np.zeros([3,nl,ns])
    lsct[0,off_inv:-off_inv,:] = results[:,0,:]
    lsct[1,off_inv:-off_inv,:] = results[:,1,:]
    lsct[2,off_inv:-off_inv,:] = results[:,2,:]
    print('time cost: ', end - start, 's')
    return lsct

def inv_mpl_agl_multiple_msg(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pg_n, pg_o, pg_ahi, wl=10.8):
    '''
    多角度，多像元的反演方法
    :param lst_n: 垂直方向
    :param lst_o: 倾斜方向
    :param lst_ahi: 静止方向
    :param emis_s: 发射率
    :param emis_v: 发射率
    :param fvcN: 覆盖度
    :param fvcO: 覆盖度
    :param fvcAhi: 覆盖度
    :param pg_n: 光照比例
    :param pg_o: 光照比例
    :param pg_ahi: 光照比例
    :param wl: 参考波长
    :return: 组分温度
    '''

    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    pure_soil_threshold = 0.05
    pure_leaf_threshold = 0.95
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    off_inv = 2  ## 反演的边界对应5*5
    off_avi = 2  ## 感兴趣点反演的宽度，有效数据缓冲区
    start = time.time()
    [nl, ns] = np.shape(lst_n)
    result = np.zeros([4, nl, ns])

    ######### FVC_NDVI
    # fvc_n = (ndvi_n - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    # fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold
    # fvc_o = (ndvi_o - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    # fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold
    # fvc_ahi = (ndvi_ahi - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    # fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ######### FVC LAI
    fvc_n = fvcN * 1.0
    fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold
    fvc_o = fvcO * 1.0
    fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold
    fvc_ahi = fvcAhi * 1.0
    fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ####### The radiance
    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

    rad_ahi = planck(wl,lst_ahi)
    # emisd2_v = resize_data(emis_v,nl/2,(ns+1)/2,method=cv2.INTER_NEAREST)
    # emisd2_s = resize_data(emis_s,nl/2,(ns+1)/2,method=cv2.INTER_NEAREST)
    # emisd2_v = resize_data_near(emis_v, nl / 2,  ns/ 2)
    # emisd2_s = resize_data_near(emis_s, nl / 2, ns / 2)
    # emisd2_v = resize_data(emis_v, nl / 2, (ns + 1) / 2)
    # emisd2_s = resize_data(emis_s, nl / 2, (ns + 1) / 2)
    # fvc_ahi = resize_data(fvcAhi, nl / 2, (ns + 1) / 2)
    emisd2_s = emis_s
    emisd2_v = emis_v
    rad_ahiData = rad_ahi *(fvc_ahi*emisd2_v + (1-fvc_ahi)*emisd2_s)
    rad_ahi = resize_data(rad_ahiData, nl, ns,method=cv2.INTER_NEAREST)

    # component effective emissivity matrix
    wN = np.asarray([emis_s * (1 - fvc_n)*pg_n, emis_s * (1 - fvc_n)*(1-pg_n), emis_v * (fvc_n)])
    wO = np.asarray([emis_s * (1 - fvc_o)*pg_o, emis_s * (1 - fvc_o)*(1-pg_o), emis_v * (fvc_o)])

    # pg_ahi = resize_data(pg_ahi,nl/2, (ns+1)/2,method=cv2.INTER_NEAREST)
    wAhiData= np.asarray([emisd2_s * (1 - fvc_ahi)*pg_ahi, emisd2_s * (1 - fvc_ahi)*(1-pg_ahi), emisd2_v * (fvc_ahi)])
    wAhi = np.asarray([resize_data(wAhiData[0], nl, ns,method=cv2.INTER_NEAREST),
                       resize_data(wAhiData[1],nl,ns,method=cv2.INTER_NEAREST),
                       resize_data(wAhiData[2],nl,ns,method=cv2.INTER_NEAREST)])

    mask = np.zeros([nl, ns])
    ind0 = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
          (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
          (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind0] = 1

    para = []
    for kn in range(off_inv, nl-off_inv):
        wNLine = wN[:,kn-off_inv:kn+off_inv+1,:]
        wOLine = wO[:,kn-off_inv:kn+off_inv+1,:]
        wALine = wAhi[:, kn - off_inv:kn + off_inv+1, :]
        radNLine = rad_n[kn-off_inv:kn+off_inv+1,:]
        radOLine = rad_o[kn - off_inv:kn + off_inv+1, :]
        radAhiLine = rad_ahi[kn - off_inv:kn + off_inv+1, :]
        maskLine = mask[kn-off_inv:kn+off_inv+1,:]
        para.append([wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine, ns])


    # doMultiple_line_inv(para[0])
    tasks = []
    pool_ = Pool(min(24, cpu_count()))
    for p in para:
        tasks.append(pool_.apply_async(doMultiple_lsct3_inv, (p,)))
    pool_.close()
    pool_.join()
    results = [task.get() for task in tasks]
    end = time.time()
    results = np.asarray(results)
    ### for ns/nl consistent
    lsct = np.zeros([3,nl,ns])
    lsct[0,off_inv:-off_inv,:] = results[:,0,:]
    lsct[1,off_inv:-off_inv,:] = results[:,1,:]
    lsct[2,off_inv:-off_inv,:] = results[:,2,:]
    print('time cost: ', end - start, 's')
    return lsct

def inv_mpl_agl_station(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pg_n, pg_o, pg_ahi,imagex_,imagey_, wl=10.8):
    '''
    多角度，多像元的反演方法,这里近对站点数据进行处理
    :param lst_n: 垂直方向
    :param lst_o: 倾斜方向
    :param lst_ahi: 静止方向
    :param emis_s: 发射率
    :param emis_v: 发射率
    :param fvcN: 覆盖度
    :param fvcO: 覆盖度
    :param fvcAhi: 覆盖度
    :param pg_n: 光照比例
    :param pg_o: 光照比例
    :param pg_ahi: 光照比例
    :param wl: 参考波长
    :return: 组分温度
    '''
    number_component = 2
    number_observation = 3
    number_angle = 2
    number_value_threshold = 6
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.05  # 0.01-0.2 多角度反演的不准确性，越大越不可取，先验知识用的越多
    soil_radiance_variance = 2  # 1-10 与上类似，阴影土壤设小和叶片类
    leaf_radiance_variance = 1 # 0.5-5 叶片变化小一些 能接纳离散数据的能力
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    pure_soil_threshold = 0.05
    pure_leaf_threshold = 0.95
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    off_inv = 2  ## 反演的边界对应5*5
    off_avi = 2  ## 感兴趣点反演的宽度，有效数据缓冲区
    number_component = 3
    start = time.time()
    [nl, ns] = np.shape(lst_n)
    result = np.zeros([4, nl, ns])

    ######### FVC_NDVI
    # fvc_n = (ndvi_n - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    # fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold
    # fvc_o = (ndvi_o - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    # fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold
    # fvc_ahi = (ndvi_ahi - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    # fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ######### FVC LAI
    fvc_n = fvcN * 1.0
    fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold
    fvc_o = fvcO * 1.0
    fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold
    fvc_ahi = fvcAhi * 1.0
    fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ####### The radiance
    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

    rad_ahi = planck(wl,lst_ahi)
    emisd2_v = resize_data(emis_v,nl/2,(ns+1)/2,method=cv2.INTER_NEAREST)
    emisd2_s = resize_data(emis_s,nl/2,(ns+1)/2,method=cv2.INTER_NEAREST)
    # emisd2_v = resize_data_near(emis_v, nl / 2,  ns/ 2)
    # emisd2_s = resize_data_near(emis_s, nl / 2, ns / 2)
    rad_ahiData = rad_ahi *(fvc_ahi*emisd2_v + (1-fvc_ahi)*emisd2_s)
    rad_ahi = resize_data(rad_ahiData, nl, ns,method=cv2.INTER_NEAREST)

    # component effective emissivity matrix
    wN = np.asarray([emis_s * (1 - fvc_n)*pg_n, emis_s * (1 - fvc_n)*(1-pg_n), emis_v * (fvc_n)])
    wO = np.asarray([emis_s * (1 - fvc_o)*pg_o, emis_s * (1 - fvc_o)*(1-pg_o), emis_v * (fvc_o)])

    pg_ahi = resize_data(pg_ahi,nl/2, (ns+1)/2,method=cv2.INTER_NEAREST)
    wAhiData= np.asarray([emisd2_s * (1 - fvc_ahi)*pg_ahi, emisd2_s * (1 - fvc_ahi)*(1-pg_ahi), emisd2_v * (fvc_ahi)])
    wAhi = np.asarray([resize_data(wAhiData[0], nl, ns,method=cv2.INTER_NEAREST),
                       resize_data(wAhiData[1],nl,ns,method=cv2.INTER_NEAREST),
                       resize_data(wAhiData[2],nl,ns,method=cv2.INTER_NEAREST)])

    maskImage = np.zeros([nl, ns])
    ind0 = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
          (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
          (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    maskImage[ind0] = 1

    off_inv2 = 0
    n_station = np.size(imagex_)
    lsct = np.zeros([number_component,nl,ns])
    for k in range(n_station):

        kl0 = imagex_[k]
        ks0 = imagey_[k]
        maskk = maskImage[kl0,ks0]
        if maskk == 0: continue
        for kll in range(-off_avi,off_avi+1):
            for kss in range(-off_avi,off_avi+1):
                ks = ks0 + kss
                kl = kl0 + kll
                ns1 = ks0 + kss - off_inv
                ns2 = ks0 + kss + off_inv + 1
                nl1 = kl0 + kll - off_inv
                nl2 = kl0 + kll + off_inv + 1

                w1 = wN[:, nl1:nl2, ns1:ns2]
                w1 = np.asarray(np.reshape(w1, (number_component, -1)))
                w2 = wO[:, nl1:nl2, ns1:ns2]
                w2 = np.asarray(np.reshape(w2, (number_component, -1)))

                bb1 = (np.reshape(rad_n[nl1:nl2, ns1:ns2], -1))
                bb2 = (np.reshape(rad_o[nl1:nl2, ns1:ns2], -1))

                mask = np.reshape(maskImage[nl1:nl2, ns1:ns2], -1)
                ind = (mask == 1) * (np.isnan(w1[0, :]) == 0)

                num_val_point = np.sum(ind)
                if (num_val_point < number_value_threshold): continue

                ### w1 for nadir and w2 for oblique
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

                coeffprior = fitting_unknown_linear_sklearn(bb, ww, method='ridge')
                # print(kk)
                # coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]
                # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
                # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
                # ctprior = np.transpose(np.matrix([cd1, cd2]))

                ###############################################
                ### Bayes method with priori information
                ###############################################
                # bbb = sorted(b)
                # halfpoint = np.int(num_point / 2)
                # rleaf = np.average(bbb[0])
                # rsoil = np.average(bbb[1])
                # coeffprior = np.transpose(np.matrix([rsoil, 0, 0, 0, 0, 0, rleaf, 0, 0, 0, 0, 0]))
                # bb = np.transpose(np.matrix(bb))
                # ww = np.transpose(ww)
                # Cd = np.matrix(np.diag(np.ones(num_point * 2)) * Cdvaluep)
                # Cm = np.matrix(np.diag(np.ones(2 * part)))
                # Cm[0, 0] = 15.0
                # Cm[part, part] = 10.0
                # pre = np.linalg.inv(np.transpose(ww) * np.linalg.inv(Cd) * ww + np.linalg.inv(Cm))
                # ctprior = pre * (np.transpose(ww) * np.linalg.inv(Cd) * bb + np.linalg.inv(Cm) * coeffprior)

                #################################################
                ### first result without averaging information
                #################################################
                # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
                # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
                # ctprior = np.transpose(np.matrix([cd1, cd2]))

                ################################################
                ### first reult with averaing information
                ################################################
                offcenter = np.int(((2 * off_inv + 1) * (2 * off_inv + 1) - 1) / 2)
                fd = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
                fd = np.reshape(fd, -1) * 1.0

                coeffprior = np.asarray(coeffprior)
                ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
                ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
                ct3 = np.asarray([np.sum(coeffprior[2 * part:3 * part] * x[:part, j]) for j in range(25)])
                indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                         (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold) * \
                         (ct3 > radiance_min_threshold) * (ct3 < radiance_max_threshold)
                apoint = np.sum(indnew)
                if (apoint <= 1):
                    cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
                    cd2 = np.sum(coeffprior[part:2 * part] * x[:, offcenter])
                    cd3 = np.sum(coeffprior[2 * part:3 * part] * x[:, offcenter])
                    ctprior = np.transpose(np.matrix([cd1, cd2, cd3]))
                else:
                    fd[indnew] = fd[indnew] / np.sum(fd[indnew])

                    # inver-distance weight but not used
                    # bb0 = bb1[offcenter]
                    # fdnew = np.zeros(25)
                    # dismax = max(abs(bb1[indnew] - bb0))
                    # if dismax != 0:
                    #     fdnew[indnew] = 1.0 - abs(1.0 * bb1[indnew] - bb0) / dismax
                    # else:
                    #     fdnew[:] = 1
                    # fdnew[indnew] = fdnew[indnew] / np.sum(fdnew[indnew])
                    # fd[indnew] = (fdnew[indnew] * fd[indnew]) / np.sum(fdnew[indnew] * fd[indnew])

                    cd1new = np.sum(ct1[indnew] * fd[indnew])
                    cd2new = np.sum(ct2[indnew] * fd[indnew])
                    cd3new = np.sum(ct3[indnew] * fd[indnew])
                    ctprior = np.transpose(np.matrix([cd1new, cd2new, cd3new]))
                component_temperature = inv_planck(wl, ctprior)
                #################################################
                ### second result by combining one-point result
                #################################################

                ns1 = ks - off_inv2
                ns2 = ks + off_inv2 + 1
                nl1 = kl - off_inv2
                nl2 = kl + off_inv2 + 1
                # k22 = np.uint16(kk / 2)
                w1 = wN[:, nl1:nl2, ns1:ns2]
                w1 = np.asarray(np.reshape(w1, (number_component, -1)))
                w2 = wO[:,  nl1:nl2, ns1:ns2]
                w2 = np.asarray(np.reshape(w2, (number_component, -1)))
                w3 = wAhi[:,  nl1:nl2, ns1:ns2]
                w3 = np.asarray(np.reshape(w3, (number_component, -1)))

                b1 = np.reshape(rad_n[ nl1:nl2, ns1:ns2], -1)
                b2 = np.reshape(rad_o[ nl1:nl2, ns1:ns2], -1)
                b3 = np.reshape(rad_ahi[ nl1:nl2, ns1:ns2], -1)
                w = np.hstack((w1, w2, w3))
                b = np.hstack((b1, b2, b3))
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
                Cm = np.diag([soil_radiance_variance, soil_radiance_variance, leaf_radiance_variance])
                pre = np.linalg.inv(w * Cm * np.transpose(w) + Cd)
                coeff = ctprior + (Cm * np.transpose(w) * pre) * (b - w * ctprior)

                # coeff = ctprior + Cm * w.H * (
                #     lsqr(w * Cm * w.H + Cd, b - w * ctprior, iter_lim=400)[0]
                # )
                component_radiance = np.asarray(coeff)

                if (np.min(component_radiance) < radiance_min_threshold): continue
                if (np.max(component_radiance) > radiance_max_threshold): continue

                component_temperature = inv_planck(wl, component_radiance)
                # rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
                # temperature_soil = inv_planck(wl, rad_soil)

                lsct[:,kl,ks] = [component_temperature[0], component_temperature[1], component_temperature[2]]


    # doMultiple_line_inv(para[0])
    end = time.time()
    print('time cost: ', end - start, 's')
    return lsct


'''
反演2组分
'''

def lsct2_inv(wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine,ns = 1024):
    wl = 10.8
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.10
    number_component = 3
    number_angle = 3
    number_value_threshold = 12
    result = np.zeros([3, ns])

    ###
    off_inv = 2
    off_inv2 = 0

    for kk in range(off_inv, ns-off_inv):


        maskk = maskLine[2, kk]
        if maskk == 0: continue

        ns1 = kk - off_inv
        ns2 = kk + off_inv + 1

        w1 = wNLine[:,:, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,:, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))

        bb1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        bb2 = (np.reshape(radOLine[:, ns1:ns2], -1))



        mask = np.reshape(maskLine[:, ns1:ns2],-1)
        ind = (mask==1) * (np.isnan(w1[0,:])==0)

        num_val_point = np.sum(ind)
        if (num_val_point < number_value_threshold): continue

        ### w1 for nadir and w2 for oblique
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

        coeffprior = fitting_unknown_linear_sklearn(bb,ww,method='ridge')
        # print(kk)
        # coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ###############################################
        ### Bayes method with priori information
        ###############################################
        # bbb = sorted(b)
        # halfpoint = np.int(num_point / 2)
        # rleaf = np.average(bbb[0])
        # rsoil = np.average(bbb[1])
        # coeffprior = np.transpose(np.matrix([rsoil, 0, 0, 0, 0, 0, rleaf, 0, 0, 0, 0, 0]))
        # bb = np.transpose(np.matrix(bb))
        # ww = np.transpose(ww)
        # Cd = np.matrix(np.diag(np.ones(num_point * 2)) * Cdvaluep)
        # Cm = np.matrix(np.diag(np.ones(2 * part)))
        # Cm[0, 0] = 15.0
        # Cm[part, part] = 10.0
        # pre = np.linalg.inv(np.transpose(ww) * np.linalg.inv(Cd) * ww + np.linalg.inv(Cm))
        # ctprior = pre * (np.transpose(ww) * np.linalg.inv(Cd) * bb + np.linalg.inv(Cm) * coeffprior)

        #################################################
        ### first result without averaging information
        #################################################
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ################################################
        ### first reult with averaing information
        ################################################
        offcenter = np.int(((2 * off_inv + 1) * (2 * off_inv + 1) - 1) / 2)
        fd = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
        fd = np.reshape(fd, -1) * 1.0

        coeffprior = np.asarray(coeffprior)
        ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
        ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
        ct3 = np.asarray([np.sum(coeffprior[2 * part:3 * part] * x[:part, j]) for j in range(25)])
        indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                 (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold) * \
                 (ct3 > radiance_min_threshold) * (ct3 < radiance_max_threshold)
        apoint = np.sum(indnew)
        if (apoint <= 1):
            cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
            cd2 = np.sum(coeffprior[part:2 * part] * x[:, offcenter])
            cd3 = np.sum(coeffprior[2 * part:3 * part] * x[:, offcenter])
            ctprior = np.transpose(np.matrix([cd1, cd2, cd3]))
        else:
            fd[indnew] = fd[indnew] / np.sum(fd[indnew])

            # inver-distance weight but not used
            # bb0 = bb1[offcenter]
            # fdnew = np.zeros(25)
            # dismax = max(abs(bb1[indnew] - bb0))
            # if dismax != 0:
            #     fdnew[indnew] = 1.0 - abs(1.0 * bb1[indnew] - bb0) / dismax
            # else:
            #     fdnew[:] = 1
            # fdnew[indnew] = fdnew[indnew] / np.sum(fdnew[indnew])
            # fd[indnew] = (fdnew[indnew] * fd[indnew]) / np.sum(fdnew[indnew] * fd[indnew])

            cd1new = np.sum(ct1[indnew] * fd[indnew])
            cd2new = np.sum(ct2[indnew] * fd[indnew])
            cd3new = np.sum(ct3[indnew] * fd[indnew])
            ctprior = np.transpose(np.matrix([cd1new, cd2new, cd3new]))
        component_temperature = inv_planck(wl, ctprior)
        #################################################
        ### second result by combining one-point result
        #################################################

        ns1 = kk - off_inv2
        ns2 = kk + off_inv2 + 1
        # k22 = np.uint16(kk / 2)
        w1 = wNLine[:, 2, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,2, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        w3 = wALine[:,2, ns1:ns2]
        w3 = np.asarray(np.reshape(w3, (number_component, -1)))

        b1 = np.reshape(radNLine[2, ns1:ns2], -1)
        b2 = np.reshape(radOLine[2, ns1:ns2], -1)
        b3 = np.reshape(radAhiLine[2, ns1:ns2], -1)
        w = np.hstack((w1, w2, w3))
        b = np.hstack((b1, b2, b3))
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
        Cm = np.diag([soil_radiance_variance, soil_radiance_variance, leaf_radiance_variance])
        pre = np.linalg.inv(w * Cm * np.transpose(w) + Cd)
        coeff = ctprior + (Cm * np.transpose(w) * pre) * (b - w * ctprior)

        # coeff = ctprior + Cm * w.H * (
        #     lsqr(w * Cm * w.H + Cd, b - w * ctprior, iter_lim=400)[0]
        # )
        component_radiance = np.asarray(coeff)

        if (np.min(component_radiance) < radiance_min_threshold): continue
        if (np.max(component_radiance) > radiance_max_threshold): continue

        component_temperature = inv_planck(wl, component_radiance)
        # rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
        # temperature_soil = inv_planck(wl, rad_soil)

        result[:, kk] = [component_temperature[0], component_temperature[1], component_temperature[2]]

    # result[result < temperature_min_threshold] = default_nan_temperature
    # result[result > temperature_max_threshold] = default_nan_temperature

    return result

def doMultiple_lsct2_inv(param):
    '''
    组分温度反演回归的中间件
    :param param:参数/变量
    :return: 组分温度结果
    '''
    return lsct3_inv((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]),param[6],param[7])

def inv_mpl_agl_lsct2(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, wl=10.8):
    '''
    多角度，多像元的反演方法
    :param lst_n: 垂直方向
    :param lst_o: 倾斜方向
    :param lst_ahi: 静止方向
    :param emis_s: 发射率
    :param emis_v: 发射率
    :param fvcN: 覆盖度
    :param fvcO: 覆盖度
    :param fvcAhi: 覆盖度
    :param pg_n: 光照比例
    :param pg_o: 光照比例
    :param pg_ahi: 光照比例
    :param wl: 参考波长
    :return: 组分温度
    '''

    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    pure_soil_threshold = 0.05
    pure_leaf_threshold = 0.95
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    off_inv = 2  ## 反演的边界对应5*5
    off_avi = 2  ## 感兴趣点反演的宽度，有效数据缓冲区
    start = time.time()
    [nl, ns] = np.shape(lst_n)
    result = np.zeros([4, nl, ns])

    ######### FVC_NDVI
    # fvc_n = (ndvi_n - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    # fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold
    # fvc_o = (ndvi_o - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    # fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold
    # fvc_ahi = (ndvi_ahi - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    # fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ######### FVC LAI
    fvc_n = fvcN * 1.0
    fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold
    fvc_o = fvcO * 1.0
    fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold
    fvc_ahi = fvcAhi * 1.0
    fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ####### The radiance
    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

    rad_ahi = planck(wl,lst_ahi)
    emisd2_v = resize_data(emis_v,nl/2,(ns+1)/2,method=cv2.INTER_NEAREST)
    emisd2_s = resize_data(emis_s,nl/2,(ns+1)/2,method=cv2.INTER_NEAREST)
    # emisd2_v = resize_data_near(emis_v, nl / 2,  ns/ 2)
    # emisd2_s = resize_data_near(emis_s, nl / 2, ns / 2)
    rad_ahiData = rad_ahi *(fvc_ahi*emisd2_v + (1-fvc_ahi)*emisd2_s)
    rad_ahi = resize_data(rad_ahiData, nl, ns,method=cv2.INTER_NEAREST)

    # component effective emissivity matrix
    wN = np.asarray([emis_s * (1 - fvc_n),  emis_v * (fvc_n)])
    wO = np.asarray([emis_s * (1 - fvc_o),  emis_v * (fvc_o)])
    wAhiData= np.asarray([emisd2_s * (1 - fvc_ahi), emisd2_v * (fvc_ahi)])
    wAhi = np.asarray([resize_data(wAhiData[0], nl, ns,method=cv2.INTER_NEAREST),
                       resize_data(wAhiData[1],nl,ns,method=cv2.INTER_NEAREST)])

    mask = np.zeros([nl, ns])
    ind0 = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
          (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
          (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind0] = 1

    para = []
    for kn in range(off_inv, nl-off_inv):
        wNLine = wN[:,kn-off_inv:kn+off_inv+1,:]
        wOLine = wO[:,kn-off_inv:kn+off_inv+1,:]
        wALine = wAhi[:, kn - off_inv:kn + off_inv+1, :]
        radNLine = rad_n[kn-off_inv:kn+off_inv+1,:]
        radOLine = rad_o[kn - off_inv:kn + off_inv+1, :]
        radAhiLine = rad_ahi[kn - off_inv:kn + off_inv+1, :]
        maskLine = mask[kn-off_inv:kn+off_inv+1,:]
        para.append([wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine, ns])


    # doMultiple_line_inv(para[0])
    tasks = []
    pool = Pool(min(24, cpu_count()))
    for p in para:
        tasks.append(pool.apply_async(doMultiple_lsct3_inv, (p,)))
    pool.close()
    pool.join()
    results = [task.get() for task in tasks]
    end = time.time()
    results = np.asarray(results)
    ### for ns/nl consistent
    lsct = np.zeros([3,nl,ns])
    lsct[0,off_inv:-off_inv,:] = results[:,0,:]
    lsct[1,off_inv:-off_inv,:] = results[:,1,:]
    lsct[2,off_inv:-off_inv,:] = results[:,2,:]
    print('time cost: ', end - start, 's')
    return lsct

