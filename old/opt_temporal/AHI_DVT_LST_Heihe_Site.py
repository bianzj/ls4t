from util.myfun import *
from normalization_temporal.fitting_DTC import *
import time
from multiprocessing import Pool, cpu_count
import multiprocessing


### 时间连续数据拟合DTC的系数
### 用于参考，与改进的结果进行对比


if __name__ =='__main__':
    multiprocessing.freeze_support()

    indir_tif0 = r'E:\AHI_heihe\tif\\'
    indir_lst0 = r'E:\AHI_heihe\lst\\'

    indir_coeffs00 = r'E:\ShIP_DVT\Coeff_DVT_heihe\\'
    indir_coeffs0 = r'E:\ShIP_DVT\Coeff_DVT_heihe\\'
    outdir_lst = r'E:\ShIP_DVT\LST_DVT_heihe\\'

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


    nss = ns
    nll = nl


    for kmonth0 in range(8,9):
        thedoy = (kmonth0-1)*30+16

        for kday0 in range(1,32):

            kdoy = date2DOY(2019, kmonth0, kday0)
            infile_coeffta1 = indir_coeffs0 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_ta1.tif'%kdoy
            infile_coeffto1 = indir_coeffs0 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_to1.tif'%kdoy
            infile_coeffta2 = indir_coeffs0 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_ta2.tif'%kdoy
            infile_coeffto2 = indir_coeffs0 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_to2.tif'%kdoy
            infile_coeffta3 = indir_coeffs00 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_ta3.tif'%kdoy
            infile_coeffto3 = indir_coeffs00 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_to3.tif'%kdoy
            infile_coeffts = indir_coeffs00 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_ts.tif'%kdoy
            infile_coefftm = indir_coeffs00 + '%02d\\' % kmonth0 + '%02d\\'% kday0 + '2019%03d_tm.tif'%kdoy

            [coeffta1, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffta1)
            [coeffto1, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffto1)
            [coeffta2, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffta2)
            [coeffto2, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffto2)
            [coeffta3, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffta3)
            [coeffto3, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffto3)
            [coefftsr, ns, nl, nb, geog, proj] = read_image_gdal(infile_coeffts)
            [coefftm, ns, nl, nb, geog, proj] = read_image_gdal(infile_coefftm)


            omg = 4.0 / 3.0 * (coefftm - coefftsr)
            for khour0 in range(3-8,21-8):
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
                    infile_red = indir_tif + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_red.tif'
                    infile_nir = indir_tif + symbol + '_2019%03d' % (
                        kdoy) + '_%02d' % khour + '%1d0' % kmin + '_nir.tif'
                    print(infile_lst)
                    if ((os.path.exists(infile_lst) == 1) & (os.path.exists(infile_red) == 1)):
                        [obs, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst)
                        [cloud, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud)
                        cloud = resize_data_near(cloud, nl, ns)
                        [red, ns, nl, temp, geog, proj] = read_image_gdal(infile_red)
                        [nir, ns, nl, temp, geog, proj] = read_image_gdal(infile_nir)

                        ind = (red < 0.5) * (obs > 245) * (nir > 0.005)

                        if np.sum(ind) > 0:
                            vi = np.zeros([nll, nss])
                            bf = np.zeros([nll, nss])
                            vi[ind] = (nir[ind] - red[ind]) / (nir[ind] + red[ind])
                            bf[ind] = (nir[ind] + red[ind]) / 2.0
                            pst = khour0 + 8 + kmin / 6.0

                            fvi = coeffto1 + coeffta1 * np.cos(np.pi / omg * (pst - coefftm))
                            fbf = coeffto2 + coeffta2 * np.cos(np.pi / omg * (pst - coefftm))
                            fiso = coeffto3 + coeffta3 * np.cos(np.pi / omg * (pst - coefftm))

                            Tn = fvi * vi + fbf * bf + fiso
                            # Tn = fiso
                            outfile = outdir_lst +  r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\' + symbol+  '_2019%03d' % (kdoy) + '_%02d' % khour + '%1d0' % kmin + '_lst.tif'
                            write_image_gdal(Tn, nss, nll, 1, geog, proj, outfile)
