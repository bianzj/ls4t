from utils.old.util import *
import zipfile
from datetime import datetime, timedelta

def unzip_single_file_from_zip(zip_file_path, output_directory):
    try:
        # 打开zip文件
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # 获取zip文件的名称（不带扩展名）
            zip_file_name = os.path.splitext(os.path.basename(zip_file_path))[0]

            # 获取zip文件中唯一的文件名
            extracted_file_name = zip_ref.namelist()[0]

            # 从zip文件中提取唯一的文件
            extracted_file = zip_ref.extract(extracted_file_name, output_directory)

            # 重命名提取的文件为zip文件的名称
            new_file_path = os.path.join(output_directory, f"{zip_file_name}{os.path.splitext(extracted_file_name)[1]}")
            os.rename(extracted_file, new_file_path)
            print(new_file_path)

            return new_file_path
    except zipfile.BadZipFile:
        print(f"错误：{zip_file_path} 不是一个有效的zip文件")
        return None
    except Exception as e:
        print(f"解压缩 {zip_file_path} 时出现错误：{str(e)}")
        return None


def write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale, noDataValues, bandnumbers):
    '''
    导出用于gdal vrt的配置文件
    :param vrtfile: 该配置文件名称
    :param datafile: 所要操作的文件名称
    :param xfile: 经度坐标文件 lon
    :param yfile: 纬度坐标文件 lat
    :param xscale: 列数
    :param yscale: 行数
    :param noDataValues: 无效值列表，每个波段的无效值
    :param bandnumbers: 波段编号列表，每个波段的编号
    :return: 无
    '''
    f = open(vrtfile, 'w')
    f.write(r'<VRTDataset rasterXSize="%d"' % xscale + ' rasterYSize="%d">' % yscale)
    f.write('\n')
    f.write(r'  <Metadata domain="GEOLOCATION">')
    f.write('\n')
    f.write(
        r'    <MDI key="SRS">GEOGCS["WGS 84(DD)",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AXIS["Long",EAST],AXIS["Lat",NORTH]]</MDI>')
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

    for bandnumber, noDataValue in zip(bandnumbers, noDataValues):
        f.write(r'  <VRTRasterBand dataType="Uint16" band="%d">' % bandnumber)
        f.write('\n')
        f.write(r'    <ColorInterp>Gray</ColorInterp>')
        f.write('\n')
        f.write(r'    <NoDataValue>%d</NoDataValue>' % noDataValue)
        f.write('\n')
        f.write(r'    <SimpleSource>')
        f.write('\n')
        f.write(r'      <SourceFilename relativeToVRT="1">' + datafile + r'</SourceFilename>')
        f.write('\n')
        f.write(r'      <SourceBand>%d</SourceBand>' % bandnumber)
        f.write('\n')
        f.write(r'    </SimpleSource>')
        f.write('\n')
        f.write(r'  </VRTRasterBand>')
        f.write('\n')

    f.write('</VRTDataset>')
    f.close()
    return 1


def hours_to_datetime(hours_since_1900):
    if isinstance(hours_since_1900, int):
        hours_since_1900 = [hours_since_1900]
    elif isinstance(hours_since_1900, np.ndarray):
        hours_since_1900 = hours_since_1900.tolist()

    result_list = []

    for hours in hours_since_1900:
        # 将hours转换为普通的Python整数
        hours = int(hours)

        # 1900年0点0分的时间
        base_time = datetime(1900, 1, 1, 0, 0, 0)

        # 计算时间差
        time_difference = timedelta(hours=hours)

        # 计算现在的时间
        current_time = base_time + time_difference

        # 提取年、月、日、小时
        year = current_time.year
        month = current_time.month
        day = current_time.day
        hour = current_time.hour

        result_list.append([year, month, day, hour])

    return result_list


'''ERA5_land'''
'''0.1度分辨率'''
'''包含产品：表皮温度，两米空气温度，土壤温度'''

indir = r'E:\ERA5_land_2002-2012\Monthly_Average_Hour\\'
infile_type = r"D:\data\type\type_world_10000.tif"

ifunzip = 0
ifreproj = 1

if ifunzip:
    for y in range(2002,2013):
        indir_year = indir + r'\zip\%04d\\' % y
        outdir_year = indir + r'\raw\%04d\\' % y
        fileNames = search_file(indir_year,['zip'])
        fileNum = len(fileNames)

        for i in range(fileNum):
            infile = indir_year + fileNames[i]
            unzip_single_file_from_zip(infile,outdir_year)

