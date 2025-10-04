import netCDF4
import time
from util.util_constant import *
from util.util import *
import warnings
warnings.filterwarnings("ignore")

'''slstr垂直观测角度数据解析'''
'''根据slstr的下载数据，读取所需要的数据，包括亮度温度，红、近红外发射率，观测几何，云掩膜'''
'''SLSTR 和modis数据处理的思路一样，但是数据格式不同'''
'''
1. 先提出出来成tif
2. gdal进行投影转换
3. 研究区重采样
'''

'''注意：不同时区一定要调day、night symbol'''

def ifallfilesexists(fileDir):
    infile = fileDir + r'\S2_radiance_an.nc'
    c1 = os.path.exists(infile)
    infile = fileDir + r'\geodetic_in.nc'
    c2 = os.path.exists(infile)
    infile = fileDir + r'\met_tx.nc'
    c4 = os.path.exists(infile)
    infile = fileDir + r'\S6_radiance_an.nc'
    c5 = os.path.exists(infile)
    infile = fileDir + r'\S8_BT_in.nc'
    c6 = os.path.exists(infile)
    return c1 * c2 * c4 * c5 * c6

def getDatafromNc(fileName, objectName):
    try:
        dataset = netCDF4.Dataset(fileName)
    except (OSError, RuntimeError):
        print(fileName + ' File Error')
        predata = np.asarray(None)
    else:
        try:
            predata = np.asarray(dataset.variables[objectName][:])
        except RuntimeError:
            print(fileName + ' Attribute Error')
            predata = np.asarray(None)
        finally:
            dataset.close();
    return predata

def resize_file(infile, outfile, f=2):
    [preArray, im_width, im_height, im_bands, im_geotrans, im_proj] = read_image_gdal(infile)
    ns = im_width * f
    nl = im_height * f
    data = cv2.resize(preArray, (ns, nl), interpolation=cv2.INTER_BITS)
    write_image_gdal(data, ns, nl, 1, im_geotrans, im_proj, outfile)
    return data

def resizefromSmall2Image(ifnadir, preArray):
    if (ifnadir == 1):
        newArray = cv2.resize(preArray[:, adjust_xmin_n_g:adjust_xmax_n_g],
                              (ns_nadir_g, nl_nadir_g), cv2.INTER_NEAREST)
    else:
        newArray = cv2.resize(preArray[:, adjust_xmin_o_g:adjust_xmax_o_g],
                              (ns_obliq_g, nl_obliq_g), cv2.INTER_NEAREST)
    return newArray

def getVNIRdatafromNc(fileDir, outDir):
    '''mask'''
    ns = ns_nadir_g
    nl = nl_nadir_g

    # get red data_satellite
    fileName = fileDir + '\\S2_radiance_an.nc'
    objectName = r'S2_radiance_an'
    rad_red = getDatafromNc(fileName, objectName)
    fileName = fileDir + '\\S2_quality_an.nc'
    objectName = r'S2_solar_irradiance_an'
    sr_red = getDatafromNc(fileName, objectName)

    # get nir data_satellite
    fileName = fileDir + '\\S3_radiance_an.nc'
    objectName = r'S3_radiance_an'
    rad_nir = getDatafromNc(fileName, objectName)
    fileName = fileDir + '\\S3_quality_an.nc'
    objectName = r'S3_solar_irradiance_an'
    sr_nir = getDatafromNc(fileName, objectName)

    # if not (rad_red.all() and sr_red.all() and rad_nir.all() and sr_nir.all()):
    #     return 0;

    refl_red = rad_red / (sr_red[0] / np.pi)
    refl_nir = rad_nir / (sr_nir[0] / np.pi)


    # outfile = fileDir + '\\red.tif'
    refl_red = resize_data(refl_red, nl, ns)
    outfile = outDir + 'red.tif'
    write_image_gdal(refl_red[:nl, :ns], ns, nl, 1, '', '', outfile)

    # outfile = fileDir + '\\nir.tif'
    refl_nir = resize_data(refl_nir, nl, ns)
    outfile = outDir + 'nir.tif'
    write_image_gdal(refl_nir[:nl, :ns], ns, nl, 1, '', '', outfile)

    return 1

