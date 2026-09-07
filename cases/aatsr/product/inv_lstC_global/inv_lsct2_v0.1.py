import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1" 
os.environ["OPENBLAS_NUM_THREADS"] = "1" 
os.environ["VECLIB_MAXIMUM_THREADS"] = "1" 
os.environ["NUMEXPR_NUM_THREADS"] = "1"
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from AATSR_product.util.util_aatsr import *
from datetime import datetime, timezone
import calendar
import time
import warnings
warnings.filterwarnings("ignore")
from numpy.lib.stride_tricks import sliding_window_view

'''2025.12.15'''
'''两角度 多像元异温，重构版本'''
'''要求是要输出v1和v2'''

def inv_lsct2_winquad(w, b, mask,n, m=2, ws=5,wl=10.8,if_bayesian = 1):
    '''
    多角度 多组分 窗口反演 假设窗口内组分温度分布为二次函数
    :param n: 角度数
    :param m: 组分数
    :param ws: 窗口大小
    :param wl: 波长
    :param w: 有效发射率矩阵 shape(nl,ns,n,m)
    :param b: 亮温矩阵 shape(nl,ns,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(nl,ns,n)
    :param if_bayesian: 是否使用贝叶斯联合单点解
    :return: p： 组分温度 shape(nl,ns,m）
    '''
    off = ws // 2 
    weights = set_weights(ws) 
    nl, ns = w.shape[0], w.shape[1]
    result = np.zeros([nl, ns, m])
    weight = set_weights(ws)
    
    Cm_mat = np.matrix(np.diag([soil_radiance_variance, leaf_radiance_variance]))
    Cm_inv = np.linalg.inv(Cm_mat)

    for i in range(off, nl - off):
        for j in range(off, ns - off):
            if np.sum(mask[i, j, :]) >= n:
                w_win = w[i-off:i+off+1, j-off:j+off+1, :, :]
                b_win = b[i-off:i+off+1, j-off:j+off+1, :]
                mask_win = mask[i-off:i+off+1, j-off:j+off+1, :]
                
                # 初始拟合
                p = fitting_Nangle_Mcomponent_window_quadratic(w_win, b_win, n, m, mask_win, weight, window_size=5)

                if if_bayesian:
                    w_point = w[i,j,:,:]
                    b_point = b[i,j,:]
                    mask_point = mask[i,j,:]

                    w_mat = np.matrix(w_point)
                    b_vec = np.matrix(b_point).T 
                    if b_vec.shape[1] != 1: b_vec = b_vec.T
                    p_vec = np.matrix(p).T
                    
                    Cd_mat = np.matrix(np.diag(np.ones(n)) * sensor_noise)
                    Cd_inv = np.linalg.inv(Cd_mat)
                    
                    # Term 1: (W^T * Cd^-1 * W + Cm^-1)^-1
                    # 形状: (m,n) * (n,n) * (n,m) + (m,m) -> (m,m)
                    posterior_cov_inv = np.transpose(w_mat) * Cd_inv * w_mat + Cm_inv
                    pre = np.linalg.inv(posterior_cov_inv)
                    
                    # Term 2: W^T * Cd^-1 * b + Cm^-1 * p_prior
                    # 形状: (m,n)*(n,n)*(n,1) + (m,m)*(m,1) -> (m,1)
                    term2 = np.transpose(w_mat) * Cd_inv * b_vec + Cm_inv * p_vec
                    
                    # Result: (m,m) * (m,1) -> (m,1)
                    p = pre * term2
                    
                    # 赋值前转回扁平数组，匹配 result 的维度
                    p = np.array(p).flatten()
                result[i, j, :] = p
            else:
                result[i, j, :] = np.nan
                
    lsct = inv_planck(wl, result)
    return lsct

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
    outdir_lsct_v0_1 = r'/home/hero/data/AATSR/global_test/aatsr_lsct_v0.1/'

    n, m = 2,2 # 角度数，组分数
    ws = 5 # 多像元窗口大小
    wl = 10.8

    lst_min, lst_max = 250, 350
    lsct_min ,lsct_max = 250, 350
    fvc_min, fvc_max = 0.03, 0.97  # LAI 0.05 7.0 -> fvc 0.03 0.97 注意fvc只限制nadir
    rad_min, rad_max = 4.0, 20.0 # Rad 4.0 20.0 -> 250.6K 357.5K

    soil_radiance_variance = 2.0
    leaf_radiance_variance = 1.0
    sensor_noise = 0.05

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
                    outfile_lsct_v0_1 = outdir_lsct_v0_1 + time_str + basename.replace('obs', 'lsct_v0.1')

                    if os.path.exists(outfile_lsct_v0_1):
                        print(f'    已存在lsct文件: {outfile_lsct_v0_1}')
                        os.remove(outfile_lsct_v0_1)
                        # continue

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

                    end_time = time.time()
                    print(f"    数据读取时间，耗时: {end_time - start_time:.4f}秒")

                    # 1. 计算有效发射率矩阵
                    emis_start_time = time.time()
                    hspot = 0.2
                    emisS, emisV = emis_s_arr[indx, indy], emis_v_arr[indx, indy]
                    classif = classif_arr[indx, indy]
                    vza = np.stack((vzaN, vzaF), axis=2)
                    vaa = np.stack((vaaN, vaaF), axis=2)

                    w = cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vza, sza, vaa, saa, n , m)
                    # fvc_n = cal_fvc_from_lai(vzaN, lai)
                    # fvc_o = cal_fvc_from_lai(vzaF, lai)

                    # fvc_n[fvc_n > 1] = 1
                    # fvc_n[fvc_n < 0] = 0
                    # fvc_o[fvc_o > 1] = 1
                    # fvc_o[fvc_o < 0] = 0

                    # wN = np.asarray([emisS * (1 - fvc_n) , emisV * (fvc_n)])
                    # wO = np.asarray([emisS * (1 - fvc_o) , emisV * (fvc_o)])
                    # wN = np.transpose(wN, (1, 2, 0))
                    # wO = np.transpose(wO, (1, 2, 0))
                    # w = np.concatenate([wN[:,:,np.newaxis,:], wO[:,:,np.newaxis,:]], axis=2) # 形状: (nl, ns, n,m)

                    end_time = time.time()
                    print(f"    计算发射率矩阵，耗时: {end_time - emis_start_time:.4f}秒")

                    # 2.计算观测亮度矩阵 b
                    b_start_time = time.time()
                    bN = cal_rad_from_lst(lstN,wl,lai,vzaN,emisS,emisV)
                    bF = cal_rad_from_lst(lstF,wl,lai,vzaF,emisS,emisV)
                    b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2) # 形状: (nl, ns, m)
                    end_time = time.time()
                    print(f"    计算观测亮度矩阵，耗时: {end_time - b_start_time:.4f}秒")

                    # 3. 多线程求解
                    inv_start_time = time.time()
                    ### mask 处, 注意fvc仅mask了nadir，lst是都mask的
                    fvcN = cal_fvc_from_lai(vzaN, lai)
                    cloN_mask = cloN_mask * (fvcN>fvc_min)*(fvcN<fvc_max)
                    lst = np.concatenate([lstN[:,:,np.newaxis], lstF[:,:,np.newaxis]], axis=2)
                    mask = np.concatenate([cloN_mask[:,:,np.newaxis], cloF_mask[:,:,np.newaxis]], axis=2)
                    mask = mask * (lst>lst_min)*(lst<lst_max)

                    ### 多进程求解 每列多线程
                    off = ws // 2
                    para = []
                    for kn in range(off, ns-off):
                        wLine = w[:,kn-off:kn+off+1,:,:]
                        bLine = b[:,kn-off:kn+off+1,:]
                        maskLine = mask[:,kn-off:kn+off+1,:]
                        para.append([wLine,bLine,maskLine,n,m,ws,wl,0])

                    tasks= []
                    pool = Pool(min(192,cpu_count()))
                    tasks = [pool.apply_async(inv_lsct2_winquad, tuple(p)) for p in para]
                    pool.close()
                    pool.join()
                    results = [t.get() for t in tasks]

                    lsct = np.zeros((nl, ns, m))
                    for idx, res in enumerate(results):
                        kn = idx + off
                        # 如果 res 形状是 (nl, m)，直接赋值
                        lsct[:, kn, :] = res[:,off,:]

                    end_time = time.time()
                    print(f"    反演完成，耗时: {end_time - inv_start_time:.4f}秒")

                    ### v0.1 保存结果
                    # mask 掉结果异常值
                    Ts = lsct[:,:,0]
                    Tv = lsct[:,:,1]
                    ind = (Ts<lsct_min)+(Ts>lsct_max)+(Tv<lsct_min)+(Tv>lsct_max)
                    Ts[ind] = np.nan
                    Tv[ind] = np.nan
                    Ts = Ts * 100
                    Tv = Tv * 100
                    mkdir_if_not_exist(outdir_lsct_v0_1+time_str)
                    if os.path.exists(outfile_lsct_v0_1): os.remove(outfile_lsct_v0_1)

                    metadata = {
                        'Author': 'Yifan Lu',
                        'Supervisor': 'Zunjian Bian, Qing Xiao',
                        'Version': 'v0.1',
                        'Create_time': datetime.now(timezone.utc).isoformat() + 'Z',
                        'Description': 'AATSR v1 product: dual angle, single pixel, lai , no constraints',
                        'Solve method': method,
                        'Window size': ws
                    }
                    with h5py.File(outfile_lsct_v0_1, 'w') as h5f:
                        for key, value in metadata.items():
                            h5f.attrs[key] = value

                        Ts_data = h5f.create_dataset('Ts', data=Ts, dtype='uint16', compression='gzip')
                        Ts_data.attrs['scalar'] = '0.01'

                        Tv_data = h5f.create_dataset('Tv', data=Tv, dtype='uint16', compression='gzip')
                        Tv_data.attrs['scalar'] = '0.01'