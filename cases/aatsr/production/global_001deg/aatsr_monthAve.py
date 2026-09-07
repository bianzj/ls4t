import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from cases.AATSR_product.util.util_aatsr import *

indir0 = r"/media/hero/aatsr_data/"
outdir00 = r"/media/hero/aatsr_data/"

# indir0 = r"g:/"
# outdir0 = r"g:/"

indir_lst0 = indir0 + r"/aatsr_lst//"
indir_lsct0 = indir0 + r"/aatsr_lsct_v1.0/"
indir_clo0 = indir0 + r"/aatsr_clo/"
indir_ang0 = indir0 + r"/aatsr_ang//"
indir_loc0 = indir0 + r"/aatsr_loc//"
indir_aux0 = indir0 + r"/aatsr_aux//"

outdir0 = outdir00 + r"/aatsr_lsct_month_v1.0//"
mkdir_if_not_exist(outdir0)
error_file = outdir0 + 'error.txt'

# 新增日均输出目录
outdir_day = outdir00 + r"/aatsr_lsct_day_v1.0//"
mkdir_if_not_exist(outdir_day)

'''
白天夜晚：sza < 90; sza<=0 or sza > 90
温度阈值：250-350
云检测阈值：cloN_maks == 1 * cloF_mask == 1
温度差异：|Ts - lstN| < 30(10); |Ts - Tv| < 30(15); |lstN - Tv| < 20(10)
'''

infile_ref = indir0 + r'/base/type/ref_world_0.05.tif'
ref0, ns0, nl0, nb0, geog0, proj0 = read_image_gdal(infile_ref)
Tmin_threshold = 25300
Tmax_threshold = 35000

