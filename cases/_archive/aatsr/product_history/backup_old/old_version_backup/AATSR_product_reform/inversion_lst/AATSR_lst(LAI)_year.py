# sys.path.append('/data1/home/AircasBianzj/code/')
from utils.old.util import *
from utils.old.util_constant import *
import math
# from utils.myfun_lyf import *
import calendar
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

# year = sys.argv[1]
# month = sys.argv[2]
# day = sys.argv[3]


'''
23.9.16 AATSR垂直观测lst反演（LAI）
'''

if_lst_n = 1
if_lst_f = 1
ifind = 1

ndvi_min = ndvi_min_g
ndvi_max = ndvi_max_g

'''
type    0.01    36000*18000
lai     0.01    36000*18000
ERA5    0.2     1800*900
'''
# indir_tif_ = r'G:\AATSR\\'
# indir_base = r'G:\data\0_base\base/'
# indir_type = r'G:\data\0_base\type/'
# indir_tcw = r'G:\ERA5_tcw_2002-2012\tif\\'
# indir_lai_ = r'G:\Musyq_LAI_2002-2012\mosaic\\'
indir_tif_ = r'/mnt/g/AATSR/'
indir_base = r'/mnt/g/data/0_base/base/'
indir_type = r'/mnt/g/data/0_base/type/'
indir_tcw = r'/mnt/g/ERA5_tcw_2002-2012/tif/'
indir_lai_ = r'/mnt/g/Musyq_LAI_2002-2012/mosaic/'

emis1_dir = indir_base + 'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
emis2_dir = indir_base + 'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE12.tif'
IGBP_dir = indir_base + r'IGBP_Emi.txt'
type_dir = indir_type + 'type_world_1000.tif'
SW_day_dir = indir_base + 'Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt'
SW_night_dir = indir_base + 'Sentinel3A_SLSTR_SW_Seebor_Coef_Night.txt'
tcw0_dir = indir_type + r"tcw0.tif"

coeffs_day = read_txt_array(SW_day_dir, 0, 15)
coeffs_day = coeffs_day[:, 2:10]
coeffs_night = read_txt_array(SW_night_dir, 0, 15)
coeffs_night = coeffs_night[:, 2:10]

