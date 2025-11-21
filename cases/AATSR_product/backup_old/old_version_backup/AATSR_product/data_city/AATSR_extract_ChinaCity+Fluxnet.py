import calendar
from datetime import timedelta
from utils.old.util import *


'''2024.10.16'''
'''Extract city + FLuxnet'''

indir_base = r"/home/hero/data/base/"
indir_type = indir_base + r"0_base/type/"
infile_type = indir_type + r"type_world_1000.tif"
indir_emis = indir_base +  r"0_base/emis//"
infile_emis_s = indir_emis + r"AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif"
infile_veg_emis = indir_emis + 'IGBP_Emi.txt'
infile_vzaN = indir_type + r"vza_n.tif"
infile_vzaO = indir_type + r"vza_f.tif"
infile_vaaN = indir_type + r"vaa_n.tif"
infile_vaaO = indir_type + r"vaa_f.tif"


'''city'''
dataset = gdal.Open(infile_type)
outdir = r"/home/hero/data/AATSR/City3/"
infile_city_list = r"/home/hero/data/AATSR/City/records.csv"
data = pd.read_csv(infile_city_list)
city_names = data['city']
site_lon_arr = data['lon']
site_lat_arr = data['lat']
indx_arr,indy_arr = loc2map(site_lat_arr,site_lon_arr,dataset)

'''Fluxnet'''
indir_Fluxnet = r"/home/hero/data/Fluxnet/Fluxnet_data/"
infile_site_fluxnet = indir_Fluxnet + r"FLUXSITE.xlsx"
infile_site_imagexy_fluxnet = indir_Fluxnet + r"FLUXSITE_imagexy.csv"
outdir_fluxnet = r"/home/hero/data/Fluxnet/AATSR_data/raw/"
mkdir_if_not_exist(outdir)

data_loc_f = pd.read_csv(infile_site_imagexy_fluxnet)
site_name_f = data_loc_f["SITE_ID"]
site_lon_f = data_loc_f["LOCATION_LONG"]
site_lat_f = data_loc_f["LOCATION_LAT"]
site_imagex_f = data_loc_f["IMAGEX"]
site_imagey_f = data_loc_f["IMAGEY"]
site_startyear_f = data_loc_f["START_YEAR"]
site_endyear_f = data_loc_f["END_YEAR"]


'''读取发射率'''
[emis_s, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_emis_s)
emis_s = emis_s / 1000
[type,  ns_type, nl_type, nb_type, geog_type, proj_type] = read_image_gdal(infile_type)
type = np.asarray(type, np.int_)
type[type == 255] = 17
emis_v = read_txt_array(infile_veg_emis, 0, 2)
emis_v = emis_v[type, 0] / 1000

'''读取vza'''
vza_n , temp1, temp2, temp3, temp4, temp5 = read_image_gdal(infile_vzaN)
vza_o , temp1, temp2, temp3, temp4, temp5 = read_image_gdal(infile_vzaO)
vza_n = vza_n[0,:]
vza_o = vza_o[0,:]
vaa_n , temp1, temp2, temp3, temp4, temp5 = read_image_gdal(infile_vaaN)
vaa_o , temp1, temp2, temp3, temp4, temp5 = read_image_gdal(infile_vaaO)
vza_n, vza_o, vaa_n, vaa_o = 90 - vza_n / 100, 90 - vza_o / 100, vaa_n / 100, vaa_o / 100

