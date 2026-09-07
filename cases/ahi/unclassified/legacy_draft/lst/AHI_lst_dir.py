from util.util import *


'''
AHI计算
计算整个文件夹下的数据，而不是所有的全年时刻
'''

# os.environ['PROJ_LIB'] = r'C:\ProgramData\Anaconda3\envs\python37\Library\share\proj'
############################
### functions
##############################

ndvi_min = 0.05
ndvi_max = 0.95

indir_tif = r'F:\data\AHI_2022_heihe\ahi_tif\\'
outdir_lst = r'F:\data\AHI_2022_heihe\ahi_lst\\'

indir_emis = r'D:\data\emis\\'
indir_type =r'D:\data\type\\'
indir_split = r'D:\data\base\\'

infile10 = indir_emis + 'heihe//emis1_heihe_utm47N.tif'
infile11 = indir_emis + 'heihe//emis2_heihe_utm47N.tif'
infile13 = indir_emis + r'IGBP_Emi.txt'
infile12 = indir_type + 'type_heihe_2000_utm47N.tif'
infile14 = indir_split + 'Himawari8_AHI_SW_Seebor_Coef_Day.txt'
infile15 = indir_split + 'Himawari8_AHI_SW_Seebor_Coef_Night.txt'

# 0.fvc通过lai计算，1.通过lai产品算fvc
iffvc = 0
indir_fvc = ''

# 0.tcw设置为0,1.tcw通过ERA5产品得到
iftcw  = 1
indir_tcw = r'F:\data\ERA5_tcw_tif\\'

# 查找水汽对应坐标
dataset = gdal.Open(infile12)
[data, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile12)
nsi = np.zeros([nl, ns])
nli = np.zeros([nl, ns])
for k in range(nl):
    nli[k, :] = k
    nsi[k, :] = np.linspace(0, ns - 1, ns)
nli = np.reshape(nli,-1)
nsi = np.reshape(nsi,-1)
dataset = gdal.Open(infile12)
temp1, temp2 = imagexy2geo(dataset, nli, nsi)
lon, lat = geo2lonlat(dataset, temp1, temp2)
lon = np.reshape(lon,[nl,ns])
lat = np.reshape(lat,[nl, ns])
tcw_dir_0 = r"F:\data\ERA5_tcw_tif\2017\\\001\\ERA5_tcw_2017_001_00.tif"
dataset = gdal.Open(tcw_dir_0)
indx, indy = loc2map(lat, lon, dataset)



coeffs_day = read_txt_array(infile14, 0, 15)
coeffs_day = coeffs_day[:, 2:10]
coeffs_night = read_txt_array(infile15, 0, 15)
coeffs_night = coeffs_night[:, 2:10]

[emis1_s, ns, nl, nb, geog, proj] = read_image_gdal(infile10)
emis1_s = emis1_s / 1000.0
[emis2_s, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile11)
emis2_s = emis2_s / 1000.0
[classif, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile12)
classif = np.asarray(classif, np.int)
emis_v = read_txt_array(infile13, 0, 2)


# 此处vza应为根据type裁剪过的vza
infile_vza = r'D:\data\base\AHI_vza_heihe_utm47N_2000.tif'
[vza,ns,nl,nb,geog,proj] = read_image_gdal(infile_vza)


