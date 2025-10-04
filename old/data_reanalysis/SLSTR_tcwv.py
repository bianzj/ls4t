from util.util import *
from pyhdf.SD import SD, SDC
import time
import os

# os.environ['PROJ_LIB'] = r'C:\Users\zzz\anaconda3\envs\patrol\Library\share\proj'

##############################################3
######## total water colume polar orbiting
###############################################
indir_ERA5 = r'D:\data\era5\\era5_2019_tcw/'
indir_data = 'd:/data/s3b_tif_heihe/'
# indir_data = 'h:/s3b_tif/'
targetArea = r'D:\data\Type\type_heihe_10000.tif'
dayNights = ['day', 'night']
infile_ear5_ref = r'D:\data\map\world_equal_latlon.tif'
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
dataset = None

dataset = gdal.Open(infile_ear5_ref)
if dataset == None:
    print(infile_ear5_ref + "")
im_width = dataset.RasterXSize
im_height = dataset.RasterYSize
im_bands = dataset.RasterCount
im_geotrans = dataset.GetGeoTransform()
im_proj = dataset.GetProjection()
temp1, temp2 = lonlat2geo(dataset, lat, lon)
imagex, imagey = geo2imagexy(dataset, temp1, temp2)
imagex = np.asarray(imagex, np.int)
imagey = np.asarray(imagey, np.int)
ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
imagex[imagex < 0] = 0
imagex[imagex > im_height - 1] = im_height - 1
imagey[imagey < 0] = 0
imagey[imagey > im_width - 1] = im_width - 1
imagex = np.reshape(imagex, [nl, ns])
imagey = np.reshape(imagey, [nl, ns]) - 720

object_name = 'tcwv'

dayNight = 'day'
fileNames = search_file_rej(indir_data, [dayNight, 'bt1'], 'obliq')
fileNum = len(fileNames)
for k in range(fileNum):
    fileName = fileNames[k]
    print(fileName)
    year = np.int(fileName[-25:-21])
    doy = np.int(fileName[-21:-18])
    symbol = fileName[-29:-26]

    file0 = symbol + '_%04d' % year + '%03d' % doy + '_' + dayNight
    kmonth, kday = doy2date(year, doy)
    infile = indir_ERA5 + 'ERA5.single-level.2019%02d' % kmonth + '%02d.nc' % kday
    dataset = netCDF4.Dataset(infile)
    data = dataset.variables[object_name][:]

    infile = indir_data + file0 + '_time.tif'
    outfile = indir_data + file0 + '_tcw.tif'
    [ptime, ns, nl, nb, geog, proj] = read_image_gdal(infile)

    nl = np.int(nl/10+0.5)
    ns = np.int(ns/10+0.5)
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
        # write_image_gdal(data[0,:,:], im_width, im_height, 1, '', '', outfile)
    print(k, fileName)

dayNight = 'night'
fileNames = search_file_rej(indir_data, [dayNight, 'bt1'], 'obliq')
fileNum = len(fileNames)
for k in range(fileNum):
    fileName = fileNames[k]
    year = np.int(fileName[-27:-23])
    doy = np.int(fileName[-23:-20])
    symbol = fileName[-31:-28]
    print(k, fileName)
    file0 = symbol + '_%04d' % year + '%03d' % doy + '_' + dayNight
    kmonth, kday = doy2date(year, doy)
    infile = indir_ERA5 + 'ERA5.single-level.2019%02d' % kmonth + '%02d.nc' % kday
    dataset = netCDF4.Dataset(infile)
    data = dataset.variables[object_name][:]

    infile = indir_data + file0 + '_time.tif'
    outfile = indir_data + file0 + '_tcw.tif'
    [ptime, ns, nl, nb, geog, proj] = read_image_gdal(infile)

    nl = np.int(nl/10+0.5)
    ns = np.int(ns/10+0.5)
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
