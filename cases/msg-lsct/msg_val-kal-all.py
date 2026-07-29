import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score
from scipy import stats
import math
from base.util_phys import *

# ================= 配置参数 =================
file_inferred = "/Users/bianzj/Downloads/data/msg/PRODUCTS/LSCT_Site_Results.csv"
file_measured = "/Users/bianzj/Downloads/data/msg/field/Kal-2017.csv"
output_stats = "/Users/bianzj/Downloads/data/msg/PRODUCTS/LSCT_Validation_Stats_KAL.csv"

# --- 时间选择设定 ---
START_DATE = '2017-08-01'  # 设定起始日期 (包含)
END_DATE = '2017-12-31'  # 设定结束日期 (包含)
SELECT_HOURS = [9, 10, 11, 12, 13, 14, 15]  # 设定小时区间

# 设定残差阈值（单位：K）
DIFF_THRESHOLD = 15.0
target_site = "KAL"
Tsky = 250
emis_v = 0.975
emis_s = 0.965

# 格式：(反演列名, 实测列名, 显示标题)
tasks = [
    ('T_Sunlit_Soil', 'bt_s', 'Sunlit Soil vs bt_s'),
    ('T_Vegetation', 'bt_v', 'Vegetation vs bt_v'),
    ('LST_Euro', 'bt_s', 'LST Euro vs bt_s'),
    ('LST_Euro', 'bt_v', 'LST Euro vs bt_v')
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
# 规整到最近的 5 分钟，并做一次均值去重

df_mea = df_mea.groupby('DateTime', as_index=False).mean(numeric_only=True)

# 自动处理摄氏度转开尔文
measured_cols = list(set([t[1] for t in tasks]))
for col in measured_cols:
    if col in df_mea.columns:
        if df_mea[col].mean() < 150:
            df_mea[col] = df_mea[col] + 273.15

# ================= 3. 数据匹配与时间过滤 =================
df_merge = pd.merge(df_inf, df_mea, on='DateTime', suffixes=('_inf', '_mea'))

# 过滤日期范围
df_merge = df_merge[(df_merge['DateTime'] >= START_DATE) &
                    (df_merge['DateTime'] <= END_DATE) &
                    (df_merge['LAI'] >= 0.25)]
# 过滤特定小时
if SELECT_HOURS:
    df_merge = df_merge[df_merge['DateTime'].dt.hour.isin(SELECT_HOURS)]

if df_merge.empty:
    print(f"未能匹配到数据！请检查日期范围 {START_DATE}~{END_DATE} 或小时设定 {SELECT_HOURS}")
    exit()

print(f"匹配与时间过滤完成，初始样本数: {len(df_merge)}")

# 辐射校正
bg = planck(10.5, df_merge['bt_s'])
bv = planck(10.5, df_merge['bt_v'])
bsky = planck(10.5, 250)
df_merge['bt_s'] = inv_planck(10.5, (bg - (1 - emis_s) * bsky) / emis_s)
df_merge['bt_v'] = inv_planck(10.5, (bv - (1 - emis_v) * bsky) / emis_v)

# ================= 4. 提取完全一致的公共数据点 =================
# 【核心修正】：先执行全局过滤，获取共同交集数据集 df_common
global_valid_mask = pd.Series(True, index=df_merge.index)

for inf_col, mea_col, _ in tasks:
    not_na_mask = df_merge[inf_col].notna() & df_merge[mea_col].notna()
    abs_diff = np.abs(df_merge[inf_col] - df_merge[mea_col])
    threshold_mask = abs_diff <= DIFF_THRESHOLD

    global_valid_mask = global_valid_mask & not_na_mask & threshold_mask

df_common = df_merge[global_valid_mask].copy()

print(f"经过严苛交集过滤后，所有任务共同拥有的有效样本数: {len(df_common)}")
if df_common.empty:
    print("警告：没有共同的有效数据点，无法画图！请检查数据或放宽残差阈值。")
    exit()

# ================= 5. 基于公共数据点画图与统计 =================
stats_list = []
cols_plot = 2
rows_plot = math.ceil(len(tasks) / cols_plot)
plt.figure(figsize=(12, 5 * rows_plot))

# 标题显示全局统一的 N 值
plt.suptitle(
    f"Site: {target_site} | {START_DATE} to {END_DATE} | Hours: {SELECT_HOURS}\nStrict Intersection (N = {len(df_common)})",
    fontsize=14, fontweight='bold')

for i, (inf_col, mea_col, title_name) in enumerate(tasks):
    # 【核心修正】：直接从 df_common 获取数据，不需要再次掩码过滤
    y_true = df_common[mea_col]
    y_pred = df_common[inf_col]

    bias = np.mean(y_pred - y_true)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r_val, _ = stats.pearsonr(y_true, y_pred)

    stats_list.append({
        'Task': title_name,
        'Bias': bias, 'RMSE': rmse, 'R': r_val,
        'Valid_Count': len(y_true)
    })

    # 画散点图
    ax = plt.subplot(rows_plot, cols_plot, i + 1)
    ax.scatter(y_true, y_pred, alpha=0.6, c='darkorange', edgecolors='k', s=25)

    # 画 1:1 线
    v_min = min(y_true.min(), y_pred.min()) - 2
    v_max = max(y_true.max(), y_pred.max()) + 2
    ax.plot([v_min, v_max], [v_min, v_max], 'k--', alpha=0.6, label='1:1')

    # 图表设置 (强制 XY 轴范围一致)
    ax.set_title(f'{title_name}', fontweight='bold')
    ax.set_xlabel('Measured (K)')
    ax.set_ylabel('Inferred (K)')
    ax.set_xlim(v_min, v_max)
    ax.set_ylim(v_min, v_max)

    # 文本框 (去掉了 Excluded，因为全局交集下，剔除的数量是整体的，不局限于单张图)
    res_txt = f"N: {len(y_true)}\nRMSE: {rmse:.2f} K\nBias: {bias:.2f} K\nR: {r_val:.2f}"
    ax.text(0.05, 0.70, res_txt, transform=ax.transAxes, fontsize=10,
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

plt.tight_layout(rect=[0, 0.03, 1, 0.93])  # 为总标题留出空间
df_stats = pd.DataFrame(stats_list)
df_stats.to_csv(output_stats, index=False)
plt.show()

# ================= 6. 打印最终统计汇总 =================
print("\n" + "=" * 80)
print(f"      反演结果验证汇总表 (严格交集控制变量) (站点: {target_site})")
print(f" 时间范围: {START_DATE} 至 {END_DATE}")
print(f" 选择小时: {SELECT_HOURS}")
print(f" 残差阈值: {DIFF_THRESHOLD} K")
print("-" * 80)

if not df_stats.empty:
    print(df_stats[['Task', 'Valid_Count', 'RMSE', 'Bias', 'R']].to_string(
        index=False,
        justify='center',
        formatters={
            'RMSE': '{:,.3f} K'.format,
            'Bias': '{:,.3f} K'.format,
            'R': '{:,.3f}'.format
        }
    ))
else:
    print("警告：没有生成统计结果。")

print("=" * 80 + "\n")