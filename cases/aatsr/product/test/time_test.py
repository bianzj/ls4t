import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from util_ls4t import *


def process_tile(tile_data):
    """处理单个数据块"""
    w, psoil = cal_effective_emissivity_hom(
        lai=tile_data['lai'],
        hspot=tile_data['hspot'],
        wl=tile_data['wl'],
        emisS=tile_data['emisS'],
        emisV=tile_data['emisV'],
        vza=tile_data['vza'],
        sza=tile_data['sza'],
        vaa=tile_data['vaa'],
        saa=tile_data['saa'],
        component_number=tile_data['component_number']
    )
    return {
        'w': w,
        'psoil': psoil,
        'y_start': tile_data['y_start'],
        'y_end': tile_data['y_end'],
        'x_start': tile_data['x_start'],
        'x_end': tile_data['x_end']
    }


def main():
    # 设置随机种子
    np.random.seed(42)

    # 数据维度
    nl, ns = 43520, 512
    print(f"数据尺寸: {nl}行 × {ns}列, 总像元数: {nl * ns:,}")

    # 生成模拟数据
    print("生成模拟数据...")
    start_time = time.time()

    # LAI: 0.5-5.0 的均匀分布
    lai = np.random.uniform(0.5, 5.0, size=(nl, ns))

    # 发射率参数
    emisS = np.random.uniform(0.9, 0.95, size=(nl, ns))  # 土壤发射率
    emisV = np.random.uniform(0.95, 0.97, size=(nl, ns))  # 植被发射率

    # 角度参数（单位：度）
    vza = np.random.uniform(0, 55, size=(nl, ns))  # 观测天顶角
    sza = np.random.uniform(0, 70, size=(nl, ns))  # 太阳天顶角
    vaa = np.random.uniform(0, 360, size=(nl, ns))  # 观测方位角
    saa = np.random.uniform(0, 360, size=(nl, ns))  # 太阳方位角

    print(f"数据生成完成，耗时: {time.time() - start_time:.2f}s")

    # 划分数据块 - 85个512×512的块
    block_size = 512
    num_blocks = nl // block_size
    print(f"划分数据为 {num_blocks} 个 {block_size}×{block_size} 的块...")

    tiles = []
    for i in range(num_blocks):
        y_start = i * block_size
        y_end = (i + 1) * block_size

        tile_data = {
            'lai': lai[y_start:y_end, :],
            'emisS': emisS[y_start:y_end, :],
            'emisV': emisV[y_start:y_end, :],
            'vza': vza[y_start:y_end, :],
            'sza': sza[y_start:y_end, :],
            'vaa': vaa[y_start:y_end, :],
            'saa': saa[y_start:y_end, :],
            'hspot': 0.1,
            'wl': 10.5,
            'component_number': 4,
            'y_start': y_start,
            'y_end': y_end,
            'x_start': 0,
            'x_end': ns
        }
        tiles.append(tile_data)

    # 准备结果容器
    full_w = np.zeros((4, nl, ns))
    full_psoil = np.zeros((nl, ns))

    # 获取CPU核心数
    num_cores = os.cpu_count()
    workers = min(num_cores, 192)  # 使用192个或实际核心数
    print(f"系统CPU核心数: {num_cores}, 使用 {workers} 个工作线程")

    # 多线程处理
    print("开始并行计算...")
    start_calc = time.time()

    completed_count = 0
    total_tiles = len(tiles)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # 提交所有任务
        future_to_tile = {executor.submit(process_tile, tile): i for i, tile in enumerate(tiles)}

        # 处理完成的任务
        for future in as_completed(future_to_tile):
            tile_result = future.result()

            # 更新进度
            completed_count += 1
            if completed_count % 5 == 0:
                elapsed = time.time() - start_calc
                print(f"进度: {completed_count}/{total_tiles} 块, "
                      f"耗时: {elapsed:.1f}s, "
                      f"剩余时间: {elapsed / completed_count * (total_tiles - completed_count):.1f}s")

            # 保存结果
            y_start = tile_result['y_start']
            y_end = tile_result['y_end']
            full_w[:, y_start:y_end, :] = tile_result['w']
            full_psoil[y_start:y_end, :] = tile_result['psoil']

    # 计算总耗时
    total_time = time.time() - start_calc
    print("\n计算完成!")
    print(f"总计算时间: {total_time:.2f}秒")
    print(f"处理速度: {nl * ns / total_time:,.0f} 像素/秒")

    # 返回结果 (实际使用时可以保存到文件)
    return full_w, full_psoil


if __name__ == "__main__":
    w_result, psoil_result = main()

    # 打印部分结果验证
    print("\n结果验证:")
    print(f"w 形状: {w_result.shape}")
    print(f"psoil 形状: {psoil_result.shape}")
    print("前5行前5列的土壤概率:")
    print(psoil_result[:5, :5])