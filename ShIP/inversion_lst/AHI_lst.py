from util.util import *
'''
AHI结果
AHI的每十分钟数据进行的LST计算，全年数据
'''

os.environ['PROJ_LIB'] = r'C:\ProgramData\Anaconda3\envs\python37\Library\share\proj'
############################
### functions
##############################

ndvi_min = 0.05
ndvi_max = 0.95

indir_tif0 = r'N:\ahi_tif\\'
outdir_lst0 = r'N:\ahi_lst_fvc_ahi\\'

indir_emis = r'd:\data\emis\\'
indir_fvc = r'D:\data\fvc\fvc_china\fvc_china_ahi//'
indir_type =r'd:\data\type\\'
indir_split = r'd:\data\split\\'
indir_map = r'd:\data\map\\'

infile10 = indir_emis + 'emis1_geo.tif'
infile11 = indir_emis + 'emis2_geo.tif'
infile13 = indir_emis + r'IGBP_Emi.txt'
infile12 = indir_type + 'type_China_2000.tif'
infile14 = indir_split + 'Himawari8_AHI_SW_Seebor_Coef_Day.txt'
infile15 = indir_split + 'Himawari8_AHI_SW_Seebor_Coef_Night.txt'

# indir_tif0 = r'd:\data\ahi_tif_heihe\\'
# indir_lst0 = r'D:\mydata\ahi_lst_heihe\\'
#
# indir_emis = r'd:\data\emis\\'
# indir_fvc = r'D:\data\fvc\fvc_heihe_ahi//'
# indir_type =r'd:\data\type\\'
# indir_split = r'd:\data\split\\'
# indir_map = r'd:\data\map\\'
#
# infile10 = indir_emis + 'emis1_geo_heihe.tif'
# infile11 = indir_emis + 'emis2_geo_heihe.tif'
# infile13 = indir_emis + r'IGBP_Emi.txt'
# infile12 = indir_type + 'type_heihe_2000.tif'
# infile14 = indir_split + 'Himawari8_AHI_SW_Seebor_Coef_Day.txt'
# infile15 = indir_split + 'Himawari8_AHI_SW_Seebor_Coef_Night.txt'

coeffs_day = read_txt_array(infile14, 0, 15)
coeffs_day = coeffs_day[:, 2:10]
coeffs_night = read_txt_array(infile15, 0, 15)
coeffs_night = coeffs_night[:, 2:10]

[emis1_s, ns, nl, nb, geog, proj] = read_image_gdal(infile10)
emis1_s = emis1_s / 1000.0
[emis2_s, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile11)
emis2_s = emis2_s / 1000.0
[classif, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile12)
classif = np.asarray(classif, np.int)
emis_v = read_txt_array(infile13, 0, 2)

