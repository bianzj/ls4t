import gzip
import os
import shutil
import sys
import time

zip = 1
year = sys.argv[1]
month = sys.argv[2]
day = sys.argv[3]

# year = "2019"
# month = "01"
# day = "01"

aatsr_dir = r"/data1/public1/Bianzj/neodc/aatsr_multimission/aatsr-v2.1/data/ats_toa_1p//"
aatsr_zip_dir = r"/data1/public1/Bianzj/neodc/aatsr_multimission/.aatsr-v2.0-original//"

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

def make_gz(file_name, infile, out_dir):
    mkdir_if_not_exist(out_dir)
    f_name = infile + file_name #输出文件名
    g_file = out_dir + file_name + ".gz" #创建gz对象
    f = open(f_name, 'rb') #读取所需文件
    value = f.read()
    f.close()
    gz_file = gzip.GzipFile(filename="img.jpg", mode="wb", compresslevel=9,
                            fileobj=open(g_file, "wb"))
    gz_file.write(value)
    gz_file.close()
    print("zip " + filename + " finished!")


def search_file(dir, specstr, nstr=False):
    """
    在dir中寻找文件，文件名中带有需要的字符（最多三个），需要list把标识括起来，即使只有1个
    :param dir: 文件夹地址
    :param specstr:需要搜索的字符
    :return: 文件名列表
    :nstr：需要筛除的字符
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
    if nstr:
        num_2 = len(nstr)
        if num_2 == 1:
            nstr1 = nstr[0]
            for x in os.listdir(dir):
                if os.path.isfile(os.path.join(dir, x)) and nstr1 in x:
                    results.remove(x)
        if num_2 == 2:
            nstr1 = nstr[0]
            nstr2 = nstr[1]
            for x in os.listdir(dir):
                if os.path.isfile(os.path.join(dir, x)) and nstr1 in x and nstr2 in x:
                    results.remove(x)
        if num_2 == 3:
            nstr1 = nstr[0]
            nstr2 = nstr[1]
            nstr3 = nstr[2]
            for x in os.listdir(dir):
                if os.path.isfile(os.path.join(dir, x)) and nstr1 in x and nstr2 in x and nstr3 in x:
                    results.remove(x)



    return results


if zip == 1:
    infile = aatsr_dir + year + r"//" + month + r"//" + day + r"//"
    # infile = aatsr_dir + year + r"//" + month + r"//" + day + r"//"
    filenames = search_file(infile, ["N1"], ["md5"])
    num = 1
    for filename in filenames:
        print(num, filename)
        indir = infile + filename
        outdir = aatsr_zip_dir + year + r"//" + month + r"//" + day + r"//" + r"ats_toa_1p//"
        make_gz(filename, infile, outdir)
        num = num + 1