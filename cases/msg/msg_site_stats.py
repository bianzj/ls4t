import os
import glob
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

# ==================== 参数设置 ====================
# 数据根目录
field_root = '/Users/bianzj/Downloads/data/field/f2025/'

# 要分析的小时（24小时制）
TARGET_HOUR = 14  # 下午2点

# 输出目录
output_dir = '/Users/bianzj/Downloads/data/field_analysis'
os.makedirs(output_dir, exist_ok=True)

# ==================== 查找所有站点 ====================
print("=" * 60)
print("查找所有野外站点数据...")
print("=" * 60)

# 查找所有 ICOSETC_*_METEO_L2 文件夹
site_folders = glob.glob(os.path.join(field_root, 'ICOSETC_*_METEO_L2'))

if len(site_folders) == 0:
    print("未找到任何站点文件夹!")
    exit()

print(f"找到 {len(site_folders)} 个站点")

# 提取站点名称
site_names = []
for folder in site_folders:
    folder_name = os.path.basename(folder)
    # 提取 ICOSETC_XXX_METEO_L2 中的 XXX
    site_name = folder_name.replace('ICOSETC_', '').replace('_METEO_L2', '')
    site_names.append(site_name)

print(f"站点列表: {site_names}")

# ==================== 遍历站点，提取数据 ====================
all_results = {}

for site_idx, site_name in enumerate(site_names):
    print(f"\n处理站点 {site_idx + 1}/{len(site_names)}: {site_name}")

    # 构建文件路径
    folder_path = os.path.join(field_root, f'ICOSETC_{site_name}_METEO_L2')
    file_path = os.path.join(folder_path, f'ICOSETC_{site_name}_METEO_L2.csv')

    if not os.path.exists(file_path):
        print(f"  警告: 文件不存在 - {file_path}")
        continue

    try:
        # 读取数据
        df = pd.read_csv(file_path)

        # 检查必要的列是否存在
        if 'TIMESTAMP_START' not in df.columns:
            print(f"  警告: TIMESTAMP_START 列不存在")
            continue
        if 'TS_1' not in df.columns or 'TA' not in df.columns:
            print(f"  警告: TS_1 或 TA 列不存在")
            continue

        # 解析时间
        df['datetime'] = pd.to_datetime(df['TIMESTAMP_START'], format='%Y%m%d%H%M')
        df['year'] = df['datetime'].dt.year
        df['month'] = df['datetime'].dt.month
        df['hour'] = df['datetime'].dt.hour

        # 筛选下午2点（14:00）的数据
        df_hour = df[df['hour'] == TARGET_HOUR].copy()

        if len(df_hour) == 0:
            print(f"  警告: 没有 {TARGET_HOUR}:00 的数据")
            continue

        # 清理不合理值
        df_hour['TS_1_clean'] = df_hour['TS_1'].copy()
        df_hour['TA_clean'] = df_hour['TA'].copy()

        # 将不合理值设为NaN（<-100或>100）
        df_hour.loc[(df_hour['TS_1'] < -100) | (df_hour['TS_1'] > 100), 'TS_1_clean'] = np.nan
        df_hour.loc[(df_hour['TA'] < -100) | (df_hour['TA'] > 100), 'TA_clean'] = np.nan

        # 计算温差 (TS_1 - TA)
        df_hour['temp_diff'] = df_hour['TS_1_clean'] - df_hour['TA_clean']

        # 按月统计
        monthly_stats = df_hour.groupby(['year', 'month']).agg({
            'temp_diff': ['mean', 'std', 'count', 'sem'],
            'TS_1_clean': 'mean',
            'TA_clean': 'mean'
        }).reset_index()

        # 重命名列
        monthly_stats.columns = ['year', 'month', 'diff_mean', 'diff_std', 'diff_count', 'diff_sem',
                                 'ts1_mean', 'ta_mean']

        # 创建日期列用于绘图
        monthly_stats['date'] = pd.to_datetime(monthly_stats[['year', 'month']].assign(day=1))

        # 保存结果
        all_results[site_name] = monthly_stats

        print(f"  成功: {len(monthly_stats)} 个月的数据")

    except Exception as e:
        print(f"  错误: {e}")
        continue

# ==================== 绘制结果 ====================
if len(all_results) == 0:
    print("\n没有成功读取任何站点数据!")
    exit()

