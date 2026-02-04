import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score
from scipy import stats
import math

# ================= 配置参数 =================
file_inferred = "/Users/bianzj/Downloads/data/PRODUCTS/LSCT_Site_Results.csv"
file_measured = "/Users/bianzj/Downloads/data/stations/Kal-2017.csv"
output_stats = "/Users/bianzj/Downloads/data/PRODUCTS/LSCT_Validation_Stats_KAL.csv"

# --- 新增：时间选择设定 ---
START_DATE = '2017-08-01'       # 设定起始日期 (包含)
END_DATE   = '2017-12-31'       # 设定结束日期 (包含)
SELECT_HOURS = [11, 12, 13, 14, 15]  # 设定小时区间 (如只看白天)

# 设定残差阈值（单位：K）
DIFF_THRESHOLD = 10.0
target_site = "KAL"

# 格式：(反演列名, 实测列名, 显示标题)
tasks = [
    ('T_Sunlit_Soil', 'bt_s', 'Sunlit Soil vs bt_s'),
    ('T_Shaded_Soil', 'bt_v', 'Shaded Soil vs bt_v'),
    ('T_Vegetation', 'bt_v', 'Vegetation vs bt_v'),
    ('LST_Euro', 'bt_s', 'LST Euro vs bt_s'),
    ('LST_Euro', 'bt_v', 'LST Euro vs bt_v'),
    ('LST_IODC', 'bt_s', 'LST IODC vs bt_s')
]

# ================= 1. 处理反演数据 (Inferred) =================
df_inf = pd.read_csv(file_inferred)
# 确保站点名称匹配 (KAL)
df_inf = df_inf[df_inf['Site'] == target_site].copy()

def parse_inf_time(val):
    s = "{:.0f}".format(float(val))
    return pd.to_datetime(s, format='%Y%m%d%H%M')

df_inf['DateTime'] = df_inf['DateTime'].apply(parse_inf_time)

# ================= 2. 处理实测数据 (Measured) =================
df_mea = pd.read_csv(file_measured)
# 注意：这里根据你的代码将实测时间列名设为 'time'
df_mea['DateTime'] = pd.to_datetime(df_mea['time'], dayfirst=True)

# 自动处理摄氏度转开尔文
measured_cols = list(set([t[1] for t in tasks]))
for col in measured_cols:
    if col in df_mea.columns:
        if df_mea[col].mean() < 150:
            df_mea[col] = df_mea[col] + 273.15

# ================= 3. 数据匹配与时间过滤 =================
df_merge = pd.merge(df_inf, df_mea, on='DateTime', suffixes=('_inf', '_mea'))

# --- 核心新增：执行时间过滤逻辑 ---
# 1. 过滤日期范围
df_merge = df_merge[(df_merge['DateTime'] >= START_DATE) & (df_merge['DateTime'] <= END_DATE)]

# 2. 过滤特定小时
df_merge = df_merge[df_merge['DateTime'].dt.hour.isin(SELECT_HOURS)]

if df_merge.empty:
    print(f"未能匹配到数据！请检查日期范围 {START_DATE}~{END_DATE} 或小时设定 {SELECT_HOURS}")
    exit()

print(f"时间过滤完成，剩余样本数: {len(df_merge)}")

# ================= 4. 统计与绘图 =================
stats_list = []
cols_plot = 3
rows_plot = math.ceil(len(tasks) / cols_plot)
plt.figure(figsize=(10, 5 * rows_plot))

# 添加总标题显示当前过滤条件
plt.suptitle(f"Site: {target_site} | {START_DATE} to {END_DATE} | Hours: {SELECT_HOURS}", fontsize=16)

for i, (inf_col, mea_col, title_name) in enumerate(tasks):
    mask = (df_merge[inf_col].notna()) & (df_merge[mea_col].notna())
    abs_diff = np.abs(df_merge[inf_col] - df_merge[mea_col])
    valid_mask = mask & (abs_diff <= DIFF_THRESHOLD)

    y_true = df_merge.loc[valid_mask, mea_col]
    y_pred = df_merge.loc[valid_mask, inf_col]
    removed_count = np.sum(mask) - np.sum(valid_mask)

    if len(y_true) < 2:
        print(f"任务 {title_name} 有效数据不足，跳过。")
        continue

    bias = np.mean(y_pred - y_true)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r_val, _ = stats.pearsonr(y_true, y_pred)

    stats_list.append({
        'Task': title_name,
        'Bias': bias, 'RMSE': rmse, 'R': r_val,
        'Valid_Count': len(y_true), 'Removed': removed_count
    })

    ax = plt.subplot(rows_plot, cols_plot, i + 1)
    ax.scatter(y_true, y_pred, alpha=0.5, c='darkorange', edgecolors='k')

    v_min = min(y_true.min(), y_pred.min()) - 2
    v_max = max(y_true.max(), y_pred.max()) + 2
    ax.plot([v_min, v_max], [v_min, v_max], 'k--', alpha=0.5, label='1:1')

    ax.set_title(f'{title_name}')
    ax.set_xlabel('Measured (K)')
    ax.set_ylabel('Inferred (K)')

    res_txt = f"N: {len(y_true)}\nRMSE: {rmse:.2f}K\nBias: {bias:.2f}K\nR: {r_val:.2f}\nRemoved: {removed_count}"
    ax.text(0.05, 0.65, res_txt, transform=ax.transAxes, fontsize=9, bbox=dict(facecolor='white', alpha=0.8))

plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # 留出顶部标题空间
df_stats = pd.DataFrame(stats_list)
df_stats.to_csv(output_stats, index=False)
print(f"处理完成。结果保存至: {output_stats}")
plt.show()


# ================= 5. 打印最终统计汇总 =================
print("\n" + "="*80)
print(f"      反演结果验证汇总表 (站点: {target_site})")
print(f" 时间范围: {START_DATE} 至 {END_DATE}")
print(f" 选择小时: {SELECT_HOURS}")
print(f" 残差阈值: {DIFF_THRESHOLD} K")
print("-" * 80)

if not df_stats.empty:
    # 格式化打印主要指标
    # 使用 to_string(index=False) 去掉行号，让表格更整洁
    print(df_stats[['Task', 'Valid_Count', 'RMSE', 'Bias', 'R']].to_string(
        index=False,
        justify='center',
        formatters={
            'RMSE': '{:,.3f}K'.format,
            'Bias': '{:,.3f}K'.format,
            'R': '{:,.3f}'.format
        }
    ))
else:
    print("警告：没有生成统计结果，请检查数据匹配或过滤条件。")

print("="*80 + "\n")