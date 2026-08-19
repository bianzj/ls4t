import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_file import *
from base.util_data import *
import os
import calendar
from datetime import datetime,timedelta



indir = r"E:/aatsr_global/"
outdir = r"E:/aatsr_month/"

nl = 14570
ns = 36000
nb = 1

for kyear in range(2003,2004):
    for kmonth in range(1,13):

        tempall = np.zeros((nl,ns))
        timeall = np.zeros((nl,ns))

        for kday in range(1, calendar.monthrange(kyear, kmonth)[1]+1):
            infile = indir + '%04d/%02d/%02d/aatsr_%04d_%02d_%02d_day_lstN.tif'%(kyear,kmonth,kday,kyear,kmonth,kday)

            print(infile)
            temp,ns,nl,nb,geog,proj = read_image_gdal(infile)

            ind = np.where(temp>=225)
            tempall[ind] =tempall[ind] + temp[ind]
            timeall[ind] = timeall[ind] + 1



        valid_mask = timeall > 0
        tempall[valid_mask] = tempall[valid_mask] / timeall[valid_mask]
        outfile = outdir + r"aatsr_month_%04d/%02d/%02d_lst.tif"%(kyear,kmonth,kday)

        write_image_gdal(outfile,tempall,ns,nl,nb,geog,proj)




