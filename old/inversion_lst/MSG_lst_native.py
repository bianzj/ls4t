from util.util import *
import calendar
import warnings
warnings.filterwarnings("ignore")

'''MSG反演地表温度'''
'''对应的是MSG全境native格式的数据'''


ndvi_min = 0.05
ndvi_max = 0.95


# 2017年全部是MSG3
sat_name = 'MSG3'  # MSG2,MSG3,MSG4
# indir_tif = r'F:\data\MSG_2017_full-range\native\tif\Europe\\'
# indir_lst = r'F:\data\MSG_2017_full-range\native\lst\Europe\\'

indir_tif = r'F:\data\MSG_2017_full-range\native\tif\Full\\'
indir_lst = r'F:\data\MSG_2017_full-range\native\lst\Full\\'


mkdir_if_not_exist(indir_lst)


indir_base = r'D:\data\base\\'
indir_emis = r'D:\data\emis\\'
indir_type =r'D:\data\type\\'
indir_tcw = r"F:\data\ERA5_tcw_tif\2017\\"

# indir_emis1 = indir_emis + 'emis1_Europe_0.03.tif'
# indir_emis2 = indir_emis + 'emis2_Europe_0.03.tif'
# indir_type = indir_type + 'type_Europe_0.03.tif'
# indir_vza = r"D:\data\base\msg_angle\\" + "Europe_vza_0.03.tif"
indir_emis1 = indir_emis + 'emis1_MSG_Full_0.03.tif'
indir_emis2 = indir_emis + 'emis2_MSG_Full_0.03.tif'
indir_type = indir_type + 'type_MSG_Full_0.03.tif'
indir_vza = r"D:\data\base\msg_angle\\" + "Full_vza_0.03.tif"


indir_IGBP = indir_emis + r'IGBP_Emi.txt'
indir_SW_cof = indir_base + sat_name + '_SEVIRI_SW_Seebor_Coef_Day.txt'


'''读取数据'''
# 读取劈窗参数
coeffs_day = read_txt_array(indir_SW_cof, 0, 15)
coeffs_day = coeffs_day[:, 2:10]

# 查找水汽对应坐标
dataset = gdal.Open(indir_type)
[data, ns, nl, nb, geog_type, proj_type] = read_image_gdal(indir_type)
nsi = np.zeros([nl, ns])
nli = np.zeros([nl, ns])
for k in range(nl):
    nli[k, :] = k
    nsi[k, :] = np.linspace(0, ns - 1, ns)
nli = np.reshape(nli,-1)
nsi = np.reshape(nsi,-1)
dataset = gdal.Open(indir_type)
temp1, temp2 = imagexy2geo(dataset, nli, nsi)
lon, lat = geo2lonlat(dataset, temp1, temp2)
lon = np.reshape(lon,[nl,ns])
lat = np.reshape(lat,[nl, ns])
tcw_dir_0 = r"F:\data\ERA5_tcw_tif\2017\\\001\\ERA5_tcw_2017_001_00.tif"
dataset = gdal.Open(tcw_dir_0)
indx, indy = loc2map(lat, lon, dataset)

# 读取土壤发射率
[emis1_s_data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(indir_emis1)
emis1_s_data = emis1_s_data / 1000.0
[emis2_s_data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(indir_emis2)
emis2_s_data = emis2_s_data / 1000.0

# 读取分类和植被发射率
[classif, ns, nl, nb, geog, proj] = read_image_gdal(indir_type)
classif = np.asarray(classif, np.int)
emis_v = read_txt_array(indir_IGBP, 0, 2)
dataset = gdal.Open(indir_type)

emis1_s = np.resize(emis1_s_data,[nl,ns])
emis2_s = np.resize(emis2_s_data,[nl,ns])

# 读取vza
[vza, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(indir_vza)

year= 2017
for m in range(1, 2):
    daynum = calendar.monthrange(year, m + 1)[1]
    for d in range(0,1):
        month = m + 1
        day = d + 1
        indir_tif_day = indir_tif + "/%02d" % month + "/%02d//" % day
        indir_lst_day = indir_lst + "/%02d" % month + "/%02d//" % day
        if not os.path.exists(indir_tif_day): continue
        mkdir_if_not_exist(indir_lst_day)
        '''开始反演'''
        fileNames = search_file_rej(indir_tif_day, ['bt1'], 'enp')
        fileNum = len(fileNames)
        off = 7
        for k in range(fileNum):
            fileName = fileNames[k]
            infile = indir_tif_day + fileName
            print(k, infile)
            # 时间信息
            date_str = fileName[5:13]
            time_str = fileName[13:17]
            year = int(date_str[0:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            hour = int(time_str[0:2])
            minute = int(time_str[2:4])

            doy = date2DOY(2017, month, day)

            # 读取数据
            infile1 = indir_tif_day + fileName[:-off] + 'bt1.tif'
            infile2 = indir_tif_day + fileName[:-off] + 'bt2.tif'
            infile3 = indir_tif_day + fileName[:-12] + '1200_red.tif'
            infile4 = indir_tif_day + fileName[:-12] + '1200_nir.tif'

            [BT8, ns, nl, nb, geog, proj] = read_image_gdal(infile1)
            [BT9, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile2)
            [red, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile3)
            [nir, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile4)

            BT8 = BT8/100
            BT9 = BT9/100
            red = red/100
            ninr = nir/100

            # 计算fvc
            ndvi = (nir - red) / (nir + red)
            fvc = (ndvi - ndvi_min) / (ndvi_max - ndvi_min)
            fvc = resize_data(fvc, nl, ns)
            fvc[fvc > 1] = 1
            fvc[fvc < 0] = 0

            # 读取水汽
            if hour != 23:
                tcw_filename1 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % hour
                tcw_filename2 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % (hour + 1)
                tcw_dir1 = indir_tcw + "/%03d/" % doy + tcw_filename1
                tcw_dir2 = indir_tcw + "/%03d/" % doy + tcw_filename2
            else:
                if doy == 365: continue
                tcw_filename1 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % hour
                tcw_filename2 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % (doy + 1) + "00.tif"
                tcw_dir1 = indir_tcw + "/%03d/" % doy + tcw_filename1
                tcw_dir2 = indir_tcw + "/%03d/" % (doy + 1) + tcw_filename2

            [tcw1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir1)
            [tcw2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir2)
            f = minute / 60
            tcw_data = (f * tcw2 + (1 - f) * tcw1) / 100 / 10
            tcw = np.zeros([nl, ns])
            tcw = tcw_data[indx, indy]
            tcw = np.reshape(tcw, [nl, ns])

            # 通用劈窗
            classif[classif == 255] = 17
            ind0 = (classif < 17) * (classif > 0)
            emis1_v = emis_v[classif, 0] / 1000.0
            emis2_v = emis_v[classif, 1] / 1000.0
            emis1_v = np.reshape(emis1_v, [nl, ns])
            emis2_v = np.reshape(emis2_v, [nl, ns])

            emis8 = emis1_s * (1 - fvc) + emis1_v * fvc
            emis9 = emis2_s * (1 - fvc) + emis2_v * fvc

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

                    ind = (tcw >= wvc_[kwvc]) * (tcw < wvc_[kwvc + 1]) * (vza >= vza_[kvza]) * (
                                vza < vza_[kvza + 1]) * (
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
            ind = LST < 225
            LST[ind] = 0
            outfile = indir_lst_day + fileName[:-off] + 'lst.tif'
            write_image_gdal(LST, ns, nl, 1, geog, proj, outfile)









