import glob
import math

import numpy as np
from satpy.scene import Scene
from satpy.resample import get_area_def
from satpy import find_files_and_readers
from util.util import *
from pyorbital import astronomy

'''
本脚本用于计算全域MSG星的vza和vaa,提供了两种方法计算
注意，satpy包需要用python39版本来运行，python37概率报错
'''

indir_raw = r'F:\data\MSG_2017_full-range\naive\test\\'

ifmethod = 2

fnames = glob.glob(indir_raw + r"*.nat*")

# fileNames = search_file(indir_raw,['.nc'])
# for filename in fileNames:
#     filedir = indir_raw + filename
#     scn = Scene(filenames=filedir, reader='seviri_l1b_nc')
#     red_scn = scn[0.8]


scn = Scene(filenames=fnames, reader='seviri_l1b_native')
print(scn.available_dataset_names())
scn.load(['VIS006','VIS008','IR_108', 'IR_120'], upper_right_corner='NE')
vis008 = scn["VIS008"]
vis008_meas = vis008.values
lon, lat = vis008.attrs['area'].get_lonlats()
outfile = r'D:\data\MSG\lon.tif'
# write_image_gdal(lon, lon.shape[0], lon.shape[1], 1, '', '', outfile)
outfile = r'D:\data\MSG\lat.tif'
# write_image_gdal(lat, lon.shape[0], lon.shape[1], 1, '', '', outfile)
lon_shape = lon.shape
# 中心经纬度 3712*3712
lon_center = (lon[1856,1856] + lon[1857,1856] + lon[1856,1857] + lon[1857,1857])/4
lat_center = (lat[1856,1856] + lat[1857,1856] + lat[1856,1857] + lat[1857,1857])/4

zen = np.zeros([lon_shape[0],lon_shape[1]])
azi = np.zeros([lon_shape[0],lon_shape[1]])


# 方法一 https://blog.csdn.net/qq_37970770/article/details/109278770
if ifmethod == 0:
    # 地球半径和静止卫星轨道
    re = 6378.137
    rs = 42164.17
    # 经纬度到弧度
    lon = lon * math.pi / 180
    lat = lat * math.pi / 180
    # 中心经纬度
    lon_center = lon_center * math.pi / 180
    lat_center = lat_center * math.pi / 180

    # 非空值区域
    ind_r = abs(lon) < 3.2

    # γ角和日地距离初始化
    gama = np.zeros([lon_shape[0], lon_shape[1]])
    d = np.zeros([lon_shape[0], lon_shape[1]])

    # 每个像元进行计算
    for i in range(lon.shape[0]):
        print(i)
        for j in range(lat.shape[1]):
            lat_p = lat[i, j]
            lon_p = lon[i, j]
            if np.isnan(lon_p): continue
            if np.isinf(lon_p): continue
            GEO_lat = lat_center

            # 计算γ角
            gama[i,j] = math.acos(np.cos(lat_p) * cos(lat_center) *cos(lon_center - lon_p)+sin(lat_p)*sin(GEO_lat))
            # gama[i,j] = math.acos(np.cos(lat_p) *cos(lon_center - lon_p))
            # 计算日地距离
            d[i,j] = rs * sqrt(1 +(re/rs)**2 -2*(re/rs)*cos(gama[i,j]))
            # 计算vza
            # zen[i,j] = arcsin(rs/d[i,j]*sin(gama[i,j])) *180 / pi
            zen[i,j] = (pi / 2 - arccos(rs/d[i,j]*sin(gama[i,j]))) *180 / pi
            # 计算vaa
            azi[i,j] = tan(abs(lon_center - lon_p)) / sin(abs(lat_p))
            azi[i,j] = math.atan(azi[i,j]) * 180 / pi

            # 根据卫星和像元的位置判断azi的大小
            inter_angle_Ai = azi[i,j]
            earth_sta_lat = lat_p
            earth_sta_lon = lon_p
            sat_long = lon_center
            if earth_sta_lat < 0:
                if earth_sta_lon < sat_long:  # If the satellite is North East of the Earth station
                    azi[i,j] = inter_angle_Ai
                elif earth_sta_lon > sat_long:  # If the satellite is North West of the Earth station
                    azi[i,j] = 360 - inter_angle_Ai
                else:  # If the satellite is on the same longitude and North of the Earth station
                    azi[i,j] = 0
            elif earth_sta_lat > 0:
                if earth_sta_lon < sat_long:  # If the satellite is South East of the Earth station
                    azi[i,j] = 180 - inter_angle_Ai
                elif earth_sta_lon > sat_long:  # If the satellite is South West of the Earth station
                    azi[i,j] = 180 + inter_angle_Ai
                else:  # If the satellite is on the same longitude and South of the Earth station
                    azi[i,j] = 180
            else:
                if earth_sta_lon > sat_long:  # If the satellite is on the same latitude and East of the Earth station
                    azi[i,j] = 90
                elif earth_sta_lon < sat_long:  # If the satellite is on the same latitude and West of the Earth station
                    azi[i,j] = 270
                else:  # If the satellite directly above the Earth station
                    azi[i,j] = 0
    outfile = r'D:\data\MSG\vza_2.tif'
    write_image_gdal(zen, lon.shape[0], lon.shape[1], 1, '', '', outfile)
    outfile = r'D:\data\MSG\vaa_2.tif'
    write_image_gdal(azi, lon.shape[0], lon.shape[1], 1, '', '', outfile)

