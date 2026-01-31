import matplotlib.pyplot as plt
import numpy as np

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


deg2rad = 3.1415926/180
NS_PER_HR = 1.e9 * 3600.  # nanoseconds per hour
elev = 0
altitude = 0
pressure = 101325 / 100  # pressure must be in millibars for calculation
atmos_refract = 0.5667
line1 = 3712  # 1rst line (start reading from south)
lineN = 0  # last line (northwards)

indir = r"/Users/bianzj/Downloads/data/msg/"
indir_msg0 = '/Volumes/My Book/MDSSFTD_Disk/2024_MSG_SEVIRI/'
outdir = indir + "/sitedata/"

indirs = search_dir(indir_msg0,np.asarray(["Disk"]))
num_dir = len(indirs)

infile = indir + "sites.txt"
site_info = read_txt_str(infile, r",")
site_name = np.asarray([_[0] for _ in site_info])
lat_ = np.asarray([_[1] for _ in site_info], dtype=float)
lon_ = np.asarray([_[2] for _ in site_info], dtype=float)
num_site = len(site_name)

infile = indir + "/sample/others/MSG_VZA"
vza, ns, nl, nb, geog, proj = read_image_gdal(infile)
infile = indir + "/sample/others/MSG_VAA"
vaa, ns, nl, nb, geog, proj = read_image_gdal(infile)
vza = np.fliplr(vza)
vza = np.flipud(vza)
vaa = np.fliplr(vaa)
vaa = np.flipud(vaa)


lin_ = np.int_(np.zeros(num_site))
col_ = np.int_(np.zeros(num_site))


isloc = 0

