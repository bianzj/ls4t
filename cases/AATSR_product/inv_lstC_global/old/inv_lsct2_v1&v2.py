import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
# from base.util_lsct import *
# from base.util_constant import *
# from base.util_file import *
# from base.util_data import *
from util.util_aatsr import *
from backup_old.old_version_backup.AATSR_product_new.util.util_lsct import *
from backup_old.old_version_backup.AATSR_product_new.util.util import *
import time
from datetime import datetime
from multiprocessing import Pool, freeze_support, cpu_count
import warnings
warnings.filterwarnings("ignore")

'''
2024.10.28
AATSR_world 组分温度反演
两角度，多像元
'''

def cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,component_number):
    nl,ns = np.shape(vza)
    w4 = sample_hom_Emis(lai,hspot,wl,emisS,emisV,vza,sza,np.abs(vaa-saa))
    psoil = gap_probability_hom_analytical(lai,sza)
    if component_number == 2:
        w = np.zeros([2,nl,ns])
        w[0,:,:] = w4[0,:,:] + w4[1,:,:]
        w[1,:,:] = w4[2,:,:] + w4[3,:,:]
    if component_number == 3:
        w = np.zeros([3,nl,ns])
        w[0:2,:,:] = w4[0:2,:,:]
        w[2,:,:] = w4[2,:,:] + w4[3,:,:]
    if component_number == 4:
        w = w4
    return w,psoil

