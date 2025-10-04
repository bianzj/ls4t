import numpy as np
from util.util import *

'''
从数据集中提取感兴趣点及其缓冲区对应的数据和角度信息
在’uav_bian_stack_for_track'中得到了串联图像及其对应的观测信息
逐个点位计算角度信息，需要说明的是角度信息会累计到一起，
但是验证等多被用于太阳主平面或者垂直太阳主平面（也并一定是主平面，主要是十字交叉的飞行方式），需要进行分割出4条变化的线路
'''


a = 3.55946070e-02
b = 2.40778447e+02
indir = r'F:\UAVpro\20200604huailai\1201\TIR_result\\'
sza = 20.8
saa = 167
lineaa = 180
vza_hold = 25

### 白板，杨树，柏树，松树，玉米
posx = np.asarray([192,295,367,445,254])
posy = np.asarray([332,260,280,300,400])
num_sample = 5

track1 = '2_1'
track2 = '2_0'
off = 25

infile = r'F:\UAVpro\20200604huailai\1201\TIR_ref.tif'
temp_data, temp_width, temp_height, temp_band, temp_geotrans, temp_proj, temp_dataset = read_image_dataset_gdal(infile)
img = temp_data
img = img * a - b
for k in range(num_sample):
    img[posx[k]-off:posx[k]+off,posy[k]-off:posy[k]+off] = 25
plt.imshow(img,cmap='jet',vmin = 25,vmax = 35)
plt.show()


