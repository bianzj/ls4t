import numpy as np

from util.myfun import *
from normalization_temporal.fitting_DTC import *
import time
from multiprocessing import Pool, cpu_count
import multiprocessing
from sklearn.linear_model import LinearRegression

### 时间连续数据拟合DTC的系数
### 用于参考，与改进的结果进行对比


if __name__ =='__main__':
    multiprocessing.freeze_support()

    indir_tif0 = r'E:\AHI_heihe\tif\\'
    indir_lst0 = r'E:\AHI_heihe\lst\\'
    indir_lai = r'e:\lai_heihe2\\'
    ### 处理直接DTC角度协同结果
    # indir_coeffs0 = r'E:\ShIP_DTC\DTC_VinRL_heihe\\'
    # outdir_lst = r'E:\ShIP_DTC\LST_DTC_VinRL_heihe\\'

    ### 处理先角度后DTC结果
    # indir_coeffs0 = r'E:\ShIP_DTC\DTC_afterVinRL_heihe\\'
    # outdir_lst = r'E:\ShIP_DTC\LST_DTC_afterVinRL_heihe\\'

    ### 不同的算法
    indir_coeffs00 = r'E:\ShIP_VTKD\Coeff_DTC\\'
    indir_coeffs0 = r'E:\ShIP_VTKD\Coeff_Red_RossLi\\'
    # outdir_lst = r'E:\ShIP_KDTC\LST_KDTC_RLSFLi_heihe\\'

    symbol = 'AHI'

    indir_map = r'E:\map\\'
    infile_vza = infile8 = indir_map + 'ahi_vza_heihe.tif'
    [vza,ns,nl,nb,geog,proj] = read_image_gdal(infile_vza)
    infile_vaa = infile8 = indir_map + 'ahi_vaa_heihe.tif'
    [vaa,ns,nl,nb,geog,proj] = read_image_gdal(infile_vaa)
    infile_dem = infile8 = indir_map + 'dem_geo_heihe.tif'
    [dem,ns,nl,nb,geog,proj] = read_image_gdal(infile_dem)

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

            kdoy = date2DOY(2019, kmonth0, kday0)
            infile_coeffta1 = indir_coeffs0 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_daya.tif'%kdoy
            infile_coeffto1 = indir_coeffs0 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_dayb.tif'%kdoy
            infile_coeffta2 = indir_coeffs0 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_dayc.tif'%kdoy
            # infile_coeffto2 = indir_coeffs0 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_dayk.tif'%kdoy

            infile_coeffta3 = indir_coeffs00 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_ta.tif'%kdoy
            infile_coeffto3 = indir_coeffs00 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_to.tif'%kdoy
            infile_coeffts = indir_coeffs00 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_ts.tif'%kdoy
            infile_coefftm = indir_coeffs00 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_tm.tif'%kdoy

            infile_lai = indir_lai + '2019_doy%03d.tif'%kdoy

            [coeffa, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffta1)
            [coeffb, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffto1)
            [coeffc, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffta2)
            # [coeffk, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffto2)

            [coeffta, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffta3)
            [coeffto, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffto3)
            [coeffts, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffts)
            [coefftm, ns, nl, nb, geog, proj] = read_image_gdal(infile_coefftm)

            [lai, ns, nl, nb, geog, proj] = read_image_gdal(infile_lai)

            omg = 4.0 / 3.0 * (coefftm - coeffts)

            nb = 40

            obss = np.zeros([nb, nll, nss])
            kisos = np.zeros([nb, nll, nss])
            tbns = np.zeros([nb, nll, nss])
            # vzas = np.zeros([nb, nll, nss])
            # szas = np.zeros([nb, nll, nss])
            # psis = np.zeros([nb, nll, nss])
            tccs = np.zeros([nb, nll, nss])
            # refs = np.zeros([nb, nll, nss])
            psts = np.zeros([nb, nll, nss])
            kvols = np.zeros([nb,nll,nss])
            khots = np.zeros([nb,nll,nss])
            tas = np.zeros([nb,nll,nss])
            rads = np.zeros([nb,nll,nss])
            sms =  np.zeros([nb,nll,nss])
            coms =  np.zeros([nb,nll,nss])
            # lai = np.zeros([nll,nss])
            kvols1 = np.zeros([nb, nll, nss])
            khots1 = np.zeros([nb, nll, nss])
            kisos1 = np.zeros([nb, nll, nss])

            kstep = 0
            for khour0 in range(10-8,16-8):
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
                    infile_lst = indir_lst + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_lst.tif'
                    infile_cloud = indir_tif + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_tcc.tif'
                    infile_sza = indir_tif + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_sza.tif'
                    infile_saa = indir_tif + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_saa.tif'
                    infile_ta  = indir_tif + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_ta.tif'
                    infile_rad  = indir_tif + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_rad.tif'
                    infile_sm  = indir_tif + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_sm.tif'
                    # print(infile_lst)
                    if ((os.path.exists(infile_lst) == 1)):
                        [obs, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst)
                        [cloud, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud)
                        [ta, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_ta)
                        [rad, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_rad)
                        [sm, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_sm)


                        cloud = resize_data_near(cloud, nl, ns)
                        ta = resize_data_near(ta, nl, ns)
                        rad = resize_data_near(rad, nl, ns)
                        sm = resize_data_near(sm, nl, ns)

                        if (os.path.exists(infile_sza) == 1):
                            [sza, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza)
                            [saa, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa)
                        else:
                            sza = np.zeros([nl, ns]) + 90
                            saa = np.zeros([nl,ns])
                    else:
                        kstep = kstep + 1
                        continue


                    # vza[:] = 0
                    k = 1.0
                    # k = coeffk

                    raa = np.abs(saa-vaa)
                    pst  = khour0 + 8 + kmin/6.0
                    ind = raa > 180
                    raa[ind] = 360 - raa[ind]

                    thetas = np.deg2rad(sza)
                    thetaa = np.deg2rad(raa)
                    thetav = np.deg2rad(abs(vza))

                    fhs = np.zeros([nll, nss])
                    Kross = np.zeros([nll, nss])

                    ind = (obs > 0) * (sza < 60)
                    az = np.cos(thetas[ind]) * np.cos(thetav[ind]) + \
                         np.sin(thetas[ind]) * np.sin(thetav[ind]) * np.cos(thetaa[ind])
                    angle = np.arccos(az)
                    fhs[ind] = np.sqrt(
                        (np.power(np.tan(thetas[ind]), 2) + np.power(np.tan(thetav[ind]), 2) - 2 * np.tan(
                            thetas[ind]) * np.tan(thetav[ind]) *
                         np.cos(thetaa[ind])))


                    fn = np.tan(thetas)
                    kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.01 - np.exp(-k * fn))
                    kR = np.exp(-k * fhs)


                    Kross[ind] = ((np.pi / 2.0 - angle) * az + np.sin(angle)) / (
                            np.cos(thetav[ind]) + np.cos(thetas[ind])) - np.pi / 4.0

                    # kVin = kernel_Vin(vza)
                    kli = kernel_LiDense(vza,sza,raa)
                    # kli = kernel_LiSparse(vza, sza, raa)
                    kVin = np.cos(vza*rd)

                    cthetv = np.cos(np.deg2rad(vza))
                    klsf = 0.069 * cthetv * cthetv - 0.215 * cthetv + 1.176


                    bv = 1-np.exp(-lai * 0.5)
                    bi = 1-np.exp(-lai * 0.5 / np.cos(sza * rd))

                    tbn = coeffto + coeffta * np.cos(np.pi / omg * (pst - coefftm))


                    obs[dem>2000] = 0
                    obs[coeffa ==0] = 0
                    obs[coeffb ==0] = 0
                    obs[coeffc ==0] = 0
                    obs[Kross==0] = 0
                    obs[lai <0.05] =0
                    obs[lai > 3.05] = 0
                    # obs[lai <0.01] = 0
                    # obs[sm < 0.05] = 0

                    ta = ta-273.15
                    # com =  Kross*coeffa*rad
                    com = kli * coeffb * ta
                    # com = kli*coeffb*ta*bi + klsf*coeffa*bv*ta
                    kvols[kstep,:] = Kross*coeffa*ta
                    khots[kstep,:] = kli*coeffb*ta

                    kvols1[kstep,:] = Kross*coeffa*rad/3600.0
                    khots1[kstep,:] = kli*coeffb*rad/3600.0
                    kisos1[kstep,:] = coeffc*rad/3600.0

                    obss[kstep,:] = obs
                    tccs[kstep,:] = cloud
                    tbns[kstep,:] = tbn+273.15
                    kisos[kstep,:] = coeffc*ta
                    tas[kstep,:] = ta
                    sms[kstep,:] = sm
                    rads[kstep,:] = rad
                    coms[kstep,:] = com
                    kstep = kstep + 1

                    # Tn = fVin * kVin + fRL * kLi + fIso
                    # outfile = outdir_lst +  r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\' + symbol+  '_2019%03d' % (kdoy) + '_%02d' % khour + '%1d0' % kmin + '_lst.tif'
                    # write_image_gdal(Tn, nss, nll, 1, geog, proj, outfile)

            temp_max = np.percentile(kvols, 95)
            temp_min = np.percentile(kvols, 5)
            temp_max2 = np.percentile(khots, 95)
            temp_min2 = np.percentile(khots,5)

            ind = (tbns > 275) * (obss > 275) * (tccs < 0.01) * (np.abs(tbns - obss) < 5.0) * (kvols > temp_min) * (
                        kvols < temp_max)* (khots > temp_min2) * (
                        khots < temp_max2) *(sms < 0.15)*(sms>0.00)
            if np.sum(ind) < 10000: continue
            rdbt = tbns[ind] - obss[ind]
            kvols = kvols[ind]
            khots = khots[ind]
            kisos = kisos[ind]
            kvols1 = kvols1[ind]
            khots1 = khots1[ind]
            kisos1 = kisos1[ind]
            sms = sms[ind]
            rads = rads[ind]
            tas = tas[ind]
            coms = coms[ind]

            model = LinearRegression(copy_X=True, fit_intercept=True, n_jobs=-1, normalize=False)

            A = np.asarray([kvols, khots, kisos,kvols1,khots1,kisos1])
            A = np.transpose(A)
            Y = rdbt
            model.fit(A, Y)

            coef = model.coef_
            y0 = model.intercept_
            YY = model.predict(A)
            dif = YY - Y
            dai = np.std(Y)
            aai = np.average(np.abs(Y))
            rmse = np.sqrt(np.mean(dif * dif))
            # print(kdoy,np.size(dif),dai,aai,rmse)

            plt.figure(figsize=[4.5, 4.0])
            plt.hist2d(YY, Y, bins=60, norm=LogNorm(), cmap='jet')
            plt.xlabel('fitted LST DA')
            plt.ylabel('simulated LST DA')
            plt.xlim([-4,2.5])
            plt.ylim([-4,2.5])
            # plt.plot(khot_all_new[ind],obsda_all[ind],'.')
            plt.show()
            print(kdoy,coef)