print(f"\n{'=' * 60}")
print(f"成功处理 {len(all_results)} 个站点")
print(f"{'=' * 60}")

# 1. 绘制所有站点的月温差变化（子图）
n_sites = len(all_results)
n_cols = 3
n_rows = (n_sites + n_cols - 1) // n_cols

fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
axes = axes.flatten()

for idx, (site_name, monthly_stats) in enumerate(sorted(all_results.items())):
    ax = axes[idx]

    if len(monthly_stats) > 0:
        # 绘制月均温差
        ax.plot(monthly_stats['date'], monthly_stats['diff_mean'],
                marker='o', linewidth=1.5, markersize=4, label='TS_1 - TA')

        # 添加误差条（标准差）
        ax.fill_between(monthly_stats['date'],
                        monthly_stats['diff_mean'] - monthly_stats['diff_std'],
                        monthly_stats['diff_mean'] + monthly_stats['diff_std'],
                        alpha=0.2, label='±1σ')

        # 添加零线
        ax.axhline(y=0, color='r', linestyle='--', alpha=0.3, linewidth=0.8)

        # 设置标签
        ax.set_xlabel('时间')
        ax.set_ylabel('温差 (°C)')
        ax.set_title(f'{site_name}\n(14:00 TS_1 - TA)')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # 格式化x轴
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(plt.matplotlib.dates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

# 隐藏多余的子图
for idx in range(len(all_results), len(axes)):
    axes[idx].set_visible(False)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'all_sites_monthly_temp_diff.png'), dpi=300, bbox_inches='tight')
plt.show()

# 2. 绘制汇总统计（所有站点的平均月温差）
print("\n绘制所有站点平均月温差...")

# 合并所有站点的月数据，按月份对齐
all_monthly_diffs = {}
for site_name, monthly_stats in all_results.items():
    for _, row in monthly_stats.iterrows():
        key = (row['year'], row['month'])
        if key not in all_monthly_diffs:
            all_monthly_diffs[key] = []
        all_monthly_diffs[key].append(row['diff_mean'])

# 计算统计
summary_data = []
for (year, month), diffs in sorted(all_monthly_diffs.items()):
    if len(diffs) > 0:
        summary_data.append({
            'year': year,
            'month': month,
            'date': pd.Timestamp(year=year, month=month, day=1),
            'mean_diff': np.mean(diffs),
            'std_diff': np.std(diffs),
            'sem_diff': np.std(diffs) / np.sqrt(len(diffs)),
            'n_sites': len(diffs)
        })

summary_df = pd.DataFrame(summary_data)

# 绘制平均月温差
fig, ax = plt.subplots(figsize=(12, 6))

if len(summary_df) > 0:
    ax.plot(summary_df['date'], summary_df['mean_diff'],
            marker='o', linewidth=2, markersize=6, color='blue', label='平均温差')

    # 添加误差条（标准误）
    ax.fill_between(summary_df['date'],
                    summary_df['mean_diff'] - summary_df['sem_diff'],
                    summary_df['mean_diff'] + summary_df['sem_diff'],
                    alpha=0.2, color='blue', label='±1 SEM')

    # 添加零线
    ax.axhline(y=0, color='r', linestyle='--', alpha=0.5, linewidth=1)

    # 显示站点数量
    for _, row in summary_df.iterrows():
        ax.text(row['date'], row['mean_diff'] + 0.2,
                f'n={row["n_sites"]}', fontsize=8, ha='center')

    ax.set_xlabel('时间')
    ax.set_ylabel('平均温差 (°C)')
    ax.set_title(f'所有站点平均月温差 (14:00 TS_1 - TA)\n共 {len(all_results)} 个站点')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 格式化x轴
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(plt.matplotlib.dates.MonthLocator(interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'all_sites_average_monthly_temp_diff.png'), dpi=300, bbox_inches='tight')
    plt.show()

# 3. 保存统计结果到CSV
print("\n保存统计结果...")

# 保存每个站点的月数据
for site_name, monthly_stats in all_results.items():
    output_file = os.path.join(output_dir, f'{site_name}_monthly_stats.csv')
    monthly_stats.to_csv(output_file, index=False)

# 保存汇总统计
if len(summary_df) > 0:
    summary_df.to_csv(os.path.join(output_dir, 'all_sites_summary_monthly_stats.csv'), index=False)

print(f"\n所有结果已保存到: {output_dir}")
print("\n完成!")
