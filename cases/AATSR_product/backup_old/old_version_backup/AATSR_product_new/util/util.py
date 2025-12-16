import os
import numpy as np
import pandas as pd
# import cv2
from osgeo import gdal
from osgeo import osr,ogr
import h5py
import re
import scipy
import xlrd
import os
import struct
import netCDF4
import seaborn as sns
import matplotlib.pylab as plt
from matplotlib.colors import LogNorm
from pylab import *
import gzip
import shutil
from scipy.linalg import lstsq
from scipy import stats
from scipy.optimize import minimize
from scipy.optimize import least_squares
from scipy.interpolate import griddata
from sklearn.linear_model import Lasso
from sklearn.linear_model import LassoCV
from sklearn.linear_model import RidgeCV
from sklearn.linear_model import BayesianRidge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import BayesianRidge
from sklearn.linear_model import LinearRegression


########################################################################################################################

'''
util_constant
'''
rd = np.pi/180.0
planck_c1 = 11910.439340652
planck_c2 = 14388.291040407
temperature_threshold = 100
temperature_zero = 273.15

'''
util_file
'''
def search(dir):
    '''
    查找路径下所有的文件和文件夹
    :param dir: 路径
    :return: 文件和文件夹名字
    '''
    results = os.listdir(dir)
    return results


def search_file(dir,specstr):
    '''
    查找某个路径下，含有特定标识的文件，需要list把标识括起来，即使只有1个
    :param dir: 路径
    :param specstr: 特定的标识
    :return: 文件名
    '''
    results = []
    num = np.size(specstr)
    if num == 0:
        results = os.listdir(dir)
    elif num==1:
        specstr0 = specstr[0]
        results += [x for x in os.listdir(dir) if
                    os.path.isfile(os.path.join(dir, x)) and
                    specstr0 in x]
    elif num==2:
        specstr1 = specstr[0]
        specstr2 = specstr[1]
        results += [x for x in os.listdir(dir) if
                    os.path.isfile(os.path.join(dir, x)) \
                    and specstr1 in x
                    and specstr2 in x]
    elif num==3:
        specstr1 = specstr[0]
        specstr2 = specstr[1]
        specstr3 = specstr[2]
        results += [x for x in os.listdir(dir) if
                    os.path.isfile(os.path.join(dir, x)) \
                    and specstr1 in x
                    and specstr2 in x
                    and specstr3 in x]
    return results
def search_dir(dir,specstr):
    '''
    查找某个路径下，含有特定标识的文件夹，需要list把标识括起来，即使只有1个
    :param dir: 路径
    :param specstr:
    :return:
    '''
    results = []
    num = len(specstr)
    if num == 0:
        results = os.listdir(dir)
    elif num==1:
        results += [x for x in os.listdir(dir) if
                    os.path.isdir(os.path.join(dir, x)) and
                    specstr in x]
    elif num==2:
        specstr1 = specstr[0]
        specstr2 = specstr[1]
        results += [x for x in os.listdir(dir) if
                    os.path.isdir(os.path.join(dir, x)) \
                    and specstr1 in x
                    and specstr2 in x]
    elif num==3:
        specstr1 = specstr[0]
        specstr2 = specstr[1]
        specstr3 = specstr[2]
        results += [x for x in os.listdir(dir) if
                    os.path.isdir(os.path.join(dir, x)) \
                    and specstr1 in x
                    and specstr2 in x
                    and specstr3 in x]
    return results


def search_file_rej(dir,specstr,rejstr):
    '''
    查找某个路径下，含有特定标识,又不含有某个标识的文件，需要list把标识括起来，即使只有1个，可以有多个“有”标识，但是只有1个“没有”标识
    :param dir: 路径
    :param specstr: “有”标识
    :param rejstr: “没有”标识
    :return: 文件名数组
    '''
    results = []
    num = len(specstr)
    if num == 0:
        results = os.listdir(dir)
    elif num==1:
        specstr0 = specstr[0]
        results += [x for x in os.listdir(dir) if
                    os.path.isfile(os.path.join(dir, x))
                    and specstr0 in x
                    and rejstr not in x]
    elif num==2:
        specstr1 = specstr[0]
        specstr2 = specstr[1]
        results += [x for x in os.listdir(dir) if
                    os.path.isfile(os.path.join(dir, x)) \
                    and specstr1 in x
                    and specstr2 in x
                    and rejstr not in x]
    elif num==3:
        specstr1 = specstr[0]
        specstr2 = specstr[1]
        specstr3 = specstr[2]
        results += [x for x in os.listdir(dir) if
                    os.path.isfile(os.path.join(dir, x)) \
                    and specstr1 in x
                    and specstr2 in x
                    and specstr3 in x
                    and rejstr not in x]
    return results

def search_dir_rej(dir,specstr,rejstr):
    '''
    查找某个路径下，含有特定标识,又不含有某个标识的文件夹，需要list把标识括起来，即使只有1个，可以有多个“有”标识，但是只有1个“没有”标识
    :param dir: 路径
    :param specstr: “有”标识
    :param rejstr: “没有”标识
    :return: 文件夹名数组
    '''
    results = []
    num = len(specstr)
    if num == 0:
        results = os.listdir(dir)
    elif num==1:
        specstr0 = specstr[0]
        results += [x for x in os.listdir(dir) if
                    os.path.isdir(os.path.join(dir, x))
                    and specstr0 in x
                    and rejstr not in x]
    elif num==2:
        specstr1 = specstr[0]
        specstr2 = specstr[1]
        results += [x for x in os.listdir(dir) if
                    os.path.isdir(os.path.join(dir, x)) \
                    and specstr1 in x
                    and specstr2 in x
                    and rejstr not in x]
    elif num==3:
        specstr1 = specstr[0]
        specstr2 = specstr[1]
        specstr3 = specstr[2]
        results += [x for x in os.listdir(dir) if
                    os.path.isdir(os.path.join(dir, x)) \
                    and specstr1 in x
                    and specstr2 in x
                    and specstr3 in x
                    and rejstr not in x]
    return results


def remove_file(dir, specstr):
    '''
    删除某个路径下，含有某个标识的所有文件
    :param dir: 路径
    :param specstr:标识
    :return: 没有
    '''
    for x in os.listdir(dir):
        fp = os.path.join(dir, x)
        # 如果文件存在，返回true
        if re.search(specstr, x) is not None:
            print(fp)
            os.remove(fp)


def rename_file(dir, specstr):
    '''
    对路径下，含有某个标识的文件批量修改名称
    :param dir: 路径
    :param specstr: 标识
    :return: 没有
    '''
    for x in os.listdir(dir):
        fp = os.path.join(dir, x)
        # print(x)
        # 如果文件存在，返回true
        if re.search(specstr, x) is not None:
            [filename, hz] = os.path.splitext(x)
            outfile = dir + filename + '_test.tif'
            print(fp)
            print(outfile)
            if os.path.exists(outfile) == 1:
                os.remove(outfile)
            os.rename(fp, outfile)


