from util.util import *
from util.util_constant import *
import warnings
warnings.filterwarnings("ignore")
import h5py

'''
AATSR保存成hdf数据
'''

def write_img_gdal_hdf(data,lon,lat,dir):
    '''
    写hdf文件，包含数据集和经纬度坐标
    :param data: 要保存的数据集
    :param lon: 经度
    :param lat: 纬度
    :param dir: 保存位置
    :return:
    '''
    # Create a HDF5 file.
    f = h5py.File(dir, "w")  # mode = {'w', 'r', 'a'}
    # Create a dataset under root '/'.
    d = f.create_dataset("data", data=data)
    d2 = f.create_dataset("lon", data=lon)
    d3 = f.create_dataset("lat", data=lat)
    f.close()

indir_lst = r"D:\data\data_download\AATSR\example\AATSR_lst\\"
indir_tif = r"D:\data\data_download\AATSR\example\AATSR_med\\"
outdir_hdf = r"D:\data\data_download\AATSR\example\AATSR_lst_hdf\\"

fileNames = search_file(indir_lst,["lst_n"])
for filename in fileNames:
    offset = -9
    file = filename[:-9]
    lstN_file_dir = indir_lst + file + "lst_n.tif"
    lstO_file_dir = indir_lst + file + "lst_f.tif"
    lon_file_dir = indir_tif + file + "lon.tif"
    lat_file_dir = indir_tif + file + "lat.tif"
    [lstN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(lstN_file_dir)
    [lstO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(lstO_file_dir)
    [lon, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(lon_file_dir)
    [lat, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(lat_file_dir)
    lstN  = lstN * 100
    lstO  = lstO * 100
    outfile = outdir_hdf + file + "lst.hdf5"
    f = h5py.File(outfile, "w")
    d1 = f.create_dataset("lstN", data=lstN.astype('uint16'))
    d2 = f.create_dataset("lstO", data=lstO.astype('uint16'))
    d3 = f.create_dataset("lon", data=lon)
    d4 = f.create_dataset("lat", data=lat)
    f.close()
    print("creat " + outfile + "successful!")



