from utils.old.util import *
import warnings
warnings.filterwarnings("ignore")

'''2024.7.3'''
'''画站点温度变化'''
'''筛选出有数据的站点，然后把AATSR和测量都有数据的搞出来，算个平均'''
'''看一下LST变化和土壤植被温度变化的速率是否一致'''

indir_Fluxnet = r"D:\data\AATSR_product\Fluxnet2015\\"
infile_site_imagexy = indir_Fluxnet + r"FLUXSITE_imagexy.csv"
data_loc = pd.read_csv(infile_site_imagexy)
# selected_sites = data_loc[(data_loc['START_YEAR']==2002) * (data_loc['END_YEAR'] ==2012)]['SITE_ID'].tolist()
selected_sites = data_loc['SITE_ID'].tolist()
print(selected_sites)

indir_csv = r"D:\data\AATSR_product\Fluxnet_AATSR\2_val_2002-2012\0_raw_h5_2002-2012\Merge_csv\\"
outdir_csv = r"D:\data\AATSR_product\Fluxnet_AATSR\2_val_2002-2012\0_raw_h5_2002-2012\Merge_csv_month_ave\\"
save_file = r"D:\data\AATSR_product\Fluxnet_AATSR\monthly_averages.csv"
mkdir_if_not_exist(outdir_csv)

ifextract = 0
ifmerge = 0
ifplot = 0
ifplot_lst = 1
ifplot_Ts = 0
ifplot_Tv = 0

if ifextract:
    def process_file(filepath):
        data = pd.read_csv(filepath)
        data['UTC_Time'] = pd.to_datetime(data['UTC_Time'])
        data.set_index('UTC_Time', inplace=True)
        return data

    columns = ['lstN', 'lstO', 'lst', 'Ts', 'Tv', 'TS_F_MDS_1', 'TA_F_MDS', 'SWC_F_MDS_1']
    for site in selected_sites:
        monthly_averages = {}
        infile_csv = indir_csv + site + ".csv"
        if not os.path.isfile(infile_csv): continue
        print(site)

        for year in range(2002, 2013):
            for month in range(1, 13):
                monthly_data = {}
                if not os.path.exists(infile_csv):
                    continue
                data = process_file(infile_csv)

                # 逐个变量进行筛选并计算平均值
                for column in columns:
                    if column == 'lstN':
                        ind = (data['lstN'] >= 220)
                    elif column == 'lstO':
                        ind = (data['lstO'] >= 220)
                    elif column == 'lst':
                        ind = (data['lst'] >= 220) & (data['lst'] != np.nan)
                    elif column == 'Ts':
                        ind = (data['Ts'] != 273.15) & (data['Ts'] >= 220)
                    elif column == 'Tv':
                        ind = (data['Tv'] != 273.15) & (data['Tv'] >= 220)
                    elif column == 'TS_F_MDS_1':
                        ind = (data['TS_F_MDS_1'] >= 0) & (data['TS_F_MDS_1'] != np.nan)
                    elif column == 'SWC_F_MDS_1':
                        ind = (data['SWC_F_MDS_1'] >= 0)
                    # 其他列筛选条件可以根据需要添加
                    else:
                        ind = (data[column] != np.nan)

                    filtered_data = data[(data.index.year == year) & (data.index.month == month) & ind]
                    if not filtered_data.empty:
                        monthly_data[column] = filtered_data[column].mean()

                if monthly_data:
                    monthly_averages[(year, month)] = monthly_data

        # Convert dictionary to DataFrame
        monthly_averages_df = pd.DataFrame(monthly_averages).T
        monthly_averages_df.index.names = ['Year', 'Month']

        # Sort the DataFrame by Year and Month
        monthly_averages_df = monthly_averages_df.sort_index(level=['Year', 'Month'])

        # Print or save the monthly averages
        print(monthly_averages_df)
        monthly_averages_df.to_csv(outdir_csv + site + ".csv")

