from util import *

'''
数据裁切的各种具体的例子
'''

###################################################
####  RENAME OR MOVE
###################################################
# indir = r'G:\s3b_tif\\'
# outdir = r'G:\s3b_tif\\'
# dirNames = search_dir_rej(indir,['SEN3'],'zip')
# num = len(dirNames)
# for k in range(num):
#     source_file = indir+dirNames[k]+'/refl_red.tif'
#     dest_file = outdir+dirNames[k]+'/red.tif'
#     move_file(source_file,dest_file)


# indir = r'G:\mod_tif\\'
# outdir = r'G:\mod_tif\\'
# dirNames = search_file(indir,['bt31'])
# num = len(dirNames)
# for k in range(num):
#     source_file = indir+dirNames[k]
#     dest_file = outdir+dirNames[k][:-8]+'bt1.tif'
#     print(source_file,dest_file)
    # move_file(source_file,dest_file)

###################################################
####  REMOVE FILES
###################################################
# indir = r'G:\s3b_raw\\'
# target_file = 'cloud.tif'
# dirNames = search_file_rej(indir,['cloud'],'zip')
# num = len(dirNames)
# for k in range(1,num-1):
#     target_dir = indir+dirNames[k]
#     remove_file(target_dir,target_file)


#################################################
##### WRITE WINRAR.BAT FOR UNZIP FILE
##################################################
# indir = r'G:\s3b_raw'
# outfile = 'G:\s3b_raw\winrar.bat'
# f = open(outfile,'w')
# fileNames = search_file_rej(indir,'zip','SEN3')
# fileNum = len(fileNames)
# for k in range(fileNum):
#     f.write('winrar x '+fileNames[k] +'\n')
# f.close()


# indir = r'G:/s3a_raw/'
# outfile = 'G:/s3a_raw/winrar.bat'
# f = open(outfile,'w')
# fileNames = search_file_rej(indir,'zip','SEN3')
# fileNum = len(fileNames)
# for k in range(fileNum):
#     if os.path.exists(indir+fileNames[k][:-3]+'SEN3')==1:
#         continue
#     f.write('winrar x '+fileNames[k] +'\n')
# f.close()

###################################################3
####  GET VAA
###################################################

# infile = 'G:/base/AHI8_VZA.tif'
# outfile = 'G:/base/AHI8_VAA.tif'
# dataset = gdal.Open(infile)
# if dataset == None:
#     print(infile + " can not be opened ! ")
# ns = dataset.RasterXSize
# nl = dataset.RasterYSize
# im_bands = dataset.RasterCount
# data = dataset.ReadAsArray(0, 0, ns, nl)
# geog = dataset.GetGeoTransform()
# proj = dataset.GetProjection()
# nsi = np.zeros([nl, ns])
# nli = np.zeros([nl, ns])
# for k in range(nl):
#     nli[k, :] = k
#     nsi[k, :] = np.linspace(0, ns - 1, ns)
# nli = np.reshape(nli,-1)
# nsi = np.reshape(nsi,-1)
# temp1,temp2= imagexy2geo(dataset,nli,nsi)
# lon,lat = geo2lonlat(dataset,temp1,temp2)
# vaa = calc_azimuth(0,140,lat,lon)
# vaa = (vaa+180) % 360
# vaa = np.reshape(vaa,[nl,ns])
# write_image_gdal(vaa,ns,nl,1,geog,proj,outfile)


#################################################333
#### lat and lon
###################################################

# outfile1 = 'G:/ahi_med/lat.tif'
# outfile2 = 'G:/ahi_med/lon.tif'
#
# nl = 250
# ns = 250
# lat_temp = np.arange(42.7,37.7,-0.02)
# lon_temp = np.arange(97.0,102,0.02)
#
# lat = np.zeros([nl,ns])
# lon = np.zeros([nl,ns])
#
# for k in range(250):
#     lat[k,:] = lat_temp[k]
#     lon[k,:] = lon_temp
#
#
# write_image_gdal(lat,ns,nl,1,'','',outfile1)
# write_image_gdal(lon,ns,nl,1,'','',outfile2)


