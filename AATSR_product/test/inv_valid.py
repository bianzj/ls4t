import sys
sys.path.append('/home/hero/code/AATSR_product')
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from util.util_base import *
from util.util_ls4t import *
from multiprocessing import Pool, freeze_support, cpu_count

'''2025.6.30'''
'''方法验证'''

def initial_para():
    nl, ns = 43520, 512
    lai = np.random.uniform(0.1, 5.0, size=(nl, ns))
    emisS = np.random.uniform(0.9, 0.97, size=(nl, ns))  # 土壤发射率
    emisV = np.random.uniform(0.93, 0.97, size=(nl, ns))  # 植被发射率
    vza1 = np.random.uniform(0, 30, size=(nl, ns))  # 观测天顶角
    vaa1 = np.random.uniform(0, 360, size=(nl, ns))  # 观测方位角
    vza2 = np.random.uniform(54, 56, size=(nl, ns))
    vaa2 = np.random.uniform(0, 360, size=(nl, ns))
    sza = np.random.uniform(0, 70, size=(nl, ns))  # 太阳天顶角
    saa = np.random.uniform(0, 360, size=(nl, ns))  # 太阳方位角

    Tsl = 315
    Tsh = 300
    Tvl = 303
    Tvh = 298

    hspot = 0.2
    wavelength = 10.8
    return lai,emisS,emisV,vza1,vaa1,vza2,vaa2,sza,saa,Tsl,Tsh,Tvl,Tvh,hspot,wavelength

def generate_2ang_hom_mlt(lai, emisS, emisV, vza1, vaa1, vza2, vaa2, sza, saa, Tsl, Tsh, Tvl, Tvh, hspot, wl,block_size):
    # 两角度 均质 场景 多线程
    start_time = time.time()
    nl,ns = 43520, 512
    wavelength = wl

    num_blocks = (nl + block_size - 1) // block_size
    print(f"划分数据为 {num_blocks} 个 {block_size}×{ns} 的块...")

    tiles = []
    for i in range(num_blocks):
        y_start = i * block_size
        y_end = min((i + 1) * block_size, nl)

        tile_data = {
            'lai': lai[y_start:y_end, :],
            'emisS': emisS[y_start:y_end, :],
            'emisV': emisV[y_start:y_end, :],
            'vza1': vza1[y_start:y_end, :],
            'vza2': vza2[y_start:y_end, :],
            'sza': sza[y_start:y_end, :],
            'vaa1': vaa1[y_start:y_end, :],
            'vaa2': vaa2[y_start:y_end, :],
            'saa': saa[y_start:y_end, :],
            'hspot': hspot,
            'wl': wl,
            'y_start': y_start,
            'y_end': y_end,
            'x_start': 0,
            'x_end': ns
        }
        tiles.append(tile_data)
    full_w1,full_w2 = np.zeros((4, nl, ns)),np.zeros((4, nl, ns))
    full_bt1,full_bt2 = np.zeros(( nl, ns)),np.zeros(( nl, ns))

    num_cores = os.cpu_count()
    workers = min(num_cores, 192)  # 使用192个或实际核心数
    # print("开始并行计算...")
    completed_count = 0
    total_tiles = len(tiles)

    def process_tile_mlt(tile_data):
        """处理单个数据块"""
        d = tile_data
        bt1 = sample_hom_bt(Tsl,Tsh,Tvl,Tvh,d['lai'],hspot,wavelength,d['emisS'],d['emisV'],d['vza1'],d['sza'],np.abs(d['vaa1']-d['saa']))
        bt2 = sample_hom_bt(Tsl, Tsh, Tvl, Tvh, d['lai'], hspot, wavelength, d['emisS'], d['emisV'], d['vza2'], d['sza'],
                           np.abs(d['vaa2'] - d['saa']))
        w1 = sample_hom_Emis(d['lai'],hspot,wavelength,d['emisS'],d['emisV'],d['vza1'],d['sza'],np.abs(d['vaa1']-d['saa']))
        w2 = sample_hom_Emis(d['lai'],hspot,wavelength,d['emisS'],d['emisV'],d['vza2'],d['sza'],np.abs(d['vaa2']-d['saa']))
        return {
            'w1': w1,
            'w2': w2,
            'bt1': bt1,
            'bt2': bt2,
            'y_start': tile_data['y_start'],
            'y_end': tile_data['y_end'],
            'x_start': tile_data['x_start'],
            'x_end': tile_data['x_end']
        }

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # 提交所有任务
        future_to_tile = {executor.submit(process_tile_mlt, tile): i for i, tile in enumerate(tiles)}

        # 处理完成的任务
        for future in as_completed(future_to_tile):
            tile_result = future.result()

            # 更新进度
            completed_count += 1
            if completed_count % 5 == 0:
                elapsed = time.time() - start_time
                print(f"进度: {completed_count}/{total_tiles} 块, "
                      f"耗时: {elapsed:.1f}s, "
                      f"剩余时间: {elapsed / completed_count * (total_tiles - completed_count):.1f}s")

            # 保存结果
            y_start = tile_result['y_start']
            y_end = tile_result['y_end']
            full_w1[:,y_start:y_end, :] = tile_result['w1']
            full_w2[:,y_start:y_end, :] = tile_result['w2']
            full_bt1[y_start:y_end, :] = tile_result['bt1']
            full_bt2[y_start:y_end, :] = tile_result['bt2']
    total_time = time.time() - start_time
    print("\n多线程计算完成!")
    print(f"总计算时间: {total_time:.2f}秒")
    # print(f"处理速度: {nl * ns / total_time:,.0f} 像素/秒")

    # 返回结果 (实际使用时可以保存到文件)
    return full_bt1, full_bt2, full_w1, full_w2

