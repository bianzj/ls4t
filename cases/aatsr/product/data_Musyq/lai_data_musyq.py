import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *

'''Musyq LAI拼接,存储成wgs84，h5格式'''
'''0.01（500m->1km）'''

infile_type = r"/media/airt/D/rawdata/laidata/type/type_sin.tif"
infile_type_wgs84 = r"/media/airt/D/rawdata/laidata/type/type_world_1000.tif"
[type, ns_sin, nl_sin, nb, geog_type, proj_type] = read_image_gdal(infile_type)
[type_wgs84, ns_wgs84, nl_wgs84, nb_wgs84, geog_type_wgs84, proj_type_wgs84] = read_image_gdal(infile_type_wgs84)

indir = r"/media/airt/D/rawdata/laidata/other/"
out_reproj = r"/media/airt/D/rawdata/laidata/other/reproj/"
out_h5 = r"/media/airt/D/rawdata/laidata/"
mkdir_if_not_exist(out_reproj)

for y in range(2019,2021):
    for doy in range(0,367):
        indir_day = indir + "%04d//" % y + "A%04d" % y + "%03d//" % doy
        if not os.path.exists(indir_day): continue
        outdir = out_reproj + "%04d//" % y
        mkdir_if_not_exist(outdir)
        print(y,doy)
        fileNames = search_file(indir_day,['h5'])
        fileNum = len(fileNames)
        save = np.zeros([nl_sin,ns_sin])
        if os.path.exists(out_h5+ "%04d//" % y + "LAI_" + fileNames[0][15:22] + ".h5"): continue
        for fileName in fileNames:
            infile = indir_day + fileName
            hv = fileName[-13:-7]
            h_num = int(hv[1:3])
            v_num = int(hv[4:7])
            # print(h_num,v_num)
            datasets = gdal.Open(infile)
            # 打开子数据集
            dsSubDatasets = datasets.GetSubDatasets()
            # 打开ndvi数据
            productName = dsSubDatasets[0][1]
            if str(productName)[-25:-17] == "LAI_500m":
                laiRaster = gdal.Open(dsSubDatasets[0][0])
            else:
                laiRaster = gdal.Open(dsSubDatasets[1][0])
            im_width = laiRaster.RasterXSize
            im_height = laiRaster.RasterYSize
            lai = laiRaster.ReadAsArray(0, 0, im_width, im_height)
            lai = resize_data(lai,im_height/2,im_width/2,'cv2.INTER_NEAREST')
            save[v_num*1200:(v_num+1)*1200,h_num*1200:(h_num+1)*1200] = lai
            # print(v_num*1200,(v_num+1)*1200,h_num*1200,(h_num+1)*1200)
        tempfile = outdir  + "temp.tif"
        print(tempfile)
        write_image_gdal(save.astype('uint16'),ns_sin, nl_sin, nb, geog_type, proj_type,tempfile)
        infile = tempfile

        '''重投影'''
        srcSRS = proj_type
        dstSRS = proj_type_wgs84
        xRes = 0.01
        yRes = 0.01
        resample_method = gdal.GRIORA_NearestNeighbour
        outfile = outdir + fileName[0:22] + ".tif"
        ds = gdal.Open(infile)
        gdal.Warp(outfile, ds, format='GTiff', srcSRS=srcSRS, dstSRS=dstSRS, xRes=xRes, yRes=yRes,outputBounds = (-180,-90,180,90),
                  resampleAlg=resample_method)
        print(outfile)
        [data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(outfile)

        '''h5'''
        outdir_h5 = out_h5+ "%04d//" % y
        mkdir_if_not_exist(outdir_h5)
        outfile_h5 = outdir_h5 + "LAI_" + fileNames[0][15:22] + ".h5"
        f = h5py.File(outfile_h5,"w")
        d1 = f.create_dataset("data",data = data,dtype="uint16",compression = "gzip")
        f.close()
        print(outfile_h5)