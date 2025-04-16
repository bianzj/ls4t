import eumdac
import requests
import datetime
import shutil
import os

'''脚本用于下载EMUETSAT数据MSG'''
'''运行前请先配置环境'''
# https://gitlab.eumetsat.int/eumetlab/data-services/eumetsat_python_for_data_services

# 账号 luyifan3
consumer_key = 'qV_L7vxq0EbScobn5piUn7mxRlYa'
consumer_secret = 'Nz4dCSTWY5bFw48gS0odqTz0A7oa'

credentials = (consumer_key, consumer_secret)

token = eumdac.AccessToken(credentials)

try:
    print(f"This token '{token}' expires {token.expiration}")
except requests.exceptions.HTTPError as error:
    print(f"Error when tryng the request to the server: '{error}'")

# Retrieve how many collection objects are available from DataStore
datastore = eumdac.DataStore(token)
# try:
#     print(f"EUMETSATs DataStore provides access to {len(datastore.collections)} collections.")
# except eumdac.datastore.DataStoreError as error:
#     print(f"Error related to the data store: '{error.msg}'")
# except requests.exceptions.RequestException as error:
#     print(f"Unexpected error: {error}")
#
# try:
#     for collection in datastore.collections:
#         print(f"{collection} - {collection.title}")
# except eumdac.datastore.DataStoreError as error:
#     # The message will be: Load collections failed.
#     print(f"Error related to the DataStore:'{error.msg}'")
# except eumdac.collection.CollectionError as error:
#     # The message will be: Related to a failed loading of properties related to the collection ID.
#     print(f"Error related to a collection: '{error.msg}'")
# except requests.exceptions.RequestException as error:
#     print(f"Unexpected error: {error}")

'''date fillter'''
# EO:EUM:DAT:MSG:HRSEVIRI - High Rate SEVIRI Level 1.5 Image Data - MSG - 0 degree
# EO:EUM:DAT:0615 - SLSTR Level 1B Radiances and Brightness Temperatures (version BC004) - Sentinel-3 - Reprocessed

# Select our collection
selected_collection = datastore.get_collection('EO:EUM:DAT:MSG:HRSEVIRI')

latest = selected_collection.search().first()

try:
    print(latest)
except eumdac.collection.CollectionError as error:
    print(f"Error related to the collection: '{error.msg}'")
except requests.exceptions.RequestException as error:
    print(f"Unexpected error: {error}")

# # Set bounding-box coordinates bottom left, top right
# area = '-9.003, 37.540, -7.003, 39.540'

# Set sensing start and end time
start = datetime.datetime(2017, 8, 1, 0, 0)
end = datetime.datetime(2017, 8, 2, 0, 0)
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
    out = r"F:\data\MSG_2017_full-range\zip\\" + str(product) + ".zip"
    if os.path.exists(out):
        print("file exists!")
        continue
    try:
        with product.open() as fsrc, \
                open(out, mode='wb') as fdst:
            shutil.copyfileobj(fsrc, fdst)
            print(f'Download of product {product} finished.')
    except eumdac.product.ProductError as error:
        print(f"Error related to the product '{product}' while trying to download it: '{error.msg}'")
    except requests.exceptions.RequestException as error:
        print(f"Unexpected error: {error}")

print('All downloads are finished.')