# infile1 = r'D:\data\map\AHI_VZA_CHINA.tif'
# infile2 = r'D:\data\map\AHI_VAA_CHINA.tif'
# targetArea = r'D:\data\type\type_heihe_2000.tif'
# dataset = gdal.Open(targetArea)
# if dataset == None:
#     print(targetArea + " ")
# ns = dataset.RasterXSize
# nl = dataset.RasterYSize
# im_bands = dataset.RasterCount
# data = dataset.ReadAsArray(0, 0, ns, nl)
# geog = dataset.GetGeoTransform()
# proj = dataset.GetProjection()
# nsi = np.zeros([nl, ns])
# nli = np.zeros([nl, ns])
# for k in range(nl):
#     nli[k, :] = k
#     nsi[k, :] = np.linspace(0, ns - 1, ns)
# nli = np.reshape(nli, -1)
# nsi = np.reshape(nsi, -1)
# ###
# temp1, temp2 = imagexy2geo(dataset, nli, nsi)
# lon, lat = geo2lonlat(dataset, temp1, temp2)
#
#
# data1 = np.zeros([nl, ns])
# data2 = np.zeros([nl, ns])
#
# outfile1 = r'D:\data\MAP\AHI_VZA_HEIHE.tif'
# dataset = gdal.Open(infile1)
# im_width = dataset.RasterXSize
# im_height = dataset.RasterYSize
# im_bands = dataset.RasterCount
# data = dataset.ReadAsArray(0, 0, im_width, im_height)
# im_geotrans = dataset.GetGeoTransform()
# im_proj = dataset.GetProjection()
# temp1, temp2 = lonlat2geo(dataset, lon, lat)
# imagex, imagey = geo2imagexy(dataset, temp1, temp2)
#
# imagex = np.asarray(imagex, np.int)
# imagey = np.asarray(imagey, np.int)
# ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
# imagex[imagex < 0] = 0
# imagex[imagex > im_height - 1] = im_height - 1
# imagey[imagey < 0] = 0
# imagey[imagey > im_width - 1] = im_width - 1
# temp = data[imagex, imagey]
# indnew = (temp < 5000) * (temp > 0) * ind
# data1 = np.reshape(data1, [-1])
# data1[indnew] = temp[indnew]
# data1 = np.reshape(data1, [nl, ns])
# data1[data1 < 0] = 0
# data1[data1 > 5000] = 0
#
# outfile2 = r'D:\data\MAP\AHI_VAA_HEIHE.tif'
# [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile2)
# temp = data[imagex, imagey]
# indnew = (temp < 5000) * (temp > 0) * ind
# data2 = np.reshape(data2, [-1])
# data2[indnew] = temp[indnew]
# data2 = np.reshape(data2, [nl, ns])
# data2[data2 < 0] = 0
# data2[data2 > 5000] = 0
#
# write_image_gdal(data1, ns, nl, 1, geog, proj, outfile1)
# write_image_gdal(data2, ns, nl, 1, geog, proj, outfile2)

##############################################


###################################################
####   AHI vza and vaa
####################################################
# infile1 = r'D:\data\map\AHI_VZA_CHINA.tif'
# infile2 = r'D:\data\map\AHI_VAA_CHINA.tif'
# targetArea = r'D:\data\type\type_heihe_2000.tif'
# dataset = gdal.Open(targetArea)
# if dataset == None:
#     print(targetArea + " ")
# ns = dataset.RasterXSize
# nl = dataset.RasterYSize
# im_bands = dataset.RasterCount
# data = dataset.ReadAsArray(0, 0, ns, nl)
# geog = dataset.GetGeoTransform()
# proj = dataset.GetProjection()
# nsi = np.zeros([nl, ns])
# nli = np.zeros([nl, ns])
# for k in range(nl):
#     nli[k, :] = k
#     nsi[k, :] = np.linspace(0, ns - 1, ns)
# nli = np.reshape(nli, -1)
# nsi = np.reshape(nsi, -1)
# ###
# temp1, temp2 = imagexy2geo(dataset, nli, nsi)
# lon, lat = geo2lonlat(dataset, temp1, temp2)
#
#
# data1 = np.zeros([nl, ns])
# data2 = np.zeros([nl, ns])
#
# outfile1 = r'D:\data\MAP\AHI_VZA_HEIHE.tif'
# dataset = gdal.Open(infile1)
# im_width = dataset.RasterXSize
# im_height = dataset.RasterYSize
# im_bands = dataset.RasterCount
# data = dataset.ReadAsArray(0, 0, im_width, im_height)
# im_geotrans = dataset.GetGeoTransform()
# im_proj = dataset.GetProjection()
# temp1, temp2 = lonlat2geo(dataset, lon, lat)
# imagex, imagey = geo2imagexy(dataset, temp1, temp2)
#
# imagex = np.asarray(imagex, np.int)
# imagey = np.asarray(imagey, np.int)
# ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
# imagex[imagex < 0] = 0
# imagex[imagex > im_height - 1] = im_height - 1
# imagey[imagey < 0] = 0
# imagey[imagey > im_width - 1] = im_width - 1
# temp = data[imagex, imagey]
# indnew = (temp < 5000) * (temp > 0) * ind
# data1 = np.reshape(data1, [-1])
# data1[indnew] = temp[indnew]
# data1 = np.reshape(data1, [nl, ns])
# data1[data1 < 0] = 0
# data1[data1 > 5000] = 0
#
# outfile2 = r'D:\data\MAP\AHI_VAA_HEIHE.tif'
# [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile2)
# temp = data[imagex, imagey]
# indnew = (temp < 5000) * (temp > 0) * ind
# data2 = np.reshape(data2, [-1])
# data2[indnew] = temp[indnew]
# data2 = np.reshape(data2, [nl, ns])
# data2[data2 < 0] = 0
# data2[data2 > 5000] = 0
#
# write_image_gdal(data1, ns, nl, 1, geog, proj, outfile1)
# write_image_gdal(data2, ns, nl, 1, geog, proj, outfile2)

