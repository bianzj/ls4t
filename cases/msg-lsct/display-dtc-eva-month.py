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
mpl.rcParams['axes.titlesize'] = 14
mpl.rcParams['axes.labelsize'] = 13
mpl.rcParams['xtick.labelsize'] = 11
mpl.rcParams['ytick.labelsize'] = 11
mpl.rcParams['legend.fontsize'] = 11
mpl.rcParams['axes.linewidth'] = 1.2
mpl.rcParams['lines.linewidth'] = 1.5

# ================= 配置参数 =================
file_inferred = "/Users/bianzj/Downloads/data/msg/PRODUCTS/LSCT_Site_Results.csv"
file_measured = "/Users/bianzj/Downloads/data/msg/field/Evo-2017.csv"
output_stats = "/Users/bianzj/Downloads/data/msg/PRODUCTS/LSCT_Validation_Stats_Evora.csv"
output_fig = "/Users/bianzj/Downloads/data/msg/PRODUCTS/LSCT_Diurnal_Validation_Evora.png"
output_rmse_fig = "/Users/bianzj/Downloads/data/msg/PRODUCTS/LSCT_RMSE_Bar_Evora.png"
output_scatter_fig = "/Users/bianzj/Downloads/data/msg/PRODUCTS/LSCT_Scatter_Evora.png"  # 新增散点图

# --- 时间选择设定 ---
START_DATE = '2017-07-01'
END_DATE = '2017-12-30'

# 设定只提取特定的小时
SELECT_HOURS = [9,10,11, 12, 13, 14, 15]

# 设定残差阈值（单位：K）
DIFF_THRESHOLD = 10.0
target_site = "Evora"
Tsky = 250
emis_v = 0.985
emis_s = 0.985

