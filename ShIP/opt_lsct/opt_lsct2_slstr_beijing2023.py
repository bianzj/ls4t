import numpy as np
from scipy import interpolate
import matplotlib.mlab as ml
import matplotlib.pyplot as plt
import time
from util.util import *
from multiple_lsct import *
from util_lsct import *
from multiprocessing import Pool
import warnings
warnings.filterwarnings("ignore")


"""
slstr 两组分温度反演
"""

def line_inv_2(wNLine, wOLine, radNLine, radOLine, maskLine,ns = 1024):
    wl = 10.8
    off_ = 0
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.05
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    number_component = 2
    number_angle = 2
    number_value_threshold = 12

    result = np.zeros([number_component,ns])
    result_point = np.zeros([number_component, ns])

    off = 2
    for kk in range(off, ns-off):
        maskk = maskLine[2,kk]
        if maskk == 0: continue

        ns1 = kk - off
        ns2 = kk + off + 1
        ###### w1是nadir，w2是oblique
        w1 = wNLine[:,:,ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, :, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))

        bb1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        bb2 = (np.reshape(radOLine[:, ns1:ns2], -1))

        mask = np.reshape(maskLine[:, ns1:ns2], -1)
        ind = (mask == 1) * (np.isnan(w1[0, :]) == 0)

        num_val_point = np.sum(ind)
        if (num_val_point < number_value_threshold): continue
        ns_temp = np.asarray([-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
        nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
        part = 6

        n0 = np.ones(len(ns_temp))
        x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
        w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
        w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

        ww = np.hstack((w11[:, ind], w22[:, ind]))
        bb = np.hstack((bb1[ind], bb2[ind]))

        ###############################################
        ### least-square method
        ###############################################
        ww = np.transpose(ww)

        coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]

        ################################################
        ### first reult with averaing information
        ################################################
        offcenter = np.int(((2 * off + 1) * (2 * off + 1) - 1) / 2)
        fd = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
        fd = np.reshape(fd, -1) * 1.0

        coeffprior = np.asarray(coeffprior)
        ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
        ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
        indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                 (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold)
        apoint = np.sum(indnew)
        if (apoint <= 1):
            cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
            cd2 = np.sum(coeffprior[part:] * x[:, offcenter])
            ctprior = np.transpose(np.matrix([cd1, cd2]))
        else:
            fd[indnew] = fd[indnew] / np.sum(fd[indnew])

            cd1new = np.sum(ct1[indnew] * fd[indnew])
            cd2new = np.sum(ct2[indnew] * fd[indnew])
            ctprior = np.transpose(np.matrix([cd1new, cd2new]))
        component_temperature = inv_planck(wl, ctprior)
        #################################################
        ### second result by combining one-point result
        #################################################

        ns1 = kk - off_
        ns2 = kk + off_ + 1
        w1 = wNLine[:, 2, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, 2, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        b1 = (np.reshape(radNLine[2, ns1:ns2], -1))
        b2 = (np.reshape(radOLine[2, ns1:ns2], -1))
        w = np.hstack((w1, w2))
        b = np.hstack((b1, b2))
        w = np.transpose(w)

        #################################################
        ### least-squared method
        #################################################
        coeffprior = np.asarray(lstsq(w, b))[0]
        coeffprior_point = np.asarray(lstsq(w, b))[0]

        component_temperature_point = inv_planck(wl, coeffprior_point)
        result_point[:, kk] = [component_temperature_point[0], component_temperature_point[1]]

        #################################################
        ### Bayes method
        #################################################

        w = np.matrix(w)
        b = np.matrix(b)
        b = np.transpose(b)

        Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
        Cm = np.diag([soil_radiance_variance, leaf_radiance_variance])
        pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
        coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * b + np.linalg.inv(Cm) * ctprior)
        ### another solution for using priori information
        # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
        component_radiance = np.asarray(coeff)

        if (np.min(component_radiance) < radiance_min_threshold): continue
        if (np.max(component_radiance) > radiance_max_threshold): continue

        component_temperature = inv_planck(wl, component_radiance)

        result[:, kk] = [component_temperature[0], component_temperature[1]]

    return result_point


if __name__ == '__main__':

    indir_lstN = r'D:\data\data_download\Sentinel3\s3_lst/'
    indir_lstO = r'D:\data\data_download\Sentinel3\s3_lst/'
    outdir_lsct = r'D:\data\data_download\Sentinel3\s3_lsct/'

    indir_tif = r'D:\data\data_download\Sentinel3\s3_tif\\'
    # indir_fvcN = r'D:\data\lai\MCD_TIF\fvc//'
    # indir_fvcO = r'D:\data\lai\MCD_TIF\fvc//'
    # indir_lai = r'D:\data\lai\lai_heihe/'
    indir_type = 'd:/data/type/'
    indir_ems = r'D:\data\emis/'

    infile_soil_emis = indir_ems + 'emis1_polar_beijing.tif'
    infile_type = indir_type + 'type_beijing_1000.tif'
    infile_veg_emis = indir_ems + 'IGBP_Emi.txt'

    [emis_s, emis_v, geog, proj] = file2Array_static(infile_soil_emis, infile_veg_emis, infile_type)
    # [type, width, height, bands, geog, proj] = read_image_gdal(infile_type)

    filesName = search_file(indir_lstN, ['day','lst'])
    filesNum = len(filesName)

    for fileI in range(filesNum):
        fileName = filesName[fileI][:-18]
        doyStr = fileName[-3:]
        infileLstN = indir_lstN + fileName + '_day_lst_nadir.tif'
        infileLstO = indir_lstO + fileName + '_day_lst_obliq.tif'
        c1 = os.path.exists(infileLstN)
        c2 = os.path.exists(infileLstO)
        if c1 * c2  == 0:
            print(fileName + ' lack lst data')
            continue

        infileVzaN = indir_tif + fileName + '_day_vza_nadir.tif'
        infileVaaN = indir_tif + fileName + '_day_vaa_nadir.tif'
        infileVzaO = indir_tif + fileName + '_day_vza_obliq.tif'
        infileVaaO = indir_tif + fileName + '_day_vaa_obliq.tif'
        c1 = os.path.exists(infileVzaN)
        c2 = os.path.exists(infileVaaN)
        c3 = os.path.exists(infileVzaO)
        c4 = os.path.exists(infileVaaO)
        if c1 * c2 * c3 * c4== 0:
            print(fileName + ' lack observation angle data')
            continue

        infileSza = indir_tif + fileName + '_day_sza_nadir.tif'
        infileSaa = indir_tif + fileName + '_day_saa_nadir.tif'
        c1 = os.path.exists(infileSza)
        c2 = os.path.exists(infileSaa)
        if c1 * c2 == 0:
            print(fileName + ' lack sun angle data')
            continue

        # infileFvcN = indir_fvcN + fileName +  '_fvcN.tif'
        # infileFvcO = indir_fvcO + fileName + '_fvcO.tif'
        # c1 = os.path.exists(infileFvcN)
        # c2 = os.path.exists(infileFvcO)
        # if c1 * c2  == 0:
        #     print(fileName + ' lack fvc data')
        #     continue

        # infileLai = indir_lai + '2019_doy' + doyStr + '_lai.tif'
        # if os.path.exists(infileLai) == 0:
        #     print(fileName + ' lack LAI data')
        #     continue

        outfileLsct = outdir_lsct + fileName + '_lsct.tif'
        # if os.path.exists(outfileLsct):
        #     print(fileName + '_lsct.tif exists')
        #     continue
        # else:
        #     print(fileName + '_lsct.tif processing...')


        [lstN, width, height,bands, geog, proj] = read_image_gdal(infileLstN)
        [lstO, width, height, bands, geog, proj] = read_image_gdal(infileLstO)

        # [fvcN, width, height, bands, geog, proj] = read_image_gdal(infileFvcN)
        # [fvcO, width, height, bands, geog, proj] = read_image_gdal(infileFvcO)
        infile1 = indir_tif + fileName +  '_day_red_nadir.tif'
        infile2 = indir_tif + fileName +  '_day_nir_nadir.tif'
        infile3 = indir_tif + fileName +  '_day_red_obliq.tif'
        infile4 = indir_tif + fileName +  '_day_nir_obliq.tif'
        [redN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile1)
        [nirN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile2)
        [redO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile3)
        [nirO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile4)

        ndvi_max = 0.95
        ndvi_min = 0.05
        ndviN = (nirN - redN) / (nirN + redN)
        ndviN[np.isnan(ndviN)] = 0
        fvcN = (ndviN - ndvi_min) / (ndvi_max - ndvi_min)
        fvcN = resize_data(fvcN, height, width)
        fvcN[fvcN > 1] = 1
        fvcN[fvcN < 0] = 0

        ndviO = (nirO - redO) / (nirO + redO)
        ndviO[np.isnan(ndviO)] = 0
        fvcO = (ndviO - ndvi_min) / (ndvi_max - ndvi_min)
        fvcO = resize_data(fvcO,  height, width)
        fvcO[fvcO > 1] = 1
        fvcO[fvcO < 0] = 0

        lsct = inv_mpl_agl_multiple_2(lstN, lstO, emis_s, emis_v, fvcN, fvcO, wl=10.8)
        [ns, nl, nb] = np.shape(lsct)
        if (np.sum(lsct) == 0):
            print(fileName + '_lsct.tif' + ' no result')
            continue
        write_image_gdal(lsct, ns, nl, nb, geog, proj, outfileLsct)
        print(fileName + '_lsct.tif done')
