import cdsapi
import calendar
from subprocess import call
import numpy as np
import os

'''era5数据借助idm高速下载脚本'''
# '1.先安装idm，将破解exe放在安装文件下' \
# '2.conda install cdsapi' \
# '3.创建 C:\Users\USERNAME\.cdsapirc 内容为（账号lu-yifan）：' \
# 'url: https://cds.climate.copernicus.eu/api/v2'
# 'key: 181809:c26b115c-5143-4794-a80d-e880744d3d2d'
# '4.调整下载格式，本脚本一天一个nc文件' \
# '5.运行后，在IDM中开始队列，批量下载，一天下五年数据不成问题 :)'


def idmDownloader(task_url, folder_path, file_name):
    """
    IDM下载器
    :param task_url: 下载任务地址
    :param folder_path: 存放文件夹
    :param file_name: 文件名
    :return:
    """
    # IDM安装目录
    # idm_engine = "C:\\Program Files (x86)\\Internet Download Manager\\IDMan.exe"
    # # 将任务添加至队列
    # call([idm_engine, '/d', task_url, '/p', folder_path, '/f', file_name, '/a'])
    # # 开始任务队列
    # call([idm_engine, '/s'])
    IDMPath = "C:\\Program Files (x86)\\Internet Download Manager\\"
    os.chdir(IDMPath)
    IDM = "IDMan.exe"
    command = ' '.join([IDM, '/d', task_url, '/p', folder_path, '/f', file_name, '/a'])
    # os.system('chcp65001')
    os.system(command)


if __name__ == '__main__':
    c = cdsapi.Client()  # 创建用户

    # 数据信息字典
    dic = {
        'product_type': 'reanalysis',
        'variable': 'total_column_water_vapour',
        'format': 'netcdf',
        'year': '',  # 年，设为空
        'month': '',  # 月，设为空
        'day': '',  # 日，设为空
        'time': [  # 小时
            '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
        ]
    }
    for y in range(2017, 2018):
        for m in range(1, 13):  # 遍历月
            day_num = calendar.monthrange(y, m)[1]  # 根据年月，获取当月日数
            # 将年、月、日更新至字典中
            for d in range(1, day_num + 1):
                dic['year'] = str(y)
                dic['month'] = str(m).zfill(2)
                dic['day'] = str(d).zfill(2)
                r = c.retrieve('reanalysis-era5-single-levels', dic, )  # 文件下载器
                url = r.location  # 获取文件下载地址
                path = r'D:\data\ERA5_tcw\%04d'% y  # 存放文件夹
                filename = 'ERA5_single-level_%04d' % y + '%02d' % m + '%02d' % (d) + '.nc'  # 文件名
                outfile = path +'//'+ filename
                if os.path.exists(outfile):
                    print(outfile, ' exists!')
                    continue

                idmDownloader(url, path, filename)  # 添加进IDM中下载