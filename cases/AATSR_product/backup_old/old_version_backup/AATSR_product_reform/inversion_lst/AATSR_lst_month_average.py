from utils.old.util import *
from utils.old.util_constant import *
import warnings

warnings.filterwarnings("ignore")
import calendar

'''
AATSR 结果统计，以全球type为地图，生成每个月的统计图，包含五个图层，分别为lst_n\lst_o\lsct_soil\lsct_vege\count
目前并未使用！
'''

year = 2012
month = 1
daynum = calendar.monthrange(year, month)[1]

indir_tif = r'D:\data\data_download\AATSR\statistic\tif\\'
indir_lst = r'D:\data\data_download\AATSR\statistic\lst\\'
indir_lsct = r'D:\data\data_download\AATSR\statistic\lsct\\'
oudir_statistic = r'D:\data\data_download\AATSR\statistic\statistic\\'
indir_type = r'D:\data\type\\'
type_dir = indir_type + 'type_world_10000.tif'
[classif_, ns_type, nl_type, bands, geog_type, proj_type] = read_image_gdal(type_dir)

# 初值，分别为垂直、倾斜lst，土壤植被lsct，过境次数，及不为0的次数（用来平均）
lst_n_ = np.zeros([nl_type, ns_type])
lst_f_ = np.zeros([nl_type, ns_type])
lsct_s_ = np.zeros([nl_type, ns_type])
lsct_v_ = np.zeros([nl_type, ns_type])
count_ = np.zeros([nl_type, ns_type])
c_lst_n_ = np.zeros([nl_type, ns_type])
c_lst_f_ = np.zeros([nl_type, ns_type])
c_lsct_s_ = np.zeros([nl_type, ns_type])
c_lsct_v_ = np.zeros([nl_type, ns_type])

