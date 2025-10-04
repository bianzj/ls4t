import cv2

from util.util import *
from opt_lsct.util_lsct import *
import warnings
warnings.filterwarnings("ignore")


def cal_FVC_from_NDVI(red,NIR,ndvi_min=0.05,ndvi_max = 0.95):
    [nl,ns] = np.shape(red)
    ndvi = np.zeros([nl,ns])
    ind = red > 0
    ndvi[ind] = (NIR[ind]-red[ind])/(NIR[ind]+red[ind])
    fvc = (ndvi-ndvi_min)/(ndvi_max-ndvi_min)
    return fvc

def cal_LAI_from_FVC(fvc,vza,G=0.5):
    # fvc = np.exp(-LAI*G/np.cos(vza))
    thetav = np.cos(vza*rd)
    lai = -np.log(1-fvc)/G*thetav
    return lai


# 3 observations from slstr + ahi for 3 components
if __name__ == '__main__':


    indir_lstN = r'E:\slstr_2022\lst/'
    indir_lstO = r'E:\slstr_2022\lst/'
    indir_lstAhi = r'E:\ahi_2022\lst/'
    indir_tif = r'E:\slstr_2022\tif//'
    indir_tifAhi =  r'E:\ahi_2022\tif/'
    # indir_fvcN = r'D:\data\fvc\fvc_china\fvc_china_n/'
    # indir_fvcO = r'D:\data\fvc\fvc_china\fvc_china_o/'
    # indir_fvcAhi = r'D:\data\fvc\fvc_china\fvc_china_ahi/'
    # indir_lai = r'D:\data\lai\lai_china/'

    outdir_lsct = r'E:\slstr_2022\lsct3/'

    indir_type = 'e:/type/'
    indir_ems = r'e:\emis/'

    infile_soil_emis = indir_ems + 'emis1_polar_heihe_1000_zhong.tif'
    infile_type = indir_type + 'type_heihe_1000_zhong.tif'
    infile_veg_emis = indir_ems + 'IGBP_Emi.txt'

    [emis_s,emis_v,geog,proj] = readImages_emis(infile_soil_emis, infile_veg_emis, infile_type)
    [type, width, height, bands, geog, proj] = read_image_gdal(infile_type)

    filesName = search_file(indir_lstN, ['day','nadir','lst'])
    filesNum = np.size(filesName)

    ahiFileNames = search_file(indir_lstAhi,['lst'])

    for fileI in range(filesNum):
        fileName = filesName[fileI][:-18]
        doyStr = fileName[-3:]
        infileLstN = indir_lstN + fileName + '_day_lst_nadir.tif'
        infileLstO = indir_lstO + fileName + '_day_lst_obliq.tif'
        # infileLstAhi = indir_lstAhi + fileName + '_day_lst.tif'

        ahifileArr = [ahifile for ahifile in ahiFileNames if doyStr in ahifile ]
        if np.size(ahifileArr)<=0:continue
        ahiFileName = ahifileArr[0][:-7]
        infileLstAhi = indir_lstAhi+ahiFileName+'lst.tif'

        print(infileLstAhi)
        print(infileLstN)
        print(infileLstO)
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
        infileRedN = indir_tif + fileName + '_day_red_nadir.tif'
        infileNirN = indir_tif + fileName + '_day_nir_nadir.tif'
        infileRedO = indir_tif + fileName + '_day_red_obliq.tif'
        infileNirO = indir_tif + fileName + '_day_nir_obliq.tif'

        infileRedA =  indir_tifAhi + ahiFileName+'red.tif'
        infileNirA =  indir_tifAhi + ahiFileName+'nir.tif'

        infileVzaAhi = r'E:\map\vza_heihe_2000_zhong.tif'
        infileVaaAhi = r'E:\map\vaa_heihe_2000_zhong.tif'
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

        '''This is for the simple version with only VNIR observations'''
        [redN, width, height, bands, geog, proj] = read_image_gdal(infileRedN)
        nl = height
        ns = width
        [redO, width, height, bands, geog, proj] = read_image_gdal(infileRedO)
        [redA, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileRedA)
        [nirN, width, height, bands, geog, proj] = read_image_gdal(infileNirN)
        [nirO, width, height, bands, geog, proj] = read_image_gdal(infileNirO)
        [nirA, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileNirA)

        fvcN = cal_FVC_from_NDVI(redN,nirN)
        fvcO = cal_FVC_from_NDVI(redO,nirO)
        fvcAhi = cal_FVC_from_NDVI(redA,nirA)
        print(np.min(fvcN),np.max(fvcN))
        # fvcAhi = resize_data_near(fvcAhi,nl,ns)
        '''This is for the LAI and FVC version'''
        # infileFvcN = indir_fvcN + '2019_doy' + doyStr + '_fvc.tif'
        # infileFvcO = indir_fvcO + '2019_doy' + doyStr + '_fvc.tif'
        # infileFvcAhi = indir_fvcAhi + '2019_doy' + doyStr + '_fvc.tif'
        # c1 = os.path.exists(infileFvcN)
        # c2 = os.path.exists(infileFvcO)
        # c3 = os.path.exists(infileFvcAhi)
        # if c1 * c2 * c3 == 0:
        #     print(fileName + ' lack fvc data')
        #     continue
        #
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
        [lstAhi, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileLstAhi)
        # lstAhi = resize_data_near(lstAhi,nl,ns)

        [vzaN, width, height, bands, geog, proj] = read_image_gdal(infileVzaN)
        [vzaO, width, height, bands, geog, proj] = read_image_gdal(infileVzaO)
        [vzaA, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileVzaAhi)
        [vaaN, width, height, bands, geog, proj] = read_image_gdal(infileVaaN)
        [vaaO, width, height, bands, geog, proj] = read_image_gdal(infileVaaO)
        [vaaA, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileVaaAhi)
        [sza, width, height, bands, geog, proj] = read_image_gdal(infileSza)
        [saa, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileSaa)

        lai  = cal_LAI_from_FVC(fvcN,vzaN)

        pgN,ind = cal_hotspot(lai,vzaN,vaaN,sza,saa)
        pgO,ind = cal_hotspot(lai,vzaO,vaaO,sza,saa)
        vzaA = resize_data(vzaA, nl, ns,method=cv2.INTER_NEAREST)
        vaaA = resize_data(vaaA, nl, ns,method=cv2.INTER_NEAREST)
        pgAhi,ind = cal_hotspot(lai,vzaA,vaaA,sza,saa)
        pgAhi = resize_data(pgAhi,nl/2,ns/2,method=cv2.INTER_NEAREST)
        # pgN = file2Array_hotspot(infileLai, infileVzaN, infileVaaN, infileSza, infileSaa, resample=1)
        # pgO = file2Array_hotspot(infileLai, infileVzaO, infileVaaO, infileSza, infileSaa, resample=1)
        # pgAhi = file2Array_hotspot(infileLai, infileVzaAhi, infileVaaAhi, infileSza, infileSaa, resample=2)
        #
        # [fvcN, width, height, bands, geog, proj] = read_image_gdal(infileFvcN)
        # [fvcO, width, height, bands, geog, proj] = read_image_gdal(infileFvcO)
        # [fvcAhi, widthAhi, heightAhi, bands, geog, proj] = read_image_gdal(infileFvcAhi)


        lsct = inv_mpl_agl_multiple(lstN, lstO, lstAhi,emis_s, emis_v, fvcN, fvcO, fvcAhi,pgN,pgO,pgAhi, wl=10.8)
        [ns, nl, nb] = np.shape(lsct)
        if (np.sum(lsct) == 0):
            print(fileName + '_lsct.tif' + ' no result')
            continue
        write_image_gdal(lsct, ns, nl, nb, geog, proj, outfileLsct)
        print(fileName + '_lsct.tif done')
