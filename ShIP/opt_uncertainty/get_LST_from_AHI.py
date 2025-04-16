from util.util import *
# from pysolar import *


'''
Extract LST results of 9 sites from AHI data in Heihe area
'''

infile_loc = r'E:\field\heihe_site.txt'
mydata = read_txt_str(infile_loc,',')
mydata = np.asarray(mydata)
lon = np.asarray(mydata[:,1],dtype=np.float16)
lat = np.asarray(mydata[:,2],dtype =np.float16)



############################################################################
symbol = 'AHI'

### DTC 与VinRL
# method ='DTC'
# outfile = r'E:\ShIP_DVT\\lst_'+method+'.txt'
# indir_lst0 = r'E:\ShIP_DVT\LST_'+method+'_heihe\\'
# indir_tif0 = r'E:\AHI_heihe\tif\\'

method ='DVT'
outfile = r'E:\ShIP_DVT\\lst_'+method+'.txt'
indir_lst0 = r'E:\ShIP_DVT\nadir_'+method+'_heihe\\'
indir_tif0 = r'E:\AHI_heihe\tif\\'
#
#
# method ='o'
# outfile = r'E:\ShIP_DVT\\lst_'+method+'.txt'
# indir_lst0 = r'E:\AHI_heihe\lst\\'
# indir_tif0 = r'E:\AHI_heihe\tif\\'

npixel = 0

################################################################################

indir_map = r'E:\map\\'
infile_vza = infile8 = indir_map + 'ahi_vza_heihe.tif'
[vza0, ns, nl, nb, geog, proj] = read_image_gdal(infile_vza)
infile_vaa = infile8 = indir_map + 'ahi_vaa_heihe.tif'
[vaa0, ns, nl, nb, geog, proj] = read_image_gdal(infile_vaa)

lst = np.asarray([])
lst_obliq = np.asarray([])
lst_nadir_normalized = np.asarray([])
lst_obliq_normalized = np.asarray([])
days_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

nss = ns
nll = nl


###############################################################################


infile_ref = r'E:\type\type_heihe_2000.tif'
dataset = gdal.Open(infile_ref)
im_width = dataset.RasterXSize * 1
im_height = dataset.RasterYSize * 1
im_bands = dataset.RasterCount * 1
data = dataset.ReadAsArray(0, 0, im_width, im_height)
im_geotrans = dataset.GetGeoTransform()
im_proj = dataset.GetProjection()
# 返回经纬度对应的投影坐标
temp1, temp2 = lonlat2geo(dataset, lat, lon)
# 将投影坐标或地理坐标转化为图像坐标，行列号
imagex, imagey = geo2imagexy(dataset, temp1, temp2)
imagex =np.asarray(imagex,dtype=np.int16)
# [270 218 285 226 229 219  54  54  47]
imagey = np.asarray(imagey,dtype = np.int16)
# [126  66 155 128 125 132 181 181 176]


result_ = []
#  有9个站点
num_loc = 9

for kmonth0 in range(8, 9):
    thedoy = (kmonth0 - 1) * 30 + 16

    for kday0 in range(1, 32):
        kstep = 0
        for khour0 in range(3 - 8, 21 - 8):
            indir_lst = indir_lst0 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'
            indir_tif = indir_tif0 + r'\%02d' % kmonth0 + r'\%02d' % kday0 + '\\'

            kdoy = date2DOY(2019, kmonth0, kday0)

            khour = khour0
            kday = kday0
            kmonth = kmonth0
            if khour0 < 0:
                kdoy = kdoy - 1
                khour = khour0 + 24
                if kday0 == 1:
                    if kmonth0 == 1: continue
                    kmonth = kmonth0 - 1
                    kday = days_of_month[kmonth0 - 2]
                    indir_lst = indir_lst0 + r'\%02d' % kmonth + r'\%02d' % kday + '\\'
                    indir_tif = indir_tif0 + r'\%02d' % kmonth + r'\%02d' % kday + '\\'
                else:
                    kday = kday0 - 1
                    indir_lst = indir_lst0 + r'\%02d' % (kmonth0) + r'\%02d' % (kday) + '\\'
                    indir_tif = indir_tif0 + r'\%02d' % (kmonth0) + r'\%02d' % (kday) + '\\'

            for kmin in range(0, 4, 3):
                pst = '%02d'%khour + '%d0'%kmin+'00'
                result = np.zeros(38)
                result[0] = kdoy
                result[1] = np.int(pst)

                infile_lst = indir_lst + symbol + '_2019%03d' % (
                    kdoy) + '_%02d' % khour + '%1d0' % kmin + '_lst.tif'
                infile_tcc = indir_tif + symbol + '_2019%03d' % (
                    kdoy) + '_%02d' % khour + '%1d0' % kmin + '_tcc.tif'
                infile_sza = indir_tif + symbol + '_2019%03d' % (
                    kdoy) + '_%02d' % khour + '%1d0' % kmin + '_sza.tif'
                infile_saa = indir_tif + symbol + '_2019%03d' % (
                    kdoy) + '_%02d' % khour + '%1d0' % kmin + '_saa.tif'
                print(infile_lst)
                if (os.path.exists(infile_lst) == 0):
                    # 将日期和时间写入文件中，第0列和第1列
                    result_.append(result)
                    continue

                print(infile_lst)
                [lst, ns, nl, temp, geog, proj] = read_image_gdal(infile_lst)
                [tcc, ns0, nl0, temp, geog, proj] = read_image_gdal(infile_tcc)
                tcc = resize_data_near(tcc, nl, ns)
                if (os.path.exists(infile_sza) == 1):
                    [sza, ns, nl, temp, geog, proj] = read_image_gdal(infile_sza)
                    [saa, ns, nl, temp, geog, proj] = read_image_gdal(infile_saa)
                else:
                    sza = np.zeros([nl, ns]) + 90
                    saa = np.zeros([nl,ns])

                ind = (lst < 100) *(lst !=0)*(np.isnan(lst)==0)
                lst[ind] = lst[ind] + 273.15
                # 将9个站点的平均地表温度存下来，从第2列到第10列
                result[2:2 + num_loc] = getStatic_ave(lst, imagex, imagey, npixel, 250, 350)
                # 将云量TCC存储下来，存在第11列到19列
                result[2 + num_loc:2 + num_loc*2] = getStatic_ave(tcc, imagex, imagey, npixel, -1, 500)
                vza = vza0[imagex,imagey]
                vaa = vaa0[imagex,imagey]
                # 将vza存下来，存在第20列到第28列
                result[2 + num_loc*2:2 + num_loc*3] = vza
                sza = sza[imagex, imagey]
                saa = saa[imagex, imagey]
                psi = np.abs(vaa-saa)
                thetas = np.deg2rad(sza)
                thetaa = np.deg2rad(psi)
                thetav = np.deg2rad(abs(vza))

                # 把9个站点热点模型中的f（d）计算出来放在文本文件的最后9列
                f = np.sqrt(
                    (np.power(np.tan(thetas), 2) + np.power(np.tan(thetav), 2) - 2 * np.tan(thetas) * np.tan(thetav) *
                     np.cos(thetaa)))
                result[2 + num_loc*3:2 + num_loc*4] = f
                result_.append(result)

result_ = np.asarray(result_)
np.savetxt(outfile,result_,fmt='%5.3f')