for kdir in range(num_dir):

    line_ = [[] for _ in range(num_site)]
    kstart = 1

    indir_temp = indir_msg0 + indirs[kdir]


    files = search_file(indir_temp,"nat")
    infiles = np.asarray([indir_temp+file for file in files])

    reader = "seviri_l1b_native"

    doy0 = 0

    file = files[0]
    date_str = file[-32:-24]
    year_str = file[-32:-28]
    month_str = file[-28:-26]
    day_str = file[-26:-24]
    hh_str = file[-24:-22]
    mn_str = file[-22:-20]
    year_int = np.int_(year_str)
    month_int = np.int_(month_str)
    day_int = np.int_(day_str)
    hh_int = np.int_(hh_str)
    doy_int = date2DOY(year_int, month_int, day_int)
    doy0 = doy_int

    if month_int< 10:continue

    outfile = outdir + site_name[0] +"_euro_2024_%03d"%doy0+".txt"
    if os.path.exists(outfile):
        continue

    for kfile in range(len(files)):
    # for k in range(5):
        file = files[kfile]
        infile = indir_temp + r"//"+ file
        print(infile)

        date_str = file[-32:-24]
        year_str = file[-32:-28]
        month_str = file[-28:-26]
        day_str = file[-26:-24]
        hh_str = file[-24:-22]
        mn_str = file[-22:-20]
        year_int = np.int_(year_str)
        month_int = np.int_(month_str)
        day_int = np.int_(day_str)
        hh_int = np.int_(hh_str)



        if(hh_int <= 3): continue
        if(hh_int >= 20): continue
        #scn = Scene(filenames=filenames, reader="seviri_l1b_native", reader_kwargs={'fill_disk': True})
        scn = Scene(filenames={reader: [infile]},reader_kwargs={'fill_disk': True})
        # extract data set names
        dataset_names = scn.all_dataset_names()
        # print available datasets


        dataset = "VIS006"
        # we need to load the data, different calibration can be chosen
        scn.load([dataset])
        # let us extract the longitude and latitude data



        if isloc == 0:
            lon, lat = scn[dataset].area.get_lonlats()
            for k in range(len(site_name)):
                lon_temp = lon_[k]
                lat_temp = lat_[k]
                distance = np.power((lon - lon_temp), 2) + np.power((lat - lat_temp), 2)
                tempx, tempy = np.where(distance == np.min(distance))
                lin_[k] = tempx[0]
                col_[k] = tempy[0]
            time_bias_ = 12 * (np.int_(lin_) - line1) / (line1 - lineN) + 3  # in minutes
            isloc = 1
            vza_ = vza[lin_, col_] / 100.0
            vaa_ = vaa[lin_, col_] / 100.0

            # outfile = indir + "/sample/others/EURO_lat_bad.tif"
            # write_image_gdal(lat,3712,3712,1,"","",outfile)
            # outfile = indir + "/sample/others/EURO_lon_bad.tif"
            # write_image_gdal(lon, 3712, 3712, 1, "", "", outfile)
            # A = 10


        doy_int = date2DOY(year_int, month_int, day_int)
        doy0 = doy_int
        hh_int_ = np.repeat(hh_int, num_site)
        mn_int_ = np.int_(mn_str) - time_bias_
        mn_int_ = np.int_(mn_int_)
        ind = mn_int_ < 0
        if np.sum(ind) > 0:
            mn_int_[ind] = 0
        ind = mn_int_ > 59
        if np.sum(ind) > 0:
            mn_int_[ind] = 59

        # and finally we also extract the data
        values = scn[dataset].values
        dataset_obj = scn[dataset]
        VIS006_ = values[lin_,col_]




        dataset = "VIS008"
        # we need to load the data, different calibration can be chosen
        scn.load([dataset])
        values = scn[dataset].values
        VIS008_ = values[lin_,col_]

        dataset = "IR_016"
        # we need to load the data, different calibration can be chosen
        scn.load([dataset])
        values = scn[dataset].values
        IR016_ = values[lin_, col_]

        dataset = "IR_108"
        # we need to load the data, different calibration can be chosen
        scn.load([dataset])
        values = scn[dataset].values
        IR108_ = values[lin_,col_]

        dataset = "IR_120"
        # we need to load the data, different calibration can be chosen
        scn.load([dataset])
        values = scn[dataset].values
        IR120_ = values[lin_,col_]

        # plt.imshow(values)
        # plt.show()

        a = 10
        # date_str = file[-52:-44]
        # year_str = file[-52:-48]
        # month_str = file[-48:-46]
        # day_str = file[-46:-44]
        # hh_str = file[-44:-42]
        # mn_str = file[-42:-40]


        sza_ = np.zeros(num_site)
        saa_ = np.zeros(num_site)
        for ksite in range(num_site):
            time_temp = pd.date_range(date_str + ' ' + np.str_(hh_int_[ksite] )+ ':' + np.str_(mn_int_[ksite]) + ':00',date_str + ' ' + np.str_(hh_int_[ksite] ) + ':' + np.str_(mn_int_[ksite] ) + ':00',freq='0.25h', tz='UTC')
            site_temp = Location(lat_[ksite], lon_[ksite], 'Etc/GMT', altitude, 'None')
            solpos_temp = pvlib.solarposition.get_solarposition(time_temp, site_temp.latitude, site_temp.longitude, site_temp.altitude, method='nrel_numpy')
            sza_temp = solpos_temp['zenith'].to_numpy()
            sza_temp = np.int_(sza_temp * 100) / 100
            saa_temp = solpos_temp['azimuth'].to_numpy()
            saa_temp = np.int_(saa_temp * 100) / 100
            sza_[ksite] = sza_temp[0]
            saa_[ksite] = saa_temp[0]
            lat_temp = lat_[ksite]
            lon_temp = lon_[ksite]
            vza_temp = vza_[ksite]
            vaa_temp = vaa_[ksite]
            VIS006_temp = VIS006_[ksite]
            VIS008_temp = VIS008_[ksite]
            IR016_temp = IR016_[ksite]
            IR108_temp = IR108_[ksite]
            IR120_temp = IR120_[ksite]
            line = np.asarray([lat_temp,lon_temp,year_int,month_int,day_int,hh_int_[ksite],mn_int_[ksite],doy_int,sza_temp[0],saa_temp[0],vza_temp,vaa_temp,VIS006_temp,VIS008_temp,IR016_temp,IR108_temp,IR120_temp])
            if(kstart == 1):
                line_[ksite] = line
            else:
                line_[ksite] = np.vstack([line_[ksite],line])
        kstart = 0

    for ksite in range(len(site_name)):
        line = np.asarray(line_[ksite])
        ind = np.argsort(line[:,5]/24+line[:,6]/60/24+line[:,7])
        line = line[ind,:]
        outfile = outdir + site_name[ksite] +"_euro_2024_%03d"%doy0+".txt"
        np.savetxt(outfile,line,fmt='%10.4f')










