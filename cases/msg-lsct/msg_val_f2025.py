import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
import os

warnings.filterwarnings('ignore')

# ==================== 参数设置 ====================
# 站点和年份
site = 'FR-AUR'  # 站点名称
year = '2022'  # 年份

# site = 'ES-LMA'  # 站点名称
# year = '2025'  # 年份

# ==================== 选择要对比的变量 ====================
# 配置对比组合: [MSG变量, 野外变量, 标签]
# 可选MSG变量: LST1, LST2, LST3, LST4
# 可选野外变量: TS_1, TA
comparisons = [
    {'msg_var': 'LST4', 'field_var': 'TS_1', 'label': 'LST1 vs TS_1'},
    {'msg_var': 'LST2', 'field_var': 'TA', 'label': 'LST2 vs TA'},
    # 可以添加更多对比，例如:
    # {'msg_var': 'LST3', 'field_var': 'TS_1', 'label': 'LST3 vs TS_1'},
    # {'msg_var': 'LST4', 'field_var': 'TA', 'label': 'LST4 vs TA'},
]

# ==================== 时间筛选参数 ====================
# 选择要分析的小时（24小时制）
SELECTED_HOURS = [12,13,14,15,16]  # 只分析10、11、12点的数据
# 如果不想筛选，设置为 None 或空列表
# SELECTED_HOURS = None  # 分析所有小时

# ==================== 误差筛选参数 ====================
# 误差阈值：只保留 |MSG - Field| <= ERROR_THRESHOLD 的数据
ERROR_THRESHOLD = 15  # 单位：°C，可根据实际情况调整
# 是否启用误差筛选
USE_ERROR_FILTER = True  # True: 启用筛选, False: 不筛选

# ==================== 其他参数 ====================
# 差异阈值：超过此值的差异将被标记为异常（用于统计）
DIFF_THRESHOLD = 10  # 单位：°C，可根据实际情况调整
# 合理温度范围：低于此值视为不合理数据，设为NaN
MIN_VALID_TEMP = -100  # °C

# 输出目录
output_dir = '/Users/bianzj/Downloads/data/validation_results'
os.makedirs(output_dir, exist_ok=True)

# 自动构建文件路径
msg_file = f'/Users/bianzj/Downloads/data/msg/retrieved/{site}_{year}.csv'
field_file = f'/Users/bianzj/Downloads/data/field/f2025/ICOSETC_{site}_METEO_L2/ICOSETC_{site}_METEO_L2.csv'


# ==================== 定义数据清理函数 ====================
def clean_field_data(temp_values, var_name=''):
    """清理野外温度数据（已经是°C）"""
    converted = np.array(temp_values, dtype=float)

    valid_mask = ~np.isnan(converted)
    if valid_mask.any():
        invalid_mask = (converted < MIN_VALID_TEMP) | (converted > 100)
        if invalid_mask.any():
            print(f"  {var_name}: 将 {invalid_mask.sum()} 个不合理值(<-100或>100)设为NaN")
            converted[invalid_mask] = np.nan

    return converted


def convert_k_to_celsius(kelvin_values, var_name=''):
    """将开尔文(K)转换为摄氏度(°C)"""
    converted = np.array(kelvin_values, dtype=float)

    valid_mask = ~np.isnan(converted)
    if valid_mask.any():
        invalid_mask = (converted < 200) | (converted > 350)
        if invalid_mask.any():
            print(f"  {var_name}: 将 {invalid_mask.sum()} 个不合理的开尔文值设为NaN")
            converted[invalid_mask] = np.nan

        still_valid = ~np.isnan(converted)
        if still_valid.any():
            converted[still_valid] = converted[still_valid] - 273.15
            print(f"  {var_name}: 将 {still_valid.sum()} 个值从K转换为°C")

    valid_mask = ~np.isnan(converted)
    if valid_mask.any():
        invalid_mask = (converted < MIN_VALID_TEMP) | (converted > 100)
        if invalid_mask.any():
            print(f"  {var_name}: 将 {invalid_mask.sum()} 个转换后不合理的值设为NaN")
            converted[invalid_mask] = np.nan

    return converted