def process_tile(tile_data):
    """处理单个数据块"""
    d = tile_data
    hspot,wavelength = d['hspot'],d['wl']
    Tsl,Tsh,Tvl,Tvh = d['Tsl'],d['Tsh'],d['Tvl'],d['Tvh']
    bt1 = sample_hom_bt(Tsl,Tsh,Tvl,Tvh,d['lai'],hspot,wavelength,d['emisS'],d['emisV'],d['vza1'],d['sza'],np.abs(d['vaa1']-d['saa']))
    bt2 = sample_hom_bt(Tsl, Tsh, Tvl, Tvh, d['lai'], hspot, wavelength, d['emisS'], d['emisV'], d['vza2'], d['sza'],
                       np.abs(d['vaa2'] - d['saa']))
    w1 = sample_hom_Emis(d['lai'],hspot,wavelength,d['emisS'],d['emisV'],d['vza1'],d['sza'],np.abs(d['vaa1']-d['saa']))
    w2 = sample_hom_Emis(d['lai'],hspot,wavelength,d['emisS'],d['emisV'],d['vza2'],d['sza'],np.abs(d['vaa2']-d['saa']))
    return {
        'w1': w1,
        'w2': w2,
        'bt1': bt1,
        'bt2': bt2,
        'y_start': tile_data['y_start'],
        'y_end': tile_data['y_end'],
        'x_start': tile_data['x_start'],
        'x_end': tile_data['x_end']
    }

