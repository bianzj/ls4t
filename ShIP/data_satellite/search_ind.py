from util.util import *

target_lat = 38.54043
target_lon = -8.003297

indir_med = r'F:\data\MSG_2017_full-range\native\med\\'
outfile_lon = indir_med + 'lon.tif'
outfile_lat = indir_med + 'lat.tif'
[lon, ns, nl, temp3, temp4, temp5] = read_image_gdal(outfile_lon)
[lat, ns, nl, temp3, temp4, temp5] = read_image_gdal(outfile_lat)

min_dis = 1000
target_i = 0
target_j = 0
# ns是图像宽度，nl是图像高度
for i in range(nl):
    for j in range(ns):
        print(i,j)
        if lat[i,j] == np.inf: continue
        dif_lat = target_lat - lat[i,j]
        dif_lon = target_lon - lon[i, j]
        dis = sqrt(dif_lon*dif_lon+dif_lat*dif_lat)
        if dis<min_dis:
            min_dis = dis
            target_i = i
            target_j = j
            print("closer")
print(target_i,target_j)



