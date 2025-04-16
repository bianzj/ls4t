import numpy as np
from scipy import interpolate
import matplotlib.mlab as ml
import matplotlib.pyplot as plt
import time
from util.util import *
from util_lsct import *
from multiprocessing import Pool
import warnings
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

### forest and crop
# lat_ =np.asarray([38.848909,38.853457])
# lon_ = np.asarray([100.371799,100.371343])
lat_ =np.asarray([38.853457])
lon_ = np.asarray([100.371343])

def list2onearray(list):
    result = np.asarray(list)
    result = result.flatten()
    return result

infile_type = r'D:\data\type\type_heihe_1000_new.tif'
type, ns, nl, nb, geog, proj,dataset = read_image_dataset_gdal(infile_type)
imagex_,imagey_ = loc2map(lat_,lon_,dataset)
outfile = r'D:\data\LSCT\lst.txt'

if __name__ == '__main__':

    indir_lstN = r'D:\data\LSCT\slstr_2022\lst2/'
    indir_lstO = r'D:\data\LSCT\slstr_2022\lst2/'
    indir_lstAhi = r'D:\data\LSCT\ahi_2022\lst2/'
    indir_tif = r'D:\data\LSCT\slstr_2022\tif/'
    indir_tif_ahi = r"D:\data\LSCT\ahi_2022\tif\\"
    indir_lai = r'D:\data\lai\MCD_TIF\lai/'
    indir_fvcN = r'D:\data\lai\MCD_TIF\fvc/'
    indir_fvcO = r'D:\data\lai\MCD_TIF\fvc/'
    indir_fvcAhi = r'D:\data\lai\MCD_TIF\fvc/'

    indir_type = 'd:/data/type/'
    indir_ems = r'D:\data\emis/'

    filesName = search_file(indir_lstN, ['nadir', 'lst'])
    filesNum = len(filesName)
    ahiFileNames = search_file(indir_lstAhi, ['lst'])
    lst_N_ = []
    lst_O_ = []
    lst_A_ = []
    time_ = []
    doy_ = []
    saa_ = []
    sza_ = []
    vaa_n_ = []
    vza_n_ = []
    vaa_o_ = []
    vza_o_ = []
    vaa_a_ = []
    vza_a_ = []
    pgn_ = []
    pgo_ =[]
    pga_ = []
    fvc_n_ = []
    fvc_o_ = []
    fvc_a_ = []
    bt_n_ = []
    bt_o_ = []
    bt_a_ = []


    for fileI in range(filesNum):
        # for fileI in range(243,244):
        fileName = filesName[fileI][:-18]
        doyStr = fileName[-3:]
        infileLstN = indir_lstN + fileName + '_day_lst_nadir.tif'
        infileLstO = indir_lstO + fileName + '_day_lst_obliq.tif'
        ahifileArr = [ahifile for ahifile in ahiFileNames if doyStr+"_" in ahifile]
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
        infileSza = indir_tif + fileName + '_day_sza_nadir.tif'
        infileSaa = indir_tif + fileName + '_day_saa_nadir.tif'
        infileVzaAhi = r'D:\data\base\ahi_angle_2022\AHI_VZA_HEIHE_cut.tif'
        infileVaaAhi = r'D:\data\base\ahi_angle_2022\AHI_VAA_HEIHE_cut.tif'
        infileLai = indir_lai + fileName + '_lai.tif'

        infilebt1_n = indir_tif + fileName + '_day_bt1_nadir.tif'
        infilebt2_n = indir_tif + fileName + '_day_bt2_nadir.tif'
        infilebt1_o = indir_tif + fileName + '_day_bt1_obliq.tif'
        infilebt2_o = indir_tif + fileName + '_day_bt2_obliq.tif'
        infilebt1_a_1 = indir_tif_ahi + ahiFileName1 + 'bt1.tif'
        infilebt2_a_1 = indir_tif_ahi + ahiFileName1 + 'bt2.tif'
        infilebt1_a_2 = indir_tif_ahi + ahiFileName2 + 'bt1.tif'
        infilebt2_a_2 = indir_tif_ahi + ahiFileName2 + 'bt2.tif'
        [bt1_n, width, height, bands, geog, proj] = read_image_gdal(infilebt1_n)
        [bt2_n, width, height, bands, geog, proj] = read_image_gdal(infilebt2_n)
        [bt1_o, width, height, bands, geog, proj] = read_image_gdal(infilebt1_o)
        [bt2_o, width, height, bands, geog, proj] = read_image_gdal(infilebt2_o)
        [bt1_a_1, width, height, bands, geog, proj] = read_image_gdal(infilebt1_a_1)
        [bt2_a_1, width, height, bands, geog, proj] = read_image_gdal(infilebt2_a_1)
        [bt1_a_2, width, height, bands, geog, proj] = read_image_gdal(infilebt1_a_2)
        [bt2_a_2, width, height, bands, geog, proj] = read_image_gdal(infilebt2_a_2)
        bt_n = (bt1_n+bt2_n)/2
        bt_o = (bt1_o + bt2_o) / 2
        bt_a_1 = (bt1_a_1+bt2_a_1)/2
        bt_a_2 = (bt1_a_2+bt2_a_2)/2

        # if int(doyStr)!= 202: continue
        infile_time = indir_tif + fileName + '_day_time.tif'
        [lstN, width, height, bands, geog, proj] = read_image_gdal(infileLstN)
        [lstO, width, height, bands, geog, proj] = read_image_gdal(infileLstO)
        [lstAhi1, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileLstAhi1)
        [lstAhi2, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileLstAhi2)
        [slstrTime, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infile_time)
        lstAhi1 = resize_data(lstAhi1,nl,ns)
        lstAhi2 = resize_data(lstAhi2, nl, ns)
        time_.append(slstrTime[imagex_,imagey_])

        ahiTime1 = ahiTime1 // 100 * 60 + ahiTime1 % 100
        ahiTime2 = ahiTime2 // 100 * 60 + ahiTime2 % 100
        slstrTime = (slstrTime[imagex_,imagey_] / 100)
        slstrTime = slstrTime // 100 * 60 + slstrTime % 100
        lstAhi = np.abs((slstrTime - ahiTime2) / 10) * lstAhi1 + np.abs((slstrTime - ahiTime1) / 10) * lstAhi2
        bt_a = np.abs((slstrTime - ahiTime2) / 10) * bt_a_1 + np.abs((slstrTime - ahiTime1) / 10) * bt_a_2
        bt_a = resize_data(bt_a,nl,ns)

        if (fileName[0:3] == "S3A"):
            lstAhi = lstAhi * 0.9727491898535005 + 8.14384409751824
        else:
            lstAhi = lstAhi * 0.9738654689993518 + 7.602965534546172


        infileFvcN = indir_fvcN + fileName + '_fvcN.tif'
        infileFvcO = indir_fvcO + fileName + '_fvcO.tif'
        infileFvcAhi = indir_fvcAhi + fileName + '_fvcAhi.tif'

        [sza, ns, nl, nb, geog, proj] = read_image_gdal(infileSza)
        [saa, ns, nl, nb, geog, proj] = read_image_gdal(infileSaa)
        [vza_n, ns, nl, nb, geog, proj] = read_image_gdal(infileVzaN)
        [vaa_n, ns, nl, nb, geog, proj] = read_image_gdal(infileVaaN)
        [vza_o, ns, nl, nb, geog, proj] = read_image_gdal(infileVzaO)
        [vaa_o, ns, nl, nb, geog, proj] = read_image_gdal(infileVaaO)
        [vza_a, ns, nl, nb, geog, proj] = read_image_gdal(infileVzaAhi)
        [vaa_a, ns, nl, nb, geog, proj] = read_image_gdal(infileVaaAhi)
        [fvc_n, ns, nl, nb, geog, proj] = read_image_gdal(infileFvcN)
        [fvc_o, ns, nl, nb, geog, proj] = read_image_gdal(infileFvcO)
        [fvc_a, ns, nl, nb, geog, proj] = read_image_gdal(infileFvcAhi)



        pgN = readImages_angle(infileLai, infileVzaN, infileVaaN, infileSza, infileSaa, resample=1)
        pgO = readImages_angle(infileLai, infileVzaO, infileVaaO, infileSza, infileSaa, resample=1)
        pgAhi = readImages_angle(infileLai, infileVzaAhi, infileVaaAhi, infileSza, infileSaa, resample=1)
        doy = np.int_(fileName[8:11])
        doy_.append(doy)
        lst_N_.append(lstN[imagex_,imagey_])
        lst_O_.append(lstO[imagex_,imagey_])
        lst_A_.append(lstAhi[imagex_,imagey_])

        vza_n_.append(vza_n[imagex_,imagey_])
        vza_o_.append(vza_o[imagex_, imagey_])
        vza_a_.append(vza_a[imagex_, imagey_])
        vaa_n_.append(vaa_n[imagex_,imagey_])
        vaa_o_.append(vaa_o[imagex_, imagey_])
        vaa_a_.append(vaa_a[imagex_, imagey_])
        saa_.append(saa[imagex_, imagey_])
        sza_.append(sza[imagex_, imagey_])
        pgn_.append(pgN[imagex_,imagey_])
        pgo_.append(pgO[imagex_, imagey_])
        pga_.append(pgAhi[imagex_, imagey_])
        fvc_n_.append(fvc_n[imagex_, imagey_])
        fvc_o_.append(fvc_o[imagex_, imagey_])
        fvc_a_.append(fvc_a[imagex_, imagey_])
        bt_n_.append(bt_n[imagex_,imagey_])
        bt_o_.append(bt_o[imagex_, imagey_])
        bt_a_.append(bt_a[imagex_, imagey_])

