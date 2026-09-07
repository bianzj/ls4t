import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from cases.AATSR_product.util.util_aatsr import *
import time
import warnings
warnings.filterwarnings("ignore")

indir_lai = r'/media/hero/lsct02/lai/'
indir_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/0_raw_h5/SN-Dhr/'

fileNames = search_file(indir_sites,['h5'])
fileNames.sort()
for fileName in fileNames:
    print(fileName)
    year = int(fileName.split('_')[1])
    doy = int(fileName.split('_')[2])
    doy1 = (doy//4)*4 + 1
    doy2 = doy1 + 4
    f = doy % 4 - 1
    infile_doy1 = indir_lai  + r'/%04d/LAI_%04d%03d.h5' % (year,year,doy1)
    infile_doy2 = indir_lai  + r'/%04d/LAI_%04d%03d.h5' % (year,year,doy2)

    if os.path.exists(infile_doy1) and os.path.exists(infile_doy2):
        print(infile_doy1,infile_doy2)
        lai1 = read_h5py_item(infile_doy1,'data')
        lai2 = read_h5py_item(infile_doy2,'data')
        lai = lai1 * (4 - f) / 4 + lai2 * f / 4

        indx,indy,lai_site = read_h5py_items(indir_sites + fileName, ['indx','indy','lai'])
        indx = indx.astype('int')
        indy = indy.astype('int')

        lai_new = lai[indx,indy]

        print(lai_new[16,16],lai_site[16,16])
        print(np.nanmean(lai_new - lai_site))
        write_h5py_item(indir_sites + fileName, 'lai_new',lai_new, 'f')