def batch_rename(work_dir, old_ext, new_ext):
    """
    This will batch rename a group of files in a given directory,
    once you pass the current and new extensions
    """
    # files = os.listdir(work_dir)
    for filename in os.listdir(work_dir):
        # Get the file extension
        split_file = os.path.splitext(filename)
        # Unpack tuple element
        root_name, file_ext = split_file
        # Start of the logic to check the file extensions, if old_ext = file_ext
        if old_ext == file_ext:
            # Returns changed name of the file with new extention
            newfile = root_name + new_ext

            # Write the files
            os.rename(
                os.path.join(work_dir, filename),
                os.path.join(work_dir, newfile)
            )
    print("rename is done!")
    print(os.listdir(work_dir))


def move_file(infile,outfile):
    '''
    修改名称，其实是修改路径
    :param infile: 旧名称
    :param outfile: 新名称
    :return: 没有
    '''
    os.rename(infile,outfile)


def read_txt_float(filename):
    '''
    读取txt文件，并将其按照float存储，行列号作为索引的矩阵
    :param filename: 文件路径
    :return: float数组
    '''
    mydata = []
    with open(filename) as f:
        lines = f.readline()
        while lines:
            line = lines.split()
            mydata.append(line)
            lines = f.readline()
    mydata = np.asarray(mydata,dtype=float)
    return mydata


def read_txt_str(filename, spt):
    '''
    读取文件数据，然后按照特定的约束进行解析，随后按照行列进行存储
    :param filename: 文件名称
    :param spt: 解析表示
    :return: 解析后数组
    '''
    mydata = []
    with open(filename) as f:
        lines = f.readline()
        while lines:
            line = lines.split(spt)
            mydata.append(line)
            lines = f.readline()
    return mydata


def read_txt_array(filename, num_pass, num_col):
    '''
    限定读取txt文本数据，考虑了要跳过的行，但是必须要给定列数
    :param filename: 文件名
    :param num_pass: 要跳过的行数
    :param num_col: 数据的列数
    :return: 返回数组
    '''
    f = open(filename, 'r')
    temp = f.readlines()
    temp = np.asarray(temp)
    temp = temp[num_pass:]
    num = len(temp)
    lut = np.zeros([num, num_col])
    for k in range(num):
        if (temp[k] == ""): continue
        tempp = (re.split(r'\s+', temp[k].strip()))
        lut[k, :] = np.asarray(tempp)
    return lut

def read_excel_sheet(filename,sheetname='Sheet1'):
    '''
    读取excel数据，返回册数据集，这里用了xlrd
    :param filename:文件名
    :param sheetname: 册名
    :return: 册数据集
    '''
    ExcelFile = xlrd.open_workbook(filename)
    ExcelFile.sheet_names()
    sheet = ExcelFile.sheet_by_name(sheetname)
    return sheet

def read_excel_sheet_col(filename,col,sheetname='Sheet1'):
    '''
    读取excel数据，返回某个册的某列数据，这里用了pandas
    :param filename: 文件名
    :param col: 某列
    :param sheetname:册名
    :return: 列数组
    '''
    df = pd.read_excel(filename,sheet_name=sheetname)
    colvalue = df.ix[:,col]
    return colvalue

def read_excel_sheet_row(filename,row,sheetname='Sheet1'):
    '''
    读取excel数据，然后某册某行数据，这里用了pandas
    :param filename: 文件名
    :param row: 某行
    :param sheetname:某册
    :return: 行数组
    '''
    ExcelFile = xlrd.open_workbook(filename)
    ExcelFile.sheet_names()
    sheet = ExcelFile.sheet_by_name(sheetname)
    rowvalue = sheet.row_values(row)
    return rowvalue

def read_binary(filename, type = int):
    '''
    读取二进制文件，并转成特定格式，默认是整型
    :param filename:文件名
    :param type: 数据格式
    :return: 数组
    '''
    fin = open(filename, 'rb')
    temp =[]
    while True:
        fileContent = fin.read(4)
        num = len(fileContent)
        if num !=4:
            break
        tp = struct.unpack('l',fileContent)
        temp.extend(tp)
    fin.close()
    temp = np.array(temp,dtype=type)
    return temp

def read_image_gdal(filename):
    '''
    使用gdal,读取图像文件，并格式输出
    :param filename:文件名
    :return: 文件，列数，行数，波段数，地理信息，投影信息
    '''
    dataset = gdal.Open(filename)
    if dataset == None:
        print(filename + "文件无法打开")
        return
    im_width = dataset.RasterXSize
    im_height = dataset.RasterYSize
    im_bands = dataset.RasterCount
    im_data = dataset.ReadAsArray(0, 0, im_width, im_height)
    im_geotrans = dataset.GetGeoTransform()
    im_proj = dataset.GetProjection()
    return im_data,im_width,im_height,im_bands,im_geotrans,im_proj

def read_image_dataset_gdal(filename):
    '''
    读取图像文件，特别的，会返回数据集
    :param filename: 文件名
    :return: 文件，列数，行数，波段数，地理信息，投影信息，数据集
    '''
    dataset = gdal.Open(filename)
    if dataset == None:
        print(filename + "文件无法打开")
        return
    im_width = dataset.RasterXSize
    im_height = dataset.RasterYSize
    im_bands = dataset.RasterCount
    im_data = dataset.ReadAsArray(0, 0, im_width, im_height)
    im_geotrans = dataset.GetGeoTransform()
    im_proj = dataset.GetProjection()
    return im_data,im_width,im_height,im_bands,im_geotrans,im_proj,dataset

def read_image_raw(filename, ns, nl, nb, type = np.int_):
    '''
    在给定行列号的情况下，读取二进制文件，需要指定数据类型，确定每次读取的步长
    :param filename:文件名
    :param ns:列数
    :param nl: 行数
    :param nb:波段数
    :param type:数据类型
    :return: 数组
    '''
    fb = open(filename, 'rb')
    mydata = np.zeros((ns,nl,nb))
    for kb in range(nb):
        for ks in range(ns):
            for kl in range(nl):
                if type == np.int_:
                    arr = fb.read(2)
                else:
                    arr = fb.read(4)
                elem = struct.unpack('h',arr)[0]
                mydata[ks][kl][kb] = elem
    return mydata


def read_image_Nc_group(fileName, groupName, objectName,ifscale=0):
    '''
    读取NC格式的数据，需要指定是否需要缩放转换
    :param fileName:文件名
    :param groupName: 组名
    :param objectName: 目标名
    :param ifscale: 是否缩放
    :return: 数组
    '''
    dataset = netCDF4.Dataset(fileName)
    if ifscale ==0:
        dataset.groups[groupName].variables[objectName].set_auto_maskandscale(False)
    predata = np.asarray(dataset.groups[groupName].variables[objectName][:])
    return predata