time_ = list2onearray(time_)
lst_N_ = list2onearray(lst_N_)
lst_O_ = list2onearray(lst_O_)
lst_A_ = list2onearray(lst_A_)
sza_ = list2onearray(sza_)
saa_ = list2onearray(saa_)
vza_n_ = list2onearray(vza_n_)
vaa_n_ = list2onearray(vaa_n_)
vza_o_ = list2onearray(vza_o_)
vaa_o_ = list2onearray(vaa_o_)
vza_a_ = list2onearray(vza_a_)
vaa_a_ = list2onearray(vaa_a_)
pgn_ = list2onearray(pgn_)
pgo_ = list2onearray(pgo_)
pga_ = list2onearray(pga_)
fvc_n_ = list2onearray(fvc_n_)
fvc_o_ = list2onearray(fvc_o_)
fvc_a_ = list2onearray(fvc_a_)
bt_n_ = list2onearray(bt_n_)
bt_o_ = list2onearray(bt_o_)
bt_a_ = list2onearray(bt_a_)

result = np.vstack([doy_,time_,lst_N_,lst_O_,lst_A_,sza_,saa_,vza_n_,vaa_n_,vza_o_,vaa_o_,vza_a_,vaa_a_,pgn_,pgo_,pga_,fvc_n_,fvc_o_,fvc_a_,bt_n_,bt_o_,bt_a_])
result = np.transpose(result)
np.savetxt(outfile,result,fmt='%.3f')

