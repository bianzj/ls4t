import os
import sys
import h5py
import argparse
import numpy as np
import matplotlib.pyplot as plt

lin_LaCrau = 475
col_LaCrau = 1982
 
#dir_path = 'D:/DISK'
file_path = 'E:/MSG/HDF5/DISK/LAI/'

head = 'HDF5_LSASAF_MSG_LAI_MSG-Disk_'
YY = '2023'
data = [0]*2

for mm in range(10,11):
    strm = str(mm)
    if len(strm) == 1: strm = '0'+strm 
    for dd in range(6,9):
        strd = str(dd)
        if len(strd) == 1: strd = '0'+strd
        date = YY+strm+strd
        print(file_path)
        if os.path.exists(file_path):
            file_out = 'MSG4-SEVI-MSG15_'+date+'_X=475-Y=1982_LaCrau_LAI.dat'    
            f_out = open(file_path + file_out,'w')
            file_in = file_path + '/' + head + date + '0000'
            print(file_in)
            if os.path.isfile(file_in):
                hf = h5py.File(file_in,'r')
                    #get global attributes of the hdf5 file
                    # for attr in hf.attrs.keys():
                        #print("global attribute %s : %s" % (attr,hf.attrs[attr]))
                        #list the hdf5 datasets. It opens like a python dictionary
                        #print("keys: \n%s" % hf.keys())
                for key in hf.keys():
                    dset = hf[key]
                    if key == 'LAI': 
                        LAI = dset[:][:] 
                        #ind = np.where(LAI > -1.0 )   
                        #LAI[ind] = 0
                        LAI_LaCrau = LAI[col_LaCrau, lin_LaCrau]
                        data[0] = int(date) 
                        data[1] = LAI_LaCrau/1000
                        print(data)   
                        valeurs = "%14i %8i\n" \
                            % (data[0],data[1])
                        f_out.write(valeurs)
                        extent = 0, 3712, 0, 3712
                        im2 = plt.imshow(LAI/100, cmap="hot", alpha=1.0, extent=extent, vmin=0, vmax=50)
                        fig = plt.subplots_adjust(bottom=0.1, right=0.9, top=0.9)
                        cax = plt.axes([0.82, 0.115, 0.03, 0.76])
                        cbar = plt.colorbar(cax=cax)
                        cbar.set_label('LAI (m²/m²)', rotation=270, va='center')
                        cax.text(-14,30, date, fontsize=12, verticalalignment='top', color='w')
                        plt.savefig('C:/Users/roujeanj/Desktop/Python/figures/LAI_DISK_'+date+'.png')
                        plt.show()
                hf.close()
            f_out.close()
