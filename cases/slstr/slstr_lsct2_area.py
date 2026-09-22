import numpy as np
from base.files import mkdir_if_not_exist, read_image_gdal, read_txt_array, search_file_rej, write_image_gdal
from base.lsct import cal_effective_emissivity_hom, cal_rad_from_lst, inv_lsct2_window

import sys
import os
import warnings
warnings.filterwarnings("ignore")

'''2025.10.14'''
'''
两组分窗口2组分温度反演
先确定观测角度n，反演组分数m，窗口大小ws
1. 计算有效发射率
2. 计算辐亮度
3. 求解组分温度
'''

if __name__ == '__main__':
    '''读入数据'''
    indir_tif = r'/home/hero/data/SLSTR_heihe/tif/'
    indir_lst = r'/home/hero/data/SLSTR_heihe/lst/'
    indir_lai = r'/home/hero/data/SLSTR_heihe/lai/' 
    outdir_lsct = r'/home/hero/data/SLSTR_heihe/lsct2/'
    mkdir_if_not_exist(outdir_lsct)

    indir_type = r'/home/hero/data/LSCT3/LSCT_dm_2022/0_base/type/'
    indir_ems = r'/home/hero/data/LSCT3/LSCT_dm_2022/0_base/emis/'
    infile_soil_emis = indir_ems + 'emis1_heihe_utm47N_1000.tif'
    infile_type = indir_type + 'type_heihe_1000_utm47N.tif'
    infile_veg_emis = indir_ems + 'IGBP_Emi.txt'
    [emis_s, ns, nl, nb, geog, proj] = read_image_gdal(infile_soil_emis)
    if np.average(emis_s[emis_s > 0]) > 1.0:
        emisS = emis_s / 1000.0
    [classif, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_type)
    classif = np.asarray(classif, int)
    emis_v = read_txt_array(infile_veg_emis, 0, 2)
    emisV = emis_v[classif, 0] / 1000.0

    fileNames = search_file_rej(indir_lst, ['lst_nadir'], 'aux')
    fileNum = len(fileNames)
    for k,fileName in enumerate(fileNames):
        print(f'{k+1}/{fileNum}: {fileName}')

        # 1. 读取数据
        infile_lstN = indir_lst + fileName
        basename = fileName[:-13]
        print(basename)
        infile_lstF = indir_lst + basename + 'lst_obliq.tif'
        infile_cloN = indir_tif + basename + 'cloud_nadir.tif'
        infile_cloF = indir_tif + basename + 'cloud_obliq.tif'
        infile_vzaN = indir_tif + basename + 'vza_nadir.tif'
        infile_vzaF = indir_tif + basename + 'vza_obliq.tif'
        infile_vaaN = indir_tif + basename + 'vaa_nadir.tif'
        infile_vaaF = indir_tif + basename + 'vaa_obliq.tif'
        infile_sza = indir_tif + basename + 'sza_nadir.tif'
        infile_saa = indir_tif + basename + 'saa_nadir.tif'
        outfile_Ts = outdir_lsct + basename + 'ts.tif'
        outfile_Tv = outdir_lsct + basename + 'tv.tif'
        year = basename.split('_')[1]
        doy = basename.split('_')[2]
        infile_lai = indir_lai + year + '_' + doy + '_lai.tif'
        print(infile_lai)
        [lai, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai)
        [lstN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lstN)
        [lstF, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lstF)
        [cloN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_cloN)
        [cloF, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_cloF)
        [vzaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vzaN)
        [vzaF, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vzaF)
        [vaaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaaN)
        [vaaF, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaaF)
        [sza, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_sza)
        [saa, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_saa)

        nl,ns = lstN.shape

        # 1. 计算有效发射率 (LAI)
        n,m= 2,2
        ws = 5
        hspot=0.2
        wl = 10.8
        w = np.zeros([nl,ns,n,m])
        for i in range(nl):
            for j in range(ns):
                w[i,j,:,:] =cal_effective_emissivity_hom(lai[i,j],hspot,wl,emisS[i,j],emisV[i,j],[vzaN[i,j],vzaF[i,j]],[sza[i,j],sza[i,j]],[vaaN[i,j],vaaF[i,j]],[saa[i,j],saa[i,j]],n,m)

        # 2. 计算辐亮度
        bN = cal_rad_from_lst(lstN,wl,lai,vzaN,emisS,emisV)
        bF = cal_rad_from_lst(lstF,wl,lai,vzaF,emisS,emisV)
        b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2)

        # 3. 求解组分温度
        lst = np.concatenate([lstN[:,:,np.newaxis], lstF[:,:,np.newaxis]], axis=2)
        cloN_mask = (cloN == 0) * (lai>0.1)
        cloF_mask = (cloF == 0) * (lai>0.1)
        mask = np.concatenate([cloN_mask[:,:,np.newaxis], cloF_mask[:,:,np.newaxis]], axis=2)
        lsct = inv_lsct2_window(n, m, ws, wl, w, b, mask, lst)


        # 保存结果
        write_image_gdal(lsct[:,:,0], ns, nl, 1, geog, proj, outfile_Ts)
        write_image_gdal(lsct[:,:,1], ns, nl, 1, geog, proj, outfile_Tv)
