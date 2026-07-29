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

indir = "/media/hero/MSG/"
# 新旧反演数据路径
file_inferred_new = indir + "/PRODUCTS/LSCT_Site_Results.csv"
file_inferred_old = indir + "/PRODUCTS/LSCT_Site_Results_old.csv"
file_measured = indir + "/field/Evo-2017.csv"

output_stats = indir + "/PRODUCTS/LSCT_Validation_Stats_Evora_Compare.csv"
output_fig = indir + "/PRODUCTS/LSCT_Diurnal_Validation_Evora_Compare.png"
output_rmse_fig = indir + "/PRODUCTS/LSCT_RMSE_Bar_Evora_Compare.png"
output_scatter_fig = indir + "/PRODUCTS/LSCT_Scatter_Evora_Compare.png"

# --- 时间选择设定 ---
START_DATE = '2017-07-01'
END_DATE = '2017-12-30'

# 设定只提取特定的小时
SELECT_HOURS = [10, 11, 12, 13, 14, 15, 16]

# 设定残差阈值（单位：K）
DIFF_THRESHOLD = 10.0
target_site = "Evora"
Tsky = 250
emis_v = 0.985
emis_s = 0.985

# 任务定义：4组对比（旧土壤、新土壤、旧植被、新植被）【散点图保留4张】
tasks = [
    ('T_Sunlit_Soil', 'Ts', '(a) Soil Temperature', 'old'),
    ('T_Sunlit_Soil', 'Ts', '(b) Soil Temperature (proposed)', 'new'),
    ('T_Vegetation', 'Tcrown', '(c) Vegetation Temperature', 'old'),
    ('T_Vegetation', 'Tcrown', '(d) Vegetation Temperature (proposed)', 'new')
]

# ========== 关键修改：柱状图只保留植被新旧两组，删除土壤 ==========
bar_groups = [
    ('Old Canopy', 'T_Vegetation', 'old'),
    ('New Canopy', 'T_Vegetation', 'new')
]

# ================= 1. 读取并解析新旧反演数据 =================
def parse_inf_time(val):
    s = "{:.0f}".format(float(val))
    return pd.to_datetime(s, format='%Y%m%d%H%M')

# 新反演数据
df_inf_new = pd.read_csv(file_inferred_new)
df_inf_new = df_inf_new[df_inf_new['Site'] == target_site].copy()
df_inf_new['DateTime'] = df_inf_new['DateTime'].apply(parse_inf_time)

# 旧反演数据
df_inf_old = pd.read_csv(file_inferred_old)
df_inf_old = df_inf_old[df_inf_old['Site'] == target_site].copy()
df_inf_old['DateTime'] = df_inf_old['DateTime'].apply(parse_inf_time)

# ================= 2. 处理实测数据 (Measured) =================
df_mea = pd.read_csv(file_measured)
df_mea['DateTime'] = pd.to_datetime(df_mea['Time'], dayfirst=True)

# 温度单位转换（如果是℃转K）
measured_cols = list(set([t[1] for t in tasks]))
for col in measured_cols:
    if col in df_mea.columns:
        if df_mea[col].mean() < 150:
            df_mea[col] = df_mea[col] + 273.15

# ================= 3. 数据匹配与预处理（新旧分别合并） =================
# 新数据合并
df_merge_new = pd.merge(df_inf_new, df_mea, on='DateTime', suffixes=('_inf', '_mea'))
df_merge_new = df_merge_new[(df_merge_new['DateTime'] >= START_DATE) & (df_merge_new['DateTime'] <= END_DATE)]
if SELECT_HOURS is not None and len(SELECT_HOURS) > 0:
    df_merge_new = df_merge_new[df_merge_new['DateTime'].dt.hour.isin(SELECT_HOURS)]

# 旧数据合并
df_merge_old = pd.merge(df_inf_old, df_mea, on='DateTime', suffixes=('_inf', '_mea'))
df_merge_old = df_merge_old[(df_merge_old['DateTime'] >= START_DATE) & (df_merge_old['DateTime'] <= END_DATE)]
if SELECT_HOURS is not None and len(SELECT_HOURS) > 0:
    df_merge_old = df_merge_old[df_merge_old['DateTime'].dt.hour.isin(SELECT_HOURS)]

