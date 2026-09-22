import os
import sys
from base.files import search_file, un_gz

'''
26.1.2
AATSR 代码重构
解压原始数据，从gz解压到N1
'''

aatsr_zip_dir = r"/home/hero/data/ls4t/aatsr/zip/"
aatsr_raw_dir = r'/home/hero/data/ls4t/aatsr/raw/'

if __name__ == '__main__':
    for year in range(2006, 2007):
        for month in range(1, 13):
            for day in range(1, 32):
                time_str = '%04d/%02d/%02d' % (year, month, day)
                indir = aatsr_zip_dir + time_str + r"//ats_toa_1p//"
                if not os.path.exists(indir): continue
                filenames = search_file(indir,["gz"])
                num = 1
                for filename in filenames:
                    print(num, filename)
                    infile = indir + filename
                    outdir = aatsr_raw_dir + time_str + r"//"
                    un_gz(filename, indir, outdir)
                    num = num +1
