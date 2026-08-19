import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

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
ksm = 0.15
klai = 2.0

kyear = 2025
kmonth = 6
kday = 5
ndays = 30

# 观测参数
klai0 = 1.5
hspot = 0.15
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
# columns: 0 doy | 1 hour | 2 sat_id | 3 Tb
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
                obs_all.append([kdoy, hour_frac, isat, obs[isat]])

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
    polar_obs.append([doy, hour_frac, obs[0]])

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
# 绘图：GEO 静止卫星按天画线 + POLAR 极轨点
# ==============================
plt.figure(figsize=(8, 5))

# 统一 DOY 颜色归一化
all_doy = np.concatenate([obs_all[:, 0], polar_obs[:, 0]])
norm = plt.Normalize(all_doy.min(), all_doy.max())

# GEO 两角度渐变色
cmap_geo = [plt.cm.Blues, plt.cm.Oranges]

# GEO 两角度，按天画线
for isat in [0, 1]:
    ind_sat = obs_all[:, 2] == isat
    days = np.unique(obs_all[ind_sat, 0])
    for doy in days:
        ind_day = (obs_all[:, 0] == doy) & (obs_all[:, 2] == isat)
        hours = obs_all[ind_day, 1]
        Tb = obs_all[ind_day, 3]
        plt.plot(
            hours,
            Tb,
            color=cmap_geo[isat](norm(doy)),
            alpha=0.6,
            linewidth=1.5,
            label=f'GEO angle {isat+1}' if doy == days[0] else None
        )

# POLAR 极轨卫星，灰色渐变
cmap_polar = plt.cm.Greys
plt.scatter(
    polar_obs[:, 1],
    polar_obs[:, 2],
    c=polar_obs[:, 0],
    cmap=cmap_polar,
    norm=norm,
    s=35,
    marker='o',
    edgecolor='k',
    linewidth=0.3,
    alpha=0.7,
    label='Polar-orbiting'
)

import matplotlib.lines as mlines
geo_line1 = mlines.Line2D([], [], color=plt.cm.Blues(0.6), linewidth=1.5, label='GEO angle 1')
geo_line2 = mlines.Line2D([], [], color=plt.cm.Oranges(0.6), linewidth=1.5, label='GEO angle 2')
polar_marker = mlines.Line2D([], [], color='gray', marker='o', linestyle='None',
                             markersize=7, markeredgecolor='k', label='Polar-orbiting')

plt.legend(handles=[geo_line1, geo_line2, polar_marker], frameon=False, fontsize=9)


# 颜色条
cbar = plt.colorbar()
cbar.set_label('Day of Year')

plt.xlabel('Hour of day')
plt.ylabel('Brightness temperature (K)')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