# ==================== 1. 读取数据 ====================
print(f"处理站点: {site}, 年份: {year}")
if SELECTED_HOURS:
    print(f"分析小时: {SELECTED_HOURS}")
else:
    print("分析所有小时")
if USE_ERROR_FILTER:
    print(f"误差筛选阈值: ±{ERROR_THRESHOLD}°C")
else:
    print("未启用误差筛选")
print("=" * 60)
print(f"MSG文件: {msg_file}")
print(f"野外文件: {field_file}")
print("=" * 60)

print("\n读取数据...")
try:
    msg_df = pd.read_csv(msg_file)
    field_df = pd.read_csv(field_file)
except FileNotFoundError as e:
    print(f"错误: 文件不存在 - {e}")
    exit()

print(f"MSG数据形状: {msg_df.shape}")
print(f"野外数据形状: {field_df.shape}")

# ==================== 2. 处理时间 ====================
msg_df['datetime'] = pd.to_datetime(msg_df[['year', 'month', 'day', 'hour']])
field_df['datetime'] = pd.to_datetime(field_df['TIMESTAMP_START'], format='%Y%m%d%H%M')

# 提取小时信息
msg_df['hour'] = msg_df['datetime'].dt.hour
field_df['hour'] = field_df['datetime'].dt.hour

print(f"\nMSG时间范围: {msg_df['datetime'].min()} 到 {msg_df['datetime'].max()}")
print(f"野外时间范围: {field_df['datetime'].min()} 到 {field_df['datetime'].max()}")

# ==================== 3. 筛选特定小时 ====================
if SELECTED_HOURS:
    print(f"\n筛选小时: {SELECTED_HOURS}")
    msg_df = msg_df[msg_df['hour'].isin(SELECTED_HOURS)]
    field_df = field_df[field_df['hour'].isin(SELECTED_HOURS)]
    print(f"筛选后MSG数据形状: {msg_df.shape}")
    print(f"筛选后野外数据形状: {field_df.shape}")

    if len(msg_df) == 0 or len(field_df) == 0:
        print("警告: 筛选后没有数据!")
        exit()

# ==================== 4. 数据转换和清理 ====================
print("\n" + "=" * 60)
print("数据转换: MSG (K→°C), 清理不合理值")
print("=" * 60)

# 获取所有需要转换的MSG变量
msg_vars = list(set([comp['msg_var'] for comp in comparisons]))
# 转换MSG的LST数据（K → °C）
for lst_var in msg_vars:
    if lst_var in msg_df.columns:
        msg_df[lst_var] = convert_k_to_celsius(msg_df[lst_var], lst_var)
    else:
        print(f"警告: {lst_var} 不存在于MSG数据中!")

# 获取所有需要清理的野外变量
field_vars = list(set([comp['field_var'] for comp in comparisons]))
# 清理野外数据（已经是°C）
for var in field_vars:
    if var in field_df.columns:
        field_df[var] = clean_field_data(field_df[var], var)
    else:
        print(f"警告: {var} 不存在于野外数据中!")

# ==================== 5. 匹配时间并筛选误差 ====================
print("\n匹配时间数据...")
msg_df['hour_key'] = msg_df['datetime'].dt.floor('H')
field_df['hour_key'] = field_df['datetime'].dt.floor('H')

# 为每个对比创建匹配数据
merged_dfs = []
all_merged_before_filter = []  # 用于记录筛选前的数据量

