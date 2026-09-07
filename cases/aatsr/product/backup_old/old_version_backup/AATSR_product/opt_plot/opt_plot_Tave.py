from utils.old.util import *
import warnings
warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
matplotlib.use('agg')
from matplotlib.colors import LinearSegmentedColormap
import gc

'''画平均温度动图'''
ifsave_jpg = 1
ifsave_gif = 1

file_path = r'H:\AATSR\lsct/'
out_path = r"H:\AATSR\graph\Tave\jpg4//"
gif_path = r"H:\AATSR\graph\Tave\\T_ave.gif"


if ifsave_jpg:
    mkdir_if_not_exist(out_path)
    plt.rc('font', family='Times New Roman')
    for year in range(2002, 2013):
        for month in range(1, 13):
            path0 = file_path + '%04d'%year+ '/lsct_month/' + '%02d'%month +'/'
            print(path0)
            if not os.path.exists(path0):
                continue
            if os.path.exists(out_path + str(year) + '-' + '%02d'%month + '.jpg'):
                continue
            file_name = search_file(path0, ['lst_n'])
            file_name = file_name[0]
            file = path0 + file_name
            print(file)
            if not os.path.exists(file):
                continue
            data, im_width, im_height, im_bands, im_geotrans, im_proj = read_image_gdal(file)
            data = data / 100

            # 创建图形和坐标轴
            fig, ax = plt.subplots(figsize=(20, 9))

            # 创建掩码，将数据中的0掩盖起来
            masked_data = np.ma.masked_where(data == 0, data)

            # 使用imshow在图中创建2D图的3D表示，颜色深浅表示数值大小
            # colors = [(0.984, 0.235, 0.235), (0.020, 0.066, 0.505)]    # 从#2F7AFF到#D90429

            # 创建自定义颜色映射
            # custom_cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=256)
            # cmap = plt.cm.BrBG.reversed()
            # cmap = plt.cm.coolwarm

            # colors = [
            #     (0.02, 0.07, 0.505, 1),  # 深蓝色
            #     (0.18, 0.498, 1, 1),  # 浅蓝色
            #
            #     (1, 0.8, 0.8, 1),  # 更浅的红色
            #
            #     (0.98, 0.24, 0.24, 1),  # 深红色
            #     (1, 0, 0, 1),  # 深红色
            #     (0.8, 0.2, 0.2, 1)
            # ]

            colors = [
                (0.02,0.07,0.505,1),  # 深蓝色(0.18，0.498，1，1)， # 浅蓝色
                (0.18,0.498,1,1),  # 绿色(1，1，0，1),
                (0,1,0,0.4),
                (1,1,0,1),
                (0.98,0.24,0.24,1),
                (0.98, 0.24, 0.24, 1),
                (1,0,0,1)
            ]  # 黄色

            # 创建颜色映射
            cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=256)

            # cmap =sns.color_palette("RdYlBu_r",as_cmap=True)
            norm = mcolors.Normalize(vmin=masked_data.min(), vmax=masked_data.max())
            im = ax.imshow(masked_data, cmap=cmap, norm=norm, interpolation='nearest', aspect='auto')
            # 设置图形的背景颜色
            # fig.patch.set_facecolor('#333333')

            # 设置坐标轴的背景颜色
            # ax.set_facecolor('#404040')

            # 添加颜色条（colorbar）
            cbar = ax.figure.colorbar(im, ax=ax)
            cbar.ax.tick_params(labelsize=20)
            # cbar.set_label(fontsize=20)
            # 设置自定义纵坐标刻度和标签
            ax.set_yticks([0, 1125, 2250, 3375, 4500, 5625, 6750, 7875, 8999])  # 选择要显示标签的位置
            ax.set_yticklabels(['90°', '66.5°', '45°', '23.5°', '0°', '-23.5°', '-45°', '-66.5°', '-90°'], fontsize=20)

            # 设置x轴刻度和标签
            ax.set_xticks([0, 2250, 4500, 6750, 9000, 11250, 13500, 15750, 17999])  # 选择要显示标签的位置
            ax.set_xticklabels(['-180°', '-135°', '-90°', '-45°', '0°', '45°', '90°', '-135°', '180°'], fontsize=20)

            ax.set_title('%d-'%year + '%02d'%month, fontsize=25)
            plt.savefig(out_path + str(year) + '-' + '%02d'%month + '.jpg')
            fig.clf()
            plt.close('all')
            del data
            gc.collect()

if ifsave_gif:
    from PIL import Image

    # 读取文件夹中的所有图片
    images = [Image.open(os.path.join(out_path, img)) for img in sorted(os.listdir(out_path))]
    # 保存为 GIF，每0.5秒切
    # 换一张照片
    images[0].save(gif_path, save_all=True, append_images=images[1:], optimize=False, duration=500, loop=0, quality=10)