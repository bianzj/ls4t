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

    indir_lstN = r'D:\mydata\s3a\lst_china\s3a_lst_china/'
    indir_lstO = r'D:\mydata\s3a\lst_china\s3a_lst_china/'
    indir_lstAhi = r'D:\mydata\s3a\lst_china\ahi_lst_china/'
    indir_tif = r'D:\data\s3a_tif/'
    indir_fvcN = r'D:\data\fvc\fvc_china\fvc_china_n/'
    indir_fvcO = r'D:\data\fvc\fvc_china\fvc_china_o/'
    indir_fvcAhi = r'D:\data\fvc\fvc_china\fvc_china_ahi/'
    indir_lai = r'D:\data\lai\lai_china/'

    # indir_lstN = r'E:\s3a_lst/'
    # indir_lstO = r'E:\s3a_lst/'
    # indir_lstAhi = r'e:\ahi_s3a_lst/'
    # indir_tif = r'e:\s3a_tif/'
    # indir_fvcN = r'e:\fvc_s3a_n/'
    # indir_fvcO = r'e:\fvc_s3a_o/'
    # indir_fvcAhi = r'e:\fvc_s3a_ahi/'
    # indir_lai = r'e:\lai/'

    outdir_lsct = r'D:\mydata\s3a\s3a_lsct_china/'

    indir_type = 'd:/data/type/'
    indir_ems = r'D:\data\emis/'

    infile_soil_emis = indir_ems + 'emis1_polar.tif'
    infile_type = indir_type + 'type_china_1000.tif'
    infile_veg_emis = indir_ems + 'IGBP_Emi.txt'

    [emis_s,emis_v,geog,proj] = readImages_emis(infile_soil_emis, infile_veg_emis, infile_type)
    [type, width, height, bands, geog, proj] = read_image_gdal(infile_type)

    filesName = search_file(indir_lstN, ['day','lst'])
    filesNum = len(filesName)

    for fileI in range(filesNum):
    # for fileI in range(243,244):
        fileName = filesName[fileI][:-18]
        doyStr = fileName[-3:]
        infileLstN = indir_lstN + fileName + '_day_lst_nadir.tif'
        infileLstO = indir_lstO + fileName + '_day_lst_obliq.tif'
        infileLstAhi = indir_lstAhi + fileName + '_day_lst.tif'
        c1 = os.path.exists(infileLstN)
        c2 = os.path.exists(infileLstO)
        c3 = os.path.exists(infileLstAhi)
        if c1 * c2 * c3 == 0:
            print(fileName + ' lack lst data')
            continue

        infileVzaN = indir_tif + fileName + '_day_vza_nadir.tif'
        infileVaaN = indir_tif + fileName + '_day_vaa_nadir.tif'
        infileVzaO = indir_tif + fileName + '_day_vza_obliq.tif'
        infileVaaO = indir_tif + fileName + '_day_vaa_obliq.tif'
        infileVzaAhi = r'D:\data\map\ahi_vza.tif'
        infileVaaAhi = r'd:\data\map\ahi_vaa.tif'
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

        infileFvcN = indir_fvcN + '2019_doy' + doyStr + '_fvc.tif'
        infileFvcO = indir_fvcO + '2019_doy' + doyStr + '_fvc.tif'
        infileFvcAhi = indir_fvcAhi + '2019_doy' + doyStr + '_fvc.tif'
        c1 = os.path.exists(infileFvcN)
        c2 = os.path.exists(infileFvcO)
        c3 = os.path.exists(infileFvcAhi)
        if c1 * c2 * c3 == 0:
            print(fileName + ' lack fvc data')
            continue

        infileLai = indir_lai + '2019_doy' + doyStr + '_lai.tif'
        if os.path.exists(infileLai) == 0:
            print(fileName + ' lack LAI data')
            continue

        outfileLsct = outdir_lsct + fileName + '_lsct.tif'
        if os.path.exists(outfileLsct):
            print(fileName + '_lsct.tif exists')
            continue
        else:
            print(fileName + '_lsct.tif processing...')


        [lstN, width, height,bands, geog, proj] = read_image_gdal(infileLstN)
        [lstO, width, height, bands, geog, proj] = read_image_gdal(infileLstO)
        [lstAhi, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileLstAhi)

        pgN = readImages_angle(infileLai, infileVzaN, infileVaaN, infileSza, infileSaa, resample=1)
        pgO = readImages_angle(infileLai, infileVzaO, infileVaaO, infileSza, infileSaa, resample=1)
        pgAhi = readImages_angle(infileLai, infileVzaAhi, infileVaaAhi, infileSza, infileSaa, resample=2)

        [fvcN, width, height, bands, geog, proj] = read_image_gdal(infileFvcN)
        [fvcO, width, height, bands, geog, proj] = read_image_gdal(infileFvcO)
        [fvcAhi, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileFvcAhi)

        lsct = inv_mpl_agl_multiple(lstN, lstO, lstAhi,emis_s, emis_v, fvcN, fvcO, fvcAhi, wl=10.8)
        [ns, nl, nb] = np.shape(lsct)
        if (np.sum(lsct) == 0):
            print(fileName + '_lsct.tif' + ' no result')
            continue
        write_image_gdal(lsct, ns, nl, nb, geog, proj, outfileLsct)
        print(fileName + '_lsct.tif done')
