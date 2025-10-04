import numpy as np
import pandas as pd
from util.myfun_lyf import *

### MOD

### 投影proj

### 批量创建pbs任务，以天为单位
#
# out_dir = r"D:\data\PBS\MOD_PROJ/"
#
# for doy in range(1,366,1):
#     filename = "MOD_PROJ_" + str(doy) +  '.txt'
#     file_dir = out_dir +filename
#     print(doy,file_dir)
#     with open(file_dir, 'w') as f:
#         f.write("# !/bin/bash" + "\n")
#         f.write("#PBS -N " + "MOD_PROJ_" + str(doy) +"\n")
#         f.write("#PBS -l nodes=1:ppn=4" + "\n")
#         f.write("#PBS -q rtlab1_4"+"\n")
#         f.write("#PBS -o /data1/home/AircasBianzj/TASK/MOD/MOD_PROJ/OUT/MOD_PROJ_"+ str(doy) +".out" + "\n")
#         f.write("#PBS -e /data1/home/AircasBianzj/TASK/MOD/MOD_PROJ/OUT/MOD_PROJ_" + str(doy) + ".err" + "\n")
#         f.write('date "+%Y/%m/%d %H:%M:%S"'+ "\n")
#         f.write("export PATH=/data1/home/AircasBianzj/python3.7.3/bin:$PATH"+ "\n")
#         f.write("/data1/home/AircasBianzj/python3.7.3/bin/python3 /data1/home/AircasBianzj/code/MOD_PROJ/MODIS_data_input.py 1 "+str(doy)+ "\n")
#         f.write('date "+%Y/%m/%d %H:%M:%S"')
#         f.close()
# batch_rename(out_dir,".txt",".pbs")

### 写SH文件
# sh_out_dir = r"D:\data\MOD_PBS/sh/"
# sh_filename = "MOD_PROJ"
# sh_file_dir = sh_out_dir +sh_filename +".txt"
# print(sh_file_dir)
# with open(sh_file_dir,"w") as f:
#     f.write('echo "batch proj start"' + '\n')
#     for doy in range(1,366,1):
#         dir = r"/data1/home/AircasBianzj/TASK/MOD/MOD_PROJ/PBS/"
#         filename = "MOD_PROJ_" + str(doy) + '.pbs'
#         f.write("qsub "+ dir+filename + "\n")
# batch_rename(sh_out_dir,".txt",".sh")


### 拼接 mosaic
### 批量创建pbs任务，以天为单位

# out_dir = r"D:\data\PBS\MOD_MOSAIC/"
#
# for doy in range(1,366,1):
#     filename = "MOD_MOSAIC_" + str(doy) +  '.txt'
#     file_dir = out_dir +filename
#     print(doy,file_dir)
#     with open(file_dir, 'w') as f:
#         f.write("# !/bin/bash" + "\n")
#         f.write("#PBS -N " + "MOD_MOSAIC_" + str(doy) +"\n")
#         f.write("#PBS -l nodes=1:ppn=4" + "\n")
#         f.write("#PBS -q rtlab1_4"+"\n")
#         f.write("#PBS -o /data1/home/AircasBianzj/TASK/MOD/MOD_MOSAIC/OUT/MOD_MOSAIC_"+ str(doy) +".out" + "\n")
#         f.write("#PBS -e /data1/home/AircasBianzj/TASK/MOD/MOD_MOSAIC/OUT/MOD_MOSAIC_" + str(doy) + ".err" + "\n")
#         f.write('date "+%Y/%m/%d %H:%M:%S"'+ "\n")
#         f.write("export PATH=/data1/home/AircasBianzj/python3.7.3/bin:$PATH"+ "\n")
#         f.write("/data1/home/AircasBianzj/python3.7.3/bin/python3 /data1/home/AircasBianzj/code/MOD_MOSAIC/MODIS_data_input.py 2 "+str(doy)+ "\n")
#         f.write('date "+%Y/%m/%d %H:%M:%S"')
#         f.close()
# batch_rename(out_dir,".txt",".pbs")
#
# ### 写SH文件
# sh_out_dir = r"D:\data\PBS\MOD_MOSAIC\sh/"
# sh_filename = "MOD_MOSAIC"
# sh_file_dir = sh_out_dir +sh_filename +".txt"
# print(sh_file_dir)
# with open(sh_file_dir,"w") as f:
#     f.write('echo "batch MOSAIC start"' + '\n')
#     for doy in range(1,366,1):
#         dir = r"/data1/home/AircasBianzj/TASK/MOD/MOD_MOSAIC/PBS/"
#         filename = "MOD_MOSAIC_" + str(doy) + '.pbs'
#         f.write("qsub "+ dir+filename + "\n")
# batch_rename(sh_out_dir,".txt",".sh")


