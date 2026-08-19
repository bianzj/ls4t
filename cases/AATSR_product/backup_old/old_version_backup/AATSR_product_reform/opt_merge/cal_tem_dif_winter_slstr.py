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
month = 7
daynum = calendar.monthrange(year, month)[1]
# daynum = 1


indir_lst = r'G:\data\slstr_china\lst\\'

count_no = 0
count_on = 0
for d in range(182,212):
    print("year/month/day:" + str(year) + '%02d' % int(month) + '%02d' % int(d))
    # time_str = str(year) + "//" + '%02d' % int(month) + "//" + '%02d' % int(d + 1) + "//"
    time_str = '%02d' % int(month) + "//" + '%02d' % int(d + 1) + "//"
    indir_lst_day = indir_lst
    doystr = '2019%03d' %d
    fileNames = search_file_rej(indir_lst, ['day_lst_n',doystr], 'enp')
    fileNum = np.size(fileNames)
    off_set = 9

    for file in fileNames:
        fileName = file[:-17]
        print(fileName)


        '''读取温度和组分温度'''
        lst_n_dir = indir_lst_day + fileName + 'day_lst_nadir.tif'
        lst_f_dir = indir_lst_day + fileName + 'day_lst_obliq.tif'

        [lstN, ns, nl, bands, geog, proj] = read_image_gdal(lst_n_dir)
        [lstF, ns, nl, bands, geog, proj] = read_image_gdal(lst_f_dir)

        ind_no = (lstN>lstF) * (lstN>24000)*(lstN<35000)* (lstF>24000)*(lstF<35000)
        ind_on = (lstN<lstF)* (lstN>24000)*(lstN<35000)* (lstF>24000)*(lstF<35000)
        print(np.sum(ind_no),np.sum(ind_on))
        print(np.sum(ind_no)/(np.sum(ind_no)+np.sum(ind_on)))
        count_no = count_no + np.sum(ind_no)
        count_on = count_on + np.sum(ind_on)
print(count_no,count_on)
print(count_no/(count_on+count_no))