import pandas as pd
import matplotlib.pyplot as plt

'''画Dahra站点观测'''
infile = r"D:\data\AATSR_product\Dahra_2009\\Dahra_LST_Apogee_forMatchup_extend.xlsx"
# 读取 Excel 文件，跳过第1、3、4行，第2行为索引，第一列为时间
df = pd.read_excel(infile, skiprows=[0, 2, 3], index_col=0, parse_dates=True, date_parser=lambda x: pd.to_datetime(x, format='%Y/%m/%d %H:%M:%S'))

# 选择时间范围为 11.2 （8点）- 11.14（1点）
start_time = '2009-11-02 08:00:00'
end_time = '2009-11-10 08:00:00'
df_selected = df.loc[start_time:end_time, ['Apogee grass', 'apogee  crown', 'apogee shade']]

# 绘制图表
plt.rc('font', family='Times New Roman', size=12)
plt.figure(figsize=(8, 4))
plt.plot(df_selected.index, df_selected['Apogee grass'], label='Sunlit background')
plt.plot(df_selected.index, df_selected['apogee shade'], label='Shaded background')
plt.plot(df_selected.index, df_selected['apogee  crown'], label='Crown')

plt.xlabel('Time')
plt.ylabel('Temperature')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()