if ifmerge:
    fileNames = search_file(outdir_csv, '.csv')
    all_data = pd.DataFrame()

    for fileName in fileNames:
        print(fileName)
        file_path = os.path.join(outdir_csv, fileName)
        data = pd.read_csv(file_path)

        # Add a column for the site name (file name without extension)
        site_name = fileName[:-4]
        data['site_name'] = site_name
        data = data.fillna(-9999).replace(0, -9999)
        # Append the data to the all_data DataFrame
        all_data = pd.concat([all_data, data], ignore_index=True)

    # Save the combined data to a CSV file
    outfile = r"D:\data\AATSR_product\Fluxnet_AATSR\2_val_2002-2012\0_raw_h5_2002-2012\\All_sites_month_ave.csv"
    all_data.to_csv(outfile, index=False)

if ifplot:
    data = pd.read_csv(save_file)
    data['Time'] = data['Year']*100 + data['Month']
    plt.figure(figsize=(12,6))
    # plt.plot(range(len(data['Time'])),data['lst'], label='lst')
    plt.plot(data['Ts']-data['Tv'])
    # plt.plot(range(len(data['Time'], data['Ts'], label='Ts')))
    # plt.xticks([index for index in range(len(data['Time']))], rotation=45)
    plt.legend()
    plt.ylim(-5,5)
    plt.show()

if ifplot_lst:
    file_path = r'D:\data\AATSR_product\Fluxnet_AATSR\2_val_2002-2012\0_raw_h5_2002-2012\All_sites_month_ave.csv'
    data = pd.read_csv(file_path)

    # 转换Year和Month为日期格式，筛选2002年7月到2012年4月的数据
    data['Date'] = pd.to_datetime(data[['Year', 'Month']].assign(day=1))
    filtered_data = data[(data['Date'] >= '2002-07-01') & (data['Date'] <= '2012-04-30')]

    # 将-9999值替换为NaN
    filtered_data.replace(-9999, pd.NA, inplace=True)

    # 转换lstN为数值类型，并移除包含NaN的行
    filtered_data['lstN'] = pd.to_numeric(filtered_data['lstN'], errors='coerce')
    filtered_data.dropna(subset=['lstN'], inplace=True)

    # 创建数据透视表，确保每个年份包含所有月份
    pivot_data = filtered_data.pivot_table(index='Year', columns='Month', values='lstN')

    # 计算每个月的十年平均温度
    monthly_avg = pivot_data.mean()

    # 计算每个月的温度与十年平均温度的差值
    temp_diff = pivot_data.subtract(monthly_avg, axis=1)

    # 准备月份名称
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # 准备颜色映射
    norm = plt.Normalize(temp_diff.min().min(), temp_diff.max().max())
    cmap = plt.get_cmap('coolwarm')

    # 生成图形
    fig, axes = plt.subplots(nrows=2, ncols=6, figsize=(20, 6), subplot_kw=dict(aspect="equal"))
    axes = axes.flatten()

    for i, (year, ax) in enumerate(zip(temp_diff.index, axes[:-1])):  # 忽略最后一个子图
        values = temp_diff.loc[year].tolist()
        colors = [cmap(norm(value)) for value in values]

        wedges, _ = ax.pie([0.05] + [1] * 12, colors=['white'] + colors, startangle=90, counterclock=True,  # 修改为逆时针
                           wedgeprops=dict(width=0.5))

        # 添加年份标签
        ax.text(0, 0, str(year), horizontalalignment='center', verticalalignment='center', fontsize=20, weight='bold')

    # 在最后一个位置画example
    ax = axes[-1]
    example_values = [-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]  # 示例数据
    example_colors = [plt.cm.coolwarm(norm(value)) for value in example_values]
    wedges, _ = ax.pie([0.05] + [1] * 12, colors=['white'] + example_colors, startangle=90, counterclock=True,  # 修改为逆时针
                       wedgeprops=dict(width=0.5))

    # 添加'Example'标签
    ax.text(0, 0, 'Example', horizontalalignment='center', verticalalignment='center', fontsize=14, weight='bold')

    # 添加月份标签
    bbox_props = dict(boxstyle="square,pad=0.3", fc="white", ec="none", alpha=0)  # 设置边框为透明
    kw = dict(bbox=bbox_props, zorder=1, va="center", fontsize=14)  # 增加字体大小和zorder
    for j, (wedge, month) in enumerate(zip(wedges[1:], months)):
        ang = (wedge.theta2 - wedge.theta1) / 2. + wedge.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]

        # 调整标签位置，使其位于饼图内部
        ax.annotate(month, xy=(x, y), xytext=(1.0 * x, 1.0 * y),
                    horizontalalignment=horizontalalignment, **kw)

    # 添加颜色条
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    # 创建一个新的轴用于颜色条
    fig.subplots_adjust(right=0.90, wspace=None, hspace=None)
    cbar_ax = fig.add_axes([0.93, 0.15, 0.02, 0.7])  # 左, 下, 宽, 高

    # 添加颜色条
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation='vertical', label='Temperature difference (K)')
    cbar.ax.tick_params(labelsize=14)  # 设置刻度标签的字体大小

    plt.tight_layout(rect=[0, 0, 0.9, 1])
    plt.show()