for kp in range(num_sample):
    ##########################################################################
    ### yyy 210--300   xxx 255--300
    ############################################################################
    ### 近太阳侧
    # kp = 0
    dbt_ = []
    vza_ = []
    vaa_ = []
    infile = indir+'dbt'+track1+'.tif'
    dbt,width,height,band,geotrans,proj = read_image_gdal(infile)
    infile = indir+'vza'+track1+'.tif'
    vza,width,height,band,geotrans,proj = read_image_gdal(infile)
    infile = indir+'vaa'+track1+'.tif'
    vaa,width,height,band,geotrans,proj = read_image_gdal(infile)
    for kb in range(band):
        temp = dbt[kb,posx[kp]-off:posx[kp]+off,posy[kp]-off:posy[kp]+off]
        ind = (temp > 6500) *(temp < 8550) *(np.isnan(temp)==0)
        if np.sum(ind) <= 10: continue
        dbt_.append(np.average(temp[ind]))
        temp = vza[kb, posx[kp]:posx[kp]+1, posy[kp]:posy[kp]+1]
        vza_.append(np.average(temp))
        # temp = vaa[kb, posx[kp]:posx[kp]+1, posy[kp]:posy[kp]+1]
        # vaa_.append(np.average(temp))
        # temp = vza[kb,posx[kp]-off:posx[kp]+off,posy[kp]-off:posy[kp]+off]
        # vza_.append(np.average(temp[ind]))
        temp = vaa[kb,posx[kp]-off:posx[kp]+off,posy[kp]-off:posy[kp]+off]
        vaa_.append(np.average(temp[ind]))
    ############ 将离散数据整理到特定的角度区间
    vaa_ = np.asarray(vaa_)
    vza_ = np.asarray(vza_)
    dbt_ = np.asarray(dbt_)
    ind = np.abs(vaa_ - lineaa) > 90
    vza_[ind] = vza_[ind] * (-1)
    newvza1_ = np.zeros(37)
    newvaa1_ = np.zeros(37)
    newdbt1_ = np.zeros(37)
    kk = 0
    for kvza in range(-54,55,3):
        ind = (vza_>(kvza-1.5))*(vza_<(kvza+1.5))
        if np.sum(ind) > 1:

            newvza1_[kk] = (np.average(vza_[ind]))
            newvaa1_[kk] = (np.average(vaa_[ind][1]))
            newdbt1_[kk] = (np.average(dbt_[ind]))
        kk = kk + 1

    ############################################################################
    ### 远太阳侧
    dbt_ = []
    vza_ = []
    vaa_ = []
    infile = indir+'dbt'+track2+'.tif'
    dbt,width,height,band,geotrans,proj = read_image_gdal(infile)
    infile = indir+'vza'+track2+'.tif'
    vza,width,height,band,geotrans,proj = read_image_gdal(infile)
    infile = indir+'vaa'+track2+'.tif'
    vaa,width,height,band,geotrans,proj = read_image_gdal(infile)
    for kb in range(band):
        temp = dbt[kb,posx[kp]-off:posx[kp]+off,posy[kp]-off:posy[kp]+off]
        ind = (temp > 6500) *(temp < 8550) *(np.isnan(temp)==0)
        if np.sum(ind) <= 10: continue
        dbt_.append(np.average(temp[ind]))
        temp = vza[kb, posx[kp]:posx[kp]+1, posy[kp]:posy[kp]+1]
        vza_.append(np.average(temp))
        # temp = vaa[kb, posx[kp]:posx[kp]+1, posy[kp]:posy[kp]+1]
        # vaa_.append(np.average(temp))
        # temp = vza[kb,posx[kp]-off:posx[kp]+off,posy[kp]-off:posy[kp]+off]
        # vza_.append(np.average(temp[ind]))
        temp = vaa[kb,posx[kp]-off:posx[kp]+off,posy[kp]-off:posy[kp]+off]
        vaa_.append(np.average(temp[ind]))
    ####### 将离散数据整理到特定的角度空间间隔空间
    vaa_ = np.asarray(vaa_)
    vza_ = np.asarray(vza_)
    dbt_ = np.asarray(dbt_)
    ind = np.abs(vaa_ - lineaa) > 90
    vza_[ind] = vza_[ind] * (-1)
    newvza2_ = np.zeros(37)
    newvaa2_ = np.zeros(37)
    newdbt2_ = np.zeros(37)
    kk = 0
    for kvza in range(-54,55,3):
        ind = (vza_>(kvza-1.5))*(vza_<(kvza+1.5))
        if np.sum(ind) > 1:
            newvza2_[kk] = (np.average(vza_[ind]))
            newvaa2_[kk] = (np.average(vaa_[ind][1]))
            newdbt2_[kk] = (np.average(dbt_[ind]))
        kk = kk + 1

    ######################################################################################
    ### 得到两条航带的各自的方向效应
    indd = (np.abs(newvza1_) < vza_hold) * (np.abs(newvza2_) < vza_hold) * (newdbt1_ > 0) * (newdbt2_ > 0)
    ind = (newdbt1_) > 0
    newdbt1_[ind] = newdbt1_[ind] - np.average(newdbt1_[indd])
    ind = (newdbt2_) > 0
    newdbt2_[ind] = newdbt2_[ind] - np.average(newdbt2_[indd])

    newdbt_ = np.zeros(37)
    newvza_ = np.zeros(37)
    newvaa_ = np.zeros(37)

    ### 通过相同区域的数据的平均值，调整一下航带数据的变化偏差
    ind = (newdbt2_ != 0) * (newdbt1_ != 0) * (np.abs(newvza1_) < 50) * (np.abs(newvza2_) < 50)
    test = (newdbt1_[ind] * 0.5 + newdbt2_[ind] * 0.5)
    bias1 = np.average(newdbt1_[ind] - test)
    bias2 = np.average(newdbt2_[ind] - test)

    ### 如果数据都有，则取平均；
    ### 如果数据只有一条航带，则用偏差值进行校正
    ind = (newdbt2_ != 0) * (newdbt1_ != 0)
    newdbt_[ind] = (newdbt1_[ind] * 0.5 + newdbt2_[ind] * 0.5)
    newvza_[ind] = (newvza1_[ind] * 0.5 + newvza2_[ind] * 0.5)
    newvaa_[ind] = (newvaa1_[ind] * 0.5 + newvaa2_[ind] * 0.5)
    ind = (newdbt2_ == 0) * (newdbt1_ != 0)
    newdbt_[ind] = newdbt1_[ind] * 1.0 - bias1
    newvza_[ind] = newvza1_[ind] * 1.0
    newvaa_[ind] = newvaa1_[ind] * 1.0
    ind = (newdbt2_ != 0) * (newdbt1_ == 0)
    newdbt_[ind] = newdbt2_[ind] * 1.0 - bias2
    newvza_[ind] = newvza2_[ind] * 1.0
    newvaa_[ind] = newvaa2_[ind] * 1.0

    newdbt_ = newdbt_ * a

    ind = np.abs(newvza_) > 0
    plt.rcParams['figure.dpi'] = 150
    plt.rcParams['figure.figsize'] = (4.0, 3.2)
    plt.xlabel(r'VZA $(\degree)$', fontsize=12)
    plt.ylabel(r'Directional Anisotropies ($\degree$C)', fontsize=12)
    plt.plot(newvza_[ind], newdbt_[ind], 'ko', markersize=5)
    plt.ylim([-5.0, 4.0])
    plt.xlim([-60, 60])
    plt.legend(loc='upper left', labels=['Mea', 'Sim'], ncol=1)
    plt.show()