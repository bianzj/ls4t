import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from base.util_packages import *




'''util_file'''
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
                    specstr[0] in x]
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

def read_binary(filename, type = np.int_):
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

def write_image_gdal_bigfile(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff'):
    '''
    优化版的GDAL图像保存函数，提高CPU运行效率
    '''
    try:
        # 预定义数据类型映射，避免重复字符串检查
        dtype_mapping = {
            'int8': gdal.GDT_Byte,
            'uint8': gdal.GDT_Byte,
            'uint16': gdal.GDT_UInt16, 
            'int16': gdal.GDT_Int16,
            'uint32': gdal.GDT_UInt32,
            'int32': gdal.GDT_Int32,
            'float32': gdal.GDT_Float32,
            'float64': gdal.GDT_Float64
        }
        
        # 获取数据类型，默认为Float32
        datatype = dtype_mapping.get(im_data.dtype.name, gdal.GDT_Float32)
        
        # 优化数组形状处理
        data_shape = im_data.shape
        data_ndim = im_data.ndim
        
        if data_ndim == 3:
            # 确保数组形状为 (bands, height, width)
            if data_shape[0] == im_bands and data_shape[1] == im_height and data_shape[2] == im_width:
                # 形状匹配，直接使用
                pass
            else:
                # 自动检测正确的形状
                if data_shape[2] == im_bands:  # 可能是 (height, width, bands)
                    im_data = np.transpose(im_data, (2, 0, 1))
                im_bands, im_height, im_width = im_data.shape
                
        elif data_ndim == 2:
            # 单波段数据，确保形状为 (1, height, width)
            im_data = im_data.reshape(1, im_height, im_width)
            im_bands = 1
        else:
            raise ValueError(f"不支持的数组维度: {data_ndim}")
        
        # 确保数据在内存中连续存储，提高写入性能
        if not im_data.flags['C_CONTIGUOUS']:
            im_data = np.ascontiguousarray(im_data)
        
        # 创建输出目录（如果不存在）
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # 创建GDAL数据集
        driver = gdal.GetDriverByName(imageType)
        if driver is None:
            raise ValueError(f"不支持的GDAL驱动类型: {imageType}")
        
        # 使用更高效的创建选项
        creation_options = []
        if imageType == 'GTiff':
            creation_options = ['COMPRESS=LZW', 'TILED=YES', 'BIGTIFF=IF_SAFER']
        
        dataset = driver.Create(path, im_width, im_height, im_bands, datatype, creation_options)
        
        if dataset is None:
            raise RuntimeError(f"无法创建文件: {path}")
        
        # 设置地理参考信息
        if im_trans and im_proj:
            dataset.SetGeoTransform(im_trans)
            dataset.SetProjection(im_proj)
        
        # 优化波段写入：批量处理，减少Python循环开销
        if im_bands == 1:
            # 单波段直接写入
            dataset.GetRasterBand(1).WriteArray(im_data[0])
        else:
            # 多波段写入，使用更高效的方式
            for i in range(im_bands):
                band = dataset.GetRasterBand(i + 1)
                band.WriteArray(im_data[i])
                # 可选：设置无数据值
                # band.SetNoDataValue(nodata_value)
        
        # 强制刷新到磁盘
        dataset.FlushCache()
        del dataset
        
        return True
        
    except Exception as e:
        print(f"保存图像时出错: {str(e)}")
        # 清理可能创建的不完整文件
        if 'dataset' in locals() and dataset is not None:
            del dataset
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
        return False


def read_dataset_gdal(fileName):
    '''
    读取数据，返回数据集，多用于基于数据集的数据转换
    :param fileName: 数据名
    :return: 数据集
    '''
    dataset = gdal.Open(fileName)
    return dataset

def write_h5py_item(infile,name,data,dtype,if_overwrite=1,compression=None):
    '''
    Write h5py
    para infile: h5py
    para name: string
    para data: numpy array
    para dtype: string
    para if_overwrite: 0 or 1
    para compression: string
    '''
    if not os.path.exists(infile):
        f = h5py.File(infile,'w')
    else:
        f = h5py.File(infile,'a')
    if name in f and if_overwrite == 1:
        del f[name]
    f.create_dataset(name,data=data,dtype=dtype,compression=compression)
    f.close()


def write_h5py_file(infile,name_list,data_list,dtype_list,compression=None,ifcover = 0):
    '''
    Write h5py
    para infile: h5py
    para name_list:
    para data_list:
    para dtype_list:
    para compression: gzip, lzf, szip, None (only applied to array data)
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
        data = data_list[i]
        # Only apply compression to array/matrix data
        if isinstance(data, (np.ndarray, list, tuple)) and len(np.shape(data)) > 0:
            f.create_dataset(name,data=data,dtype=dtype_list[i],compression=compression)
        else:
            f.create_dataset(name,data=data,dtype=dtype_list[i])
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
    # 初始化一个空列表，用于存储从h5py文件中读取的数据
    data_list = []
    # 打开h5py文件
    f = h5py.File(infile)
    # 遍历输入的名称列表
    for name in names:
        # 检查当前名称是否存在于h5py文件中
        if name in f:
            # 如果存在，将数据转换为numpy数组并添加到结果列表中
            data_list.append(np.array(f[name]))
        else:
            # 如果不存在，添加一个空列表到结果列表中
            data_list.append([])
    # 返回包含所有数据的列表
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

def unzip_file(zipfilename,outdir):
    '''
    解压zip文件
    :param zipfilename: 要解压文件名称
    :param outdir: 输出位置
    '''
    mkdir_if_not_exist(outdir)
    zip_file = zipfile.ZipFile(zipfilename)
    for names in zip_file.namelist():
        zip_file.extract(names, outdir)  # 解压到outdir目录下
    zip_file.close()
    print("Unzip " + zipfilename + " finished!")




#####################################3
### Part for aatsr
######################################


from base.util_constant import *
from base.util_file import *
from base.util_data import *

'''
AATSR 数据读取
'''

def aatsr_read_aux_data(indir_emis=r"/home/hero/data/base/0_base/emis/", indir_type=r"/home/hero/data/base/0_base/type/"):
    '''
    aatsr 读取辅助数据
    :param indir_emis: 发射率
    :param indir_type:  地表类型
    :return: 土壤发射率、植被发射率、分类、密度、观测天顶角、方位角
    '''
    # 读取type emis
    infile_type = indir_type + 'type_world_1000.tif'
    infile_soil_emis = indir_emis + r'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
    infile_veg_emis = indir_emis + 'IGBP_Emi.txt'
    infile_vzaN = indir_type + r"vza_n.tif"
    infile_vaaN = indir_type + r"vaa_n.tif"
    infile_vzaO = indir_type + r"vza_f.tif"
    infile_vaaO = indir_type + r"vaa_f.tif"
    [emis_s, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_soil_emis)
    [classif, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_type)
    [vzaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vzaN)
    [vaaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaaN)
    [vzaO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vzaO)
    [vaaO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaaO)
    vzaN, vzaO, vaaN, vaaO = 90 - vzaN / 100, 90 - vzaO / 100, vaaN / 100, vaaO / 100
    emis_s = emis_s / 1000
    classif = np.asarray(classif, np.int_)
    classif[classif == 255] = 17
    emis_v = read_txt_array(infile_veg_emis, 0, 2)
    emis_v = emis_v[classif, 0] / 1000
    return emis_s, emis_v, classif, vzaN, vzaO, vaaN, vaaO


def aatsr_read_crown_data(indir_veg_pra):
    '''
    读取植被参数
    :param indir_veg_pra: 地址
    :return: 树密度、覆盖度、树冠高度
    '''
    infile_std = indir_veg_pra + "Tree_density(STD)/global_TreeDensity_0.01.tif"
    infile_TCC = indir_veg_pra + "Tree_cover(TCC)/global_TreeCover2010_0.01.tif"
    infile_hcr = indir_veg_pra + "Cnopy_height(hcr)/global_CanopyHeight_0.01.tif"
    [std, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_std)
    [TCC, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_TCC)
    [hcr, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_hcr)
    hcr = np.nan_to_num(hcr,0.0)
    std = std / 1000000
    hcr = hcr / 2
    TCC = TCC / 100
    return  std, TCC, hcr


def aatsr_cal_r(tcc, std, lai):
    G = 0.5  # Given constant
    cthetx = 1  # Given constant

    def equation(r, tcc_val, std_val, lai_val):
        areav = np.pi * r ** 2
        bv_in = np.exp(- (G * lai_val) / (areav * std_val))
        return np.log(tcc_val) + areav * (1 - bv_in) * std_val

    r_solution = np.zeros_like(tcc)
    for i in range(tcc.shape[0]):
        for j in range(tcc.shape[1]):
            r_initial_guess = 1.0  # Initial guess for r
            r_result = fsolve(equation, r_initial_guess, args=(tcc[i, j], std[i, j], lai[i, j]))
            r_solution[i, j] = np.clip(r_result[0], 0.5, 30)  # Ensure r is within bounds

    return r_solution


'''
时间 读取
'''
def get_timezone(lat, lon):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if timezone_str:
        return pytz.timezone(timezone_str)
    else:
        return None

def utc_to_local(utc_time,lon,lat):
    utc_time = pd.to_datetime(utc_time).dt.tz_localize('UTC')
    timezone = get_timezone(lat, lon)
    local_time = utc_time.dt.tz_convert(timezone)
    return local_time


'''
云量读取
'''

def aatsr_clo(clo):
    """
    将输入的十进制数或数组转换为二进制，
    第一位表示是否为陆地，第二位表示是否有云。
    只有陆地（第一位为1）且无云（第二位为0）时返回 True，否则返回 False。

    :param clo: 十进制整数或数组
    :return: 是否符合条件（True/False），单个值返回 bool，数组返回 np.ndarray，维度与输入相同
    """

    def check_condition(value):
        value = int(value)
        binary_str = format(value, 'b').zfill(2)  # 转换为二进制字符串，至少两位
        is_land = binary_str[-1] == '1'  # 低位第一位表示是否为陆地
        no_cloud = binary_str[-2] == '0'  # 低位第二位表示是否有云
        return is_land and no_cloud

    vectorized_check = np.vectorize(check_condition)
    return vectorized_check(clo)

def aatsr_clo_optimized(clo):
    """
    优化版：使用位运算检查最低两位
    最低位(第0位)表示是否为陆地(1)，第1位表示是否有云(0)
    只有陆地且无云时返回True

    :param clo: 十进制整数或数组
    :return: 是否符合条件(bool或np.ndarray)
    """
    # 转换为整数类型确保位运算正确
    clo = np.asarray(clo, dtype=np.int32)

    # 使用位运算同时检查两个条件:
    # 1. (clo & 0b01) == 1 检查最低位是否为1(陆地)
    # 2. (clo & 0b10) == 0 检查第1位是否为0(无云)
    return np.bitwise_and((clo & 0b01) == 1, (clo & 0b10) == 0)


'''
aatsr_sites fluxnet 切片数据读取
'''
def aatsr_read_sites_obs(infile,ifNDVI=1):
    items_obs = ['nirN','nirF','redN','redF','cloN','cloF']
    [nirN, nirF, redN, redF, cloN, cloF] = read_h5py_items(infile, items_obs)
    cloN_mask = aatsr_clo_optimized(cloN)
    cloF_mask = aatsr_clo_optimized(cloF)
    if ifNDVI == 1:
        ndviN = (nirN - redN) / (nirN + redN)
        ndviF = (nirF - redF) / (nirF + redF)
        ndviN[ndviN < -1] = -1
        ndviN[ndviN > 1] = 1
        ndviF[ndviF < -1] = -1
        ndviF[ndviF > 1] = 1
        ndviN[(redN ==0) + (nirN==0)] = np.nan
        ndviF[(redF ==0) + (nirF==0)] = np.nan
        return ndviN, ndviF
    return nirN, nirF, redN, redF

def aatsr_read_sites_clo(infile):
    items_clo = ['cloN','cloF']
    [cloN, cloF] = read_h5py_items(infile, items_clo)
    cloN_mask = aatsr_clo_optimized(cloN)
    cloF_mask = aatsr_clo_optimized(cloF)
    return cloN_mask, cloF_mask

def aatsr_read_sites_lst(infile):
    items_lst = ['lstN','lstO']
    [lstN, lstO] = read_h5py_items(infile, items_lst)
    lstN, lstF = lstN / 100, lstO / 100
    return lstN, lstF

def aatsr_read_sites_angle(infile):
    items_angle = ['vzaN','vzaF','vaaN','vaaF','sza','saa']
    [vzaN, vzaF, vaaN, vaaF, sza, saa] = read_h5py_items(infile, items_angle)
    vzaN,vzaF,vaaN,vaaF,sza,saa = vzaN / 100,vzaF/100,vaaN/100,vaaF/100,sza/100,saa/100
    sza[sza >= 90] = 89.99
    return vzaN,vzaF,vaaN,vaaF,sza,saa

def aatsr_read_sites_emis(infile):
    items_emis = ['emis_s','emis_v','type','lai']
    [emis_s,emis_v,type_,lai] = read_h5py_items(infile, items_emis)
    lai = np.array(lai)/1000
    return emis_s,emis_v,type_,lai

def aatsr_read_sites_loc(infile):
    items_loc = ['indx','indy','ref_indx','ref_indy','lat','lon']
    [indx,indy,ref_indx,ref_indy,lat,lon] = read_h5py_items(infile, items_loc)
    return indx,indy,ref_indx,ref_indy,lat,lon

def aatsr_read_sites_time(infile):
    items_time = ['ref_time','sec']
    [ref_time,sec] = read_h5py_items(infile, items_time)
    ref_time_str = infile[-18:-10]
    utc_time = datetime.strptime(ref_time_str, '%Y_%j') + timedelta(seconds=int(np.mean(sec)))
    return utc_time

def aatsr_read_sites(site_dir, fileName, timezone, lat, lon, window_size):
    offset = window_size // 2
    infile = os.path.join(site_dir, fileName)
    '''读取数据'''
    items = ['lon', 'lat', 'lstN', 'lstO', 'LAI', 'vzaN', 'vzaO', 'vaaN', 'vaaO', 'sza', 'saa', 'indx', 'indy',
             'ref_indx', 'ref_indy', 'ref_time', 'sec', 'type', 'emis_s', "emis_v", 'cloN', 'cloF']
    lon_, lat_, lstN_, lstO_, lai_, vzaN_, vzaO_, vaaN_, vaaO_, sza_, saa_, indx_, indy_, ref_indx_, ref_indy_, ref_time_, sec_, type_, emis_s_, emis_v_, cloN_, cloF_ = read_h5py_items(
        infile, items)
    ref_time_str = fileName[6:-10]
    utc_time = datetime.strptime(ref_time_str, '%Y_%j') + timedelta(seconds=int(np.mean(sec_)))
    year, doy = int(ref_time_str[:4]), int(ref_time_str[5:8])
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone)
    print(local_time)

    '提取站点数据'
    id = (indx_ == ref_indx_) * (indy_ == ref_indy_)
    idx, idy = np.where(id)
    if sum(id) == 0:
        print("No Data!")
        return

    lstN = lstN_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    lstF = lstO_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    if np.shape(lstN) != (window_size, window_size): return
    lai = lai_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    lai[lai >= 100] = lai[lai >= 100] / 1000
    vzaN = vzaN_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    vzaF = vzaO_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    vaaN = vaaN_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    vaaF = vaaO_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    classif = type_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    emisS = emis_s_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    emisV = emis_v_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    cloN = cloN_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    cloF = cloF_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    indx = indx_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1].astype(int)
    indy = indy_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1].astype(int)
    '''格式转化'''
    lstN[lstN > 20000] = lstN[lstN > 20000] / 100
    lstF[lstF > 20000] = lstF[lstF > 20000] / 100

    nl, ns = np.shape(lstN)

    if sza_ != []:
        sza = sza_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
        saa = saa_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
        if np.abs(sza[offset, offset] - (90 - Sun.get_altitude(lat, lon, local_time))) < 10:
            sza = sza
        elif sza[offset, offset] > 89.9:
            sza = np.full_like(sza, 89.9)
        else:
            sza = 90 - sza
            print(90 - sza[offset, offset], (90 - Sun.get_altitude(lat, lon, local_time)))
    else:
        sza_ = 90 - Sun.get_altitude(lat, lon, local_time)
        saa_ = Sun.get_azimuth(lat, lon, local_time)
        sza = np.full([nl, ns], sza_)
        saa = np.full([nl, ns], saa_)

    def Azimuth_angle_transform(xaa):
        xaa[xaa < 0] = xaa[xaa < 0] + 360
        return xaa
    vzaN = 90 - vzaN / 100
    vzaF = 90 - vzaF / 100
    vaaN = Azimuth_angle_transform(vaaN)
    vaaF = Azimuth_angle_transform(vaaF)
    saa = Azimuth_angle_transform(saa)
    if np.sum(vaaN) == 0: return

    return lstN, lstF, lai, vzaN, vzaF, vaaN, vaaF, sza, saa, cloN, cloF, emisS, emisV, classif, utc_time, local_time, indx, indy



'''aatsr_h5 读取'''
def aatsr_read_lst(infile_lst):
    '''
    读取aatsr h5 lst数据
    :param infile_lst: lst文件地址
    :return: 两角度LST
    '''
    items = ['lstN','lstO']
    lstN, lstF = read_h5py_items(infile_lst, items)
    lstN, lstF = lstN/100.0, lstF/100.0
    return lstN, lstF

def aatsr_read_NDVI(infile_obs):
    '''
    读取aatsr h5 obs数据并计算NDVI
    :param infile_obs: obs文件地址
    :return: 两角度NDVI
    '''
    items = ['redN','nirN','redF','nirF']
    redN, nirN, redF, nirF = read_h5py_items(infile_obs, items)
    redN, nirN, redF, nirF = redN/10, nirN/10, redF/10, nirF/10
    ndviN = (nirN - redN) / (nirN + redN)
    ndviF = (nirF - redF) / (nirF + redF)
    ndviN[ndviN < -1] = -1
    ndviN[ndviN > 1] = 1
    ndviF[ndviF < -1] = -1
    ndviF[ndviF > 1] = 1
    ndviN[(redN ==0) + (nirN==0)] = np.nan
    ndviF[(redF ==0) + (nirF==0)] = np.nan
    return ndviN, ndviF

def aatsr_read_obs(infile_obs):
    '''
    读取aatsr h5 obs数据
    :param infile_obs: obs文件地址
    :return: 两角度红、近红外
    '''
    items = ['bt8N','bt8F','bt9N','bt9F']
    bt8N, bt8F, bt9N, bt9F = read_h5py_items(infile_obs, items)
    bt8N, bt8F, bt9N, bt9F = bt8N/100.0, bt8F/100.0, bt9N/100.0, bt9F/100.0
    return bt8N, bt8F, bt9N, bt9F

def aatsr_read_clo(infile_clo):
    '''
    读取aatsr h5 clo数据(自动计算并保存mask)
    :param infile_clo: clo文件地址
    :return: 两角度clo
    '''
    items = ['cloN_mask','cloF_mask']
    cloN_mask, cloF_mask = None, None

    # 先检查文件是否存在mask数据集
    with h5py.File(infile_clo, 'r') as f:
        if 'cloN_mask' not in f:
            print(f"Warning: Missing clo_mask in {infile_clo}")
            items = ['cloN','cloF']
            cloN, cloF = read_h5py_items(infile_clo, items)
            cloN_mask = aatsr_clo_optimized(cloN)
            cloF_mask = aatsr_clo_optimized(cloF)
        else:
            cloN_mask, cloF_mask = read_h5py_items(infile_clo, items)
            return cloN_mask, cloF_mask

    if 'cloN_mask' not in h5py.File(infile_clo, 'r'):
        with h5py.File(infile_clo, 'a') as f_write:
            f_write.create_dataset('cloN_mask', data=cloN_mask, dtype='bool', compression='gzip')
            f_write.create_dataset('cloF_mask', data=cloF_mask, dtype='bool', compression='gzip')

    return cloN_mask, cloF_mask

def aatsr_read_loc(infile_loc, iflonlat = 0):
    '''
    读取aatsr h5 loc数据
    :param infile_loc: loc文件地址
    :param iflonlat: 是否返回经纬度，0-否，1-是
    :return: 像元索引(行列)，可选经纬度
    '''
    items = ['indx','indy']
    if iflonlat == 1:
        items = ['indx','indy','lon','lat']
        indx, indy, lon, lat = read_h5py_items(infile_loc, items)
        return indx, indy, lon, lat
    else:
        indx, indy = read_h5py_items(infile_loc, items)
        return indx, indy

def aatsr_read_lai(infile_aux):
    '''
    读取aatsr h5 aux数据
    :param infile_aux: aux文件地址
    :return: LAI
    '''
    items = ['LAI']
    lai = read_h5py_items(infile_aux, items)[0]
    lai = lai / 1000.0
    return lai

def aatsr_read_angle(infile_ang,ifsun=1,ifview=1):
    '''
    读取aatsr h5 ang数据
    :param infile_ang: ang文件地址
    :return: 太阳天顶角、方位角
    '''
    if ifsun == 1:
        items = ['sza','saa']
        sza, saa = read_h5py_items(infile_ang, items)
        sza = sza / 100.0
        saa = saa / 100.0
        sza[sza>89.99] = 89.99
    if ifview == 1:
        items = ['vzaN','vaaN','vzaF','vaaF']
        vzaN, vaaN, vzaF, vaaF = read_h5py_items(infile_ang, items)
        vzaN, vzaF = vzaN / 100.0, vzaF / 100.0
        vaaN, vaaF = vaaN / 100.0, vaaF / 100.0

    if ifsun == 1 and ifview == 1:
        return sza, saa, vzaN, vzaF, vaaN, vaaF
    if ifsun == 1 and ifview == 0:
        return sza, saa
    if ifsun == 0 and ifview == 1:
        return vzaN, vzaF, vaaN, vaaF

def aatsr_read_lsct(infile_lsct):
    '''
    读取aatsr h5 lsct数据
    :param infile_lsct: lsct文件地址
    :return: 两角度地表温度
    '''
    items = ['Ts','Tv']
    Ts, Tv = read_h5py_items(infile_lsct, items)
    Ts, Tv = Ts / 100.0, Tv / 100.0
    return Ts, Tv