if ifplot_Ts:
    item = 'Ts'
    file_path = r'D:\data\AATSR_product\Fluxnet_AATSR\2_val_2002-2012\0_raw_h5_2002-2012\All_sites_month_ave.csv'
    data = pd.read_csv(file_path)

    # 转换Year和Month为日期格式，筛选2002年7月到2012年4月的数据
    data['Date'] = pd.to_datetime(data[['Year', 'Month']].assign(day=1))
    filtered_data = data[(data['Date'] >= '2002-07-01') & (data['Date'] <= '2012-04-30')]

    # 将-9999值替换为NaN
    filtered_data.replace(-9999, pd.NA, inplace=True)

    # 转换lstN为数值类型，并移除包含NaN的行
    filtered_data[item] = pd.to_numeric(filtered_data[item], errors='coerce')
    filtered_data.dropna(subset=[item], inplace=True)

    # 创建数据透视表，确保每个年份包含所有月份
    pivot_data = filtered_data.pivot_table(index='Year', columns='Month', values=item)

    # 计算每个月的十年平均温度
    monthly_avg = pivot_data.mean()

    # 计算每个月的温度与十年平均温度的差值
    temp_diff = pivot_data.subtract(monthly_avg, axis=1)

    # 准备月份名称
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # 准备颜色映射
    norm = plt.Normalize(temp_diff.min().min(), temp_diff.max().max())
    cmap = plt.get_cmap('coolwarm')

    # 生成图形
    fig, axes = plt.subplots(nrows=2, ncols=6, figsize=(20, 6), subplot_kw=dict(aspect="equal"))
    axes = axes.flatten()

    for i, (year, ax) in enumerate(zip(temp_diff.index, axes[:-1])):  # 忽略最后一个子图
        values = temp_diff.loc[year].tolist()
        colors = [cmap(norm(value)) for value in values]

        wedges, _ = ax.pie([0.05] + [1] * 12, colors=['white'] + colors, startangle=90, counterclock=True,  # 修改为逆时针
                           wedgeprops=dict(width=0.5))

        # 添加年份标签
        ax.text(0, 0, str(year), horizontalalignment='center', verticalalignment='center', fontsize=20, weight='bold')

    # 在最后一个位置画example
    ax = axes[-1]
    example_values = [-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]  # 示例数据
    example_colors = [plt.cm.coolwarm(norm(value)) for value in example_values]
    wedges, _ = ax.pie([0.05] + [1] * 12, colors=['white'] + example_colors, startangle=90, counterclock=True,  # 修改为逆时针
                       wedgeprops=dict(width=0.5))

    # 添加'Example'标签
    ax.text(0, 0, 'Example', horizontalalignment='center', verticalalignment='center', fontsize=14, weight='bold')

    # 添加月份标签
    bbox_props = dict(boxstyle="square,pad=0.3", fc="white", ec="none", alpha=0)  # 设置边框为透明
    kw = dict(bbox=bbox_props, zorder=1, va="center", fontsize=14)  # 增加字体大小和zorder
    for j, (wedge, month) in enumerate(zip(wedges[1:], months)):
        ang = (wedge.theta2 - wedge.theta1) / 2. + wedge.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]

        # 调整标签位置，使其位于饼图内部
        ax.annotate(month, xy=(x, y), xytext=(1.0 * x, 1.0 * y),
                    horizontalalignment=horizontalalignment, **kw)

    # 添加颜色条
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    # 创建一个新的轴用于颜色条
    fig.subplots_adjust(right=0.90, wspace=None, hspace=None)
    cbar_ax = fig.add_axes([0.93, 0.15, 0.02, 0.7])  # 左, 下, 宽, 高

    # 添加颜色条
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation='vertical', label='Temperature difference (K)')
    cbar.ax.tick_params(labelsize=14)  # 设置刻度标签的字体大小

    plt.tight_layout(rect=[0, 0, 0.9, 1])
    plt.show()

