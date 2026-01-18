import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from scipy import stats
import seaborn as sns
from matplotlib.gridspec import GridSpec

from pvlib.location import Location
import pvlib

from base.util_lst import *
from base.util_data import *
from base.util_fitting import *
from base.util_kernel import *
from base.util_file import *
from base.rt.hom import *

# ==============================
# 常量与路径
# ==============================
deg2rad = np.pi / 180
altitude = 0

indir = r"/Users/bianzj/Downloads/data/msg/"
indir0 = r"/Users/bianzj/Downloads/data/msg/output/"

# ==============================
# 站点信息
# ==============================
infile = os.path.join(indir, "sites.txt")
site_info = read_txt_str(infile, r",")

site_name = np.asarray([_[0] for _ in site_info])
lat_ = np.asarray([_[1] for _ in site_info], dtype=float)
lon_ = np.asarray([_[2] for _ in site_info], dtype=float)

# ==============================
# 情景参数
# ==============================
ksm = 0.25
klai = 2.0

kyear = 2025
kmonth = 6
kday = 1
ndays = 27

# 观测参数
klai0 = 2.0
hspot = 0.35
wl = 10.5

emissivity_soil = 0.955
emissivity_leaf = 0.97

# GEO 两个观测角度
vza = np.asarray([28.29, 42.12])
vaa = np.asarray([-38.73 + 360, 61.56])

# ==============================
# 初始化 HOM
# ==============================
hom = Hom()
hom.set_structure(klai0, hspot)
hom.set_optical(wl, emissivity_soil, emissivity_leaf)

# ==============================
# 读取温度驱动数据
# ==============================
indir_case = os.path.join(
    indir0,
    f"F_2025_LAI{klai:.1f}_SMC{ksm:.2f}"
)
temp_file = os.path.join(indir_case, "surftemp.dat")
temps = read_txt_array(temp_file, 0, 11)

# ==============================
# GEO 模拟
# ==============================
obs_all = []

ksite = 5

for day_offset in range(ndays):
    cur_date = pd.Timestamp(kyear, kmonth, kday) + pd.Timedelta(days=day_offset)
    kdoy = date2DOY(cur_date.year, cur_date.month, cur_date.day)

    site = Location(lat_[ksite], lon_[ksite], 'Etc/GMT', altitude, 'None')

    for khh in range(1, 24):
        for kmm in range(0, 60, 15):

            khhh = khh + 1
            if khhh >= 24: khhh = khh
            time_temp = pd.date_range(
                f"{cur_date:%Y-%m-%d} {khhh:02d}:{kmm:02d}:00",
                periods=1, freq='15min', tz='UTC'
            )

            solpos = pvlib.solarposition.get_solarposition(
                time_temp,
                site.latitude,
                site.longitude,
                site.altitude,
                method='nrel_numpy'
            )

            sza = min(solpos['zenith'].values[0], 85.0)
            saa = solpos['azimuth'].values[0]

            hour_frac = khh + kmm / 60.0
            ktime = kdoy + hour_frac / 24.0

            ind = np.where(np.abs(temps[:, 2] - ktime) < 0.001)[0]
            if len(ind) == 0:
                continue

            compts = temps[ind[0], 4:8] + 273.15
            hom.set_thermal(compts[1], compts[0], compts[2], compts[3])

            raa = np.abs(vaa - saa)
            hom.set_angle(vza, sza, raa)

            obs = hom.run()

            for isat in range(2):
                obs_all.append([kdoy, hour_frac, isat, vza[isat], vaa[isat], sza, saa, obs[isat]])

obs_all = np.asarray(obs_all)

# ==============================
# POLAR 模拟
# ==============================
polar_file = os.path.join(indir, "TRISHNA_simul_orbit_Faidherbia.dat")
polar = read_txt_float(polar_file)

# 0 month | 1 day | 2 hour | 3 minute | 4 SZA | 5 SAA | 6 VZA | 7 VAA
polar = polar[polar[:, 0] == 6]

polar_obs = []

