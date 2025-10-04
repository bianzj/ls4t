from util.myfun import *
from normalization_temporal.fitting_DTC import *
import time
from pathos.multiprocessing import Pool, cpu_count
import pathos.multiprocessing
from kdinversion import *
from kdmodel import *
from fitting_kernels import *




'''
光学系数与红外变化构建线性关系
1. VNIR and TIR combination with an empirical assumption
2. For link coefficients
'''







def kd_fitting(lst,tvol1,tvol2,tgeo1,tgeo2,tiso1,tiso2,ref,kpixel = 0):
    [nb,nl,ns] = np.shape(lst)
    coeffs_ = np.zeros([6,nl-2*kpixel,ns-2*kpixel])

    for kl in range(kpixel,nl-kpixel):
        for ks in range(kpixel, ns - kpixel):
            lst_temp = lst[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            tiso1_temp = tiso1[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            tiso2_temp = tiso2[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            ind = (lst_temp > -10) * (tiso1_temp != 0) * (tiso2_temp != 0)*(lst_temp<10)
            if np.sum(ind) < 10: continue

            tgeo1_temp = tgeo1[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            tgeo2_temp = tgeo2[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            tvol1_temp = tvol1[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            tvol2_temp = tvol2[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            ref_temp = ref[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]



            # lai_temp = np.average(lai)
            # coeffs = fitting_DTC_VinRL(obs_temp,pst_temp,vza_temp,sza_temp,raa_temp,rad_temp)
            # Powell 1669
            # TNC 1290 sparse many points
            # SLSQP 1100

            coeffs = fitting_linear7_ridge(lst_temp[ind],tvol1_temp[ind],
                                        tvol2_temp[ind],tgeo1_temp[ind],
                                        tgeo2_temp[ind],tiso1_temp[ind],
                                        tiso2_temp[ind],ref_temp[ind])

            lstsim = coeffs[0] * tvol1_temp[ind]  + coeffs[1] * tvol2_temp[ind]  + coeffs[2] * tgeo1_temp[ind]  +\
                     coeffs[3] * tgeo2_temp[ind] + coeffs[4] * tiso1_temp[ind]  + coeffs[5] * tiso2_temp[ind] + coeffs[6]* ref_temp[ind]

            dif = lstsim - lst_temp[ind]
            bias = np.average(dif)
            rmse = np.sqrt(np.average(dif * dif))
            print(kmonth0, np.sum(ind),np.std(lst_temp[ind]), bias, rmse)

            coeffs_[0,kl-kpixel,ks-kpixel] = coeffs[0]
            coeffs_[1,kl-kpixel,ks-kpixel] = coeffs[1]
            coeffs_[2,kl-kpixel,ks-kpixel] = coeffs[2]
            coeffs_[3,kl-kpixel,ks-kpixel] = coeffs[3]
            coeffs_[4,kl-kpixel,ks-kpixel] = coeffs[4]
            coeffs_[5,kl-kpixel,ks-kpixel] = coeffs[5]


    return coeffs_



def do_multiple(param):
    return kd_fitting((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]), param[6],param[7])
    # return 1

if __name__ =='__main__':
    pathos.multiprocessing.freeze_support()
    # multiprocessing.freeze_support()

    indir_slstr = r'E:\SLSTR_Heihe\\'
    indir_lai = r'E:\lai_heihe1\\'
    indir_vnircoeff = r'E:\SLSTR_Heihe\coeff\\'
    outdir_linkcoeff = r'E:\SLSTR_Heihe\coeff\\'
    kd = 'rosslis'

    days_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    kpixel = 0  # the area for inversion at each
    kinv = 2  # the area for inversion

    '''
    Extract LST results of 9 sites from AHI data in Heihe area
    '''
    infile_loc = r'E:\field\heihe_site.txt'
    mydata = read_txt_str(infile_loc, ',')
    mydata = np.asarray(mydata)
    lon = np.asarray(mydata[:, 1], dtype=np.float16)
    lat = np.asarray(mydata[:, 2], dtype=np.float16)
    infile_ref = r'E:\type\type_heihe_1000.tif'
    dataset = gdal.Open(infile_ref)
    im_width = dataset.RasterXSize * 1
    im_height = dataset.RasterYSize * 1
    im_bands = dataset.RasterCount * 1
    data = dataset.ReadAsArray(0, 0, im_width, im_height)
    im_geotrans = dataset.GetGeoTransform()
    im_proj = dataset.GetProjection()
    # 返回经纬度对应的投影坐标
    temp1, temp2 = lonlat2geo(dataset, lat, lon)
    # 将投影坐标或地理坐标转化为图像坐标，行列号
    imagex_, imagey_ = geo2imagexy(dataset, temp1, temp2)
    imagex_ = np.asarray(imagex_, dtype=np.int16)
    # [270 218 285 226 229 219  54  54  47]
    imagey_ = np.asarray(imagey_, dtype=np.int16)
    # [126  66 155 128 125 132 181 181 176]
    npoint = np.size(imagex_)

    nss = im_width
    nll = im_height
    nbb = 45

    for kmonth0 in range(1,13):
        thedoy = (kmonth0-1)*30+16

        lsts = np.zeros([nbb, nll, nss])
        refs = np.zeros([nbb,nll,nss])
        tvol1s = np.zeros([nbb, nll, nss])
        tgeo1s = np.zeros([nbb, nll, nss])
        tiso1s = np.zeros([nbb, nll, nss])
        tvol2s = np.zeros([nbb, nll, nss])
        tgeo2s = np.zeros([nbb, nll, nss])
        tiso2s = np.zeros([nbb, nll, nss])
        kstep = 0


        infile_fvol1 =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_kvol1.tif'
        infile_fgeo1 =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_kgeo1.tif'
        infile_fiso1 =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_kiso1.tif'
        infile_fvol2 =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_kvol2.tif'
        infile_fgeo2 =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_kgeo2.tif'
        infile_fiso2 =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_kiso2.tif'
        [fvol1, ns, nl, temp, geog, proj] = read_image_gdal(infile_fvol1)
        [fgeo1, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_fgeo1)
        [fiso1, ns, nl, temp, geog, proj] = read_image_gdal(infile_fiso1)
        [fvol2, ns, nl, temp, geog, proj] = read_image_gdal(infile_fvol2)
        [fgeo2, ns, nl, temp, geog, proj] = read_image_gdal(infile_fgeo2)
        [fiso2, ns, nl, temp, geog, proj] = read_image_gdal(infile_fiso2)

        for kday0 in range(1,32):
            kdoy = date2DOY(2019, kmonth0, kday0)
            # infile_lai = indir_lai + '2019_doy%03d.tif' % kdoy
            # [lai, ns, nl, nb, geog, proj] = read_image_gdal(infile_lai)


            '''S3A NADIR'''
            symbol = 's3a'
            dayNight ='day'
            nadirOblique = 'nadir'
            infile_lst_nadir = indir_slstr + symbol +'\\lst\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_lst_'+nadirOblique+'.tif'
            infile_cloud_nadir = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_cloud_'+nadirOblique+'.tif'
            infile_sza_nadir = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_sza_'+nadirOblique+'.tif'
            infile_vza_nadir = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vza_'+nadirOblique+'.tif'
            infile_saa_nadir = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_saa_'+nadirOblique+'.tif'
            infile_vaa_nadir = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vaa_'+nadirOblique+'.tif'


            nadirOblique = 'obliq'
            infile_lst_obliq = indir_slstr + symbol +'\\lst\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_lst_'+nadirOblique+'.tif'
            infile_cloud_obliq = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_cloud_'+nadirOblique+'.tif'
            infile_sza_obliq = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_sza_'+nadirOblique+'.tif'
            infile_vza_obliq = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vza_'+nadirOblique+'.tif'
            infile_saa_obliq = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_saa_'+nadirOblique+'.tif'
            infile_vaa_obliq = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vaa_'+nadirOblique+'.tif'

            infile_rad = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_ta'+'.tif'

            if ((os.path.exists(infile_lst_nadir) == 1) & (os.path.exists(infile_lst_obliq) == 1)):
                [lst_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst_nadir)
                            
                [cloud_nadir, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud_nadir)
                [sza_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza_nadir)
                [vza_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_vza_nadir)
                [saa_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa_nadir)
                [vaa_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_vaa_nadir)

                [lst_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst_obliq)
                [cloud_obliq, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud_obliq)
                [sza_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza_obliq)
                [vza_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_vza_obliq)
                [saa_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa_obliq)
                [vaa_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_vaa_obliq)
                [rad, ns, nl, temp, geog, proj] = read_image_gdal(infile_rad)


                ind = (cloud_nadir==0) *(cloud_obliq == 0) *(lst_nadir > 250) *(lst_obliq >  250)
                if np.sum(ind) > nll*nss*0.1:

                    tvol1 = np.zeros([nll,nss])
                    tvol2 = np.zeros([nll,nss])
                    tgeo1 = np.zeros([nll,nss])
                    tgeo2 = np.zeros([nll,nss])
                    tiso1 = np.zeros([nll,nss])
                    tiso2 = np.zeros([nll,nss])

                    rad = resize_data_ls(rad,nl0,ns0)
                    raa_nadir = np.abs(vaa_nadir - saa_nadir)
                    raa_obliq = np.abs(vaa_obliq - saa_obliq)

                    indd = (fiso1!=0) | (fiso2 !=0) | (fgeo1 !=0) | (fgeo2 != 0) | (fvol1 != 0) | (fvol2 !=0)
                    tvol1[indd] = fvol1[indd]*kernel_RossThick(vza_nadir[indd],sza_nadir[indd],raa_nadir[indd])
                    tvol2[indd] = fvol2[indd]*kernel_RossThick(vza_obliq[indd],sza_obliq[indd],raa_obliq[indd])
                    tgeo1[indd] = fgeo1[indd]*kernel_LiSparse(vza_nadir[indd],sza_nadir[indd],raa_nadir[indd])
                    tgeo2[indd] = fgeo2[indd]*kernel_LiSparse(vza_obliq[indd],sza_obliq[indd],raa_obliq[indd])
                    tiso1[indd] = fiso1[indd]*1.0
                    tiso2[indd] = fiso2[indd]*1.0
                    
                    
                    
                    tvol1s[kstep, :] = tvol1*1.0
                    tvol2s[kstep, :] = tvol2*1.0
                    tgeo1s[kstep, :] = tgeo1*1.0
                    tgeo2s[kstep, :] = tgeo2*1.0
                    tiso1s[kstep, :] = tiso1*1.0
                    tiso2s[kstep, :] = tiso2*1.0
                    refs[kstep, :] = rad*1.0
                    lsts[kstep,:] = lst_obliq - lst_nadir
                    kstep = kstep + 1



            '''S3B NADIR'''
            symbol = 's3b'
            dayNight = 'day'
            nadirOblique = 'nadir'
            infile_lst_nadir = indir_slstr + symbol + '\\lst\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_lst_' + nadirOblique + '.tif'
            infile_cloud_nadir = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_cloud_' + nadirOblique + '.tif'
            infile_sza_nadir = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_sza_' + nadirOblique + '.tif'
            infile_vza_nadir = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_vza_' + nadirOblique + '.tif'
            infile_saa_nadir = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_saa_' + nadirOblique + '.tif'
            infile_vaa_nadir = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_vaa_' + nadirOblique + '.tif'

            nadirOblique = 'obliq'
            infile_lst_obliq = indir_slstr + symbol + '\\lst\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_lst_' + nadirOblique + '.tif'
            infile_cloud_obliq = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_cloud_' + nadirOblique + '.tif'
            infile_sza_obliq = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_sza_' + nadirOblique + '.tif'
            infile_vza_obliq = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_vza_' + nadirOblique + '.tif'
            infile_saa_obliq = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_saa_' + nadirOblique + '.tif'
            infile_vaa_obliq = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_vaa_' + nadirOblique + '.tif'

            infile_rad = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (kdoy) + dayNight + '_ta' + '.tif'

            if ((os.path.exists(infile_lst_nadir) == 1) & (os.path.exists(infile_lst_obliq) == 1)):
                [lst_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst_nadir)

                [cloud_nadir, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud_nadir)
                [sza_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza_nadir)
                [vza_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_vza_nadir)
                [saa_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa_nadir)
                [vaa_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_vaa_nadir)

                [lst_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst_obliq)
                [cloud_obliq, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud_obliq)
                [sza_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza_obliq)
                [vza_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_vza_obliq)
                [saa_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa_obliq)
                [vaa_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_vaa_obliq)
                [rad, ns, nl, temp, geog, proj] = read_image_gdal(infile_rad)

                ind = (cloud_nadir == 0) * (cloud_obliq == 0) * (lst_nadir > 250) * (lst_obliq > 250)
                if np.sum(ind) > nll * nss * 0.1:
                    tvol1 = np.zeros([nll, nss])
                    tvol2 = np.zeros([nll, nss])
                    tgeo1 = np.zeros([nll, nss])
                    tgeo2 = np.zeros([nll, nss])
                    tiso1 = np.zeros([nll, nss])
                    tiso2 = np.zeros([nll, nss])

                    rad = resize_data_ls(rad, nl0, ns0)
                    raa_nadir = np.abs(vaa_nadir - saa_nadir)
                    raa_obliq = np.abs(vaa_obliq - saa_obliq)

                    indd = (fiso1 != 0) | (fiso2 != 0) | (fgeo1 != 0) | (fgeo2 != 0) | (fvol1 != 0) | (fvol2 != 0)
                    tvol1[indd] = fvol1[indd] * kernel_RossThick(vza_nadir[indd], sza_nadir[indd], raa_nadir[indd])
                    tvol2[indd] = fvol2[indd] * kernel_RossThick(vza_obliq[indd], sza_obliq[indd], raa_obliq[indd])
                    tgeo1[indd] = fgeo1[indd] * kernel_LiSparse(vza_nadir[indd], sza_nadir[indd], raa_nadir[indd])
                    tgeo2[indd] = fgeo2[indd] * kernel_LiSparse(vza_obliq[indd], sza_obliq[indd], raa_obliq[indd])
                    tiso1[indd] = fiso1[indd]*1.0
                    tiso2[indd] = fiso2[indd]*1.0

                    tvol1s[kstep, :] = tvol1*1.0
                    tvol2s[kstep, :] = tvol2*1.0
                    tgeo1s[kstep, :] = tgeo1*1.0
                    tgeo2s[kstep, :] = tgeo2*1.0
                    tiso1s[kstep, :] = tiso1*1.0
                    tiso2s[kstep, :] = tiso2*1.0
                    refs[kstep, :] = rad*1.0
                    lsts[kstep, :] = lst_obliq - lst_nadir
                    kstep = kstep + 1

        ####multiple
        param = []
        for kp in range(npoint):
            kl = imagex_[kp]
            ks = imagey_[kp]

            tvol1_temp = tvol1s[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            tvol2_temp = tvol2s[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            tgeo1_temp = tgeo1s[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            tgeo2_temp = tgeo2s[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            tiso1_temp = tiso1s[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            tiso2_temp = tiso2s[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            ref_temp = refs[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            lst_temp = lsts[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]

            param.append([lst_temp,
                          tvol1_temp,
                          tvol2_temp,
                          tgeo1_temp,
                          tgeo2_temp,
                          tiso1_temp,
                          tiso2_temp,
                          ref_temp])

        result = do_multiple(param[0])
        print(kmonth0)
        #
        # a = 0
        # start = time.time()
        # tasks = []
        # pool = Pool(min(12, cpu_count()))
        # for p in param:
        #     tasks.append(pool.apply_async(do_multiple, (p,)))
        # pool.close()
        # pool.join()
        # results = [task.get() for task in tasks]
        # end = time.time()
        # print('time cost: ', end - start, 's')
        #
        #
        # a = np.zeros([nll, nss])
        # b = np.zeros([nll, nss])
        # c = np.zeros([nll, nss])
        # d = np.zeros([nll, nss])
        # e = np.zeros([nll, nss])
        # f = np.zeros([nll, nss])
        #
        # results = np.asarray(results)
        #
        # for kp in range(npoint):
        #     kl = imagex_[kp]
        #     ks = imagey_[kp]
        #     a[(kl - kinv + kpixel):(kl + kinv + 1 - kpixel),
        #     (ks - kinv + kpixel):(ks + kinv + 1 - kpixel)] = results[kp, 0, :]
        #     b[(kl - kinv + kpixel):(kl + kinv + 1 - kpixel),
        #     (ks - kinv + kpixel):(ks + kinv + 1 - kpixel)] = results[kp, 1, :]
        #     c[(kl - kinv + kpixel):(kl + kinv + 1 - kpixel),
        #     (ks - kinv + kpixel):(ks + kinv + 1 - kpixel)] = results[kp, 2, :]
        #     d[(kl - kinv + kpixel):(kl + kinv + 1 - kpixel),
        #     (ks - kinv + kpixel):(ks + kinv + 1 - kpixel)] = results[kp, 3, :]
        #     e[(kl - kinv + kpixel):(kl + kinv + 1 - kpixel),
        #     (ks - kinv + kpixel):(ks + kinv + 1 - kpixel)] = results[kp, 4, :]
        #     f[(kl - kinv + kpixel):(kl + kinv + 1 - kpixel),
        #     (ks - kinv + kpixel):(ks + kinv + 1 - kpixel)] = results[kp, 5, :]
        #
        #
        # if np.sum(a!=0)<1:print('error!!!')
        #
        # outfile = outdir_linkcoeff + '2019%02d_' % (kmonth0) +kd+ '_a.tif'
        # write_image_gdal(a, nss, nll, 1, geog, proj, outfile)
        # outfile = outdir_linkcoeff + '2019%02d_' % (kmonth0) +kd+ '_c.tif'
        # write_image_gdal(c, nss, nll, 1, geog, proj, outfile)
        # outfile = outdir_linkcoeff + '2019%02d_' % (kmonth0) +kd+ '_e.tif'
        # write_image_gdal(e, nss, nll, 1, geog, proj, outfile)
        # outfile = outdir_linkcoeff + '2019%02d_' % (kmonth0) +kd+ '_b.tif'
        # write_image_gdal(b, nss, nll, 1, geog, proj, outfile)
        # outfile = outdir_linkcoeff + '2019%02d_' % (kmonth0 ) +kd+ '_d.tif'
        # write_image_gdal(d, nss, nll, 1, geog, proj, outfile)
        # outfile = outdir_linkcoeff + '2019%02d_' % (kmonth0) +kd+ '_f.tif'
        # write_image_gdal(f, nss, nll, 1, geog, proj, outfile)
        #