def read_image_Nc(fileName, objectName,ifscale):
    '''
    读取NC格式的数据，没有组名，也需要指定是否需要缩放
    :param fileName:  文件名
    :param objectName:  目标名
    :param ifscale:  是否缩放
    :return:  数组
    '''
    dataset = netCDF4.Dataset(fileName)
    if ifscale ==0:
        dataset.variables[objectName].set_auto_maskandscale(False)
    predata = np.asarray(dataset.variables[objectName][:])
    return predata

def getDatafromNc(fileName, objectName):
    '''
    读取NC文件，文件名和项目名
    :param fileName: 文件名
    :param objectName: 项目名
    :return: 值
    '''
    try:
        dataset = netCDF4.Dataset(fileName)
    except (OSError, RuntimeError):
        print(fileName + ' File Error')
        predata = np.asarray(None)
    else:
        try:
            predata = np.asarray(dataset.variables[objectName][:])
        except RuntimeError:
            print(fileName + ' Attribute Error')
            predata = np.asarray(None)
        finally:
            dataset.close();
    return predata

def write_h5py_item(infile,name,data,dtype,compression=None):
    '''
    Write h5py
    para infile: h5py
    para name: string
    para data: numpy array
    para dtype: string
    para compression: string
    '''
    if not os.path.exists(infile):
        f = h5py.File(infile,'w')
    else:
        f = h5py.File(infile,'a')
    f.create_dataset(name,data=data,dtype=dtype,compression=compression)
    f.close()

def read_h5py_item(infile,name):
    '''
    para infile: h5py
    para name: string
    '''
    f = h5py.File(infile,'r')
    data = f[name]
    return data


def write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType = 'GTiff'):
    '''
    保存数据，输出成tif格式
    :param im_data: 数组
    :param im_width:  列数
    :param im_height:  行数
    :param im_bands:  波段数
    :param im_trans:  地理坐标
    :param im_proj:  投影坐标
    :param path:  路径
    :return: 无
    '''
    if 'int8' in im_data.dtype.name:
        datatype = gdal.GDT_Byte
    elif 'uint16' in im_data.dtype.name:
        datatype = gdal.GDT_UInt16
    elif 'int16' in im_data.dtype.name:
        datatype = gdal.GDT_Int16
    else:
        datatype = gdal.GDT_Float32
    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    elif len(im_data.shape) == 2:
        im_data = np.array([im_data])
    else:
        im_bands, (im_height, im_width) = 1, im_data.shape
    driver = gdal.GetDriverByName(imageType)
    dataset = driver.Create(path, im_width, im_height, im_bands, datatype)
    if (dataset != None and im_trans != '' and im_proj != ''):
        dataset.SetGeoTransform(im_trans)
        dataset.SetProjection(im_proj)
    for i in range(im_bands):
        dataset.GetRasterBand(i+1).WriteArray(im_data[i])
    del dataset


def read_dataset_gdal(fileName):
    '''
    读取数据，返回数据集，多用于基于数据集的数据转换
    :param fileName: 数据名
    :return: 数据集
    '''
    dataset = gdal.Open(fileName)
    return dataset


def write_h5py_item(infile,name,data,dtype,compression=None):
    '''
    Write h5py
    para infile: h5py
    para name: string
    para data: numpy array
    para dtype: string
    para compression: string
    '''
    if not os.path.exists(infile):
        f = h5py.File(infile,'w')
    else:
        f = h5py.File(infile,'a')
    f.create_dataset(name,data=data,dtype=dtype,compression=compression)
    f.close()

def write_h5py_file(infile,name_list,data_list,dtype_list,compression=None,ifcover = 0):
    '''
    Write h5py
    para infile: h5py
    para name_list:
    para data_list:
    para dtype_list:
    para compression: string
    '''
    item_num = len(name_list)
    if item_num == 0:
        return 0
    if os.path.exists(infile):
        if ifcover: mode = "w"
        else: mode = "a"
        f = h5py.File(infile,mode)
    else:
        f = h5py.File(infile,'w')
    for i,name in enumerate(name_list):
        f.create_dataset(name,data=data_list[i],dtype=dtype_list[i],compression=compression)
    f.close()

def read_h5py_item(infile,name):
    '''
    para infile: h5py
    para name: string
    '''
    f = h5py.File(infile,'r')
    data = f[name]
    return np.array(data)

def read_h5py_items(infile,names):
    '''
    para infile: h5py
    para name: string
    '''
    data_list = []
    f = h5py.File(infile)
    for name in names:
        if name in f:
            data_list.append(np.array(f[name]))
        else:
            data_list.append([])
    return data_list

def read_h5py_file(infile):
    '''
    para infile: h5py
    '''
    f = h5py.File(infile)
    name_list = []
    data_list = []
    for key in f.keys():
        name_list.append(key)
        data_list.append(np.array(f[key]))
    return name_list,data_list

'''
util_data
'''


def resize_data(preArray, nl, ns, method = 'cv2.INTER_LINEAR'):
    '''
    数组的缩放，用到了cv2库，方法主要有：
    ‘最邻近‘cv2.INTER_NEAREST，‘双线性插值’cv2.INTER_LINEAR，‘三次立方’cv2.INTER_CUBIC，’等面积’cv2.INTER_AREA
    :param preArray: 原有数组
    :param nl: 目标行数
    :param ns: 目标列数
    :param method:  缩放方法,默认是双线性插值
    :return: 返回缩放后的数组
    '''
    ns = np.int(ns)
    nl = np.int(nl)
    data = cv2.resize(preArray,(ns,nl),interpolation=0)
    return data

def resize_data_ratio(preArray, ratio = 0.5, method = 'cv2.INTER_LINEAR'):
    '''
    并不是给定行列号，而是行列号的比例确定新数据的行列号
    :param preArray: 原有数组
    :param ratio: 转换比例
    :param method:  缩放方法，默认是双线性插值
    :return: 新数组
    '''
    [pre_nl,pre_ns] = np.shape(preArray)
    ns = np.int(pre_ns*ratio)
    nl = np.int(pre_nl*ratio)
    data = cv2.resize(preArray,(ns,nl),interpolation=method)
    return data

