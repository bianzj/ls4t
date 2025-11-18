from utils.old.util import *
from matplotlib.colors import ListedColormap

'''2024.6.25'''
'''画站点位置和地表类型统计图'''

base_dir = r"D:\data\AATSR_product\Fluxnet_AATSR\\"
lsct_name = "0_raw_h5_2002-2012"
val_dir = base_dir + r"2_val_2002-2012\\" + lsct_name + r"\Merge_csv\\"
type_world = r"D:\data\0_base\type\\type_world_1000.tif"
infile_site_igbp = r"D:\data\AATSR_product\Fluxnet2015\\FLUXSITE.xlsx"
infile_site_loc = r"D:\data\AATSR_product\Fluxnet2015\\FLUXSITE_imagexy.csv"
infile_selected_sites = r"D:\data\AATSR_product\Fluxnet2015\\Selected_sites.csv"

ifget_siteName = 0
ifplot_img = 1
ifstats = 0

if ifget_siteName:
    fileNames = search_file(val_dir, ['.csv'])
    therhold = 9
    alldata = []
    valid_site_names = []
    invalid_site_num = 0
    for fileName in fileNames:
        infile = val_dir + fileName
        data = pd.read_csv(infile)
        lstN_inv = data['lstN']
        lstO_inv = data['lstO']
        lst_mea = data['lst']
        invalid_num = sum(np.abs(lstN_inv - lst_mea) < therhold)
        print("--------------------------------------------------------------------------------")
        print(fileName)
        print("有效点数：%03d" % invalid_num)
        if invalid_num <= 30: continue
        if invalid_num > 30:
            valid_site_names.append(fileName.split('.')[0])

    site_igbp_df = pd.read_excel(infile_site_igbp)
    site_loc_df = pd.read_csv(infile_site_loc)

    filtered_site_igbp_df = site_igbp_df[site_igbp_df['SITE_ID'].isin(valid_site_names)]
    filtered_site_loc_df = site_loc_df[site_loc_df['SITE_ID'].isin(valid_site_names)]

    merged_df = pd.merge(filtered_site_loc_df, filtered_site_igbp_df, on='SITE_ID', how='inner')

    # 排除特定的IGBP类型
    excluded_igbp = ['WET', 'URB', 'SNO', 'WAT']
    merged_df = merged_df[~merged_df['IGBP'].isin(excluded_igbp)]

    # 选择所需的列
    selected_columns = ['SITE_ID', 'IGBP', 'LOCATION_LONG_x', 'LOCATION_LAT_x', 'IMAGEX', 'IMAGEY']
    result_df = merged_df[selected_columns]

    # 保存结果到CSV文件
    result_df.to_csv(infile_selected_sites, index=False)


