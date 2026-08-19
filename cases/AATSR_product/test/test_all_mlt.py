import sys
sys.path.append('/home/hero/code/AATSR_product')
from util.util_ls4t import *
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

'''2025.9.11'''
'''所有代码测试'''
def initial_para():
    n ,m = 2,2 # 角度数，组分数
    nl,ns = 43520,512 # 行列数
    Tsl = np.full((nl,ns),315)
    Tsh = np.full((nl,ns),315)
    Tvl = np.full((nl,ns),300)
    Tvh = np.full((nl,ns),300)
    hspot = 1.0
    wl = 10.8
    lai = np.random.uniform(0.1, 5.0, size=(nl, ns))
    emisS = np.random.uniform(0.92, 0.95, size=(nl, ns))  # 土壤发射率
    emisV = np.random.uniform(0.95, 0.97, size=(nl, ns))  # 植被发射率
    vza = np.random.uniform(0, 70, size=(nl,ns,n))
    vaa = np.random.uniform(0, 360, size=(nl,ns,n))
    sza = np.full((nl,ns,n),45)
    saa = np.full((nl,ns,n),180)
    mask = np.random.randint(0, 2, (nl,ns,n))  # mask = np.full((nl,ns,n),1)
    return n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa, mask


if __name__ == '__main__':
    import time

    '''A.生成区域代码 测试'''
    n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,mask = initial_para()
    
    print("图像开始生成...")
    start_time = time.time()
    bt,w = generate_hom_Nangle_Mcomponent_mlt(n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,ifmlt=1)
    lst = np.zeros([nl,ns,n])
    for i in range(n):
        lst[:,:,i] = cal_lst_from_bt(bt[:,:,i],wl,lai,vza[:,:,i],emisS,emisV)
    end_time = time.time()
    
    # print("\n测试结果:")
    # print(bt.shape,w.shape)
    # print(bt,w)
    print(f"\n执行时间: {end_time - start_time:.4f}秒")

    outfile = r'/home/hero/code/AATSR_product/test/data/test_%01dangele_%01dcomponent.h5' % (n,m)
    name_list = ['n','m','nl','ns','Tsl','Tsh','Tvl','Tvh','lai','hspot','wl','emisS','emisV','vza','sza','vaa','saa','mask','bt','w','lst']
    data_list = [n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,mask,bt,w,lst]
    dtype_list = ['int','int','int','int','float','float','float','float','float','float','float','float','float','float','float','float','float','float','float','float','float']
    write_h5py_file(outfile,name_list,data_list,dtype_list)


    # '''B. 反演代码 测试'''
    # b = planck(wl, bt)
    # print("开始分块多线程反演...")
    # print(f"数据尺寸: {nl} × {ns} = {nl * ns} 个点")
    # print(f"分块大小: 64×64")
    # print(f"CPU核心数: 192")

    # start_time = time.time()

    # result = np.zeros([nl, ns, m])

    # # 定义分块大小
    # chunk_size = 512

    # # 计算分块数量
    # num_chunks_i = (nl + chunk_size - 1) // chunk_size
    # num_chunks_j = (ns + chunk_size - 1) // chunk_size
    # total_chunks = num_chunks_i * num_chunks_j

    # print(f"分块数量: {num_chunks_i} × {num_chunks_j} = {total_chunks} 块")

    # # 准备所有任务
    # tasks = []
    # for i in range(num_chunks_i):
    #     for j in range(num_chunks_j):
    #         i_start = i * chunk_size
    #         i_end = min((i + 1) * chunk_size, nl)
    #         j_start = j * chunk_size
    #         j_end = min((j + 1) * chunk_size, ns)
    #         tasks.append(((i_start, i_end), (j_start, j_end), w, b, mask, n, m, 'ls'))

    # print(f"任务数量: {len(tasks)}")

    # # 使用线程池执行，设置合适的线程数
    # # 对于192核心，可以设置稍多一些的线程数，但不要过多以免上下文切换开销
    # max_workers = min(200, len(tasks))  # 限制最大线程数

    # print(f"使用线程数: {max_workers}")

    # completed_chunks = 0
    # total_chunks = len(tasks)

    # with ThreadPoolExecutor(max_workers=max_workers) as executor:
    #     # 提交所有任务
    #     future_to_chunk = {executor.submit(process_chunk, task): task for task in tasks}
        
    #     # 处理完成的任务
    #     for future in as_completed(future_to_chunk):
    #         try:
    #             chunk_i, chunk_j, chunk_result = future.result()
    #             i_start, i_end = chunk_i
    #             j_start, j_end = chunk_j
                
    #             # 将结果写入到总数组中
    #             result[i_start:i_end, j_start:j_end, :] = chunk_result
                
    #             completed_chunks += 1
    #             if completed_chunks % 100 == 0:  # 每完成100块打印进度
    #                 progress = completed_chunks / total_chunks * 100
    #                 print(f"进度: {completed_chunks}/{total_chunks} ({progress:.1f}%)")
                    
    #         except Exception as e:
    #             chunk_i, chunk_j = future_to_chunk[future][:2]
    #             print(f"处理块{chunk_i}-{chunk_j}时出错: {e}")

    # print(f"所有任务完成! 共处理 {completed_chunks} 个数据块")

    # lsct = inv_planck(wl, result)
    # print(lsct)

    # end_time = time.time()
    # total_time = end_time - start_time
    # print(f"\n多线程执行时间: {total_time:.4f}秒")
    # print(f"平均每块处理时间: {total_time/len(tasks):.4f}秒")