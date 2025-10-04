import os.path
import numpy as np
import eumdac
import time
import requests
import datetime
import fnmatch
import shutil

def read_txt_float(filename):
    '''
    读取txt文件，并将其按照float存储，行列号作为索引的矩阵
    :param filename: 文件路径
    :return: float数组
    '''
    mydata = []
    with open(filename) as f:
        lines = f.readline()
        while lines:
            line = lines.split()
            mydata.append(line)
            lines = f.readline()
    mydata = np.asarray(mydata,dtype=float)
    return mydata

def doy2date(year, doy):
    '''
    doy 到日期的转换
    :param year: 年
    :param doy: day of year
    :return:  日期（月,日）
    '''
    year = int(year)
    doy = int(doy)
    month_leapyear = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_notleap = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        for i in range(0, 12):
            if doy > month_leapyear[i]:
                doy -= month_leapyear[i]
                continue
            if doy <= month_leapyear[i]:
                month = i + 1
                day = doy
                break
    else:
        for i in range(0, 12):
            if doy > month_notleap[i]:
                doy -= month_notleap[i]
                continue
            if doy <= month_notleap[i]:
                month = i + 1
                day = doy
                break
    return month, day

'''obain the time data'''
infile_time = r'D:\data\LSCT_evo_2020\slstr_time2.txt'
data = read_txt_float(infile_time)
idex=np.lexsort([data[:,0]])
doy_ = data[:,0]
pst_ = data[:,1]
year = 2020

# 账号 luyifan3
consumer_key = 'jKjCTW0HHm5aUi8kOFfkRTmv9_Aa'
consumer_secret = 'dIN8cefDVRT5vgnBXsCy8KI0bMMa'

credentials = (consumer_key, consumer_secret)

token = eumdac.AccessToken(credentials)

try:
    print(f"This token '{token}' expires {token.expiration}")
except requests.exceptions.HTTPError as exc:
    print(f"Error when trying the request to the server: '{exc}'")

datastore = eumdac.DataStore(token)
selected_collection = datastore.get_collection('EO:EUM:DAT:MSG:HRSEVIRI')

for i in range(len(doy_)):
    # token = eumdac.AccessToken(credentials)
    # datastore = eumdac.DataStore(token)
    # selected_collection = datastore.get_collection('EO:EUM:DAT:MSG:HRSEVIRI')
    doy = doy_[i]
    month,day = doy2date(year,doy)
    pst = pst_[i]
    hh = pst // 10000
    min = (pst % 10000) //100
    min_count = hh * 60 + min
    start_hh = int((min_count-15)//60)
    start_mm = int((min_count-15) % 60)
    end_hh = int((min_count+15)//60)
    end_mm = int((min_count+15) % 60)

    # Set bounding-box coordinates bottom left, top right
    area = '-9.003, 37.540, -7.003, 39.540'

    # Set sensing start and end time
    start = datetime.datetime(year, month, day, start_hh, start_mm)
    end = datetime.datetime(year, month, day, end_hh, end_mm)
    # Retrieve datasets that match our filter
    products = selected_collection.search(
        bbox=area,
        dtstart=start,
        dtend=end)
    datatailor = eumdac.DataTailor(token)
    # Defining the chain configuration
    chain = eumdac.tailor_models.Chain(
        product='HRSEVIRI',
        format='geotiff',
        filter={"bands": ["channel_1", "channel_2", "channel_9", "channel_10"]},
        projection='geographic',
        roi={"NSWE": [40.540, 36.540, -10.003, -6.003]}
    )
    for product in products:
        print(product)
        out = r"D:\data\MSG\EVO_2020\\" + str(product) + ".tif"
        if os.path.exists(out):
            print("file exists!")
            continue

        customisation = datatailor.new_customisation(product, chain)

        try:
            print(f"Customisation {customisation._id} started.")
        except eumdac.datatailor.DataTailorError as error:
            print(f"Error related to the Data Tailor: '{error.msg}'")
        except requests.exceptions.RequestException as error:
            print(f"Unexpected error: {error}")

        '''loop'''
        status = customisation.status
        sleep_time = 10  # seconds
        # Customisation Loop
        while status:
            # Get the status of the ongoing customisation
            status = customisation.status

            if "DONE" in status:
                print(f"Customisation {customisation._id} is successfully completed.")
                break
            elif status in ["ERROR", "FAILED", "DELETED", "KILLED", "INACTIVE"]:
                print(f"Customisation {customisation._id} was unsuccessful. Customisation log is printed.\n")
                print(customisation.logfile)
                break
            elif "QUEUED" in status:
                print(f"Customisation {customisation._id} is queued.")
            elif "RUNNING" in status:
                print(f"Customisation {customisation._id} is running.")
            time.sleep(sleep_time)

        '''download'''
        jobID = customisation._id

        print(f"Dowloading the Tif output of the customisation {jobID}")
        tif, = fnmatch.filter(customisation.outputs, '*.tif')

        try:
            with customisation.stream_output(tif, ) as stream, open(out, 'wb') as fdst:
                shutil.copyfileobj(stream, fdst)
            print(f"Dowloaded the TIF output of the customisation {jobID}")
        except eumdac.datatailor.CustomisationError as error:
            print(f"Data Tailor Error", error)
        except requests.exceptions.RequestException as error:
            print(f"Unexpected error: {error}")

        '''delete'''
        try:
            customisation.delete()
        except eumdac.datatailor.CustomisationError as exc:
            print("Customisation Error:", exc)
        except requests.exceptions.RequestException as error:
            print("Unexpected error:", error)





