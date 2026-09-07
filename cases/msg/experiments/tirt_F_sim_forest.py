
import matplotlib.pyplot as plt
import numpy as np

from base.util_kernel import fitting_DTC
from base.util_lst import *
from base.util_data import *
from base.util_fitting import *
from base.util_kernel import *
from base.util_file import *
import h5py
import seaborn as sns
import seaborn_image as isns
from pvlib import atmosphere
#from pvlib.tools import datetime_to_djd, djd_to_datetime
import pvlib
from pvlib.location import Location
from osgeo import gdal
from osgeo import osr
import os
import pyresample as pr
from satpy import Scene
from base.rt.hom import *
from base.rt.crown import *

deg2rad = 3.1415926/180
NS_PER_HR = 1.e9 * 3600.  # nanoseconds per hour
elev = 0
altitude = 0
pressure = 101325 / 100  # pressure must be in millibars for calculation
atmos_refract = 0.5667
line1 = 3712  # 1rst line (start reading from south)
lineN = 0  # last line (northwards)

indir = r"/Users/bianzj/Downloads/data/msg/"
outdir = indir + "/sitedata/"
indir0 = r"/Users/bianzj/Downloads/data/msg/output/"

infile = indir + "sites.txt"
site_info = read_txt_str(infile, r",")
site_name = np.asarray([_[0] for _ in site_info])
lat_ = np.asarray([_[1] for _ in site_info], dtype=float)
lon_ = np.asarray([_[2] for _ in site_info], dtype=float)
num_site = len(site_name)

'''This is for tempeature of components'''
ksm = 0.15
klai = 2.0
kyear = 2025
kmonth = 6
kday = 5


'''this is for obs sim'''
klai0 = 2.5
hspot = 0.15
stand = 0.05
radi_vertical = 2.0
radi_horizontal = 2.0
wl = 10.5
emissivity_soil = 0.955
emissivity_leaf = 0.975
vza = np.asarray([28.2900, 42.1200 ]) ### euro and iodc
vaa = np.asarray([-38.7300+360, 61.5600])  ### euro and iodc




'''1.initial;'''
crown = Crown()
'''2.set variables;'''
crown.set_structure(klai0, hspot,stand,radi_vertical,radi_horizontal)
crown.set_optical(wl, emissivity_soil, emissivity_leaf)

''''3.run'''

indir = os.path.join(indir0, f"F_2025_LAI{klai:.1f}_SMC{ksm:.2f}/")
for ksite in range(5,6):
    date_str = '%04d'%(kyear)+"-%02d"%(kmonth)+"-%02d"%(kday)
    kdoy = date2DOY(kyear,kmonth,kday)
    infile_temp = os.path.join(indir0, f"F_2025_LAI{klai:.1f}_SMC{ksm:.2f}/surftemp.dat")
    try:
        temps = read_txt_array(infile_temp, 0, 11)
        print(f"成功读取温度数据，形状: {temps.shape}")
    except Exception as e:
        print(f"读取温度数据失败: {e}")
        temps = np.array([])

    obs_ = np.asarray([])
    for khh in range(1,24,1):
        for kmm in range(0,60,15):
            time_temp = pd.date_range(date_str + ' ' + np.str_(khh) + ':' + np.str_(kmm) + ':00',
                                      date_str + ' ' + np.str_(khh) + ':' + np.str_(kmm) + ':00',
                                      freq='0.25h', tz='UTC')
            site_temp = Location(lat_[ksite], lon_[ksite], 'Etc/GMT', altitude, 'None')
            solpos_temp = pvlib.solarposition.get_solarposition(time_temp, site_temp.latitude, site_temp.longitude, site_temp.altitude, method='nrel_numpy')
            sza_temp = solpos_temp['zenith'].to_numpy()
            sza = np.int_(sza_temp[0] * 100) / 100
            saa_temp = solpos_temp['azimuth'].to_numpy()
            saa = np.int_(saa_temp[0] * 100) / 100
            ktime = khh/24+kmm/60/24.0 + kdoy
            ind = where(abs(ktime - temps[:,2])<0.001)
            compts = temps[ind,4:8]+273.15
            crown.set_thermal(compts[0,0,1], compts[0,0,0], compts[0,0,2],compts[0,0,3])
            raa = np.abs(vaa - saa)
            if sza > 85: sza = 85
            crown.set_angle(vza, sza, raa)
            obs = crown.run()

            line = np.asarray([ktime,sza,saa,vza[0],vaa[0],obs[0],vza[1],vaa[1],obs[1]])
            if obs_.shape[0]>0:
                obs_ = np.vstack((obs_, line))
            else:
                obs_ = line

        a = 10


    plt.plot(obs_[:,0], obs_[:,5], 'ro')
    plt.plot(obs_[:,0], obs_[:,8], 'bo')
    plt.show()