if __name__ == '__main__':
    # 年 月 （日）
    year = 2007
    month = 7
    day = 2
    # year = int(sys.argv[1])
    # month = int(sys.argv[2])
    # day = int(sys.argv[3])

    # 模式
    number_component = 2
    if_use_crown = False   # 未经过debug

    # hdf 路径
    # AATSR_dir = r"/media/hero/lsct04/AATSR/%04d//" % year
    indir_obs = r'/media/hero/lsct03/aatsr_obs/'
    indir_clo = r'/media/hero/lsct03/aatsr_clo/'
    indir_ang = r'/media/hero/lsct03/aatsr_ang/'
    indir_loc = r'/media/hero/lsct04/aatsr_loc/'
    indir_lst = r'/media/hero/lsct04/aatsr_lst/'
    indir_aux = r'/media/hero/lsct04/aatsr_aux/'

    # AATSR_dir = r"/media/hero/265047F75047CBED/T7920_backup/AATSR/%04d//" % year
    outdir_hdf = r'/home/hero/data/AATSR/global_test/aatsr_lsct_v2.0(combined)/'
    outdir_hdf_p = r'/home/hero/data/AATSR/global_test/aatsr_lsct_v1.0(combined)/'
    # base 文件路径
    base_dir = r"/home/hero/data/base/0_base/"
    indir_emis = base_dir + r"emis/"
    indir_type = base_dir + r"type/"
    indir_veg_pra = base_dir + "Veg_para/"

    emisS_gl, emisV_gl, classif_gl,  vzaN_st, vzaF_st, vaaN_st, vaaF_st = aatsr_read_aux_data(
        indir_emis, indir_type)
    if if_use_crown:
        std_gl, tcc_gl, hcr_gl = aatsr_read_crown_data(indir_veg_pra)

    # 输入 / 输出 路径
    # indir_hdf = AATSR_dir + "hdf/"
    # indir_hdf_day = indir_hdf + r"/%02d/%02d//" % (month, day)
    outdir_hdf_day = outdir_hdf + r"/%02d/%02d//" % (month, day)
    outdir_hdf_day_p = outdir_hdf_p + r"/%02d/%02d//" % (month, day)
    mkdir_if_not_exist(outdir_hdf_day)
    mkdir_if_not_exist(outdir_hdf_day_p)
    # fileNames = search_file_rej(indir_hdf_day, ['.h5'], 'enp')
    time_str = f'{year}/{month:02d}/{day:02d}/'
    fileNames = search_file_rej(indir_obs+time_str, ['h5'],'xml')
    fileNum = len(fileNames)

    mkdir_if_not_exist(outdir_hdf + r"error/")
    error_file_dir = outdir_hdf + r"error/" + r"%02d_%02d_%02d.txt" % (year, month, day)

    error_files = []
    for i, fileName in enumerate(fileNames):
        print(i + 1, '/', fileNum , fileName)
        start = time.time()

        out_hdf5 = outdir_hdf_day + fileName[:-3] + "_lsct.h5"
        out_hdf5_p = outdir_hdf_day_p + fileName[:-3] + "_lsct.h5"
        
        # if os.path.exists(out_hdf5) and os.path.exists(out_hdf5_p): continue

        # 读取数据
        # infile_h5 = indir_hdf_day + fileName
        # items = name_list = ["lon", 'lat', "indx", "indy", "time", "LAI", 'sza', 'saa', 'clo_N', 'clo_O', "lstN",
        #                      "lstO"]
        # try:
        #     lon_st, lat_st, indx, indy, time_st, lai, sza, saa, cloN, cloF, lstN, lstF = read_h5py_items(infile_h5,
        #                                                                                                  items)
        # except OSError as e:
        #     error_files.append(infile_h5)
        #     print(f"Error reading {infile_h5}: {e}")
        #     continue

        # lstN, lstF = lstN / 100, lstF / 100
        # sza, saa = 90 - sza / 100, saa / 100
        # if np.average(lai[lai!=0]>10): lai = lai / 1000
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
        sza, saa = read_h5py_items(infile_ang, ['sza', 'saa'])
        sza = sza /100
        saa = saa / 100


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
            wN,posil = cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vzaN,sza,vaaN,saa,2)
            wF,psoil = cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vzaF,sza,vaaF,saa,2)
        else:
            hspot = 1.0
            wN,psoil = cal_effective_emissivity_crown(lai,hspot,wl,emisS,emisV,vzaN,sza,vaaN,saa,classif,rcr,tcc,hcr,2)
            wF,psoil = cal_effective_emissivity_crown(lai, hspot, wl, emisS, emisV, vzaF, sza, vaaF, saa, classif, std, rcr,
                                                hcr, 2)

        # 添加 mask
        rad_th_max, rad_th_min = 20, 3.2
        maskN = (radN > rad_th_min) * (radN < rad_th_max) * (cloN_mask == 1)
        maskF = (radF > rad_th_min) * (radF < rad_th_max) * (cloF_mask == 1)

        # 给定温度限制
        DT = np.zeros([nl, ns])
        DT = determine_DT_lat_time(DT, month, lat)

        # 反演
        window_size = 5 # 奇数 3、5、7
        off = int((window_size - 1) / 2)
        para = []
        results = np.zeros([4, nl, ns])
        for kn in range(off, nl - off):
            ###### 取wN的所有组分的n列，行全部，进行多线程的操作
            wNLine = wN[:, kn - off: kn + off + 1, :]
            wOLine = wF[:, kn - off: kn + off + 1, :]
            radNLine = radN[kn - off:kn + off + 1, :]
            radOLine = radF[kn - off:kn + off + 1, :]
            maskNLine = maskN[kn - off: kn + off + 1, :]
            maskOLine = maskF[kn - off: kn + off + 1, :]
            lstNLine = lstN[kn - off: kn + off + 1, :]
            lstFLine = lstF[kn - off: kn + off + 1, :]
            DTLine = DT[kn - off:kn + off + 1, :]
            '''调试用,非多线程'''
            # results[:,kn,:] = inv_lsct2_AATSR_line(wNLine, wOLine, radNLine, radOLine, maskNLine, maskOLine, lstNLine, lstFLine,DTLine, ns)
            '''多线程'''
            para.append([wNLine, wOLine, radNLine, radOLine, maskNLine, maskOLine, lstNLine,lstFLine, DTLine, ns])
        tasks = []
        pool = Pool(min(192, cpu_count()))
        for p in para:
            tasks.append(pool.apply_async(doMultiple_line_inv_2_AATSR, (p,)))
        pool.close()
        pool.join()
        results = np.array([task.get() for task in tasks])
        results = np.array(results)
        results_transposed = np.transpose(results, (1, 0, 2))
        results = np.zeros((4, nl, ns))
        results[:, 2:-2, :] = results_transposed
        #
        Ts_inv = results[0, :, :]
        Tv_inv = results[1, :, :]
        Ts_b_inv = results[2, :, :]
        Tv_b_inv = results[3, :, :]

        # '''save'''
        # outfile = outdir_hdf_day + fileName[:-3] + "_lsct.h5"
        # name_list = ['indx','indy','lstN','lstF','Ts', 'Tv', 'Ts_b','Tv_b']
        # data_list = [indx, indy, lstN*100,lstF*100,Ts_inv * 100, Tv_inv * 100,  Ts_b_inv * 100,Tv_b_inv * 100]
        # dtype_list = ['uint16', 'uint16','uint16', 'uint16', 'uint16', 'uint16']
        # write_h5py_file(outfile, name_list, data_list, dtype_list, compression=None, ifcover=1)
        # end = time.time()
        # print('time cost: ', end - start, 's')


        '''写h5文件'''
        out_hdf5 = outdir_hdf_day + fileName[:-3] + "_lsct.h5"
        if not os.path.exists(out_hdf5):
            f = h5py.File(out_hdf5, 'w')
        else:
            continue

        '''save'''
        f.attrs['Origin File'] = fileName
        f.attrs['Version'] = 'v1'
        f.attrs['Creation Date'] = str(datetime.now())
        f.attrs['Author'] = 'Lu Yifan / Bian Zunjian'
        f.attrs['Method'] = 'Ts/Tv: 2 angle 5 pixel(with weight / bounds, without)'

        datasets = {
            'Ts':(Ts_inv * 100,'soil temperature(in K,*100),Scale = 100, type = uint16', np.uint16),
            'Tv': (Tv_inv * 100, 'veg temperature(in K,*100),Scale = 100, type = uint16', np.uint16),
        }

        for dset_name, (data, description, dtype) in datasets.items():
            if dset_name in f:
                del f[dset_name]
            dset = f.create_dataset(dset_name, data=data, dtype=dtype, compression='gzip')
            dset.attrs['description'] = description

        f.close()

        '''写h5文件'''
        out_hdf5 = outdir_hdf_day_p + fileName[:-3] + "_lsct.h5"
        if not os.path.exists(out_hdf5):
            f = h5py.File(out_hdf5, 'w')
        else:
            continue
        '''save'''
        f.attrs['Origin File'] = fileName
        f.attrs['Version'] = 'v0'
        f.attrs['Creation Date'] = str(datetime.now())
        f.attrs['Author'] = 'Lu Yifan / Bian Zunjian'
        f.attrs['Method'] = 'Ts_p/Tv_p: 2angle 1 pixel'

        datasets = {
            'Ts_p':(Ts_b_inv * 100,'Pixel soil temperature(in K,*100),Scale = 100, type = uint16', np.uint16),
            'Tv_p': (Tv_b_inv * 100, 'Pixel veg temperature(in K,*100),Scale = 100, type = uint16', np.uint16),
        }

        for dset_name, (data, description, dtype) in datasets.items():
            if dset_name in f:
                del f[dset_name]
            dset = f.create_dataset(dset_name, data=data, dtype=dtype, compression='gzip')
            dset.attrs['description'] = description

        # 关闭文件
        f.close()
        print(f"Complete！")

        end = time.time()
        print('time cost: ', end - start, 's')

    if len(error_files)!=0:
        with open(error_file_dir, 'w') as f:
            for error_file in error_files:
                f.write(f"{error_file}\n")