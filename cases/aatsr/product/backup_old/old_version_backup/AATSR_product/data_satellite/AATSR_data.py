import epr

from utils.old.util import *
from utils.old.util_constant import *
import os
import calendar

# os.environ['PROJ_LIB'] = r'C:\Users\zzz\anaconda3\envs\patrol\Library\share\proj'

'''
处理AATSR数据
'''

ifread = 1

# def assign_spatial_reference(filepath):
#     sr = osr.SpatialReference()
#     sr.ImportFromEPSG(4326)  # 地理坐标投影
#
#     ds = gdal.Open(filepath, gdal.GA_Update)
#     ds.SetProjection(sr.ExportToWkt())
#     ds.SetGeoTransform([0, 1, 0, 0, 0, 1])  # 地理6参数
#
#     ds = None


# def write_raw_image(output_dir, product, band_name):
#     """Generate the ENVI binary pattern image file for an actual DS.
#
#     The first parameter is the output directory path.
#     """
#     # Build ENVI file path, DS name specifically
#     # image_file_path = os.path.join(output_dir, band_name + ".raw")
#     image_file_path = output_dir + ".raw"
#
#     band = product.get_band(band_name)
#     source_w = product.get_scene_width()
#     source_h = product.get_scene_height()
#     source_step_x = 1
#     source_step_y = 1
#
#     raster = band.create_compatible_raster(source_w, source_h,
#                                            source_step_x, source_step_y)
#
#     print(f"Reading band {band_name!r}...")
#     raster = band.read_raster(0, 0, raster)
#
#     with open(image_file_path, "wb") as out_stream:
#         for line in raster.data:
#             out_stream.write(line.tostring())
#         # or better: raster.data.tofile(out_stream)
#
#     print(f"Raw image data successfully written to {image_file_path!r}.")
#     print("C data type is %r, element size %u byte(s), "
#           "raster size is %u x %u pixels." % (
#               epr.data_type_id_to_str(raster.data_type),
#               raster.get_elem_size(),
#               raster.get_width(),
#               raster.get_height()))

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

indir_raw_ = r"F:\2010\raw\\"
indir_tif_ = r"F:\2010\tif\\"
symbol = "AATSR"

'''读取数据'''
for year in range(2010,2011):
    for month in range(5,6):
        daynum = calendar.monthrange(year,month)[1]
        for day in range(27,32):
            # time_str = "%04d//" % year + "%02d//" % month + "%02d//" % (day+1)
            time_str = "%02d//" % month + "%02d//" % (day + 1)
            indir_raw = indir_raw_ + time_str
            if not os.path.exists(indir_raw): continue
            indir_tif = indir_tif_ + time_str
            mkdir_if_not_exist(indir_tif)
            fileNames = search_file_rej(indir_raw, ['ATS_TOA'],'.md5')
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
                print(infile)
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
                try:
                    band = product.get_band('btemp_nadir_1100')
                    bt1_n = band.read_as_array()
                    band = product.get_band('btemp_nadir_1200')
                    bt2_n = band.read_as_array()

                    band = product.get_band('btemp_fward_1100')
                    bt1_f = band.read_as_array()
                    band = product.get_band('btemp_fward_1200')
                    bt2_f = band.read_as_array()
                except Exception as e:
                    print("file damaged!")
                    continue

                '''读取可见光信息'''
                # band = product.get_band('reflec_nadir_0670')
                # red_n = band.read_as_array()
                # band = product.get_band('reflec_nadir_0870')
                # nir_n = band.read_as_array()
                #
                # band = product.get_band('reflec_fward_0670')
                # red_f = band.read_as_array()
                # band = product.get_band('reflec_fward_0870')
                # nir_f = band.read_as_array()

                '''读取云层信息'''
                band = product.get_band('cloud_flags_nadir')
                try:
                    cloud_n = band.read_as_array()
                    band = product.get_band('cloud_flags_fward')
                    cloud_f = band.read_as_array()
                except Exception as e:
                    cloud_n = np.zeros([height,width])
                    cloud_f = np.zeros([height,width])



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
                try :
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
                except Exception as e:
                    print("file damaged!")
                    continue

                # 'red/nir *100'
                # red_n[red_n < 0] = 0
                # red_n_save = red_n[:nl, :ns]*100
                # write_image_gdal(red_n_save.astype(uint16), ns, nl, 1, '', '', red_n_dir)
                # nir_n[nir_n < 0] = 0
                # nir_n_save = nir_n[:nl, :ns]*100
                # write_image_gdal(nir_n_save.astype(uint16), ns, nl, 1, '', '', nir_n_dir)
                # red_f[red_f < 0] = 0
                # red_f_save = red_f[:nl, :ns]*100
                # write_image_gdal(red_f_save.astype(uint16), ns, nl, 1, '', '', red_f_dir)
                # nir_f[nir_f < 0] = 0
                # nir_f_save = nir_f[:nl, :ns]*100
                # write_image_gdal(nir_f_save.astype(uint16), ns, nl, 1, '', '', nir_f_dir)

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
