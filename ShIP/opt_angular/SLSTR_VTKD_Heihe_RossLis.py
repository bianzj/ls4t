from util.myfun import *
from normalization_temporal.fitting_DTC import *
import time
from pathos.multiprocessing import Pool, cpu_count
import pathos.multiprocessing
from kdinversion import *
from kdmodel import *
from fitting_kernels import *




'''
1. for kernel coefficients using both S3A and S3B at a 1-month step
2. using a multi-process strategy for only validation points
光学核驱动拟合
'''




def kd_fitting(nir,red,vza,sza,raa,tcc,ref,kpixel = 0):
    [nb,nl,ns] = np.shape(vza)
    coeffs_ = np.zeros([6,nl-2*kpixel,ns-2*kpixel])

    for kl in range(kpixel,nl-kpixel):
        for ks in range(kpixel, ns - kpixel):
            nir_temp = nir[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            red_temp = red[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            tcc_temp = tcc[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            ind = (nir_temp > 0) * (tcc_temp < 0.25) * (red_temp >0)

            if np.sum(ind) < 7: continue

            vza_temp = vza[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            sza_temp = sza[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            raa_temp = raa[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]


            # lai_temp = np.average(lai)
            # coeffs = fitting_DTC_VinRL(obs_temp,pst_temp,vza_temp,sza_temp,raa_temp,rad_temp)
            # Powell 1669
            # TNC 1290 sparse many points
            # SLSQP 1100

            kvol = kernel_RossThick(vza_temp[ind],sza_temp[ind],raa_temp[ind])
            kgeo = kernel_LiSparse(vza_temp[ind],sza_temp[ind],raa_temp[ind])

            coeffs = fitting_linear3_ls(red_temp[ind],kvol,kgeo)

            coeffs_[0,kl-kpixel,ks-kpixel] = coeffs[0]*1.0
            coeffs_[1,kl-kpixel,ks-kpixel] = coeffs[1]*1.0
            coeffs_[2,kl-kpixel,ks-kpixel] = coeffs[2]*1.0

            coeffs = fitting_linear3_ls(nir_temp[ind],kvol,kgeo)

            coeffs_[3,kl-kpixel,ks-kpixel] = coeffs[0]*1.0
            coeffs_[4,kl-kpixel,ks-kpixel] = coeffs[1]*1.0
            coeffs_[5,kl-kpixel,ks-kpixel] = coeffs[2]*1.0


    return coeffs_



def do_multiple(param):
    return kd_fitting((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]), param[6])
    # return 1

if __name__ =='__main__':
    pathos.multiprocessing.freeze_support()
    # multiprocessing.freeze_support()

    indir_slstr = r'E:\SLSTR_Heihe\\'
    indir_lai = r'E:\lai_heihe1\\'
    outdir_coeff = r'E:\SLSTR_Heihe\coeff\\'
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
    nbb = 90

    for kmonth0 in range(1,13):
        thedoy = (kmonth0-1)*30+16

        reds = np.zeros([nbb, nll, nss])
        nirs = np.zeros([nbb, nll, nss])
        vzas = np.zeros([nbb, nll, nss])
        szas = np.zeros([nbb, nll, nss])
        raas = np.zeros([nbb, nll, nss])
        tccs = np.zeros([nbb, nll, nss])
        refs = np.zeros([nbb, nll, nss])
        kstep = 0
        for kday0 in range(1,32):
            kdoy = date2DOY(2019, kmonth0, kday0)
            # infile_lai = indir_lai + '2019_doy%03d.tif' % kdoy
            # [lai, ns, nl, nb, geog, proj] = read_image_gdal(infile_lai)


            '''S3A NADIR'''
            symbol = 's3a'
            dayNight ='day'
            nadirOblique = 'nadir'
            infile_nir = indir_slstr + symbol +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_nir_'+nadirOblique+'.tif'
            infile_red = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (kdoy) + dayNight + '_red_' + nadirOblique + '.tif'
            infile_cloud = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_cloud_'+nadirOblique+'.tif'
            infile_sza = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_sza_'+nadirOblique+'.tif'
            infile_vza = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vza_'+nadirOblique+'.tif'
            infile_saa = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_saa_'+nadirOblique+'.tif'
            infile_vaa = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vaa_'+nadirOblique+'.tif'
            infile_rad = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_rad'+'.tif'
            if ((os.path.exists(infile_nir) == 1)):
                [nir, ns, nl, temp, geog, proj] = read_image_gdal(infile_nir)
                [red, ns, nl, temp, geog, proj] = read_image_gdal(infile_red)
                [cloud, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud)
                [sza, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza)
                [vza, ns, nl, temp, geog, proj] = read_image_gdal(infile_vza)
                [saa, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa)
                [vaa, ns, nl, temp, geog, proj] = read_image_gdal(infile_vaa)
                [rad, ns, nl, temp, geog, proj] = read_image_gdal(infile_rad)
                ind = (nir > 0.15)*(nir < 0.5)*(red <0.35)*(red>0)
                if np.sum(ind) > nll*nss*0.1:
                    rad = resize_data_ls(rad,nl0,ns0)
                    raa = np.abs(vaa - saa)
                    vzas[kstep, :] = vza
                    nirs[kstep, :] = nir
                    reds[kstep, :] = red
                    tccs[kstep, :] = cloud
                    szas[kstep, :] = sza
                    raas[kstep, :] = raa
                    refs[kstep, :] = rad
                    kstep = kstep + 1


            '''S3A OBLIQ'''
            symbol = 's3a'
            dayNight ='day'
            nadirOblique = 'obliq'
            infile_nir = indir_slstr + symbol +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_nir_'+nadirOblique+'.tif'
            infile_red = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (kdoy) + dayNight + '_red_' + nadirOblique + '.tif'
            infile_cloud = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_cloud_'+nadirOblique+'.tif'
            infile_sza = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_sza_'+nadirOblique+'.tif'
            infile_vza = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vza_'+nadirOblique+'.tif'
            infile_saa = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_saa_'+nadirOblique+'.tif'
            infile_vaa = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vaa_'+nadirOblique+'.tif'
            infile_rad = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_rad'+'.tif'
            if ((os.path.exists(infile_nir) == 1)):
                [nir, ns, nl, temp, geog, proj] = read_image_gdal(infile_nir)
                [red, ns, nl, temp, geog, proj] = read_image_gdal(infile_red)
                [cloud, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud)
                [sza, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza)
                [vza, ns, nl, temp, geog, proj] = read_image_gdal(infile_vza)
                [saa, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa)
                [vaa, ns, nl, temp, geog, proj] = read_image_gdal(infile_vaa)
                [rad, ns, nl, temp, geog, proj] = read_image_gdal(infile_rad)
                ind = (nir > 0.15)*(nir < 0.5)*(red <0.35)*(red>0)
                if np.sum(ind) > nll*nss*0.1:
                    rad = resize_data_ls(rad,nl0,ns0)
                    raa = np.abs(vaa - saa)
                    vzas[kstep, :] = vza
                    nirs[kstep, :] = nir
                    reds[kstep, :] = red
                    tccs[kstep, :] = cloud
                    szas[kstep, :] = sza
                    raas[kstep, :] = raa
                    refs[kstep, :] = rad
                    kstep = kstep + 1

            '''S3B NADIR'''
            symbol = 's3b'
            dayNight = 'day'
            nadirOblique = 'nadir'
            infile_nir = indir_slstr + symbol +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_nir_'+nadirOblique+'.tif'
            infile_red = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (kdoy) + dayNight + '_red_' + nadirOblique + '.tif'
            infile_cloud = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_cloud_'+nadirOblique+'.tif'
            infile_sza = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_sza_'+nadirOblique+'.tif'
            infile_vza = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vza_'+nadirOblique+'.tif'
            infile_saa = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_saa_'+nadirOblique+'.tif'
            infile_vaa = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vaa_'+nadirOblique+'.tif'
            infile_rad = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_rad'+'.tif'
            if ((os.path.exists(infile_nir) == 1)):
                [nir, ns, nl, temp, geog, proj] = read_image_gdal(infile_nir)
                [red, ns, nl, temp, geog, proj] = read_image_gdal(infile_red)
                [cloud, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud)
                [sza, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza)
                [vza, ns, nl, temp, geog, proj] = read_image_gdal(infile_vza)
                [saa, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa)
                [vaa, ns, nl, temp, geog, proj] = read_image_gdal(infile_vaa)
                [rad, ns, nl, temp, geog, proj] = read_image_gdal(infile_rad)
                ind =(nir > 0.15)*(nir < 0.5)*(red <0.35)*(red>0)
                if np.sum(ind) > nll*nss*0.1:
                    rad = resize_data_ls(rad,nl0,ns0)
                    raa = np.abs(vaa - saa)
                    vzas[kstep, :] = vza
                    nirs[kstep, :] = nir
                    reds[kstep, :] = red
                    tccs[kstep, :] = cloud
                    szas[kstep, :] = sza
                    raas[kstep, :] = raa
                    refs[kstep, :] = rad
                    kstep = kstep + 1

            '''S3B OBLIQ'''
            symbol = 's3b'
            dayNight = 'day'
            nadirOblique = 'obliq'
            infile_nir = indir_slstr + symbol +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_nir_'+nadirOblique+'.tif'
            infile_red = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (kdoy) + dayNight + '_red_' + nadirOblique + '.tif'
            infile_cloud = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_cloud_'+nadirOblique+'.tif'
            infile_sza = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_sza_'+nadirOblique+'.tif'
            infile_vza = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vza_'+nadirOblique+'.tif'
            infile_saa = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_saa_'+nadirOblique+'.tif'
            infile_vaa = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vaa_'+nadirOblique+'.tif'
            infile_rad = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_rad'+'.tif'
            if ((os.path.exists(infile_nir) == 1)):
                [nir, ns, nl, temp, geog, proj] = read_image_gdal(infile_nir)
                [red, ns, nl, temp, geog, proj] = read_image_gdal(infile_red)
                [cloud, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud)
                [sza, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza)
                [vza, ns, nl, temp, geog, proj] = read_image_gdal(infile_vza)
                [saa, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa)
                [vaa, ns, nl, temp, geog, proj] = read_image_gdal(infile_vaa)
                [rad, ns, nl, temp, geog, proj] = read_image_gdal(infile_rad)
                ind = (nir > 0.15)*(nir < 0.5)*(red <0.35)*(red>0)
                if np.sum(ind) > nll*nss*0.1:
                    rad = resize_data_ls(rad,nl0,ns0)
                    raa = np.abs(vaa - saa)
                    vzas[kstep, :] = vza
                    nirs[kstep, :] = nir
                    reds[kstep, :] = red
                    tccs[kstep, :] = cloud
                    szas[kstep, :] = sza
                    raas[kstep, :] = raa
                    refs[kstep, :] = rad
                    kstep = kstep + 1

        ####multiple
        param = []
        for kp in range(npoint):
            kl = imagex_[kp]
            ks = imagey_[kp]

            vza_temp = vzas[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            nir_temp = nirs[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            red_temp = reds[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            sza_temp = szas[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            raa_temp = raas[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            ref_temp = refs[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
            tcc_temp = tccs[:kstep+1, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]

            param.append([nir_temp,
                          red_temp,
                          vza_temp,
                          sza_temp,
                          raa_temp,
                          tcc_temp,
                          ref_temp])

        result = do_multiple(param[0])
        print(kmonth0)

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
        # kvol1 = np.zeros([nll,nss])
        # kgeo1 = np.zeros([nll, nss])
        # kiso1 = np.zeros([nll, nss])
        # kvol2 = np.zeros([nll, nss])
        # kgeo2 = np.zeros([nll, nss])
        # kiso2 = np.zeros([nll, nss])
        #
        # results = np.asarray(results)
        #
        # for kp in range(npoint):
        #     kl = imagex_[kp]
        #     ks = imagey_[kp]
        #     kvol1[(kl - kinv + kpixel):(kl + kinv + 1 - kpixel),
        #     (ks - kinv + kpixel):(ks + kinv + 1 - kpixel)] = results[kp, 0, :]
        #     kgeo1[(kl - kinv + kpixel):(kl + kinv + 1 - kpixel),
        #     (ks - kinv + kpixel):(ks + kinv + 1 - kpixel)] = results[kp, 1, :]
        #     kiso1[(kl - kinv + kpixel):(kl + kinv + 1 - kpixel),
        #     (ks - kinv + kpixel):(ks + kinv + 1 - kpixel)] = results[kp, 2, :]
        #     kvol2[(kl - kinv + kpixel):(kl + kinv + 1 - kpixel),
        #     (ks - kinv + kpixel):(ks + kinv + 1 - kpixel)] = results[kp, 3, :]
        #     kgeo2[(kl - kinv + kpixel):(kl + kinv + 1 - kpixel),
        #     (ks - kinv + kpixel):(ks + kinv + 1 - kpixel)] = results[kp, 4, :]
        #     kiso2[(kl - kinv + kpixel):(kl + kinv + 1 - kpixel),
        #     (ks - kinv + kpixel):(ks + kinv + 1 - kpixel)] = results[kp, 5, :]
        #
        #
        #
        # outfile = outdir_coeff + '2019%02d_' % (kmonth0) +kd+ '_kvol1.tif'
        # write_image_gdal(kvol1, nss, nll, 1, geog, proj, outfile)
        # outfile = outdir_coeff + '2019%02d_' % (kmonth0) +kd+ '_kgeo1.tif'
        # write_image_gdal(kgeo1, nss, nll, 1, geog, proj, outfile)
        # outfile = outdir_coeff + '2019%02d_' % (kmonth0) +kd+ '_kiso1.tif'
        # write_image_gdal(kiso1, nss, nll, 1, geog, proj, outfile)
        # outfile = outdir_coeff + '2019%02d_' % (kmonth0) +kd+ '_kvol2.tif'
        # write_image_gdal(kvol2, nss, nll, 1, geog, proj, outfile)
        # outfile = outdir_coeff + '2019%02d_' % (kmonth0 ) +kd+ '_kgeo2.tif'
        # write_image_gdal(kgeo2, nss, nll, 1, geog, proj, outfile)
        # outfile = outdir_coeff + '2019%02d_' % (kmonth0) +kd+ '_kiso2.tif'
        # write_image_gdal(kiso2, nss, nll, 1, geog, proj, outfile)
        # #


