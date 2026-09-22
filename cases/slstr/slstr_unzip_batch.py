from base.files import mkdir_if_not_exist, search_file_rej

import sys
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


'''26.2.10'''
'''
只解压需要的数据，
fileName/
    S2_radiance_an.nc
    S2_quality_an.nc
    S2_radiance_ao.nc
    S2_quality_ao.nc
    S3_radiance_an.nc
    S3_quality_an.nc
    S3_radiance_ao.nc
    S3_quality_ao.nc
    geometry_tn.nc
    geometry_to.nc
    geodetic_in.nc
    geodetic_io.nc
    met_tx.nc
    S8_BT_in.nc
    S8_BT_io.nc
    S9_BT_in.nc
    S9_BT_io.nc
    flags_in.nc
    flags_io.nc
'''
'''25.10.12'''
'''SLSTR数据解压'''

WANTED_FILES = {
    'S2_radiance_an.nc', 'S2_quality_an.nc',
    'S2_radiance_ao.nc', 'S2_quality_ao.nc',
    'S3_radiance_an.nc', 'S3_quality_an.nc',
    'S3_radiance_ao.nc', 'S3_quality_ao.nc',
    'geometry_tn.nc', 'geometry_to.nc',
    'geodetic_in.nc', 'geodetic_io.nc',
    'met_tx.nc',
    'S8_BT_in.nc', 'S8_BT_io.nc',
    'S9_BT_in.nc', 'S9_BT_io.nc',
    'flags_in.nc', 'flags_io.nc'
}

# 添加线程锁用于打印输出，避免输出混乱
print_lock = threading.Lock()


def safe_print(*args, **kwargs):
    """线程安全的打印函数"""
    with print_lock:
        print(*args, **kwargs)


def unzip_file_SLSTR(zipfilename, outdir):
    '''
    解压zip文件中指定的文件
    :param zipfilename: 要解压文件名称
    :param outdir: 输出位置
    '''
    mkdir_if_not_exist(outdir)

    if os.path.exists(os.path.join(outdir, 'flags_io.nc')):
        return 1

    try:
        # 使用上下文管理器打开，无需手动close
        with zipfile.ZipFile(zipfilename, 'r') as zip_file:
            # 遍历压缩包内的所有文件
            for member in zip_file.namelist():
                filename = os.path.basename(member)

                # 检查文件名是否在我们需要列表中
                if filename in WANTED_FILES:
                    zip_file.extract(member, outdir)  # 解压到outdir目录下

        safe_print(f"Unzip finished: {os.path.basename(zipfilename)}")
        return 0
    except Exception as e:
        safe_print(f"Error unzipping {zipfilename}: {e}")
        return -1


def process_single_file(file_info):
    """
    处理单个文件的解压任务
    :param file_info: 包含文件信息的元组 (i, total, fileName, fileName0, year, indir_zip, outdir_unzip)
    :return: (fileName, success_status)
    """
    i, total, fileName, fileName0, year, indir_zip, outdir_unzip = file_info

    outdir = os.path.join(outdir_unzip, '%04d/raw/' % year)
    mkdir_if_not_exist(outdir)

    # 检查是否已处理过
    sen3_path = os.path.join(outdir, fileName[:-4] + '.SEN3')
    if os.path.exists(sen3_path):
        safe_print(f'[{i + 1}/{total}] Skipping (already processed): {fileName}')
        return (fileName, 'skipped')

    # 执行解压
    full_zip_path = os.path.join(indir_zip, fileName0)

    try:
        result = unzip_file_SLSTR(full_zip_path, outdir)
        if result == 0:
            safe_print(f'[{i + 1}/{total}] Success: {fileName}')
            return (fileName, 'success')
        else:
            safe_print(f'[{i + 1}/{total}] Already exists: {fileName}')
            return (fileName, 'exists')
    except Exception as e:
        safe_print(f'[{i + 1}/{total}] Error processing {fileName}: {e}')
        return (fileName, 'error')


def main():
    # --- 主逻辑 ---
    indir_zip = r'/media/hero/SLSTR_download3/S3A_Euro/2021/'
    outdir_unzip = r'/media/hero/SLSTR_download3/S3A_Euro/2021_tif/'
    start_year, end_year = 2021, 2022
    start_month, end_month = 1, 13

    # 可配置的线程数
    MAX_WORKERS = 64  # 可根据CPU核心数调整，通常设置为CPU核心数的2-4倍

    mkdir_if_not_exist(outdir_unzip)

    fileNames = search_file_rej(indir_zip, ['.zip'], 'aux')
    fileNames.sort()  # 确保文件按顺序处理
    fileNum = len(fileNames)
    print(f"Total files found: {fileNum}")

    # 准备任务列表
    tasks = []
    for i, fileName in enumerate(fileNames):
        # 处理文件名前缀逻辑
        fileName0 = fileName
        if fileName.split('_')[0] == '018':
            fileName = fileName[4:]

        # 提取时间
        try:
            timestr = fileName.split('_')[8]
            year = int(timestr[0:4])
            month = int(timestr[4:6])
        except (IndexError, ValueError) as e:
            print(f"Skipping {fileName}: Cannot parse date. Error: {e}")
            continue

        # 筛选时间范围
        if year < start_year or year >= end_year or month < start_month or month >= end_month:
            continue

        tasks.append((i, fileNum, fileName, fileName0, year, indir_zip, outdir_unzip))

    print(f"Files to process: {len(tasks)}")
    print(f"Using {MAX_WORKERS} threads...")

    # 使用线程池并行处理
    success_count = 0
    skipped_count = 0
    error_count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_file = {executor.submit(process_single_file, task): task[2] for task in tasks}

        # 处理完成的任务
        for future in as_completed(future_to_file):
            file_name = future_to_file[future]
            try:
                result_file, status = future.result()
                if status == 'success':
                    success_count += 1
                elif status == 'skipped':
                    skipped_count += 1
                elif status == 'exists':
                    skipped_count += 1
                else:
                    error_count += 1
            except Exception as e:
                print(f"Unexpected error processing {file_name}: {e}")
                error_count += 1

    # 输出统计信息
    print("\n" + "=" * 50)
    print("Processing completed!")
    print(f"Success: {success_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"Total: {len(tasks)}")


if __name__ == "__main__":
    main()
