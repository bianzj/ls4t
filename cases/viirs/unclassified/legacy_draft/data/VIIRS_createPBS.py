import numpy as np
import pandas as pd
from util.myfun_lyf import *

# ### VIIRS:VNP
#
# ## 投影proj
#
# ## 批量创建pbs任务，以天为单位
#
# out_dir = r"D:\data\PBS\VNP_PROJ/"
# mkdir_if_not_exist(out_dir)
#
# for doy in range(1,366,1):
#     filename = "VNP_PROJ_" + str(doy) +  '.txt'
#     file_dir = out_dir +filename
#     print(doy,file_dir)
#     with open(file_dir, 'w') as f:
#         f.write("# !/bin/bash" + "\n")
#         f.write("#PBS -N " + "VNP_PROJ_" + str(doy) +"\n")
#         f.write("#PBS -l nodes=1:ppn=4" + "\n")
#         f.write("#PBS -q rtlab1_4"+"\n")
#         f.write("#PBS -o /data1/home/AircasBianzj/TASK/VNP/VNP_PROJ/OUT/VNP_PROJ_"+ str(doy) +".out" + "\n")
#         f.write("#PBS -e /data1/home/AircasBianzj/TASK/VNP/VNP_PROJ/OUT/VNP_PROJ_" + str(doy) + ".err" + "\n")
#         f.write('date "+%Y/%m/%d %H:%M:%S"'+ "\n")
#         f.write("export PATH=/data1/home/AircasBianzj/python3.7.3/bin:$PATH"+ "\n")
#         f.write("/data1/home/AircasBianzj/python3.7.3/bin/python3 /data1/home/AircasBianzj/code/VNP_PROJ/VIIRS_data_input.py 1 "+str(doy)+ "\n")
#         f.write('date "+%Y/%m/%d %H:%M:%S"')
#         f.close()
# batch_rename(out_dir,".txt",".pbs")
#
# ## 写SH文件
# sh_out_dir = r"D:\data\PBS\VNP_PROJ/sh/"
# mkdir_if_not_exist(sh_out_dir)
# sh_filename = "VNP_PROJ"
# sh_file_dir = sh_out_dir +sh_filename +".txt"
# print(sh_file_dir)
# with open(sh_file_dir,"w") as f:
#     f.write('echo "batch proj start"' + '\n')
#     for doy in range(1,366,1):
#         dir = r"/data1/home/AircasBianzj/TASK/VNP/VNP_PROJ/PBS/"
#         filename = "VNP_PROJ_" + str(doy) + '.pbs'
#         f.write("qsub "+ dir+filename + "\n")
# batch_rename(sh_out_dir,".txt",".sh")
#
#
# ## 拼接 mosaic
# ## 批量创建pbs任务，以天为单位
#
# out_dir = r"D:\data\PBS\VNP_MOSAIC/"
# mkdir_if_not_exist(out_dir)
#
# for doy in range(1,366,1):
#     filename = "VNP_MOSAIC_" + str(doy) +  '.txt'
#     file_dir = out_dir +filename
#     print(doy,file_dir)
#     with open(file_dir, 'w') as f:
#         f.write("# !/bin/bash" + "\n")
#         f.write("#PBS -N " + "VNP_MOSAIC_" + str(doy) +"\n")
#         f.write("#PBS -l nodes=1:ppn=4" + "\n")
#         f.write("#PBS -q rtlab1_4"+"\n")
#         f.write("#PBS -o /data1/home/AircasBianzj/TASK/VNP/VNP_MOSAIC/OUT/VNP_MOSAIC_"+ str(doy) +".out" + "\n")
#         f.write("#PBS -e /data1/home/AircasBianzj/TASK/VNP/VNP_MOSAIC/OUT/VNP_MOSAIC_" + str(doy) + ".err" + "\n")
#         f.write('date "+%Y/%m/%d %H:%M:%S"'+ "\n")
#         f.write("export PATH=/data1/home/AircasBianzj/python3.7.3/bin:$PATH"+ "\n")
#         f.write("/data1/home/AircasBianzj/python3.7.3/bin/python3 /data1/home/AircasBianzj/code/VNP_MOSAIC/VIIRS_data_input.py 2 "+str(doy)+ "\n")
#         f.write('date "+%Y/%m/%d %H:%M:%S"')
#         f.close()
# batch_rename(out_dir,".txt",".pbs")
#
# ### 写SH文件
# sh_out_dir = r"D:\data\PBS\VNP_MOSAIC\sh/"
# mkdir_if_not_exist(sh_out_dir)
# sh_filename = "VNP_MOSAIC"
# sh_file_dir = sh_out_dir +sh_filename +".txt"
# print(sh_file_dir)
# with open(sh_file_dir,"w") as f:
#     f.write('echo "batch MOSAIC start"' + '\n')
#     for doy in range(1,366,1):
#         dir = r"/data1/home/AircasBianzj/TASK/VNP/VNP_MOSAIC/PBS/"
#         filename = "VNP_MOSAIC_" + str(doy) + '.pbs'
#         f.write("qsub "+ dir+filename + "\n")
# batch_rename(sh_out_dir,".txt",".sh")


