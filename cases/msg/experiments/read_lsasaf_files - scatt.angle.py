import os
import sys
import h5py
import argparse
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import math
import datetime as dt
try:
    from importlib import reload
except ImportError:
    try:
        from imp import reload
    except ImportError:
        pass
import pandas as pd
import scipy.optimize as so
import warnings

from pvlib import atmosphere
from pvlib.tools import datetime_to_djd, djd_to_datetime
import pvlib
from pvlib.location import Location

file_in = 'D:/MSG/HDF5_LSASAF_MSG_VAA_MSG-Disk'
hf = h5py.File(file_in,'r')
for key in hf.keys():
    dset = hf[key]
VAA = dset[:][:]
VAA = VAA / 100

file_in = 'D:/MSG/HDF5_LSASAF_MSG_VZA_MSG-Disk'
hf = h5py.File(file_in,'r')
for key in hf.keys():
    dset = hf[key]
VZA = dset[:][:]
VZA = VZA / 100

file_in = 'D:/MSG/hdf5_lsasaf_msg_lat_msg-disk_4bytesprecision'
hf = h5py.File(file_in,'r')
for key in hf.keys():
    dset = hf[key]
LAT = dset[:][:]
LAT = LAT / 10000

file_in = 'D:/MSG/hdf5_lsasaf_msg_lon_msg-disk_4bytesprecision'
hf = h5py.File(file_in,'r')
for key in hf.keys():
    dset = hf[key]
LON = dset[:][:]
LON = LON / 10000

file_in = 'D:/MSG/hdf5_lsasaf_usgs-igbp_lwmask_msg-disk'
hf = h5py.File(file_in,'r')
for key in hf.keys():
    dset = hf[key]
LWM = dset[:][:]

for i in range(0,3712):
    ind = np.where(LWM[i,:]==0)
    LWM[i,ind]=2
    ind = np.where(LWM[i,:]==1)
    LWM[i,ind]=0

##############################
# calcul des angles solaires #
##############################

deg2rad = math.pi/180

NS_PER_HR = 1.e9 * 3600.  # nanoseconds per hour

elev = 0
altitude = 0
pressure = 101325 / 100  # pressure must be in millibars for calculation

atmos_refract = 0.5667

for d in range(6,7,1):
    strd = str(d)
    if len(strd) == 1: strd = '0'+strd 
    for hh in range(11,14):
        strh = str(hh)
        if len(strh) == 1: strh = '0'+strh 
#        for mn in range(0,60,15):
        for mn in range(0,60,15):
            strm = str(mn)
            if len(strm) == 1: strm = '0'+strm
            date = '2023-10-'+strd
            date1= date+'-'+strh+'-'+strm
            times = pd.date_range(date+' '+strh+':'+strm+':00', date+' '+strh+':'+strm+':00', freq='0.25H', tz='UTC')
            csca = LWM*1.0    
            for j in range(0,3712):#500,1500
                for i in range(0,3712):#1200,2200
                    latitude = LAT[i,j]
                    longitude = LON[i,j]           
#                    if latitude != 91000 and csca[i,j] == 0:
                    if latitude <= 70000 and latitude >= 15000 and csca[i,j] == 0:
                        site = Location(latitude, longitude, 'Etc/GMT', altitude, 'None') 
                        solpos = pvlib.solarposition.get_solarposition(times, site.latitude, site.longitude, site.altitude, method='nrel_numpy')
                        SZA = solpos['zenith'].to_numpy()
                        SAA = solpos['azimuth'].to_numpy()
                        csca[i,j] = math.cos(SZA*deg2rad)*math.cos(VZA[i,j]*deg2rad) + \
                            math.sin(SZA*deg2rad)*math.sin(VZA[i,j]*deg2rad) * \
                            math.cos(abs(SAA-VAA[i,j])*deg2rad)
            # if csca > csca0:
            #     csca0 = csca
                        print(date1,i,j,latitude,longitude,SZA,SAA,VZA[i,j],VAA[i,j],csca[i,j])

            hf = h5py.File('E:/MSG/csca_'+date1+'.h5', 'w')
            hf.create_dataset('csca', data=csca)
#        <HDF5 dataset "csca": shape (3712, 3712), type "<f8">
            hf.close()

