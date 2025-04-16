import matplotlib.pyplot as plt
from osgeo import gdal
import numpy as np
import cv2

def resize_data(preArray, nl, ns, method='cv2.INTER_LINEAR'):
    ns = int(ns)
    nl = int(nl)
    data = cv2.resize(preArray, (ns, nl), interpolation=0)
    return data

# Specify TIFF file paths
tiff_file_path1 = "D:\data\other\SST\plot2\GF5B_VIMI_N37.1_E126.5_20230615_009418_L10000346381_IR_SST.tiff"
tiff_file_path2 = "D:\data\other\SST\plot2\TERRA_MODIS.20230615T130001.L2.SST._out.tif"

# Use GDAL to open TIFF files
dataset1 = gdal.Open(tiff_file_path1)
dataset2 = gdal.Open(tiff_file_path2)

# Read temperature data
temperature_data1 = dataset1.GetRasterBand(1).ReadAsArray()
temperature_data2 = dataset2.GetRasterBand(1).ReadAsArray()

sst_gf = temperature_data1
sst_mod = temperature_data2
nl, ns = sst_gf.shape
sst_mod = resize_data(sst_mod, nl, ns)

# Set values equal to 200 as gray
ind = (sst_mod < 200) & (sst_mod > 100) & (sst_gf != 0)
sst_gf[ind] = 200
sst_mod[ind] = 200

# Cut
sst_mod[sst_gf == 0] = 0
sst_gf[sst_mod == 0] = 0

plt.rc('font', family='Times New Roman')

# Set the desired temperature range and background value
temperature_range = (280, 300)
background_value = 0

plt.figure(figsize=(10, 5))

# Plotting sst_gf
sst_gf_masked = np.ma.masked_where(sst_gf == background_value, sst_gf)
ax1 = plt.subplot(1, 2, 1)
img_gf = ax1.imshow(sst_gf_masked, cmap='RdBu_r', vmin=temperature_range[0], vmax=temperature_range[1])
plt.title('SST GF')

# Plotting sst_mod
sst_mod_masked = np.ma.masked_where(sst_mod == background_value, sst_mod)
ax2 = plt.subplot(1, 2, 2)
img_mod = ax2.imshow(sst_mod_masked, cmap='RdBu_r', vmin=temperature_range[0], vmax=temperature_range[1])
plt.title('SST MODIS')

# Set color for value 200 to gray
cmap = plt.cm.get_cmap('RdBu_r')
cmap.set_under('gray')

# Set color for value 200 to a lighter shade of gray
cmap = plt.cm.get_cmap('RdBu_r')
cmap.set_under('#F0F0F0')  # Light gray

# Add a single colorbar for both plots
cbar_ax = plt.gcf().add_axes([0.95, 0.15, 0.02, 0.7])  # [x, y, width, height]
cbar = plt.colorbar(img_mod, cax=cbar_ax, orientation='vertical')
cbar.set_label('Temperature (K)')

# Remove x and y axis labels
plt.setp([ax1, ax2], xticks=[], yticks=[])

plt.show()
