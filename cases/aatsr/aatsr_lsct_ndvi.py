from base.lsct_window import fitting_Nangle_Mcomponent_window
import os
import sys
import time
from datetime import datetime, timezone
from multiprocessing import Pool
from multiprocessing import cpu_count
import calendar
import h5py
import numpy as np
import warnings
from numpy import min
from cases.aatsr.util_aatsr import aatsr_read_NDVI, aatsr_read_aux_data, aatsr_read_clo, aatsr_read_loc, aatsr_read_lst
from base.files import mkdir_if_not_exist, read_h5py_item, search_file_rej
from base.lsct import cal_rad_from_lst_fvc, constraint_func_Nangle_2component, set_weights, set_x0_bnds_Nangle_Mcomponent
from base.radiometry import inv_planck

warnings.filterwarnings("ignore")

'''2025.10.7'''
'''两角度 多像元 NDVI计算FVC'''

def aatsr_inv_lsct2_window(n, m, ws, wl, w, b, mask, lst):
    off = ws//2 # 窗口偏移量
    weights = set_weights(ws) # 窗口权重
    nl,ns = w.shape[0], w.shape[1]
    result = np.zeros([nl,ns,m])
    for i in range(off,nl-off):
        for j in range(off,ns-off):
            if np.sum(mask[i,j,:]) >= n:
                w_win = w[i-off:i+off+1,j-off:j+off+1,:,:]
                b_win = b[i-off:i+off+1,j-off:j+off+1,:]
                mask_win = mask[i-off:i+off+1,j-off:j+off+1,:]
                lst_win = lst[i-off:i+off+1,j-off:j+off+1,:]

                # 两组分温差约束
                d = [-5,30]
                constraints = {
                    'type': 'ineq',  # 不等式约束
                    'fun': constraint_func_Nangle_2component,
                    'args': (lst_win, d,ws, wl)  # 注意是元组
                }

                x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst_win,n,m,ws)

                p = fitting_Nangle_Mcomponent_window(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method='SLSQP')
                result[i,j,:] = p
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    return lsct

