import numpy as np

from util.util import *


### forest and crop
lat_ =np.asarray([38.848909,38.853457])
lon_ = np.asarray([100.371799,100.371343])

# lat_ =np.asarray([38.85544116,38.853457])
# lon_ = np.asarray([100.37424145,100.371343])


infile_type = r'D:\data\type\type_heihe_1000_new.tif'
type, ns, nl, nb, geog, proj,dataset = read_image_dataset_gdal(infile_type)
imagex_,imagey_ = loc2map(lat_,lon_,dataset)



indir_lsct = r'D:\data\LSCT_heihe_2022\slstr_2022\lsct2_soil\\'
indir_tif = r'D:\data\LSCT_heihe_2022\slstr_2022\tif\\'
infiles = search_file(indir_lsct,['lsct'])
n_file = np.size(infiles)
outfile = r'D:\data\LSCT_heihe_2022\lsct2_soil.txt'

off = 1 # distance for averge
tc_inv_ = []
tsh_inv_ = []
tss_inv_ = []
time_ =[]
doy_ = []
cloud_nadir_ = []
cloud_obliq_ = []
for k in range(n_file):
    filename = infiles[k][:12]
    print(filename)
    infile_lsct = indir_lsct + infiles[k]

    infile_time = indir_tif+filename+'day_time.tif'
    infile_cloud_nadir = indir_tif+filename+'day_cloud_nadir.tif'
    infile_cloud_obliq = indir_tif+filename +'day_cloud_obliq.tif'
    [lsct,ns,nl,nb,geog,proj] = read_image_gdal(infile_lsct)
    [cloud_nadir,ns,nl,nb,geog,proj] = read_image_gdal(infile_cloud_nadir)
    [cloud_obliq,ns,nl,nb,geog,proj] = read_image_gdal(infile_cloud_obliq)
    [time,ns,nl,nb,geog,proj] = read_image_gdal(infile_time)

    tss_inv = lsct[0,imagex_,imagey_]
    tc_inv = lsct[1,imagex_,imagey_]

    # tss_inv = getStatic_ave(lsct[0,:,:],imagex_,imagey_,off)
    # tsh_inv =  getStatic_ave(lsct[1,:,:],imagex_,imagey_,off)
    # tc_inv =  getStatic_ave(lsct[2,:,:],imagex_,imagey_,off)
    doy = np.int_(filename[8:11])

    doy_.append(doy)
    time_.append(time[imagex_[0],imagey_[0]])
    cloud_nadir_.append(cloud_nadir[imagex_,imagey_])
    cloud_obliq_.append(cloud_obliq[imagex_,imagey_])
    tc_inv_.append(tc_inv)
    tss_inv_.append(tss_inv)



tc_inv_ = np.asarray(tc_inv_)
tss_inv_ = np.asarray(tss_inv_)
tsh_inv_ = np.asarray(tsh_inv_)
time_ = np.asarray(time_)
cloud_nadir_ = np.asarray(cloud_nadir_)
cloud_obliq_ = np.asarray(cloud_obliq_)
tc1_inv_ = (tc_inv_[:,0])
tss1_inv_ = (tss_inv_[:,0])

cloud1_ = cloud_nadir_[:,0]+cloud_obliq_[:,0]

tc2_inv_ = (tc_inv_[:,1])
tss2_inv_ = (tss_inv_[:,1])
cloud2_ =  cloud_nadir_[:,1]+cloud_obliq_[:,1]

result = np.vstack([doy_,time_,cloud1_,tss1_inv_,tc1_inv_,cloud2_,tss2_inv_,tc2_inv_])

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

np.savetxt(outfile,result,fmt='%.3f')