from util.util import *
# from geopandas import *
# import rasterio as rio
# from geopandas import GeoSeries
# import rasterio.mask
# from rasterio.warp import (reproject,Resampling, transform_bounds,calculate_default_transform as calcdt)

'''
以某个图像作为sample
然后通过这个sample从已有的一系列图像中提取出对应的图像
然后将其保存出来

这里的要点就是，飞机或者无人机连续观测，将得到一系列图像，所要的地物并不一定会存在所有的图像中，找出有用数据
1.对图像进行遍历，
2.找到包含研究区的图像；
3.把图像切出来；
'''

def read_txt2pos(infile,numskip):
    pos_ = []
    fileName_ = []
    with open(infile) as f:
        for kskip in range(numskip): lines = f.readline()
        lines = f.readline()
        while lines:
            fields = lines.split()
            fileName_.append(fields[0])
            pos_.append(fields[1:4])
            lines = f.readline()
    pos_ = np.asarray(pos_,dtype=float)
    return fileName_,pos_


wdir = r'F:\UAVpro\20200918huailai\1429\TIR_result\\'
wdirout = r'F:\UAVpro\20200918huailai\1429\yangshu_result\\'

##################################################################
#### 样本区域
#################################################################
infile_loc =  r'F:\UAVpro\20200918huailai\1429\\yangshu.tif'
dataset = gdal.Open(infile_loc)
if dataset == None:
    print(infile_loc + "文件无法打开")
ns = dataset.RasterXSize  # 栅格矩阵的列数
nl = dataset.RasterYSize  # 栅格矩阵的行数
im_bands = dataset.RasterCount  # 波段数
data = dataset.ReadAsArray(0, 0, ns, nl)  # 获取数据
geog = dataset.GetGeoTransform()  # 获取仿射矩阵信息
proj = dataset.GetProjection()  # 获取投影信息
nsi = np.zeros([nl, ns])
nli = np.zeros([nl, ns])
for k in range(nl):
    nli[k, :] = k
    nsi[k, :] = np.linspace(0, ns - 1, ns)
nli = np.reshape(nli,-1)
nsi = np.reshape(nsi,-1)
temp1,temp2 = imagexy2geo(dataset,nli,nsi)
lon,lat = geo2lonlat(dataset,temp1,temp2)
lon_o = lon
lat_o = lat

fileNames = search_file(wdir,'tif')
number = len(fileNames)

minNumber = 0
maxNumber = 10000


##################
### 相机信息
# infile = r'cameras_tir.txt'
# fileNamePos,pos = read_txt2pos(infile,2,10)



for kimage in range(number):

    filename = fileNames[kimage]
    number = filename[-7:-4]
    if np.int(number) < minNumber:continue
    if np.int(number) > maxNumber:continue
    print(filename)
    infile = wdir + filename
    outfile = wdirout + filename


    dataset = gdal.Open(infile)
    if dataset == None:
        print(infile + "文件无法打开")
        continue
    im_width = dataset.RasterXSize
    im_height = dataset.RasterYSize
    im_bands = dataset.RasterCount
    data = dataset.ReadAsArray(0, 0, im_width, im_height)
    im_geotrans = dataset.GetGeoTransform()
    im_proj = dataset.GetProjection()
    temp1, temp2 = lonlat2geo(dataset, lat_o, lon_o)
    imagex, imagey = geo2imagexy(dataset, temp1, temp2)
    imagex = np.asarray(imagex, np.int)
    imagey = np.asarray(imagey, np.int)
    # print(np.max(imagex),np.max(imagey))

    ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
    imagex[imagex < 0] = 0
    imagex[imagex > im_height - 1] = im_height - 1
    imagey[imagey < 0] = 0
    imagey[imagey > im_width - 1] = im_width - 1
    temp = data[imagex,imagey]

    indnew = (temp > 10) * ind
    if np.sum(indnew) <= nl*ns*0.5: continue

    data_new = np.zeros([nl, ns])
    data_new = np.reshape(data_new,[-1])
    data_new[indnew] = temp[indnew]
    data_new = np.reshape(data_new,[nl,ns])
    data_new[data_new > 10000] = 0

    write_image_gdal(data_new, ns, nl, 1, geog, proj, outfile)


