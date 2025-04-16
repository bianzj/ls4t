import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from numpy import polyfit, poly1d
from util.util import *

# x = np.array([4,5,3,2,6])
# y = np.array([4,5,3,2,6])
#
# coeff = polyfit(x, y, 1)
# print(coeff)

infile_type = r"D:\data\LSCT_evo_2017\0_base\type\\type_evo_1000.tif"
[type, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile_type)
xmin = geog_type[0]
xscale = geog_type[1]
xmax = xmin + ns * xscale
ymax = geog_type[3]
yscale = geog_type[5]
ymin = ymax + nl * yscale
spatial_range = (xmin,ymin,xmax,ymax)
print(spatial_range)


