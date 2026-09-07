import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from base.util_file import *
from base.util_data import *
from base.util_constant import *
from util_aatsr import *
import math
import warnings
warnings.filterwarnings("ignore")

def cal_fvc_from_lai(thetav,lai):
    G = 0.5
    rd = np.pi / 180.0
    costhetanv = np.cos(thetav * rd)
    fvc = 1 - exp(-G*lai/costhetanv)
    fvc[fvc>1] = 1
    fvc[fvc<0] = 0
    return fvc

'''
26.1.4
LST 反演重构,和原来结果大部分点完全一致，少部分有约0.02K轻微差异（尚未确定原因，有可能是lonlat问题）；tcwv时间匹配用的是开始时间（一景总时间108分钟左右，影响不大）；SW日夜都用的日系数。
'''
'''23.9.16 AATSR垂直观测lst反演（LAI）'''

if_lst_n = 1
if_lst_f = 1


base_dir = r'/home/hero/data/ls4t/aatsr/'
indir_obs = base_dir + 'aatsr_obs/'
indir_loc = base_dir + 'aatsr_loc/'
indir_ang = base_dir + 'aatsr_ang/'
indir_aux = base_dir + 'aatsr_aux/'
outdir_lst = base_dir + 'aatsr_lst/'
indir_tcwv = base_dir + 'tcwv/'

indir_base0 = r'/home/hero/data/ls4t/aatsr/base/'
indir_type = indir_base0 + 'type/'
indir_emis = indir_base0 + 'emis/'
indir_base = indir_base0 + 'base/'

emis1_dir = indir_emis + 'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
emis2_dir = indir_emis + 'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE12.tif'
IGBP_dir = indir_base + r'IGBP_Emi.txt'
type_dir = indir_type + 'type_world_1000.tif'
SW_day_dir = indir_base + 'Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt'
SW_night_dir = indir_base + 'Sentinel3A_SLSTR_SW_Seebor_Coef_Night.txt'

coeffs_day = read_txt_array(SW_day_dir, 0, 15)
coeffs_day = coeffs_day[:, 2:10]
coeffs_night = read_txt_array(SW_night_dir, 0, 15)
coeffs_night = coeffs_night[:, 2:10]

