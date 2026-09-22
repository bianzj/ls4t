import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cases.slstr.support.util_data import *
from cases.slstr.support.util_file import *

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


def unzip_file_SLSTR(zipfilename, outdir):
    '''
    解压zip文件中指定的文件
    :param zipfilename: 要解压文件名称
    :param outdir: 输出位置
    '''
    mkdir_if_not_exist(outdir)


    if os.path.exists(outdir + '/flags_io.nc'):
        return 1

    # 使用上下文管理器打开，无需手动close
    with zipfile.ZipFile(zipfilename, 'r') as zip_file:
        # 遍历压缩包内的所有文件
        for member in zip_file.namelist():
            filename = os.path.basename(member)

            # 检查文件名是否在我们需要列表中
            if filename in WANTED_FILES:
                zip_file.extract(member, outdir)  # 解压到outdir目录下

    print("Unzip finished!")


# --- 主逻辑 ---
#\\wsl.localhost\Ubuntu\mnt\wsl\PHYSICALDRIVE2\S3A_Euro_2022-2024
indir_zip = r'/media/hero/SLSTR_download1/S3A_Euro_2022-2024/2024/'
outdir_unzip = r'/media/hero/slstr-euro/'
start_year, end_year = 2024,2025
start_month, end_month = 1, 13

mkdir_if_not_exist(outdir_unzip)

fileNames = search_file_rej(indir_zip, ['.zip'], 'aux')
fileNames.sort()  # 确保文件按顺序处理
fileNum = len(fileNames)
print(fileNum)
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
    print(f'{i + 1}/{fileNum}: {fileName}')

    outdir = outdir_unzip + '%04d/raw/' % (year)
    mkdir_if_not_exist(outdir)

    # 执行解压
    full_zip_path = os.path.join(indir_zip, fileName0)  # 建议使用 os.path.join 拼接路径

    if os.path.exists(outdir + fileName[:-4] + '.SEN3'):
        continue
    else:
        try:
            unzip_file_SLSTR(indir_zip + fileName0, outdir)
        except Exception as e:
            print(f"Skipping {fileName}: {e}")
            continue
