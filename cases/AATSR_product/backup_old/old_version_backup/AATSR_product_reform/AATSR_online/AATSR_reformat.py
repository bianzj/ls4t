import sys
sys.path.append('/data1/home/AircasBianzj/code/')
from utils.old.util import *
from utils.myfun_lyf import *
import warnings
warnings.filterwarnings("ignore")
import h5py

'''
AATSR保存成hdf数据
'''

year = sys.argv[1]
month = sys.argv[2]
day = sys.argv[3]
time_str = "//%04d" % int(year) + "//%02d" % int(month) + "//%02d" % int(day) + "//"

indir_tif = r'/data1/public1/Bianzj/AATSR/AATSR_tif/'+ time_str
indir_lst = r'/data1/public1/Bianzj/AATSR/AATSR_lst/'+ time_str
outdir_hdf = r'/data1/public1/Bianzj/AATSR/AATSR_lst_hdf/'+ time_str


fileNames = search_file(indir_lst,["lst_n"])
for filename in fileNames:
    mkdir_if_not_exist(outdir_hdf)
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