[emis1_s_, ns, nl, nb, geog, proj] = read_image_gdal(emis1_dir)
emis1_s_ = emis1_s_ / 1000.0
[emis2_s_, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(emis2_dir)
emis2_s_ = emis2_s_ / 1000.0
[classif_, ns_type, nl_type, temp3, temp4, temp5] = read_image_gdal(type_dir)
classif_ = np.asarray(classif_, np.int)
emis_v = read_txt_array(IGBP_dir, 0, 2)



for year in range(2008,2009):
    indir_lai = indir_lai_ + "//%04d//" % int(year)
    for month in range(3,4):
        print(year,month)
        daynum = calendar.monthrange(int(year),int(month))[1]
        for day in range(daynum):

            time_str = "%02d//" % month + "%02d//" % (day + 1)
            indir_tif = indir_tif_ + r"/%04d/tif/" % int(year) + time_str
            if not os.path.exists(indir_tif): continue
            indir_lst = indir_tif_ + r"/%04d/lst/" % int(year) + time_str
            mkdir_if_not_exist(indir_lst)
            fileNames = search_file_rej(indir_tif, ['bt1', 'n.'], 'enp')
            fileNum = np.size(fileNames)
            off = 9
            for k in range(fileNum):
                if if_lst_n:
                    mkdir_if_not_exist(indir_lst)
                    fileName = fileNames[k]
                    year = fileName[6:10]
                    doy_str = fileName[11:14]
                    time_str = fileName[15:21]
                    doy = np.int(doy_str)
                    m, d = doy2date(year, doy)

                    outfile = indir_lst + fileName[:-off] + 'lst_n.tif'
                    print(fileName[:-off] + 'lst_n.tif')
                    # if os.path.exists(outfile) == 1: continue

                    '''读取数据'''
                    bt1_n_dir = indir_tif + fileName[:-off] + 'bt1_n.tif'
                    bt2_n_dir = indir_tif + fileName[:-off] + 'bt2_n.tif'
                    vza_n_dir = indir_tif + fileName[:-off] + 'vza_n.tif'
                    red_n_dir = indir_tif + fileName[:-off] + 'red_n.tif'
                    nir_n_dir = indir_tif + fileName[:-off] + 'nir_n.tif'

                    [BT8, ns, nl, nb, geog, proj] = read_image_gdal(bt1_n_dir)
                    [BT9, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(bt2_n_dir)
                    [vza, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(vza_n_dir)
                    # [red, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(red_n_dir)
                    # [nir, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(nir_n_dir)
                    BT8 = BT8 / 100
                    BT9 = BT9 / 100
                    # red = red / 100
                    # nir = nir / 100
                    vza = vza / 100
                    vza = 90 - vza

                    '''根据type文件找对应坐标并保存'''
                    dataset = gdal.Open(type_dir)
                    lon_dir = indir_tif + fileName[:-off] + 'lon.tif'
                    lat_dir = indir_tif + fileName[:-off] + 'lat.tif'
                    [lon, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(lon_dir)
                    [lat, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(lat_dir)
                    indx, indy = loc2map(lat, lon, dataset)
                    indx[indx >= 18000] = 0
                    indy[indy >= 36000] = 0
                    if ifind:
                        outfile_indx = indir_tif + fileName[:-off] + 'indx.tif'
                        outfile_indy = indir_tif + fileName[:-off] + 'indy.tif'
                        write_image_gdal(np.reshape(indx,[nl, ns]).astype(uint16), ns, nl, 1, '', '',outfile_indx)
                        write_image_gdal(np.reshape(indy,[nl, ns]).astype(uint16), ns, nl, 1, '', '',outfile_indy)


                    emis1_s = emis1_s_[indx, indy]
                    emis2_s = emis2_s_[indx, indy]
                    classif = classif_[indx, indy]
                    emis1_s = np.reshape(emis1_s, [nl, ns])
                    emis2_s = np.reshape(emis2_s, [nl, ns])
                    classif = np.reshape(classif, [nl, ns])


                    '''读取LAI'''
                    doy1 = (doy // 4) * 4 + 1
                    doy2 = (doy // 4) * 4 + 5
                    infile_lai1 = indir_lai + r"MuSyQ.CSC.LAI.A" + '%04d%03d' %(int(year),doy1) + '.tif'
                    infile_lai2 = indir_lai + r"MuSyQ.CSC.LAI.A" + '%04d%03d' %(int(year),doy2) + '.tif'
                    if not os.path.exists(infile_lai2): infile_lai2=infile_lai1
                    [lai1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai1)
                    [lai2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai2)
                    lai = (1-(doy-doy1)/4) * lai1[indx,indy] + (doy-doy1)/4 * lai2[indx,indy]
                    lai = np.reshape(lai, [nl, ns])
                    lai[lai>=30000] = 0
                    lai = lai/1000

                    fvc = cal_fvc_from_lai(vza,lai)

                    # outfile_lai = indir_tif + fileName[:-off] + 'lai.tif'
                    # write_image_gdal(np.reshape(lai, [nl, ns]), ns, nl, 1, '', '', outfile_lai)
                    # outfile_fvc = indir_tif + fileName[:-off] + 'fvcN.tif'
                    # write_image_gdal(np.reshape(fvc, [nl, ns]), ns, nl, 1, '', '', outfile_fvc)
                    # outfile_type = indir_tif + fileName[:-off] + 'type.tif'
                    # write_image_gdal(np.reshape(classif, [nl, ns]), ns, nl, 1, '', '', outfile_type)

                    '''读取水汽'''
                    indx_tcw = np.floor(np.array(indx/20))
                    indy_tcw = np.floor(np.array(indy/20))

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
                    tcw_dir1 = indir_tcw + "/%04d/" % year + "/%03d/" % doy + tcw_filename1
                    tcw_dir2 = indir_tcw + "/%04d/" % year + "/%03d/" % doy2 + tcw_filename2
                    [tcw1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir1)
                    [tcw2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir2)
                    f = min / 60
                    indx_tcw = indx_tcw.astype('uint16')
                    indy_tcw = indy_tcw.astype('uint16')
                    tcw_data = (f * tcw2[indx_tcw,indy_tcw] + (1 - f) * tcw1[indx_tcw,indy_tcw]) / 100 / 10

                    tcw = np.reshape(tcw_data, [nl, ns])

                    # outfile_tcw = indir_tif + fileName[:-off] + 'tcw.tif'
                    # write_image_gdal(np.reshape(tcw, [nl, ns]), ns, nl, 1, '', '', outfile_tcw)

                    ind0 = (classif < 17) * (classif > 0)
                    classif[classif == 255] = 17

                    emis1_v = emis_v[classif, 0] / 1000.0
                    emis2_v = emis_v[classif, 1] / 1000.0
                    emis1_v = np.reshape(emis1_v, [nl, ns])
                    emis2_v = np.reshape(emis2_v, [nl, ns])

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
                    LST = LST*100
                    outfile = indir_lst + fileName[:-off] + 'lst_n.tif'
                    write_image_gdal(LST.astype('uint16'), ns, nl, 1, '', '', outfile)

                if if_lst_f:
                    outfile = indir_lst + fileName[:-off] + 'lst_f.tif'
                    print(fileName[:-off] + 'lst_f.tif')
                    # if os.path.exists(outfile) == 1: continue

                    '''读取数据'''
                    bt1_f_dir = indir_tif + fileName[:-off] + 'bt1_f.tif'
                    bt2_f_dir = indir_tif + fileName[:-off] + 'bt2_f.tif'
                    vza_f_dir = indir_tif + fileName[:-off] + 'vza_f.tif'
                    red_f_dir = indir_tif + fileName[:-off] + 'red_f.tif'
                    nir_f_dir = indir_tif + fileName[:-off] + 'nir_f.tif'

                    [BT8, ns, nl, nb, geog, proj] = read_image_gdal(bt1_f_dir)
                    [BT9, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(bt2_f_dir)
                    [vza, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(vza_f_dir)
                    # [red, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(red_f_dir)
                    # [nir, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(nir_f_dir)
                    BT8 = BT8 / 100
                    BT9 = BT9 / 100
                    # red = red / 100
                    # nir = nir / 100
                    vza = vza / 100
                    vza = 90 - vza

                    fvc = cal_fvc_from_lai(vza,lai)

                    # outfile_fvc = indir_tif + fileName[:-off] + 'fvcO.tif'
                    # write_image_gdal(np.reshape(fvc, [nl, ns]), ns, nl, 1, '', '', outfile_fvc)

                    # '''计算fvc'''
                    # ndvi = (nir - red) / (nir + red)
                    # ndvi[np.isnan(ndvi)] = 0
                    # fvc = (ndvi - ndvi_min) / (ndvi_max - ndvi_min)
                    # fvc = resize_data(fvc, nl, ns,0)
                    # fvc[fvc > 1] = 1
                    # fvc[fvc < 0] = 0

                    # '''读取水汽'''
                    # hour = math.floor(int(time_str) / 10000)
                    # min = int((int(time_str) - math.floor(int(time_str) / 10000) * 10000) / 100)
                    # year = int(year)
                    # doy2 = doy
                    # if hour != 23:
                    #     tcw_filename1 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % hour
                    #     tcw_filename2 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % (hour + 1)
                    # else:
                    #     doy2 = doy2 + 1
                    #     if doy == 365 or doy == 366:
                    #         tcw_filename1 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % hour
                    #         tcw_filename2 = tcw_filename1
                    #     tcw_filename1 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % hour
                    #     tcw_filename2 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % (doy + 1) + "00.tif"
                    # tcw_dir1 = indir_tcw + "/%04d/" % year+ "/%03d/" % doy + tcw_filename1
                    # tcw_dir2 = indir_tcw + "/%04d/" % year+ "/%03d/" % doy2 + tcw_filename2
                    # [tcw1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir1)
                    # [tcw2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir2)
                    # f = min / 60
                    # tcw_data = (f * tcw2 + (1 - f) * tcw1) / 100 / 10
                    #
                    # '''根据lon、lat调整tcw'''
                    # dataset = gdal.Open(tcw0_dir)
                    # lon_dir = indir_tif + fileName[:-off] + 'lon.tif'
                    # lat_dir = indir_tif + fileName[:-off] + 'lat.tif'
                    # [lon, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(lon_dir)
                    # [lat, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(lat_dir)
                    # indx, indy = loc2map(lat, lon, dataset)
                    # indx[indx == 721] = 0
                    # indy[indy == 1440] = 0
                    # tcw = tcw_data[indx, indy]
                    # tcw = np.reshape(tcw, [nl, ns])

                    # '''根据lon、lat调整emis'''
                    # dataset = gdal.Open(emis1_dir)
                    # indx, indy = loc2map(lat, lon, dataset)
                    # indx[indx == 18000] = 0
                    # indy[indy == 36000] = 0
                    # emis1_s = emis1_s_[indx, indy]
                    # emis2_s = emis2_s_[indx, indy]
                    # classif = classif_[indx, indy]
                    # emis1_s = np.reshape(emis1_s, [nl, ns])
                    # emis2_s = np.reshape(emis2_s, [nl, ns])
                    # classif = np.reshape(classif, [nl, ns])

                    '''构建emis'''
                    ind0 = (classif < 17) * (classif > 0)
                    # # tcw = tcw / 10.0
                    # # tcw = resize_data_near(tcw,nl0,ns0)
                    # tcw = np.zeros([nl, ns])
                    # tcw[:] = 1.0

                    classif[classif == 255] = 17

                    emis1_v = emis_v[classif, 0] / 1000.0
                    emis2_v = emis_v[classif, 1] / 1000.0
                    emis1_v = np.reshape(emis1_v, [nl, ns])
                    emis2_v = np.reshape(emis2_v, [nl, ns])

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
                    outfile = indir_lst + fileName[:-off] + 'lst_f.tif'
                    write_image_gdal(LST.astype('uint16'), ns, nl, 1, '', '', outfile)
