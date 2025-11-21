import cdsapi
import calendar
from subprocess import call
import numpy as np
import os
import datetime

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
    base_dir = r'D:\data\data_download\ERA5\ERA5_download\\'
    os.makedirs(base_dir, exist_ok=True)

    # 数据信息字典
    dic = {
        'product_type': 'reanalysis',
        'variable': ['total_column_water_vapour','soil_temperature_level_1'],
        'format': 'netcdf',
        'year': '',  # 年，设为空
        'month': '',  # 月，设为空
        'day': '',  # 日，设为空
        'time': [  # 小时
            '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
        ],
        "download_format": "zip",
    }
    for year in range(2009, 2013):
        for month in range(1, 13):  # 遍历每个月
            # 创建年份目录
            year_dir = os.path.join(base_dir, f"{year:04d}")
            os.makedirs(year_dir, exist_ok=True)

            # 获取当月天数并生成日期列表
            _, days_in_month = calendar.monthrange(year, month)
            day_list = [f"{day:02d}" for day in range(1, days_in_month + 1)]  # 格式如 ['01','02',...,'31']

            # 设置请求参数（使用列表格式）
            dic['year'] = str(year)
            dic['month'] = f"{month:02d}"
            dic['day'] = day_list

            # 生成文件名（按月）
            filename = f"ERA5_single-level_{year:04d}{month:02d}.nc"
            output_path = os.path.join(year_dir, filename)

            # 检查文件是否已存在
            if os.path.exists(output_path):
                print(f"文件已存在: {output_path}")
                continue

            # 获取下载链接并下载整月数据
            try:
                retrieval = c.retrieve('reanalysis-era5-single-levels', dic,)
                download_url = retrieval.location
                idmDownloader(download_url, year_dir, filename)
                print(f"成功下载 {year}-{month:02d} 的整月数据")
            except Exception as e:
                print(f"下载 {year}-{month:02d} 整月数据时出错: {str(e)}")

