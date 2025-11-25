import cdsapi
import numpy as np
import os
from subprocess import Popen

'''2025.11.13'''
'''下载ERA5月平均数据 作为约束数据'''
'''python 环境 ERA5'''

# c = cdsapi.Client()
for year in range(2002, 2013):
    outfile = r'/media/hero/lsct02/ERA5_month/raw1/ERA5_MonthAve_%04d.nc' % (year)
    if os.path.exists(outfile): continue

    dataset = "reanalysis-era5-single-levels-monthly-means"
    request = {
        "product_type": ["monthly_averaged_reanalysis_by_hour_of_day"],
        # "variable": [
        #     "2m_temperature",
        #     "skin_temperature"
        # ],
        "variable": [
            "soil_temperature_level_1",
            "soil_temperature_level_2",
            "soil_temperature_level_3",
            "soil_temperature_level_4"
        ],
        "year": '%04d' % year,
        "month": [
            "01", "02", "03",
            "04", "05", "06",
            "07", "08", "09",
            "10", "11", "12"
        ],
        "time": [
            "00:00", "01:00", "02:00",
            "03:00", "04:00", "05:00",
            "06:00", "07:00", "08:00",
            "09:00", "10:00", "11:00",
            "12:00", "13:00", "14:00",
            "15:00", "16:00", "17:00",
            "18:00", "19:00", "20:00",
            "21:00", "22:00", "23:00"
        ],
        "data_format": "netcdf",
        "download_format": "unarchived"
    }

    client = cdsapi.Client()
    client.retrieve(dataset, request, outfile)
