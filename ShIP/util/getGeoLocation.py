from util.myfun import *
import pandas as pd
import time
from datetime import datetime
from sklearn.metrics import r2_score
# -*- coding: utf-8 -*-
import pandas as pd


def pd_toExcel(stationNameAll, longitude, latitude, fileName):  # pandas库储存数据到excel
    ids = []
    names = []
    prices = []
    for i in range(len(stationNameAll)):
        ids.append(stationNameAll[i])
        names.append(longitude[i])
        prices.append(latitude[i])

    dfData = {  # 用字典设置DataFrame所需数据
        'stationName': ids,
        'longitude': names,
        'latitude': prices
    }
    df = pd.DataFrame(dfData)  # 创建DataFrame
    df.to_excel(fileName, index=False)  # 存表，去除原始索引列（0,1,2...）


# 黑河数据
# stationNameAll = ['AR','JYL','DM','HZZ','SD','SDQ','HHL','HM']
#
# geolocation = {'AR':[100.4643,38.0473], 'DSL':[98.9406,38.8399],
#                    'JYL':[101.1160, 37.8384],'DM':[100.3722,38.8556],
#                    'HZZ':[100.3201,38.7659], 'SD':[100.4464,38.9751],
#                    'SDQ':[101.1374,42.0012], 'HHL':[101.1335,41.9903],
#                    'HM':[100.9872,42.1135]}
# location = pd.DataFrame(geolocation)
#
# fileName = r'D:\data\field\黑河数据\\geoLocation_heihe.xlsx'
# pd_toExcel(location, fileName, stationNameAll)


# 那曲数据
stationNames = ['BC+-01', 'BC+', 'BC02-01', 'BC03', 'BC04', 'BC05', 'BC06-01',
                'BC07-01', 'BC07', 'BC08', 'C1', 'C2', 'C3-01', 'C3', 'C4-01',
                'C4', 'CD01-01', 'CD01', 'CD02', 'CD03', 'CD04-01', 'CD04', 'CD05-01',
                'CD06', 'CD07-01', 'F1', 'F2', 'F3', 'F4', 'F5', 'MS3475', 'MS3482', 'MS3488',
                'MS3494', 'MS3501', 'MS3506-01', 'MS3513', 'MS3518', 'MS3523', 'MS3527', 'MS3533',
                'MS3545', 'MS3552', 'MS3559', 'MS3576-01', 'MS3593', 'MS3603', 'MS3614', 'MS3620',
                'MS3627', 'MS3633', 'MSBJ', 'MSNQRW', 'P1', 'P10', 'P11-01', 'P11', 'P2', 'P5', 'P7', 'P8', 'P9']

infileGeoLoc = r'D:\data\Field\青藏高原\青藏高原中部土壤温湿度多尺度观测网数据集（2010-2021）\Stations_information_NAQU.xlsx'
geoLocation = pd.read_excel(infileGeoLoc)
stationNameAll = []
latitude = []
longitude = []
for station in stationNames:
    latStr = geoLocation[geoLocation['Site'] == station]['Latitude(degree-minute)']
    lonStr = geoLocation[geoLocation['Site'] == station]['Longitude(degree-minute)']
    # 格式化获取到经纬度
    lat = latStr.str.extract(r'(\d+)+.(\d+.\d+)')[0].astype(float) \
          + latStr.str.extract(r'(\d+)+.(\d+.\d+)')[1].astype(float) / 60.0
    lon = lonStr.str.extract(r'(\d+)+.(\d+.\d+)')[0].astype(float) \
          + lonStr.str.extract(r'(\d+)+.(\d+.\d+)')[1].astype(float) / 60.0
    lat = lat.values[0]
    lon = lon.values[0]
    stationNameAll.append(station)
    latitude.append(lat)
    longitude.append(lon)

fileName = r'D:\data\field\青藏高原\\geoLocation_naqu.xlsx'
pd_toExcel(stationNameAll, longitude, latitude, fileName)