tasks = [
    ('T_Sunlit_Soil', 'Ts', '(a) Sunlit Soil Temperature'),
    ('T_Vegetation', 'Tcrown', '(b) Vegetation Canopy Temperature')
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
df_mea['DateTime'] = pd.to_datetime(df_mea['Time'], dayfirst=True)

measured_cols = list(set([t[1] for t in tasks]))
for col in measured_cols:
    if col in df_mea.columns:
        if df_mea[col].mean() < 150:
            df_mea[col] = df_mea[col] + 273.15

# ================= 3. 数据匹配与日期过滤 =================
df_merge = pd.merge(df_inf, df_mea, on='DateTime', suffixes=('_inf', '_mea'))
df_merge = df_merge[(df_merge['DateTime'] >= START_DATE) & (df_merge['DateTime'] <= END_DATE)]

# 过滤特定小时
if SELECT_HOURS is not None and len(SELECT_HOURS) > 0:
    df_merge = df_merge[df_merge['DateTime'].dt.hour.isin(SELECT_HOURS)]

if df_merge.empty:
    print(f"未能匹配到数据！请检查日期范围 {START_DATE} ~ {END_DATE} 或 小时设定 {SELECT_HOURS}")
    exit()

print(f"经过日期和指定小时过滤后，剩余有效样本数: {len(df_merge)}")

# ================= 4. 辐射校正 =================
bg = planck(10.5, df_merge['Ts'])
bv = planck(10.5, df_merge['Tcrown'])
bsky = planck(10.5, 250)
df_merge['Ts'] = inv_planck(10.5, (bg - (1 - emis_s) * bsky) / emis_s)
df_merge['Tcrown'] = inv_planck(10.5, (bv - (1 - emis_v) * bsky) / emis_v)

# ================= 5. 数据清洗与准备 =================
df_merge['Hour'] = df_merge['DateTime'].dt.hour
df_merge['Month'] = df_merge['DateTime'].dt.to_period('M')  # 提取月份（如 2017-07）

# ================= 6. 计算月均（先按月+小时分组） =================
print("\n" + "=" * 60)
print("步骤1: 计算每个月每个时刻的月均值")
print("=" * 60)

monthly_means = {}  # 存储月均数据，用于后续分析和绘图

for inf_col, mea_col, title_name in tasks:
    # 过滤无效数据和异常值
    mask = (df_merge[inf_col].notna()) & (df_merge[mea_col].notna())
    abs_diff = np.abs(df_merge[inf_col] - df_merge[mea_col])
    valid_mask = mask & (abs_diff <= DIFF_THRESHOLD)
    df_temp = df_merge[valid_mask].copy()

    if len(df_temp) == 0:
        print(f"警告: {title_name} 没有有效数据")
        continue

    # 【核心】：按月+小时分组，计算月均值
    monthly_grouped = df_temp.groupby(['Month', 'Hour']).agg({
        inf_col: ['mean', 'std', 'count'],
        mea_col: ['mean', 'std', 'count']
    }).reset_index()

    # 重命名列，使结构更清晰
    monthly_grouped.columns = ['Month', 'Hour',
                               f'{inf_col}_mean', f'{inf_col}_std', f'{inf_col}_count',
                               f'{mea_col}_mean', f'{mea_col}_std', f'{mea_col}_count']

    # 过滤样本数太少的月份-小时组合（可选，至少要有2个样本）
    monthly_grouped = monthly_grouped[monthly_grouped[f'{inf_col}_count'] >= 2]

    print(f"\n{title_name}:")
    print(f"  共得到 {len(monthly_grouped)} 个月-小时组合（月均数据点）")
    print(f"  月份范围: {monthly_grouped['Month'].min()} 至 {monthly_grouped['Month'].max()}")

    monthly_means[title_name] = monthly_grouped

# ================= 7. 基于月均值计算各小时的统计量 =================
print("\n" + "=" * 60)
print("步骤2: 基于月均值计算各小时的RMSE和统计量")
print("=" * 60)

hourly_stats = {}  # 存储基于月均的每小时统计
hourly_rmse = {}  # 存储基于月均的每小时RMSE

for inf_col, mea_col, title_name in tasks:
    if title_name not in monthly_means:
        continue

    df_monthly = monthly_means[title_name]

    # 基于月均值，按小时分组计算统计量
    hourly_grouped = df_monthly.groupby('Hour').agg({
        f'{inf_col}_mean': ['mean', 'std'],
        f'{mea_col}_mean': ['mean', 'std'],
        f'{inf_col}_count': 'sum'  # 总样本数
    }).reset_index()

    hourly_grouped.columns = ['Hour',
                              f'{inf_col}_mean', f'{inf_col}_std',
                              f'{mea_col}_mean', f'{mea_col}_std',
                              'count']

    # 填充NaN标准差为0
    hourly_grouped[f'{inf_col}_std'] = hourly_grouped[f'{inf_col}_std'].fillna(0)
    hourly_grouped[f'{mea_col}_std'] = hourly_grouped[f'{mea_col}_std'].fillna(0)

    hourly_stats[title_name] = hourly_grouped

    # 【核心】：基于月均值计算RMSE
    # RMSE = sqrt(mean((月均反演值 - 月均实测值)^2))
    rmse_by_hour = {}
    for hour in SELECT_HOURS:
        hour_monthly = df_monthly[df_monthly['Hour'] == hour]
        if len(hour_monthly) > 0:
            # 使用月均值计算RMSE
            rmse = np.sqrt(np.mean((hour_monthly[f'{inf_col}_mean'] -
                                    hour_monthly[f'{mea_col}_mean']) ** 2))
            rmse_by_hour[hour] = rmse
        else:
            rmse_by_hour[hour] = np.nan

    hourly_rmse[title_name] = rmse_by_hour

# ================= 8. 打印基于月均的各时刻RMSE =================
print("\n" + "=" * 60)
print("基于月均值的各时刻RMSE统计")
print("=" * 60)

for title_name in hourly_rmse.keys():
    print(f"\n{title_name}:")
    print("-" * 50)
    print(f"{'时刻':<10} {'RMSE (K)':<12} {'月数':<10}")
    print("-" * 50)

    if title_name in monthly_means:
        df_monthly = monthly_means[title_name]

    for hour in SELECT_HOURS:
        rmse_val = hourly_rmse[title_name].get(hour, np.nan)

        # 获取该小时的月数
        if title_name in monthly_means:
            n_months = len(df_monthly[df_monthly['Hour'] == hour])
        else:
            n_months = 0

        if not np.isnan(rmse_val):
            print(f"{hour}:00{'':<6} {rmse_val:<12.3f} {n_months:<10}")
        else:
            print(f"{hour}:00{'':<6} {'N/A':<12} {n_months:<10}")

# 打印基于月均的总体RMSE
print("\n" + "-" * 40)
print("基于月均值的总体统计:")
print("-" * 40)
for inf_col, mea_col, title_name in tasks:
    if title_name not in monthly_means:
        continue

    df_monthly = monthly_means[title_name]

    if len(df_monthly) > 0:
        overall_rmse = np.sqrt(np.mean((df_monthly[f'{inf_col}_mean'] -
                                        df_monthly[f'{mea_col}_mean']) ** 2))

        # 计算R²（基于月均值）
        r2 = r2_score(df_monthly[f'{mea_col}_mean'], df_monthly[f'{inf_col}_mean'])
        bias = np.mean(df_monthly[f'{inf_col}_mean'] - df_monthly[f'{mea_col}_mean'])

        print(f"{title_name}:")
        print(f"  RMSE (月均) = {overall_rmse:.3f} K")
        print(f"  R² (月均) = {r2:.4f}")
        print(f"  Bias (月均) = {bias:.3f} K")
        print(f"  月-小时组合数 = {len(df_monthly)}")

# ================= 9. 绘制散点图（月均值：实测 vs 反演） =================
print("\n正在生成散点图...")

cols_plot = 2
rows_plot = math.ceil(len(tasks) / cols_plot)
fig_scatter, axes_scatter = plt.subplots(rows_plot, cols_plot, figsize=(14, 6 * rows_plot))

hours_str = f"{min(SELECT_HOURS)}:00-{max(SELECT_HOURS)}:00" if SELECT_HOURS else "Full Day"
fig_scatter.suptitle(f"Monthly Mean Validation at {target_site}\n({START_DATE} to {END_DATE} | {hours_str})",
                     fontsize=16, fontweight='bold', y=0.98)

if rows_plot == 1 and cols_plot == 1:
    axes_scatter = np.array([[axes_scatter]])
elif rows_plot == 1:
    axes_scatter = axes_scatter.reshape(1, -1)
elif cols_plot == 1:
    axes_scatter = axes_scatter.reshape(-1, 1)

# 颜色映射（不同小时用不同颜色）
hour_colors = plt.cm.viridis(np.linspace(0, 1, len(SELECT_HOURS)))
hour_color_dict = {hour: hour_colors[i] for i, hour in enumerate(SELECT_HOURS)}

for idx, (inf_col, mea_col, title_name) in enumerate(tasks):
    row = idx // cols_plot
    col = idx % cols_plot
    ax = axes_scatter[row, col]

    if title_name not in monthly_means:
        ax.text(0.5, 0.5, 'No Valid Data', ha='center', va='center',
                transform=ax.transAxes, fontsize=12)
        ax.set_title(f'{title_name}', fontweight='bold')
        continue

    df_monthly = monthly_means[title_name]

    # 绘制1:1线
    all_vals = np.concatenate([df_monthly[f'{mea_col}_mean'].values,
                               df_monthly[f'{inf_col}_mean'].values])
    min_val = np.min(all_vals) - 2
    max_val = np.max(all_vals) + 2
    ax.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=0.8, alpha=0.5, label='1:1 Line')

    # 按小时绘制散点
    for hour in SELECT_HOURS:
        hour_data = df_monthly[df_monthly['Hour'] == hour]
        if len(hour_data) > 0:
            ax.scatter(hour_data[f'{mea_col}_mean'], hour_data[f'{inf_col}_mean'],
                       color=hour_color_dict[hour], s=80, alpha=0.7, edgecolors='black',
                       linewidth=0.5, label=f'{hour}:00', zorder=3)

    # 计算并显示统计量
    overall_rmse = np.sqrt(np.mean((df_monthly[f'{inf_col}_mean'] -
                                    df_monthly[f'{mea_col}_mean']) ** 2))
    r2 = r2_score(df_monthly[f'{mea_col}_mean'], df_monthly[f'{inf_col}_mean'])
    bias = np.mean(df_monthly[f'{inf_col}_mean'] - df_monthly[f'{mea_col}_mean'])

    # 添加统计文本框
    stats_text = f'RMSE = {overall_rmse:.2f} K\nR² = {r2:.3f}\nBias = {bias:.2f} K\nN = {len(df_monthly)}'
    props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8, edgecolor='gray')
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)

    # 样式设置
    ax.set_title(f'{title_name}', pad=15, fontweight='bold')
    ax.set_xlabel('Measured Temperature (K)', fontweight='bold')
    ax.set_ylabel('Inverted Temperature (K)', fontweight='bold')
    ax.set_xlim(min_val, max_val)
    ax.set_ylim(min_val, max_val)
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.tick_params(axis='both', direction='in', length=5, width=1.2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(loc='lower right', frameon=True, fontsize=9, ncol=2)

# 隐藏多余的子图
for idx in range(len(tasks), rows_plot * cols_plot):
    row = idx // cols_plot
    col = idx % cols_plot
    axes_scatter[row, col].set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig(output_scatter_fig, dpi=400, bbox_inches='tight', transparent=False)
plt.show()
print(f"散点图已保存至: {output_scatter_fig}")

# ================= 10. 绘制RMSE柱状图（基于月均值） =================
print("\n正在生成RMSE柱状图...")

fig, ax = plt.subplots(figsize=(10, 6))

colors = ['#d62728', '#1f77b4']
hatches = ['/', '\\']
bar_width = 0.35
x_positions = np.arange(len(SELECT_HOURS))

for idx, (inf_col, mea_col, title_name) in enumerate(tasks):
    if title_name in hourly_rmse:
        rmse_values = [hourly_rmse[title_name].get(hour, np.nan) for hour in SELECT_HOURS]

        bars = ax.bar(x_positions + idx * bar_width,
                      rmse_values,
                      bar_width,
                      label=title_name,
                      color=colors[idx],
                      alpha=0.8,
                      edgecolor='black',
                      linewidth=1.2,
                      hatch=hatches[idx])

        for i, (bar, value) in enumerate(zip(bars, rmse_values)):
            if not np.isnan(value):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.05,
                        f'{value:.2f}',
                        ha='center',
                        va='bottom',
                        fontsize=10,
                        fontweight='bold')