if ifplot_img:
    dataset = gdal.Open(type_world)
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()

    plt.rc('font', family='Times New Roman')

    # 定义颜色映射
    colors = ['#05450a', '#086a10', '#54a708', '#78d203', '#009900', '#c6b044', '#dcd159',
              '#dade48', '#fbff13', '#b6ff05', '#27ff87', '#c24f44', '#a5a5a5', '#ff6d4c',
              '#69fff8', '#f9ffa4', 'white']  # '#1c0dff'
    categories = ['EBF', 'ENF', 'DNF', 'DBF', 'MF', 'CSH', 'OSH', 'WSA', 'SAV', 'GRA', 'WET', 'CRO', 'URB', 'CVM',
                  'SNO', 'BSV', 'WAT']
    cmap = ListedColormap(colors)

    # 分类颜色字典
    classification_colors = {
        "Forest": 'red',
        "Shrub": 'purple',
        "Savanna": 'blue',
        'Grass': 'yellow',
        "Crop": 'black',
        'Other': 'green'
    }
    classification = {
        "Forest": ['EBF', 'ENF', 'DNF', 'DBF', 'MF'],
        "Savanna": ['WSA', 'SAV'],
        "Shrub": ['CSH', 'OSH'],
        'Grass': ['GRA'],
        "Crop": ['CRO', 'CVM'],
        'Other': ['BSV','WET', 'URB', 'SNO', 'WAT']
    }

    # 创建图像
    fig, ax = plt.subplots(figsize=(10, 5))
    cax = ax.imshow(data, cmap=cmap, vmin=1, vmax=17, extent=[-180, 180, -90, 90])

    # 添加颜色条
    cbar = fig.colorbar(cax, ticks=np.arange(1.5, 18.5))
    cbar.ax.set_yticklabels(categories)

    # 设置坐标系范围
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    infile_selected_sites = r"D:\data\AATSR_product\Fluxnet2015\Selected_sites.csv"
    sites = pd.read_csv(infile_selected_sites)

    # 在主图中标注站点
    for idx, row in sites.iterrows():
        igbp_class = row['IGBP']
        color = 'red'  # 默认颜色
        # for key, values in classification.items():
        #     if igbp_class in values:
        #         color = classification_colors[key]
        #         break
        ax.plot(row['LOCATION_LONG_x'], row['LOCATION_LAT_x'], marker='^', color=color, markersize=6)


    def create_zoomed_inset(ax, xlim, ylim, location):
        ax_inset = fig.add_axes(location)
        ax_inset.imshow(data, cmap=cmap, vmin=1, vmax=17, extent=[-180, 180, -90, 90])
        ax_inset.set_xlim(xlim)
        ax_inset.set_ylim(ylim)
        ax_inset.set_xticks([])
        ax_inset.set_yticks([])

        for idx, row in sites.iterrows():
            if xlim[0] <= row['LOCATION_LONG_x'] <= xlim[1] and ylim[0] <= row['LOCATION_LAT_x'] <= ylim[1]:
                igbp_class = row['IGBP']
                color = 'red'
                # for key, values in classification.items():
                #     if igbp_class in values:
                #         color = classification_colors[key]
                #         break
                ax_inset.plot(row['LOCATION_LONG_x'], row['LOCATION_LAT_x'], marker='^', color=color, markersize=6)

        return ax_inset


    # # 创建美国、欧洲和澳大利亚的放大窗口
    # create_zoomed_inset(ax, [-130, -70], [25, 60], [0.10, 0.5, 0.2, 0.3])  # 美国
    # create_zoomed_inset(ax, [-10, 25], [35, 60], [0.325, 0.6, 0.15, 0.25])  # 欧洲
    # create_zoomed_inset(ax, [110, 155], [-45, -10], [0.6, 0.175, 0.2, 0.3])  # 澳大利亚

    # # 添加图例
    # legend_elements = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10, label=key)
    #                    for key, color in classification_colors.items()]
    # ax.legend(handles=legend_elements, loc='lower left', title="FluxNet")

    plt.tight_layout()
    plt.show()

if ifstats:
    # 读取CSV文件
    infile_selected_sites = r"D:\data\AATSR_product\Fluxnet2015\Selected_sites.csv"
    sites = pd.read_csv(infile_selected_sites)

    # 统计IGBP类型的频数
    igbp_counts = sites['IGBP'].value_counts()

    # 定义IGBP类型及其顺序
    categories = ['EBF', 'ENF', 'DNF', 'DBF', 'MF', 'CSH', 'OSH', 'WSA', 'SAV', 'GRA', 'WET', 'CRO', 'URB', 'CVM', 'SNO', 'BSV', 'WAT']
    igbp_counts = igbp_counts.reindex(categories).fillna(0)

    # 过滤掉频数为零的类别
    igbp_counts = igbp_counts[igbp_counts > 0]

    # 创建柱状图
    plt.rc('font', family='Times New Roman', size=12)
    plt.figure(figsize=(8, 6))

    # 定义颜色映射
    colors = ['lightcoral', 'lightcoral', 'lightcoral', 'lightcoral',  # EBF, ENF, DNF, DBF, MF
              'lavender', 'lavender',  # CSH, OSH
              'lightblue', 'lightblue',  # WSA, SAV
              'lightgoldenrodyellow',
              'lightgrey'  # GRA
              ]

    bars = igbp_counts.plot(kind='bar', color=colors)

    # 在每个柱子上标注整数数字
    for i, val in enumerate(igbp_counts):
        plt.text(i, val + 0.2, str(int(val)), ha='center', va='bottom', fontsize=12)

    # 设置标题和标签
    plt.xlabel('IGBP Types')
    plt.ylabel('Frequency')
    plt.xticks(rotation=45, ha='right')

    # 显示图例
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, color='lightcoral', label='Forest (EBF, ENF, DNF, DBF, MF)'),
        plt.Rectangle((0, 0), 1, 1, color='lavender', label='Shrub (CSH, OSH)'),
        plt.Rectangle((0, 0), 1, 1, color='lightblue', label='Savanna (WSA, SAV)'),
        plt.Rectangle((0, 0), 1, 1, color='lightgoldenrodyellow', label='Grassland (GRA)'),
        plt.Rectangle((0, 0), 1, 1, color='lightgray', label='Crop (CRO)'),
        # plt.Rectangle((0, 0), 1, 1, color='cyan', label='Others (WET, URB, CVM, SNO, BSV, WAT)'),
    ]
    plt.legend(handles=legend_elements, loc='upper center')

    # 显示图表
    plt.tight_layout()
    plt.show()

# 换成三角形一个颜色