for row in polar:
    month, day, hour, minute, sza, saa, vza_p, vaa_p = row
    cur_date = pd.Timestamp(kyear, int(month), int(day))
    doy = date2DOY(cur_date.year, cur_date.month, cur_date.day)

    hour_frac = hour + minute / 60.0
    ktime = doy + hour_frac / 24.0

    dt = temps[:, 2] - ktime
    ind_exact = np.where(np.abs(dt) < 0.001)[0]

    if len(ind_exact) > 0:
        compts = temps[ind_exact[0], 4:8] + 273.15
    else:
        ind_before = np.where(dt < 0)[0]
        ind_after = np.where(dt > 0)[0]
        if len(ind_before) == 0 or len(ind_after) == 0:
            continue
        i1 = ind_before[np.argmax(dt[ind_before])]
        i2 = ind_after[np.argmin(dt[ind_after])]
        compts = (temps[i1, 4:8] + temps[i2, 4:8]) / 2.0 + 273.15

    hom.set_thermal(compts[1], compts[0], compts[2], compts[3])

    hom.set_angle(
        np.asarray([vza_p]),
        np.asarray([min(sza, 85.0)]),
        np.asarray([np.abs(vaa_p - saa)])
    )

    obs = hom.run()
    polar_obs.append([doy, hour_frac, vza_p, vaa_p, sza, saa, obs[0]])

polar_obs = np.asarray(polar_obs)

# ==============================
# 仅保留 GEO & POLAR 同时存在的 DOY
# ==============================
geo_doy = np.unique(obs_all[:, 0])
polar_doy = np.unique(polar_obs[:, 0])
common_doy = np.intersect1d(geo_doy, polar_doy)

obs_all = obs_all[np.isin(obs_all[:, 0], common_doy)]
polar_obs = polar_obs[np.isin(polar_obs[:, 0], common_doy)]

# ==============================
# 拟合处理
# ==============================
original_msg_ = []
fitted_msg_ = []
ref_msg_ = []
original_polar_ = []
fitted_polar_ = []
ref_polar_ = []
daily_results = []  # 存储每天的结果

