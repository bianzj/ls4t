

from base.util_data import *
from base.util_file import *
from base.util_lst import *
from base.util_phys import *


indir0 = r"/Users/bianzj/Downloads/data/"
indir = indir0 + r"airborne/"


infile = indir + "TASI_2012_06_30_143420_g.pix"
obs,ns,nl,nb,geog,proj = read_image_gdal(infile)


infile = indir + "TASI_2012_06_30_143420_A_B0328_LST.img"
lst,ns,nl,nb,geog,proj = read_image_gdal(infile)

wl_ = linspace(8.0,11.4,32)
obs0 = [planck(wl,lst) for wl in wl_]


emis = obs/obs0

outfile =  indir + "TASI_2012_06_30_143420_g_emis.pix"
write_image_gdal(emis,ns,nl,32,geog,proj,outfile)

plt.imshow(lst)
plt.show()

