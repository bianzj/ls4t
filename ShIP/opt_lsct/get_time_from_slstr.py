import numpy as np

from util.util import *


### forest and crop
lat_ =np.asarray([38.848909,38.853457])
lon_ = np.asarray([100.371799,100.371343])


infile_type = r'D:\data\type\type_heihe_1000_utm47N.tif'
type, ns, nl, nb, geog, proj,dataset = read_image_dataset_gdal(infile_type)
imagex_,imagey_ = loc2map(lat_,lon_,dataset)

indir_tif = r'F:\data\S3_2022_heihe\tif\\'
indir_lst = r'F:\data\S3_2022_heihe\lst\\'
infiles = search_file_rej(indir_lst,['lst_obliq'],'enp')
n_file = np.size(infiles)


off = 1 # distance for averge
time1_ =[]
time2_ =[]
doy_ = []

for k in range(n_file):
    filename = infiles[k][:-13]
    print(filename)
    infile_lst = indir_lst + infiles[k]

    infile_time = indir_tif+filename+'time.tif'

    [time,ns,nl,nb,geog,proj] = read_image_gdal(infile_time)
    [lst_o, ns, nl, nb, geog, proj] = read_image_gdal(infile_lst)
    if lst_o[imagex_[0], imagey_[0]] == 0 or lst_o[imagex_[1], imagey_[1]] == 0:
        continue


    doy = np.int_(filename[9:12])
    time1_.append(time[imagex_[0], imagey_[0]])
    time2_.append(time[imagex_[1], imagey_[1]])

    doy_.append(doy)



result = np.vstack([doy_,time1_,time2_])

# ind = (tc1_inv_ > 250)*(tss1_inv_>250)*(tsh1_inv_>250)
# plt.plot(tc1_inv_[ind],'green')
# plt.plot(tss1_inv_[ind],'red')
# plt.plot(tsh1_inv_[ind],'blue')
# plt.show()
#
# ind = (tc2_inv_ > 250)*(tss2_inv_>250)*(tsh2_inv_>250)
# plt.plot(tc2_inv_[ind],'green')
# plt.plot(tss2_inv_[ind],'red')
# plt.plot(tsh2_inv_[ind],'blue')
# plt.show()
result = np.transpose(result)
outfile = r'F:\data\S3_2022_heihe\time.txt'
np.savetxt(outfile,result,fmt='%.3f')