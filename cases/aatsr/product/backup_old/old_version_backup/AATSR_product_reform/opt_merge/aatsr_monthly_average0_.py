from utils.old.util import *

indir_lst0 = r"/media/hero/lsct04/aatsr_lst//"
indir_lsct0 = "/media/hero/lsct04/aatsr_lsct_v0//"
indir_obs0 = r"E:/AATSR//"
indir_ang0 = r"/media/hero/lsct04/aatsr_ang//"
indir_loc0 = r"/media/hero/lsct04/aatsr_loc//"

outdir0 = r"/media/hero/lsct04/aatsr_lsct_month_v0//"


'''
温度阈值：250-330
云检测阈值：cn+co<100
温度差异：20,25,20
叶面积指数：0.01-10
白天夜晚：sza>0; sza<=0
'''


infile_ref =  r"/media/hero/lsct04/0_base/ref_world_0.05.tif"
ref0,ns0,nl0,nb0,geog0,proj0 = read_image_gdal(infile_ref)
Tmin_threshold = 25000
Tmax_threshold = 33000

for kyear in range(2008, 2013):
    for kmonth in range(2, 13):

        outfile1 = outdir0 + "aatsr_%04d_" % kyear + "%02d_" % kmonth + "_day.tif"
        if os.path.exists(outfile1):continue

        lstN_day_all = np.zeros([nl0,ns0],dtype=np.float32)
        Ts_day_all = np.zeros([nl0,ns0],dtype=np.float32)
        lstO_day_all = np.zeros([nl0,ns0],dtype=np.float32)
        Tv_day_all = np.zeros([nl0,ns0],dtype=np.float32)
        count_day_all = np.zeros([nl0,ns0],dtype=np.float32)

        lstN_night_all = np.zeros([nl0, ns0],dtype=np.float32)
        Ts_night_all = np.zeros([nl0, ns0],dtype=np.float32)
        lstO_night_all = np.zeros([nl0, ns0],dtype=np.float32)
        Tv_night_all = np.zeros([nl0, ns0],dtype=np.float32)
        count_night_all = np.zeros([nl0,ns0],dtype=np.float32)



        for kday in range(1, 31):


            indir_lst = indir_lst0 + "%04d" % kyear + "/%02d/" % kmonth + "%02d/" % kday
            indir_lsct = indir_lsct0 + "%04d" % kyear + "/%02d/" % kmonth + "%02d/" % kday
            indir_loc = indir_loc0 + "%04d" % kyear + "/%02d/" % kmonth + "%02d/" % kday
            indir_ang = indir_ang0 + "%04d" % kyear + "/%02d/" % kmonth + "%02d/" % kday

            if os.path.exists(indir_lsct) == 0: continue
            fileNames = search_file_rej(indir_lsct, ['h5'], 'xml')
            fileNum = len(fileNames)
            for i, fileName in enumerate(fileNames):

                infile_lsct = indir_lsct + fileName

                infile_lst = indir_lst + fileName[:-8]+"_lst.h5"
                infile_loc = indir_loc + fileName[:-8]+"_loc.h5"
                infile_ang = indir_ang + fileName[:-8]+"_ang.h5"


                print(infile_lst)
                if (os.path.exists(infile_lsct)==0) or (os.path.exists(infile_lsct)==0): continue

                try:
                    fin = h5py.File(infile_lst)
                    lstN = fin['lstN'][:]
                    lstO = fin['lstO'][:]
                    fin.close()

                    fin_ = h5py.File(infile_loc)
                    indx = fin_['indx'][:]
                    indy = fin_['indy'][:]
                    fin_.close()

                    fin_ = h5py.File(infile_ang)
                    sza = fin_['sza'][:]
                    fin_.close()

                    fin = h5py.File(infile_lsct)
                    # Ts = fin['Ts_p'][:]
                    # Tv = fin['Tv_p'][:]
                    Ts = fin['Ts'][:]
                    Tv = fin['Tv'][:]
                    fin.close()
                except Exception as e:
                    continue

                indx = np.int_(indx/5)
                indy = np.int_(indy/5)
                print(infile_lsct)

                ind = ((sza > 0) * (lstN > Tmin_threshold) * (lstN < Tmax_threshold) *(Ts > Tmin_threshold) *(Ts < Tmax_threshold)*(Tv > Tmin_threshold)*
                       (Tv < Tmax_threshold)*(np.abs(lstN*1.0 - Tv*1.0)<2000)*(np.abs(Ts*1.0 - Tv*1.0)<2500)*(np.abs(lstN*1.0 - Ts*1.0)<2000)* (lstO > Tmin_threshold) * (lstO < Tmax_threshold))

                count = np.sum(ind)
                print(count)

                lstN_day_all[indx[ind],indy[ind]] += lstN[ind]
                lstO_day_all[indx[ind],indy[ind]] += lstO[ind]
                Ts_day_all[indx[ind],indy[ind]] += Ts[ind]
                Tv_day_all[indx[ind],indy[ind]] += Tv[ind]
                count_day_all[indx[ind],indy[ind]] += 1

                ind = ((sza <= 0) * (lstN > Tmin_threshold) * (lstN < Tmax_threshold) * (Ts > Tmin_threshold) * (
                            Ts < Tmax_threshold) * (Tv > Tmin_threshold) *
                       (Tv < Tmax_threshold) * (np.abs(lstN * 1.0 - Tv * 1.0) < 2000) * (
                                   np.abs(Ts * 1.0 - Tv * 1.0) < 2500) * (np.abs(lstN * 1.0 - Ts * 1.0) < 2000) * (
                                   lstO > Tmin_threshold) * (lstO < Tmax_threshold))

                count = np.sum(ind)
                print(count)

                lstN_night_all[indx[ind], indy[ind]] += lstN[ind]
                lstO_night_all[indx[ind], indy[ind]] += lstO[ind]
                Ts_night_all[indx[ind], indy[ind]] += Ts[ind]
                Tv_night_all[indx[ind], indy[ind]] += Tv[ind]
                count_night_all[indx[ind], indy[ind]] += 1


        ind = count_day_all>0
        lstN_day_all[ind] = lstN_day_all[ind]/count_day_all[ind]
        lstO_day_all[ind] = lstO_day_all[ind]/count_day_all[ind]
        Tv_day_all[ind] = Tv_day_all[ind]/count_day_all[ind]
        Ts_day_all[ind] = Ts_day_all[ind]/count_day_all[ind]

        ind = count_night_all>0
        lstN_night_all[ind] = lstN_night_all[ind]/count_night_all[ind]
        lstO_night_all[ind] = lstO_night_all[ind]/count_night_all[ind]
        Tv_night_all[ind] = Tv_night_all[ind]/count_night_all[ind]
        Ts_night_all[ind] = Ts_night_all[ind]/count_night_all[ind]

        if(np.sum(lstN_day_all)>10):
            # outfile = outdir0 + "aatsr_%04d_" % kyear + "%02d_" % kmonth + "lstn_day.tif"
            # write_image_gdal(lstN_day_all,ns0,nl0,nb0,geog0,proj0,outfile)
            # outfile = outdir0 + "aatsr_%04d_" % kyear + "%02d_" % kmonth + "lsto_day.tif"
            # write_image_gdal(lstO_day_all,ns0,nl0,nb0,geog0,proj0,outfile)
            # outfile = outdir0 + "aatsr_%04d_" % kyear + "%02d_" % kmonth + "ts_day.tif"
            # write_image_gdal(Ts_day_all,ns0,nl0,nb0,geog0,proj0,outfile)
            # outfile = outdir0 + "aatsr_%04d_" % kyear + "%02d_" % kmonth + "tv_day.tif"
            # write_image_gdal(Tv_day_all,ns0,nl0,nb0,geog0,proj0,outfile)
            outfile1 = outdir0 + "aatsr_%04d_" % kyear + "%02d" % kmonth + "_day.tif"
            name_list = ['Ts', 'Tv', 'Tnadir', 'Tobliq']
            data_list = [Ts_day_all, Tv_day_all, lstN_day_all , lstO_day_all ]
            dtype_list = ['uint16', 'uint16', 'uint16', 'uint16']
            write_h5py_file(outfile1, name_list, data_list, dtype_list, compression='gzip', ifcover=1)

        if(np.sum(lstN_night_all)>10):
            # outfile = outdir0 + "aatsr_%04d_" % kyear + "%02d_" % kmonth + "lstn_night.tif"
            # write_image_gdal(lstN_night_all,ns0,nl0,nb0,geog0,proj0,outfile)
            # outfile = outdir0 + "aatsr_%04d_" % kyear + "%02d_" % kmonth + "lsto_night.tif"
            # write_image_gdal(lstO_night_all,ns0,nl0,nb0,geog0,proj0,outfile)
            # outfile = outdir0 + "aatsr_%04d_" % kyear + "%02d_" % kmonth + "ts_night.tif"
            # write_image_gdal(Ts_night_all,ns0,nl0,nb0,geog0,proj0,outfile)
            # outfile = outdir0 + "aatsr_%04d_" % kyear + "%02d_" % kmonth + "tv_night.tif"
            # write_image_gdal(Tv_night_all,ns0,nl0,nb0,geog0,proj0,outfile)
            outfile2 = outdir0 + "aatsr_%04d_" % kyear + "%02d" % kmonth + "_night.tif"
            name_list = ['Ts', 'Tv', 'Tnadir', 'Tobliq']
            data_list = [Ts_night_all, Tv_night_all, lstN_night_all, lstO_night_all]
            dtype_list = ['uint16', 'uint16', 'uint16', 'uint16']
            write_h5py_file(outfile2, name_list, data_list, dtype_list, compression='gzip', ifcover=1)