for comp in comparisons:
    msg_var = comp['msg_var']
    field_var = comp['field_var']

    # 检查变量是否存在
    if msg_var not in msg_df.columns or field_var not in field_df.columns:
        print(f"跳过 {comp['label']}: 变量不存在")
        continue

    # 合并数据
    merged_df = pd.merge(
        msg_df[['datetime', 'hour_key', msg_var, 'hour']],
        field_df[['hour_key', field_var]],
        on='hour_key',
        how='inner'
    )

    # 重命名列以便统一处理
    merged_df = merged_df.rename(columns={msg_var: 'msg_value', field_var: 'field_value'})
    merged_df['msg_var'] = msg_var
    merged_df['field_var'] = field_var
    merged_df['label'] = comp['label']

    # 计算初始误差（用于筛选）
    merged_df['error'] = merged_df['msg_value'] - merged_df['field_value']
    merged_df['abs_error'] = np.abs(merged_df['error'])

    # 记录筛选前的数据量
    before_count = len(merged_df)
    all_merged_before_filter.append((comp['label'], before_count))

    # 应用误差筛选
    if USE_ERROR_FILTER:
        # 只保留误差 <= ERROR_THRESHOLD 的数据（同时去除NaN）
        valid_mask = merged_df['msg_value'].notna() & merged_df['field_value'].notna()
        merged_df = merged_df[valid_mask & (merged_df['abs_error'] <= ERROR_THRESHOLD)]

        after_count = len(merged_df)
        print(
            f"{comp['label']}: 筛选前 {before_count} 个点, 筛选后 {after_count} 个点 (保留 {after_count / before_count * 100:.1f}%)")
    else:
        after_count = before_count
        print(f"{comp['label']}: 匹配到 {before_count} 个点 (未筛选)")

    merged_dfs.append(merged_df)

if len(merged_dfs) == 0:
    print("警告: 没有匹配到任何数据!")
    exit()


# ==================== 6. 计算统计指标 ====================
def calculate_stats(df, label):
    """计算统计指标并打印"""
    # 去除缺失值
    valid_mask = df['msg_value'].notna() & df['field_value'].notna()
    x_values = df.loc[valid_mask, 'msg_value'].values
    y_values = df.loc[valid_mask, 'field_value'].values

    if len(x_values) == 0:
        print(f"\n{label}: 没有有效数据!")
        return None

    # 计算差异
    diff = x_values - y_values
    abs_diff = np.abs(diff)

    # 计算统计指标
    mae = mean_absolute_error(y_values, x_values)
    rmse = np.sqrt(mean_squared_error(y_values, x_values))
    r2 = r2_score(y_values, x_values)
    bias = np.mean(diff)
    std_diff = np.std(diff)

    # 计算异常值比例
    outlier_ratio = (abs_diff > DIFF_THRESHOLD).sum() / len(x_values) * 100

    print(f"\n{'=' * 60}")
    print(f"{label}")
    print(f"{'=' * 60}")
    print(f"样本数: {len(x_values)}")
    print(f"MAE: {mae:.4f}°C")
    print(f"RMSE: {rmse:.4f}°C")
    print(f"R²: {r2:.4f}")
    print(f"Bias (MSG - Field): {bias:.4f}°C")
    print(f"标准差 (差异): {std_diff:.4f}°C")
    print(f"异常值比例 (>±{DIFF_THRESHOLD}°C): {outlier_ratio:.1f}%")
    print(f"MSG均值: {np.mean(x_values):.4f}°C")
    print(f"Field均值: {np.mean(y_values):.4f}°C")

    # 按小时统计
    if 'hour' in df.columns:
        print(f"\n按小时统计:")
        for hour in sorted(df['hour'].unique()):
            hour_mask = df['hour'] == hour
            hour_valid = hour_mask & valid_mask
            if hour_valid.sum() > 0:
                hour_msg = df.loc[hour_valid, 'msg_value'].values
                hour_field = df.loc[hour_valid, 'field_value'].values
                hour_diff = hour_msg - hour_field
                print(
                    f"  {hour:02d}:00 - n={len(hour_msg)}, Bias={np.mean(hour_diff):.2f}°C, RMSE={np.sqrt(np.mean(hour_diff ** 2)):.2f}°C")

    return {
        'n': len(x_values),
        'MAE': mae,
        'RMSE': rmse,
        'R2': r2,
        'Bias': bias,
        'Std_diff': std_diff,
        'Outlier_ratio': outlier_ratio,
        'mean_msg': np.mean(x_values),
        'mean_field': np.mean(y_values),
        'msg_var': df['msg_var'].iloc[0],
        'field_var': df['field_var'].iloc[0]
    }


