import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score
from scipy import stats
import math
from base.util_phys import *

# ================= 配置参数 =================
indir = "/media/hero/MSG/"
file_inferred = indir + "/PRODUCTS/LSCT_Site_Results.csv"
file_measured = indir + "/field/Evo-2017.csv"
output_stats = indir + "/PRODUCTS/LSCT_Validation_Stats_Evora.csv"

# --- 新增：时间选择设定 ---
START_DATE = '2017-08-01'  # 开始日期 (包含)
END_DATE   = '2017-12-31'  # 结束日期 (包含)
SELECT_HOURS = [10, 11, 12, 13, 14, 15,16] # 只选 10:00 到 16:00 的数据

# 设定残差阈值（单位：K）
DIFF_THRESHOLD = 12.0
target_site = "Evora"
Tsky = 250
emis_v = 0.975
emis_s = 0.975

tasks = [
    ('T_Sunlit_Soil', 'Ts', 'Soil'),
    ('T_Vegetation', 'Tcrown', 'Vegetation'),
    ('LST_Euro', 'Ts', 'LST vs Ts'),
    ('LST_Euro', 'Tcrown', 'LST vs Vegetation')
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

# ================= 3. 数据匹配与时间过滤 =================
df_merge = pd.merge(df_inf, df_mea, on='DateTime', suffixes=('_inf', '_mea'))

# --- 核心新增：执行时间过滤 ---
# 1. 过滤日期区间
df_merge = df_merge[(df_merge['DateTime'] >= START_DATE) & (df_merge['DateTime'] <= END_DATE)]

# 2. 过滤小时段
df_merge = df_merge[df_merge['DateTime'].dt.hour.isin(SELECT_HOURS)]

if df_merge.empty:
    print(f"未能匹配到数据！请检查日期范围 {START_DATE} ~ {END_DATE} 及小时设定 {SELECT_HOURS}")
    exit()

print(f"过滤后剩余有效样本数: {len(df_merge)}")


bg = planck(10.5,df_merge['Ts'])
bv = planck(10.5,df_merge['Tcrown'])
bsky = planck(10.5,250)
df_merge['Ts'] = inv_planck(10.5,(bg-(1-emis_s)*bsky)/emis_s)-273.15
df_merge['Tcrown'] = inv_planck(10.5,(bv-(1-emis_v)*bsky)/emis_v)-273.15


# ================= 4. 统计与绘图 =================
stats_list = []
cols_plot = 2
rows_plot = math.ceil(len(tasks) / cols_plot)
plt.figure(figsize=(10, 5 * rows_plot))

# 在总标题显示时间范围
plt.suptitle(f"Site: {target_site} | Period: {START_DATE} to {END_DATE} | Hours: {SELECT_HOURS}", fontsize=16)

for i, (inf_col, mea_col, title_name) in enumerate(tasks):
    mask = (df_merge[inf_col].notna()) & (df_merge[mea_col].notna())
    abs_diff = np.abs(df_merge[inf_col] - df_merge[mea_col])
    valid_mask = mask & (abs_diff <= DIFF_THRESHOLD)

    y_true = df_merge.loc[valid_mask, mea_col]
    y_pred = df_merge.loc[valid_mask, inf_col]
    removed_count = np.sum(mask) - np.sum(valid_mask)

    if len(y_true) < 2:
        print(f"任务 {title_name} 在此时间段内有效数据不足。")
        continue

    bias = np.mean(y_pred - y_true)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r_val, _ = stats.pearsonr(y_true, y_pred)

    stats_list.append({
        'Task': title_name,
        'Bias': bias, 'RMSE': rmse, 'R': r_val,
        'Valid_Count': len(y_true)
    })

    ax = plt.subplot(rows_plot, cols_plot, i + 1)
    ax.scatter(y_true, y_pred, alpha=0.5, c='darkorange', edgecolors='k')

    v_min = min(y_true.min(), y_pred.min()) - 2
    v_max = max(y_true.max(), y_pred.max()) + 2
    ax.plot([v_min, v_max], [v_min, v_max], 'k--', alpha=0.5)

    ax.set_title(f'{title_name}')
    ax.set_xlabel('Measured (K)')
    ax.set_ylabel('Inverted (K)')

    res_txt = f"N: {len(y_true)}\nRMSE: {rmse:.2f}K\nBias: {bias:.2f}K\nR: {r_val:.2f}\nExcluded: {removed_count}"
    ax.text(0.05, 0.65, res_txt, transform=ax.transAxes, fontsize=9, bbox=dict(facecolor='white', alpha=0.8))

plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # 为总标题留出空间
df_stats = pd.DataFrame(stats_list)
df_stats.to_csv(output_stats, index=False)
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