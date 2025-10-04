from myfun_map import *
from myfun_sci import *
from kernel_RossLi_mv import *
from matplotlib.colors import LogNorm

'''基于widas的track-1和track-2数据，进行角度拟合'''

for ktrack in range(11,12):

    if ktrack == 8: continue
    dic_ = ['cam02','cam02','cam02','cam01','cam01','cam01','cam01','cam02','cam02','cam02']
    off_ = ['a+45','a+40','a+30','a+20','a+10','a-10','a-20','a-30','a-40','a-45']
    track2 = 'track%d-2'%ktrack
    track1 = 'track%d-1'%ktrack
    tracknew = 'track%d'%ktrack
    print(tracknew)

    if ktrack == 8: continue
    if (track2 =='track15-2') | (track2 =='track6-2'):
        track1= track1+'a'

    track_ = ['cam2' + track2, 'cam2' + track2, 'cam2' + track2,track2, track2,
              track1, track1,'cam2' + track1, 'cam2' + track1, 'cam2' + track1 ]

    infile_tir0 = r'E:\lstndvi\Cam01\\' + track1 + '_mosaic_TIR_atmcor.a+00'
    infile_vnir0 = r'E:\lstndvi\Cam01\\' + track1 + '_mosaic_VNIR_atmcor.a+00'
    infile_angle0 = r'E:\lstndvi\Cam01\\' + track1 + '_mosaic_angle.a+00'
    numband = 11
    if os.path.exists(infile_tir0) == 0: continue

    outdir = r'E:\lstndvi\widas_result\\'
    outfile_rmse = outdir+tracknew+'_rmse_vinli12.tif'
    outfile_std = outdir+tracknew+'_std_vinli12.tif'
    outfile_tvdi = outdir+tracknew+'_tvdi12.tif'
    outfile_tvdinew = outdir+tracknew+'_tvdinew_vinli12.tif'
    outfile_pred = outdir+tracknew+'_pred_vinli12.tif'
    outfile_coeffs = outdir + tracknew+'_coeffs_vinli12.tif'
    outfile_pixel = outdir + tracknew+'_pixel_vinli12.tif'

    indir = r'E:\lstndvi\\'

    [lst0, ns0, nl0, nb, geog, proj,dataset_tir0] = read_image_gdal_dataset(infile_tir0)
    lst0 = lst0/10.0

    dataset_vnir0 = read_dataset_gdal(infile_vnir0)
    vnir = map2map(dataset_tir0,dataset_vnir0)
    red0 = vnir[2, :, :]/10000.0
    nir0 = vnir[4, :, :]/10000.0
    redmax = np.max(red0[red0 < 0.3])
    nirmax = np.max(nir0[nir0 < 0.5])
    red0[red0 > 0.3] = redmax
    nir0[nir0 > 0.5] = nirmax
    ndvi0 = (nir0 - red0) / (nir0 + red0)
    ind = (nir0 < 0.15)
    ndvi0[ind] = 0
    ind = (red0 > 0.25)
    ndvi0[ind] = 0

    dataset_angle0 = read_dataset_gdal(infile_angle0)
    angle0 =  map2map(dataset_tir0,dataset_angle0)
    vza0 = angle0[0, :, :] / 100.0
    raa0 = np.abs(angle0[1, :, :] - angle0[3, :, :]) / 100.0
    sza0 = angle0[2, :, :] / 100.0

    lst_ = np.zeros([numband,nl0,ns0])
    ndvi_ = np.zeros([numband,nl0,ns0])
    vza_ = np.zeros([numband,nl0,ns0])
    raa_ = np.zeros([numband,nl0,ns0])
    sza_ = np.zeros([numband,nl0,ns0])
    red_ = np.zeros([numband,nl0,ns0])

    for kangle0 in range(numband-1):

        kangle = kangle0*1.0
        if kangle0 > 4: kangle = kangle0 + 1
        kangle = np.int(kangle)

        infile_tir =  indir+'\\'+dic_[kangle0]+'\\'+track_[kangle0]+'_mosaic_TIR_atmcor.'+off_[kangle0]
        dataset_tir = read_dataset_gdal(infile_tir)
        lst = map2map(dataset_tir0,dataset_tir)
        lst = lst/10.0
        infile_vnir = indir+'\\'+dic_[kangle0]+'\\'+track_[kangle0]+'_mosaic_VNIR_atmcor.'+off_[kangle0]
        dataset_vnir = read_dataset_gdal(infile_vnir)
        vnir = map2map(dataset_tir0,dataset_vnir)

        red = vnir[2, :, :] / 10000.0
        nir = vnir[4, :, :] / 10000.0
        redmax = np.max(red[red < 0.3])
        nirmax = np.max(nir[nir < 0.5])
        red[red > 0.3] = redmax
        nir[nir > 0.5] = nirmax
        ndvi = (nir - red) / (nir + red)
        ind = (nir < 0.15)
        ndvi[ind] = 0
        ind = (red > 0.25)
        ndvi[ind] = 0


        infile_angle = indir + '\\' + dic_[kangle0] + '\\' + track_[kangle0] + '_mosaic_angle.' + off_[kangle0]
        dataset_angle = read_dataset_gdal(infile_angle)
        angle = map2map(dataset_tir0, dataset_angle)

        if (ktrack == 11) and (kangle==10):
            sza_[kangle,:,:] = sza_[kangle-1,:,:]
            raa_[kangle,:,:] = np.abs(angle[1,:,:])/100.0-saa
        else:
            sza_[kangle, :, :] = angle[2, :, :] / 100.0
            saa = angle[3,:,:]/100.0
            raa_[kangle, :, :] = np.abs(angle[1, :, :]) / 100.0 - saa

        vza_[kangle,:,:] = angle[0,:,:]/100.0
        lst_[kangle,:,:] = lst
        ndvi_[kangle,:,:] = ndvi
        red_[kangle,:,:] = red


    lst_[5,:,:] = lst0
    ndvi_[5,:,:] = ndvi0
    vza_[5,:,:] = vza0
    raa_[5,:,:] = raa0
    sza_[5,:,:] = sza0
    red_[5,:,:] = red0

    lst = lst_
    ndvi = ndvi_
    red = red_
    ind = (~np.isnan(ndvi))*(~np.isnan(lst))
    ndvi = ndvi[ind]
    lst = lst[ind]
    red = red[ind]
    ind = (ndvi>0.03)*(lst<335)*(ndvi<0.95)*(lst>290)*(red<0.15)*(red>0.001)
    ndvi = ndvi[ind]
    lst = lst[ind]



    ### obtian a general result

    # ndvi_value_n, lstmax_value_n, fmax_n, lstmin_value_n, fmin_n = find_hot_cold_line(ndvi_n, lst_n)
    # ndvi_value_o, lstmax_value_o, fmax_o, lstmin_value_o, fmin_o = find_hot_cold_line(ndvi_o, lst_o)
    ndvi_value, lstmax_value, fmax, lstmin_value, fmin = find_hot_cold_line_5_percent(ndvi_, lst_)


    ndvi_plt = [0,1]
    lstmax_value_plt = np.polyval(fmax,ndvi_plt)
    lstmin_value_plt = np.polyval(fmin,ndvi_plt)
    # Tsmin = np.average(lstmin_value_plt)
    Tsmin = np.polyval(fmin,ndvi_)
    Tsmax = np.polyval(fmax,ndvi_)
    tvdi_ = (lst_-Tsmin)/(Tsmax-Tsmin)

    newtvdi_ = np.zeros([numband,nl0,ns0])-1
    tvdi_std = np.zeros([nl0,ns0])
    tvdi_rmse = np.zeros([nl0,ns0])
    tvdi_pred = np.zeros([nl0,ns0])
    tvdi_coeffs = np.zeros([3,nl0,ns0])
    n_pixel = np.zeros([nl0, ns0])

    for kl in range(nl0):
        for ks in range(ns0):


            sza = sza_[:,kl,ks]
            vza = vza_[:,kl,ks]
            raa = raa_[:,kl,ks]
            tvdi = tvdi_[:,kl,ks]
            ndvi = ndvi_[:,kl,ks]

            ind = (~np.isnan(sza))*(~np.isnan(vza))*(~np.isnan(raa))*(~np.isnan(tvdi))*(tvdi>0)*(tvdi<1.0)*(ndvi>0.03)*(ndvi<1.0)
            n_pixel[kl,ks] = np.sum(ind)
            if np.sum(ind) < numband-3: continue

            predicted, coeffs, std, rmse, newtvdi, maxdif = kernels_LSFLI_mv(sza[ind], vza[ind], raa[ind], tvdi[ind])
            newtvdi_[ind,kl,ks] = newtvdi
            tvdi_std[kl,ks] = std
            tvdi_rmse[kl,ks] = rmse
            tvdi_pred[kl,ks] = predicted
            tvdi_coeffs[:, kl, ks] = coeffs



    write_image_gdal(tvdi_pred,ns0,nl0,1,geog,proj,outfile_pred)
    write_image_gdal(tvdi_rmse,ns0,nl0,1,geog,proj,outfile_rmse)
    write_image_gdal(tvdi_std,ns0,nl0,1,geog,proj,outfile_std)
    write_image_gdal(tvdi_,ns0,nl0,numband,geog,proj,outfile_tvdi)
    write_image_gdal(newtvdi_,ns0,nl0,numband,geog,proj,outfile_tvdinew)
    write_image_gdal(tvdi_coeffs,ns0,nl0,numband,geog,proj,outfile_coeffs)
    write_image_gdal(n_pixel,ns0,nl0,1,geog,proj,outfile_pixel)


    ind = (tvdi_ > 0)*(newtvdi_ > 0)*(tvdi_<1)*(newtvdi_<1)
    plt.hist2d(tvdi_[ind], newtvdi_[ind], bins=60, norm=LogNorm(), cmap='jet')
    plt.colorbar()
    plt.show()



    data1 = tvdi_std[1100:1200,:]
    data2 = tvdi_rmse[1100:1200,:]

    plt.figure()
    plt.imshow(data1,vmin = 0,vmax = 0.25,cmap='jet')
    cb = plt.colorbar()
    cb.set_label('$TVDI_std{50}$')
    plt.show()


    plt.figure()
    plt.imshow(data2,vmin = 0,vmax = 0.25,cmap='jet')
    cb = plt.colorbar()
    cb.set_label('$TVDI_rmse$')
    plt.show()


    ind = (tvdi_std > 0) * (tvdi_rmse>0)
    data1 = tvdi_std[ind]
    data2 = tvdi_rmse[ind]
    data = np.stack([data1,data2])
    data =np.transpose(data)
    bins = np.arange(0, 0.4, 0.03)
    plt.hist(data, bins=bins, histtype="bar", rwidth=0.75, alpha=0.6)
    plt.xlabel("Difference")
    plt.ylabel("Frequency")
    plt.legend(['STD','RMSE'])
    plt.show()


    ind = (newtvdi_ >0) *(tvdi_>0)*(np.abs(newtvdi_-tvdi_)<0.5)
    data1 = tvdi_[ind]
    data2 = newtvdi_[ind]
    dif = data2-data1
    rmse = np.sqrt(np.mean(dif * dif))
    bias = np.mean(dif)
    r = np.corrcoef(data1,data2)[1,0]
    r2 = r*r
    plt.figure(figsize=[4.5,3.6])
    plt.hist2d(data1, data2, bins=100, norm=LogNorm(), cmap='jet')
    plt.plot([0,1.5],[0,1.5],'k--')
    plt.xlim([0,1.2])
    plt.ylim([0,1.2])
    plt.xlabel('Measured TVDI')
    plt.ylabel('Simulated TVDI')
    plt.text(0.7, 0.32,'RMSE = %2.3f' % rmse)
    plt.text(0.7,0.24,'$R^2$ = %2.3f'%r2)
    plt.text(0.7,0.16,'Bias = %2.3f'%bias)
    cb=plt.colorbar()
    # cb.set_label('SMC')
    plt.show()
