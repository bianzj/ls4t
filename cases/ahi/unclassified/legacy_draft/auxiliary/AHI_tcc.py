from util.util import *
# from pyhdf.SD import SD, SDC
import time
import os

'''
云覆盖情况 （0-1）
以参考为模板确定在ERA5中的位置（空间位置）
对AHI数据进行循环，（所有数据）
然后找到对应时刻的ERA5数据（对应时间）
对应区域的点提取出来
'''

os.environ['PROJ_LIB'] = r'C:\ProgramData\Anaconda3\envs\python37\Library\share\proj'

##############################################3
######## total water colume polar orbiting
###############################################
# indir_ERA5 = r'D:\data\era5\era5_2019_cloud/'
# indir_data0 = r'n:\ahi_tif/'
# targetArea = r'D:\data\type\type_china_10000.tif'
# infile_ear5_ref = r'D:\data\map\world_equal_latlon.tif'
days_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

indir_ERA5 = r'G:\era5\era5_2019_cloud/'
indir_data0 = r'E:\AHI_heihe\tif/'
targetArea = r'E:\type\type_heihe_10000.tif'
infile_ear5_ref = r'E:\map\world_equal_latlon.tif'



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

object_name = 'tcc'

dayNight = 'day'
for kmonth in range(7,9):
    for kday in range(1,32):
        indir_data = indir_data0 + '/%02d'%kmonth+'/%02d'%kday+'/'
        fileNames = search_file(indir_data, ['bt1'])
        fileNum = len(fileNames)
        if fileNum<=0 : continue
        for k in range(0,fileNum):
            fileName = fileNames[k]
            year = np.int(fileName[-20:-16])
            doy = np.int(fileName[-16:-13])
            passtime = np.int(fileName[-12:-8])
            symbol = fileName[-24:-21]

            file0 = symbol + '_%04d' % year + '%03d' % doy + '_' + '%04d'%passtime
            print(k, fileName)
            kmonth, kday = doy2date(year, doy)
            infile = indir_ERA5 + 'ERA5.single-level.2019%02d' % kmonth + '%02d.nc' % kday
            dataset = netCDF4.Dataset(infile)
            data = dataset.variables[object_name][:]


            outfile = indir_data + file0 + '_tcc.tif'

            ptime_one = passtime
            # if ptime_one == 0: continue
            hh = np.int(ptime_one // 100)
            mm = ((ptime_one // 10) % 10)
            mm_prop = mm / 6.0
            temp1 = data[hh, imagex, imagey]
            if hh == 23:
                #kday = kday + 1
                infile = indir_ERA5 + 'ERA5.single-level.2019%02d' % kmonth + '%02d.nc' % (kday+1)
                if kday == days_of_month[kmonth-1]:
                    infile = indir_ERA5 + 'ERA5.single-level.2019%02d' % (kmonth+1) + '%02d.nc' % (1)

                dataset = netCDF4.Dataset(infile)
                data = dataset.variables[object_name][:]
                temp2 = data[0, imagex, imagey]
            else:
                temp2 = data[hh + 1, imagex, imagey]

            tcw = np.zeros([nl, ns])
            tcw = temp1

            write_image_gdal(tcw, ns, nl, 1, geog, proj, outfile)
            print(outfile)
            # write_image_gdal(data[0,:,:], im_width, im_height, 1, '', '', outfile)
