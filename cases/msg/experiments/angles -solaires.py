
import logging
import warnings
from datetime import datetime, timedelta

import dask.array as da
import numpy as np
import xarray as xr
from pandas.core.resample import TimeGrouper

#from pyresample import geometry
import matplotlib.pyplot as plt

import os
import math
import glob
import pandas as pd

import datetime as dt
try:
    from importlib import reload
except ImportError:
    try:
        from imp import reload
    except ImportError:
        pass

from pvlib import atmosphere
#from pvlib.tools import datetime_to_djd, djd_to_datetime
import pvlib
from pvlib.location import Location


deg2rad = math.pi/180

NS_PER_HR = 1.e9 * 3600.  # nanoseconds per hour

elev = 0
altitude = 0
pressure = 101325 / 100  # pressure must be in millibars for calculation

atmos_refract = 0.5667
  
# Tatuoca
latitude = 1.2024817
longitude = -48.50629427

data = [0]*15

YY = '2024'

print()

f_out = open('E:/Tatuoca/time_23022024.txt', "w")

for mm in range(2,3):
    strm = str(mm)
    if len(strm) == 1: strm = '0'+strm 
    for dd in range(23,24):
        strd = str(dd)
        if len(strd) == 1: strd = '0'+strd
        date = YY+strm+strd
        for hh in range(9,22):
            strh = str(hh)
            if len(strh) == 1: strh = '0'+strh
            for mn in range(0,60,5):
                strmn = str(mn)
                if len(strmn) == 1: strmn = '0'+strmn  
                times = pd.date_range(date+' '+strh+':'+strmn+':00', date+' '+strh+':'+strmn+':00', freq='0.25H', tz='UTC')
                site = Location(latitude, longitude, 'Etc/GMT', altitude, 'None') 
                solpos = pvlib.solarposition.get_solarposition(times, site.latitude, site.longitude, site.altitude, method='nrel_numpy')
                SZA = solpos['zenith'].to_numpy()
                SZA = int(SZA*100)/100
                SAA = solpos['azimuth'].to_numpy()
                SAA = int(SAA*100)/100
                if SAA < 0 : SSA = 360 + SAA
                date1 = date + strh + strmn
                data[0] = float(date1)    
                data[1] = float(SAA)
                data[2] = float(SZA)
                data[3] = latitude
                data[4] = longitude
                print(data)
                valeurs = "%14.0f %10.6f %10.6f %10.6f %10.6f\n" \
                    % (data[0],data[1],data[2],data[3],data[4])
                f_out.write(valeurs)

f_out.close()


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
