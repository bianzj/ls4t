from utils.old.util import *
from utils.old.util_constant import *
import pysolar.solar as Sun
import warnings
warnings.filterwarnings("ignore")
import calendar
from datetime import timezone

'''
AATSR 生成每月全球合成图
1km直接到2km底图
'''

indir_type = r'D:\LU\data\type\\'
type_dir_1000 = indir_type + 'type_world_1000.tif'
type_dir_10000 = indir_type + 'type_world_10000.tif'
type_dir_2000 = indir_type + 'type_world_2000.tif'
[classif_, ns_type, nl_type, bands, geog_type, proj_type] = read_image_gdal(type_dir_2000)
# [classif_, ns_type_out, nl_type_out, bands, geog_type_out, proj_type_out] = read_image_gdal(type_dir_10000)

for year in range(2009,2010):
    indir_tif = r'H:\AATSR\%04d\tif\\' %year
    indir_lst = r'H:\AATSR\%04d\lst\\'%year
    indir_lsct = r'H:\AATSR\%04d\lsct\\'%year
    oudir_composite = r'H:\AATSR\%04d\lsct_month\\'%year
    for month in range(7,13):
        lst_n_ = np.zeros([nl_type, ns_type])
        lst_f_ = np.zeros([nl_type, ns_type])
        lsct_s_ = np.zeros([nl_type, ns_type])
        lsct_v_ = np.zeros([nl_type, ns_type])
        count_ = np.zeros([nl_type, ns_type])
        c_lst_n_ = np.zeros([nl_type, ns_type])
        c_lst_f_ = np.zeros([nl_type, ns_type])
        c_lsct_s_ = np.zeros([nl_type, ns_type])
        c_lsct_v_ = np.zeros([nl_type, ns_type])
        time_ = np.zeros([nl_type, ns_type])

        # '''跳过跑完的'''
        # if os.path.exists(oudir_composite + '%02d' % int(month)  + "//" + "AATSR_" + str(
        #         year) + '_%02d' % int(month) + '_lst_n.tif'):
        #     continue


        daynum = calendar.monthrange(year, month)[1]

        for d in range(daynum):
            print("year/month/day:" + str(year) + '%02d' % int(month) + '%02d' % int(d + 1))
            # time_str = str(year) + "//" + '%02d' % int(month) + "//" + '%02d' % int(d + 1) + "//"
            time_str =  '%02d' % int(month) + "//" + '%02d' % int(d + 1) + "//"
            indir_tif_day = indir_tif + time_str
            indir_lst_day = indir_lst + time_str
            indir_lsct_day = indir_lsct + time_str
            # indir_tif_day = indir_tif
            # indir_lst_day = indir_lst
            # indir_lsct_day = indir_lsct


            c1 = os.path.exists(indir_tif_day)
            c2 = os.path.exists(indir_lst_day)
            c3 = os.path.exists(indir_lsct_day)
            if not c1 * c2 * c3: continue


            fileNames = search_file_rej(indir_lst_day, ['lst_n'], 'enp')
            fileNum = np.size(fileNames)
            off_set = 9
            for file in fileNames:
                fileName = file[:-9]
                print(fileName)

                '''时间信息'''
                from datetime import datetime, timedelta
                time_delta = timedelta(seconds=6528)
                year_str= fileName[6:10]
                doy_str = fileName[11:14]
                time_str = fileName[15:21]
                month,day = doy2date(int(year_str),int(doy_str))
                time_start = datetime(int(year_str),month,day,int(time_str[0:2]),int(time_str[2:4]),int(time_str[4:6]))
                # sec_num_start = int(time_str[0:2])*3600+int(time_str[2:4])*60+int(time_str[4:6])
                # total_columns = 43520
                # sec_interval = 6528 / (total_columns-1)
                # time_array = np.array(
                #     [sec_num_start + i * sec_interval for i in range(total_columns)])
                # sec_save = np.transpose(np.array([time_array] *512))

                '''确定lst和lsct在'''
                lst_n_dir = indir_lst_day + fileName + 'lst_n.tif'
                lst_f_dir = indir_lst_day + fileName + 'lst_f.tif'
                lsct_dir = indir_lsct_day + fileName + '_lsct.tif'
                c1 = os.path.exists(lst_n_dir)
                c2 = os.path.exists(lst_f_dir)
                c3 = os.path.exists(lsct_dir)
                if not c1 * c2 * c3:
                    print('lack lst or lsct')
                    continue

                '''确定数据都在'''
                lon_dir = indir_tif_day + fileName + 'lon.tif'
                lat_dir = indir_tif_day + fileName + 'lat.tif'
                sza_dir = indir_tif_day + fileName + 'sza.tif'
                indx_dir = indir_tif_day + fileName + 'indx.tif'
                indy_dir = indir_tif_day + fileName + 'indy.tif'
                c1 = os.path.exists(lon_dir)
                c2 = os.path.exists(lat_dir)
                c3 = os.path.exists(sza_dir)
                c4 = os.path.exists(indx_dir)
                c5 = os.path.exists(indy_dir)

                if not c1 * c2:
                    print('lack tif')
                    continue

                if not c4 * c5:
                    type_dir = type_dir_1000
                    dataset = gdal.Open(type_dir)
                    [lon, ns, nl, temp3, temp4, temp5] = read_image_gdal(lon_dir)
                    [lat, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(lat_dir)
                    indx, indy = loc2map(lat, lon, dataset)
                    indx[indx >= 18000] = 0
                    indy[indy >= 36000] = 0
                    write_image_gdal(np.reshape(indx, [nl, ns]).astype(uint16), ns, nl, 1, '', '', indx_dir)
                    write_image_gdal(np.reshape(indy, [nl, ns]).astype(uint16), ns, nl, 1, '', '', indy_dir)

                # 注意这！！！
                if 1:
                    [lon, ns, nl, bands, geog, proj] = read_image_gdal(lon_dir)
                    [lat, ns, nl, bands, geog, proj] = read_image_gdal(lat_dir)
                    time_start = time_start.replace(tzinfo=timezone.utc)

                    time1 = time_start + timedelta(minutes=14)
                    time2 = time_start + timedelta(minutes=42)
                    time3 = time_start + timedelta(minutes=69)
                    time4 = time_start + timedelta(minutes=97)
                    sza1 = np.zeros([nl,ns])
                    sza1[0:int(nl/4),:] = Sun.get_altitude_fast(lat[0:int(nl/4),:], lon[0:int(nl/4),:], time1)
                    sza1[int(nl / 4):2*int(nl / 4), :] = Sun.get_altitude_fast(lat[int(nl / 4):2*int(nl / 4), :], lon[int(nl / 4):2*int(nl / 4), :], time2)
                    sza1[2*int(nl / 4):3*int(nl / 4), :] = Sun.get_altitude_fast(lat[2*int(nl / 4):3*int(nl / 4), :], lon[2*int(nl / 4):3*int(nl / 4), :], time3)
                    sza1[3*int(nl / 4):, :] = Sun.get_altitude_fast(lat[3*int(nl / 4):, :], lon[3*int(nl / 4):, :], time4)
                    write_image_gdal(np.reshape(sza1*100, [nl, ns]).astype(int16), ns, nl, 1, '', '', sza_dir)


                '''读取温度和组分温度'''
                [lstN, ns, nl, bands, geog, proj] = read_image_gdal(lst_n_dir)
                [lstF, ns, nl, bands, geog, proj] = read_image_gdal(lst_f_dir)
                [lsct, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(lsct_dir)
                lsct_soil = np.zeros([nl, ns])
                lsct_veg = np.zeros([nl, ns])
                lsct_soil = lsct[0]
                lsct_veg = lsct[1]
                lstN = lstN/100
                lstF = lstF/100

                '''去除黑夜'''
                # [sza, ns, nl, bands, geog, proj] = read_image_gdal(sza_dir)
                ind = sza1 < 0

                if np.sum(ind)==0:
                    ind  = np.ones_like(sza1)
                    if sza1.shape[0] <=20000: continue
                    ind[10000:-10000] = 0
                lstN[ind] = 0
                lstF[ind] = 0

                if lsct_soil.shape[0] % 512==508:
                    lsct_soil_ = np.zeros([lsct_soil.shape[0]+4,lsct_soil.shape[1]])
                    lsct_soil_[2:-2,:] = lsct_soil
                    lsct_veg_ = np.zeros([lsct_soil.shape[0]+4,lsct_soil.shape[1]])
                    lsct_veg_[2:-2,:] = lsct_veg

                    lsct_soil = lsct_soil_
                    lsct_veg = lsct_veg_
                lsct_soil[ind] = 0
                lsct_veg[ind] = 0

                '''数据去噪'''
                indN = (lstN < 240) + (lstN > 350)
                lstN[indN] = 0

                indF = (lstF < 240) + (lstF > 350)
                lstF[lstF < 240] = 0
                lstF[lstF > 350] = 0

                lsct_soil = np.nan_to_num(lsct_soil)
                lsct_veg = np.nan_to_num(lsct_veg)
                ind = (lsct_soil > 350) + (lsct_soil < 240) + (lsct_veg > 350) + (lsct_veg < 240) + indN + indF
                lsct_soil[ind] = 0
                lsct_veg[ind] = 0

                '''（类）重投影'''
                # dataset = gdal.Open(type_dir_2000)
                # indx, indy = loc2map(lat, lon, dataset)

                [indx, ns, nl, bands, geog, proj] = read_image_gdal(indx_dir)
                [indy, ns, nl, bands, geog, proj] = read_image_gdal(indy_dir)
                indx = np.array((indx/2)).astype(uint16)
                indy = np.array((indy/2)).astype(uint16)
                indx[indx == 18000/2] = 0
                indy[indy == 36000/2] = 0
                indx = np.reshape(indx, [nl, ns])
                indy = np.reshape(indy, [nl, ns])

                f1 = (lstN != 0)
                f2 = (lstF != 0)
                f3 = (lsct_soil != 0)
                f4 = (lsct_veg != 0)

                lst_n_[indx[f1], indy[f1]] += lstN[f1]
                c_lst_n_[indx[f1], indy[f1]] += 1

                lst_f_[indx[f2], indy[f2]] += lstF[f2]
                c_lst_f_[indx[f2], indy[f2]] += 1

                lsct_s_[indx[f3], indy[f3]] += lsct_soil[f3]
                c_lsct_s_[indx[f3], indy[f3]] += 1

                lsct_v_[indx[f4], indy[f4]] += lsct_veg[f4]
                c_lsct_v_[indx[f4], indy[f4]] += 1

                count_[indx[ind], indy[ind]] += 1
                print(1)
                # time_[indx,indy] = sec_save

                # indx_dir = indir_tif_day + fileName + 'indx.tif'
                # indy_dir = indir_tif_day + fileName + 'indy.tif'
                # write_image_gdal((indx).astype(uint16), ns, nl, 1, geog, proj, indx_dir)
                # write_image_gdal((indy).astype(uint16), ns, nl, 1, geog, proj, indy_dir)


        '''平均'''
        lst_n_[c_lst_n_ != 0] = lst_n_[c_lst_n_ != 0] / c_lst_n_[c_lst_n_ != 0]
        lst_f_[c_lst_f_ != 0] = lst_f_[c_lst_f_ != 0] / c_lst_f_[c_lst_f_ != 0]
        lsct_s_[c_lsct_s_ != 0] = lsct_s_[c_lsct_s_ != 0] / c_lsct_s_[c_lsct_s_ != 0]
        lsct_v_[c_lsct_v_ != 0] = lsct_v_[c_lsct_v_ != 0] / c_lsct_v_[c_lsct_v_ != 0]

        # '''1000米到10000米平均'''
        # '''方法有5种 cv2.INTER_NEAREST、cv2.INTER_LINEAR、cv2.INTER_AREA、cv2.INTER_CUBIC、cv2.INTER_LANCZOS4'''
        # method = cv2.INTER_LANCZOS4
        # lst_n_ = cv2.resize(lst_n_.astype('float32'),(ns_type_out,nl_type_out),interpolation=method)
        # lst_f_ = cv2.resize(lst_f_.astype('float32'),(ns_type_out,nl_type_out),interpolation=method)
        # lsct_s_ = cv2.resize(lsct_s_.astype('float32'),(ns_type_out,nl_type_out),interpolation=method)
        # lsct_v_ = cv2.resize(lsct_v_.astype('float32'),(ns_type_out,nl_type_out),interpolation=method)
        # count_ = cv2.resize(count_.astype('float32'),(ns_type_out,nl_type_out),interpolation=method)

        '''保存数据'''
        # ns_type = ns_type_out
        # nl_type = nl_type_out
        # geog_type = geog_type_out
        # proj_type = proj_type_out
        oudir_statistic = oudir_composite + '%02d' % int(month) + "//"
        mkdir_if_not_exist(oudir_statistic)
        outfile1 = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month)+  '_lst_n.tif'
        outfile2 = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month)+  '_lst_f.tif'
        outfile3 = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month)+  '_lsct_s.tif'
        outfile4 = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month)+  '_lsct_v.tif'
        outfile5 = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month)+  '_count.tif'
        # outfile6 = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month)+  '_time.tif'
        write_image_gdal((lst_n_ * 100).astype(uint16), ns_type, nl_type, 1, geog_type, proj_type, outfile1)
        write_image_gdal((lst_f_ * 100).astype(uint16), ns_type, nl_type, 1, geog_type, proj_type, outfile2)
        write_image_gdal((lsct_s_ * 100).astype(uint16), ns_type, nl_type, 1, geog_type, proj_type, outfile3)
        write_image_gdal((lsct_v_ * 100).astype(uint16), ns_type, nl_type, 1, geog_type, proj_type, outfile4)
        write_image_gdal(count_.astype(uint8), ns_type, nl_type, 1, geog_type, proj_type, outfile5)
        # write_image_gdal(time_.astype(uint32), ns_type, nl_type, 1, geog_type, proj_type, outfile6)
        # save = np.zeros([5, nl_type, ns_type])
        # save[0] = (lst_n_ * 100).astype(uint16)
        # save[1] = (lst_f_ * 100).astype(uint16)
        # save[2] = (lsct_s_ * 100).astype(uint16)
        # save[3] = (lsct_v_ * 100).astype(uint16)
        # save[4] = count_.astype(uint8)
        # outfile = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month) + '_stats.tif'
        # write_image_gdal(save, ns_type, nl_type, 5, geog_type, proj_type, outfile)
        print("Save successful!")
