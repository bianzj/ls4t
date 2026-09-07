import sys
sys.path.append('/data1/home/AircasBianzj/code/')
from multiple_lsct import *
from util_lsct import *
from utils.myfun_lyf import *
import warnings
warnings.filterwarnings("ignore")
from utils.old.util_constant import *


"""
AATSR 两组分温度反演
"""

year = sys.argv[1]
month = sys.argv[2]
day = sys.argv[3]
time_str = "//%04d" % int(year) + "//%02d" % int(month) + "//%02d" % int(day) + "//"

def cal_fvc_from_lai(thetav,lai):
    G = 0.5
    rd = np.pi / 180.0
    costhetanv = np.cos(thetav * rd)
    fvc = 1 - exp(-G*lai/costhetanv)
    fvc[fvc>1] = 1
    fvc[fvc<0] = 0
    return fvc

if __name__ == '__main__':

    indir_lstN = r'/data1/public1/Bianzj/AATSR/AATSR_lst/'+ time_str
    indir_lstO = indir_lstN
    outdir_lsct = r'/data1/public1/Bianzj/AATSR/AATSR_lsct/'+ time_str

    indir_tif = r'/data1/public1/Bianzj/AATSR/AATSR_tif/'+ time_str
    indir_type = r'/data1/public1/Bianzj/type/'
    indir_emis = r'/data1/public1/Bianzj/base/'
    indir_lai = r'/data1/public1/Bianzj/LAI/%04d//' %int(year)

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
        doy = int(doy_str)
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

        # infileRedN = indir_tif + fileName_str + 'red_n.tif'
        # infileNirN = indir_tif + fileName_str + 'nir_n.tif'
        # infileRedO = indir_tif + fileName_str + 'red_f.tif'
        # infileNirO = indir_tif + fileName_str + 'nir_f.tif'

        infileVzaN = indir_tif + fileName_str + 'vza_n.tif'
        infileVzaO = indir_tif + fileName_str + 'vza_f.tif'
        infileIndx = indir_tif + fileName_str + 'indx.tif'
        infileIndy = indir_tif + fileName_str + 'indy.tif'
        c1 = os.path.exists(infileVzaN)
        c2 = os.path.exists(infileVzaO)
        c3 = os.path.exists(infileIndx)
        c4 = os.path.exists(infileIndy)
        if c1 * c2 * c3 * c4== 0:
            print(fileName + ' lack observation angle data')
            continue

        '''读取数据'''
        [lstN, ns, nl,bands, geog, proj] = read_image_gdal(infileLstN)
        [lstO, width, height, bands, geog, proj] = read_image_gdal(infileLstO)
        lstN = lstN/100
        lstO = lstO/100

        # [redN, width, height, bands, geog, proj] = read_image_gdal(infileRedN)
        # [nirN, width, height, bands, geog, proj] = read_image_gdal(infileNirN)
        # [redO, width, height, bands, geog, proj] = read_image_gdal(infileRedO)
        # [nirO, width, height, bands, geog, proj] = read_image_gdal(infileNirO)
        [vza_n, width, height, bands, geog, proj] = read_image_gdal(infileVzaN)
        [vza_o, width, height, bands, geog, proj] = read_image_gdal(infileVzaO)
        [indx, width, height, bands, geog, proj] = read_image_gdal(infileIndx)
        [indy, width, height, bands, geog, proj] = read_image_gdal(infileIndy)
        vza_n = 90 - (vza_n/100)
        vza_o = 90 - (vza_o/100)
        '''计算FVC'''
        '''读取LAI'''
        doy1 = (doy // 4) * 4 + 1
        doy2 = (doy // 4) * 4 + 5
        infile_lai1 = indir_lai + r"MuSyQ.CSC.LAI.A" + '%04d%03d' % (int(year), doy1) + '.tif'
        infile_lai2 = indir_lai + r"MuSyQ.CSC.LAI.A" + '%04d%03d' % (int(year), doy2) + '.tif'
        if not os.path.exists(infile_lai2): infile_lai2 = infile_lai1
        [lai1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai1)
        [lai2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai2)
        lai = (1 - (doy - doy1) / 4) * lai1[indx, indy] + (doy - doy1) / 4 * lai2[indx, indy]
        lai = np.reshape(lai, [nl, ns])
        lai[lai >= 30000] = 0
        lai = lai / 1000

        fvc_n = cal_fvc_from_lai(vza_n, lai)
        fvc_o = cal_fvc_from_lai(vza_o, lai)

        fvc_n[fvc_n > 1] = 1
        fvc_n[fvc_n < 0] = 0
        fvc_o[fvc_o > 1] = 1
        fvc_o[fvc_o < 0] = 0

        # dif_fvc = fvc_n - fvc_o
        # outfiledfvc = outdir_lsct + fileName_str + '_dfvc.tif'
        # write_image_gdal(dif_fvc, ns, nl, 1, geog, proj, outfiledfvc)


        '''根据lon、lat调整emis'''
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

        lsct_save = np.zeros([nb,ns,512])
        lsct_save[0,:,2:-2] = np.reshape(lsct[:,:,0],[ns,nl])
        lsct_save[1,:,2:-2] = np.reshape(lsct[:,:,1],[ns,nl])

        write_image_gdal(lsct_save, nl, ns+4, nb, geog, proj, outfileLsct)
        print(fileName + '_lsct.tif done')

        # break

