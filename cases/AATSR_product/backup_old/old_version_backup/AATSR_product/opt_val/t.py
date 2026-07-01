import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool, freeze_support

# 生成示例数据，替换为你的实际数据
data_set1 = np.random.rand(10, 1800, 3600)
data_set2 = np.random.rand(10, 1800, 3600)

# 将数据集展平以便于向量化操作
flat_data_set1 = data_set1.reshape((10, -1))
flat_data_set2 = data_set2.reshape((10, -1))

# 初始化相关系数数组
correlation_coefficients = np.zeros((flat_data_set1.shape[1],))

# 定义函数以计算相关系数
def calculate_correlation(i):
    pixel_set1 = flat_data_set1[:, i]
    pixel_set2 = flat_data_set2[:, i]

    if np.any(np.isnan(pixel_set1)) or np.any(np.isnan(pixel_set2)):
        return np.nan
    else:
        return np.corrcoef(pixel_set1, pixel_set2)[0, 1]

if __name__ == '__main__':
    # 在 Windows 上使用 multiprocessing 时需要加上 freeze_support()
    freeze_support()

    # 使用多进程计算相关系数
    with Pool() as pool:
        correlation_coefficients = pool.map(calculate_correlation, range(flat_data_set1.shape[1]))

    # 将相关系数重塑回图像大小
    correlation_coefficients = np.array(correlation_coefficients).reshape((1800, 3600))

    # 绘制相关系数图
    plt.imshow(correlation_coefficients, cmap='viridis')
    plt.colorbar()
    plt.title('Correlation Coefficient Map')
    plt.show()