if ifplot_Tv:
    item = 'Tv'
    file_path = r'D:\data\AATSR_product\Fluxnet_AATSR\2_val_2002-2012\0_raw_h5_2002-2012\All_sites_month_ave.csv'
    data = pd.read_csv(file_path)

    # 转换Year和Month为日期格式，筛选2002年7月到2012年4月的数据
    data['Date'] = pd.to_datetime(data[['Year', 'Month']].assign(day=1))
    filtered_data = data[(data['Date'] >= '2002-07-01') & (data['Date'] <= '2012-04-30')]

    # 将-9999值替换为NaN
    filtered_data.replace(-9999, pd.NA, inplace=True)

    # 转换lstN为数值类型，并移除包含NaN的行
    filtered_data[item] = pd.to_numeric(filtered_data[item], errors='coerce')
    filtered_data.dropna(subset=[item], inplace=True)

    # 创建数据透视表，确保每个年份包含所有月份
    pivot_data = filtered_data.pivot_table(index='Year', columns='Month', values=item)

    # 计算每个月的十年平均温度
    monthly_avg = pivot_data.mean()

    # 计算每个月的温度与十年平均温度的差值
    temp_diff = pivot_data.subtract(monthly_avg, axis=1)

    # 准备月份名称
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # 准备颜色映射
    norm = plt.Normalize(temp_diff.min().min(), temp_diff.max().max())
    cmap = plt.get_cmap('coolwarm')

    # 生成图形
    fig, axes = plt.subplots(nrows=2, ncols=6, figsize=(20, 6), subplot_kw=dict(aspect="equal"))
    axes = axes.flatten()

    for i, (year, ax) in enumerate(zip(temp_diff.index, axes[:-1])):  # 忽略最后一个子图
        values = temp_diff.loc[year].tolist()
        colors = [cmap(norm(value)) for value in values]

        wedges, _ = ax.pie([0.05] + [1] * 12, colors=['white'] + colors, startangle=90, counterclock=True,  # 修改为逆时针
                           wedgeprops=dict(width=0.5))

        # 添加年份标签
        ax.text(0, 0, str(year), horizontalalignment='center', verticalalignment='center', fontsize=20, weight='bold')

    # 在最后一个位置画example
    ax = axes[-1]
    example_values = [-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]  # 示例数据
    example_colors = [plt.cm.coolwarm(norm(value)) for value in example_values]
    wedges, _ = ax.pie([0.05] + [1] * 12, colors=['white'] + example_colors, startangle=90, counterclock=True,  # 修改为逆时针
                       wedgeprops=dict(width=0.5))

    # 添加'Example'标签
    ax.text(0, 0, 'Example', horizontalalignment='center', verticalalignment='center', fontsize=14, weight='bold')

    # 添加月份标签
    bbox_props = dict(boxstyle="square,pad=0.3", fc="white", ec="none", alpha=0)  # 设置边框为透明
    kw = dict(bbox=bbox_props, zorder=1, va="center", fontsize=14)  # 增加字体大小和zorder
    for j, (wedge, month) in enumerate(zip(wedges[1:], months)):
        ang = (wedge.theta2 - wedge.theta1) / 2. + wedge.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]

        # 调整标签位置，使其位于饼图内部
        ax.annotate(month, xy=(x, y), xytext=(1.0 * x, 1.0 * y),
                    horizontalalignment=horizontalalignment, **kw)

    # 添加颜色条
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    # 创建一个新的轴用于颜色条
    fig.subplots_adjust(right=0.90, wspace=None, hspace=None)
    cbar_ax = fig.add_axes([0.93, 0.15, 0.02, 0.7])  # 左, 下, 宽, 高

    # 添加颜色条
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation='vertical', label='Temperature difference (K)')
    cbar.ax.tick_params(labelsize=14)  # 设置刻度标签的字体大小

    plt.tight_layout(rect=[0, 0, 0.9, 1])
    plt.show()