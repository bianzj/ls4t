from util.util import *
from util.util_constant import *
from pyhdf.SD import SD, SDC
import time
import os
os.environ['PROJ_LIB'] = r'C:\Users\zzz\anaconda3\envs\patrol\Library\share\proj'

"""
注，需要先用modistool转化投影
处理MCD15A3H4天的LAI产品，并将其存储为tif
"""

years = [2016,2017,2018,2019,2020,2021,2022]
year = years[1]

indir_raw = r"H:\LAI\%04d\raw\\" % year
indir_med = r"H:\LAI\%04d\med\\" % year
indir_tif = r"H:\LAI\%04d\tif\\" % year
outdir_interpolation = r"H:\LAI\%04d\lai\\" % year
outdir_fvc =  r"H:\LAI\%04d\fvc\\" % year

mkdir_if_not_exist(indir_med)
mkdir_if_not_exist(indir_tif)
mkdir_if_not_exist(outdir_interpolation)
mkdir_if_not_exist(outdir_fvc)

indir_slstr_tif = r'H:\Sentinel-3\%04d\tif\\' % year

targetArea = r'H:\Sentinel-3\base\type\type_heihe_1000_utm47N.tif'
ifextract = 0
ifcut = 0
ifinterpolation = 0
iffvc = 1

def lai_normalize(lai):
    lai[lai == 250] = 0  # 250 城市
    lai[lai == 251] = 0  # 251 “永久”湿地/淹没的沼泽地
    lai[lai == 252] = 0  # 252 常年的雪、冰
    lai[lai == 253] = 0  # 253 贫瘠、稀疏植被的土地覆盖(岩石、苔原、沙漠)
    lai[lai == 254] = 0  # 254 水体或盐地
    lai[lai == 255] = 0  # 255 反射率产品或分类没有值
    lai = lai * 0.1
    return lai

def cut_tif_bytif(prefile_dir,targetArea_dir,outfile_dir):
    """
    使用目标区域tif裁剪tif，同时重投影重采样
    :param prefile_dir: 原数据
    :param targetArea_dir: 目标格式
    :param outfile_dir: 输出
    :return: none
    """
    '''读取目标区域信息'''
    dataset = gdal.Open(targetArea_dir)
    if dataset == None:
        print(targetArea_dir+ " ")
    [data, ns, nl, im_bands, geog, proj] = read_image_gdal(targetArea_dir)
    nsi = np.zeros([nl, ns])
    nli = np.zeros([nl, ns])
    for k in range(nl):
        nli[k, :] = k
        nsi[k, :] = np.linspace(0, ns - 1, ns)
    nli = np.reshape(nli, -1)
    nsi = np.reshape(nsi, -1)
    temp1, temp2 = imagexy2geo(dataset, nli, nsi)
    lon, lat = geo2lonlat(dataset, temp1, temp2)
    '''读取待裁剪区域信息'''
    [dataset,im_width,im_height,im_bands,g,p] = read_image_gdal(prefile_dir)
    dataset = gdal.Open(prefile_dir)
    data = dataset.ReadAsArray(0, 0, im_width, im_height)
    temp1, temp2 = lonlat2geo(dataset, lat, lon)
    imagex, imagey = geo2imagexy(dataset, temp1, temp2)
    '''裁剪'''
    if os.path.exists(outfile_dir) == 1:
        [out_result, ns, nl, im_bands, geog, proj] = read_image_gdal(outfile_dir)
    else:
        out_result = np.zeros([nl, ns])

    imagex = np.asarray(imagex, np.int_)
    imagey = np.asarray(imagey, np.int_)
    ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
    imagex[imagex < 0] = 0
    imagex[imagex > (im_height - 1)] = im_height - 1
    imagey[imagey < 0] = 0
    imagey[imagey > (im_width - 1)] = im_width - 1
    temp = data[imagex, imagey]
    indnew = (temp<250)*(temp>0)*ind
    # indnew = ind
    out_result = np.reshape(out_result, [-1])
    out_result[indnew] = temp[indnew]
    out_result = np.reshape(out_result, [nl, ns])
    '''输出'''
    write_image_gdal(out_result, ns, nl, 1, geog, proj, outfile_dir)
    print("save",outfile_dir," successful!")


def interpolation(lai_start,lai2_end):
    dif = (lai2_end - lai_start)/4
    lai1 = lai_start
    lai2 = lai1 + dif
    lai3 = lai2 + dif
    lai4 = lai3 + dif
    return lai1,lai2,lai3,lai4

def cal_fvc_from_lai(thetav,lai):
    G = 0.5
    rd = np.pi / 180.0
    costhetanv = np.cos(thetav * rd)
    fvc = 1 - exp(-G*lai/costhetanv)
    fvc[fvc>1] = 1
    fvc[fvc<0] = 0
    return fvc


