import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from AATSR_product.util.util_aatsr import *
from AATSR_product.backup_old.old_version_backup.AATSR_product.opt_lsct.multiple_lsct import *
from AATSR_product.backup_old.old_version_backup.AATSR_product.util.old.util_lsct import *
import calendar
import multiprocessing
from functools import partial
import warnings
warnings.filterwarnings("ignore")
from AATSR_product.backup_old.old_version_backup.AATSR_product.util.old.util_constant import *
import time

"""
AATSR 两组分温度反演 注意版本python37
v0.2 版本，和最原始的v0相比，仅仅是算回b加了多次散射，其他都没有变化
不剔云、有效发射率不加多次散射、加窗口平均
"""

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
    radiance_min_threshold = 4.0  # 4.5
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
        # ctprior = np.transpose(np.matrix([coeffprior[0],coeffprior[6]]))

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
        w1 = wNLine[:,nl1:nl2, 2] # 2*1
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
    ###### 注意！ 这里有变化！
    F = 0.75
    C = (1 - emis_s) * emis_v  * F * (1 - fvc_n)
    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s + C)

    C = (1 - emis_s) * emis_v  * F * (1 - fvc_o)
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s + C)

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
    pool = Pool(min(196,int(cpu_count())))
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

def aatsr_read_aux_data(indir_emis, indir_type):
    '''
    aatsr 读取辅助数据
    :param indir_emis: 发射率
    :param indir_type:  地表类型
    :return: 土壤发射率、植被发射率、分类、密度、树覆盖比例、树冠高度，观测天顶角、方位角
    '''
    # 读取type emis std hcr rcr
    infile_type = indir_type + 'type_world_1000.tif'
    infile_soil_emis = indir_emis + r'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
    infile_veg_emis = indir_emis + 'IGBP_Emi.txt'
    infile_vzaN = indir_type + r"vza_n.tif"
    infile_vaaN = indir_type + r"vaa_n.tif"
    infile_vzaO = indir_type + r"vza_f.tif"
    infile_vaaO = indir_type + r"vaa_f.tif"
    [emis_s, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_soil_emis)
    [classif, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_type)
    [vzaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vzaN)
    [vaaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaaN)
    [vzaO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vzaO)
    [vaaO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaaO)
    vzaN, vzaO, vaaN, vaaO = 90 - vzaN / 100, 90 - vzaO / 100, vaaN / 100, vaaO / 100
    emis_s = emis_s / 1000
    classif = np.asarray(classif, np.int_)
    classif[classif == 255] = 17
    emis_v = read_txt_array(infile_veg_emis, 0, 2)
    emis_v = emis_v[classif, 0] / 1000
    return emis_s, emis_v, classif, vzaN, vzaO, vaaN, vaaO


