import numpy as np
import matplotlib.pylab as plt
from scipy.interpolate import griddata
from scipy.linalg import lstsq
from osgeo import gdal
from osgeo import osr,ogr
import re
import scipy
import xlrd
import cv2
import os
import numpy as np
from util.util import *

'''
在太阳主平面方向，跑出来是个类似于widas的感兴趣区的多角度数据集
包括了对应的观测角度和统计数目
由于会有个参考角度的累计过程，为了不把不同的方位角但是相同天顶角的累计到一起，分别有太阳主平面和垂直太阳主平面的分割
'''


def calc_azimuth(lat1, lon1, lat2, lon2):
    lat1_rad = lat1 * np.pi / 180
    lon1_rad = lon1 * np.pi / 180
    lat2_rad = lat2 * np.pi / 180
    lon2_rad = lon2 * np.pi / 180

    y = np.sin(lon2_rad - lon1_rad) * np.cos(lat2_rad)
    x = np.cos(lat1_rad) * np.sin(lat2_rad) - \
        np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(lon2_rad - lon1_rad)

    brng = np.arctan2(y, x) * 180 / np.pi

    return float((brng + 360.0) % 360.0)

def ope_getSRSPair(dataset):
    '''
    获得给定数据的投影参考系和地理参考系
    :param dataset: GDAL地理数据
    :return: 投影参考系和地理参考系
    '''
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(dataset.GetProjection())
    geosrs = prosrs.CloneGeogCS()
    return prosrs, geosrs

def ope_search0(dir):
    results = os.listdir(dir)
    return results

def ope_search1(dir,specstr):
    results = []
    results += [x for x in os.listdir(dir) if os.path.isfile(os.path.join(dir, x)) and specstr in x]
    return results

def read_Tiff(fileName):
    dataset = gdal.Open(fileName)
    if dataset == None:
        print(fileName + "Canot open !!!")
        return
    im_width = dataset.RasterXSize  # 栅格矩阵的列数
    im_height = dataset.RasterYSize  # 栅格矩阵的行数
    im_bands = dataset.RasterCount  # 波段数
    im_data = dataset.ReadAsArray(0, 0, im_width, im_height)  # 获取数据
    im_geotrans = dataset.GetGeoTransform()  # 获取仿射矩阵信息
    im_proj = dataset.GetProjection()  # 获取投影信息
    return im_data,im_width,im_height,im_bands,im_geotrans,im_proj,dataset

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

def lonlat2geo(dataset, lon, lat):
    '''
        将经纬度坐标转为投影坐标（具体的投影坐标系由给定数据确定）
        :param dataset: GDAL地理数据
        :param lon: 地理坐标lon经度
        :param lat: 地理坐标lat纬度
        :return: 经纬度坐标(lon, lat)对应的投影坐标
    '''
    # dataset = gdal.Open(fileName, gdal.GA_ReadOnly)
    prosrs, geosrs = ope_getSRSPair(dataset)
    ct = osr.CoordinateTransformation(geosrs, prosrs)
    lon = np.reshape(lon,[-1])
    lat = np.reshape(lat,[-1])
    temp = np.asarray([lon,lat])
    temp = np.transpose(temp)
    coords = np.asarray(ct.TransformPoints(temp))
    # coords = ct.TransformPoints(lon,lat)
    return coords[:,0],coords[:,1]

def geo2imagexy(dataset, x, y):
    '''
    根据GDAL的六 参数模型将给定的投影或地理坐标转为影像图上坐标（行列号）
    :param dataset: GDAL地理数据
    :param x: 投影或地理坐标x
    :param y: 投影或地理坐标y
    :return: 影坐标或地理坐标(x, y)对应的影像图上行列号(row, col)
    '''
    trans = dataset.GetGeoTransform()
    a = np.array([[trans[1], trans[2]], [trans[4], trans[5]]])
    b = np.array([x - trans[0], y - trans[3]])
    return np.linalg.solve(a, b)  # 使用numpy的linalg.solve进行二元一次方程的求解

def geo2lonlat(dataset, x, y):
    '''
    将投影坐标转为经纬度坐标（具体的投影坐标系由给定数据确定）
    :param dataset: GDAL地理数据
    :param x: 投影坐标x
    :param y: 投影坐标y
    :return: 投影坐标(x, y)对应的经纬度坐标(lon, lat)
    '''
    prosrs, geosrs = ope_getSRSPair(dataset)
    ct = osr.CoordinateTransformation(prosrs, geosrs)
    x = np.reshape(x, [-1])
    y = np.reshape(y, [-1])
    temp = np.asarray([x, y])
    temp = np.transpose(temp)
    coords = np.asarray(ct.TransformPoints(temp))
    return coords[:,0],coords[:,1]

