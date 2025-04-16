from util.util import *
from util.util_constant import *
import math

'''用来提取era数据并投影'''

years = [2016,2017,2018,2019,2020,2021,2022]
year = years[1]

indir_raw = r'H:\ERA5\ERA5_tcw_raw\%04d\\' % year
indir_tif = r'H:\ERA5\ERA5_tcw_tif\%04d\\' % year
indir_med = r'H:\ERA5\ERA5_tcw_tif\%04d\med\\'% year
mkdir_if_not_exist(indir_med)

indir_type =r'H:\Sentinel-3\base\type\\'
infile12 = indir_type + 'type_heihe_1000_utm47N.tif'

fileNames = search_file(indir_raw,['.nc'])
fileNum = len(fileNames)

symbol = 'ERA5_tcw'
ifextract = 0
ifcut = 1

def write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale, noDataValue = 65535, bandnumber = 1):
    '''
    导出用于gdal vrt的配置文件
    # 与函数配合使用，outfile为转成的文件路径，resampleAlg为重采样的
    # dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)
    :param vrtfile:  该配置文件名称
    :param datafile:  所要操作的文件名称
    :param xfile:  经度坐标文件 lon
    :param yfile:  纬度坐标文件 lat
    :param xscale:  列数
    :param yscale:  行数
    :param noDataValue: 无值填补
    :param bandnumber:  波段数据
    :return: 无
    '''
    f = open(vrtfile, 'w')
    f.write(r'<VRTDataset rasterXSize="%d"'%xscale + 'rasterYSize="%d">'%yscale)
    f.write('\n')
    f.write(r'  <Metadata domain="GEOLOCATION">')
    f.write('\n')
    f.write(r'    <MDI key="SRS">GEOGCS["WGS 84(DD)",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AXIS["Long",EAST],AXIS["Lat",NORTH]]</MDI>')
    # f.write(r'    <MDI key="SRS">GEOGCS["WGS 84(DD)",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG", "9122"],AUTHORITY["EPSG", "4490"]</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="X_DATASET">' + xfile + r'</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="X_BAND">1</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="PIXEL_OFFSET">0</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="PIXEL_STEP">1</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="Y_DATASET">' + yfile + r'</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="Y_BAND">1</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="LINE_OFFSET">0</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="LINE_STEP">1</MDI>')
    f.write('\n')
    f.write(r'  </Metadata>')
    f.write('\n')
    f.write(r'  <VRTRasterBand dataType = "Uint16" band = "%d">'%bandnumber)
    f.write('\n')
    f.write(r'    <ColorInterp>Gray</ColorInterp >')
    f.write('\n')
    f.write(r'    <NoDataValue>%d</NoDataValue >'%noDataValue)
    f.write('\n')
    f.write(r'    <SimpleSource>')
    f.write('\n')
    f.write(r'      <SourceFilename relativeToVRT = "1" >' + datafile + r'</SourceFilename>')
    f.write('\n')
    f.write(r'      <SourceBand>1</SourceBand>')
    f.write('\n')
    f.write(r'    </SimpleSource>')
    f.write('\n')
    f.write(r'  </VRTRasterBand>')
    f.write('\n')
    f.write('</VRTDataset>')
    f.close()
    return 1

