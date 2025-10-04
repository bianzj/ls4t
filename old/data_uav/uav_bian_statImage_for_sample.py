from util.util import *
# import rasterio as rio
# from geopandas import GeoSeries
# import rasterio.mask
# from rasterio.warp import (reproject,Resampling, transform_bounds,calculate_default_transform as calcdt)

'''
将一条航带数据的所有的图像进行方向亮温提取和平均，最后输出了角度变化，输出观测方位角和天顶角，观测结果是图像的平均值
这是接着“uav_bian_cutImage_for_sample.py”的结果进行后续处理
流程如下：
1. 基于图像坐标和传感器坐标，计算角度；
2. 进行角度和亮温的平均，输出每个图像的结果；
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



sample = 'yangshu'


wdir = r'F:\UAVpro\20200918huailai\1429\\'+sample+'_result/'

infile = r'F:\UAVpro\20200918huailai\1429\cameras_tir.txt'
# blackdir = r'F:\UAVpro\20200604huailai\1201\black_nir_result\\'
# whitedir = r'F:\UAVpro\20200604huailai\1201\white_nir_result\\'
# graydir = r'F:\UAVpro\20200604huailai\1201\gray_nir_result\\'

fileNames = search_file(wdir,'tif')
number = len(fileNames)

###################################
### med track
minNumber = 200
maxNumber = 3000
outfile = r'F:\UAVpro\20200918huailai\1429\\'+sample+'_result/track.txt'
# minNumber = 1500
# maxNumber = 1650
# outfile = r'F:\UAVpro\20200604huailai\1201\\'+sample+'_'+band+'_result/track22.txt'

number_threshold = 0
min_dn = 7000
max_dn = 7500



################## GPS DATA

fileNamePos,pos = read_txt2pos(infile,2)

#################################
result_ = []
for kimage in range(5,number):

    filename = fileNames[kimage][:-4]
    number = filename[:5]
    if np.int(number) < minNumber:continue
    if np.int(number) > maxNumber:continue

    infile = wdir + filename+'.tif'

    ########################################################
    # blackfile = blackdir + filename+'.tif'
    # whitefile = whitedir + filename+'.tif'
    # grayfile = graydir +filename+'.tif'
    # if(os.path.exists(blackfile) and os.path.exists(whitefile) and os.path.exists(graydir)):
    #     [black,temp,temp,temp,temp,temp] = read_image_gdal(blackfile)
    #     [white,temp,temp,temp,temp,temp] = read_image_gdal(whitefile)
    #     [gray,temp,temp,temp,temp,temp] = read_image_gdal(grayfile)
    # else:
    #     continue
    # ind = (black > min_dn) *(black < max_dn)
    # result_black = np.average(black[ind])
    # ind = (white > min_dn) * (white < max_dn)
    # result_white = np.average(white[ind])
    # ind = (gray > min_dn) * (gray < max_dn)
    # result_gray = np.average(gray[ind])




    #########################################################################
    kpos = fileNamePos.index(filename)
    if kpos < 0: continue
    camera_lat = pos[kpos, 1]
    camera_lon = pos[kpos, 0]
    camera_height = pos[kpos, 2]

    ##########################################################################
    dataset1 = gdal.Open(infile)
    temp_width1 = dataset1.RasterXSize
    temp_height1 = dataset1.RasterYSize
    temp_geotrans1 = dataset1.GetGeoTransform()
    temp_proj1 = dataset1.GetProjection()
    temp_data1 = dataset1.ReadAsArray(0, 0, temp_width1, temp_height1)
    temp_x1 = np.zeros([temp_height1, temp_width1], dtype=np.int)
    temp_y1 = np.zeros([temp_height1, temp_width1], dtype=np.int)
    temp = np.arange(0, temp_width1)
    for k in range(temp_height1):
        temp_x1[k, :] = k
        temp_y1[k, :] = temp
    temp_geox1, temp_geoy1 = imagexy2geo(dataset1, temp_x1, temp_y1)
    temp_lon1, temp_lat1 = geo2lonlat(dataset1, temp_geox1, temp_geoy1)

    ###############################################################################
    #### calculate viewing angle for each pixel in this file
    camera_geox1, camera_geoy1 = lonlat2geo(dataset1, camera_lat,camera_lon)
    camera_y1, camera_x1 = geo2imagexy(dataset1, camera_geox1, camera_geoy1)


    distance = np.sqrt((temp_geox1 - camera_geox1) * (temp_geox1 - camera_geox1) +
                       (temp_geoy1 - camera_geoy1) * (temp_geoy1 - camera_geoy1))
    temp_zenith = np.arctan(distance / camera_height) / np.pi * 180.0
    temp_azimuth = np.arctan2((temp_lon1 - camera_lon), (temp_lat1 - camera_lat)) / np.pi * 180.0
    temp_azimuth = ((temp_azimuth + 360.0 + 180.0) % 360.0)
    temp_azimuth = np.reshape(temp_azimuth, [temp_height1, temp_width1])

    temp_zenith = np.asarray(temp_zenith, dtype=np.int)
    temp_azimuth = np.asarray(temp_azimuth, dtype=np.int)

    #################################################################################
    ind = (temp_data1 > min_dn) *(temp_data1<max_dn) * (np.isnan(temp_data1)<1)

    number_threshold =temp_width1*temp_height1

    if(np.sum(ind) < number_threshold): continue
    result_data    = np.average(temp_data1[ind])
    result_azimuth = np.average(temp_azimuth[ind])
    result_zenith  = np.average(temp_zenith[ind])

    print(number,result_azimuth,result_zenith,result_data)
    result = np.hstack([result_azimuth,result_zenith,result_data])
    result_.append(result)

result_ = np.asarray(result_)
np.savetxt(outfile,(result_),fmt='%5.3f')



