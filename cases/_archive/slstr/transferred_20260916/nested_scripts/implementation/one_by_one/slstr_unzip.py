import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cases.slstr.support.util_data import *
from cases.slstr.support.util_file import *

'''25.10.12'''
'''SLSTR数据解压'''

indir_zip = r'/media/hero/MSG/euro/'
outdir_unzip = r'/media/hero/MSG/s3a/2025/raw'

mkdir_if_not_exist(outdir_unzip)

fileNames = search_file_rej(indir_zip,['.zip'],'aux')
fileNum = len(fileNames)
for i,fileName in enumerate(fileNames):
    if i+1<= 10456: continue
    print(f'{i+1}/{fileNum}: {fileName}')
    outdir = outdir_unzip
    unzip_file(indir_zip + fileName, outdir)
