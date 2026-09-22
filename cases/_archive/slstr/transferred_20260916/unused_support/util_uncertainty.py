from cases.slstr.support.util_packages import *
from cases.slstr.support.util_data import *
from cases.slstr.support.util_file import *
from cases.slstr.support.util_constant import *
from cases.slstr.support.util_phys import *



#### 从遥感极轨图像提取数据，每天一景
def get_data_from_polar():

    infile_loc = r'E:\field\heihe_site.txt'
    mydata = read_txt_str(infile_loc, ',')
    mydata = np.asarray(mydata)
    lon = np.asarray(mydata[:, 1], dtype=np.float16)
    lat = np.asarray(mydata[:, 2], dtype=np.float16)

    ############################################################################
    dayNight = 'day'
    nadirObliq = 'obliq'
    symbol = 's3b'

    ### Ermida
    outfile = r'E:\\ship_vnir\\' + symbol + '_lst_' + dayNight + '_' + nadirObliq + '_Ermida.txt'
    indir_lst = r'E:\ShIP_VNIR\Ecoeff_static_heihe\\'

    ### 直接使用
    # outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_direct.txt'
    # indir_lst = r'E:\ShIP_VNIR\LST_direct_heihe\\'

    ### 红光使用
    # outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_step_vt_red.txt'
    # indir_lst = r'E:\ShIP_VNIR\LST_step_vt_red_heihe\\'
    #
    # ### 近红外使用
    # outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_step_vt_nir.txt'
    # indir_lst = r'E:\ShIP_VNIR\LST_step_vt_nir_heihe\\'

    ### 分步使用
    # outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_step.txt'
    # indir_lst = r'E:\ShIP_VNIR\LST_step_heihe\\'

    ### 集成使用
    # outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_step_one.txt'
    # indir_lst = r'E:\ShIP_VNIR\LST_step_one_heihe\\'

    ### 原始温度产品
    # outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_origin.txt'
    # indir_lst = r'E:\SLSTR\\'+symbol+'_heihe\lst\\'

    indir_tif = r'E:\SLSTR\\' + symbol + '_heihe\\tif\\'
    ###############################################################################

    infile_ref = r'E:\type\type_heihe_1000.tif'
    dataset = gdal.Open(infile_ref)
    im_width = dataset.RasterXSize * 1
    im_height = dataset.RasterYSize * 1
    im_bands = dataset.RasterCount * 1
    data = dataset.ReadAsArray(0, 0, im_width, im_height)
    im_geotrans = dataset.GetGeoTransform()
    im_proj = dataset.GetProjection()
    temp1, temp2 = lonlat2geo(dataset, lat, lon)
    imagex, imagey = geo2imagexy(dataset, temp1, temp2)
    imagex = np.asarray(imagex, dtype=np.int16)
    imagey = np.asarray(imagey, dtype=np.int16)

    result_ = []
    num_loc = 9
    for kdoy in range(1, 366):

        file = symbol + '_2019%03d_' % kdoy + dayNight

        infile_lst = indir_lst + file + '_lst_' + nadirObliq + '.tif'
        infile_pst = indir_tif + file + '_time.tif'
        infile_tcc = indir_tif + file + '_cloud_' + nadirObliq + '.tif'
        infile_vza = indir_tif + file + '_vza_' + nadirObliq + '.tif'

        result = np.zeros(38)
        result[0] = kdoy
        print(infile_lst, infile_pst)
        if (os.path.exists(infile_lst) == 0) or (os.path.exists(infile_pst) == 0):
            result_.append(result)
            continue

        [pst, ns, nl, nb, geog, proj] = read_image_gdal(infile_pst)
        pst = np.max(pst[imagex, imagey])
        result[1] = (pst)

        [lst, ns, nl, nb, geog, proj] = read_image_gdal(infile_lst)
        # result[2:11]=(lst[imagex,imagey])
        # result[2:2 + num_loc] = a(lst, imagex, imagey, 0, 250, 350)

        [tcc, ns, nl, nb, geog, proj] = read_image_gdal(infile_tcc)
        # result[11:]=(tcc[imagex,imagey])
        # result[11:11 + num_loc] = a(tcc, imagex, imagey, 1, -1, 500)

        [vza, ns, nl, nb, geog, proj] = read_image_gdal(infile_vza)
        vza = vza[imagex, imagey]
        result[20:20 + num_loc] = vza

        if dayNight == 'day':
            infile_sza = indir_tif + file + '_sza_' + nadirObliq + '.tif'
            infile_vaa = indir_tif + file + '_vaa_' + nadirObliq + '.tif'
            infile_saa = indir_tif + file + '_saa_' + nadirObliq + '.tif'

            [vaa, ns, nl, nb, geog, proj] = read_image_gdal(infile_vaa)
            vaa = vaa[imagex, imagey]
            [sza, ns, nl, nb, geog, proj] = read_image_gdal(infile_sza)
            sza = sza[imagex, imagey]
            [saa, ns, nl, nb, geog, proj] = read_image_gdal(infile_saa)
            saa = saa[imagex, imagey]

            psi = np.abs(vaa - saa)
            thetas = np.deg2rad(sza)
            thetaa = np.deg2rad(psi)
            thetav = np.deg2rad(abs(vza))

            f = np.sqrt(
                (np.power(np.tan(thetas), 2) + np.power(np.tan(thetav), 2) - 2 * np.tan(thetas) * np.tan(thetav) *
                 np.cos(thetaa)))
            result[29:29 + num_loc] = f

        print(file, kdoy)
        result_.append(result)

    result_ = np.asarray(result_)
    np.savetxt(outfile, result_, fmt='%5.3f')

