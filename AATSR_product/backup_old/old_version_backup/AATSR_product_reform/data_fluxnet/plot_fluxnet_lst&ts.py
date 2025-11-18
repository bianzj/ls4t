from timezonefinder import TimezoneFinder
import pytz
import csv
from utils.old.util import *
from datetime import datetime, time

'''Plot fluxnet ts/lst'''

indir = r"/home/hero/data/Fluxnet/Fluxnet_data/Fluxnet_csv_2002-2012/"


# 读取 FLUXNET 站点位置
def read_fluxnet_locations(file_path):
    locations = {}
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            site_name = row['SITE_ID']
            lat = float(row['LOCATION_LAT'])
            lon = float(row['LOCATION_LONG'])
            locations[site_name] = (lat, lon)
    return locations


# 获取时区
def get_timezone(lat, lon):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if timezone_str:
        return pytz.timezone(timezone_str)
    else:
        return None


fluxnet_loc_file = r"/home/hero/data/Fluxnet/Fluxnet_data/FLUXSITE_imagexy.csv"
fluxnet_locations = read_fluxnet_locations(fluxnet_loc_file)

fileNames = search_file_rej(indir, 'csv', '~lock')

for fileName in fileNames:
    # if fileName != 'AT-Neu_2002-2012.csv':
    #     continue
    print(f"Processing file: {fileName}")
    site_name = fileName[:6]

    if site_name in fluxnet_locations:
        lat, lon = fluxnet_locations[site_name]
        timezone = get_timezone(lat, lon)
    else:
        print(f"Site {site_name} not found in location file.")
        continue

    # 读取数据
    data = pd.read_csv(indir + fileName)

    # 处理时间戳
    local_times = []
    for timestamp in data['TIMESTAMP_START']:
        try:
            timestamp_str = str(int(timestamp))  # 确保 timestamp 是字符串
            utc_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M')
            local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone)
            local_times.append(local_time)
        except Exception as e:
            print(f"Error processing timestamp {timestamp} in {fileName}: {e}")
            local_times.append(None)

    # 添加本地时间列
    data['LOCAL_TIME'] = local_times
    if not pd.api.types.is_datetime64_any_dtype(data['LOCAL_TIME']):
        data['LOCAL_TIME'] = pd.to_datetime(data['LOCAL_TIME'])

    # 筛选每天 10:30 到 11:30 的数据
    filtered_data = data[
        (data['LOCAL_TIME'].dt.time >= time(10, 30)) &
        (data['LOCAL_TIME'].dt.time <= time(11, 30))
        ]

    if filtered_data.empty:
        print(f"No data found in the time range for file {fileName}.")
        continue

    # 检查列是否存在
    required_columns = ['lst', 'TA_F_MDS', 'TS_F_MDS_1']
    for col in required_columns:
        if col not in filtered_data.columns:
            print(f"Column {col} not found in file {fileName}.")
            continue

    lst = filtered_data['lst']
    ta = filtered_data['TA_F_MDS']
    ts = filtered_data['TS_F_MDS_1']

    # 筛选条件
    ind = pd.notna(lst) & (ts > 10) & (lst > 200)
    if ind.sum() == 0:
        print(f"No valid data points found in {fileName}.")
        continue

    # 防止索引越界
    s = np.where(ind)[0][0]
    length = 48 * 5
    end_index = min(s + length, len(ts))  # 防止越界

    # 绘图
    plt.plot(range(end_index - s), ts[s:end_index] + 273.15, label='ts')
    plt.plot(range(end_index - s), lst[s:end_index], label='lst')
    plt.legend()
    plt.title(f"Fluxnet Data: {fileName}")
    plt.xlabel("Time Steps")
    plt.ylabel("Temperature (K)")
    plt.show()

    print(np.average(lst[ind] - ts[ind]-273.15))
