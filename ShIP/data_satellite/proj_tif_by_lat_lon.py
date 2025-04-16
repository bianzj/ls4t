from util.myfun import *
# from pyhdf.SD import SD, SDC
import netCDF4
import time
import os

os.environ['PROJ_LIB'] = r'C:\ProgramData\Anaconda3\envs\python37\Library\share\proj'


file = 'coeffA'
ns = 7200
nl = 3600
fileDir = r'E:\ShIP_Coef\\'
datafile = fileDir + file + '.tif'
xfile = fileDir + '\\lon.tif'
yfile = fileDir + '\\lat.tif'
vrtfile = fileDir + '\\' + file + '.vrt'
write_vrt(vrtfile, datafile, xfile, yfile, ns, nl)
outfile = fileDir +  file + '_proj.tif'
dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_Bilinear)


file = 'coeffB'
ns = 7200
nl = 3600
fileDir = r'E:\ShIP_Coef\\'
datafile = fileDir + file + '.tif'
xfile = fileDir + '\\lon.tif'
yfile = fileDir + '\\lat.tif'
vrtfile = fileDir + '\\' + file + '.vrt'
write_vrt(vrtfile, datafile, xfile, yfile, ns, nl)
outfile = fileDir +  file + '_proj.tif'
dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_Bilinear)


file = 'coeffD'
ns = 7200
nl = 3600
fileDir = r'E:\ShIP_Coef\\'
datafile = fileDir + file + '.tif'
xfile = fileDir + '\\lon.tif'
yfile = fileDir + '\\lat.tif'
vrtfile = fileDir + '\\' + file + '.vrt'
write_vrt(vrtfile, datafile, xfile, yfile, ns, nl)
outfile = fileDir +  file + '_proj.tif'
dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_Bilinear)

file = 'coeffK'
ns = 7200
nl = 3600
fileDir = r'E:\ShIP_Coef\\'
datafile = fileDir + file + '.tif'
xfile = fileDir + '\\lon.tif'
yfile = fileDir + '\\lat.tif'
vrtfile = fileDir + '\\' + file + '.vrt'
write_vrt(vrtfile, datafile, xfile, yfile, ns, nl)
outfile = fileDir +  file + '_proj.tif'
dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_Bilinear)