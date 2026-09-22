"""AATSR case helpers moved from the run project on 2026-09-16."""


# ---------------------------------------------------------------------------
# AATSR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
from datetime import datetime, timedelta
import h5py
import numpy as np
from base.files import read_h5py_items, read_image_gdal, read_txt_array


def aatsr_read_aux_data(indir_emis=r"/home/hero/data/base/0_base/emis/", indir_type=r"/home/hero/data/base/0_base/type/"):
    '''
    aatsr 读取辅助数据
    :param indir_emis: 发射率
    :param indir_type:  地表类型
    :return: 土壤发射率、植被发射率、分类、密度、观测天顶角、方位角
    '''
    # 读取type emis
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


def aatsr_read_crown_data(indir_veg_pra):
    '''
    读取植被参数
    :param indir_veg_pra: 地址
    :return: 树密度、覆盖度、树冠高度
    '''
    infile_std = indir_veg_pra + "Tree_density(STD)/global_TreeDensity_0.01.tif"
    infile_TCC = indir_veg_pra + "Tree_cover(TCC)/global_TreeCover2010_0.01.tif"
    infile_hcr = indir_veg_pra + "Cnopy_height(hcr)/global_CanopyHeight_0.01.tif"
    [std, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_std)
    [TCC, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_TCC)
    [hcr, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_hcr)
    hcr = np.nan_to_num(hcr,0.0)
    std = std / 1000000
    hcr = hcr / 2
    TCC = TCC / 100
    return  std, TCC, hcr


def aatsr_clo_optimized(clo):
    """
    优化版：使用位运算检查最低两位
    最低位(第0位)表示是否为陆地(1)，第1位表示是否有云(0)
    只有陆地且无云时返回True

    :param clo: 十进制整数或数组
    :return: 是否符合条件(bool或np.ndarray)
    """
    # 转换为整数类型确保位运算正确
    clo = np.asarray(clo, dtype=np.int32)

    # 使用位运算同时检查两个条件:
    # 1. (clo & 0b01) == 1 检查最低位是否为1(陆地)
    # 2. (clo & 0b10) == 0 检查第1位是否为0(无云)
    return np.bitwise_and((clo & 0b01) == 1, (clo & 0b10) == 0)


def aatsr_read_sites_obs(infile,ifNDVI=1):
    items_obs = ['nirN','nirF','redN','redF','cloN','cloF']
    [nirN, nirF, redN, redF, cloN, cloF] = read_h5py_items(infile, items_obs)
    cloN_mask = aatsr_clo_optimized(cloN)
    cloF_mask = aatsr_clo_optimized(cloF)
    if ifNDVI == 1:
        ndviN = (nirN - redN) / (nirN + redN)
        ndviF = (nirF - redF) / (nirF + redF)
        ndviN[ndviN < -1] = -1
        ndviN[ndviN > 1] = 1
        ndviF[ndviF < -1] = -1
        ndviF[ndviF > 1] = 1
        ndviN[(redN ==0) + (nirN==0)] = np.nan
        ndviF[(redF ==0) + (nirF==0)] = np.nan
        return ndviN, ndviF
    return nirN, nirF, redN, redF


def aatsr_read_sites_clo(infile):
    items_clo = ['cloN','cloF']
    [cloN, cloF] = read_h5py_items(infile, items_clo)
    cloN_mask = aatsr_clo_optimized(cloN)
    cloF_mask = aatsr_clo_optimized(cloF)
    return cloN_mask, cloF_mask


def aatsr_read_sites_lst(infile):
    items_lst = ['lstN','lstO']
    [lstN, lstO] = read_h5py_items(infile, items_lst)
    lstN, lstF = lstN / 100, lstO / 100
    return lstN, lstF


def aatsr_read_sites_angle(infile):
    items_angle = ['vzaN','vzaF','vaaN','vaaF','sza','saa']
    [vzaN, vzaF, vaaN, vaaF, sza, saa] = read_h5py_items(infile, items_angle)
    vzaN,vzaF,vaaN,vaaF,sza,saa = vzaN / 100,vzaF/100,vaaN/100,vaaF/100,sza/100,saa/100
    sza[sza >= 90] = 89.99
    return vzaN,vzaF,vaaN,vaaF,sza,saa


def aatsr_read_sites_emis(infile):
    items_emis = ['emis_s','emis_v','type','lai']
    [emis_s,emis_v,type_,lai] = read_h5py_items(infile, items_emis)
    lai = np.array(lai)/1000
    return emis_s,emis_v,type_,lai


def aatsr_read_sites_loc(infile):
    items_loc = ['indx','indy','ref_indx','ref_indy','lat','lon']
    [indx,indy,ref_indx,ref_indy,lat,lon] = read_h5py_items(infile, items_loc)
    return indx,indy,ref_indx,ref_indy,lat,lon


def aatsr_read_sites_time(infile):
    items_time = ['ref_time','sec']
    [ref_time,sec] = read_h5py_items(infile, items_time)
    ref_time_str = infile[-18:-10]
    utc_time = datetime.strptime(ref_time_str, '%Y_%j') + timedelta(seconds=int(np.mean(sec)))
    return utc_time


