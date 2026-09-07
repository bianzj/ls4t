import sys
sys.path.append('/data1/home/AircasBianzj/code/')
from utils.old.util import *
from utils.myfun_lyf import *
from utils.old.util_constant import *
import warnings
warnings.filterwarnings("ignore")


year_ = sys.argv[1]
month_ = sys.argv[2]
day_ = sys.argv[3]

doy_ =date2DOY(int(year_),int(month_),int(day_))
time_str = "//%04d" % int(year_) + "//%03d" % int(doy_) + "//"


'''用来提取era数据并投影'''


indir_raw = r'/data1/public1/Bianzj/ERA5_tcw/ERA5_tcw_raw//' + "//%04d" % int(year_)+"//"
indir_tif = r'/data1/public1/Bianzj/ERA5_tcw/ERA5_tcw_tif//' + time_str
indir_med = r'/data1/public1/Bianzj/ERA5_tcw/ERA5_tcw_med//' + time_str
mkdir_if_not_exist(indir_tif)
mkdir_if_not_exist(indir_med)

fileNames = search_file(indir_raw,['.nc'])
fileNum = len(fileNames)

symbol = 'ERA5_tcw'

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

for k in range(fileNum):
    fileName = fileNames[k]
    infile = indir_raw  + fileName
    # print(k, infile)
    year = fileName[18:22]
    month = fileName[22:24]
    day = fileName[24:26]
    doy = date2DOY(year, month, day)
    if doy == doy_:
        print('match!')
    else:
        print(doy,doy_)
        continue


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

    time = read_image_Nc(fileName, 'time',1)
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
    lat_dir = indir_med + "%04d_"%int(year)+"%03d_"%int(doy)+'lat.tif'
    lon_dir = indir_med + "%04d_"%int(year)+"%03d_"%int(doy)+ 'lon.tif'
    write_image_gdal(lat[:nl, :ns].astype(float64), ns, nl, 1, '', '', lat_dir)
    write_image_gdal(lon_save[:nl, :ns].astype(float64), ns, nl, 1, '', '', lon_dir)
    for hour in range(24):
        hour_str = "%02d" % hour
        tcw_dir = indir_med + "%04d_"%int(year)+"%03d_"%int(doy)+"%02d_"%int(hour)+'tcw.tif'
        write_image_gdal((tcwv_save[hour]).astype('uint16'), ns, nl, 1, '', '', tcw_dir)
        file = 'tcw'
        datafile = tcw_dir
        xfile = indir_med + "%04d_"%int(year)+"%03d_"%int(doy)+'lon.tif'
        yfile = indir_med + "%04d_"%int(year)+"%03d_"%int(doy)+ 'lat.tif'
        vrtfile = indir_med + "%04d_"%int(year)+"%03d_"%int(doy)+"%02d_"%int(hour)+file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, ns, nl, bandnumber=1)
        outfile = indir_tif + symbol + "_" + str(year) + "_%03d_" % doy + hour_str + '.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour,outputBounds=(-180,-90,180,90),xRes=0.2,yRes=0.2)
    break











