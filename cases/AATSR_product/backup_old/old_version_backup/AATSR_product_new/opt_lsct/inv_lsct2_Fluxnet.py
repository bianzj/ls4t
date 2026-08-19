from utils.old.util_lsct import *

'''2025.3.6'''
'''Fluxnet 站点2组分温度反演'''
'''用于方法测试，只反演目标像元保存结果到csv中'''

if __name__ == '__main__':
    raw_dir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/0_raw_h5/'
    out_dir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/results/lsct2_hom/aatsr_csv/'
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

    for site_name in site_names:
        print("--------------------------------------------------------------------------------")
        print(site_name)
        # if (site_name not in filtered_list): continue
        site_dir = os.path.join(raw_dir, site_name)
        site_out_file = out_dir + site_name + ".csv"
        if os.path.exists(site_out_file): continue

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
            data = read_aatsr_sites(site_dir, fileName, timezone, lat, lon)
            if data is None:
                continue
            elif np.shape(data[0]) !=(5,5): continue
            lstN, lstF, lai, vzaN, vzaF, vaaN, vaaF, sza, saa, clo, emisS, emisV, classif, utc_time = data

            '反演数据准备'
            #  计算L能量
            wl = 10.8
            radN = cal_rad_from_lst(lstN, wl, lai, vzaN, emisS, emisV)
            radF = cal_rad_from_lst(lstF, wl, lai, vzaF, emisS, emisV)

            '有效发发射率'
            #  计算W有效发射率
            if_use_crown = False
            if not if_use_crown:
                hspot = 0.2
                wN, posil = cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vzaN, sza, vaaN, saa, 2)
                wF, psoil = cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vzaF, sza, vaaF, saa, 2)
            else:
                hspot = 1.0
                rcr,hcr,tcc = 1,1,0.5
                wN, psoil = cal_effective_emissivity_crown(lai, hspot, wl, emisS, emisV, vzaN, sza, vaaN, saa, classif,
                                                           rcr, tcc, hcr, 2)
                wF, psoil = cal_effective_emissivity_crown(lai, hspot, wl, emisS, emisV, vzaF, sza, vaaF, saa, classif,
                                                           std, rcr,
                                                           hcr, 2)
            # 添加 mask
            rad_th_max, rad_th_min = 20, 3.2
            maskN = (radN > rad_th_min) * (radN < rad_th_max)  * (classif == classif[2,2])
            maskF = (radF > rad_th_min) * (radF < rad_th_max) * (classif == classif[2,2])

            # 给定温度限制
            DT = np.zeros([5, 5])

            results = inv_lsct2_AATSR_line(wN, wF, radN, radF, maskN, maskF, lstN, lstF, DT,
                                 ns=5)
            if np.shape(results) != (4, 5):
                continue
            results = results[:,2]
            Ts_p , Tv_p, Ts_w, Tv_w = results[0],results[1],results[2],results[3]
            print(Ts_p,Tv_p,Ts_w,Tv_w)

            results_list.append([
                utc_time, lstN[2,2], lstF[2,2],clo[2,2], Ts_p, Tv_p, Ts_w, Tv_w
            ])
        df_out = pd.DataFrame(results_list, columns=["UTC_Time", "lstN", "lstF","clo", "Ts_p", "Tv_p", "Ts_w", "Tv_w"])
        # 保存 CSV
        df_out.to_csv(site_out_file, index=False)
        print('save ', site_out_file)

