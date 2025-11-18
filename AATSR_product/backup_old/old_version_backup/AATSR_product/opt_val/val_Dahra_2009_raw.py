import calendar
from utils.old.util import *
from datetime import datetime, timedelta

def cal_fvc_from_lai(thetav, lai):
    G = 0.5
    rd = np.pi / 180.0
    costhetanv = np.cos(thetav * rd)
    fvc = 1 - exp(-G * lai / costhetanv)
    fvc[fvc > 1] = 1
    fvc[fvc < 0] = 0
    return fvc

def cal_rmse_r2(data1,data2,tshred=10):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2

def write_float_array_to_txt_file(float_array, file_path,fmt='%.3f'):
    np.savetxt(file_path, float_array, fmt=fmt)

def read_txt_file(file_path):
    return np.loadtxt(file_path, dtype=float)

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
        w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
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


def SVD_bayesian(A,b,x0):
    '''基于贝叶斯理论的初值SVD分解'''
    U, s, VT = np.linalg.svd(A)
    V = VT.T
    s = np.diag(s)

    p0 = x0
    pm = np.asarray(lstsq(A, b, rcond=None))[0]
    # print(inv_planck(10.8,pm))
    # print(pm)

    temp1 = dot(V, np.linalg.inv((dot(s, s) + np.identity(s.shape[0]))))
    temp2 = dot(dot(dot(s, s), VT), pm) + dot(VT, x0)
    p = dot(temp1 ,temp2)
    # print(inv_planck(10.8,p))
    # print(p)

    # for i in range(times):
    #     temp1 = dot(V.T, np.linalg.inv((dot(s, s) + np.identity(s.shape[0]))))
    #     temp2 = dot(dot(s, U.T), b-dot(A,p)) + dot(V, p0-p)
    #     detap = dot(temp1,temp2)
    #     p = p+detap
    #     # print(i,inv_planck(10.8,p))
    #     print(p)
    return p


def SVD_bayesian_Truncated(A,b,x0,times):
    '''SVD分解'''
    U, s, V = np.linalg.svd(A)

    '''根据条件数判断留奇异值个数'''
    # print(s[0],s[1],s[2])
    s_sum = np.sum(s)
    s_add = 0
    k = 0
    while s_add/s_sum < 0.95:
        s_add = s_add + s[k]
        k=k+1
    # print("保留%01d个奇异值，前后条件数为%03f，%03f"%(k,s[0]/s[-1],s[0]/s[k-1]))
    if k<2: k=2

    U_ = np.matrix(U[:, :k])
    s_ = np.matrix(np.diag(s[0:k]))
    V_ = np.matrix(V[:k, :])
    A_ = U_ * s_ * V_

    # x_ = np.asarray(lstsq(A_, b, rcond=None))[0]
    p0 = x0
    pm = np.asarray(lstsq(A_, b, rcond=None))[0]

    temp1 = dot(V_.T, np.linalg.inv((dot(s_, s_) + np.identity(s_.shape[0]))))
    temp2 = dot(dot(dot(s_, s_), V_), pm) + dot(V_, x0)
    p = temp1 * temp2
    # print(p)
    # for i in range(times):
    #     temp1 = dot(V_.T, np.linalg.inv((dot(s_, s_) + np.identity(s_.shape[0]))))
    #     temp2 = dot(dot(s_, U_.T), b - A * p) + dot(V_, p0 - p)
    #     detap = temp1 * temp2
    #     p = p + detap
    #     print(i, p)
    return p

def SVD_bayesian_preconditioner(A,b,x0,times):
    '''SVD分解'''
    U, s, V = np.linalg.svd(A)

    '''根据条件数判断留奇异值个数'''
    # print(s[0],s[1],s[2])
    s_sum = np.sum(s)
    s_add = 0
    k = 0
    while s_add/s_sum < 0.95:
        s_add = s_add + s[k]
        k=k+1
    print("保留%01d个奇异值，前后条件数为%03f，%03f"%(k,s[0]/s[-1],s[0]/s[k-1]))

    U_ = np.matrix(U[:, :k])
    s_ = np.matrix(np.diag(s[0:k]))
    V_ = np.matrix(V[:k, :])
    A_ = U_ * s_ * V_

    # x_ = np.asarray(lstsq(A_, b, rcond=None))[0]
    p0 = x0
    pm = np.asarray(lstsq(A_, b, rcond=None))[0]
    print(inv_planck(10.8,pm))

    temp1 = dot(V_.T, np.linalg.inv((dot(s_, s_) + np.identity(s_.shape[0]))))
    temp2 = dot(dot(dot(s_, s_), V_), pm) + dot(V_, x0)
    p = temp1 * temp2
    # for i in range(times):
    #     temp1 = dot(V_.T, np.linalg.inv((dot(s_, s_) + np.identity(s_.shape[0]))))
    #     temp2 = dot(dot(s_, U_.T), b - A * p) + dot(V_, p0 - p)
    #     detap = temp1 * temp2
    #     p = p + detap
        # print(i, p)
    return p


