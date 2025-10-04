from base.util_data import *
from base.util_file import *




'''
down ERA5 reanalysis data
montly, hourly and yearly
'''



def download_era5_cdsadi_global():
    #c = cdsapi.Client()
    c= 10
    kmonth_ = [1,2,3,4,5,6,7,8,9,10,11,12]
    # kday_ = np.linspace(13,29,17)
    kday_ = np.asarray([31,28,31,30,31,30,31,31,30,31,30,31])
    for k1 in range(len(kmonth_)):
        kmonth = kmonth_[k1]
        for k2 in range(kday_[k1]):
            # kday = kday_[k2]
            kday = k2+1

            outfile = 'G:\ERA5_downward\ERA5.single-level.2019%02d'%kmonth+'%02d'%kday+'.nc'
            c.retrieve(
                'reanalysis-era5-single-levels',
                {
                    'product_type': 'reanalysis',
                    'variable': [
                        '2m_temperature', 'skin_temperature', 'surface_solar_radiation_downward_clear_sky',
                        'surface_solar_radiation_downwards', 'surface_thermal_radiation_downward_clear_sky',
                        'surface_thermal_radiation_downwards',
                        'uv_visible_albedo_for_diffuse_radiation', 'uv_visible_albedo_for_direct_radiation',
                    ],
                    'year': '2019',
                    'month': '%02d'%kmonth,
                    'day': '%02d'%kday,
                    'time': [
                        '00:00', '01:00', '02:00',
                        '03:00', '04:00', '05:00',
                        '06:00', '07:00', '08:00',
                        '09:00', '10:00', '11:00',
                        '12:00', '13:00', '14:00',
                        '15:00', '16:00', '17:00',
                        '18:00', '19:00', '20:00',
                        '21:00', '22:00', '23:00',
                    ],
                    'format': 'netcdf',
                },
                outfile)



def download_era5_cdsadi_land():
    # c = cdsapi.Client()
    c = 10
    c.retrieve(
        'reanalysis-era5-land',
        {
            'variable': [
                '10m_u_component_of_wind', '10m_v_component_of_wind', '2m_temperature',
                'leaf_area_index_high_vegetation', 'leaf_area_index_low_vegetation', 'skin_temperature',
                'snow_cover', 'soil_temperature_level_1', 'surface_pressure',
                'surface_solar_radiation_downwards', 'surface_thermal_radiation_downwards', 'temperature_of_snow_layer',
                'total_precipitation', 'volumetric_soil_water_layer_1',
            ],
            'year': '2019',
            'month': '09',
            'day': [
                '01',
            ],
            'time': [
                '00:00', '01:00', '02:00',
                '03:00', '04:00', '05:00',
                '06:00', '07:00', '08:00',
                '09:00', '10:00', '11:00',
                '12:00', '13:00', '14:00',
                '15:00', '16:00', '17:00',
                '18:00', '19:00', '20:00',
                '21:00', '22:00', '23:00',
            ],
            'format': 'netcdf.zip',
        },
        'download.netcdf.zip')



'''
从earthdata和copernicus下载数据
From earthdata, download remote sensing data onboard polar satellite, such as modis, viirs, avhrr;
From earthdata, download remote sensing data onboard polar satellite, such as sentinel;
'''

'''
从earthdata下载，
需要现在系统里下单，
然后通过下单后的订单号下载
'''
# k = 0
# target_dir = 'F:/vnp' ### target directory
# order_number = '501783069' #### order number
# # strips = 'Ymlhbnpqb3RoZXI6WW1saGJucHFRSEpoWkdrdVlXTXVZMjQ9OjE2NTMwMjk3NjU6NTg1ODdmODg5MWI5Zjg3NzJhNWU5YjVhYjI0MzA1NzViNzA1Zjg2ZA'
# while k<100:
#     p = Popen('wget -e robots=off -m -np -R .html,.tmp -nH -c --cut-dirs=3 "https://ladsweb.modaps.eosdis.nasa.gov/archive/orders/'+order_number+'/" --header "Authorization: Bearer Ymlhbnpqb3RoZXI6WW1saGJucHFRSEpoWkdrdVlXTXVZMjQ9OjE2NTMwMjk3NjU6NTg1ODdmODg5MWI5Zjg3NzJhNWU5YjVhYjI0MzA1NzViNzA1Zjg2ZA" -P '+target_dir)
#     stdout, stderr = p.communicate()
#     k = k+1
# print('success!')