def aatsr_read_lst(infile_lst):
    '''
    读取aatsr h5 lst数据
    :param infile_lst: lst文件地址
    :return: 两角度LST
    '''
    items = ['lstN','lstO']
    lstN, lstF = read_h5py_items(infile_lst, items)
    lstN, lstF = lstN/100.0, lstF/100.0
    return lstN, lstF


def aatsr_read_NDVI(infile_obs):
    '''
    读取aatsr h5 obs数据并计算NDVI
    :param infile_obs: obs文件地址
    :return: 两角度NDVI
    '''
    items = ['redN','nirN','redF','nirF']
    redN, nirN, redF, nirF = read_h5py_items(infile_obs, items)
    redN, nirN, redF, nirF = redN/10, nirN/10, redF/10, nirF/10
    ndviN = (nirN - redN) / (nirN + redN)
    ndviF = (nirF - redF) / (nirF + redF)
    ndviN[ndviN < -1] = -1
    ndviN[ndviN > 1] = 1
    ndviF[ndviF < -1] = -1
    ndviF[ndviF > 1] = 1
    ndviN[(redN ==0) + (nirN==0)] = np.nan
    ndviF[(redF ==0) + (nirF==0)] = np.nan
    return ndviN, ndviF


def aatsr_read_obs(infile_obs):
    '''
    读取aatsr h5 obs数据
    :param infile_obs: obs文件地址
    :return: 两角度红、近红外
    '''
    items = ['bt8N','bt8F','bt9N','bt9F']
    bt8N, bt8F, bt9N, bt9F = read_h5py_items(infile_obs, items)
    bt8N, bt8F, bt9N, bt9F = bt8N/100.0, bt8F/100.0, bt9N/100.0, bt9F/100.0
    return bt8N, bt8F, bt9N, bt9F


def aatsr_read_clo(infile_clo):
    '''
    读取aatsr h5 clo数据(自动计算并保存mask)
    :param infile_clo: clo文件地址
    :return: 两角度clo
    '''
    items = ['cloN_mask','cloF_mask']
    cloN_mask, cloF_mask = None, None

    # 先检查文件是否存在mask数据集
    with h5py.File(infile_clo, 'r') as f:
        if 'cloN_mask' not in f:
            print(f"Warning: Missing clo_mask in {infile_clo}")
            items = ['cloN','cloF']
            cloN, cloF = read_h5py_items(infile_clo, items)
            cloN_mask = aatsr_clo_optimized(cloN)
            cloF_mask = aatsr_clo_optimized(cloF)
        else:
            cloN_mask, cloF_mask = read_h5py_items(infile_clo, items)
            return cloN_mask, cloF_mask

    if 'cloN_mask' not in h5py.File(infile_clo, 'r'):
        with h5py.File(infile_clo, 'a') as f_write:
            f_write.create_dataset('cloN_mask', data=cloN_mask, dtype='bool', compression='gzip')
            f_write.create_dataset('cloF_mask', data=cloF_mask, dtype='bool', compression='gzip')

    return cloN_mask, cloF_mask


def aatsr_read_loc(infile_loc, iflonlat = 0):
    '''
    读取aatsr h5 loc数据
    :param infile_loc: loc文件地址
    :param iflonlat: 是否返回经纬度，0-否，1-是
    :return: 像元索引(行列)，可选经纬度
    '''
    items = ['indx','indy']
    if iflonlat == 1:
        items = ['indx','indy','lon','lat']
        indx, indy, lon, lat = read_h5py_items(infile_loc, items)
        return indx, indy, lon, lat
    else:
        indx, indy = read_h5py_items(infile_loc, items)
        return indx, indy


def aatsr_read_lai(infile_aux):
    '''
    读取aatsr h5 aux数据
    :param infile_aux: aux文件地址
    :return: LAI
    '''
    items = ['LAI']
    lai = read_h5py_items(infile_aux, items)[0]
    lai = lai / 1000.0
    return lai


def aatsr_read_angle(infile_ang,ifsun=1,ifview=1):
    '''
    读取aatsr h5 ang数据
    :param infile_ang: ang文件地址
    :return: 太阳天顶角、方位角
    '''
    if ifsun == 1:
        items = ['sza','saa']
        sza, saa = read_h5py_items(infile_ang, items)
        sza = sza / 100.0
        saa = saa / 100.0
        sza[sza>89.99] = 89.99
    if ifview == 1:
        items = ['vzaN','vaaN','vzaF','vaaF']
        vzaN, vaaN, vzaF, vaaF = read_h5py_items(infile_ang, items)
        vzaN, vzaF = vzaN / 100.0, vzaF / 100.0
        vaaN, vaaF = vaaN / 100.0, vaaF / 100.0

    if ifsun == 1 and ifview == 1:
        return sza, saa, vzaN, vzaF, vaaN, vaaF
    if ifsun == 1 and ifview == 0:
        return sza, saa
    if ifsun == 0 and ifview == 1:
        return vzaN, vzaF, vaaN, vaaF
