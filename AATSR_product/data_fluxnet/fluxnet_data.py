import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *

'''Fluxnet 半小时数据提取代码'''
'''提取参数包括：Ta, Ts, LW_IN, LW_OUT, SWC'''
'''注意全部用F，QC0 = measured; 1 = good quality gapfill; 2 = medium;3 = poor'''

'''2024.2.26'''
'''提取FLUXNET站点中2002-2012年数据，并提取ta与ts的结果'''
'''2024.3.19'''
'''补充提取了上下行长波'''
'''2025.10.28'''
'''筛减了参数，只提取有用的'''

base_dir = '/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/'
raw_dir = base_dir + r"/Fluxnet_raw/"
fileter_dir = base_dir +  r"/Fluxnet_data/"
mkdir_if_not_exist(fileter_dir)

dir_Names = search_dir(raw_dir, 'FLX')
dir_Names.sort()
siteNum = len(dir_Names)

filter_sitenum = 0
for dirName in dir_Names:

    print(dirName)
    if dirName == "FLX_AA-Flx_BIF_ALL_20200501": continue

    '''解析文件名'''
    siteName = dirName.split('_')[1]
    year_range = dirName.split('_')[4]
    start_year = int(year_range.split('-')[0])
    end_year = int(year_range.split('-')[1])
    version = dirName.split('_')[-1]

    '''筛选时间'''
    if start_year > 2012 or end_year < 2002: continue
    filter_sitenum = filter_sitenum + 1

    '''读取文件'''
    csv_name = 'FLX_' + siteName + '_FLUXNET2015_FULLSET_HH_' + year_range + "_" + version + ".csv"
    infile = raw_dir + dirName + r"/" + csv_name
    if not os.path.exists(infile):
        csv_name = 'FLX_' + siteName + '_FLUXNET2015_FULLSET_HR_' + year_range + "_" + version + ".csv"
        infile = raw_dir + dirName + r"/" + csv_name
    if start_year < 2002: start_year = 2002
    if end_year > 2012: end_year = 2012
    out_name = siteName + "_" + str(start_year) + "-" + str(end_year) + ".csv"
    outfile = fileter_dir + out_name
    if os.path.exists(outfile): continue

    '''读取指定列'''
    data = pd.read_csv(infile)
    if 'TS_F_MDS_1' not in data.columns:
        data['TS_F_MDS_1'] = -9999
    if 'TS_F_MDS_1_QC' not in data.columns:
        data['TS_F_MDS_1_QC'] = -9999
    if 'LW_IN_F' not in data.columns:
        data['LW_IN_F'] = -9999
    if 'LW_OUT' not in data.columns:
        data['LW_OUT'] = -9999
    if 'SWC_F_MDS_1' not in data.columns:
        data['SWC_F_MDS_1'] = -9999
    if 'SWC_F_MDS_1_QC' not in data.columns:
        data['SWC_F_MDS_1_QC'] = -9999
    mask = (data['TIMESTAMP_START'] >= 200206010000) & (data['TIMESTAMP_START'] <= 201205010000)
    selected_data = data[
        ['TIMESTAMP_START', 'TIMESTAMP_END',  'TA_F', 'TA_F_QC', 'TS_F_MDS_1',
         'TS_F_MDS_1_QC', 'LW_IN_F', 'LW_IN_F_QC', 'LW_OUT','SWC_F_MDS_1','SWC_F_MDS_1_QC']] # 'lw_out not available'
    selected_data = selected_data[mask]
    selected_data.to_csv(outfile, index=False)
