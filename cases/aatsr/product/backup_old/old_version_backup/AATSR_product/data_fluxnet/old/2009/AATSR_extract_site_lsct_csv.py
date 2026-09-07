import calendar
from datetime import timedelta
from utils.old.util import *

'''2024.2.27'''
'''脚本用于根据站点经纬度坐标裁剪lsct结果文件'''
'''由于数据量过大，弃用'''

indir_base = r"F:\AATSR\\"
indir_type = indir_base + r"0_base\type\\"
infile_type = indir_type + r"type_world_1000.tif"

indir_Fluxnet = r"D:\data\Fluxnet2015\\"
infile_site = indir_Fluxnet + r"FLUXSITE.xlsx"
infile_site_imagexy = indir_Fluxnet + r"FLUXSITE_imagexy.csv"

outdir = r"D:\LU\data\Fluxnet2015\AATSR_h5\\"

type, ns_type, nl_type, nb_type, geog_type, proj_type = read_image_gdal(infile_type)

'''读取站点经纬度'''
data = pd.read_excel(infile_site)
site_name = data["SITE_ID"]
site_lon = data["LOCATION_LONG"]
site_lat = data["LOCATION_LAT"]

'''经纬度转化为图上坐标'''
'''把年份也加进来，并筛选'''
indir_filter = r"D:\LU\data\Fluxnet2015\filter\\"
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
for year in range(2009,2010):
    indir_tif_year = indir_base + "%04d//tif" % year
    indir_lst_year = indir_base + "%04d//lst" % year
    indir_lsct_year = indir_base + "%04d//lsct" % year

    indir_lai_year = indir_base + "lai//%04d//" % year
    for month in range(1,3):
        daynum = calendar.monthrange(year,month)[1]
        for d in range(daynum):
            day = d + 1
            indir_tif_day = indir_tif_year + "//%02d//%02d//" %(month,day)
            indir_lst_day = indir_lst_year + "//%02d//%02d//" %(month,day)
            indir_lsct_day = indir_lsct_year + "//%02d//%02d//" %(month,day)
            print(indir_lsct_day)
            if not os.path.exists(indir_lsct_day): continue

            '''LAI'''
            doy = date2DOY(year,month,day)
            doy1 = (doy // 4) * 4 + 1
            doy2 = (doy // 4) * 4 + 5
            infile_lai1 = indir_lai_year + r"MuSyQ.CSC.LAI.A" + '%04d%03d' % (int(year), doy1) + '.tif'
            infile_lai2 = indir_lai_year + r"MuSyQ.CSC.LAI.A" + '%04d%03d' % (int(year), doy2) + '.tif'
            if not os.path.exists(infile_lai2): infile_lai2 = infile_lai1
            [lai1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai1)
            [lai2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai2)
            lai = (1 - (doy - doy1) / 4) * lai1 + (doy - doy1) / 4 * lai2
            lai = np.reshape(lai, [nl_type, ns_type])
            lai[lai >= 30000] = 0
            lai = lai / 1000

            fileNames = search_file_rej(indir_lsct_day,['.tif'],'enp')
            fileNum = len(fileNames)
            for fileName in fileNames:
                print(fileName)
                fn = fileName[:-9]

                '''读取需要的数据'''
                infile_imagex = indir_tif_day + fn + "indx.tif"
                infile_imagey = indir_tif_day + fn + "indy.tif"


                infile_lstN = indir_lst_day + fn + "lst_n.tif"
                infile_lstO = indir_lst_day + fn + "lst_f.tif"

                infile_lsct = indir_lsct_day + fn + "_lsct.tif"

                if not os.path.exists(infile_imagex): continue

                indx, ns, nl, nb, geog, proj = read_image_gdal(infile_imagex)
                indy, ns, nl, nb, geog, proj = read_image_gdal(infile_imagey)
                # clo, ns, nl, nb, geog, proj = read_image_gdal(infile_clo)

                lstN, ns, nl, nb, geog, proj = read_image_gdal(infile_lstN)
                lstO, ns, nl, nb, geog, proj = read_image_gdal(infile_lstO)

                lsct, ns, nl, nb, geog, proj = read_image_gdal(infile_lsct)

                '''时间'''
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
                lai_ = lai[indx,indy]


                for index,[site_id,lon,lat,imagex,imagey,start_year,end_year] in data_loc.iterrows():
                    if year < start_year or year > end_year: continue
                    mask_x = indx == imagex
                    mask_y = indy == imagey
                    mask = np.bitwise_and(mask_x,mask_y)
                    ind = np.argwhere(mask)
                    if len(ind) == 0: continue
                    print(site_id, start_year, end_year)
                    print(len(ind))
                    ix = ind[0][0]
                    iy = ind[0][1]
                    ix_min = ix - 15
                    ix_max = ix + 16
                    iy_min = iy - 15
                    iy_max = iy + 16

                    outdir_site_lsct = outdir + site_id + "//lsct//"
                    outdir_site_tif = outdir + site_id + "//tif//"
                    outdir_site_lst = outdir + site_id + "//lst//"
                    mkdir_if_not_exist(outdir_site_lsct)
                    mkdir_if_not_exist(outdir_site_lst)
                    mkdir_if_not_exist(outdir_site_tif)

                    # outfile_vzaN = outdir_site_tif + fn + "vzaN.csv"
                    # outfile_vzaO = outdir_site_tif + fn + "vzaO.csv"
                    # outfile_clo = outdir_site_tif + fn + "clo.csv"
                    outfile_aux = outdir_site_tif + fn + "aux.csv"
                    outfile_lai = outdir_site_tif + fn + "lai.csv"
                    outfile_lstN = outdir_site_lst + fn + "lstN.csv"
                    outfile_lstO = outdir_site_lst + fn + "lstO.csv"
                    outfile_ts = outdir_site_lsct + fn + "ts.csv"
                    outfile_tv = outdir_site_lsct + fn + "tv.csv"

                    # save_vzaN = pd.DataFrame(vzaN[ix_min:ix_max, iy_min:iy_max])
                    # save_vzaO = pd.DataFrame(vzaO[ ix_min:ix_max, iy_min:iy_max])
                    # save_clo = pd.DataFrame(clo[ix_min:ix_max, iy_min:iy_max])
                    save_lstN = pd.DataFrame(lstN[ix_min:ix_max, iy_min:iy_max])
                    save_lstO = pd.DataFrame(lstO[ix_min:ix_max,iy_min:iy_max])
                    save_ts = pd.DataFrame(lsct[0, ix_min:ix_max, iy_min:iy_max])
                    save_tv = pd.DataFrame(lsct[1,ix_min:ix_max,iy_min:iy_max])
                    save_lai = pd.DataFrame(lai_[ix_min:ix_max,iy_min:iy_max])
                    save_aux = pd.DataFrame({"type":[type[imagex,imagey]],"lai":[lai[imagex,imagey]],"sec":[sec_save[ix,iy]]})

                    # save_vzaN.to_csv(outfile_vzaN, index=False, header=0)
                    # save_vzaO.to_csv(outfile_vzaO, index=False, header=0)
                    # save_clo.to_csv(outfile_clo, index=False, header=0)
                    save_lstN.to_csv(outfile_lstN, index=False, header=0)
                    save_lstO.to_csv(outfile_lstO, index=False, header=0)
                    save_ts.to_csv(outfile_ts, index=False, header=0)
                    save_tv.to_csv(outfile_tv, index=False, header=0)
                    save_lai.to_csv(outfile_lai, index=False, header=0)
                    save_aux.to_csv(outfile_aux,index=False)
                    print(lsct[0,ind[0][0],ind[0][1]])


