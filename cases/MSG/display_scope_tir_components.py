
import matplotlib.pyplot as plt
import numpy as np
import h5py
import seaborn as sns
import seaborn_image as isns
from pvlib import atmosphere
from pvlib.location import Location
from osgeo import gdal, osr
import os
import pyresample as pr
from satpy import Scene

# 导入自定义模块
from base.util_kernel import fitting_DTC
from base.util_lst import *
from base.util_data import *
from base.util_fitting import *
from base.util_kernel import *
from base.util_file import *

# ==================== 参数设置 ====================

# 当前参数值
klai = 2.0
ksm = 0.35


# ==================== 路径设置 ====================
indir0 = r"/Users/bianzj/Downloads/data/msg/output/"
indir = os.path.join(indir0, f"F_2025_LAI{klai:.1f}_SMC{ksm:.2f}/Directional/")

# 检查目录是否存在
if not os.path.exists(indir):
    print(f"错误: 目录不存在 - {indir}")
    exit()

# ==================== 读取温度数据 ====================
infile_temp = os.path.join(indir0, f"F_2025_LAI{klai:.1f}_SMC{ksm:.2f}/surftemp.dat")

try:
    temps = read_txt_array(infile_temp, 0, 11)
    print(f"成功读取温度数据，形状: {temps.shape}")
except Exception as e:
    print(f"读取温度数据失败: {e}")
    temps = np.array([])

# ==================== 处理文件数据 ====================
doy1 = 156
doy2 = 157

# 搜索温度文件
infiles = search_file(indir, ["Temperature"])
print(f"找到 {len(infiles)} 个温度文件")

result_list = []  # 使用列表代替数组，更灵活

for infile in infiles:
    try:
        # 解析文件名中的时间
        filename_parts = str(infile).split("_")
        if len(filename_parts) < 2:
            print(f"跳过无法解析的文件名: {infile}")
            continue

        time_part = filename_parts[1].split(".")[0]
        if len(filename_parts[1].split(".")) > 1:
            time_decimal = filename_parts[1].split(".")[1]
            ktime = float(time_part) + float(time_decimal) / 100.0
        else:
            ktime = float(time_part)

        # 检查时间范围
        if (ktime > doy2) or (ktime < doy1):
            continue

        # 读取数据
        filepath = os.path.join(indir, infile)
        data = read_txt_array(filepath, 0, 2)

        if data.size > 0:
            dt1 = data[0][0]
            dt2 = data[0][1]
            result_list.append([ktime, dt1, dt2])

    except Exception as e:
        print(f"处理文件 {infile} 时出错: {e}")
        continue

# 转换为numpy数组
if result_list:
    result_ = np.array(result_list)
    print(f"处理完成，结果数组形状: {result_.shape}")
else:
    result_ = np.array([])
    print("没有找到符合条件的数据")

# ==================== 数据可视化 ====================
if result_.size > 0:
    # 筛选数据
    ind = (result_[:, 0] > doy1) & (result_[:, 0] < doy2)

    if np.any(ind):
        # 创建图形
        plt.figure(figsize=(12, 8))

        # 子图1: 原始数据
        plt.subplot(2, 2, 1)
        plt.plot(result_[ind, 0], result_[ind, 1], "ko", markersize=6, label="euro")
        plt.plot(result_[ind, 0], result_[ind, 2], "ro", markersize=6, label="iodc")
        plt.xlabel("DOY")
        plt.ylabel("Temperature")
        plt.title(f"Temperature Data (kLAI={klai:.1f}, kSMC={ksm:.2f})")
        plt.legend()
        plt.grid(True, alpha=0.3)

        # 子图2: 差值
        plt.subplot(2, 2, 2)
        diff = result_[ind, 1] - result_[ind, 2]
        plt.plot(result_[ind, 0], diff, "bo-", linewidth=2, markersize=6)
        plt.xlabel("DOY")
        plt.ylabel("Difference (euro - iodc)")
        plt.title("Temperature Difference")
        plt.grid(True, alpha=0.3)

        # 子图3: 散点图
        plt.subplot(2, 2, 3)
        plt.scatter(result_[ind, 1], result_[ind, 2], c=result_[ind, 0], cmap="viridis", s=50)
        plt.xlabel("euro Temperature")
        plt.ylabel("iodc Temperature")
        plt.title("Scatter Plot")
        plt.colorbar(label="DOY")

        # 添加1:1线
        min_val = min(result_[ind, 1].min(), result_[ind, 2].min())
        max_val = max(result_[ind, 1].max(), result_[ind, 2].max())
        plt.plot([min_val, max_val], [min_val, max_val], "r--", alpha=0.5, label="1:1 line")
        plt.legend()

        # 子图4: 统计信息
        plt.subplot(2, 2, 4)
        if temps.size > 0:
            indd = (temps[:, 2] > doy1) & (temps[:, 2] < doy2)
            if np.any(indd):
                colors = ["yo", "co", "mo", "go", "bo"]
                labels = ["Ta", "Tsh", "Tss", "Tvs", "Tvh"]

                for i in range(5):
                    if i + 3 < temps.shape[1]:  # 确保列索引有效
                        plt.plot(temps[indd, 2], temps[indd, i+ 3], colors[i], markersize=4, label=labels[i])

                plt.xlabel("DOY")
                plt.ylabel("Surface Temperature")
                plt.title("Additional Temperature Data")
                plt.legend(loc="best", fontsize=8)
                plt.grid(True, alpha=0.3)
            else:
                plt.text(0.5, 0.5, "No temperature data\nin specified DOY range",
                         ha="center", va="center", transform=plt.gca().transAxes)
        else:
            plt.text(0.5, 0.5, "No temperature data available",
                     ha="center", va="center", transform=plt.gca().transAxes)

        plt.tight_layout()
        plt.show()

        # 打印统计信息
        print("\n=== 统计信息 ===")
        print(f"数据点数: {np.sum(ind)}")
        print(f"euro温度范围: {result_[ind, 1].min():.2f} - {result_[ind, 1].max():.2f}")
        print(f"iodc温度范围: {result_[ind, 2].min():.2f} - {result_[ind, 2].max():.2f}")
        print(f"平均差值: {diff.mean():.2f} ± {diff.std():.2f}")

    else:
        print(f"在DOY范围 {doy1}-{doy2} 内没有数据")
else:
    print("没有可用的结果数据")

# ==================== 可选: 保存结果 ====================
if result_.size > 0:
    # 保存处理后的数据
    output_file = os.path.join(indir0, f"processed_results_LAI{klai:.1f}_SMC{ksm:.2f}.npy")
    np.save(output_file, result_)
    print(f"结果已保存到: {output_file}")

    # 保存为文本文件
    txt_file = os.path.join(indir0, f"processed_results_LAI{klai:.1f}_SMC{ksm:.2f}.txt")
    header = "DOY\teuro_temp\tiodc_temp"
    np.savetxt(txt_file, result_, delimiter="\t", header=header, fmt="%.6f")
    print(f"文本结果已保存到: {txt_file}")









