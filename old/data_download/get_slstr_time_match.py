import numpy as np
from util.util import *


### forest and crop
lat_ = np.asarray([38.54043])
lon_ = np.asarray([-8.003297])
# lat_ =np.asarray([38.85544116,38.853457])
# lon_ = np.asarray([100.37424145,100.371343])


infile_type = r'D:\data\LSCT_evo_2017\0_base\type/type_evo_1000.tif'
type, ns, nl, nb, geog, proj,dataset = read_image_dataset_gdal(infile_type)
imagex_,imagey_ = loc2map(lat_,lon_,dataset)
# 118 116

indir_tif = r'G:\S3_EVO_2020\tif2\\'


infiles = search_file_rej(indir_tif,['time'],'enp')
n_file = np.size(infiles)
outfile = r'D:\data\LSCT_evo_2020\slstr_time2.txt'

off = 1 # distance for averge

doy_ = []
time_ =[]

for k in range(n_file):
    filename = infiles[k][:12]
    doy = np.int_(filename[9:12])
    print(filename)
    infile_lsct = indir_tif + infiles[k]
    infile_time = indir_tif+filename+'_time.tif'
    [time,ns,nl,nb,geog,proj] = read_image_gdal(infile_time)
    if time[imagex_,imagey_]==0: continue
    doy_.append(doy)
    time_.append(time[imagex_,imagey_])
time_ = np.asarray(time_)
time_ = np.reshape(time_,[-1])
result = np.vstack([doy_,time_])
result = np.transpose(result)
np.savetxt(outfile,result,fmt='%.3f')