# ### VJ1

## 投影proj

## 批量创建pbs任务，以天为单位

out_dir = r"D:\data\PBS\VJ1_PROJ/"
mkdir_if_not_exist(out_dir)

for doy in range(1,366,1):
    filename = "VJ1_PROJ_" + str(doy) +  '.txt'
    file_dir = out_dir +filename
    print(doy,file_dir)
    with open(file_dir, 'w') as f:
        f.write("# !/bin/bash" + "\n")
        f.write("#PBS -N " + "VJ1_PROJ_" + str(doy) +"\n")
        f.write("#PBS -l nodes=1:ppn=4" + "\n")
        f.write("#PBS -q rtlab1_4"+"\n")
        f.write("#PBS -o /data1/home/AircasBianzj/TASK/VJ1/VJ1_PROJ/OUT/VJ1_PROJ_"+ str(doy) +".out" + "\n")
        f.write("#PBS -e /data1/home/AircasBianzj/TASK/VJ1/VJ1_PROJ/OUT/VJ1_PROJ_" + str(doy) + ".err" + "\n")
        f.write('date "+%Y/%m/%d %H:%M:%S"'+ "\n")
        f.write("export PATH=/data1/home/AircasBianzj/python3.7.3/bin:$PATH"+ "\n")
        f.write("/data1/home/AircasBianzj/python3.7.3/bin/python3 /data1/home/AircasBianzj/code/VJ1_PROJ/VIIRS_data_input.py 1 "+str(doy)+ "\n")
        f.write('date "+%Y/%m/%d %H:%M:%S"')
        f.close()
batch_rename(out_dir,".txt",".pbs")

## 写SH文件
sh_out_dir = r"D:\data\PBS\VJ1_PROJ/sh/"
mkdir_if_not_exist(sh_out_dir)
sh_filename = "VJ1_PROJ"
sh_file_dir = sh_out_dir +sh_filename +".txt"
print(sh_file_dir)
with open(sh_file_dir,"w") as f:
    f.write('echo "batch proj start"' + '\n')
    for doy in range(1,366,1):
        dir = r"/data1/home/AircasBianzj/TASK/VJ1/VJ1_PROJ/PBS/"
        filename = "VJ1_PROJ_" + str(doy) + '.pbs'
        f.write("qsub "+ dir+filename + "\n")
batch_rename(sh_out_dir,".txt",".sh")


## 拼接 mosaic
## 批量创建pbs任务，以天为单位

out_dir = r"D:\data\PBS\VJ1_MOSAIC/"
mkdir_if_not_exist(out_dir)

for doy in range(1,366,1):
    filename = "VJ1_MOSAIC_" + str(doy) +  '.txt'
    file_dir = out_dir +filename
    print(doy,file_dir)
    with open(file_dir, 'w') as f:
        f.write("# !/bin/bash" + "\n")
        f.write("#PBS -N " + "VJ1_MOSAIC_" + str(doy) +"\n")
        f.write("#PBS -l nodes=1:ppn=4" + "\n")
        f.write("#PBS -q rtlab1_4"+"\n")
        f.write("#PBS -o /data1/home/AircasBianzj/TASK/VJ1/VJ1_MOSAIC/OUT/VJ1_MOSAIC_"+ str(doy) +".out" + "\n")
        f.write("#PBS -e /data1/home/AircasBianzj/TASK/VJ1/VJ1_MOSAIC/OUT/VJ1_MOSAIC_" + str(doy) + ".err" + "\n")
        f.write('date "+%Y/%m/%d %H:%M:%S"'+ "\n")
        f.write("export PATH=/data1/home/AircasBianzj/python3.7.3/bin:$PATH"+ "\n")
        f.write("/data1/home/AircasBianzj/python3.7.3/bin/python3 /data1/home/AircasBianzj/code/VJ1_MOSAIC/VIIRS_data_input.py 2 "+str(doy)+ "\n")
        f.write('date "+%Y/%m/%d %H:%M:%S"')
        f.close()
batch_rename(out_dir,".txt",".pbs")

### 写SH文件
sh_out_dir = r"D:\data\PBS\VJ1_MOSAIC\sh/"
mkdir_if_not_exist(sh_out_dir)
sh_filename = "VJ1_MOSAIC"
sh_file_dir = sh_out_dir +sh_filename +".txt"
print(sh_file_dir)
with open(sh_file_dir,"w") as f:
    f.write('echo "batch MOSAIC start"' + '\n')
    for doy in range(1,366,1):
        dir = r"/data1/home/AircasBianzj/TASK/VJ1/VJ1_MOSAIC/PBS/"
        filename = "VJ1_MOSAIC_" + str(doy) + '.pbs'
        f.write("qsub "+ dir+filename + "\n")
batch_rename(sh_out_dir,".txt",".sh")

