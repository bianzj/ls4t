from util.myfun import *
from util.drought_funs import *

'''生成SLSTR tvdi'''

ll1 = 280+50+25
ll2 = 530-50+25
ss1 = 100+50+50
ss2 = 350
### med
ll1 = 280
ll2 = 530
ss1 = 100
ss2 = 350


### small
# ll1 = 370
# ll2 = 490
# ss1 = 190
# ss2 = 290


### LARGE
# ll1 = 180
# ll2 = 530
# ss1 = 50
# ss2 = 400

indir_dem = r'E:\map\dem_polar_heihe.tif'
dem,ns,nl,nb,geog,proj = read_image_gdal(indir_dem)
dem = dem[ll1:ll2,ss1:ss2]

indir_lst = r'E:\SLSTR_heihe\s3a\lst\\'
indir_tif = r'E:\SLSTR_heihe\s3a\tif\\'
outdir = r'E:\SLSTR_heihe\s3a\tvdi\\'
symbol0 = 'S3A'

doymin = 150
doymax = 300
lstshred = 273.15+15
demthred = 2000
psthred = 0.35
files = search_file_rej(indir_lst,['day','lst'],'obliq')

ffoutfile = outdir + 's3a_nadir.txt'

ff_ = []

num_files = np.size(files)
for kfile in range(num_files):

    file = files[kfile][:-14]
    doy = np.int(file[8:11])
    if(doy < doymin):continue
    if(doy > doymax):continue

    infile_lst = indir_lst + file+'_lst_nadir.tif'
    infile_red = indir_tif + file+'_red_nadir.tif'
    infile_nir = indir_tif + file+'_nir_nadir.tif'
    infile_cloud = indir_tif + file+'_cloud_nadir.tif'

    lst,ns,nl,nb,geog,proj = read_image_gdal(infile_lst)
    red,ns,nl,nb,geog,proj = read_image_gdal(infile_red)
    nir,ns,nl,nb,geog,proj = read_image_gdal(infile_nir)
    cloud,ns,nl,nb,geog,proj = read_image_gdal(infile_cloud)



    nl_sub = ll2-ll1
    ns_sub = ss2-ss1


    lst_ = lst[ll1:ll2,ss1:ss2]
    red_ = red[ll1:ll2,ss1:ss2]
    nir_ = nir[ll1:ll2,ss1:ss2]
    cloud_ = cloud[ll1:ll2,ss1:ss2]
    ndvi_ = (nir_ - red_) / (nir_ + red_)

    # lst = resize_data_line(lst,nl,ns)
    # ndvi = resize_data_near(ndvi,nl,ns)
    # cloud = resize_data_near(cloud,nl,ns)



    ind = (cloud_ == 0) *(~np.isnan(ndvi_)) *(lst_ > lstshred)*(lst_<335)*(ndvi_>0.01)*(ndvi_<1.95) *\
          (red_ < 0.35) *(nir_ < 0.5)*(nir_ > 0.15) * (dem < demthred)

    # ndvi = ndvi_[ind]
    # lst = lst_[ind]

    if np.sum(ind) <= nl_sub*ns_sub*psthred:continue

    print(kfile,infile_lst)
    # ndvi_value, lstmax_value, fmax, lstmin_value, fmin = find_hot_cold_line_5_percent(ndvi_[ind], lst_[ind])
    ndvi_value, lstmax_value, fmax, lstmin_value, fmin = find_hot_cold_line_3_2(ndvi_[ind], lst_[ind])
    '''to eliminate the bad cold line'''
    prob = 0.66
    if fmin[0] > 5:
        fcenter = fmin[0] * prob + fmin[1]
        fmin[0] = 5
        fmin[1] = fcenter - fmin[0] * prob
    if fmin[0] < -5:
        fcenter = fmin[0] * prob + fmin[1]
        fmin[0] = -5
        fmin[1] = fcenter - fmin[0] * prob
    if fmax[0] > -15:
        fcenter = fmax[0] * prob + fmax[1]
        fmax[0] = -15
        fmax[1] = fcenter - fmax[0] * prob
    maxdif = fmax[1] - lstshred
    if fmax[0] < -maxdif:
        fcenter = fmax[0] * prob + fmax[1]
        fmax[0] = -maxdif
        fmax[1] = fcenter - fmax[0] * prob
    #
    # fmin[1] = fmin[1] + prob * fmin[0]
    # fmin[0] = 0
    # fmin[1] = np.percentile(lst_[ind], 1)

    ########################################
    ndvi_plt = [0, 1]
    lstmax_value_plt = np.polyval(fmax, ndvi_plt)
    lstmin_value_plt = np.polyval(fmin, ndvi_plt)

    min1 = 0.0
    max1 = 1.0
    min2 = 275
    max2 = 335
    data1 = ndvi_[ind]
    data2 = lst_[ind]
    ind = (data1 > 0.01) * (data2 > 270) * (data2 < 335) * (data1 < 0.95)
    plt.hist2d(data1[ind], data2[ind], bins=100, norm=LogNorm(), cmap='jet')
    # plt.plot(ndvi_value,lstmax_value,'k+')
    plt.plot(ndvi_plt, lstmax_value_plt, 'r-')
    # plt.plot(ndvi_value,lstmin_value,'k+')
    plt.plot(ndvi_plt, lstmin_value_plt, 'k-')
    plt.text(0.1, 295, '$LST_{max}$ = %.2f' % fmax[0] + '*NDVI+%.2f' % fmax[1], color='r', fontsize=10)
    plt.text(0.1, 292, '$LST_{min}$ = %.2f' % fmin[0] + '*NDVI+%.2f' % fmin[1], color='k', fontsize=10)
    plt.xlim([min1, max1])
    plt.ylim([min2, max2])
    plt.xlabel(r'NDVI')
    plt.ylabel(r'LST (K)')
    plt.colorbar()
    plt.show()
    ##########################################



    print(fmin,fmax)
    Tsmin = np.polyval(fmin, ndvi_)
    Tsmax = np.polyval(fmax, ndvi_)
    Tsminave = np.average(Tsmin[Tsmin > 270])
    # Tsmin[:] = Tsminave
    # Tsmin[:] = np.min(Tsmin)
    # Tsmin[:] = np.average(lstmin_value_plt[lstmin_value_plt > 270])
    tvdi_ = (lst_ - Tsmin) / (Tsmax - Tsmin)
    # ind = (ndvi_ > 0.01) * (lst_ < 335) * (ndvi_ < 1.95) * (lst_ > lstshred) * (~np.isnan(ndvi_)) * (~np.isnan(lst_))*(cloud_==0) *\
    #       (red_ < 0.35)*(nir_ < 0.5)*(nir_ > 0.15)* (dem < demthred)

    '''important'''
    ind = (ndvi_ > 0.01) * (lst_ < 335) * (ndvi_ < 1.95) * (lst_ > lstshred) * (~np.isnan(ndvi_)) * (~np.isnan(lst_))*(cloud_ == 0) *\
          (red_ < 0.35)*(nir_ < 0.5)*(nir_ > 0.15)* (dem < demthred)
    indd = (tvdi_ > -0.25) * (tvdi_ < 1.25)
    # if np.sum(indd) <= np.sum(ind)*0.35:continue

    tvdi_[~ind] = 0
    tvdi_ = np.reshape(tvdi_,[nl_sub,ns_sub])
    tvdi = np.zeros([nl,ns])
    tvdi[ll1:ll2,ss1:ss2] = tvdi_
    symbol = symbol0 + '_nadir'
    outfile = outdir + file+'_tvdi_'+symbol+'.tif'
    write_image_gdal(tvdi,ns,nl,1,'','',outfile)

    ff = np.zeros(6)
    ff[0] = doy
    ff[1:3] = fmin
    ff[3]  = Tsminave
    ff[4:] = fmax
    ff_.append(ff)



    ### for obliqe

    file = files[kfile][:-14]
    doy = np.int(file[8:11])
    if(doy < doymin):continue
    if(doy > doymax):continue

    infile_lst = indir_lst + file+'_lst_obliq.tif'
    infile_red = indir_tif + file+'_red_obliq.tif'
    infile_nir = indir_tif + file+'_nir_obliq.tif'
    infile_cloud = indir_tif + file+'_cloud_obliq.tif'

    if os.path.exists(infile_lst) == 0: continue

    lst,ns,nl,nb,geog,proj = read_image_gdal(infile_lst)
    red,ns,nl,nb,geog,proj = read_image_gdal(infile_red)
    nir,ns,nl,nb,geog,proj = read_image_gdal(infile_nir)
    cloud,ns,nl,nb,geog,proj = read_image_gdal(infile_cloud)


    nl_sub = ll2-ll1
    ns_sub = ss2-ss1


    lst_ = lst[ll1:ll2,ss1:ss2]
    red_ = red[ll1:ll2,ss1:ss2]
    nir_ = nir[ll1:ll2,ss1:ss2]
    cloud_ = cloud[ll1:ll2,ss1:ss2]
    ndvi_ = (nir_ - red_) / (nir_ + red_)

    ind = (cloud_ == 0) *(~np.isnan(ndvi_)) *(lst_ > lstshred)*(lst_<335)*(ndvi_>0.01)*(ndvi_<0.95) *\
          (red_ < 0.35) *(nir_ < 0.5)*(nir_ > 0.15) * (dem < demthred)
    if np.sum(ind) <= nl_sub*ns_sub*0.1:continue
    # ndvi_value, lstmax_value, fmax, lstmin_value, fmin = find_hot_cold_line_3(ndvi_[ind], lst_[ind])
    # ndvi_value, lstmax_value, fmax, lstmin_value, fmin = find_hot_cold_line_5_percent(ndvi_[ind], lst_[ind])
    # prob = 0.66
    # if fmin[0] > 10:
    #     fcenter = fmin[0] * prob + fmin[1]
    #     fmin[0] = 10
    #     fmin[1] = fcenter - fmin[0] * prob
    # if fmin[0] < -10:
    #     fcenter = fmin[0] * prob + fmin[1]
    #     fmin[0] = -10
    #     fmin[1] = fcenter - fmin[0] * prob
    # if fmax[0] > -10:
    #     fcenter = fmax[0] * prob + fmax[1]
    #     fmax[0] = -10
    #     fmax[1] = fcenter - fmax[0] * prob
    # maxdif = fmax[1] - lstshred
    # if fmax[0] < -maxdif:
    #     fcenter = fmax[0] * prob + fmax[1]
    #     fmax[0] = -maxdif
    #     fmax[1] = fcenter - fmax[0] * prob
    # fmin[1] = fmin[1] + prob * fmin[0]
    # fmin[0] = 0
    # fmin[1] = np.percentile(lst_[ind], 1)


    Tsmin = np.polyval(fmin, ndvi_)
    Tsmax = np.polyval(fmax, ndvi_)
    # Tsmin[:] = Tsminave
    tvdi_ = (lst_ - Tsmin) / (Tsmax - Tsmin)
    ind = (ndvi_ > 0.01) * (lst_ < 335) * (ndvi_ < 0.95) * (lst_ > lstshred) * (~np.isnan(ndvi_)) * (~np.isnan(lst_))*(cloud_==0) *\
          (red_ < 0.35) *(nir_ < 0.5)*(nir_ > 0.15)* (dem < demthred)
    tvdi_[~ind] = 0
    tvdi_ = np.reshape(tvdi_,[nl_sub,ns_sub])
    tvdi = np.zeros([nl,ns])
    tvdi[ll1:ll2,ss1:ss2] = tvdi_
    symbol = symbol0 + '_obliq'
    outfile = outdir + file+'_tvdi_'+symbol+'.tif'
    write_image_gdal(tvdi,ns,nl,1,'','',outfile)



ff_ = np.asarray(ff_)
np.savetxt(ffoutfile, ff_, fmt='%.3f')