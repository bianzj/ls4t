from util.util import *

'''根据slstr的观测时间，查找AHI对应时刻的观测数据，十分钟内的内插'''
'''slstr时间分辨率为1天，AHI为10min'''

indir_slstr_lst = r'd:\data\S3a_lst_heihe\\'
indir_slstr_tif = r'd:\data\S3a_tif_heihe\\'
indir_ahi_lst0 = r'd:\data\ahi_lst_heihe\\'
indir_ahi_tif0 = r'd:\data\ahi_tif_heihe\\'
outdir_lst = r'd:\\data\S3a_lst_heihe_AHI\\'
outdir_tif = r'd:\\data\S3a_tif_heihe_AHI\\'

fileNames = search_file_rej(indir_slstr_tif, ['day','time'],'obliq')
fileNum = np.size(fileNames)


for k in range(0,fileNum):
    kneed = 0

    print(fileNames[k])
    fileName = fileNames[k]
    doy_str = fileName[8:11]
    doy = np.int(doy_str)
    infile = indir_slstr_tif+fileName
    [passtime,ns,nl,nb,geog,proj] = read_image_gdal(infile)

    ns = np.int32(ns/2)
    nl = np.int32(nl/2)
    passtime = resize_data(passtime,nl,ns,method=cv2.INTER_NEAREST)

    passtime_unique = np.unique(passtime)

    outfile1 = outdir_lst + 'S3A_2019'  + doy_str + '_day_lst.tif'
    outfile3 = outdir_tif + 'S3A_2019'  + doy_str + '_day_red.tif'
    outfile4 = outdir_tif + 'S3A_2019'  + doy_str + '_day_nir.tif'

    if os.path.exists(outfile1) == 1:
        continue
    else:
        data1 = np.zeros([nl, ns])
        data3 = np.zeros([nl, ns])
        data4 = np.zeros([nl, ns])

    for kk in range(len(passtime_unique)):
        passtime_one = passtime_unique[kk]
        if passtime_one ==0: continue
        hh = passtime_one//10000
        m = ((passtime_one//1000) % 10)
        mm = (passtime_one//100) % 10
        mm_prop = mm/10.0
        hh_str1 = "%02d"%hh
        mm_str1 = "%02d"%(m*10)
        doy_str1 = "%03d"%doy
        hh_str2 = "%02d"%hh
        mm_str2 = "%02d"%((m+1)*10)
        doy_str2 = "%03d"%doy

        if m == 5:
            mm_str2 = "00"
            hh_str2 = "%02d"%(hh+1)
            if hh == 23:
                hh_str2 = "00"
                doy_str2 = "%03d"%(doy+1)

        year_str1 = '2019'
        year_str2 = '2019'
        name1 = "AHI_"+year_str1+doy_str1+"_"+hh_str1+mm_str1
        name2 = "AHI_"+year_str2+doy_str2+"_"+hh_str2+mm_str2
        print(name1)
        print(name2)


        kmonth,kday = doy2date(2019,np.int(doy_str1))
        indir_ahi_lst1 = indir_ahi_lst0 + '/%02d' % kmonth + '/%02d' % kday + '/'
        indir_ahi_tif1 = indir_ahi_tif0 + '/%02d' % kmonth + '/%02d' % kday + '/'

        infile1 = indir_ahi_lst1+name1+'_lst.tif'
        infile3 = indir_ahi_tif1+name1+'_red.tif'
        infile4 = indir_ahi_tif1+name1+'_nir.tif'

        kmonth,kday = doy2date(2019,np.int(doy_str2))
        indir_ahi_lst2 = indir_ahi_lst0 + '/%02d' % kmonth + '/%02d' % kday + '/'
        indir_ahi_tif2 = indir_ahi_tif0 + '/%02d' % kmonth + '/%02d' % kday + '/'
        infile8 = indir_ahi_lst2+name2+'_lst.tif'
        infile10 = indir_ahi_tif2+name2+'_red.tif'
        infile11 = indir_ahi_tif2+name2+'_nir.tif'


        if os.path.exists(infile1) == 0:continue
        if os.path.exists(infile3) == 0: continue
        if os.path.exists(infile4) == 0: continue
        if os.path.exists(infile8) == 0: continue
        if os.path.exists(infile10) == 0: continue
        if os.path.exists(infile11) == 0: continue

        kneed = 1

        ind = (passtime == passtime_one)
        [temp1,ns,nl,nb,geog,proj] = read_image_gdal(infile1)
        [temp2,ns,nl,nb,geog,proj] = read_image_gdal(infile8)
        data1[ind] = temp1[ind]*(1-mm_prop)+temp2[ind]*mm_prop


        [temp1,ns,nl,nb,geog,proj] = read_image_gdal(infile3)
        [temp2,ns,nl,nb,geog,proj] = read_image_gdal(infile10)
        data3[ind] = temp1[ind]*(1-mm_prop)+temp2[ind]*mm_prop


        [temp1,ns,nl,nb,geog,proj] = read_image_gdal(infile4)
        [temp2,ns,nl,nb,geog,proj] = read_image_gdal(infile11)
        data4[ind] = temp1[ind]*(1-mm_prop)+temp2[ind]*mm_prop


    if kneed == 1:
        write_image_gdal(data1, ns, nl, nb, geog, proj, outfile1)
        write_image_gdal(data3, ns, nl, nb, geog, proj, outfile3)
        write_image_gdal(data4, ns, nl, nb, geog, proj, outfile4)