for kmonth in range(3,13):
    for kday in range(1,32):

        indir_tif = indir_tif0 + '%02d/'%kmonth+'%02d/'%kday
        outdir_lst = outdir_lst0 + '%02d/' % kmonth + '%02d/' % kday

        fileNames = search_file(indir_tif, ['bt1'])
        fileNum = np.size(fileNames)
        off = 7
        infile8 = indir_map + 'ahi_vza_china.tif'
        pre_str = ''
        [vza, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile8)

        if fileNum ==0:continue

        for k in range(fileNum):
            fileName = fileNames[k]
            print(k,fileName)
            date_str = fileName[4:11]
            time_str = fileName[12:16]

            doy_str = fileName[8:11]
            doy = np.int(doy_str)


            if doy_str != pre_str:
                infile10 = indir_fvc + '2019_doy'+doy_str+'_fvc.tif'
                if os.path.exists(infile10) == 0:
                    continue
                [fvc, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile10)
                fvc = resize_data(fvc,nl,ns,method=cv2.INTER_NEAREST)



            hh = np.int(time_str[:2])
            infile1 = indir_tif + fileName[:-off] + 'bt1.tif'
            infile2 = indir_tif + fileName[:-off] + 'bt2.tif'
            infile5 = indir_tif + fileName[:-off] + 'tcw.tif'

            outfile = outdir_lst + fileName[:-off] + 'lst.tif'

            if os.path.exists(outfile) == 1:
                print('file exists')
                continue

            if os.path.exists(infile1) * os.path.exists(infile2) * os.path.exists(infile5) == 0:
                print('missing data')
                continue

            [BT8, ns, nl, nb, geog, proj] = read_image_gdal(infile1)
            [BT9, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile2)
            [tcw, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile5)
            tcw = resize_data(tcw,nl,ns)

            # if hh > 22 or hh < 11:
            #     # infile3 = indir_tif + fileName[:-off] + 'red.tif'
            #     # infile4 = indir_tif + fileName[:-off] + 'nir.tif'
            #     # [red, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile3)
            #     # [nir, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile4)
            #     # ndvi = (nir-red)/(nir+red)
            #     #infile9 = indir_ndvi + 'NDVI_' + date_str + '.tif'
            #     infile9 = indir_tif + fileName[:-off] + 'ndvi.tif'
            #     [ndvi, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile9)
            # else:
            #     continue
            #     infile9 = indir_ndvi + 'NDVI_' + date_str + '.tif'
            #     [ndvi, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile9)
            ind0 = (classif < 17) *(classif > 0)


            tcw = tcw/10.0
            # fvc = (ndvi - ndvi_min) / (ndvi_max - ndvi_min)
            # fvc = resize_data_ls(fvc, nl, ns)
            fvc[fvc > 1] = 1
            fvc[fvc < 0] = 0

            emis1_v = emis_v[classif, 0] / 1000.0
            emis2_v = emis_v[classif, 1] / 1000.0
            emis1_v = np.reshape(emis1_v, [nl, ns])
            emis2_v = np.reshape(emis2_v, [nl, ns])

            emis8 = emis1_s*(1-fvc) + emis1_v*fvc
            emis9 = emis2_s*(1-fvc) + emis2_v*fvc

            emis = (emis8 + emis9) * 0.5
            demis = emis8 - emis9
            x3 = np.zeros([nl, ns])
            x4 = np.zeros([nl, ns])
            x6 = np.zeros([nl, ns])
            x7 = np.zeros([nl, ns])
            x1 = 1
            x2 = (BT8 + BT9) / 2.0
            ind = emis != 0
            x3[ind] = (1 - emis[ind]) / emis[ind] * x2[ind]
            x4[ind] = demis[ind] / (emis[ind] * emis[ind]) * x2[ind]
            x5 = (BT8 - BT9) / 2
            x6[ind] = (1 - emis[ind]) / emis[ind] * x5[ind]
            x7[ind] = demis[ind] / (emis[ind] * emis[ind]) * x5[ind]
            x8 = (BT8 - BT9) * (BT8 - BT9)

            wvc_ = np.asarray([0, 1.25, 2.25, 3.25, 4.25, 5.25, 100])
            vza_ = np.asarray([0, 3, 14.9, 38.6, 44.5, 51.2, 58, 65, 70, 75, 80])

            LST = np.zeros([nl, ns])
            for kwvc in range(len(wvc_) - 1):
                for kvza in range(len(vza_) - 1):

                    ind = (tcw >= wvc_[kwvc]) * (tcw < wvc_[kwvc + 1]) * (vza >= vza_[kvza]) * (vza < vza_[kvza + 1]) * (BT8 > 0) * (emis8 > 0)*ind0
                    if (np.sum(ind) <= 0): continue

                    ##########################################
                    ### the normal result
                    ##########################################

                    ind1 = kvza * 6 + kwvc
                    ind2 = (kvza + 1) * 6 + kwvc
                    coeff1 = coeffs_day[ind1, :]
                    coeff2 = coeffs_day[ind2, :]
                    vzatemp = vza[ind]
                    prop2 = (vzatemp - vza_[kvza]) / (vza_[kvza + 1] - vza_[kvza])
                    prop1 = 1 - prop2
                    LSTtemp = x1 * (prop1 * coeff1[0] + coeff2[0] * prop2) + x2[ind] * (
                            prop1 * coeff1[1] + coeff2[1] * prop2) + \
                              x3[ind] * (prop1 * coeff1[2] + coeff2[2] * prop2) + x4[ind] * (
                                      prop1 * coeff1[3] + coeff2[3] * prop2) + \
                              x5[ind] * (prop1 * coeff1[4] + coeff2[4] * prop2) + x6[ind] * (
                                      prop1 * coeff1[5] + coeff2[5] * prop2) + \
                              x7[ind] * (prop1 * coeff1[6] + coeff2[6] * prop2) + x8[ind] * (
                                      prop1 * coeff1[7] + coeff2[7] * prop2)

                    LST[ind] = LSTtemp


            ind = LST > 365
            LST[ind] = 365
            ind = LST < 225
            LST[ind] = 0
            outfile = outdir_lst + fileName[:-off] + 'lst.tif'
            write_image_gdal(LST, ns, nl, 1, geog, proj, outfile)

