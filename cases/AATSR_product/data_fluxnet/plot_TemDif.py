import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
from matplotlib.offsetbox import AnchoredText
from scipy import stats
from scipy.optimize import curve_fit
import matplotlib.colors as mcolors
from scipy.ndimage import gaussian_filter

# ================= 配置区域 =================
INPUT_DIR = "/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/Fluxnet_data_Ts0cm/"
OUTPUT_FIG_DIR = os.path.join(INPUT_DIR, "figures")

# 时间筛选
TARGET_HOUR = 11
TARGET_MINUTE = 30

# === 科研绘图风格设置 ===
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 14,
    'axes.linewidth': 1.5,
    'axes.labelsize': 16,
    'axes.titlesize': 16,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.top': True,
    'ytick.right': True,
    'xtick.major.size': 6,
    'ytick.major.size': 6,
    'legend.frameon': False,
    'legend.fontsize': 11,
    'mathtext.default': 'regular'
})

# ================= 辅助函数 =================

def load_and_filter_data(input_dir):
    all_files = glob.glob(os.path.join(input_dir, "*.csv"))
    print(f"Found {len(all_files)} files.")
    data_list = []
    for f in all_files:
        try:
            df = pd.read_csv(f, na_values=['-9999', '-9999.0', -9999, -9999.0])
            required_cols = ['TIMESTAMP_START', 'TA_F', 'TS_F_MDS_1', 'Ts0cm']
            if not set(required_cols).issubset(df.columns): continue
            time_str = df['TIMESTAMP_START'].astype(str)
            hours = time_str.str[-4:-2].astype(int)
            minutes = time_str.str[-2:].astype(int)
            mask_time = (hours == TARGET_HOUR) & (minutes == TARGET_MINUTE)
            df_target = df.loc[mask_time].copy()
            if df_target.empty: continue
            cols_to_keep = ['TA_F', 'TS_F_MDS_1', 'Ts0cm']
            if 'LAI' in df.columns: cols_to_keep.append('LAI')
            else: df_target['LAI'] = np.nan; cols_to_keep.append('LAI')
            data_list.append(df_target[cols_to_keep])
        except Exception as e: continue
    if not data_list: return pd.DataFrame()
    return pd.concat(data_list, ignore_index=True)

def calc_stats(x, y):
    mask = ~np.isnan(x) & ~np.isnan(y)
    x_valid = x[mask]
    y_valid = y[mask]
    if len(x_valid) < 2: return 0, 0, 0, 0
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_valid, y_valid)
    r2 = r_value**2
    rmse = np.sqrt(np.mean((y_valid - x_valid)**2))
    bias = np.mean(y_valid - x_valid)
    return r2, rmse, bias, len(x_valid)

# ================= 1. 定义色带 =================

def create_academic_cmap():
    """选项 1: RdYlBu_r (起始白)"""
    original_cmap = plt.get_cmap('RdYlBu_r')
    colors = original_cmap(np.linspace(0, 1, 256))
    for i in range(5):
        colors[i] = [1, 1, 1, 1]
    return mcolors.LinearSegmentedColormap.from_list("academic_rdylbu_white", colors)

# ================= 2. 拟合线绘制函数 =================

def add_linear_fit(ax, x, y, label, color, style, min_x=None, max_x=None):
    """线性拟合"""
    mask = ~np.isnan(x) & ~np.isnan(y)
    x_valid, y_valid = x[mask], y[mask]
    if len(x_valid) < 10: return
    slope, intercept, _, _, _ = stats.linregress(x_valid, y_valid)
    x_plot_min = x_valid.min() if min_x is None else min_x
    x_plot_max = x_valid.max() if max_x is None else max_x
    x_plot = np.linspace(x_plot_min, x_plot_max, 100)
    y_plot = slope * x_plot + intercept
    ax.plot(x_plot, y_plot, color=color, linestyle=style, linewidth=2, label=label, zorder=10)

def exponential_func(x, a, b, c):
    """指数模型: y = a * exp(b * x) + c"""
    return a * np.exp(b * x) + c

def add_exp_fit(ax, x, y, label, color, style):
    """指数拟合"""
    mask = ~np.isnan(x) & ~np.isnan(y)
    x_valid, y_valid = x[mask], y[mask]
    if len(x_valid) < 10: return
    
    # 初始猜测
    p0 = [np.max(y_valid) - np.min(y_valid), -0.5, np.min(y_valid)]
    
    try:
        popt, pcov = curve_fit(exponential_func, x_valid, y_valid, p0=p0, maxfev=10000)
        x_plot = np.linspace(x_valid.min(), x_valid.max(), 100)
        y_plot = exponential_func(x_plot, *popt)
        ax.plot(x_plot, y_plot, color=color, linestyle=style, linewidth=2, label=label, zorder=10)
    except Exception as e:
        pass

# ================= 3. 主绘图函数 =================

