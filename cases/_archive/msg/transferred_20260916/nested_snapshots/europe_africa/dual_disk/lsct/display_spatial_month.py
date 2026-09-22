import h5py
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import rasterio

# ===================== 路径 =====================
h5_path = ("/media/hero/MSG/PRODUCTS/LSCT/MLST_COMPONENT/"
           "MONTHLY_HOUR_TOPLEVEL_2018-2025/MLST_MONTH_201807_HH12.h5")
lon_path = "/media/hero/MSG/Static/combined_euro_lon.tif"
lat_path = "/media/hero/MSG/Static/combined_euro_lat.tif"

# ===================== 读取经纬度 =====================
with rasterio.open(lon_path) as ds:
    lon = ds.read(1)
with rasterio.open(lat_path) as ds:
    lat = ds.read(1)

# ===================== 读取数据 =====================
with h5py.File(h5_path, 'r') as f:
    dset_list = list(f.values())
    data_3d = dset_list[0][:]

layer1 = data_3d[0]/100.0
layer2 = data_3d[1]/100.0
layer1 = np.flipud(layer1)
layer2 = np.flipud(layer2)

# 异常值掩码
layer1 = np.clip(layer1, 290, 325)
layer2 = np.clip(layer2, 290, 325)

# ===================== seaborn 快速绘图 =====================
sns.set_style("white")
sns.set_context("talk", font_scale=0.8)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# 图层1
im1 = ax1.imshow(layer1, cmap='RdYlBu_r', origin='lower')
ax1.set_title('Layer 1', fontweight='bold')
fig.colorbar(im1, ax=ax1, shrink=0.8, label='Temperature (K)')

# 图层2
im2 = ax2.imshow(layer2, cmap='RdYlBu_r', origin='lower')
ax2.set_title('Layer 2', fontweight='bold')
fig.colorbar(im2, ax=ax2, shrink=0.8, label='Temperature (K)')

# 去掉坐标轴刻度（更像空间分布图）
for ax in [ax1, ax2]:
    ax.set_xticks([])
    ax.set_yticks([])

plt.tight_layout()
plt.savefig("/media/hero/MSG/fast_spatial_plot.png", dpi=300, bbox_inches='tight')
plt.show()