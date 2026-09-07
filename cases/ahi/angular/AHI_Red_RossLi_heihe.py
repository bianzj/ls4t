from normalization_temporal.fitting_DTC import *
import time
from util.myfun import *
from multiprocessing import Pool, cpu_count
import multiprocessing

def coeffdtc_invert(obs,pst,vza,sza,raa,tcc,rad):
    [nb, nl, ns] = np.shape(vza)
    abck = np.zeros([3, ns])


    ind = raa > 180
    raa[ind] = 360 - raa[ind]

    thetas = np.deg2rad(sza)
    thetaa = np.deg2rad(raa)
    thetav = np.deg2rad(abs(vza))


    fhs = np.zeros([nb, nl,ns])
    Kross = np.zeros([nb,nl, ns])
    kli = np.zeros([nb,nl,ns])


    ind = (obs > 0) *(sza < 65)
    az = np.cos(thetas[ind]) * np.cos(thetav[ind]) + \
         np.sin(thetas[ind]) * np.sin(thetav[ind]) * np.cos(thetaa[ind])
    angle = np.arccos(az)
    fhs[ind] = np.sqrt((np.power(np.tan(thetas[ind]), 2) + np.power(np.tan(thetav[ind]), 2) - 2 * np.tan(
        thetas[ind]) * np.tan(thetav[ind]) *
                          np.cos(thetaa[ind])))
    Kross[ind] = ((np.pi / 2.0 - angle) * az + np.sin(angle)) / (
                np.cos(thetav[ind]) + np.cos(thetas[ind])) - np.pi / 4.0
    # kli = kernel_LiSparse(vza,sza,raa)
    kli[ind] = kernel_LiDense(vza[ind],sza[ind],raa[ind])
    # tcc = np.tile(tcc, [nb, 1, 1])

    kpixel = 1
    for ks in range(kpixel, ns - kpixel):

        obs0 = obs[:, :, (ks - kpixel):(ks + kpixel + 1)]
        tcc0 = tcc[:, :, (ks - kpixel):(ks + kpixel + 1)]
        sza0 = sza[:, :, (ks - kpixel):(ks + kpixel + 1)]
        fhs0 = fhs[:, :, (ks - kpixel):(ks + kpixel + 1)]
        Kross0 = Kross[:, :, (ks - kpixel):(ks + kpixel + 1)]
        kli0 = kli[:, :, (ks - kpixel):(ks + kpixel + 1)]

        ind1 = (obs0 > 0) * (tcc0 < 0.05) * (sza0 < 60)


        obs1 = obs0[ind1]
        fhs1 = fhs0[ind1]
        Kross1 = Kross0[ind1]
        kli1 = kli0[ind1]

        # temp = fitting_ROSSRL_VNIR_min(obs1, Kross1, kli1)

        temp = fitting_ROSSLi_VNIR_min(obs1, Kross1, kli1)

        abck[0, ks] = temp[0]
        abck[1, ks] = temp[1]
        abck[2, ks] = temp[2]
        # abck[3, ks] = temp[3]

        # dtcabk[0, kl - kpixel, ks - kpixel] = coeffs[0]
        # dtcabk[1, kl - kpixel, ks - kpixel] = coeffs[1]
        # dtcabk[2, kl - kpixel, ks - kpixel] = coeffs[2]
        # dtcabk[3, kl - kpixel, ks - kpixel] = coeffs[3]

    return abck



def doMultiple12(param):
    return coeffdtc_invert((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]), param[6])