# 计算统计
print("\n" + "=" * 60)
print("统计结果")
print("=" * 60)

stats_results = []
for merged_df in merged_dfs:
    stats = calculate_stats(merged_df, merged_df['label'].iloc[0])
    if stats:
        stats_results.append((merged_df, stats))

# ==================== 7. 绘图 ====================
n_comparisons = len(stats_results)
if n_comparisons == 0:
    print("没有有效数据可以绘图!")
    exit()

# 创建子图布局
n_rows = n_comparisons
n_cols = 2
fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 5 * n_rows))
if n_rows == 1:
    axes = axes.reshape(1, -1)

for idx, (merged_df, stats) in enumerate(stats_results):
    label = merged_df['label'].iloc[0]
    msg_var = stats['msg_var']
    field_var = stats['field_var']

    # 按小时分组着色
    if 'hour' in merged_df.columns:
        hours = sorted(merged_df['hour'].unique())
        colors = plt.cm.tab10(np.linspace(0, 1, len(hours)))
        hour_color_map = {hour: colors[i] for i, hour in enumerate(hours)}

    # 时间序列
    ax1 = axes[idx, 0]
    sorted_df = merged_df.sort_values('datetime')

    # 按小时分组绘制
    if 'hour' in merged_df.columns and len(hours) > 1:
        for hour in hours:
            hour_df = sorted_df[sorted_df['hour'] == hour]
            if len(hour_df) > 0:
                ax1.scatter(hour_df['datetime'], hour_df['msg_value'],
                            label=f'{msg_var} ({hour:02d}:00)', alpha=0.7, s=15,
                            color=hour_color_map[hour], marker='o')
                ax1.scatter(hour_df['datetime'], hour_df['field_value'],
                            label=f'{field_var} ({hour:02d}:00)', alpha=0.7, s=15,
                            color=hour_color_map[hour], marker='s')
    else:
        ax1.plot(sorted_df['datetime'], sorted_df['msg_value'],
                 label=f'{msg_var} (MSG)', alpha=0.7, linewidth=1.5)
        ax1.plot(sorted_df['datetime'], sorted_df['field_value'],
                 label=f'{field_var} (Field)', alpha=0.7, linewidth=1.5)

    ax1.set_xlabel('时间')
    ax1.set_ylabel('温度 (°C)')
    hour_str = ', '.join([f'{h:02d}:00' for h in hours]) if 'hour' in merged_df.columns else 'all'
    filter_str = f'误差≤{ERROR_THRESHOLD}°C' if USE_ERROR_FILTER else '未筛选'
    ax1.set_title(f'{site} {year}: {label}\n小时: {hour_str}, {filter_str}')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)

    # 散点图
    ax2 = axes[idx, 1]
    valid_mask = merged_df['msg_value'].notna() & merged_df['field_value'].notna()
    if valid_mask.any():
        # 按小时着色
        if 'hour' in merged_df.columns and len(hours) > 1:
            for hour in hours:
                hour_mask = valid_mask & (merged_df['hour'] == hour)
                if hour_mask.any():
                    ax2.scatter(merged_df.loc[hour_mask, 'field_value'],
                                merged_df.loc[hour_mask, 'msg_value'],
                                alpha=0.6, s=25, label=f'{hour:02d}:00',
                                color=hour_color_map[hour])
        else:
            ax2.scatter(merged_df.loc[valid_mask, 'field_value'],
                        merged_df.loc[valid_mask, 'msg_value'],
                        alpha=0.5, s=20)

        # 1:1线
        min_val = min(merged_df.loc[valid_mask, 'field_value'].min(),
                      merged_df.loc[valid_mask, 'msg_value'].min())
        max_val = max(merged_df.loc[valid_mask, 'field_value'].max(),
                      merged_df.loc[valid_mask, 'msg_value'].max())
        margin = (max_val - min_val) * 0.05
        ax2.plot([min_val - margin, max_val + margin],
                 [min_val - margin, max_val + margin],
                 'k--', alpha=0.5, linewidth=1, label='1:1线')

        # 显示误差阈值范围（如果启用筛选）
        if USE_ERROR_FILTER:
            # 绘制误差边界线
            min_val_field = merged_df.loc[valid_mask, 'field_value'].min()
            max_val_field = merged_df.loc[valid_mask, 'field_value'].max()
            ax2.fill_between([min_val_field, max_val_field],
                             [min_val_field + ERROR_THRESHOLD, max_val_field + ERROR_THRESHOLD],
                             [min_val_field - ERROR_THRESHOLD, max_val_field - ERROR_THRESHOLD],
                             alpha=0.1, color='gray', label=f'误差≤{ERROR_THRESHOLD}°C')

        ax2.set_xlabel(f'{field_var} (Field) °C')
        ax2.set_ylabel(f'{msg_var} (MSG) °C')
        ax2.set_title(f'{label}\nR²={stats["R2"]:.3f}, RMSE={stats["RMSE"]:.2f}°C, n={stats["n"]}')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(
    f'{output_dir}/{site}_{year}_validation_results_hour{"_".join(map(str, SELECTED_HOURS)) if SELECTED_HOURS else "all"}_filter{ERROR_THRESHOLD if USE_ERROR_FILTER else "none"}.png',
    dpi=300, bbox_inches='tight')
