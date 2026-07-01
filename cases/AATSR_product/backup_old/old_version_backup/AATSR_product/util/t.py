import numpy as np
import os
import scipy
import h5py
import sklearn
from scipy.interpolate import griddata



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
    return data

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

infile = r"D:\\test.h5"
name = ["1","2","3"]
array1 = np.array([0])
array2 = np.array([0,1])
array3 = np.array([0,1,4])
dtype = ['f','f','int16']
compression = 'gzip'
data = [array1,array2,array3]
write_h5py_file(infile,name_list=name,data_list=data,dtype_list=dtype,compression=compression,ifcover=1)
name,data = read_h5py_file(infile)
print(data[0])