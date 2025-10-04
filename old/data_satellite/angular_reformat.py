import numpy as np
import sys
from util.util import *

"""
用于修正reformat后角度的结果
如果角度为负值，保存成uint16会出现问题，此脚本用于解决这个问题
最终存为int32，范围-2,147,483,648 到 2,147,483,647（int16，范围-32768 到 32767）
"""

indir_tif = r'D:\data\MOD\mod_tif\\'
outdir_tif = r'D:\data\MOD\mod_reformat\\'

fileNames = search_file_rej(indir_tif,['saa'],'enp') + search_file_rej(indir_tif,['vaa'],'enp')
fileNum = len(fileNames)
for k in range(fileNum):
    fileName = fileNames[k]
    infile = indir_tif + fileName
    print(k+1, infile)
    [temp, temp1, temp2, temp3, geog, proj] = read_image_gdal(infile)
    a, b = temp.shape
    ind = np.zeros([a, b])
    ind = temp > 36000
    save = temp.astype(int32)
    save[ind] = -(65536 - save[ind])
    outfile = outdir_tif + fileName
    write_image_gdal(save.astype(int32), temp1, temp2, temp3, geog, proj,outfile)