if __name__ =='__main__':
    multiprocessing.freeze_support()



    indir_tif0 = r'e:\AHI_heihe\tif\\'
    indir_lst0 = r'e:\AHI_heihe\tif\\'
    outdir_coeffs0 = r'E:\ShIP_VTKD\Coeff_Red_RossLi\\'
    symbol = 'AHI'

    indir_map = r'e:\map\\'
    # 观测天顶角vza和观测方位角vaa
    infile_vza = infile8 = indir_map + 'ahi_vza_heihe.tif'
    # 读tif文件，返回观测天顶角vza，图像宽度x，图像高度y，波段数，（左上角x坐标， 水平分辨率，旋转参数， 左上角y坐标，旋转参数，竖直分辨率），投影
    [vza,ns,nl,nb,geog,proj] = read_image_gdal(infile_vza)
    infile_vaa = infile8 = indir_map + 'ahi_vaa_heihe.tif'
    [vaa,ns,nl,nb,geog,proj] = read_image_gdal(infile_vaa)



    obs = np.asarray([])
    lst_obliq = np.asarray([])
    lst_nadir_normalized = np.asarray([])
    lst_obliq_normalized = np.asarray([])
    days_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


    nss = ns
    nll = nl


    for kmonth0 in range(8,9):
        thedoy = (kmonth0-1)*30+16

        for kday0 in range(1,32):

            nb = 40

            obss = np.zeros([nb, nll, nss])
            vzas = np.zeros([nb, nll, nss])
            szas = np.zeros([nb, nll, nss])
            psis = np.zeros([nb, nll, nss])
            tccs = np.zeros([nb , nll, nss])
            refs = np.zeros([nb, nll, nss])
            psts = np.zeros([nb, nll, nss])


            kstep = 0
            for khour0 in range(9-8,16-8):
                indir_lst = indir_lst0 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'
                indir_tif = indir_tif0 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'
                outdir_coeffs = outdir_coeffs0 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'
                kdoy = date2DOY(2019, kmonth0, kday0)

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
                    infile_lst = indir_lst + symbol + '_2019%03d' % (kdoy) + '_%02d' % khour + '%1d0' % kmin + '_red.tif'
                    infile_cloud = indir_tif + symbol + '_2019%03d' % (kdoy ) + '_%02d' % khour + '%1d0' % kmin + '_tcc.tif'
                    infile_sza = indir_tif + symbol + '_2019%03d' % (kdoy) + '_%02d' % khour + '%1d0' % kmin + '_sza.tif'
                    print(infile_lst)
                    if ((os.path.exists(infile_lst) == 1)):
                        [obs, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst)
                        [cloud, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud)
                        cloud = resize_data_near(cloud,nl,ns)
                        if (os.path.exists(infile_sza) == 1):
                            [sza, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza)
                        else:
                            sza = np.zeros([nl,ns])+90
                    else:
                        kstep = kstep + 1
                        continue

                    ind = (sza < 75) * (obs > 0)

                    if np.sum(ind) > 0:
                        # infile_vaa = indir2 + symbol + '_2019%03d' % (
                        #             kdoy + 1) + '_%1d0' % khour + '%1d0' % kmin + '_vaa.tif'
                        infile_saa = indir_tif + symbol + '_2019%03d' % (
                                kdoy ) + '_%02d' % khour + '%1d0' % kmin + '_saa.tif'
                        infile_rad = indir_tif + symbol + '_2019%03d' % (
                                kdoy ) + '_%02d' % khour + '%1d0' % kmin + '_rad.tif'
                        [rad, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_rad)
                        ref0 = resize_data_near(rad, nl, ns)
                        if (os.path.exists(infile_sza) == 1):
                            [saa, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa)
                        else:
                            saa = np.zeros([nl, ns]) + 90
                    else:
                        kstep = kstep + 1
                        continue


                    psi = np.abs(vaa - saa)
                    ref0 = ref0

                    vzas[kstep, :] = vza
                    obss[kstep, :] = obs
                    tccs[kstep, :] = cloud
                    szas[kstep, :] = sza
                    psis[kstep, :] = psi
                    refs[kstep, :] = ref0
                    psts[kstep, :] = khour0+8+kmin/6.0
                    kstep = kstep + 1


            ####multiple
            param = []
            kpixel = 1
            for kl in range(kpixel, nll - kpixel):


                vza_temp = vzas[:, (kl - kpixel):(kl + kpixel + 1), :]
                obs_temp = obss[:, (kl - kpixel):(kl + kpixel + 1), :]
                sza_temp = szas[:, (kl - kpixel):(kl + kpixel + 1), :]
                psi_temp = psis[:, (kl - kpixel):(kl + kpixel + 1), :]
                rad_temp = refs[:, (kl - kpixel):(kl + kpixel + 1), :]
                tcc_temp = tccs[:,(kl - kpixel):(kl + kpixel + 1),:]
                pst_temp = psts[:,(kl - kpixel):(kl + kpixel + 1),:]

                param.append([obs_temp,
                              pst_temp,
                              vza_temp,
                              sza_temp,
                              psi_temp,
                              tcc_temp,
                              rad_temp])
            #
            # result = doMultiple12(param[10])
            # a = 0
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



            results = np.asarray(results)

            a = np.zeros([nll, nss])
            b = np.zeros([nll, nss])
            c = np.zeros([nll, nss])
            # k = np.zeros([nll, nss])



            a[kpixel:-kpixel,:] = results[:, 0, :]
            b[kpixel:-kpixel,:] = results[:, 1, :]
            c[kpixel:-kpixel,:] = results[:, 2, :]
            # k[kpixel:-kpixel,:] = results[:, 3, :]



            outdir = outdir_coeffs

            outfile = outdir + '2019%03d' % (kdoy ) + '_daya.tif'
            write_image_gdal(a, nss, nll, 1, geog, proj, outfile)
            outfile = outdir + '2019%03d' % (kdoy) + '_dayb.tif'
            write_image_gdal(b, nss, nll, 1, geog, proj, outfile)
            outfile = outdir + '2019%03d' % (kdoy) + '_dayc.tif'
            write_image_gdal(c, nss, nll, 1, geog, proj, outfile)
            # outfile = outdir + '2019%03d' % (kdoy) + '_dayk.tif'
            # write_image_gdal(k, nss, nll, 1, geog, proj, outfile)