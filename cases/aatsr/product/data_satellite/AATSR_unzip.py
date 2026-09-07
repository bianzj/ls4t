import gzip
import os
import shutil
import sys
import calendar

'''
此脚本用于解压AATSR的gz文件
其目录格式为/data1/pub年份lic1/Bianzj/neodc/aatsr_multimission/.aatsr-v2.0-original/年份
'''

unzip = 1
# unzip_years = [2002, 2003, 2004, 2005, 2006, 2007]
unzip_years = ['2012']
months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
# year = sys.argv[1]
# month = sys.argv[2]
# day = sys.argv[3]

aatsr_zip_dir = r"/media/hero/raw01/"
aatsr_unzip_dir = r'/media/hero/SLSTR_Euro/'

def mkdir_if_not_exist(dir_name, is_delete=False):
    """
    创建文件夹
    :param dir_name: 文件夹
    :param is_delete: 是否删除
    :return: 是否成功
    """
    try:
        if is_delete:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                print("Path exists, remove and recreate")

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print("Created path:" + dir_name)
        return True
    except Exception as e:
        return False


def un_gz(file_name, infile, outdir):
    """ungz zip file"""
    mkdir_if_not_exist(outdir)
    f_name = outdir + file_name.replace(".gz", "")
    # 获取文件的名称，去掉
    g_file = gzip.GzipFile(infile + file_name)
    # 创建gzip对象
    open(f_name, "wb+").write(g_file.read())
    # gzip对象用read()打开后，写入open()建立的文件里。
    g_file.close()  # 关闭gzip对象
    print("Unzip " + filename + " finished!")


def search_file(dir, specstr):
    """
    在dir中寻找文件，文件名中带有需要的字符（最多三个），需要list把标识括起来，即使只有1个
    :param dir: 文件夹地址
    :param specstr:需要搜索的字符
    :return: 文件名列表
    """
    results = []
    num = len(specstr)
    if num == 0:
        results = os.listdir(dir)
    elif num == 1:
        specstr0 = specstr[0]
        results += [x for x in os.listdir(dir) if
                    os.path.isfile(os.path.join(dir, x)) and
                    specstr0 in x]
    elif num == 2:
        specstr1 = specstr[0]
        specstr2 = specstr[1]
        results += [x for x in os.listdir(dir) if
                    os.path.isfile(os.path.join(dir, x)) \
                    and specstr1 in x
                    and specstr2 in x]
    elif num == 3:
        specstr1 = specstr[0]
        specstr2 = specstr[1]
        specstr3 = specstr[2]
        results += [x for x in os.listdir(dir) if
                    os.path.isfile(os.path.join(dir, x)) \
                    and specstr1 in x
                    and specstr2 in x
                    and specstr3 in x]
    return results


if unzip == 1:
    base_dir = r'/media/hero/lsct03/'
    error_log_path = base_dir + r'unzip_error_log.txt'
    for year in unzip_years:
        for month in months:
            days = calendar.monthrange(int(year), int(month))[1]
            for d in range(days):
                day = '%02d' % (d + 1)
                infile = aatsr_zip_dir + year + r"//" + month + r"//" + day + r"//ats_toa_1p//"
                if not os.path.exists(infile): continue
                filenames = search_file(infile,["gz"])
                for num, filename in enumerate(filenames):
                    print(num, filename)
                    indir = infile + filename
                    outdir = aatsr_unzip_dir + year + r"//" + month + r"//" + day + r"//"
                    if os.path.exists(outdir):
                        if os.path.exists(outdir + filename.replace(".gz", "")): continue
                    try:
                        un_gz(filename, infile, outdir)
                    except Exception as e:
                        with open(error_log_path, 'a') as f:  # 使用追加模式
                            f.write(f" {infile}")
                            f.write(f"{str(e)}\n\n")
