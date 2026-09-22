import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from sklearn.metrics import mean_squared_error, r2_score
from scipy import stats
import math
from base.util_phys import *

# ================= 全局绘图风格设置 (Publication Ready) =================
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
mpl.rcParams['font.size'] = 12
mpl.rcParams['axes.titlesize'] = 13
mpl.rcParams['axes.labelsize'] = 12
mpl.rcParams['xtick.labelsize'] = 11
mpl.rcParams['ytick.labelsize'] = 11
mpl.rcParams['legend.fontsize'] = 11
mpl.rcParams['axes.linewidth'] = 1.2
mpl.rcParams['lines.linewidth'] = 1.5

# ================= 配置参数 =================
file_inferred = "/Users/bianzj/Downloads/data/msg/PRODUCTS/LSCT_Site_Results.csv"
file_measured = "/Users/bianzj/Downloads/data/msg/field/Kal-2017.csv"
# 新增图片输出路径
output_fig = "/Users/bianzj/Downloads/data/msg/PRODUCTS/LSCT_Diurnal_Validation_KAL.png"

# --- 时间选择设定 ---
START_DATE = '2017-07-01'
END_DATE = '2017-09-30'

# 【新增】：设定只提取特定的小时 (如 11点 到 15点)
# 如果想看全天，可以写成 [] 或 np.arange(0, 24).tolist()
SELECT_HOURS = [9, 10, 11, 12, 13, 14, 15]

# 设定残差阈值（单位：K）
DIFF_THRESHOLD = 15.0
target_site = "KAL"
Tsky = 250
emis_v = 0.975
emis_s = 0.975

# 格式：(反演列名, 实测列名, 显示标题)
tasks = [
    ('T_Sunlit_Soil', 'bt_s', '(a) Sunlit Soil vs bt_s'),
    ('T_Vegetation', 'bt_v', '(b) Vegetation vs bt_v'),
]

# ================= 1. 处理反演数据 (Inferred) =================
df_inf = pd.read_csv(file_inferred)
df_inf = df_inf[df_inf['Site'] == target_site].copy()


def parse_inf_time(val):
    s = "{:.0f}".format(float(val))
    return pd.to_datetime(s, format='%Y%m%d%H%M')


df_inf['DateTime'] = df_inf['DateTime'].apply(parse_inf_time)

# ================= 2. 处理实测数据 (Measured) =================
df_mea = pd.read_csv(file_measured)
df_mea['DateTime'] = pd.to_datetime(df_mea['time'], dayfirst=True)

# -------------------------------------------------------------
# 将实测时间规整到最近的 10 分钟级别，并求平均去重
# -------------------------------------------------------------
df_mea['DateTime'] = df_mea['DateTime'].dt.round('10min')
df_mea = df_mea.groupby('DateTime', as_index=False).mean(numeric_only=True)

measured_cols = list(set([t[1] for t in tasks]))
for col in measured_cols:
    if col in df_mea.columns:
        if df_mea[col].mean() < 150:
            df_mea[col] = df_mea[col] + 273.15

# ================= 3. 数据匹配与时间过滤 =================
df_merge = pd.merge(df_inf, df_mea, on='DateTime', suffixes=('_inf', '_mea'))

# 1. 过滤日期范围
df_merge = df_merge[(df_merge['DateTime'] >= START_DATE) & (df_merge['DateTime'] <= END_DATE)]

# 2. 【核心新增】：过滤特定小时
if SELECT_HOURS is not None and len(SELECT_HOURS) > 0:
    df_merge = df_merge[df_merge['DateTime'].dt.hour.isin(SELECT_HOURS)]

if df_merge.empty:
    print(f"未能匹配到数据！请检查日期范围 {START_DATE}~{END_DATE} 或小时设定 {SELECT_HOURS}")
    exit()

print(f"经过 10 分钟规整及小时过滤后，剩余有效样本数: {len(df_merge)}")

# ================= 4. 辐射校正 =================
bg = planck(10.5, df_merge['bt_s'])
bv = planck(10.5, df_merge['bt_v'])
bsky = planck(10.5, 250)
df_merge['bt_s'] = inv_planck(10.5, (bg - (1 - emis_s) * bsky) / emis_s)
df_merge['bt_v'] = inv_planck(10.5, (bv - (1 - emis_v) * bsky) / emis_v)

# ================= 5. 计算日变化（按小时平均） =================
df_merge['Hour'] = df_merge['DateTime'].dt.hour
hourly_stats = {}