def imagexy2geo(dataset, row,col):
    '''
    根据GDAL的六参数模型将影像图上坐标（行列号）转为投影坐标或地理坐标（根据具体数据的坐标系统转换）
    :param dataset: GDAL地理数据
    :param row: 像素的行号
    :param col: 像素的列号
    :return: 行列号(row, col)对应的投影坐标或地理坐标(x, y)
    '''
    trans = dataset.GetGeoTransform()
    px = trans[0] + col * trans[1] + row * trans[2]
    py = trans[3] + col * trans[4] + row * trans[5]
    return px, py

def write_Tiff(im_data, im_width, im_height, im_bands, im_geotrans, im_proj, path):
    if 'int8' in im_data.dtype.name:
        datatype = gdal.GDT_Byte
    elif 'int16' in im_data.dtype.name:
        datatype = gdal.GDT_UInt16
    else:
        datatype = gdal.GDT_Float32

    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    elif len(im_data.shape) == 2:
        im_data = np.array([im_data])
    else:
        im_bands, (im_height, im_width) = 1, im_data.shape
        # 创建文件
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(path, im_width, im_height, im_bands, datatype)
    if (dataset != None and im_geotrans != '' and im_proj != ''):
        dataset.SetGeoTransform(im_geotrans)
        dataset.SetProjection(im_proj)
    for i in range(im_bands):
        dataset.GetRasterBand(i + 1).WriteArray(im_data[i])
    del dataset


####################################################
indir = r'G:\UAVpro\20200604huailai\1201\\'
# ### 06041201 track 1
track = 1
start = np.asarray([1680,5925])
end = np.asarray([2410+1,6660+1])
# ### 06041201 track 1
track = 2
start = np.asarray([2525,5050])
end = np.asarray([3275+1,5825+1])
# # ### 06041201 track 1
track = 3
start = np.asarray([3375,4215])
end = np.asarray([4125+1,4950+1])
###################################################
# indir = r'G:\UAVpro\20200604huailai\1401\\'
# # ### 06041401 track 1
# track = 1
# start = np.asarray([2010,6280])
# end = np.asarray([2710+1,6900+1])
# # ### 06041401 track 1
# track = 2
# start = np.asarray([2900,5340])
# end = np.asarray([3560+1,6020+1])
# # ### 06041401 track 1
# track = 3
# start = np.asarray([3725,4510])
# end = np.asarray([4400+1,5170+1])
###################################################
# indir = r'G:\UAVpro\20200615huailai\1001\\'
### 06151001 track 1
# track = 1
# start = np.asarray([1720,8375])
# end = np.asarray([2320+1,8975+1])
# ### 06151001 track 1
# track = 2
# start = np.asarray([2460,7610])
# end = np.asarray([3070+1,8215+1])
# ### 06151001 track 1
# track = 3
# start = np.asarray([3275,6870])
# end = np.asarray([3835+1,7445+1])
###################################################


#################### reference orth image
infile = indir + r'TIR_ref.tif'
temp,ref_width,ref_height,ref_band,ref_geotrans,ref_proj,refdataset = read_Tiff(infile)
numZen = 15
numAzim = 2
numAngle = 25
stepZen = 5

################## GPS DATA
infile = indir + r'cameras.txt'
fileNamePos,pos = read_txt2pos(infile,2)
################ INPUT FILE
indir = indir + r'TIR_result\\'
outdirmed = indir + r'TIR_result\\'
offz = 0