# for i in range(0,dim[0]):
#     if float(sza[i])<90:
#         print(str(times[i]),str(sza[i]),str(saa[i]),file=f)

# f.close()

# extent = 0, 3712, 0, 3712
# im2 = plt.imshow(csca, cmap="hot", alpha=1.0, extent=extent, vmin=0, vmax=1)
# fig = plt.subplots_adjust(bottom=0.09, right=0.92, top=0.89)
# cax = plt.axes([0.82, 0.110, 0.03, 0.76])
# cbar = plt.colorbar(cax=cax)
# cbar.set_label('cosine scattering angle', rotation=270, labelpad=20) #va='center')
# #plt.savefig(dir_path+"zenith_Optris.png")
# plt.show()

extent = 0, 3712, 0, 3712
cmap = plt.get_cmap('terrain', 7)
im2 = plt.imshow(csca, cmap,alpha=1.0, extent=extent, vmin=0., vmax=1)
fig = plt.subplots_adjust(bottom=0.09, right=0.92, top=0.89)
cax = plt.axes([0.82, 0.110, 0.03, 0.76])
cbar = plt.colorbar(cax=cax)
cbar.set_label('cosine scattering angle', rotation=270, labelpad=20) #va='center')
#plt.savefig(dir_path+"zenith_Optris.png")
plt.show()


###########################################################

def get_solarposition(time, latitude, longitude,
                      altitude=None, pressure=None,
                      method='nrel_numpy',
                      temperature=12, **kwargs):

    if altitude is None and pressure is None:
        altitude = 0.
        pressure = 101325.
    elif altitude is None:
        altitude = atmosphere.pres2alt(pressure)
    elif pressure is None:
        pressure = atmosphere.alt2pres(altitude)

    method = method.lower()
    if isinstance(time, dt.datetime):
        time = pd.DatetimeIndex([time, ])

        ephem_df = spa_python(time, latitude, longitude, altitude,
                              pressure, temperature,
                              how='numpy', **kwargs)

    return ephem_df


def _spa_python_import(how):
    """Compile spa.py appropriately"""

    from pvlib import spa

    # check to see if the spa module was compiled with numba
    using_numba = spa.USE_NUMBA

    if how == 'numpy' and using_numba:
        # the spa module was compiled to numba code, so we need to
        # reload the module without compiling
        # the PVLIB_USE_NUMBA env variable is used to tell the module
        # to not compile with numba
        warnings.warn('Reloading spa to use numpy')
        os.environ['PVLIB_USE_NUMBA'] = '0'
        spa = reload(spa)
        del os.environ['PVLIB_USE_NUMBA']
    elif how == 'numba' and not using_numba:
        # The spa module was not compiled to numba code, so set
        # PVLIB_USE_NUMBA so it does compile to numba on reload.
        warnings.warn('Reloading spa to use numba')
        os.environ['PVLIB_USE_NUMBA'] = '1'
        spa = reload(spa)
        del os.environ['PVLIB_USE_NUMBA']
    elif how != 'numba' and how != 'numpy':
        raise ValueError("how must be either 'numba' or 'numpy'")

    return spa


def spa_python(time, latitude, longitude,
               altitude=0, pressure=101325, temperature=12, delta_t=67.0,
               atmos_refract=None, how='numpy', numthreads=4, **kwargs):

    lat = latitude
    lon = longitude
    elev = altitude
    pressure = pressure / 100  # pressure must be in millibars for calculation

    atmos_refract = atmos_refract or 0.5667

    if not isinstance(time, pd.DatetimeIndex):
        try:
            time = pd.DatetimeIndex(time)
        except (TypeError, ValueError):
            time = pd.DatetimeIndex([time, ])

    unixtime = np.array(time.view(np.int64)/10**9)

    spa = _spa_python_import(how)

    delta_t = delta_t or spa.calculate_deltat(time.year, time.month)

    app_zenith, zenith, app_elevation, elevation, azimuth, eot = \
        spa.solar_position(unixtime, lat, lon, elev, pressure, temperature,
                           delta_t, atmos_refract, numthreads)

    result = pd.DataFrame({'apparent_zenith': app_zenith, 'zenith': zenith,
                           'apparent_elevation': app_elevation,
                           'elevation': elevation, 'azimuth': azimuth,
                           'equation_of_time': eot},
                          index=time)

    return result