for inf_col, mea_col, title_name in tasks:
    mask = (df_merge[inf_col].notna()) & (df_merge[mea_col].notna())
    abs_diff = np.abs(df_merge[inf_col] - df_merge[mea_col])
    valid_mask = mask & (abs_diff <= DIFF_THRESHOLD)

    df_temp = df_merge[valid_mask].copy()

    if len(df_temp) == 0:
        continue

    hourly_mean_inf = df_temp.groupby('Hour')[inf_col].agg(['mean', 'std', 'count'])
    hourly_mean_mea = df_temp.groupby('Hour')[mea_col].agg(['mean', 'std', 'count'])

    hourly_mean = pd.DataFrame({
        'Hour': hourly_mean_inf.index,
        f'{inf_col}_mean': hourly_mean_inf['mean'],
        f'{inf_col}_std': hourly_mean_inf['std'],
        f'{mea_col}_mean': hourly_mean_mea['mean'],
        f'{mea_col}_std': hourly_mean_mea['std'],
        'count': hourly_mean_inf['count']
    })

    # 抛弃掉原来由 groupby 生成的同名索引 'Hour'，避免 sort_values 时产生歧义
    hourly_mean = hourly_mean.reset_index(drop=True)

    # 保护机制：按小时排序，并处理因数据量不足导致的 NaN 标准差
    hourly_mean = hourly_mean.sort_values('Hour').dropna(subset=[f'{inf_col}_mean', f'{mea_col}_mean'])
    hourly_mean[f'{inf_col}_std'] = hourly_mean[f'{inf_col}_std'].fillna(0)
    hourly_mean[f'{mea_col}_std'] = hourly_mean[f'{mea_col}_std'].fillna(0)

    hourly_stats[title_name] = hourly_mean

# ================= 6. 绘制学术级日变化图 =================
cols_plot = 2
rows_plot = math.ceil(len(tasks) / cols_plot)
fig, axes = plt.subplots(rows_plot, cols_plot, figsize=(14, 5.5 * rows_plot))

# 动态显示标题时间段
hours_str = f"{min(SELECT_HOURS)}:00-{max(SELECT_HOURS)}:00" if SELECT_HOURS else "Full Day"
fig.suptitle(f"Diurnal Variation at {target_site} ({START_DATE} to {END_DATE} | {hours_str})",
             fontsize=16, fontweight='bold', y=0.96)

if rows_plot == 1 and cols_plot == 1:
    axes = np.array([[axes]])
elif rows_plot == 1:
    axes = axes.reshape(1, -1)
elif cols_plot == 1:
    axes = axes.reshape(-1, 1)

color_mea = '#1f77b4'  # 深蓝 (实测)
color_inf = '#d62728'  # 砖红 (反演)

for idx, (inf_col, mea_col, title_name) in enumerate(tasks):
    row = idx // cols_plot
    col = idx % cols_plot
    ax = axes[row, col]

    if title_name not in hourly_stats or hourly_stats[title_name].empty:
        ax.text(0.5, 0.5, 'No Valid Data', ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_title(f'{title_name}', fontweight='bold')
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        continue

    df_hourly = hourly_stats[title_name]

    # 因为选定区间通常较短，适当减小位移，防止点离得太开
    offset = 0.1

    ax.errorbar(df_hourly['Hour'] - offset, df_hourly[f'{mea_col}_mean'],
                yerr=df_hourly[f'{mea_col}_std'],
                fmt='o-', color=color_mea,
                markerfacecolor='white', markeredgecolor=color_mea, markeredgewidth=1.5,
                capsize=4, capthick=1.5, elinewidth=1.5,
                label='Measured (In-situ)', markersize=7, zorder=3)

    ax.errorbar(df_hourly['Hour'] + offset, df_hourly[f'{inf_col}_mean'],
                yerr=df_hourly[f'{inf_col}_std'],
                fmt='s-', color=color_inf,
                markerfacecolor='white', markeredgecolor=color_inf, markeredgewidth=1.5,
                capsize=4, capthick=1.5, elinewidth=1.5,
                label='Inverted (Satellite)', markersize=6, zorder=3)

    # 【核心新增】：X 轴自适应逻辑
    if SELECT_HOURS:
        ax.set_xticks(SELECT_HOURS)  # 仅在指定小时画刻度
        ax.set_xlim(min(SELECT_HOURS) - 1, max(SELECT_HOURS) + 1)
    else:
        ax.set_xticks(np.arange(0, 24, 2))
        ax.set_xlim(-1, 24)

    ax.set_ylim(290, 340)

    ax.tick_params(axis='both', direction='in', length=5, width=1.2, top=False, right=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, axis='y', linestyle='--', alpha=0.6, zorder=0)

    ax.set_title(f'{title_name}', pad=12, fontweight='bold')
    ax.set_xlabel('Local Time (Hour)', fontweight='bold')
    ax.set_ylabel('Temperature (K)', fontweight='bold')
    ax.legend(loc='upper left', frameon=False)

for idx in range(len(tasks), rows_plot * cols_plot):
    row = idx // cols_plot
    col = idx % cols_plot
    axes[row, col].set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(output_fig, dpi=400, bbox_inches='tight', transparent=False)
print(f"处理完成。图片保存至: {output_fig}")
plt.show()