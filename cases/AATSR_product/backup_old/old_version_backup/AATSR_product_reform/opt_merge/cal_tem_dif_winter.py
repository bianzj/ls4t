from utils.old.util import *
from utils.old.util_constant import *
import warnings

warnings.filterwarnings("ignore")
import calendar

'''
AATSR 生成每日全球合成图
1km直接到2km底图
'''

year = 2009
month = 1
daynum = calendar.monthrange(year, month)[1]
# daynum = 1

indir_tif = r'I:\AATSR\2009\tif\\'
indir_lst = r'I:\AATSR\2009\lst\\'
indir_lsct = r'I:\AATSR\2009\lsct\\'
oudir_composite = r'I:\AATSR\2009\lsct_3day\\'
indir_type = r'D:\LU\data\type\\'
type_dir_1000 = indir_type + 'type_world_1000.tif'
type_dir_10000 = indir_type + 'type_world_10000.tif'
type_dir_2000 = indir_type + 'type_world_2000.tif'
[classif_, ns_type, nl_type, bands, geog_type, proj_type] = read_image_gdal(type_dir_2000)
# [classif_, ns_type_out, nl_type_out, bands, geog_type_out, proj_type_out] = read_image_gdal(type_dir_10000)


for d in range(daynum):
    lst_n_ = np.zeros([nl_type, ns_type])
    lst_f_ = np.zeros([nl_type, ns_type])
    lsct_s_ = np.zeros([nl_type, ns_type])
    lsct_v_ = np.zeros([nl_type, ns_type])
    count_ = np.zeros([nl_type, ns_type])
    time_ = np.zeros([nl_type, ns_type])
    c_lst_n_ = np.zeros([nl_type, ns_type])
    c_lst_f_ = np.zeros([nl_type, ns_type])
    c_lsct_s_ = np.zeros([nl_type, ns_type])
    c_lsct_v_ = np.zeros([nl_type, ns_type])

    count_no = 0
    count_on = 0

    print("year/month/day:" + str(year) + '%02d' % int(month) + '%02d' % int(d + 1))
    # time_str = str(year) + "//" + '%02d' % int(month) + "//" + '%02d' % int(d + 1) + "//"
    time_str = '%02d' % int(month) + "//" + '%02d' % int(d + 1) + "//"
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
        print(fileName)

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

        [lstN, ns, nl, bands, geog, proj] = read_image_gdal(lst_n_dir)
        [lstF, ns, nl, bands, geog, proj] = read_image_gdal(lst_f_dir)
        ind_china = (lon>70)*(lon<140)*(lat>0)*(lat<55)

        ind_no = (lat >= 0) *(lstN>lstF) * (lstN>24000)*(lstN<35000)* (lstF>24000)*(lstF<35000) * (sza>0)*ind_china
        ind_on = (lat >= 0) * (lstN<lstF)* (lstN>24000)*(lstN<35000)* (lstF>24000)*(lstF<35000) * (sza>0)*ind_china
        print(np.sum(ind_no),np.sum(ind_on))
        print(np.sum(ind_no)/(np.sum(ind_no)+np.sum(ind_on)))
        count_no = count_no + np.sum(ind_no)
        count_on = count_on + np.sum(ind_on)
print(count_no,count_on)
print(count_no/(count_on+count_no))