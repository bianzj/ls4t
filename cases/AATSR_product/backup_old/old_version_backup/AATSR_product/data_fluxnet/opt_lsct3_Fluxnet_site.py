import sys
sys.path.append('/')
import os
os.environ['PROJ_LIB'] = r"/home/hero/anaconda3/envs/python37/share/proj"
from utils.old.util_lsct3 import *
# from opt_lsct.multiple_lsct import *
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime, timedelta
import pysolar.solar as Sun
import warnings
warnings.filterwarnings("ignore")


'''2024.4.18'''
'''Fluxnet站点三组分组分温度'''

def get_timezone(lat, lon):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if timezone_str:
        return pytz.timezone(timezone_str)
    else:
        return None

def cal_fvc_from_lai(thetav,lai):
    G = 0.5
    rd = np.pi / 180.0
    costhetanv = np.cos(thetav * rd)
    fvc = 1 - exp(-G*lai/costhetanv)
    fvc[fvc>1] = 1
    fvc[fvc<0] = 0
    return fvc


def read_aux_data( indir_veg_pra):
    # 读取std hcr rcr
    infile_std = indir_veg_pra + "Tree_density(STD)/global_TreeDensity_0.01.tif"
    infile_TCC = indir_veg_pra + "Tree_cover(TCC)/global_TreeCover2010_0.01.tif"
    infile_hcr = indir_veg_pra + "Cnopy_height(hcr)/global_CanopyHeight_0.01.tif"
    [std, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_std)
    [TCC, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_TCC)
    [hcr, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_hcr)
    hcr = np.nan_to_num(hcr,0.0)
    return std, TCC, hcr

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
    raw_dir = r"/home/hero/data/Fluxnet/AATSR_data/0_raw_h5_2002-2012/"
    out_dir = r"/home/hero/data/Fluxnet/AATSR_data/1_lsct3_h5/"
    site_names = search_dir(raw_dir,'')
    site_names.sort()
    infile_site_info_xls = r"/home/hero/data/Fluxnet/Fluxnet_data/FLUXSITE.xlsx"
    sites_info = pd.read_excel(infile_site_info_xls)

    # base 文件路径
    base_dir = r"/home/hero/data/base/0_base/"
    indir_emis = base_dir + r"emis/"
    indir_type = base_dir + r"type/"
    indir_veg_pra = base_dir + "Veg_para/"

    # 读取辅助数据
    std_arr, TCC_arr, hcr_arr = read_aux_data(indir_veg_pra)

    for site_name in site_names:
        print("--------------------------------------------------------------------------------")
        print(site_name)
        # if (site_name not in filtered_list): continue
        site_dir = os.path.join(raw_dir, site_name)
        site_out_dir = os.path.join(out_dir, site_name)
        mkdir_if_not_exist(site_out_dir)

        # 读取IGBP 分类
        # 1.常绿针叶 ENF 2.常绿阔叶 EBF 3.落叶针叶 DNF 4.落叶阔叶 DBF 5.混交林 MF 6.封闭灌木 CSH
        # 7.开阔灌木 OSH 8.木质稀疏草原 WSA 9. 稀疏草原 SAV 10.草原 GRA 11.永久湿地 WET
        # 12.农田 CRO 13.城市和建筑 URB 14.农田、自然植被 CVM 15.永久冰雪 SNO
        # 16.裸地 BSV 17.水体 WAT
        site_info= sites_info[sites_info["SITE_ID"] == site_name]
        IGBP = site_info['IGBP'].iloc[0]
        lon = site_info['LOCATION_LONG'].iloc[0]
        lat = site_info['LOCATION_LAT'].iloc[0]
        timezone = get_timezone(lat, lon)

        infile_type = indir_type + 'type_world_1000.tif'
        indx, indy = loc2map(lat,lon,gdal.Open(infile_type))

        fileNames = search_file(site_dir,['h5'])
        fileNames.sort()
        for fileName in fileNames:
            print("----------------------------------")
            print(fileName)
            infile = os.path.join(site_dir, fileName)
            outfile = os.path.join(site_out_dir, fileName)
            if os.path.exists(outfile): continue

            '''读取数据'''
            items = ['lon','lat','lstN','lstO','lai','vzaN','vzaO','vaaN','vaaO','sza','saa','indx','indy','ref_indx','ref_indy','ref_time','sec','type','emis_s',"emis_v",'clo']
            lon_,lat_,lstN_,lstO_,lai_,vzaN_,vzaO_,vaaN_,vaaO_,sza_,saa_,indx_,indy_,ref_indx_,ref_indy_,ref_time_,sec_,type_,emis_s_,emis_v_,clo_ = read_h5py_items(infile,items)
            ref_time_str = fileName[6:-10]
            utc_time = datetime.strptime(ref_time_str, '%Y_%j') + timedelta(seconds=int(np.mean(sec_)))
            local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone)
            print(local_time)
            if local_time.hour < 6 or local_time.hour >= 18:
                print("Pass Night!")
                continue

            id = (indx_ == ref_indx_) * (indy_ == ref_indy_)
            if sum(id) == 0:
                print("No Data!")
                continue

            indx_,indy_ = indx_.astype(int),indy_.astype(int)
            std, hcr, tcc = std_arr[indx_, indy_], hcr_arr[indx_, indy_], TCC_arr[indx_, indy_]
            if IGBP in ['WET', 'WAT', 'SNO', 'URB', 'BSV']:
                print("IGBP type:", IGBP, ", continue!")
                continue
            if IGBP in ['ENF', 'EBF', 'DNF', 'DBF', 'MF', 'WSA', 'SAV']:
                mode = 'Crown'
                hspot = 1.0
                std = std / 1000000
                hcr = hcr / 2
                tcc = tcc / 100
                rcr = np.sqrt(tcc / np.pi / std)
                rcr[rcr<0.5] =0.5
                rcr[rcr>30]=30
            if IGBP in ['GRA', 'CSH', 'OSH', 'CRO', 'CVM']:
                mode = 'Hom'

            lstN,lstO = lstN_,lstO_
            lai = lai_/1000
            vzaN,vzaO,vaaN,vaaO,sza,saa = vzaN_,vzaO_,vaaN_,vaaO_,sza_,saa_
            type = type_
            emis_s = emis_s_
            emis_v = emis_v_

            '''格式转化'''
            lstN = lstN / 100
            lstO = lstO / 100
            vzaN = 90 - (vzaN / 100)
            vzaO = 90 - (vzaO / 100)

            nl,ns = np.shape(lstN)
            if sza != []:
                sza = (sza / 100)
            else:
                sza_ = 90 - Sun.get_altitude(lat, lon, local_time)
                saa_ = Sun.get_azimuth(lat, lon, local_time) *100
                sza = np.full([nl,ns],sza_)
                saa = np.full([nl,ns],saa_)

            def Azimuth_angle_transform(xaa):
                xaa = xaa / 100
                xaa[xaa<0] = xaa[xaa<0] + 360
                return xaa

            vaaN = Azimuth_angle_transform(vaaN)
            vaaO = Azimuth_angle_transform(vaaO)
            saa = Azimuth_angle_transform(saa)
            raaN = np.abs(vaaN-saa)
            raaO = np.abs(vaaO-saa)

            #  计算L能量
            wl = 10.8
            fvcN = 1 - gap_probability_hom_analytical(lai, vzaN)
            fvcO = 1 - gap_probability_hom_analytical(lai, vzaO)
            radN = planck(wl, lstN)
            radN = radN * (fvcN * emis_v + (1 - fvcN) * emis_s)
            radO = planck(wl, lstO)
            radO = radO * (fvcO * emis_v + (1 - fvcO) * emis_s)

            '''有效发发射率'''
            wavelength = 10.8
            wN4, wO4 = np.zeros([4, nl, ns]), np.zeros([4, nl, ns])
            wN, wO = np.zeros([3, nl, ns]), np.zeros([3, nl, ns])
            psoil = np.zeros([nl, ns])
            if mode == 'Hom':
                hspot = 0.2
                wN4 = sample_hom_Emis(lai, hspot, wl, emis_s, emis_v,vzaN, sza,np.abs(vaaN - saa))
                wO4 = sample_hom_Emis(lai, hspot, wl, emis_s, emis_v,vzaO, sza,np.abs(vaaO - saa))
                psoil = gap_probability_hom_analytical(lai, sza)

            elif mode == 'Tall Crown' or mode == 'Short Crown':
                hspot = 1.0
                wN4 = sample_crown_Emis(lai, hspot, std, rcr, hcr, wl,emis_s, emis_v, vzaN, sza,np.abs(vaaN - saa))
                wO4 = sample_crown_Emis(lai, hspot, std, rcr, hcr, wl,emis_s, emis_v, vzaO, sza,np.abs(vaaO - saa))
                psoil = gap_probability_crown_analytical(lai, std, hcr,rcr, sza)

            wN[:2, :, :] = wN4[0:2, :, :]
            wN[2, :, :] = wN4[2, :, :] + wN4[3, :, :]
            wO[:2, :, :] = wO4[0:2, :, :]
            wO[2, :, :] = wO4[2, :, :] + wO4[3, :, :]

            # 给定温差大小DT
            DT = np.zeros([nl, ns])
            month,day = doy2date(int(ref_time_str[:4]),int(ref_time_str[5:7]))
            DT = determine_DT(DT,month,lat)

            # mask掉纯像元和clound
            rad_th_max, rad_th_min = 20, 4.5
            fvc_th_max, fvc_th_min = 0.99, 0.03
            maskN = (radN > rad_th_min) * (radN < rad_th_max) * (
                    clo_ <= 100)  # * (cloN != 0) * (fvcN > fvc_th_min) * (fvcN < fvc_th_max)
            maskO = (radO > rad_th_min) * (radO < rad_th_max) * (
                    clo_ <= 100)  # * (cloO != 0) * (fvcO > fvc_th_min) * (fvcO < fvc_th_max)


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
            pool = Pool(min(192, cpu_count()))
            for p in para:
                tasks.append(pool.apply_async(doMultiple_line_inv_3_AATSR, (p,)))
            pool.close()
            pool.join()
            results = [task.get() for task in tasks]
            lsct3 = np.asarray(results)

            [nl, nb, ns] = np.shape(lsct3)
            lsct3 = lsct3.transpose(1, 0, 2)
            # print(np.shape(lsct3))
            if (np.sum(lsct3[0, :, :] != 0) < 1):
                print(fileName + '_lsct.tif' + ' no result')
                continue

            lsct_save = np.zeros([3, nl + 2 * off, ns])
            lsct_save[:, off:-off, :] = lsct3

            Tsl = lsct_save[0, :, :]
            Tsh= lsct_save[1, :, :]
            Tv = lsct_save[2, :, :]
            Ts = inv_planck(wl, planck(wl, Tsl) * psoil + planck(wl, Tsh) * (1 - psoil))

            name_list = ['lstN','lstO','lai','vzaN','vzaO','indx','indy','ref_indx','ref_indy','ref_tmie','sec','type','emis_s',"emis_v",'Ts','Tv','Tsl','Tsh']

            data = [lstN_,lstO_,lai_,vzaN_,vzaO_,indx_,indy_,ref_indx_,ref_indy_,ref_time_,sec_,type_,emis_s_,emis_v_,Ts,Tv,Tsl,Tsh]

            write_h5py_file(outfile, name_list, data_list=data,
                            dtype_list=['f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f','f','f'],
                            compression=None, ifcover=1)