for d in range(daynum):
    print("year/month/day:" + str(year) + '%02d' % int(month) + '%02d' % int(d + 1))
    time_str = str(year) + "//" + '%02d' % int(month) + "//" + '%02d' % int(d + 1) + "//"
    indir_tif_day = indir_tif + time_str
    indir_lst_day = indir_lst + time_str
    indir_lsct_day = indir_lsct + time_str

    c1 = os.path.exists(indir_tif_day)
    c2 = os.path.exists(indir_lst_day)
    c3 = os.path.exists(indir_lsct_day)
    if not c1 * c2 * c3: continue

    fileNames = search_file_rej(indir_lst_day, ['lst_n'], 'enp')
    fileNum = np.size(fileNames)
    off_set = 9
    for file in fileNames:
        fileName = file[:-9]

        '''读取经纬度和太阳方位角（用来剔除黑夜）'''
        lon_dir = indir_tif_day + fileName + 'lon.tif'
        lat_dir = indir_tif_day + fileName + 'lat.tif'
        sza_dir = indir_tif_day + fileName + 'sza.tif'

        c1 = os.path.exists(lon_dir)
        c2 = os.path.exists(lat_dir)
        c3 = os.path.exists(sza_dir)
        if not c1 * c2 * c3: continue

        [lon, ns, nl, bands, geog, proj] = read_image_gdal(lon_dir)
        [lat, ns, nl, bands, geog, proj] = read_image_gdal(lat_dir)
        [sza, ns, nl, bands, geog, proj] = read_image_gdal(sza_dir)

        '''读取温度和组分温度'''
        lst_n_dir = indir_lst_day + fileName + 'lst_n.tif'
        lst_f_dir = indir_lst_day + fileName + 'lst_f.tif'
        lsct_dir = indir_lsct_day + fileName + '_lsct.tif'

        c1 = os.path.exists(lst_n_dir)
        c2 = os.path.exists(lst_f_dir)
        c3 = os.path.exists(lsct_dir)
        if not c1 * c2 * c3: continue

        [lstN, ns, nl, bands, geog, proj] = read_image_gdal(lst_n_dir)
        [lstF, ns, nl, bands, geog, proj] = read_image_gdal(lst_f_dir)
        [lsct, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(lsct_dir)
        lsct_soil = np.zeros([nl, ns])
        lsct_veg = np.zeros([nl, ns])
        lsct_soil[2:-2, :] = lsct[0]
        lsct_veg[2:-2, :] = lsct[1]

        '''去除黑夜'''
        ind = sza < 0
        lstN[ind] = 0
        lstF[ind] = 0
        lsct_soil[ind] = 0
        lsct_veg[ind] = 0

        '''数据去噪'''
        lstN[lstN < 240] = 0
        lstN[lstN > 350] = 0

        lstF[lstF < 240] = 0
        lstF[lstF > 350] = 0

        lsct_soil = np.nan_to_num(lsct_soil)
        lsct_veg = np.nan_to_num(lsct_veg)
        ind = (lsct_soil > 350) + (lsct_soil < 240) + (lsct_veg > 350) + (lsct_veg < 240)
        lsct_soil[ind] = 0
        lsct_veg[ind] = 0

        '''（类）重投影'''
        dataset = gdal.Open(type_dir)
        indx, indy = loc2map(lat, lon, dataset)
        indx[indx == 1800] = 0
        indy[indy == 3600] = 0
        indx = np.reshape(indx, [nl, ns])
        indy = np.reshape(indy, [nl, ns])

        '''1km->10km像元平均'''
        '''原图像（高分辨率）内多个像元对应目标图像（低分辨率）一个像元的点的平均，由于空洞存在，平均时要滤除0'''
        i1 = lstN != 0
        i2 = lstF != 0
        i3 = lsct_soil != 0
        i4 = lsct_veg != 0
        indx_max = np.max(indx)
        indx_min = np.min(indx)
        indy_max = np.max(indy)
        indy_min = np.min(indy)

        for x in range(np.min(indx), np.max(indx) + 1):
            for y in range(np.min(indy), np.max(indy) + 1):
                ix = indx == x
                iy = indy == y
                f1 = ix * iy * i1
                if len(f1) != 0:
                    lst_n_[x, y] += np.average(lstN[f1])
                    c_lst_n_[x, y] += 1

                f2 = ix * iy * i2
                if len(f2) != 0:
                    lst_f_[x, y] += np.average(lstF[f2])
                    c_lst_f_[x, y] += 1

                f3 = ix * iy * i3
                if len(f3) != 0:
                    lsct_s_[x, y] += np.average(lsct_soil[f3])
                    c_lsct_s_[x, y] += 1

                f4 = ix * iy * i4
                if len(f4) != 0:
                    lsct_v_[x, y] += np.average(lsct_soil[f4])
                    c_lsct_v_[x, y] += 1
                print(x,y)

        count_[indx, indy] += 1

'''平均'''
lst_n_[c_lst_n_ != 0] = lst_n_[c_lst_n_ != 0] / c_lst_n_[c_lst_n_ != 0]
lst_f_[c_lst_f_ != 0] = lst_f_[c_lst_f_ != 0] / c_lst_f_[c_lst_f_ != 0]
lsct_s_[c_lsct_s_ != 0] = lsct_s_[c_lsct_s_ != 0] / c_lsct_s_[c_lsct_s_ != 0]
lsct_v_[c_lsct_v_ != 0] = lsct_v_[c_lsct_v_ != 0] / c_lsct_v_[c_lsct_v_ != 0]

# '''1000米到10000米平均'''
# lst_n_ = cv2.resize(lst_n_.astype('float32'),(ns_type_out,nl_type_out),interpolation=cv2.INTER_LINEAR)
# lst_f_ = cv2.resize(lst_f_.astype('float32'),(ns_type_out,nl_type_out),interpolation=cv2.INTER_LINEAR)
# lsct_s_ = cv2.resize(lsct_s_.astype('float32'),(ns_type_out,nl_type_out),interpolation=cv2.INTER_LINEAR)
# lsct_v_ = cv2.resize(lsct_v_.astype('float32'),(ns_type_out,nl_type_out),interpolation=cv2.INTER_LINEAR)
# count_ = cv2.resize(count_.astype('float32'),(ns_type_out,nl_type_out),interpolation=cv2.INTER_LINEAR)

'''保存数据'''
outfile1 = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month) + '_lst_n.tif'
outfile2 = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month) + '_lst_f.tif'
outfile3 = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month) + '_lsct_s.tif'
outfile4 = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month) + '_lsct_v.tif'
outfile5 = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month) + '_count.tif'
write_image_gdal((lst_n_ * 100).astype(uint16), ns_type, nl_type, 1, geog_type, proj_type, outfile1)
write_image_gdal((lst_f_ * 100).astype(uint16), ns_type, nl_type, 1, geog_type, proj_type, outfile2)
write_image_gdal((lsct_s_ * 100).astype(uint16), ns_type, nl_type, 1, geog_type, proj_type, outfile3)
write_image_gdal((lsct_v_ * 100).astype(uint16), ns_type, nl_type, 1, geog_type, proj_type, outfile4)
write_image_gdal(count_.astype(uint8), ns_type, nl_type, 1, geog_type, proj_type, outfile5)
save = np.zeros([5, nl_type, ns_type])
save[0] = (lst_n_ * 100).astype(uint16)
save[1] = (lst_f_ * 100).astype(uint16)
save[2] = (lsct_s_ * 100).astype(uint16)
save[3] = (lsct_v_ * 100).astype(uint16)
save[4] = count_.astype(uint8)
outfile = oudir_statistic + "AATSR_" + str(year) + '_%02d' % int(month) + '_stats.tif'
write_image_gdal(save, ns_type, nl_type, 5, geog_type, proj_type, outfile)
print("Save successful!")