if ifextract:
    for k in range(fileNum):
        fileName = fileNames[k]
        infile = indir_raw + fileName
        print(k, infile)
        year = int(fileName[18:22])
        month = fileName[22:24]
        day = fileName[24:26]
        doy = date2DOY(year, month, day)
        # if doy < 250: continue

        '''提取信息'''
        fileName = infile
        objectName = 'time'
        ###### test error and file error
        try:
            nf = netCDF4.Dataset(fileName)
        except OSError:
            print(fileName + ' os error')
            continue
        # nf.variables.keys()
        if (objectName not in nf.variables.keys()): continue

        time = read_image_Nc(fileName, 'time', 1)
        tcwv = read_image_Nc(fileName, 'tcwv', 1)
        lat_data = read_image_Nc(fileName, 'latitude', 1)
        lon_data = read_image_Nc(fileName, 'longitude', 1)

        band, nl, ns = tcwv.shape

        lon = np.zeros([nl, ns])
        lon_data[lon_data > 180] = lon_data[lon_data > 180] - 360
        lat = np.zeros([nl, ns])
        for i in range(ns):
            lon[:, i] = lon_data[i]
        for i in range(nl):
            lat[i, :] = lat_data[i]

        '''调整一下位置,太平洋中心->大西洋中心'''
        lon_save = np.zeros([nl, ns])
        lon_save[:, :719] = lon[:, 721:]
        lon_save[:, 719:] = lon[:, :721]
        tcwv_save = np.zeros([band, nl, ns])
        tcwv_save[:, :, :719] = tcwv[:, :, 721:]
        tcwv_save[:, :, 719:] = tcwv[:, :, :721]

        '''劈窗算法中tcw最大也只用5.25*10，uint16存储范围0-65535'''
        tcwv_save = tcwv_save * 100
        tcwv_save[tcwv_save > 65535] = 65500

        '''输出位置'''
        lat_dir = indir_med + 'lat.tif'
        lon_dir = indir_med + 'lon.tif'
        write_image_gdal(lat[:nl, :ns].astype(float64), ns, nl, 1, '', '', lat_dir)
        write_image_gdal(lon_save[:nl, :ns].astype(float64), ns, nl, 1, '', '', lon_dir)
        for hour in range(24):
            hour_str = "%02d" % hour
            tcw_dir = indir_med + 'tcw.tif'
            write_image_gdal((tcwv_save[hour]).astype('uint16'), ns, nl, 1, '', '', tcw_dir)
            fileDir = indir_tif + "%03d" % doy + r"\\"
            mkdir_if_not_exist(fileDir)
            file = 'tcw'
            datafile = indir_med + file + '.tif'
            xfile = indir_med + 'lon.tif'
            yfile = indir_med + 'lat.tif'
            vrtfile = indir_med + file + '.vrt'
            write_vrt(vrtfile, datafile, xfile, yfile, ns, nl, bandnumber=1)
            outfile = fileDir + symbol + "_" + str(year) + "_%03d_" % doy + hour_str + '.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

if ifcut:
    indir_tif_slstr = r'H:\Sentinel-3\%04d\tif\\' % year

    # 查找水汽对应坐标
    dataset = gdal.Open(infile12)
    [data, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile12)
    nsi = np.zeros([nl, ns])
    nli = np.zeros([nl, ns])
    for k in range(nl):
        nli[k, :] = k
        nsi[k, :] = np.linspace(0, ns - 1, ns)
    nli = np.reshape(nli, -1)
    nsi = np.reshape(nsi, -1)
    dataset = gdal.Open(infile12)
    temp1, temp2 = imagexy2geo(dataset, nli, nsi)
    lon, lat = geo2lonlat(dataset, temp1, temp2)
    lon = np.reshape(lon, [nl, ns])
    lat = np.reshape(lat, [nl, ns])
    tcw_dir_0 = r"H:\ERA5\ERA5_tcw_tif\2022\\\001\\ERA5_tcw_2022_001_00.tif"
    dataset = gdal.Open(tcw_dir_0)
    indx, indy = loc2map(lat, lon, dataset)

    fileNames = search_file_rej(indir_tif_slstr, ['bt1'], 'obliq')
    fileNum = np.size(fileNames)
    off = 13
    for k in range(fileNum):
        fileName = fileNames[k]
        print(fileName)
        time_str = fileName[4:12]
        year = int(time_str[0:4])
        doy_str = time_str[5:8]
        doy = np.int(doy_str)

        infile = indir_tif_slstr + fileName[:-off] + 'time.tif'
        [slstrTime, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile)

        # 时间取平均值
        slstr_time = slstrTime[int(temp2 / 2), int(temp1 / 2)]
        if slstr_time==0:
            slstr_time = (np.array(slstrTime[slstrTime>0]).reshape(-1,1))[0]
        hour = math.floor(slstr_time / 10000)
        m = math.floor((slstr_time - hour * 10000) / 100)
        sec = slstr_time % 100
        min = m + sec / 60

        # 读取水汽
        if hour != 23:
            tcw_filename1 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % hour
            tcw_filename2 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % (hour + 1)
        else:
            tcw_filename1 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % doy + "%02d.tif" % hour
            tcw_filename2 = "ERA5_tcw_" + "%04d_" % year + "%03d_" % (doy + 1) + "00.tif"
        tcw_dir1 = indir_tif + "/%03d/" % doy + tcw_filename1
        tcw_dir2 = indir_tif + "/%03d/" % doy + tcw_filename2
        [tcw1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir1)
        [tcw2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir2)
        f = min / 60
        tcw_data = (f * tcw2 + (1 - f) * tcw1) / 100 / 10
        tcw = np.zeros([nl, ns])
        tcw = tcw_data[indx, indy]
        tcw = np.reshape(tcw, [nl, ns])

        outfile = indir_tif_slstr + fileName[:-off] + 'tcw.tif'
        print(outfile)
        write_image_gdal(tcw,ns, nl, nb, geog_type, proj_type,outfile)















