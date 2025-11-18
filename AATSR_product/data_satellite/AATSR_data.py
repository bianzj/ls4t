import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from base.util_file import *
from base.util_data import *
import epr
import os
import calendar
from datetime import datetime

'''2025.6.17'''
'''AATSR 数据提取 extract'''
'''25.6.22: red/nir 读取的已经是反射率因子了，单位是%, 不需要再读取solar irradiance'''

'''
数据结构：
aatsr_obs: redN,redF,nirN,nirF,bt1N,bt1F,bt2N,bt2F
aatsr_clo: cloN,cloF
aatsr_ang: sza,saa,(vzaN,vzaF,vaaN,vaaF)
aatsr_loc: lon,lat,indx,indy
'''

base_dir = r'/media/hero/lsct03/'
indir_raw = r'/media/hero/SLSTR_Euro/'
outdir_obs = base_dir + r'aatsr_obs/'
outdir_clo = base_dir + r'aatsr_clo/'
outdir_ang = base_dir + r'aatsr_ang/'
outdir_loc = base_dir + r'aatsr_loc/'
outdir_tim = base_dir + r'aatsr_tim/'
outdir_aux = base_dir + r'aatsr_aux/'
error_log_path = base_dir + r'unzip_error_log.txt'
extract_error_log_path = base_dir + r'extract_error_log.txt'

