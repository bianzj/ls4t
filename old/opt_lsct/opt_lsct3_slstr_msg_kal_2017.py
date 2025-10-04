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

    indir_lstN = r'D:\data\LSCT_kal_2017\slstr\lst\\'
    indir_lstO = r'D:\data\LSCT_kal_2017\slstr\lst\\'
    indir_lstMsg = r'D:\data\LSCT_kal_2017\msg\lst/'
    indir_tif = r'D:\data\LSCT_kal_2017\slstr\tif/'
    indir_lai = r'D:\data\LSCT_kal_2017\lai\lai_Interpolation\\'
    indir_fvc = r'D:\data\LSCT_kal_2017\lai\fvc\\'

    outdir_lsct = r'D:\data\LSCT_kal_2017\lsct\\'

    indir_type = 'd:/data/type/'
    indir_ems = r'D:\data\emis/'

    infile_soil_emis = indir_ems + 'emis1_kal_3000.tif'
    infile_type = indir_type + 'type_kal_3000.tif'
    infile_veg_emis = indir_ems + 'IGBP_Emi.txt'

    [emis_s, emis_v, geog, proj] = readImages_emis(infile_soil_emis, infile_veg_emis, infile_type)
    [type, width_type, height_type, bands, geog, proj] = read_image_gdal(infile_type)

    filesName = search_file_rej(indir_lstN, ['lst_nadir'],'enp')
    filesNum = len(filesName)
    msgFileNames = search_file(indir_lstMsg, ['lst'])

    for fileI in range(filesNum):
        # for fileI in range(243,244):
        fileName = filesName[fileI][:-14]
        doyStr = fileName[-3:]
        yearStr = fileName[4:8]
        doy = int(doyStr)
        year = int(yearStr)
        infileLstN = indir_lstN + fileName + '_lst_nadir.tif'
        infileLstO = indir_lstO + fileName + '_lst_obliq.tif'

        infileTime = indir_tif + fileName + '_time.tif'
        [slstrTime, ns_1000, nl_1000, bands, geog, proj] = read_image_gdal(infileTime)
        slstr_time = slstrTime[int(nl_1000/2),int(ns_1000/2)]
        if slstr_time == 0.0: continue
        hour = math.floor(slstr_time /10000)
        m = math.floor((slstr_time-hour*10000)/100)
        sec = slstr_time % 100
        min = m + sec /60

        if min >= 0 and min < 15:
            f = min/15
            msg_timeStr1 = doyStr + '_' + "%02d" % hour + "00"
            msg_timeStr2 = doyStr + '_' + "%02d" % hour + "15"
        elif min >=15 and min<30:
            f = (min-15)/15
            msg_timeStr1 = doyStr + '_' + "%02d" % hour + "15"
            msg_timeStr2 = doyStr + '_' + "%02d" % hour + "30"
        elif min >=30 and min<45:
            f = (min-30)/15
            msg_timeStr1 = doyStr + '_' + "%02d" % hour + "30"
            msg_timeStr2 = doyStr + '_' + "%02d" % hour + "45"
        elif min >=45 and min<60:
            f = (min-45)/15
            msg_timeStr1 = doyStr + '_' + "%02d" % hour + "45"
            msg_timeStr2 = doyStr + '_' + "%02d" % (hour+1) + "00"

        msgfileArr1 = [msgfile for msgfile in msgFileNames if msg_timeStr1  in msgfile]
        msgfileArr2 = [msgfile for msgfile in msgFileNames if msg_timeStr2  in msgfile]

        infileLstMsg1 = indir_lstMsg + msgfileArr1[0]
        infileLstMsg2 = indir_lstMsg + msgfileArr2[0]
        c1 = os.path.exists(infileLstN)
        c2 = os.path.exists(infileLstO)
        c3 = os.path.exists(infileLstMsg1)
        c4 = os.path.exists(infileLstMsg1)
        if c1 * c2 * c3 *c4 == 0:
            print(fileName + ' lack lst data')
            continue

        infileVzaN = indir_tif + fileName + '_vza_nadir.tif'
        infileVaaN = indir_tif + fileName + '_vaa_nadir.tif'
        infileVzaO = indir_tif + fileName + '_vza_obliq.tif'
        infileVaaO = indir_tif + fileName + '_vaa_obliq.tif'

        infileVaaMsg = r"D:\data\base\msg_angle\\" + "kal_vza.tif"
        infileVzaMsg = r"D:\data\base\msg_angle\\" + "kal_vaa.tif"
        c1 = os.path.exists(infileVzaN)
        c2 = os.path.exists(infileVaaN)
        c3 = os.path.exists(infileVzaO)
        c4 = os.path.exists(infileVaaO)
        if c1 * c2 * c3 * c4 == 0:
            print(fileName + ' lack observation angle data')
            continue

        infileSza = indir_tif + fileName + '_sza_nadir.tif'
        infileSaa = indir_tif + fileName + '_saa_nadir.tif'
        c1 = os.path.exists(infileSza)
        c2 = os.path.exists(infileSaa)
        if c1 * c2 == 0:
            print(fileName + ' lack sun angle data')
            continue

        infileFvcN = indir_fvc + fileName + '_fvcN.tif'
        infileFvcO = indir_fvc + fileName + '_fvcO.tif'
        infileFvcMsg = indir_fvc + fileName + '_fvcMsg.tif'
        c1 = os.path.exists(infileFvcN)
        c2 = os.path.exists(infileFvcO)
        c3 = os.path.exists(infileFvcMsg)
        if c1 * c2 * c3 == 0:
            print(fileName + ' lack fvc data')
            continue

        infileLai = indir_lai + yearStr+'_'+doyStr + '_lai.tif'
        if os.path.exists(infileLai) == 0:
            print(fileName + ' lack LAI data')
            continue

        outfileLsct = outdir_lsct + fileName + '_lsct.tif'
        if os.path.exists(outfileLsct):
            print(fileName + '_lsct.tif exists')
            # continue
        else:
            print(fileName + '_lsct.tif processing...')

        [lstN, width, height, bands, geog, proj] = read_image_gdal(infileLstN)
        [lstO, width, height, bands, geog, proj] = read_image_gdal(infileLstO)
        [lstMsg1, widthMsg, heightMsg, bands, geog, proj] = read_image_gdal(infileLstMsg1)
        [lstMsg2, widthMsg, heightMsg, bands, geog, proj] = read_image_gdal(infileLstMsg2)

        lstMsg = (1-f) * lstMsg1 + f * lstMsg2

        # if(fileName[0:3]=="S3A"):
        #     lstAhi = lstAhi * 0.9727491898535005 + 8.14384409751824
        # else:
        #     lstAhi = lstAhi * 0.9738654689993518 + 7.602965534546172

        pgN = readImages_angle(infileLai, infileVzaN, infileVaaN, infileSza, infileSaa, resample=1)
        pgO = readImages_angle(infileLai, infileVzaO, infileVaaO, infileSza, infileSaa, resample=1)
        pgAhi = readImages_angle(infileLai, infileVzaMsg, infileVaaMsg, infileSza, infileSaa, resample=1)

        [fvcN, width, height, bands, geog, proj] = read_image_gdal(infileFvcN)
        [fvcO, width, height, bands, geog, proj] = read_image_gdal(infileFvcO)
        [fvcMsg, widthMsg, heightMsg, bands, geog, proj] = read_image_gdal(infileFvcMsg)

        fvcMsg = resize_data(fvcMsg,height,width)
        lstMsg = resize_data(lstMsg,height,width)
        emis_v = resize_data(emis_v,height,width)
        emis_s = resize_data(emis_s, height, width)
        lsct = inv_mpl_agl_multiple_msg(lstN, lstO, lstMsg, emis_s, emis_v, fvcN, fvcO, fvcMsg, pgN, pgO, pgAhi, wl=10.8)
        lsct_out = np.zeros([3,heightMsg,widthMsg])
        lsct_out[0] = resize_data(lsct[0],heightMsg,widthMsg)
        lsct_out[1] = resize_data(lsct[1],heightMsg,widthMsg)
        lsct_out[2] = resize_data(lsct[2],heightMsg,widthMsg)
        [ns, nl, nb] = np.shape(lsct_out)
        # lsct,lsct_window,lsct_point = inv_mpl_agl_multiple(lstN, lstO, lstAhi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pgN, pgO, pgAhi, wl=10.8)
        # [ns, nl, nb] = np.shape(lsct)
        if (np.sum(lsct) == 0):
            print(fileName + '_lsct.tif' + ' no result')
            continue
        write_image_gdal(lsct_out, ns, nl, nb, geog, proj, outfileLsct)
        # outfileLsct_window = outdir_lsct_window + fileName+ '_lsct_window.tif'
        # outfileLsct_point = outdir_lsct_point + fileName+ '_lsct_point.tif'
        # write_image_gdal(lsct_window, ns, nl, nb, geog, proj, outfileLsct_window)
        # write_image_gdal(lsct_point, ns, nl, nb, geog, proj, outfileLsct_point)
        print(fileName + '_lsct.tif done')
