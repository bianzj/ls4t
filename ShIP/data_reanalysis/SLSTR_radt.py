from util.util import *
from pyhdf.SD import SD, SDC

import time
import os

# os.environ['PROJ_LIB'] = r'C:\Users\zzz\anaconda3\envs\patrol\Library\share\proj'


##############################################3
######## total rad
###############################################
indir_ERA5 = r'D:\data\lst\\era5_rad/'
indir_data = 'f:/s3a_tif/'
# indir_data = 'h:/s3b_tif/'
targetArea = r'D:\data\lst\base\typed2.tif'
dayNights = ['day', 'night']
infile_ear5_ref = r'D:\data\lst\base\world_equal_latlon.tif'
days_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

dataset = gdal.Open(targetArea)
if dataset == None:
    print(targetArea + "")
ns = dataset.RasterXSize
nl = dataset.RasterYSize
im_bands = dataset.RasterCount
data = dataset.ReadAsArray(0, 0, ns, nl)
geog = dataset.GetGeoTransform()
proj = dataset.GetProjection()
nsi = np.zeros([nl, ns])
nli = np.zeros([nl, ns])
for k in range(nl):
    nli[k, :] = k
    nsi[k, :] = np.linspace(0, ns - 1, ns)
nli = np.reshape(nli, -1)
nsi = np.reshape(nsi, -1)
temp1, temp2 = imagexy2geo(dataset, nli, nsi)
lon, lat = geo2lonlat(dataset, temp1, temp2)

dataset = gdal.Open(infile_ear5_ref)
if dataset == None:
    print(infile_ear5_ref + "")
im_width = dataset.RasterXSize
im_height = dataset.RasterYSize
im_bands = dataset.RasterCount
im_geotrans = dataset.GetGeoTransform()
im_proj = dataset.GetProjection()
temp1, temp2 = lonlat2geo(dataset, lat, lon)
imagey, imagex = geo2imagexy(dataset, temp1, temp2)
imagex = np.asarray(imagex, np.int)
imagey = np.asarray(imagey, np.int)
ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
imagex[imagex < 0] = 0
imagex[imagex > im_height - 1] = im_height - 1
imagey[imagey < 0] = 0
imagey[imagey > im_width - 1] = im_width - 1
imagex = np.reshape(imagex, [nl, ns])
imagey = np.reshape(imagey, [nl, ns]) - 720

object_name = 'strd'

dayNight = 'day'
fileNames = search_file_rej(indir_data, [dayNight, 'bt1'], 'obliq')
fileNum = len(fileNames)
for k in range(fileNum):
    fileName = fileNames[k]

    year = np.int(fileName[-19:-15])
    doy = np.int(fileName[-15:-12])
    symbol = fileName[-23:-20]

    file0 = symbol + '_%04d' % year + '%03d' % doy + '_' + dayNight
    print(k, fileName)
    kmonth, kday = doy2date(year, doy)
    infile = indir_ERA5 + 'ERA5.single-level.2019%02d' % kmonth + '%02d.nc' % kday
    dataset = netCDF4.Dataset(infile)
    data = dataset.variables[object_name][:]

    infile = indir_data + file0 + '_time.tif'
    outfile = indir_data + file0 + '_radt.tif'
    [ptime, ns, nl, nb, geog, proj] = read_image_gdal(infile)

    nl = np.int(nl/2)
    ns = np.int(ns/2)
    ptime = resize_data_near(ptime,nl,ns)

    ptime_unque = np.unique(ptime)

    tcw = np.zeros([nl, ns])
    for kk in range(len(ptime_unque)):
        ptime_one = ptime_unque[kk]
        if ptime_one == 0: continue
        hh = np.int(ptime_one // 10000)
        mm = ((ptime_one // 100) % 100)
        mm_prop = mm / 60.0

        ind = ptime_one == ptime
        temp1 = data[hh, imagex[ind], imagey[ind]]
        if hh == 23:
            # kday = kday + 1
            infile = indir_ERA5 + 'ERA5.single-level.2019%02d' % kmonth + '%02d.nc' % (kday + 1)
            if kday == days_of_month[kmonth - 1]:
                infile = indir_ERA5 + 'ERA5.single-level.2019%02d' % (kmonth + 1) + '%02d.nc' % (1)

            dataset = netCDF4.Dataset(infile)
            data = dataset.variables[object_name][:]
            temp2 = data[0, imagex[ind], imagey[ind]]
        else:
            temp2 = data[hh + 1, imagex[ind], imagey[ind]]

        temp_tcw = temp1 * (1 - mm_prop) + temp2 * mm_prop
        tcw[ind] = temp_tcw
    write_image_gdal(tcw, ns, nl, 1, geog, proj, outfile)
    print(outfile)


dayNight = 'night'
fileNames = search_file_rej(indir_data, [dayNight, 'bt1'], 'obliq')
fileNum = len(fileNames)
for k in range(fileNum):
    fileName = fileNames[k]
    year = np.int(fileName[-21:-17])
    doy = np.int(fileName[-17:-14])
    symbol = fileName[-25:-22]
    print(k, fileName)
    file0 = symbol + '_%04d' % year + '%03d' % doy + '_' + dayNight
    kmonth, kday = doy2date(year, doy)
    infile = indir_ERA5 + 'ERA5.single-level.2019%02d' % kmonth + '%02d.nc' % kday
    dataset = netCDF4.Dataset(infile)
    data = dataset.variables[object_name][:]

    infile = indir_data + file0 + '_time.tif'
    outfile = indir_data + file0 + '_radt.tif'
    [ptime, ns, nl, nb, geog, proj] = read_image_gdal(infile)
    nl = np.int(nl/2)
    ns = np.int(ns/2)
    ptime = resize_data_near(ptime,nl,ns)

    ptime_unque = np.unique(ptime)

    tcw = np.zeros([nl, ns])
    for kk in range(len(ptime_unque)):
        ptime_one = ptime_unque[kk]
        if ptime_one == 0: continue
        hh = np.int(ptime_one // 10000)
        mm = ((ptime_one // 100) % 100)
        mm_prop = mm / 60.0
        temp1 = data[hh, imagex, imagey]
        if hh == 23:
            kday = kday + 1
            infile = indir_ERA5 + 'ERA5.single-level.2019' % kmonth + '%02d.nc' % kday
            dataset = netCDF4.Dataset(infile)
            data = dataset.variables[object_name][:]
            temp2 = data[0, imagex, imagey]
        else:
            temp2 = data[hh + 1, imagex, imagey]

        ind = (ptime == ptime_one)

        tcw[ind] = temp1[ind] * (1 - mm_prop) + temp2[ind] * mm_prop
    write_image_gdal(tcw, ns, nl, 1, geog, proj, outfile)