def generate_2ang_hom_mlp_old(lai, emisS, emisV, vza1, vaa1, vza2, vaa2, sza, saa, Tsl, Tsh, Tvl, Tvh, hspot, wl,block_size):
    # 两角度 均质 场景 多进程
    start_time = time.time()
    nl, ns = 43520, 512

    num_blocks = nl // block_size
    print(f"划分数据为 {num_blocks} 个 {block_size}×{ns} 的块...")

    para = []
    for i in range(num_blocks):
        y_start = i * block_size
        y_end = (i + 1) * block_size

        tile_data = {
            'lai': lai[y_start:y_end, :],
            'emisS': emisS[y_start:y_end, :],
            'emisV': emisV[y_start:y_end, :],
            'vza1': vza1[y_start:y_end, :],
            'vza2': vza2[y_start:y_end, :],
            'sza': sza[y_start:y_end, :],
            'vaa1': vaa1[y_start:y_end, :],
            'vaa2': vaa2[y_start:y_end, :],
            'saa': saa[y_start:y_end, :],
            'hspot': hspot,
            'wl': wl,
            'y_start': y_start,
            'y_end': y_end,
            'x_start': 0,
            'x_end': ns,
            'Tsl' : Tsl,
            'Tsh': Tsh,
            'Tvl': Tvl,
            'Tvh': Tvh,
        }
        para.append(tile_data)
    full_w1,full_w2 = np.zeros((4, nl, ns)),np.zeros((4, nl, ns))
    full_bt1,full_bt2 = np.zeros(( nl, ns)),np.zeros(( nl, ns))


    # print("开始并行计算...")
    start_calc = time.time()
    pool = Pool(min(192, cpu_count()))
    # 提交所有任务
    tasks = [pool.apply_async(process_tile, (p,)) for p in para]

    # 获取结果并填充到full数组
    completed = 0
    total = len(tasks)

    for task in tasks:
        result = task.get()  # 获取计算结果

        # 填充结果到full数组
        y_slice = slice(result['y_start'], result['y_end'])
        x_slice = slice(result['x_start'], result['x_end'])

        full_w1[:, y_slice, x_slice] = result['w1']
        full_w2[:, y_slice, x_slice] = result['w2']
        full_bt1[y_slice, x_slice] = result['bt1']
        full_bt2[y_slice, x_slice] = result['bt2']

        # 进度报告
        completed += 1
        if completed % 5 == 0:
            elapsed = time.time() - start_calc
            remaining = elapsed / completed * (total - completed)
            # print(f"进度: {completed}/{total} 块, "
            #       f"耗时: {elapsed:.1f}s, "
            #       f"剩余时间: {remaining:.1f}s")

    # 关闭进程池
    pool.close()
    pool.join()

    # 计算统计信息
    total_time = time.time() - start_calc
    print("多进程计算完成!")
    print(f"总计算时间: {total_time:.2f}秒")
    # print(f"处理速度: {nl * ns / total_time:,.0f} 像素/秒")

    return full_bt1, full_bt2, full_w1, full_w2

