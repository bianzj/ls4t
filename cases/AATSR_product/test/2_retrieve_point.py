import sys
import time
import numpy as np
from multiprocessing import Pool, cpu_count
from threading import Thread
from queue import Queue
sys.path.append('/home/hero/code/AATSR_product')
from util.util_ls4t import *

def inv_lsct_Nangle_Mcomponent_point(n,m,w,b,wl,method='ls'):
    '''
    单点反演
    :param n: 角度数
    :param m: 组分数
    :param w: 有效发射率矩阵
    :param b: rad矩阵
    :param method: 求解方法 ridge、lasso、bayesianridge、ls
    :return: lsct
    '''
    result = np.zeros([nl,ns,m])
    for i in range(nl):
        for j in range(ns):
            if np.sum(mask[i,j,:]) >= n:
                p = fitting_Nangle_Mcomponent_point(w[i,j,:,:],b[i,j,:],n,m,method = method)
                result[i,j,:] = p
    lsct = inv_planck(wl,result)
    return lsct

def _worker_chunk(args):
    """分块工作函数"""
    i_start, i_end, j_start, j_end, n, m, w, b, mask, method = args
    chunk_result = np.zeros([i_end-i_start, j_end-j_start, m])
    for i in range(i_start, i_end):
        for j in range(j_start, j_end):
            if np.sum(mask[i,j,:]) >= n:
                chunk_result[i-i_start, j-j_start, :] = fitting_Nangle_Mcomponent_point(
                    w[i,j,:,:], b[i,j,:], n, m, method=method)
    return i_start, i_end, j_start, j_end, chunk_result

def _process_in_parallel(n, m, w, b, mask, method, parallel_func, chunk_size=None):
    """并行处理框架(优化版)"""
    result = np.zeros([nl, ns, m])
    num_cores = cpu_count()
    
    # 动态计算分块大小
    if chunk_size is None:
        # 每个核心处理约4个任务
        chunk_size = max(100, (nl + num_cores * 4 - 1) // (num_cores * 4))
    
    # 创建分块任务 - 按行分块
    tasks = []
    for i in range(0, nl, chunk_size):
        tasks.append((
            i, min(i+chunk_size, nl),
            0, ns,  # 整行处理
            n, m, w, b, mask, method
        ))
    
    # 动态计算chunksize
    chunks_per_core = max(1, len(tasks) // (num_cores * 2))
    
    # 使用指定的并行函数处理
    for i_start, i_end, j_start, j_end, chunk_result in parallel_func(tasks, chunks_per_core):
        result[i_start:i_end, j_start:j_end, :] = chunk_result
    
    return result

def inv_lsct_Nangle_Mcomponent_point_mp(n,m,w,b,wl,method='ls',chunk_size=None):
    '''
    多进程单点反演(高性能优化版)
    '''
    def parallel_func(tasks, chunks_per_core):
        with Pool(processes=cpu_count()) as pool:
            # 使用starmap提高性能
            yield from pool.starmap(_worker_chunk, tasks, chunksize=chunks_per_core)
    
    result = _process_in_parallel(n,m,w,b,mask,method,parallel_func,chunk_size)
    lsct = inv_planck(wl,result)
    return lsct

def inv_lsct_Nangle_Mcomponent_point_mt(n,m,w,b,wl,method='ls',chunk_size=50):
    '''
    多线程单点反演(分块优化)
    '''
    def parallel_func(tasks):
        results = []
        threads = []
        q = Queue()
        
        def worker(task):
            q.put(_worker_chunk(task))
            
        for task in tasks:
            t = Thread(target=worker, args=(task,))
            t.start()
            threads.append(t)
        
        for _ in tasks:
            yield q.get()
            
        for t in threads:
            t.join()
    
    result = _process_in_parallel(n,m,w,b,mask,method,parallel_func,chunk_size)
    lsct = inv_planck(wl,result)
    return lsct

def inv_lsct_Nangle_Mcomponent_point_mt(n,m,w,b,wl,method='ls'):
    '''
    多线程单点反演
    '''
    result = np.zeros([nl,ns,m])
    q = Queue()
    threads = []
    
    def worker(i,j):
        if np.sum(mask[i,j,:]) >= n:
            p = fitting_Nangle_Mcomponent_point(w[i,j,:,:],b[i,j,:],n,m,method=method)
            q.put((i,j,p))
    
    for i in range(nl):
        for j in range(ns):
            t = Thread(target=worker, args=(i,j))
            t.start()
            threads.append(t)
    
    for _ in range(nl*ns):
        i,j,p = q.get()
        result[i,j,:] = p
    
    for t in threads:
        t.join()
    
    lsct = inv_planck(wl,result)
    return lsct

if __name__ == '__main__':
    ifmlp = 1
    ifmlt = 0

    '''读取数据'''
    n,m,nl,ns = 2,2,4352,50
    infile = outfile = r'/home/hero/code/AATSR_product/test/data/test_%01dangele_%01dcomponent_%d_%d.h5' % (n,m,nl,ns)
    name_list = ['n','m','nl','ns','Tsl','Tsh','Tvl','Tvh','lai','hspot','wl','emisS','emisV','vza','sza','vaa','saa','mask','bt','w','lst']
    n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,mask,bt,w,lst = read_h5py_items(infile,name_list)
    
    start_time = time.time()
    b = planck(wl,bt)
    if ifmlp + ifmlt == 0: # 1. 测试单点代码(不加速)
        print("开始单点反演...")
        lsct = inv_lsct_Nangle_Mcomponent_point(n,m,w,b,wl,method='bayesianridge')
    elif ifmlp:
        print("开始单点反演(多进程)...")
        lsct = inv_lsct_Nangle_Mcomponent_point_mp(n,m,w,b,wl,method='bayesianridge',chunk_size=50)
    elif ifmlt:
        print("开始单点反演(多线程)...")
        lsct = inv_lsct_Nangle_Mcomponent_point_mt(n,m,w,b,wl,method='bayesianridge')
    
    for i in range(m):
        print(lsct[:,:,i])
    end_time = time.time()
    print(f"\n执行时间: {end_time - start_time:.4f}秒")
    