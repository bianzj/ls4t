from utils.old.util import *
import calendar

'''2025.2.27'''
'''从h5文件中提取chinaflux站点的观测数据'''

indir_lsct = r"/media/hero/lsct04/"
indir_base = r"/media/hero/lsct04/"
indir_type = r"/media/hero/lsct04/0_base/type/"
infile_type = indir_type + r"type_world_1000.tif"
indir_emis = r"/media/hero/lsct04/0_base/emis//"
infile_emis_s = indir_emis + r"AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif"
infile_veg_emis = indir_emis + 'IGBP_Emi.txt'

infile_vzaN = indir_type + r"vza_n.tif"
infile_vzaO = indir_type + r"vza_f.tif"
infile_vaaN = indir_type + r"vaa_n.tif"
infile_vaaO = indir_type + r"vaa_f.tif"

'''ChinaFlux'''
indir_chinaflux = r'/home/hero/data/AATSR/Sites/ChinaNet/'
infile_site = indir_chinaflux + "ChinaFlux.xlsx"
outdir = r'/home/hero/data/AATSR/Validation/AATSR_extract/'

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
vaa_n = vaa_n[0,:]
vaa_o = vaa_o[0,:]

'''读取站点经纬度'''
data = pd.read_excel(infile_site)
site_name = data["SITE_ID"]
site_lon = data["LOCATION_LONG"]
site_lat = data["LOCATION_LAT"]
imagex,imagey = loc2map(site_lat,site_lon,gdal.Open(infile_type))
# print(imagex,imagey)
start_year, end_year = np.full_like(imagex,2000),np.full_like(imagex,2013)
data_loc = pd.DataFrame({
    'site_name': site_name,
    'site_lon': site_lon,
    'site_lat': site_lat,
    'imagex': imagex,
    'imagey': imagey,
    'start_year': start_year,
    'end_year': end_year
})

