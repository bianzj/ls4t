from utils.old.util import *
from util_lsct import *

'''2024.3.22'''
'''利用站点切片反演组分温度'''

indir_h5 = r"D:\data\AATSR_product\Fluxnet2015\AATSR_h5\\"
outdir_lsct = r"D:\data\AATSR_product\Fluxnet2015\AATSR_h5_re\\"

def cal_fvc_from_lai(thetav,lai):
    G = 0.5
    rd = np.pi / 180.0
    costhetanv = np.cos(thetav * rd)
    fvc = 1 - exp(-G*lai/costhetanv)
    fvc[fvc>1] = 1
    fvc[fvc<0] = 0
    return fvc

siteNames = search_dir(indir_h5,'')
for siteName in siteNames:
    indir_site = indir_h5  +  siteName
    fileNames = search_file(indir_site, '.csv')
    for fileName in fileNames:
        '''读取数据'''
        print(fileName)
        infile = indir_site + r"\\"+ fileName
        items = ["indx", "indy", "ref_indx", "ref_indy", "sec", "ref_tmie", "type", "emis_s", "emis_v", "lai", 'vzaN', 'vzaO',
         "lstN", "lstO", "Ts", "Tv"]
        [indx,iny,ref_indx,ref_indy,sec,ref_time,type,emis_s,emis_v,lai,vzaN,vzaO,lstN,lstO,Ts,Tv] = read_h5py_items(infile,items)
        lstN = lstN / 100
        lstO = lstO / 100
        vzaN = 90 - vzaN / 100
        vzaO = 90 - vzaO / 100

        '''计算fvc'''
        fvc_n = cal_fvc_from_lai(vzaN, lai)
        fvc_o = cal_fvc_from_lai(vzaO, lai)

        fvc_n[fvc_n > 1] = 1
        fvc_n[fvc_n < 0] = 0
        fvc_o[fvc_o > 1] = 1
        fvc_o[fvc_o < 0] = 0

        '''计算lsct'''
        lsct = inv_mpl_agl_multiple_2(lstN,lstO,emis_s,emis_v,fvc_n,fvc_o)

        lsct_save = np.zeros([31,31])
        lsct_save[0, :, 2:-2] = np.reshape(lsct[:, :, 0], [31, 31])
        lsct_save[1, :, 2:-2] = np.reshape(lsct[:, :, 1], [31, 31])





