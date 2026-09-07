from utils.old.util import *

'''2024.7.2'''
'''按季节画平均图'''

base_dir = r"E:\AATSR\2009\lsct_month\\"
indir_base = r"E:\AATSR\\"
indir_type = indir_base + r"0_base\type\\"
infile_type = indir_type + r"type_world_2000.tif"

ifave = 0
ifplot = 1

seasons = {
    "Q1th": ['01', '02', '03'],
    "Q2nd": ['04', '05', '06'],
    "Q3rd": ['07', '08', '09'],
    'Q4th': ['10','11','12'],
}

if ifave:
    type, ns_type, nl_type, nb_type, geog_type, proj_type = read_image_gdal(infile_type)
    for season in seasons.keys():
        print(season)
        months = seasons[season]
        save_s = np.zeros([nl_type,ns_type])
        save_v = np.zeros([nl_type, ns_type])
        num_s = np.zeros([nl_type, ns_type])
        num_v = np.zeros([nl_type, ns_type])
        for month in months:
            infile_s = base_dir + month + r"\\AATSR_2009_%02d_lsct_s.tif" % int(month)
            infile_v = base_dir + month + r"\\AATSR_2009_%02d_lsct_v.tif" % int(month)
            data_s,ns, nl, nb, geog, proj = read_image_gdal(infile_s)
            data_v,ns, nl, nb, geog, proj = read_image_gdal(infile_s)
            save_s = save_s + data_s
            save_v = save_v + data_v
            num_s[data_s!=0] = num_s[data_s!=0] + 1
            num_v[data_v!=0] = num_v[data_v!=0] + 1
        outfile_s = base_dir + season + "_s.tif"
        outfile_v = base_dir + season + "_v.tif"
        write_image_gdal(save_s/num_s, ns_type, nl_type, nb_type, geog_type, proj_type,outfile_s)
        write_image_gdal(save_v /num_v, ns_type, nl_type, nb_type, geog_type, proj_type, outfile_v)

if ifplot:
    seasons = ["Q1th", "Q2nd", "Q3rd", "Q4th"]
    types = ["s", "v"]

    plt.rc('font', family='Times New Roman', size=40)
    fig, axs = plt.subplots(4, 2, figsize=(40, 40))

    for i, season in enumerate(seasons):
        for j, t in enumerate(types):
            infile = base_dir + f"{season}_{t}.tif"

            data, ns, nl, nb, geog, proj = read_image_gdal(infile)
            data = data / 100
            data[data < 230] = 0
            data[data > 370] = 0

            # 将 0 值替换为 NaN
            data[data == 0] = np.nan

            # 创建自定义的 colormap
            cmap = plt.get_cmap('jet')
            cmap.set_bad(color='white')

            ax = axs[i, j]
            ax.axhline(y=0, color='gray',linestyle=(0, (5, 10)), linewidth=2)  # 赤道
            ax.axhline(y=23.5, color='lightgray', linestyle=(0, (5, 10)), linewidth=2)  # 北回归线
            ax.axhline(y=-23.5, color='lightgray',  linestyle=(0, (5, 10)), linewidth=2)  # 南回归线
            ax.axhline(y=66.5, color='lightgray',  linestyle=(0, (5, 10)), linewidth=2)  # 北极圈
            ax.axhline(y=-66.5, color='lightgray',  linestyle=(0, (5, 10)), linewidth=2)  # 南极圈

            img = ax.imshow(data, cmap=cmap, vmin=250, vmax=330, extent=[-180, 180, -90, 90])
            ax.set_title(f"{season} - {'Soil' if t == 's' else 'Vegetation'}")
            fig.colorbar(img, ax=ax, orientation='vertical')

            # 设置X轴标注
            ax.set_xticks([-180, -120, -60, 0, 60, 120, 180])
            ax.set_yticks([-66.5,-23.5,0,23.5,66.5])


    plt.tight_layout()
    plt.show()