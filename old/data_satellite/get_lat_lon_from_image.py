
import datetime
from util.util import *
import numpy as np
import time
from datetime import datetime
from datetime import timezone
import pandas as pd


'''
计算并保存图像的经纬度
就是把投影和地理信息给转换，把经度和纬度数据给单独存出来
'''




kyear = 2019
kmonth = 8
kday = 10
khour = 15 - 8
kmin = 0

'''from vza and vaa to geo site position'''
infile_vaa = 'E:\map\AHI_VAA.tif'
infile_vza = 'E:\map\AHI_VZA.tif'
vza, ns, nl, nb, geog, proj,dataset = read_image_dataset_gdal(infile_vza)
vaa, ns, nl, nb, geog, proj = read_image_gdal(infile_vaa)
nsi = np.zeros([nl, ns])
nli = np.zeros([nl, ns])
for k in range(nl):
    nli[k, :] = k
    nsi[k, :] = np.linspace(0, ns - 1, ns)
nli = np.reshape(nli,-1)
nsi = np.reshape(nsi,-1)
temp1,temp2= imagexy2geo(dataset,nli,nsi)
lon,lat = geo2lonlat(dataset,temp1,temp2)
dataset = None

lon = np.reshape(lon,[nl,ns])
lat = np.reshape(lat,[nl,ns])
infile_lat = 'E:\map\AHI_lat.tif'
infile_lon = 'E:\map\AHI_lon.tif'
write_image_gdal(lat,ns,nl,1,geog,proj,infile_lat)
write_image_gdal(lon,ns,nl,1,geog,proj,infile_lon)

#
# newnl = 600
# newns = 600
# lat = np.resize(lat,[newnl,newns])
# lon = np.resize(lon,[newnl,newns])
# dobj = datetime(kyear,kmonth,kday,khour,kmin,tzinfo=timezone.utc)
# sza = float(90)-get_altitude(lat, lon, dobj)
#
#
# sza = np.reshape(sza,[newnl,newns])
# plt.imshow(sza)
# plt.colorbar()
# plt.show()