def Tikhonov_regularization_iteration(A,b,x0,alpha,epoch):
    x_est = x0
    for i in range(epoch):
        # 计算更新方向
        ATA = np.dot(A.T, A)
        I = np.identity(ATA.shape[0])
        delta_x = np.dot(np.linalg.inv(ATA + alpha * I), np.dot(A.T, b - np.dot(A, x_est)))

        # 更新估计的解
        x_est += delta_x

        # 检查停止条件
        if np.linalg.norm(delta_x) < 1e-3:
            break
    return x_est



def inv_lsct2_angle2_station(lst_n,lst_o,w_n,w_o,imagex_,imagey_,methodname=0,wl=10.8):
    '''
    两角度（极轨2）反演组分温度
    :param lst_n: 垂直温度 nl*ns
    :param lst_o: 倾斜温度 nl*ns
    :param w_n: n方向上3组分的有效发射率矩阵 3*nl*ns
    :param w_o: o方向上3组分的有效发射率矩阵 3*nl*ns
    :param imagex_: 要反演的坐标x
    :param imagey_: 要反演的坐标y
    :param methodname: 最小二乘方法 0（简单最小二乘）\bayesianridge\ridge\lasso
    :param wl: 中心波长
    :return: LSCT
    '''
    '''温度转能量'''
    start = time.time()
    [nl, ns] = np.shape(lst_n)
    lsct = np.zeros(2)

    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (w_n[0,:,:] + w_n[1,:,:])
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (w_o[0,:,:] + w_o[1,:,:])

    '''掩膜（判断像元能否反演）'''
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    maskImage = np.zeros([nl, ns])
    ind0 = (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
           (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    maskImage[ind0] = 1

    '''逐点开始反演'''
    n_station = np.size(imagex_)
    for k in range(n_station):
        kl0 = imagex_[k]
        ks0 = imagey_[k]
        if maskImage[kl0,ks0] == 0:
            print("when retrieving lsct, LST out of range.")
            continue

        '''两角度反演两组分'''
        w_n_ = np.reshape(w_n[:,imagex_, imagey_],(1,2))  # 1*2
        w_o_ = np.reshape(w_o[:,imagex_, imagey_],(1,2))
        b_n_ = np.reshape(rad_n[imagex_,imagey_],(1,1))   # 1*1
        b_o_ = np.reshape(rad_o[imagex_,imagey_],(1,1))

        w = np.vstack((w_n_,w_o_))  # 2*3
        b = np.vstack((b_n_,b_o_))  # 2*1

        '''反演方法选择'''
        x0 = np.array([planck(wl, np.array([310])), planck(wl, np.array([308]))]).reshape([2, 1])

        if methodname == 0:
            coeff = np.asarray(lstsq(w, b, rcond=None))[0]
        elif methodname == 'SVD_bayesian_Truncated':
            times = 10
            print('x0:' + str(inv_planck(wl, x0)))
            coeff = SVD_bayesian_Truncated(w, b, x0, times)
        elif methodname == "Tikhonov_regularization_iteration":
            times = 100
            alpha = 10
            coeff = Tikhonov_regularization_iteration(w,b,x0,alpha,times)
        elif methodname == "multi pixel":
            off_avi = 2
            off_inv = 2
            number_component =2
            number_value_threshold = 6
            for kll in range(-off_avi, off_avi + 1):
                for kss in range(-off_avi, off_avi + 1):
                    # ks,kl是站点附近5*5区域内点的遍历
                    ks = ks0 + kss
                    kl = kl0 + kll
                    # ns1-ns2;nl1-nl2是被遍历的点的5*5区域
                    ns1 = ks0 + kss - off_inv
                    ns2 = ks0 + kss + off_inv + 1
                    nl1 = kl0 + kll - off_inv
                    nl2 = kl0 + kll + off_inv + 1

                    '''多像元法计算初值'''
                    w1 = w_n[:, nl1:nl2, ns1:ns2]
                    w1 = np.asarray(np.reshape(w1, (number_component, -1)))
                    w2 = w_o[:, nl1:nl2, ns1:ns2]
                    w2 = np.asarray(np.reshape(w2, (number_component, -1)))

                    bb1 = (np.reshape(rad_n[nl1:nl2, ns1:ns2], -1))
                    bb2 = (np.reshape(rad_o[nl1:nl2, ns1:ns2], -1))

                    mask = np.reshape(maskImage[nl1:nl2, ns1:ns2], -1)
                    ind = (mask == 1) * (np.isnan(w1[0, :]) == 0)

                    # number_value_threshold=6，如果5*5=25个点中符合条件的点小于六个就退出
                    num_val_point = np.sum(ind)
                    if (num_val_point < number_value_threshold): continue

                    ### w1 for nadir and w2 for oblique
                    ns_temp = np.asarray(
                        [-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
                    nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
                    part = 6

                    n0 = np.ones(len(ns_temp))
                    x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
                    w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
                    w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

                    ww = np.hstack((w11[:, ind], w22[:, ind]))
                    bb = np.hstack((bb1[ind], bb2[ind]))

                    # 这一步目的是计算一个初值，解为3（组分）*6（系数） = 18个
                    ww = np.transpose(ww)
                    # 解方程方法
                    coeffprior = fitting_unknown_linear_sklearn(bb, ww, method="bayesianridge")
                    # coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]

                    ################################################
                    ### first reult with averaing information
                    ################################################
                    offcenter = np.int(((2 * off_inv + 1) * (2 * off_inv + 1) - 1) / 2)
                    fd = np.asarray(
                        [[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
                    fd = np.reshape(fd, -1) * 1.0

                    coeffprior = np.asarray(coeffprior)
                    ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
                    ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
                    indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                             (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold)
                    apoint = np.sum(indnew)
                    if (apoint <= 1):
                        cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
                        cd2 = np.sum(coeffprior[part:2 * part] * x[:, offcenter])
                        ctprior = np.transpose(np.matrix([cd1, cd2]))
                    else:
                        fd[indnew] = fd[indnew] / np.sum(fd[indnew])

                        cd1new = np.sum(ct1[indnew] * fd[indnew])
                        cd2new = np.sum(ct2[indnew] * fd[indnew])
                        ctprior = np.transpose(np.matrix([cd1new, cd2new]))
                    component_temperature = inv_planck(wl, ctprior)
                    coeff = ctprior
        else:
            coeff = fitting_unknown_linear_sklearn(b, w, method=methodname)
        lsct = inv_planck(wl, coeff)
    end = time.time()
    print('time cost: ', end - start, 's')
    return lsct


'''直接从tif图获得邻域信息'''
indir_type = r'D:\data\type\\'
indir_tif = r'E:\AATSR\2009\tif\\'
indir_lst = r'E:\AATSR\2009\lst\\'
indir_lsct = r'E:\AATSR\2009\lsct\\'
indir_lai = r'E:\AATSR\lai\2009\\'
oudir_composite = r'E:\AATSR\2009\lsct_day\\'
outdir = r'E:\AATSR\2009\Dahra\\'
infile_emis = r'D:\data\emis\\AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
outfile = r'E:\AATSR\2009\Dahra_retrieve.txt'
file_path = 'D:\data\LSCT_Validation\Dahra_2009\Dahra_LST.xlsx'

get_from_raw = 0
get_ERA5 = 0
if_inv = 0
if_val = 1

if get_from_raw:
    '''根据坐标找图上坐标'''
    lat_ = np.asarray([15.402])
    lon_ = np.asarray([-15.443])
    type_dir_1000 = indir_type + 'type_world_1000.tif'
    type, ns, nl, nb, geog, proj, dataset = read_image_dataset_gdal(type_dir_1000)
    imagex_, imagey_ = loc2map(lat_, lon_, dataset)
    emis_s, ns_, nl_, nb_, geog_, proj_, dataset_ = read_image_dataset_gdal(infile_emis)

    '''找图上点'''
    year = 2009
    doy_ = []
    time_ = []
    lsct_s_ = []
    lsct_v_ = []
    lst_n_ = []
    lst_f_ = []
    size = 7 # 提取7*7窗口
    for month in range(7,12):
        daynum = calendar.monthrange(year,month)[1]
        for d in range(daynum):
            day = d + 1
            print(year, month, day)
            indir_tif_day = indir_tif +  '%02d' % int(month) + "//" + '%02d' % int(day) + "//"
            indir_lst_day = indir_lst +  '%02d' % int(month) + "//" + '%02d' % int(day) + "//"
            indir_lsct_day = indir_lsct +  '%02d' % int(month) + "//" + '%02d' % int(day) + "//"
            if not os.path.exists(indir_tif_day): continue
            fileNames = search_file_rej(indir_tif_day,['indx'],'enp')
            for fileName in fileNames:
                print(fileName)
                infile = indir_tif_day + fileName[:-8]
                infile_indx = indir_tif_day + fileName[:-8] + "indx.tif"
                infile_indy = indir_tif_day + fileName[:-8] + "indy.tif"
                infile_vza_n = indir_tif_day + fileName[:-8] + "vza_n.tif"
                infile_vza_f = indir_tif_day + fileName[:-8] + "vza_f.tif"
                infile_lstN = indir_lst_day + fileName[:-8] + "lst_n.tif"
                infile_lstF = indir_lst_day + fileName[:-8] + "lst_f.tif"
                infile_lsct = indir_lsct_day + fileName[:-8] + "_lsct.tif"

                if not (os.path.exists(infile_indx) and os.path.exists(infile_indy)):
                    continue

                '''过滤时间'''
                hour = int(fileName[-15:-13])
                doy =int(fileName[-19:-16])
                month,day = doy2date(2009,doy)
                # print(month,day)
                if hour <= 8 or hour >= 13:
                    continue
                # if doy!= 290:
                #     continue

                '''提中心点'''
                [indx, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_indx)
                [indy, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_indy)
                ind = (indx==imagex_)*(indy==imagey_)
                if np.sum(ind)==0:
                    continue

                '''读取数据'''
                [vzaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vza_n)
                [vzaF, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vza_f)
                [lsct, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lsct)
                vzaN = 90 - (vzaN / 100)
                vzaF = 90 - (vzaF / 100)
                lsct_s = np.reshape(lsct[0,:,:],(lsct.shape[1],-1))
                lsct_v = np.reshape(lsct[1,:,:],(lsct.shape[1],-1))
                [lstN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lstN)
                [lstF, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lstF)

                '''需要保存相应的两个lst，两个lsct，一个time，一个lai'''
                outdir_day = outdir + "%03d//" %doy
                mkdir_if_not_exist(outdir_day)
                out_lstN = outdir_day + fileName[:-8] + "lst_n.txt"
                out_lstF = outdir_day + fileName[:-8] + "lst_f.txt"
                out_vzaN = outdir_day + fileName[:-8] + "vza_n.txt"
                out_vzaF = outdir_day + fileName[:-8] + "vza_f.txt"
                out_lsct_s = outdir_day + fileName[:-8] + "lsct_s.txt"
                out_lsct_v = outdir_day + fileName[:-8] + "lsct_v.txt"

                out_emis =  outdir_day + fileName[:-8] + "emis.txt"
                out_lai =  outdir_day + fileName[:-8] + "lai.txt"

                lsct_s_ = np.zeros([size,size])
                lsct_v_ = np.zeros_like(lsct_s_)
                lst_n_ = np.zeros_like(lsct_s_)
                lst_f_ = np.zeros_like(lsct_s_)
                vza_n_ = np.zeros_like(lsct_s_)
                vza_f_ = np.zeros_like(lsct_s_)

                off = int(size/2)
                for i in range(-off,off+1):
                    for j in range(-off,off+1):
                        # print(i,j)
                        ind = (indx == imagex_ + i) * (indy == imagey_ + i)
                        if np.sum(ind)==0:
                            lsct_s_[i+off,j+off]=0
                            lsct_v_[i + off, j + off] = 0
                            lst_n_[i + off, j + off] = 0
                            lst_f_[i + off, j + off] = 0
                            vza_n_[i + off, j + off] = 0
                            vza_f_[i + off, j + off] = 0
                        else:
                            lsct_s_[i + off, j + off] = np.average(lsct_s[ind])
                            lsct_v_[i + off, j + off] = np.average(lsct_v[ind])
                            lst_n_[i + off, j + off] = np.average(lstN[ind])
                            lst_f_[i + off, j + off] = np.average(lstF[ind])
                            vza_n_[i + off, j + off] = np.average(vzaN[ind])
                            vza_f_[i + off, j + off] = np.average(vzaF[ind])

                print(lsct_s_)
                write_float_array_to_txt_file(lsct_s_,out_lsct_s)
                write_float_array_to_txt_file(lsct_v_, out_lsct_v)
                write_float_array_to_txt_file(lst_n_/100, out_lstN)
                write_float_array_to_txt_file(lst_f_/100, out_lstF)
                write_float_array_to_txt_file(vza_n_, out_vzaN)
                write_float_array_to_txt_file(vza_f_, out_vzaF)


                '''保存其他信息'''
                '''时间'''
                time_delta = timedelta(seconds=6528)
                year_str = fileName[6:10]
                doy_str = fileName[11:14]
                time_str = fileName[15:21]
                month, day = doy2date(int(year_str), int(doy_str))
                time_start = datetime(int(year_str), month, day, int(time_str[0:2]), int(time_str[2:4]),
                                      int(time_str[4:6]))
                sec_num_start = int(time_str[0:2]) * 3600 + int(time_str[2:4]) * 60 + int(time_str[4:6])
                total_columns = temp2
                sec_interval = 6528 / (total_columns - 1)
                time_array = np.array(
                    [sec_num_start + i * sec_interval for i in range(total_columns)])
                sec_save = np.transpose(np.array([time_array] * 512))
                ind = (indx==imagex_)*(indy==imagey_)
                time_ = np.average(sec_save[ind])

                '''植被类型，土壤发射率和植被发射率'''
                type_ = type[imagex_,imagey_]
                emis_s_ = emis_s[imagex_,imagey_]
                infile_veg_emis = r'D:\data\base\\' + 'IGBP_Emi.txt'
                emis_v_ = read_txt_array(infile_veg_emis, 0, 2)
                emis_v_ = emis_v_[type_, 0] / 1000

                '''LAI'''
                doy1 = (doy // 4) * 4 + 1
                doy2 = (doy // 4) * 4 + 5
                infile_lai1 = indir_lai + r"MuSyQ.CSC.LAI.A" + '%04d%03d' % (int(year), doy1) + '.tif'
                infile_lai2 = indir_lai + r"MuSyQ.CSC.LAI.A" + '%04d%03d' % (int(year), doy2) + '.tif'
                if not os.path.exists(infile_lai2): infile_lai2 = infile_lai1
                [lai1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai1)
                [lai2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai2)
                lai = (1 - (doy - doy1) / 4) * lai1 + (doy - doy1) / 4 * lai2
                lai = np.reshape(lai, [nl, ns])
                lai[lai >= 30000] = 0
                lai = lai / 1000
                imagex = int(imagex_)
                imagey = int(imagey_)
                lai_ =  np.array(lai[imagex-off:imagex+off+1,imagey-off:imagey+off+1])

                other = np.array([time_,type_,emis_s_/1000,emis_v_])
                write_float_array_to_txt_file(other, out_emis,'%.6f')

                write_float_array_to_txt_file(lai_, out_lai,'%.3f')

if get_ERA5:
    '''根据坐标找图上坐标'''
    lat_ = np.asarray([15.402])
    lon_ = np.asarray([-15.443])
    indir_st1 = r"E:\AATSR\st1\2009\raw\\"
    indir_ta2 = r"E:\AATSR\ta2\2009\raw\\"
    st1_ = []
    ta2_ = []
    for doy in range(180,360):
        print(doy)
        indir_day = outdir + "%03d//" %doy
        if not os.path.exists(indir_day): continue

        month,day = doy2date(2009,doy)
        infile_st1 = indir_st1 +  r"ERA5_single-level_2009%02d%02d.nc" %(month,day)
        infile_ta2 = indir_ta2 +  r"ERA5_single-level_2009%02d%02d.nc" %(month,day)

        '''st1'''
        fileName = infile_st1
        stl1 = read_image_Nc(fileName, 'stl1', 1)

        fileName = infile_ta2
        ta2 = read_image_Nc(fileName, 't2m', 1)
        print(stl1[11, 298, 1378],ta2[11, 298, 1378])


        st1_.append(stl1[11, 298, 1378])
        ta2_.append(ta2[11, 298, 1378])
        out_era5 = indir_day + "era5.txt"
        write_float_array_to_txt_file([stl1[11, 298, 1378],ta2[11, 298, 1378]], out_era5, '%.3f')


if if_inv:
    for doy in range(180,360):
        indir_day = outdir + "%03d//" %doy
        if not os.path.exists(indir_day): continue

        fileName = search_file(indir_day,['emis.txt'])[0]

        '''文件地址'''
        in_lstN = indir_day + fileName[:-8] + "lst_n.txt"
        in_lstF = indir_day + fileName[:-8] + "lst_f.txt"
        in_vzaN = indir_day + fileName[:-8] + "vza_n.txt"
        in_vzaF = indir_day + fileName[:-8] + "vza_f.txt"
        in_lsct_s = indir_day + fileName[:-8] + "lsct_s.txt"
        in_lsct_v = indir_day + fileName[:-8] + "lsct_v.txt"
        in_emis = indir_day + fileName[:-8] + "emis.txt"
        in_lai = indir_day + fileName[:-8] + "lai.txt"

        '''读取数据'''
        vzaN = read_txt_file(in_vzaN)
        vzaF = read_txt_file(in_vzaF)
        lai = read_txt_file(in_lai)
        lstN = read_txt_file(in_lstN)
        lstF = read_txt_file(in_lstF)
        sec_num,type,emis_s,emis_v = read_txt_file(in_emis)
        print(sec_num)
        hour_ = sec_num // 3600
        min_ = (sec_num - 3600 * hour_) // 60
        sec_ = sec_num % 60
        year = 2009
        print(year,doy,int(hour_),int(min_),int(sec_))

        lsct_s = read_txt_file(in_lsct_s)
        lsct_v = read_txt_file(in_lsct_v)

        '''计算FVC'''
        fvc_n = cal_fvc_from_lai(vzaN, lai)
        fvc_f = cal_fvc_from_lai(vzaF, lai)
        fvc_n[fvc_n > 1] = 1
        fvc_n[fvc_n < 0] = 0
        fvc_f[fvc_f > 1] = 1
        fvc_f[fvc_f < 0] = 0

        '''反演lsct'''
        wN =  np.asarray([(1 - fvc_n) * emis_s , emis_v * fvc_n])
        wO =  np.asarray([(1 - fvc_f) * emis_s , emis_v * fvc_f])

        wl = 10.8
        rad_n = planck(wl, lstN)
        rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
        rad_o = planck(wl, lstF)
        rad_o = rad_o * (fvc_f * emis_v + (1 - fvc_f) * emis_s)

        ind0 =  np.ones_like(rad_n)

        '''5*5'''
        if rad_n.shape[0] == 5:
            lsct = line_inv_2_s(wN,wO,rad_n,rad_o,ind0,5)
            lsct_s = lsct[0,2]
            lsct_v = lsct[1,2]
            print(lsct_s,lsct_v)
        elif rad_n.shape[0] == 7:
            lsct_s = np.zeros([7,7])
            lsct_v = np.zeros([7,7])
            for i in range(3):
                lsct = line_inv_2_s(wN[:,:,i:i+5],wO[:,:,i:i+5],rad_n[:,i:i+5],rad_o[:,i:i+5],ind0[:,i:i+5],7)
                lsct_s[:,i+2] = np.reshape(lsct[0,:],(7))
                lsct_v[:,i+2] = np.reshape(lsct[1,:],(7))
            out_lsct_s = indir_day + fileName[:-8] + "lsct_s_B.txt"
            out_lsct_v = indir_day + fileName[:-8] + "lsct_v_B.txt"
            write_float_array_to_txt_file(lsct_s, out_lsct_s, '%.3f')
            write_float_array_to_txt_file(lsct_v, out_lsct_v, '%.3f')

        '''Truncated SVD'''
        lsct_s = np.zeros([7,7])
        lsct_v = np.zeros_like(lsct_s)
        for imagex in range(7):
            for imagey in range(7):
                lsct_s[imagex,imagey],lsct_v[imagex,imagey] = inv_lsct2_angle2_station(lstN,lstF,wN,wO,[imagex],[imagey],methodname="SVD_bayesian_Truncated")
        out_lsct_s = indir_day + fileName[:-8] + "lsct_s_S.txt"
        out_lsct_v = indir_day + fileName[:-8] + "lsct_v_S.txt"
        write_float_array_to_txt_file(lsct_s, out_lsct_s, '%.3f')
        write_float_array_to_txt_file(lsct_v, out_lsct_v, '%.3f')


if if_val:
    '''验证数据'''
    file_path = 'D:\data\LSCT_Validation\Dahra_2009\Dahra_LST.xlsx'
    df = pd.read_excel(file_path)
    df = df.dropna()
    df['Time'] = pd.to_datetime(df['Time'])
    time_mea = []
    lsct_s_mea = []
    lsct_v_mea = []
    lsct_s_inv = []
    lsct_v_inv = []
    doy_ = []
    lstN_ = []
    lstF_ = []
    ts1_ = []
    t2m_ = []

    for doy in range(180,360):
        indir_day = outdir + "%03d//" %doy
        if not os.path.exists(indir_day): continue

        fileName = search_file(indir_day,['emis.txt'])[0]
        in_emis = indir_day + fileName[:-8] + "emis.txt"
        sec_num, type, emis_s, emis_v = read_txt_file(in_emis)
        # print(sec_num)
        hour_ = sec_num // 3600
        min_ = (sec_num - 3600 * hour_) // 60
        sec_ = sec_num % 60
        year = 2009
        # print(year, doy, int(hour_), int(min_), int(sec_))
        month,day = doy2date(year,doy)
        doy_.append(doy)

        '''lst'''
        in_lst_n = indir_day + fileName[:-8] + "lst_n.txt"
        in_lst_f = indir_day + fileName[:-8] + "lst_f.txt"
        lst_n = read_txt_file(in_lst_n)
        lst_f = read_txt_file(in_lst_f)
        lstN_.append(lst_n[3,3])
        lstF_.append(lst_f[3,3])

        '''原始结果'''
        in_lsct_s = indir_day + fileName[:-8] + "lsct_s.txt"
        in_lsct_v = indir_day + fileName[:-8] + "lsct_v.txt"
        '''贝叶斯结果'''
        in_lsct_s_B = indir_day + fileName[:-8] + "lsct_s_B.txt"
        in_lsct_v_B = indir_day + fileName[:-8] + "lsct_v_B.txt"
        '''SVD结果'''
        in_lsct_s_S = indir_day + fileName[:-8] + "lsct_s_S.txt"
        in_lsct_v_S = indir_day + fileName[:-8] + "lsct_v_S.txt"

        lsct_s = read_txt_file(in_lsct_s_S)
        lsct_v = read_txt_file(in_lsct_v_S)

        lsct_s_inv.append(lsct_s[3,3])
        lsct_v_inv.append(lsct_v[3,3])

        '''ERA5'''
        in_era5 = indir_day +  "era5.txt"
        ts1,t2m = read_txt_file(in_era5)
        ts1_.append(ts1)
        t2m_.append(t2m)

        '''找观测数据'''
        search_time = datetime(year, month, day, int(hour_), int(min_), int(sec_))
        filtered_data = df[(df['Time'] >= search_time - pd.Timedelta(minutes=7.5)) & (
                    df['Time'] <= search_time + pd.Timedelta(minutes=7.5))]
        if filtered_data.empty:
            time_mea.append(0)
            lsct_s_mea.append(0)
            lsct_v_mea.append(0)
        else:
            time_mea.append(filtered_data['Time'].iloc[0])
            lsct_s_mea.append(filtered_data['Tg'].iloc[0] + 273.15)
            lsct_v_mea.append(filtered_data['Tc'].iloc[0] + 273.15)

    '''剔除异常值'''
    tep_min = 240
    tep_max = 350
    lsct_s_inv = np.array(lsct_s_inv)
    lsct_v_inv = np.array(lsct_v_inv)
    lsct_s_mea = np.array(lsct_s_mea)
    lsct_v_mea = np.array(lsct_v_mea)
    ts1_ = np.array(ts1_)
    t2m_ = np.array(t2m_)

    ind = (lsct_s_inv > tep_min) * (lsct_s_inv < tep_max) * (lsct_v_inv > tep_min) * (lsct_s_inv < tep_max) * (
                np.array(lsct_v_mea) > tep_min)* (np.abs(lsct_s_inv - lsct_s_mea)<15)

    '''验证并作图'''
    plt.rc('font', family='Times New Roman')
    print("Dahra")
    dif_threshold = 10
    ts_mea, tc_mea, ts_inv, tc_inv = np.array(lsct_s_mea), np.array(lsct_v_mea), lsct_s_inv, lsct_v_inv
    bias_tss, rmse_tss, r2_tss = cal_rmse_r2(ts_mea[ind], ts_inv[ind], dif_threshold)
    bias_tc, rmse_tc, r2_tc = cal_rmse_r2(tc_mea[ind], tc_inv[ind], dif_threshold)
    i = np.abs(ts_mea[ind]-ts_inv[ind])<10
    print("num:%02d"%np.sum(i))
    mea = np.stack([ts_mea[ind], tc_mea[ind]])
    inv = np.stack([ts_inv[ind], tc_inv[ind]])
    bias_all, rmse_all, r2_all = cal_rmse_r2(mea, inv, dif_threshold)
    print("bias:%.2f,%.2f,%.2f" % (bias_tss, bias_tc, bias_all))
    print("r2:%.3f,%.3f,%.3f" % (r2_tss[0], r2_tc[0], r2_all[0]))
    print("rmse:%.2f,%.2f,%.2f" % (rmse_tss, rmse_tc, rmse_all))

    plt.figure(figsize=[4.5, 4], dpi=300)
    plt.plot(ts_mea[ind], ts_inv[ind], 'ro')
    # plt.plot(tsh_forest_mea[ind],tsh_forest_inv[ind],'bo')
    plt.plot(tc_mea[ind], tc_inv[ind], 'go')
    plt.xlim([290, 330])
    plt.ylim([290, 330])
    plt.plot([290, 330], [290, 330], 'k--')
    plt.xlabel('Measured Temperature/K')
    plt.ylabel('Inverted Temperature/K')
    plt.legend(['Soil', 'Canopy'])
    plt.title('Dahra')
    plt.show()

    '''ERA5 验证'''
    print("Dahra")
    dif_threshold = 10
    ts_mea, tc_mea, ts_era, tc_era = np.array(lsct_s_mea), np.array(lsct_v_mea), ts1_, t2m_
    bias_tss, rmse_tss, r2_tss = cal_rmse_r2(ts_mea[ind], ts_era[ind], dif_threshold)
    bias_tc, rmse_tc, r2_tc = cal_rmse_r2(tc_mea[ind], tc_era[ind], dif_threshold)
    i = np.abs(ts_mea[ind] - ts_era[ind]) < 10
    print("num:%02d" % np.sum(i))
    mea = np.stack([ts_mea[ind], tc_mea[ind]])
    era = np.stack([ts_era[ind], tc_era[ind]])
    bias_all, rmse_all, r2_all = cal_rmse_r2(mea, era, dif_threshold)
    print("bias:%.2f,%.2f,%.2f" % (bias_tss, bias_tc, bias_all))
    print("r2:%.3f,%.3f,%.3f" % (r2_tss[0], r2_tc[0], r2_all[0]))
    print("rmse:%.2f,%.2f,%.2f" % (rmse_tss, rmse_tc, rmse_all))

    plt.figure(figsize=[4.5, 4], dpi=300)
    plt.plot(ts_mea[ind], ts_era[ind], 'ro')
    # plt.plot(tsh_forest_mea[ind],tsh_forest_inv[ind],'bo')
    plt.plot(tc_mea[ind], tc_era[ind], 'go')
    plt.xlim([290, 330])
    plt.ylim([290, 330])
    plt.plot([290, 330], [290, 330], 'k--')
    plt.xlabel('Measured Temperature/K')
    plt.ylabel('ERA5 Temperature/K')
    plt.legend(['Soil', 'Canopy'])
    plt.title('Dahra')
    plt.show()


    '''时序图'''
    doy_ = np.array(doy_)
    lstN_ = np.array(lstN_)
    lstF_ = np.array(lstF_)
    # plt.plot(doy_[ind], ts_mea[ind], 'r.')
    # plt.plot(doy_[ind], tc_mea[ind], 'g.')
    # plt.plot(doy_[ind], ts_era[ind], color='orange')
    # # plt.plot(doy_[ind], tc_era[ind], 'b.')
    # # plt.plot(doy_[ind],lstN_[ind],'orange')
    # # plt.plot(doy_[ind],lstF_[ind],'b')
    # plt.plot(doy_[ind], ts_inv[ind], 'r')
    # plt.plot(doy_[ind], tc_inv[ind], 'g')
    # plt.legend(['Ts_mea', 'Tc_mea','Ts_era', 'Ts_inv', 'Tc_inv'])
    # plt.xlabel('DOY')
    # plt.ylabel('Measured Temperature/K')
    # plt.title('Measurement')
    # plt.ylim([290, 325])
    # plt.show()
    confidence_interval_width = 3
    plt.plot(doy_[ind], ts_mea[ind], 'r.')
    plt.plot(doy_[ind], tc_mea[ind], 'g.')
    plt.plot(doy_[ind], ts_era[ind], color='orange')
    plt.plot(doy_[ind], ts_inv[ind], 'r')
    plt.plot(doy_[ind], tc_inv[ind], 'g')

    # 计算样本平均值和标准差
    data = ts_inv[ind]
    mean_value = np.mean(data)
    std_dev = np.std(data, ddof=1)  # 使用样本标准差，自由度为 n-1
    # 设置置信水平和计算置信区间
    confidence_level = 0.95  # 例如，95% 的置信水平
    alpha = 1 - confidence_level
    z_score = stats.norm.ppf(1 - alpha / 2)  # 对于正态分布的 Z 分数
    # 计算置信区间
    margin_of_error_s = z_score * (std_dev / np.sqrt(len(data)))
    print(margin_of_error_s)

    # 计算样本平均值和标准差
    data = tc_inv[ind]
    mean_value = np.mean(data)
    std_dev = np.std(data, ddof=1)  # 使用样本标准差，自由度为 n-1
    # 设置置信水平和计算置信区间
    confidence_level = 0.95  # 例如，95% 的置信水平
    alpha = 1 - confidence_level
    z_score = stats.norm.ppf(1 - alpha / 2)  # 对于正态分布的 Z 分数
    # 计算置信区间
    margin_of_error_c = z_score * (std_dev / np.sqrt(len(data)))
    print(margin_of_error_c)

    # Confidence intervals
    plt.fill_between(doy_[ind], ts_inv[ind] - margin_of_error_s, ts_inv[ind] + margin_of_error_s,
                     color='lightcoral', alpha=0.3)
    plt.fill_between(doy_[ind], tc_inv[ind] - margin_of_error_c, tc_inv[ind] + margin_of_error_c,
                     color='lightgreen', alpha=0.3)

    plt.legend(['Ts_mea', 'Tc_mea', 'Ts_era', 'Ts_inv', 'Tc_inv'])
    plt.xlabel('DOY')
    plt.ylabel('Measured Temperature/K')
    plt.ylim([290, 325])
    plt.show()