if ifextract:
    fileNames = search_file(indir_raw,['hdf'])
    fileNum = len(fileNames)
    for k in range(fileNum):
        fileName = fileNames[k]
        print(k,fileName)
        infile = indir_raw +fileName
        # 打开hdf文件
        datasets = gdal.Open(infile)
        # 打开子数据集
        dsSubDatasets = datasets.GetSubDatasets()
        # 打开ndvi数据
        laiRaster = gdal.Open(dsSubDatasets[1][0])
        # 获取元数据
        metaData = datasets.GetMetadata()
        # for key, value in metaData.items():
        #   print('{key}:{value}'.format(key = key, value = value))
        # 获取数据时间
        time = metaData['RANGEBEGINNINGDATE']
        # 命名输出完整路径文件名
        outName = indir_med + fileName[:-4] + '.tif'
        # 进行几何校正
        geoData = gdal.Warp(outName, laiRaster,
                            dstSRS='EPSG:4326', format='GTiff',
                            resampleAlg=gdal.GRA_NearestNeighbour)
        del geoData

if ifcut:
    fileNames = search_file_rej(indir_med,['.tif'],'enp')
    fileNum = len(fileNames)

    for k in range(fileNum):
        fileName = fileNames[k]
        year_str = fileName[10:14]
        doy_str = fileName[14:17]
        infile = indir_med + fileName
        outfile = indir_tif + year_str + '_' + doy_str + "_lai.tif"
        print(k,outfile)
        cut_tif_bytif(infile,targetArea,outfile)

if ifinterpolation:
    fileNames = search_file_rej(indir_tif, ['lai'],'enp')
    fileNum = len(fileNames)
    fileNames.sort()
    for k in range(fileNum-1):
        fileName1 = fileNames[k]
        infile1 = indir_tif + fileName1
        print(k, infile1)
        doy1 = int(fileName1[5:8])
        if doy1 <= 365:
            doy2 = doy1 + 4
            print('%03d' % doy2)
            fileName2 = fileName1[0:5] + '%03d' % doy2 + "_lai.tif"
            infile2 = indir_tif + fileName2
            # if doy1 != 93: continue

            if not os.path.exists(infile2):
                [lai_1, width, height, bands, geog, proj] = read_image_gdal(infile1)
                write_image_gdal(lai_1, width, height, bands, geog, proj, infile2)

        doy2 = int(fileName2[5:8])
        # if doy2 - doy1 != 4: continue
        date_str = fileName1[5:8]
        date = int(date_str)

        outfile1 = outdir_interpolation + fileName1[0:5] + date_str + "_lai.tif"
        outfile2 = outdir_interpolation + fileName1[0:5] + "%03d" %(date + 1) + "_lai.tif"
        outfile3 = outdir_interpolation + fileName1[0:5] + "%03d" %(date + 2) + "_lai.tif"
        outfile4 = outdir_interpolation + fileName1[0:5] + "%03d" %(date + 3) + "_lai.tif"
        outfile5 = outdir_interpolation + fileName1[0:5] + "%03d" %(date + 4) + "_lai.tif"

        [lai_1, width, height, bands, geog, proj] = read_image_gdal(infile1)
        [lai_2, width, height, bands, geog, proj] = read_image_gdal(infile2)
        lai_1 = lai_normalize(lai_1)
        lai_2 = lai_normalize(lai_2)
        lai1,lai2,lai3,lai4 = interpolation(lai_1,lai_2)
        write_image_gdal(lai1,width, height, bands, geog, proj,outfile1)
        write_image_gdal(lai2, width, height, bands, geog, proj, outfile2)
        write_image_gdal(lai3, width, height, bands, geog, proj, outfile3)
        write_image_gdal(lai4, width, height, bands, geog, proj, outfile4)
        if k != fileNum-2: continue
        write_image_gdal(lai_2, width, height, bands, geog, proj, outfile5)

if iffvc:
    filesName = search_file_rej(indir_slstr_tif, ['vza_nadir'],'enp')
    filesNum = len(filesName)
    for fileI in range(filesNum):
        # for fileI in range(243,244):
        fileName = filesName[fileI][:-14]
        doyStr = fileName[-3:]
        doy = int(doyStr)
        year_str = fileName[4:8]
        infilelai_dir = outdir_interpolation + year_str+ '_' + doyStr + "_lai.tif"
        print( infilelai_dir)
        infileVzaN = indir_slstr_tif + fileName + '_vza_nadir.tif'
        infileVzaO = indir_slstr_tif + fileName + '_vza_obliq.tif'
        c1 = os.path.exists(infileVzaN)
        c2 = os.path.exists(infileVzaO)
        if c1 * c2 == 0: continue

        [vza_n, ns, nl, nb, geog, proj] = read_image_gdal(infileVzaN)
        # [vaa_n, ns, nl, nb, geog, proj] = read_image_gdal(infileVaaN)
        [vza_o, ns, nl, nb, geog, proj] = read_image_gdal(infileVzaO)
        # [vaa_o, ns, nl, nb, geog, proj] = read_image_gdal(infileVaaO)

        [lai, width, height, bands, geog, proj] = read_image_gdal(infilelai_dir)

        fvc_n = cal_fvc_from_lai(vza_n/100,lai)
        fvc_o = cal_fvc_from_lai(vza_o/100, lai)


        outfilefvc_n = outdir_fvc + fileName + '_fvcN.tif'
        outfilefvc_o = outdir_fvc + fileName + '_fvcO.tif'


        write_image_gdal(fvc_n, width, height, bands, geog, proj, outfilefvc_n)
        write_image_gdal(fvc_o, width, height, bands, geog, proj, outfilefvc_o)
















