import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from AATSR_product.util.util_aatsr import *
from datetime import datetime, timezone
import calendar
import warnings
warnings.filterwarnings("ignore")

'''2025.12.14'''
'''补充了异常值的限制'''
'''2025.12.12'''
'''两角度 单像元 ls求解（用更新后的函数）'''
'''经验正和原始v0版本结果一样，且修正了晚上结果错误的问题'''
'''ridge和ls结果差不多，甚至有时候ridge结果更离谱，且时间明显长（40s vs 1000s）'''

if __name__ == '__main__':
    years = np.arange(2007, 2008)
    months = np.arange(7, 8)
    method = 'ls'

    indir_obs = r'/media/hero/lsct03/aatsr_obs/'
    indir_clo = r'/media/hero/lsct03/aatsr_clo/'
    indir_ang = r'/media/hero/lsct03/aatsr_ang/'
    indir_loc = r'/media/hero/lsct04/aatsr_loc/'
    indir_lst = r'/media/hero/lsct04/aatsr_lst/'
    indir_aux = r'/media/hero/lsct04/aatsr_aux/'
    outdir_lsct = r'/home/hero/data/AATSR/global_test/aatsr_lsct_v1.1/'

    n, m = 2,2 # 角度数，组分数
    ws = 1 # 多像元窗口大小
    wl = 10.8

    lst_min, lst_max = 250, 350
    lsct_min ,lsct_max = 250, 350
    fvc_min, fvc_max = 0.03, 0.97  # LAI 0.05 7.0 -> fvc 0.03 0.97 注意fvc只限制nadir
    rad_min, rad_max = 4.0, 20.0 # Rad 4.0 20.0 -> 250.6K 357.5K

    emis_s_arr, emis_v_arr, classif_arr,  vzaN_arr, vzaO_arr, vaaN_arr, vaaO_arr = aatsr_read_aux_data()

    for year in years:
        for month in months:
            daynum = calendar.monthrange(year, month)[1]
            for day in range(1, daynum + 1):
                time_str = f'{year}/{month:02d}/{day:02d}/'
                if not os.path.exists(indir_lst+time_str): continue
                print(f'{year}-{month:02d}-{day:02d}')
                fileNames = search_file_rej(indir_obs+time_str, ['h5'],'xml')
                fileNum = len(fileNames)
                for i,fileName in enumerate(fileNames):
                    print(f'  {i+1}/{fileNum}: {fileName}')
                    start_time = time.time()
                    basename = os.path.basename(fileName)
                    infile_obs = indir_obs + time_str + basename
                    infile_lst = indir_lst + time_str + basename.replace('obs', 'lst')
                    infile_clo = indir_clo + time_str + basename.replace('obs', 'clo')
                    infile_ang = indir_ang + time_str + basename.replace('obs', 'ang')
                    infile_loc = indir_loc + time_str + basename.replace('obs', 'loc')
                    infile_aux = indir_aux + time_str + basename.replace('obs', 'aux')
                    outfile = outdir_lsct + time_str + basename.replace('obs', 'lsct_v1.1')
                    if os.path.exists(outfile):
                        print(f'    已存在lsct文件: {outfile}')
                        continue

                    if not os.path.exists(infile_lst): 
                        print(f'    不存在lst文件: {infile_lst}')
                        continue
                    if not os.path.exists(infile_clo): 
                        print(f'    不存在clo文件: {infile_clo}')
                        continue
                    if not os.path.exists(infile_ang): 
                        print(f'    不存在ang文件: {infile_ang}')
                        continue
                    if not os.path.exists(infile_loc): 
                        print(f'    不存在loc文件: {infile_loc}')
                        continue

                    # 读取数据
                    lstN, lstF = aatsr_read_lst(infile_lst)
                    nl, ns = lstN.shape[0], lstF.shape[1] # 行列数
                    cloN_mask , cloF_mask = aatsr_read_clo(infile_clo)
                    indx, indy = aatsr_read_loc(infile_loc, iflonlat = 0)
                    lai = aatsr_read_lai(infile_aux)
                    sza, saa, vzaN, vzaF, vaaN, vaaF = aatsr_read_angle(infile_ang,ifsun = 1, ifview = 1)
                    # vzaN,vzaF,vaaN,vaaF =vzaN_arr,vzaO_arr,vaaN_arr,vaaO_arr

                    # 1. 计算有效发射率矩阵
                    hspot = 0.2
                    emisS, emisV = emis_s_arr[indx, indy], emis_v_arr[indx, indy]
                    classif = classif_arr[indx, indy]
                    vza = np.stack((vzaN, vzaF), axis=2)
                    vaa = np.stack((vaaN, vaaF), axis=2)

                    w = cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vza, sza, vaa, saa, n , m)

                    # 2.计算观测亮度矩阵 b
                    bN = cal_rad_from_lst(lstN,wl,lai,vzaN,emisS,emisV)
                    bF = cal_rad_from_lst(lstF,wl,lai,vzaF,emisS,emisV)
                    b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2) # 形状: (nl, ns, m)

                    # 3. 多线程求解
                    inv_start_time = time.time()
                    ### mask 处, 注意fvc仅mask了nadir，lst是都mask的
                    fvcN = cal_fvc_from_lai(vzaN, lai)
                    cloN_mask = cloN_mask * (fvcN>fvc_min)*(fvcN<fvc_max)
                    lst = np.concatenate([lstN[:,:,np.newaxis], lstF[:,:,np.newaxis]], axis=2)
                    mask = np.concatenate([cloN_mask[:,:,np.newaxis], cloF_mask[:,:,np.newaxis]], axis=2)
                    mask = mask * (lst>lst_min)*(lst<lst_max)


                    ### 多进程求解 每列多线程
                    off = 0
                    para = []
                    for kn in range(off, ns-off):
                        wLine = w[:,kn-off:kn+off+1,:,:]
                        bLine = b[:,kn-off:kn+off+1,:]
                        maskLine = mask[:,kn-off:kn+off+1,:]
                        para.append([wLine,bLine,maskLine,n,m,wl,method])
                    
                    tasks= []
                    pool = Pool(min(192,cpu_count()))
                    tasks = [pool.apply_async(inv_lsct_point, tuple(p)) for p in para]
                    pool.close()
                    pool.join()
                    results = [t.get() for t in tasks]

                    lsct = np.zeros((nl, ns, m))
                    for idx, res in enumerate(results):
                        kn = idx + off
                        # 如果 res 形状是 (nl, m)，直接赋值
                        lsct[:, kn, :] = res.squeeze()
                    end_time = time.time()
                    print(f"    反演完成，耗时: {end_time - inv_start_time:.4f}秒")

                    # mask 掉结果异常值
                    Ts = lsct[:,:,0]
                    Tv = lsct[:,:,1]
                    ind = (Ts<lsct_min)+(Ts>lsct_max)+(Tv<lsct_min)+(Tv>lsct_max)
                    Ts[ind] = np.nan
                    Tv[ind] = np.nan
                    Ts = Ts * 100
                    Tv = Tv * 100
                    mkdir_if_not_exist(outdir_lsct+time_str)

                    metadata = {
                        'Author': 'Yifan Lu',
                        'Supervisor': 'Zunjian Bian, Qing Xiao',
                        'Version': 'v1.1',
                        'Create_time': datetime.now(timezone.utc).isoformat() + 'Z',
                        'Description': 'AATSR v1 product: dual angle, single pixel, lai , no constraints',
                        'Solve method': method,
                        'Window size': ws
                    }
                    with h5py.File(outfile, 'w') as h5f:
                        for key, value in metadata.items():
                            h5f.attrs[key] = value

                        Ts_data = h5f.create_dataset('Ts', data=Ts, dtype='uint16', compression='gzip')
                        Ts_data.attrs['scalar'] = '0.01'

                        Tv_data = h5f.create_dataset('Tv', data=Tv, dtype='uint16', compression='gzip')
                        Tv_data.attrs['scalar'] = '0.01'
                    end_time = time.time()
                    print(f"执行时间: {end_time - start_time:.4f}秒")