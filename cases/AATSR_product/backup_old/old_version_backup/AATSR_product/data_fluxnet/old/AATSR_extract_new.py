import calendar
from utils.old.util import *

'''2024.6.17'''
'''根据h5文件提取站点h5'''
indir_lsct = r"H:\AATSR\\"
indir_base = r"H:\AATSR\\"
indir_type = r"D:\data\0_base\type\\"
infile_type = indir_type + r"type_world_1000.tif"
indir_emis = r"D:\data\0_base\emis\\"
infile_emis_s = indir_emis + r"AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif"
infile_veg_emis = indir_emis + 'IGBP_Emi.txt'

infile_vzaN = indir_type + r"vza_n.tif"
infile_vzaO = indir_type + r"vza_f.tif"
infile_vaaN = indir_type + r"vaa_n.tif"
infile_vaaO = indir_type + r"vaa_f.tif"

'''Fluxnet'''
indir_Fluxnet = r"D:\data\AATSR_product\Fluxnet2015\\"
infile_site = indir_Fluxnet + r"FLUXSITE.xlsx"
infile_site_imagexy = indir_Fluxnet + r"FLUXSITE_imagexy.csv"
outdir = r"D:\data\AATSR_product\Fluxnet_AATSR\0_raw_h5_2002-2012\\"
mkdir_if_not_exist(outdir)

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

'''经纬度转化为图上坐标'''
'''把年份也加进来，并筛选'''
indir_filter = r"D:\data\AATSR_product\Fluxnet2015\filter\\"
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
for year in range(2003,2004):
    indir_hdf_year = indir_base + "%04d//hdf" % year
    indir_lsct_year = indir_lsct + "%04d//lsct" % year
    for month in range(12,13):
        daynum = calendar.monthrange(year,month)[1]
        for day in range(1,daynum+1):
            indir_hdf_day = indir_hdf_year + "//%02d//%02d//" %(month,day)
            indir_lsct_day = indir_lsct_year + "//%02d//%02d//" %(month,day)
            print("--------------%04d-%02d-%02d----------------" %(year,month,day))
            if not os.path.exists(indir_hdf_day): continue
            fileNames = search_file_rej(indir_hdf_day, ['.h5'], 'enp')
            fileNum = len(fileNames)
            for i, fileName in enumerate(fileNames):
                print(i,fileName)
                time_str = fileName[15:21]
                infile_h5 = indir_hdf_day + fileName
                items = name_list = ["lon",'lat',"indx","indy","time","LAI",'sza','saa','clo_N','clo_O',"lstN","lstO"]
                lon_arr,lat_arr,indx,indy,time,lai,sza,saa,cloN,cloO,lstN,lstO = read_h5py_items(infile_h5,items)
                fn = fileName[:-3]
                infile_lsct = indir_lsct_day + fn + "__lsct.tif"
                if not os.path.exists(infile_lsct): continue
                lsct, ns, nl, nb, geog, proj = read_image_gdal(infile_lsct)

                for index,[site_id,lon,lat,imagex,imagey,start_year,end_year] in data_loc.iterrows():
                    if year < start_year or year > end_year: continue
                    outdir_site = outdir + site_id + "//"
                    mkdir_if_not_exist(outdir_site)
                    outfile = outdir_site + fn + ".h5"

                    # if os.path.exists(outfile):
                    #     if os.path.getsize(outfile) > 8000:
                    #         continue

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
                    if iy_max>512: iy_max = 512


                    save_lstN = np.array((lstN[ix_min:ix_max, iy_min:iy_max]))
                    save_lstO = np.array(lstO[ix_min:ix_max,iy_min:iy_max])
                    save_ts = np.array(lsct[0, ix_min:ix_max, iy_min:iy_max])
                    save_tv = np.array(lsct[1,ix_min:ix_max,iy_min:iy_max])
                    save_lai = np.array(lai[ix_min:ix_max,iy_min:iy_max])
                    save_indx = np.array(indx[ix_min:ix_max,iy_min:iy_max])
                    save_indy = np.array(indy[ix_min:ix_max,iy_min:iy_max])
                    save_lon = np.array(lon_arr[ix_min:ix_max,iy_min:iy_max])
                    save_lat = np.array(lat_arr[ix_min:ix_max,iy_min:iy_max])
                    save_type = np.array(type[save_indx,save_indy])
                    save_emis_s = np.array(emis_s[save_indx,save_indy])
                    save_emis_v = np.array(emis_v[save_indx, save_indy])
                    sec_save = np.array(time[ix_min:ix_max, iy_min:iy_max])
                    save_vzaN = np.expand_dims(vza_n[iy_min:iy_max],0).repeat(ix_max-ix_min,axis = 0)
                    save_vzaO = np.expand_dims(vza_o[iy_min:iy_max],0).repeat(ix_max-ix_min,axis = 0)
                    save_vaaN = np.expand_dims(vaa_n[iy_min:iy_max],0).repeat(ix_max-ix_min,axis = 0)
                    save_vaaO = np.expand_dims(vaa_o[iy_min:iy_max],0).repeat(ix_max-ix_min,axis = 0)

                    save_clo = np.array(cloN[ix_min:ix_max, iy_min:iy_max]) + np.array(
                        cloO[ix_min:ix_max, iy_min:iy_max])
                    save_sza = np.array(sza[ix_min:ix_max, iy_min:iy_max])
                    save_saa = np.array(saa[ix_min:ix_max, iy_min:iy_max])

                    name_list = ["lon",'lat',"indx","indy","ref_indx","ref_indy","sec","ref_time","type","emis_s","emis_v","lai",'vzaN','vzaO','vaaN','vaaO','sza','saa','clo',"lstN","lstO","Ts","Tv"]
                    data = [save_lon,save_lat,save_indx,save_indy,imagex,imagey,sec_save,int(time_str),save_type,save_emis_s,save_emis_v,save_lai,save_vzaN,save_vzaO,save_vaaN,save_vaaO,save_sza,save_saa,save_clo,save_lstN,save_lstO,save_ts,save_tv]
                    write_h5py_file(outfile,name_list,data_list=data,dtype_list=['f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f'],compression=None,ifcover=1)
                    print(lsct[0, ind[0][0], ind[0][1]])