def getPointfromImage(data, imagex_, imagey_, dist= 0, dn = 3,  minThreshold = -100, maxThreshold = 100):
    '''
    从图像中找点位对应的值，如有必要进行简单的统计
    :param data: 图像数据
    :param imagex_: 行列号，x坐标
    :param imagey_: 行列号，y坐标
    :param dist: 距离，默认0
    :param dn: 绝对值大小，默认3倍
    :param minThreshold: 绝对最小阈值
    :param maxThreshold: 绝对最大阈值
    :return: 图像值或统计结果数组
    '''
    size = np.size(imagex_)
    result = np.zeros(size)
    for k in range(size):
        imagex = imagex_[k]
        imagey = imagey_[k]
        x1 = imagex - dist
        x2 = imagex + dist + 1
        y1 = imagey - dist
        y2 = imagey + dist + 1
        temp = data[x1:x2, y1:y2]
        ### 绝对大小阈值判断
        ind = (temp > minThreshold) * (temp < maxThreshold)
        if np.sum(ind) < 1: continue
        ### 相对大小阈值判断
        std = np.std(temp[ind])
        ave = np.average(temp[ind])
        indd = (temp > minThreshold) * (temp < maxThreshold) *(temp < ave+dn*std) *(temp > ave-dn*std)
        if np.sum(indd) < 1: continue
        result[k] = np.average(temp[indd])
    return result

def mkdir_if_not_exist(dir_name, is_delete=False):
    """
    创建文件夹
    :param dir_name: 文件夹
    :param is_delete: 是否删除
    :return: 是否成功
    """
    try:
        if is_delete:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                print("Path exists, remove and recreate")

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print("Created path:" + dir_name)
        return True
    except Exception as e:
        return False

def un_gz(file_name,infile,outdir):
    '''
    解压gz文件
    :param file_name:要解压文件名称
    :param infile:要解压文件位置
    :param outdir:输出位置
    '''
    mkdir_if_not_exist(outdir)
    f_name = outdir + file_name.replace(".gz", "")
    # 获取文件的名称，去掉
    g_file = gzip.GzipFile(infile + file_name)
    # 创建gzip对象
    open(f_name, "wb+").write(g_file.read())
    # gzip对象用read()打开后，写入open()建立的文件里。
    g_file.close()  # 关闭gzip对象
    print("Unzip " + file_name + " finished!")
'''
util_map
'''


def getSRSPair(dataset):
    '''
    获得给定数据的投影参考系和地理参考系
    :param dataset: GDAL地理数据
    :return: 投影参考系和地理参考系
    '''
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(dataset.GetProjection())
    geosrs = prosrs.CloneGeogCS()
    return prosrs, geosrs

def geo2lonlat(dataset, x, y):
        '''
        将投影坐标转为经纬度坐标（具体的投影坐标系由给定数据确定）
        :param dataset: GDAL地理数据
        :param x: 投影坐标x
        :param y: 投影坐标y
        :return: 投影坐标(x, y)对应的经纬度坐标(lon, lat)
        '''
        prosrs, geosrs = getSRSPair(dataset)
        ct = osr.CoordinateTransformation(prosrs, geosrs)
        x = np.reshape(x, [-1])
        y = np.reshape(y, [-1])
        temp = np.asarray([x, y])
        temp = np.transpose(temp)
        coords = np.asarray(ct.TransformPoints(temp))
        return coords[:,0],coords[:,1]

def lonlat2geo(dataset,lat,lon):
    '''
        将经纬度坐标转为投影坐标（具体的投影坐标系由给定数据确定），尤其注意，不同版本经度和纬度是反的
        :param dataset: GDAL地理数据
        :param lon: 地理坐标lon经度
        :param lat: 地理坐标lat纬度
        :return: 经纬度坐标(lon, lat)对应的投影坐标
    '''
    # dataset = gdal.Open(fileName, gdal.GA_ReadOnly)
    prosrs, geosrs = getSRSPair(dataset)
    ct = osr.CoordinateTransformation(geosrs, prosrs)
    lon = np.reshape(lon,[-1])
    lat = np.reshape(lat,[-1])
    temp = np.asarray([lon,lat])
    temp = np.transpose(temp)
    # temp = np.asarray([lat[0:2],lon[0:2]])
    coords = np.asarray(ct.TransformPoints(temp))

    return coords[:,0],coords[:,1]

def geo2imagexy(dataset, x, y):
    '''
    根据GDAL的六 参数模型将给定的投影或地理坐标转为影像图上坐标（行列号）
    :param dataset: GDAL地理数据
    :param x: 投影或地理坐标x
    :param y: 投影或地理坐标y
    :return: 影坐标或地理坐标(x, y)对应的影像图上行列号(row, col) nl ns
    '''
    trans = dataset.GetGeoTransform()
    a = np.array([[trans[2], trans[1]], [trans[5], trans[4]]])
    b = np.array([x - trans[0], y - trans[3]])
    return np.linalg.solve(a, b)  # 使用numpy的linalg.solve进行二元一次方程的求解

def imagexy2geo(dataset, row,col):
    '''
    根据GDAL的六参数模型将影像图上坐标（行列号）转为投影坐标或地理坐标（根据具体数据的坐标系统转换）
    :param dataset: GDAL地理数据
    :param row: 像素的行号
    :param col: 像素的列号
    :return: 行列号(row, col)对应的投影坐标或地理坐标(x, y)
    '''
    trans = dataset.GetGeoTransform()
    px = trans[0] + col * trans[1] + row * trans[2]
    py = trans[3] + col * trans[4] + row * trans[5]
    return px, py

def reproj_image_gdal(dataset_destination, dataset_source):
    '''
    源数据集重投影，提取与目标数据集对应的数据，数据来自源数据，结果的坐标与投影与目标数据一致
    :param dataset_destination: 目标数据集
    :param dataset_source: 源数据集
    :return: 数据集，其数据来自源，坐标与投影与目标一致
    '''
    ns1 = dataset_destination.RasterXSize
    nl1 = dataset_destination.RasterYSize
    nb1 = dataset_destination.RasterCount
    # data1,ns1,nl1,nb1,trans1,proj1,dataset1 = read_image_gdal_dataset(infile1)
    xi = np.zeros([nl1,ns1])
    yi = np.zeros([nl1,ns1])
    temp = np.linspace(0,nl1-1,nl1)
    for k in range(ns1):
        xi[:,k] = temp
        yi[:,k] = k
    temp11,temp12 = imagexy2geo(dataset_destination, xi, yi)
    lon,lat = geo2lonlat(dataset_destination, temp11, temp12)
    ns2 = dataset_source.RasterXSize
    nl2 = dataset_source.RasterYSize
    nb2 = dataset_source.RasterCount
    data2 = dataset_source.ReadAsArray(0, 0, ns2, nl2)
    temp21, temp22 = lonlat2geo(dataset_source, lat, lon)
    imagex, imagey = geo2imagexy(dataset_source, temp21, temp22)
    imagex = np.asarray(imagex+0.5, np.int)
    imagey = np.asarray(imagey+0.5, np.int)
    imagex[imagex < 0] = 0
    imagey[imagey < 0] = 0
    imagex[imagex >= nl2-1] = nl2-1
    imagey[imagey >= ns2-1] = ns2-1
    if nb2 <=1:
        data = np.zeros([nl1, ns1])
        data[:] = np.reshape(data2[imagex,imagey],[nl1,ns1])
    else:
        data = np.zeros([nb2,nl1, ns1])
        for k in range(nb2):
            temp = data2[k,:,:]*1.0
            data[k,:] =  np.reshape(temp[imagex,imagey],[nl1,ns1])
    return data

