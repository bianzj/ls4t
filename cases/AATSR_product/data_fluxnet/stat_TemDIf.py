import pandas as pd
import numpy as np
import glob
import os
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, linregress
from sklearn.metrics import mean_squared_error

# ================= 配置区域 =================
INPUT_DIR = "/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/Fluxnet_data/processed_Ts0cm_new/"
OUTPUT_FIG = os.path.join(INPUT_DIR, "Scatter_Density_Ts0cm_Hampel_Filter.png")
OUTPUT_CSV = os.path.join(INPUT_DIR, "Validation_Stats_Hampel.csv")

# 时间筛选
TARGET_HOUR = 12
TARGET_MINUTE = 0

# 物理范围筛选 (Celsius)
VALID_MIN = -20
VALID_MAX = 80

# ================= 核心算法: Hampel Identifier =================

def apply_hampel_filter(series, n_sigma=3.0):
    """
    使用 Hampel Identifier 进行稳健的异常值检测 (Davies and Gather, 1993)
    公式: S = 1.4826 * median(|xi - xm|)
    保留条件: |xi - xm| <= n_sigma * S
    """
    # 1. 计算中位数 (xm)
    xm = series.median()
    
    # 2. 计算绝对中位差 (MAD)
    mad = np.abs(series - xm).median()
    
    # 3. 估计标准差 (S)
    # 1.4826 是高斯分布下 MAD 转 Std 的无偏估计系数
    S = 1.4826 * mad
    
    # 4. 判断离群点
    threshold = n_sigma * S
    is_valid = np.abs(series - xm) <= threshold
    
    stats = {
        'median': xm,
        'MAD': mad,
        'estimated_sigma': S,
        'threshold': threshold
    }
    
    return is_valid, stats

# ================= 辅助函数 =================

def load_and_filter_data(input_dir):
    all_files = glob.glob(os.path.join(input_dir, "*.csv"))
    print(f"Found {len(all_files)} files.")
    
    data_list = []
    
    for f in all_files:
        try:
            df = pd.read_csv(f, na_values=['-9999', '-9999.0', -9999, -9999.0])
            
            fvc_col = None
            if 'FVC' in df.columns: fvc_col = 'FVC'
            elif 'fvc' in df.columns: fvc_col = 'fvc'
            elif 'LAI' in df.columns: fvc_col = 'LAI' 
            
            if fvc_col is None: continue

            cols_needed = ['TIMESTAMP_START', 'LST', 'fvc_30', 'Ts0cm', 'TS_F_MDS_1', fvc_col]
            if not set(cols_needed).issubset(df.columns): continue

            time_str = df['TIMESTAMP_START'].astype(str)
            hours = time_str.str[-4:-2].astype(int)
            minutes = time_str.str[-2:].astype(int)
            mask_time = (hours == TARGET_HOUR) & (minutes == TARGET_MINUTE)
            df_target = df.loc[mask_time].copy()
            
            if df_target.empty: continue
            
            cols = ['LST', 'fvc_30', 'Ts0cm', 'TS_F_MDS_1', fvc_col]
            df_sub = df_target[cols].copy()
            df_sub.rename(columns={fvc_col: 'FVC_Site'}, inplace=True)
            
            df_sub.dropna(inplace=True)
            if not df_sub.empty:
                data_list.append(df_sub)
                
        except Exception:
            continue
            
    if not data_list: return pd.DataFrame()
    return pd.concat(data_list, ignore_index=True)

def calc_stats(x, y):
    rmse = np.sqrt(mean_squared_error(x, y))
    bias = np.mean(y - x)
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    r2 = r_value**2
    return rmse, bias, r2, len(x)

def plot_scatter_density(ax, x, y, title, xlabel, ylabel):
    # 计算密度
    xy = np.vstack([x, y])
    z = gaussian_kde(xy)(xy)
    idx = z.argsort()
    x, y, z = x.iloc[idx], y.iloc[idx], z[idx]
    
    # 绘图
    sc = ax.scatter(x, y, c=z, s=15, cmap='Spectral_r', edgecolor=None, alpha=0.8)
    
    # 1:1 线
    lims = [np.min([ax.get_xlim(), ax.get_ylim()]), np.max([ax.get_xlim(), ax.get_ylim()])]
    ax.plot(lims, lims, 'k--', alpha=0.75, zorder=0)
    
    # 统计信息
    rmse, bias, r2, n = calc_stats(x, y)
    stats_text = (f"N = {n}\n"
                  f"RMSE = {rmse:.2f} K\n"
                  f"Bias = {bias:.2f} K\n"
                  f"$R^2$ = {r2:.2f}")
    
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, linestyle=':', alpha=0.6)
    return sc