[emis1_s_, ns, nl, nb, geog, proj] = read_image_gdal(emis1_dir)
emis1_s_ = emis1_s_ / 1000.0
[emis2_s_, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(emis2_dir)
emis2_s_ = emis2_s_ / 1000.0
[classif_, ns_type, nl_type, temp3, temp4, temp5] = read_image_gdal(type_dir)
classif_ = np.asarray(classif_, int)
emis_v = read_txt_array(IGBP_dir, 0, 2)

for year in range(2006, 2007):
    for month in range(7,8):
        for day in range(1, 32):
            doy = date2DOY(year, month, day)
            time_Str = '%04d/%02d/%02d' % (year, month, day)
            indir_obs_day = indir_obs + time_Str + '/'
            indir_aux_day = indir_aux + time_Str + '/'
            indir_ang_day = indir_ang + time_Str + '/'
            indir_loc_day = indir_loc + time_Str + '/'
            outdir_lst_day = outdir_lst + time_Str + '/'

            if not os.path.exists(indir_obs_day): continue
            print('-----%04d/%02d/%02d-----' % (year, month, day))

            fileNames = search_file_rej(indir_obs_day, ['.h5'], 'xml')
            fileNum = np.size(fileNames)

            for i,fileName in enumerate(fileNames):
                base_name = fileName[:-6]
                outfile_lst = outdir_lst_day + base_name + 'lst.h5'
                mkdir_if_not_exist(outdir_lst_day)
                infile_obs = indir_obs_day + base_name + 'obs.h5'
                infile_ang = indir_ang_day + base_name + 'ang.h5'
                infile_loc = indir_loc_day + base_name + 'loc.h5'
                infile_aux = indir_aux_day + base_name + 'aux.h5'

                '''读取obs数据'''
                bt8N, bt8F, bt9N, bt9F = aatsr_read_obs(infile_obs)
                ndviN, ndviF = aatsr_read_NDVI(infile_obs)
                sza, saa, vzaN, vzaF, vaaN, vaaF = aatsr_read_angle(infile_ang)
                lai = aatsr_read_lai(infile_aux)
                indx,indy = aatsr_read_loc(infile_loc)
                nl, ns = np.shape(bt8N)

                '''读取水汽数据'''
                indx_tcw = np.floor(np.array(indx/20))
                indy_tcw = np.floor(np.array(indy/20))

                time_str = base_name.split('_')[3]
                hour = math.floor(int(time_str) / 10000)
                min = int((int(time_str) - math.floor(int(time_str) / 10000) * 10000) / 100)
                year = int(year)
                doy2 = doy
                if hour != 23:
                    tcw_filename1 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % hour
                    tcw_filename2 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % (hour + 1)
                else:
                    doy2 = doy + 1
                    if doy == 365 or doy == 366:  # 年末粗略处理
                        tcw_filename1 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % hour
                        tcw_filename2 = tcw_filename1
                    tcw_filename1 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % hour
                    tcw_filename2 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % (doy + 1) + "00.tif"
                tcw_dir1 = indir_tcwv + "/%04d/" % year + "/%03d/" % doy + tcw_filename1
                tcw_dir2 = indir_tcwv + "/%04d/" % year + "/%03d/" % doy2 + tcw_filename2
                [tcw1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir1)
                [tcw2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir2)
                f = min / 60
                indx_tcw = indx_tcw.astype('uint16')
                indy_tcw = indy_tcw.astype('uint16')
                tcw_data = (f * tcw2[indx_tcw,indy_tcw] + (1 - f) * tcw1[indx_tcw,indy_tcw]) / 100 / 10

                tcw = np.reshape(tcw_data, [nl, ns])

                '''读取发射率'''
                emis1_s = emis1_s_[indx, indy]
                emis2_s = emis2_s_[indx, indy]
                classif = classif_[indx, indy]
                emis1_s = np.reshape(emis1_s, [nl, ns])
                emis2_s = np.reshape(emis2_s, [nl, ns])
                classif = np.reshape(classif, [nl, ns])

                ind0 = (classif < 17) * (classif > 0)
                classif[classif == 255] = 17
                emis1_v = emis_v[classif, 0] / 1000.0
                emis2_v = emis_v[classif, 1] / 1000.0
                emis1_v = np.reshape(emis1_v, [nl, ns])
                emis2_v = np.reshape(emis2_v, [nl, ns])

                if if_lst_n:
                    '''反演nadir 角度 LST'''
                    BT8, BT9, vza = bt8N, bt9N, vzaN
                    fvc = cal_fvc_from_lai(vza,lai)
                    # fvc = (ndviN - ndvi_min_g) / (ndvi_max_g - ndvi_min_g)

                    F = 0.75  # 地形因子
                    C1 = (1 - emis1_s) * emis1_v * F * (1 - fvc)  # 多次散射项
                    C2 = (1 - emis2_s) * emis2_v * F * (1 - fvc)  # 多次散射项
                    emis8 = emis1_s * (1 - fvc) + emis1_v * fvc + C1
                    emis9 = emis2_s * (1 - fvc) + emis2_v * fvc + C2
                    emis8[emis8 > 0.995] = 0.995
                    emis9[emis9 > 0.995] = 0.995

                    emis = (emis8 + emis9) * 0.5
                    demis = emis8 - emis9
                    x3 = np.zeros([nl, ns])
                    x4 = np.zeros([nl, ns])
                    x6 = np.zeros([nl, ns])
                    x7 = np.zeros([nl, ns])
                    x1 = 1
                    x2 = (BT8 + BT9) / 2.0
                    ind = emis != 0
                    x3[ind] = (1 - emis[ind]) / emis[ind] * x2[ind]
                    x4[ind] = demis[ind] / (emis[ind] * emis[ind]) * x2[ind]
                    x5 = (BT8 - BT9) / 2
                    x6[ind] = (1 - emis[ind]) / emis[ind] * x5[ind]
                    x7[ind] = demis[ind] / (emis[ind] * emis[ind]) * x5[ind]
                    x8 = (BT8 - BT9) * (BT8 - BT9)

                    wvc_ = np.asarray([0, 1.25, 2.25, 3.25, 4.25, 5.25, 100])
                    vza_ = np.asarray([0, 3, 14.9, 38.6, 44.5, 51.2, 58, 65, 70, 75, 80])

                    LST = np.zeros([nl, ns])
                    for kwvc in range(len(wvc_) - 1):
                        for kvza in range(len(vza_) - 1):

                            ind = (tcw >= wvc_[kwvc]) * (tcw < wvc_[kwvc + 1]) * (vza >= vza_[kvza]) * (vza < vza_[kvza + 1]) * (
                                    BT8 > 0) * (emis8 > 0) * ind0
                            if (np.sum(ind) <= 0): continue

                            ##########################################
                            ### the normal result
                            ##########################################

                            ind1 = kvza * 6 + kwvc
                            ind2 = (kvza + 1) * 6 + kwvc
                            coeff1 = coeffs_day[ind1, :]
                            coeff2 = coeffs_day[ind2, :]
                            vzatemp = vza[ind]
                            prop2 = (vzatemp - vza_[kvza]) / (vza_[kvza + 1] - vza_[kvza])
                            prop1 = 1 - prop2
                            LSTtemp = x1 * (prop1 * coeff1[0] + coeff2[0] * prop2) + x2[ind] * (
                                    prop1 * coeff1[1] + coeff2[1] * prop2) + \
                                    x3[ind] * (prop1 * coeff1[2] + coeff2[2] * prop2) + x4[ind] * (
                                            prop1 * coeff1[3] + coeff2[3] * prop2) + \
                                    x5[ind] * (prop1 * coeff1[4] + coeff2[4] * prop2) + x6[ind] * (
                                            prop1 * coeff1[5] + coeff2[5] * prop2) + \
                                    x7[ind] * (prop1 * coeff1[6] + coeff2[6] * prop2) + x8[ind] * (
                                            prop1 * coeff1[7] + coeff2[7] * prop2)

                            LST[ind] = LSTtemp

                    ind = LST > 365
                    LST[ind] = 365
                    ind = LST < 220
                    LST[ind] = 0
                    LST = LST * 100
                    lstN = LST

                if if_lst_f:
                    BT8, BT9, vza = bt8F, bt9F, vzaF
                    fvc = cal_fvc_from_lai(vza,lai)
                    # fvc = (ndviF - ndvi_min_g) / (ndvi_max_g - ndvi_min_g)

                    F = 0.5  # 地形因子
                    C1 = (1 - emis1_s) * emis1_v * F * (1 - fvc)  # 多次散射项
                    C2 = (1 - emis2_s) * emis2_v * F * (1 - fvc)  # 多次散射项
                    emis8 = emis1_s * (1 - fvc) + emis1_v * fvc + C1
                    emis9 = emis2_s * (1 - fvc) + emis2_v * fvc + C2
                    emis8[emis8 > 0.995] = 0.995
                    emis9[emis9 > 0.995] = 0.995

                    emis = (emis8 + emis9) * 0.5
                    demis = emis8 - emis9
                    x3 = np.zeros([nl, ns])
                    x4 = np.zeros([nl, ns])
                    x6 = np.zeros([nl, ns])
                    x7 = np.zeros([nl, ns])
                    x1 = 1
                    x2 = (BT8 + BT9) / 2.0
                    ind = emis != 0
                    x3[ind] = (1 - emis[ind]) / emis[ind] * x2[ind]
                    x4[ind] = demis[ind] / (emis[ind] * emis[ind]) * x2[ind]
                    x5 = (BT8 - BT9) / 2
                    x6[ind] = (1 - emis[ind]) / emis[ind] * x5[ind]
                    x7[ind] = demis[ind] / (emis[ind] * emis[ind]) * x5[ind]
                    x8 = (BT8 - BT9) * (BT8 - BT9)

                    wvc_ = np.asarray([0, 1.25, 2.25, 3.25, 4.25, 5.25, 100])
                    vza_ = np.asarray([0, 3, 14.9, 38.6, 44.5, 51.2, 58, 65, 70, 75, 80])

                    LST = np.zeros([nl, ns])
                    for kwvc in range(len(wvc_) - 1):
                        for kvza in range(len(vza_) - 1):

                            ind = (tcw >= wvc_[kwvc]) * (tcw < wvc_[kwvc + 1]) * (vza >= vza_[kvza]) * (vza < vza_[kvza + 1]) * (
                                    BT8 > 0) * (emis8 > 0) * ind0
                            if (np.sum(ind) <= 0): continue

                            ##########################################
                            ### the normal result
                            ##########################################

                            ind1 = kvza * 6 + kwvc
                            ind2 = (kvza + 1) * 6 + kwvc
                            coeff1 = coeffs_day[ind1, :]
                            coeff2 = coeffs_day[ind2, :]
                            vzatemp = vza[ind]
                            prop2 = (vzatemp - vza_[kvza]) / (vza_[kvza + 1] - vza_[kvza])
                            prop1 = 1 - prop2
                            LSTtemp = x1 * (prop1 * coeff1[0] + coeff2[0] * prop2) + x2[ind] * (
                                    prop1 * coeff1[1] + coeff2[1] * prop2) + \
                                    x3[ind] * (prop1 * coeff1[2] + coeff2[2] * prop2) + x4[ind] * (
                                            prop1 * coeff1[3] + coeff2[3] * prop2) + \
                                    x5[ind] * (prop1 * coeff1[4] + coeff2[4] * prop2) + x6[ind] * (
                                            prop1 * coeff1[5] + coeff2[5] * prop2) + \
                                    x7[ind] * (prop1 * coeff1[6] + coeff2[6] * prop2) + x8[ind] * (
                                            prop1 * coeff1[7] + coeff2[7] * prop2)

                            LST[ind] = LSTtemp

                    ind = LST > 365
                    LST[ind] = 365
                    ind = LST < 220
                    LST[ind] = 0
                    LST = LST * 100
                    lstF = LST
                
                metadata = {
                    'Author': 'TIRT team',
                    'Version': 'v 1.0',
                    'Create_time': datetime.utcnow().isoformat() + 'Z',
                }

                with h5py.File(outfile_lst, 'w') as h5f:
                    if if_lst_n:
                        lstN_data = h5f.create_dataset('lstN', data=lstN, compression='gzip', dtype=np.uint16)
                        lstN_data.attrs['scalar'] = 0.01
                    if if_lst_f:
                        lstF_data = h5f.create_dataset('lstO', data=lstF, compression='gzip', dtype=np.uint16)
                        lstF_data.attrs['scalar'] = 0.01
