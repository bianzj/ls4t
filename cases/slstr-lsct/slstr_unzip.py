import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from base.util_data import *
from base.util_file import *

'''25.10.12'''
'''SLSTR数据解压'''

indir_zip = r'/home/hero/data/SLSTR_heihe/zip/'
outdir_unzip = r'/home/hero/data/SLSTR_heihe/raw/'

mkdir_if_not_exist(outdir_unzip)

fileNames = search_file_rej(indir_zip,['.zip'],'aux')
fileNum = len(fileNames)
for i,fileName in enumerate(fileNames):
    print(f'{i+1}/{fileNum}: {fileName}')
    outdir = outdir_unzip
    unzip_file(indir_zip + fileName, outdir)