#### 下载ecostress
# infile = r'E:\ecos_2019\123.txt'
# usernamee = "bianzjnew"
# password = "123457Abc"
# outdir = r'E:\ecos_2019\\'
# tempdata = read_txt_str(infile,'\n')
# for k in range(1):
#     for temp in tempdata:
#         # if 'https' not in temp:continue
#         print(temp)
#         dirname = temp[0][72:108]
#         filename = temp[0][68:]
#         url = temp[0]
#         print(filename,url)
#         line = r'wget -c --no-check-certificate --user=' +usernamee + " --password=" +password  + " " +url +  " -O " +outdir+filename
#         p = Popen(line)
#         stdout,stderr = p.communicate()


'''
copernicus下载，
会从系统下载下来包含文件名和路径的文档，
先从文档中解析出路径，然后进行下载
'''

#
# infile = r'C:\Users\zzz\Downloads\products_pbt.meta4'
# usernamee = "bianzj"
# password = "123457Abc"
# outdir = r'E:\slstr_2022\\'
# tempdata = read_txt_str(infile,'name="')
#
# for k in range(10):
#     for temp in tempdata[0]:
#         if 'zip' not in temp:continue
#         filename = temp[:98]
#         url = temp[183:183+98]
#         print(filename,url)
#         line = r'wget -c --no-check-certificate --user=' +usernamee + " --password=" +password  + " " +url +  " -O " +outdir+filename
#         p = Popen(line)
#         stdout,stderr = p.communicate()
#
#
#     # for temp in tempdata[1]:
#     #     if 'zip' not in temp: continue
#     #     filename = temp[:98]
#     #     url = temp[182:182+98]
#     #     print(filename, url)
#     #     # line = r'wget --no-check-certificate --user=' + usernamee + " --password=" + password + " " + temp[:98] + " -P " + outdir
#     #     # p = Popen(line)
#     #     # stdout, stderr = p.communicate()
#     #     # line = r'wget --no-check-certificate --user=' +usernamee + " --password=" +password  + " " +temp[:98] + " -P "+outdir
#     #     # p = Popen(line)
#     #     # stdout,stderr = p.communicate()



'''
从地面测量数据进行解析
然后分别按照要求存成csv或者txt
'''

