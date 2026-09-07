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
VAA_ = dset[:][:]
VAA_ = VAA_ / 100

file_in = 'D:/MSG/HDF5_LSASAF_MSG_VZA_MSG-Disk'
hf = h5py.File(file_in,'r')
for key in hf.keys():
    dset = hf[key]
VZA_ = dset[:][:]
VZA_ = VZA_ / 100

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

# Tenerife
#col = 1340
#lin = 885

# TIDBIT1
# col = 2357
# lin = 2682

# Beyrouth
#col = 2825
#lin = 750

##############################
# calcul des angles solaires #
##############################

deg2rad = math.pi/180

NS_PER_HR = 1.e9 * 3600.  # nanoseconds per hour

elev = 0
altitude = 0
pressure = 101325 / 100  # pressure must be in millibars for calculation

atmos_refract = 0.5667

#file = 'hotspot_Beyrouth_2023.dat'    
#f_out = open('C:/Users/roujeanj/Desktop/Python/'+file, "w")

data = [0]*10

month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

for m in range(9,10,1):
    strm = str(m)
    if len(strm) == 1: strm = '0'+strm 
#    for d in range(1,month[m-1]+1,1):
    for d in range(21,22,1):
        strd = str(d)
        if len(strd) == 1: strd = '0'+strd 
        for hh in range(12,13):
            strh = str(hh)
            if len(strh) == 1: strh = '0'+strh 
            for mn in range(15,60,60):
                strmn = str(mn)
                if len(strmn) == 1: strmn = '0'+strmn
                date = '2023-'+strm+'-'+strd
                date1= date+'-'+strh+'-'+strmn
                times = pd.date_range(date+' '+strh+':'+strmn+':00', date+' '+strh+':'+strmn+':00', freq='0.25H', tz='UTC')
                csca = LWM*1.0    
                for j in range(0,3712):#500,1500
                    for i in range(0,3712):#1200,2200
                        if LWM[i,j] == 0:
#                        if csca[i,j] == 17: csca[i,j]=0
                            latitude = LAT[i,j]
                            longitude = LON[i,j]
                        #                    if latitude <= 15 and latitude >= 7 and longitude <= 76 and longitude >= 68 and csca[i,j] == 0:
#                        if latitude <= 35 and latitude >= 5 and longitude <= 90 and longitude >= 65 and csca[i,j] == 0:
#                        if i == int(lin) and j == int(col) and csca[i,j] == 0:
#                           print(latitude,longitude)
                            site = Location(latitude, longitude, 'Etc/GMT', altitude, 'None') 
                            solpos = pvlib.solarposition.get_solarposition(times, site.latitude, site.longitude, site.altitude, method='nrel_numpy')
                            SZA = solpos['zenith'].to_numpy()
                            SZA = int(SZA*100)/100
                            SAA = solpos['azimuth'].to_numpy()
                            SAA = int(SAA*100)/100
                            if SAA < 0 : SSA = 360 + SAA
                            VAA = float(VAA_[i,j])
                            if VAA < 0 : VAA = 360 + VAA
                            VZA = float(VZA_[i,j])
                            csca[i,j] = math.cos(SZA*deg2rad)*math.cos(VZA*deg2rad) + \
                                math.sin(SZA*deg2rad)*math.sin(VZA*deg2rad) * \
                                    math.cos(abs(SAA-VAA)*deg2rad)
                            print(date1,i,j,latitude,longitude,SZA,SAA,VZA,VAA,csca[i,j])

            # if csca > csca0:
            #     csca0 = csca
#                        if float(SZA) <90:
#                             data[0] = date1
#                             data[1] = i
#                             data[2] = j
#                             data[3] = latitude
#                             data[4] = longitude
#                             data[5] = SZA
#                             data[6] = SAA
#                             data[7] = VZA
#                             data[8] = VAA
#                             data[9] = csca[i,j]
# #                           print(data)   
#                             valeurs = "%17a %5i %5i %8.4f %8.4f %8.2f %8.2f %8.2f %8.2f %12.8f\n" \
#                                 % (data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9])
#                             f_out.write(valeurs)
    
                hf = h5py.File('D:/MSG/images_HS/csca_'+date1+'_Euro.h5', 'w')
                hf.create_dataset('csca', data=csca)
 #        <HDF5 dataset "csca": shape (3712, 3712), type "<f8">
                hf.close()

                extent = 0, 3712, 0, 3712
                cmap = plt.get_cmap('nipy_spectral',500)
                im2 = plt.imshow(csca, cmap,alpha=1.0, extent=extent, vmin=0.50, vmax=1.)
#                cmap = plt.get_cmap('terrain', 7)
#                im2 = plt.imshow(csca, cmap,alpha=1.0, extent=extent, vmin=0., vmax=1)
#                fig = plt.subplots_adjust(bottom=0.09, right=0.92, top=0.89)
#                cax = plt.axes([0.82, 0.110, 0.03, 0.76])
                fig = plt.subplots_adjust(bottom=0.09, right=0.92, top=0.89)
                cax = plt.axes([0.82, 0.110, 0.03, 0.76])
                cbar = plt.colorbar(cax=cax)
#                cbar.set_label('cosine scattering angle', rotation=270, labelpad=20) #va='center')
                cbar.set_label('cosine scattering angle', rotation=270, labelpad=20) #va='center')
                cax.text(-14,0.60, date1, fontsize=12, verticalalignment='top', color='k')
                plt.savefig('D:/MSG/figures_HS/csca_'+date1+'_Euro.png')
                plt.show()


f_out.close()

# for i in range(0,dim[0]):
#     if float(sza[i])<90:
#         print(str(times[i]),str(sza[i]),str(saa[i]),file=f)

# f.close()



# extent = 0, 3712, 0, 3712
# cmap = plt.get_cmap('terrain', 7)
# im2 = plt.imshow(csca, cmap,alpha=1.0, extent=extent, vmin=0., vmax=1)
# fig = plt.subplots_adjust(bottom=0.09, right=0.92, top=0.89)
# cax = plt.axes([0.82, 0.110, 0.03, 0.76])
# cbar = plt.colorbar(cax=cax)
# cbar.set_label('cosine scattering angle', rotation=270, labelpad=20) #va='center')
# #plt.savefig(dir_path+"zenith_Optris.png")
# plt.show()


###########################################################

def get_solarposition(time, latitude, longitude,
                      altitude=None, pressure=None,
                      method='nrel_numpy',
                      temperature=12, **kwargs):

    if altitude is None and pressure is NonD:
        altitude = 0.
        pressure = 101325.
    elif altitude is NonD:
        altitude = atmosphere.pres2alt(pressure)
    elif pressure is NonD:
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