'''遍历lsct年份'''
year = 2009
for year in range(year,year + 1):
    indir_clo_year = indir_base + "aatsr_clo//%04d" % year
    indir_loc_year = indir_base + "aatsr_loc//%04d" % year
    indir_lst_year = indir_base + "aatsr_lst//%04d" % year
    indir_tim_year = indir_base + "aatsr_tim//%04d" % year

    indir_v0_year = indir_base + "aatsr_lsct_v0//%04d" % year
    indir_v1_year = indir_base + "aatsr_lsct_v1//%04d" % year
    indir_v2_year = indir_base + "aatsr_lsct_v2//%04d" % year

    for month in range(1,13):
        daynum = calendar.monthrange(year,month)[1]
        for day in range(1,daynum+1):
            indir_clo_year_day = indir_clo_year+ "//%02d//%02d//" %(month,day)
            indir_loc_year_day = indir_loc_year+ "//%02d//%02d//" %(month,day)
            indir_lst_year_day = indir_lst_year+ "//%02d//%02d//" %(month,day)
            indir_tim_year_day = indir_tim_year+ "//%02d//%02d//" %(month,day)

            indir_v0_year_day = indir_v0_year+ "//%02d//%02d//" %(month,day)
            indir_v1_year_day = indir_v1_year+ "//%02d//%02d//" %(month,day)
            indir_v2_year_day = indir_v2_year+ "//%02d//%02d//" %(month,day)

            print("--------------%04d-%02d-%02d----------------" %(year,month,day))
            if not os.path.exists(indir_v2_year_day): continue
            fileNames = search_file_rej(indir_v2_year_day, ['.h5'], 'aux')
            fileNum = len(fileNames)
            for i, fileName in enumerate(fileNames):
                print(i,fileName)
                time_str = fileName[15:21]
                fn = fileName[:-7]
                infile_clo = indir_clo_year_day + fn + 'clo.h5'
                infile_loc = indir_loc_year_day + fn + 'loc.h5'
                infile_lst = indir_lst_year_day + fn + 'lst.h5'
                infile_tim = indir_tim_year_day + fn + 'tim.h5'
                infile_v0 = indir_v0_year_day + fn + 'lsct.h5'
                infile_v1 = indir_v1_year_day + fn + 'lsct.h5'
                infile_v2 = indir_v2_year_day + fn + 'lsct.h5'

                if not os.path.exists(infile_clo) * os.path.exists(infile_loc) * os.path.exists(infile_lst) * os.path.exists(infile_tim) * os.path.exists(infile_v1) * os.path.exists(infile_v2):
                    continue

                clo_array = read_h5py_items(infile_clo,['clo'])
                lon_arr,lat_arr,indx,indy = read_h5py_items(infile_loc,['lon','lat','indx','indy'])
                lon_arr = np.array(lon_arr)
                lat_arr = np.array(lat_arr)
                if len(lon_arr) ==0:
                    lon_arr,lat_arr = np.zeros_like(clo_array),np.zeros_like(clo_array)

                lstN, lstO = read_h5py_items(infile_lst,['lstN','lstO'])
                time = read_h5py_items(infile_tim,['time'])

                if os.path.exists(infile_v0):
                    ts0,tv0 = read_h5py_items(infile_v0,['Ts','Tv'])
                else:
                    ts0,tv0 = np.zeros_like(lstN),np.zeros_like(lstN)
                if len(tv0)==0:
                    tv0 = np.zeros_like(clo_array)
                ts1,tv1 = read_h5py_items(infile_v1,['Ts_p','Tv_p'])
                ts2,tv2 = read_h5py_items(infile_v2,['Ts','Tv'])

                clo_array = np.reshape(np.array(clo_array),(-1,512))
                time = np.reshape(np.array(time),(-1))
                ts1 = np.reshape(np.array(ts1),(-1,512))
                tv1 = np.reshape(np.array(tv1),(-1,512))
                ts2 = np.reshape(np.array(ts2),(-1,512))
                tv2 = np.reshape(np.array(tv2),(-1,512))

                for index,[site_id,lon,lat,imagex,imagey,start_year,end_year] in data_loc.iterrows():
                    if year < start_year or year > end_year: continue
                    outdir_site = outdir + site_id + "//"
                    mkdir_if_not_exist(outdir_site)
                    outfile = outdir_site + fn + ".h5"

                    # if os.path.exists(outfile):
                    #     continue

                    mask_x = indx == imagex
                    mask_y = indy == imagey
                    mask = np.bitwise_and(mask_x,mask_y)
                    ind = np.argwhere(mask)
                    if len(ind) == 0: continue

                    ix = ind[0][0]
                    iy = ind[0][1]
                    print(site_id, start_year, end_year)
                    ix = ind[0][0]
                    iy = ind[0][1]
                    ix_min = ix - 15
                    ix_max = ix + 16
                    iy_min = iy - 15
                    iy_max = iy + 16

                    if ix_min<0: ix_min=0
                    if iy_min<0: iy_min=0
                    if ix_max>43520: ix_max = 43520
                    if ix_min>ix_max: continue
                    if iy_min>iy_max: continue
                    if iy_max>512: iy_max = 512


                    save_lstN = np.array((lstN[ix_min:ix_max, iy_min:iy_max]))
                    save_lstO = np.array(lstO[ix_min:ix_max,iy_min:iy_max])
                    save_clo = np.array(clo_array[ix_min:ix_max, iy_min:iy_max])
                    # save_lai = np.array(lai[ix_min:ix_max,iy_min:iy_max])
                    save_indx = np.array(indx[ix_min:ix_max,iy_min:iy_max])
                    save_indy = np.array(indy[ix_min:ix_max,iy_min:iy_max])
                    save_lon = np.array(lon_arr[ix_min:ix_max,iy_min:iy_max])
                    save_lat = np.array(lat_arr[ix_min:ix_max,iy_min:iy_max])
                    save_type = np.array(type[save_indx,save_indy])
                    save_emis_s = np.array(emis_s[save_indx,save_indy])
                    save_emis_v = np.array(emis_v[save_indx, save_indy])
                    sec_save = np.array(time[ix])
                    save_vzaN = np.expand_dims(vza_n[iy_min:iy_max],0).repeat(ix_max-ix_min,axis = 0)
                    save_vzaO = np.expand_dims(vza_o[iy_min:iy_max],0).repeat(ix_max-ix_min,axis = 0)
                    save_vaaN = np.expand_dims(vaa_n[iy_min:iy_max],0).repeat(ix_max-ix_min,axis = 0)
                    save_vaaO = np.expand_dims(vaa_o[iy_min:iy_max],0).repeat(ix_max-ix_min,axis = 0)
                    save_ts0 = np.array(ts0[ix_min:ix_max, iy_min:iy_max])
                    save_tv0 = np.array(tv0[ix_min:ix_max,iy_min:iy_max])
                    save_ts1 = np.array(ts1[ix_min:ix_max, iy_min:iy_max])
                    save_tv1 = np.array(tv1[ix_min:ix_max, iy_min:iy_max])
                    save_ts2 = np.array(ts2[ix_min:ix_max, iy_min:iy_max])
                    save_tv2 = np.array(tv2[ix_min:ix_max, iy_min:iy_max])


                    name_list = ["lon",'lat',"indx","indy","ref_indx","ref_indy","sec","ref_time","type","emis_s","emis_v",'vzaN','vzaO','vaaN','vaaO','clo',"lstN","lstO","Ts0","Tv0","Ts1","Tv1","Ts2","Tv2"]
                    data = [save_lon,save_lat,save_indx,save_indy,imagex,imagey,sec_save,int(time_str),save_type,save_emis_s,save_emis_v,save_vzaN,save_vzaO,save_vaaN,save_vaaO,save_clo,save_lstN,save_lstO,save_ts0,save_tv0,save_ts1,save_tv1,save_ts2,save_tv2]
                    write_h5py_file(outfile,name_list,data_list=data,dtype_list=['f'] * len(name_list),compression=None,ifcover=1)
