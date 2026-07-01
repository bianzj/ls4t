import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from base.util_lsct import *

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import calendar
import multiprocessing
from functools import partial
import warnings

warnings.filterwarnings("ignore")
from base.util_constant import *
from base.util_file import *
from base.util_data import *
import time

"""
AATSR 两组分温度反演 注意版本python37
"""
from sklearn.linear_model import Ridge
def fitting_with_ridge(bb, ww):
    # alpha 是正则化强度，需要根据数据噪声调优，通常尝试 0.01, 0.1, 1.0
    reg = Ridge(alpha=0.01, fit_intercept=False)
    reg.fit(ww.T, bb.T)  # 注意你的维度是 (3, N) 还是 (N, 3)，需要保持一致
    return reg.coef_



def cal_fvc_from_lai(thetav, lai):
    G = 0.5
    rd = np.pi / 180.0
    costhetanv = np.cos(thetav * rd)
    fvc = 1 - exp(-G * lai / costhetanv)
    fvc[fvc > 1] = 1
    fvc[fvc < 0] = 0
    return fvc


def inv_mpl_agl_multiple_2(lst_n, lst_o, emis_s, emis_v, fvcN, fvcO, wl=10.8):
    radiance_max_threshold = 20
    radiance_min_threshold = 2.5
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
    number_component = 2
    number_angle = 2
    number_value_threshold = 12
    off = 2
    off_ = 0

    start = time.time()
    [nl, ns] = np.shape(lst_n)
    result = np.zeros([2, nl, ns])

    ###### fvc LAI 根据LAI计算得到的fvc，为此函数的输入项
    fvc_n = fvcN * 1.0
    fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold

    fvc_o = fvcO * 1.0
    fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold

    ###### the radiance 根据fvc和植被土壤的发射率计算像元的有效发射率，加上反演得到的地表温度计算像元的能量
    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

    ###### component effective emissivity matrix 组分有效发射率，分别对应光土壤，植被
    wV = np.asarray([emis_v * (fvc_n),emis_v * fvc_o])
    wS = np.asarray([emis_s * (1 - fvc_n),emis_s * (1 - fvc_o)])

    mask = np.zeros([nl, ns])
    ind0 = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
           (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
           (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind0] = 1

    para = []
    resultT = np.zeros([2, nl, ns])

    if np.sum(mask) < 1:
        return resultT

    indx,indy = np.where(mask)

    nump = len(indx)

    off = 2
    for kp in range(nump):

        kl =  indx[kp]
        ks = indy[kp]

        kl1 = kl - off
        kl2 = kl + off + 1
        ks1 = ks - off
        ks2 = ks + off + 1
        eeV = np.reshape(wV[:, kl1:kl2, ks1:ks2], -1)
        eeS = np.reshape(wS[:, kl1:kl2, ks1:ks2], -1)
        bN = np.reshape(rad_n[kl1:kl2, ks1:ks2], -1)
        bO = np.reshape(rad_o[kl1:kl2, ks1:ks2], -1)
        mask1 = np.reshape(mask[kl1:kl2, ks1:ks2], -1)
        mask2 = np.hstack([mask1,mask1])

        ind2 = (eeS > 0.1) * mask2 * (eeS < 0.9)
        if (np.sum(ind2) <= 5): continue
        bb = np.hstack([bN, bO])
        ww = np.stack([eeS[ind2], eeV[ind2]])
        bb = bb[ind2]
        coeffs = np.asarray(lstsq(np.transpose(ww), np.transpose(bb))[0])
        temp = inv_planck(wl, coeffs)
        resultT[:, kl, ks] = temp

    return resultT

def aatsr_read_aux_data(indir_emis, indir_type):
    '''
    aatsr 读取辅助数据
    :param indir_emis: 发射率
    :param indir_type:  地表类型
    :return: 土壤发射率、植被发射率、分类、密度、树覆盖比例、树冠高度，观测天顶角、方位角
    '''
    # 读取type emis std hcr rcr
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


if __name__ == '__main__':
    # indir0 = r'/home/bianzj/AATSR_test/'
    # indir0 = r"/mnt/g/base/"

    indir0 = r"/media/hero/lsct04/"
    outdir0 = r"/media/hero/lsct04/aatsr_lsct_v2/"

    indir_type = indir0 + r'/0_base/type/'
    indir_emis = indir0 + r'/0_base/emis/'
    indir_base = indir0 + r'/0_base/base/'
    indir_lai0 = indir0 + r'/lai/'

    indir_lst = indir0 + "/aatsr_lst/"
    indir_loc = indir0 + "/aatsr_loc/"
    indir_clo = indir0 + "/aatsr_clo/"
    indir_ang = indir0 + "/aatsr_ang/"
    indir_aux = indir0 + "/aatsr_aux/"


    infile_soil_emis = indir_emis + r'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
    infile_type = indir_type + 'type_world_1000.tif'
    infile_veg_emis = indir_emis + 'IGBP_Emi.txt'

    '''读取发射率'''
    print(os.path.exists(infile_soil_emis))
    emis_s_, emis_v_, classif_, vzaN, vzaF, vaaN, vaaF = aatsr_read_aux_data(
        indir_emis, indir_type)

    '''读取数据'''
    for kyear in range(2006, 2007):
        indir_lai = indir_lai0 + '%04d/' % kyear

        outdir = outdir0 + '/%04d/' % kyear
        indir = indir0 + '/%04d' % kyear
        for kmonth in range(3, 11):
            daynum = calendar.monthrange(kyear, kmonth)[1]
            for day in range(1, 32):


                year, month = kyear, kmonth
                time_str = f'{year}/{month:02d}/{day:02d}/'
                outdir_hdf_day = outdir + r"/%02d/%02d//" % (month, day)
                mkdir_if_not_exist(outdir_hdf_day)


                if os.path.exists(indir_lst + time_str) == 0: continue
                fileNames = search_file_rej(indir_lst + time_str, ['h5'], 'xml')
                fileNum = len(fileNames)



                for i, fileName in enumerate(fileNames):
                    print(i + 1, '/', fileNum, fileName)

                    out_hdf5 = outdir_hdf_day + fileName[:-3] + "_lsct.h5"
                    if os.path.exists(out_hdf5):
                        # os.remove(out_hdf5)
                        continue

                    year = fileName[6:10]
                    doy_str = fileName[11:14]
                    fileName_str = fileName[0:22]
                    doy = int(doy_str)

                    basename = os.path.basename(fileName)

                    infile_lst = indir_lst + time_str +basename
                    infile_clo = indir_clo + time_str + basename.replace('lst', 'clo')
                    infile_ang = indir_ang + time_str + basename.replace('lst', 'ang')
                    infile_loc = indir_loc + time_str + basename.replace('lst', 'loc')
                    infile_aux = indir_aux + time_str + basename.replace('lst', 'aux')

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

                    cloN_mask, cloF_mask = aatsr_read_clo(infile_clo)
                    indx, indy, lon, lat = aatsr_read_loc(infile_loc, iflonlat=1)
                    nl, ns = lstN.shape[0], lstF.shape[1]  # 行列数
                    lai = read_h5py_item(infile_aux, 'LAI') / 1000



                    fvc_n = cal_fvc_from_lai(vzaN, lai)
                    fvc_o = cal_fvc_from_lai(vzaF, lai)


                    fvc_n[fvc_n > 1] = 1
                    fvc_n[fvc_n < 0] = 0
                    fvc_o[fvc_o > 1] = 1
                    fvc_o[fvc_o < 0] = 0

                    '''根据lon、lat调整emis'''
                    indx[indx == 18000] = 0
                    indy[indy == 36000] = 0
                    emis_s = emis_s_[indx, indy]
                    emis_v = emis_v_[indx, indy]
                    classif = classif_[indx, indy]
                    emis_s = np.reshape(emis_s, [nl, ns])
                    emis_v = np.reshape(emis_v, [nl, ns])
                    classif = np.reshape(classif, [nl, ns])

                    '''反演LSCT'''

                    lsct = inv_mpl_agl_multiple_2(lstN, lstF, emis_s, emis_v, fvc_n, fvc_o, wl=10.8)


                    [ns, nl, nb] = np.shape(lsct)
                    if (np.sum(lsct) == 0):
                        print(fileName + '_lsct.tif' + ' no result')
                        continue

                    lsct_save = np.zeros([nb, ns, 512])
                    lsct_save[0, :, 2:-2] = np.reshape(lsct[:, :, 0], [ns, nl])
                    lsct_save[1, :, 2:-2] = np.reshape(lsct[:, :, 1], [ns, nl])

                    # write_image_gdal(lsct_save, nl, ns+4, nb, geog, proj, outfileLsct)
                    # print(fileName + '_lsct.tif done')

                    # break
                    '''写h5文件'''
                    out_hdf5 = outdir_hdf_day + fileName[:-3] + "_lsct.h5"
                    if not os.path.exists(out_hdf5):
                        f = h5py.File(out_hdf5, 'w')
                    else:
                        continue

                    '''save'''
                    f.attrs['Origin File'] = fileName
                    f.attrs['Version'] = 'v0'
                    from datetime import datetime

                    f.attrs['Creation Date'] = str(datetime.now())
                    f.attrs['Author'] = 'Lu Yifan / Bian Zunjian'
                    f.attrs['Method'] = 'Ts/Tv: 2 angle 5 pixel(bayesian)'

                    datasets = {
                        'Ts': (
                        lsct_save[0, :, :] * 100, 'soil temperature(in K,*100),Scale = 100, type = uint16', np.uint16),
                        'Tv': (
                        lsct_save[1, :, :] * 100, 'veg temperature(in K,*100),Scale = 100, type = uint16', np.uint16),
                    }

                    for dset_name, (data, description, dtype) in datasets.items():
                        if dset_name in f:
                            del f[dset_name]
                        dset = f.create_dataset(dset_name, data=data, dtype=dtype, compression='gzip')
                        dset.attrs['description'] = description

                    f.close()

