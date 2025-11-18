import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from util.util_aatsr import *
import calendar

# os.environ['PROJ_LIB'] = r'/home/hero/anaconda3/envs/python37/share/proj'

'''提取Fluxnet站点'''

'''2025.7.14'''
'''补充提取VNIR波段'''
'''2025.1.10'''
'''根据h5文件提取站点h5'''
'''把v0 v1(单点两组分) v2（5*5两组分无温差限制） 都提出来'''

indir_raw = r"/media/hero/lsct03/"
indir_result = r"/media/hero/lsct04/"
indir_type = r"/media/hero/lsct04/0_base/type/"
infile_type = indir_type + r"type_world_1000.tif"
indir_emis = r"/media/hero/lsct04/0_base/emis//"
infile_emis_s = indir_emis + r"AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif"
infile_veg_emis = indir_emis + 'IGBP_Emi.txt'
outfile_missingfile = indir_raw + 'missing_files.txt'

'''Fluxnet'''
indir_Fluxnet = r"/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/"
infile_site = indir_Fluxnet + r"FLUXSITE.xlsx"
infile_site_imagexy = indir_Fluxnet + r"FLUXSITE_imagexy.csv"
outdir = r"/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/0_raw_h5/"
mkdir_if_not_exist(outdir)

'''读取发射率'''
[emis_s, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_emis_s)
emis_s = emis_s / 1000
[type,  ns_type, nl_type, nb_type, geog_type, proj_type] = read_image_gdal(infile_type)
type = np.asarray(type, np.int_)
type[type == 255] = 17
emis_v = read_txt_array(infile_veg_emis, 0, 2)
emis_v = emis_v[type, 0] / 1000

# '''读取vza'''
# vza_n , temp1, temp2, temp3, temp4, temp5 = read_image_gdal(infile_vzaN)
# vza_o , temp1, temp2, temp3, temp4, temp5 = read_image_gdal(infile_vzaO)
# vza_n = vza_n[0,:]
# vza_o = vza_o[0,:]
# vaa_n , temp1, temp2, temp3, temp4, temp5 = read_image_gdal(infile_vaaN)
# vaa_o , temp1, temp2, temp3, temp4, temp5 = read_image_gdal(infile_vaaO)
# vaa_n = vaa_n[0,:]
# vaa_o = vaa_o[0,:]

'''读取站点经纬度'''
data = pd.read_excel(infile_site)
site_name = data["SITE_ID"]
site_lon = data["LOCATION_LONG"]
site_lat = data["LOCATION_LAT"]

'''经纬度转化为图上坐标'''
'''把年份也加进来，并筛选'''
indir_filter = r"/home/hero/data/Fluxnet/Fluxnet_data/Fluxnet_csv_2002-2012/"
if not os.path.exists(infile_site_imagexy):
    dataset = read_dataset_gdal(infile_type)
    imagex,imagey = loc2map(site_lat, site_lon, dataset)
    exist_site_name = []
    start_year = []
    end_year = []
    SitesNameYears = search_file(indir_filter,['.csv'])
    for siteNameYear in SitesNameYears:
        siteName = siteNameYear.split('_')[0]
        exist_site_name.append(siteName)
        year_str = siteNameYear.split('_')[1]
        start_year.append(int(year_str.split('-')[0]))
        end_year.append(int(year_str.split('-')[1][:-4]))
    df_exist = pd.DataFrame({'SITE_ID':exist_site_name,'START_YEAR':start_year,'END_YEAR':end_year})
    df = pd.DataFrame({'SITE_ID':site_name,"LOCATION_LONG":site_lon,"LOCATION_LAT":site_lat,'IMAGEX':imagex,'IMAGEY':imagey})

    df_save = pd.merge(df,df_exist,how='inner')
    df_save.to_csv(infile_site_imagexy,index=False)

data_loc = pd.read_csv(infile_site_imagexy)
site_imagex = data_loc["IMAGEX"]
site_imagey = data_loc["IMAGEY"]
site_startyear = data_loc["START_YEAR"]
site_endyear = data_loc["END_YEAR"]

