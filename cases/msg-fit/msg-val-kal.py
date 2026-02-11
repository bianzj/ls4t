import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from scipy import stats
import math
from base.util_phys import *

# ================= 1. 配置参数 =================
file_fitting = "/Users/bianzj/Downloads/data/msg/PRODUCTS/SITE/ALL_SITES_LST_FITTING_RESULTS.csv"
file_measured = "/Users/bianzj/Downloads/data/stations/Kal-2017.csv"
output_stats = "/Users/bianzj/Downloads/data/msg/PRODUCTS/Validation_Stats_KAL_Nadir.csv"

target_site = "KAL"
START_DATE = '2017-08-01'
END_DATE = '2017-12-31'
SELECT_HOURS = [h for h in range(9, 16)]
DIFF_THRESHOLD = 5.0  # 剔除异常残差的阈值
Tsky = 270
emis_v = 0.985
emis_s = 0.975


# 验证任务列表
tasks = [
    ('LST_obs_E', 'Original LST (Sensor E)'),
    ('LST_obs_I', 'Original LST (Sensor I)'),
    ('LST_nadir_DTC', 'Nadir DTC'),
    ('LST_nadir_DTCRL', 'Nadir DTCRL'),
    ('LST_nadir_DTCLSFRL', 'Nadir DTCLSFRL')
]

# ================= 2. 处理拟合数据 =================
df_all = pd.read_csv(file_fitting)
df_inf = df_all[df_all['site'] == target_site].copy()

# 转换时间：date (str) + local_time (float hours)
df_inf['DateTime'] = pd.to_datetime(df_inf['date']) + pd.to_timedelta(df_inf['local_time'], unit='h')
df_inf['DateTime'] = df_inf['DateTime'].dt.round('1min')  # 对齐到分钟

# ================= 3. 处理 KAL 实测数据 =================
df_mea = pd.read_csv(file_measured)
# KAL 的时间列名通常是 'time'
df_mea['DateTime'] = pd.to_datetime(df_mea['time'], dayfirst=True).dt.round('1min')

# 自动处理摄氏度转开尔文
for col in ['bt_s', 'bt_v']:
    if col in df_mea.columns:
        if df_mea[col].mean() < 150:
            df_mea[col] += 273.15

# ================= 4. 合并与计算参考 LST =================
df_merge = pd.merge(df_inf, df_mea, on='DateTime')

bg = planck(10.5,df_merge['bt_s'])
bv = planck(10.5,df_merge['bt_v'])
bsky = planck(10.5,250)
df_merge['bt_S'] = inv_planck(10.5,(bg-(1-emis_s)*bsky)/emis_s)
df_merge['bt_v'] = inv_planck(10.5,(bv-(1-emis_v)*bsky)/emis_v)



# 使用 LAI 计算植被覆盖度 fc，合成参考 LST
df_merge['fc'] = 1 - np.exp(-0.5 * df_merge['LAI'])
df_merge['LST_Ref'] = df_merge['fc'] * df_merge['bt_v'] + (1 - df_merge['fc']) * df_merge['bt_s']
# df_merge['LST_Ref'] = (df_merge['fc'] * (df_merge['bt_v']**4) + (1 - df_merge['fc']) * (df_merge['bt_s']**4))**(1/4)
# 执行过滤
df_merge = df_merge[(df_merge['DateTime'] >= START_DATE) & (df_merge['DateTime'] <= END_DATE)]
df_merge = df_merge[df_merge['DateTime'].dt.hour.isin(SELECT_HOURS)]

if df_merge.empty:
    print(f"站点 {target_site} 未能匹配到有效数据，请检查路径和时间设置。")
    exit()

# 准备绘图宽表：区分传感器 E 和 I
df_e = df_merge[df_merge['sensor'] == 'E'].rename(columns={'LST_obs': 'LST_obs_E'})
df_i = df_merge[df_merge['sensor'] == 'I'].rename(columns={'LST_obs': 'LST_obs_I'})

# 合并 E 和 I 的观测以便在同一个时间轴验证
df_plot = pd.merge(
    df_e[['DateTime', 'LST_Ref', 'LST_obs_E', 'LST_nadir_DTC', 'LST_nadir_DTCRL', 'LST_nadir_DTCLSFRL']],
    df_i[['DateTime', 'LST_obs_I']],
    on='DateTime', how='inner'
)

# ================= 5. 统计与绘图 =================
stats_list = []
plt.figure(figsize=(16, 10))
plt.suptitle(
    f"KAL Site Validation | Period: {START_DATE} to {END_DATE} | Hours: {SELECT_HOURS}\nReference LST = fc*bt_v + (1-fc)*bt_s",
    fontsize=16)

for i, (col_name, title) in enumerate(tasks):
    y_true = df_plot['LST_Ref']
    y_pred = df_plot[col_name]

    # 有效性掩码
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    valid_mask = mask & (np.abs(y_true - y_pred) <= DIFF_THRESHOLD)

    y_t = y_true[valid_mask]
    y_p = y_pred[valid_mask]

    if len(y_t) < 5:
        print(f"任务 {title} 有效数据太少({len(y_t)})，跳过。")
        continue

    # 指标计算
    bias = np.mean(y_p - y_t)
    rmse = np.sqrt(mean_squared_error(y_t, y_p))
    r_val, _ = stats.pearsonr(y_t, y_p)

    stats_list.append({
        'Task': title, 'RMSE': rmse, 'Bias': bias, 'R': r_val, 'Count': len(y_t)
    })

    # 画图
    ax = plt.subplot(2, 3, i + 1)
    ax.scatter(y_t, y_p, alpha=0.6, c='royalblue', edgecolors='w', s=30)

    # 1:1线
    limit_min = min(y_t.min(), y_p.min()) - 2
    limit_max = max(y_t.max(), y_p.max()) + 2
    ax.plot([limit_min, limit_max], [limit_min, limit_max], 'r--', lw=1.5)

    ax.set_title(title, fontsize=12)
    ax.set_xlabel('Reference LST (K)')
    ax.set_ylabel('Result LST (K)')

    stats_text = f"N: {len(y_t)}\nRMSE: {rmse:.2f}K\nBias: {bias:.2f}K\nR: {r_val:.2f}"
    ax.text(0.05, 0.70, stats_text, transform=ax.transAxes, fontsize=10,
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray'))

plt.tight_layout(rect=[0, 0.03, 1, 0.93])
df_res = pd.DataFrame(stats_list)
df_res.to_csv(output_stats, index=False)
plt.show()

# ================= 6. 输出汇总表 =================
print("\n" + "=" * 70)
print(f"            KAL 站点验证汇总 (Nadir vs Reference)")
print("-" * 70)
print(df_res.to_string(index=False, formatters={
    'RMSE': '{:,.2f}K'.format,
    'Bias': '{:,.2f}K'.format,
    'R': '{:,.3f}'.format
}))
print("=" * 70)