def getGeodatafromNc(fileDir, outDir):
    # get red data_satellite

    ns = ns_nadir_g
    nl = nl_nadir_g

    '''zenith and azimuth'''
    fileName = fileDir + '\\geometry_tn.nc'
    objectName = r'sat_zenith_tn'
    vza = getDatafromNc(fileName, objectName)
    objectName = r'solar_zenith_tn'
    sza = getDatafromNc(fileName, objectName)
    objectName = r'sat_azimuth_tn'
    vaa = getDatafromNc(fileName, objectName)
    objectName = r'solar_azimuth_tn'
    saa = getDatafromNc(fileName, objectName)
    # psi = np.abs(vaa - saa)
    if not (vza.any() and sza.all() and vaa.all() and saa.all()):
        return 0;
    vza = resizefromSmall2Image(1, vza)
    sza = resizefromSmall2Image(1, sza)
    vaa = resizefromSmall2Image(1, vaa)
    saa = resizefromSmall2Image(1, saa)
    # psi = resizefromSmall2Image(1, psi)
    # psi[psi > 180] = 360 - psi[psi > 180]

    # # outfile = fileDir + '\\vza.tif'
    outfile = outDir + 'vza.tif'
    write_image_gdal(vza[:nl, :ns], ns, nl, 1, '', '', outfile)
    # outfile = fileDir + '\\sza.tif'
    outfile = outDir + 'sza.tif'
    write_image_gdal(sza[:nl, :ns], ns, nl, 1, '', '', outfile)
    # # outfile = fileDir + '\\psi.tif'
    # # write_image_gdal(psi[:nl, :ns], ns, nl, 1, '', '', outfile)

    # outfile = fileDir + '\\vaa.tif'
    outfile = outDir + 'vaa.tif'
    write_image_gdal(vaa[:nl, :ns], ns, nl, 1, '', '', outfile)
    # outfile = fileDir + '\\saa.tif'
    outfile = outDir + 'saa.tif'
    write_image_gdal(saa[:nl, :ns], ns, nl, 1, '', '', outfile)

    '''lon and lat'''
    fileName = fileDir + '\\geodetic_in.nc'
    objectName = r'latitude_in'
    lat = getDatafromNc(fileName, objectName)

    fileName = fileDir + '\\geodetic_in.nc'
    objectName = r'longitude_in'
    lon = getDatafromNc(fileName, objectName)

    if not (lat.all() and lon.all()):
        return 0
    #
    outfile = outDir + 'lat.tif'
    write_image_gdal(lat[:nl, :ns], ns, nl, 1, '', '', outfile)
    #
    # # lat2 = resize_data(lat[:nl,:ns],2)
    # # # outfile = fileDir + '\\lat_v.tif'
    # # outfile = outDir + 'lat_v.tif'
    # # write_image_gdal(lat2, ns*2, nl*2, 1, '', '', outfile)
    #
    # # outfile = fileDir + '\\lon.tif'
    outfile = outDir + 'lon.tif'
    write_image_gdal(lon[:nl, :ns], ns, nl, 1, '', '', outfile)
    #
    # # lon2 = resize_data(lon[:nl,:ns],2)
    # # # outfile = fileDir + '\\lon_v.tif'
    # # outfile = outDir + 'lon_v.tif'
    # # write_image_gdal(lon2, ns*2, nl*2, 1, '', '', outfile)
    #
    '''cloud'''
    fileName = fileDir + '\\flags_in.nc'
    objectName = r'cloud_in'
    cloud = getDatafromNc(fileName, objectName)

    outfile = outDir + 'cloud.tif'
    write_image_gdal(cloud[:nl, :ns], ns, nl, 1, '', '', outfile)

    return 1

def getTIRdatafromNc(fileDir, outDir):

    fileName = fileDir + '\\S8_BT_in.nc'
    objectName = r'S8_BT_in'
    BT8 = getDatafromNc(fileName, objectName)


    fileName = fileDir + '\\S9_BT_in.nc'
    objectName = r'S9_BT_in'
    BT9 = getDatafromNc(fileName, objectName)

    if not (BT8.all() and BT9.all()):
        return 0;

    BT8 = BT8[:nl_nadir_g, :]
    BT9 = BT9[:nl_nadir_g, :]


    # outfile = fileDir + '\\bt8.tif'
    outfile = outDir + 'bt8.tif'
    write_image_gdal(BT8, ns_nadir_g, nl_nadir_g, 1, '', '', outfile)

    # # outfile = fileDir + '\\bt9.tif'
    outfile = outDir + 'bt9.tif'
    write_image_gdal(BT9, ns_nadir_g, nl_nadir_g, 1, '', '', outfile)

    return 1

def writevrt_nadir(infile, datafile, xfile, yfile):
    write_vrt(infile, datafile, xfile, yfile, 1500, 1200)
    return 1

def writevrt_obliq(infile, datafile, xfile, yfile):
    write_vrt(infile, datafile, xfile, yfile, 900, 1200)
    return 1

