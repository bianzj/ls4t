from util.util import *
from multiprocessing import Pool, cpu_count
import multiprocessing
import time

'''
使用tif数据作为参考（要有投影信息），批量的裁剪tif数据
'''


targetArea = r'D:\data\lst\base\type.tif'
dataset = gdal.Open(targetArea)
if dataset == None:
    print(targetArea + " ")
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
nli = np.reshape(nli,-1)
nsi = np.reshape(nsi,-1)
temp1,temp2= imagexy2geo(dataset,nli,nsi)
lon,lat = geo2lonlat(dataset,temp1,temp2)



def sampling(kmonth):
    indir = r'D:\data\lst\CI_Month_V002-2019\CI_Month_V002\2019\\'
    outdir = r'D:\data\lst\CI_AREA\\'
    indir1 = indir+'2019%02d/'%(kmonth+1)
    infiles = search_file(indir1,['tif'])
    filenum = np.size(infiles)

    out_result = np.zeros([nl,ns])

    for kfile in range(filenum):
        infile = indir1 + infiles[kfile]
        print(kmonth,infiles[kfile])
        dataset = gdal.Open(infile)
        if dataset == None:
            print(infile + " ")
            continue
        im_width = dataset.RasterXSize*1
        im_height = dataset.RasterYSize*1
        im_bands = dataset.RasterCount*1
        data = dataset.ReadAsArray(0, 0, im_width, im_height)
        data = data[0,:,:]
        data = data/10000.0
        im_geotrans = dataset.GetGeoTransform()
        im_proj = dataset.GetProjection()
        temp1,temp2=lonlat2geo(dataset,lat,lon)
        imagey,imagex=geo2imagexy(dataset,temp1,temp2)

        imagex = np.asarray(imagex,np.int)
        imagey = np.asarray(imagey,np.int)
        ind = (imagex>0)* (imagex<im_height-1) * (imagey>0) * (imagey<im_width-1)
        imagex[imagex<0] = 0
        imagex[imagex>(im_height-1)] = im_height-1
        imagey[imagey<0] = 0
        imagey[imagey>(im_width-1)] = im_width-1
        temp = data[imagex,imagey]
        indnew = (temp<1.5)*(temp>0)*ind
        if np.sum(indnew) == 0:continue
        out_result = np.reshape(out_result,[-1])
        out_result[indnew] = temp[indnew]
        out_result = np.reshape(out_result,[nl,ns])
        out_result[out_result<0] = 0
        out_result[out_result > 1.5] = 0

    outfile = outdir + '2019_month%02d'%(kmonth+1)+'.tif'
    write_image_gdal(out_result,ns,nl,1,geog,proj,outfile)

def doMultiple(param):
    return sampling(int(param[0]))


if __name__ == '__main__':
    multiprocessing.freeze_support()


    ####multiple
    start = time.time()
    param = []
    for i in range(0,13):
        param.append([i])
    print(param[0])
    # doMultiple(param[1])
    pool = Pool(min(24, cpu_count()))
    for p in param:
        pool.apply_async(doMultiple, (p,))
    pool.close()
    pool.join()
    end = time.time()
    print('time cost: ', end - start, 's')