# 方法二 原理与方法一类似，但是由于计算像元到地心加入高程，所以理论上更准
if ifmethod ==1 :
    EARTH_EQUA_RAD = 6378.14  # Earth radius on the equator 地球半径
    EARTH_ECCENT = 0.08182  # Eccentricity of the Earth 地球曲率
    GEO_RAD = 42164.17  # Geostationary orbit radius 静止卫星轨道半径
    GEO_ALT = 35786  # GSO altitude 静止卫星高度

    # 读全球1km高程数据
    DEM_dir = r"D:\data\base\dem_world_1000\new.tif"
    [dem, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(DEM_dir)
    dataset = gdal.Open(DEM_dir)
    ind_r = abs(lon) < 90
    indx, indy = loc2map(lat[ind_r], lon[ind_r], dataset)
    dem_range = np.zeros([lon_shape[0],lon_shape[1]])
    dem_range[ind_r] = dem[indx,indy]
    dem_range[dem_range>10000] = 0 # 过滤掉海

    # 逐像元计算 考虑高程的算法
    for i in range(lon.shape[0]):
        print(i)
        for j in range(lat.shape[1]):
            lat_p = lat[i,j]
            lon_p = lon[i, j]

            # 过滤空值
            if np.isnan(lon_p):continue
            if np.isinf(lon_p): continue
            # 如缺少高程就用0代替，否则用拼接后的GLOBE Topography，将全球陆地分为16块，分辨率1km
            # EarthStaAlt = 0
            EarthStaAlt = dem_range[i,j]

            lat_p = math.radians(lat_p)
            lon_p = math.radians(lon_p)
            lon_center = math.radians(lon_center)

            # 计算经度差
            diff_lon = lon_p - lon_center
            # 计算γ角
            beta = math.acos(math.cos(diff_lon) * math.cos(lat_p))

            l = ((EARTH_EQUA_RAD / math.sqrt(
                1 - pow(EARTH_ECCENT, 2) * pow(math.sin(lat_p), 2))) + EarthStaAlt) * math.cos(lat_p)
            z = ((EARTH_EQUA_RAD * (1 - pow(EARTH_ECCENT, 2)) / math.sqrt(
                1 - pow(EARTH_ECCENT, 2) * pow(math.sin(lat_p), 2))) + EarthStaAlt) * math.sin(lat_p)

            # Calculate the Radius to the center of the Earth from the ground station
            # 地心距离
            sta_rad = math.sqrt(l ** 2 + z ** 2)
            # Calculate the intermediate angle Ψᴇ
            inter_angle_psi = math.atan(z / l)
            # Calculate the Range to the satellite
            # 余弦定理，算像元到卫星的距离
            range_to_sat = math.sqrt(
                pow(sta_rad, 2) + pow(GEO_RAD, 2) - 2 * sta_rad * GEO_RAD * math.cos(inter_angle_psi) * math.cos(diff_lon))
            # Calculate the Elevation Angle of the satellite
            # 正弦定理，算高度角
            elev = ((EARTH_EQUA_RAD + GEO_ALT) / range_to_sat) * math.sqrt(
                1 - pow(math.cos(diff_lon), 2) * pow(math.cos(lat_p), 2))
            # 由于浮点存在很多1.00001这种值，这里过滤掉
            if elev >1.0: elev = 1.0
            if elev<-1.0: elev=-1.0
            elev = math.degrees(math.acos(elev))
            # 天顶角和高度角互余
            zen[i,j] = 90 - elev

            # 计算方位角
            earth_sta_lat = lat_p
            earth_sta_lon = lon_p
            sat_long = lon_center
            inter_angle_Ai = math.degrees(math.asin(math.sin(abs(diff_lon)) / math.sin(beta)))
            if earth_sta_lat < 0:
                if earth_sta_lon < sat_long:  # If the satellite is North East of the Earth station
                    azi[i,j] = inter_angle_Ai
                elif earth_sta_lon > sat_long:  # If the satellite is North West of the Earth station
                    azi[i,j] = 360 - inter_angle_Ai
                else:  # If the satellite is on the same longitude and North of the Earth station
                    azi[i,j] = 0
            elif earth_sta_lat > 0:
                if earth_sta_lon < sat_long:  # If the satellite is South East of the Earth station
                    azi[i,j] = 180 - inter_angle_Ai
                elif earth_sta_lon > sat_long:  # If the satellite is South West of the Earth station
                    azi[i,j] = 180 + inter_angle_Ai
                else:  # If the satellite is on the same longitude and South of the Earth station
                    azi[i,j] = 180
            else:
                if earth_sta_lon > sat_long:  # If the satellite is on the same latitude and East of the Earth station
                    azi[i,j] = 90
                elif earth_sta_lon < sat_long:  # If the satellite is on the same latitude and West of the Earth station
                    azi[i,j] = 270
                else:  # If the satellite directly above the Earth station
                    azi[i,j] = 0

    out = np.zeros([3, lon_shape[0], lon_shape[1]])
    out[1] = lon[lon!=np.Inf]
    out[2] = lat[lat!=np.Inf]
    out[0] = zen
    outfile = r'D:\data\MSG\MSG_vza.tif'
    write_image_gdal(out, lon.shape[0], lon.shape[1], 3, '', '', outfile)

    out[0] = azi
    outfile = r'D:\data\MSG\MSG_vaa.tif'
    write_image_gdal(out, lon.shape[0], lon.shape[1], 3, '', '', outfile)
    # outfile = r'D:\data\MSG\dem.tif'
    # write_image_gdal(dem_range, lon.shape[0], lon.shape[1], 1, '', '', outfile)

# 方法二 改版 重投影到0.03度的底图上
if ifmethod == 2:
    EARTH_EQUA_RAD = 6378.14  # Earth radius on the equator 地球半径
    EARTH_ECCENT = 0.08182  # Eccentricity of the Earth 地球曲率
    GEO_RAD = 42164.17  # Geostationary orbit radius 静止卫星轨道半径
    GEO_ALT = 35786  # GSO altitude 静止卫星高度

    # 读取type数据
    indir_type = r'D:\data\type\type_world_0.03.tif'
    dataset = gdal.Open(indir_type)
    [data, ns, nl, nb, geog_type, proj_type] = read_image_gdal(indir_type)
    nsi = np.zeros([nl, ns])
    nli = np.zeros([nl, ns])
    for k in range(nl):
        nli[k, :] = k
        nsi[k, :] = np.linspace(0, ns - 1, ns)
    nli = np.reshape(nli,-1)
    nsi = np.reshape(nsi,-1)
    dataset = gdal.Open(indir_type)
    temp1, temp2 = imagexy2geo(dataset, nli, nsi)
    lon, lat = geo2lonlat(dataset, temp1, temp2)
    lon = np.reshape(lon,[nl,ns])
    lat = np.reshape(lat,[nl, ns])

    zen = np.zeros([nl,ns])
    azi = np.zeros([nl,ns])

    # 读全球1km高程数据
    DEM_dir = r"D:\data\base\dem_world_1000\new.tif"
    [dem, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(DEM_dir)
    dataset = gdal.Open(DEM_dir)
    ind_r = abs(lon) < 90
    indx, indy = loc2map(lat[ind_r], lon[ind_r], dataset)
    dem_range = np.zeros([nl, ns])
    dem_range[ind_r] = dem[indx,indy]
    dem_range[dem_range>10000] = 0 # 过滤掉海


    # 逐像元计算 考虑高程的算法
    for i in range(lon.shape[0]):
        print(i)
        flag = 0
        for j in range(lat.shape[1]):
            lat_p = lat[i,j]
            lon_p = lon[i, j]
            if abs(lon_p) > 90: continue
            # 过滤空值
            if np.isnan(lon_p):continue
            if np.isinf(lon_p): continue
            # 如缺少高程就用0代替，否则用拼接后的GLOBE Topography，将全球陆地分为16块，分辨率1km
            # EarthStaAlt = 0
            EarthStaAlt = dem_range[i,j]

            lat_p = math.radians(lat_p)
            lon_p = math.radians(lon_p)
            lon_center = math.radians(lon_center)

            # 计算经度差
            diff_lon = lon_p - lon_center
            # 计算γ角
            beta = math.acos(math.cos(diff_lon) * math.cos(lat_p))

            l = ((EARTH_EQUA_RAD / math.sqrt(
                1 - pow(EARTH_ECCENT, 2) * pow(math.sin(lat_p), 2))) + EarthStaAlt) * math.cos(lat_p)
            z = ((EARTH_EQUA_RAD * (1 - pow(EARTH_ECCENT, 2)) / math.sqrt(
                1 - pow(EARTH_ECCENT, 2) * pow(math.sin(lat_p), 2))) + EarthStaAlt) * math.sin(lat_p)

            # Calculate the Radius to the center of the Earth from the ground station
            # 地心距离
            sta_rad = math.sqrt(l ** 2 + z ** 2)
            # Calculate the intermediate angle Ψᴇ
            inter_angle_psi = math.atan(z / l)
            # Calculate the Range to the satellite
            # 余弦定理，算像元到卫星的距离
            range_to_sat = math.sqrt(
                pow(sta_rad, 2) + pow(GEO_RAD, 2) - 2 * sta_rad * GEO_RAD * math.cos(inter_angle_psi) * math.cos(diff_lon))
            # Calculate the Elevation Angle of the satellite
            # 正弦定理，算高度角
            elev = ((EARTH_EQUA_RAD + GEO_ALT) / range_to_sat) * math.sqrt(
                1 - pow(math.cos(diff_lon), 2) * pow(math.cos(lat_p), 2))
            # 由于浮点存在很多1.00001这种值，这里过滤掉
            if elev >1.0: elev = 1.0
            if elev<-1.0: elev=-1.0
            elev = math.degrees(math.acos(elev))

            if round(elev) == 0:
                if flag == 0:
                    flag += 1
                    a = j
                if flag == 1:
                    flag += 1
                    b = j
                elif flag == 2:
                    b = j

            # 天顶角和高度角互余
            zen[i,j] = 90 - elev

            # 计算方位角
            earth_sta_lat = lat_p
            earth_sta_lon = lon_p
            sat_long = lon_center
            if math.sin(beta) == 0 : continue
            if math.sin(abs(diff_lon)) / math.sin(beta) <= 1:
                inter_angle_Ai = math.degrees(math.asin(math.sin(abs(diff_lon)) / math.sin(beta)))
            else: inter_angle_Ai = 90
            if earth_sta_lat < 0:
                if earth_sta_lon < sat_long:  # If the satellite is North East of the Earth station
                    azi[i,j] = inter_angle_Ai
                elif earth_sta_lon > sat_long:  # If the satellite is North West of the Earth station
                    azi[i,j] = 360 - inter_angle_Ai
                else:  # If the satellite is on the same longitude and North of the Earth station
                    azi[i,j] = 0
            elif earth_sta_lat > 0:
                if earth_sta_lon < sat_long:  # If the satellite is South East of the Earth station
                    azi[i,j] = 180 - inter_angle_Ai
                elif earth_sta_lon > sat_long:  # If the satellite is South West of the Earth station
                    azi[i,j] = 180 + inter_angle_Ai
                else:  # If the satellite is on the same longitude and South of the Earth station
                    azi[i,j] = 180
            else:
                if earth_sta_lon > sat_long:  # If the satellite is on the same latitude and East of the Earth station
                    azi[i,j] = 90
                elif earth_sta_lon < sat_long:  # If the satellite is on the same latitude and West of the Earth station
                    azi[i,j] = 270
                else:  # If the satellite directly above the Earth station
                    azi[i,j] = 0
        if flag == 0 or flag ==1:
            zen[i,:] = 0
            azi[i,:] = 0
        elif flag ==2:
            zen[i,:a] = 0
            zen[i,b:] = 0
            azi[i,:a] = 0
            azi[i,b:] = 0

    outfile = r'D:\data\base\msg_angle\MSG_vza_0.03_new.tif'
    write_image_gdal(zen, ns, nl, nb, geog_type, proj_type, outfile)


    outfile = r'D:\data\base\msg_angle\MSG_vaa_0.03_new.tif'
    write_image_gdal(azi,ns, nl, nb, geog_type, proj_type, outfile)
    print("Save successful")
    # outfile = r'D:\data\MSG\dem.tif'
    # write_image_gdal(dem_range, lon.shape[0], lon.shape[1], 1, '', '', outfile)



