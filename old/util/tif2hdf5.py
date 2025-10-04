import datetime
import gdal
import netCDF4 as nc
import numpy as np
import os
import osr
import sys
import time
import h5py
import tables
import pandas as pd

fileDir = r'N:\mydata\otherFormat\\'
fileName = fileDir + 'S3B_2019352_lsct.tif'
dataset = gdal.Open(fileName)
if dataset == None:
    print(fileName + "文件无法打开")
im_width = dataset.RasterXSize
im_height = dataset.RasterYSize
im_bands = dataset.RasterCount
im_data = dataset.ReadAsArray(0, 0, im_width, im_height)
im_geotrans = dataset.GetGeoTransform()
im_proj = dataset.GetProjection()

i = 10

soilData = im_data[0,:,:]
leafData = im_data[0,:,:]

# #普通格式存储
# hdfFile = h5py.File(fileDir + 'test.h5', 'w')
# hdfFile.create_dataset('soil', data=soilData)
# hdfFile.create_dataset('leaf', data=leafData)
# hdfFile.close()
# print('created')


#无损压缩格式存储
# h5 = h5py.File(fileDir + 'test_gzip.h5', 'w')
# h5.create_dataset('soil', data=soilData, compression='gzip')
# h5.create_dataset('leaf', data=leafData, compression='gzip')
# h5.close()

# h5 = h5py.File(fileDir + 'test_lzf.h5', 'w')
# h5.create_dataset('soil', data=soilData, compression='lzf')
# h5.create_dataset('leaf', data=leafData, compression='lzf')
# h5.close()

h5 = h5py.File(fileDir + 'test_gzip.h5', 'w')
h5.attrs['Date'] = 0
h5.attrs['Height'] = im_height
h5.attrs['Width'] = im_width
h5.attrs['Resolution'] = '500m'
h5.attrs['Unit'] = 'k'
h5.attrs['GeoTransform'] = im_geotrans
h5.attrs['Projection'] = im_proj
h5.create_dataset('Time', data=soilData, compression='gzip')

grpLSVT = h5.create_group("LSVT")
grpLSVT.create_dataset('soil', data=soilData, compression='gzip')
grpLSVT.create_dataset('leaf', data=leafData, compression='gzip')

grpLST = h5.create_group("LST")
grpLST.create_dataset('Nadir',  data=soilData, compression='gzip')
grpLST.create_dataset('Oblique',  data=leafData, compression='gzip')



h5.close()