if __name__ == '__main__':
    # indir0 = r'/home/bianzj/AATSR_test/'
    indir0 = r"/home/hero/data/base/"

    indir_type = indir0 + r'/0_base/type/'
    indir_emis = indir0 + r'/0_base/emis/'
    indir_base = indir0 + r'/0_base/base/'
    indir_lai0 = indir0 + r'/lai/'

    indir_obs = r'/media/hero/lsct03/aatsr_obs/'
    indir_clo = r'/media/hero/lsct03/aatsr_clo/'
    indir_ang = r'/media/hero/lsct03/aatsr_ang/'
    indir_loc = r'/media/hero/lsct04/aatsr_loc/'
    indir_lst = r'/media/hero/lsct04/aatsr_lst/'
    indir_aux = r'/media/hero/lsct04/aatsr_aux/'

    infile_soil_emis = indir_emis + r'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
    infile_type = indir_type + 'type_world_1000.tif'
    infile_veg_emis = indir_emis + 'IGBP_Emi.txt'

    '''读取发射率'''
    emis_s_, emis_v_, classif_,  vzaN, vzaF, vaaN, vaaF = aatsr_read_aux_data(
        indir_emis, indir_type)
    # [emis_s_, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_soil_emis)
    # emis_s_ = emis_s_ / 1000
    # [classif_, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_type)
    # classif_ = np.asarray(classif_, np.int_)
    # classif_[classif_ == 255] = 17
    # emis_v_ = read_txt_array(infile_veg_emis, 0, 2)
    # emis_v_ = emis_v_[classif_, 0] / 1000

    '''读取数据'''
    for kyear in range(2006, 2007):
        indir_lai = indir_lai0+'%04d/'%kyear

        outdir0 = r'/home/hero/data/AATSR/global_test/aatsr_lsct_v0.2/'
        outdir = outdir0 + '/%04d/'%kyear
        indir = indir0 + '/%04d'%kyear
        for kmonth in range(7, 8):
            daynum = calendar.monthrange(kyear, kmonth)[1]
            for day in range(2,3):
                # time_str = "%02d//" % kmonth + "%02d//" % (day + 1)
                # indir_tif = indir + r"/tif/" + time_str
                # if not os.path.exists(indir_tif): continue

                # indir_lstN = indir + r"/lst//" + time_str
                # indir_lstO = indir_lstN

                year , month = kyear, kmonth
                time_str = f'{year}/{month:02d}/{day:02d}/'
                outdir_hdf_day = outdir0 + r"/%02d/%02d//" % (month, day)
                mkdir_if_not_exist(outdir_hdf_day)

                # fileNames = search_file_rej(indir_lstN, ['lst_n'], 'enp')
                # fileNum = np.size(fileNames)
                # off = 9
                fileNames = search_file_rej(indir_obs+time_str, ['h5'],'xml')
                fileNum = len(fileNames)


                # print(fileNum)
                # for k in range(fileNum):
                #     filesName = search_file_rej(indir_lstN, ['lst_n'], 'enp')
                #     filesNum = len(filesName)

                for i, fileName in enumerate(fileNames):
                    print(i + 1, '/', fileNum , fileName)

                    out_hdf5 = outdir_hdf_day + fileName[:-3] + "_lsct.h5"
                    if os.path.exists(out_hdf5): 
                        os.remove(out_hdf5)

                    year = fileName[6:10]
                    doy_str = fileName[11:14]
                    fileName_str = fileName[0:22]
                    doy = int(doy_str)

                    basename = os.path.basename(fileName)

                    infile_obs = indir_obs + time_str + basename
                    infile_lst = indir_lst + time_str + basename.replace('obs', 'lst')
                    infile_clo = indir_clo + time_str + basename.replace('obs', 'clo')
                    infile_ang = indir_ang + time_str + basename.replace('obs', 'ang')
                    infile_loc = indir_loc + time_str + basename.replace('obs', 'loc')
                    infile_aux = indir_aux + time_str + basename.replace('obs', 'aux')


                    if not os.path.exists(infile_lst): 
                        print(f'    不存在lst文件: {infile_lst}')
                        continue
                    if not os.path.exists(infile_clo): 
                        print(f'    不存在clo文件: {infile_clo}')
                        continue
                    if not os.path.exists(infile_ang): 
                        print(f'    不存在ang文件: {infile_ang}')
                        continue
                    if not os.path.exists(infile_loc): 
                        print(f'    不存在loc文件: {infile_loc}')
                        continue

                    # 读取数据
                    lstN, lstF = aatsr_read_lst(infile_lst)
                    ndviN, ndviF = aatsr_read_NDVI(infile_obs)
                    cloN_mask , cloF_mask = aatsr_read_clo(infile_clo)
                    indx, indy,lon,lat = aatsr_read_loc(infile_loc, iflonlat = 1)
                    nl, ns = lstN.shape[0], lstF.shape[1] # 行列数
                    lai = read_h5py_item(infile_aux, 'LAI')/1000
                    # sza, saa = read_h5py_items(infile_ang, ['sza', 'saa'])
                    # sza = sza /100
                    # saa = saa / 100



                    # infileLstN = indir_lstN + fileName_str + 'lst_n.tif'
                    # infileLstO = indir_lstO + fileName_str + 'lst_f.tif'

                    # '''输出路径'''
                    # outfileLsct = outdir_lsct + fileName_str + '_lsct.tif'
                    # if os.path.exists(outfileLsct) == 1: continue


                    # '''确定所需数据都存在'''
                    # c1 = os.path.exists(infileLstN)
                    # c2 = os.path.exists(infileLstO)
                    # if c1 * c2  == 0:
                    #     print(fileName + ' lack lst data')
                    #     continue

                    # infileVzaN = indir_tif + fileName_str + 'vza_n.tif'
                    # infileVaaN = indir_tif + fileName_str + 'vaa_n.tif'
                    # infileVzaO = indir_tif + fileName_str + 'vza_f.tif'
                    # infileVaaO = indir_tif + fileName_str + 'vaa_f.tif'
                    # c1 = os.path.exists(infileVzaN)
                    # c2 = os.path.exists(infileVaaN)
                    # c3 = os.path.exists(infileVzaO)
                    # c4 = os.path.exists(infileVaaO)
                    # if c1 * c2 * c3 * c4== 0:
                    #     print(fileName + ' lack observation angle data')
                    #     continue
                    #
                    # infileSza = indir_tif + fileName_str + 'sza.tif'
                    # infileSaa = indir_tif + fileName_str + 'saa.tif'
                    # c1 = os.path.exists(infileSza)
                    # c2 = os.path.exists(infileSaa)
                    # if c1 * c2 == 0:
                    #     print(fileName + ' lack sun angle data')
                    #     continue

                    # infileRedN = indir_tif + fileName_str + 'red_n.tif'
                    # infileNirN = indir_tif + fileName_str + 'nir_n.tif'
                    # infileRedO = indir_tif + fileName_str + 'red_f.tif'
                    # infileNirO = indir_tif + fileName_str + 'nir_f.tif'

                    # infileVzaN = indir_tif + fileName_str + 'vza_n.tif'
                    # infileVzaO = indir_tif + fileName_str + 'vza_f.tif'
                    # infileIndx = indir_tif + fileName_str + 'indx.tif'
                    # infileIndy = indir_tif + fileName_str + 'indy.tif'
                    # c1 = os.path.exists(infileVzaN)
                    # c2 = os.path.exists(infileVzaO)
                    # c3 = os.path.exists(infileIndx)
                    # c4 = os.path.exists(infileIndy)
                    # if c1 * c2 * c3 * c4== 0:
                    #     print(fileName + ' lack observation angle data')
                    #     continue

                    # '''读取数据'''
                    # [lstN, ns, nl,bands, geog, proj] = read_image_gdal(infileLstN)
                    # [lstO, width, height, bands, geog, proj] = read_image_gdal(infileLstO)
                    # lstN = lstN/100
                    # lstO = lstO/100

                    # [redN, width, height, bands, geog, proj] = read_image_gdal(infileRedN)
                    # [nirN, width, height, bands, geog, proj] = read_image_gdal(infileNirN)
                    # [redO, width, height, bands, geog, proj] = read_image_gdal(infileRedO)
                    # [nirO, width, height, bands, geog, proj] = read_image_gdal(infileNirO)
                    # [vza_n, width, height, bands, geog, proj] = read_image_gdal(infileVzaN)
                    # [vza_o, width, height, bands, geog, proj] = read_image_gdal(infileVzaO)
                    # [indx, width, height, bands, geog, proj] = read_image_gdal(infileIndx)
                    # [indy, width, height, bands, geog, proj] = read_image_gdal(infileIndy)
                    # vza_n = 90 - (vza_n/100)
                    # vza_o = 90 - (vza_o/100)
                    # '''计算FVC'''
                    # '''读取LAI'''
                    # doy1 = (doy // 4) * 4 + 1
                    # doy2 = (doy // 4) * 4 + 5
                    # infile_lai1 = indir_lai + r"MuSyQ.CSC.LAI.A" + '%04d%03d' % (int(year), doy1) + '.tif'
                    # infile_lai2 = indir_lai + r"MuSyQ.CSC.LAI.A" + '%04d%03d' % (int(year), doy2) + '.tif'
                    # if not os.path.exists(infile_lai2): infile_lai2 = infile_lai1
                    # [lai1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai1)
                    # [lai2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai2)
                    # lai = (1 - (doy - doy1) / 4) * lai1[indx, indy] + (doy - doy1) / 4 * lai2[indx, indy]
                    # lai = np.reshape(lai, [nl, ns])
                    # lai[lai >= 30000] = 0
                    # lai = lai / 1000

                    fvc_n = cal_fvc_from_lai(vzaN, lai)
                    fvc_o = cal_fvc_from_lai(vzaF, lai)

                    fvc_n[fvc_n > 1] = 1
                    fvc_n[fvc_n < 0] = 0
                    fvc_o[fvc_o > 1] = 1
                    fvc_o[fvc_o < 0] = 0

                    # dif_fvc = fvc_n - fvc_o
                    # outfiledfvc = outdir_lsct + fileName_str + '_dfvc.tif'
                    # write_image_gdal(dif_fvc, ns, nl, 1, geog, proj, outfiledfvc)


                    '''根据lon、lat调整emis'''
                    indx[indx == 18000] = 0
                    indy[indy == 36000] = 0
                    emis_s = emis_s_[indx, indy]
                    emis_v = emis_v_[indx, indy]
                    classif = classif_[indx, indy]
                    emis_s = np.reshape(emis_s, [nl, ns])
                    emis_v = np.reshape(emis_v, [nl, ns])
                    classif = np.reshape(classif, [nl, ns])

                    '''反演LSCT'''
                    print(fileName + '_lsct.tif start')
                    lsct = inv_mpl_agl_multiple_2(lstN, lstF, emis_s, emis_v, fvc_n, fvc_o, wl=10.8)


                    [ns, nl, nb] = np.shape(lsct)
                    if (np.sum(lsct) == 0):
                        print(fileName + '_lsct.tif' + ' no result')
                        continue

                    lsct_save = np.zeros([nb,ns,512])
                    lsct_save[0,:,2:-2] = np.reshape(lsct[:,:,0],[ns,nl])
                    lsct_save[1,:,2:-2] = np.reshape(lsct[:,:,1],[ns,nl])

                    # write_image_gdal(lsct_save, nl, ns+4, nb, geog, proj, outfileLsct)
                    # print(fileName + '_lsct.tif done')


                    # break
                    '''写h5文件'''
                    out_hdf5 = outdir_hdf_day + fileName[:-3] + "_lsct.h5"
                    if not os.path.exists(out_hdf5):
                        f = h5py.File(out_hdf5, 'w')
                    else:
                        continue

                    '''save'''
                    f.attrs['Origin File'] = fileName
                    f.attrs['Version'] = 'v0'
                    from datetime import datetime
                    f.attrs['Creation Date'] = str(datetime.now())
                    f.attrs['Author'] = 'Lu Yifan / Bian Zunjian'
                    f.attrs['Method'] = 'Ts/Tv: 2 angle 5 pixel(bayesian)'

                    datasets = {
                        'Ts':(lsct_save[0,:,:] * 100,'soil temperature(in K,*100),Scale = 100, type = uint16', np.uint16),
                        'Tv': (lsct_save[1,:,:] * 100, 'veg temperature(in K,*100),Scale = 100, type = uint16', np.uint16),
                    }

                    for dset_name, (data, description, dtype) in datasets.items():
                        if dset_name in f:
                            del f[dset_name]
                        dset = f.create_dataset(dset_name, data=data, dtype=dtype, compression='gzip')
                        dset.attrs['description'] = description

                    f.close()

