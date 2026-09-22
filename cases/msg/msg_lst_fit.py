import os
from osgeo import gdal
from satpy import Scene
import numpy as np
from numpy import min
from base.dates import date2DOY
from base.files import mkdir_if_not_exist, read_image_gdal, read_txt_array, search_file
from base.lsct import ndvi_max_g, ndvi_min_g
from base.spatial import loc2map, resize_data

def write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff',
                     nodata_value=None):
    # 处理输入参数冲突
    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    elif len(im_data.shape) == 2:
        im_data = np.array([im_data])
        im_bands = 1
    else:
        im_data = np.array([im_data])
        im_bands = 1
        im_height, im_width = im_data.shape[1], im_data.shape[2] if im_data.ndim > 2 else im_data.shape[1]

    # 自动检测数据类型
    im_bands = int(im_bands)
    im_height = int(im_height)
    im_width = int(im_width)
    dtype_name = im_data.dtype.name.lower()  # 统一转小写判断

    if 'uint8' in dtype_name or 'int8' in dtype_name:
        datatype = gdal.GDT_Byte
        default_nodata = 255
    elif 'uint16' in dtype_name:  # 修正大小写
        datatype = gdal.GDT_UInt16
        default_nodata = 0
    elif 'int16' in dtype_name:
        datatype = gdal.GDT_Int16
        default_nodata = -32768
    elif 'uint32' in dtype_name:
        datatype = gdal.GDT_UInt32
        default_nodata = 0
    elif 'int32' in dtype_name:
        datatype = gdal.GDT_Int32
        default_nodata = -2147483648
    elif 'float32' in dtype_name:
        datatype = gdal.GDT_Float32
        default_nodata = np.nan
    elif 'float64' in dtype_name:
        datatype = gdal.GDT_Float64
        default_nodata = np.nan
    else:
        datatype = gdal.GDT_Float32
        default_nodata = np.nan

    if nodata_value is None:
        nodata_value = default_nodata

    driver = gdal.GetDriverByName(imageType)
    dataset = driver.Create(path, im_width, im_height, im_bands, datatype)

    if dataset is not None:
        if im_trans is not None and im_trans != '':
            dataset.SetGeoTransform(im_trans)
        if im_proj is not None and im_proj != '':
            dataset.SetProjection(im_proj)

        for i in range(im_bands):
            band = dataset.GetRasterBand(i + 1)
            band.WriteArray(im_data[i])
            if not (isinstance(nodata_value, float) and np.isnan(nodata_value)):
                band.SetNoDataValue(nodata_value)
            else:
                band.SetNoDataValue(-9999)  # 对于NaN，TIFF通常建议设置一个物理掩码值
            band.FlushCache()
            band.ComputeStatistics(False)
    del dataset
    return 1


deg2rad = np.pi / 180
NS_PER_HR = 1.e9 * 3600.
elev = 0
altitude = 0
pressure = 1013.25  # 单位：mb
atmos_refract = 0.5667
ndvi_min = ndvi_min_g
ndvi_max = ndvi_max_g

indir_raw = r"/Users/bianzj/Downloads/data/msg/msg_raw/"
indir_tif = r"/Users/bianzj/Downloads/data/msg/msg_tif/"
indir_lst = r"/Users/bianzj/Downloads/data/msg/msg_lst/"
indir_base = "/Users/bianzj/Downloads/data/msg/Static/Disk/"
infile_emis1 = "/Users/bianzj/Downloads/data/msg/msg_euro_emis1.tif"
infile_emis2 = "/Users/bianzj/Downloads/data/msg/msg_euro_emis2.tif"
infile_type = "/Users/bianzj/Downloads/data/msg/msg_euro_type.tif"
infile_veg_emis = "/Users/bianzj/Downloads/data/msg/IGBP_Emi.txt"
indir_tcw = r"/Users/bianzj/Downloads/data/msg/"

# 读取经纬度
infile = os.path.join(indir_base, "EURO_lat.tif")
lat0, ns, nl, nb, geog, proj = read_image_gdal(infile)
infile = os.path.join(indir_base, "EURO_lon.tif")
lon0, ns, nl, nb, geog, proj = read_image_gdal(infile)

lat0 = lat0 / 100.0
lon0 = lon0 / 100.0
ns_short = np.int16(ns / 20)
nl_short = np.int16(nl / 20)
lat = resize_data(lat0, nl_short, ns_short)
lon = resize_data(lon0, nl_short, ns_short)
ind = (lat < -90) | (lat > 90)
lat[ind] = np.nan
lon[ind] = np.nan