# 检查数据
if df_merge_new.empty and df_merge_old.empty:
    print(f"新旧数据均未能匹配到有效样本！请检查路径、日期范围或小时设定")
    exit()
print(f"新数据有效样本数: {len(df_merge_new)}")
print(f"旧数据有效样本数: {len(df_merge_old)}")

# ================= 4. 辐射校正（新旧数据分别处理） =================
def radiometric_correction(df):
    """辐射校正函数，返回校正后的Ts、Tcrown（K）"""
    bg = planck(10.5, df['Ts'])
    bv = planck(10.5, df['Tcrown'])
    bsky = planck(10.5, 250)
    # 校正并转换为K
    df['Ts'] = inv_planck(10.5, (bg - (1 - emis_s) * bsky) / emis_s)
    df['Tcrown'] = inv_planck(10.5, (bv - (1 - emis_v) * bsky) / emis_v)
    return df

# 执行校正
df_merge_new = radiometric_correction(df_merge_new)
df_merge_old = radiometric_correction(df_merge_old)

# 转换为℃（和原代码保持一致）
df_merge_new['Ts'] = df_merge_new['Ts'] - 273.15
df_merge_new['Tcrown'] = df_merge_new['Tcrown'] - 273.15
df_merge_old['Ts'] = df_merge_old['Ts'] - 273.15
df_merge_old['Tcrown'] = df_merge_old['Tcrown'] - 273.15

# ================= 5. 数据清洗与准备 =================
def add_time_features(df):
    """添加时间特征"""
    df['Hour'] = df['DateTime'].dt.hour
    df['Month'] = df['DateTime'].dt.to_period('M')
    return df

df_merge_new = add_time_features(df_merge_new)
df_merge_old = add_time_features(df_merge_old)

# ================= 6. 计算月均值（新旧分别计算） =================
print("\n" + "=" * 60)
print("步骤1: 计算新旧数据的月均值")
print("=" * 60)

monthly_means = {}  # 存储所有任务的月均数据
hourly_rmse = {}  # 存储所有任务的每小时RMSE
hourly_stats = {}  # 存储所有任务的每小时统计量

# 分别处理每个任务（旧/新 土壤/植被）
for inf_col, mea_col, title_name, data_type in tasks:
    # 选择对应数据集
    df_merge = df_merge_new if data_type == 'new' else df_merge_old

    # 过滤无效数据和异常值
    mask = (df_merge[inf_col].notna()) & (df_merge[mea_col].notna())
    abs_diff = np.abs(df_merge[inf_col] - df_merge[mea_col])
    valid_mask = mask & (abs_diff <= DIFF_THRESHOLD)
    df_temp = df_merge[valid_mask].copy()

    if len(df_temp) == 0:
        print(f"警告: {title_name} 没有有效数据")
        continue

    # 按月+小时分组，计算月均值
    monthly_grouped = df_temp.groupby(['Month', 'Hour']).agg({
        inf_col: ['mean', 'std', 'count'],
        mea_col: ['mean', 'std', 'count']
    }).reset_index()

    # 重命名列
    monthly_grouped.columns = ['Month', 'Hour',
                               f'{inf_col}_mean', f'{inf_col}_std', f'{inf_col}_count',
                               f'{mea_col}_mean', f'{mea_col}_std', f'{mea_col}_count']

    # 过滤样本数太少的组合
    monthly_grouped = monthly_grouped[monthly_grouped[f'{inf_col}_count'] >= 2]

    print(f"\n{title_name}:")
    print(f"  共得到 {len(monthly_grouped)} 个月-小时组合")
    print(f"  月份范围: {monthly_grouped['Month'].min()} 至 {monthly_grouped['Month'].max()}")

    # 存储月均数据
    monthly_means[title_name] = monthly_grouped

    # ================= 7. 计算每小时统计量和RMSE =================
    # 按小时分组计算统计量
    hourly_grouped = monthly_grouped.groupby('Hour').agg({
        f'{inf_col}_mean': ['mean', 'std'],
        f'{mea_col}_mean': ['mean', 'std'],
        f'{inf_col}_count': 'sum'
    }).reset_index()

    hourly_grouped.columns = ['Hour',
                              f'{inf_col}_mean', f'{inf_col}_std',
                              f'{mea_col}_mean', f'{mea_col}_std',
                              'count']

    # 填充NaN标准差
    hourly_grouped[f'{inf_col}_std'] = hourly_grouped[f'{inf_col}_std'].fillna(0)
    hourly_grouped[f'{mea_col}_std'] = hourly_grouped[f'{mea_col}_std'].fillna(0)

    hourly_stats[title_name] = hourly_grouped

    # 计算每小时RMSE
    rmse_by_hour = {}
    for hour in SELECT_HOURS:
        hour_monthly = monthly_grouped[monthly_grouped['Hour'] == hour]
        if len(hour_monthly) > 0:
            rmse = np.sqrt(np.mean((hour_monthly[f'{inf_col}_mean'] -
                                    hour_monthly[f'{mea_col}_mean']) ** 2))
            rmse_by_hour[hour] = rmse
        else:
            rmse_by_hour[hour] = np.nan

    hourly_rmse[title_name] = rmse_by_hour

