import eumdac
import time
import requests
import datetime
import fnmatch
import shutil

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

# Set bounding-box coordinates bottom left, top right
area = '-9.003, 37.540, -7.003, 39.540'

# Set sensing start and end time
start = datetime.datetime(2017, 1, 1, 9, 16)
end = datetime.datetime(2017, 1, 1, 10, 00)
# Retrieve datasets that match our filter
products = selected_collection.search(
    bbox=area,
    dtstart=start,
    dtend=end)

try:
    print(f'Found Datasets: {len(products)} datasets for the given area of interest')
except eumdac.collection.CollectionError as error:
    print(f"Error related to the collection: '{error.msg}'")
except requests.exceptions.RequestException as error:
    print(f"Unexpected error: {error}")

datatailor = eumdac.DataTailor(token)
# Defining the chain configuration
chain = eumdac.tailor_models.Chain(
    product='HRSEVIRI',
    format='geotiff',
    filter={"bands" : ["channel_1","channel_2","channel_9","channel_10"]},
    projection='geographic',
    roi={"NSWE" :[40.540,36.540,-10.003,-6.003]}
)
# roi parameter above is a pre-defined one. It's possible to use "roi=" as follows "{"NSWE" : [37,2,-19,21]}".


for product in products:
    print(product)
    out = r"D:\data\MSG\EVO_2020\\" + str(product) + ".tif"

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


