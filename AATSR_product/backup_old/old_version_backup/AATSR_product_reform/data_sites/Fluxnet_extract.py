from utils.old.util import *

'''从所有FLUXNET站点观测中提取有用信息并保存到csv中，格式为csv'''

'''2024.2.26'''
'''提取FLUXNET站点中2002-2012年数据，并提取ta与ts的结果'''
'''2024.3.19'''
'''补充提取了上下行长波'''
'''2025.3.8'''
'''对于没有上下行长波的也进行提取'''

raw_dir = r"/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/Fluxnet_raw/"
fileter_dir = r"/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/Fluxnet_filter/"
mkdir_if_not_exist(fileter_dir)
excel_file = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/FLUXSITE_imagexy.xlsx'

dir_Names = search_dir(raw_dir, 'FLX')
siteNum = len(dir_Names)

ifextract = 1
ifupdate = 0

if ifextract:
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
        if 'TS_F_MDS_1' not in data.columns or 'TS_F_MDS_1_QC' not in data.columns:
            print(f" {csv_name} 中缺少 'TS_F_MDS_1' 和 'TS_F_MDS_1_QC' 列，跳过。")
            continue
        if 'LW_IN_F' not in data.columns or 'LW_OUT' not in data.columns:
            print(f" {csv_name} 中缺少 'LW_IN_F' 和 'LW_OUT' 列。")
            data['LW_IN_F'] = -9999
            data['LW_OUT'] = -9999
        if 'SWC_F_MDS_1' not in data.columns:
            data['SWC_F_MDS_1'] = -9999
        mask = (data['TIMESTAMP_START'] >= 200206010000) & (data['TIMESTAMP_START'] <= 201205010000)
        selected_data = data[
            ['TIMESTAMP_START', 'TIMESTAMP_END', 'TA_F_MDS', 'TA_F_MDS_QC', 'TA_ERA', 'TA_F', 'TA_F_QC', 'TS_F_MDS_1',
             'TS_F_MDS_1_QC', 'LW_IN_F_MDS', 'LW_IN_F_MDS_QC', 'LW_IN_F', 'LW_IN_F_QC', 'LW_OUT','SWC_F_MDS_1']]
        selected_data = selected_data[mask]
        selected_data.to_csv(outfile, index=False)

if ifupdate:
    data = pd.read_excel(excel_file)
    data['start_year'], data['end_year'] = '',''
    filenames = search_file(fileter_dir,'csv')
    for fileName in filenames:
        print(fileName)
        '''解析文件名'''
        dirName = fileName
        siteName = dirName.split('_')[0]
        year_range = dirName.split('_')[1][:-4]
        start_year = int(year_range.split('-')[0])
        end_year = int(year_range.split('-')[1])
        data.loc[data['SITE_ID'] == siteName, 'start_year'] = start_year
        data.loc[data['SITE_ID'] == siteName, 'end_year'] = end_year
    data.to_excel(excel_file, index=False)