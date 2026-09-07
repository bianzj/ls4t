from utils.old.util import *
import csv
import pandas as pd
from scipy.stats import pearsonr

'''2024.9.26'''
'''calculate variable r'''


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


if __name__ == '__main__':
    base_dir = r'/home/hero/data/Fluxnet/'
    indir_Fluxnet = r"/home/hero/data/Fluxnet/Fluxnet_data/"
    infile_site_imagexy = indir_Fluxnet + r"FLUXSITE_imagexy.csv"

    fluxnet_loc_file = infile_site_imagexy
    fluxnet_locations = read_fluxnet_locations(fluxnet_loc_file)

    indir = base_dir + 'Merge/Merge_all/'
    fileNames = search_file(indir, ['.csv'])

    results = {}

    for fileName in fileNames:
        site_name = fileName[:-4]
        print(site_name)

        if site_name in fluxnet_locations:
            lat, lon = fluxnet_locations[site_name]
            infile = indir + fileName

            # 读取数据
            data = pd.read_csv(infile)

            # 筛选 LAI
            lai_filtered_data = data[(data['LAI'] >= 0) & (data['LAI'] <= 5)]
            # 筛选 SWC
            swc_filtered_data = data[data['SWC_F_MDS_1'] >= 0]

            # 清理数据，去掉包含 NaN 或 inf 的行
            lai_filtered_data = lai_filtered_data.replace([np.inf, -np.inf], np.nan).dropna()
            swc_filtered_data = swc_filtered_data.replace([np.inf, -np.inf], np.nan).dropna()

            # LAI 相关性计算
            if len(lai_filtered_data) >= 10 and all(
                    col in lai_filtered_data.columns for col in ['lstN', 'Ts', 'Tv', 'LAI']):
                correlations_lai = {}
                for variable in ['lstN', 'Ts', 'Tv']:
                    r, _ = pearsonr(lai_filtered_data[variable], lai_filtered_data['LAI'])
                    correlations_lai[variable] = r
                results[site_name] = correlations_lai

            # SWC 相关性计算（可以根据需要添加）
            # ...

    # 输出结果为 DataFrame
    results_df = pd.DataFrame(results).T
    results_df.columns = ['lstN_LAI', 'Ts_LAI', 'Tv_LAI']  # 可以根据需要修改列名
    results_df.index.name = 'Site Name'

    # 输出到 CSV 文件
    results_df.to_csv(base_dir + 'correlation_results.csv')

    print(results_df)
