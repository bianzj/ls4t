import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *

'''2025.10.27'''
'''Musyq fvc拼接,存储成wgs84，h5格式'''
'''0.005（500m）'''

infile_type = r"/home/hero/data/type/type_sin.tif"
infile_type_500 = r"/home/hero/data/type/type_sin_500.tif"
infile_type_wgs84 = r"/home/hero/data/type/type_world_1000.tif"
infile_type_wgs84_500 = r"/home/hero/data/type/type_world_500.tif"
indir = r"/media/hero/lsct02/Musyq/FVC/"
out_mosaic = r"/media/hero/lsct02/fvc/"
outdir_h5 = r'/media/hero/lsct02/fvc_h5/'
mkdir_if_not_exist(out_mosaic)
mkdir_if_not_exist(outdir_h5)


if not os.path.exists(infile_type_500):
    [type, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile_type)
    ds = gdal.Open(infile_type)
    # 获取原始分辨率并计算一半分辨率
    transform = ds.GetGeoTransform()
    x_res = transform[1] / 2  # 原始x分辨率的一半
    y_res = -transform[5] / 2  # 原始y分辨率的一半(取绝对值)
    gdal.Warp(infile_type_500, ds, format='GTiff', xRes=x_res, yRes=y_res,
              resampleAlg=gdal.GRIORA_NearestNeighbour)
    ds = None

if not os.path.exists(infile_type_wgs84_500):
    [type_wgs84, ns_wgs84, nl_wgs84, nb_wgs84, geog_type_wgs84, proj_type_wgs84] = read_image_gdal(infile_type_wgs84)
    ds = gdal.Open(infile_type_wgs84)
    gdal.Warp(infile_type_wgs84_500, ds, format='GTiff',  xRes=0.005, yRes=0.005,outputBounds = (-180,-90,180,90),
                  resampleAlg=gdal.GRIORA_NearestNeighbour)
    ds = None

[type, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile_type_500)
[type_wgs84, ns_wgs84, nl_wgs84, nb_wgs84, geog_type_wgs84, proj_type_wgs84] = read_image_gdal(infile_type_wgs84_500)


for y in range(2002,2013):
    for doy in range(0,367):

        indir_day = indir + "%04d//" % y + "A%04d" % y + "%03d//" % doy
        if not os.path.exists(indir_day): continue
        outdir = out_mosaic + "%04d//" % y
        mkdir_if_not_exist(outdir)
        print(y,doy)
        fileNames = search_file(indir_day,['h5'])
        fileNames.sort()
        fileNum = len(fileNames)
        save = np.zeros([nl,ns])

        outfile = outdir + fileNames[0][0:22] + ".tif"
        print(outfile)
        if not os.path.exists(outfile):
            for fileName in fileNames:
                infile = indir_day + fileName
                hv = fileName[-13:-7]
                h_num = int(hv[1:3])
                v_num = int(hv[4:7])
                # print(h_num,v_num)
                datasets = gdal.Open(infile)
                try:
                    # 打开子数据集
                    dsSubDatasets = datasets.GetSubDatasets()
                    # 打开ndvi数据
                    productName = dsSubDatasets[0][1]
                    if str(productName)[-25:-17] == "FVC_500m":
                        laiRaster = gdal.Open(dsSubDatasets[0][0])
                    else:
                        laiRaster = gdal.Open(dsSubDatasets[1][0])
                    im_width = laiRaster.RasterXSize
                    im_height = laiRaster.RasterYSize
                    lai = laiRaster.ReadAsArray(0, 0, im_width, im_height)
                except:
                    lai = np.zeros([2400,2400])
                save[v_num*2400:(v_num+1)*2400,h_num*2400:(h_num+1)*2400] = lai
                # print(v_num*1200,(v_num+1)*1200,h_num*1200,(h_num+1)*1200)
            tempfile = "/home/hero/data/%04dtemp.tif" % y
            print(tempfile)
            write_image_gdal_bigfile(save.astype('uint16'), ns, nl, nb, geog_type, proj_type, tempfile)
            infile = tempfile

            '''重投影'''
            srcSRS = proj_type
            dstSRS = proj_type_wgs84
            xRes = 0.005
            yRes = 0.005
            resample_method = gdal.GRIORA_NearestNeighbour
            ds = gdal.Open(infile)
            gdal.Warp(outfile, ds, format='GTiff', srcSRS=srcSRS, dstSRS=dstSRS, xRes=xRes, yRes=yRes,outputBounds = (-180,-90,180,90),
                    resampleAlg=resample_method,
                    creationOptions=['COMPRESS=LZW', 'PREDICTOR=2'])
            print(outfile)
            ds = None

        '''h5'''
        outdir_h5_year = outdir_h5 + "%04d//" % y
        mkdir_if_not_exist(outdir_h5_year)
        outfile_h5 = outdir_h5_year + "FVC_" + fileNames[0][15:22] + ".h5"
        if os.path.exists(outfile_h5): continue
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile)

        f = h5py.File(outfile_h5,"w")
        d1 = f.create_dataset("data",data = data,dtype="uint16",compression = "gzip")
        f.close()
        print(outfile_h5)