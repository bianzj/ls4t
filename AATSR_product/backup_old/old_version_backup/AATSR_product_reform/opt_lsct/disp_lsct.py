from utils.old.util_old import *


infile = '/home/bianzj/AATSR_test/lsct/AATSR_2012_001_015548__lsct.tif'


data,ns,nl,nb,geog,proj = read_image_gdal(infile)

da = data[0,:,:]
plt.imshow(da)
plt.show()


