import cdsapi
import numpy as np
import os
from subprocess import Popen

'''批量下载ER5 数据'''
'''2025.7.7'''
'''补充下载stl1、tcwv'''


###########################################
#### down ERA5 reanalysis data
###########################################
c = cdsapi.Client()
kmonth_ = [1,2,3,4,5,6,7,8,9,10,11,12]
kday_ = np.asarray([31,28,31,30,31,30,31,31,30,31,30,31])
for k1 in range(len(kmonth_)):
    kmonth = kmonth_[k1]
    for k2 in range(kday_[k1]):
        # kday = kday_[k2]
        kday = k2+1

        outfile = 'D:\data\ERA5_data\ERA5.single-level.2019%02d'%kmonth+'%02d'%kday+'.nc'
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'variable': [
                    "soil_temperature_level_1",
                    "total_column_water_vapour",
                    'surface_solar_radiation_downward_clear_sky',
                    'surface_solar_radiation_downwards',
                    'surface_thermal_radiation_downward_clear_sky',
                    'surface_thermal_radiation_downwards',
                    'uv_visible_albedo_for_diffuse_radiation',
                    'uv_visible_albedo_for_direct_radiation',
                ],
                'year': '2002',
                'month': '%02d'%kmonth,
                'day': '%02d'%kday,
                'time': [
                    '00:00', '01:00', '02:00',
                    '03:00', '04:00', '05:00',
                    '06:00', '07:00', '08:00',
                    '09:00', '10:00', '11:00',
                    '12:00', '13:00', '14:00',
                    '15:00', '16:00', '17:00',
                    '18:00', '19:00', '20:00',
                    '21:00', '22:00', '23:00',
                ],
                'format': 'netcdf',
                "download_format": "zip",
            },
            outfile)


















# c = cdsapi.Client()
# kmonth_ = [1,2,3,4,5,6,7,8,9,10,11,12]
# # kday_ = np.linspace(13,29,17)
# kday_ = np.asarray([31,28,31,30,31,30,31,31,30,31,30,31])
# for k1 in range(len(kmonth_)):
#     kmonth = kmonth_[k1]
#     for k2 in range(kday_[k1]):
#         # kday = kday_[k2]
#         kday = k2+1
#
#         outfile = 'G:\ERA5_downward\ERA5.single-level.2019%02d'%kmonth+'%02d'%kday+'.nc'
#         c.retrieve(
#             'reanalysis-era5-single-levels',
#             {
#                 'product_type': 'reanalysis',
#                 'variable': [
#                     '2m_temperature', 'skin_temperature', 'surface_solar_radiation_downward_clear_sky',
#                     'surface_solar_radiation_downwards', 'surface_thermal_radiation_downward_clear_sky',
#                     'surface_thermal_radiation_downwards',
#                     'uv_visible_albedo_for_diffuse_radiation', 'uv_visible_albedo_for_direct_radiation',
#                 ],
#                 'year': '2019',
#                 'month': '%02d'%kmonth,
#                 'day': '%02d'%kday,
#                 'time': [
#                     '00:00', '01:00', '02:00',
#                     '03:00', '04:00', '05:00',
#                     '06:00', '07:00', '08:00',
#                     '09:00', '10:00', '11:00',
#                     '12:00', '13:00', '14:00',
#                     '15:00', '16:00', '17:00',
#                     '18:00', '19:00', '20:00',
#                     '21:00', '22:00', '23:00',
#                 ],
#                 'format': 'netcdf',
#             },
#             outfile)