from util.util import *


'''
批处理
1. 修改图像的尺寸
2. 修改图像的数据类型
'''


'''LST'''

# indir_source = r'H:\S3A19_lst_china\\'
# indir_target = r'F:\s3a_lst\\'
#
#
# infiles = search_file_rej(indir_source,['lst','day'],'2km')
# num_infiles = np.size(infiles)
#
# for k in range(num_infiles):
#     infile = indir_source+infiles[k]
#     outfile = indir_target + infiles[k]
#     [temp,ns,nl,nb,geog,proj] = read_image_gdal(infile)
#     temp = temp * 100.0
#     print(infile)
#     write_image_gdal(temp.astype(uint16),ns,nl,nb,geog,proj,outfile)



'''NDVI'''

indir_source = r'H:\S3A19_tif\\'
indir_target = r'F:\s3a_tif\\'


infiles = search_file_rej(indir_source,['red','day','nadir'],'2km')
num_infiles = np.size(infiles)

for k in range(num_infiles):
    infile_red = indir_source+infiles[k][:-13]+'red_nadir.tif'
    infile_nir = indir_source+infiles[k][:-13]+'nir_nadir.tif'
    outfile = indir_target + infiles[k][:-13]+'ndiv_nadir.tif'
    [red,ns,nl,nb,geog,proj] = read_image_gdal(infile_red)
    [nir, ns, nl, nb, geog, proj] = read_image_gdal(infile_nir)
    ind = (red >0) *(nir >0)
    temp = np.zeros([nl,ns])
    temp[ind] = (nir[ind]-red[ind])/(nir[ind]+red[ind])

    temp = temp * 10000.0
    print(infiles[k][:-13])
    write_image_gdal(temp.astype(uint16),ns,nl,nb,geog,proj,outfile)

