from utils.old.util_lsct import *

'''2025.3.21'''
'''Fluxnet 站点3组分温度反演 crown 假设'''
'''用于方法测试，只反演目标像元保存结果到csv中'''

if __name__ == '__main__':
    raw_dir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/0_raw_h5_new/'
    out_dir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/results/lsct3_crown/aatsr_csv/'
    mkdir_if_not_exist(out_dir)

    site_names = search_dir(raw_dir, '')
    site_names.sort()
    infile_site_info_xls = r"/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet//FLUXSITE_imagexy.xlsx"
    sites_info = pd.read_excel(infile_site_info_xls)

    # base 文件路径
    base_dir = r"/home/hero/data/base/0_base/"
    indir_emis = base_dir + r"emis/"
    indir_type = base_dir + r"type/"
    indir_veg_pra = base_dir + "Veg_para/"

    std_gl, tcc_gl, hcr_gl = aatsr_read_crown_data(indir_veg_pra)

    for site_name in site_names:
        print("--------------------------------------------------------------------------------")
        print(site_name)
        if site_name != 'SN-Dhr': continue
        # if (site_name not in filtered_list): continue
        site_dir = os.path.join(raw_dir, site_name)
        site_out_file = out_dir + site_name + ".csv"
        # if os.path.exists(site_out_file): continue

        # 读取IGBP 分类
        # 1.常绿针叶 ENF 2.常绿阔叶 EBF 3.落叶针叶 DNF 4.落叶阔叶 DBF 5.混交林 MF 6.封闭灌木 CSH
        # 7.开阔灌木 OSH 8.木质稀疏草原 WSA 9. 稀疏草原 SAV 10.草原 GRA 11.永久湿地 WET
        # 12.农田 CRO 13.城市和建筑 URB 14.农田、自然植被 CVM 15.永久冰雪 SNO
        # 16.裸地 BSV 17.水体 WAT
        site_info = sites_info[sites_info["SITE_ID"] == site_name]
        IGBP = site_info['IGBP'].iloc[0]
        lon = site_info['LOCATION_LONG'].iloc[0]
        lat = site_info['LOCATION_LAT'].iloc[0]
        indx = site_info['IMAGEX'].iloc[0]
        indY = site_info['IMAGEY'].iloc[0]
        timezone = get_timezone(lat, lon)

        fileNames = search_file(site_dir, ['h5'])
        fileNames.sort()
        results_list = []
        for fileName in fileNames:
            print(fileName)
            # if fileName!='AATSR_2007_111_203420.h5': continue
            data = aatsr_read_sites(site_dir, fileName, timezone, lat, lon)
            if data is None:
                continue
            elif np.shape(data[0]) !=(5,5): continue
            lstN, lstF, lai, vzaN, vzaF, vaaN, vaaF, sza, saa, cloN,cloF, emisS, emisV, classif, utc_time, local_time,indx,indy = data
            ifday = local_time.hour < 18 and local_time.hour >= 8

            tcc = np.reshape(tcc_gl[indx, indy], [5, 5])
            std = np.reshape(std_gl[indx, indy], [5, 5])
            hcr = np.reshape(hcr_gl[indx, indy], [5, 5])
            rcr = aatsr_cal_r(tcc, std, hcr)
            print(tcc)
            print(hcr)
            print(std)
            print(rcr)

        #     '反演数据准备'
        #     #  计算L能量
        #     wl = 10.8
        #     radN = cal_rad_from_lst(lstN, wl, lai, vzaN, emisS, emisV)
        #     radF = cal_rad_from_lst(lstF, wl, lai, vzaF, emisS, emisV)
        #
        #     '有效发发射率'
        #     #  计算W有效发射率
        #     if ifday:
        #         hspot = 0.2
        #         wN, posil = cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vzaN, sza, vaaN, saa, 3)
        #         wF, psoil = cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vzaF, sza, vaaF, saa, 3)
        #     else:
        #         hspot = 0.2
        #         wN, posil = cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vzaN, sza, vaaN, saa, 2)
        #         wF, psoil = cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vzaF, sza, vaaF, saa, 2)
        #
        #     # 添加 mask
        #     rad_th_max, rad_th_min = 20, 3.2
        #     maskN = (radN > rad_th_min) * (radN < rad_th_max)  * (classif == classif[2,2])
        #     maskF = (radF > rad_th_min) * (radF < rad_th_max) * (classif == classif[2,2])
        #
        #     # 给定温度限制
        #     DT = np.zeros([5, 5])
        #
        #     if ifday:
        #         results = inv_lsct3_AATSR_line(wN, wF, radN, radF, maskN, maskF, psoil,  DT,
        #                              ns=5)
        #         if np.shape(results) != (4, 5):
        #             continue
        #         results = results[:,2]
        #         Tsl , Tsh, Ts, Tv = results[0],results[1],results[2],results[3]
        #     else:
        #         results = inv_lsct2_AATSR_line(wN, wF, radN, radF, maskN, maskF,lstN,lstF,DT,ns=5)
        #         if np.shape(results) != (4, 5):
        #             continue
        #         results = results[:,2]
        #         Tsl , Tsh, Ts, Tv = results[0],0.0,results[0],results[1]
        #     print(Tsl,Tsh,Ts,Tv)
        #     results_list.append([
        #         utc_time, lstN[2,2], lstF[2,2],clo[2,2], Tsl, Tsh, Ts, Tv
        #     ])
        # df_out = pd.DataFrame(results_list, columns=["UTC_Time", "lstN", "lstF","clo", "Tsl", "Tsh", "Ts", "Tv"])
        # # 保存 CSV
        # df_out.to_csv(site_out_file, index=False)
        # print('save ', site_out_file)