years = [2012]
months = [4]
# months = [1,2,3,4,5,6,7,8,9,10,11,12]
# months = [1,2,3,4,5,6]
# months = [7,8,9,10,11,12]
# months = [1,2,3]
# months = [4,5,6]
# months = [7, 8,9]
# months = [10,11,12]
for year in years:
    for month in months:
        daynum = calendar.monthrange(year, month)[1]
        for d in range(daynum):
            day = d + 1
            print('---------------%04d/%02d/%02d/---------------' % (year, month, day))
            time_str = "//%04d" % int(year) + "//%02d" % int(month) + "//%02d" % int(day) + "//"
            indir_raw_day = indir_raw + time_str
            if not os.path.exists(indir_raw_day): continue
            outdir_obs_day = outdir_obs + '%04d/%02d/%02d/' % (year, month, day)
            outdir_clo_day = outdir_clo + '%04d/%02d/%02d/' % (year, month, day)
            outdir_ang_day = outdir_ang + '%04d/%02d/%02d/' % (year, month, day)
            outdir_loc_day = outdir_loc + '%04d/%02d/%02d/' % (year, month, day)
            outdir_tim_day = outdir_tim + '%04d/%02d/%02d/' % (year, month, day)
            outdir_aux_day = outdir_aux + '%04d/%02d/%02d/' % (year, month, day)
            mkdir_if_not_exist(outdir_obs_day)
            mkdir_if_not_exist(outdir_clo_day)
            mkdir_if_not_exist(outdir_ang_day)
            mkdir_if_not_exist(outdir_loc_day)
            # mkdir_if_not_exist(outdir_tim_day)
            # mkdir_if_not_exist(outdir_aux_day)
            fileNames = search_file_rej(indir_raw_day, ['ATS_TOA'], 'md5')
            fileNum = len(fileNames)
            for i, fileName in enumerate(fileNames):
                print('%02d / %02d' % (i + 1, fileNum))
                '''读取时间信息'''
                year_str = fileName[14:18]
                date_str = fileName[18:22]
                time_str = fileName[23:29]
                doy_int = date2DOY(int(year_str), int(date_str[0:2]), int(date_str[2:4]))
                doy_str = str(doy_int).zfill(3)

                '''读取产品'''
                infile = indir_raw_day + fileName

                try:
                    product = epr.Product(infile)
                except Exception as e:
                    with open(extract_error_log_path, 'a') as f:  # 使用追加模式
                        f.write(f" {infile}")
                        f.write(f"{str(e)}\n\n")

                fN = 'AATSR' + "_" + year_str + "_" + doy_str + "_" + time_str + '_'
                outfile_obs = outdir_obs_day + fN + 'obs.h5'
                outfile_clo = outdir_clo_day + fN + 'clo.h5'
                outfile_ang = outdir_ang_day + fN + 'ang.h5'
                outfile_loc = outdir_loc_day + fN + 'loc.h5'
                outfile_tim = outdir_tim_day + fN + 'tim.h5'
                outfile_aux = outdir_aux_day + fN + 'aux.h5'
                if os.path.exists(outfile_obs) and os.path.exists(outfile_clo): continue

                # '''读取经纬度信息'''
                # band = product.get_band('latitude')
                # lat = band.read_as_array()
                # band = product.get_band('longitude')
                # lon = band.read_as_array()
                # height, width = np.shape(lat)
                #
                # band = product.get_band('lat_corr_nadir')
                # lat_corr_nadir = band.read_as_array()
                # band = product.get_band('lon_corr_nadir')
                # lon_corr_nadir = band.read_as_array()

                '''读取角度信息'''
                try:
                    band = product.get_band('sun_elev_nadir')
                    sza = band.read_as_array()
                    sza = 90 - sza
                    band = product.get_band('view_elev_nadir')
                    vzaN = band.read_as_array()
                    vzaN = 90 - vzaN
                    band = product.get_band('sun_azimuth_nadir')
                    saa = band.read_as_array()
                    band = product.get_band('view_azimuth_nadir')
                    vaaN = band.read_as_array()
                    band = product.get_band('view_elev_fward')
                    vzaF = band.read_as_array()
                    vzaF = 90 - vzaF
                    band = product.get_band('view_azimuth_fward')
                    vaaF = band.read_as_array()

                    '''读取热红外信息'''
                    band = product.get_band('btemp_nadir_1100')
                    bt8_N = band.read_as_array()
                    band = product.get_band('btemp_nadir_1200')
                    bt9_N = band.read_as_array()

                    height, width = np.shape(bt8_N)
                    '''输出'''
                    nl = height
                    ns = width

                    band = product.get_band('btemp_fward_1100')
                    bt8_F = band.read_as_array()
                    band = product.get_band('btemp_fward_1200')
                    bt9_F = band.read_as_array()

                    '''读取可见光信息'''
                    '''25.6.22: 读取的已经是反射率因子了，单位是%'''
                    band = product.get_band('reflec_nadir_0670')
                    redN = band.read_as_array()
                    band = product.get_band('reflec_nadir_0870')
                    nirN = band.read_as_array()

                    band = product.get_band('reflec_fward_0670')
                    redF = band.read_as_array()
                    band = product.get_band('reflec_fward_0870')
                    nirF = band.read_as_array()

                    '''读取云层信息'''
                    band = product.get_band('cloud_flags_nadir')
                    cloN = band.read_as_array()
                    band = product.get_band('cloud_flags_fward')
                    cloF = band.read_as_array()
                except Exception as e:
                    with open(extract_error_log_path, 'a') as f:  # 使用追加模式
                        f.write(f" {infile}")
                        f.write(f"{str(e)}\n\n")
                        continue

                # try:
                #     red_sr = \
                #     product.get_dataset('VISIBLE_CALIB_COEFS_GADS').read_record(0).get_field('sol_irr_067').get_elems()[
                #         0]
                #     nir_sr = \
                #     product.get_dataset('VISIBLE_CALIB_COEFS_GADS').read_record(0).get_field('sol_irr_087').get_elems()[
                #         0]
                # except (AttributeError, IndexError, KeyError, Exception) as e:
                #     # 如果出现任何异常（如字段不存在、索引越界、数据集不存在等），则设为 0
                #     print(fileName)
                #     print(f"No calibration coefficients")
                #     # print(product.get_dataset('VISIBLE_CALIB_COEFS_GADS'))
                #     red_sr = 0
                #     nir_sr = 0






                metadata = {
                    'Author': 'TIRT team',
                    'Version': '1.0',
                    'Create_time': datetime.utcnow().isoformat() + 'Z',
                    'source': fileName,
                }


                redN[redN < 0], redF[redF < 0], nirN[nirN < 0], nirF[nirF < 0] = 0, 0, 0, 0
                bt8_N[bt8_N < 0], bt8_F[bt8_F < 0], bt9_N[bt9_N < 0], bt9_F[bt9_F < 0] = 0, 0, 0, 0
                redN = np.rint(redN * 10).astype(uint16)
                redF = np.rint(redF * 10).astype(uint16)
                nirN = np.rint(nirN * 10).astype(uint16)
                nirF = np.rint(nirF * 10).astype(uint16)
                bt8_N = np.rint(bt8_N * 100).astype(uint16)
                bt8_F = np.rint(bt8_F * 100).astype(uint16)
                bt9_N = np.rint(bt9_N * 100).astype(uint16)
                bt9_F = np.rint(bt9_F * 100).astype(uint16)

                with h5py.File(outfile_obs, 'w') as h5f:
                    redN_data = h5f.create_dataset('redN', data=redN, compression='gzip', dtype=np.uint16)
                    redN_data.attrs['missing_value'] = 0
                    redN_data.attrs['scalar'] = 0.1

                    redF_data = h5f.create_dataset('redF', data=redF, compression='gzip', dtype=np.uint16)
                    redF_data.attrs['missing_value'] = 0
                    redF_data.attrs['scalar'] = 0.1

                    nirN_data = h5f.create_dataset('nirN', data=nirN, compression='gzip', dtype=np.uint16)
                    nirN_data.attrs['missing_value'] = 0
                    nirN_data.attrs['scalar'] = 0.1

                    nirF_data = h5f.create_dataset('nirF', data=nirF, compression='gzip', dtype=np.uint16)
                    nirF_data.attrs['missing_value'] = 0
                    nirF_data.attrs['scalar'] = 0.1

                    # red_sr_data = h5f.create_dataset('red_sr', data=float(red_sr))
                    # nir_sr_data = h5f.create_dataset('nir_sr', data=float(nir_sr))

                    bt8_N_data = h5f.create_dataset('bt8N', data=bt8_N, compression='gzip', dtype=np.uint16)
                    bt8_N_data.attrs['scalar'] = 0.01
                    bt8_N_data.attrs['missing_value'] = 0

                    bt8_F_data = h5f.create_dataset('bt8F', data=bt8_F, compression='gzip', dtype=np.uint16)
                    bt8_F_data.attrs['scalar'] = 0.01
                    bt8_F_data.attrs['missing_value'] = 0

                    bt9_N_data = h5f.create_dataset('bt9N', data=bt9_N, compression='gzip', dtype=np.uint16)
                    bt9_N_data.attrs['scalar'] = 0.01
                    bt9_N_data.attrs['missing_value'] = 0

                    bt9_F_data = h5f.create_dataset('bt9F', data=bt9_F, compression='gzip', dtype=np.uint16)
                    bt9_F_data.attrs['scalar'] = 0.01
                    bt9_F_data.attrs['missing_value'] = 0

                    # 添加元数据
                    for key, value in metadata.items():
                        h5f.attrs[key] = value

                '''clo'''
                '''16 bit integer'''
                with h5py.File(outfile_clo, 'w') as h5f:
                    cloN_data = h5f.create_dataset('cloN', data=cloN, compression='gzip', dtype=np.uint16)
                    cloN_data.attrs['missing_value'] = 0  # 设置缺失值为0

                    cloF_data = h5f.create_dataset('cloF', data=cloF, compression='gzip', dtype=np.uint16)
                    cloF_data.attrs['missing_value'] = 0  # 设置缺失值为0

                    for key, value in metadata.items():
                        h5f.attrs[key] = value

                '''ang'''
                '''16km (异常值为-999)'''
                vaaN[vaaN == -999] = 65535
                vzaN[vzaN == -999] = 65535
                vaaF[vaaF == -999] = 65535
                vzaF[vzaF == -999] = 65535
                saa[saa == -999] = 65535
                sza[sza == -999] = 65535

                vaaN = np.rint(vaaN * 100).astype(np.uint16)
                vzaN = np.rint(vzaN * 100).astype(np.uint16)
                vaaF = np.rint(vaaF * 100).astype(np.uint16)
                vzaF = np.rint(vzaF * 100).astype(np.uint16)
                saa = np.rint(saa * 100).astype(np.uint16)
                sza = np.rint(sza * 100).astype(np.uint16)

                with h5py.File(outfile_ang, 'w') as h5f:
                    vaaN_data = h5f.create_dataset('vaaN', data=vaaN, compression='gzip', dtype=np.uint16)
                    vaaF_data = h5f.create_dataset('vaaF', data=vaaF, compression='gzip', dtype=np.uint16)
                    vzaN_data = h5f.create_dataset('vzaN', data=vzaN, compression='gzip', dtype=np.uint16)
                    vzaF_data = h5f.create_dataset('vzaF', data=vzaF, compression='gzip', dtype=np.uint16)
                    saa_data = h5f.create_dataset('saa', data=saa, compression='gzip', dtype=np.uint16)
                    sza_data = h5f.create_dataset('sza', data=sza, compression='gzip', dtype=np.uint16)

                    # 添加 scalar 和 missing_value 属性
                    vaaN_data.attrs['scalar'] = 0.01
                    vaaN_data.attrs['missing_value'] = 65535
                    vaaF_data.attrs['scalar'] = 0.01
                    vaaF_data.attrs['missing_value'] = 65535
                    vzaN_data.attrs['scalar'] = 0.01
                    vzaN_data.attrs['missing_value'] = 65535
                    vzaF_data.attrs['scalar'] = 0.01
                    vzaF_data.attrs['missing_value'] = 65535
                    saa_data.attrs['scalar'] = 0.01
                    saa_data.attrs['missing_value'] = 65535
                    sza_data.attrs['scalar'] = 0.01
                    sza_data.attrs['missing_value'] = 65535

                    # 添加元数据
                    for key, value in metadata.items():
                        h5f.attrs[key] = value

                # '''loc'''
                # '''10-6 -9999999999'''
                # lat[lat < -10000], lon[lon < -10000] = -32768, -32768
                # lat[np.isclose(lat, -9.99e-4)], lon[np.isclose(lon, -9.99e-4)] = -32768, -32768
                # with h5py.File(outfile_loc, 'w') as h5f:
                #     lon_data = h5f.create_dataset('lon', data=np.rint(lon * 100).astype(int16), compression='gzip',
                #                                   dtype=np.int16)
                #     lon_data.attrs['scalar'] = 100
                #     lon_data.attrs['missing_value'] = -32768
                #     lat_data = h5f.create_dataset('lat', data=np.rint(lat * 100).astype(int16), compression='gzip',
                #                                   dtype=np.int16)
                #     lat_data.attrs['scalar'] = 100
                #     lat_data.attrs['missing_value'] = -32768
                #     for key, value in metadata.items():
                #         h5f.attrs[key] = value
                product.close()