ax.set_xticks(x_positions + bar_width / 2)
ax.set_xticklabels([f'{h}:00' for h in SELECT_HOURS], fontsize=12)
ax.set_ylabel('RMSE (K)', fontsize=14, fontweight='bold')
ax.set_xlabel('Local Time (Hour)', fontsize=14, fontweight='bold')
ax.set_title(f'RMSE Based on Monthly Means - {target_site}\n({START_DATE} to {END_DATE} | {hours_str})',
             fontsize=16, fontweight='bold', pad=20)

y_max = 0
for title_name in hourly_rmse.keys():
    rmse_vals = [v for v in hourly_rmse[title_name].values() if not np.isnan(v)]
    if rmse_vals:
        y_max = max(y_max, max(rmse_vals))
ax.set_ylim(0, y_max * 1.2)

ax.grid(True, axis='y', linestyle='--', alpha=0.3, zorder=0)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='both', direction='in', length=5, width=1.2)

legend = ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True, fontsize=11)
legend.get_frame().set_alpha(0.9)

plt.tight_layout()
plt.savefig(output_rmse_fig, dpi=400, bbox_inches='tight', transparent=False)
plt.show()
print(f"RMSE柱状图已保存至: {output_rmse_fig}")

# ================= 11. 绘制日变化图（基于月均值） =================
print("\n正在生成日变化图...")