def generate_2ang_hom_mlp(lai, emisS, emisV, vza1, vaa1, vza2, vaa2, sza, saa,
                          Tsl, Tsh, Tvl, Tvh, hspot, wl, x_size, y_size):
    """两角度均质场景多进程计算（按x_size×y_size分块）"""
    start_time = time.time()
    nl, ns = lai.shape  # 获取输入数据的实际尺寸

    # 计算分块数量
    num_blocks_x = (ns + x_size - 1) // x_size  # 沿x方向分块数
    num_blocks_y = (nl + y_size - 1) // y_size  # 沿y方向分块数
    total_blocks = num_blocks_x * num_blocks_y
    print(f"划分数据为 {total_blocks} 个区块（{y_size}×{x_size}）...")

    # 准备任务参数
    para = []
    for i in range(num_blocks_y):
        for j in range(num_blocks_x):
            y_start = i * y_size
            y_end = min((i + 1) * y_size, nl)
            x_start = j * x_size
            x_end = min((j + 1) * x_size, ns)

            tile_data = {
                'lai': lai[y_start:y_end, x_start:x_end],
                'emisS': emisS[y_start:y_end, x_start:x_end],
                'emisV': emisV[y_start:y_end, x_start:x_end],
                'vza1': vza1[y_start:y_end, x_start:x_end],
                'vza2': vza2[y_start:y_end, x_start:x_end],
                'sza': sza[y_start:y_end, x_start:x_end],
                'vaa1': vaa1[y_start:y_end, x_start:x_end],
                'vaa2': vaa2[y_start:y_end, x_start:x_end],
                'saa': saa[y_start:y_end, x_start:x_end],
                'hspot': hspot,
                'wl': wl,
                'y_start': y_start,
                'y_end': y_end,
                'x_start': x_start,
                'x_end': x_end,
                'Tsl': Tsl,
                'Tsh': Tsh,
                'Tvl': Tvl,
                'Tvh': Tvh
            }
            para.append(tile_data)

    # 预分配结果数组
    full_w1 = np.zeros((4, nl, ns))
    full_w2 = np.zeros((4, nl, ns))
    full_bt1 = np.zeros((nl, ns))
    full_bt2 = np.zeros((nl, ns))

    # 多进程计算
    start_calc = time.time()

    with Pool(min(192, cpu_count())) as pool:
        # 提交任务并获取结果
        for i, result in enumerate(pool.imap_unordered(process_tile, para)):
            # 填充结果
            y_slice = slice(result['y_start'], result['y_end'])
            x_slice = slice(result['x_start'], result['x_end'])

            full_w1[:, y_slice, x_slice] = result['w1']
            full_w2[:, y_slice, x_slice] = result['w2']
            full_bt1[y_slice, x_slice] = result['bt1']
            full_bt2[y_slice, x_slice] = result['bt2']

            # 进度报告（每10%进度报告一次）
            if (i + 1) % max(1, total_blocks // 10) == 0:
                elapsed = time.time() - start_calc
                # print(f"进度: {i + 1}/{total_blocks} 块 [{(i + 1) / total_blocks:.0%}] 耗时: {elapsed:.1f}s")
    pool.close()

    # 性能统计
    total_time = time.time() - start_time
    print(f"计算完成! 总耗时: {total_time:.2f}秒")
    print(f"处理速度: {nl * ns / total_time:,.0f} 像素/秒")

    return full_bt1, full_bt2, full_w1, full_w2

if __name__ == "__main__":
    lai, emisS, emisV, vza1, vaa1, vza2, vaa2, sza, saa, Tsl, Tsh, Tvl, Tvh, hspot, wl = initial_para()
    # bt1, bt2, w1, w2 = generate_2ang_hom_mlt(lai, emisS, emisV, vza1, vaa1, vza2, vaa2, sza, saa, Tsl, Tsh, Tvl, Tvh,
    #                                          hspot, wl, 1024)
    bt1, bt2_, w1, w2_ = generate_2ang_hom_mlt(lai, emisS, emisV, vza1, vaa1, vza2, vaa2, sza, saa, Tsl, Tsh, Tvl,
                                                 Tvh,
                                                 hspot, wl, 1024)
    # for y_size in [1,1,1,1,1,1,1,1,1,1]:
    #     print(y_size)
    #     bt1_, bt2_, w1_, w2_ = generate_2ang_hom_mlp(lai, emisS, emisV, vza1, vaa1, vza2, vaa2, sza, saa, Tsl, Tsh,
    #                                                      Tvl, Tvh, hspot, wl,  512,y_size)
    #     print(np.mean(bt1 - bt1_), np.mean(w1 - w1_))

    for block_size in [1024,1024,1024,1024,1024,1024,1024,1024,1024]:
        print(block_size)
        bt1_, bt2_, w1_, w2_ = generate_2ang_hom_mlt(lai, emisS, emisV, vza1, vaa1, vza2, vaa2, sza, saa, Tsl, Tsh, Tvl, Tvh,
                                                 hspot, wl, block_size)
        # bt1_, bt2_, w1_, w2_ = generate_2ang_hom_mlp(lai, emisS, emisV, vza1, vaa1, vza2, vaa2, sza, saa, Tsl, Tsh,
        #                                              Tvl, Tvh, hspot, wl,  512,y_size)
        print(np.mean(bt1 - bt1_), np.mean(w1 - w1_))




    # print(np.mean(bt1 - bt1_), np.mean(w1 - w1_))
    # print(np.max(np.abs(bt1 - bt1_)), np.max(np.abs(bt2 - bt2_)))