### 从遥感静止卫星提取数据，每小时一景
def get_data_from_geo():
    ############################################################################
    symbol = 'AHI'
    station = 'dongbei'
    ### DTC 与VinRL
    # method ='dtc'
    # outfile = r'F:\result\ShIP_DVT\\lst_'+method+"_"+station+'.txt'
    # indir_lst0 =  r'F:\result\ShIP_DVT\lst_dtc_'+station+'\\'
    # indir_tif0 = r'F:\data\ShIP_DVT\ahi_'+station+'\\tif\\'
    # npixel = 0

    # method ='DVT'
    #
    # outfile = r'D:\data\ship_dvt\\lst_'+method+station+'.txt'
    # indir_lst0 = r'D:\data\ship_dvt\nadir_'+method+'_'+station+'\\'
    # indir_tif0 = r'D:\data\zsy_cut\ahi_'+station+'\\tif\\'
    #
    #
    method = 'o'
    outfile = r'F:\result\ShIP_DVT\\lst_' + method + "_" + station + '.txt'
    indir_lst0 = r'F:\data\ShIP_DVT\ahi_' + station + '\\lst\\'
    indir_tif0 = r'F:\data\ShIP_DVT\ahi_' + station + '\\tif\\'
    npixel = 0

    infile_loc = r'F:\data\field\\' + station + '_site.txt'
    mydata = read_txt_str(infile_loc, ',')
    mydata = np.asarray(mydata)
    lon = np.asarray(mydata[:, 1], dtype=np.float_)
    lat = np.asarray(mydata[:, 2], dtype=np.float_)

    ################################################################################
    indir_map = r'F:\data\ShIP_DVT\base\\' + station + '\\'
    infile_type = infile8 = indir_map + 'type_China_1000.tif'
    [type0, ns0, nl0, nb, geog, proj] = read_image_gdal(infile_type)
    indir_map = r'F:\data\ShIP_DVT\base\\' + station + '_ahi\\'
    infile_vza = infile8 = indir_map + 'ahi_vza_china.tif'
    [vza0, ns, nl, nb, geog, proj] = read_image_gdal(infile_vza)
    infile_vaa = infile8 = indir_map + 'ahi_vaa_china.tif'
    [vaa0, ns, nl, nb, geog, proj] = read_image_gdal(infile_vaa)

    lst = np.asarray([])
    lst_obliq = np.asarray([])
    lst_nadir_normalized = np.asarray([])
    lst_obliq_normalized = np.asarray([])
    days_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    nss = ns
    nll = nl

    ###############################################################################

    infile_ref = infile_vza
    dataset = gdal.Open(infile_ref)
    im_width = dataset.RasterXSize * 1
    im_height = dataset.RasterYSize * 1
    im_bands = dataset.RasterCount * 1
    data = dataset.ReadAsArray(0, 0, im_width, im_height)
    im_geotrans = dataset.GetGeoTransform()
    im_proj = dataset.GetProjection()
    # 返回经纬度对应的投影坐标
    temp1, temp2 = lonlat2geo(dataset, lon, lat)
    # 将投影坐标或地理坐标转化为图像坐标，行列号
    imagex, imagey = geo2imagexy(dataset, temp1, temp2)
    imagex = np.asarray(imagex, dtype=np.int16)
    # [270 218 285 226 229 219  54  54  47]
    imagey = np.asarray(imagey, dtype=np.int16)
    # [126  66 155 128 125 132 181 181 176]

    result_ = []
    #  有9个站点
    num_loc = np.size(imagex)

    for kmonth0 in range(6, 11):
        thedoy = (kmonth0 - 1) * 30 + 16

        for kday0 in range(1, 32):
            kstep = 0
            for khour0 in range(9 - 8, 17 - 8):
                indir_lst = indir_lst0 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'
                indir_tif = indir_tif0 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'

                kdoy = date2DOY(2019, kmonth0, kday0)

                khour = khour0
                kday = kday0
                kmonth = kmonth0
                if khour0 < 0:
                    kdoy = kdoy - 1
                    khour = khour0 + 24
                    if kday0 == 1:
                        if kmonth0 == 1: continue
                        kmonth = kmonth0 - 1
                        kday = days_of_month[kmonth0 - 2]
                        indir_lst = indir_lst0 + r'\%02d' % kmonth + r'\%02d' % kday + '\\'
                        indir_tif = indir_tif0 + r'\%02d' % kmonth + r'\%02d' % kday + '\\'
                    else:
                        kday = kday0 - 1
                        indir_lst = indir_lst0 + r'\%02d' % (kmonth0) + r'\%02d' % (kday) + '\\'
                        indir_tif = indir_tif0 + r'\%02d' % (kmonth0) + r'\%02d' % (kday) + '\\'

                for kmin in range(0, 4, 3):
                    pst = '%02d' % khour + '%d0' % kmin + '00'
                    result = np.zeros(4 * num_loc + 2)
                    result[0] = kdoy
                    result[1] = np.int(pst)

                    infile_lst = indir_lst + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_lst.tif'
                    infile_tcc = indir_tif + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_tcc.tif'
                    infile_sza = indir_tif + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_sza.tif'
                    infile_saa = indir_tif + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_saa.tif'
                    print(infile_lst)
                    if (os.path.exists(infile_lst) == 0):
                        # 将日期和时间写入文件中，第0列和第1列
                        result_.append(result)
                        continue

                    print(infile_lst)
                    [lst, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst)
                    [tcc, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_tcc)
                    tcc = tcc / 1000.0
                    tcc = resize_data(tcc, nl, ns)
                    if (os.path.exists(infile_sza) == 1):
                        [sza, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza)
                        [saa, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa)
                        sza = sza / 100.0
                        saa = saa / 100.0
                        saa[saa > 360] = saa[saa > 360] - 360
                    else:
                        sza = np.zeros([nl, ns]) + 90
                        saa = np.zeros([nl, ns])

                    ind = (lst < 100) * (lst != 0) * (np.isnan(lst) == 0)
                    lst[ind] = lst[ind] + 273.15
                    # 将9个站点的平均地表温度存下来，从第2列到第10列
                    result[2:2 + num_loc] = getPointfromImage(lst, imagex, imagey, npixel, 3, 250, 350)
                    # 将云量TCC存储下来，存在第11列到19列
                    result[2 + num_loc:2 + num_loc * 2] = getPointfromImage(tcc, imagex, imagey, npixel, 3, -1, 500)
                    vza = vza0[imagex, imagey]
                    vaa = vaa0[imagex, imagey]
                    # 将vza存下来，存在第20列到第28列
                    result[2 + num_loc * 2:2 + num_loc * 3] = vza
                    sza = sza[imagex, imagey]
                    saa = saa[imagex, imagey]
                    psi = np.abs(vaa - saa)
                    thetas = np.deg2rad(sza)
                    thetaa = np.deg2rad(psi)
                    thetav = np.deg2rad(abs(vza))
                    # 把9个站点热点模型中的f（d）计算出来放在文本文件的最后9列
                    cosang = np.cos(sza * rd) * np.cos(vza * rd) + np.sin(sza * rd) * np.sin(vza * rd) * np.cos(
                        psi * rd)
                    ang = np.arccos(cosang) / rd
                    print(np.average(ang))
                    # angdis_.append(ang)
                    # f = np.sqrt(
                    #     (np.power(np.tan(thetas), 2) + np.power(np.tan(thetav), 2) - 2 * np.tan(thetas) * np.tan(thetav) *
                    #      np.cos(thetaa)))
                    result[2 + num_loc * 3:2 + num_loc * 4] = ang
                    result_.append(result)

    result_ = np.asarray(result_)
    np.savetxt(outfile, result_, fmt='%5.3f')

