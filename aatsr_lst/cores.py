import sys
import os
import multiprocessing
import psutil
import platform


# ... 其他导入 ...

def print_cpu_info():
    """打印详细的CPU信息"""
    print("=" * 60)
    print("CPU Information:")
    print("=" * 60)

    # 1. 逻辑核心数（线程数）
    logical_cores = multiprocessing.cpu_count()
    print(f"Logical cores (threads): {logical_cores}")

    # 2. 物理核心数
    try:
        # 使用psutil获取物理核心数
        physical_cores = psutil.cpu_count(logical=False)
        print(f"Physical cores: {physical_cores}")
    except:
        # 如果psutil不可用，尝试其他方法
        try:
            if platform.system() == "Windows":
                physical_cores = int(os.environ.get('NUMBER_OF_PROCESSORS', logical_cores))
                # Windows下这个值可能不准确
                print(f"Physical cores (approx): {physical_cores}")
            else:
                # Linux/Mac
                physical_cores = len(os.sched_getaffinity(0))
                print(f"Physical cores (approx): {physical_cores}")
        except:
            print("Physical cores: Unable to determine")

    # 3. 当前进程可用的CPU核心数
    try:
        available_cores = len(os.sched_getaffinity(0))
        print(f"Available cores for this process: {available_cores}")
    except:
        print("Available cores: Unable to determine")

    # 4. CPU详细信息
    try:
        cpu_info = platform.processor()
        if cpu_info:
            print(f"Processor: {cpu_info}")
    except:
        pass

    # 5. 操作系统信息
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Machine: {platform.machine()}")

    # 6. 推荐进程数
    recommended = min(logical_cores, 16)  # 保守推荐
    if logical_cores > 16:
        print(f"\nRecommended processes (conservative): {recommended}")
        print(f"Recommended processes (aggressive): {logical_cores}")
        print(f"Note: Threadripper has many cores, but memory is the bottleneck!")
    else:
        print(f"\nRecommended processes: {recommended}")

    print("=" * 60)
    print()


def main():
    # 首先打印CPU信息
    print_cpu_info()

    # 配置参数
    indir0 = r"e://"
    outdir0 = r"e://aatsr_lsct_v2/"

    # ... 其他配置 ...

    # 根据CPU核心数和内存动态调整进程数
    logical_cores = multiprocessing.cpu_count()

    # 检测内存大小
    try:
        memory = psutil.virtual_memory()
        total_memory_gb = memory.total / (1024 ** 3)
        print(f"Total RAM: {total_memory_gb:.1f} GB")
        print(f"Available RAM: {memory.available / (1024 ** 3):.1f} GB")

        # 根据内存决定进程数
        if total_memory_gb >= 64:
            # 64GB+ 内存，可以使用更多进程
            num_processes = min(logical_cores, 24)
        elif total_memory_gb >= 32:
            # 32GB 内存，适度使用
            num_processes = min(logical_cores, 12)
        elif total_memory_gb >= 16:
            # 16GB 内存，保守使用
            num_processes = min(logical_cores, 8)
        else:
            # 16GB以下，非常保守
            num_processes = min(logical_cores, 4)
    except:
        # 如果无法检测内存，使用保守设置
        num_processes = min(logical_cores, 8)
        print("Unable to detect RAM, using conservative process count.")

    print(f"\nUsing {num_processes} processes for processing")
    print("=" * 60)

    # ... 继续处理 ...


if __name__ == '__main__':
    main()