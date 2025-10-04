import julian
import numpy as np

from util.util import *


'''
用来读取EVO站点和KAL的NC数据，并保存为csv的格式
'''

indir_nc = r"D:\data\LSCT_Validation\LSCT_EVO_2020\\GT_MDB_IS_INSIT_EVO__-20200101_0002XX-KKIT-0.00X0.00-V.1.0newemis.nc"
outdir_csv = r'D:\data\LSCT_Validation\LSCT_EVO_2020\\LSCT_EVO_2020.csv'

# indir_nc = r"D:\data\LSCT_Validation\LSCT_KAL_2017\\GT_MDB_IS_INSIT_KAL_H-20170101_0000XX-KKIT-0.00X0.00-V.2.0.nc"
# outdir_csv = r'D:\data\LSCT_Validation\LSCT_KAL_2017\\LSCT_KAL_2017.csv'

ifread = 1

if ifread == 1 :
    try:
        nf = netCDF4.Dataset(indir_nc)
    except OSError:
        print(indir_nc + ' os error')


    objectName = 'BT'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    BT = read_image_Nc(indir_nc, objectName,1)

    objectName = 'BT_unc'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    BT_unc = read_image_Nc(indir_nc, objectName,1)

    objectName = 'BT_sky'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    BT_sky = read_image_Nc(indir_nc, objectName,1)

    objectName = 'BT_sky_unc'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    BT_sky_unc = read_image_Nc(indir_nc, objectName,1)

    objectName = 'emis'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    emis = read_image_Nc(indir_nc, objectName,1)

    objectName = 'endmember'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    endmember = read_image_Nc(indir_nc, objectName,1)

    objectName = 'jul_date'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    jul_date = read_image_Nc(indir_nc, objectName,1)

    objectName = 'lat'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    lat = read_image_Nc(indir_nc, objectName,1)

    objectName = 'lon'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    lon = read_image_Nc(indir_nc, objectName,1)
    #
    # objectName = 'lcc'
    # if (objectName not in nf.variables.keys()):
    #     print("No such object!")
    # lcc = read_image_Nc(indir_nc, objectName,1)

    objectName = 'LST'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    LST = read_image_Nc(indir_nc, objectName,1)

    objectName = 'LST_uncertainty'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    LST_unc = read_image_Nc(indir_nc, objectName,1)

    # objectName = 'senaz'
    # if (objectName not in nf.variables.keys()):
    #     print("No such object!")
    # vaa = read_image_Nc(indir_nc, objectName,1)
    #
    # objectName = 'senze'
    # if (objectName not in nf.variables.keys()):
    #     print("No such object!")
    # vza = read_image_Nc(indir_nc, objectName,1)

    objectName = 'elevation'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    ele = read_image_Nc(indir_nc, objectName,1)


    objectName = 't2m'
    if (objectName not in nf.variables.keys()):
        print("No such object!")
    ta_2m = read_image_Nc(indir_nc, objectName,1)


    # julian date to normal date
    jd = jul_date.astype(np.float)
    dt = map(lambda x:(julian.from_jd(x,fmt = 'jd')).strftime('%Y-%m-%d %H:%M:%S'),jd)
    dt = np.asarray((dt))

    bt_v = np.asarray(BT[0,:])
    bt_s = np.asarray(BT[1,:])
    bt_v_unc = np.asarray(BT_unc[0,:])
    bt_s_unc = np.asarray(BT_unc[1, :])
    emis_v = np.asarray(emis[0,:])
    emis_s = np.asarray(emis[1, :])
    # vaa_v = np.asarray(vaa[0,:])
    # vaa_s = np.asarray(vaa[1,:])
    # vza_v = np.asarray(vza[0,:])
    # vza_s = np.asarray(vza[1,:])

    # dataframe = pd.DataFrame({'time': dt, 'bt_v': bt_v,'bt_s':bt_s, 'bt_v_unc': bt_v_unc,'bt_s_unc':bt_s_unc,'bt_sky':BT_sky,'bt_sky_unc':BT_sky_unc,'emis_v':emis_v,'emis_s':emis_s,'lat':lat,'lon':lon,'lcc':lcc,'LST':LST,'LST_unc':LST_unc,'vaa_v':vaa_v,'vaa_s':vaa_s,'vza_v':vza_v,'vza_s':vza_s,'ta_2m':ta_2m})
    dataframe = pd.DataFrame(
        {'time': dt, 'bt_v': bt_v, 'bt_s': bt_s, 'bt_v_unc': bt_v_unc, 'bt_s_unc': bt_s_unc, 'bt_sky': BT_sky,
         'bt_sky_unc': BT_sky_unc, 'emis_v': emis_v, 'emis_s': emis_s,  'LST': LST,
         'LST_unc': LST_unc,'ta_2m': ta_2m})
    dataframe.to_csv(outdir_csv, index=False, sep=',',float_format="%.3f")