def plot_density_with_fits(ax, x, y, x_label, y_label, title, 
                           plot_range, 
                           fit_config=None, 
                           add_1to1=True, 
                           bins=250, sigma=2.0):
    
    # A. 绘制密度图
    mask = ~np.isnan(x) & ~np.isnan(y)
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) == 0:
        ax.text(0.5, 0.5, "No Data", transform=ax.transAxes, ha='center'); return None

    hist_range = [plot_range[0], plot_range[1]] 
    H, xedges, yedges = np.histogram2d(x_clean, y_clean, bins=bins, range=hist_range)
    H_smoothed = gaussian_filter(H.T, sigma=sigma)
    
    xcenters = (xedges[:-1] + xedges[1:]) / 2
    ycenters = (yedges[:-1] + yedges[1:]) / 2
    X, Y = np.meshgrid(xcenters, ycenters)
    
    custom_cmap = create_academic_cmap()
    levels = np.linspace(H_smoothed.max()*0.005, H_smoothed.max(), 50)
    
    cf = ax.contourf(X, Y, H_smoothed, levels=levels, cmap=custom_cmap, extend='max')

    # B. 绘制拟合线
    if fit_config:
        for item in fit_config:
            sub_mask = item['filter_mask'] & mask 
            if np.sum(sub_mask) > 10:
                if item['type'] == 'linear':
                    add_linear_fit(ax, x[sub_mask], y[sub_mask], item['label'], item['color'], item['style'])
                elif item['type'] == 'exp':
                    add_exp_fit(ax, x[sub_mask], y[sub_mask], item['label'], item['color'], item['style'])

    # C. 装饰
    ax.set_xlim(plot_range[0])
    ax.set_ylim(plot_range[1])

    if add_1to1:
        lims = [np.min([ax.get_xlim(), ax.get_ylim()]), np.max([ax.get_xlim(), ax.get_ylim()])]
        ax.plot(lims, lims, 'k-', alpha=0.3, zorder=5, linewidth=1) 
    else:
        ax.axhline(0, color='k', linestyle='-', linewidth=1, alpha=0.3, zorder=5)

    r2, rmse, bias, n = calc_stats(x_clean, y_clean)
    stats_text = (f"N = {n}\n$R^2$ = {r2:.2f}\nRMSE = {rmse:.2f}\nBias = {bias:.2f}")
    at = AnchoredText(stats_text, prop=dict(size=12), frameon=True, loc='upper left')
    at.patch.set_boxstyle("round,pad=0.3,rounding_size=0.1")
    at.patch.set_alpha(0.9)
    ax.add_artist(at)
    
    if fit_config:
        ax.legend(loc='lower right', framealpha=0.9, fontsize=10)

    ax.set_xlabel(x_label, fontweight='bold', labelpad=10)
    ax.set_ylabel(y_label, fontweight='bold', labelpad=10)
    ax.set_title(title, fontweight='bold', pad=15)
    ax.grid(True, linestyle=':', alpha=0.3)

    return cf

# ================= 主程序 =================