def aatsr_inv_lsct2_Line(n, m, ws, wl, w, b, mask, lst):
    off = ws//2 # 窗口偏移量
    weights = set_weights(ws) # 窗口权重
    nl,ns = w.shape[0], w.shape[1]
    result = np.zeros([nl,ns,m])
    for i in range(off,nl-off):
        for j in range(off,ns-off):
            if np.sum(mask[i,j,:]) >= n:
                w_win = w[i-off:i+off+1,j-off:j+off+1,:,:]
                b_win = b[i-off:i+off+1,j-off:j+off+1,:]
                mask_win = mask[i-off:i+off+1,j-off:j+off+1,:]
                lst_win = lst[i-off:i+off+1,j-off:j+off+1,:]

                # 两组分温差约束
                d = [-5,30]
                constraints = {
                    'type': 'ineq',  # 不等式约束
                    'fun': constraint_func_Nangle_2component,
                    'args': (lst_win, d,ws, wl)  # 注意是元组
                }

                x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst_win,n,m,ws)

                p = fitting_Nangle_Mcomponent_window(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method='SLSQP')
                result[i,j,:] = p
            else:
                result[i,j,:] = np.nan
    lsct = inv_planck(wl,result)
    if ns == ws:
        return lsct[:,ws//2,:]
    elif ns > ws:
        return lsct[:,off:ns-off,:]

if __name__ == '__main__':
    years = np.arange(2009, 2010)
    months = np.arange(9, 13)

    indir_obs = r'/media/hero/lsct03/aatsr_obs/'
    indir_clo = r'/media/hero/lsct03/aatsr_clo/'
    indir_ang = r'/media/hero/lsct03/aatsr_ang/'
    indir_loc = r'/media/hero/lsct04/aatsr_loc/'
    indir_lst = r'/media/hero/lsct04/aatsr_lst/'
    outdir_lsct = r'/media/hero/lsct04/aatsr_lsct_NDVI/'

    # 赵静老师给的NDVI范围（Muxihan 2017 / Zhaojing 2020 JAG）
    # 取系数的大概中位数
    ndvi_max = 0.87
    ndvi_min = 0.04
    k = 1
    lst_min, lst_max = 250, 350
    n, m = 2,2 # 角度数，组分数
    ws = 5 # 多像元窗口大小
    wl = 10.8

    emis_s_arr, emis_v_arr, classif_arr,  vzaN_arr, vzaO_arr, vaaN_arr, vaaO_arr = aatsr_read_aux_data()

    for year in years:
        for month in months:
            daynum = calendar.monthrange(year, month)[1]
            for day in range(1, daynum + 1):
                time_str = f'{year}/{month:02d}/{day:02d}/'
                if not os.path.exists(indir_obs+time_str): continue
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
                    outfile = outdir_lsct + time_str + basename.replace('obs', 'lsct')
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
                    ndviN, ndviF = aatsr_read_NDVI(infile_obs)
                    cloN_mask , cloF_mask = aatsr_read_clo(infile_clo)
                    indx, indy = aatsr_read_loc(infile_loc, iflonlat = 0)
                    sza = read_h5py_item(infile_ang, 'sza')
                    nl, ns = lstN.shape[0], lstF.shape[1] # 行列数
                    if ndviN.shape[0]!=lstN.shape[0] or ndviF.shape[1]!=lstF.shape[1]:
                        with open('log_lsct_NDVI.txt','a') as f:
                            f.write(f'{infile_obs}\n')
                            f.write(f'    NDVI与LST行列数不匹配，跳过\n')
                        print(f'    NDVI与LST行列数不匹配，跳过')
                        continue

                    # 1. 计算有效发射率矩阵
                    emisS, emisV = emis_s_arr[indx, indy], emis_v_arr[indx, indy]
                    classif = classif_arr[indx, indy]

                    fvcN = (ndviN - ndvi_min) / (ndvi_max - ndvi_min)
                    fvcF = (ndviF - ndvi_min) / (ndvi_max - ndvi_min)
                    fvcN[fvcN < 0] = 0
                    fvcN[fvcN > 1] = 1
                    fvcF[fvcF < 0] = 0
                    fvcF[fvcF > 1] = 1
                    fvcN[cloN_mask == 0] = 0
                    fvcF[cloF_mask == 0] = 0

                    wN = np.stack([emisS * (1-fvcN), emisV * fvcN], axis=-1)  # 形状: (nl, ns, m)
                    wF = np.stack([emisS * (1-fvcF), emisV * fvcF], axis=-1)  # 形状: (nl, ns, m)
                    w = np.stack([wN, wF], axis=2)

                    # 2. 计算有效观测矩阵
                    bN = cal_rad_from_lst_fvc(lstN,wl,fvcN,emisS,emisV)
                    bF = cal_rad_from_lst_fvc(lstF,wl,fvcF,emisS,emisV)
                    b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2)

                    # 3. 多线程求解
                    inv_start_time = time.time()
                    lst = np.concatenate([lstN[:,:,np.newaxis], lstF[:,:,np.newaxis]], axis=2)
                    sza = 90 - sza/100
                    cloN_mask = cloN_mask * (fvcN>0.01) * (sza>0.0) * (sza<90.0)
                    cloF_mask = cloF_mask * (fvcF>0.01) * (sza>0.0) * (sza<90.0)
                    mask = np.concatenate([cloN_mask[:,:,np.newaxis], cloF_mask[:,:,np.newaxis]], axis=2)
                    mask = mask * (lst>lst_min)*(lst<lst_max) # 只保留合理范围内的LST
                    off = ws//2

                    # lsct = aatsr_inv_lsct2_window(n, m, ws, wl, w, b, mask, lst)
                    
                    ### 多进程
                    para = []
                    for kn in range(off, ns-off):
                        wLine = w[:,kn-off:kn+off+1,:,:]
                        bLine = b[:,kn-off:kn+off+1,:]
                        maskLine = mask[:,kn-off:kn+off+1,:]
                        lstLine = lst[:,kn-off:kn+off+1,:]
                        para.append([n,m,ws,wl,wLine,bLine,maskLine,lstLine])
                    tasks= []
                    pool = Pool(min(192,cpu_count()))
                    tasks = [pool.apply_async(aatsr_inv_lsct2_Line, tuple(p)) for p in para]
                    pool.close()
                    pool.join()
                    results = [t.get() for t in tasks]

                    lsct = np.zeros((nl, ns, m))
                    for idx, res in enumerate(results):
                        kn = idx + off
                        # 如果 res 形状是 (nl, m)，直接赋值
                        lsct[:, kn, :] = res

                    end_time = time.time()
                    print(f"    反演完成，耗时: {end_time - inv_start_time:.4f}秒")

                    Ts = lsct[:,:,0] * 100
                    Tv = lsct[:,:,1] * 100
                    fvcN = fvcN * 1000
                    fvcF = fvcF * 1000

                    mkdir_if_not_exist(outdir_lsct+time_str)

                    metadata = {
                        'Author': 'TIRT team',
                        'Version': '1.0',
                        'Create_time': datetime.now(timezone.utc).isoformat() + 'Z',
                    }
                    with h5py.File(outfile, 'w') as h5f:
                        for key, value in metadata.items():
                            h5f.attrs[key] = value

                        Ts_data = h5f.create_dataset('Ts', data=Ts, dtype='uint16', compression='gzip')
                        Ts_data.attrs['scalar'] = '0.01'

                        Tv_data = h5f.create_dataset('Tv', data=Tv, dtype='uint16', compression='gzip')
                        Tv_data.attrs['scalar'] = '0.01'

                        fvcN_data = h5f.create_dataset('fvcN', data=fvcN, dtype='uint16', compression='gzip')
                        fvcN_data.attrs['scalar'] = '0.001'

                        fvcF_data = h5f.create_dataset('fvcF', data=fvcF, dtype='uint16', compression='gzip')
                        fvcF_data.attrs['scalar'] = '0.001'

                    end_time = time.time()
                    print(f"执行时间: {end_time - start_time:.4f}秒")