# ================= 主程序 =================

print("Step 1: Loading data...")
df = load_and_filter_data(INPUT_DIR)

if not df.empty:
    # 1. 自动转换 LST 单位并进行范围筛选
    if df['LST'].mean() > 200:
        df['LST_C'] = df['LST'] - 273.15
    else:
        df['LST_C'] = df['LST']

    # 【新增】Step 2: 物理范围筛选 (-20 ~ 80)
    print(f"\nApplying Physical Range Filter [{VALID_MIN}, {VALID_MAX}]...")
    initial_len = len(df)
    mask_range = (df['Ts0cm'] >= VALID_MIN) & (df['Ts0cm'] <= VALID_MAX) & \
                 (df['LST_C'] >= VALID_MIN) & (df['LST_C'] <= VALID_MAX)
    df = df[mask_range].copy()
    print(f"Removed {initial_len - len(df)} points out of range.")

    # 【新增】Step 3: Hampel Identifier 3-Sigma 剔除
    print("\nApplying Hampel Identifier (Robust 3-Sigma)...")
    df['Diff'] = df['LST_C'] - df['Ts0cm']
    
    mask_hampel, stats = apply_hampel_filter(df['Diff'], n_sigma=3.0)
    df_clean = df[mask_hampel].copy()
    
    print(f"  > Median of Diff (xm): {stats['median']:.4f}")
    print(f"  > MAD: {stats['MAD']:.4f}")
    print(f"  > Estimated Sigma (S): {stats['estimated_sigma']:.4f}")
    print(f"  > Threshold (3*S): {stats['threshold']:.4f}")
    print(f"Removed {len(df) - len(df_clean)} outliers using Hampel filter.")

    # 4. 应用裸土筛选条件 (fvc_30 < 0.05 & FVC_Site < 3000)
    mask_condition = (df_clean['fvc_30'] < 0.05) & (df_clean['FVC_Site'] < 3000)
    df_plot = df_clean[mask_condition].copy()
    
    print(f"\nFinal Count for Bare Soil Validation: {len(df_plot)}")
    
    if not df_plot.empty:
        fig, axes = plt.subplots(1, 2, figsize=(16, 7.5))
        
        # --- 左图: 反演结果 vs LST ---
        sc1 = plot_scatter_density(axes[0], df_plot['LST_C'], df_plot['Ts0cm'], 
                                   r'(a) Inverted $T_{s,0cm}$ vs LST (Hampel Filtered)', 
                                   r'LST (Observed) [°C]', r'Inverted $T_{s,0cm}$ [°C]')
        
        # --- 右图: 原始5cm土温 vs LST ---
        sc2 = plot_scatter_density(axes[1], df_plot['LST_C'], df_plot['TS_F_MDS_1'], 
                                   r'(b) Original $T_{s,5cm}$ vs LST', 
                                   r'LST (Observed) [°C]', r'Original $T_{s,5cm}$ [°C]')
        
        # Colorbar
        cbar_ax = fig.add_axes([0.15, 0.05, 0.7, 0.025])
        cbar = fig.colorbar(sc1, cax=cbar_ax, orientation='horizontal')
        cbar.set_label('Point Density (Gaussian KDE)', fontsize=12)
        
        plt.subplots_adjust(bottom=0.15)
        plt.suptitle(f"Bare Soil Validation (fvc_30<0.05, FVC<3000, 3$\sigma$-Hampel)", fontsize=16, y=0.98)
        
        plt.savefig(OUTPUT_FIG, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {OUTPUT_FIG}")
        
        # 保存统计结果 CSV
        df_plot.to_csv(OUTPUT_CSV, index=False)
        print(f"Data saved to: {OUTPUT_CSV}")
        
        plt.show()
    else:
        print("No data points satisfy all conditions.")
else:
    print("Failed to load data.")