cols_plot = 2
rows_plot = math.ceil(len(tasks) / cols_plot)
fig, axes = plt.subplots(rows_plot, cols_plot, figsize=(14, 5.5 * rows_plot))

fig.suptitle(f"Monthly Mean Diurnal Validation at {target_site}\n({START_DATE} to {END_DATE} | {hours_str})",
             fontsize=16, fontweight='bold', y=0.98)

if rows_plot == 1 and cols_plot == 1:
    axes = np.array([[axes]])
elif rows_plot == 1:
    axes = axes.reshape(1, -1)
elif cols_plot == 1:
    axes = axes.reshape(-1, 1)

color_mea = '#1f77b4'
color_inf = '#d62728'

for idx, (inf_col, mea_col, title_name) in enumerate(tasks):
    row = idx // cols_plot
    col = idx % cols_plot
    ax = axes[row, col]

    if title_name not in hourly_stats or hourly_stats[title_name].empty:
        ax.text(0.5, 0.5, 'No Valid Data', ha='center', va='center',
                transform=ax.transAxes, fontsize=12)
        ax.set_title(f'{title_name}', fontweight='bold')
        continue

    df_hourly = hourly_stats[title_name]
    offset = 0.1

    # 绘制实测（基于月均统计的均值和标准差）
    ax.errorbar(df_hourly['Hour'] - offset, df_hourly[f'{mea_col}_mean'],
                yerr=df_hourly[f'{mea_col}_std'],
                fmt='o-', color=color_mea,
                markerfacecolor='white', markeredgecolor=color_mea, markeredgewidth=1.5,
                capsize=4, capthick=1.5, elinewidth=1.5,
                label='Measured (In-situ)', markersize=7, zorder=3)

    # 绘制反演（基于月均统计的均值和标准差）
    ax.errorbar(df_hourly['Hour'] + offset, df_hourly[f'{inf_col}_mean'],
                yerr=df_hourly[f'{inf_col}_std'],
                fmt='s-', color=color_inf,
                markerfacecolor='white', markeredgecolor=color_inf, markeredgewidth=1.5,
                capsize=4, capthick=1.5, elinewidth=1.5,
                label='Inverted (Satellite)', markersize=6, zorder=3)

    if SELECT_HOURS:
        ax.set_xticks(SELECT_HOURS)
        ax.set_xlim(min(SELECT_HOURS) - 0.5, max(SELECT_HOURS) + 0.5)
    else:
        ax.set_xticks(np.arange(0, 24, 2))
        ax.set_xlim(-1, 24)

    ax.set_ylim(290, 340)
    ax.tick_params(axis='both', direction='in', length=5, width=1.2, top=False, right=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, axis='y', linestyle='--', alpha=0.6, zorder=0)
    ax.set_title(f'{title_name}', pad=15, fontweight='bold')
    ax.set_xlabel('Local Time (Hour)', fontweight='bold')
    ax.set_ylabel('Temperature (K)', fontweight='bold')
    ax.legend(loc='upper left', frameon=False)

for idx in range(len(tasks), rows_plot * cols_plot):
    row = idx // cols_plot
    col = idx % cols_plot
    axes[row, col].set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig(output_fig, dpi=400, bbox_inches='tight', transparent=False)
plt.show()
print(f"日变化图已保存至: {output_fig}")

print("\n" + "=" * 60)
print("所有分析完成！")
print("=" * 60)
print(f"散点图: {output_scatter_fig}")
print(f"RMSE柱状图: {output_rmse_fig}")
print(f"日变化图: {output_fig}")