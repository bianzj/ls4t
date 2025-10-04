import shapefile
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os
import h5py
from util.util import *

'''
从shapefile中提取空间坐标数据
并基于一个参考图像，得到坐标数据在参考图像中的行列号
'''


file=shapefile.Reader(r'D:\data\S3A_LST\level2\res2_4m.shp',encoding='gbk')  #读取城市.shp文件
shapes=file.shapes()   #获取point
records=file.records() #获取省-市名称

pro_city_points = []  # 建立城市边界列表
pro_city_names = []  # 建立城市名称列表
pro_names = []  # 建立省份列表

for i in range(len(shapes)):
    points = shapes[i].points  # h获取经纬度数据
    pro_city_name = file.records()[i][9]  # 获取省名称
    # city_name = file.records()[i][6]  # 获取市区名称
    # city_ch_name = file.records()[i][8]  # 获取市区中文名称
    # pro_city_name = [pro_name, city_name, city_ch_name]

    lon = []
    lat = []
    # 将每个tuple的lon和lat组合起来
    [lon.append(points[i][0]) for i in range(len(points))]
    [lat.append(points[i][1]) for i in range(len(points))]

    lon = np.array(lon).reshape(-1, 1)
    lat = np.array(lat).reshape(-1, 1)
    loc = np.concatenate((lon, lat), axis=1)

    pro_city_points.append(loc)
    pro_city_names.append(pro_city_name)
    # pro_names.append(pro_name)


pro_city_points = np.asarray(pro_city_points)
pro_city_names = np.asarray(pro_city_names)

targetArea = r'D:\data\S3A_LST\ref.tif'
dataset = gdal.Open(targetArea)
if dataset == None:
    print(targetArea + " ")
im_width = dataset.RasterXSize
im_height = dataset.RasterYSize
im_bands = dataset.RasterCount
ns = im_width
nl = im_height
data = dataset.ReadAsArray(0, 0, ns, nl)
geog = dataset.GetGeoTransform()
proj = dataset.GetProjection()
nsi = np.zeros([nl, ns])
nli = np.zeros([nl, ns])
for k in range(nl):
    nli[k, :] = k
    nsi[k, :] = np.linspace(0, ns - 1, ns)
nli = np.reshape(nli, -1)
nsi = np.reshape(nsi, -1)
###

lat = pro_city_points[:,0,1]
lon = pro_city_points[:,0,0]
temp1, temp2 = lonlat2geo(dataset, lat, lon)
imagey, imagex = geo2imagexy(dataset, temp1, temp2)

imagex = np.asarray(imagex, np.int)
imagey = np.asarray(imagey, np.int)




out_result = np.stack([imagex,imagey,lon,lat])
out_result = np.transpose(out_result)
outfile = 'D:\data\S3A_LST\city_location.txt'
np.savetxt(outfile,out_result,fmt='%d')

