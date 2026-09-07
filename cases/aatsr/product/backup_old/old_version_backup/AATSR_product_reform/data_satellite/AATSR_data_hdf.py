import epr
from utils.old.util import *
from utils.old.util_constant import *

# os.environ['PROJ_LIB'] = r'C:\Users\zzz\anaconda3\envs\patrol\Library\share\proj'

'''
处理AATSR数据,并保存成hdf格式
'''

ifread = 1


'write_image_gdal函数，改进了保存时的格式，与util.py有不同！'
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

indir_raw_ = r"F:\data\AATSR\raw\\"
indir_tif_ = r"F:\data\AATSR\tif\\"
symbol = "AATSR"

'''读取数据'''
# for year in range(2012,2013):
#     for month in range(3,5):
#         daynum = calendar.monthrange(year,month)[1]
#         for day in range(daynum):

# time_str = "%04d//" % year + "%02d//" % month + "%02d//" % (day+1)
# indir_raw = indir_raw_ + time_str
indir_raw = indir_raw_
# if not os.path.exists(indir_raw): continue
# indir_tif = indir_tif_ + time_str
indir_tif = indir_tif_
mkdir_if_not_exist(indir_tif)
fileNames = search_file_rej(indir_raw, ['ATS_TOA'],'enp')
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
    hdf_dir = common_dir + 'tif.hdf'

    'bt *100'
    bt1_n[bt1_n < 0] = 0
    bt1_n_save = bt1_n[:nl, :ns]*100
    bt2_n[bt2_n < 0] = 0
    bt2_n_save = bt2_n[:nl, :ns]*100
    bt1_f[bt1_f < 0] = 0
    bt1_f_save = bt1_f[:nl, :ns]*100
    bt2_f[bt2_f< 0] = 0
    bt2_f_save = bt2_f[:nl, :ns]*100

    # 'red/nir *100'
    # red_n[red_n < 0] = 0
    # red_n_save = red_n[:nl, :ns]*100
    # nir_n[nir_n < 0] = 0
    # nir_n_save = nir_n[:nl, :ns]*100
    # red_f[red_f < 0] = 0
    # red_f_save = red_f[:nl, :ns]*100
    # nir_f[nir_f < 0] = 0
    # nir_f_save = nir_f[:nl, :ns]*100

    'ang *100'
    sza_n_save = (sza_n[:nl, :ns]*100).astype(int16)
    saa_n_save = (saa_n[:nl, :ns]*100)
    vza_n_save = (vza_n[:nl, :ns]*100)
    vaa_n_save = (vaa_n[:nl, :ns]*100)
    vza_f_save = (vza_f[:nl, :ns]*100)
    vaa_f_save = (vaa_f[:nl, :ns]*100)

    file = h5py.File(hdf_dir, 'w')
    file.create_dataset('bt1_n', data=bt1_n_save.astype(uint16))
    file.create_dataset('bt1_f', data=bt1_f_save.astype(uint16))
    file.create_dataset('bt2_n', data=bt2_n_save.astype(uint16))
    file.create_dataset('bt2_f', data=bt2_f_save.astype(uint16))

    file.create_dataset('vza_n', data=vza_n_save.astype(uint16))
    file.create_dataset('vaa_n', data=vaa_n_save.astype(int16))
    file.create_dataset('vza_f', data=vza_f_save.astype(uint16))
    file.create_dataset('vaa_f', data=vaa_f_save.astype(int16))

    file.create_dataset('sza_n', data=sza_n_save.astype(int16))
    file.create_dataset('saa_n', data=saa_n_save.astype(int16))

    file.create_dataset('cloud_n', data=cloud_n.astype(uint16))
    file.create_dataset('cloud_f', data=cloud_f.astype(uint16))

    file.create_dataset('lat', data=lat)
    file.create_dataset('lon', data=lon)
    file.close()


    # hdf_db = pd.HDFStore(hdf_dir,mode='w', complevel=0, complib='blosc')
    # hdf_db.create_data
    # hdf_db.put(key='bt1_n', value=bt1_n)
    # hdf_db.put(key='bt2_n', value=bt2_n)
    # hdf_db.put(key='bt1_f', value=bt1_f)
    # hdf_db.put(key='bt2_f', value=bt2_f)
    # print(datetime.datetime.now().strftime('%Y-%m-%d  %H:%M:%S') + '  : ' + fileName)
    # hdf_db.close()
    product.close()
    break
