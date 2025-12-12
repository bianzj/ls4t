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
from satpy import Scene

deg2rad = 3.1415926/180
NS_PER_HR = 1.e9 * 3600.  # nanoseconds per hour
elev = 0
altitude = 0
pressure = 101325 / 100  # pressure must be in millibars for calculation
atmos_refract = 0.5667
line1 = 3712  # 1rst line (start reading from south)
lineN = 0  # last line (northwards)

indir = r"/Users/bianzj/Downloads/data/LSA-SAF/LSASAF_Inputs/MSG/sample/"

#
infile = indir + "/others/MSG_VZA"
vza,ns,nl,nb,goog,proj = read_image_gdal(infile)
infile = indir + "/others/MSG_VAA"
vaa,ns,nl,nb,goog,proj = read_image_gdal(infile)

infile = indir + "/others/DISK_LAT.img"
lat,ns,nl,nb,goog,proj = read_image_gdal(infile)
infile = indir + "/others/DISK_LON.img"
lon,ns,nl,nb,goog,proj = read_image_gdal(infile)


name = 'Victoria'
# col = 2975
# lin = 1888
lat_temp = -0.86667
lon_temp = 32.86667

distance = np.power((lon - lon_temp),2) + np.power((lat - lat_temp),2)
tempx,tempy = np.where(distance==np.min(distance))
lin = tempx[0]
col = tempy[0]
col = 2525
lin = 2423

time_bias = 12 * (int(lin) - line1) / (line1 - lineN) + 3  # in minutes


vza_temp = vza[lin,col]/100.0
vaa_temp = vaa[lin,col]/100.0



indir = '/Users/bianzj/Downloads/data/LSA-SAF/LSASAF_Inputs/MSG/sample/tb/'
files = search_file(indir,"HDF")
infiles = np.asarray([indir+file for file in files])

line_ = np.array([])
for k in range(len(files)):
    infile = indir + files[k]
    hf = h5py.File(infile,'r')
    dset = hf["Brightness Temperature"]
    BT = dset[:][:]
    bt_temp = BT[lin,col]* 0.01 + 273.15


    date_str = files[k][-12:-4]
    year_str = files[k][-12:-8]
    month_str = files[k][-8:-6]
    day_str = files[k][-6:-4]
    hh_str = files[k][-4:-2]
    mn_str = files[k][-2:]

    year_int = int(year_str)
    month_int = int(month_str)
    day_int = int(day_str)
    hh_int = int(hh_str)
    mn_int = int(mn_str) - time_bias
    if mn_int < 0:
        mn_int = mn_int + 60
        hh_int = hh_int - 1
    mn_str = str(mn_int)
    hh_str = str(hh_int)
    times = pd.date_range(date_str + ' ' + hh_str + ':' + mn_str + ':00', date_str + ' ' + hh_str + ':' + mn_str + ':00',
                          freq='0.25H', tz='UTC')
    site = Location(lat_temp, lon_temp, 'Etc/GMT', altitude, 'None')
    solpos = pvlib.solarposition.get_solarposition(times, site.latitude, site.longitude, site.altitude, method='nrel_numpy')
    sza_temp = solpos['zenith'].to_numpy()
    sza_temp = int(sza_temp * 100) / 100
    saa_temp = solpos['azimuth'].to_numpy()
    saa_temp = int(saa_temp * 100) / 100

    print(files[k])
    line = np.asarray([lat_temp,lon_temp,year_int,month_int,day_int,hh_int,mn_int,sza_temp,saa_temp,vza_temp,vaa_temp,bt_temp])
    if(k == 0):
        line_ = line
    else:
        line_ = np.vstack([line_,line])

ind = np.argsort(line_[:,5]*60+line_[:,6])
line_ = line_[ind,:]


obs = np.asarray(line_[:,11])
pst = np.asarray(line_[:,5]+line_[:,6]/60.0)

ind = (pst > 4.0) & (pst < 20.0)

results = fitting_DTC(obs[ind],pst[ind],Tbase = 273.15)
fitted = model_DTC(results,pst)


plt.plot(pst,obs,"o")
plt.plot(pst,fitted,"r-")
plt.show()