for doy in [161]:
    # -----------------------------
    # MSG / GEO
    # -----------------------------
    ind = np.where(obs_all[:, 0] == doy)[0]
    obs = obs_all[ind, 7]  # 观测 Tb
    pst = obs_all[ind, 1]  # 小时
    vza = obs_all[ind, 3]
    vaa = obs_all[ind, 4]
    sza = obs_all[ind, 5]
    saa = obs_all[ind, 6]
    ist = obs_all[ind, 2]
    ind1 = ist == 0
    ind2 = ist == 1

    raa = np.abs(vaa - saa)
    raa[raa > 180] = 360 - raa[raa > 180]
    fhs = kernel_RLf(vza, sza, raa)
    ind_fit = (pst > 4) & (pst < 21)
    ind_eva = (pst >= 9) & (pst <= 15)

    x0 = np.asarray([283.15, 15, 15, 6, 1.5, 0.5])
    results_dtcr = fitting_DTCR(obs[ind_fit], pst[ind_fit], fhs[ind_fit], x0=x0)
    fitted_dtcr = model_DTCR(results_dtcr, pst, fhs)

    fitted_dtcr1 = model_DTCR(results_dtcr, pst[ind1], fhs[ind1])
    fitted_dtcr2 = model_DTCR(results_dtcr, pst[ind2], fhs[ind2])
    ref_dtc = model_DTC(results_dtcr[0:4], pst)

    # 计算每天的统计
    rmse_dtcr = np.sqrt(np.mean((obs[ind_eva] - fitted_dtcr[ind_eva]) ** 2))
    bias_dtcr = np.mean(fitted_dtcr[ind_eva] - obs[ind_eva])
    r2_dtcr = 1 - np.sum((obs[ind_eva] - fitted_dtcr[ind_eva]) ** 2) / np.sum(
        (obs[ind_eva] - np.mean(obs[ind_eva])) ** 2)

    # 保存每天的结果
    daily_results.append({
        'doy': doy,
        'geo_obs': obs[ind_eva],
        'geo_fitted': fitted_dtcr[ind_eva],
        'geo_ref': ref_dtc[ind_eva],
        'geo_rmse': rmse_dtcr,
        'geo_bias': bias_dtcr,
        'geo_r2': r2_dtcr,
        'fit_params': results_dtcr
    })

    # 保存结果
    fitted_msg_.append(fitted_dtcr[ind_eva])
    original_msg_.append(obs[ind_eva])
    ref_msg_.append(ref_dtc[ind_eva])

    # -----------------------------
    # POLAR
    # -----------------------------
    ind_p = np.where(polar_obs[:, 0] == doy)[0]
    if len(ind_p) == 0:
        continue
    obs_p = polar_obs[ind_p, 6]
    pst_p = polar_obs[ind_p, 1]
    vza_p = polar_obs[ind_p, 2]
    vaa_p = polar_obs[ind_p, 3]
    sza_p = polar_obs[ind_p, 4]
    saa_p = polar_obs[ind_p, 5]
    raa_p = np.abs(vaa_p - saa_p)
    raa_p[raa_p > 180] = 360 - raa_p[raa_p > 180]
    fhs_p = kernel_RLf(vza_p, sza_p, raa_p)
    # 用同一天 GEO 拟合参数来拟合 POLAR
    fitted_p = model_DTCR(results_dtcr, pst_p, fhs_p)
    ref_p = model_DTC(results_dtcr[0:4], pst_p)

    # 计算POLAR的统计
    rmse_p = np.sqrt(np.mean((obs_p - fitted_p) ** 2))
    bias_p = np.mean(fitted_p - obs_p)
    r2_p = 1 - np.sum((obs_p - fitted_p) ** 2) / np.sum((obs_p - np.mean(obs_p)) ** 2)




    import matplotlib.pyplot as plt
    import numpy as np

    plt.figure(figsize=(6, 5))

    # 统一 DOY 颜色归一化
    all_doy = np.concatenate([obs_all[:, 0], polar_obs[:, 0]])
    norm = plt.Normalize(all_doy.min(), all_doy.max())

    # 定义Nature风格颜色
    nature_colors = {
        'blue': '#1f77b4',
        'orange': '#ff7f0e',
        'green': '#2ca02c',
        'red': '#d62728',
        'gray': '#7f7f7f'
    }

    # GEO 数据 - 使用Nature颜色
    # 第一角度（红色系）
    plt.plot(pst[ind1], obs[ind1],
             'o',
             color=nature_colors['blue'],
             markersize=5,
             alpha=0.8,
             label='EURO ')

    plt.plot(pst[ind1], fitted_dtcr[ind1],
             '-',
             color=nature_colors['blue'],
             linewidth=1.8,
             alpha=0.9,label='EURO-fitted')

    # 第二角度（蓝色系）
    plt.plot(pst[ind2], obs[ind2],
             'o',
             color=nature_colors['red'],
             markersize=5,
             alpha=0.8,
             label='IODC')

    plt.plot(pst[ind2], fitted_dtcr[ind2],
             '-',
             color=nature_colors['red'],
             linewidth=1.8,
             alpha=0.9,
             label='IODC-fitted')


    plt.plot(pst[ind1], ref_dtc[ind1],
             '-',
             color=nature_colors['gray'],
             linewidth=1.8,
             alpha=0.9,
             label='DTC-fitted')

    # POLAR 数据 - 使用绿色系
    plt.plot(pst_p, obs_p,
             's',  # 方形标记
             color=nature_colors['green'],
             markersize=4,
             alpha=0.7,
             label='Polar Obs')

    plt.plot(pst_p, fitted_p,
             'x',
             color=nature_colors['green'],
             markersize=5,
             linewidth=1.5,
             alpha=0.8,
             label='Polar Fitted')

    # 坐标轴标签
    plt.xlabel('Hour of Day', fontsize=11, fontweight='normal')
    plt.ylabel('Brightness Temperature (K)', fontsize=11, fontweight='normal')

    # 坐标轴刻度
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)

    # 添加图例
    plt.legend(fontsize=9,
               frameon=True,
               framealpha=0.9,
               edgecolor=nature_colors['gray'])

    # 网格设置
    plt.grid(True,
             alpha=0.2,
             linestyle='--',
             linewidth=0.5,
             color=nature_colors['gray'])

    # 边框设置
    for spine in plt.gca().spines.values():
        spine.set_linewidth(0.8)
        spine.set_color(nature_colors['gray'])

    plt.tight_layout()
    plt.xlim(6,21)
    plt.show()