print(
    f"\n图表已保存到: {output_dir}/{site}_{year}_validation_results_hour{'_'.join(map(str, SELECTED_HOURS)) if SELECTED_HOURS else 'all'}_filter{ERROR_THRESHOLD if USE_ERROR_FILTER else 'none'}.png")
plt.show()

# ==================== 8. 保存结果 ====================
# 保存统计结果
if stats_results:
    stats_list = []
    for _, stats in stats_results:
        stats_list.append({
            'Comparison': f"{stats['msg_var']}_vs_{stats['field_var']}",
            'Site': site,
            'Year': year,
            'Hours': str(SELECTED_HOURS) if SELECTED_HOURS else 'all',
            'Error_Filter': ERROR_THRESHOLD if USE_ERROR_FILTER else 'none',
            'N': stats['n'],
            'MAE_°C': stats['MAE'],
            'RMSE_°C': stats['RMSE'],
            'R2': stats['R2'],
            'Bias_°C': stats['Bias'],
            'Std_Diff_°C': stats['Std_diff'],
            'Outlier_%': stats['Outlier_ratio'],
            'MSG_mean_°C': stats['mean_msg'],
            'Field_mean_°C': stats['mean_field']
        })

    stats_df = pd.DataFrame(stats_list)
    stats_file = f'{output_dir}/{site}_{year}_statistics_hour{"_".join(map(str, SELECTED_HOURS)) if SELECTED_HOURS else "all"}_filter{ERROR_THRESHOLD if USE_ERROR_FILTER else "none"}.csv'
    stats_df.to_csv(stats_file, index=False)
    print(f"统计结果已保存到: {stats_file}")

# 保存匹配数据
for idx, (merged_df, stats) in enumerate(stats_results):
    hour_str = "_".join(map(str, SELECTED_HOURS)) if SELECTED_HOURS else "all"
    filter_str = f"filter{ERROR_THRESHOLD}" if USE_ERROR_FILTER else "nofilter"
    output_file = f'{output_dir}/{site}_{year}_{stats["msg_var"]}_vs_{stats["field_var"]}_matched_hour{hour_str}_{filter_str}.csv'
    merged_df.to_csv(output_file, index=False)
    print(f"匹配数据已保存到: {output_file}")

print(f"\n{site} {year} 验证完成!")
print(f"分析小时: {SELECTED_HOURS if SELECTED_HOURS else '所有小时'}")
print(f"误差筛选: {'启用 (阈值=' + str(ERROR_THRESHOLD) + '°C)' if USE_ERROR_FILTER else '未启用'}")