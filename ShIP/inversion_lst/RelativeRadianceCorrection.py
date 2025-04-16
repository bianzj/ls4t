import numpy as np

from util.util import *

'''相对辐射校正'''
'''SLSTR + MSG'''

targetArea = r'D:\data\type\type_Europe_0.03.tif'
[data, ns, nl, nb, geog_type, proj_type] = read_image_gdal(targetArea)

time_match = 5
vza_match = 5
vaa_match = 5

indir_polar_lst = r"E:\data\Sentinel3_SLSTR\S3_2017_Europe\03\lst\\"
indir_polar_tif = r"E:\data\Sentinel3_SLSTR\S3_2017_Europe\03\tif\\"
indir_geo_lst = r""
indir_geo_tif = r""
infile_geo_vza = r"D:\data\base\msg_angle\\Europe_vza_0.03.tif"

[vza_geo, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile_geo_vza)

offset = 14
fileNames_polar = search_file_rej(indir_polar_lst,["lst"],"enp")
for fileName_polar in fileNames_polar:
    print(fileName_polar)
    fn_polar = fileName_polar[:-offset]
    dayNight = fileName_polar[-17:-14]
    year = int(fn_polar[4:8])
    doy = int(fn_polar[9:12])
    month,day = doy2date(year,doy)

    indir_geo_lst_day = indir_geo_lst + "%02d//" % month + "%02d//" %day
    fileNames_polar = search_file_rej(indir_geo_lst_day, ["lst"], "enp")

    infile_time = indir_polar_tif + fn_polar + "_time.tif"
    infile_lst = indir_polar_lst + fn_polar + "_lst_nadir.tif"
    infile_vza = indir_polar_tif + fn_polar + "_vza_nadir.tif"

    if dayNight == "day":
        continue
        infile_vaa = indir_polar_tif + fn_polar + "vaa_nadir.tif"

    '''vza_match'''
    [vza_pol, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile_vza)
    dif_vza = np.full([nl,ns],100.0)
    dif_vza[vza_pol!=0] = np.abs(vza_pol[vza_pol!=0]-vza_geo[vza_pol!=0])
    ind_vza = dif_vza < vza_match
    print(np.sum(ind_vza!=0))
    # outfile = r"E:\data\Sentinel3_SLSTR\S3_2017_Europe\\dif_vza.tif"
    # write_image_gdal(dif_vza, ns, nl, 1, geog_type, proj_type, outfile)

    '''time_match'''
    [time_pol, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile_time)
    # hhmmss
    dif_time = np.full([nl,ns],10)
    dif_time[time_pol != 0] = (time_pol[time_pol!=0] // 100) % 100 % 15
    ind_time = (dif_time < time_match) + (dif_time > 15 - time_match)
    print(np.sum(ind_time))

    ind = ind_time * ind_vza
    print(np.sum(ind_time * ind_vza))

    '''找匹配MSG'''
    hh = np.zeros([nl,ns])
    mm = np.zeros([nl,ns])
    mm_1= np.zeros([nl,ns])
    mm_2= np.zeros([nl,ns])
    hh[time_pol!=0] = time_pol[time_pol!=0] // 10000
    mm_1[time_pol!=0] = (time_pol[time_pol!=0] //100) % 100 // 15
    mm_2[time_pol != 0] = (time_pol[time_pol != 0] // 100) % 100 % 15
    mm_2[mm_2 <= 7.5] = 0
    mm_2[mm_2 > 7.5] = 15
    mm = mm_1 * 15 + mm_2
    hh[mm ==60] = hh[mm==60]+1
    mm[mm==60] = 0

    geo_time = hh*100+mm
    search_times = np.unique(geo_time)
    print(search_time)
    for search_time in search_times:
        if search_time == 0:
            continue
        search_time_str = str(search_time)
        geo_Arr = [ahifile for ahifile in ahiFileNames if doyStr in ahifile]



