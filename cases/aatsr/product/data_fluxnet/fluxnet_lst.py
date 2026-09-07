import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *

'''2024.3.19'''
'''通过上下行辐射计算温度'''
'''目前超级简单来做：土壤发射率0.92，植被发射率0.97，fvc根据lai计算'''
'''Ts = [(F上-（1-e宽）*F下)/玻尔兹曼*e宽]0.25'''
'''2025.11.4'''
'''通过fvc计算lst'''

def cal_lst_from_longwave(F_in,F_out,fvc,emis_s,emis_v):
    '''
    通过长波辐射计算lst Ts = [(F上-（1-e宽）*F下)/玻尔兹曼*e宽]0.25
    para F_in:
    para F_out:
    para fvc:
    para emis_s:
    para emis_v:
    '''
    stf_blzm_constant = 5.67 * (10**-8)
    F = 0.75
    emis = emis_s * (1-fvc) + emis_v * fvc + (1 - emis_s) * emis_v * F * (1 - fvc)
    temp1 = F_out - (1-emis) * F_in
    temp2 = temp1 / (stf_blzm_constant * emis)
    return temp2**(0.25)


if __name__ == '__main__':
    fluxnet_indir = r"/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/Fluxnet_data/"
    ifcal_lst = 0
    ifcal_invalid_sites_num = 1
    base_dir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/'
    infile_fluxnet = base_dir + r'FLUXSITE_imagexy.xlsx'
    data_emis = pd.read_excel(infile_fluxnet)

    if ifcal_lst:
        fileNames = search_file(fluxnet_indir,['.csv'])
        for fileName in fileNames:
            siteName = (fileName[:-4]).split('_')[0]
            print(siteName)
            infile = fluxnet_indir + fileName
            data = pd.read_csv(infile)
            # data['TIMESTAMP_START'] = pd.to_datetime(data['TIMESTAMP_START'], format='%Y%m%d%H%M')

            L_in = data['LW_IN_F']
            L_out = data['LW_OUT']
            fvc = data['fvc']/100
            lai = data['LAI']/1000
            emisS = data_emis[data_emis['SITE_ID'] == siteName]['emisS']
            emisV = data_emis[data_emis['SITE_ID'] == siteName]['emisV']
            ind = (L_out > 100) * (L_out < 1000) * (fvc < 100) * (fvc > 0)
            LST = np.full_like(L_in, -9999)
            LST[ind] = cal_lst_from_longwave(L_in[ind],L_out[ind],fvc[ind],float(emisS),float(emisV))
            data['LST'] = LST
            data.to_csv(fluxnet_indir + fileName,index=False)
    
    if ifcal_invalid_sites_num:
        fileNames = search_file(fluxnet_indir,['.csv'])
        fileNames.sort()
        invalid_sites_num = 0
        soil_sites = 0
        veg_sites = 0
        soil_sites_name = []
        veg_sites_name = []
        outfile_soil = base_dir + r'soil_sites.txt'
        outfile_veg = base_dir + r'veg_sites.txt'
        all_sites_num = len(fileNames)
        if os.path.exists(outfile_soil): os.remove(outfile_soil)
        if os.path.exists(outfile_veg): os.remove(outfile_veg)

        for fileName in fileNames:
            siteName = (fileName[:-4]).split('_')[0]
            print(siteName)
            infile = fluxnet_indir + fileName
            data = pd.read_csv(infile)
            LST = data['LST']
            fvc = data['fvc']/100
            if np.sum(LST > 300.0)>1:
                print(siteName)
                invalid_sites_num += 1

                if np.sum((fvc < 5) * (fvc > 0.1)) > 100:
                    with open(outfile_soil,'a') as f:
                        f.write(siteName + '\n')
                    soil_sites += 1
                    print('soil ',siteName)
                    soil_sites_name.append(siteName)
                if np.sum((fvc > 95) * (fvc < 100)) > 100:
                    with open(outfile_veg,'a') as f:
                        f.write(siteName + '\n')
                    veg_sites += 1
                    print('veg ',siteName)
                    veg_sites_name.append(siteName)
        print('soil_sites:',soil_sites)
        print('veg_sites:',veg_sites)
        print(invalid_sites_num,all_sites_num)