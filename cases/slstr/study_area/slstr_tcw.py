import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from base.util_constant import *
from base.util_file import *
from base.util_data import *

'''用来提取era数据并投影'''

def write_vrt_era5(vrtfile, datafile, xfile, yfile, xscale, yscale, noDataValue = 65535, bandnumber = 1):
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


indir_raw = r'/home/hero/data/SLSTR_heihe/tcwv/raw/'
indir_tif = r'/home/hero/data/SLSTR_heihe/tcwv/tif/'
indir_med = r'/home/hero/data/SLSTR_heihe/tcwv/med/'
mkdir_if_not_exist(indir_tif)
mkdir_if_not_exist(indir_med)


fileNames = search_file(indir_raw , ['.nc'])
fileNum = len(fileNames)

symbol = 'ERA5_tcw'


for k in range(fileNum):
    fileName = fileNames[k]
    infile = indir_raw + fileName
    print(k, infile)
    # year = fileName[18:22]
    # month = fileName[22:24]
    # day = fileName[24:26]
    # doy = date2DOY(year, month, day)
    year = 2022
    month = 6
    day = 29
    doy = date2DOY(year, month, day)

    '''提取信息'''
    fileName = infile
    objectName = 'valid_time'
    ###### test error and file error
    try:
        nf = netCDF4.Dataset(fileName)
    except OSError:
        print(fileName + ' os error')
        continue
    # nf.variables.keys()
    if (objectName not in nf.variables.keys()): continue

    time = read_image_Nc(fileName, 'valid_time',1)
    tcwv = read_image_Nc(fileName, 'tcwv', 1)
    lat_data = read_image_Nc(fileName, 'latitude', 1)
    lon_data = read_image_Nc(fileName, 'longitude', 1)

    band,nl,ns = tcwv.shape

    lon = np.zeros([nl, ns])
    lon_data[lon_data>180] = lon_data[lon_data>180]-360
    lat = np.zeros([nl,ns])
    for i in range(ns):
        lon[:,i] = lon_data[i]
    for i in range(nl):
        lat[i,:] = lat_data[i]

    '''调整一下位置,太平洋中心->大西洋中心'''
    lon_save = np.zeros([nl,ns])
    lon_save[:,:719] = lon[:,721:]
    lon_save[:,719:] = lon[:,:721]
    tcwv_save = np.zeros([band,nl,ns])
    tcwv_save[:,:,:719] = tcwv[:,:,721:]
    tcwv_save[:, :, 719:] = tcwv[:,:, :721]

    '''劈窗算法中tcw最大也只用5.25*10，uint16存储范围0-65535'''
    tcwv_save = tcwv_save * 100
    tcwv_save[tcwv_save>65535] = 65500

    '''输出位置'''
    lat_dir = indir_med + 'lat.tif'
    lon_dir = indir_med + 'lon.tif'
    write_image_gdal(lat[:nl, :ns].astype(float64), ns, nl, 1, '', '', lat_dir)
    write_image_gdal(lon_save[:nl, :ns].astype(float64), ns, nl, 1, '', '', lon_dir)
    for hour in range(24):
        hour_str = "%02d" % hour
        tcw_dir = indir_med + 'tcw.tif'
        write_image_gdal((tcwv_save[hour]).astype('uint16'), ns, nl, 1, '', '', tcw_dir)
        fileDir = indir_tif + '/%03d/' % doy
        mkdir_if_not_exist(fileDir)
        file = 'tcw'
        datafile = indir_med + file + '.tif'
        xfile = indir_med + 'lon.tif'
        yfile = indir_med + 'lat.tif'
        vrtfile = indir_med + file + '.vrt'
        write_vrt_era5(vrtfile, datafile, xfile, yfile, ns, nl, bandnumber=1)
        outfile = fileDir + symbol + "_" + str(year) + "_%03d_" % doy + hour_str + '.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)


# for year in range(2002,2013):
#     indir_raw_year = indir_raw + str(year) + r"\\"
#     fileNames = search_file(indir_raw_year, ['.nc'])
#     fileNum = len(fileNames)

#     symbol = 'ERA5_tcw'

#     for k in range(fileNum):
#         fileName = fileNames[k]
#         infile = indir_raw_year + fileName
#         print(k, infile)
#         year = fileName[18:22]
#         month = fileName[22:24]
#         day = fileName[24:26]
#         doy = date2DOY(year, month, day)

#         '''提取信息'''
#         fileName = infile
#         objectName = 'time'
#         ###### test error and file error
#         try:
#             nf = netCDF4.Dataset(fileName)
#         except OSError:
#             print(fileName + ' os error')
#             continue
#         # nf.variables.keys()
#         if (objectName not in nf.variables.keys()): continue

#         time = read_image_Nc(fileName, 'time', 1)
#         tcwv = read_image_Nc(fileName, 'tcwv', 1)
#         lat_data = read_image_Nc(fileName, 'latitude', 1)
#         lon_data = read_image_Nc(fileName, 'longitude', 1)

#         band, nl, ns = tcwv.shape

#         lon = np.zeros([nl, ns])
#         lon_data[lon_data > 180] = lon_data[lon_data > 180] - 360
#         lat = np.zeros([nl, ns])
#         for i in range(ns):
#             lon[:, i] = lon_data[i]
#         for i in range(nl):
#             lat[i, :] = lat_data[i]

#         '''调整一下位置,太平洋中心->大西洋中心'''
#         lon_save = np.zeros([nl, ns])
#         lon_save[:, :719] = lon[:, 721:]
#         lon_save[:, 719:] = lon[:, :721]
#         tcwv_save = np.zeros([band, nl, ns])
#         tcwv_save[:, :, :719] = tcwv[:, :, 721:]
#         tcwv_save[:, :, 719:] = tcwv[:, :, :721]

#         '''劈窗算法中tcw最大也只用5.25*10，uint16存储范围0-65535'''
#         tcwv_save = tcwv_save * 100
#         tcwv_save[tcwv_save > 65535] = 65500

#         '''输出位置'''
#         lat_dir = indir_med + 'lat.tif'
#         lon_dir = indir_med + 'lon.tif'
#         write_image_gdal(lat[:nl, :ns].astype(float64), ns, nl, 1, '', '', lat_dir)
#         write_image_gdal(lon_save[:nl, :ns].astype(float64), ns, nl, 1, '', '', lon_dir)
#         for hour in range(24):
#             hour_str = "%02d" % hour
#             tcw_dir = indir_med + 'tcw.tif'
#             write_image_gdal((tcwv_save[hour]).astype('uint16'), ns, nl, 1, '', '', tcw_dir)
#             fileDir = indir_tif + "%04d" % int(year) + r"\\" + "%03d" % doy + r"\\"
#             mkdir_if_not_exist(fileDir)
#             file = 'tcw'
#             datafile = indir_med + file + '.tif'
#             xfile = indir_med + 'lon.tif'
#             yfile = indir_med + 'lat.tif'
#             vrtfile = indir_med + file + '.vrt'
#             write_vrt(vrtfile, datafile, xfile, yfile, ns, nl, bandnumber=1)
#             outfile = fileDir + symbol + "_" + str(year) + "_%03d_" % doy + hour_str + '.tif'
#             dst_ds = gdal.Warp(outfile, vrtfile,  resampleAlg=gdal.GRIORA_NearestNeighbour,outputBounds=(-180,-90,180,90),xRes=0.2,yRes=0.2)