def main():
    if not os.path.exists(OUTPUT_FIG_DIR): os.makedirs(OUTPUT_FIG_DIR)
    print("Step 1: Loading data...")
    df = load_and_filter_data(INPUT_DIR)
    if df.empty: print("Dataset is empty."); return
    
    Ta = df['TA_F'].values
    Ts_5cm = df['TS_F_MDS_1'].values 
    Ts_0cm = df['Ts0cm'].values       
    LAI = df['LAI'].values
    LAI_scaled = LAI / 1000.0

    mask_Ta_positive = Ta > 0 
    
    # ================= 图 1: Ts vs Ta (保持不变) =================
    print("Step 2: Plotting Figure 1...")
    fig1, axs1 = plt.subplots(1, 2, figsize=(14, 7.5)) 
    temp_range = ((-40, 45), (-40, 45)) 

    fit_conf_fig1 = [
        {
            'filter_mask': mask_Ta_positive & (LAI_scaled <= 0.5),
            'label': r'LAI $\leq$ 0.5 ($T_a > 0$)',
            'color': 'black', 'style': '--', 'type': 'linear'
        },
        {
            'filter_mask': mask_Ta_positive & (LAI_scaled > 1) & (LAI_scaled < 2),
            'label': r'1 < LAI < 2 ($T_a > 0$)',
            'color': 'black', 'style': '-', 'type': 'linear'
        },
        {
            'filter_mask': mask_Ta_positive & (LAI_scaled > 4),
            'label': r'LAI > 4 ($T_a > 0$)',
            'color': 'black', 'style': ':', 'type': 'linear'
        }
    ]

    cf1 = plot_density_with_fits(axs1[0], Ta, Ts_5cm,
                                 x_label=r'Air Temperature ($T_a$) [°C]', 
                                 y_label=r'Soil Temp @ 5cm ($T_{s,5cm}$) [°C]', 
                                 title=r'(a) $T_{s,5cm}$ vs $T_a$', 
                                 plot_range=temp_range, fit_config=fit_conf_fig1)
    
    cf2 = plot_density_with_fits(axs1[1], Ta, Ts_0cm,
                                 x_label=r'Air Temperature ($T_a$) [°C]', 
                                 y_label=r'Surface Temp ($T_{s,0cm}$) [°C]', 
                                 title=r'(b) $T_{s,0cm}$ vs $T_a$', 
                                 plot_range=temp_range, fit_config=fit_conf_fig1)
    
    if cf1:
        cbar_ax = fig1.add_axes([0.25, 0.05, 0.5, 0.025])
        cbar = fig1.colorbar(cf1, cax=cbar_ax, orientation='horizontal')
        cbar.set_label('Density', fontsize=12)
        cbar.outline.set_linewidth(0.5)

    plt.subplots_adjust(bottom=0.18, wspace=0.25)
    plt.savefig(os.path.join(OUTPUT_FIG_DIR, "Fig1_Temp_Fitted.png"), dpi=300, bbox_inches='tight')
    
    # ================= 图 2: Ts 分组 (0, 15, 30度, +-5) =================
    print("Step 3: Plotting Figure 2 with 0, 15, 30 (+-5)...")
    fig2, axs2 = plt.subplots(1, 2, figsize=(14, 7.5))
    
    delta_T_5cm = Ts_5cm - Ta
    delta_T_0cm = Ts_0cm - Ta
    dt_range = ((0, 6.5), (-10, 35))

    # --- 左图配置: 使用 Ts_5cm ---
    # 范围: (-5, 5), (10, 20), (25, 35)
    fit_conf_fig2_5cm = [
        {
            'filter_mask': (Ts_5cm > -5) & (Ts_5cm < 5),
            'label': r'$T_s = 0^\circ$C ($\pm 5$)',
            'color': 'black', 'style': '--', 'type': 'exp'
        },
        {
            'filter_mask': (Ts_5cm > 10) & (Ts_5cm < 20),
            'label': r'$T_s = 15^\circ$C ($\pm 5$)',
            'color': 'black', 'style': '-', 'type': 'exp'
        },
        {
            'filter_mask': (Ts_5cm > 25) & (Ts_5cm < 35),
            'label': r'$T_s = 30^\circ$C ($\pm 5$)',
            'color': 'black', 'style': ':', 'type': 'exp'
        }
    ]

    # --- 右图配置: 使用 Ts_0cm ---
    fit_conf_fig2_0cm = [
        {
            'filter_mask': (Ts_0cm > -5) & (Ts_0cm < 5),
            'label': r'$T_s = 0^\circ$C ($\pm 5$)',
            'color': 'black', 'style': '--', 'type': 'exp'
        },
        {
            'filter_mask': (Ts_0cm > 10) & (Ts_0cm < 20),
            'label': r'$T_s = 15^\circ$C ($\pm 5$)',
            'color': 'black', 'style': '-', 'type': 'exp'
        },
        {
            'filter_mask': (Ts_0cm > 25) & (Ts_0cm < 35),
            'label': r'$T_s = 30^\circ$C ($\pm 5$)',
            'color': 'black', 'style': ':', 'type': 'exp'
        }
    ]

    # 绘图 A
    cf_dt1 = plot_density_with_fits(axs2[0], LAI_scaled, delta_T_5cm,
                                    x_label=r'Leaf Area Index (LAI)', 
                                    y_label=r'$T_{s,5cm} - T_a$ [°C]', 
                                    title=r'(a) $\Delta T_{5cm}$ vs LAI', 
                                    plot_range=dt_range, add_1to1=False, 
                                    fit_config=fit_conf_fig2_5cm)
        
    # 绘图 B
    cf_dt2 = plot_density_with_fits(axs2[1], LAI_scaled, delta_T_0cm,
                                    x_label=r'Leaf Area Index (LAI)', 
                                    y_label=r'$T_{s,0cm} - T_a$ [°C]', 
                                    title=r'(b) $\Delta T_{0cm}$ vs LAI', 
                                    plot_range=dt_range, add_1to1=False, 
                                    fit_config=fit_conf_fig2_0cm)

    if cf_dt1:
        cbar_ax2 = fig2.add_axes([0.25, 0.05, 0.5, 0.025])
        cbar2 = fig2.colorbar(cf_dt1, cax=cbar_ax2, orientation='horizontal')
        cbar2.set_label('Density', fontsize=12)
        cbar2.outline.set_linewidth(0.5)

    plt.subplots_adjust(bottom=0.18, wspace=0.25)
    save_path2 = os.path.join(OUTPUT_FIG_DIR, "Fig2_DeltaT_Fitted_Exp_0_15_30.png")
    plt.savefig(save_path2, dpi=300, bbox_inches='tight')
    print(f"Fig 2 Saved to: {save_path2}")

    print("All Done.")

if __name__ == "__main__":
    main()