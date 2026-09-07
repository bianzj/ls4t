from utils.old.util import *
import math

'''AATSR city reformat'''

indir_city = r"/home/hero/data/AATSR/City3/"
outdir_city = r"/home/hero/data/AATSR/City_reformat_new/"

infile_city_list = r"/home/hero/data/AATSR/City/records.csv"
data = pd.read_csv(infile_city_list)
city_names = data['city']
site_lon_arr = data['lon']
site_lat_arr = data['lat']

indir_base = r"/home/hero/data/base/"
indir_type = indir_base + r"0_base/type/"
infile_type = indir_type + r"type_world_1000.tif"
dataset = gdal.Open(infile_type)

# city_names = ['beijing']  # 可以根据需要替换城市名称
for city_name in city_names:
    site_lon,site_lat = float(data[data['city'] == city_name]['lon']), float(data[data['city'] == city_name]['lat'])
    print(city_name,site_lon,site_lat)
    site_lon_center = math.floor(site_lon * 100) / 100
    site_lat_center = math.ceil(site_lat * 100) / 100
    site_lon_min = round(site_lon_center - 0.01 * 22,2)
    site_lon_max = round(site_lon_center + 0.01 * (22 + 1),2)
    site_lat_min = round(site_lat_center - 0.01 * 22,2)
    site_lat_max = round(site_lat_center + 0.01 * (22 + 1),2)

    indir = indir_city + city_name + '/'
    outdir = outdir_city + city_name + '/'
    mkdir_if_not_exist(outdir)

    fileNames = search_file_rej(indir, ['h5'],'.h.h5')
    for fileName in fileNames:
        # print(fileName)
        infile = indir + fileName
        outfile = outdir + fileName
        if os.path.exists(outfile): continue
        name_list = ["lon", 'lat', "indx", "indy", "ref_indx", "ref_indy", "sec", "ref_time", "type",
                     "emis_s", "emis_v", "lai", 'vzaN', 'vzaO', 'vaaN', 'vaaO', 'sza', 'saa', 'clo',
                     "lstN", "lstO"]

        lon, lat, indx, indy, imagex, imagey, sec_save, time_str, type, emis_s, emis_v, lai, vzaN, vzaO, vaaN, vaaO, sza, saa, clo, lstN, lstO = read_h5py_items(
            infile, name_list)

        lon_new = np.arange(site_lon_min, site_lon_max- 0.0001, 0.01)
        lat_new = np.arange(site_lat_min, site_lat_max- 0.0001, 0.01)
        lon_grid, lat_grid = np.meshgrid(lon_new, lat_new)

        # 将数据展平
        lon_flat = lon.flatten()
        lat_flat = lat.flatten()
        type_flat = type.flatten()
        emis_s_flat = emis_s.flatten()
        emis_v_flat = emis_v.flatten()
        lai_flat = lai.flatten()
        vzaN_flat = vzaN.flatten()
        vzaO_flat = vzaO.flatten()
        vaaN_flat = vaaN.flatten()
        vaaO_flat = vaaO.flatten()
        sza_flat = sza.flatten()
        saa_flat = saa.flatten()
        clo_flat = clo.flatten()
        lstN_flat = lstN.flatten()
        lstO_flat = lstO.flatten()
        indx_flat = indx.flatten()
        indy_flat = indy.flatten()

        if vaaN_flat.shape[0] == 0:
            print(fileName + ' vaa error')
            continue

        # 使用 griddata 进行插值
        type_new = griddata((lon_flat, lat_flat), type_flat, (lon_grid, lat_grid), method='nearest')
        emis_s_new = griddata((lon_flat, lat_flat), emis_s_flat, (lon_grid, lat_grid), method='nearest')
        emis_v_new = griddata((lon_flat, lat_flat), emis_v_flat, (lon_grid, lat_grid), method='nearest')
        lai_new = griddata((lon_flat, lat_flat), lai_flat, (lon_grid, lat_grid), method='nearest')
        vzaN_new = griddata((lon_flat, lat_flat), vzaN_flat, (lon_grid, lat_grid), method='nearest')
        vzaO_new = griddata((lon_flat, lat_flat), vzaO_flat, (lon_grid, lat_grid), method='nearest')
        vaaN_new = griddata((lon_flat, lat_flat), vaaN_flat, (lon_grid, lat_grid), method='nearest')
        vaaO_new = griddata((lon_flat, lat_flat), vaaO_flat, (lon_grid, lat_grid), method='nearest')
        sza_new = griddata((lon_flat, lat_flat), sza_flat, (lon_grid, lat_grid), method='nearest')
        saa_new = griddata((lon_flat, lat_flat), saa_flat, (lon_grid, lat_grid), method='nearest')
        clo_new = griddata((lon_flat, lat_flat), clo_flat, (lon_grid, lat_grid), method='nearest')
        lstN_new = griddata((lon_flat, lat_flat), lstN_flat, (lon_grid, lat_grid), method='nearest')
        lstO_new = griddata((lon_flat, lat_flat), lstO_flat, (lon_grid, lat_grid), method='nearest')
        indx_new = griddata((lon_flat, lat_flat), indx_flat, (lon_grid, lat_grid), method='nearest')
        indy_new = griddata((lon_flat, lat_flat), indy_flat, (lon_grid, lat_grid), method='nearest')


        indx_arr, indy_arr = loc2map(lat_grid, lon_grid, dataset)
        indx_arr = indx_arr.reshape([45,45])
        indy_arr = indy_arr.reshape([45,45])

        # 保存处理后的数据
        save_name_list = ["ref_indx", "ref_indy", "sec", "ref_time", "lon", 'lat', "indx", "indy", "type", "emis_s", "emis_v", "lai",
                          'vzaN', 'vzaO', 'vaaN', 'vaaO', 'sza', 'saa', 'clo', "lstN", "lstO"]
        save_data = [imagex, imagey, sec_save, time_str,lon_grid, lat_grid, indx_arr, indy_arr, type_new, emis_s_new, emis_v_new, lai_new,
                     vzaN_new, vzaO_new, vaaN_new, vaaO_new, sza_new, saa_new, clo_new, lstN_new, lstO_new]

        # 使用 write_h5py_items 将处理后的数据写入新的 HDF5 文件
        write_h5py_file(outfile, save_name_list, data_list=save_data,
                        dtype_list=['f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f',
                                    'f', 'f', 'f', 'f', 'f', 'f', 'f', 'f'], compression=None,
                        ifcover=1)
