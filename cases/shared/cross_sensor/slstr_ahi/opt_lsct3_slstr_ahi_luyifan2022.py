import numpy as np
from scipy import interpolate
import matplotlib.mlab as ml
import matplotlib.pyplot as plt
import time
from util.util import *
from util_lsct import *
from multiprocessing import Pool
import warnings

warnings.filterwarnings("ignore")

# 3 observations from slstr + ahi for 3 components
if __name__ == '__main__':

    indir_lstN = r'D:\data\LSCT\slstr_2022\lst/'
    indir_lstO = r'D:\data\LSCT\slstr_2022\lst/'
    indir_lstAhi = r'D:\data\LSCT\ahi_2022\lst/'
    indir_tif = r'D:\data\LSCT\slstr_2022\tif/'
    indir_fvcN = r'D:\data\LSCT\fvc_2022/'
    indir_fvcO = r'D:\data\LSCT\fvc_2022/'
    indir_fvcAhi = r'D:\data\LSCT\fvc_2022/'
    indir_lai = r'D:\data\LSCT\lai_2022/'

    # indir_lstN = r'E:\s3a_lst/'
    # indir_lstO = r'E:\s3a_lst/'
    # indir_lstAhi = r'e:\ahi_s3a_lst/'
    # indir_tif = r'e:\s3a_tif/'
    # indir_fvcN = r'e:\fvc_s3a_n/'
    # indir_fvcO = r'e:\fvc_s3a_o/'
    # indir_fvcAhi = r'e:\fvc_s3a_ahi/'
    # indir_lai = r'e:\lai/'

    outdir_lsct = r'D:\data\LSCT\slstr_2022\lsct3_new/'
    outdir_lsct_window = r'D:\data\LSCT\slstr_2022\lsct3_window/'
    outdir_lsct_point = r'D:\data\LSCT\slstr_2022\lsct3_point/'

    indir_type = 'd:/data/type/'
    indir_ems = r'D:\data\emis/'

    infile_soil_emis = indir_ems + 'emis1_polar_heihe_cut.tif'
    infile_type = indir_type + 'type_heihe_1000_new.tif'
    infile_veg_emis = indir_ems + 'IGBP_Emi.txt'

    [emis_s, emis_v, geog, proj] = readImages_emis(infile_soil_emis, infile_veg_emis, infile_type)
    [type, width, height, bands, geog, proj] = read_image_gdal(infile_type)

    filesName = search_file(indir_lstN, ['day', 'lst'])
    filesNum = len(filesName)
    ahiFileNames = search_file(indir_lstAhi, ['lst'])

    for fileI in range(filesNum):
        # for fileI in range(243,244):
        fileName = filesName[fileI][:-18]
        doyStr = fileName[-3:]
        infileLstN = indir_lstN + fileName + '_day_lst_nadir.tif'
        infileLstO = indir_lstO + fileName + '_day_lst_obliq.tif'
        #
        ahifileArr = [ahifile for ahifile in ahiFileNames if doyStr+"_"  in ahifile]
        if np.size(ahifileArr) <= 1: continue
        ahiFileName1 = ahifileArr[0][:-7]
        ahiFileName2 = ahifileArr[1][:-7]
        infileLstAhi1 = indir_lstAhi + ahiFileName1 + 'lst.tif'
        infileLstAhi2 = indir_lstAhi + ahiFileName2 + 'lst.tif'
        ahiTime1 = int(ahiFileName1[12:16])
        ahiTime2 = int(ahiFileName2[12:16])
        c1 = os.path.exists(infileLstN)
        c2 = os.path.exists(infileLstO)
        c3 = os.path.exists(infileLstAhi1)
        c4 = os.path.exists(infileLstAhi2)
        if c1 * c2 * c3 *c4 == 0:
            print(fileName + ' lack lst data')
            continue

        infileVzaN = indir_tif + fileName + '_day_vza_nadir.tif'
        infileVaaN = indir_tif + fileName + '_day_vaa_nadir.tif'
        infileVzaO = indir_tif + fileName + '_day_vza_obliq.tif'
        infileVaaO = indir_tif + fileName + '_day_vaa_obliq.tif'
        infileTime = indir_tif + fileName + '_day_time.tif'
        infileVzaAhi = r'D:\data\base\ahi_angle_2022\AHI_VZA_HEIHE_cut.tif'
        infileVaaAhi = r'D:\data\base\ahi_angle_2022\AHI_VAA_HEIHE_cut.tif'
        c1 = os.path.exists(infileVzaN)
        c2 = os.path.exists(infileVaaN)
        c3 = os.path.exists(infileVzaO)
        c4 = os.path.exists(infileVaaO)
        if c1 * c2 * c3 * c4 == 0:
            print(fileName + ' lack observation angle data')
            continue

        infileSza = indir_tif + fileName + '_day_sza_nadir.tif'
        infileSaa = indir_tif + fileName + '_day_saa_nadir.tif'
        c1 = os.path.exists(infileSza)
        c2 = os.path.exists(infileSaa)
        if c1 * c2 == 0:
            print(fileName + ' lack sun angle data')
            continue

        infileFvcN = indir_fvcN + fileName + '_fvcN.tif'
        infileFvcO = indir_fvcO + fileName + '_fvcO.tif'
        infileFvcAhi = indir_fvcAhi + fileName + '_fvcAhi.tif'
        c1 = os.path.exists(infileFvcN)
        c2 = os.path.exists(infileFvcO)
        c3 = os.path.exists(infileFvcAhi)
        if c1 * c2 * c3 == 0:
            print(fileName + ' lack fvc data')
            continue

        infileLai = indir_lai + fileName + '_lai.tif'
        if os.path.exists(infileLai) == 0:
            print(fileName + ' lack LAI data')
            continue

        outfileLsct = outdir_lsct + fileName + '_lsct.tif'
        if os.path.exists(outfileLsct):
            print(fileName + '_lsct.tif exists')
            continue
        else:
            print(fileName + '_lsct.tif processing...')

        [lstN, width, height, bands, geog, proj] = read_image_gdal(infileLstN)
        [lstO, width, height, bands, geog, proj] = read_image_gdal(infileLstO)
        [lstAhi1, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileLstAhi1)
        [lstAhi2, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileLstAhi2)

        [slstrTime, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileTime)

        ### AHI加权求和,由于研究区很小，基本时间都一致，取众数
        ahiTime1 = ahiTime1//100 *60 + ahiTime1 % 100
        ahiTime2 = ahiTime2//100 *60 + ahiTime2 % 100
        slstrTime = (slstrTime[96,83]/100)
        slstrTime = slstrTime//100 * 60 + slstrTime % 100
        lstAhi = np.abs((slstrTime-ahiTime2)/10) * lstAhi1 + np.abs((slstrTime-ahiTime1)/10) * lstAhi2
        if(fileName[0:3]=="S3A"):
            lstAhi = lstAhi * 0.9727491898535005 + 8.14384409751824
        else:
            lstAhi = lstAhi * 0.9738654689993518 + 7.602965534546172

        pgN = readImages_angle(infileLai, infileVzaN, infileVaaN, infileSza, infileSaa, resample=1)
        pgO = readImages_angle(infileLai, infileVzaO, infileVaaO, infileSza, infileSaa, resample=1)
        pgAhi = readImages_angle(infileLai, infileVzaAhi, infileVaaAhi, infileSza, infileSaa, resample=1)

        [fvcN, width, height, bands, geog, proj] = read_image_gdal(infileFvcN)
        [fvcO, width, height, bands, geog, proj] = read_image_gdal(infileFvcO)
        [fvcAhi, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileFvcAhi)

        lsct = inv_mpl_agl_multiple(lstN, lstO, lstAhi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pgN, pgO, pgAhi, wl=10.8)
        [ns, nl, nb] = np.shape(lsct)
        # lsct,lsct_window,lsct_point = inv_mpl_agl_multiple(lstN, lstO, lstAhi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pgN, pgO, pgAhi, wl=10.8)
        # [ns, nl, nb] = np.shape(lsct)
        if (np.sum(lsct) == 0):
            print(fileName + '_lsct.tif' + ' no result')
            continue
        write_image_gdal(lsct, ns, nl, nb, geog, proj, outfileLsct)
        # outfileLsct_window = outdir_lsct_window + fileName+ '_lsct_window.tif'
        # outfileLsct_point = outdir_lsct_point + fileName+ '_lsct_point.tif'
        # write_image_gdal(lsct_window, ns, nl, nb, geog, proj, outfileLsct_window)
        # write_image_gdal(lsct_point, ns, nl, nb, geog, proj, outfileLsct_point)
        print(fileName + '_lsct.tif done')
