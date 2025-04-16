import sys
sys.path.append('//')
import time
from util.util import *
from multiprocessing import Pool, cpu_count
from util.rt.hom import *
from util.util_lsct3 import *
from pysolar.solar import *
from datetime import datetime,timezone,timedelta
import calendar
import warnings
warnings.filterwarnings("ignore")

'''2024.8.19'''
'''三组分 五像元 组分温度 + 植被参数 + DT'''


def read_aux_data(indir_emis, indir_type, indir_veg_pra):
    # 读取type emis std hcr rcr
    infile_type = indir_type + 'type_world_1000.tif'
    infile_soil_emis = indir_emis + r'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
    infile_veg_emis = indir_emis + 'IGBP_Emi.txt'
    infile_std = indir_veg_pra + "Tree_density(STD)/global_TreeDensity_0.01.tif"
    infile_TCC = indir_veg_pra + "Tree_cover(TCC)/global_TreeCover2010_0.01.tif"
    infile_hcr = indir_veg_pra + "Cnopy_height(hcr)/global_CanopyHeight_0.01.tif"
    infile_vzaN = indir_type + r"vza_n.tif"
    infile_vaaN = indir_type + r"vaa_n.tif"
    infile_vzaO = indir_type + r"vza_f.tif"
    infile_vaaO = indir_type + r"vaa_f.tif"
    [emis_s, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_soil_emis)
    [classif, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_type)
    [std, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_std)
    [TCC, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_TCC)
    [hcr, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_hcr)
    [vzaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vzaN)
    [vaaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaaN)
    [vzaO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vzaO)
    [vaaO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaaO)
    vzaN, vzaO, vaaN, vaaO = 90 - vzaN / 100, 90 - vzaO / 100, vaaN / 100, vaaO / 100
    hcr = np.nan_to_num(hcr,0.0)
    emis_s = emis_s / 1000
    classif = np.asarray(classif, np.int_)
    classif[classif == 255] = 17
    emis_v = read_txt_array(infile_veg_emis, 0, 2)
    emis_v = emis_v[classif, 0] / 1000
    return emis_s, emis_v, classif, std, TCC, hcr, vzaN, vzaO, vaaN, vaaO

def determine_DT(DT,month,lat_arr):
    if np.isin(month, [1, 2, 3]):
        DT[lat_arr > 66.5] = 1
        DT[(lat_arr < 66.5) * (lat_arr > 23.5)] = 2
        DT[(lat_arr < 23.5) * (lat_arr > 0)] = 4
        DT[(lat_arr < 0) * (lat_arr > -23.5)] = 5
        DT[(lat_arr < -23.5) * (lat_arr > -66.5)] = 4
        DT[(lat_arr < -66.5)] = 3
    elif np.isin(month, [4,5,6]):
        DT[lat_arr > 66.5] = 2
        DT[(lat_arr < 66.5) * (lat_arr > 23.5)] = 3
        DT[(lat_arr < 23.5) * (lat_arr > 0)] = 5
        DT[(lat_arr < 0) * (lat_arr > -23.5)] = 4
        DT[(lat_arr < -23.5) * (lat_arr > -66.5)] = 3
        DT[(lat_arr < -66.5)] = 2
    elif np.isin(month, [7,8,9]):
        DT[lat_arr > 66.5] = 3
        DT[(lat_arr < 66.5) * (lat_arr > 23.5)] = 4
        DT[(lat_arr < 23.5) * (lat_arr > 0)] = 5
        DT[(lat_arr < 0) * (lat_arr > -23.5)] = 4
        DT[(lat_arr < -23.5) * (lat_arr > -66.5)] = 2
        DT[(lat_arr < -66.5)] = 1
    elif np.isin(month, [10,11,12]):
        DT[lat_arr > 66.5] = 2
        DT[(lat_arr < 66.5) * (lat_arr > 23.5)] = 3
        DT[(lat_arr < 23.5) * (lat_arr > 0)] = 4
        DT[(lat_arr < 0) * (lat_arr > -23.5)] = 5
        DT[(lat_arr < -23.5) * (lat_arr > -66.5)] = 3
        DT[(lat_arr < -66.5)] = 2
    return DT