def reproj_image_ref_gdal(dataset_destination, dataset_reff, dataset_source):
    '''
    数据重投影到新区域，原数据并不直接到目标数据，原数据先数值变换到中间参考，然后通过中间参考投影信息到目标投影信息
    :param dataset_destination: 目标数据
    :param dataset_reff: 中间参考
    :param dataset_source: 原始数据
    :return: 新图像，其坐标和投影信息来自目标，数据信息来自源数据
    '''
    ns1 = dataset_destination.RasterXSize
    nl1 = dataset_destination.RasterYSize
    nb1 = dataset_destination.RasterCount
    # data1,ns1,nl1,nb1,trans1,proj1,dataset1 = read_image_gdal_dataset(infile1)
    xi = np.zeros([nl1,ns1])
    yi = np.zeros([nl1,ns1])
    temp = np.linspace(0,nl1-1,nl1)
    for k in range(ns1):
        xi[:,k] = temp
        yi[:,k] = k
    temp11,temp12 = imagexy2geo(dataset_destination, xi, yi)
    lon,lat = geo2lonlat(dataset_destination, temp11, temp12)
    ns2 = dataset_reff.RasterXSize
    nl2 = dataset_reff.RasterYSize
    nb2 = dataset_reff.RasterCount
    ns3 = dataset_source.RasterXSize
    nl3 = dataset_source.RasterYSize
    nb3 = dataset_source.RasterCount
    temp = dataset_source.ReadAsArray(0, 0, ns3, nl3)
    data2 = np.zeros([nb3,nl2, ns2])
    for k in range(nb3):
        data2[k,:,:] = resize_data(temp[k,:,:],nl2,ns2)
    temp21, temp22 = lonlat2geo(dataset_reff, lat, lon)
    imagex, imagey = geo2imagexy(dataset_reff, temp21, temp22)
    imagex = np.asarray(imagex+0.5, np.int)
    imagey = np.asarray(imagey+0.5, np.int)

    imagex[imagex < 0] = 0
    imagey[imagey < 0] = 0
    imagex[imagex >= nl2-1] = nl2-1
    imagey[imagey >= ns2-1] = ns2-1
    if nb3 <=1:
        data = np.zeros([nl1, ns1])
        data[:] = np.reshape(data2[imagex,imagey],[nl1,ns1])
    else:
        data = np.zeros([nb3,nl1, ns1])
        for k in range(nb3):
            temp = data2[k,:,:]*1.0
            data[k,:] =  np.reshape(temp[imagex,imagey],[nl1,ns1])
    return data


def loc2map(lat, lon, dataset):
    '''
    经纬度转图上行列号
    :param lat: 纬度
    :param lon: 经度
    :param dataset: 数据集，提供了地理和投影信息
    :return: 行列号
    '''
    ns2 = dataset.RasterXSize
    nl2 = dataset.RasterYSize
    nb2 = dataset.RasterCount
    data2 = dataset.ReadAsArray(0, 0, ns2, nl2)
    temp21, temp22 = lonlat2geo(dataset, lat, lon)
    imagex, imagey = geo2imagexy(dataset, temp21, temp22)
    # imagex = np.asarray(imagex+0.5, np.int)
    # imagey = np.asarray(imagey+0.5, np.int)
    imagex = np.asarray(imagex, np.int)
    imagey = np.asarray(imagey, np.int)
    return imagex,imagey


def calc_azimuth(lat1, lon1, lat2, lon2):
    '''
    计算地球上两点间的相对方位角
    :param lat1: 点1的纬度
    :param lon1: 点1的经度
    :param lat2: 点2的纬度
    :param lon2: 点2的经度
    :return: 相对方位角
    '''
    lat1_rad = lat1 * np.pi / 180
    lon1_rad = lon1 * np.pi / 180
    lat2_rad = lat2 * np.pi / 180
    lon2_rad = lon2 * np.pi / 180
    y = np.sin(lon2_rad - lon1_rad) * np.cos(lat2_rad)
    x = np.cos(lat1_rad) * np.sin(lat2_rad) - \
        np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(lon2_rad - lon1_rad)
    brng = np.arctan2(y, x) * 180 / np.pi
    return float((brng + 360.0) % 360.0)



def write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale, noDataValue = 65535, bandnumber = 1):
    '''
    导出用于gdal vrt的配置文件
    # 与函数配合使用，outfile为转成的文件路径，resampleAlg为重采样的
    # dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)
    :param vrtfile:  该配置文件名称
    :param datafile:  所要操作的文件名称
    :param xfile:  经度坐标文件 lon
    :param yfile:  纬度坐标文件 lat
    :param xscale:  列数
    :param yscale:  行数
    :param noDataValue: 无值填补
    :param bandnumber:  波段数据
    :return: 无
    '''
    f = open(vrtfile, 'w')
    f.write(r'<VRTDataset rasterXSize="%d"'%xscale + 'rasterYSize="%d">'%yscale)
    f.write('\n')
    f.write(r'  <Metadata domain="GEOLOCATION">')
    f.write('\n')
    f.write(r'    <MDI key="SRS">GEOGCS["WGS 84(DD)",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AXIS["Long",EAST],AXIS["Lat",NORTH]]</MDI>')
    # f.write(r'    <MDI key="SRS">GEOGCS["WGS 84(DD)",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG", "9122"],AUTHORITY["EPSG", "4490"]</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="X_DATASET">' + xfile + r'</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="X_BAND">1</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="PIXEL_OFFSET">0</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="PIXEL_STEP">1</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="Y_DATASET">' + yfile + r'</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="Y_BAND">1</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="LINE_OFFSET">0</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="LINE_STEP">1</MDI>')
    f.write('\n')
    f.write(r'  </Metadata>')
    f.write('\n')
    f.write(r'  <VRTRasterBand dataType = "Float32" band = "%d">'%bandnumber)
    f.write('\n')
    f.write(r'    <ColorInterp>Gray</ColorInterp >')
    f.write('\n')
    f.write(r'    <NoDataValue>%d</NoDataValue >'%noDataValue)
    f.write('\n')
    f.write(r'    <SimpleSource>')
    f.write('\n')
    f.write(r'      <SourceFilename relativeToVRT = "1" >' + datafile + r'</SourceFilename>')
    f.write('\n')
    f.write(r'      <SourceBand>1</SourceBand>')
    f.write('\n')
    f.write(r'    </SimpleSource>')
    f.write('\n')
    f.write(r'  </VRTRasterBand>')
    f.write('\n')
    f.write('</VRTDataset>')
    f.close()
    return 1


