import numpy as np
from scipy import interpolate
import matplotlib.mlab as ml
import matplotlib.pyplot as plt
import time
from util.util import *
from util_lsct import *
from multiprocessing import Pool
import warnings

warnings.filterwarnings("ignore")

def lsct3_inv_window_point(wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine,ns = 1024):
    """
    用于反演三组分组分温度,同时给出窗口和点的值
    :param wNLine: 窗口垂直方向组分有效发射率
    :param wOLine: 窗口倾斜方向组分有效发射率
    :param wALine: 窗口AHI组分有效发射率
    :param radNLine: 窗口垂直方向能量
    :param radOLine: 窗口倾斜方向能量
    :param radAhiLine: 窗口AHI能量
    :param maskLine:判断了fvc和能量是否有值，有值为1，无则为0
    :param ns: 列号，长度
    :return:result窗口的贝叶斯结合，简单结合，单点多角度
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
        ### 我猜这个fd是归一化的F矩阵，代表权重值
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

        component_temperature_window = inv_planck(wl, coeffprior_window)
        result_window[:, kk] = [component_temperature_window[0], component_temperature_window[1],
                                component_temperature_window[2]]
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
        coeffprior_point = np.asarray(lstsq(w, b))[0]

        component_temperature_point = inv_planck(wl, coeffprior_point)
        result_point[:, kk] = [component_temperature_point[0], component_temperature_point[1], component_temperature_point[2]]

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
    return result,result_window,result_point

def doMultiple_lsct3_inv(param):
    '''
    组分温度反演回归的中间件
    :param param:参数/变量
    :return: 组分温度结果
    '''
    return lsct3_inv_window_point((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]),param[6],param[7])

def inv_mpl_agl_multiple_window_point(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pg_n, pg_o, pg_ahi, wl=10.8):
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
    rad_n = planck(wl, lst_n)  ### 黑体辐射值
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)  ###真实发射的能量
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

    rad_ahi = planck(wl, lst_ahi)
    # emisd2_v = resize_data(emis_v,nl/2,(ns+1)/2,method=cv2.INTER_NEAREST)
    # emisd2_s = resize_data(emis_s,nl/2,(ns+1)/2,method=cv2.INTER_NEAREST)
    # emisd2_v = resize_data_near(emis_v, nl / 2,  ns/ 2)
    # emisd2_s = resize_data_near(emis_s, nl / 2, ns / 2)
    emisd2_v = resize_data(emis_v, nl / 2, (ns + 1) / 2)
    emisd2_s = resize_data(emis_s, nl / 2, (ns + 1) / 2)
    fvc_ahi = resize_data(fvcAhi, nl / 2, (ns + 1) / 2)
    rad_ahiData = rad_ahi * (fvc_ahi * emisd2_v + (1 - fvc_ahi) * emisd2_s)
    rad_ahi = resize_data(rad_ahiData, nl, ns, method=cv2.INTER_NEAREST)

    # component effective emissivity matrix
    wN = np.asarray([emis_s * (1 - fvc_n) * pg_n, emis_s * (1 - fvc_n) * (1 - pg_n), emis_v * (fvc_n)])
    wO = np.asarray([emis_s * (1 - fvc_o) * pg_o, emis_s * (1 - fvc_o) * (1 - pg_o), emis_v * (fvc_o)])

    pg_ahi = resize_data(pg_ahi, nl / 2, (ns + 1) / 2, method=cv2.INTER_NEAREST)
    wAhiData = np.asarray(
        [emisd2_s * (1 - fvc_ahi) * pg_ahi, emisd2_s * (1 - fvc_ahi) * (1 - pg_ahi), emisd2_v * (fvc_ahi)])
    wAhi = np.asarray([resize_data(wAhiData[0], nl, ns, method=cv2.INTER_NEAREST),
                       resize_data(wAhiData[1], nl, ns, method=cv2.INTER_NEAREST),
                       resize_data(wAhiData[2], nl, ns, method=cv2.INTER_NEAREST)])

    mask = np.zeros([nl, ns])
    ind0 = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
           (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
           (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind0] = 1

    para = []
    for kn in range(off_inv, nl - off_inv):
        wNLine = wN[:, kn - off_inv:kn + off_inv + 1, :]
        wOLine = wO[:, kn - off_inv:kn + off_inv + 1, :]
        wALine = wAhi[:, kn - off_inv:kn + off_inv + 1, :]
        radNLine = rad_n[kn - off_inv:kn + off_inv + 1, :]
        radOLine = rad_o[kn - off_inv:kn + off_inv + 1, :]
        radAhiLine = rad_ahi[kn - off_inv:kn + off_inv + 1, :]
        maskLine = mask[kn - off_inv:kn + off_inv + 1, :]
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
    # results_window = np.asarray(results_window)
    # results_point = np.asarray(results_point)
    ### for ns/nl consistent
    lsct = np.zeros([3, nl, ns])
    lsct_window = np.zeros([3, nl, ns])
    lsct_point = np.zeros([3, nl, ns])
    lsct[0,off_inv:-off_inv,:] = results[:,0,0,:]
    lsct[1,off_inv:-off_inv,:] = results[:,0,1,:]
    lsct[2,off_inv:-off_inv,:] = results[:,0,2,:]
    lsct_window[0,off_inv:-off_inv,:] = results[:,1,0,:]
    lsct_window[1,off_inv:-off_inv,:] = results[:,1,1,:]
    lsct_window[2,off_inv:-off_inv,:] = results[:,1,2,:]
    lsct_point[0,off_inv:-off_inv,:] = results[:,2,0,:]
    lsct_point[1,off_inv:-off_inv,:] = results[:,2,1,:]
    lsct_point[2,off_inv:-off_inv,:] = results[:,2,2,:]

    print('time cost: ', end - start, 's')

    # lsct = np.zeros([3, nl, ns])
    # lsct_window = np.zeros([3, nl, ns])
    # lsct_point = np.zeros([3, nl, ns])
    # for p in para:
    #     results,result_window,result_point = doMultiple_lsct3_inv(p)
    #     ### 把结果连起来
    # lsct[0, off_inv:-off_inv, :] = results[ 0, :]
    # lsct[1, off_inv:-off_inv, :] = results[ 1, :]
    # lsct[2, off_inv:-off_inv, :] = results[ 2, :]
    # lsct_window[0, off_inv:-off_inv, :] = result_window[ 0, :]
    # lsct_window[1, off_inv:-off_inv, :] = result_window[ 1, :]
    # lsct_window[2, off_inv:-off_inv, :] = result_window[ 2, :]
    # lsct_point[0, off_inv:-off_inv, :] = result_point[ 0, :]
    # lsct_point[1, off_inv:-off_inv, :] = result_point[ 1, :]
    # lsct_point[2, off_inv:-off_inv, :] = result_point[ 2, :]

    return lsct,lsct_window,lsct_point

# 3 observations from slstr + ahi for 3 components
if __name__ == '__main__':

    indir_lstN = r'D:\data\LSCT\slstr_2022\lst/'
    indir_lstO = r'D:\data\LSCT\slstr_2022\lst/'
    indir_lstAhi = r'D:\data\LSCT\ahi_2022\lst/'
    indir_tif = r'D:\data\LSCT\slstr_2022\tif/'
    indir_fvcN = r'D:\data\LSCT\fvc_2022/'
    indir_fvcO = r'D:\data\LSCT\fvc_2022/'
    indir_fvcAhi = r'D:\data\LSCT\fvc_2022/'
    indir_lai = r'D:\data\LSCT\lai_2022/'

    # indir_lstN = r'E:\s3a_lst/'
    # indir_lstO = r'E:\s3a_lst/'
    # indir_lstAhi = r'e:\ahi_s3a_lst/'
    # indir_tif = r'e:\s3a_tif/'
    # indir_fvcN = r'e:\fvc_s3a_n/'
    # indir_fvcO = r'e:\fvc_s3a_o/'
    # indir_fvcAhi = r'e:\fvc_s3a_ahi/'
    # indir_lai = r'e:\lai/'

    outdir_lsct = r'D:\data\LSCT\slstr_2022\lsct3_new2/'
    outdir_lsct_window = r'D:\data\LSCT\slstr_2022\lsct3_window/'
    outdir_lsct_point = r'D:\data\LSCT\slstr_2022\lsct3_point/'

    indir_type = 'd:/data/type/'
    indir_ems = r'D:\data\emis/'

    infile_soil_emis = indir_ems + 'emis1_polar_heihe_cut.tif'
    infile_type = indir_type + 'type_heihe_1000_new.tif'
    infile_veg_emis = indir_ems + 'IGBP_Emi.txt'

    [emis_s, emis_v, geog, proj] = readImages_emis(infile_soil_emis, infile_veg_emis, infile_type)
    [type, width, height, bands, geog, proj] = read_image_gdal(infile_type)

    filesName = search_file(indir_lstN, ['day', 'lst'])
    filesNum = len(filesName)
    ahiFileNames = search_file(indir_lstAhi, ['lst'])

    for fileI in range(filesNum):
        # for fileI in range(243,244):
        fileName = filesName[fileI][:-18]
        doyStr = fileName[-3:]
        infileLstN = indir_lstN + fileName + '_day_lst_nadir.tif'
        infileLstO = indir_lstO + fileName + '_day_lst_obliq.tif'
        #
        ahifileArr = [ahifile for ahifile in ahiFileNames if doyStr in ahifile]
        if np.size(ahifileArr) <= 1: continue
        ahiFileName1 = ahifileArr[0][:-7]
        ahiFileName2 = ahifileArr[1][:-7]
        infileLstAhi1 = indir_lstAhi + ahiFileName1 + 'lst.tif'
        infileLstAhi2 = indir_lstAhi + ahiFileName2 + 'lst.tif'
        ahiTime1 = int(ahiFileName1[12:16])
        ahiTime2 = int(ahiFileName2[12:16])
        c1 = os.path.exists(infileLstN)
        c2 = os.path.exists(infileLstO)
        c3 = os.path.exists(infileLstAhi1)
        c4 = os.path.exists(infileLstAhi2)
        if c1 * c2 * c3 *c4 == 0:
            print(fileName + ' lack lst data')
            continue

        infileVzaN = indir_tif + fileName + '_day_vza_nadir.tif'
        infileVaaN = indir_tif + fileName + '_day_vaa_nadir.tif'
        infileVzaO = indir_tif + fileName + '_day_vza_obliq.tif'
        infileVaaO = indir_tif + fileName + '_day_vaa_obliq.tif'
        infileTime = indir_tif + fileName + '_day_time.tif'
        infileVzaAhi = r'D:\data\base\ahi_angle_2022\AHI_VZA_HEIHE_cut.tif'
        infileVaaAhi = r'D:\data\base\ahi_angle_2022\AHI_VAA_HEIHE_cut.tif'
        c1 = os.path.exists(infileVzaN)
        c2 = os.path.exists(infileVaaN)
        c3 = os.path.exists(infileVzaO)
        c4 = os.path.exists(infileVaaO)
        if c1 * c2 * c3 * c4 == 0:
            print(fileName + ' lack observation angle data')
            continue

        infileSza = indir_tif + fileName + '_day_sza_nadir.tif'
        infileSaa = indir_tif + fileName + '_day_saa_nadir.tif'
        c1 = os.path.exists(infileSza)
        c2 = os.path.exists(infileSaa)
        if c1 * c2 == 0:
            print(fileName + ' lack sun angle data')
            continue

        infileFvcN = indir_fvcN + fileName + '_fvcN.tif'
        infileFvcO = indir_fvcO + fileName + '_fvcO.tif'
        infileFvcAhi = indir_fvcAhi + fileName + '_fvcAhi.tif'
        c1 = os.path.exists(infileFvcN)
        c2 = os.path.exists(infileFvcO)
        c3 = os.path.exists(infileFvcAhi)
        if c1 * c2 * c3 == 0:
            print(fileName + ' lack fvc data')
            continue

        infileLai = indir_lai + fileName + '_lai.tif'
        if os.path.exists(infileLai) == 0:
            print(fileName + ' lack LAI data')
            continue

        outfileLsct = outdir_lsct + fileName + '_lsct.tif'
        if os.path.exists(outfileLsct):
            print(fileName + '_lsct.tif exists')
            continue
        else:
            print(fileName + '_lsct.tif processing...')

        [lstN, width, height, bands, geog, proj] = read_image_gdal(infileLstN)
        [lstO, width, height, bands, geog, proj] = read_image_gdal(infileLstO)
        [lstAhi1, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileLstAhi1)
        [lstAhi2, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileLstAhi2)

        [slstrTime, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileTime)

        ### AHI加权求和,由于研究区很小，基本时间都一致，取众数
        ahiTime1 = ahiTime1//100 *60 + ahiTime1 % 100
        ahiTime2 = ahiTime2//100 *60 + ahiTime2 % 100
        slstrTime = (slstrTime/100).tolist()
        print(max(slstrTime))
        slstrTime = max(max(slstrTime,key=slstrTime.count))
        print(slstrTime)
        slstrTime = slstrTime//100 * 60 + slstrTime % 100
        lstAhi = np.abs((slstrTime-ahiTime2)/10) * lstAhi1 + np.abs((slstrTime-ahiTime1)/10) * lstAhi2
        if(fileName[0:3]=="S3A"):
            lstAhi = lstAhi * 0.9727491898535005 + 8.14384409751824
        else:
            lstAhi = lstAhi * 0.9738654689993518 + 7.602965534546172

        pgN = readImages_angle(infileLai, infileVzaN, infileVaaN, infileSza, infileSaa, resample=1)
        pgO = readImages_angle(infileLai, infileVzaO, infileVaaO, infileSza, infileSaa, resample=1)
        pgAhi = readImages_angle(infileLai, infileVzaAhi, infileVaaAhi, infileSza, infileSaa, resample=1)

        [fvcN, width, height, bands, geog, proj] = read_image_gdal(infileFvcN)
        [fvcO, width, height, bands, geog, proj] = read_image_gdal(infileFvcO)
        [fvcAhi, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileFvcAhi)

        lsct,lsct_window,lsct_point = inv_mpl_agl_multiple_window_point(lstN, lstO, lstAhi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pgN, pgO, pgAhi, wl=10.8)
        [ns, nl, nb] = np.shape(lsct)
        # [ns, nl, nb] = np.shape(lsct)
        if (np.sum(lsct) == 0):
            print(fileName + '_lsct.tif' + ' no result')
            continue
        write_image_gdal(lsct, ns, nl, nb, geog, proj, outfileLsct)
        outfileLsct_window = outdir_lsct_window + fileName+ '_lsct_window.tif'
        outfileLsct_point = outdir_lsct_point + fileName+ '_lsct_point.tif'
        write_image_gdal(lsct_window, ns, nl, nb, geog, proj, outfileLsct_window)
        write_image_gdal(lsct_point, ns, nl, nb, geog, proj, outfileLsct_point)
        print(fileName + '_lsct.tif done')
