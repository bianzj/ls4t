from util.util import *
# import rasterio as rio
# from geopandas import GeoSeries
# import rasterio.mask
# from rasterio.warp import (reproject,Resampling, transform_bounds,calculate_default_transform as calcdt)

'''
将一条航带中所有的图像都投影到一个感兴趣区，然后将会得到
data/vza/vaa 3个文件

流程如下：
1. 找到并展开感兴趣区；
2. 如果图像中包含感兴趣区，提取出来；
3. 根据相机与图像的相对位置，计算角度；
4. 把数据及其对应的角度，保存成一个很大的数组/3维图像；
'''

def read_txt2pos(infile,numskip):
    pos_ = []
    fileName_ = []
    with open(infile) as f:
        for kskip in range(numskip): lines = f.readline()
        lines = f.readline()
        while lines:
            fields = lines.split()
            fileName_.append(fields[0])
            pos_.append(fields[1:4])
            lines = f.readline()
    pos_ = np.asarray(pos_,dtype=float)
    return fileName_,pos_




wdir = r'F:\UAVpro\20200918huailai\1045\TIR_result/'

infile = r'F:\UAVpro\20200918huailai\1045\cameras_tir.txt'
# blackdir = r'F:\UAVpro\20200604huailai\1201\black_nir_result\\'
# whitedir = r'F:\UAVpro\20200604huailai\1201\white_nir_result\\'
# graydir = r'F:\UAVpro\20200604huailai\1201\gray_nir_result\\'

fileNames = search_file(wdir,'tif')
fileNum = len(fileNames)

###################################
###

num_threshold = 1000
min_dn = 7000
max_dn = 7500
min_num = 10
max_num = 20

track09181429 = np.asarray([[211,336],[360,455],[470,570],[570,670],[680,780],[780,880],
                            [930,1030],[1040,1140],[1150,1240],[1245,1335],[1345,1435],[1450,1550]])
track09181211 = np.asarray([[400,510],[520,670],[680,780],[790,890],[900,1010],[1020,1120],
                            [1200,1300],[1300,1400],[1400,1510],[1515,1615],[1620,1720],[1730,1830]])
track09181045 = np.asarray([[730,790],[795,855],[860,920],[930,1020],[1020,1080],[1090,1145],[1150,1200],[1210,1260],
                            [1300,1370],[1380,1444],[1460,1530],[1540,1620],[1620,1690],[1690,1760],[1770,1835],[1840,1916]])


##################
### 研究区
infile_studyarea = r'F:\UAVpro\20200918huailai\1045\tir_ref.tif'
ref_data, ref_width, ref_height, ref_band, ref_geotrans, ref_proj, ref_dataset = read_image_dataset_gdal(infile_studyarea)
outdir = r'F:\UAVpro\20200918huailai\1045\Ref_result\\'
### 获取到研究区的经纬度
ref_x = np.zeros([ref_height, ref_width], dtype=np.int)
ref_y = np.zeros([ref_height, ref_width], dtype=np.int)
temp_data = np.arange(0, ref_width)
for k in range(ref_height):
    ref_x[k, :] = k
    ref_y[k, :] = temp_data
ref_geox, ref_geoy = imagexy2geo(ref_dataset, ref_x, ref_y)
ref_lon, ref_lat = geo2lonlat(ref_dataset, ref_geox, ref_geoy)


################## GPS DATA

fileNamePos,pos = read_txt2pos(infile,2)

#################################
for ktrack in range(16):
    min_num = track09181045[ktrack][0]
    max_num = track09181045[ktrack][1]
    klayer = 0
    temp_data_ = []
    temp_zenith_ = []
    temp_azimuth_ = []
    for kimage in range(0,fileNum):
        ### 每张图像
        filename = fileNames[kimage][:-4]
        number = filename[:5]
        if np.int(number) < min_num:continue
        if np.int(number) > max_num:continue
        infile = wdir + filename+'.tif'
        ### 每张图像得到结果, 并且将该图像展开在参考图像上
        temp_data, temp_width, temp_height, temp_band, temp_geotrans, temp_proj, temp_dataset = read_image_dataset_gdal(infile)
        temp_geox,temp_geoy = lonlat2geo(temp_dataset,ref_lat,ref_lon)
        temp_y,temp_x = geo2imagexy(temp_dataset,temp_geox,temp_geoy)
        ### temp_y 是行
        ### temp_x 是列
        temp_x = np.asarray(temp_x, np.int)
        temp_y = np.asarray(temp_y, np.int)
        ind = (temp_x > 0) * (temp_x < temp_width - 1) * (temp_y > 0) * (temp_y < temp_height - 1)
        temp_x[temp_x < 0] = 0
        temp_x[temp_x > temp_width - 1] = temp_width - 1
        temp_y[temp_y < 0] = 0
        temp_y[temp_y > temp_height - 1] = temp_height - 1
        temp_data = temp_data[temp_y, temp_x]
        if np.sum(temp_data > 7000) <= num_threshold: continue
        temp_data = np.reshape(temp_data, [ref_height, ref_width])
        temp_data_.append(temp_data)
        klayer = klayer + 1

        ####
        #########################################################################
        ### 飞行姿态数据
        kpos = fileNamePos.index(filename)
        if kpos < 0: continue
        camera_lat = pos[kpos, 1]
        camera_lon = pos[kpos, 0]
        camera_height = pos[kpos, 2]

        ###############################################################################
        #### calculate viewing angle for each pixel in this file
        camera_geox, camera_geoy = lonlat2geo(temp_dataset, camera_lat, camera_lon)
        # camera_y1, camera_x1 = geo2imagexy(ref_dataset, camera_geox, camera_geoy)

        distance = np.sqrt((temp_geox - camera_geox) * (temp_geox - camera_geox) +
                           (temp_geoy - camera_geoy) * (temp_geoy - camera_geoy))
        temp_zenith = np.arctan(distance / camera_height) / np.pi * 180.0
        temp_azimuth = np.arctan2((ref_lon - camera_lon), (ref_lat - camera_lat)) / np.pi * 180.0
        temp_azimuth = ((temp_azimuth + 360.0 + 180.0) % 360.0)
        temp_azimuth = np.reshape(temp_azimuth, [ref_height, ref_width])
        temp_zenith = np.reshape(temp_zenith, [ref_height, ref_width])
        # temp_zenith = np.asarray(temp_zenith, dtype=np.int)
        # temp_azimuth = np.asarray(temp_azimuth, dtype=np.int)
        temp_zenith_.append(temp_zenith)
        temp_azimuth_.append(temp_azimuth)



    temp_data_ = np.asarray(temp_data_)
    temp_zenith_ = np.asarray(temp_zenith_)
    temp_azimuth_ = np.asarray(temp_azimuth_)
    outfile = outdir + 'ref_data_track%02d'%ktrack+'.tif'
    write_image_gdal(temp_data_,ref_width,ref_height,klayer,ref_geotrans,ref_proj,outfile)
    outfile = outdir + 'ref_vaa_track%02d'%ktrack+'.tif'
    write_image_gdal(temp_azimuth_,ref_width,ref_height,klayer,ref_geotrans,ref_proj,outfile)
    outfile = outdir + 'ref_vza_track%02d'%ktrack+'.tif'
    write_image_gdal(temp_zenith_,ref_width,ref_height,klayer,ref_geotrans,ref_proj,outfile)