def eliminate_edge(data,edge=1):
    '''
    消除重采样后边界的异常值
    :param data: 数据
    :param edge: 要剔除数据的步长
    :return:  剔除边界的新数据
    '''
    dataa = data*1.0
    [nl,ns] = np.shape(data)
    data1 = np.ones([nl,ns])
    data2 = np.ones([nl,ns])
    data1[:,:ns-edge] = data[:,edge:ns]
    data2[:,edge:ns] = data[:,:ns-edge]
    temp = (data1)*data*data2
    dataa[temp ==0] = 0
    return dataa


'''
util_plot
'''

'''
plot with plt and seaborn
plt 的用法，有多少列数据，就是多少列
seaborn 的用法，有很多列数据，但是只有1列表现出来，用标签标识不同的列
'''
def plt_scatter(data1,data2,title='',dif=10,min1 = 225,min2 = 225,max1 = 335,max2 = 335):
    '''
    画散点图，并进行数据1和数据2 的统计信息
    :param data1: 数据1
    :param data2: 数据2
    :param title: 名称
    :param dif:  偏差阈值
    :param min1:  数据1的最小值
    :param min2:  数据2的最小值
    :param max1:  数据1的最大值
    :param max2:  数据2的最大值
    :return:  无
    '''
    plt.rcParams['figure.dpi'] = 150
    plt.rcParams['figure.figsize'] = (4.0, 3.2)
    ind = (data1>min1)*(data1<max1)*(data2>min2)*(data2<max2)*(np.abs(data1-data2)<dif)
    ind = np.where(ind > 0)
    dif = data2[ind]-data1[ind]
    rmse = np.sqrt(np.mean(dif*dif))
    std = np.std(dif)
    bias = np.mean(dif)
    r = np.corrcoef(data1[ind],data2[ind])
    r2 = r[0,1]*r[0,1]
    plt.figure(figsize=[4.5,4])
    plt.plot(data1[ind],data2[ind],'ko',markersize=2.5)
    plt.plot([min1,max1],[min2,max2],'k-.')
    plt.title([rmse,r2])
    plt.xlim([min1,max1])
    plt.ylim([min2,max2])
    plt.text(min1+(max1-min1)*3/5, min2+(max2-min2)*1/5, "$RMSE$ = %2.2f$\degree$C" % rmse + "\n$Bias$ = %2.2f$\degree$C" % bias +
             "\n$r^2$ = %2.2f" % r2 + "\n$\sigma$ = %2.2f$\degree$C" % std, fontsize=14)
    plt.title(title)
    plt.show()
    return 0


