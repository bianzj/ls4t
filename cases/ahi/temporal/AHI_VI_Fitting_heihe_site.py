from util.myfun import *
from normalization_temporal.fitting_DTC import *
import time
from multiprocessing import Pool, cpu_count
import multiprocessing

### 时间连续数据拟合DTC的系数
### 考虑了角度效应的影响
### 此时角度效应的系数是已知的
### 这里认为是能够有效的抵挡角度效应影响
### 以每个点进行了多线程

def coeffdtc_invert(vi,bf,vza,sza,raa,tcc,kpixel = 0):
    [nb,nl,ns] = np.shape(vza)
    dtcabk = np.zeros([6,nl-2*kpixel,ns-2*kpixel])

    for kl in range(kpixel,nl-kpixel):
        for ks in range(kpixel, ns - kpixel):
            vi_temp = vi[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            bf_temp = bf[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            tcc_temp = tcc[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            ind = (vi_temp != 0) * (tcc_temp < 0.1) *(bf_temp !=0)

            if np.sum(ind) < 5: continue

            vza_temp = vza[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            sza_temp = sza[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]
            raa_temp = raa[:, (kl - kpixel):(kl + kpixel + 1), (ks - kpixel):(ks + kpixel + 1)]

            kross = kernel_RossThick(vza_temp[ind],sza_temp[ind],raa_temp[ind])
            klis = kernel_LiSparse(vza_temp[ind],sza_temp[ind],raa_temp[ind])

            coeffs = fitting_kernels_ridge(vi_temp[ind],kross,klis)
            dtcabk[0,kl-kpixel,ks-kpixel] = coeffs[0]
            dtcabk[1,kl-kpixel,ks-kpixel] = coeffs[1]
            dtcabk[2,kl-kpixel,ks-kpixel] = coeffs[2]
            coeffs = fitting_kernels_ridge(bf_temp[ind],kross,klis)
            dtcabk[3,kl-kpixel,ks-kpixel] = coeffs[0]
            dtcabk[4,kl-kpixel,ks-kpixel] = coeffs[1]
            dtcabk[5,kl-kpixel,ks-kpixel] = coeffs[2]

    return dtcabk



def doMultiple12(param):
    return coeffdtc_invert((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]))


if __name__ =='__main__':
    multiprocessing.freeze_support()

    kpixel = 0
    kinv = 2
    indir_tif0 = r'E:\AHI_heihe\tif\\'
    indir_lst0 = r'E:\AHI_heihe\lst\\'
    outdir_coeffs0 = r'E:\ShIP_DVT\Coeff_VNIR_heihe\\'
    symbol = 'AHI'

    indir_map = r'E:\map\\'
    infile_vza = infile8 = indir_map + 'ahi_vza_heihe.tif'
    [vza,ns,nl,nb,geog,proj] = read_image_gdal(infile_vza)
    infile_vaa = infile8 = indir_map + 'ahi_vaa_heihe.tif'
    [vaa,ns,nl,nb,geog,proj] = read_image_gdal(infile_vaa)

    obs = np.asarray([])
    lst_obliq = np.asarray([])
    lst_nadir_normalized = np.asarray([])
    lst_obliq_normalized = np.asarray([])
    days_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    '''
    Extract LST results of 9 sites from AHI data in Heihe area
    '''
    infile_loc = r'E:\field\heihe_site.txt'
    mydata = read_txt_str(infile_loc, ',')
    mydata = np.asarray(mydata)
    lon = np.asarray(mydata[:, 1], dtype=np.float16)
    lat = np.asarray(mydata[:, 2], dtype=np.float16)
    infile_ref = r'E:\type\type_heihe_2000.tif'
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


    nss = ns
    nll = nl


    # for kmonth0 in range(1,13):
    for kmonth0 in range(8,9):
        thedoy = (kmonth0-1)*30+16
        # kdoy = thedoy*1.0

        for kday0 in range(1,32):
        # for kday0 in range(10, 11):
            nb = 40

            vis = np.zeros([nb, nll, nss])
            bfs = np.zeros([nb, nll, nss])
            vzas = np.zeros([nb, nll, nss])
            szas = np.zeros([nb, nll, nss])
            psis = np.zeros([nb, nll, nss])
            tccs = np.zeros([nb , nll, nss])


            kdoy0 = date2DOY(2019, kmonth0, kday0)

            kstep = 0
            for khour0 in range(10-8,15-8):

                indir_lst = indir_lst0 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'
                indir_tif = indir_tif0 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'
                outdir_coeffs = outdir_coeffs0 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'

                kdoy = kdoy0 + 0
                khour = khour0
                if khour0 < 0:
                    kdoy = kdoy - 1
                    khour = khour0 + 24
                    if kday0 == 1:
                        indir_lst = indir_lst0 + r'\%02d' % (kmonth0-1) + r'\%02d' % days_of_month[kmonth0-2] + '\\'
                        indir_tif = indir_tif0 + r'\%02d' % (kmonth0-1) + r'\%02d' % days_of_month[kmonth0-2] + '\\'
                    else:
                        indir_lst = indir_lst0 + r'\%02d' % (kmonth0) + r'\%02d' % (kday0-1) + '\\'
                        indir_tif = indir_tif0 + r'\%02d' % (kmonth0) + r'\%02d' % (kday0-1) + '\\'

                for kmin in range(0,4,3):
                    infile_red = indir_tif + symbol + '_2019%03d' % (kdoy) + '_%02d' % khour + '%1d0' % kmin + '_red.tif'
                    infile_nir = indir_tif + symbol + '_2019%03d' % (kdoy) + '_%02d' % khour + '%1d0' % kmin + '_nir.tif'
                    infile_cloud = indir_tif + symbol + '_2019%03d' % (kdoy ) + '_%02d' % khour + '%1d0' % kmin + '_tcc.tif'
                    infile_sza = indir_tif + symbol + '_2019%03d' % (kdoy) + '_%02d' % khour + '%1d0' % kmin + '_sza.tif'
                    infile_saa = indir_tif + symbol + '_2019%03d' % (kdoy) + '_%02d' % khour + '%1d0' % kmin + '_saa.tif'
                    print(infile_red)
                    if ((os.path.exists(infile_red) == 1) & (os.path.exists(infile_sza) == 1)):
                        [red, ns, nl, temp, geog, proj] = read_image_gdal(infile_red)
                        [nir, ns, nl, temp, geog, proj] = read_image_gdal(infile_nir)
                        [cloud, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud)
                        cloud = resize_data_near(cloud,nl,ns)
                        [saa, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa)
                        [sza, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza)

                        ind = (red>0.001) *(nir > 0.001)*(sza > 0)
                        if np.sum(ind) > nll*nss*0.1:
                            vi = np.zeros([nll,nss])
                            bf = np.zeros([nll,nss])
                            vi[ind] = (nir[ind]-red[ind])/(nir[ind]+red[ind])
                            bf[ind] = (nir[ind] + red[ind])/2.0

                            psi = np.abs(vaa - saa)
                            vzas[kstep, :] = vza
                            vis[kstep, :] = vi
                            bfs[kstep,:] = bf
                            tccs[kstep, :] = cloud
                            szas[kstep, :] = sza
                            psis[kstep, :] = psi
                            kstep = kstep + 1


            ####multiple
            param = []
            if kstep < 5:continue
            for kp in range(npoint):

                kl = imagex_[kp]
                ks = imagey_[kp]

                vza_temp = vzas[:, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
                vi_temp = vis[:, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
                bf_temp = bfs[:,(kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
                sza_temp = szas[:, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
                psi_temp = psis[:, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]
                tcc_temp = tccs[:, (kl - kinv):(kl + kinv + 1), (ks - kinv):(ks + kinv + 1)]

                param.append([vi_temp,
                              bf_temp,
                              vza_temp,
                              sza_temp,
                              psi_temp,
                              tcc_temp ])

            # result = doMultiple12(param[0])
            a = 0
            start = time.time()
            tasks = []
            pool = Pool(min(12, cpu_count()))
            for p in param:
                tasks.append(pool.apply_async(doMultiple12, (p,)))
            pool.close()
            pool.join()
            results = [task.get() for task in tasks]
            end = time.time()
            print('time cost: ', end - start, 's')


            via = np.zeros([nll,nss])
            vib = np.zeros([nll, nss])
            vic = np.zeros([nll, nss])
            bfa = np.zeros([nll, nss])
            bfb = np.zeros([nll, nss])
            bfc = np.zeros([nll, nss])



            results = np.asarray(results)


            for kp in range(npoint):
                kl = imagex_[kp]
                ks = imagey_[kp]
                via[(kl - kinv+kpixel):(kl + kinv + 1-kpixel), (ks - kinv+kpixel):(ks + kinv + 1-kpixel)] = results[kp, 0, :]
                vib[(kl - kinv+kpixel):(kl + kinv + 1-kpixel), (ks - kinv+kpixel):(ks + kinv + 1-kpixel)] = results[kp, 1, :]
                vic[(kl - kinv+kpixel):(kl + kinv + 1-kpixel), (ks - kinv+kpixel):(ks + kinv + 1-kpixel)] = results[kp, 2, :]
                bfa[(kl - kinv+kpixel):(kl + kinv + 1-kpixel), (ks - kinv+kpixel):(ks + kinv + 1-kpixel)] = results[kp, 3, :]
                bfb[(kl - kinv+kpixel):(kl + kinv + 1-kpixel), (ks - kinv+kpixel):(ks + kinv + 1-kpixel)] = results[kp, 4, :]
                bfc[(kl - kinv+kpixel):(kl + kinv + 1-kpixel), (ks - kinv+kpixel):(ks + kinv + 1-kpixel)] = results[kp, 5, :]


            outdir = outdir_coeffs


            # ta[ta > 100] = 0
            # ta[ta < -100] = 0
            # to[to > 100] = 0
            # to[to < -100] = 0
            # tm[tm < -100] = 0
            # ts[ts > 100] = 0
            # tm[tm > 100] = 0
            # ts[ts < -100] = 0
            # a[a > 100] = 0
            # a[a < -100] = 0
            # b[b > 100] = 0
            # b[b < -100] = 0
            # k[k < -100] = 0
            # k[k > 100] = 0
            outfile = outdir + '2019%03d' % (kdoy) + '_via.tif'
            write_image_gdal(via, nss, nll, 1, geog, proj, outfile)
            outfile = outdir + '2019%03d' % (kdoy) + '_vib.tif'
            write_image_gdal(vib, nss, nll, 1, geog, proj, outfile)
            outfile = outdir + '2019%03d' % (kdoy) + '_vic.tif'
            write_image_gdal(vic, nss, nll, 1, geog, proj, outfile)
            outfile = outdir + '2019%03d' % (kdoy) + '_bfa.tif'
            write_image_gdal(bfa, nss, nll, 1, geog, proj, outfile)
            outfile = outdir + '2019%03d' % (kdoy ) + '_bfb.tif'
            write_image_gdal(bfb, nss, nll, 1, geog, proj, outfile)
            outfile = outdir + '2019%03d' % (kdoy) + '_bfc.tif'
            write_image_gdal(bfc, nss, nll, 1, geog, proj, outfile)
            # outfile = outdir + '2019%03d' % (kdoy) + '_tm.tif'
            # write_image_gdal(tm, nss, nll, 1, geog, proj, outfile)
            # outfile = outdir + '2019%03d' % (kdoy) + '_ts.tif'
            # write_image_gdal(ts, nss, nll, 1, geog, proj, outfile)