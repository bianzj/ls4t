import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
import warnings
warnings.filterwarnings("ignore")

'''2025.10.28'''
'''Musyq lai/fvc 提取Fluxnet值'''
'''提取土壤发射率值'''
'''需要先运行fvc_extract_sites.py 跑出FVC500m全图'''

if __name__ == '__main__':
    if_lai = 1
    if_fvc = 0
    indir_fvc = r'/media/hero/lsct02/fvc_h5/'
    indir_lai = r'/media/hero/lsct02/lai/'
    base_dir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/'
    indir_fluxnet_data = base_dir + r'Fluxnet_data/'
    infile_fluxnet = base_dir + r'FLUXSITE_imagexy.xlsx'

    infile_type_wgs84_500 = r"/home/hero/data/type/type_world_500.tif"
    indir_emis = r'/home/hero/data/base/0_base/emis/'
    indir_type = r'/home/hero/data/type/'
    infile_soil_emis = indir_emis + 'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
    infile_type = indir_type + 'type_world_1000.tif'
    infile_veg_emis = indir_emis + 'IGBP_Emi.txt'
    
    data = pd.read_excel(infile_fluxnet)
    lon,lat = data['LOCATION_LONG'],data['LOCATION_LAT']
    if 'IMAGEX_500' not in data.columns:
        lat = data['LOCATION_LAT']
        lon = data['LOCATION_LONG']
        imagex,imagey = loc2map(lat,lon,gdal.Open(infile_type_wgs84_500))
        data['IMAGEX_500'] = imagex
        data['IMAGEY_500'] = imagey
        data.to_excel(infile_fluxnet,index=False)
    
    if 'emisS' not in data.columns:
        '''读取发射率'''
        [emis_s_, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_soil_emis)
        emis_s_ = emis_s_ / 1000
        [classif_, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_type)
        classif_ = np.asarray(classif_, int)
        classif_[classif_ == 255] = 17
        emis_v_ = read_txt_array(infile_veg_emis, 0, 2)
        emis_v_ = emis_v_[classif_, 0] / 1000
        indx,indy = data['IMAGEX'],data['IMAGEY']
        data['emisS'] = emis_s_[indx,indy]
        data['emisV'] = emis_v_[indx,indy]
        data.to_excel(infile_fluxnet,index=False)

    if if_lai:
        if_extract = 0
        if_interpolated = 0
        if_ifmerge = 1

        site_id = data['SITE_ID']
        imagex,imagey = data['IMAGEX'],data['IMAGEY']
        outfile_lai = base_dir + 'lai_fluxnet.xlsx'

        if if_extract:
            '''读取LAI'''
            for year in range(2002,2013):
                indir_year = indir_lai + '%04d' % year + '/'
                fileNames = search_file_rej(indir_year,['h5'],'temp')
                fileNames.sort()
                for fileName in fileNames:
                    print(fileName)
                    doy = int(fileName[-6:-3])
                    month,day = doy2date(year,doy)
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    infile = indir_year + fileName
                    lai_data = read_h5py_item(infile,'data')
                    lai = lai_data[imagex,imagey]
                    
                    # 创建DataFrame保存数据，site_id作为列名
                    df = pd.DataFrame([lai], index=[date_str], columns=site_id)
                    
                    # 如果文件不存在则创建，否则追加
                    if not os.path.exists(outfile_lai):
                        df.to_excel(outfile_lai)
                    else:
                        existing_df = pd.read_excel(outfile_lai, index_col=0)
                        combined_df = pd.concat([existing_df, df])
                        combined_df.to_excel(outfile_lai)
            
        if if_interpolated:
            # LAI数据插值处理
            print("开始LAI数据插值处理...")
            lai_df = pd.read_excel(outfile_lai, index_col=0)
            lai_df.index = pd.to_datetime(lai_df.index)
            lai_df = lai_df.sort_index()
            
            # 创建完整日期范围(每天)
            full_date_range = pd.date_range(
                start=lai_df.index.min(),
                end=lai_df.index.max(),
                freq='D'
            )
            
            # 重新索引并线性插值
            lai_df = lai_df.reindex(full_date_range)
            lai_df_interpolated = lai_df.interpolate(method='linear')
            
            # 保存插值结果
            outfile_lai_interp = base_dir + 'lai_fluxnet_interpolated.xlsx'
            lai_df_interpolated.to_excel(outfile_lai_interp)

        if if_ifmerge:
            print("开始将插值后的 LAI 合并写入 Fluxnet CSV 中...")
            # 读取插值后的 LAI（每日）
            outfile_lai_interp = base_dir + 'lai_fluxnet_interpolated.xlsx'
            lai_df = pd.read_excel(outfile_lai_interp, index_col=0)
            # 确保索引为 datetime
            lai_df.index = pd.to_datetime(lai_df.index)
            # 为映射方便，建立按日期 (date object) 索引的字典：site -> Series(date -> lai_value)
            lai_map = {}
            for col in lai_df.columns:
                # 用 date 作为索引键（python date 对象），这样可以直接映射 csv 中的 timestamp.date()
                series_by_date = pd.Series(lai_df[col].values, index=lai_df.index.date)
                lai_map[col] = series_by_date

            # 遍历 Fluxnet CSV 文件
            csv_files = search_file_rej(indir_fluxnet_data, ['csv'], 'temp')  # 若已有该函数可用，否则可用 glob
            import glob
            if not csv_files:
                csv_files = glob.glob(os.path.join(indir_fluxnet_data, '*.csv'))

            for csv_file in csv_files:
                print("处理:", csv_file)
                try:
                    df_csv = pd.read_csv(indir_fluxnet_data + csv_file, dtype=str)  # 先全部读为 str，后面解析时间列
                except Exception as e:
                    print("  无法读取 CSV:", csv_file, e)
                    continue

                time_col = df_csv.columns[0]
                times = pd.to_datetime(df_csv[time_col], errors='coerce', infer_datetime_format=True)

                df_csv['_TIMESTAMP_parsed'] = times
                # 先假定解析成功，否则尝试合并 DATE+TIME（如需要可扩展）
                if df_csv['_TIMESTAMP_parsed'].isna().all() and 'DATE' in df_csv.columns and 'TIME' in df_csv.columns:
                    df_csv['_TIMESTAMP_parsed'] = pd.to_datetime(df_csv['DATE'].astype(str) + ' ' + df_csv['TIME'].astype(str),
                                                                errors='coerce', infer_datetime_format=True)
                if df_csv['_TIMESTAMP_parsed'].isna().all():
                    print("  警告：无法解析时间列，跳过文件。")
                    continue

                # 推断站点 ID（同原逻辑）
                basename = csv_file.split('_')[0]
                site_id = basename
                chosen_site_col = None
                chosen_site_col = site_id

                if chosen_site_col is None:
                    # 尝试用 data 表匹配
                    try:
                        if 'SITE_ID' in data.columns:
                            candidates = data['SITE_ID'].astype(str).tolist()
                            for c in candidates:
                                if c.lower() in site_id.lower() or site_id.lower() in c.lower():
                                    chosen_site_col = c
                                    break
                    except Exception:
                        pass

                if chosen_site_col is None:
                    print("  警告：无法找到对应的 LAI 列（site）。跳过文件：", csv_file)
                    continue

                # --- 计算时区并转换到 UTC 日期（优先用时区库，回退为经度估算） ---
                tz = None
                lat_site = None
                lon_site = None
                try:
                    # 先尝试按 SITE_ID 精确匹配 data 表查经纬度
                    row = data[data['SITE_ID'].astype(str).str.lower() == str(chosen_site_col).lower()]
                    if row.empty:
                        # 尝试模糊匹配 LOCATION 或文件名
                        row = data[(data['SITE_ID'].astype(str).str.contains(site_id, case=False, na=False)) |
                                   (data['LOCATION_LONG'].astype(str).str.contains(site_id, case=False, na=False)) |
                                   (data['LOCATION_LAT'].astype(str).str.contains(site_id, case=False, na=False))]
                    if not row.empty and 'LOCATION_LAT' in row.columns and 'LOCATION_LONG' in row.columns:
                        lat_site = float(row['LOCATION_LAT'].iloc[0])
                        lon_site = float(row['LOCATION_LONG'].iloc[0])
                        tz = get_timezone(lat_site, lon_site)
                except Exception:
                    tz = None

                # 如果没有找到时区，再尝试 data 表可能的时区/偏移字段
                if tz is None:
                    try:
                        row = data[data['SITE_ID'].astype(str).str.lower() == str(chosen_site_col).lower()]
                        if not row.empty:
                            if 'UTC_OFFSET' in row.columns and pd.notnull(row['UTC_OFFSET'].iloc[0]):
                                offset_hours = float(row['UTC_OFFSET'].iloc[0])
                            elif 'TIMEZONE' in row.columns and pd.notnull(row['TIMEZONE'].iloc[0]):
                                # 若 TIMEZONE 存的是时区名
                                try:
                                    tz = pytz.timezone(str(row['TIMEZONE'].iloc[0]))
                                except Exception:
                                    offset_hours = float(row['TIMEZONE'].iloc[0])
                            else:
                                offset_hours = None
                        else:
                            offset_hours = None
                    except Exception:
                        offset_hours = None

                # 产生 UTC 日期用于映射 LAI（LAI 是以 UTC 日为索引）
                if tz is not None:
                    # 使用时区库确保处理夏令时等
                    def to_utc_date(ts):
                        if pd.isna(ts):
                            return None
                        try:
                            # 若 ts 为 pandas.Timestamp（naive），用 tz.localize；若已带时区，直接 astimezone
                            if ts.tzinfo is None:
                                loc = tz.localize(ts)
                            else:
                                loc = ts.astimezone(tz)
                            utc = loc.astimezone(pytz.UTC)
                            return utc.date()
                        except Exception:
                            return None

                    df_csv['_UTC_date'] = df_csv['_TIMESTAMP_parsed'].apply(to_utc_date)
                else:
                    # 回退：用经度估算偏移小时（每 15° 约一小时），若有 offset_hours 则使用
                    if 'offset_hours' not in locals():
                        offset_hours = None
                    if offset_hours is None:
                        if lon_site is not None:
                            offset_hours = int(round(lon_site / 15.0))
                        else:
                            offset_hours = 0
                    df_csv['_TIMESTAMP_utc'] = df_csv['_TIMESTAMP_parsed'] - pd.to_timedelta(offset_hours, unit='h')
                    df_csv['_UTC_date'] = df_csv['_TIMESTAMP_utc'].dt.date

                # 使用映射将每日 LAI（UTC 日）填入每条 30 分钟记录
                series_map = lai_map.get(chosen_site_col, None)
                if series_map is None:
                    # 尝试模糊匹配 lai_map 列名
                    for col in lai_map.keys():
                        if site_id.lower() in col.lower() or col.lower() in site_id.lower():
                            series_map = lai_map[col]
                            break

                if series_map is None:
                    print("  警告：无法找到对应的 LAI 列（site）。跳过文件：", csv_file)
                    continue

                df_csv['LAI'] = df_csv['_UTC_date'].map(series_map)

                # 清理中间列并保存（覆盖原文件）
                df_csv.drop(columns=[c for c in ['_TIMESTAMP_parsed', '_TIMESTAMP_utc', '_UTC_date'] if c in df_csv.columns], inplace=True)
                out_csv = indir_fluxnet_data + csv_file
                try:
                    # 如需缩放在此处理
                    df_csv.to_csv(out_csv, index=False)
                    print("  已保存：", out_csv, " 时区:", getattr(tz, 'zone', offset_hours if 'offset_hours' in locals() else 'UTC'))
                except Exception as e:
                    print("  保存失败：", e)
        print("处理完成。")

    if if_fvc:
        if_extract = 0
        if_interpolated = 0
        if_ifmerge = 1

        site_id = data['SITE_ID']
        imagex,imagey = data['IMAGEX_500'],data['IMAGEY_500']
        outfile_fvc = base_dir + 'fvc_fluxnet.xlsx'

        if if_extract:
            '''读取FVC'''
            for year in range(2002,2013):
                indir_year = indir_fvc + '%04d' % year + '/'
                fileNames = search_file_rej(indir_year,['h5'],'temp')
                fileNames.sort()
                for fileName in fileNames:
                    print(fileName)
                    doy = int(fileName[-6:-3])
                    month,day = doy2date(year,doy)
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    infile = indir_year + fileName
                    fvc_data = read_h5py_item(infile,'data')
                    fvc = fvc_data[imagex,imagey]
                    
                    # 创建DataFrame保存数据，site_id作为列名
                    df = pd.DataFrame([fvc], index=[date_str], columns=site_id)
                    
                    # 如果文件不存在则创建，否则追加
                    if not os.path.exists(outfile_fvc):
                        df.to_excel(outfile_fvc)
                    else:
                        existing_df = pd.read_excel(outfile_fvc, index_col=0)
                        combined_df = pd.concat([existing_df, df])
                        combined_df.to_excel(outfile_fvc)
            
        if if_interpolated:
            # LAI数据插值处理
            print("开始LAI数据插值处理...")
            fvc_df = pd.read_excel(outfile_fvc, index_col=0)
            fvc_df.index = pd.to_datetime(fvc_df.index)
            fvc_df = fvc_df.sort_index()
            
            # 创建完整日期范围(每天)
            full_date_range = pd.date_range(
                start=fvc_df.index.min(),
                end=fvc_df.index.max(),
                freq='D'
            )
            
            # 重新索引并线性插值
            fvc_df = fvc_df.reindex(full_date_range)
            fvc_df_interpolated = fvc_df.interpolate(method='linear')
            
            # 保存插值结果
            outfile_fvc_interp = base_dir + 'fvc_fluxnet_interpolated.xlsx'
            fvc_df_interpolated.to_excel(outfile_fvc_interp)

        if if_ifmerge:
            print("开始将插值后的 fvc 合并写入 Fluxnet CSV 中...")
            # 读取插值后的 fvc（每日）
            outfile_fvc_interp = base_dir + 'fvc_fluxnet_interpolated.xlsx'
            fvc_df = pd.read_excel(outfile_fvc_interp, index_col=0)
            # 确保索引为 datetime
            fvc_df.index = pd.to_datetime(fvc_df.index)
            # 为映射方便，建立按日期 (date object) 索引的字典：site -> Series(date -> fvc_value)
            fvc_map = {}
            for col in fvc_df.columns:
                # 用 date 作为索引键（python date 对象），这样可以直接映射 csv 中的 timestamp.date()
                series_by_date = pd.Series(fvc_df[col].values, index=fvc_df.index.date)
                fvc_map[col] = series_by_date

            # 遍历 Fluxnet CSV 文件
            csv_files = search_file_rej(indir_fluxnet_data, ['csv'], 'temp')  # 若已有该函数可用，否则可用 glob
            import glob
            if not csv_files:
                csv_files = glob.glob(os.path.join(indir_fluxnet_data, '*.csv'))

            for csv_file in csv_files:
                print("处理:", csv_file)
                try:
                    df_csv = pd.read_csv(indir_fluxnet_data + csv_file, dtype=str)  # 先全部读为 str，后面解析时间列
                except Exception as e:
                    print("  无法读取 CSV:", csv_file, e)
                    continue

                time_col = df_csv.columns[0]
                times = pd.to_datetime(df_csv[time_col], errors='coerce', infer_datetime_format=True)

                df_csv['_TIMESTAMP_parsed'] = times
                # 先假定解析成功，否则尝试合并 DATE+TIME（如需要可扩展）
                if df_csv['_TIMESTAMP_parsed'].isna().all() and 'DATE' in df_csv.columns and 'TIME' in df_csv.columns:
                    df_csv['_TIMESTAMP_parsed'] = pd.to_datetime(df_csv['DATE'].astype(str) + ' ' + df_csv['TIME'].astype(str),
                                                                errors='coerce', infer_datetime_format=True)
                if df_csv['_TIMESTAMP_parsed'].isna().all():
                    print("  警告：无法解析时间列，跳过文件。")
                    continue

                # 推断站点 ID（同原逻辑）
                basename = csv_file.split('_')[0]
                site_id = basename
                chosen_site_col = None
                chosen_site_col = site_id

                if chosen_site_col is None:
                    # 尝试用 data 表匹配
                    try:
                        if 'SITE_ID' in data.columns:
                            candidates = data['SITE_ID'].astype(str).tolist()
                            for c in candidates:
                                if c.lower() in site_id.lower() or site_id.lower() in c.lower():
                                    chosen_site_col = c
                                    break
                    except Exception:
                        pass

                if chosen_site_col is None:
                    print("  警告：无法找到对应的 fvc 列（site）。跳过文件：", csv_file)
                    continue

                # --- 计算时区并转换到 UTC 日期（优先用时区库，回退为经度估算） ---
                tz = None
                lat_site = None
                lon_site = None
                try:
                    # 先尝试按 SITE_ID 精确匹配 data 表查经纬度
                    row = data[data['SITE_ID'].astype(str).str.lower() == str(chosen_site_col).lower()]
                    if row.empty:
                        # 尝试模糊匹配 LOCATION 或文件名
                        row = data[(data['SITE_ID'].astype(str).str.contains(site_id, case=False, na=False)) |
                                   (data['LOCATION_LONG'].astype(str).str.contains(site_id, case=False, na=False)) |
                                   (data['LOCATION_LAT'].astype(str).str.contains(site_id, case=False, na=False))]
                    if not row.empty and 'LOCATION_LAT' in row.columns and 'LOCATION_LONG' in row.columns:
                        lat_site = float(row['LOCATION_LAT'].iloc[0])
                        lon_site = float(row['LOCATION_LONG'].iloc[0])
                        tz = get_timezone(lat_site, lon_site)
                except Exception:
                    tz = None

                # 如果没有找到时区，再尝试 data 表可能的时区/偏移字段
                if tz is None:
                    try:
                        row = data[data['SITE_ID'].astype(str).str.lower() == str(chosen_site_col).lower()]
                        if not row.empty:
                            if 'UTC_OFFSET' in row.columns and pd.notnull(row['UTC_OFFSET'].iloc[0]):
                                offset_hours = float(row['UTC_OFFSET'].iloc[0])
                            elif 'TIMEZONE' in row.columns and pd.notnull(row['TIMEZONE'].iloc[0]):
                                # 若 TIMEZONE 存的是时区名
                                try:
                                    tz = pytz.timezone(str(row['TIMEZONE'].iloc[0]))
                                except Exception:
                                    offset_hours = float(row['TIMEZONE'].iloc[0])
                            else:
                                offset_hours = None
                        else:
                            offset_hours = None
                    except Exception:
                        offset_hours = None

                # 产生 UTC 日期用于映射 fvc（fvc 是以 UTC 日为索引）
                if tz is not None:
                    # 使用时区库确保处理夏令时等
                    def to_utc_date(ts):
                        if pd.isna(ts):
                            return None
                        try:
                            # 若 ts 为 pandas.Timestamp（naive），用 tz.localize；若已带时区，直接 astimezone
                            if ts.tzinfo is None:
                                loc = tz.localize(ts)
                            else:
                                loc = ts.astimezone(tz)
                            utc = loc.astimezone(pytz.UTC)
                            return utc.date()
                        except Exception:
                            return None

                    df_csv['_UTC_date'] = df_csv['_TIMESTAMP_parsed'].apply(to_utc_date)
                else:
                    # 回退：用经度估算偏移小时（每 15° 约一小时），若有 offset_hours 则使用
                    if 'offset_hours' not in locals():
                        offset_hours = None
                    if offset_hours is None:
                        if lon_site is not None:
                            offset_hours = int(round(lon_site / 15.0))
                        else:
                            offset_hours = 0
                    df_csv['_TIMESTAMP_utc'] = df_csv['_TIMESTAMP_parsed'] - pd.to_timedelta(offset_hours, unit='h')
                    df_csv['_UTC_date'] = df_csv['_TIMESTAMP_utc'].dt.date

                # 使用映射将每日 fvc（UTC 日）填入每条 30 分钟记录
                series_map = fvc_map.get(chosen_site_col, None)
                if series_map is None:
                    # 尝试模糊匹配 fvc_map 列名
                    for col in fvc_map.keys():
                        if site_id.lower() in col.lower() or col.lower() in site_id.lower():
                            series_map = fvc_map[col]
                            break

                if series_map is None:
                    print("  警告：无法找到对应的 fvc 列（site）。跳过文件：", csv_file)
                    continue

                df_csv['fvc'] = df_csv['_UTC_date'].map(series_map)

                # 清理中间列并保存（覆盖原文件）
                df_csv.drop(columns=[c for c in ['_TIMESTAMP_parsed', '_TIMESTAMP_utc', '_UTC_date'] if c in df_csv.columns], inplace=True)
                out_csv = indir_fluxnet_data + csv_file
                try:
                    # 如需缩放在此处理
                    df_csv.to_csv(out_csv, index=False)
                    print("  已保存：", out_csv, " 时区:", getattr(tz, 'zone', offset_hours if 'offset_hours' in locals() else 'UTC'))
                except Exception as e:
                    print("  保存失败：", e)
        print("处理完成。")