from util.myfun import *
from pysolar import *


infile_loc = r'E:\field\heihe_site.txt'
mydata = read_txt_str(infile_loc,',')
mydata = np.asarray(mydata)
lon = np.asarray(mydata[:,1],dtype=np.float16)
lat = np.asarray(mydata[:,2],dtype =np.float16)



############################################################################
dayNight = 'day'
nadirObliq = 'obliq'
symbol = 's3b'

### Ermida
outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_Ermida.txt'
indir_lst = r'E:\ShIP_VNIR\Ecoeff_static_heihe\\'

### 直接使用
# outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_direct.txt'
# indir_lst = r'E:\ShIP_VNIR\LST_direct_heihe\\'

### 红光使用
# outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_step_vt_red.txt'
# indir_lst = r'E:\ShIP_VNIR\LST_step_vt_red_heihe\\'
#
# ### 近红外使用
# outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_step_vt_nir.txt'
# indir_lst = r'E:\ShIP_VNIR\LST_step_vt_nir_heihe\\'

### 分步使用
# outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_step.txt'
# indir_lst = r'E:\ShIP_VNIR\LST_step_heihe\\'

### 集成使用
# outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_step_one.txt'
# indir_lst = r'E:\ShIP_VNIR\LST_step_one_heihe\\'

### 原始温度产品
# outfile = r'E:\\ship_vnir\\'+symbol+'_lst_'+dayNight+'_'+nadirObliq+'_origin.txt'
# indir_lst = r'E:\SLSTR\\'+symbol+'_heihe\lst\\'


indir_tif = r'E:\SLSTR\\'+symbol+'_heihe\\tif\\'
###############################################################################


infile_ref = r'E:\type\type_heihe_1000.tif'
dataset = gdal.Open(infile_ref)
im_width = dataset.RasterXSize * 1
im_height = dataset.RasterYSize * 1
im_bands = dataset.RasterCount * 1
data = dataset.ReadAsArray(0, 0, im_width, im_height)
im_geotrans = dataset.GetGeoTransform()
im_proj = dataset.GetProjection()
temp1, temp2 = lonlat2geo(dataset, lat, lon)
imagex, imagey = geo2imagexy(dataset, temp1, temp2)
imagex =np.asarray(imagex,dtype=np.int16)
imagey = np.asarray(imagey,dtype = np.int16)



result_ = []
num_loc = 9
for kdoy in range(1,366):

    file = symbol + '_2019%03d_'%kdoy+dayNight

    infile_lst = indir_lst + file+'_lst_'+nadirObliq+'.tif'
    infile_pst =  indir_tif + file+'_time.tif'
    infile_tcc =  indir_tif + file+'_cloud_'+nadirObliq+'.tif'
    infile_vza = indir_tif + file+'_vza_'+nadirObliq+'.tif'




    result = np.zeros(38)
    result[0] = kdoy
    print(infile_lst,infile_pst)
    if (os.path.exists(infile_lst)==0) or (os.path.exists(infile_pst)==0):
        result_.append(result)
        continue

    [pst,ns,nl,nb,geog,proj] = read_image_gdal(infile_pst)
    pst=np.max(pst[imagex, imagey])
    result[1]=(pst)

    [lst,ns,nl,nb,geog,proj] = read_image_gdal(infile_lst)
    # result[2:11]=(lst[imagex,imagey])
    result[2:2+num_loc] = getStatic_ave(lst,imagex,imagey,0,250,350)

    [tcc,ns,nl,nb,geog,proj] = read_image_gdal(infile_tcc)
    # result[11:]=(tcc[imagex,imagey])
    result[11:11+num_loc] = getStatic_ave(tcc,imagex,imagey,1,-1,500)



    [vza,ns,nl,nb,geog,proj] = read_image_gdal(infile_vza)
    vza = vza[imagex,imagey]
    result[20:20+num_loc] = vza

    if dayNight =='day':
        infile_sza = indir_tif + file + '_sza_' + nadirObliq + '.tif'
        infile_vaa = indir_tif + file + '_vaa_' + nadirObliq + '.tif'
        infile_saa = indir_tif + file + '_saa_' + nadirObliq + '.tif'

        [vaa, ns, nl, nb, geog, proj] = read_image_gdal(infile_vaa)
        vaa = vaa[imagex, imagey]
        [sza, ns, nl, nb, geog, proj] = read_image_gdal(infile_sza)
        sza = sza[imagex, imagey]
        [saa, ns, nl, nb, geog, proj] = read_image_gdal(infile_saa)
        saa = saa[imagex, imagey]


        psi = np.abs(vaa-saa)
        thetas = np.deg2rad(sza)
        thetaa = np.deg2rad(psi)
        thetav = np.deg2rad(abs(vza))

        f = np.sqrt(
            (np.power(np.tan(thetas), 2) + np.power(np.tan(thetav), 2) - 2 * np.tan(thetas) * np.tan(thetav) *
             np.cos(thetaa)))
        result[29:29+num_loc] = f


    print(file,kdoy)
    result_.append(result)

result_ = np.asarray(result_)
np.savetxt(outfile,result_,fmt='%5.3f')