### 提取后的数据与csv或者excl的数据进行比对，出图
def val_result_insite():
    '''
    使用地表观测数据对模拟的结果进行验证
    '''
    wl = 11.2
    start = time.clock()
    dataDir = r'F:\data\field\dongbei\\'
    infile1 = dataDir + 'DLLT_2019.csv'

    aws = pd.read_csv(infile1, parse_dates=['TIMESTAMP'], dayfirst=True)

    low = datetime(2019, 1, 1, 0)
    high = datetime(2019, 12, 31, 23)
    aws = aws[aws['TIMESTAMP'] >= low]
    aws = aws[aws['TIMESTAMP'] <= high]

    Time_aws = aws['TIMESTAMP']
    doy = Time_aws.apply(lambda x: x.dayofyear)
    hour = Time_aws.apply(lambda x: x.hour)
    minute = Time_aws.apply(lambda x: x.minute)
    t_aws = np.asarray(doy + hour / 24.0 + minute / 60.0 / 24.0, dtype=np.float)

    # Ms_aws = np.asarray((aws['Ms_2cm'].values+aws['Ms_4cm'].values)*0.5,dtype=np.float)
    # Ta_aws = np.asarray(aws['Ta_10m'].values,dtype=np.float)
    # Ws_aws = np.asarray(aws['WS_10m'].values,dtype=np.float)
    # Rh_aws = np.asarray(aws['RH_5m'].values,dtype=np.float)
    Dl_aws = np.asarray(aws['DLRC_Avg'].values, dtype=np.float)
    Ds_aws = np.asarray(aws['DR_Avg'].values, dtype=np.float)
    Ul_aws = np.asarray(aws['ULRC_Avg'].values, dtype=np.float)
    Us_aws = np.asarray(aws['UR_Avg'].values, dtype=np.float)

    # SBTempC_Avg

    Ir_aws = np.asarray(aws['TargTempC_Avg'].values, dtype=np.float)
    # Ir_aws = np.asarray(aws['SBTempC_Avg'].values,dtype=np.float)
    # Ir2_aws = np.asarray(aws['IRT_2'].values,dtype=np.float)
    # Pa_aws = np.asarray(aws['Press'].values,dtype=np.float)
    # Ir_aws = (Ir1_aws+Ir2_aws)/2.0

    # SCP,124.6388193,44.08709566
    # KS1,125.6107214,44.786944256591868
    # KS2,125.6225684,44.78738782
    # KS3,125.6165359,44.7874161
    # KS4,125.6212454,44.79092645
    # KS5,125.6186579,44.79187568
    # LWX,125.017633,44.083198
    # DLLT,125.3337201,44.56591868
    # SSP1,124.6123317,44.11951799
    # SSP2,124.5992356,44.12700706
    # TPS,124.466738,44.190351

    col = 9
    ifirt = 1
    emis = 0.975

    symbol = 'AHI'
    station = 'dongbei'
    # method = 'direct'
    methods = ['o', 'vta', 'vta', 'vt']

    method = methods[0]
    infile_lst = r'F:\result\ShIP_DVT\\' + 'lst_' + method + '_' + station + '.txt'
    print(infile_lst)
    mydata = read_txt_array(infile_lst, 0, 46)
    doy = mydata[:, 0]
    hh = mydata[:, 1] // 10000
    mm = (mydata[:, 1] % 10000) // 100
    inv0 = mydata[:, col]
    cloud = mydata[:, col + 9]
    ind = doy < 365
    doy = doy[ind]
    hh = hh[ind]
    mm = mm[ind]
    inv0 = inv0[ind]
    n_point = np.size(doy)

    kyear = 2019
    mea_ = []
    for kpoint in range(n_point):
        mea_temp = 0
        kdoy = doy[kpoint]
        khour = hh[kpoint] + 8
        kmin = mm[kpoint]
        kmonth, kday = doy2date(kyear, kdoy)
        specTime = datetime(kyear, kmonth, kday, np.int_(khour), np.int_(kmin))
        ind0 = where(aws['TIMESTAMP'] == (specTime))
        if np.sum(ind0) < 1:
            mea_.append(mea_temp)
            continue
        if np.size(ind0) > 1:
            ind1 = ind0[0][0]
            ind2 = ind1 + 1
            print('error')
        else:
            ind1 = ind0[0][0]
            ind2 = ind1 + 1
        # ind1 = np.asarray((doy-1) * 144 + (hh+8) * 6 + mm // 10,dtype=np.int32)
        # ind2 = np.asarray((doy-1) * 144 + (hh+8) * 6 + mm // 10+1,dtype=np.int32)
        rate = (kmin % 10) / 10.0

        if ifirt == 1:
            mea = (1 - rate) * (Ir_aws[ind1] + 273.15) + rate * (Ir_aws[ind2] + 273.15)
            rad = planck(wl, mea)
            rad = rad - (1 - emis) * planck(wl, 250)
            rad = rad / emis
            mea_temp = inv_planck(wl, rad)

        else:
            netrad = Ul_aws[ind1] - (1 - emis) * Dl_aws[ind1]
            netrad = netrad / (5.67 * 1e-8 * emis)
            netrad = (1 - rate) * netrad
            mea_temp = np.power(netrad, 0.25)
            # pass
        mea_.append(mea_temp)
    mea = np.asarray(mea_)

    method = methods[1]
    infile_lst = r'F:\result\ShIP_DVT\\' + 'nadir_' + method + '_' + station + '.txt'
    print(infile_lst)
    mydata = read_txt_array(infile_lst, 0, 46)
    doy = mydata[:, 0]
    inv1 = mydata[:, col]
    ind = doy < 365
    doy = doy[ind]
    hh = hh[ind]
    mm = mm[ind]
    inv1 = inv1[ind]

    method = methods[2]
    infile_lst = r'F:\result\ShIP_DVT\\' + 'nadir_' + method + '_' + station + '.txt'
    print(infile_lst)
    mydata = read_txt_array(infile_lst, 0, 46)
    doy = mydata[:, 0]
    inv2 = mydata[:, col]
    ind = doy < 365
    doy = doy[ind]
    hh = hh[ind]
    mm = mm[ind]
    inv2 = inv2[ind]

    method = methods[3]
    infile_lst = r'F:\result\ShIP_DVT\\' + 'nadir_' + method + '_' + station + '.txt'
    print(infile_lst)
    mydata = read_txt_array(infile_lst, 0, 46)
    doy = mydata[:, 0]
    inv3 = mydata[:, col]
    ind = doy < 365
    doy = doy[ind]
    hh = hh[ind]
    mm = mm[ind]
    inv3 = inv3[ind]

    dif_threshold = 7.5
    ind = (mea > 100) * (inv1 > 100) * \
          (np.abs(mea - inv3) < dif_threshold) * ((hh + 8) % 24 >= 9) * ((hh + 8) % 24 <= 17) * (cloud <= 0.001) * \
          (inv3 > 100) * (np.abs(mea - inv1) < dif_threshold) * (inv2 > 0) * ((np.abs(mea - inv2) < dif_threshold)) * (
                      inv0 > 100) * (np.abs(mea - inv0) < dif_threshold)

    # data1 = mea[ind]
    # data3 = inv3[ind]
    # data1 = inv1[ind]
    # data2 = inv2[ind]
    num = np.sum(ind)

    '''
    yuanshi
    '''

    data2 = inv0[ind]
    data1 = mea[ind]
    dif = data2 - data1
    bias = np.mean(dif)
    rmse0 = np.sqrt(np.mean(dif * dif))
    rr = np.corrcoef(data1, data2)
    r2 = rr[1, 0] * rr[1, 0]
    print("origin: ", "num=", num, "rmse=", rmse0, "bias=", bias, "r2=", r2)

    '''
    dvts
    '''
    data2 = inv1[ind]
    data1 = mea[ind]
    dif = data2 - data1
    bias = np.mean(dif)
    rmse1 = np.sqrt(np.mean(dif * dif))
    rr = np.corrcoef(data1, data2)
    r2 = rr[1, 0] * rr[1, 0]
    print("dvts: ", "num=", num, "rmse=", rmse1, "bias=", bias, "r2=", r2)

    '''
    dvta
    '''
    data2 = inv2[ind]
    data1 = mea[ind]
    dif = data2 - data1
    bias = np.mean(dif)
    rmse2 = np.sqrt(np.mean(dif * dif))
    rr = np.corrcoef(data1, data2)
    r2 = rr[1, 0] * rr[1, 0]
    print("dvta: ", "num=", num, "rmse=", rmse2, "bias=", bias, "r2=", r2)

    #
    # sns.set_theme(style="white")
    # fig = plt.figure(figsize=(5.0,4.3))
    # xmin, xmax, ymin, ymax = 275, 320, 275, 320
    # # plt.hist2d(data1, data2, bins=50, norm=LogNorm(), cmap='jet')
    # df = pd.DataFrame({'SCOPE LST (K)': data1, 'Fitted LST (K)': data2})
    # g = sns.histplot(x='SCOPE LST (K)', y='Fitted LST (K)',data=df, bins=20,cbar=True,cmap="Spectral_r")
    # # g = sns.jointplot(x='SCOPE LST (K)', y='Fitted LST (K)', data=df, kind='hex',dropna=False,palette='red')
    # plt.plot([xmin, xmax], [ymin, ymax], '--')
    # g.set(xlabel='Measured LST (K)',ylabel='Normalized LST (K)')
    # # plt.xlabel("SCOPE LST")
    # # plt.ylabel("Fitted LST")
    # plt.xlim([xmin, xmax])
    # plt.ylim([ymin, ymax])
    # plt.text(300, 298-8, 'RMSE = %2.2f' % rmse)
    # plt.text(300, 295-8, '$R^2$ = %2.2f' % r2)
    # plt.text(300, 292-8, 'Bias = %2.2f' % bias)
    # plt.show()

    '''
    dvt
    '''
    data3 = inv3[ind]
    data1 = mea[ind]
    dif = data3 - data1
    bias = np.mean(dif)
    rmse3 = np.sqrt(np.mean(dif * dif))
    rr = np.corrcoef(data1, data3)
    r2 = rr[1, 0] * rr[1, 0]
    print("dvt: ", "num=", num, "rmse=", rmse3, "bias=", bias, "r2=", r2)

    sns.set_theme(style="white")
    fig = plt.figure(figsize=(5.0, 4.3))
    xmin, xmax, ymin, ymax = 275, 320, 275, 320
    # plt.hist2d(data1, data2, bins=50, norm=LogNorm(), cmap='jet')
    data11 = np.hstack([mea[ind], mea[ind]])
    data23 = np.hstack([inv3[ind], inv1[ind]])
    layer1 = np.repeat('Original', num)
    layer2 = np.repeat('Normalized', num)
    layer = np.hstack([layer1, layer2])
    data23 = data23 - data11
    df = pd.DataFrame({'LST Difference (K)': data23, 'type': layer})
    g = sns.histplot(x='LST Difference (K)', data=df, hue='type', stat="density")
    plt.text(-5, 0.1, '$RMSE_{O}$ = %2.2f K' % rmse0)
    plt.text(-5, 0.08, '$RMSE_{R}$ = %2.2f K' % rmse3)
    plt.show()





