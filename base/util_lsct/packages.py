import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from base.util_packages import *
from base.util_lsct.rt.hom import *
from base.util_lsct.rt.crown import *
import pysolar.solar as Sun
from scipy.optimize import fsolve
from multiprocessing import Pool, freeze_support, cpu_count


'''推荐python版本：3.11'''