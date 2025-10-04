import numpy as np

from util.util import *

'''
本脚本用于裁剪角度数据至目标区域（EVO\KAL）
未用
'''

indir_base = r"D:\data\base\\"
indir_med = r"D:\data\base\msg_angle\med\\"
indir_type = r'D:\data\type\type_world_0.03.tif'
outdir = r"D:\data\base\msg_angle\\"

msg_vza_dir = indir_base + "MSG_vza.tif"
msg_vaa_dir = indir_base + "MSG_vaa.tif"

'''读取type数据'''
dataset = gdal.Open(indir_type)
[data, ns, nl, nb, geog_type, proj_type] =read_image_gdal(indir_type)
vza_save = np.zeros([nl,ns])
vaa_save = np.zeros([nl,ns])


'''读取角度信息和经纬度'''
[vza_data, im_width, im_height, im_bands, geotrans, proj] = read_image_gdal(msg_vza_dir)
[vaa_data, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(msg_vaa_dir)
lon = vza_data[1]
lat = vza_data[2]
vza = vza_data[0]
vaa = vaa_data[0]
ind = (lon == np.inf)
lon[ind] = 0
lat[ind] = 0

'''粗投影'''
dataset = gdal.Open(indir_type)
indx, indy = loc2map(lat, lon, dataset)
# indx[indx == 18000/3] = 0
# indy[indy == 36000/3] = 0
indx = np.reshape(indx, [im_height, im_width])
indy = np.reshape(indy, [im_height, im_width])

vza_save[indx, indy] = vza
vaa_save[indx, indy] = vaa

outfile1 = outdir + "MSG_vza_0.03.tif"
outfile2 = outdir + "MSG_vaa_0.03.tif"
write_image_gdal(vza_save, ns, nl, 1, geog_type, proj_type, outfile1)
write_image_gdal(vaa_save, ns, nl, 1, geog_type, proj_type, outfile2)
print("Save successful")