# ================= 8. 打印总体统计结果 =================
print("\n" + "=" * 60)
print("新旧数据总体统计对比")
print("=" * 60)

for inf_col, mea_col, title_name, data_type in tasks:
    if title_name not in monthly_means:
        continue

    df_monthly = monthly_means[title_name]
    if len(df_monthly) > 0:
        overall_rmse = np.sqrt(np.mean((df_monthly[f'{inf_col}_mean'] -
                                        df_monthly[f'{mea_col}_mean']) ** 2))
        r2 = r2_score(df_monthly[f'{mea_col}_mean'], df_monthly[f'{inf_col}_mean'])
        bias = np.mean(df_monthly[f'{inf_col}_mean'] - df_monthly[f'{mea_col}_mean'])

        print(f"\n{title_name}:")
        print(f"  RMSE (月均) = {overall_rmse:.3f} K")
        print(f"  R² (月均) = {r2:.4f}")
        print(f"  Bias (月均) = {bias:.3f} K")
        print(f"  有效月-小时组合数 = {len(df_monthly)}")

# ================= 9. 绘制4组散点图（新旧对比，统一单色） =================
print("\n正在生成散点图...")

cols_plot = 2
rows_plot = 2  # 2行2列，正好4组
fig_scatter, axes_scatter = plt.subplots(rows_plot, cols_plot, figsize=(14, 11))

hours_str = f"{min(SELECT_HOURS)}:00-{max(SELECT_HOURS)}:00" if SELECT_HOURS else "Full Day"


# 散点配色：旧数据浅灰，新数据深灰，区分度清晰
scatter_colors = {
    'old': '#808080',
    'new': '#262626'
}

for idx, (inf_col, mea_col, title_name, data_type) in enumerate(tasks):
    row = idx // cols_plot
    col = idx % cols_plot
    ax = axes_scatter[row, col]

    if title_name not in monthly_means:
        ax.text(0.5, 0.5, 'No Valid Data', ha='center', va='center',
                transform=ax.transAxes, fontsize=12)
        ax.set_title(f'{title_name}', fontweight='bold')
        continue

    df_monthly = monthly_means[title_name]
    point_color = scatter_colors[data_type]

    # 绘制1:1线
    all_vals = np.concatenate([df_monthly[f'{mea_col}_mean'].values,
                               df_monthly[f'{inf_col}_mean'].values])
    min_val = np.min(all_vals) - 2
    max_val = np.max(all_vals) + 2
    ax.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=0.8, alpha=0.5, label='1:1 Line')

    # 统一单色绘制散点（不按小时区分颜色）
    ax.scatter(
        df_monthly[f'{mea_col}_mean'],
        df_monthly[f'{inf_col}_mean'],
        color=point_color,
        s=70,
        alpha=0.7,
        edgecolors='black',
        linewidth=0.5,
        zorder=3
    )

    # 计算统计量
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
    ax.legend(loc='lower right', frameon=True, fontsize=9)

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig(output_scatter_fig, dpi=400, bbox_inches='tight', transparent=False)
plt.show()
print(f"散点对比图已保存至: {output_scatter_fig}")

