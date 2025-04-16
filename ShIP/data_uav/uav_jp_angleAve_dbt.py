from util.util import *

'''
将观测图像进行提取，得到多角度数据集
该方法是Jean-Pierre Lagourede et al.等一致
地物在某个角度的可视比例=地物在像元中出现的概率
用于处理水平均质的地表类型，即观测目标唯一才能平均
与directAve相比，该程序考虑了每个图像的观测角度是不同的
'''

### 565   585
###
####################################################
indir = r'E:\20211414chengde\dataset\10\tir\\'

### 不同航带情况，每条航带选择特定的图像编号
start = np.asarray([930,830,524,555,608,612])
end = np.asarray([935+1,900+1,528+1,560+1,610,618])



####################
### 参考图像，即底图
infile = indir + r'areaa.tif'
temp,ref_width,ref_height,ref_band,ref_geotrans,ref_proj,refdataset = read_image_dataset_gdal(infile)

##################
### GPS 数据
infile = indir + r'areaa_10.txt'
mydata = read_txt_array(infile,0,16)
fileNamePos = mydata[:,0]
pos = mydata[:,1:4]
################
### 输入数据的文件夹
indir = indir + r'areaa\orth\\'

#### 要保存出的多角度数据集的范围
numVZA = 75
numVAA = 360
outdir = indir

dbt = np.zeros([numVZA, numVAA])
dbt_ave = np.zeros([numVZA, numVAA])
count = np.zeros([numVZA, numVAA], dtype=np.int)
iffirst = 1
for kline in range(0,5):
    for kimage in range(start[kline], end[kline],1):

        ####################################################
        ##### 输入数据文件夹情况
        infile = "%05d"%(kimage)
        fileName = indir + infile+'.tif'
        if 1-os.path.exists(fileName):
            continue
        print(infile)
        #######################################################
        ### 相机数据
        # kpos = fileNamePos (infile)
        kpos = np.where(fileNamePos == np.int(infile))
        if kpos[0] < 0: continue
        camera_geoy1 = pos[kpos, 1][0][0]
        camera_geox1 = pos[kpos, 0][0][0]
        camera_height = pos[kpos, 2][0]


        #######################################################
        #### 该文件的情况，即temp开头的是正在处理的单张影像
        dataset1 = gdal.Open(fileName)
        temp_width1 = dataset1.RasterXSize
        temp_height1 = dataset1.RasterYSize
        temp_geotrans1 = dataset1.GetGeoTransform()
        temp_proj1 = dataset1.GetProjection()
        temp_data1 = dataset1.ReadAsArray(0, 0, temp_width1, temp_height1)
        temp_x1 = np.zeros([temp_height1, temp_width1], dtype=np.int)
        temp_y1 = np.zeros([temp_height1, temp_width1], dtype=np.int)
        temp = np.arange(0, temp_width1)
        for k in range(temp_height1):
            temp_x1[k, :] = k
            temp_y1[k, :] = temp
        temp_geox1, temp_geoy1 = imagexy2geo(dataset1, temp_x1, temp_y1)
        temp_lon1, temp_lat1 = geo2lonlat(dataset1, temp_geox1, temp_geoy1)
        ind = (temp_data1 < 6750)
        temp_data1[ind] = 0
        ind = (temp_data1 > 7500)
        temp_data1[ind] = 0

        #########################################################
        #### calculate viewing angle for each pixel in this file
        # camera_geox1, camera_geoy1 = lonlat2geo(dataset1, camera_lon, camera_lat)
        # camera_y1, camera_x1 = geo2imagexy(dataset1, camera_geox1, camera_geoy1)
        camera_lon,camera_lat = geo2lonlat(dataset1,camera_geox1,camera_geoy1)

        ref_geogx1, ref_geogy1 = lonlat2geo(refdataset, temp_lon1, temp_lat1)
        ref_y, ref_x = geo2imagexy(refdataset, ref_geogx1, ref_geogy1)
        distance = np.sqrt((temp_geox1 - camera_geox1) * (temp_geox1 - camera_geox1) +
                           (temp_geoy1 - camera_geoy1) * (temp_geoy1 - camera_geoy1))
        temp_zenith = np.arctan(distance / camera_height) / np.pi * 180.0
        temp_azimuth = np.arctan2((temp_lon1 - camera_lon), (temp_lat1 - camera_lat)) / np.pi * 180.0



        temp_azimuth = ((temp_azimuth + 360.0 + 180.0) % 360.0)
        temp_azimuth = np.reshape(temp_azimuth, [temp_height1, temp_width1])

        temp_zenith = np.asarray(temp_zenith,dtype=np.int)
        temp_azimuth = np.asarray(temp_azimuth,dtype= np.int)

        differ = 0
        ###########################################################
        ##### 由于温度的时间变化，因此在长时间观测时候，会进行数据的时间偏移校正
        ##### 1）通过星下点观测数据进行时间变化调整
        ####  2）数据要满足一定的条件，数目达标
        ###########################################################
        # ind = (temp_zenith < 33) *(temp_data1 > 6750) *(dbt[temp_zenith,temp_azimuth]>6750)
        # if np.sum(ind) > 500:
        #     temp_nadir = np.average(temp_data1[ind])
        #     ave_nadir = np.average(dbt_ave[temp_zenith[ind],temp_azimuth[ind]])
        #     differ =  (ave_nadir - temp_nadir)*1.00
        #     print(ave_nadir,temp_nadir,differ)
        #     iffirst = 0
        # else:
        #     if iffirst == 0:
        #         continue

        ################################################################
        ##### 要采纳的数据也要满足一定的条件，例如不要温度太高的建筑，
        ####  也不要温度太低的水体，保证观测的是相同地物
        ################################################################
        ind = (temp_data1+differ > 6750) *(temp_data1+differ < 7150)
        dbt[temp_zenith[ind],temp_azimuth[ind]] = dbt[temp_zenith[ind],temp_azimuth[ind]] + temp_data1[ind]+differ
        count[temp_zenith[ind], temp_azimuth[ind]] = count[temp_zenith[ind], temp_azimuth[ind]] +1

        ############################################################
        #### 地表亮温的平均值
        ind = count > 0
        dbt_ave[ind] = dbt[ind] / count[ind]


ind = count > 0
dbt[ind] = dbt[ind] / count[ind]

outfile = outdir + r'dbt.tif'
write_image_gdal(dbt, numVAA, numVZA, 1, '', '', outfile)


