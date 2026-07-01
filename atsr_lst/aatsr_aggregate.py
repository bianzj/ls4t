import os
import time

from base.util_file import read_image_gdal

# ================= 锁死底层多线程，防止 384 核互相打架 =================
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["GDAL_NUM_THREADS"] = "1"
# ================================================================

import glob
import warnings
import numpy as np
import rasterio
from rasterio.transform import Affine
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

warnings.filterwarnings("ignore")

from base.util_data import *
from base.util_file import *


if __name__ == "__main__":
    indir_ref = "/media/hero/lsct04/monthly/"
    indir0 = "/media/hero/lsct04/aatsr_global/"
    outdir = "/media/hero/lsct04/aatsr_global_monthly1km/"
    year = 2003

    for kyear in range(year,year+1):
        for kmonth in range(3,4):

            infile_ref = indir_ref + "aatsr_%02d_monthly_mean_lstN_agg5.tif"%kmonth
            ref,ns0,nl0,nb,geog,proj = read_image_gdal(infile_ref)

            ns = ns0*5
            nl = nl0*5
            ref = resize_data(ref,nl,ns)
            ts_all = np.zeros([nl,ns])
            tv_all = np.zeros([nl,ns])
            count_all = np.zeros([nl,ns])
            for kday in range(1,32):

                indir = indir0 + "%04d/"%kyear + "%02d/"%kmonth + "%02d/"%kday
                infile_ts = indir + "aatsr_%04d"%kyear+"_%02d"%kmonth+"_%02d_day_Ts.tif"%kday
                infile_tv = indir + "aatsr_%04d" % kyear + "_%02d" % kmonth + "_%02d_day_Tv.tif" % kday

                print(infile_ts)
                print(infile_tv)

                if os.path.exists(infile_ts)==0:continue
                if os.path.exists(infile_tv)==0:continue
                tv, ns, nl, nb, geog, proj = read_image_gdal(infile_tv)
                ts,ns,nl,nb,geog,proj = read_image_gdal(infile_ts)


                ind = (np.abs(tv - ref)<25000) * (np.abs(ts - ref)<25000) *(np.abs(ts - tv)<35000)
                if np.sum(ind)<1: continue
                tv_all[ind] = tv_all[ind] + tv[ind]
                ts_all[ind] = ts_all[ind] + ts[ind]
                count_all[ind] = count_all[ind]+1

            ind = count_all > 0
            tv_all[ind] = tv_all[ind]/count_all[ind]
            ts_all[ind] = ts_all[ind]/count_all[ind]

            outfile_ts = outdir +  "aatsr_%04d"%kyear+"_%02d"%kmonth+"_day_Ts.tif"
            outfile_tv = outdir + "aatsr_%04d" % kyear + "_%02d" % kmonth + "_day_Tv.tif"
            write_image_gdal(ts_all,ns,nl,1,geog,proj,outfile_ts)
            write_image_gdal(tv_all, ns, nl, 1, geog, proj, outfile_tv)