# ================= 10. 【修改后】仅植被新旧两组RMSE对比柱状图 =================
# print("\n正在生成植被新旧RMSE对比柱状图...")
# fig, ax = plt.subplots(figsize=(10, 6))
# # 仅两组配色+填充纹理
# bar_colors = ['#98df8a', '#2ca02c']    # 旧植被浅绿，新植被深绿
# bar_hatches = ['//', '\\\\']
# bar_width = 0.35    # 两组加宽更美观
# x_positions = np.arange(len(SELECT_HOURS))

# ==========================
# 图1：植被温度 RMSE 柱状图
# ==========================
print("\n正在生成植被温度新旧RMSE对比图...")
fig, ax = plt.subplots(figsize=(10,6))
bar_width = 0.35
x = np.arange(len(SELECT_HOURS))

old_task = '(c) Vegetation Temperature'
new_task = '(d) Vegetation Temperature (proposed)'

rmse_old = [hourly_rmse[old_task].get(h, np.nan) for h in SELECT_HOURS]
rmse_new = [hourly_rmse[new_task].get(h, np.nan) for h in SELECT_HOURS]

ax.bar(x - bar_width/2, rmse_old, bar_width, label='existing', color='#98df8a', ec='k', hatch='//')
ax.bar(x + bar_width/2, rmse_new, bar_width, label='proposed', color='#2ca02c', ec='k', hatch='\\\\')

for i, v in enumerate(rmse_old):
    if not np.isnan(v): ax.text(i-bar_width/2, v+0.05, f'{v:.2f}', ha='center', fontsize=9, fontweight='bold')
for i, v in enumerate(rmse_new):
    if not np.isnan(v): ax.text(i+bar_width/2, v+0.05, f'{v:.2f}', ha='center', fontsize=9, fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels([f'{h}:00' for h in SELECT_HOURS])
ax.set_ylabel('RMSE (K)')
ax.set_xlabel('Hour')
ax.set_title(f'Canopy Temperature RMSE: Old vs New\n{target_site}', fontweight='bold')
ax.legend()
ax.grid(axis='y', ls='--', alpha=0.3)
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig(output_rmse_fig, dpi=400, bbox_inches='tight')
plt.show()

# ==========================
# 图2：新增 土壤温度 RMSE 柱状图
# ==========================
print("\n正在生成土壤温度新旧RMSE对比图...")
fig, ax = plt.subplots(figsize=(10,6))

soil_old_task = '(a) Soil Temperature'
soil_new_task = '(b) Soil Temperature (proposed)'

rmse_soil_old = [hourly_rmse[soil_old_task].get(h, np.nan) for h in SELECT_HOURS]
rmse_soil_new = [hourly_rmse[soil_new_task].get(h, np.nan) for h in SELECT_HOURS]

ax.bar(x - bar_width/2, rmse_soil_old, bar_width, label='existing', color='#ff9896', ec='k', hatch='//')
ax.bar(x + bar_width/2, rmse_soil_new, bar_width, label='proposed', color='#d62728', ec='k', hatch='\\\\')

for i, v in enumerate(rmse_soil_old):
    if not np.isnan(v): ax.text(i-bar_width/2, v+0.05, f'{v:.2f}', ha='center', fontsize=9, fontweight='bold')
for i, v in enumerate(rmse_soil_new):
    if not np.isnan(v): ax.text(i+bar_width/2, v+0.05, f'{v:.2f}', ha='center', fontsize=9, fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels([f'{h}:00' for h in SELECT_HOURS])
ax.set_ylabel('RMSE (K)')
ax.set_xlabel('Hour')
ax.set_title(f'Soil Temperature RMSE: Old vs New\n{target_site}', fontweight='bold')
ax.legend()
ax.grid(axis='y', ls='--', alpha=0.3)
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.show()

