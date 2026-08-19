#!/usr/bin/env python
#-*- coding: utf-8 -*-

#from math import *
import argparse

import math
import numpy as np
#from matplotlib import pyplot as plt
#from math import floor
#import matplotlib.font_manager as font_manager
#import datetime

station = ['SABRES','URGONS','CREON','PEYRUSSE','CONDOM','LAHAS', \
          'SAVENES','MONTAUT','St FELIX','MOUTHOUMET','LEZIGNAN','NARBONNE', \
          'POR','PYR','SFr','CEu','EEu','NAfr','FLUXPEC', \
          'ROM','BLI','CIN','DAK','DJO','TAM', \
          'ILO','OUA','DMN','BAN','AGO','SOL','SED', \
          'AUR','LAM','SMOS-UV','HES', \
          'BAR','CAR','CHI','FOR','GRA','HAM','ISP','FAU', \
          'LEC','MIN','MOL','MOS','NIA','PAL','PAR','RAS', \
          'TOU', 'SMO', \
          'CH-Oe2','DE-Geb','DE-Kli','FR-Aur','FR-Avi','FR-Gri','FR-Lam','IT-BCi','IT-Cas', \
          'EU1','EU2','EU3', \
          'LIN','PAL', \
          'SBO', \
          'F1', 'F2', 'F3', 'F4', 'F5', 'F6',  \
          'Poland1', 'Poland2', 'Poland3',  \
          'Israel1', 'Israel2',  \
          'Mou','Pra','Jal','Der','Tho','Tre', \
          'LaCendrosa','Verdu',  \
          'Lautaret', \
          'Auzeville', \
          'Bernadouze', \
          'Toulouse', \
          'test', \
          'Chaal', \
          'Mahres',\
          'SMVDA',\
          'Sfax',\
          'LaCrau',\
          'Beyrouth',\
          'Nawagam',\
          'Malegaon',\
          'Bombay',\
          'Berambadi',\
          'Ko',\
          'Masada',\
          'Lisan',\
          'Evora',\
          'Thessalo',\
          'Tenerife',\
          'Gobabeb_Plains',\
          'Gobabeb_Wind',\
          'TIDBIT1',\
          'Angola',\
          'Botswana',\
          'Victoria', \
          'Guyaflux']
          
LAT2=[44.1475,43.6397,43.9936,43.6664,43.9744,43.5472, \
      43.8250,43.1922,43.4417,42.9600,43.1733,43.1500, \
      38.750,42.802,43.865,49.897,48.911,21.300,39.9403, \
      41.8396,36.5083,13.2784,14.3942,9.7601,22.7900, \
      8.32,12.2,13.216717,13.541167,15.3454,24.906933,30.855, \
      43.5497,43.4965,39.5217,48.6750, \
      41.386,44.083,51.144,35.333,37.164,53.568,45.803,43.384, \
      40.335,53.920,47.000,55.700,13.481,48.700,48.867,31.670, \
      43.136, \
      43.3833, \
      47.30,51.10,50.90,43.55,43.90,48.85,43.50,40.50,45.05, \
      51.7,44.1,46.2, \
      52.2100,48.7130, \
      30.5, \
      31.72, 31.76, 30.98, 30.98, 31.37, 32.29,  \
      51.74138889, 51.84166667, 51.758275,  \
      31.74333333, 31.70694444,  \
      45.659155, 44.582316, 46.402240,  \
      47.689676, 47.619386, 48.159816,  \
      41.693406, 41.5969444,  \
      45.03556,  \
      43.528417, \
      42.803987, \
      43.597628, \
      80, \
      34.631516, \
      34.630555, \
      34.599166, \
      34.766666, \
      43.558889, \
      33.877222, \
      22.79811, \
      20.668736, \
      19.08000, \
      11.7611, \
      6.952778, \
      31.319, \
      31.325,
      38.5411, \
      40.634, \
      28.300, \
      -23.5194, \
      -23.5508, \
      -23.5359, \
      -7.754, \
      -21.798, \
      -0.86667, \
       5.281667 ]
     