###################################################
####   emissivity
####################################################
# infile1 = r'D:\data\emis\emis1_geo.TIF'
# infile2 = r'D:\data\emis\emis2_geo.TIF'
# targetArea = r'D:\data\type\type_heihe_2000.tif'
# dataset = gdal.Open(targetArea)
# if dataset == None:
#     print(targetArea + " ")
# ns = dataset.RasterXSize
# nl = dataset.RasterYSize
# im_bands = dataset.RasterCount
# data = dataset.ReadAsArray(0, 0, ns, nl)
# geog = dataset.GetGeoTransform()
# proj = dataset.GetProjection()
# nsi = np.zeros([nl, ns])
# nli = np.zeros([nl, ns])
# for k in range(nl):
#     nli[k, :] = k
#     nsi[k, :] = np.linspace(0, ns - 1, ns)
# nli = np.reshape(nli, -1)
# nsi = np.reshape(nsi, -1)
# ###
# temp1, temp2 = imagexy2geo(dataset, nli, nsi)
# lon, lat = geo2lonlat(dataset, temp1, temp2)
#
#
# data1 = np.zeros([nl, ns])
# data2 = np.zeros([nl, ns])
#
# outfile1 = r'D:\data\emis\emis1_geo_heihe.tif'
# dataset = gdal.Open(infile1)
# im_width = dataset.RasterXSize
# im_height = dataset.RasterYSize
# im_bands = dataset.RasterCount
# data = dataset.ReadAsArray(0, 0, im_width, im_height)
# im_geotrans = dataset.GetGeoTransform()
# im_proj = dataset.GetProjection()
# temp1, temp2 = lonlat2geo(dataset, lon, lat)
# imagex, imagey = geo2imagexy(dataset, temp1, temp2)
#
# imagex = np.asarray(imagex, np.int)
# imagey = np.asarray(imagey, np.int)
# ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
# imagex[imagex < 0] = 0
# imagex[imagex > im_height - 1] = im_height - 1
# imagey[imagey < 0] = 0
# imagey[imagey > im_width - 1] = im_width - 1
# temp = data[imagex, imagey]
# indnew = (temp < 5000) * (temp > 0) * ind
# data1 = np.reshape(data1, [-1])
# data1[indnew] = temp[indnew]
# data1 = np.reshape(data1, [nl, ns])
# data1[data1 < 0] = 0
# data1[data1 > 5000] = 0
#
# outfile2 = r'D:\data\emis\emis2_geo_heihe.tif'
# [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile2)
# temp = data[imagex, imagey]
# indnew = (temp < 5000) * (temp > 0) * ind
# data2 = np.reshape(data2, [-1])
# data2[indnew] = temp[indnew]
# data2 = np.reshape(data2, [nl, ns])
# data2[data2 < 0] = 0
# data2[data2 > 5000] = 0
#
# write_image_gdal(data1, ns, nl, 1, geog, proj, outfile1)
# write_image_gdal(data2, ns, nl, 1, geog, proj, outfile2)


###################################################
####   AHI sza
####################################################
#
# for utc in range(24):
#     print(cal_sza_saa([97,102],[42,37],2019,8,3,np.asarray([4])))