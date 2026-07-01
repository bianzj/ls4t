import numpy as np
import matplotlib.pyplot as plt

# 定义一个二维数组 a
a = np.array([[10, 20, 30],
              [40, 50, 60],
              [70, 80, 90],
              [100, 110, 120],
              [130, 140, 150]])

# 对应的索引 indx 和 indy，形状与 a 一致
indx = np.array([[2, 2, 2],
                 [4, 4, 4],
                 [6, 6, 6],
                 [8, 8, 8],
                 [10, 10, 10]])

indy = np.array([[3, 4, 5],
                 [3, 4, 5],
                 [7, 8, 9],
                 [7, 8, 9],
                 [11, 11, 11]])

# 定义参考范围
ref_indx_min = 3
ref_indx_max = 5
ref_indy_min = 0
ref_indy_max = 11

# 生成目标图像的大小
img_height = ref_indx_max - ref_indx_min + 1
img_width = ref_indy_max - ref_indy_min + 1

# 初始化图像矩阵和计数矩阵
image = np.zeros((img_height, img_width))
count = np.zeros((img_height, img_width))  # 用来记录每个像素的累加次数

# 将二维数组 a 的值填充到对应的图像位置，并计算平均值
for i in range(a.shape[0]):  # 遍历行
    for j in range(a.shape[1]):  # 遍历列
        x = indx[i, j] - ref_indx_min  # 将真实 x 位置映射到图像坐标
        y = indy[i, j] - ref_indy_min  # 将真实 y 位置映射到图像坐标

        # 检查映射后的索引是否在图像范围内
        if 0 <= x < img_height and 0 <= y < img_width:
            image[x, y] += a[i, j]  # 累加值
            count[x, y] += 1  # 计数+1

# 计算每个位置的平均值，避免除以0的情况
with np.errstate(divide='ignore', invalid='ignore'):
    image = np.where(count > 0, image / count, 0)

# 输出生成的图像矩阵
print("生成的图像矩阵：")
print(image)

# 可视化图像
plt.imshow(image, cmap='gray', origin='lower')
plt.colorbar()
plt.title("Generated Image from 2D Array with Averaging")
plt.show()