for year in range(2009,2010):
    AATSR_dir = r"/media/hero/265047F75047CBED/T7920_backup/AATSR/%04d//" % year
    # AATSR_dir = r"/media/hero/lsct01/AATSR/%04d//" % year
    log_file = AATSR_dir + "error.log"
    indir_hdf = AATSR_dir + "hdf/"
    for month in range(7,13):
        daynum = calendar.monthrange(year, month)[1]
        for day in range(1, daynum + 1):
            indir_hdf_day = indir_hdf + r"/%02d/%02d//" % (month, day)
            if not os.path.exists(indir_hdf_day): continue
            fileNames = search_file_rej(indir_hdf_day, ['.h5'], 'enp')
            for i, fileName in enumerate(fileNames):
                print(year,month,day)
                # if i ==0: continue
                print(i, fileName)
                infile_h5 = indir_hdf_day + fileName

                items = name_list = ["lon", 'lat', "indx", "indy", "time", "LAI", 'sza', 'saa', 'clo_N', 'clo_O',
                                     "lstN",
                                     "lstO"]
                try:
                    lon_arr, lat_arr, indx, indy, time_, lai, sza, saa, cloN, cloO, lstN, lstO = read_h5py_items(infile_h5,
                                                                                                             items)
                except OSError as e:
                    print(f"Error reading file {fileName}: {e}")

                    # Append the problematic file name to the log file
                    with open(log_file, 'a') as f:
                        f.write(f"{fileName}\n")
                    continue

                if len(np.array(lstN).flatten()) == 0: continue
                lstN, lstO = lstN / 100, lstO / 100
                sza, saa = 90 - sza / 100, saa / 100
                if np.average(lai[lai!=0]) > 100:
                    lai = lai/1000

                '''时间'''
                nl,ns = lstN.shape
                time_delta = timedelta(seconds=6528)
                year_str = fileName[6:10]
                doy_str = fileName[11:14]
                time_str = fileName[15:21]
                month, day = doy2date(int(year_str), int(doy_str))
                time_start = datetime.datetime(int(year_str), month, day, int(time_str[0:2]), int(time_str[2:4]),int(time_str[4:6]))
                sec_num_start = int(time_str[0:2]) * 3600 + int(time_str[2:4]) * 60 + int(time_str[4:6])
                total_columns = nl
                sec_interval = 6528 / (total_columns - 1)
                time_array = np.array(
                    [sec_num_start + i * sec_interval for i in range(total_columns)])
                sec_save = np.transpose(np.array([time_array] * 512))

                for i in range(len(city_names)):
                    site_id = city_names[i]
                    imagex, imagey = indx_arr[i], indy_arr[i]
                    site_lon, site_lat = site_lon_arr[i], site_lat_arr[i]
                    outdir_site = outdir + site_id + "//"
                    mkdir_if_not_exist(outdir_site)
                    outfile = outdir_site + fileName[:-3] + ".h5"
                    # if os.path.exists(outfile):continue

                    '''lon,lat method'''
                    lon_diff = np.abs(lon_arr - site_lon)
                    lat_diff = np.abs(lat_arr - site_lat)

                    # 找到同时满足条件的索引
                    ind = np.argwhere((lon_diff < 0.02) & (lat_diff < 0.02))
                    if len(ind)==0:continue

                    # '''indxy method'''
                    # mask_x = indx == imagex
                    # mask_y = indy == imagey
                    # mask = np.bitwise_and(mask_x, mask_y)
                    # ind = np.argwhere(mask)
                    # if len(ind) == 0: continue


                    print(site_id)
                    ix = ind[0][0]
                    iy = ind[0][1]
                    ix_min = ix - 30
                    ix_max = ix + 31
                    iy_min = iy - 30
                    iy_max = iy + 31

                    if ix_min < 0: ix_min = 0
                    if iy_min < 0: iy_min = 0
                    if ix_max > nl: ix_max = nl
                    if iy_max > 512: iy_max = 512

                    save_lstN = np.array((lstN[ix_min:ix_max, iy_min:iy_max]))
                    save_lstO = np.array(lstO[ix_min:ix_max, iy_min:iy_max])
                    save_lai = np.array(lai[ix_min:ix_max, iy_min:iy_max])

                    save_indx = np.array(indx[ix_min:ix_max, iy_min:iy_max])
                    save_indy = np.array(indy[ix_min:ix_max, iy_min:iy_max])
                    save_lon = np.array(lon_arr[ix_min:ix_max, iy_min:iy_max])
                    save_lat = np.array(lat_arr[ix_min:ix_max, iy_min:iy_max])
                    save_type = np.array(type[save_indx, save_indy])
                    save_emis_s = np.array(emis_s[save_indx, save_indy])
                    save_emis_v = np.array(emis_v[save_indx, save_indy])
                    save_vzaN = np.expand_dims(vza_n[iy_min:iy_max], 0).repeat(ix_max - ix_min, axis=0)
                    save_vzaO = np.expand_dims(vza_o[iy_min:iy_max], 0).repeat(ix_max - ix_min, axis=0)
                    save_vaaN = vaa_n[ix_min:ix_max, iy_min:iy_max]
                    save_vaaO = vaa_o[ix_min:ix_max, iy_min:iy_max]

                    save_clo = np.array(cloN[ix_min:ix_max, iy_min:iy_max]) + np.array(
                        cloO[ix_min:ix_max, iy_min:iy_max])
                    save_sza = np.array(sza[ix_min:ix_max, iy_min:iy_max])
                    save_saa = np.array(saa[ix_min:ix_max, iy_min:iy_max])


                    name_list = ["lon", 'lat', "indx", "indy", "ref_indx", "ref_indy", "sec", "ref_time", "type",
                                 "emis_s", "emis_v", "lai", 'vzaN', 'vzaO', 'vaaN', 'vaaO', 'sza', 'saa', 'clo',
                                 "lstN", "lstO"]
                    data = [save_lon, save_lat, save_indx, save_indy, imagex, imagey, sec_save[ix, iy],
                            int(time_str), save_type, save_emis_s, save_emis_v, save_lai, save_vzaN, save_vzaO,
                            save_vaaN, save_vaaO, save_sza, save_saa, save_clo, save_lstN, save_lstO]
                    write_h5py_file(outfile, name_list, data_list=data,
                                    dtype_list=['f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f',
                                                'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f'], compression=None,
                                    ifcover=1)

                for i in range(len(site_name_f)):
                    site_id, site_lon,site_lat,imagex,imagey,start_year,end_year = site_name_f[i],site_lon_f[i],site_lat_f[i],site_imagex_f[i],site_imagey_f[i],site_startyear_f[i],site_endyear_f[i]
                    if year < start_year or year > end_year: continue
                    outdir_site = outdir_fluxnet + site_id + "//"
                    mkdir_if_not_exist(outdir_site)
                    outfile = outdir_site + fileName[:-3] + ".h5"

                    '''lon,lat method'''
                    lon_diff = np.abs(lon_arr - site_lon)
                    lat_diff = np.abs(lat_arr - site_lat)

                    # 找到同时满足条件的索引
                    ind = np.argwhere((lon_diff < 0.02) & (lat_diff < 0.02))
                    if len(ind)==0:continue

                    print(site_id)
                    ix = ind[0][0]
                    iy = ind[0][1]
                    ix_min = ix - 30
                    ix_max = ix + 31
                    iy_min = iy - 30
                    iy_max = iy + 31

                    if ix_min < 0: ix_min = 0
                    if iy_min < 0: iy_min = 0
                    if ix_max > nl: ix_max = nl
                    if iy_max > 512: iy_max = 512

                    save_lstN = np.array((lstN[ix_min:ix_max, iy_min:iy_max]))
                    save_lstO = np.array(lstO[ix_min:ix_max, iy_min:iy_max])
                    save_lai = np.array(lai[ix_min:ix_max, iy_min:iy_max])

                    save_indx = np.array(indx[ix_min:ix_max, iy_min:iy_max])
                    save_indy = np.array(indy[ix_min:ix_max, iy_min:iy_max])
                    save_lon = np.array(lon_arr[ix_min:ix_max, iy_min:iy_max])
                    save_lat = np.array(lat_arr[ix_min:ix_max, iy_min:iy_max])
                    save_type = np.array(type[save_indx, save_indy])
                    save_emis_s = np.array(emis_s[save_indx, save_indy])
                    save_emis_v = np.array(emis_v[save_indx, save_indy])
                    save_vzaN = np.expand_dims(vza_n[iy_min:iy_max], 0).repeat(ix_max - ix_min, axis=0)
                    save_vzaO = np.expand_dims(vza_o[iy_min:iy_max], 0).repeat(ix_max - ix_min, axis=0)
                    save_vaaN = vaa_n[ix_min:ix_max, iy_min:iy_max]
                    save_vaaO = vaa_o[ix_min:ix_max, iy_min:iy_max]

                    save_clo = np.array(cloN[ix_min:ix_max, iy_min:iy_max]) + np.array(
                        cloO[ix_min:ix_max, iy_min:iy_max])
                    save_sza = np.array(sza[ix_min:ix_max, iy_min:iy_max])
                    save_saa = np.array(saa[ix_min:ix_max, iy_min:iy_max])

                    name_list = ["lon", 'lat', "indx", "indy", "ref_indx", "ref_indy", "sec", "ref_time", "type",
                                 "emis_s", "emis_v", "lai", 'vzaN', 'vzaO', 'vaaN', 'vaaO', 'sza', 'saa', 'clo',
                                 "lstN", "lstO"]
                    data = [save_lon, save_lat, save_indx, save_indy, imagex, imagey, sec_save[ix, iy],
                            int(time_str), save_type, save_emis_s, save_emis_v, save_lai, save_vzaN, save_vzaO,
                            save_vaaN, save_vaaO, save_sza, save_saa, save_clo, save_lstN, save_lstO]
                    write_h5py_file(outfile, name_list, data_list=data,
                                    dtype_list=['f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f',
                                                'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f'], compression=None,
                                    ifcover=1)