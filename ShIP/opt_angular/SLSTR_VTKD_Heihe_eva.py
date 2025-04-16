import numpy as np

from util.myfun import *
from normalization_temporal.fitting_DTC import *
import time
from pathos.multiprocessing import Pool, cpu_count
import pathos.multiprocessing
from kdinversion import *
from kdmodel import *
from fitting_kernels import *




'''
使用S3A的倾斜与垂直的关系，来判断该拟合关系是否合适；
即原有关系全是从垂直得到的，使用倾斜来试试是否可行
'''


if __name__ =='__main__':
    pathos.multiprocessing.freeze_support()
    # multiprocessing.freeze_support()

    indir_slstr = r'E:\SLSTR_Heihe\\'
    indir_lai = r'E:\lai_heihe1\\'
    indir_vnircoeff = r'E:\SLSTR_Heihe\coeff\\'
    outdir_linkcoeff = r'E:\SLSTR_Heihe\coeff\\'
    kd = 'rosslis'

    days_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    kpixel = 0  # the area for inversion at each
    kinv = 2  # the area for inversion

    '''
    Extract LST results of 9 sites from AHI data in Heihe area
    '''
    infile_loc = r'E:\field\heihe_site.txt'
    mydata = read_txt_str(infile_loc, ',')
    mydata = np.asarray(mydata)
    lon = np.asarray(mydata[:, 1], dtype=np.float16)
    lat = np.asarray(mydata[:, 2], dtype=np.float16)
    infile_ref = r'E:\type\type_heihe_1000.tif'
    dataset = gdal.Open(infile_ref)
    im_width = dataset.RasterXSize * 1
    im_height = dataset.RasterYSize * 1
    im_bands = dataset.RasterCount * 1
    data = dataset.ReadAsArray(0, 0, im_width, im_height)
    im_geotrans = dataset.GetGeoTransform()
    im_proj = dataset.GetProjection()
    # 返回经纬度对应的投影坐标
    temp1, temp2 = lonlat2geo(dataset, lat, lon)
    # 将投影坐标或地理坐标转化为图像坐标，行列号
    imagex_, imagey_ = geo2imagexy(dataset, temp1, temp2)
    imagex_ = np.asarray(imagex_, dtype=np.int16)
    # [270 218 285 226 229 219  54  54  47]
    imagey_ = np.asarray(imagey_, dtype=np.int16)
    # [126  66 155 128 125 132 181 181 176]
    npoint = np.size(imagex_)

    nss = im_width
    nll = im_height
    nbb = 45

    for kmonth0 in range(1,13):
        thedoy = (kmonth0-1)*30+16

        lsts = np.zeros([nbb, nll, nss])
        lstsims = np.zeros([nbb, nll, nss])
        kstep = 0


        infile_fvol1 =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_kvol1.tif'
        infile_fgeo1 =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_kgeo1.tif'
        infile_fiso1 =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_kiso1.tif'
        infile_fvol2 =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_kvol2.tif'
        infile_fgeo2 =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_kgeo2.tif'
        infile_fiso2 =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_kiso2.tif'
        [fvol1, ns, nl, temp, geog, proj] = read_image_gdal(infile_fvol1)
        [fgeo1, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_fgeo1)
        [fiso1, ns, nl, temp, geog, proj] = read_image_gdal(infile_fiso1)
        [fvol2, ns, nl, temp, geog, proj] = read_image_gdal(infile_fvol2)
        [fgeo2, ns, nl, temp, geog, proj] = read_image_gdal(infile_fgeo2)
        [fiso2, ns, nl, temp, geog, proj] = read_image_gdal(infile_fiso2)



        infile_a =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_a.tif'
        infile_b =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_b.tif'
        infile_c =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_c.tif'
        infile_d =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_d.tif'
        infile_e =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_e.tif'
        infile_f =  indir_vnircoeff + '2019%02d_' % (kmonth0) +kd+ '_f.tif'
        [a, ns, nl, temp, geog, proj] = read_image_gdal(infile_a)
        [b, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_b)
        [c, ns, nl, temp, geog, proj] = read_image_gdal(infile_c)
        [d, ns, nl, temp, geog, proj] = read_image_gdal(infile_d)
        [e, ns, nl, temp, geog, proj] = read_image_gdal(infile_e)
        [f, ns, nl, temp, geog, proj] = read_image_gdal(infile_f)

        for kday0 in range(1,32):
            kdoy = date2DOY(2019, kmonth0, kday0)
            # infile_lai = indir_lai + '2019_doy%03d.tif' % kdoy
            # [lai, ns, nl, nb, geog, proj] = read_image_gdal(infile_lai)


            '''S3A NADIR'''
            symbol = 's3a'
            dayNight ='day'
            nadirOblique = 'nadir'
            infile_lst_nadir = indir_slstr + symbol +'\\lst\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_lst_'+nadirOblique+'.tif'
            infile_cloud_nadir = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_cloud_'+nadirOblique+'.tif'
            infile_sza_nadir = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_sza_'+nadirOblique+'.tif'
            infile_vza_nadir = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vza_'+nadirOblique+'.tif'
            infile_saa_nadir = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_saa_'+nadirOblique+'.tif'
            infile_vaa_nadir = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vaa_'+nadirOblique+'.tif'


            nadirOblique = 'obliq'
            infile_lst_obliq = indir_slstr + symbol +'\\lst\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_lst_'+nadirOblique+'.tif'
            infile_cloud_obliq = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_cloud_'+nadirOblique+'.tif'
            infile_sza_obliq = indir_slstr+ symbol  +'\\tif\\'+''+ symbol + '_2019%03d_' % (kdoy) + dayNight+ '_sza_'+nadirOblique+'.tif'
            infile_vza_obliq = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vza_'+nadirOblique+'.tif'
            infile_saa_obliq = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_saa_'+nadirOblique+'.tif'
            infile_vaa_obliq = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_vaa_'+nadirOblique+'.tif'

            infile_rad = indir_slstr+ symbol  +'\\tif\\'+''+ symbol+ '_2019%03d_' % (kdoy) + dayNight+ '_rad'+'.tif'

            if ((os.path.exists(infile_lst_nadir) == 1) & (os.path.exists(infile_lst_obliq) == 1)):
                [lst_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst_nadir)
                            
                [cloud_nadir, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud_nadir)
                [sza_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza_nadir)
                [vza_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_vza_nadir)
                [saa_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa_nadir)
                [vaa_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_vaa_nadir)

                [lst_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst_obliq)
                [cloud_obliq, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud_obliq)
                [sza_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza_obliq)
                [vza_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_vza_obliq)
                [saa_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa_obliq)
                [vaa_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_vaa_obliq)
                [rad, ns, nl, temp, geog, proj] = read_image_gdal(infile_rad)


                ind = (cloud_nadir==0) *(cloud_obliq == 0) *(lst_nadir > 250) *(lst_obliq >  250)
                if np.sum(ind) > nll*nss*0.1:

                    tvol1 = np.zeros([nll,nss])
                    tvol2 = np.zeros([nll,nss])
                    tgeo1 = np.zeros([nll,nss])
                    tgeo2 = np.zeros([nll,nss])
                    tiso1 = np.zeros([nll,nss])
                    tiso2 = np.zeros([nll,nss])
                    lstsim = np.zeros([nll,nss])

                    rad = resize_data_ls(rad,nl0,ns0)
                    raa_nadir = np.abs(vaa_nadir - saa_nadir)
                    raa_obliq = np.abs(vaa_obliq - saa_obliq)

                    indd = (fiso1!=0) | (fiso2 !=0) | (fgeo1 !=0) | (fgeo2 != 0) | (fvol1 != 0) | (fvol2 !=0)
                    tvol1[indd] = fvol1[indd]*kernel_RossThick(vza_nadir[indd],sza_nadir[indd],raa_nadir[indd])
                    tvol2[indd] = fvol2[indd]*kernel_RossThick(vza_obliq[indd],sza_obliq[indd],raa_obliq[indd])
                    tgeo1[indd] = fgeo1[indd]*kernel_LiSparse(vza_nadir[indd],sza_nadir[indd],raa_nadir[indd])
                    tgeo2[indd] = fgeo2[indd]*kernel_LiSparse(vza_obliq[indd],sza_obliq[indd],raa_obliq[indd])
                    tiso1[indd] = fiso1[indd]
                    tiso2[indd] = fiso2[indd]
                    
                    lstsim[indd] = a[indd] * tvol1[indd]*rad[indd] + b[indd] * tvol2[indd]*rad[indd]  + c[indd] * tgeo1[indd]*rad[indd]  + d[indd] * \
                                   tgeo2[indd]*rad[indd]  + e[indd] * tiso1[indd]*rad[indd]  + f[indd] * tiso2[indd]*rad[indd]
                    lstsims[kstep,:] = lstsim
                    lsts[kstep,:] = lst_obliq - lst_nadir
                    kstep = kstep + 1



            '''S3B NADIR'''
            symbol = 's3b'
            dayNight = 'day'
            nadirOblique = 'nadir'
            infile_lst_nadir = indir_slstr + symbol + '\\lst\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_lst_' + nadirOblique + '.tif'
            infile_cloud_nadir = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_cloud_' + nadirOblique + '.tif'
            infile_sza_nadir = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_sza_' + nadirOblique + '.tif'
            infile_vza_nadir = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_vza_' + nadirOblique + '.tif'
            infile_saa_nadir = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_saa_' + nadirOblique + '.tif'
            infile_vaa_nadir = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_vaa_' + nadirOblique + '.tif'

            nadirOblique = 'obliq'
            infile_lst_obliq = indir_slstr + symbol + '\\lst\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_lst_' + nadirOblique + '.tif'
            infile_cloud_obliq = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_cloud_' + nadirOblique + '.tif'
            infile_sza_obliq = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_sza_' + nadirOblique + '.tif'
            infile_vza_obliq = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_vza_' + nadirOblique + '.tif'
            infile_saa_obliq = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_saa_' + nadirOblique + '.tif'
            infile_vaa_obliq = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_vaa_' + nadirOblique + '.tif'

            infile_rad = indir_slstr + symbol + '\\tif\\' + '' + symbol + '_2019%03d_' % (
                kdoy) + dayNight + '_rad' + '.tif'

            if ((os.path.exists(infile_lst_nadir) == 1) & (os.path.exists(infile_lst_obliq) == 1)):
                [lst_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst_nadir)

                [cloud_nadir, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud_nadir)
                [sza_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza_nadir)
                [vza_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_vza_nadir)
                [saa_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa_nadir)
                [vaa_nadir, ns, nl, temp, geog, proj] = read_image_gdal(infile_vaa_nadir)

                [lst_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst_obliq)
                [cloud_obliq, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_cloud_obliq)
                [sza_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza_obliq)
                [vza_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_vza_obliq)
                [saa_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa_obliq)
                [vaa_obliq, ns, nl, temp, geog, proj] = read_image_gdal(infile_vaa_obliq)
                [rad, ns, nl, temp, geog, proj] = read_image_gdal(infile_rad)

                ind = (cloud_nadir == 0) * (cloud_obliq == 0) * (lst_nadir > 250) * (lst_obliq > 250)
                if np.sum(ind) > nll * nss * 0.1:
                    tvol1 = np.zeros([nll, nss])
                    tvol2 = np.zeros([nll, nss])
                    tgeo1 = np.zeros([nll, nss])
                    tgeo2 = np.zeros([nll, nss])
                    tiso1 = np.zeros([nll, nss])
                    tiso2 = np.zeros([nll, nss])
                    lstsim = np.zeros([nll, nss])

                    rad = resize_data_ls(rad, nl0, ns0)
                    raa_nadir = np.abs(vaa_nadir - saa_nadir)
                    raa_obliq = np.abs(vaa_obliq - saa_obliq)

                    indd = (fiso1 != 0) | (fiso2 != 0) | (fgeo1 != 0) | (fgeo2 != 0) | (fvol1 != 0) | (fvol2 != 0)
                    tvol1[indd] = fvol1[indd] * kernel_RossThick(vza_nadir[indd], sza_nadir[indd], raa_nadir[indd])
                    tvol2[indd] = fvol2[indd] * kernel_RossThick(vza_obliq[indd], sza_obliq[indd], raa_obliq[indd])
                    tgeo1[indd] = fgeo1[indd] * kernel_LiSparse(vza_nadir[indd], sza_nadir[indd], raa_nadir[indd])
                    tgeo2[indd] = fgeo2[indd] * kernel_LiSparse(vza_obliq[indd], sza_obliq[indd], raa_obliq[indd])
                    tiso1[indd] = fiso1[indd]
                    tiso2[indd] = fiso2[indd]

                    lstsim[indd] = a[indd] * tvol1[indd]*rad[indd] + b[indd] * tvol2[indd]*rad[indd]  + c[indd] * tgeo1[indd]*rad[indd]  + d[indd] * \
                                   tgeo2[indd]*rad[indd]  + e[indd] * tiso1[indd]*rad[indd]  + f[indd] * tiso2[indd]*rad[indd]

                    lstsims[kstep, :] = lstsim
                    lsts[kstep, :] = lst_obliq - lst_nadir
                    kstep = kstep + 1


        ind = (lsts!=0) *(lstsims!=0)*(lsts <10)*(lsts>-10)*(lstsims<10)*(lstsims>-10)
        dif = lsts[ind] - lstsims[ind]
        bias = np.average(dif)
        rmse = np.sqrt(np.average(dif*dif))
        print(kmonth0,np.sum(ind),bias,rmse)
        #


