import sys
sys.path.append('//')
from utils.old.util import *

'''
批量产生PBS文件
'''

### 批量创建pbs任务
# 产品名和操作名称
product_name = "AATSR"
edit_name = "lsct"
# 需要执行的python文件位置
py_dir = '/home/hero/code/AATSR_product_new/opt_lsct/opt_lsct2_mpl.py'

### 提供了两种批量的方法：0.年积日 1.年/月/日
method = 1

# PBS文件保存位置
# dir = r'/data1/home/AircasBianzj/TASK/' + product_name + r'/' + product_name + r'_' + edit_name + r'/'
dir = r'//home/hero/data/PBS/' + product_name + r'/' + product_name + r'_' + edit_name + r'/'
mkdir_if_not_exist(dir)
PBS_dir = dir + "PBS/"
mkdir_if_not_exist(PBS_dir)
OUT_dir = dir + "OUT/"
mkdir_if_not_exist(OUT_dir)
# PBS_name = product_name + r'_' + edit_name
PBS_name = edit_name

# 1.年积日
if method == 0:
    for doy in range(1, 366, 1):
        filename = PBS_name + '_' + str(doy) + '.txt'
        file_dir = PBS_dir + filename
        print(doy, file_dir)
        with open(file_dir, 'w') as f:
            f.write("# !/bin/bash" + "\n")
            f.write("#PBS -N " + PBS_name + '_' + str(doy) + "\n")
            f.write("#PBS -l nodes=1:ppn=4" + "\n")
            f.write("#PBS -q rtlab1_4" + "\n")
            f.write("#PBS -o " + OUT_dir + PBS_name + '_' + str(doy) + ".out" + "\n")
            f.write("#PBS -e " + OUT_dir + PBS_name + '_' + str(doy) + ".err" + "\n")
            f.write('date "+%Y/%m/%d %H:%M:%S"' + "\n")
            f.write("export PATH=/data1/home/AircasBianzj/python3.7.3/bin:$PATH" + "\n")
            f.write("/data1/home/AircasBianzj/python3.7.3/bin/python3 " + py_dir + " " + str(doy) + "\n")
            f.write('date "+%Y/%m/%d %H:%M:%S"')
            f.close()
    batch_rename(PBS_dir, ".txt", ".pbs")

# 2.年月日
years = [2002]
# months = [1,2,3,4,5,6,7,8,9,10,11,12]
# months = [1,2,3,4,5,6]
months = [7,8,9,10,11,12]

def Caluculate_DaysNum(year, month):
    if ((year % 4 == 0 and (year % 100) != 0) or (year % 400 == 0)):
        if (month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12):
            return 31
        elif (month == 2):
            return 28
        else:
            return 30
    else:
        if (month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12):
            return 31
        elif (month == 2):
            return 29
        else:
            return 30

if method == 1:
    for year in years:
        for month in months:
            daynum = Caluculate_DaysNum(year, month)
            days = np.linspace(1,daynum,daynum)
            for day in days:
                month = "%02d" % int(month)  # 存为01、02的格式
                day = "%02d" % int(day)
                time_str = str(year) + r'_' + str(month) + r'_' + str(day)
                filename = PBS_name + '_' + time_str + '.txt'
                file_dir = PBS_dir + filename
                print(time_str, file_dir)
                with open(file_dir, 'w') as f:
                    f.write("# !/bin/bash" + "\n")
                    f.write("#PBS -N " + PBS_name + '_' + time_str + "\n")
                    f.write("#PBS -l nodes=1:ppn=17" + "\n")
                    f.write("#PBS -q TIRT" + "\n")
                    f.write("#PBS -o " + OUT_dir + PBS_name + '_' + time_str + ".out" + "\n")
                    f.write("#PBS -e " + OUT_dir + PBS_name + '_' + time_str + ".err" + "\n")
                    f.write('date "+%Y/%m/%d %H:%M:%S"' + "\n")
                    f.write("export PATH=/home/hero/anaconda3/envs/python37/bin:$PATH" + "\n")
                    f.write("/home/hero/anaconda3/envs/python37/bin/python " + py_dir + " " + str(year) + r' ' + str(
                        month) + r' ' + str(day) + "\n")
                    f.write('date "+%Y/%m/%d %H:%M:%S"')
                    f.close()
            batch_rename(PBS_dir, ".txt", ".pbs")

## 写SH文件
sh_out_dir = dir
sh_filename = PBS_name
sh_file_dir = sh_out_dir + sh_filename + ".txt"
print(sh_file_dir)
with open(sh_file_dir, "w") as f:
    f.write('echo "batch start"' + '\n')
    if method == 0:
        for doy in range(1, 366, 1):
            filename = PBS_name + '_' + str(doy) + '.pbs'
            f.write("qsub " + PBS_dir + filename + "\n")
    elif method == 1:
        for year in years:
            for month in months:
                daynum = Caluculate_DaysNum(year, month)
                days = np.linspace(1, daynum, daynum)
                for day in days:
                    month = "%02d" % int(month)  # 存为01、02的格式
                    day = "%02d" % int(day)
                    time_str = str(year) + r'_' + str(month) + r'_' + str(day)
                    filename = PBS_name + '_' + time_str + '.pbs'
                    f.write("qsub " + PBS_dir + filename + "\n")
batch_rename(sh_out_dir, ".txt", ".sh")
