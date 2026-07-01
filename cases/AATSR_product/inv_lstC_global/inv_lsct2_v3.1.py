import sys
import os
import traceback # 用于获取详细报错信息
from multiprocessing import Pool, cpu_count 
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

'''2025.12.14'''
'''补充了异常值的限制'''
'''2025.12.12'''
'''两角度 多像元同温 + bayesian'''
'''要求是要输出v1和v2、v3'''

def inv_lsct2_v3_1(w, b, mask, lst, n, m=2, ws=5, wl=10.8, method='ls', ifcons=0):
    '''
    多角度 多组分 窗口反演 BFGS/powell/SLSQP/L-BFGS-B/TNC
    优化版: 移除了 np.matrix，优化了 Bayesian 矩阵运算
    '''
    off = ws // 2 # 窗口偏移量
    nl, ns = w.shape[0], w.shape[1]
    result = np.zeros([nl, ns, 8])
    
    # 提前计算常量
    Cm_inv = np.linalg.inv(np.diag([soil_radiance_variance, leaf_radiance_variance]))
    inv_sensor_noise = 1.0 / sensor_noise 

    for i in range(off, nl - off):
        for j in range(off, ns - off):
            if np.sum(mask[i, j, :]) >= n:
                # v0 版本 多像元异温
                w_win = w[i-off:i+off+1, j-off:j+off+1, :, :]
                b_win = b[i-off:i+off+1, j-off:j+off+1, :]
                mask_win = mask[i-off:i+off+1, j-off:j+off+1, :]
                weight = set_weights(ws)
                p0 = fitting_Nangle_Mcomponent_window_quadratic(w_win, b_win, n, m, mask_win, weight, window_size=5)
                result[i, j, :2] = p0

                ### v1 版本 单像元解
                w_point = w[i, j, :, :]
                b_point = b[i, j, :]
                mask_point = mask[i, j, :]
                p1 = fitting_Nangle_Mcomponent_point(w_point[mask_point], b_point[mask_point], n, m, method)
                result[i, j, 2:4] = p1

                ### v2 版本 多像元同温解
                n_win = np.sum(mask_win)
                p2 = fitting_Nangle_Mcomponent_point(w_win[mask_win], b_win[mask_win], n_win, m, method='ls')
                result[i, j, 4:6] = p2

                ### v3 版本 bayesian (极速优化版)
                w_arr = w_point # shape (n, m)
                b_arr = b_point # shape (n,)
                p2_arr = p2     # shape (m,)
                
                KT = w_arr.T
                KTK = KT @ w_arr
                posterior_cov_inv = KTK * inv_sensor_noise + Cm_inv
                
                KTb = KT @ b_arr
                term2 = KTb * inv_sensor_noise + Cm_inv @ p2_arr
                
                try:
                    p3 = np.linalg.solve(posterior_cov_inv, term2)
                    result[i, j, 6:] = p3
                except np.linalg.LinAlgError:
                    result[i, j, 6:] = np.nan
            else:
                result[i, j, :] = np.nan
                
    lsct = inv_planck(wl, result)
    return lsct