'''遍历lsct年份'''
year = 2009
for year in range(year,year + 1):
    indir_obs_year = indir_raw + 'aatsr_obs//%04d' % year
    indir_clo_year = indir_raw + "aatsr_clo//%04d" % year
    indir_loc_year = indir_result + "aatsr_loc//%04d" % year
    indir_lst_year = indir_result + "aatsr_lst//%04d" % year
    indir_tim_year = indir_result + "aatsr_tim//%04d" % year
    indir_ang_year = indir_raw + "aatsr_ang//%04d" % year
    indir_aux_year = indir_result + "aatsr_aux//%04d" % year

    indir_v0_year = indir_result + "aatsr_lsct_v0//%04d" % year
    indir_v1_year = indir_result + "aatsr_lsct_v1//%04d" % year
    indir_v2_year = indir_result + "aatsr_lsct_v2//%04d" % year

    for month in range(1,13):
        daynum = calendar.monthrange(year,month)[1]
        for day in range(1,daynum+1):
            doy = date2DOY(year,month,day)
            if doy < 330: continue
            indir_obs_year_day = indir_obs_year + "//%02d//%02d//" % (month,day)
            indir_clo_year_day = indir_clo_year+ "//%02d//%02d//" %(month,day)
            indir_loc_year_day = indir_loc_year+ "//%02d//%02d//" %(month,day)
            indir_lst_year_day = indir_lst_year+ "//%02d//%02d//" %(month,day)
            indir_tim_year_day = indir_tim_year+ "//%02d//%02d//" %(month,day)
            indir_ang_year_day = indir_ang_year+ "//%02d//%02d//" %(month,day)
            indir_aux_year_day = indir_aux_year+ "//%02d//%02d//" %(month,day)

            indir_v0_year_day = indir_v0_year+ "//%02d//%02d//" %(month,day)
            indir_v1_year_day = indir_v1_year+ "//%02d//%02d//" %(month,day)
            indir_v2_year_day = indir_v2_year+ "//%02d//%02d//" %(month,day)

            print("--------------%04d-%02d-%02d----------------" %(year,month,day))
            if not os.path.exists(indir_obs_year_day): continue
            fileNames = search_file_rej(indir_obs_year_day, ['.h5'], 'aux')
            fileNum = len(fileNames)
            for i, fileName in enumerate(fileNames):
                print(i,fileName)
                time_str = fileName[15:21]
                fn = fileName[:-6]
                infile_obs = indir_obs_year_day + fn + 'obs.h5'
                infile_clo = indir_clo_year_day + fn + 'clo.h5'
                infile_loc = indir_loc_year_day + fn + 'loc.h5'
                infile_lst = indir_lst_year_day + fn + 'lst.h5'
                infile_tim = indir_tim_year_day + fn + 'tim.h5'
                infile_ang = indir_ang_year_day + fn + 'ang.h5'
                infile_aux = indir_aux_year_day + fn + 'aux.h5'
                infile_v0 = indir_v0_year_day + fn + 'lsct.h5'
                infile_v1 = indir_v1_year_day + fn + 'lsct.h5'
                infile_v2 = indir_v2_year_day + fn + 'lsct.h5'
                if not os.path.exists(infile_lst):
                    print('Lack file!')
                    with open(outfile_missingfile,'a') as f:
                        f.write(fn+'\n')
                    continue

                if not os.path.exists(infile_clo) * os.path.exists(infile_loc) * os.path.exists(infile_lst) * os.path.exists(infile_tim) * os.path.exists(infile_v1) * os.path.exists(infile_v2):
                    with open(outfile_missingfile,'a') as f:
                        f.write(fn+'\n')
                    continue

                # 读取数据
                try:
                    redN,redF,nirN,nirF= read_h5py_items(infile_obs,['redN','redF','nirN','nirF'])
                    cloN_array,cloF_array = read_h5py_items(infile_clo,['cloN','cloF'])
                    lon_arr,lat_arr,indx,indy = read_h5py_items(infile_loc,['lon','lat','indx','indy'])
                    saa,sza,vaaN,vaaF,vzaN,vzaF = read_h5py_items(infile_ang,['saa','sza','vaaN','vaaF','vzaN','vzaF'])
                    lai = read_h5py_items(infile_aux,['LAI'])
                except Exception as e:
                    with open(outfile_missingfile,'a') as f:
                        f.write(fn+'\n')
                    continue

                lon_arr = np.array(lon_arr)
                lat_arr = np.array(lat_arr)
                if len(lon_arr) ==0:
                    lon_arr,lat_arr = np.zeros_like(cloN_array),np.zeros_like(cloN_array)

                lstN, lstO = read_h5py_items(infile_lst,['lstN','lstO'])
                time = read_h5py_items(infile_tim,['time'])

                if os.path.exists(infile_v0):
                    ts0,tv0 = read_h5py_items(infile_v0,['Ts','Tv'])
                else:
                    ts0,tv0 = np.zeros_like(lstN),np.zeros_like(lstN)
                if len(tv0)==0:
                    tv0 = np.zeros_like(cloN_array)
                ts1,tv1 = read_h5py_items(infile_v1,['Ts_p','Tv_p'])
                ts2,tv2 = read_h5py_items(infile_v2,['Ts','Tv'])


                cloN_array = np.reshape(np.array(cloN_array),(-1,512))
                cloF_array = np.reshape(np.array(cloF_array),(-1,512))
                time = np.reshape(np.array(time),(-1))
                nirN = np.reshape(np.array(nirN),(-1,512))
                nirF = np.reshape(np.array(nirF),(-1,512))
                redN = np.reshape(np.array(redN),(-1,512))
                redF = np.reshape(np.array(redF),(-1,512))
                ts1 = np.reshape(np.array(ts1),(-1,512))
                tv1 = np.reshape(np.array(tv1),(-1,512))
                ts2 = np.reshape(np.array(ts2),(-1,512))
                tv2 = np.reshape(np.array(tv2),(-1,512))
                saa = np.reshape(np.array(saa),(-1,512))
                sza = np.reshape(np.array(sza),(-1,512))
                vzaN = np.reshape(np.array(vzaN),(-1,512))
                vzaF = np.reshape(np.array(vzaF),(-1,512))
                vaaN = np.reshape(np.array(vaaN),(-1,512))
                vaaF = np.reshape(np.array(vaaF),(-1,512))
                lai = np.reshape(np.array(lai),(-1,512))

                for index,[site_id,lon,lat,imagex,imagey,start_year,end_year] in data_loc.iterrows():
                    if year < start_year or year > end_year: continue
                    outdir_site = outdir + site_id + "//"
                    mkdir_if_not_exist(outdir_site)
                    outfile = outdir_site + fn[:-1] + ".h5"

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
                    save_cloN = np.array(cloN_array[ix_min:ix_max, iy_min:iy_max])
                    save_cloF = np.array(cloF_array[ix_min:ix_max, iy_min:iy_max])
                    save_lai = np.array(lai[ix_min:ix_max,iy_min:iy_max])
                    save_indx = np.array(indx[ix_min:ix_max,iy_min:iy_max])
                    save_indy = np.array(indy[ix_min:ix_max,iy_min:iy_max])
                    save_lon = np.array(lon_arr[ix_min:ix_max,iy_min:iy_max])
                    save_lat = np.array(lat_arr[ix_min:ix_max,iy_min:iy_max])
                    save_type = np.array(type[save_indx,save_indy])
                    save_emis_s = np.array(emis_s[save_indx,save_indy])
                    save_emis_v = np.array(emis_v[save_indx, save_indy])
                    sec_save = np.array(time[ix])
                    save_vzaN = np.array(vzaN[ix_min:ix_max,iy_min:iy_max])
                    save_vzaF = np.array(vzaF[ix_min:ix_max,iy_min:iy_max])
                    save_vaaN = np.array(vaaN[ix_min:ix_max,iy_min:iy_max])
                    save_vaaF = np.array(vaaF[ix_min:ix_max,iy_min:iy_max])
                    save_sza = np.array(sza[ix_min:ix_max,iy_min:iy_max])
                    save_saa = np.array(sza[ix_min:ix_max,iy_min:iy_max])
                    save_redN = np.array(redN[ix_min:ix_max,iy_min:iy_max])
                    save_redF = np.array(redF[ix_min:ix_max, iy_min:iy_max])
                    save_nirN = np.array(nirN[ix_min:ix_max, iy_min:iy_max])
                    save_nirF = np.array(nirF[ix_min:ix_max, iy_min:iy_max])
                    save_ts0 = np.array(ts0[ix_min:ix_max, iy_min:iy_max])
                    save_tv0 = np.array(tv0[ix_min:ix_max,iy_min:iy_max])
                    save_ts1 = np.array(ts1[ix_min:ix_max, iy_min:iy_max])
                    save_tv1 = np.array(tv1[ix_min:ix_max, iy_min:iy_max])
                    save_ts2 = np.array(ts2[ix_min:ix_max, iy_min:iy_max])
                    save_tv2 = np.array(tv2[ix_min:ix_max, iy_min:iy_max])


                    name_list = [
                        "lon",'lat',"indx","indy","ref_indx","ref_indy",
                        "sec","ref_time",
                        "type",
                        "emis_s","emis_v",
                        'vzaN','vzaF','vaaN','vaaF','sza','saa',
                        'cloN','cloF',
                        'redN','redF','nirN','nirF',
                        'lai',
                        "lstN","lstO",
                        "Ts0","Tv0",
                        "Ts1","Tv1",
                        "Ts2","Tv2"
                        ]
                    data = [
                        save_lon,save_lat,save_indx,save_indy,imagex,imagey,
                        sec_save,int(time_str),
                        save_type,
                        save_emis_s,save_emis_v,
                        save_vzaN,save_vzaF,save_vaaN,save_vaaF,save_sza,save_saa,
                        save_cloN,save_cloF,
                        save_redN, save_redF,save_nirN,save_nirF,
                        save_lai,
                        save_lstN,save_lstO,
                        save_ts0,save_tv0,
                        save_ts1,save_tv1,
                        save_ts2,save_tv2
                    ]
                    write_h5py_file(outfile,name_list,data_list=data,dtype_list=['f'] * len(name_list),compression=None,ifcover=1)