if ifreproj:
    indir_med = r'E:\ERA5_land_2002-2012\Monthly_Average_Hour\med\\'
    for y in range(2002,2013):
        indir_raw_year = indir + r'\raw\%04d\\' % y
        outdir_tif_year = indir + r'\tif_loc_11\%04d\\' % y
        mkdir_if_not_exist(outdir_tif_year)
        fileNames = search_file(indir_raw_year, ['.nc'])
        fileNum = len(fileNames)
        for k in range(fileNum):
            fileName = fileNames[k]
            infile = indir_raw_year + fileName
            print(k, infile)

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
            dif_hour = read_image_Nc(fileName, 'time', 1)
            time = hours_to_datetime(dif_hour)
            time = np.reshape(time,(-1,4))

            lat_data = read_image_Nc(fileName, 'latitude', 1)
            lon_data = read_image_Nc(fileName, 'longitude', 1)
            band, nl, ns = 3,1801,3600
            lon = np.zeros([nl, ns])
            # lon_data[lon_data >= 180] = lon_data[lon_data >= 180] - 360
            lat = np.zeros([nl, ns])
            for i in range(ns):
                lon[:, i] = lon_data[i]
            for i in range(nl):
                lat[i, :] = lat_data[i]

            # '''提取UTC_11'''
            # band, nl, ns = 3, 1801, 3600
            # ind = time[:,3]==11
            # lat_data = read_image_Nc(fileName, 'latitude', 1)
            # lon_data = read_image_Nc(fileName, 'longitude', 1)
            # skt = read_image_Nc(fileName, 'skt', 1)[ind]
            # stl1 = read_image_Nc(fileName, 'stl1', 1)[ind]
            # t2m = read_image_Nc(fileName, 't2m', 1)[ind]

            '''提取loc_11'''
            skt = np.zeros([1801,3600])
            stl1 = np.zeros([1801, 3600])
            t2m = np.zeros([1801, 3600])
            skt_raw = read_image_Nc(fileName, 'skt', 1)
            stl1_raw = read_image_Nc(fileName, 'stl1', 1)
            t2m_raw = read_image_Nc(fileName, 't2m', 1)
            skt_raw[skt_raw<0]=0
            stl1_raw[stl1_raw < 0] = 0
            t2m_raw[t2m_raw < 0] = 0
            for i in range(24):
                lon_center = i * 15
                lon_min = lon_center - 7.5
                lon_max = lon_center + 7.5
                t = 11 - i
                if t >= 24: t = t-24
                if t < 0 : t = t +24
                # print(i,lon_center,lon_min,lon_max,t)
                if lon_min > 0:
                    ind = (lon>lon_min) * (lon<=lon_max)
                elif lon_min < 0:
                    ind = (lon>lon_min) + (lon<=lon_max)
                ind_time = (time[:,3]==t)
                if t == 0:
                    ind_time_1 = (time[:,3]==0) * (time[:,2]==1)
                    ind_time_2 = (time[:,3]==0) * (time[:,2]==2)
                    skt[ind] = (np.reshape((skt_raw[ind_time_1]+skt_raw[ind_time_2]), [1801, 3600]))[ind]
                    stl1[ind] = (np.reshape(stl1_raw[ind_time_1]+stl1_raw[ind_time_2], [1801, 3600]))[ind]
                    t2m[ind] = (np.reshape(t2m_raw[ind_time_1]+t2m_raw[ind_time_2], [1801, 3600]))[ind]
                else:
                    skt[ind] = (np.reshape(skt_raw[ind_time], [1801, 3600]))[ind]
                    stl1[ind] = (np.reshape(stl1_raw[ind_time], [1801, 3600]))[ind]
                    t2m[ind] = (np.reshape(t2m_raw[ind_time], [1801, 3600]))[ind]



            data = np.zeros([3,1801,3600])
            data[0,:,:] = skt
            data[1,:,:] = stl1
            data[2,:,:] = t2m



            '''调整一下位置,太平洋中心->大西洋中心'''
            lon_save = np.zeros([nl, ns])
            lon_save[:, :1799] = lon[:, 1801:]
            lon_save[:, 1799:] = lon[:, :1801]
            data_save = np.zeros([band, nl, ns])
            data_save[:, :, :1799] = data[:, :, 1801:]
            data_save[:, :, 1799:] = data[:, :, :1801]
            lon = lon_save

            # data_save = data

            data_save = data_save * 100
            data_save[data_save > 65535] = 65500
            data_save[data_save <= 0] = 0

            '''六参数方法'''
            im_data,im_width,im_height,im_bands,im_geotrans,im_proj = read_image_gdal(infile_type)
            geo = [-180.0,0.1,0.0,90.0,0.0,-0.1]
            outfile = outdir_tif_year + fileNames[k][:-3] + '.tif'
            write_image_gdal((data_save).astype('uint16'), ns, nl, 3, geo, im_proj, outfile)


            '''vrt方法'''
            # '''输出位置'''
            # lat_dir = indir_med + 'lat.tif'
            # lon_dir = indir_med + 'lon.tif'
            # if not os.path.exists(lat_dir):
            #     write_image_gdal(lat[:nl, :ns], ns, nl, 1, '', '', lat_dir)
            #     write_image_gdal(lon[:nl, :ns], ns, nl, 1, '', '', lon_dir)
            #
            # data_dir = indir_med + 'data.tif'
            # write_image_gdal((data_save).astype('uint16'), ns, nl, 3, '', '', data_dir)
            # file = 'data'
            # datafile = indir_med + file + '.tif'
            # xfile = indir_med + 'lon.tif'
            # yfile = indir_med + 'lat.tif'
            # vrtfile = indir_med + file + '.vrt'
            # write_vrt(vrtfile, datafile, xfile, yfile, ns, nl,noDataValues=[65535,65535,65535], bandnumbers=[1,2,3])
            # outfile = outdir_tif_year + fileNames[k][:-3] + '.tif'
            # dst_ds = gdal.Warp(outfile,% vrtfile, resampleAlg=gdal.GRIORA_NearestNeighbour,
            #                    outputBounds=(-180, -90, 180, 90), xRes=0.1, yRes=0.1)

            # break



