
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import netCDF4
import time
from base.util_constant import *
from base.util_file import *
from base.util_data import *
import math
import warnings
import shutil
import numpy as np

warnings.filterwarnings("ignore")




infile = "/home/hero/下载/2020-era5-tcwv/data.grib"



