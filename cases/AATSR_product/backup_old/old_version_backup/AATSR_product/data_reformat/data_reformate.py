import calendar
from utils.old.util import *
from datetime import datetime, timedelta

'''2024.5.24'''
'''将tif数据转化为hdf5'''
'''包括lat,lon,indx,indy,saa,sza,clo,lai,time,lstN,lstO'''

base_dir = r"/media/hero/lsct04/"
raw_dir = r"/media/hero/raw02/"
unzip_dir = r"D:\data\\"
year = 2002

def un_gz(file_name, infile, outdir):
    """ungz zip file"""
    mkdir_if_not_exist(outdir)
    f_name = outdir + file_name.replace(".gz", "")
    # 获取文件的名称，去掉
    g_file = gzip.GzipFile(infile + file_name)
    # 创建gzip对象
    open(f_name, "wb+").write(g_file.read())
    # gzip对象用read()打开后，写入open()建立的文件里。
    g_file.close()  # 关闭gzip对象
    print("Unzip " + file_name + " finished!")

def log_error(file_name, error_type, log_file="error_log2.txt"):
    with open(log_file, "a") as f:
        f.write(f"File: {file_name}, Error Type: {error_type}\n")

infile_type = r"/home/hero/data/0_base/type/type_world_1000.tif"
type_dir = infile_type
dataset = gdal.Open(type_dir)