# wl = 10.5
# start =time.clock()
# dataDir = r'D:\Data\lstSimulate\2012\\'
# infile1 = dataDir+'AWS_01.csv'
# infile2 = dataDir+'LAI_01.dat'
# dataDir = r'D:\Data\lstSimulate\\'
# outfile1 = dataDir+'inputX_2012_01.csv'
# outfile2 = dataDir+'inputY_2012_01.csv'
#
#
# wl = 10.5
# aws = pd.read_csv(infile1, parse_dates=['Time'])
#
# low = datetime(2012, 6, 15, 0)
# high = datetime(2012, 9, 6, 0)
# aws = aws[aws['Time'] >= low]
# aws = aws[aws['Time'] <= high]
#
# Time_aws = aws['Time']
# doy = Time_aws.apply(lambda x:x.dayofyear)
# hour = Time_aws.apply(lambda x:x.hour)
# minute = Time_aws.apply(lambda x:x.minute)
# t_aws = np.asarray(doy+ hour/24.0 + minute/60.0/24.0,dtype=np.float)
#
# Ms_aws = np.asarray(aws['Ms_2cm'].values,dtype=np.float)
# Ta_aws = np.asarray(aws['Ta_5m'].values,dtype=np.float)
# Ws_aws = np.asarray(aws['WS_10m'].values,dtype=np.float)
# Rh_aws = np.asarray(aws['RH_5m'].values,dtype=np.float)
# Dl_aws = np.asarray(aws['DLR_Cor'].values,dtype=np.float)
# Ds_aws = np.asarray(aws['DR'].values,dtype=np.float)
# Ul_aws = np.asarray(aws['ULR_Cor'].values,dtype=np.float)
# Us_aws = np.asarray(aws['UR'].values,dtype=np.float)
# Ir1_aws = np.asarray(aws['IRT_1'].values,dtype=np.float)
# Ir2_aws = np.asarray(aws['IRT_2'].values,dtype=np.float)
# # Pa_aws = np.asarray(aws['Press'].values,dtype=np.float)
# Ir_aws = (Ir1_aws+Ir2_aws)/2.0
# Pa_aws = np.asarray(aws['Press'].values,dtype=np.float)
# Ms_aws = Ms_aws/100.0
# Dl_aws[Dl_aws < 0] = 0
# Ds_aws[Ds_aws < 0] = 0
# Pa_aws[:] = 880
# Ms_aws[Ms_aws<0] =0.25
# Ea_aws = vp(Ta_aws,Rh_aws)
#
# # doy = Time_aws.apply(lambda x:x.dayofyear)
# # hour = Time_aws.apply(lambda x:x.hour)
# # minute = Time_aws.apply(lambda x:x.minute)
# # year_aws = Time_aws.apply(lambda x:x.year)
# # size_data = np.size(t_aws)
# # timeSeries = np.arange(size_data)
# # ind = np.asarray(( timeSeries % 3 ) == 0,dtype=np.bool)  ### ( timeSeries % 3 ) == 0  ;;; ( timeSeries % 3 ) >= 0
#
# '''
# 输出数据结构
# '''
#
# size_data = np.size(t_aws)
# mark=np.zeros(size_data)
# ind = (hour > 6) * (hour < 18)
# mark[:] = 2
# mark[ind] = 1
#
# timeSeries = np.arange(size_data)
# ind = np.asarray(( timeSeries % 3 ) == 0,dtype=np.bool)  ### ( timeSeries % 3 ) == 0  ;;; ( timeSeries % 3 ) >= 0
# input1 = np.stack([Ms_aws[ind],Ta_aws[ind],Ws_aws[ind],Rh_aws[ind],
#                    Ds_aws[ind],Dl_aws[ind],Us_aws[ind],Ul_aws[ind],mark[ind]],axis=1)
# # output1 = np.stack([Ir_aws,Ts_mea,Tv_mea],axis = 1)
# output1 = np.transpose(np.stack([Ir_aws[ind]]))
#
# # np.savetxt(outfile,result,fmt='%f')
#
# '''
# 写成CSV
# '''
# out = open(outfile1,'w', newline='')
# csv_write = csv.writer(out)
# csv_write.writerows(input1)
#
# out = open(outfile2,'w', newline='')
# csv_write = csv.writer(out)
# csv_write.writerows(output1)
#
#
# end = time.clock()
# print('Running time: %s Seconds'%(end-start))
#
# '''
# 写成TXT
# '''
# # np.savetxt(outdir+'ea_.dat',Ea_aws[ind],fmt='%.3f')
# # np.savetxt(outdir+'p_.dat',Pa_aws[ind],fmt='%.3f')
# # np.savetxt(outdir+'Ta_.dat',Ta_aws[ind],fmt='%.3f')
# # np.savetxt(outdir+'u_.dat',Ws_aws[ind],fmt='%.3f')
# # np.savetxt(outdir+'Rin_.dat',Ds_aws[ind],fmt='%.3f')
# # np.savetxt(outdir+'Rli_.dat',Dl_aws[ind],fmt='%.3f')
# # np.savetxt(outdir+'t_.dat',t_aws[ind],fmt= '%.3f')
# # np.savetxt(outdir+'year_.dat',year_aws[ind],fmt= '%d')
# # np.savetxt(outdir+'Irt_.dat',Ir_aws[ind],fmt = "%.3f")
# # np.savetxt(outdir+'SMC_.dat',Ms_aws[ind],fmt = "%.3f")
# # np.savetxt(outdir+'uRin_.dat',Us_aws[ind],fmt='%.3f')
# # np.savetxt(outdir+'uRli_.dat',Ul_aws[ind],fmt='%.3f')