off = 7
infiles = search_file(indir_tif,['bt1.tif'])
for k in range(np.size(infiles)):
    fileName = infiles[k]

    infile = indir_tif + fileName
    print(k,infile)

    fsize = os.path.getsize(infile)
    if fsize < 900: continue

    date_str = fileName[4:11]
    time_str = fileName[12:16]
    doy_str = fileName[8:11]
    doy = np.int(doy_str)
    year = (np.uint(date_str[0:4]))
    month = (np.uint(date_str[4:6]))
    day = (np.uint(date_str[6:8]))

    hh = np.int(time_str[:2])
    mm = np.int(time_str[2:4])

    infile1 = indir_tif + fileName[:-off] + 'bt1.tif'
    infile2 = indir_tif + fileName[:-off] + 'bt2.tif'
    # infile5 = indir_tif + fileName[:-off] + 'tcw.tif'
    outfile = outdir_lst + fileName[:-off] + 'lst.tif'
    infile3 = indir_tif + fileName[:-off] + 'red.tif'
    infile4 = indir_tif + fileName[:-off] + 'nir.tif'

    if os.path.exists(outfile) == 1:
        print('file exists')
        continue

    if os.path.exists(infile1) * os.path.exists(infile2)  == 0:
        print('missing data')
        continue

    [BT8, ns, nl, nb, geog, proj] = read_image_gdal(infile1)
    [BT9, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile2)
    # [tcw, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile5)
    [red, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile3)
    [nir, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile4)
    # tcw = resize_data_ls(tcw,nl,ns)
    ndvi = (nir - red) / (nir + red)

    # fvcNames = search_file(indir_fvc,[doy_str+'_fvcAhi'])
    # if len(fvcNames)==0: continue
    # infile9 = indir_fvc + fvcNames[0]
    # if os.path.exists(infile9) == 0:
    #     continue
    # [fvc, ns0, nl0, temp3, temp4, temp5] = read_image_gdal(infile9)
    fvc = (ndvi - ndvi_min) / (ndvi_max - ndvi_min)
    fvc = resize_data(fvc,nl, ns)
    fvc[fvc > 1] = 1
    fvc[fvc < 0] = 0

    vza = resize_data(vza, nl, ns)

    ind0 = (classif < 17) *(classif > 0)

    '''水汽'''
    if not iftcw:
        tcw = 1.0
    elif iftcw:
        hour = hh
        min = mm
        if hour != 23:
            tcw_filename1 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % hour
            tcw_filename2 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % (hour + 1)
        else:
            if doy == 365: continue
            tcw_filename1 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % hour
            tcw_filename2 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % (doy + 1) + "00.tif"
        tcw_dir1 = indir_tcw + "/%04d/" % year+ "/%03d/" % doy + tcw_filename1
        tcw_dir2 = indir_tcw + "/%04d/" % year+"/%03d/" % doy + tcw_filename2
        [tcw1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir1)
        [tcw2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir2)
        f = min / 60
        tcw_data = (f * tcw2 + (1 - f) * tcw1) / 100 / 10
        tcw = np.zeros([nl, ns])
        tcw = tcw_data[indx, indy]
        tcw = np.reshape(tcw, [nl, ns])

    # fvc = (ndvi - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc = resize_data_ls(fvc, nl, ns)


    emis1_v = emis_v[classif, 0] / 1000.0
    emis2_v = emis_v[classif, 1] / 1000.0
    emis1_v = np.reshape(emis1_v, [nl, ns])
    emis2_v = np.reshape(emis2_v, [nl, ns])
    # fvc = np.reshape(fvc, [nl, ns])
    emis1_s = np.resize(emis1_s,[nl,ns])
    emis2_s = np.resize(emis2_s, [nl, ns])

    F = 0.75  # 地形因子
    C1 = (1 - emis1_s) * emis1_v * F * (1 - fvc)  # 多次散射项
    C2 = (1 - emis2_s) * emis2_v * F * (1 - fvc)  # 多次散射项
    emis8 = emis1_s * (1 - fvc) + emis1_v * fvc + C1
    emis9 = emis2_s * (1 - fvc) + emis2_v * fvc + C2
    emis8[emis8 > 0.995] = 0.995
    emis9[emis9 > 0.995] = 0.995

    # emis8 = emis1_s*(1-fvc) + emis1_v*fvc
    # emis9 = emis2_s*(1-fvc) + emis2_v*fvc

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

            ind = (tcw >= wvc_[kwvc]) * (tcw < wvc_[kwvc + 1]) * (vza >= vza_[kvza]) * (vza < vza_[kvza + 1]) * (BT8 > 0) * (emis8 > 0)*ind0
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
    outfile = outdir_lst + fileName[:-off] + 'lst.tif'
    write_image_gdal(LST, ns, nl, 1, geog, proj, outfile)

