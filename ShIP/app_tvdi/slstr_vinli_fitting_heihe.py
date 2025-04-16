from util.drought_funs import *
from inversion_tvdi.kdinversion import *

'''生成的SLSTR tvdi进行拟合'''


indir_lst_3a = r'E:\SLSTR_heihe\s3a\lst\\'
indir_tif_3a = r'E:\SLSTR_heihe\s3a\tif\\'
indir_tvdi_3a = r'E:\SLSTR_heihe\s3a\tvdi\\'

indir_lst_3b = r'E:\SLSTR_heihe\s3b\lst\\'
indir_tif_3b = r'E:\SLSTR_heihe\s3b\tif\\'
indir_tvdi_3b = r'E:\SLSTR_heihe\s3b\tvdi\\'

outdir_tvdi = r'E:\SLSTR_Heihe\tvdi\\'

indir_site = r'E:\field\\'


infile_site_geo = r'E:\field\Heihe_Site_2019.txt'
tempdata = read_txt_str(infile_site_geo,',')
lon = [np.float(tempdata[i][1]) for i in range(np.shape(tempdata)[0])]
lat = [np.float(tempdata[i][2]) for i in range(np.shape(tempdata)[0])]

#获得经纬度
infile_dem = r'E:\type\type_heihe_1000.tif'
dem, ns, nl, nb, geog, proj,dataset = read_image_dataset_gdal(infile_dem)
imagex,imagey = loc2map(lat,lon,dataset)

doyoff = 4
n_avail = 2
n_pixel = 1
n_pos = 6
layerthred = 4
n_layer = (doyoff*2+1)*4

