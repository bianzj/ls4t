# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 15:09:44 2023

@author: roujeanj
"""

import math
import h5py
import numpy as np
from matplotlib import pyplot as plt
from math import floor
import matplotlib.font_manager as font_manager
import datetime

legend_IGBP = \
    ['Unclassified',\
     'Evergreen Needleleaf Forests ', \
     'Evergreen Broadleaf Forests', \
     'Deciduous Needleleaf Forests', \
     'Deciduous Broadleaf Forests', \
     'Mixed Forests', \
     'Closed Shrublands', \
     'Open Shrublands', \
     'Woody Savannas', \
     'Savannas', \
     'Grasslands', \
     'Permanent Wetlands', \
     'Croplands', \
     'Urban and Built-up Lands', \
     'Cropland/Natural Vegetation Mosaics', \
     'Permanent Snow and Ice', \
     'Barren', \
     'Water Bodies']

file_in = 'E:/MDSSFTD_Disk/Static/Disk/hdf5_lsasaf_usgs-igbp_landcov_msg-disk'
hf = h5py.File(file_in,'r')
for key in hf.keys():
    dset = hf[key]
LDC = dset[:][:]
for i in range(0,3712):
    ind = np.where(LDC[i,:]>50)
    LDC[i,ind]=0

stry = '2023'
strm = '08'

for dd in range(6,7):
    strd = str(dd)
    if len(strd) == 1: strd = '0'+strd  
    day = stry+strm+strd
    file = 'MSG4-SEVI-MSG15_'+day+'_X=2975-Y=1888_Victoria_angles_HRS.dat'
    f = open('E:/MDSSFTD_Disk/GoldenDays_Victoria/'+file, "r")   
    #f = open('E:/MSG/'+file, "r")
    print(file_in)

    lin = file[34:38]
    print(lin)
    lin = int(lin)
    col = file[27:31]
    print(col)
    col = int(col)

    numb_LDC = LDC[int(lin)][int(col)]
    type_LDC = legend_IGBP[numb_LDC-1]
    print(type_LDC)

    # time correction
    line1 = 3712          # 1rst line (start reading from south)
    lineN = 0            # last line (northwards)
    time_bias_csca = 12*(int(lin)-lineN)/(line1-lineN) + 3 # in minutes
    print(time_bias_csca)
    time_bias_csca = 0
    time_bias_rad = 0
    


    rows = 96
    cpt=0

    time_csca = np.empty(rows)
    time_rad  = np.empty(rows)
    hour = np.empty(rows)
    VIS006 = np.empty(rows)
    VIS008 = np.empty(rows)
    IR_016 = np.empty(rows)
    IR_087 = np.empty(rows)
    IR_097 = np.empty(rows)
    IR_108 = np.empty(rows)
    IR_120 = np.empty(rows)
    csca = np.empty(rows)

    for line in f:
        line = line.strip()
        print(line)
        columns = line.split()
        dayall = columns[0]
        hour[cpt] = int(dayall[8:10])    
        minutes   = int(dayall[10:12])
        minutes_csca   = (minutes - time_bias_csca)*(100/60)
        minutes_rad    = (minutes - time_bias_rad)*(100/60)
        #    print(dayall,hour[cpt],minutes)    
        time_csca[cpt] = hour[cpt] + minutes_csca/100
        time_rad[cpt] = hour[cpt] + minutes_rad/100
        VIS006[cpt] = float(columns[1])
        VIS008[cpt] = float(columns[2])
        IR_016[cpt] = float(columns[3])
        IR_087[cpt] = float(columns[4])
        IR_097[cpt] = float(columns[5])
        IR_108[cpt] = float(columns[6])
        IR_120[cpt] = float(columns[7])
        csca[cpt]   = float(columns[12])    
        cpt+=1
        f.close

    max_csca = np.max(csca)
    max_index = np.where(csca == max_csca)
    print(max_csca,max_index,time_csca[max_index])

    X1 = np.empty(2)
    X1[0] = time_csca[max_index]
    X1[1] = time_csca[max_index]
    
    Y1 = np.empty(2)
    Y1[0] = 0
    Y1[1] = 1
 

    date = dayall[0:8]
    area = type_LDC
    fig, ax1 = plt.subplots()
    lns11 = ax1.plot(time_rad[0:cpt-1],  VIS006[0:cpt-1], 'r-', ms = 3, mec = 'r',label='VIS006')
    plt.xlabel("UTC")
    plt.ylabel("reflectance")
    plt.title("SEVIRI L1B longitude=0°")
    plt.xlim([0, 24])
    plt.ylim([0, 1.0])
    plt.xticks(np.arange(min(hour), max(hour)+1, step=1.0))
    lns12 = ax1.plot(time_rad[0:cpt-1],  VIS008[0:cpt-1], 'g-', ms = 3, mec = 'g',label='VIS008')
    lns13 = ax1.plot(time_rad[0:cpt-1],  IR_016[0:cpt-1], 'b-', ms = 3, mec = 'b',label='IR_016')
    lns14 = ax1.plot(time_csca[0:cpt-1],   csca[0:cpt-1], 'g--', ms = 3, mec = 'b',label='csca')
    lns15 = ax1.plot(X1+0., Y1,'g--', ms = 3, mec = 'b')

    textstr = date,area,col,lin

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    
    ax1.text(0.02, 0.95, textstr, transform=ax1.transAxes, fontsize=8,
         verticalalignment='top', bbox=props)

    ax1.grid()

    ax2 = ax1.twinx()
    lns21 = ax2.plot(time_rad[0:cpt-1], IR_087[0:cpt-1], 'c-', ms = 3, mec = 'c',label='IR_087')
    lns22 = ax2.plot(time_rad[0:cpt-1], IR_097[0:cpt-1], 'm-', ms = 3, mec = 'm',label='IR_097')
    lns23 = ax2.plot(time_rad[0:cpt-1], IR_108[0:cpt-1], 'y-', ms = 3, mec = 'y',label='IR_108')
    lns24 = ax2.plot(time_rad[0:cpt-1], IR_120[0:cpt-1], 'k-', ms = 3, mec = 'k',label='IR_120')
    ax2.set_ylabel("Temperature (K)", color='k')
    plt.ylim([270, 330])

    lns = lns11+lns12+lns13+lns14+lns15+lns21+lns22+lns23+lns24
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc=1)
    plt.savefig('C:/Users/roujeanj/Desktop/Python/Victoria/Figure '+stry+'-'+strm+'-'+strd+'.png')

    plt.show()