### MYD

## 投影proj

## 批量创建pbs任务，以天为单位

out_dir = r"D:\data\PBS\MYD_PROJ/"

for doy in range(1,366,1):
    filename = "MYD_PROJ_" + str(doy) +  '.txt'
    file_dir = out_dir +filename
    print(doy,file_dir)
    with open(file_dir, 'w') as f:
        f.write("# !/bin/bash" + "\n")
        f.write("#PBS -N " + "MYD_PROJ_" + str(doy) +"\n")
        f.write("#PBS -l nodes=1:ppn=4" + "\n")
        f.write("#PBS -q rtlab1_4"+"\n")
        f.write("#PBS -o /data1/home/AircasBianzj/TASK/MYD/MYD_PROJ/OUT/MYD_PROJ_"+ str(doy) +".out" + "\n")
        f.write("#PBS -e /data1/home/AircasBianzj/TASK/MYD/MYD_PROJ/OUT/MYD_PROJ_" + str(doy) + ".err" + "\n")
        f.write('date "+%Y/%m/%d %H:%M:%S"'+ "\n")
        f.write("export PATH=/data1/home/AircasBianzj/python3.7.3/bin:$PATH"+ "\n")
        f.write("/data1/home/AircasBianzj/python3.7.3/bin/python3 /data1/home/AircasBianzj/code/MYD_PROJ/MODIS_data_input.py 1 "+str(doy)+ "\n")
        f.write('date "+%Y/%m/%d %H:%M:%S"')
        f.close()
batch_rename(out_dir,".txt",".pbs")

## 写SH文件
sh_out_dir = r"D:\data\PBS\MYD_PROJ\sh/"
sh_filename = "MYD_PROJ"
sh_file_dir = sh_out_dir +sh_filename +".txt"
print(sh_file_dir)
with open(sh_file_dir,"w") as f:
    f.write('echo "batch proj start"' + '\n')
    for doy in range(1,366,1):
        dir = r"/data1/home/AircasBianzj/TASK/MYD/MYD_PROJ/PBS/"
        filename = "MYD_PROJ_" + str(doy) + '.pbs'
        f.write("qsub "+ dir+filename + "\n")
batch_rename(sh_out_dir,".txt",".sh")


## 拼接 mosaic
## 批量创建pbs任务，以天为单位

out_dir = r"D:\data\PBS\MYD_MOSAIC/"

for doy in range(1,366,1):
    filename = "MYD_MOSAIC_" + str(doy) +  '.txt'
    file_dir = out_dir +filename
    print(doy,file_dir)
    with open(file_dir, 'w') as f:
        f.write("# !/bin/bash" + "\n")
        f.write("#PBS -N " + "MYD_MOSAIC_" + str(doy) +"\n")
        f.write("#PBS -l nodes=1:ppn=4" + "\n")
        f.write("#PBS -q rtlab1_4"+"\n")
        f.write("#PBS -o /data1/home/AircasBianzj/TASK/MYD/MYD_MOSAIC/OUT/MYD_MOSAIC_"+ str(doy) +".out" + "\n")
        f.write("#PBS -e /data1/home/AircasBianzj/TASK/MYD/MYD_MOSAIC/OUT/MYD_MOSAIC_" + str(doy) + ".err" + "\n")
        f.write('date "+%Y/%m/%d %H:%M:%S"'+ "\n")
        f.write("export PATH=/data1/home/AircasBianzj/python3.7.3/bin:$PATH"+ "\n")
        f.write("/data1/home/AircasBianzj/python3.7.3/bin/python3 /data1/home/AircasBianzj/code/MYD_MOSAIC/MODIS_data_input.py 2 "+str(doy)+ "\n")
        f.write('date "+%Y/%m/%d %H:%M:%S"')
        f.close()
batch_rename(out_dir,".txt",".pbs")

### 写SH文件
sh_out_dir = r"D:\data\PBS\MYD_MOSAIC\sh/"
sh_filename = "MYD_MOSAIC"
sh_file_dir = sh_out_dir +sh_filename +".txt"
print(sh_file_dir)
with open(sh_file_dir,"w") as f:
    f.write('echo "batch MOSAIC start"' + '\n')
    for doy in range(1,366,1):
        dir = r"/data1/home/AircasBianzj/TASK/MYD/MYD_MOSAIC/PBS/"
        filename = "MYD_MOSAIC_" + str(doy) + '.pbs'
        f.write("qsub "+ dir+filename + "\n")
batch_rename(sh_out_dir,".txt",".sh")



