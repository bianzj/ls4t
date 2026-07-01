import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from scipy import stats
from base.util_lst import *
from base.util_phys import *
import math
import os

# ================= 配置参数 =================
file_fitting = "/Users/bianzj/Downloads/data/msg/PRODUCTS/SITE/ALL_SITES_LST_FITTING_RESULTS.csv"
file_measured = "/Users/bianzj/Downloads/data/stations/Evo-2017.csv"
output_stats = "Validation_Stats_Nadir_vs_Obs.csv"

target_site = "Evora"
START_DATE = '2017-08-01'
END_DATE = '2017-12-31'
SELECT_HOURS = [h for h in range(9, 16)]
DIFF_THRESHOLD = 10.0  # 剔除异常值的阈值
Tsky = 250
emis_v = 0.985
emis_s = 0.975

# 定义验证任务：(反演列名, 标题)
# 我们要验证：两个卫星的原始观测、以及三种模型的天底(Nadir)预测
tasks = [
    ('LST_obs_E', 'Original LST (Sensor E)'),
    ('LST_obs_I', 'Original LST (Sensor I)'),
    ('LST_nadir_DTC', 'Nadir DTC'),
    ('LST_nadir_DTCRL', 'Nadir DTCRL'),
    ('LST_nadir_DTCLSFRL', 'Nadir DTCLSFRL')
]

# ================= 1. 加载并预处理拟合数据 =================
df_all = pd.read_csv(file_fitting)
df_inf = df_all[df_all['site'] == target_site].copy()

# 将 date + local_time 转换为 DateTime 对象以便匹配
# 假设 local_time 是 0-24 之间的浮点数
df_inf['DateTime'] = pd.to_datetime(df_inf['date']) + pd.to_timedelta(df_inf['local_time'], unit='h')
# 向上/下取整到最近的15分钟或1小时，确保能跟实测数据对上（这里先取整到分钟）
df_inf['DateTime'] = df_inf['DateTime'].dt.round('1min')

# ================= 2. 加载并预处理实测数据 =================
df_mea = pd.read_csv(file_measured)
df_mea['DateTime'] = pd.to_datetime(df_mea['Time'], dayfirst=True).dt.round('1min')

# 单位转换 (C -> K)
for col in ['Ts', 'Tcrown','Tgrass']:
    if df_mea[col].mean() < 150:
        df_mea[col] += 273.15

# ================= 3. 数据合并与参考 LST 计算 =================
df_merge = pd.merge(df_inf, df_mea, on='DateTime')

# 根据 LAI 计算植被覆盖度 fc，合成参考 LST (LST_Ref)
# 如果不想用 fc，可以直接 (Ts + Tcrown)/2，但用 fc 更科学
df_merge['fc'] = 1 - np.exp(-0.5 * df_merge['LAI'])

bg = planck(10.5,df_merge['Ts'])
bv = planck(10.5,df_merge['Tcrown'])
bsky = planck(10.5,250)
df_merge['Ts'] = inv_planck(10.5,(bg-(1-emis_s)*bsky)/emis_s)
df_merge['Tcrown'] = inv_planck(10.5,(bv-(1-emis_v)*bsky)/emis_v)



df_merge['LST_Ref'] = df_merge['fc'] * df_merge['Tcrown'] + (1 - df_merge['fc']) * df_merge['Tgrass']
# df_merge['LST_Ref'] = df_merge['Ts']


# 时间过滤
df_merge = df_merge[(df_merge['DateTime'] >= START_DATE) & (df_merge['DateTime'] <= END_DATE)]
df_merge = df_merge[df_merge['DateTime'].dt.hour.isin(SELECT_HOURS)]

if df_merge.empty:
    print("没有匹配到有效数据，请检查日期范围或 DateTime 格式。")
    exit()

# ================= 4. 分列提取卫星 E 和 I 的原始数据 =================
# 因为 nadir 结果对 E 和 I 是一样的，我们要分别看原始观测
df_e = df_merge[df_merge['sensor'] == 'E'].rename(columns={'LST_obs': 'LST_obs_E'})
df_i = df_merge[df_merge['sensor'] == 'I'].rename(columns={'LST_obs': 'LST_obs_I'})

# 为了绘图方便，我们将 E 和 I 合并到一个宽表里（按时间对齐）
df_plot = pd.merge(df_e[['DateTime', 'LST_Ref', 'LST_obs_E', 'LST_nadir_DTC', 'LST_nadir_DTCRL', 'LST_nadir_DTCLSFRL']],
                   df_i[['DateTime', 'LST_obs_I']], on='DateTime', how='inner')

# ================= 5. 统计与绘图 =================
stats_list = []
plt.figure(figsize=(15, 10))
plt.suptitle(f"Validation at {target_site} ({START_DATE} to {END_DATE})\nReference: fc*Tcrown + (1-fc)*Ts", fontsize=16)

for i, (col_name, title) in enumerate(tasks):
    y_true = df_plot['LST_Ref']
    y_pred = df_plot[col_name]

    # 剔除无效值和极端差异值
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    diff = np.abs(y_true - y_pred)
    valid_mask = mask & (diff <= DIFF_THRESHOLD)

    y_t = y_true[valid_mask]
    y_p = y_pred[valid_mask]

    if len(y_t) < 5: continue

    # 计算指标
    bias = np.mean(y_p - y_t)
    rmse = np.sqrt(mean_squared_error(y_t, y_p))
    r_val, _ = stats.pearsonr(y_t, y_p)

    stats_list.append({
        'Task': title, 'RMSE': rmse, 'Bias': bias, 'R': r_val, 'N': len(y_t)
    })

    # 绘图
    ax = plt.subplot(2, 3, i + 1)
    ax.scatter(y_t, y_p, alpha=0.6, edgecolors='w')

    # 1:1 线
    mn, mx = min(y_t.min(), y_p.min()) - 2, max(y_t.max(), y_p.max()) + 2
    ax.plot([mn, mx], [mn, mx], 'r--')

    ax.set_title(title)
    ax.set_xlabel('Measured LST (K)')
    ax.set_ylabel('Inferred/Nadir LST (K)')

    text = f"N: {len(y_t)}\nRMSE: {rmse:.2f}K\nBias: {bias:.2f}K\nR: {r_val:.2f}"
    ax.text(0.05, 0.75, text, transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.7))

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
pd.DataFrame(stats_list).to_csv(output_stats, index=False)
plt.show()

# 打印表格
print("\n" + "=" * 50)
print(f"验证结果汇总 ({target_site})")
print("-" * 50)
print(pd.DataFrame(stats_list).to_string(index=False))
print("=" * 50)