import numpy as np
from scipy import interpolate
import matplotlib.mlab as ml
import matplotlib.pyplot as plt
import time
from util.rt.crown import *
from util.rt.hom import *
from util.util import *
from multiprocessing import Pool
from util.util_inversion_hotspot import *
from util.util_inversion_hotspot_simulation import *
import warnings
warnings.filterwarnings("ignore")

from util_lsct import *

'''2024.7.8'''
'''三角度反演组分温度最新版'''
'''2022年DM站'''

def ifexist_angles(indir_tif , fileName):
    infileVzaN = indir_tif + fileName + '_vza_nadir.tif'
    infileVaaN = indir_tif + fileName + '_vaa_nadir.tif'
    infileVzaO = indir_tif + fileName + '_vza_obliq.tif'
    infileVaaO = indir_tif + fileName + '_vaa_obliq.tif'
    infileTime = indir_tif + fileName + '_time.tif'

    c1 = os.path.exists(infileVzaN)
    c2 = os.path.exists(infileVaaN)
    c3 = os.path.exists(infileVzaO)
    c4 = os.path.exists(infileVaaO)
    if c1 * c2 * c3 * c4 == 0:
        print(fileName + ' lack observation angle data')
        return False

    infileSza = indir_tif + fileName + '_sza_nadir.tif'
    infileSaa = indir_tif + fileName + '_saa_nadir.tif'
    c1 = os.path.exists(infileSza)
    c2 = os.path.exists(infileSaa)
    if c1 * c2 == 0:
        print(fileName + ' lack sun angle data')
        return False
    return infileVzaN,infileVaaN,infileVzaO,infileVaaO,infileTime,infileSza,infileSaa

def ifexist_LAI(indir_fvc , fileName):
    '''判断fvc和lai'''
    infileFvcN = indir_fvc + fileName + '_fvcN.tif'
    infileFvcO = indir_fvc + fileName + '_fvcO.tif'
    infileFvcAhi = indir_fvc + fileName + '_fvcAhi.tif'
    c1 = os.path.exists(infileFvcN)
    c2 = os.path.exists(infileFvcO)
    c3 = os.path.exists(infileFvcAhi)
    if c1 * c2 * c3 == 0:
        print(fileName + ' lack fvc data')
        return False
    infileLai = indir_lai + yearStr + "_" + doyStr + '_lai.tif'
    if os.path.exists(infileLai) == 0:
        print(fileName + ' lack LAI data')
        return False
    return infileFvcN,infileFvcO,infileFvcAhi,infileLai

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