if __name__ == '__main__':
    # 定义错误日志路径
    ERROR_LOG_FILE = r'/media/hero/lsct04/inv_aatsr_v3_errorlog.txt'

    years = np.arange(2007, 2008)
    months = np.arange(7, 8)
    method = 'ls'

    indir_obs = r'/media/hero/lsct03/aatsr_obs/'
    indir_clo = r'/media/hero/lsct03/aatsr_clo/'
    indir_ang = r'/media/hero/lsct03/aatsr_ang/'
    indir_loc = r'/media/hero/lsct04/aatsr_loc/'
    indir_lst = r'/media/hero/lsct04/aatsr_lst/'
    indir_aux = r'/media/hero/lsct04/aatsr_aux/'
    outdir_lsct_v0_1 = r'/home/hero/data/AATSR/global_test/aatsr_lsct_v0.1(combined)2/'
    outdir_lsct_v1_1 = r'/home/hero/data/AATSR/global_test/aatsr_lsct_v1.1(combined)2/'
    outdir_lsct_v2_1 = r'/home/hero/data/AATSR/global_test/aatsr_lsct_v2.1(combined)2/'
    outdir_lsct_v3_1 = r'/home/hero/data/AATSR/global_test/aatsr_lsct_v3.1(combined)2/'

    n, m = 2, 2 
    ws = 5 
    wl = 10.8

    lst_min, lst_max = 250, 350
    lsct_min ,lsct_max = 250, 350
    fvc_min, fvc_max = 0.03, 0.97
    rad_min, rad_max = 4.0, 20.0

    soil_radiance_variance = 2.0
    leaf_radiance_variance = 1.0
    sensor_noise = 0.05

    emis_s_arr, emis_v_arr, classif_arr, vzaN_arr, vzaO_arr, vaaN_arr, vaaO_arr = aatsr_read_aux_data()

    pool = Pool(min(192, cpu_count()))

    try:
        for year in years:
            for month in months:
                daynum = calendar.monthrange(year, month)[1]
                for day in range(1, daynum + 1):
                    time_str = f'{year}/{month:02d}/{day:02d}/'
                    if not os.path.exists(indir_lst+time_str): continue
                    print(f'{year}-{month:02d}-{day:02d}')
                    fileNames = search_file_rej(indir_obs+time_str, ['h5'],'xml')
                    fileNum = len(fileNames)
                    
                    for i, fileName in enumerate(fileNames):
                        # 【新增】单文件错误捕获开始
                        try:
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
                            outfile_lsct_v1_1 = outdir_lsct_v1_1 + time_str + basename.replace('obs', 'lsct_v1.1')
                            outfile_lsct_v2_1 = outdir_lsct_v2_1 + time_str + basename.replace('obs', 'lsct_v2.1')
                            outfile_lsct_v3_1 = outdir_lsct_v3_1 + time_str + basename.replace('obs', 'lsct_v3.1')

                            if os.path.exists(outfile_lsct_v0_1) and os.path.exists(outfile_lsct_v1_1) and \
                               os.path.exists(outfile_lsct_v2_1) and os.path.exists(outfile_lsct_v3_1):
                                print(f'    已存在lsct文件: {outfile_lsct_v3_1}')
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
                            nl, ns = lstN.shape[0], lstF.shape[1]
                            cloN_mask , cloF_mask = aatsr_read_clo(infile_clo)
                            indx, indy = aatsr_read_loc(infile_loc, iflonlat = 0)
                            lai = aatsr_read_lai(infile_aux)
                            sza, saa, vzaN, vzaF, vaaN, vaaF = aatsr_read_angle(infile_ang,ifsun = 1, ifview = 1)

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
                            b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2)

                            # 3. 多线程求解
                            inv_start_time = time.time()
                            fvcN = cal_fvc_from_lai(vzaN, lai)
                            cloN_mask = cloN_mask * (fvcN>fvc_min)*(fvcN<fvc_max)
                            lst = np.concatenate([lstN[:,:,np.newaxis], lstF[:,:,np.newaxis]], axis=2)
                            mask = np.concatenate([cloN_mask[:,:,np.newaxis], cloF_mask[:,:,np.newaxis]], axis=2)
                            mask = mask * (lst>lst_min)*(lst<lst_max)

                            off = ws // 2
                            para = []
                            for kn in range(off, ns-off):
                                wLine = w[:,kn-off:kn+off+1,:,:]
                                bLine = b[:,kn-off:kn+off+1,:]
                                maskLine = mask[:,kn-off:kn+off+1,:]
                                lstLine = lst[:,kn-off:kn+off+1,:]
                                para.append([wLine,bLine,maskLine,lstLine,n,m,ws,wl,method])
                            
                            tasks = [pool.apply_async(inv_lsct2_v3_1, tuple(p)) for p in para]
                            results = [t.get() for t in tasks]

                            # 【重要修正】移除了重复的初始化，只保留一次赋值
                            lsct = np.zeros((nl, ns, 8))
                            for idx, res in enumerate(results):
                                kn = idx + off
                                lsct[:, kn, :] = res[:,off,:]

                            end_time = time.time()
                            print(f"    反演完成，耗时: {end_time - inv_start_time:.4f}秒")

                            ### v0.1 保存结果
                            Ts = lsct[:,:,0]
                            Tv = lsct[:,:,1]
                            ind = (Ts<lsct_min)+(Ts>lsct_max)+(Tv<lsct_min)+(Tv>lsct_max)
                            Ts[ind] = np.nan; Tv[ind] = np.nan
                            Ts = Ts * 100; Tv = Tv * 100
                            mkdir_if_not_exist(outdir_lsct_v0_1+time_str)
                            if os.path.exists(outfile_lsct_v0_1): os.remove(outfile_lsct_v0_1)

                            metadata = {
                                'Author': 'Yifan Lu',
                                'Supervisor': 'Zunjian Bian, Qing Xiao',
                                'Version': 'v0.1',
                                'Create_time': datetime.now(timezone.utc).isoformat() + 'Z',
                                'Description': 'AATSR v0 product:inv_lsct2_lai_winquad_noconstraint',
                                'Solve method': method,
                                'Window size': ws
                            }
                            with h5py.File(outfile_lsct_v0_1, 'w') as h5f:
                                for key, value in metadata.items(): h5f.attrs[key] = value
                                Ts_data = h5f.create_dataset('Ts', data=Ts, dtype='uint16', compression='gzip')
                                Ts_data.attrs['scalar'] = '0.01'
                                Tv_data = h5f.create_dataset('Tv', data=Tv, dtype='uint16', compression='gzip')
                                Tv_data.attrs['scalar'] = '0.01'

                            ### v1.1 保存结果
                            Ts = lsct[:,:,2]
                            Tv = lsct[:,:,3]
                            ind = (Ts<lsct_min)+(Ts>lsct_max)+(Tv<lsct_min)+(Tv>lsct_max)
                            Ts[ind] = np.nan; Tv[ind] = np.nan
                            Ts = Ts * 100; Tv = Tv * 100
                            mkdir_if_not_exist(outdir_lsct_v1_1+time_str)
                            if os.path.exists(outfile_lsct_v1_1): os.remove(outfile_lsct_v1_1)

                            metadata['Version'] = 'v1.1'
                            metadata['Description'] = 'AATSR v1 product:inv_lsct2_lai_pixel_noconstraint'
                            with h5py.File(outfile_lsct_v1_1, 'w') as h5f:
                                for key, value in metadata.items(): h5f.attrs[key] = value
                                Ts_data = h5f.create_dataset('Ts', data=Ts, dtype='uint16', compression='gzip')
                                Tv_data = h5f.create_dataset('Tv', data=Tv, dtype='uint16', compression='gzip')
                            
                            ### v2.1 保存结果
                            Ts = lsct[:,:,4]
                            Tv = lsct[:,:,5]
                            ind = (Ts<lsct_min)+(Ts>lsct_max)+(Tv<lsct_min)+(Tv>lsct_max)
                            Ts[ind] = np.nan; Tv[ind] = np.nan
                            Ts = Ts * 100; Tv = Tv * 100
                            mkdir_if_not_exist(outdir_lsct_v2_1+time_str)
                            if os.path.exists(outfile_lsct_v2_1): os.remove(outfile_lsct_v2_1)

                            metadata['Version'] = 'v2.1'
                            metadata['Description'] = 'AATSR v2 product:inv_lsct2_lai_wincons_noconstraint'
                            with h5py.File(outfile_lsct_v2_1, 'w') as h5f:
                                for key, value in metadata.items(): h5f.attrs[key] = value
                                Ts_data = h5f.create_dataset('Ts', data=Ts, dtype='uint16', compression='gzip')
                                Tv_data = h5f.create_dataset('Tv', data=Tv, dtype='uint16', compression='gzip')

                            ### v3.1 保存结果
                            Ts = lsct[:,:,6]
                            Tv = lsct[:,:,7]
                            ind = (Ts<lsct_min)+(Ts>lsct_max)+(Tv<lsct_min)+(Tv>lsct_max)
                            Ts[ind] = np.nan; Tv[ind] = np.nan
                            Ts = Ts * 100; Tv = Tv * 100
                            mkdir_if_not_exist(outdir_lsct_v3_1+time_str)
                            if os.path.exists(outfile_lsct_v3_1): os.remove(outfile_lsct_v3_1)

                            metadata['Version'] = 'v3.1'
                            metadata['Description'] = 'AATSR v3 product:inv_lsct2_lai_wincons_noconstraint_bayesian'
                            metadata['Sensor noise & soil/leaf variance'] = '%.2f, %.2f, %.2f' %(sensor_noise,soil_radiance_variance,leaf_radiance_variance)
                            
                            with h5py.File(outfile_lsct_v3_1, 'w') as h5f:
                                for key, value in metadata.items(): h5f.attrs[key] = value
                                Ts_data = h5f.create_dataset('Ts', data=Ts, dtype='uint16', compression='gzip')
                                Ts_data.attrs['scalar'] = '0.01'
                                Tv_data = h5f.create_dataset('Tv', data=Tv, dtype='uint16', compression='gzip')
                                Tv_data.attrs['scalar'] = '0.01'
                                
                            print(f"    完成: {time.time() - start_time:.2f}秒")

                        except Exception as e:
                            # 【错误日志记录】
                            print(f"    处理文件 {fileName} 时发生错误，已跳过。请查看日志。")
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            error_msg = traceback.format_exc()
                            
                            with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
                                f.write("="*60 + "\n")
                                f.write(f"Time: {current_time}\n")
                                f.write(f"File: {fileName}\n")
                                f.write(f"Error Type: {type(e).__name__}\n")
                                f.write(f"Error Message: {str(e)}\n")
                                f.write("Traceback:\n")
                                f.write(error_msg)
                                f.write("\n")
                            continue # 继续下一个文件
    finally:
        pool.close()
        pool.join()