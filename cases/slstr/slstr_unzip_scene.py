from base.files import mkdir_if_not_exist, search_file_rej, unzip_file

import sys
import os

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
