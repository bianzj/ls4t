from utils.old.util import *

'''2024.3.19'''
'''通过上下行辐射计算温度'''
'''目前超级简单来做：土壤发射率0.92，植被发射率0.97，fvc根据lai计算'''
'''Ts = [(F上-（1-e宽）*F下)/玻尔兹曼*e宽]0.25'''

infile_lai = r"D:\data\AATSR_product\Fluxnet2015\Aux_data\Fluxnet_LAI_2002-2012-MCD15A3H-061\LAI-fluxnet-2002-2012-MCD15A3H-061-results.csv"
lai_raw_dir = r"D:\data\AATSR_product\Fluxnet2015\Aux_data\Fluxnet_lai_site_raw\\"
lai_interpolate_dir = r"D:\data\AATSR_product\Fluxnet2015\Aux_data\Fluxnet_lai_site_interpolate\\"
fluxnet_indir = r"D:\data\AATSR_product\Fluxnet2015\Fluxnet_filter\\"
fluxnet_outdir_lst = r"D:\data\AATSR_product\Fluxnet2015\Fluxnet_filter_lst\\"

ifextract_lai = 0
ifinterpolate_lai = 0
ifcal_lst = 1

if ifextract_lai:
    data = pd.read_csv(infile_lai, usecols=['ID', 'Date', 'MCD15A3H_061_Lai_500m'])

    # 按照ID分组，并生成对应的CSV文件
    for name, group in data.groupby('ID'):
        print(name)
        group.to_csv(lai_raw_dir + f"{name}.csv", index=False)

if ifinterpolate_lai:
    fileNames = search_file(lai_raw_dir,['csv'])
    for site in fileNames:
        print(site)
        infile = lai_raw_dir + site
        df = pd.read_csv(infile,usecols=['Date', 'MCD15A3H_061_Lai_500m'])
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df_interpolated = df.resample('1D').interpolate()
        df_interpolated.to_csv(lai_interpolate_dir + site)

def cal_fvc_from_lai(thetav,lai):
    G = 0.5
    rd = np.pi / 180.0
    costhetanv = np.cos(thetav * rd)
    fvc = 1 - exp(-G*lai/costhetanv)
    fvc[fvc>1] = 1
    fvc[fvc<0] = 0
    return fvc

def cal_lst_from_longwave(F_in,F_out,fvc,emis_s,emis_v):
    '''
    通过长波辐射计算lst
    para F_in:
    para F_out:
    para fvc:
    para emis_s:
    para emis_v:
    '''
    stf_blzm_constant = 5.67 * (10**-8)
    emis = emis_s * (1-fvc) + emis_v * fvc
    temp1 = F_out - (1-emis) * F_in
    temp2 = temp1 / (stf_blzm_constant * emis)
    return temp2**(0.25)


    '''Ts = [(F上-（1-e宽）*F下)/玻尔兹曼*e宽]0.25'''


if ifcal_lst:
    emis_s = 0.92
    emis_v = 0.98
    fileNames = search_file(fluxnet_indir,['.csv'])
    for fileName in fileNames:
        siteName = (fileName[:-4]).split('_')[0]
        print(siteName)
        infile = fluxnet_indir + fileName
        data = pd.read_csv(infile)
        data['TIMESTAMP_START'] = pd.to_datetime(data['TIMESTAMP_START'], format='%Y%m%d%H%M')

        lai_file = lai_interpolate_dir + siteName + '.csv'
        lai = pd.read_csv(lai_file)
        lai['Date'] = pd.to_datetime(lai['Date'])  # 将Date列转换为日期时间对象
        lai_daily = lai.groupby(lai['Date'].dt.date).mean()  # 按日期对LAI进行每日平均

        # 将日期匹配后的LAI数据与其他数据进行合并
        data_merged = pd.merge(data, lai_daily, how='left', left_on=data['TIMESTAMP_START'].dt.date, right_index=True)

        L_in = data_merged['LW_IN_F']
        L_out = data_merged['LW_OUT']
        lai = data_merged['MCD15A3H_061_Lai_500m']
        ind = (L_out > 100) * (L_out < 1000) * (lai != np.nan)
        fvc = cal_fvc_from_lai(0,lai)
        emis = fvc * emis_v + (1-fvc)*emis_s
        LST = cal_lst_from_longwave(L_in[ind],L_out[ind],fvc[ind],emis_s,emis_v)
        data_merged['emis'] = emis
        data_merged['lst'] = LST
        data_merged['TIMESTAMP_START'] = data_merged['TIMESTAMP_START'].dt.strftime('%Y%m%d%H%M')
        data_merged.to_csv(fluxnet_outdir_lst + fileName)