for kyear in range(2003, 2013):
    for kmonth in range(1, 13):

        lstN_day_all = np.zeros([nl0, ns0], dtype=np.float32)
        Ts_day_all = np.zeros([nl0, ns0], dtype=np.float32)
        lstO_day_all = np.zeros([nl0, ns0], dtype=np.float32)
        Tv_day_all = np.zeros([nl0, ns0], dtype=np.float32)
        count_day_all = np.zeros([nl0, ns0], dtype=np.float32)

        lstN_night_all = np.zeros([nl0, ns0], dtype=np.float32)
        Ts_night_all = np.zeros([nl0, ns0], dtype=np.float32)
        lstO_night_all = np.zeros([nl0, ns0], dtype=np.float32)
        Tv_night_all = np.zeros([nl0, ns0], dtype=np.float32)
        count_night_all = np.zeros([nl0, ns0], dtype=np.float32)

        outfile1 = outdir0 + "aatsr_%04d_" % kyear + "%02d" % kmonth + "_day.h5"
        if os.path.exists(outfile1): continue

        for kday in range(1, 32):
            print('--------%04d-%02d-%02d----------' % (kyear, kmonth, kday))

            # 初始化当天数据数组
            lstN_day_day = np.zeros([nl0, ns0], dtype=np.float32)
            Ts_day_day = np.zeros([nl0, ns0], dtype=np.float32)
            lstO_day_day = np.zeros([nl0, ns0], dtype=np.float32)
            Tv_day_day = np.zeros([nl0, ns0], dtype=np.float32)
            count_day_day = np.zeros([nl0, ns0], dtype=np.float32)

            lstN_night_day = np.zeros([nl0, ns0], dtype=np.float32)
            Ts_night_day = np.zeros([nl0, ns0], dtype=np.float32)
            lstO_night_day = np.zeros([nl0, ns0], dtype=np.float32)
            Tv_night_day = np.zeros([nl0, ns0], dtype=np.float32)
            count_night_day = np.zeros([nl0, ns0], dtype=np.float32)

            indir_lst = indir_lst0 + "%04d" % kyear + "/%02d/" % kmonth + "%02d/" % kday
            indir_lsct = indir_lsct0 + "%04d" % kyear + "/%02d/" % kmonth + "%02d/" % kday
            indir_loc = indir_loc0 + "%04d" % kyear + "/%02d/" % kmonth + "%02d/" % kday
            indir_ang = indir_ang0 + "%04d" % kyear + "/%02d/" % kmonth + "%02d/" % kday
            indir_clo = indir_clo0 + "%04d" % kyear + "/%02d/" % kmonth + "%02d/" % kday
            indir_aux = indir_aux0 + "%04d" % kyear + "/%02d/" % kmonth + "%02d/" % kday

            if os.path.exists(indir_lsct) == 0: continue
            fileNames = search_file_rej(indir_lsct, ['h5'], 'xml')
            fileNum = len(fileNames)
            for i, fileName in enumerate(fileNames):

                infile_lsct = indir_lsct + fileName
                offsy = 12  ### 8/13
                infile_lst = indir_lst + fileName[:-offsy] + "_lst.h5"
                infile_loc = indir_loc + fileName[:-offsy] + "_loc.h5"
                infile_ang = indir_ang + fileName[:-offsy] + "_ang.h5"
                infile_clo = indir_clo + fileName[:-offsy] + "_clo.h5"
                infile_aux = indir_aux + fileName[:-offsy] + "_aux.h5"

                # print(infile_lst)
                print('%02d/%02d:' % (i + 1, fileNum), fileName[:-8])
                if (os.path.exists(infile_lsct) == 0) or (os.path.exists(infile_lsct) == 0): continue

                try:
                    fin = h5py.File(infile_lst)
                    lstN = fin['lstN'][:]
                    lstO = fin['lstO'][:]
                    fin.close()

                    fin_ = h5py.File(infile_loc)
                    indx = fin_['indx'][:]
                    indy = fin_['indy'][:]
                    fin_.close()

                    fin_ = h5py.File(infile_ang)
                    sza = fin_['sza'][:]
                    sza = 90 - sza / 100
                    fin_.close()

                    fin = h5py.File(infile_lsct)
                    # Ts = fin['Ts_p'][:]
                    # Tv = fin['Tv_p'][:]
                    Ts = fin['Ts'][:]
                    Tv = fin['Tv'][:]
                    fin.close()

                    cloN_mask, cloF_mask = aatsr_read_clo(infile_clo)

                    # fin = h5py.File(infile_aux)
                    # LAI = fin['LAI'][:]
                    # fin.close()

                except Exception as e:
                    print(e)
                    with open(error_file, 'a', encoding='utf-8') as f:
                        f.write(f"{infile_lsct}: {str(e)}\n")
                        import traceback

                        f.write(f"{traceback.format_exc()}\n")
                    continue

                if sza.shape != lstN.shape:
                    with open(error_file, 'a', encoding='utf-8') as f:
                        f.write(f"{infile_lsct}: shape of sza is not equal to lstN\n")
                        f.write(f"sza shape: {sza.shape}, lstN shape: {lstN.shape}\n")
                    continue

                indx = np.int_(indx / 5)
                indy = np.int_(indy / 5)
                # print(infile_lsct)

                # 筛选条件
                ind_all = (lstN > Tmin_threshold) * (lstN < Tmax_threshold) * (lstO > Tmin_threshold) * (
                            lstO < Tmax_threshold)
                ind_all = ind_all * (Ts > Tmin_threshold) * (Ts < Tmax_threshold) * (Tv > Tmin_threshold) * (
                            Tv < Tmax_threshold)
                # ind_all = ind_all * (cloN_mask == 1) * (cloF_mask == 1)
                # ind_all = ind_all * (LAI > 100) * (LAI < 10000) # LAI scale 1000 100-> 0.1

                # day
                ind = None
                ind_day = (sza < 89.9) * (sza > 0.1)
                ind = ind_all * ind_day
                ind = ind * (np.abs(lstN * 1.0 - Tv * 1.0) < 1500) * (np.abs(Ts * 1.0 - Tv * 1.0) < 2500) * (
                            np.abs(lstN * 1.0 - Ts * 1.0) < 2000)

                count = np.sum(ind)
                # print(count)
                # 累积到日平均
                lstN_day_day[indx[ind], indy[ind]] += lstN[ind]
                lstO_day_day[indx[ind], indy[ind]] += lstO[ind]
                Ts_day_day[indx[ind], indy[ind]] += Ts[ind]
                Tv_day_day[indx[ind], indy[ind]] += Tv[ind]
                count_day_day[indx[ind], indy[ind]] += 1

                # 累积到月平均
                lstN_day_all[indx[ind], indy[ind]] += lstN[ind]
                lstO_day_all[indx[ind], indy[ind]] += lstO[ind]
                Ts_day_all[indx[ind], indy[ind]] += Ts[ind]
                Tv_day_all[indx[ind], indy[ind]] += Tv[ind]
                count_day_all[indx[ind], indy[ind]] += 1

                # night
                ind = None
                ind_night = (sza > 89.9) + (sza < 0.1)
                ind = ind_all * ind_night
                ind = ind * (np.abs(lstN * 1.0 - Tv * 1.0) < 750) * (np.abs(Ts * 1.0 - Tv * 1.0) < 1250) * (
                            np.abs(lstN * 1.0 - Ts * 1.0) < 1000)
                count = np.sum(ind)
                # print(count)

                # 累积到日平均
                lstN_night_day[indx[ind], indy[ind]] += lstN[ind]
                lstO_night_day[indx[ind], indy[ind]] += lstO[ind]
                Ts_night_day[indx[ind], indy[ind]] += Ts[ind]
                Tv_night_day[indx[ind], indy[ind]] += Tv[ind]
                count_night_day[indx[ind], indy[ind]] += 1

                # 累积到月平均
                lstN_night_all[indx[ind], indy[ind]] += lstN[ind]
                lstO_night_all[indx[ind], indy[ind]] += lstO[ind]
                Ts_night_all[indx[ind], indy[ind]] += Ts[ind]
                Tv_night_all[indx[ind], indy[ind]] += Tv[ind]
                count_night_all[indx[ind], indy[ind]] += 1

            # 计算日平均并输出
            ind = count_day_day > 0
            if np.sum(ind) > 0:
                lstN_day_day[ind] = lstN_day_day[ind] / count_day_day[ind]
                lstO_day_day[ind] = lstO_day_day[ind] / count_day_day[ind]
                Tv_day_day[ind] = Tv_day_day[ind] / count_day_day[ind]
                Ts_day_day[ind] = Ts_day_day[ind] / count_day_day[ind]

                # 输出日均（白天）
                outfile_day = outdir_day + "aatsr_%04d_" % kyear + "%02d_" % kmonth + "%02d" % kday + "_day.h5"
                name_list = ['Ts', 'Tv', 'Tnadir', 'Tobliq']
                data_list = [Ts_day_day, Tv_day_day, lstN_day_day, lstO_day_day]
                dtype_list = ['uint16', 'uint16', 'uint16', 'uint16']
                write_h5py_file(outfile_day, name_list, data_list, dtype_list, compression='gzip', ifcover=1)

            ind = count_night_day > 0
            if np.sum(ind) > 0:
                lstN_night_day[ind] = lstN_night_day[ind] / count_night_day[ind]
                lstO_night_day[ind] = lstO_night_day[ind] / count_night_day[ind]
                Tv_night_day[ind] = Tv_night_day[ind] / count_night_day[ind]
                Ts_night_day[ind] = Ts_night_day[ind] / count_night_day[ind]

                # 输出日均（夜晚）
                outfile_day = outdir_day + "aatsr_%04d_" % kyear + "%02d_" % kmonth + "%02d" % kday + "_night.h5"
                name_list = ['Ts', 'Tv', 'Tnadir', 'Tobliq']
                data_list = [Ts_night_day, Tv_night_day, lstN_night_day, lstO_night_day]
                dtype_list = ['uint16', 'uint16', 'uint16', 'uint16']
                write_h5py_file(outfile_day, name_list, data_list, dtype_list, compression='gzip', ifcover=1)

        # 计算月平均并输出（白天）
        ind = count_day_all > 0
        lstN_day_all[ind] = lstN_day_all[ind] / count_day_all[ind]
        lstO_day_all[ind] = lstO_day_all[ind] / count_day_all[ind]
        Tv_day_all[ind] = Tv_day_all[ind] / count_day_all[ind]
        Ts_day_all[ind] = Ts_day_all[ind] / count_day_all[ind]

        # 计算月平均并输出（夜晚）
        ind = count_night_all > 0
        lstN_night_all[ind] = lstN_night_all[ind] / count_night_all[ind]
        lstO_night_all[ind] = lstO_night_all[ind] / count_night_all[ind]
        Tv_night_all[ind] = Tv_night_all[ind] / count_night_all[ind]
        Ts_night_all[ind] = Ts_night_all[ind] / count_night_all[ind]

        if (np.sum(lstN_day_all) > 3):
            outfile1 = outdir0 + "aatsr_%04d_" % kyear + "%02d" % kmonth + "_day.h5"
            name_list = ['Ts', 'Tv', 'Tnadir', 'Tobliq']
            data_list = [Ts_day_all, Tv_day_all, lstN_day_all, lstO_day_all]
            dtype_list = ['uint16', 'uint16', 'uint16', 'uint16']
            write_h5py_file(outfile1, name_list, data_list, dtype_list, compression='gzip', ifcover=1)

        if (np.sum(lstN_night_all) > 3):
            outfile2 = outdir0 + "aatsr_%04d_" % kyear + "%02d" % kmonth + "_night.h5"
            name_list = ['Ts', 'Tv', 'Tnadir', 'Tobliq']
            data_list = [Ts_night_all, Tv_night_all, lstN_night_all, lstO_night_all]
            dtype_list = ['uint16', 'uint16', 'uint16', 'uint16']
            write_h5py_file(outfile2, name_list, data_list, dtype_list, compression='gzip', ifcover=1)