for year in range(year,year + 1):
    indir_tif_year = base_dir + r"AATSR/%04d/tif/" % year
    indir_raw_year = raw_dir + r"%04d/" % year
    outdir_unzip_year = unzip_dir + r"AATSR/%04d/hdf/" % year
    outdir_year =  r"/media/hero/lsct04/AATSR/%04d/hdf/" % year
    file_error_report = outdir_year + "error_report.txt"
    indir_lst_year = base_dir + r"AATSR/%04d/lst/" % year
    indir_lai = base_dir + r"AATSR/lai/%04d/" % year
    for month in range(12,13):
        if_extract_zip = 0
        daynum = calendar.monthrange(year, month)[1]
        for day in range(1,daynum+1):
            print("------------------------%04d-%02d-%02d----------------------"%(year,month,day))
            indir_tif_day = indir_tif_year + "%02d/%02d/" % (month, day)
            indir_raw_day = indir_raw_year + "%02d/%02d/ats_toa_1p/" % (month, day)
            indir_lst_day = indir_lst_year + "%02d/%02d/" % (month, day)
            outdir_day = outdir_year + "%02d/%02d/" % (month, day)
            outdir_unzip_day = outdir_unzip_year + "%02d/%02d/" % (month, day)
            if not os.path.exists(indir_raw_day): continue
            mkdir_if_not_exist(outdir_day)
            # mkdir_if_not_exist(outdir_unzip_day)

            '''读取每日LAI'''
            doy = date2DOY(year,month,day)
            doy1 = (doy // 4) * 4 + 1
            doy2 = (doy // 4) * 4 + 5
            infile_lai1 = indir_lai + r"MuSyQ.CSC.LAI.A" + '%04d%03d' % (int(year), doy1) + '.tif'
            infile_lai2 = indir_lai + r"MuSyQ.CSC.LAI.A" + '%04d%03d' % (int(year), doy2) + '.tif'
            if not os.path.exists(infile_lai2): infile_lai2 = infile_lai1
            [lai1, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai1)
            [lai2, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lai2)

            fileNames = search_file_rej(indir_raw_day,['.gz'],'enp')
            fileNum = len(fileNames)
            for i,fileName in enumerate(fileNames):
                print("%02d/%02d " % (i+1,fileNum))
                print("Processing file: %s" % (fileName))
                infile_zip = indir_raw_day + fileName
                time_str = fileName.split("_")[3]
                doy = date2DOY(year,month,day)
                tif_str = "AATSR_%04d_%03d_"%(year,doy) + time_str + "_"

                out_hdf5 = outdir_day + tif_str[:-1] + '.h5'
                if os.path.exists(out_hdf5):
                    print("Pass!")
                    continue

                error_flag = 0
                infile_lat = indir_tif_day +tif_str + "lat.tif"
                infile_lon = indir_tif_day +tif_str + "lon.tif"
                if (not os.path.exists(infile_lat)) or (not os.path.exists(infile_lon)):
                    print("Lack lon lat information!")
                    error_flag = 1

                infile_indx = indir_tif_day +tif_str + "indx.tif"
                infile_indy = indir_tif_day +tif_str + "indy.tif"
                if (not os.path.exists(infile_indx)) or (not os.path.exists(infile_indy)):
                    print("Lack indxy information!")
                    error_flag = 2

                infile_cloN = indir_tif_day + tif_str + "clo_n.tif"
                infile_cloO = indir_tif_day + tif_str + "clo_f.tif"
                if (not os.path.exists(infile_cloN)) or (not os.path.exists(infile_cloO)):
                    print("Lack clo information!")
                    error_flag = 3

                infile_sza = indir_tif_day +tif_str + "sza.tif"
                infile_saa = indir_tif_day +tif_str + "saa.tif"
                if (not os.path.exists(infile_sza)) or (not os.path.exists(infile_saa)):
                    print("Lack sza/saa information!")
                    error_flag = 4

                infile_lstN = indir_lst_day + tif_str + "lst_n.tif"
                infile_lstO = indir_lst_day + tif_str + "lst_f.tif"
                if (not os.path.exists(infile_lstN)) or (not os.path.exists(infile_lstO)):
                    print("Lack lst information!")
                    error_flag = 5

                if error_flag == 2:
                    [lon, ns, nl, temp3, temp4, temp5] = read_image_gdal(infile_lon)
                    [lat, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_lat)
                    indx, indy = loc2map(lat, lon, dataset)
                    indx[indx >= 18000] = 0
                    indy[indy >= 36000] = 0
                    write_image_gdal(np.reshape(indx, [nl, ns]).astype(uint16), ns, nl, 1, '', '', infile_indx)
                    write_image_gdal(np.reshape(indy, [nl, ns]).astype(uint16), ns, nl, 1, '', '', infile_indy)
                    error_flag = 0
                    print("fix indxy!")


                if error_flag!=0:
                    log_error(fileName,error_flag,file_error_report)
                    continue


                '''读取数据'''
                [lat, ns, nl, nb, geog, proj] = read_image_gdal(infile_lat)
                [lon, ns, nl, nb, geog, proj] = read_image_gdal(infile_lon)
                [indx, ns, nl, nb, geog, proj] = read_image_gdal(infile_indx)
                [indy, ns, nl, nb, geog, proj] = read_image_gdal(infile_indy)
                [clo_N, ns, nl, nb, geog, proj] = read_image_gdal(infile_cloN)
                [clo_O, ns, nl, nb, geog, proj] = read_image_gdal(infile_cloO)
                [sza, ns, nl, nb, geog, proj] = read_image_gdal(infile_sza)
                [saa, ns, nl, nb, geog, proj] = read_image_gdal(infile_saa)
                [lstN, ns, nl, nb, geog, proj] = read_image_gdal(infile_lstN)
                [lstO, ns, nl, nb, geog, proj] = read_image_gdal(infile_lstO)

                lai = (1 - (doy - doy1) / 4) * lai1[indx, indy] + (doy - doy1) / 4 * lai2[indx, indy]
                lai = np.reshape(lai, [nl, ns])
                lai[lai >= 30000] = 0

                time_delta = timedelta(seconds=int(fileName.split('_')[4][4:8]))
                time_start = datetime(year,month,day,int(time_str[0:2]),int(time_str[2:4]),int(time_str[4:6]))
                sec_num_start = int(time_str[0:2])*3600+int(time_str[2:4])*60+int(time_str[4:6])
                total_columns = nl
                sec_interval = int(fileName.split('_')[4][4:8]) / (total_columns-1)
                time_array = np.array(
                    [sec_num_start + i * sec_interval for i in range(total_columns)])
                sec_save = np.transpose(np.array([time_array] *512))


                '''写h5文件'''
                out_hdf5 = outdir_day + tif_str[:-1] + '.h5'
                if not os.path.exists(out_hdf5):
                    f = h5py.File(out_hdf5, 'w')
                else:
                    f = h5py.File(out_hdf5, 'a')

                # 添加文件级别的属性
                f.attrs['Origin File'] = fileName
                f.attrs['Version'] = 'v 1.0'
                f.attrs['Creation Date'] = str(datetime.now())
                f.attrs['Author'] = 'AIRT Team'

                datasets = {
                    'lat': (lat, 'Latitude, Scale = 1.0, type = Float', np.float32),
                    'lon': (lon, 'Longitude, Scale = 1.0, type = Float', np.float32),
                    'sza': (sza, 'Sun zenith angle, Scale = 0.01, type = uint16', np.uint16),
                    'saa': (saa, 'Sun azimuth angle, Scale = 0.01, type = int16', np.int16),
                    'time': (sec_save, 'time in second(UTC), Scale = 1.0, type = float', np.float32),
                    'indx': (indx, 'indx(corresponding to 1 km lcc map), Scale = 1.0, type = uint16', np.uint16),
                    'indy': (indy, 'indy(corresponding to 1 km lcc map), Scale = 1.0, type = uint16', np.uint16),
                    'clo_N': (clo_N, 'nadir cloud, Scale = 1.0, type = uint16', np.uint16),
                    'clo_O': (clo_O, 'forward cloud, Scale = 1.0, type = uint16', np.uint16),
                    'LAI': (lai, 'LAI, Scale = 0.001, type = uint16', np.uint16),
                    'lstN': (lstN, 'nadir LST, Scale = 0.01, type = uint16', np.uint16),
                    'lstO': (lstO, 'forward LST, Scale = 0.01, type = uint16', np.uint16)
                }

                for dset_name, (data, description, dtype) in datasets.items():
                    if dset_name in f:
                        del f[dset_name]
                    dset = f.create_dataset(dset_name, data=data, dtype=dtype, compression='gzip')
                    dset.attrs['description'] = description

                # 关闭文件
                f.close()

                print(f"Complete！")