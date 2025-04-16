import eumdac
import requests
import datetime
import shutil
import os
import time

'''脚本用于下载EMUETSAT数据MSG'''
'''运行前请先配置环境'''
# https://gitlab.eumetsat.int/eumetlab/data-services/eumetsat_python_for_data_services
'''需要在IDM下载器中 任务栏 下载->选项->下载——>添加重复的下载链接，并覆盖已存在的文件'''
'''由于token会过期，每半个小时刷新一遍下载链接'''

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

# 账号 luyifan3
consumer_key = 'qV_L7vxq0EbScobn5piUn7mxRlYa'
consumer_secret = 'Nz4dCSTWY5bFw48gS0odqTz0A7oa'


def job():
    credentials = (consumer_key, consumer_secret)

    token = eumdac.AccessToken(credentials)

    try:
        print(f"This token '{token}' expires {token.expiration}")
    except requests.exceptions.HTTPError as error:
        print(f"Error when tryng the request to the server: '{error}'")

    # Retrieve how many collection objects are available from DataStore
    datastore = eumdac.DataStore(token)

    # Select our collection
    selected_collection = datastore.get_collection('EO:EUM:DAT:MSG:HRSEVIRI')

    # Set sensing start and end time
    start = datetime.datetime(2017, 12, 1, 0, 0)
    end = datetime.datetime(2017, 12, 2, 0, 0)
    # Retrieve datasets that match our filter
    products = selected_collection.search(
        dtstart=start,
        dtend=end)

    try:
        print(f'Found Datasets: {len(products)} datasets for the given area of interest')
    except eumdac.collection.CollectionError as error:
        print(f"Error related to the collection: '{error.msg}'")
    except requests.exceptions.RequestException as error:
        print(f"Unexpected error: {error}")

        '''direct download'''
    for product in products:
        url = product.url
        dir = r"F:\data\MSG_2017_full-range\zip\\"
        name = str(product) + ".zip"
        if os.path.exists(dir + name):
            print("file exists!")
            continue
        print(name)
        idmDownloader(url, dir, name)

def loop_func(func, second):
    while True:
        print("start loop")
        func()
        print("wait...")
        time.sleep(second)

loop_func(job,second=1800)