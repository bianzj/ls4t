from util.util import *
import calendar
import warnings
warnings.filterwarnings("ignore")

indir_tif = r'F:\data\MSG_2017_full-range\native\tif2\Full\\'
indir_lst = r'F:\data\MSG_2017_full-range\native\lst\Europe\\'

indir_type = r'D:\data\type\\'
indir_type = indir_type + 'type_MSG_Full_0.03.tif'

dataset = gdal.Open(indir_type)
[data, ns, nl, nb, geog_type, proj_type] = read_image_gdal(indir_type)

lat_ =np.asarray([38.54043])
lon_ = np.asarray([-8.003297])
imagex_,imagey_ = loc2map(lat_,lon_,dataset)

lst_ = []
BT_ = []
hour_ = []

year = 2017
for m in range(1, 2):
    daynum = calendar.monthrange(year, m + 1)[1]
    off = 7
    for d in range(0,1):
        month = m + 1
        day = d + 1
        indir_tif_day = indir_tif + "/%02d" % month + "/%02d//" % day
        indir_lst_day = indir_lst + "/%02d" % month + "/%02d//" % day
        if not os.path.exists(indir_tif_day): continue

        # fileNames = search_file_rej(indir_lst_day, ['lst'], 'enp')
        # fileNames.sort()
        # fileNum = len(fileNames)
        # for k in range(fileNum):
        #     fileName = fileNames[k]
        #     infile = indir_lst_day + fileName
        #     [lst, ns, nl, nb, geog, proj] = read_image_gdal(infile)
        #     lst_evo = lst[imagex_,imagey_]
        #     lst_.append(lst_evo)

        fileNames = search_file_rej(indir_tif_day, ['bt1.tif'], 'enp')
        fileNames.sort()
        fileNum = len(fileNames)
        for k in range(fileNum):
            fileName = fileNames[k]
            print(fileName)
            infile = indir_tif_day + fileName
            [bt8, ns, nl, nb, geog, proj] = read_image_gdal(infile)
            bt8_evo = bt8[imagex_,imagey_]/100
            BT_.append(bt8_evo)

'''画图'''
# n = len(lst_)
# x = np.linspace(0,n,n)
# plt.plot(x,lst_)
# plt.ylim(260,320)
# plt.show()

n = len(BT_)
x = np.linspace(0,n,n)
plt.plot(x,BT_)
plt.ylim(260,320)
plt.show()

# indir_med = r"F:\data\MSG_2017_full-range\native\med2\02\01\\"
# imagex_ = 1500
# imagey_ = 1500
# fileNames = search_file_rej(indir_med, ['bt1'], '.tif.')
# for filename in fileNames:
#     print(filename)
#     infile = indir_med + filename
#     [bt, ns, nl, nb, geog, proj] = read_image_gdal(infile)
#     bt_save = bt[imagex_,imagey_]
#     if bt_save < 270: continue
#     BT_.append(bt[imagex_,imagey_])
# n = len(BT_)
# x = np.linspace(0,n,n)
# plt.plot(x,BT_)
# plt.ylim(260,320)
# plt.show()


