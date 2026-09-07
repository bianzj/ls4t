import pandas as pd
import matplotlib.pyplot as plt

'''画Dahra站点的实测数据'''


# 指定Excel文件的路径
file_path = 'D:\data\LSCT_Validation\Dahra_2009\Dahra_LST.xlsx'

# 读取Excel文件中的数据
df = pd.read_excel(file_path)

# 过滤掉空值的行
df = df.dropna()

# 将时间列转换为日期时间对象
df['Time'] = pd.to_datetime(df['Time'])

# 设置起始日期和结束日期
start_date = '2009-11-01'
end_date = '2009-11-07'


# 根据日期和时间范围过滤数据
filtered_data = df[(df['Time'] >= start_date ) & (df['Time'] <= end_date)]

# 设置全局字体为Times New Roman
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = 'Times New Roman'

plt.figure(figsize=(8, 4))
# 设置颜色
colors = {'Tg': 'red', 'Tc': 'green'}

# 绘制每个组件的温度随时间变化的图像
for component, color in colors.items():
    plt.plot(filtered_data['Time'], filtered_data[component], label=component, color=color)

# 添加标签
plt.xlabel('Time')
plt.ylabel('Component Temperature / °C')

# 添加图例
plt.legend()

# 旋转x轴标签以避免重叠
# x_label = ['00:00','06:00','12:00','18:00','00:00','06:00','12:00','18:00','00:00','06:00','12:00','18:00','00:00','06:00','12:00','18:00','00:00','06:00','12:00','18:00','00:00']
# ticks= [0,360/24,720/24,1080/24,1440/24,1800/24,2160/24,2520/24,2880/24,3240/24,3600/24,3960/24,4320/24,4680/24,5040/24,5400/24,5760/24,6120/24,6480/24,6840/24,7200/24]
# plt.xticks(ticks=ticks,labels=x_label,rotation=30,fontsize=12)
# plt.vlines([1440/24, 2880/24,4320/24,5760/24], 0, 500, linestyles='dashed', colors='black')

# # 设置x轴刻度间隔为1小时
# plt.gca().xaxis.set_major_locator(plt.MultipleLocator(1))

# # 设置x轴标签位置为刻度的右侧
# plt.tick_params(axis='x', labelright=True)

# 显示图形
plt.show()