for kdoy in range(150,311):
    the_layer = 0

    obss = np.zeros([n_layer, nl, ns])
    vzas = np.zeros([n_layer, nl, ns])
    szas = np.zeros([n_layer, nl, ns])
    raas = np.zeros([n_layer, nl, ns])
    clouds = np.zeros([n_layer, nl, ns])
    coeffs = np.zeros([3, nl, ns])

    ifok = 0
    for kdoynew in range(kdoy-doyoff,kdoy+doyoff+1):

        sensor = 's3a'
        angle = 'nadir'
        indir_tvdi = indir_tvdi_3a
        indir_tif = indir_tif_3a
        infile_tvdi = indir_tvdi + sensor + '_2019%03d'%kdoynew + '_day_tvdi_'+sensor+'_' + angle +'.tif'
        infile_sza = indir_tif + sensor + '_2019%03d'%kdoynew + '_day_sza_'+ angle +'.tif'
        infile_saa = indir_tif + sensor + '_2019%03d'%kdoynew + '_day_saa_'+ angle +'.tif'
        infile_vza = indir_tif + sensor + '_2019%03d'%kdoynew + '_day_vza_'+ angle +'.tif'
        infile_vaa = indir_tif + sensor + '_2019%03d'%kdoynew + '_day_vaa_'+ angle +'.tif'
        infile_cloud = indir_tif + sensor + '_2019%03d'%kdoynew + '_day_cloud_'+ angle +'.tif'
        if os.path.exists(infile_tvdi) != 0:
            tvdi, ns, nl, nb, geog, proj = read_image_gdal(infile_tvdi)
            sza, ns, nl, nb, geog, proj = read_image_gdal(infile_sza)
            saa, ns, nl, nb, geog, proj = read_image_gdal(infile_saa)
            vza, ns, nl, nb, geog, proj = read_image_gdal(infile_vza)
            vaa, ns, nl, nb, geog, proj = read_image_gdal(infile_vaa)
            cloud, ns1, nl1, nb, geog, proj = read_image_gdal(infile_cloud)
            raa = np.abs(saa - vaa + 360) % 360
            clouds[the_layer, :] = cloud
            obss[the_layer, :] = tvdi
            szas[the_layer, :] = sza
            vzas[the_layer, :] = vza
            raas[the_layer, :] = raa
            the_layer = the_layer + 1
            if kdoynew == kdoy:
                ifok = 1

        sensor = 's3a'
        angle = 'obliq'
        indir_tvdi = indir_tvdi_3a
        indir_tif = indir_tif_3a
        infile_tvdi = indir_tvdi + sensor + '_2019%03d' % kdoynew + '_day_tvdi_' + sensor + '_' + angle + '.tif'
        infile_sza = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_sza_' + angle + '.tif'
        infile_saa = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_saa_' + angle + '.tif'
        infile_vza = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_vza_' + angle + '.tif'
        infile_vaa = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_vaa_' + angle + '.tif'
        infile_cloud = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_cloud_' + angle + '.tif'
        if os.path.exists(infile_tvdi) != 0:
            tvdi, ns, nl, nb, geog, proj = read_image_gdal(infile_tvdi)
            sza, ns, nl, nb, geog, proj = read_image_gdal(infile_sza)
            saa, ns, nl, nb, geog, proj = read_image_gdal(infile_saa)
            vza, ns, nl, nb, geog, proj = read_image_gdal(infile_vza)
            vaa, ns, nl, nb, geog, proj = read_image_gdal(infile_vaa)
            cloud, ns1, nl1, nb, geog, proj = read_image_gdal(infile_cloud)
            raa = np.abs(saa - vaa + 360) % 360
            clouds[the_layer, :] = cloud
            obss[the_layer, :] = tvdi
            szas[the_layer, :] = sza
            vzas[the_layer, :] = vza
            raas[the_layer, :] = raa
            the_layer = the_layer + 1
            # if kdoynew == kdoy: ifok = 1

        sensor = 's3b'
        angle = 'nadir'
        indir_tvdi = indir_tvdi_3b
        indir_tif = indir_tif_3b
        infile_tvdi = indir_tvdi + sensor + '_2019%03d' % kdoynew + '_day_tvdi_' + sensor + '_' + angle + '.tif'
        infile_sza = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_sza_' + angle + '.tif'
        infile_saa = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_saa_' + angle + '.tif'
        infile_vza = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_vza_' + angle + '.tif'
        infile_vaa = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_vaa_' + angle + '.tif'
        infile_cloud = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_cloud_' + angle + '.tif'
        if os.path.exists(infile_tvdi) != 0:
            tvdi, ns, nl, nb, geog, proj = read_image_gdal(infile_tvdi)
            sza, ns, nl, nb, geog, proj = read_image_gdal(infile_sza)
            saa, ns, nl, nb, geog, proj = read_image_gdal(infile_saa)
            vza, ns, nl, nb, geog, proj = read_image_gdal(infile_vza)
            vaa, ns, nl, nb, geog, proj = read_image_gdal(infile_vaa)
            cloud, ns1, nl1, nb, geog, proj = read_image_gdal(infile_cloud)
            raa = np.abs(saa - vaa + 360) % 360
            clouds[the_layer, :] = cloud
            obss[the_layer, :] = tvdi
            szas[the_layer, :] = sza
            vzas[the_layer, :] = vza
            raas[the_layer, :] = raa
            the_layer = the_layer + 1
            if kdoynew == kdoy: ifok = 1

        sensor = 's3b'
        angle = 'obliq'
        indir_tvdi = indir_tvdi_3b
        indir_tif = indir_tif_3b
        infile_tvdi = indir_tvdi + sensor + '_2019%03d' % kdoynew + '_day_tvdi_' + sensor + '_' + angle + '.tif'
        infile_sza = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_sza_' + angle + '.tif'
        infile_saa = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_saa_' + angle + '.tif'
        infile_vza = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_vza_' + angle + '.tif'
        infile_vaa = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_vaa_' + angle + '.tif'
        infile_cloud = indir_tif + sensor + '_2019%03d' % kdoynew + '_day_cloud_' + angle + '.tif'
        if os.path.exists(infile_tvdi) != 0:
            tvdi, ns, nl, nb, geog, proj = read_image_gdal(infile_tvdi)
            sza, ns, nl, nb, geog, proj = read_image_gdal(infile_sza)
            saa, ns, nl, nb, geog, proj = read_image_gdal(infile_saa)
            vza, ns, nl, nb, geog, proj = read_image_gdal(infile_vza)
            vaa, ns, nl, nb, geog, proj = read_image_gdal(infile_vaa)
            cloud, ns1, nl1, nb, geog, proj = read_image_gdal(infile_cloud)
            raa = np.abs(saa - vaa + 360) % 360
            clouds[the_layer, :] = cloud
            obss[the_layer, :] = tvdi
            szas[the_layer, :] = sza
            vzas[the_layer, :] = vza
            raas[the_layer, :] = raa
            the_layer = the_layer + 1
            # if kdoynew == kdoy: ifok = 1



    if the_layer < layerthred: continue
    if ifok == 0: continue

    for kpos in range(6):
        # if kpos ==0: continue
        # if kpos > 2: continue

        x = imagex[kpos]
        y = imagey[kpos]
        for kl in range(x - n_avail, x + n_avail + 1):
            for ks in range(y - n_avail, y + n_avail + 1):
                cloud = clouds[:, kl - n_pixel:kl + n_pixel + 1, ks - n_pixel:ks + n_pixel + 1]
                obs = obss[:, kl - n_pixel:kl + n_pixel + 1, ks - n_pixel:ks + n_pixel + 1]
                vza = vzas[:, kl - n_pixel:kl + n_pixel + 1, ks - n_pixel:ks + n_pixel + 1]
                sza = szas[:, kl - n_pixel:kl + n_pixel + 1, ks - n_pixel:ks + n_pixel + 1]
                raa = raas[:, kl - n_pixel:kl + n_pixel + 1, ks - n_pixel:ks + n_pixel + 1]

                ind = (obs > 0.05) * (obs < 1.05)
                if np.sum(ind) < 6: continue
                vza = vza[ind]
                sza = sza[ind]
                raa = raa[ind]
                obs = obs[ind]

                temp = fitting_VinLiDense_ridge(obs, vza, sza, raa,0.01)
                coeffs[0, kl, ks] = temp[0]
                coeffs[1, kl, ks] = temp[1]
                coeffs[2, kl, ks] = temp[2]
                # coeffs[3,kl,ks] = temp[3]

    outfile_coeff = outdir_tvdi + '2019%03d'%kdoy + '_coeffs_vinli.tif'
    print(outfile_coeff)
    if np.sum(coeffs) < 1:continue
    # outfile_tvdi = outdir_tvdi + '//AHI_%04d'%kyear+'%03d'%kdoy + '_%02d'%khour+'%02d'%kmin+'_tvdi.tif'
    write_image_gdal(coeffs, ns, nl, 3, '', '', outfile_coeff)