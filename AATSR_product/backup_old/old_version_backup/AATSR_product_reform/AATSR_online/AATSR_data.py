import sys
sys.path.append('/data1/home/AircasBianzj/code/')
from utils.myfun_lyf import *
from utils.old.util import *
import epr

# os.environ['PROJ_LIB'] = r'C:\Users\zzz\anaconda3\envs\patrol\Library\share\proj'

'''
处理AATSR数据
'''

ifread = 1


'改进了保存时的格式，与util.py有不同！'
def write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType = 'GTiff'):
    '''
    保存数据，输出成tif格式
    :param im_data: 数组
    :param im_width:  列数
    :param im_height:  行数
    :param im_bands:  波段数
    :param im_trans:  地理坐标
    :param im_proj:  投影坐标
    :param path:  路径
    :return: 无
    '''
    if 'int8' in im_data.dtype.name:
        datatype = gdal.GDT_Byte
    elif 'uint16' in im_data.dtype.name:
        datatype = gdal.GDT_UInt16
    elif 'int16' in im_data.dtype.name:
        datatype = gdal.GDT_Int16
    else:
        datatype = gdal.GDT_Float32
    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    elif len(im_data.shape) == 2:
        im_data = np.array([im_data])
    else:
        im_bands, (im_height, im_width) = 1, im_data.shape
    driver = gdal.GetDriverByName(imageType)
    dataset = driver.Create(path, im_width, im_height, im_bands, datatype)
    if (dataset != None and im_trans != '' and im_proj != ''):
        dataset.SetGeoTransform(im_trans)
        dataset.SetProjection(im_proj)
    for i in range(im_bands):
        dataset.GetRasterBand(i+1).WriteArray(im_data[i])
    del dataset


'''
先通过epr读取数据，提取出tif文件
'''

year = sys.argv[1]
month = sys.argv[2]
day = sys.argv[3]
time_str = "//%04d" % int(year) + "//%02d" % int(month) + "//%02d" % int(day) + "//"
indir_raw = r"/data1/public1/Bianzj/neodc/aatsr_multimission/aatsr-v2.1/data/ats_toa_1p//" + time_str
indir_tif = r"/data1/public1/Bianzj/AATSR//AATSR_tif" + time_str
# indir_med = r"D:\data\data_download\AATSR\example\AATSR_med\\"
mkdir_if_not_exist(indir_tif)
symbol = "AATSR"

