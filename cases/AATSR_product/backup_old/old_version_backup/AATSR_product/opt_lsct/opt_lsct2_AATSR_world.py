from multiple_lsct import *
import warnings
warnings.filterwarnings("ignore")
from utils.old.util_old import *


"""
AATSR 两组分温度反演
"""


if __name__ == '__main__':

    indir_lstN = r'D:\data\AATSR\lst/'
    indir_lstO = indir_lstN
    outdir_lsct = r'D:\data\AATSR\lsct/'

    indir_tif = r'D:\data\AATSR\tif/'
    indir_type = r'D:\data\AATSR\0_base\type\\'
    indir_emis = r'D:\data\AATSR\0_base\emis\\'

    infile_soil_emis = indir_emis + 'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
    infile_type = indir_type + 'type_world_1000.tif'
    infile_veg_emis = indir_emis + 'IGBP_Emi.txt'

    '''读取发射率'''
    [emis_s_, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_soil_emis)
    emis_s_ = emis_s_ / 1000
    [classif_, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_type)
    classif_ = np.asarray(classif_, np.int)
    classif_[classif_ == 255] = 17
    emis_v_ = read_txt_array(infile_veg_emis, 0, 2)
    emis_v_ = emis_v_[classif_, 0] / 1000

    '''读取数据'''
    filesName = search_file_rej(indir_lstN, ['lst_n'], 'enp')
    filesNum = len(filesName)

    for fileI in range(filesNum):
        fileName = filesName[fileI]
        year = fileName[6:10]
        doy_str = fileName[11:14]
        fileName_str = fileName[0:22]
        infileLstN = indir_lstN + fileName_str + 'lst_n.tif'
        infileLstO = indir_lstO + fileName_str + 'lst_f.tif'

        '''输出路径'''
        outfileLsct = outdir_lsct + fileName_str + '_lsct.tif'
        # if os.path.exists(outfileLsct) == 1: continue


        '''确定所需数据都存在'''
        c1 = os.path.exists(infileLstN)
        c2 = os.path.exists(infileLstO)
        if c1 * c2  == 0:
            print(fileName + ' lack lst data')
            continue

        # infileVzaN = indir_tif + fileName_str + 'vza_n.tif'
        # infileVaaN = indir_tif + fileName_str + 'vaa_n.tif'
        # infileVzaO = indir_tif + fileName_str + 'vza_f.tif'
        # infileVaaO = indir_tif + fileName_str + 'vaa_f.tif'
        # c1 = os.path.exists(infileVzaN)
        # c2 = os.path.exists(infileVaaN)
        # c3 = os.path.exists(infileVzaO)
        # c4 = os.path.exists(infileVaaO)
        # if c1 * c2 * c3 * c4== 0:
        #     print(fileName + ' lack observation angle data')
        #     continue
        #
        # infileSza = indir_tif + fileName_str + 'sza.tif'
        # infileSaa = indir_tif + fileName_str + 'saa.tif'
        # c1 = os.path.exists(infileSza)
        # c2 = os.path.exists(infileSaa)
        # if c1 * c2 == 0:
        #     print(fileName + ' lack sun angle data')
        #     continue

        infileRedN = indir_tif + fileName_str + 'red_n.tif'
        infileNirN = indir_tif + fileName_str + 'nir_n.tif'
        infileRedO = indir_tif + fileName_str + 'red_f.tif'
        infileNirO = indir_tif + fileName_str + 'nir_f.tif'
        c1 = os.path.exists(infileRedN)
        c2 = os.path.exists(infileNirN)
        c3 = os.path.exists(infileRedO)
        c4 = os.path.exists(infileNirO)
        if c1 * c2 * c3 * c4== 0:
            print(fileName + ' lack observation angle data')
            continue

        '''读取数据'''
        [lstN, ns, nl,bands, geog, proj] = read_image_gdal(infileLstN)
        [lstO, width, height, bands, geog, proj] = read_image_gdal(infileLstO)
        lstN = lstN/100
        lstO = lstO/100

        [redN, width, height, bands, geog, proj] = read_image_gdal(infileRedN)
        [nirN, width, height, bands, geog, proj] = read_image_gdal(infileNirN)
        [redO, width, height, bands, geog, proj] = read_image_gdal(infileRedO)
        [nirO, width, height, bands, geog, proj] = read_image_gdal(infileNirO)

        '''计算FVC'''
        ndvi_min = ndvi_min_g
        ndvi_max = ndvi_max_g

        ndvi_n = (nirN - redN) / (nirN + redN)
        ndvi_n[np.isnan(ndvi_n)] = 0
        fvc_n = (ndvi_n - ndvi_min) / (ndvi_max - ndvi_min)
        fvc_n = resize_data(fvc_n, nl, ns, 0)
        fvc_n[fvc_n > 1] = 1
        fvc_n[fvc_n < 0] = 0

        ndvi_o = (nirO - redO) / (nirO + redO)
        ndvi_o[np.isnan(ndvi_o)] = 0
        fvc_o = (ndvi_o - ndvi_min) / (ndvi_max - ndvi_min)
        fvc_o = resize_data(fvc_o, nl, ns, 0)
        fvc_o[fvc_o > 1] = 1
        fvc_o[fvc_o < 0] = 0

        # dif_fvc = fvc_n - fvc_o
        # outfiledfvc = outdir_lsct + fileName_str + '_dfvc.tif'
        # write_image_gdal(dif_fvc, ns, nl, 1, geog, proj, outfiledfvc)


        '''根据lon、lat调整emis'''
        lon_dir = indir_tif + fileName_str + 'lon.tif'
        lat_dir = indir_tif + fileName_str + 'lat.tif'
        [lon, ns, nl, temp3, temp4, temp5] = read_image_gdal(lon_dir)
        [lat, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(lat_dir)
        dataset = gdal.Open(infile_soil_emis)
        indx, indy = loc2map(lat, lon, dataset)
        indx[indx == 18000] = 0
        indy[indy == 36000] = 0
        emis_s = emis_s_[indx, indy]
        emis_v = emis_v_[indx, indy]
        classif = classif_[indx, indy]
        emis_s = np.reshape(emis_s, [nl, ns])
        emis_v = np.reshape(emis_v, [nl, ns])
        classif = np.reshape(classif, [nl, ns])

        '''反演LSCT'''
        print(fileName + '_lsct.tif start')
        lsct = inv_mpl_agl_multiple_2(lstN, lstO, emis_s, emis_v, fvc_n, fvc_o, wl=10.8)
        [ns, nl, nb] = np.shape(lsct)
        if (np.sum(lsct) == 0):
            print(fileName + '_lsct.tif' + ' no result')
            continue

        write_image_gdal(lsct, ns, nl, nb, geog, proj, outfileLsct)
        print(fileName + '_lsct.tif done')