def writevrt_v_nadir(infile, datafile, xfile, yfile):
    write_vrt(infile, datafile, xfile, yfile, 3000, 2400)
    return 1

def writevrt_v_obliq(infile, datafile, xfile, yfile):
    write_vrt(infile,datafile,xfile,yfile,1800,2400)
    return 1

###



##############################################
######## Examples
##############################################
# 535 FOR s3a
indir_raw = r'D:\data\data_download\Sentinel3\test\s3_raw\\'
indir_med = r'D:\data\data_download\Sentinel3\test\s3_med2\\'
indir_tif = r'D:\data\data_download\Sentinel3\test\s3_tif2\\'
symbol = 'S3B'

# indir_raw = r'H:\S3B_RAW\2019_06\\'
# indir_med = r'd:\data\S3B_temp\direct\2019_06\\'
# indir_tif = r'd:\data\S3B_tif\\'
# symbol = 'S3B'

ifunzipNC = 1
ifproj = 1
ifresample = 1
# targetArea = r'D:\data\type\\type_kal_1000.tif'
targetArea = r'D:\data\data_download\Sentinel3\s3_beijing\\type_beijing_1000.tif'

dataset = gdal.Open(targetArea)
if dataset == None:
    print(targetArea + " ")
ns = dataset.RasterXSize
nl = dataset.RasterYSize
im_bands = dataset.RasterCount
data = dataset.ReadAsArray(0, 0, ns, nl)
geog = dataset.GetGeoTransform()
proj = dataset.GetProjection()
nsi = np.zeros([nl, ns])
nli = np.zeros([nl, ns])
for k in range(nl):
    nli[k, :] = k
    nsi[k, :] = np.linspace(0, ns - 1, ns)
nli = np.reshape(nli,-1)
nsi = np.reshape(nsi,-1)
temp1,temp2= imagexy2geo(dataset,nli,nsi)
lon,lat = geo2lonlat(dataset,temp1,temp2)
dataset = None