LON2=[-0.8456,-0.4350,-0.0469,0.2217,0.3361,0.8878, \
         1.1767,1.6436,1.8800,2.5300,2.7283,2.9567, \
      -7.890, 0.999,-0.862,11.880,28.154,2.372,-5.7746, \
      12.6473,2.8806,-5.9339,-16.9586,1.5990,5.5300, \
      4.34,-1.4,12.023067,2.66475,-1.479117,46.397286,34.782222, \
      1.1062,1.2379,-1.29149,7.0667, \
       2.117, 5.058,-1.437,25.282,-3.605,9.973,8.627, 1.285, \
      18.111,27.601,28.816,37.510, 2.172,2.208,2.333,-7.599, \
       6.009, \
      1.2833, \
      7.70,10.90,13.50,1.10,4.90,1.95,1.25,14.95,8.65, \
      15.3,23.3,2.7, \
      14.1220,2.2080, \
      34.5, \
      34.82, 34.82, 34.70, 34.70, 34.70, 34.86,  \
      22.09722222, 22.51388889, 22.981929,  \
      34.80388889, 34.78527778,  \
       1.292117,  4.499668,  4.651190,  \
      -1.685287, -0.658683, -3.809080,  \
       0.928538, 1.125,  \
      6.40167,  \
      1.50375,  \
      1.418560, \
      1.430888, \
      -90., \
      10.298929, \
      10.463888, \
       9.446111, \
      10.733333, \
       4.864167, \
      35.510556, \
       72.57152, \
       74.382969, \
       72.87833, \
       76.58544, \
       2.156667,\
       35.347, \
       35.478, \
       -8.0033, \
       22.956, \
       -16.500, \
        15.0833, \
        15.0514, \
        15.1728, \
        17.296, \
        22.965, \
        32.86667, \
       -52.912222]    

pi     = 3.141592653589793238462643383279502884197
two_pi = 2.*pi

aux16 = 2.**(-16)
p1=42164.
p2=0.00675701
p3=0.993243
rp=6356.5838

deg2rad=pi/180.
rad2deg=180./pi

area = "MSG-Disk"

# The follwoing coefficients are required to relate the latitude/longitude with
# the column/line within each LSA SAF pre-defined region. Those coefficients 
# are available in the product files metadata 
#-------------------------------------------------

# Sub-Sattelite Longitude (from PROJECTION_NAME attribute at the products metadata)
if "IODC-Disk" in area: sub_lon1=45.5 			
if "MSG-Disk" in area:	sub_lon1=0	
if "Euro" in area:		sub_lon1=0	
if "NAfr" in area:		sub_lon1=0	
if "SAfr" in area:		sub_lon1=0	
if "SAme" in area:		sub_lon1=0	
	
# Column and line offset (from COFF and LOFF attributes at the products metadata)
if "IODC-Disk" in area:
    COFF=1857
    LOFF=1857
if "MSG-Disk" in area:
    COFF=1857
    LOFF=1857
if "Euro" in area:	
    COFF=308
    LOFF=1808
if "NAfr" in area:	
    COFF=618
    LOFF=1158
if "SAfr" in area:	
    COFF=-282
    LOFF=8
if "SAme" in area:	
    COFF=1818
    LOFF=398

	# Common coefficients (from CFAC and LFAC attributes at the products metadata)
CFAC=13642337
LFAC=13642337

for No in range(89,110):

    lat1 = LAT2[No]
    lon1 = LON2[No]

    lat = lat1*deg2rad			# Radians
    lon = lon1*deg2rad			# Radians
    sub_lon = sub_lon1*deg2rad	# Radians

    c_lat = math.atan(p3 * math.tan(lat))
    rl = rp / math.sqrt(1. - p2 * (math.cos(c_lat))**2)
    r1 = p1 - rl * math.cos(c_lat) * math.cos(lon - sub_lon)
    r2 = -rl * math.cos(c_lat) * math.sin(lon - sub_lon)
    r3 = rl * math.sin(c_lat)
    rn = math.sqrt(r1**2 + r2**2 + r3**2)

    x = math.atan(-r2/r1)
    y = math.asin(-r3/rn)

    x = x*rad2deg
    y = y*rad2deg

    col = COFF + round(x*aux16*CFAC)
    lin = LOFF + round(y*aux16*LFAC)


#     parser = argparse.ArgumentParser(description='\tCalcule the MSG pixel (column and line) within the LSA SAF pre-defined regions given the Latitude and Longitude')

# 	# Defining Defaults
#     parser.add_argument('-lat', metavar='lat', dest='lat', type=float, default=0 , help='[80,80]')
#     parser.add_argument('-lon', metavar='lon', dest='lon', type=float, default=0,  help='[-180,180]')
#     parser.add_argument('-a', metavar='area', dest='area', type=str, default='MSG-Disk', help='One of the LSA SAF pre-defined regions (Euro, NAfr, SAfr, SAme, MSG-Disk, IODC-Disk)')

#    args = parser.parse_args()

    # lat = args.lat
    # lon = args.lon
    # area = args.area

#    col,lin = lat_lon2col_lin(lat, lon, sub_lon, COFF,LOFF,LFAC,CFAC)

    # print('Region:   %s')%(station(No))		
    # print('Lat=   %s')%(lat)
    # print('Lon=   %s')%(lon)
    # print('        |')
    # print('        V')
    # print('Col=   %s')%(col)
    # print('Lin=   %s')%(lin)

    pix = 3./math.cos(abs(lon-sub_lon))/math.cos(lat)

    print(col, lin, LON2[No], LAT2[No], pix, station[No],sub_lon)