def plt_hist(data,bins = 30, alpha = 0.5):
    '''
    单个数据的分布图
    :param data:数据
    :param bins:大小
    :param alpha:透过率
    :return: 无
    '''
    plt.rcParams['figure.dpi'] = 150
    plt.rcParams['figure.figsize'] = (4.0, 3.2)
    kwargs = dict(histtype='stepfilled', alpha=alpha, bins=bins)
    fig, axs = plt.subplots(ncols=1, figsize=(5, 4))
    plt.hist(data, **kwargs, label='$\Delta$', color='orange')
    plt.legend()
    plt.xlabel('Difference or Value', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.show()

def plt_hist_2col(data1,data2,bins = 30, alpha = 0.5):
    '''
    数据的分布图,有两列数据，但是单独计算
    :param data1:数据1
    :param data2:数据2
    :param bins:大小
    :param alpha:透过率
    :return: 无
    '''
    plt.rcParams['figure.dpi'] = 150
    plt.rcParams['figure.figsize'] = (4.0, 3.2)
    data = np.transpose(np.stack([data1,data2]))
    kwargs = dict(histtype='stepfilled', alpha=alpha, bins=bins)
    fig, axs = plt.subplots(ncols=1, figsize=(5, 4))
    plt.hist(data, **kwargs, label='$\Delta$', color='orange')
    plt.legend()
    plt.xlabel('Difference or Value', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.show()

def plt_hist_scatter(data1,data2,bins = 30, alpha = 0.5):
    '''
    数据的分布图,两个数据的相关散点图的密度图
    :param data1:数据1
    :param data2:数据2
    :param bins:大小
    :param alpha:透过率
    :return: 无
    '''
    fig, axs = plt.subplots(ncols=1, figsize=(5, 4))
    plt.rcParams['figure.dpi'] = 150
    plt.rcParams['figure.figsize'] = (4.0, 3.2)
    plt.hist2d(data1, data2, norm=LogNorm(), cmap='jet',histtype='stepfilled', alpha=alpha, bins=bins)
    plt.legend()
    plt.xlabel('Difference or Value', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.plot([0, 1], [0, 1], 'k-')
    colorbar()
    plt.show()


def plt_pie(labels,sizes,colors):
    '''
    饼图的画法，这里是个例子
    :param labels: 饼图的图例
    :param sizes: 饼图的尺寸
    :param colors: 饼图的颜色
    :return: 无
    '''
    labers = ['Raytran', 'DART', 'RGM', 'FLIGHT', 'librat', 'FliES']
    sizes = [131, 200, 93, 180, 84, 72]
    # sizes2 = [3789, 5138, 2232, 5623, 2702, 1476]
    colors = ['red', 'blue', 'green', 'yellow', 'cyan', 'orange']
    explode = 0, 0, 0, 0, 0, 0
    patches, l_text, p_text = plt.pie(sizes, explode=explode, labels=labers,
           colors=colors, autopct='%1.1f%%', shadow=False, startangle=50)
    plt.axis('equal')
    plt.show()


def plt_coutourPolar(theta,rho,z,n,maxrho=50,step = 5):
    '''
    极坐标图的画法
    :param theta: 极坐标图的轴角
    :param rho: 极坐标图的轴长
    :param z: 各值的大小
    :param n: 值的区间数
    :param maxrho: 最大的轴长的阈值
    :return:无
    '''

    # ###transform data to Cartesian coordinates.
    # delta = maxrho/50
    # xx = rho*np.cos((90-theta)*(np.pi/180))
    # yy = rho*np.sin((90-theta)*(np.pi/180))
    # xi = np.linspace(-maxrho,maxrho,2*maxrho/delta)
    # yi = xi
    # [xi,yi] = np.meshgrid(xi,yi)
    # zi = griddata((xx,yy),z,(xi,yi),'cubic')
    # # fig, ax = plt.subplots(subplot_kw=dict(projection='polar'))
    # plt.contourf(xi,yi,zi,n,cmap='jet')
    # plt.show()

    delta = maxrho/50
    xx = np.radians(theta)
    yy = rho
    xi = np.radians(np.arange(0,365,step))
    yi = np.arange(0,maxrho,step)
    [xi,yi] = np.meshgrid(xi,yi)
    # xi = np.radians(xi)
    zi = griddata((xx,yy),z,(xi,yi))
    fig, ax = plt.subplots(subplot_kw=dict(projection='polar'))
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    plt.autumn()
    cax = ax.contourf(xi, yi, zi, n,cmap='jet')
    plt.autumn()
    cb = fig.colorbar(cax)
    # cb.set_label("Pixel reflectance") #颜色条的说明
    plt.show()

def sns_reg(data1,data2,min1 = 250,min2 = 350,max1 = 350, max2 = 350):
    '''
    画相关关系图, 同时画线性关系的线，及其不确定性，相关关系是该图的重点,点的大小和颜色并不是显示的重点，使用了seaborn库
    :param data1: 数据1
    :param data2: 数据2
    :param min1:  最小
    :param min2:  最小
    :param max1: 最大
    :param max2: 最大
    :return:
    '''
    ####################################
    #### statistical result
    ####################################
    ind = (data2 > 0)*(data1>0)
    dif = data2[ind] - data1[ind]
    rmse = np.sqrt(np.mean(dif * dif))
    std = np.std(dif)
    bias = np.mean(dif)
    r = np.corrcoef(data1[ind], data2[ind])
    r2 = r[0, 1] * r[0, 1]
    slope, intercept, r_value3, p_value3, std_err = stats.linregress(data1[ind],data2[ind])
    ####################################
    ### core code
    ####################################
    figure(figsize=[4.5, 3.2])
    sns.set_theme(style="white")
    ax = sns.regplot(x=data1, y=data2, ci=95, label='XXX')
    #ax = sns.regplot(x=data1, y=data3, ci=95, label='XXX')
    plt.tight_layout() ### 图像紧致
    plt.legend()
    plt.xlim([min1,max1])
    plt.ylim([min2,max2])
    plt.text(min1+(max1-min1)*3/5, min2+(max2-min2)*1/5, "$RMSE$ = %2.2f$\degree$C" % rmse + "\n$Bias$ = %2.2f$\degree$C" % bias +
             "\n$r^2$ = %2.2f" % r2 + "\n$\sigma$ = %2.2f$\degree$C" % std, fontsize=14)
    plt.show()

def sns_scatter(data1,data2,lai,smc):
    '''
    画散点图，重点是点的大小和颜色的展示,这里给出了一个例子
    :param data1: 数据1
    :param data2: 数据2
    :param lai:  类别1
    :param smc: 类别2
    :return:
    '''
    sns.set_theme(style="whitegrid")
    # sns.set_theme(style="white")
    # sns.set_palette(sns.color_palette("Paired", 4))
    cmap = sns.cubehelix_palette(rot=-.1, as_cmap=True)
    data = {'data1': data1, 'data2': data2, 'lai': lai, 'smc': smc}
    df = pd.DataFrame(data)
    g = sns.relplot(x='data1',y='data2',hue='SMC',size ='LAI',palette = cmap,data = df)
    g.set(xlabel ="data1",ylabel = "data2")
    # g.set()
    plt.show()


def sns_density(data1,data2,xmin = 250,xmax = 350, ymin = 250, ymax = 350):
    '''
    画散点图，重点是展示密度图
    :param data1:
    :param data2:
    :param xmin:
    :param xmax:
    :param ymin:
    :param ymax:
    :return:
    '''
    df = pd.DataFrame({'data1': data1, 'data2': data2})
    g = sns.jointplot(x='data1', y='data2', data=df, kind='hex', size=4)
    plt.plot([xmin, xmax], [ymin, ymax], '--')
    # g.set(xlabel='SCOPE LST (K)',ylabel='Fitted LST (K)')
    plt.xlabel("SCOPE LST")
    plt.ylabel("Fitted LST")
    plt.xlim([xmin, xmax])
    plt.ylim([ymin, ymax])
    # plt.colorbar()
    plt.show()

def sns_bar(data1,data2,data3, label1='data1',label2='data2',label3 ='class'):
    '''
    画直方图，通过dataframe把数据组织起来，然后通过标签进行分割分类，进行展示
    :param data1: 数据
    :param data2: 数据
    :param data3:  数据
    :param label1: 。。。
    :param label2: 。。。
    :param label3: 。。。
    :return:
    '''
    sns.set_theme(style="white")
    # sns.set_palette(sns.color_palette("Paired", 4))
    data = {label1: data1, label2:data2, label3:data3}
    df = pd.DataFrame(data)
    plt.figure(figsize=[12.0, 4.5])
    sns.barplot(data,x='data1',y='data2',hue='class', alpha=1.0)
    plt.legend(ncol=2)
    plt.tight_layout()
    plt.show()

def sns_hist(data, label='data',):
    '''
    画密度直方图，可以有颜色，分布，累计，颜色等修饰
    :param data: 数据
    :param label: 描述
    :return:
    '''
    g = sns.histplot(x=data,  bins=30, norm=LogNorm(), log_scale=(False),fill=True,
    cumulative=False, stat="density")
    plt.tight_layout()
    plt.show()
'''
util_phy
'''
def planck(wavelength, Ts):
    '''
    基于planck公式，计算某个波长时候，从温度到辐射的转换
    :param wavelength: 波长，10.5
    :param Ts: 温度，可以是亮温，也可以是摄氏度
    :return: 辐射
    '''
    c1 = planck_c1
    c2 = planck_c2
    if isinstance(Ts * 1.0, float):
        if (Ts < temperature_threshold): Ts = Ts + temperature_zero
        wavelength = np.float(wavelength)
        Ts = np.float(Ts)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    else:
        Ts[Ts < temperature_threshold] = Ts[Ts < temperature_threshold] + temperature_zero
        wavelength = float(wavelength)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    return rad


def inv_planck(wavelength, rad):
    '''
    基于planck公式，计算从辐射到亮温的转换
    :param wavelength: 波长,10.5
    :param rad: 辐射
    :return: 亮温 （300）
    '''
    c1 = planck_c1 * 10000
    c2 = planck_c2
    temp = c1 / (rad * np.power((wavelength), 5)) + 1
    Ts = c2 / (wavelength * np.log(temp))
    return Ts


def vapor(T,eap):
    '''
    计算空气的水汽压
    :param T: 空气温度
    :param eap: 湿度
    :return:
    '''
    a = 7.5
    b = 237.3
    es = 6.107*np.power(10,(7.5*T/(b+T)))
    s = es*np.log(10)*a*b/np.power(b+T,2)
    ea = es*eap*0.01
    return ea

def date2DOY(year,month,day):
    '''
    日期到Day of Year 的转换
    :param year: 年
    :param month:  月
    :param day: 日
    :return: doy
    '''
    days_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    monthsum = np.zeros(12)
    year = np.int(year)
    month = np.int(month)
    day = np.int(day)
    if isinstance(day * 1.0, float):
        total = 0
        for index in range(month - 1):
            total += days_of_month[index]
        temp = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        if month > 2 and temp:
            total += 1
        return total + day
    else:
        for index in range(1,12):
            monthsum[index] = monthsum[index-1]+days_of_month[index-1]
        month = np.asarray(month,dtype=np.int)
        DOY = monthsum[month-1] + day
        ind = ((year % 4 == 0) * (year % 100 != 0)) * (month>2)
        DOY[ind] = DOY[ind] + 1
        ind = ((year % 400 == 0))
        DOY[ind] = DOY[ind] + 1
    return DOY


def doy2date(year, doy):
    '''
    doy 到日期的转换
    :param year: 年
    :param doy: day of year
    :return:  日期（月,日）
    '''
    year = np.int(year)
    doy = np.int(doy)
    month_leapyear = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_notleap = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        for i in range(0, 12):
            if doy > month_leapyear[i]:
                doy -= month_leapyear[i]
                continue
            if doy <= month_leapyear[i]:
                month = i + 1
                day = doy
                break
    else:
        for i in range(0, 12):
            if doy > month_notleap[i]:
                doy -= month_notleap[i]
                continue
            if doy <= month_notleap[i]:
                month = i + 1
                day = doy
                break
    return month, day


def fieldcalibrate(undertemp,overtemp,atmtemp,underemis,overemis,lai,wl = 10.5):
    '''
    计算消除了大气影响后的温度
    :param undertemp: 测量的地面温度
    :param overtemp: 测量的上层温度
    :param atmtemp: 大气等效温度
    :param underemis: 上层发射率
    :param overemis: 下层发射率
    :param lai: lai
    :param wl: 波长
    :return: 消除大气校正后的结果
    '''
    rad_under = planck(wl,undertemp)
    rad_over = planck(wl,overtemp)
    rad_atm = planck(wl,atmtemp)

    fvc = 1-np.exp(-lai*0.5)
    rad_under = (rad_under - (1-underemis)*(fvc*rad_over +(1-fvc)*rad_atm))/underemis
   # rad_over = (rad_over - (1-overemis)*rad_atm)/overemis
    rad_over = (rad_over - (1-overemis)*(fvc*rad_over +(1-fvc)*rad_atm)) / overemis

    result_under = inv_planck(wl,rad_under)
    result_over = inv_planck(wl,rad_over)
    return result_under-273.15,result_over-273.15


def simpleForward(undertemp,overtemp,atmtemp,underemis,overemis,lai,wl = 10.5):
    '''
    收到大气校正影响
    :param undertemp:
    :param overtemp:
    :param atmtemp:
    :param underemis:
    :param overemis:
    :param lai:
    :param wl:
    :return:
    '''
    rad_under = planck(wl, undertemp)
    rad_over = planck(wl, overtemp)
    rad_atm = planck(wl, atmtemp)

    fvc = 1 - np.exp(-lai * 0.5)
    rad_under = (rad_under*underemis + (1 - underemis) * (fvc * rad_over + (1 - fvc) * rad_atm))
    rad_over = (rad_over*overemis + (1 - overemis) * rad_atm) / overemis

    result_under = inv_planck(wl, rad_under)
    result_over = inv_planck(wl, rad_over)
    return result_under - 273.15, result_over - 273.15



'''
util_inv
'''

def fitting_unknown_linear_ls(y,A):
    '''
    线性反演未知数，y=ax1+bx2+cx3, x3=1
    :param y: 因变量
    :param x: 自变量
    :return:
    '''
    coeffs = np.asarray(lstsq(A, y))[0]
    return coeffs


def fitting_unknown_nonlinear_fmin(fun,y,A,xn,x0):
    '''
    非线性反演/回归，基于fmin函数，能给初值，不能给边界条件
    :param fun: 函数
    :param y: 因变量
    :param x: 自变量，是个多列数组
    :param x0: 初值
    :param xn: 列数
    :return: 回归系数
    '''
    res = fmin(fun, x0=x0, args=(y,A,xn), disp=0)
    return res



def fitting_unknown_nonlinear_min(fun,y,A,xn,x0,bnds,method = 'Powell'):
    '''
    非线性反演/回归，基于minimize函数，能给初值，也能给边界条件
    :param fun: 函数
    :param y: 因变量
    :param x: 自变量，是个多列数组
    :param x0: 初值
    :param xn: 列数
    :param bnds: 边界
    :param method: 方法，默认为powell，还有slsqp，L-BFGS-B，TNC，
    :return: 回归系数
    '''
    res = minimize(fun, x0,
                   args=(y,A,xn),
                   method=method,
                   bounds=bnds, )
    return res.x


def fitting_unknown_nonlinear_ls(fun,y,A,xn,x0,bnds,method = 'trf'):
    '''
    非线性反演/回归，基于least_squares函数，能给初值，也能给边界条件
    :param fun: 函数
    :param y: 因变量
    :param A: 矩阵
    :param x0: 初值
    :param xn: 列数
    :param bnds: 边界
    :param method: 方法，trf', 'dogbox', 'lm'
    :return: 回归系数
    '''
    res = least_squares(fun, x0,
                   args=(y,A,xn),
                   method=method,
                   bounds=bnds, )
    return res.x



def fitting_unknown_linear_sklearn(y,A,method='ridge'):
    '''
    线性反演未知数，
    :param y: 因变量
    :param x: 自变量
    :param method: 方法，推荐ridge，然后是lasso，因为lasso会倾向于拟合0
    :return: 回归系数
    '''
    alphas = [0.0001,0.001,0.01,0.1,1,10,100]
    coeffs = 1.0
    if method=='ridge':
        clf = RidgeCV(alphas=alphas, fit_intercept=False)
        clf.fit(A, y)
        coeffs = clf.coef_
    elif method =='lasso':
        lasso = LassoCV(alphas=alphas, fit_intercept=False)
        lasso.fit(A, y)
        coeffs = lasso.coef_
    elif method =='bayesianridge':
        clf = BayesianRidge(fit_intercept=False)
        clf.fit(A,y)
        coeffs = clf.coef_

    return coeffs


from scipy.sparse.linalg import lsqr
def fitting_unknown_linear_sparse(y,A,iter=100):
    '''
    找到大型稀疏线性方程组的least-squares 解。
    :param y:
    :param x:
    :param iter:
    :return:
    '''
    coeffs = lsqr(A,y,iter_lim=iter)[0]
    return coeffs


