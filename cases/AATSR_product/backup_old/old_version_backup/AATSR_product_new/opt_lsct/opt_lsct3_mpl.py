from utils.old.util_lsct import *
import time
import warnings
warnings.filterwarnings("ignore")


'''
2024.10.28
AATSR_world 组分温度反演
两角度，多像元
1. 读取数据 (数据检查)
2. 计算能量
3. 计算有效发射率
4. 选择方法进行反演
'''

if __name__ == '__main__':
    # 年 月 （日）
    year = 2010
    month = 1
    day = 1

    # 模式
    number_component = 2
    if_use_crown = False

    # hdf 路径
    AATSR_dir = r"/media/hero/lsct01/AATSR/%04d//" % year
    # base 文件路径
    base_dir = r"/media/hero/lsct01/0_base/"
    indir_emis = base_dir + r"emis/"
    indir_type = base_dir + r"type/"
    indir_veg_pra = base_dir + "Veg_para/"

    emisS_gl, emisV_gl, classif_gl,  vzaN_st, vzaF_st, vaaN_st, vaaF_st = aatsr_read_aux_data(
        indir_emis, indir_type)
    if if_use_crown:
        std_gl, tcc_gl, hcr_gl = aatsr_read_crown_data(indir_veg_pra)

    # 输入 / 输出 路径
    indir_hdf = AATSR_dir + "hdf/"
    outdir_hdf = r'/home/hero/data/AATSR/%04d' % year + "lsct_hdf/"
    # outdir_hdf = r"/home/hero/data/AATSR/%04d//" % year + "lsct_hdf/"
    indir_hdf_day = indir_hdf + r"/%02d/%02d//" % (month, day)
    outdir_hdf_day = outdir_hdf + r"/%02d/%02d//" % (month, day)
    mkdir_if_not_exist(outdir_hdf_day)
    fileNames = search_file_rej(indir_hdf_day, ['.h5'], 'enp')
    fileNum  = len(fileNames)

    for i, fileName in enumerate(fileNames):
        print(i + 1, '/', fileNum , fileName)
        start = time.time()

        # 读取数据
        infile_h5 = indir_hdf_day + fileName
        items = name_list = ["lon", 'lat', "indx", "indy", "time", "LAI", 'sza', 'saa', 'clo_N', 'clo_O', "lstN",
                             "lstO"]
        lon_st, lat_st, indx, indy, time_st, lai, sza, saa, cloN, cloF, lstN, lstF = read_h5py_items(infile_h5, items)
        lstN, lstF = lstN / 100, lstF / 100
        sza, saa = 90 - sza / 100, saa / 100
        if np.average(lai[lai!=0]>10): lai = lai / 1000

        # 植被参数重投影 gl - > st
        nl, ns = 43520,512
        if np.shape(lstN) != (nl, ns):
            nl, ns = np.shape(lstN)
            print("Special file(nl,ns):" , nl, ns)
        vzaN, vzaF, vaaN, vaaF = vzaN_st[:nl, :], vzaF_st[:nl, :], vaaN_st[:nl, :], vaaF_st[:nl, :]
        emisS = np.reshape(emisS_gl[indx, indy], [nl, ns])
        emisV = np.reshape(emisV_gl[indx, indy], [nl, ns])
        classif = np.reshape(classif_gl[indx, indy], [nl, ns])
        if if_use_crown:
            tcc = np.reshape(tcc_gl[indx, indy], [nl, ns])
            std = np.reshape(std_gl[indx, indy], [nl, ns])
            hcr = np.reshape(hcr_gl[indx, indy], [nl, ns])
            rcr = np.zeros([nl, ns])
            rcr = np.sqrt(tcc / np.pi / std)
            rcr[(rcr < 0.5) * (rcr > 0)] = 0.5
            rcr[rcr > 30] = 30

        #  计算L能量
        wl = 10.8
        radN = cal_rad_from_lst(lstN,wl,lai,vzaN,emisS,emisV)
        radF = cal_rad_from_lst(lstF,wl,lai,vzaF,emisS,emisV)

        #  计算W有效发射率
        if not if_use_crown:
            hspot = 0.2
            wN,posil = cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vzaN,sza,vaaN,saa,3)
            wF,psoil = cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vzaF,sza,vaaF,saa,3)
        else:
            hspot = 1.0
            wN,psoil = cal_effective_emissivity_crown(lai,hspot,wl,emisS,emisV,vzaN,sza,vaaN,saa,classif,rcr,tcc,hcr,2)
            wF,psoil = cal_effective_emissivity_crown(lai, hspot, wl, emisS, emisV, vzaF, sza, vaaF, saa, classif, std, rcr,
                                                hcr, 2)

        # 添加 mask
        rad_th_max, rad_th_min = 20, 4.5
        maskN = (radN > rad_th_min) * (radN < rad_th_max) * (cloN <= 100)
        maskF = (radF > rad_th_min) * (radF < rad_th_max) * (cloF <= 100)

        # 给定温度限制
        DT = np.zeros([nl, ns])
        DT = determine_DT_lat_time(DT, month, lat_st)

        # 反演
        window_size = 5 # 奇数 3、5、7
        off = int((window_size - 1) / 2)
        para = []
        results = np.zeros([5, nl, ns])
        for kn in range(off, nl - off):
            ###### 取wN的所有组分的n列，行全部，进行多线程的操作
            wNLine = wN[:, kn - off: kn + off + 1, :]
            wOLine = wF[:, kn - off: kn + off + 1, :]
            radNLine = radN[kn - off:kn + off + 1, :]
            radOLine = radF[kn - off:kn + off + 1, :]
            maskNLine = maskN[kn - off: kn + off + 1, :]
            maskOLine = maskF[kn - off: kn + off + 1, :]
            psoilLine = psoil[kn - off: kn + off + 1, :]
            DTLine = DT[kn - off:kn + off + 1, :]
            '''调试用,非多线程'''
            # results[:,kn,:] = inv_lsct3_AATSR_line(wNLine, wOLine, radNLine, radOLine, maskNLine, maskOLine, psoilLine,DTLine, ns)
            '''多线程'''
            para.append([wNLine, wOLine, radNLine, radOLine, maskNLine, maskOLine, psoilLine, DTLine, ns])
        tasks = []
        pool = Pool(min(192, cpu_count()))
        for p in para:
            tasks.append(pool.apply_async(doMultiple_line_inv_3_AATSR, (p,)))
        pool.close()
        pool.join()
        results = np.array([task.get() for task in tasks])
        results = np.array(results)
        results_transposed = np.transpose(results, (1, 0, 2))
        results = np.zeros((5, nl, ns))
        results[:, 2:-2, :] = results_transposed

        Tsl_inv = results[0, :, :]
        Tsh_inv = results[1, :, :]
        Tv_inv = results[2, :, :]
        Ts_b_inv = results[3, :, :]
        Tv_b_inv = results[4, :, :]

        '''save'''
        outfile = outdir_hdf_day + fileName[:-3] + "_lsct.h5"
        name_list = ['Tsl', 'Tsh', 'Tv', 'Ts_b','Tv_b']
        data_list = [Tsl_inv * 100, Tsh_inv * 100, Tv_inv * 100, Ts_b_inv * 100,Tv_b_inv * 100]
        dtype_list = ['uint16', 'uint16', 'uint16', 'uint16', 'uint16']
        write_h5py_file(outfile, name_list, data_list, dtype_list, compression=None, ifcover=1)
        end = time.time()
        print('time cost: ', end - start, 's')