outdir = indir
offhalfz_ = np.asarray([12,12])
for kline in range(2):

    dbt = np.zeros([numAngle, ref_height, ref_width])
    vza = np.zeros([numAngle, ref_height, ref_width])
    vaa = np.zeros([numAngle, ref_height, ref_width])
    count = np.zeros([numAngle, ref_height, ref_width], dtype=np.int)

    for kimage in range(start[kline], end[kline],5):

        ####################################################
        ##### this file
        infile = "%05d"%(kimage)
        fileName = indir + infile+'.tif'
        if 1-os.path.exists(fileName):
            continue
        print(infile)
        #######################################################
        ### camera position in this file
        kpos = fileNamePos.index(infile)
        if kpos < 0: continue
        camera_lat = pos[kpos, 1]
        camera_lon = pos[kpos, 0]
        camera_height = pos[kpos, 2]


        #######################################################
        #### position for each pixel in this file
        dataset1 = gdal.Open(fileName)
        temp_width1 = dataset1.RasterXSize
        temp_height1 = dataset1.RasterYSize
        temp_geotrans1 = dataset1.GetGeoTransform()
        temp_proj1 = dataset1.GetProjection()
        temp_data1 = dataset1.ReadAsArray(0, 0, temp_width1, temp_height1)
        temp_data1 = temp_data1[0,:, :]
        temp_x1 = np.zeros([temp_height1, temp_width1], dtype=np.int)
        temp_y1 = np.zeros([temp_height1, temp_width1], dtype=np.int)
        temp = np.arange(0, temp_width1)
        for k in range(temp_height1):
            temp_x1[k, :] = k
            temp_y1[k, :] = temp
        temp_geox1, temp_geoy1 = imagexy2geo(dataset1, temp_x1, temp_y1)
        temp_lon1, temp_lat1 = geo2lonlat(dataset1, temp_geox1, temp_geoy1)
        ind = (temp_data1 < 3000)
        temp_data1[ind] = 0
        ind = (temp_data1 > 9000)
        temp_data1[ind] = 0

        #########################################################
        #### calculate viewing angle for each pixel in this file
        camera_geox1, camera_geoy1 = lonlat2geo(dataset1, camera_lon, camera_lat)
        camera_y1, camera_x1 = geo2imagexy(dataset1, camera_geox1, camera_geoy1)

        ref_geogx1, ref_geogy1 = lonlat2geo(refdataset, temp_lon1, temp_lat1)
        ref_y, ref_x = geo2imagexy(refdataset, ref_geogx1, ref_geogy1)
        distance = np.sqrt((temp_geox1 - camera_geox1) * (temp_geox1 - camera_geox1) +
                           (temp_geoy1 - camera_geoy1) * (temp_geoy1 - camera_geoy1))
        temp_zenith = np.arctan(distance / camera_height) / np.pi * 180.0
        temp_azimuth = np.arctan2((temp_lon1 - camera_lon), (temp_lat1 - camera_lat)) / np.pi * 180.0
        temp_azimuth = ((temp_azimuth + 360.0 + 180.0) % 360.0)
        temp_azimuth = np.reshape(temp_azimuth, [temp_height1, temp_width1])

        ### East-West difference for Cross-SPP
        # ref_z = np.zeros([temp_height1, temp_width1])
        # ind = (abs(temp_azimuth) > 0) * (abs(temp_azimuth) <= 90)
        # ref_z[ind] = offhalfz1 + np.asarray((temp_zenith[ind]+2.5) / stepZen,dtype=np.int)
        # ind = (abs(temp_azimuth) > 90) * (abs(temp_azimuth) <= 180)
        # ref_z[ind] = offhalfz1 + np.asarray((temp_zenith[ind]+2.5) / stepZen,dtype=np.int)
        # ind = (abs(temp_azimuth) > 270) * (abs(temp_azimuth) <= 360)
        # ref_z[ind] = offhalfz1 - np.asarray((temp_zenith[ind]+2.5) / stepZen,dtype=np.int)
        # ind = (abs(temp_azimuth) > 180) * (abs(temp_azimuth) <= 270)
        # ref_z[ind] = offhalfz1 - np.asarray((temp_zenith[ind]+2.5) / stepZen,dtype=np.int)

        ### North-South difference for SPP

        offhalfz = offhalfz_[kline]
        ref_z = np.zeros([temp_height1, temp_width1])
        ind = (abs(temp_azimuth) > 0) * (abs(temp_azimuth) <= 90)
        ref_z[ind] = offhalfz - np.asarray((temp_zenith[ind] + 2.5) / stepZen, dtype=np.int)
        ind = (abs(temp_azimuth) > 90) * (abs(temp_azimuth) <= 180)
        ref_z[ind] = offhalfz + np.asarray((temp_zenith[ind] + 2.5) / stepZen, dtype=np.int)
        ind = (abs(temp_azimuth) > 270) * (abs(temp_azimuth) <= 360)
        ref_z[ind] = offhalfz - np.asarray((temp_zenith[ind] + 2.5) / stepZen, dtype=np.int)
        ind = (abs(temp_azimuth) > 180) * (abs(temp_azimuth) <= 270)
        ref_z[ind] = offhalfz + np.asarray((temp_zenith[ind] + 2.5) / stepZen, dtype=np.int)

        #### This is for 4 phases in a Cartesian coordinate system.
        # ind = (abs(temp_azimuth) > 0) * (abs(temp_azimuth) <= 90)
        # ref_z[ind] = offhalfz1 - (temp_zenith[ind] / stepZen)
        # ind = (abs(temp_azimuth) > 90) * (abs(temp_azimuth) <= 180)
        # ref_z[ind] = offhalfz1 + (temp_zenith[ind] / stepZen)
        # ind = (abs(temp_azimuth) > 270) * (abs(temp_azimuth) <= 360)
        # ref_z[ind] = offhalfz2 - (temp_zenith[ind] / stepZen)
        # ind = (abs(temp_azimuth) > 180) * (abs(temp_azimuth) <= 270)
        # ref_z[ind] = offhalfz2 + (temp_zenith[ind] / stepZen)

        ref_z = ref_z.astype(np.int)
        ref_xx = np.reshape(ref_x.astype(np.int), [temp_height1, temp_width1])
        ref_yy = np.reshape(ref_y.astype(np.int), [temp_height1, temp_width1])

        ind = (temp_data1 > 3000) * (temp_data1 < 9000) * \
              (ref_xx >= 0) * (ref_xx < ref_height) * \
              (ref_yy >= 0) * (ref_yy < ref_width) * \
              (ref_z >= 0) * (ref_z < 25)
        if np.sum(ind) < 1: continue
        dbt[ref_z[ind], ref_xx[ind], ref_yy[ind]] = dbt[ref_z[ind], ref_xx[ind], ref_yy[ind]] + temp_data1[ind]
        vza[ref_z[ind], ref_xx[ind], ref_yy[ind]] = vza[ref_z[ind], ref_xx[ind], ref_yy[ind]] + temp_zenith[ind]

        vaa[ref_z[ind], ref_xx[ind], ref_yy[ind]] = (
                vaa[ref_z[ind], ref_xx[ind], ref_yy[ind]] * count[ref_z[ind], ref_xx[ind], ref_yy[ind]]
                + temp_azimuth[ind])
        indd = (vaa[ref_z[ind], ref_xx[ind], ref_yy[ind]] > 270) * (temp_azimuth[ind] < 90)
        vaa[ref_z[ind], ref_xx[ind], ref_yy[ind]][indd] = vaa[ref_z[ind], ref_xx[ind], ref_yy[ind]][indd] + 360
        indd = (vaa[ref_z[ind], ref_xx[ind], ref_yy[ind]] < 90) * (temp_azimuth[ind] > 270)
        vaa[ref_z[ind], ref_xx[ind], ref_yy[ind]][indd] = vaa[ref_z[ind], ref_xx[ind], ref_yy[ind]][indd] - 360
        vaa[ref_z[ind], ref_xx[ind], ref_yy[ind]] = (vaa[ref_z[ind], ref_xx[ind], ref_yy[ind]]) / (
                    count[ref_z[ind], ref_xx[ind], ref_yy[ind]] + 1)

        count[ref_z[ind], ref_xx[ind], ref_yy[ind]] = count[ref_z[ind], ref_xx[ind], ref_yy[ind]] + 1

        # outfile = outdirmed + "01%3d.tif"%(kk+k0)
        # write_Tiff(dbt_data1, temp_width1, temp_height1, 1, temp_geotrans1, temp_proj1, outfile)
        # outfile = outdirmed + "0%1d"%camera+"%3d_vza.tif"%(kk+k0)
        # write_Tiff(temp_zenith, temp_width1, temp_height1, 1, temp_geotrans1, temp_proj1, outfile)
        # outfile = outdirmed + "0%1d"%camera+"%3d_vaa.tif"%(kk+k0)
        # write_Tiff(temp_azimuth, temp_width1, temp_height1, 1, temp_geotrans1, temp_proj1, outfile)

    ind = count > 0
    dbt[ind] = dbt[ind] / count[ind]
    vza[ind] = vza[ind] / count[ind]

    vaa[vaa > 360] = vaa[vaa > 360] - 360
    vaa[vaa < 0] = vaa[vaa < 0] + 360

    # vaa[ind] = vaa[ind]/count[ind]

    outfile = outdir + r'dbt%1d' % track + '_%1d.tif'%kline
    write_Tiff(dbt, ref_height, ref_width, numAngle, ref_geotrans, ref_proj, outfile)
    outfile = outdir + r'vza%1d' % track + '_%1d.tif'%kline
    write_Tiff(vza, ref_height, ref_width, numAngle, ref_geotrans, ref_proj, outfile)
    outfile = outdir + r'vaa%1d' % track + '_%1d.tif'%kline
    write_Tiff(vaa, ref_height, ref_width, numAngle, ref_geotrans, ref_proj, outfile)
    outfile = outdir + r'count%1d' % track + '_%1d.tif'%kline
    write_Tiff(count, ref_height, ref_width, numAngle, ref_geotrans, ref_proj, outfile)