fileNames = search_dir_rej(indir_raw,[symbol],'zip')
fileNum = len(fileNames)
### 446 KAISHI
for k in range(0,fileNum):
    fileName = fileNames[k].strip()
    month = np.int(fileName[20:22])
    day = np.int(fileName[22:24])
    doy = date2DOY(2019, month, day)
    time_str = fileName[25:25 + 6]
    hh = np.int(np.uint(time_str[0:2]))
    mm = np.int(np.uint(time_str[2:4]))

    ## for day data_satellite
    if hh > 22 or hh < 11:
        dayNight = 'day'
    else:
        dayNight = 'night'
    print(hh)
    # if hh > 6 and hh < 19:
    #     dayNight = 'day'
    # else:
    #     dayNight = 'night'

    # if doy < 178:continue
    # if doy > 181:continue

    ###############################
    ### from NC to tif images
    ###############################




    if ifunzipNC == 1:
        fileName = fileNames[k].strip()
        fileDir = indir_raw + fileName + '\\'
        # fileDir = indir_raw + fileName
        print(k, fileDir)
        ccc = ifallfilesexists(fileDir)
        if(ccc==0):continue
        '''if(os.path.exists(fileDir+'/lon_v.tif')==1):
            continue'''
        temp1 = getVNIRdatafromNc(fileDir, indir_med)
        temp2 = getTIRdatafromNc(fileDir, indir_med)
        temp3 = getGeodatafromNc(fileDir, indir_med)

        if not (temp1 and temp2 and temp3):
             continue

    ###############################
    ### tif images projected to WGS 84 and resamppled to target study area
    ###############################

    if ifproj == 1:
        '''zenith and azimuth'''
        date_str = fileName[16:8 + 16]
        year = np.int(np.uint(date_str[:4]))
        month = np.int(np.uint(date_str[4:6]))
        day = np.int(np.uint(date_str[6:8]))
        doy = date2DOY(year, month, day)
        time_str = fileName[25:25 + 6]
        hh = np.int(np.uint(time_str[0:2]))
        mm = np.int(np.uint(time_str[2:4]))
        outfile0 = symbol + '_%4d' % year + '%03d' % doy + '_%02d' % hh + '%02d' % mm + '_'



        file = 'vza'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_nadir(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''cloud'''
        file = 'cloud'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_nadir(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        '''TIR'''

        file = 'bt8'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_nadir(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)
        # #
        file = 'bt9'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        writevrt_nadir(vrtfile, datafile, xfile, yfile)
        outfile = indir_med + file + '_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        if dayNight == 'day':

            file = 'sza'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            writevrt_nadir(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)
            #

            file = 'vaa'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            writevrt_nadir(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)
            #
            file = 'saa'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            writevrt_nadir(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)


            #
            '''VNIR'''
            file = 'red'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            writevrt_nadir(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            file = 'nir'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            writevrt_nadir(vrtfile, datafile, xfile, yfile)
            outfile = indir_med + file + '_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

    if ifresample == 1:
        date_str = fileName[16:8 + 16]
        year = np.int(np.uint(date_str[:4]))
        month = np.int(np.uint(date_str[4:6]))
        day = np.int(np.uint(date_str[6:8]))
        doy = date2DOY(year, month, day)
        time_str = fileName[25:25 + 6]
        hh = np.int(np.uint(time_str[0:2]))
        mm = np.int(np.uint(time_str[2:4]))
        infile0 = symbol + '_%4d' % year + '%03d' % doy + '_%02d' % hh + '%02d' % mm + '_'
        outfile0 = symbol + '_%4d' % year + '%03d' % doy + '_'



        outfile1 = indir_tif + outfile0 + dayNight + '_bt1_nadir.tif'
        outfile2 = indir_tif + outfile0 + dayNight + '_bt2_nadir.tif'
        outfile3 = indir_tif + outfile0 + dayNight + '_red_nadir.tif'
        outfile4 = indir_tif + outfile0 + dayNight + '_nir_nadir.tif'
        outfile5 = indir_tif + outfile0 + dayNight + '_vza_nadir.tif'
        outfile6 = indir_tif + outfile0 + dayNight + '_sza_nadir.tif'
        outfile8 = indir_tif + outfile0 + dayNight + '_time.tif'
        outfile9 = indir_tif + outfile0 + dayNight + '_vaa_nadir.tif'
        outfile10 = indir_tif + outfile0 + dayNight + '_saa_nadir.tif'
        outfile11 = indir_tif + outfile0 + dayNight + '_cloud_nadir.tif'

        if os.path.exists(outfile1) == 1:
            [data1, temp1, temp2, temp3, geog, proj] = read_image_gdal(outfile1)
            [data2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile2)
            [data5, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile5)
            [data8, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile8)
            [data11, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile11)

            if dayNight =='day':

                [data3, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile3)
                [data4, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile4)
                [data6, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile6)
                [data9, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile9)
                [data10, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile10)

        else:
            data1 = np.zeros([nl, ns])
            data2 = np.zeros([nl, ns])
            data5 = np.zeros([nl, ns])
            data11 = np.zeros([nl, ns])
            data8 = np.zeros([nl, ns])
            if dayNight =='day':
                data3 = np.zeros([nl, ns])
                data4 = np.zeros([nl, ns])
                data6 = np.zeros([nl, ns])
                data9 = np.zeros([nl, ns])
                data10 = np.zeros([nl, ns])


        # infile = indir_med + infile0 + r'bt8_proj.tif'
        infile = indir_med + r'bt8_proj.tif'
        dataset = gdal.Open(infile)
        if dataset == None:
            print(infile + " ")
            continue
        im_width = dataset.RasterXSize * 1
        im_height = dataset.RasterYSize * 1
        im_bands = dataset.RasterCount * 1
        data = dataset.ReadAsArray(0, 0, im_width, im_height)
        im_geotrans = dataset.GetGeoTransform()
        im_proj = dataset.GetProjection()
        temp1, temp2 = lonlat2geo(dataset, lon, lat)
        imagex, imagey = geo2imagexy(dataset, temp2, temp1)
        dataset = None

        imagex = np.asarray(imagex, np.int)
        imagey = np.asarray(imagey, np.int)
        ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
        imagex[imagex < 0] = 0
        imagex[imagex > (im_height - 1)] = im_height - 1
        imagey[imagey < 0] = 0
        imagey[imagey > (im_width - 1)] = im_width - 1
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 200) * ind
        if np.sum(indnew) == 0: continue
        data1 = np.reshape(data1, [-1])
        data1[indnew] = temp[indnew]
        data1 = np.reshape(data1, [nl, ns])
        data1[data1 < 0] = 0
        data1[data1 > 500] = 0

        # # infile = indir_med + infile0 + r'bt9_proj.tif'
        infile = indir_med + r'bt9_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 200) * ind
        data2 = np.reshape(data2, [-1])
        data2[indnew] = temp[indnew]
        data2 = np.reshape(data2, [nl, ns])
        data2[data2 < 0] = 0
        data2[data2 > 500] = 0
        #
        data8 = np.reshape(data8, [-1])
        temp[:] = np.int(np.uint(time_str))
        data8[indnew] = temp[indnew]
        data8 = np.reshape(data8, [nl, ns])
        # #
        # # #
        # # # infile = indir_med + infile0 + r'red_proj.tif'


        # # # infile = indir_med + infile0 + r'vza_proj.tif'
        infile = indir_med + r'vza_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 0) * ind
        data5 = np.reshape(data5, [-1])
        data5[indnew] = temp[indnew]
        data5 = np.reshape(data5, [nl, ns])
        data5[data5 < 0] = 0
        data5[data5 > 500] = 0

        infile = indir_med + r'cloud_proj.tif'
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
        temp = data[imagex, imagey]
        indnew = (temp < 500) * (temp > 0) * ind
        data11 = np.reshape(data11, [-1])
        data11[indnew] = temp[indnew]
        data11 = np.reshape(data11, [nl, ns])
        data11[data11 < 0] = 0
        data11[data11 > 500] = 0

        #
        if dayNight == 'day':
            # infile = indir_med + infile0 + r'red_proj.tif'
            infile = indir_med + r'red_proj.tif'
            [data_satellite, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            data_satellite = resize_data(data_satellite, im_height, im_width,0)
            temp = data_satellite[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data3 = np.reshape(data3, [-1])
            data3[indnew] = temp[indnew]
            data3 = np.reshape(data3, [nl, ns])
            data3[data3 < 0] = 0
            data3[data3 > 500] = 0

            # infile = indir_med + infile0 + r'nir_proj.tif'
            infile = indir_med + r'nir_proj.tif'
            [data_satellite, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            data_satellite = resize_data(data_satellite, im_height, im_width)
            temp = data_satellite[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data4 = np.reshape(data4, [-1])
            data4[indnew] = temp[indnew]
            data4 = np.reshape(data4, [nl, ns])
            data4[data4 < 0] = 0
            data4[data4 > 500] = 0

            infile = indir_med + r'red_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            data = resize_data(data, im_height, im_width)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data3 = np.reshape(data3, [-1])
            data3[indnew] = temp[indnew]
            data3 = np.reshape(data3, [nl, ns])
            data3[data3 < 0] = 0
            data3[data3 > 500] = 0
            #
            # # # infile = indir_med + infile0 + r'nir_proj.tif'
            infile = indir_med + r'nir_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            data = resize_data(data, im_height, im_width)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data4 = np.reshape(data4, [-1])
            data4[indnew] = temp[indnew]
            data4 = np.reshape(data4, [nl, ns])
            data4[data4 < 0] = 0
            data4[data4 > 500] = 0

            # # # infile = indir_med + infile0 + r'sza_proj.tif'
            infile = indir_med + r'sza_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data6 = np.reshape(data6, [-1])
            data6[indnew] = temp[indnew]
            data6 = np.reshape(data6, [nl, ns])
            data6[data6 < 0] = 0
            data6[data6 > 500] = 0
            #
            # infile = indir_med + infile0 + r'vaa_proj.tif'
            infile = indir_med + r'vaa_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data9 = np.reshape(data9, [-1])
            data9[indnew] = temp[indnew]
            data9 = np.reshape(data9, [nl, ns])
            data9[data9 < 0] = 0
            data9[data9 > 500] = 0
        #
            # # infile = indir_med + infile0 + r'saa_proj.tif'
            infile = indir_med + r'saa_proj.tif'
            [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)
            temp = data[imagex, imagey]
            indnew = (temp < 500) * (temp > 0) * ind
            data10 = np.reshape(data10, [-1])
            data10[indnew] = temp[indnew]
            data10 = np.reshape(data10, [nl, ns])
            data10[data10 < 0] = 0
            data10[data10 > 500] = 0


        write_image_gdal(data1, ns, nl, 1, geog, proj, outfile1)
        write_image_gdal(data2, ns, nl, 1, geog, proj, outfile2)
        write_image_gdal(data5, ns, nl, 1, geog, proj, outfile5)
        write_image_gdal(data8, ns, nl, 1, geog, proj, outfile8)
        write_image_gdal(data11, ns, nl, 1, geog, proj, outfile11)

        if dayNight == 'day':

            write_image_gdal(data3, ns, nl, 1, geog, proj, outfile3)
            write_image_gdal(data4, ns, nl, 1, geog, proj, outfile4)
            write_image_gdal(data6, ns, nl, 1, geog, proj, outfile6)
            write_image_gdal(data9, ns, nl, 1, geog, proj, outfile9)
            write_image_gdal(data10, ns, nl, 1, geog, proj, outfile10)