if __name__ == '__main__':
    '''读入数据'''
    indir_lstN = r'D:\data\LSCT3\LSCT_dm_2022\1_slstr\lst/'
    indir_lstAhi = r'D:\data\LSCT3\LSCT_dm_2022\1_ahi\ahi_lst/'
    indir_tif = r'D:\data\LSCT3\LSCT_dm_2022\1_slstr\tif/'
    indir_fvc = r'D:\data\LSCT3\LSCT_dm_2022\2_fvc(lai)//'
    indir_lai = r'D:\data\LSCT3\LSCT_dm_2022\2_lai//'
    indir_type = r'D:\data\LSCT3\LSCT_dm_2022\0_base\type/'
    indir_ems = r'D:\data\LSCT3\LSCT_dm_2022\0_base\emis/'
    infile_soil_emis = indir_ems + 'emis1_heihe_utm47N_1000.tif'
    infile_type = indir_type + 'type_heihe_1000_utm47N.tif'
    infile_veg_emis = indir_ems + 'IGBP_Emi.txt'
    infileVzaAhi = r'D:\data\LSCT3\LSCT_dm_2022\0_base\ahi_angle\AHI_vza_heihe_utm47N_2000.tif'
    infileVaaAhi = r'D:\data\LSCT3\LSCT_dm_2022\0_base\ahi_angle\AHI_vaa_heihe_utm47N_2000.tif'

    '''保存结果'''
    time_ = []
    doy_ = []
    lai_ = []
    cloud_nadir_ = []
    cloud_obliq_ = []
    ts_ = []
    tsl_ = []
    tsh_ = []
    tc_ = []
    ts2_ = []
    tc2_ = []
    lst_ = []
    lsct2_outfile = r'D:\data\LSCT3\LSCT_dm_2022\3_lsct\lsct2.txt'
    lsct3_outfile = r'D:\data\LSCT3\LSCT_dm_2022\3_lsct\lsct3.txt'
    lsct3_hom_outfile = r'D:\data\LSCT3\LSCT_dm_2022\3_lsct\lsct3_hom.txt'


    '''找反演的点的坐标'''
    lat_ = np.asarray([38.84891739])
    lon_ = np.asarray([100.3717674])
    # lat_ = np.asarray([38.85544116])
    # lon_ = np.asarray([100.3742415])
    type, ns, nl, nb, geog, proj, dataset = read_image_dataset_gdal(infile_type)
    imagex_, imagey_ = loc2map(lon_, lat_, dataset)

    '''读取发射率'''
    [emis_s, ns, nl, nb, geog, proj] = read_image_gdal(infile_soil_emis)
    if np.average(emis_s[emis_s > 0]) > 1.0:
        emis_s = emis_s / 1000.0
    [classif, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_type)
    classif = np.asarray(classif, np.int)
    emis_v = read_txt_array(infile_veg_emis, 0, 2)
    emis_v = emis_v[classif, 0] / 1000.0

    filesName = search_file_rej(indir_lstN, ['lst_nadir'], 'enp')
    filesNum = len(filesName)
    ahiFileNames = search_file(indir_lstAhi, ['lst'])
    for fileI in range(filesNum):
        fileName = filesName[fileI][:-14]
        doyStr = fileName[-3:]
        yearStr = fileName[4:8]
        month, day = doy2date(int(yearStr), int(doyStr))
        print("-----------------------%02d-%02d-%02d(%03d)-----------------------" % (
        int(yearStr), month, day, int(doyStr)))
        '''判断输入是否存在'''
        # if int(doyStr) !=206: continue
        if not ifexist_angles(indir_tif, fileName):
            continue
        infileVzaN, infileVaaN, infileVzaO, infileVaaO, infileTime, infileSza, infileSaa = ifexist_angles(indir_tif,
                                                                                                          fileName)
        if not ifexist_LAI(indir_fvc, fileName):
            continue
        infileFvcN, infileFvcO, infileFvcAhi, infileLai = ifexist_LAI(indir_fvc, fileName)

        infileLstN = indir_lstN + fileName + '_lst_nadir.tif'
        infileLstO = indir_lstN + fileName + '_lst_obliq.tif'
        ahifileArr = [ahifile for ahifile in ahiFileNames if doyStr + '_' in ahifile]
        if np.size(ahifileArr) <= 1:
            print("lack Ahi data")
            continue
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
        if c1 * c2 * c3 * c4 == 0:
            print(fileName + ' lack lst data')
            continue

        '''读入温度和各种数据'''
        [lstN, width, height, bands, geog, proj] = read_image_gdal(infileLstN)
        [lstO, width, height, bands, geog, proj] = read_image_gdal(infileLstO)
        [lstAhi1, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileLstAhi1)
        [lstAhi2, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileLstAhi2)
        [slstrTime_data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infileTime)

        ahiTime1 = ahiTime1 // 100 * 60 + ahiTime1 % 100 + 1.66  # 1.66
        ahiTime2 = ahiTime2 // 100 * 60 + ahiTime2 % 100 + 1.66
        slstrTime = (slstrTime_data[102, 95] / 100)
        slstrTime = slstrTime // 100 * 60 + slstrTime % 100
        lstAhi = np.abs((slstrTime - ahiTime2) / 10) * lstAhi1 + np.abs((slstrTime - ahiTime1) / 10) * lstAhi2

        if (fileName[0:3] == "S3A"):
            lstAhi = lstAhi * 0.9727491898535005 + 8.14384409751824
        else:
            lstAhi = lstAhi * 0.9738654689993518 + 7.602965534546172

        lstAhi = resize_data(lstAhi, nl, ns, method=cv2.INTER_NEAREST)
        [lai, ns, nl, nb, geog, proj] = read_image_gdal(infileLai)
        [fvcN, ns, nl, nb, geog, proj] = read_image_gdal(infileFvcN)
        [fvcO, ns, nl, nb, geog, proj] = read_image_gdal(infileFvcO)
        [fvcM, ns, nl, nb, geog, proj] = read_image_gdal(infileFvcAhi)
        [vza_n, ns, nl, nb, geog, proj] = read_image_gdal(infileVzaN)
        [vaa_n, ns, nl, nb, geog, proj] = read_image_gdal(infileVaaN)
        [vza_o, ns, nl, nb, geog, proj] = read_image_gdal(infileVzaO)
        [vaa_o, ns, nl, nb, geog, proj] = read_image_gdal(infileVaaO)
        [vza_a, ns_m, nl_m, nb_m, geog_m, proj_m] = read_image_gdal(infileVzaAhi)
        [vaa_a, ns_m, nl_m, nb_m, geog_m, proj_m] = read_image_gdal(infileVaaAhi)
        [sza, ns, nl, nb, geog, proj] = read_image_gdal(infileSza)
        [saa, ns, nl, nb, geog, proj] = read_image_gdal(infileSaa)
        vaa_a = resize_data(vaa_a, nl, ns)
        vza_a = resize_data(vza_a, nl, ns)


        '''有效发射率w'''
        wavelength = 10.8
        hspot = 1.0
        hcr = 1.75
        rcr = 1.25
        vsa_n = np.abs(vaa_n - saa)
        vsa_o = np.abs(vaa_o - saa)
        vsa_a = np.abs(vaa_a - saa)
        # 2000/(1000*1000) = 0.002
        # FVC 0.2 -> 0.0025
        std = 0.15
        emissivity_soil = 0.95842
        emissivity_leaf = 0.975682
        e_s = emissivity_soil
        e_v = emissivity_leaf
        t = type[imagex_, imagey_]
        lai0 = lai[imagex_, imagey_]
        lai0 = [np.average(lai[imagex_[0]-1:imagex_[0]+2, imagey_[0]-1:imagey_[0]+2])]
        VZA = np.reshape([vza_n[imagex_, imagey_], vza_o[imagex_, imagey_], vza_a[imagex_, imagey_]], (1, 3))[0]
        SZA = np.reshape([sza[imagex_, imagey_], sza[imagex_, imagey_], sza[imagex_, imagey_]], (1, 3))[0]
        RAA = np.reshape([vsa_n[imagex_, imagey_], vsa_o[imagex_, imagey_], vsa_a[imagex_, imagey_]], (1, 3))[0]
        Emis = sample_crown_Emis(lai0[0], hspot, std, rcr, hcr, wavelength, emissivity_soil, emissivity_leaf, VZA,
                                 SZA, RAA)
        Emis_nadir =  sample_crown_Emis(lai0[0], hspot, std, rcr, hcr, wavelength, emissivity_soil, emissivity_leaf, [0.0], [SZA[0]], [180.0])
        Emis = np.transpose(Emis)
        w = np.zeros([3, 3])
        w[:, 0:2] = Emis[:, 0:2]
        w[:, 2] = Emis[:, 2] + Emis[:, 3]

        '''观测向量b'''
        # 设置EVO站点附近的发射率
        fvcN0 = fvcN[imagex_, imagey_][0]
        fvcO0 = fvcO[imagex_, imagey_][0]
        fvcM0 = fvcM[imagex_, imagey_][0]
        emisN = (1 - fvcN0) * emis_s[imagex_, imagey_] + fvcN0 * emis_v[imagex_, imagey_]
        emisO = (1 - fvcO0) * emis_s[imagex_, imagey_] + fvcO0 * emis_v[imagex_, imagey_]
        emisM = (1 - fvcM0) * emis_s[imagex_, imagey_] + fvcM0 * emis_v[imagex_, imagey_]
        lstN0 = lstN[imagex_, imagey_][0]
        lstO0 = lstO[imagex_, imagey_][0]
        lstA0 = lstAhi[imagex_, imagey_][0]
        print("LSTN=%.2f LSTO=%.2f LSTA=%.2f" % (lstN0, lstO0, lstA0))
        if lstN0 * lstO0 * lstA0 == 0: continue
        if (lstN0<270) or (lstO0 < 270): continue
        # if np.abs(lstN0 - lstO0) > 5: continue
        # if np.abs(lstN0 - lstA0) > 10: continue

        b = np.array(
            [planck(wavelength, lstN0) * emisN[0], planck(wavelength, lstO0) * emisO[0], planck(wavelength, lstA0) * emisM[0]])

        # doy_.append(int(doyStr))
        # time_.append(slstrTime * 100)
        # lai_.append(lai0[0])

        '''初值范围'''
        '''确定温差限制'''
        DT = 1
        if DT == 1:
            Ts_Tv_range = [-5, 15]
            Tsl_Tsh_range, Tsh_Tv_range = [0, 10], [-5, 5]
        if DT == 3:
            Ts_Tv_range = [0, 30]
            Tsl_Tsh_range, Tsh_Tv_range = [5, 25], [-10, 10]
        if DT == 5:
            Ts_Tv_range = [5, 45]
            Tsl_Tsh_range, Tsh_Tv_range = [10, 40], [-15, 15]

        # Ts_Tv_range = [-5, 15]
        # Tsl_Tsh_range, Tsh_Tv_range = [5, 25], [-10, 10]

        '''三角度'''
        '''crown'''
        flag = 3
        w_2 = np.zeros((2,3))
        Emis = np.transpose(Emis)
        w_2[0,:] = Emis[0,:] + Emis[1,:]
        w_2[1,:] = Emis[2,:] + Emis[3,:]
        coeff0 = fitting_linear_constraint_3angle_2component(w_2, b, Ts_Tv_range)
        lsct2 = inv_planck(10.8, np.array(coeff0))
        print("初值：  %.2f,%.2f" % (lsct2[0], lsct2[1]))
        ts2_.append(float(lsct2[0]))
        tc2_.append(float(lsct2[1]))

        coeff = fitting_linear_constraint_3angle_3component(w.T, b, Tsl_Tsh_range, Tsh_Tv_range)
        lsct0 = np.reshape(inv_planck(10.8, np.array(coeff)), (-1))
        Psoil = gap_probability_crown_analytical(lai0[0], std, hcr, rcr, SZA[0], G=0.5)
        Ts0 = inv_planck(10.8, planck(10.8, lsct0[0]) * Psoil + planck(10.8, lsct0[1]) * (1 - Psoil))
        print("inv：  %.2f(%.2f,%.2f),%.2f" % (Ts0, lsct0[0], lsct0[1], lsct0[2]))
        tsl = float(lsct0[0])
        tsh = float(lsct0[1])
        tv = float(lsct0[2])
        tsl_.append(tsl)
        tsh_.append(tsh)
        tc_.append(tv)
        ts_.append(Ts0)
        lst = inv_planck(wavelength, (((Emis_nadir[0] ) * planck(wavelength, tsl)+(Emis_nadir[1] ) * planck(wavelength, tsh) + (
                    Emis_nadir[2] + Emis_nadir[3]) * planck(wavelength, tv)) / np.sum(Emis_nadir)))
        # lst_.append(np.max([lstN0,lstO0,lstA0]))
        lst_.append(lst[0])

        # '''三角度'''
        # '''hom'''
        # flag = 0
        # Emis = sample_hom_Emis(lai0[0], hspot, wavelength, emissivity_soil, emissivity_leaf, VZA,
        #                          SZA, RAA)
        # Emis = np.transpose(Emis)
        # w = np.zeros([3, 3])
        # w[:, 0:2] = Emis[:, 0:2]
        # w[:, 2] = Emis[:, 2] + Emis[:, 3]
        #
        # x0 = solve_initial_3(b[0], b[1], b[2], w[0, :], w[1, :], w[2, :],Tsl_min, Tsl_max, Tsh_min, Tsh_max, Tv_min, Tv_max, Tsl_Tsh_min, Tsl_Tsh_max, Tsh_Tv_min, Tsh_Tv_max)
        # # x0 = solve_initial_3(b[0], b[1], b[2], w[0, :], w[1, :], w[2, :])
        # lsct = inv_lsct3_site(b[0], b[1], b[2], w[0, :], w[1, :], w[2, :], 0, 0, methodname=1, x0=x0, wl=10.8)
        # print("3 Retrieve result=")
        # print(lsct)
        # tsl = float(lsct[0])
        # tsh = float(lsct[1])
        # tv = float(lsct[2])
        # tsl_.append(tsl)
        # tsh_.append(tsh)
        # tc_.append(tv)
        # lst = inv_planck(wavelength, (((Emis_nadir[0] ) * planck(wavelength, tsl)+(Emis_nadir[1] ) * planck(wavelength, tsh) + (
        #             Emis_nadir[2] + Emis_nadir[3]) * planck(wavelength, tv)) / np.sum(Emis_nadir)))
        # lst_.append(lst[0])

        # '''两角度'''
        # flag = 2
        # x0 = solve_initial_2(b[0], b[1], b[2], w[0, :], w[1, :], w[2, :], Ts_min, Ts_max, Tv_min, Tv_max, Ts_Tv_min,
        #                      Ts_Tv_max)
        #
        # lsct = inv_lsct2_site(b[0], b[1], w[0, :], w[1, :], 0, 0, methodname=1, x0=x0, wl=10.8)
        # print("2 Retrieve result=")
        # print(lsct)
        # ts = float(lsct[0])
        # tv = float(lsct[1])
        # ts_.append(ts)
        # tc_.append(tv)
        # lst = inv_planck(wavelength,(((Emis_nadir[0]+Emis_nadir[1])*planck(wavelength,ts)+(Emis_nadir[2]+Emis_nadir[3])*planck(wavelength,tv))/np.sum(Emis_nadir)))
        # lst_.append(lst[0])

        # '''window'''
        # Emis_w = []
        # window_size = 3
        # w = np.zeros([window_size ** 2, 3, 3])
        # x_min, x_max, y_min, y_max = int(imagex_ - 1), int(imagex_ + 2), int(imagey_ - 1), int(imagey_ + 2)
        # lai0 = np.reshape(lai[x_min:x_max, y_min:y_max], (9, 1))
        # VZA = np.reshape(
        #     [vza_n[x_min:x_max, y_min:y_max], vza_o[x_min:x_max, y_min:y_max], vza_a[x_min:x_max, y_min:y_max]],
        #     (3, window_size ** 2))
        # SZA = np.reshape([sza[x_min:x_max, y_min:y_max], sza[x_min:x_max, y_min:y_max], sza[x_min:x_max, y_min:y_max]],
        #                  (3, window_size ** 2))
        # RAA = np.reshape(
        #     [vsa_n[x_min:x_max, y_min:y_max], vsa_o[x_min:x_max, y_min:y_max], vsa_a[x_min:x_max, y_min:y_max]],
        #     (3, window_size ** 2))
        # for i in range(9):
        #     Emis = np.transpose(
        #         sample_crown_Emis(lai0[i, :], hspot, std, rcr, hcr, wavelength, emissivity_soil, emissivity_leaf,
        #                           VZA[:, i],
        #                           SZA[:, i], RAA[:, i]))
        #     w[i, :, 0:2] = Emis[:, 0:2]
        #     w[i, :, 2] = Emis[:, 2] + Emis[:, 3]
        #
        # fvcN0, fvcO0, fvcM0 = fvcN[x_min:x_max, y_min:y_max], fvcO[x_min:x_max, y_min:y_max], fvcM[x_min:x_max,
        #                                                                                       y_min:y_max]
        # emisN = (1 - fvcN0) * e_s + fvcN0 * e_v
        # emisO = (1 - fvcO0) * e_s + fvcO0 * e_v
        # emisM = (1 - fvcM0) * e_s + fvcM0 * e_v
        # lstN0 = lstN[x_min:x_max, y_min:y_max]
        # lstO0 = lstO[x_min:x_max, y_min:y_max]
        # lstM0 = lstAhi[x_min:x_max, y_min:y_max]
        # b = np.array(
        #     [planck(wavelength, lstN0) * emisN, planck(wavelength, lstO0) * emisO, planck(wavelength, lstM0) * emisM])
        # w = np.reshape(w, (-1, 3))
        # b = np.reshape(b, (-1))
        # coeff_w = fitting_linear_constraint_3angle_3component_window(w, b, Tsl_Tsh_range, Tsh_Tv_range)
        # lsct_w = np.reshape(inv_planck(10.8, np.array(coeff_w)), (-1))
        # Ts_w = inv_planck(10.8, planck(10.8, lsct_w[0]) * Psoil + planck(10.8, lsct_w[1]) * (1 - Psoil))
        # print("inv_w：  %.2f(%.2f,%.2f),%.2f" % (Ts_w, lsct_w[0], lsct_w[1], lsct_w[2]))

        # tsl = float(lsct_w[0])
        # tsh = float(lsct_w[1])
        # tv = float(lsct_w[2])
        # tsl_.append(tsl)
        # tsh_.append(tsh)
        # tc_.append(tv)
        # ts_.append(Ts_w)
        # lst = inv_planck(wavelength,
        #                  (((Emis_nadir[0]) * planck(wavelength, tsl) + (Emis_nadir[1]) * planck(wavelength, tsh) + (
        #                          Emis_nadir[2] + Emis_nadir[3]) * planck(wavelength, tv)) / np.sum(Emis_nadir)))
        # lst_.append(lst[0])

        '''保存结果'''
        doy_.append(int(doyStr))
        time_.append(slstrTime_data[102, 95])
        lai_.append(lai0[0])
        # lst_.append(lstN0)
        infile_cloud_nadir = indir_tif + fileName + '_cloud_nadir.tif'
        infile_cloud_obliq = indir_tif + fileName + '_cloud_obliq.tif'
        [cloud_nadir, ns, nl, nb, geog, proj] = read_image_gdal(infile_cloud_nadir)
        [cloud_obliq, ns, nl, nb, geog, proj] = read_image_gdal(infile_cloud_obliq)
        cloud_nadir_.append(cloud_nadir[imagex_, imagey_])
        cloud_obliq_.append(cloud_obliq[imagex_, imagey_])


    time_ = np.asarray(time_)
    cloud_nadir_ = np.asarray(cloud_nadir_)
    cloud_obliq_ = np.asarray(cloud_obliq_)
    cloud1_ = cloud_nadir_[:, 0] + cloud_obliq_[:, 0]

    if flag==2:
        result = np.vstack([doy_, time_, lai_, cloud1_, lst_, ts_, tc_])
        result = np.transpose(result)
        np.savetxt(lsct2_outfile, result, fmt='%.3f')
    elif flag == 3:
        result = np.vstack([doy_, time_, lai_, cloud1_, lst_, tsl_,tsh_,ts_, tc_])
        result = np.transpose(result)
        np.savetxt(lsct3_outfile, result, fmt='%.3f')

        result = np.vstack([doy_, time_, lai_, cloud1_, lst_, ts2_, tc2_])
        result = np.transpose(result)
        np.savetxt(lsct2_outfile, result, fmt='%.3f')

    elif flag == 0:
        result = np.vstack([doy_, time_, lai_, cloud1_, lst_, tsl_,tsh_, tc_])
        result = np.transpose(result)
        np.savetxt(lsct3_hom_outfile, result, fmt='%.3f')