if __name__ == '__main__':
    # 年 月 日
    year = 2005
    month = 1

    # day = 16

    # hdf 路径
    AATSR_dir = r"/media/hero/lsct03/AATSR/%04d//" % year

    # base 文件路径
    base_dir = r"/home/hero/data/base/0_base//"
    indir_emis = base_dir + r"emis/"
    indir_type = base_dir + r"type/"
    indir_veg_pra = base_dir + "Veg_para/"

    # 读取辅助数据
    emis_s_arr, emis_v_arr, classif_arr, std_arr, TCC_arr, hcr_arr, vzaN_arr, vzaO_arr, vaaN_arr, vaaO_arr = read_aux_data(
        indir_emis, indir_type, indir_veg_pra)

    # 查找AATSR hdf tif文件
    indir_hdf = AATSR_dir + "hdf/"
    outdir_hdf = AATSR_dir + "lsct_hdf/"
    # outdir_hdf = r"/home/hero/data/AATSR/%04d//" % year + "lsct_hdf/"
    mkdir_if_not_exist(outdir_hdf)

    daynum = calendar.monthrange(year, month)[1]
    for day in range(1, daynum + 1):


        indir_hdf_day = indir_hdf + r"/%02d/%02d//" % (month, day)
        outdir_hdf_day = outdir_hdf + r"/%02d/%02d//" % (month, day)
        mkdir_if_not_exist(outdir_hdf_day)

        fileNames = search_file_rej(indir_hdf_day, ['.h5'], 'enp')
        for i, fileName in enumerate(fileNames):
            # if i ==0: continue
            print(i, fileName)
            start = time.time()

            # 读取数据
            infile_h5 = indir_hdf_day + fileName
            outfile = outdir_hdf_day + fileName[:-3] + "_lsct.h5"
            if os.path.exists(outfile): continue
            items = name_list = ["lon", 'lat', "indx", "indy", "time", "LAI", 'sza', 'saa', 'clo_N', 'clo_O', "lstN",
                                 "lstO"]
            lon_arr, lat_arr, indx, indy, time_, lai, sza, saa, cloN, cloO, lstN, lstO = read_h5py_items(infile_h5, items)
            lstN, lstO = lstN / 100, lstO / 100
            sza, saa = sza / 100, saa / 100
            lai = lai / 1000

            # 根据indx indy调整参数
            nl, ns = np.shape(lon_arr)
            vzaN, vzaO, vaaN, vaaO = vzaN_arr[:nl, :], vzaO_arr[:nl, :], vaaN_arr[:nl, :], vaaO_arr[:nl, :]
            emis_s = np.reshape(emis_s_arr[indx, indy], [nl, ns])
            emis_v = np.reshape(emis_v_arr[indx, indy], [nl, ns])
            classif = np.reshape(classif_arr[indx, indy], [nl, ns])
            tcc = np.reshape(TCC_arr[indx, indy], [nl, ns])
            std = np.reshape(std_arr[indx, indy], [nl, ns])
            hcr = np.reshape(hcr_arr[indx, indy], [nl, ns])

            #  计算L能量
            wl = 10.8
            fvcN = 1 - gap_probability_hom_analytical(lai, vzaN)
            fvcO = 1 - gap_probability_hom_analytical(lai, vzaO)
            radN = planck(wl, lstN)
            radN = radN * (fvcN * emis_v + (1 - fvcN) * emis_s)
            radO = planck(wl, lstO)
            radO = radO * (fvcO * emis_v + (1 - fvcO) * emis_s)

            #  计算w有效发射率
            wN4, wO4 = np.zeros([4, nl, ns]), np.zeros([4, nl, ns])
            wN, wO = np.zeros([3, nl, ns]), np.zeros([3, nl, ns])
            psoil = np.zeros([nl, ns])
            # 对于特定场景用crown，否则用hon
            crown_class = [1, 2, 3, 4, 5, 8, 9]
            ind_crown = np.isin(classif, crown_class) * (tcc != 0) * (std != 0) * (hcr != 0)
            # 均质场景
            hspot = 0.2
            wN4[:, ~ind_crown] = sample_hom_Emis(lai[~ind_crown], hspot, wl, emis_s[~ind_crown], emis_v[~ind_crown],
                                                 vzaN[~ind_crown], sza[~ind_crown],
                                                 np.abs(vaaN[~ind_crown] - saa[~ind_crown]))
            wO4[:, ~ind_crown] = sample_hom_Emis(lai[~ind_crown], hspot, wl, emis_s[~ind_crown], emis_v[~ind_crown],
                                                 vzaO[~ind_crown], sza[~ind_crown],
                                                 np.abs(vaaO[~ind_crown] - saa[~ind_crown]))
            psoil[~ind_crown] = gap_probability_hom_analytical(lai[~ind_crown], sza[~ind_crown])
            # 森林场景
            if sum(ind_crown) > 0:
                hspot = 1.0
                std = std / 1000000
                hcr = hcr / 2
                tcc = tcc / 100
                rcr = np.zeros([nl, ns])
                rcr[ind_crown] = np.sqrt(tcc[ind_crown] / np.pi / std[ind_crown])
                rcr[(rcr<0.5)*(rcr>0)] = 0.5
                rcr[rcr>30] = 30
                wN4[:, ind_crown] = sample_crown_Emis(lai[ind_crown], hspot, std[ind_crown], rcr[ind_crown], hcr[ind_crown], wl,
                                                      emis_s[ind_crown], emis_v[ind_crown], vzaN[ind_crown], sza[ind_crown],
                                                      np.abs(vaaN[ind_crown] - saa[ind_crown]))
                wO4[:, ind_crown] = sample_crown_Emis(lai[ind_crown], hspot, std[ind_crown], rcr[ind_crown], hcr[ind_crown], wl,
                                                      emis_s[ind_crown], emis_v[ind_crown], vzaO[ind_crown], sza[ind_crown],
                                                      np.abs(vaaO[ind_crown] - saa[ind_crown]))
                psoil[ind_crown] = gap_probability_crown_analytical(lai[ind_crown], std[ind_crown], hcr[ind_crown],
                                                                    rcr[ind_crown], sza[ind_crown])
            wN[:2, :, :] = wN4[0:2, :, :]
            wN[2, :, :] = wN4[2, :, :] + wN4[3, :, :]
            wO[:2, :, :] = wO4[0:2, :, :]
            wO[2, :, :] = wO4[2, :, :] + wO4[3, :, :]

            # mask掉纯像元和clound
            rad_th_max, rad_th_min = 20, 4.5
            fvc_th_max, fvc_th_min = 0.99, 0.03
            maskN = (radN > rad_th_min) * (radN < rad_th_max) * (
                        cloN <= 100)  # * (cloN != 0) * (fvcN > fvc_th_min) * (fvcN < fvc_th_max)
            maskO = (radO > rad_th_min) * (radO < rad_th_max) * (
                        cloO <= 100)  # * (cloO != 0) * (fvcO > fvc_th_min) * (fvcO < fvc_th_max)

            # 给定温差大小DT
            DT = np.zeros([nl, ns])
            DT = determine_DT(DT,month,lat_arr)

            '''多线程'''
            #  窗口大小
            window_size = 5
            off = int((window_size - 1) / 2)
            para = []
            for kn in range(off, nl - off):
                ###### 取wN的所有组分的n列，行全部，进行多线程的操作
                wNLine = wN[:, kn - off: kn + off + 1, :]
                wOLine = wO[:, kn - off: kn + off + 1, :]
                radNLine = radN[kn - off:kn + off + 1, :]
                radOLine = radO[kn - off:kn + off + 1, :]
                maskNLine = maskN[kn - off: kn + off + 1, :]
                maskOLine = maskO[kn - off: kn + off + 1, :]
                DTLine = DT[kn - off:kn + off + 1, :]
                # if kn<400: continue
                # a = inv_lsct3_AATSR_mpl(wNLine, wOLine, radNLine, radOLine, maskNLine,maskOLine, DTLine, ns)
                para.append([wNLine, wOLine, radNLine, radOLine, maskNLine, maskOLine, DTLine, ns])
            tasks = []
            pool = Pool(min(32, cpu_count()))
            for p in para:
                tasks.append(pool.apply_async(doMultiple_line_inv_3_AATSR, (p,)))
            pool.close()
            pool.join()
            results = [task.get() for task in tasks]
            lsct3 = np.asarray(results)

            [nl, nb, ns] = np.shape(lsct3)
            lsct3 = lsct3.transpose(1, 0, 2)
            # print(np.shape(lsct3))
            if (np.sum(lsct3[0, :, :] != 0) < 100):
                print(fileName + '_lsct.tif' + ' no result')
                continue

            lsct_save = np.zeros([3, nl + 2 * off, ns])
            lsct_save[:, off:-off, :] = lsct3
            lsct_save[:, ~maskN] = 0
            lsct_save[:, ~maskO] = 0

            Tsl_save = lsct_save[0,:,:]
            Tsh_save = lsct_save[1,:,:]
            Tv_save = lsct_save[2,:,:]
            Ts_save = inv_planck(wl, planck(wl,Tsl_save) * psoil + planck(wl,Tsh_save) * (1 - psoil))


            name_list = ['Tsl','Tsh','Tv','Ts']
            data_list = [Tsl_save*100, Tsh_save*100, Tv_save*100,Ts_save*100]
            dtype_list = ['uint16','uint16','uint16','uint16']
            write_h5py_file(outfile, name_list, data_list, dtype_list, compression=None, ifcover=1)
            # write_image_gdal(lsct_save.astype(uint16), 3, nl + 2 * off, ns, '', '', outfile)
            # outfile_maskN = outdir_hdf_day + fileName[:-3] + "maskN.tif"
            # write_image_gdal(maskN, 512, 43520, 1, '', '', outfile_maskN)
            # outfile_maskO = outdir_hdf_day + fileName[:-3] + "maskO.tif"
            # write_image_gdal(maskO, 512, 43520, 1, '', '', outfile_maskO)
            end = time.time()
            print('time cost: ', end - start, 's')
