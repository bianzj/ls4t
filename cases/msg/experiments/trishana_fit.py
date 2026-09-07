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
hspot = 0.15
wl = 10.5

emissivity_soil = 0.975
emissivity_leaf = 0.99

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
            time_temp = pd.date_range(
                f"{cur_date:%Y-%m-%d} {khh:02d}:{kmm:02d}:00",
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

for doy in np.unique(common_doy):
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

    raa = np.abs(vaa - saa)
    raa[raa > 180] = 360 - raa[raa > 180]

    fhs = kernel_RLf(vza, sza, raa)

    ind_fit = (pst > 3) & (pst < 21)
    ind_eva = (pst >= 9) & (pst <= 15)

    x0 = np.asarray([293.15, 10, 14, 6, 0.5, 0.5])
    results_dtcr = fitting_DTCR(obs[ind_fit], pst[ind_fit], fhs[ind_fit], x0=x0)
    fitted_dtcr = model_DTCR(results_dtcr, pst, fhs)
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

    # 更新每天的结果
    daily_results[-1].update({
        'polar_obs': obs_p,
        'polar_fitted': fitted_p,
        'polar_ref': ref_p,
        'polar_rmse': rmse_p,
        'polar_bias': bias_p,
        'polar_r2': r2_p
    })

    fitted_polar_.append(fitted_p)
    original_polar_.append(obs_p)
    ref_polar_.append(ref_p)

# -----------------------------
# 转 numpy
# -----------------------------
fitted_msg_ = np.concatenate(fitted_msg_)
original_msg_ = np.concatenate(original_msg_)
fitted_polar_ = np.concatenate(fitted_polar_)
original_polar_ = np.concatenate(original_polar_)
ref_msg_ = np.concatenate(ref_msg_)
ref_polar_ = np.concatenate(ref_polar_)

# ==============================
# 计算总体统计
# ==============================
print("\n" + "=" * 50)
print("总体统计结果")
print("=" * 50)

# GEO统计
rmse_msg_dtcr = np.sqrt(np.mean((original_msg_ - fitted_msg_) ** 2))
bias_msg_dtcr = np.mean(fitted_msg_ - original_msg_)
r2_msg_dtcr = 1 - np.sum((original_msg_ - fitted_msg_) ** 2) / np.sum((original_msg_ - np.mean(original_msg_)) ** 2)

rmse_msg_ref = np.sqrt(np.mean((original_msg_ - ref_msg_) ** 2))
bias_msg_ref = np.mean(ref_msg_ - original_msg_)
r2_msg_ref = 1 - np.sum((original_msg_ - ref_msg_) ** 2) / np.sum((original_msg_ - np.mean(original_msg_)) ** 2)

# POLAR统计
rmse_polar_dtcr = np.sqrt(np.mean((original_polar_ - fitted_polar_) ** 2))
bias_polar_dtcr = np.mean(fitted_polar_ - original_polar_)
r2_polar_dtcr = 1 - np.sum((original_polar_ - fitted_polar_) ** 2) / np.sum(
    (original_polar_ - np.mean(original_polar_)) ** 2)

rmse_polar_ref = np.sqrt(np.mean((original_polar_ - ref_polar_) ** 2))
bias_polar_ref = np.mean(ref_polar_ - original_polar_)
r2_polar_ref = 1 - np.sum((original_polar_ - ref_polar_) ** 2) / np.sum(
    (original_polar_ - np.mean(original_polar_)) ** 2)

print(f"\nGEO卫星 (DTCR模型):")
print(f"  RMSE: {rmse_msg_dtcr:.3f} K")
print(f"  Bias: {bias_msg_dtcr:.3f} K")
print(f"  R²:   {r2_msg_dtcr:.3f}")

print(f"\nGEO卫星 (DTC模型):")
print(f"  RMSE: {rmse_msg_ref:.3f} K")
print(f"  Bias: {bias_msg_ref:.3f} K")
print(f"  R²:   {r2_msg_ref:.3f}")

print(f"\nPOLAR卫星 (DTCR模型):")
print(f"  RMSE: {rmse_polar_dtcr:.3f} K")
print(f"  Bias: {bias_polar_dtcr:.3f} K")
print(f"  R²:   {r2_polar_dtcr:.3f}")

print(f"\nPOLAR卫星 (DTC模型):")
print(f"  RMSE: {rmse_polar_ref:.3f} K")
print(f"  Bias: {bias_polar_ref:.3f} K")
print(f"  R²:   {r2_polar_ref:.3f}")

# ==============================
# 计算总体统计
# ==============================
print("\n" + "=" * 50)
print("总体统计结果")
print("=" * 50)

# GEO统计
rmse_msg_dtcr = np.sqrt(np.mean((original_msg_ - fitted_msg_) ** 2))
bias_msg_dtcr = np.mean(fitted_msg_ - original_msg_)
r2_msg_dtcr = 1 - np.sum((original_msg_ - fitted_msg_) ** 2) / np.sum((original_msg_ - np.mean(original_msg_)) ** 2)

rmse_msg_ref = np.sqrt(np.mean((original_msg_ - ref_msg_) ** 2))
bias_msg_ref = np.mean(ref_msg_ - original_msg_)
r2_msg_ref = 1 - np.sum((original_msg_ - ref_msg_) ** 2) / np.sum((original_msg_ - np.mean(original_msg_)) ** 2)

# POLAR统计
rmse_polar_dtcr = np.sqrt(np.mean((original_polar_ - fitted_polar_) ** 2))
bias_polar_dtcr = np.mean(fitted_polar_ - original_polar_)
r2_polar_dtcr = 1 - np.sum((original_polar_ - fitted_polar_) ** 2) / np.sum(
    (original_polar_ - np.mean(original_polar_)) ** 2)

rmse_polar_ref = np.sqrt(np.mean((original_polar_ - ref_polar_) ** 2))
bias_polar_ref = np.mean(ref_polar_ - original_polar_)
r2_polar_ref = 1 - np.sum((original_polar_ - ref_polar_) ** 2) / np.sum(
    (original_polar_ - np.mean(original_polar_)) ** 2)

print(f"\nGEO卫星 (DTCR模型):")
print(f"  RMSE: {rmse_msg_dtcr:.3f} K")
print(f"  Bias: {bias_msg_dtcr:.3f} K")
print(f"  R²:   {r2_msg_dtcr:.3f}")

print(f"\nGEO卫星 (DTC模型):")
print(f"  RMSE: {rmse_msg_ref:.3f} K")
print(f"  Bias: {bias_msg_ref:.3f} K")
print(f"  R²:   {r2_msg_ref:.3f}")

print(f"\nPOLAR卫星 (DTCR模型):")
print(f"  RMSE: {rmse_polar_dtcr:.3f} K")
print(f"  Bias: {bias_polar_dtcr:.3f} K")
print(f"  R²:   {r2_polar_dtcr:.3f}")

print(f"\nPOLAR卫星 (DTC模型):")
print(f"  RMSE: {rmse_polar_ref:.3f} K")
print(f"  Bias: {bias_polar_ref:.3f} K")
print(f"  R²:   {r2_polar_ref:.3f}")

# ==============================
# 绘制独立的散点图1: GEO观测 vs 拟合
# ==============================

min_val = 295
max_val = 310
plt.figure(figsize=(3.5, 3))
plt.scatter(original_msg_, fitted_msg_, alpha=0.6, s=10, color='blue')

# 添加1:1线

plt.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, linewidth=1)

plt.xlabel('Observed (K)')
plt.ylabel('Fitted (K)')
# plt.title(f'GEO: Observed \nRMSE={rmse_msg_dtcr:.3f}K, R²={r2_msg_dtcr:.3f}')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# ==============================
# 绘制独立的散点图2: POLAR观测 vs 拟合
# ==============================
plt.figure(figsize=(3.5, 3))

min_val = 300
max_val = 310

if len(original_polar_) > 0:
    plt.scatter(original_polar_, fitted_polar_, alpha=0.6, s=10, color='green')

    # 添加1:1线

    plt.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, linewidth=1)

    plt.xlabel('Observed (K)')
    plt.ylabel('Fitted (K)')
    # plt.title(f'POLAR: Observe vs DTCR-fitted\nRMSE={rmse_polar_dtcr:.3f}K, R²={r2_polar_dtcr:.3f}')

plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
