from util.myfun import *
from util.myfun_read_save import *
from kernel_RossLi import *
from util.drought_funs import *

from matplotlib.colors import LogNorm

'''基于widas的track-1数据，进行角度拟合'''

for ktrack in range(11,12):

    dic_ = ['cam01','cam01','cam01','cam01','cam02','cam02','cam02','cam02','cam02']
    off_ = ['a-05','a-10','a-15','a-20','a-25','a-30','a-35','a-40','a-45']
    # off_n = ['a-05.tif', 'a-10.tif', 'a-15.tif', 'a-20.tif', 'a-25.tif', 'a-30.tif', 'a-35.tif', 'a-40.tif', 'a-45.tif']
    track = 'track%d-1'%ktrack


    if ktrack == 8: continue
    if ktrack == 13:continue
    if (track =='track15-2') | (track =='track6-2'):
        track= track+'a'
    if (track =='track15-1') | (track =='track6-1'):
        track= track+'a'
    track_ = [track,track,track,track,'cam2'+track,'cam2'+track,'cam2'+track,'cam2'+track,'cam2'+track,'cam2'+track]

    print(track)
    tracknew = track
    offv = 'vinli7'
    outdir = r'E:\ship_lstndvi\widas_result\\'
    outfile_rmse = outdir+tracknew+'_rmse_'+offv+'.tif'
    outfile_std = outdir+tracknew+'_std_'+offv+'.tif'
    outfile_tvdi = outdir+tracknew+'_tvdi_'+offv+'.tif'
    outfile_tvdinew = outdir+tracknew+'_tvdinew_'+offv+'.tif'
    # outfile_pred = outdir+tracknew+'_pred_vinli1.tif'
    outfile_coeffs = outdir + tracknew+'_coeffs_'+offv+'.tif'
    outfile_pixel = outdir + tracknew+'_pixel_'+offv+'.tif'


    infile_tir0 = r'E:\ship_lstndvi\Cam01\\'+track+'_mosaic_TIR_atmcor.a+00'
    infile_vnir0 = r'E:\ship_lstndvi\Cam01\\'+track+'_mosaic_VNIR_atmcor.a+00'
    infile_angle0 = r'E:\ship_lstndvi\Cam01\\'+track+'_mosaic_angle.a+00'

    if os.path.exists(infile_tir0) == 0: continue
    numband = 10
    indir = r'E:\ship_lstndvi\\'

    [lst0, ns0, nl0, nb, geog, proj,dataset_tir0] = read_image_gdal_dataset(infile_tir0)
    lst0 = lst0/10.0

    dataset_vnir0= read_dataset_gdal(infile_vnir0)
    vnir = map2map(dataset_tir0, dataset_vnir0)
    # vnir = map2map_imagexy(dataset_tir0,dataset_tir0,dataset_vnir0)
    red0 = vnir[2, :, :]/10000.0
    nir0 = vnir[4, :, :]/10000.0
    redmax = np.max(red0[red0 < 1.0])
    nirmax = np.max(nir0[nir0 < 1.0])
    red0[red0 > 1.0] = redmax
    nir0[nir0 > 1.0] = nirmax
    ndvi0 = (nir0 - red0) / (nir0 + red0)
    ind = (nir0 < 0.18)
    ndvi0[ind] = 0
    ind = (red0 > 0.15)
    ndvi0[ind] = 0

    dataset_angle0 = read_dataset_gdal(infile_angle0)
    angle0 =  map2map(dataset_tir0,dataset_angle0)
    vza0 = angle0[0, :, :] / 100.0
    raa0 = np.abs(angle0[1, :, :] - angle0[3, :, :]) / 100.0
    sza0 = angle0[2, :, :] / 100.0

    lst_ = np.zeros([numband,nl0,ns0])
    ndvi_ = np.zeros([numband,nl0,ns0])
    red_ = np.zeros([numband,nl0,ns0])
    vza_ = np.zeros([numband,nl0,ns0])
    raa_ = np.zeros([numband,nl0,ns0])
    sza_ = np.zeros([numband,nl0,ns0])


    for kangle in range(numband-1):
        infile_tir =  indir+'\\'+dic_[kangle]+'\\'+track_[kangle]+'_mosaic_TIR_atmcor.'+off_[kangle]
        dataset_tir = read_dataset_gdal(infile_tir)
        lst = map2map(dataset_tir0,dataset_tir)
        lst = lst/10.0
        infile_vnir = indir+'\\'+dic_[kangle]+'\\'+track_[kangle]+'_mosaic_VNIR_atmcor.'+off_[kangle]
        dataset_vnir = read_dataset_gdal(infile_vnir)
        # vnir = map2map_imagexy(dataset_tir0,dataset_tir,dataset_vnir)
        vnir = map2map(dataset_tir0,dataset_vnir)
        red = vnir[2, :, :] / 10000.0
        nir = vnir[4, :, :] / 10000.0
        redmax = np.max(red[red < 1.0])
        nirmax = np.max(nir[nir < 1.0])
        red[red > 1.0] = redmax
        nir[nir > 1.0] = nirmax
        ndvi = (nir - red) / (nir + red)
        ind = (nir < 0.18)
        ndvi[ind] = 0
        ind = (red > 0.15)
        ndvi[ind] = 0

        infile_angle = indir + '\\' + dic_[kangle] + '\\' + track_[kangle] + '_mosaic_angle.' + off_[kangle]
        dataset_angle = read_dataset_gdal(infile_angle)
        angle = map2map(dataset_tir0, dataset_angle)

        if (track == 'track11-1') and (kangle == 8):
            sza_[kangle, :, :] = sza_[kangle - 1, :, :]
            raa_[kangle, :, :] = np.abs(angle[1, :, :]) / 100.0 - saa
        else:
            sza_[kangle, :, :] = angle[2, :, :] / 100.0
            saa = angle[3, :, :] / 100.0
            raa_[kangle, :, :] = np.abs(angle[1, :, :]) / 100.0 - saa

        vza_[kangle+1,:,:] = angle[0,:,:]/100.0
        raa_[kangle+1,:,:] = np.abs(angle[1,:,:]-angle[3,:,:])/100.0
        sza_[kangle+1,:,:] = angle[2,:,:]/100.0
        lst_[kangle+1,:,:] = lst
        ndvi_[kangle+1,:,:] = ndvi
        red_[kangle+1,:,:] = red

    lst_[0,:,:] = lst0
    ndvi_[0,:,:] = ndvi0
    vza_[0,:,:] = vza0
    raa_[0,:,:] = raa0
    sza_[0,:,:] = sza0
    red_[0,:,:] = red0


    lst = lst_ * 1.0
    ndvi = ndvi_ * 1.0
    red = red_ * 1.0
    ind = (~np.isnan(ndvi))*(~np.isnan(lst))*(ndvi>0.03)*(lst<335)*(ndvi<0.95)*(lst>290)*(red<0.15)*(red>0.001)
    ndvi = ndvi[ind]
    lst = lst[ind]
    red = red[ind]




    ### obtian a general result
    # ndvi_value_n, lstmax_value_n, fmax_n, lstmin_value_n, fmin_n = find_hot_cold_line(ndvi_n, lst_n)
    # ndvi_value_o, lstmax_value_o, fmax_o, lstmin_value_o, fmin_o = find_hot_cold_line(ndvi_o, lst_o)
    '''测试用，结果会导致TVDI值偏低'''
    # ndvi_value, lstmax_value, fmax, lstmin_value, fmin = find_hot_cold_line_5_percent(ndvi, lst)
    '''后缀3_2，极大的低估'''
    # ndvi_value, lstmax_value, fmax, lstmin_value, fmin = find_hot_cold_line_3_2(ndvi, lst)
    '''没有后缀是标准，p3是应用的拓展'''
    ndvi_value, lstmax_value, fmax, lstmin_value, fmin = find_hot_cold_line_3(ndvi, lst)
    # prob = 0.66
    # if fmin[0] > 10:
    #     fcenter = fmin[0] * prob + fmin[1]
    #     fmin[0] = 10
    #     fmin[1] = fcenter - fmin[0] * prob
    # if fmin[0] < -10:
    #     fcenter = fmin[0] * prob + fmin[1]
    #     fmin[0] = -10
    #     fmin[1] = fcenter - fmin[0] * prob
    # if fmax[0] > -15:
    #     fcenter = fmax[0] * prob + fmax[1]
    #     fmax[0] = -15
    #     fmax[1] = fcenter - fmax[0] * prob
    # maxdif = fmax[1] - 275
    # if fmax[0] < -maxdif:
    #     fcenter = fmax[0] * prob + fmax[1]
    #     fmax[0] = -maxdif
    #     fmax[1] = fcenter - fmax[0] * prob

    '''recalibrate the value'''
    # if fmax[0] > -15: fmax[0] = -15
    # if fmax[0] <-30: fmax[0] = -30
    # if fmax[1] < 320: fmax[1] = 320
    # if fmax[1] > 335: fmax[1] = 335
    # if fmin[0] > -2: fmin[0] = -2
    # if fmin[0] <-6: fmin[0] = -6
    # if fmin[1] < 297: fmin[1] = 297
    # if fmin[1] > 305: fmin[1] = 305


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

            ind = (~np.isnan(sza)) * (~np.isnan(vza)) * (~np.isnan(raa)) * (~np.isnan(tvdi)) * (tvdi > 0) * (tvdi < 1.0) *(ndvi>0.03)*(ndvi<0.95)*(sza<90)
            n_pixel[kl,ks] = np.sum(ind)
            if np.sum(ind) < 7: continue



            predicted, coeffs, std, rmse, newtvdi, maxdif = kernels_VinLi_ridge_sample(sza[ind], vza[ind], raa[ind], tvdi[ind])

            newtvdi_[ind,kl,ks] = newtvdi
            tvdi_std[kl,ks] = std
            tvdi_rmse[kl,ks] = rmse
            tvdi_pred[kl,ks] = predicted
            tvdi_coeffs[:, kl, ks] = coeffs


    # write_image_gdal(tvdi_pred,ns0,nl0,1,geog,proj,outfile_pred)
    write_image_gdal(tvdi_rmse,ns0,nl0,1,geog,proj,outfile_rmse)
    write_image_gdal(tvdi_std,ns0,nl0,1,geog,proj,outfile_std)
    write_image_gdal(tvdi_,ns0,nl0,numband,geog,proj,outfile_tvdi)
    write_image_gdal(newtvdi_,ns0,nl0,numband,geog,proj,outfile_tvdinew)
    write_image_gdal(tvdi_coeffs,ns0,nl0,numband,geog,proj,outfile_coeffs)
    write_image_gdal(n_pixel,ns0,nl0,1,geog,proj,outfile_pixel)

    ############################

    min1 = 0.0
    max1 = 1.0
    min2 = 290
    max2 = 335
    data1 = ndvi_
    data2 = lst_
    ind = (data1>0.03)*(data2>250)*(data2<335)*(data1<0.93)
    plt.hist2d(data1[ind], data2[ind], bins=100, norm=LogNorm(), cmap='jet')
    # plt.plot(ndvi_value,lstmax_value,'k+')
    plt.plot(ndvi_plt,lstmax_value_plt,'r-')
    # plt.plot(ndvi_value,lstmin_value,'k+')
    plt.plot(ndvi_plt,lstmin_value_plt,'k-')
    plt.text(0.1, 295,'$LST_{max}$ = %.2f'%fmax[0]+'*NDVI+%.2f'%fmax[1],color='r',fontsize = 10)
    plt.text(0.1, 292,'$LST_{min}$ = %.2f'%fmin[0]+'*NDVI+%.2f'%fmin[1],color='k',fontsize = 10)
    plt.xlim([min1, max1])
    plt.ylim([min2, max2])
    plt.xlabel(r'NDVI')
    plt.ylabel(r'LST (K)')
    plt.title('track%d'%ktrack)
    plt.colorbar()
    plt.show()
    #
    #
    # ############### scattering plot
    # ind = (newtvdi_ >0) *(tvdi_>0)*(np.abs(newtvdi_-tvdi_)<0.5)
    # data1 = tvdi_[ind]
    # data2 = newtvdi_[ind]
    # dif = data2-data1
    # rmse = np.sqrt(np.mean(dif * dif))
    # bias = np.mean(dif)
    # r = np.corrcoef(data1,data2)[1,0]
    # r2 = r*r
    # plt.figure(figsize=[4.5,3.6])
    # plt.hist2d(data1, data2, bins=100, norm=LogNorm(), cmap='jet')
    # plt.plot([0,1.5],[0,1.5],'k--')
    # plt.xlim([0,1.2])
    # plt.ylim([0,1.2])
    # plt.xlabel('Measured TVDI')
    # plt.ylabel('Simulated TVDI')
    # plt.text(0.7, 0.32,'RMSE = %2.3f' % rmse)
    # plt.text(0.7,0.24,'$R^2$ = %2.3f'%r2)
    # plt.text(0.7,0.16,'Bias = %2.3f'%bias)
    # cb=plt.colorbar()
    # # cb.set_label('SMC')
    # plt.show()
    #
    # #################### bar plot
    # ind = (tvdi_std > 0) * (tvdi_rmse>0)
    # data1 = tvdi_std[ind]
    # data2 = tvdi_rmse[ind]
    # data = np.stack([data1,data2])
    # data =np.transpose(data)
    # bins = np.arange(0, 0.24, 0.03)
    # fig, ax = plt.subplots(figsize=[5.5,4.6])
    # p=ax.hist(data,bins=bins,histtype="bar", rwidth=0.75, alpha=0.6)
    # ax.set_xlabel("Difference")
    # ax.set_ylabel("Count")
    # # ax.xaxis.get_major_formatter().set_powerlimits((0,1)) # 将坐标轴的base number设置为一位。
    # ax.yaxis.get_major_formatter().set_powerlimits((0,1)) # 将坐标轴的base number设置为一位。
    # plt.legend(['STD','RMSE'])
    # plt.show()



    # data1 = tvdi_std[1100:1200,:]
    # data2 = tvdi_rmse[1100:1200,:]
    # plt.figure()
    # plt.imshow(data1,vmin = 0,vmax = 0.25,cmap='jet')
    # cb = plt.colorbar()
    # cb.set_label('$TVDI_std{50}$')
    # plt.show()
    # plt.figure()
    # plt.imshow(data2,vmin = 0,vmax = 0.25,cmap='jet')
    # cb = plt.colorbar()
    # cb.set_label('$TVDI_rmse$')
    # plt.show()
