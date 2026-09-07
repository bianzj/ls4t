import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from pvlib.location import Location
import pvlib

from base.util_kernel import fitting_DTC
from base.util_lst import *
from base.util_data import *
from base.util_fitting import *
from base.util_kernel import *
from base.util_file import *
from base.rt.hom import *
from base.rt.crown import *

# ==============================
# 常量与路径
# ==============================
deg2rad = np.pi / 180
elev = 0
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
kday = 5      # 起始日
ndays = 30    # 模拟天数

# 观测参数
klai0 = 2.5
hspot = 0.15
stand = 0.075
radi_vertical = 2
radi_horizontal = 2
wl = 10.5
emissivity_soil = 0.955
emissivity_leaf = 0.97

# 两个卫星（两个观测角度）
vza = np.asarray([28.29, 42.12])
vaa = np.asarray([-38.73 + 360, 61.56])

# ==============================
# 初始化 HOM
# ==============================
crown = Crown()
'''2.set variables;'''
crown.set_structure(klai0, hspot,stand,radi_vertical,radi_horizontal)
crown.set_optical(wl, emissivity_soil, emissivity_leaf)

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
# 主循环：30 天 × 日变化 × 2 卫星
# ==============================
# columns:
# 0 day_index | 1 doy_frac | 2 hour | 3 sat_id | 4 Tb
obs_all = []

ksite = 5  # 固定站点，与原代码一致

for day_offset in range(ndays):

    cur_date = pd.Timestamp(kyear, kmonth, kday) + pd.Timedelta(days=day_offset)
    date_str = cur_date.strftime('%Y-%m-%d')
    kdoy = date2DOY(cur_date.year, cur_date.month, cur_date.day)

    site = Location(
        lat_[ksite],
        lon_[ksite],
        'Etc/GMT',
        altitude,
        'None'
    )

    for khh in range(1, 24):
        for kmm in range(0, 60, 15):

            time_temp = pd.date_range(
                f"{date_str} {khh:02d}:{kmm:02d}:00",
                periods=1,
                freq='15min',
                tz='UTC'
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

            ind = np.where(np.abs(ktime - temps[:, 2]) < 0.001)
            if len(ind[0]) == 0:
                continue

            compts = temps[ind, 4:8] + 273.15

            crown.set_thermal(
                compts[0, 0, 1],
                compts[0, 0, 0],
                compts[0, 0, 2],
                compts[0, 0, 3]
            )

            raa = np.abs(vaa - saa)
            crown.set_angle(vza, sza, raa)

            obs = crown.run()

            for isat in range(2):
                obs_all.append([
                    day_offset,
                    ktime,
                    hour_frac,
                    isat,
                    obs[isat]
                ])

# 转为 numpy
obs_all = np.asarray(obs_all)

# ==============================
# 绘图
# ==============================
plt.figure(figsize=(5.2, 4.2))

colors = ['tab:blue', 'tab:orange']
labels = ['EURO', 'IODC']

# ---- 30 天逐日结果（淡色）----
for isat in [0, 1]:
    for d in range(ndays):
        ind = (obs_all[:, 0] == d) & (obs_all[:, 3] == isat)
        plt.plot(
            obs_all[ind, 2],
            obs_all[ind, 4],
            color=colors[isat],
            alpha=0.1,
            linewidth=1
        )

# ---- 月度平均（日变化）----
for isat in [0, 1]:
    ind = obs_all[:, 3] == isat
    hours = np.unique(obs_all[ind, 2])

    Tb_mean = [
        np.mean(obs_all[ind & (obs_all[:, 2] == h), 4])
        for h in hours
    ]

    plt.plot(
        hours,
        Tb_mean,
        color=colors[isat],
        linewidth= 1.5,
        label=f'{labels[isat]} monthly mean'
    )







# ---- 图形美化 ----
plt.xlabel('Hour of day')
plt.ylabel('Brightness temperature (K)')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