'''读取数据'''
if ifread == 1:
    fileNames = search_file_rej(indir_raw, ['ATS_TOA'],'md5')
    fileNum = len(fileNames)
    if fileNum == 0: print("No data found!")
    for k in range(fileNum):
        fileName = fileNames[k]

        '''读取时间信息'''
        year_str = fileName[14:18]
        date_str = fileName[18:22]
        time_str = fileName[23:29]
        doy_int = date2DOY(int(year_str), int(date_str[0:2]), int(date_str[2:4]))
        doy_str = str(doy_int).zfill(3)

        '''读取产品'''
        infile = indir_raw + fileName
        product = epr.Product(infile)

        '''读取经纬度信息'''
        band = product.get_band('latitude')
        lat = band.read_as_array()
        band = product.get_band('longitude')
        lon = band.read_as_array()
        height, width = np.shape(lat)

        band = product.get_band('lat_corr_nadir')
        lat_corr_nadir = band.read_as_array()
        band = product.get_band('lon_corr_nadir')
        lon_corr_nadir = band.read_as_array()
        band = product.get_band('lat_corr_fward')
        lat_corr_fward = band.read_as_array()
        band = product.get_band('lon_corr_fward')
        lon_corr_fward = band.read_as_array()

        '''读取角度信息'''
        band = product.get_band('sun_elev_nadir')
        sza_n = band.read_as_array()
        band = product.get_band('view_elev_nadir')
        vza_n = band.read_as_array()
        band = product.get_band('sun_azimuth_nadir')
        saa_n = band.read_as_array()
        band = product.get_band('view_azimuth_nadir')
        vaa_n = band.read_as_array()

        # band = product.get_band('sun_elev_fward') #前向和垂直只保存一个太阳角
        # sza_f = band.read_as_array()
        band = product.get_band('view_elev_fward')
        vza_f = band.read_as_array()
        # band = product.get_band('sun_azimuth_fward')
        # sza_f = band.read_as_array()
        band = product.get_band('view_azimuth_fward')
        vaa_f = band.read_as_array()

        '''读取热红外信息'''
        band = product.get_band('btemp_nadir_1100')
        bt1_n = band.read_as_array()
        band = product.get_band('btemp_nadir_1200')
        bt2_n = band.read_as_array()

        band = product.get_band('btemp_fward_1100')
        bt1_f = band.read_as_array()
        band = product.get_band('btemp_fward_1200')
        bt2_f = band.read_as_array()

        '''读取可见光信息'''
        band = product.get_band('reflec_nadir_0670')
        red_n = band.read_as_array()
        band = product.get_band('reflec_nadir_0870')
        nir_n = band.read_as_array()

        band = product.get_band('reflec_fward_0670')
        red_f = band.read_as_array()
        band = product.get_band('reflec_fward_0870')
        nir_f = band.read_as_array()

        '''读取云层信息'''
        band = product.get_band('cloud_flags_nadir')
        cloud_n = band.read_as_array()
        band = product.get_band('cloud_flags_fward')
        cloud_f = band.read_as_array()

        '''输出raw格式文件'''
        # write_raw_image(bt1_n_dir,product,'btemp_nadir_1100')


        nl = height
        ns = width
        '''输出位置'''
        common_dir = indir_tif + symbol + "_" + year_str + "_" + doy_str + "_" + time_str + '_'

        lat_dir = common_dir + 'lat.tif'
        lon_dir = common_dir + 'lon.tif'

        saa_n_dir = common_dir + 'saa.tif'
        sza_n_dir = common_dir + 'sza.tif'
        vaa_n_dir = common_dir + 'vaa_n.tif'
        vza_n_dir = common_dir + 'vza_n.tif'
        bt1_n_dir = common_dir + 'bt1_n.tif'
        bt2_n_dir = common_dir + 'bt2_n.tif'
        red_n_dir = common_dir + 'red_n.tif'
        nir_n_dir = common_dir + 'nir_n.tif'
        clo_n_dir = common_dir + 'clo_n.tif'

        # saa_f_dir = common_dir + 'saa_f.tif'
        # sza_f_dir = common_dir + 'sza_f.tif'
        vaa_f_dir = common_dir + 'vaa_f.tif'
        vza_f_dir = common_dir + 'vza_f.tif'
        bt1_f_dir = common_dir + 'bt1_f.tif'
        bt2_f_dir = common_dir + 'bt2_f.tif'
        red_f_dir = common_dir + 'red_f.tif'
        nir_f_dir = common_dir + 'nir_f.tif'
        clo_f_dir = common_dir + 'clo_f.tif'

        '''输出tif文件'''
        write_image_gdal(lat[:height, :width], width, height, 1, '', '', lat_dir)
        write_image_gdal(lon[:height, :width], width, height, 1, '', '', lon_dir)

        'bt *100'
        bt1_n[bt1_n < 0] = 0
        bt1_n_save = bt1_n[:nl, :ns]*100
        write_image_gdal(bt1_n_save.astype(uint16), ns, nl, 1, '', '', bt1_n_dir)
        bt2_n[bt2_n < 0] = 0
        bt2_n_save = bt2_n[:nl, :ns]*100
        write_image_gdal(bt2_n_save.astype(uint16), ns, nl, 1, '', '', bt2_n_dir)
        bt1_f[bt1_f < 0] = 0
        bt1_f_save = bt1_f[:nl, :ns]*100
        write_image_gdal(bt1_f_save.astype(uint16), ns, nl, 1, '', '', bt1_f_dir)
        bt2_f[bt2_f< 0] = 0
        bt2_f_save = bt2_f[:nl, :ns]*100
        write_image_gdal(bt2_f_save.astype(uint16), ns, nl, 1, '', '', bt2_f_dir)

        'red/nir *100'
        red_n[red_n < 0] = 0
        red_n_save = red_n[:nl, :ns]*100
        write_image_gdal(red_n_save.astype(uint16), ns, nl, 1, '', '', red_n_dir)
        nir_n[nir_n < 0] = 0
        nir_n_save = nir_n[:nl, :ns]*100
        write_image_gdal(nir_n_save.astype(uint16), ns, nl, 1, '', '', nir_n_dir)
        red_f[red_f < 0] = 0
        red_f_save = red_f[:nl, :ns]*100
        write_image_gdal(red_f_save.astype(uint16), ns, nl, 1, '', '', red_f_dir)
        nir_f[nir_f < 0] = 0
        nir_f_save = nir_f[:nl, :ns]*100
        write_image_gdal(nir_f_save.astype(uint16), ns, nl, 1, '', '', nir_f_dir)

        'ang *100'
        sza_n_save = (sza_n[:nl, :ns]*100).astype(int16)
        write_image_gdal(sza_n_save, ns, nl, 1, '', '', sza_n_dir)
        saa_n_save = (saa_n[:nl, :ns]*100)
        write_image_gdal(saa_n_save.astype(int16), ns, nl, 1, '', '', saa_n_dir)
        vza_n_save = (vza_n[:nl, :ns]*100)
        write_image_gdal(vza_n_save.astype(uint16), ns, nl, 1, '', '', vza_n_dir)
        vaa_n_save = (vaa_n[:nl, :ns]*100)
        write_image_gdal(vaa_n_save.astype(int16), ns, nl, 1, '', '', vaa_n_dir)
        vza_f_save = (vza_f[:nl, :ns]*100)
        write_image_gdal(vza_f_save.astype(uint16), ns, nl, 1, '', '', vza_f_dir)
        vaa_f_save = (vaa_f[:nl, :ns]*100)
        write_image_gdal(vaa_f_save.astype(int16), ns, nl, 1, '', '', vaa_f_dir)

        write_image_gdal(cloud_n[:nl, :ns].astype(uint16), ns, nl, 1, '', '', clo_n_dir)
        write_image_gdal(cloud_f[:nl, :ns].astype(uint16), ns, nl, 1, '', '', clo_f_dir)

        print(datetime.datetime.now().strftime('%Y-%m-%d  %H:%M:%S') + '  : ' + fileName)

        product.close()