tcw_dir_0 = r"/home/hero/data/SLSTR_heihe/tcwv/tif/180/ERA5_tcw_2022_180_00.tif"
dataset = gdal.Open(tcw_dir_0)
indx, indy = loc2map(lat0, lon0, dataset)


[emis1_s, ns, nl, nb, geog, proj] = read_image_gdal(infile_emis1)
emis1_s = emis1_s / 1000.0
[emis2_s, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_emis2)
emis2_s = emis2_s / 1000.0
[classif, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_type)
classif = np.asarray(classif, int)
emis_v = read_txt_array(infile_veg_emis, 0, 2)

infile = os.path.join(indir_base, "EURO_vza.tif")
vza, ns, nl, nb, geog, proj = read_image_gdal(infile)
infile = os.path.join(indir_base, "EURO_vaa.tif")
vaa, ns, nl, nb, geog, proj = read_image_gdal(infile)

infile14 = 'Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt'
infile15 = 'Sentinel3A_SLSTR_SW_Seebor_Coef_Night.txt'
coeffs_day = read_txt_array(infile14, 0, 15)
coeffs_day = coeffs_day[:, 2:10]
coeffs_night = read_txt_array(infile15, 0, 15)
coeffs_night = coeffs_night[:, 2:10]


for kyear in range(2017, 2018):
    for kmonth in range(7, 8):
        for kday in range(1, 2):
            day_str_path = f'{kyear:04d}/{kmonth:02d}/{kday:02d}/'
            indir_temp = os.path.join(indir_raw, day_str_path)
            outdir_temp = os.path.join(indir_tif, day_str_path)

            files = search_file(indir_temp, "nat")
            if len(files) == 0: continue

            mkdir_if_not_exist(outdir_temp)
            kdoy = date2DOY(kyear, kmonth, kday)

            for kfile in range(len(files)):
                file = files[kfile]
                infile = os.path.join(indir_temp, file)
                print(f"Processing: {infile}")

                # 解析时间
                date_str = file[-32:-24]
                hh_int = int(file[-24:-22])
                mn_int = int(file[-22:-20])

                # if hh_int <= 3 or hh_int >= 20: continue

                # 优化 Satpy 读取：只实例化一次并批量 load
                scn = Scene(filenames={"seviri_l1b_native": [infile]}, reader_kwargs={'fill_disk': True})

                # 一次性加载所有需要的通道
                channels = ['VIS006', 'VIS008', 'IR_016', 'IR_108', 'IR_120']
                scn.load(['VIS006', 'VIS008', 'IR_016'], calibration='reflectance')
                scn.load(['IR_108', 'IR_120'], calibration='brightness_temperature')

                VIS006_ref = scn['VIS006'].values
                VIS008_ref = scn['VIS008'].values
                # IR016_ref = scn['IR_016'].values
                BT8 = scn['IR_108'].values
                BT9 = scn['IR_120'].values

                # 计算太阳角度
                # time_val = pd.to_datetime(f"{date_str} {hh_int:02d}:{mn_int:02d}:00").tz_localize('UTC')
                # site_temp = Location(lat_.flatten(), lon_.flatten(), 'Etc/GMT', altitude, 'None')
                # nloc = len(lat_.flatten())
                # solpos_temp = pvlib.solarposition.get_solarposition(np.repeat(time_val,nloc), site_temp.latitude,site_temp.longitude, site_temp.altitude,method='nrel_numpy')
                # sza_temp = solpos_temp['zenith'].to_numpy().reshape(lat_.shape).astype(np.float32)
                # saa_temp = solpos_temp['azimuth'].to_numpy().reshape(lat_.shape).astype(np.float32)

                ndvi = (VIS008_ref - VIS006_ref)/(VIS008_ref+VIS006_ref)
                fvc = (ndvi - ndvi_min) / (ndvi_max - ndvi_min)
                fvc = resize_data(fvc, nl, ns)
                fvc[fvc > 1] = 1
                fvc[fvc < 0] = 0

                ind0 = (classif < 17) * (classif > 0)



                # 读取水汽
                if hh_int != 23:
                    tcw_filename1 = "ERA5_tcw_" + "%04d_" % kyear + "%03d_" % kdoy + "%02d.tif" % hh_int
                    tcw_filename2 = "ERA5_tcw_" + "%04d_" % kyear + "%03d_" % kdoy + "%02d.tif" % (hh_int + 1)
                else:
                    if kdoy >= 365: continue
                    tcw_filename1 = "ERA5_tcw_" + "%04d_" % kyear + "%03d_" % kdoy + "%02d.tif" % hh_int
                    tcw_filename2 = "ERA5_tcw_" + "%04d_" % kyear + "%03d_" % (kdoy + 1) + "00.tif"
                tcw_dir1 = indir_tcw + "/%03d/" % kdoy + tcw_filename1
                tcw_dir2 = indir_tcw + "/%03d/" % kdoy + tcw_filename2
                [tcw1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir1)
                [tcw2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(tcw_dir2)
                f = min / 60
                tcw_data = (f * tcw2 + (1 - f) * tcw1) / 100 / 10
                tcw = tcw_data[indx, indy]
                tcw = np.reshape(tcw, [nl, ns])

                # tcw = tcw / 10.0
                # tcw = resize_data_near(tcw,nl0,ns0)
                # tcw = np.zeros([nl,ns])
                # tcw[:] = 1.0

                classif[102, 95] = 5
                emis1_v = emis_v[classif, 0] / 1000.0
                emis2_v = emis_v[classif, 1] / 1000.0
                emis1_v = np.reshape(emis1_v, [nl, ns])
                emis2_v = np.reshape(emis2_v, [nl, ns])

                F = 0.05  # 地形因子
                C1 = (1 - emis1_s) * emis1_v * F * (1 - fvc)  # 多次散射项
                C2 = (1 - emis2_s) * emis2_v * F * (1 - fvc)  # 多次散射项
                emis8 = emis1_s * (1 - fvc) + emis1_v * fvc + C1
                emis9 = emis2_s * (1 - fvc) + emis2_v * fvc + C2
                emis8[emis8 > 0.995] = 0.995
                emis9[emis9 > 0.995] = 0.995

                # emis8 = emis1_s * (1 - fvc) + emis1_v * fvc
                # emis9 = emis2_s * (1 - fvc) + emis2_v * fvc

                emis = (emis8 + emis9) * 0.5
                demis = emis8 - emis9
                x3 = np.zeros([nl, ns])
                x4 = np.zeros([nl, ns])
                x6 = np.zeros([nl, ns])
                x7 = np.zeros([nl, ns])
                x1 = 1
                x2 = (BT8 + BT9) / 2.0
                ind = emis != 0
                x3[ind] = (1 - emis[ind]) / emis[ind] * x2[ind]
                x4[ind] = demis[ind] / (emis[ind] * emis[ind]) * x2[ind]
                x5 = (BT8 - BT9) / 2
                x6[ind] = (1 - emis[ind]) / emis[ind] * x5[ind]
                x7[ind] = demis[ind] / (emis[ind] * emis[ind]) * x5[ind]
                x8 = (BT8 - BT9) * (BT8 - BT9)

                wvc_ = np.asarray([0, 1.25, 2.25, 3.25, 4.25, 5.25, 100])
                vza_ = np.asarray([0, 3, 14.9, 38.6, 44.5, 51.2, 58, 65, 70, 75, 80])

                LST = np.zeros([nl, ns])
                for kwvc in range(len(wvc_) - 1):
                    for kvza in range(len(vza_) - 1):

                        ind = (tcw >= wvc_[kwvc]) * (tcw < wvc_[kwvc + 1]) * (vza >= vza_[kvza]) * (
                                    vza < vza_[kvza + 1]) * (
                                      BT8 > 0) * (emis8 > 0) * ind0
                        if (np.sum(ind) <= 0): continue

                        ##########################################
                        ### the normal result
                        ##########################################

                        ind1 = kvza * 6 + kwvc
                        ind2 = (kvza + 1) * 6 + kwvc
                        coeff1 = coeffs_day[ind1, :]
                        coeff2 = coeffs_day[ind2, :]
                        vzatemp = vza[ind]
                        prop2 = (vzatemp - vza_[kvza]) / (vza_[kvza + 1] - vza_[kvza])
                        prop1 = 1 - prop2
                        LSTtemp = x1 * (prop1 * coeff1[0] + coeff2[0] * prop2) + x2[ind] * (
                                prop1 * coeff1[1] + coeff2[1] * prop2) + \
                                  x3[ind] * (prop1 * coeff1[2] + coeff2[2] * prop2) + x4[ind] * (
                                          prop1 * coeff1[3] + coeff2[3] * prop2) + \
                                  x5[ind] * (prop1 * coeff1[4] + coeff2[4] * prop2) + x6[ind] * (
                                          prop1 * coeff1[5] + coeff2[5] * prop2) + \
                                  x7[ind] * (prop1 * coeff1[6] + coeff2[6] * prop2) + x8[ind] * (
                                          prop1 * coeff1[7] + coeff2[7] * prop2)

                        LST[ind] = LSTtemp

                ind = LST > 365
                LST[ind] = 365
                ind = LST < 220
                LST[ind] = 0
                outfile = indir_lst + file + 'lst.tif'
                write_image_gdal(LST, ns, nl, 1, geog, proj, outfile)
